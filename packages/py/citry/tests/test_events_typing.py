"""
Static-typing contract of the ``citry.Events`` generic base.

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

from typing_extensions import assert_type

import citry
from citry import Citry, Component, RouteRequest
from citry import Events as EventsBase
from citry.ext.events import EventsExtension

app = Citry()

assert_type(Component.State, type | None)
assert_type(Component.Events, type | None)


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
