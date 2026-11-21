"""
Tests for ``CitryRender.has_server_events()``.

The method answers before serialization, so each test compares its
answer with what serialization then writes: whether any occurrence in the
Vue manifest carries an ``eventContext``, the record the browser uses to
call a component's event handlers. A host that trusted a wrong ``False``
would skip the CSRF cookie and every event call would fail, so the cases
cover each way an Events component can reach the page.
"""

import json
import re

import pytest

from citry import Citry, CitryRender, Component, InMemoryCache
from citry._vue import events as vue_events
from citry.ext.events import actions
from citry.ext.events.dispatcher import EventsDispatcher, TransportContext

_SIGNING_KEY = "test-secret-key"
_DATA_BLOCK = re.compile(
    r'<script type="application/json" data-citry-vue-(document|fragment)\b[^>]*>(.*?)</script>', re.DOTALL
)


# The Events records each serialization prepared, newest last.
_prepared_entries: list[list[object]] = []


@pytest.fixture(autouse=True)
def _record_prepared_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Record the Events records preparation selects for the manifest."""
    real = vue_events.build_events_manifest
    _prepared_entries.clear()

    def recording(extension, citry, entries):  # type: ignore[no-untyped-def]
        # These are the records that get an eventContext, so the test can
        # compare the answer with preparation's own selection too.
        _prepared_entries.append(list(entries))
        return real(extension, citry, entries)

    monkeypatch.setattr(vue_events, "build_events_manifest", recording)


def _engine(**settings: object) -> Citry:
    engine = Citry(autodiscover=False, secret=_SIGNING_KEY, **settings)  # type: ignore[arg-type]
    # Events need mounted routes to give the browser an endpoint.
    engine.set_mounted_prefix("/citry")
    return engine


def _manifests(html: str) -> list[dict[str, object]]:
    """Return the Vue manifest of every app or fragment data block in the HTML."""
    found = []
    for kind, body in _DATA_BLOCK.findall(html):
        data = json.loads(body)
        found.append(data["manifest"] if kind == "document" else data["vue"]["prepared"]["manifest"])
    return found


def _serialized_events(html: str) -> bool:
    """Whether the serialized HTML gives the browser any Events occurrence."""
    return any(
        "eventContext" in occurrence
        for manifest in _manifests(html)
        for occurrence in manifest["occurrences"]  # type: ignore[attr-defined]
    )


def _assert_agrees(rendered: CitryRender, *, expected: bool) -> None:
    """Check the answer before serialization against both serialize strategies."""
    answer = rendered.has_server_events()
    assert answer is expected
    for strategy in ("document", "fragment"):
        html = rendered.serialize(deps_strategy=strategy)
        # A "no" is only evidence when a Vue manifest was written to check.
        assert _manifests(html) if rendered.needs_browser_runtime() else not _manifests(html)
        assert _serialized_events(html) is expected
        if rendered.needs_browser_runtime():
            # Preparation picked Events records exactly when the answer was yes.
            assert bool(_prepared_entries[-1]) is expected
    # Asking does not change the render, so the answer stays the same.
    assert rendered.has_server_events() is answer


def _components(engine: Citry) -> dict[str, type[Component]]:
    """An Events component, interactive ones without Events, and a static one."""

    class Counter(Component):
        citry = engine

        class State:
            count: int = 0

        class Events:
            def inc(self, state):  # type: ignore[no-untyped-def]
                state.count += 1

        template = """
<button @c-click="inc">+</button>
"""

    class Quiet(Component):
        # Events without handlers still give the browser an event record.
        citry = engine

        class Events:
            pass

        template = """
<p>quiet</p>
"""

    class Slider(Component):
        # Browser behavior without server events.
        citry = engine

        def js_data(self, kwargs, slots):  # type: ignore[no-untyped-def]
            return {"value": 3}

        template = """
<input :value="value" @input="value = $event.target.value">
"""

    class Badge(Component):
        citry = engine
        template = """
<span class="badge">static</span>
"""

    class Card(Component):
        citry = engine
        template = """
<section><c-slot /></section>
"""

    return {"Counter": Counter, "Quiet": Quiet, "Slider": Slider, "Badge": Badge, "Card": Card}


def test_a_render_without_events_says_no() -> None:
    engine = _engine()
    comps = _components(engine)

    class Page(Component):
        citry = engine
        template = """
<main><c-Slider /><c-Badge /></main>
"""

    rendered = Page().render()
    # It still needs the runtime, so the answer is about events alone.
    assert rendered.needs_browser_runtime()
    _assert_agrees(rendered, expected=False)
    _assert_agrees(comps["Badge"]().render(), expected=False)


@pytest.mark.parametrize("name", ["Counter", "Quiet"])
def test_an_events_component_says_yes(name: str) -> None:
    comps = _components(_engine())
    _assert_agrees(comps[name]().render(), expected=True)


def test_a_nested_events_component_says_yes() -> None:
    engine = _engine()
    _components(engine)

    class Section(Component):
        citry = engine
        template = """
<div><c-Badge /><c-Counter /></div>
"""

    class Page(Component):
        citry = engine
        template = """
<main><c-Section /><c-Slider /></main>
"""

    _assert_agrees(Page().render(), expected=True)


def test_an_events_component_in_a_slot_says_yes() -> None:
    engine = _engine()
    _components(engine)

    class Page(Component):
        citry = engine
        template = """
<main><c-Card><c-Counter /></c-Card></main>
"""

    _assert_agrees(Page().render(), expected=True)


def test_an_events_component_called_by_a_simple_vue_component_says_yes() -> None:
    engine = _engine()
    _components(engine)

    class Row(Component):
        # A simple='vue' component renders as a record, not a frame, so
        # the Counter it calls is reached only through that record.
        citry = engine
        simple = "vue"
        template = """
<li><c-Counter /></li>
"""

    class Page(Component):
        citry = engine
        template = """
<ul><c-Row /><c-Slider /></ul>
"""

    _assert_agrees(Page().render(), expected=True)


def test_an_events_component_not_rendered_says_no() -> None:
    engine = _engine()
    _components(engine)

    class Page(Component):
        citry = engine

        class Kwargs:
            show: bool = False

        template = """
<main><c-if cond="show"><c-Counter /></c-if><c-Slider /></main>
"""

    _assert_agrees(Page().render(), expected=False)
    _assert_agrees(Page(show=True).render(), expected=True)


def test_a_record_outside_the_render_does_not_count() -> None:
    engine = _engine()
    _components(engine)

    class Page(Component):
        citry = engine
        template = """
<main><c-Counter /><c-Card><c-Slider /></c-Card></main>
"""

    rendered = Page().render()
    card = next(
        part
        for part in rendered.parts
        if isinstance(part, CitryRender) and type(part.context.component).__name__ == "Card"
    )
    # The Card's render can see the Counter's Events record, which belongs
    # to its sibling, so only the records of its own tree may count.
    assert card.context.extra.get("events")
    assert not card.has_server_events()
    _assert_agrees(rendered, expected=True)


def test_each_island_answers_for_its_own_tree() -> None:
    engine = _engine()
    _components(engine)

    class Page(Component):
        citry = engine
        template = """
<main><c-Counter /><c-Slider /><c-Badge /></main>
"""

    rendered = Page().render()
    children = [part for part in rendered.parts if isinstance(part, CitryRender) and part.is_component_root]
    assert [child.has_server_events() for child in children] == [True, False, False]
    # Each interactive child serialized on its own, as a host does for
    # islands, writes event records exactly when it said so.
    for child in children:
        if child.needs_browser_runtime():
            result = child.serialize_result(deps_position="separate")
            # The configuration data block is one of the app's own tags.
            html = "".join((result.html, *result.app_assets.js))
            assert _serialized_events(html) is child.has_server_events()
    # The parent still holds the Events child.
    _assert_agrees(rendered, expected=True)


def test_a_cached_replay_gives_the_same_answer() -> None:
    engine = _engine(cache=InMemoryCache())
    _components(engine)
    calls: list[str] = []

    class Shell(Component):
        citry = engine

        class Kwargs:
            events: bool

        class Cache:
            enabled = True

        def template_data(self, kwargs, slots):  # type: ignore[no-untyped-def]
            calls.append("data")
            return {"events": kwargs.events}

        template = """
<div><c-if cond="events"><c-Counter /></c-if><c-else><c-Slider /></c-else></div>
"""

    for events in (True, False):
        calls.clear()
        first = Shell(events=events).render()
        replayed = Shell(events=events).render()
        # The second render came from the cache.
        assert calls == ["data"]
        _assert_agrees(first, expected=events)
        _assert_agrees(replayed, expected=events)


class SwapIn:
    events: bool


def test_a_render_action_answers_for_the_fragment_it_sends() -> None:
    engine = _engine()
    comps = _components(engine)
    answers: list[bool] = []

    class Panel(Component):
        citry = engine
        template = """
<div><c-Counter /></div>
"""

    class Host(Component):
        citry = engine

        class Events:
            def swap(self, data: SwapIn):  # type: ignore[no-untyped-def]
                # A Render built in a handler is serialized as a fragment.
                rendered = Panel().render() if data.events else comps["Slider"]().render()
                answers.append(rendered.has_server_events())
                return actions.Render(rendered)

        template = """
<button @c-click="swap">swap</button>
"""

    for events in (True, False):
        answers.clear()
        envelope = {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [
                {
                    "componentClassId": Host.class_id,
                    "handlerName": "swap",
                    "callerRenderId": "c9zk1q00",
                    "args": {"events": events},
                    "sendSequence": 1,
                }
            ],
        }
        result = EventsDispatcher().dispatch(envelope, TransportContext(transport="http", citry=engine))
        [item] = result["results"]
        assert item["ok"] is True, item
        [action] = item["actions"]
        assert answers == [events]
        assert _serialized_events(action["html"]) is events
