"""Serve the project board with Citry server events."""

# Configure Django before importing views and component routes.
# ruff: noqa: E402

import sys
from pathlib import Path
from typing import Any

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
from django.urls import include, path
from model import ActionInput, apply, reset, snapshot
from render_timing import RenderTimingMiddleware, instrument

from citry import Citry, Component
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender
from citry.contrib.django import urlpatterns as citry_patterns

engine = Citry(secret="project-board-local-benchmark-only")  # noqa: S106 - isolated synthetic data


def render_snapshot(session: str) -> dict[str, Any]:
    state = snapshot(session)
    for phase in state["phase_groups"]:
        phase["anchor"] = f"phase-{phase['id']}"
        for row in phase["outputs"]:
            row["badge"] = (
                "Missing dependency"
                if any(not dependency["completed"] for dependency in row["dependencies"])
                else "Completed"
                if row["completed"]
                else "In progress"
            )
    return state


class RenderContextProvider(Component):
    citry = engine

    class Kwargs:
        context: dict

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:
        self.provide("render_context", state=kwargs.context)
        return {}

    template = "<c-slot />"


class Layout(Component):
    citry = engine

    class Kwargs:
        context: dict

    template_file = "layout.html"


class ProjectLayout(Component):
    citry = engine

    class Kwargs:
        context: dict

    template_file = "project_layout.html"


class ProjectInfo(Component):
    citry = engine

    def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
        return {"state": self.inject("render_context").state}

    template_file = "project_info.html"


class NotePanel(Component):
    citry = engine

    class Kwargs:
        tab: dict

    template_file = "note_panel.html"


class ProjectOutput(Component):
    citry = engine

    class Kwargs:
        row: dict

    def template_data(self, kwargs: Kwargs, slots: Any) -> dict[str, Any]:
        attrs = {
            "id": kwargs.row["element_id"],
            "data-row-id": kwargs.row["id"],
            "data-selected": "true" if kwargs.row["selected"] else "false",
        }
        if kwargs.row["source_id"] is not None:
            attrs["data-source-id"] = kwargs.row["source_id"]
        return {"row": kwargs.row, "row_attrs": attrs}

    template_file = "project_output.html"


class PhaseGroup(Component):
    citry = engine

    class Kwargs:
        phase: dict

    template_file = "phase_group.html"


class ProjectTabs(Component):
    citry = engine

    class Kwargs:
        state: dict

    template_file = "project_tabs.html"


class Board(Component):
    citry = engine

    class Kwargs:
        session: str

    class Slots:
        pass

    class State(Kwargs):
        pass

    class Events:
        def act(self, data: ActionInput, state: Any) -> Any:
            apply(state.session, data)
            return Board(session=state.session)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        state = render_snapshot(kwargs.session)
        return {
            **state,
            "state": state,
            "action_buttons": (
                ("insert", "Insert output"),
                ("reorder", "Reverse outputs"),
                ("remove", "Remove inserted output"),
                ("probe", "Check server"),
            ),
        }

    template_file = "board.html"


class Page(Component):
    citry = engine

    class Kwargs:
        session: str

    class Slots:
        pass

    template_file = "page.html"


def index(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        session = request.GET.get("session", "manual")
        reset(session, int(request.GET.get("count", "14")))
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    get_token(request)
    return HttpResponse(str(Page(session=session)))


urlpatterns = [
    path("", index),
    path("health", health),
    path("assets/<str:name>", asset_view(HERE / "assets", SCENARIO)),
    path("citry/", include(citry_patterns(engine, prefix="/citry"))),
]
engine.initialize()
application = get_asgi_application()


instrument(CitryElement, "render")
instrument(CitryRender, "serialize")
instrument(CitryRender, "serialize_result")

application = RenderTimingMiddleware(application)
