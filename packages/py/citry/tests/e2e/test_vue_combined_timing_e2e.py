from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


@dataclass
class CombinedTimingArgs:
    value: int


@pytest.mark.parametrize(
    ("binding", "steps", "expected"),
    # Each step is (milliseconds to advance, value to click or None). No click
    # and no final step lands exactly on a debounce or throttle deadline,
    # because such a step tests the timer's boundary rule rather than the
    # ordering of throttle and debounce this test is about. In the first case
    # click 1 opens a 50 ms window that clicks 2 and 3 fall inside and click 4
    # (at 55 ms) falls outside; in the second, click 3 (at 25 ms) is admitted
    # after the 20 ms window and its debounce replaces click 1's.
    [
        (
            "debounce.20ms.throttle.50ms",
            [(0, 1), (10, 2), (20, 3), (25, 4), (30, None)],
            [1, 4],
        ),
        ("debounce.50ms.throttle.20ms", [(0, 1), (10, 2), (15, 3), (60, None)], [3]),
    ],
)
def test_combined_event_timing_uses_throttle_admission_then_debounce(
    page: Any,
    serve_live: Any,
    binding: str,
    steps: list[tuple[int, int | None]],
    expected: list[int],
    open_citry_page: Any,
    fake_clock: Any,
    wait_for_count: Any,
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
    # Pause the clock before the page starts its timers, so only the steps
    # below move them, and click only once the app has mounted.
    fake_clock.install_paused()
    open_citry_page(serve_live(app, Timed().render().serialize(), "") + "/")
    button = page.locator("#timed")
    for elapsed, value in steps:
        fake_clock.run_for(elapsed)
        if value is not None:
            button.click()
    # The request event reaches Python a moment after the page sends it.
    wait_for_count(calls, len(expected))
    assert [call["calls"][0]["args"]["value"] for call in calls] == expected


def test_combined_control_timing_keeps_rejected_drafts_but_debounces_admitted_changes(
    page: Any, serve_live: Any, open_citry_page: Any, fake_clock: Any, wait_for_count: Any
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
    # Pause the clock before the page starts its timers, so only the steps
    # below move them, and click only once the app has mounted.
    fake_clock.install_paused()
    open_citry_page(serve_live(app, TimedControl().render().serialize(), "") + "/")
    control = page.locator("#timed")
    control.fill("first")
    fake_clock.run_for(10)
    control.fill("rejected-draft")
    draft = page.evaluate("[...__citryRuntime._apps.values().next().value.mounted.values()][0].component.$state.query")
    assert draft == "rejected-draft"
    # 25 ms in, past the 20 ms throttle window rather than on its edge.
    fake_clock.run_for(15)
    control.fill("latest-admitted")
    # The admitted change's 50 ms debounce ends at 75 ms; step past it.
    fake_clock.run_for(60)
    wait_for_count(calls, 1)
    # The one call carries the admitted value, not the rejected draft.
    assert calls[0]["calls"][0]["stateUpdates"] == {"query": "latest-admitted"}
    # A debounce the admitted change failed to replace would fire in the same
    # step, and its request could reach Python just after the first one.
    page.wait_for_timeout(20)
    assert len(calls) == 1


def test_combined_pending_debounce_survives_an_unchanged_revision(
    page: Any, serve_live: Any, open_citry_page: Any, fake_clock: Any, wait_for_count: Any
) -> None:
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
    # Pause the clock before the page starts its timers, so only the steps
    # below move them, and click only once the app has mounted.
    fake_clock.install_paused()
    open_citry_page(serve_live(app, Stable().render().serialize(), "") + "/")
    page.locator("#pending").click()
    fake_clock.run_for(10)
    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision > 0")
    # The debounce ends at 50 ms; cross it rather than stop on it.
    fake_clock.run_for(50)
    wait_for_count(calls, 2)
    assert calls.count("delayed") == 1


def test_combined_replacement_cancels_pending_and_retained_lifetimes(
    page: Any, serve_live: Any, open_citry_page: Any, fake_clock: Any, wait_for_count: Any
) -> None:
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
    # Pause the clock before the page starts its timers, so only the steps
    # below move them, and click only once the app has mounted.
    fake_clock.install_paused()
    open_citry_page(serve_live(app, Replace().render().serialize(), "") + "/")
    page.locator("#retained").click()
    # Past the 10 ms debounce, so the retained call goes out and leaves only
    # its 100 ms throttle window pending.
    fake_clock.run_for(20)
    page.locator("#pending").click()
    page.locator("#replace").click()
    page.locator("#done").wait_for()
    fake_clock.run_for(120)
    wait_for_count(calls, 2)
    # Checking that the cancelled debounce sent nothing needs a short wait for
    # a request that should not exist; the lifetime check below backs it up.
    page.wait_for_timeout(20)
    assert calls.count("delayed") == 1
    assert page.evaluate(
        "[...__citryRuntime._apps.values().next().value.mounted.values()]"
        ".every(value => !value.record.eventTimingLifetimes?.size)"
    )
