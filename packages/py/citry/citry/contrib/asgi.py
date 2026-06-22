"""
A generic ASGI sub-application serving a ``Citry`` instance's routes.

Mount it at a prefix in any ASGI framework, then record the prefix on the
instance so URL building works::

    from citry.contrib.asgi import asgi_app

    app.mount("/citry", asgi_app(citry_instance))   # Starlette / FastAPI
    citry_instance.set_mounted_prefix("/citry")

(The ``citry.contrib.fastapi.mount`` convenience does both.) Uses no
third-party packages; only the ASGI 3 protocol.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from citry.util.routing import match_route

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, MutableMapping

    from citry.citry import Citry
    from citry.util.routing import RouteResponse

    Scope = MutableMapping[str, Any]
    Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
    Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]


async def _send_response(send: Send, status: int, content_type: str, body: bytes) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", content_type.encode())],
        }
    )
    await send({"type": "http.response.body", "body": body})


def asgi_app(citry_instance: Citry) -> Callable[[Scope, Receive, Send], Awaitable[None]]:
    """Build the ASGI application serving ``citry_instance.urls``."""

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

        # When mounted, hosts report the prefix as `root_path`; some (e.g.
        # Starlette) keep the full path in `path`, others pass the remainder.
        # Strip the prefix when present, so both shapes route the same.
        path: str = scope["path"]
        root_path: str = scope.get("root_path", "")
        if root_path and path.startswith(root_path):
            path = path[len(root_path) :]
        path = path.lstrip("/")
        matched = match_route(citry_instance.urls, path)
        if matched is None:
            await _send_response(send, 404, "text/plain", b"Not Found")
            return
        if scope["method"] not in matched.route.methods and scope["method"] != "HEAD":
            await _send_response(send, 405, "text/plain", b"Method Not Allowed")
            return

        handler = matched.route.handler
        assert handler is not None  # noqa: S101 - match_route only returns handler routes
        response: RouteResponse = handler(scope, **matched.params)
        await _send_response(send, response.status, response.content_type, response.body)

    return app
