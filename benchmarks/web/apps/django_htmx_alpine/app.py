"""Serve the project board with Django templates, HTMX and Alpine."""

# Configure Django before importing views and component routes.
# ruff: noqa: E402

import sys
from pathlib import Path

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

from django_host import asset_view, configure, health

configure()

from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.middleware.csrf import get_token
from django.template import Context, Engine, Template
from django.urls import path
from model import ActionInput, apply, reset, snapshot
from render_timing import RenderTimingMiddleware, instrument

TEMPLATES = Engine(dirs=[str(HERE)])


def view_data(session: str, csrf: str) -> dict:
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


def render_board(data: dict) -> str:
    return TEMPLATES.get_template("board.html").render(Context(data))


def index(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        session = request.GET.get("session", "manual")
        reset(session, int(request.GET.get("count", "14")))
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    csrf = get_token(request)
    data = view_data(session, csrf)
    return HttpResponse(TEMPLATES.get_template("page.html").render(Context({**data, "board": render_board(data)})))


def action(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        session = request.POST["session"]
        data = ActionInput(
            action=request.POST.get("action", ""),
            operation=request.POST.get("operation", ""),
            row_id=request.POST.get("row_id", "0"),
            query=request.POST.get("query", ""),
            title=request.POST.get("title", ""),
        )
        apply(session, data)
    except (ValueError, KeyError) as exc:
        return HttpResponseBadRequest(str(exc))
    return HttpResponse(render_board(view_data(session, get_token(request))))


urlpatterns = [
    path("", index),
    path("action", action),
    path("health", health),
    path("assets/<str:name>", asset_view(HERE / "assets", SCENARIO)),
]
application = get_asgi_application()


instrument(Template, "render")

application = RenderTimingMiddleware(application)
