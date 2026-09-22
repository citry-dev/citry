from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


def _pause_fake_clock(page: Any) -> None:
    # Clock calls are separate protocol commands. Choose an explicit future
    # virtual timestamp, then set Date to it before pausing at that timestamp,
    # so the target cannot become stale between the two commands.
    target = page.evaluate("new Date(Date.now() + 1_000).toISOString()")
    page.clock.set_fixed_time(target)
    page.clock.pause_at(target)


@dataclass
class CombinedTimingArgs:
    value: int


@pytest.mark.parametrize(
    ("binding", "steps", "expected"),
    [
        (
            "debounce.20ms.throttle.50ms",
            [(0, 1), (10, 2), (20, 3), (20, 4), (20, None)],
            [1, 4],
        ),
        ("debounce.50ms.throttle.20ms", [(0, 1), (10, 2), (10, 3), (50, None)], [3]),
    ],
)
def test_combined_event_timing_uses_throttle_admission_then_debounce(
    page: Any,
    serve_live: Any,
    binding: str,
    steps: list[tuple[int, int | None]],
    expected: list[int],
) -> None:
    app = Citry(secret="combined-timing-test", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")

    class Timed(Component):
        citry = app

        class Events:
            def record(self, data: CombinedTimingArgs):
                return None

        template = f'<button id="timed" @c-click.{binding}="record({{value: next()}})">go</button>'
        js = "$component({methods:{next(){return ++this.value}}});"

        def js_data(self, kwargs, slots):
            return {"value": 0}

    dispatcher_for(app)
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(app, Timed().render().serialize(), "") + "/")
    _pause_fake_clock(page)
    button = page.locator("#timed")
    for elapsed, value in steps:
        page.clock.run_for(elapsed)
        if value is not None:
            button.click()
    page.wait_for_timeout(20)
    assert [call["calls"][0]["args"]["value"] for call in calls] == expected


def test_combined_control_timing_keeps_rejected_drafts_but_debounces_admitted_changes(
    page: Any, serve_live: Any
) -> None:
    app = Citry(secret="combined-control-test", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")

    class TimedControl(Component):
        citry = app

        class State:
            query: str = ""

        class Events:
            def record(self, state):
                return None

        template = '<input id="timed" :c-query.debounce.50ms.throttle.20ms="record">'

    dispatcher_for(app)
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(app, TimedControl().render().serialize(), "") + "/")
    _pause_fake_clock(page)
    control = page.locator("#timed")
    control.fill("first")
    page.clock.run_for(10)
    control.fill("rejected-draft")
    draft = page.evaluate("[...CitryStable._apps.values().next().value.mounted.values()][0].component.$state.query")
    assert draft == "rejected-draft"
    page.clock.run_for(10)
    control.fill("latest-admitted")
    page.clock.run_for(50)
    page.wait_for_timeout(20)
    assert len(calls) == 1


def test_combined_pending_debounce_survives_an_unchanged_revision(page: Any, serve_live: Any) -> None:
    app = Citry(secret="combined-stable-revision-test", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")

    class StableState:
        revision: int = 0

        def render(self):
            return Stable(revision=self.revision)

    class Stable(Component):
        citry = app
        State = StableState

        class Events:
            def delayed(self):
                return None

            def advance(self, state: StableState):
                state.revision += 1
                return state.render()

        template = (
            '<button id="pending" @c-click.debounce.50ms.throttle.20ms="delayed">pending</button>'
            '<button id="advance" @c-click="advance">advance</button>'
            "<output>{{ revision }}</output>"
        )

        def template_data(self, kwargs, slots):
            return {"revision": kwargs.get("revision", 0)}

    dispatcher_for(app)
    calls: list[str] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json["calls"][0]["handlerName"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(app, Stable().render().serialize(), "") + "/")
    _pause_fake_clock(page)
    page.locator("#pending").click()
    page.clock.run_for(10)
    page.locator("#advance").click()
    page.wait_for_function("CitryStable._apps.values().next().value.revision > 0")
    page.clock.run_for(40)
    page.wait_for_timeout(20)
    assert calls.count("delayed") == 1


def test_combined_replacement_cancels_pending_and_retained_lifetimes(page: Any, serve_live: Any) -> None:
    app = Citry(secret="combined-replacement-test", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")

    class ReplaceState:
        done: bool = False

        def render(self):
            return Replace(done=self.done)

    class Replace(Component):
        citry = app
        State = ReplaceState

        class Events:
            def delayed(self):
                return None

            def replace(self, state: ReplaceState):
                state.done = True
                return state.render()

        template = (
            '<c-if cond="done"><p id="done">done</p></c-if><c-else>'
            '<button id="retained" @c-click.debounce.10ms.throttle.100ms="delayed">retained</button>'
            '<button id="pending" @c-click.debounce.100ms.throttle.20ms="delayed">pending</button>'
            '<button id="replace" @c-click="replace">replace</button></c-else>'
        )

        def template_data(self, kwargs, slots):
            return {"done": kwargs.get("done", False)}

    dispatcher_for(app)
    calls: list[str] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json["calls"][0]["handlerName"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(app, Replace().render().serialize(), "") + "/")
    _pause_fake_clock(page)
    page.locator("#retained").click()
    page.clock.run_for(10)
    page.locator("#pending").click()
    page.locator("#replace").click()
    page.locator("#done").wait_for()
    page.clock.run_for(120)
    page.wait_for_timeout(20)
    assert calls.count("delayed") == 1
    assert page.evaluate(
        "[...CitryStable._apps.values().next().value.mounted.values()]"
        ".every(value => !value.record.eventTimingLifetimes?.size)"
    )
