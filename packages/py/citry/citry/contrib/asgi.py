"""
A generic ASGI sub-application serving a ``Citry`` instance's routes.

Mount it at a prefix in any ASGI framework, then record the prefix on the
instance so URL building works::

    from citry.contrib.asgi import asgi_app

    app.mount("/citry", asgi_app(citry_instance))   # Starlette / FastAPI
    citry_instance.set_mounted_prefix("/citry")

(The ``citry.contrib.fastapi.mount`` convenience does both.) Uses no
third-party packages; only the ASGI 3 protocol.

Like every citry.contrib adapter, the app does one job in three steps:
translate the host's request into a framework-neutral ``RouteRequest``,
hand it to the matched citry route handler, and translate the returned
``RouteResponse`` back into the host's response shape (here: ASGI
messages). Everything else in this file is ASGI-protocol bookkeeping.

Route handlers may be plain functions or ``async def``: async handlers are
awaited on the event loop, plain ones run in a worker thread so they cannot
block the loop (see ``citry.util.routing.call_maybe_sync``). A route that
carries an ``async def`` twin of its handler (``URLRoute.handler_async``) is
served through the twin here, so it runs natively on the loop while the
plain handler keeps serving the sync hosts.

For development, initialize Citry and add a hot-reload watcher in the app's
root lifespan::

    from contextlib import asynccontextmanager
    from citry.contrib.asgi import reload_lifespan

    watch_lifespan = reload_lifespan(citry_instance)

    @asynccontextmanager
    async def lifespan(app):
        citry_instance.initialize()
        async with watch_lifespan(app):
            yield

    app = FastAPI(lifespan=lifespan)   # or Starlette(...)
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

from citry.reload import watch
from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse, call_maybe_sync, match_route

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, MutableMapping
    from contextlib import AbstractAsyncContextManager
    from pathlib import Path

    from citry.citry import Citry
    from citry.component import Component
    from citry.reload import FileWatcher

    Scope = MutableMapping[str, Any]
    Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
    Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]

__all__ = ["asgi_app", "reload_lifespan"]

# Methods whose requests carry no body, so `receive` is never drained for them.
_BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


async def _send_response(send: Send, response: RouteResponse) -> None:
    """Translate a ``RouteResponse`` into the two ASGI response messages."""
    headers = [(b"content-type", response.content_type.encode("latin-1"))]
    headers += [(name.encode("latin-1"), value.encode("latin-1")) for name, value in response.headers]
    await send({"type": "http.response.start", "status": response.status, "headers": headers})
    await send({"type": "http.response.body", "body": response.body})


async def _read_body(receive: Receive) -> bytes | None:
    """Drain the request body from ``receive``; ``None`` when the client disconnected first."""
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return None
        chunks.append(message.get("body", b""))
        if not message.get("more_body"):
            return b"".join(chunks)


def _build_request(scope: Scope, method: str, full_path: str, body: bytes) -> RouteRequest:
    """Read the ASGI scope (plus the already-drained body) into a framework-neutral request."""
    headers = RouteHeaders(
        (name.decode("latin-1"), value.decode("latin-1")) for name, value in scope.get("headers", ())
    )
    query_string: bytes = scope.get("query_string", b"")
    query = {
        key: tuple(values) for key, values in parse_qs(query_string.decode("latin-1"), keep_blank_values=True).items()
    }
    return RouteRequest(
        method=method,
        path=full_path,
        query=query,
        headers=headers,
        body=body,
        content_type=headers.get("content-type", ""),
        native=scope,
    )


def asgi_app(citry_instance: Citry) -> Callable[[Scope, Receive, Send], Awaitable[None]]:
    """
    Build the ASGI application serving ``citry_instance.urls``.

    The returned app handles lifespan events (so it also works served
    standalone), routes each http request to the matched citry handler
    (preferring a route's ``handler_async`` twin when it carries one),
    translates the scope into a ``RouteRequest`` (``_build_request``),
    dispatches it (``call_maybe_sync``: async handlers are awaited, sync
    ones run in a worker thread), and translates the returned
    ``RouteResponse`` into ASGI messages (``_send_response``).
    """

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        # Lifespan support, so the app also works served standalone (uvicorn
        # sends lifespan events to the root app).
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

        if scope["type"] != "http":
            msg = f"citry's ASGI app only handles http scopes, got {scope['type']!r}"
            raise RuntimeError(msg)

        # When mounted, hosts report the prefix as `root_path`, but differ in
        # whether `path` still carries it (e.g. Starlette keeps the full path,
        # others pass the remainder). Normalize into the full request path
        # (for the handler's RouteRequest) and the citry-relative path (for
        # routing), so both shapes behave the same.
        path: str = scope["path"]
        root_path: str = scope.get("root_path", "")
        full_path = path if path.startswith(root_path) else root_path + path
        path = full_path[len(root_path) :].lstrip("/")
        matched = match_route(citry_instance.urls, path)
        if matched is None:
            await _send_response(send, RouteResponse(content="Not Found", status=404))
            return
        method: str = scope["method"]
        if method not in matched.route.methods and method != "HEAD":
            await _send_response(send, RouteResponse(content="Method Not Allowed", status=405))
            return

        if method in _BODYLESS_METHODS:
            body = b""
        else:
            drained = await _read_body(receive)
            if drained is None:
                return  # the client disconnected mid-request; there is nobody to answer
            body = drained
        request = _build_request(scope, method, full_path, body)

        # Prefer the route's async twin when it carries one: this adapter runs
        # an event loop, so the twin is awaited natively, while the plain
        # handler stays what the sync hosts mount.
        route = matched.route
        handler = route.handler_async if route.handler_async is not None else route.handler
        assert handler is not None  # noqa: S101 - match_route only returns handler routes
        # Translate in, dispatch, translate out.
        response = await call_maybe_sync(handler, request, **matched.params)
        await _send_response(send, response)

    return app


def reload_lifespan(
    engine: Citry,
    *,
    roots: Iterable[str | Path] | None = None,
    watcher: FileWatcher | None = None,
    on_reload: Callable[[set[Path], list[type[Component]]], None] | None = None,
) -> Callable[[Any], AbstractAsyncContextManager[None]]:
    """
    A Starlette/FastAPI ``lifespan`` that hot-reloads component files while the
    app runs.

    Compose it into the app's root lifespan::

        from contextlib import asynccontextmanager
        from citry.contrib.asgi import reload_lifespan

        watch_lifespan = reload_lifespan(citry_instance)

        @asynccontextmanager
        async def lifespan(app):
            citry_instance.initialize()
            async with watch_lifespan(app):
                yield

        app = FastAPI(lifespan=lifespan)   # or Starlette(...)

    It starts the :mod:`citry.reload` watcher on startup and stops it on
    shutdown, so editing a component's template/JS/CSS shows up on the next
    render without restarting. It manages only the watcher and does not call
    [`Citry.initialize()`][citry.Citry.initialize]; the root lifespan owns
    initialization. For development; in production simply do not add it. If you
    already have a lifespan, nest this one inside yours. The keyword arguments
    mirror :func:`citry.reload.watch`.
    """

    @asynccontextmanager
    async def lifespan(_app: Any) -> AsyncIterator[None]:
        handle = watch(engine, roots=roots, watcher=watcher, on_reload=on_reload)
        try:
            yield
        finally:
            handle.stop()

    return lifespan
