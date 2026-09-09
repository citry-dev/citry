"""Serve preview routes in a command-owned process without changing engine routes."""

from __future__ import annotations

import importlib
import math
import socket
import threading
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs
from urllib.request import ProxyHandler, build_opener

from typing_extensions import Self

from citry.contrib.asgi import asgi_app
from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse, call_maybe_sync, match_route

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, MutableMapping
    from types import TracebackType

    from citry import Citry
    from citry.util.routing import URLRoute

    Scope = MutableMapping[str, Any]
    Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
    Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
    ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_MOUNT = "/citry"
_PREVIEW = f"{_MOUNT}/ext/preview/"
_HOST_LOCK = threading.Lock()
_ACTIVE_ENGINES: set[Citry] = set()


async def _respond(send: Send, response: RouteResponse, *, head: bool = False) -> None:
    # Even errors must bypass caches: the command may serve edited examples next time.
    headers = [(b"content-type", response.content_type.encode("latin-1")), (b"cache-control", b"no-store")]
    headers.extend(
        (name.lower().encode("latin-1"), value.encode("latin-1"))
        for name, value in response.headers
        if name.lower() != "cache-control"
    )
    await send({"type": "http.response.start", "status": response.status, "headers": headers})
    await send({"type": "http.response.body", "body": b"" if head else response.body})


def preview_app(citry: Citry, routes: tuple[URLRoute, ...]) -> ASGIApp:
    """Build a root ASGI host with preview-relative routes mounted below ``/citry/ext/preview/``."""
    ordinary = asgi_app(citry)
    routes = tuple(routes)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await ordinary(scope, receive, send)
            return
        if scope["type"] != "http":
            # Neither this development host nor the ordinary adapter serves WebSockets.
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1000})
                return
            msg = f"Unsupported preview ASGI scope: {scope['type']!r}"
            raise RuntimeError(msg)
        path = scope["path"]
        method = scope["method"]
        head = method == "HEAD"
        if not path.startswith(_PREVIEW):
            if path == _MOUNT or path.startswith(_MOUNT + "/"):
                # Copy the scope so the ordinary adapter sees a genuine mount without
                # mutating the caller's request or adding routes to the engine.
                await ordinary({**scope, "root_path": _MOUNT}, receive, send)
            else:
                await _respond(send, RouteResponse("Not Found", status=404), head=head)
            return
        matched = match_route(routes, path[len(_PREVIEW) :])
        if matched is None:
            await _respond(send, RouteResponse("Not Found", status=404), head=head)
            return
        if method not in ("GET", "HEAD") or (method not in matched.route.methods and not head):
            await _respond(
                send, RouteResponse("Method Not Allowed", status=405, headers=(("Allow", "GET, HEAD"),)), head=head
            )
            return
        headers = RouteHeaders(
            (key.decode("latin-1"), value.decode("latin-1")) for key, value in scope.get("headers", ())
        )
        query = parse_qs(scope.get("query_string", b"").decode("latin-1"), keep_blank_values=True)
        request = RouteRequest(
            method=method,
            path=path,
            query={key: tuple(values) for key, values in query.items()},
            headers=headers,
            content_type=headers.get("content-type", ""),
            native=scope,
        )
        handler = matched.route.handler_async or matched.route.handler
        assert handler is not None  # noqa: S101 - match_route only returns handler routes
        response = await call_maybe_sync(handler, request, **matched.params)
        await _respond(send, response, head=head)

    return app


class PreviewServer:
    """
    Own a loopback Uvicorn listener until context exit, with bounded startup.

    A prior mounted prefix is restored on exit. An initially unmounted command
    engine retains ``/citry`` because the public mount API does not support clearing
    a prefix. Neither case changes the engine's route table.
    """

    def __init__(
        self, citry: Citry, routes: tuple[URLRoute, ...], *, port: int = 0, startup_timeout: float = 10
    ) -> None:
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            msg = "Preview port must be an integer from 0 through 65535"
            raise ValueError(msg)
        if not math.isfinite(startup_timeout) or startup_timeout <= 0:
            msg = "Preview startup timeout must be positive and finite"
            raise ValueError(msg)
        self.citry = citry
        self.routes = tuple(routes)
        self.port = port
        self.startup_timeout = startup_timeout
        self.base_url = ""
        self._server: Any = None
        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._failure: BaseException | None = None
        self._claimed = False
        self._previous_prefix: str | None = None

    def __enter__(self) -> Self:
        # The dependency is optional: HTML rendering and imports never require it.
        try:
            uvicorn = importlib.import_module("uvicorn")
        except ImportError as exc:
            msg = 'Preview serving requires Uvicorn; install "citry[ext-preview]".'
            raise RuntimeError(msg) from exc
        with _HOST_LOCK:
            if self.citry in _ACTIVE_ENGINES:
                msg = "A preview server is already running for this Citry engine"
                raise RuntimeError(msg)
            _ACTIVE_ENGINES.add(self.citry)
            self._claimed = True
        self._previous_prefix = self.citry.mounted_prefix
        try:
            self.citry.initialize()
            # Bind before changing the mount so a port conflict leaves it untouched.
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind(("127.0.0.1", self.port))
            self._socket.listen(128)
            self.citry.set_mounted_prefix(_MOUNT)
            self.port = self._socket.getsockname()[1]
            self.base_url = f"http://127.0.0.1:{self.port}{_MOUNT}"
            config = uvicorn.Config(
                preview_app(self.citry, self.routes),
                host="127.0.0.1",
                port=self.port,
                log_level="warning",
                access_log=False,
                lifespan="on",
                timeout_graceful_shutdown=2,
            )
            self._server = uvicorn.Server(config)
            self._failure = None
            self._thread = threading.Thread(target=self._run, name="citry-preview", daemon=True)
            self._thread.start()
            self._await_startup()
        except BaseException:
            self.close()
            raise
        return self

    def _run(self) -> None:
        try:
            self._server.run(sockets=[self._socket])
        except BaseException as exc:  # noqa: BLE001 - propagate server-thread failures to the command thread
            self._failure = exc

    def _await_startup(self) -> None:
        deadline = time.monotonic() + self.startup_timeout
        # Ignore shell proxy settings for the owned loopback health request.
        opener = build_opener(ProxyHandler({}))
        while time.monotonic() < deadline:
            if self._thread is None or not self._thread.is_alive():
                msg = "Preview server stopped during startup"
                raise RuntimeError(msg) from self._failure
            if self._server.started:
                try:
                    with opener.open(
                        self.base_url + "/citry.js", timeout=min(0.2, max(0.001, deadline - time.monotonic()))
                    ) as response:
                        if response.status == 200:
                            return
                except OSError:
                    pass  # A listener can be bound before the event loop accepts requests.
            time.sleep(0.01)
        msg = f"Preview server did not become ready within {self.startup_timeout:g} seconds"
        raise RuntimeError(msg)

    def wait(self) -> None:
        """Keep the command alive until interruption or unexpected server termination."""
        if self._thread is None:
            msg = "Preview server has not started"
            raise RuntimeError(msg)
        while self._thread.is_alive():
            self._thread.join(0.25)
        msg = "Preview server stopped unexpectedly"
        raise RuntimeError(msg) from self._failure

    def close(self) -> None:
        """Stop the owned server and release its engine claim, including after startup failure."""
        if not self._claimed:
            return
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(4)
            if self._thread.is_alive():
                self._server.force_exit = True
                self._thread.join(1)
        if self._socket is not None:
            self._socket.close()
        if self._thread is not None and self._thread.is_alive():
            # A stuck worker cannot safely share its engine with a second host.
            # Keep the claim and prefix until a later close confirms termination.
            msg = "Preview server did not stop within five seconds; its engine cannot start another host"
            raise RuntimeError(msg)
        try:
            if self._previous_prefix is not None:
                self.citry.set_mounted_prefix(self._previous_prefix or "/")
        finally:
            with _HOST_LOCK:
                _ACTIVE_ENGINES.discard(self.citry)
                self._claimed = False

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self.close()
