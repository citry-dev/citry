"""Render the shared board with Starlette's Jinja templates and native HTMX forms."""

# The captured scenario supplies domain data, not a shared renderer.
# ruff: noqa: E402

import os
import secrets
import sys
from pathlib import Path
from time import perf_counter

from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.applications import Starlette
from starlette.datastructures import MutableHeaders
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

from jinja2 import Template
from model import ActionInput, apply, reset, snapshot
from render_timing import RenderTimingMiddleware, instrument

# Production templates retain Jinja's compiled-code cache without checking file mtimes.
templates = Jinja2Templates(
    env=Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(), auto_reload=False)
)


def view_data(session: str, csrf: str, state: dict | None = None) -> dict:
    if state is None:
        state = snapshot(session)
    for phase in state["phase_groups"]:
        for row in phase["outputs"]:
            row["badge"] = (
                "Missing dependency"
                if any(not dependency["completed"] for dependency in row["dependencies"])
                else "Completed"
                if row["completed"]
                else "In progress"
            )
    return {
        **state,
        "csrf": csrf,
        "action_buttons": (
            ("insert", "Insert output"),
            ("reorder", "Reverse outputs"),
            ("remove", "Remove inserted output"),
            ("probe", "Check server"),
        ),
        "tab_buttons": (
            ("project-info", "Project Info"),
            ("notes-1", "Notes 1"),
            ("notes-2", "Notes 2"),
            ("notes-3", "Notes 3"),
            ("outputs", "Outputs"),
        ),
    }


def index(req: Request) -> Response:
    try:
        session = req.query_params.get("session", "manual")
        reset(session, int(req.query_params.get("count", "14")))
        state = snapshot(session)
    except ValueError as error:
        return Response(str(error), status_code=400)
    req.session["csrf"] = secrets.token_urlsafe(32)
    req.session["board_session"] = session
    req.scope["bench_identity"] = (state["operation"], state["revision"])
    return templates.TemplateResponse(req, "page.html", view_data(session, req.session["csrf"], state))


async def action(req: Request) -> Response:
    data = await req.form()
    token = data.get("csrfmiddlewaretoken", "")
    expected = req.session.get("csrf")
    origin = req.headers.get("origin")
    if (
        not isinstance(token, str)
        or not token.isascii()
        or not expected
        or not secrets.compare_digest(token, expected)
        or (origin is not None and origin != str(req.base_url).rstrip("/"))
    ):
        return Response("CSRF verification failed", status_code=403)
    session = data.get("session")
    if session != req.session.get("board_session"):
        return Response("Board session does not match the browser session", status_code=403)
    values = {key: data.get(key, "") for key in ActionInput.__dataclass_fields__}
    if not all(isinstance(value, str) for value in values.values()):
        return Response("Action fields must be text", status_code=400)
    try:
        apply(session, ActionInput(**values))
        state = snapshot(session)
    except (ValueError, KeyError, TypeError) as error:
        return Response(str(error), status_code=400)
    req.scope["bench_identity"] = (state["operation"], state["revision"])
    return templates.TemplateResponse(req, "board.html", view_data(session, expected, state))


def health(_request: Request) -> Response:
    return Response(os.environ.get("CITRY_BENCH_SERVER_NONCE", "ok"), media_type="text/plain")


def asset(request: Request) -> Response:
    name = request.path_params["name"]
    directory = SCENARIO if name == "board.css" else HERE / "assets"
    path = directory / name
    if path.parent != directory or not path.is_file():
        return Response(status_code=404)
    return Response(path.read_bytes(), media_type="text/css" if name.endswith(".css") else "text/javascript")


class ResponseTiming:
    """Measure Starlette's ASGI work through response start, before body transmission."""

    def __init__(self, application: ASGIApp) -> None:
        self.application = application

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.application(scope, receive, send)
            return
        start = perf_counter()

        async def timed_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers["Server-Timing"] = f"application;dur={(perf_counter() - start) * 1000:.3f}"
                identity = scope.get("bench_identity")
                if identity:
                    headers["X-Bench-Operation"] = identity[0]
                    headers["X-Bench-Revision"] = str(identity[1])
            await send(message)

        await self.application(scope, receive, timed_send)


app = Starlette(
    debug=False,
    routes=[
        Route("/", index, methods=["GET"]),
        Route("/action", action, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
        Route("/assets/{name}", asset, methods=["GET"]),
    ],
    middleware=[
        Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]),
        Middleware(
            SessionMiddleware,
            secret_key="project-board-local-benchmark-only",  # noqa: S106 - isolated synthetic data
        ),
    ],
)
application = ResponseTiming(app)


instrument(Template, "render")

application = RenderTimingMiddleware(application)
