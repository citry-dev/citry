import mimetypes
import re
from collections.abc import Awaitable, Callable, MutableMapping
from pathlib import Path
from typing import Any

from app.citry_app import citry_app
from app.components.about_page import AboutPage
from app.components.board_page import BoardPage
from app.components.project_page import ProjectPage
from app.data import OWNER, PROJECTS
from citry.contrib.asgi import asgi_app

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
PREFIX = "/citry"
STATIC_DIR = Path(__file__).resolve().parent / "static"
# A project page's URL ends in the project's number, such as /projects/1.
PROJECT_PATH = re.compile(r"/projects/(\d+)")

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


def _render_page(path: str) -> str | None:
    """Render the page that lives at `path`, or return None when there is none."""
    if path == "/":
        return str(BoardPage(owner=OWNER, projects=PROJECTS))
    if path == "/about":
        return str(AboutPage())
    project = PROJECT_PATH.fullmatch(path)
    if project:
        return str(ProjectPage(project_id=int(project.group(1))))
    return None


def _static_file(path: str) -> Path | None:
    """Find the file in app/static that a /static/ URL names, refusing a path that leaves the folder."""
    if not path.startswith("/static/"):
        return None
    file = (STATIC_DIR / path.removeprefix("/static/")).resolve()
    if not file.is_relative_to(STATIC_DIR) or not file.is_file():
        return None
    return file


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

    if scope.get("method") in {"GET", "HEAD"}:
        html = _render_page(path)
        if html is not None:
            body = html.encode()
            if scope.get("method") == "HEAD":
                body = b""
            await _respond(send, 200, body, b"text/html; charset=utf-8")
            return
        # Images and other files the pages link to, such as the owner's avatar.
        static_file = _static_file(path)
        if static_file is not None:
            content_type = mimetypes.guess_type(static_file.name)[0] or "application/octet-stream"
            body = b"" if scope.get("method") == "HEAD" else static_file.read_bytes()
            await _respond(send, 200, body, content_type.encode())
            return

    await _respond(send, 404, b"Not Found", b"text/plain; charset=utf-8")
