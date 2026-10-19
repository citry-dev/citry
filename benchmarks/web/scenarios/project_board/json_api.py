"""Serve identical signed-session JSON operations to the React and Vue clients."""

import os
import secrets
from pathlib import Path
from time import perf_counter

from model import ActionInput, apply, reset, snapshot
from render_timing import PreparationTimings, preparation_scope, preparation_span
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp, Message, Receive, Scope, Send

SHELL = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project board benchmark</title><link rel="icon" href="data:,">
<link rel="stylesheet" href="/assets/board.css">
<script type="module" src="/assets/client.js"></script>
</head><body><div id="root"></div></body></html>"""


def browser_snapshot(value: dict) -> dict:
    """Remove the flat compatibility view already carried by phase groups."""
    result = dict(value)
    result.pop("rows")
    return result


class ResponseTiming:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        start = perf_counter()

        async def measured(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                metrics = [f"application;dur={(perf_counter() - start) * 1000:.3f}"]
                if message["status"] < 400 and (prepare_ms := scope.get("bench_prepare_ms")) is not None:
                    metrics.append(f"prepare;dur={prepare_ms:.3f}")
                headers.extend(
                    [
                        (b"cache-control", b"no-store"),
                        (b"server-timing", ", ".join(metrics).encode("ascii")),
                    ]
                )
                if identity := scope.get("bench_identity"):
                    headers.extend(
                        [
                            (b"x-bench-operation", identity[0].encode()),
                            (b"x-bench-revision", str(identity[1]).encode()),
                        ]
                    )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, measured)


def create_application(directory: Path) -> ASGIApp:
    async def index(request: Request) -> Response:
        try:
            session = request.query_params.get("session", "manual")
            reset(session, int(request.query_params.get("count", "14")))
        except ValueError as error:
            return Response(str(error), status_code=400)
        request.session.update(board_session=session, csrf=secrets.token_urlsafe(32))
        return HTMLResponse(SHELL)

    async def initial(request: Request) -> Response:
        session = request.session.get("board_session")
        if not session:
            return Response("Initialize a board session first", status_code=403)
        timing = PreparationTimings()
        with preparation_scope(timing), preparation_span():
            value = snapshot(session)
            response = JSONResponse({"board": browser_snapshot(value), "csrf": request.session["csrf"]})
        request.scope["bench_identity"] = (value["operation"], value["revision"])
        request.scope["bench_prepare_ms"] = timing.duration * 1000
        return response

    async def action(request: Request) -> Response:
        origin = request.headers.get("origin")
        token = request.headers.get("x-csrf-token", "")
        expected = request.session.get("csrf")
        if (
            not token.isascii()
            or not expected
            or not secrets.compare_digest(token, expected)
            or (origin is not None and origin != str(request.base_url).rstrip("/"))
        ):
            return Response("CSRF verification failed", status_code=403)
        try:
            data = await request.json()
            if not isinstance(data, dict) or data.get("session") != request.session.get("board_session"):
                return Response("Board session does not match browser session", status_code=403)
            allowed = {"session", *ActionInput.__dataclass_fields__}
            if set(data) - allowed or any(not isinstance(value, str) for value in data.values()):
                return Response("Action fields must be known text fields", status_code=400)
            session = data.pop("session")
            apply(session, ActionInput(**data))
            timing = PreparationTimings()
            with preparation_scope(timing), preparation_span():
                value = snapshot(session)
                response = JSONResponse({"board": browser_snapshot(value)})
        except (ValueError, KeyError, TypeError) as error:
            return Response(str(error), status_code=400)
        request.scope["bench_identity"] = (value["operation"], value["revision"])
        request.scope["bench_prepare_ms"] = timing.duration * 1000
        return response

    async def asset(request: Request) -> Response:
        name = request.path_params["name"]
        path = Path(__file__).parent / name if name == "board.css" else directory / "generated" / name
        if name not in ("board.css", "client.js") or not path.is_file():
            return Response(status_code=404)
        return Response(path.read_bytes(), media_type="text/css" if name.endswith(".css") else "text/javascript")

    async def health(_request: Request) -> Response:
        return Response(os.environ.get("CITRY_BENCH_SERVER_NONCE", "ok"), media_type="text/plain")

    return ResponseTiming(
        Starlette(
            debug=False,
            routes=[
                Route("/", index),
                Route("/initial", initial),
                Route("/action", action, methods=["POST"]),
                Route("/assets/{name}", asset),
                Route("/health", health),
            ],
            middleware=[
                Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]),
                Middleware(SessionMiddleware, secret_key="project-board-local-benchmark-only"),  # noqa: S106 - synthetic data
            ],
        )
    )
