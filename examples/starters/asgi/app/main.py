from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from app.citry_app import citry_app
from app.components.project_page import ProjectPage
from app.data import find_projects
from citry.contrib.asgi import asgi_app

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
PREFIX = "/citry"

citry_routes = asgi_app(citry_app)
citry_app.set_mounted_prefix(PREFIX)


async def _respond(send: Send, status: int, body: bytes, content_type: bytes) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", content_type)],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def application(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                citry_app.initialize()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return

    if scope["type"] != "http":
        raise RuntimeError(f"Unsupported ASGI scope: {scope['type']!r}")

    path = scope.get("path", "")
    if path == PREFIX or path.startswith(PREFIX + "/"):
        mounted_scope = dict(scope)
        mounted_scope["root_path"] = scope.get("root_path", "") + PREFIX
        await citry_routes(mounted_scope, receive, send)
        return

    if path == "/" and scope.get("method") in {"GET", "HEAD"}:
        html = str(ProjectPage(projects=find_projects()))
        body = html.encode()
        if scope.get("method") == "HEAD":
            body = b""
        await _respond(send, 200, body, b"text/html; charset=utf-8")
        return

    await _respond(send, 404, b"Not Found", b"text/plain; charset=utf-8")
