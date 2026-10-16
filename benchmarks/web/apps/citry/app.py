"""Serve the project board through Citry's public Vue renderer."""

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
from render_timing import RenderTimingMiddleware, instrument, render_span

from citry import Citry, Component
from citry._vue.events import DirectVueEventsProducer
from citry.citry_element import CitryElement
from citry.citry_render import CitryRender
from citry.contrib.django import urlpatterns as citry_patterns
from citry.ext.events import routes as events_route_module
from citry.ext.events.renderers import dispatcher_for

engine = Citry(
    secret="project-board-local-benchmark-only",  # noqa: S106 - isolated synthetic data
    autodiscover=False,
)


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
    js = "$component({setup(){return {activeTab: Vue.inject('citry-benchmark-active-tab')}}});"


class NotePanel(Component):
    citry = engine

    class Kwargs:
        tab: dict

    class JsData:
        tab_id: str

    def js_data(self, kwargs: Kwargs, slots: Any) -> JsData:
        return self.JsData(tab_id=kwargs.tab["id"])

    template_file = "note_panel.html"
    js = "$component({setup(){return {activeTab: Vue.inject('citry-benchmark-active-tab')}}});"


class ProjectOutput(Component):
    citry = engine
    # Rows repeat 1,400 times and need no Python instance, only their own Vue
    # state, so they use the public instance-free mode.
    simple = "vue"

    class Kwargs:
        row: dict

    @staticmethod
    def template_data(kwargs: Kwargs, slots: Any) -> dict[str, Any]:  # noqa: ARG004 - Citry always passes slots
        attrs = {
            "id": kwargs.row["element_id"],
            "data-row-id": kwargs.row["id"],
            "data-selected": "true" if kwargs.row["selected"] else "false",
        }
        if kwargs.row["source_id"] is not None:
            attrs["data-source-id"] = kwargs.row["source_id"]
        return {"row": kwargs.row, "row_attrs": attrs}

    template_file = "project_output.html"
    js = "$component({data(){return {open: true};}});"


class PhaseGroup(Component):
    citry = engine

    class Kwargs:
        phase: dict

    template_file = "phase_group.html"
    js = "$component({data(){return {open: true};}});"


class ProjectTabs(Component):
    citry = engine

    class Kwargs:
        state: dict

    template_file = "project_tabs.html"
    js = (
        "$component({setup(){const activeTab=Vue.ref('outputs');"
        "Vue.provide('citry-benchmark-active-tab',activeTab);return {activeTab};}});"
    )


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
        # js_data() runs on this same render instance immediately afterward;
        # carry the scalar revision across that lifecycle boundary instead of
        # asking the model for a second full snapshot.
        self._benchmark_revision = state["revision"]
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

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {"server_revision": self._benchmark_revision}

    template_file = "board.html"
    js = """
$component({onServerRender({component, revision}) {
  const lifecycle = globalThis.__citryVueLifecycle ||= {callbacks: [], cleanups: [], effects: []};
  lifecycle.callbacks.push({revision, domRevision: Number(document.querySelector('#board')?.dataset.revision)});
  const stop = Vue.watch(
    () => component.server_revision,
    value => lifecycle.effects.push({revision, value}),
    {immediate: true},
  );
  return () => { stop(); lifecycle.cleanups.push(revision); };
}});
"""


class LocalDisclosure(Component):
    citry = engine
    template = (
        '<aside id="local-disclosure"><button type="button" data-bench-action="disclosure" '
        '@click="open = !open" :aria-expanded="open">Local details</button><p :hidden="!open" '
        'id="disclosure-content">This disclosure needs no server request.</p><label for="preserved-input">'
        'Local draft</label><input id="preserved-input" value="Unchanged draft"></aside>'
    )
    js = "$component({data(){return {open: false};}});"


class Page(Component):
    citry = engine

    class Kwargs:
        session: str

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        return {"session": kwargs.session}

    template_file = "page.html"
    js = """
$component({created(){
  if (globalThis.__citryBenchmarkObserverInstalled) return;
  globalThis.__citryBenchmarkObserverInstalled = true;
  const announce = () => {
    const board = document.querySelector('#board');
    if (!board) throw new Error('Citry Vue Board is missing after render completion');
    globalThis.__citryBench?.ready({
      session: board.dataset.session,
      operation: board.dataset.operation,
      revision: Number(board.dataset.revision),
      pending: 0,
      phase: Number(board.dataset.revision) === 0 ? 'initial' : 'update',
    });
  };
  document.addEventListener('citry:ready', announce);
  document.addEventListener('citry:rendered', announce);
}});
"""


dispatcher_for(engine)

_encode_events_envelope = events_route_module._encode_envelope


def encode_events_envelope_with_timing(envelope: Any) -> tuple[str, Any]:
    with render_span():
        return _encode_events_envelope(envelope)


events_route_module._encode_envelope = encode_events_envelope_with_timing


def index(request: HttpRequest) -> HttpResponse:
    if request.method != "GET":
        return HttpResponse(status=405)
    try:
        session = request.GET.get("session", "manual")
        reset(session, int(request.GET.get("count", "14")))
    except ValueError as exc:
        return HttpResponseBadRequest(str(exc))
    get_token(request)
    with render_span():
        html = Page(session=session).render().serialize()
    return HttpResponse(html)


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
instrument(DirectVueEventsProducer, "prepare_from_render")

application = RenderTimingMiddleware(application)


class DefinitionCacheMiddleware:
    def __init__(self, wrapped: Any) -> None:
        self.wrapped = wrapped

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        async def cache_definitions(message: dict) -> None:
            if message.get("type") != "http.response.start":
                await send(message)
                return
            headers = [
                (key, value.replace(b"render;dur=", b"prepare;dur=") if key.lower() == b"server-timing" else value)
                for key, value in message.get("headers", [])
            ]
            if scope.get("type") == "http" and scope.get("path", "").startswith("/definitions/"):
                headers = [(key, value) for key, value in headers if key.lower() != b"cache-control"]
                headers.append((b"cache-control", b"public, max-age=31536000, immutable"))
            message = {**message, "headers": headers}
            await send(message)

        await self.wrapped(scope, receive, cache_definitions)


application = DefinitionCacheMiddleware(application)
