"""
Static-typing contract of the built-in extension attributes on ``Component``
and of the ``citry.Events`` generic base.

The ``assert_type`` calls are the static half of the contract: they must stay
green under both mypy and pyright. The check gate runs both over this file:
scripts/check.py targets it in the mypy phase and in a dedicated pyright phase
(the pinned ``node_modules/.bin/pyright``, so ``npm ci`` must have run). To
re-check just this file by hand when the typing base changes, from the repo
root:

    .venv/bin/python -m mypy <this file>
    node_modules/.bin/pyright --pythonversion 3.13 --pythonpath .venv/bin/python <this file>

pytest runs the runtime half, proving that the woven config class subclasses
the base, so subclassing it in user code changes nothing at runtime. The
verified spelling matrix behind this design is
``docs/design/events_research/typing-lab-report.md``.
"""

from __future__ import annotations

from typing import Any

from typing_extensions import assert_type

import citry
from citry import CacheConfig, Citry, CitryElement, Component, DependenciesConfig, I18n, RouteRequest
from citry import Events as EventsBase
from citry.ext.events import EventRequest, EventsExtension, RenderInputs

app = Citry()

assert_type(Component.State, type | None)
assert_type(Component.Cache, type | None)
assert_type(Component.Dependencies, type | None)
assert_type(Component.Events, type | None)
assert_type(Component.I18n, type | None)


def _assert_component_extension_types(component: Component) -> None:
    assert_type(component.cache, CacheConfig)
    assert_type(component.dependencies, DependenciesConfig)
    assert_type(component.events, EventsBase[Any])
    assert_type(component.i18n, I18n)
    # The URL builder is declared on the base, so user code calling it from
    # template_data type-checks without an ignore comment.
    assert_type(component.events.url("search", query={"q": "milk"}, fragment="top"), str)


class TodoState:
    project_id: int
    query: str = ""


class TodoList(Component):
    citry = app

    State = TodoState

    class Events(EventsBase[TodoState]):
        def search(self) -> None:
            # The subscripted base types the ambient members.
            assert_type(self.state, TodoState)
            assert_type(self.state.query, str)
            assert_type(self.request, RouteRequest)
            # Typed mutation of state fields works.
            self.state.query = "updated"


class Plain(Component):
    citry = app

    class Events(EventsBase):
        def ping(self) -> None:
            # The bare base defaults the state type to None (stateless
            # handlers carry no state), so a stray attribute access is a
            # checker error instead of silent Any.
            assert_type(self.state, None)


def _profile_inputs(request: EventRequest) -> RenderInputs:
    # A dict literal is checked against RenderInputs: an unknown key or a
    # non-mapping value is a checker error.
    return {"template_globals": {"method": request.method}, "provides": {"locale": "en-GB"}}


class Profile(Component):
    citry = app

    class Events(EventsBase):
        # Checked against `Callable[[EventRequest], RenderInputs] | None`:
        # pyright checks the whole signature, mypy the return type and the
        # number of parameters.
        _render_inputs = _profile_inputs

        def ping(self) -> None:
            return None


class Unconfigured(Component):
    citry = app

    class Events(EventsBase):
        # None turns off an engine-wide default for this component.
        _render_inputs = None

        def ping(self) -> None:
            return None


def _pass_render_inputs_on(inputs: RenderInputs, element: CitryElement) -> None:
    # The keys are render()'s keyword arguments with the same types, so the
    # dict unpacks straight into the call.
    element.render(**inputs)


def test_the_typing_base_is_the_root_export() -> None:
    assert citry.Events is EventsBase


def test_subclassing_the_base_changes_nothing_at_runtime() -> None:
    # The weaving rebuilds every component's Events on the base either way,
    # so the typed spelling and the bare spelling enumerate identically.
    assert issubclass(TodoList.Events, citry.Events)
    assert issubclass(Plain.Events, citry.Events)
    ext = app.extensions.get_extension("events")
    assert isinstance(ext, EventsExtension)
    assert list(ext.resolve(TodoList).handlers) == ["search"]
    assert list(ext.resolve(Plain).handlers) == ["ping"]


def test_ambient_members_exist_only_as_declarations() -> None:
    instance = TodoList.Events(None)
    assert isinstance(instance, citry.Events)


def test_a_component_render_inputs_function_is_the_configured_one() -> None:
    ext = app.extensions.get_extension("events")
    assert isinstance(ext, EventsExtension)
    assert ext.resolve(Profile).render_inputs is _profile_inputs
    assert ext.resolve(Unconfigured).render_inputs is None
