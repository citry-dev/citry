"""Serve native Django Components through Django, HTMX and Alpine."""

# Django configuration must precede component and view imports.
# ruff: noqa: E402

import mimetypes
import sys
from pathlib import Path
from typing import Any

import django
from django.conf import settings

HERE = Path(__file__).parent
SCENARIO = HERE / "scenario"
if not SCENARIO.is_dir():
    SCENARIO = HERE.parents[1] / "scenarios" / "project_board"
sys.path.insert(0, str(SCENARIO))

settings.configure(
    DEBUG=False,
    BASE_DIR=HERE,
    SECRET_KEY="project-board-local-benchmark-only",  # noqa: S106 - isolated synthetic data
    ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
    ROOT_URLCONF="app",
    MIDDLEWARE=["django_host.ResponseTiming", "django.middleware.csrf.CsrfViewMiddleware"],
    INSTALLED_APPS=["django.contrib.staticfiles", "django_components"],
    STATIC_URL="/static/",
    USE_TZ=True,
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [str(HERE)],
            "APP_DIRS": True,
        }
    ],
    COMPONENTS={"autodiscover": False, "dirs": [HERE]},
)
django.setup()

from django.contrib.staticfiles import finders
from django.core.asgi import get_asgi_application
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.middleware.csrf import get_token
from django.template import Template
from django.urls import include, path
from django_components import Component, register
from django_host import asset_view, health
from model import ActionInput, apply, reset, snapshot
from render_timing import RenderTimingMiddleware, instrument


def render_snapshot(session: str) -> dict[str, Any]:
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
    return state


class NativeComponent(Component):
    """Expose typed component kwargs to native Django component templates."""

    def get_template_data(self, args: Any, kwargs: Any, slots: Any, context: Any) -> dict[str, Any]:
        return {name: getattr(kwargs, name) for name in kwargs.__class__.__annotations__}


@register("project_layout")
class ProjectLayout(NativeComponent):
    class Kwargs:
        state: dict

    template_file = "project_layout.html"


@register("project_info")
class ProjectInfo(NativeComponent):
    class Kwargs:
        state: dict

    template_file = "project_info.html"


@register("note_panel")
class NotePanel(NativeComponent):
    class Kwargs:
        tab: dict

    template_file = "note_panel.html"


@register("project_output")
class ProjectOutput(NativeComponent):
    class Kwargs:
        state: dict
        row: dict
        csrf: str

    template_file = "project_output.html"


@register("phase_group")
class PhaseGroup(NativeComponent):
    class Kwargs:
        state: dict
        phase: dict
        csrf: str

    template_file = "phase_group.html"


@register("project_tabs")
class ProjectTabs(NativeComponent):
    class Kwargs:
        state: dict
        csrf: str

    template_file = "project_tabs.html"


@register("board")
class Board(Component):
    class Kwargs:
        session: str
        csrf: str

    template_file = "board.html"

    def get_template_data(self, args: Any, kwargs: Kwargs, slots: Any, context: Any) -> dict[str, Any]:
        state = render_snapshot(kwargs.session)
        return {
            **state,
            "state": state,
            "csrf": kwargs.csrf,
            "action_buttons": (
                ("insert", "Insert output"),
                ("reorder", "Reverse outputs"),
                ("remove", "Remove inserted output"),
                ("probe", "Check server"),
            ),
        }


class Page(Component):
    class Kwargs:
        session: str
        csrf: str

    template_file = "page.html"

    def get_template_data(self, args: Any, kwargs: Kwargs, slots: Any, context: Any) -> dict[str, str]:
        return {"session": kwargs.session, "csrf": kwargs.csrf}


def index(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        session = request.GET.get("session", "manual")
        reset(session, int(request.GET.get("count", "14")))
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    return Page.render_to_response(
        kwargs={"session": session, "csrf": get_token(request)}, request=request, deps_strategy="document"
    )


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
    # The framework emits its normal fragment metadata and dependency loader.
    return Board.render_to_response(
        kwargs={"session": session, "csrf": get_token(request)}, request=request, deps_strategy="fragment"
    )


def component_asset(_request: HttpRequest, name: str) -> HttpResponse:
    # Resolve only the installed component package's static namespace. The shared
    # response middleware keeps these identity-encoded assets uncached.
    if ".." in Path(name).parts or Path(name).is_absolute() or not name.startswith("django_components/"):
        return HttpResponse(status=404)
    found = finders.find(name)
    if not found or not Path(found).is_file():
        return HttpResponse(status=404)
    return HttpResponse(
        Path(found).read_bytes(), content_type=mimetypes.guess_type(name)[0] or "application/octet-stream"
    )


urlpatterns = [
    path("", index),
    path("action", action),
    path("health", health),
    path("assets/<str:name>", asset_view(HERE / "assets", SCENARIO)),
    path("static/<path:name>", component_asset),
    path("", include("django_components.urls")),
]
application = get_asgi_application()


instrument(Template, "render")

instrument(Component, "render")

application = RenderTimingMiddleware(application)
