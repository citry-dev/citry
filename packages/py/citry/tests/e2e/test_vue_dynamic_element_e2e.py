from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from citry import Citry, Component
from citry.browser_render import BrowserPluginDescriptor, BrowserRenderContribution
from citry.ext.dependencies.types import Script, Style
from citry.ext.events.renderers import dispatcher_for
from citry.extension import Extension

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


def _client_bundle_source(vue_root: Path) -> str:
    fragments_source = (vue_root / "fragments.js").read_text(encoding="utf-8")
    client_source = (vue_root / "client.js").read_text(encoding="utf-8")
    return f"{fragments_source}\n{client_source}"


def test_native_polling_uses_live_element_scope_visibility_and_revision_lifecycle(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="native-poll-lifecycle-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Poller(Component):
        citry = engine

        @dataclass
        class PollArgs:
            value: int

        def js_data(self, kwargs, slots):
            return {"items": [1, 2], "show": True}

        class Events:
            def poll(self, data: Poller.PollArgs):
                return None

            def refresh(self):
                return Poller()

        template = (
            '<main><section v-if="show"><output class="poller" v-for="item in items" '
            '@c-poll.1s="poll({value:item})" v-text="item"></output></section>'
            '<button id="poll-refresh" @c-click="refresh">refresh</button></main>'
        )

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )

    def sent_calls() -> list[dict[str, Any]]:
        return [call for request in calls for call in request["calls"]]

    page.add_init_script(
        """globalThis.__citryDocumentHidden=false;
        Object.defineProperty(document,'hidden',{configurable:true,get:()=>globalThis.__citryDocumentHidden});"""
    )
    held_poll_routes: list[Any] = []
    poll_route_pattern = re.compile(r"/ext/events/call$")

    def wait_for_held_routes(count: int) -> None:
        deadline = time.monotonic() + 5
        while len(held_poll_routes) < count and time.monotonic() < deadline:
            page.wait_for_timeout(10)
        assert len(held_poll_routes) == count

    page.route(
        poll_route_pattern,
        lambda route: held_poll_routes.append(route)
        if route.request.post_data_json["calls"][0]["handlerName"] == "poll"
        else route.continue_(),
    )
    page.clock.install()
    page.goto(serve_live(engine, Poller().render().serialize(), "") + "/")

    page.clock.run_for(3_000)
    wait_for_held_routes(1)
    first_values = [call["args"]["value"] for call in held_poll_routes[0].request.post_data_json["calls"]]
    if len(first_values) == 1:
        with page.expect_request(poll_route_pattern):
            held_poll_routes[0].continue_()
        wait_for_held_routes(2)
    assert sorted(
        call["args"]["value"] for route in held_poll_routes for call in route.request.post_data_json["calls"]
    ) == [1, 2]
    for route in held_poll_routes:
        if route is not held_poll_routes[0] or len(first_values) != 1:
            route.continue_()
    page.unroute(poll_route_pattern)
    page.wait_for_function(
        "[...CitryStable._apps.values().next().value.mounted.values()].every("
        "({component}) => !component.$loading('poll'))"
    )

    calls.clear()
    page.evaluate("globalThis.__citryDocumentHidden=true;document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.run_for(5_000)
    assert calls == []
    page.evaluate("globalThis.__citryDocumentHidden=false;document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.run_for(999)
    assert calls == []
    page.clock.run_for(1)
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return !app.mounted.get(app.rootId).component.$loading('poll'); }"
    )
    assert sorted(call["args"]["value"] for call in sent_calls()) == [1, 2]

    calls.clear()
    page.clock.run_for(500)
    page.locator("#poll-refresh").click()
    page.wait_for_function("CitryStable._apps.values().next().value.revision > 0")
    page.clock.run_for(499)
    assert [call["handlerName"] for call in sent_calls()] == ["refresh"]
    page.clock.run_for(1)
    assert [call["handlerName"] for call in sent_calls()].count("refresh") == 1
    assert [call for call in sent_calls() if call["handlerName"] == "poll"] == []
    page.clock.run_for(499)
    assert [call for call in sent_calls() if call["handlerName"] == "poll"] == []
    with page.expect_request(poll_route_pattern):
        page.clock.run_for(1)
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return !app.mounted.get(app.rootId).component.$loading('poll'); }"
    )
    assert sorted(call["args"]["value"] for call in sent_calls() if call["handlerName"] == "poll") == [1, 2]

    page.clock.pause_at(page.evaluate("new Date().toISOString()"))
    page.wait_for_function(
        "() => [...CitryStable._apps.values().next().value.mounted.values()].every("
        "({component}) => !component.$loading('poll'))"
    )
    calls.clear()
    page.evaluate("CitryStable._apps.values().next().value.mounted.values().next().value.component.show=false")
    page.locator(".poller").first.wait_for(state="detached")
    assert (
        page.evaluate(
            """() => {
              const app=CitryStable._apps.values().next().value;
              const record=app.mounted.values().next().value.record;
              return record.eventTimingLifetimes?.size || 0;
            }"""
        )
        == 0
    )
    assert page.evaluate("CitryStable._apps.values().next().value.polling?.lifetimes.size || 0") == 0
    page.clock.run_for(2_000)
    assert calls == []
    assert faults == []


def test_native_poll_rechecks_lifetime_after_argument_side_effects(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="native-poll-argument-lifetime-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Poller(Component):
        citry = engine

        def js_data(self, kwargs, slots):
            return {"show": True}

        class Events:
            def poll(self):
                return None

        template = '<output v-if="show" @c-poll.1s="poll((show=false,{}))">waiting</output>'

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(engine, Poller().render().serialize(), "") + "/")
    page.clock.run_for(1_000)
    page.locator("output").wait_for(state="detached")
    page.clock.run_for(2_000)
    assert calls == []
    assert faults == []
    assert page.evaluate("!CitryStable._apps.values().next().value.terminal")


def test_native_polling_argument_failure_uses_vue_terminal_boundary(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="native-poll-error-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class BrokenPoll(Component):
        citry = engine

        class Events:
            def poll(self):
                return None

        template = '<output @c-poll.1s="poll(42)">waiting</output>'

    dispatcher_for(engine)
    faults: list[str] = []
    calls: list[dict[str, Any]] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(engine, BrokenPoll().render().serialize(), "") + "/")
    page.clock.run_for(1_000)
    page.wait_for_function("globalThis.CitryStable._apps.values().next().value.terminal === true")
    assert faults == ["Citry polling arguments must be a plain object"]
    page.clock.run_for(5_000)
    assert faults == ["Citry polling arguments must be a plain object"]
    assert calls == []


def test_native_runtime_poll_keeps_deadline_across_reordered_revision_and_visibility(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="runtime-poll-revision-lifetime-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PollState:
        revision: int = 0

        def render(self):
            return RuntimePoll(revision=self.revision)

    class RuntimePoll(Component):
        citry = engine
        State = PollState
        template = """
            <main>
                <button id="advance-poll" @c-click="advance">advance</button>
                <button id="runtime-poller" @c-click="authored" c-bind="attrs">poll</button>
                <output id="poll-revision">{{ revision }}</output>
            </main>
        """

        class Events:
            def advance(self, state: PollState):
                state.revision += 1
                return state.render()

            def poll(self):
                return None

            def key_first(self):
                return None

            def key_second(self):
                return None

            def authored(self):
                return None

        def template_data(self, kwargs, slots):
            revision = kwargs.get("revision", 0)
            attrs = (
                {"@c-poll.1s": "poll", "@c-keydown": "key_first"}
                if revision == 0
                else {"@c-keydown": "key_second", "@c-poll.1s": "poll"}
            )
            return {"attrs": attrs, "revision": revision}

    dispatcher_for(engine)
    event_url = re.compile(r"/ext/events/call$")
    held_polls: list[Any] = []
    request_batches: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: request_batches.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )

    def route_poll(route: Any) -> None:
        request = route.request.post_data_json
        if any(call["handlerName"] == "poll" for call in request["calls"]):
            held_polls.append(route)
        else:
            route.continue_()

    def wait_for_held_polls(count: int) -> None:
        deadline = time.monotonic() + 5
        while len(held_polls) < count and time.monotonic() < deadline:
            page.wait_for_timeout(10)
        assert len(held_polls) == count

    def calls_for(handler: str) -> list[dict[str, Any]]:
        return [call for batch in request_batches for call in batch["calls"] if call["handlerName"] == handler]

    page.add_init_script(
        """globalThis.__citryDocumentHidden=false;
        Object.defineProperty(document,'hidden',{configurable:true,get:()=>globalThis.__citryDocumentHidden});"""
    )
    page.route(event_url, route_poll)
    page.clock.install()
    page.goto(serve_live(engine, RuntimePoll(revision=0).render().serialize(), "") + "/")
    page.locator("#runtime-poller").wait_for()
    page.clock.pause_at(page.evaluate("new Date().toISOString()"))

    page.clock.run_for(1_000)
    wait_for_held_polls(1)
    assert held_polls[0].request.post_data_json["calls"][0]["handlerName"] == "poll"

    # The next deadline passes while this request is unresolved, but no second poll may start.
    page.clock.run_for(2_000)
    page.wait_for_timeout(30)
    assert len(held_polls) == 1
    assert len(calls_for("poll")) == 1

    held_polls[0].continue_()
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return [...app.mounted.values()].every(({component}) => !component.$loading('poll')); }"
    )
    page.clock.run_for(500)
    with page.expect_request(event_url) as revision_request:
        page.locator("#advance-poll").click()
    assert revision_request.value.post_data_json["calls"][0]["handlerName"] == "advance"
    page.wait_for_function("document.querySelector('#poll-revision')?.textContent === '1'")

    with page.expect_request(event_url) as key_request:
        page.locator("#runtime-poller").press("ArrowRight")
    assert key_request.value.post_data_json["calls"][0]["handlerName"] == "key_second"
    with page.expect_request(event_url) as authored_request:
        page.locator("#runtime-poller").click()
    assert authored_request.value.post_data_json["calls"][0]["handlerName"] == "authored"

    assert len(calls_for("poll")) == 1
    page.clock.run_for(499)
    assert len(calls_for("poll")) == 1
    page.clock.run_for(1)
    wait_for_held_polls(2)
    assert len(calls_for("poll")) == 2
    held_polls[1].continue_()
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return [...app.mounted.values()].every(({component}) => !component.$loading('poll')); }"
    )

    page.evaluate("globalThis.__citryDocumentHidden=true;document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.run_for(2_000)
    assert len(calls_for("poll")) == 2
    page.evaluate("globalThis.__citryDocumentHidden=false;document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.run_for(999)
    assert len(calls_for("poll")) == 2
    page.clock.run_for(1)
    wait_for_held_polls(3)
    assert len(calls_for("poll")) == 3
    held_polls[2].continue_()
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return [...app.mounted.values()].every(({component}) => !component.$loading('poll')); }"
    )
    page.unroute(event_url)

    assert [call["handlerName"] for call in calls_for("advance")] == ["advance"]
    assert [call["handlerName"] for call in calls_for("key_second")] == ["key_second"]
    assert [call["handlerName"] for call in calls_for("authored")] == ["authored"]
    assert faults == []


def test_native_runtime_poll_loop_elements_keep_independent_lifetimes(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="runtime-poll-loop-lifetimes-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PollState:
        rows: list[str]

        def __init__(self):
            self.rows = ["a", "b"]

        def render(self):
            return PollRows(rows=self.rows)

    class PollRows(Component):
        citry = engine
        State = PollState
        template = """
            <main>
                <button id="remove-first-poller" @c-click="remove_first">remove first</button>
                <output class="row-poller" c-for="attrs in poll_attrs" c-bind="attrs"></output>
            </main>
        """

        class Events:
            def poll(self):
                return None

            def remove_first(self, state: PollState):
                state.rows = state.rows[1:]
                return state.render()

        def template_data(self, kwargs, slots):
            rows = kwargs.get("rows", ["a", "b"])
            return {"poll_attrs": [{"data-row": row, "@c-poll.1s": "poll"} for row in rows]}

    dispatcher_for(engine)
    event_url = re.compile(r"/ext/events/call$")
    poll_routes: list[Any] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))

    def route_poll(route: Any) -> None:
        request = route.request.post_data_json
        if any(call["handlerName"] == "poll" for call in request["calls"]):
            poll_routes.append(route)
        else:
            route.continue_()

    def wait_for_poll_routes(count: int) -> None:
        deadline = time.monotonic() + 5
        while len(poll_routes) < count and time.monotonic() < deadline:
            page.wait_for_timeout(10)
        page.wait_for_timeout(30)
        assert len(poll_routes) == count

    def poll_lifetime_snapshot() -> dict[str, Any]:
        return page.evaluate(
            """() => {
              const app=CitryStable._apps.values().next().value;
              return {revision:app.revision,hidden:document.hidden,
                pollingLifetimeCount:app.polling?.lifetimes.size || 0,
                mounted:[...app.mounted.values()].map(({record})=>({
                occurrenceId:record.occurrenceId,generation:record.generation,
                pollBindings:Object.entries(record.live.value?.preparedData?.pollBindings || {}).map(([id,binding])=>
                  ({id,handler:binding.handler,interval:binding.interval})),
                lifetimes:[...(record.eventTimingLifetimes || [])].map(lifetime=>({
                  bindingId:lifetime.bindingId,kind:lifetime.kind,handler:lifetime.binding?.handler,
                  interval:lifetime.binding?.interval,timer:Boolean(lifetime.timer),inFlight:lifetime.inFlight,
                  current:record.live.value?.preparedData?.pollBindings?.[lifetime.bindingId]===lifetime.binding}))
              }))};
            }"""
        )

    def event_lifetime_count(snapshot: dict[str, Any]) -> int:
        return sum(len(mounted["lifetimes"]) for mounted in snapshot["mounted"])

    page.route(event_url, route_poll)
    page.clock.install()
    page.goto(serve_live(engine, PollRows(rows=["a", "b"]).render().serialize(), "") + "/")
    page.wait_for_function(
        "() => [...document.querySelectorAll('.row-poller')].map(node => node.dataset.row).join(',') === 'a,b'"
    )
    page.clock.pause_at(page.evaluate("new Date().toISOString()"))

    page.clock.run_for(1_000)
    wait_for_poll_routes(1)
    first_poll = poll_routes[0].request.post_data_json["calls"][0]
    assert first_poll["handlerName"] == "poll"
    page.wait_for_timeout(30)
    assert len(poll_routes) == 1

    with page.expect_request(event_url) as second_poll_request:
        poll_routes[0].continue_()
    assert second_poll_request.value.post_data_json["calls"][0]["handlerName"] == "poll"
    wait_for_poll_routes(2)
    second_poll = poll_routes[1].request.post_data_json["calls"][0]
    assert second_poll["handlerName"] == "poll"
    assert first_poll["callerRenderId"] == second_poll["callerRenderId"]
    poll_routes[1].continue_()
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return [...app.mounted.values()].every(({component}) => !component.$loading('poll')); }"
    )
    completed_initial_polls = poll_lifetime_snapshot()
    assert completed_initial_polls["pollingLifetimeCount"] == 2
    assert event_lifetime_count(completed_initial_polls) == 2
    assert all(
        lifetime["current"] for mounted in completed_initial_polls["mounted"] for lifetime in mounted["lifetimes"]
    )

    with page.expect_request(event_url) as removal_request:
        page.locator("#remove-first-poller").click()
    assert removal_request.value.post_data_json["calls"][0]["handlerName"] == "remove_first"
    page.wait_for_function(
        "() => [...document.querySelectorAll('.row-poller')].map(node => node.dataset.row).join(',') === 'b'"
    )
    after_remove = poll_lifetime_snapshot()
    assert after_remove["pollingLifetimeCount"] == 1
    assert event_lifetime_count(after_remove) == 1
    assert all(lifetime["current"] for mounted in after_remove["mounted"] for lifetime in mounted["lifetimes"])
    page.clock.run_for(999)
    assert len(poll_routes) == 2
    page.clock.run_for(1)
    page.wait_for_timeout(20)
    after_remaining_deadline = poll_lifetime_snapshot()
    assert len(poll_routes) == 3, (
        f"initial={completed_initial_polls}, after removal={after_remove}, "
        f"at remaining deadline={after_remaining_deadline}"
    )
    assert after_remaining_deadline["pollingLifetimeCount"] == 1
    assert event_lifetime_count(after_remaining_deadline) == 1
    assert all(
        lifetime["current"] and lifetime["inFlight"]
        for mounted in after_remaining_deadline["mounted"]
        for lifetime in mounted["lifetimes"]
    )
    assert poll_routes[2].request.post_data_json["calls"][0]["handlerName"] == "poll"
    poll_routes[2].continue_()
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return [...app.mounted.values()].every(({component}) => !component.$loading('poll')); }"
    )
    page.unroute(event_url)

    assert faults == []


def test_native_event_and_control_throttle_use_monotonic_time_and_replace_cleanup(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="native-event-throttle-clock-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Throttled(Component):
        citry = engine

        class State:
            query: str = ""

        class Events:
            def record(self):
                return None

        template = (
            '<button id="clock-throttle" @c-click.throttle.80ms="record">record</button>'
            '<input id="control-throttle" :c-query.throttle.80ms="record">'
        )

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.add_init_script(
        """globalThis.__citryPerfNow=100;
        Object.defineProperty(performance,'now',{configurable:true,value:()=>globalThis.__citryPerfNow});"""
    )
    page.goto(serve_live(engine, Throttled().render().serialize(), "") + "/")
    page.evaluate(
        """() => {
          const button=document.querySelector('#clock-throttle');
          const realDateNow=Date.now;
          const realSetTimeout=globalThis.setTimeout;
          const realClearTimeout=globalThis.clearTimeout;
          const timingTimers=[];
          globalThis.setTimeout=(callback,delay,...args)=>{
            if(delay!==80)return realSetTimeout(callback,delay,...args);
            const timer={callback:()=>callback(...args),cancelled:false};
            timingTimers.push(timer);
            return timer;
          };
          globalThis.clearTimeout=timer=>{
            if(timingTimers.includes(timer)){timer.cancelled=true;return}
            realClearTimeout(timer);
          };
          button.click();
          globalThis.__citryPerfNow=181;
          Date.now=()=>realDateNow()+10_000_000;
          button.click();
          for(const timer of timingTimers.slice(0,1))if(!timer.cancelled)timer.callback();
          globalThis.__citryPerfNow=200;
          button.click();
          Date.now=()=>0;
          button.click();
          globalThis.__citryPerfNow=281;
          button.click();
          Date.now=realDateNow;
          globalThis.setTimeout=realSetTimeout;
          globalThis.clearTimeout=realClearTimeout;
        }"""
    )
    page.wait_for_timeout(120)
    assert len(calls) == 3

    calls.clear()
    page.evaluate(
        """() => {
          const control=document.querySelector('#control-throttle');
          const realDateNow=Date.now;
          const send=value=>{control.value=value;control.dispatchEvent(new Event('input',{bubbles:true}))};
          globalThis.__citryPerfNow=400;
          send('a');
          globalThis.__citryPerfNow=481;
          Date.now=()=>realDateNow()+10_000_000;
          send('b');
          globalThis.__citryPerfNow=500;
          send('c');
          Date.now=()=>0;
          send('d');
          globalThis.__citryPerfNow=562;
          send('e');
          Date.now=realDateNow;
        }"""
    )
    page.wait_for_timeout(120)
    assert len(calls) == 3


def test_native_dom_event_timing_is_per_element_and_drops_retired_work(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="native-event-timing-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Timed(Component):
        citry = engine

        @dataclass
        class RecordArgs:
            value: int

        class Events:
            def record(self, data: Timed.RecordArgs):
                return None

            def refresh(self):
                return Timed()

        def js_data(self, kwargs, slots) -> dict[str, Any]:
            return {"items": [1, 2], "nextValue": 0, "showConditional": True}

        js = "$component({methods:{next(){this.nextValue += 1;return this.nextValue}}});"
        template = (
            '<main><button class="debounced" v-for="item in items" '
            '@c-click.debounce.40ms="record({value: next()})" v-text="item"></button>'
            '<button id="throttled" @c-click.throttle.80ms="record({value: next()})">throttle</button>'
            '<button id="pending" @c-click.debounce.100ms="record({value: next()})">pending</button>'
            '<button id="conditional" v-if="showConditional" '
            '@c-click.debounce.100ms="record({value: next()})">conditional</button>'
            '<button id="refresh" @c-click="refresh">refresh</button></main>'
        )

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    base = serve_live(engine, Timed().render().serialize(), "")
    page.clock.install()
    page.goto(base + "/")
    page.locator("#refresh").wait_for()
    page.clock.pause_at(page.evaluate("new Date().toISOString()"))

    def wait_for_call_count(count: int) -> None:
        deadline = time.monotonic() + 5
        while len(calls) < count and time.monotonic() < deadline:
            page.wait_for_timeout(10)
        assert len(calls) == count

    first, second = page.locator(".debounced").all()
    first.click()
    first.click()
    second.click()
    page.clock.run_for(39)
    assert calls == []
    page.clock.run_for(1)
    wait_for_call_count(2)
    args = [call["calls"][0]["args"]["value"] for call in calls]
    assert args == [2, 3]

    page.locator("#throttled").click()
    page.locator("#throttled").click()
    assert len(calls) == 3
    page.clock.run_for(80)
    page.locator("#throttled").click()
    wait_for_call_count(4)
    args = [call["calls"][0]["args"]["value"] for call in calls]
    assert args[-2:] == [4, 6]

    before = len(calls)
    page.locator("#pending").click()
    page.locator("#refresh").click()
    page.wait_for_function("CitryStable._apps.values().next().value.revision > 0")
    page.clock.run_for(130)
    page.wait_for_timeout(20)
    assert [(call["calls"][0]["handlerName"], call["calls"][0]["args"]) for call in calls[before:]] == [
        ("refresh", {}),
        ("record", {"value": 7}),
    ]

    page.locator("#conditional").click()
    page.evaluate(
        "CitryStable._apps.values().next().value.mounted.values().next().value.component.showConditional=false"
    )
    page.locator("#conditional").wait_for(state="detached")
    page.clock.run_for(130)
    page.wait_for_timeout(20)
    assert len(calls) == before + 2
    assert (
        page.evaluate(
            "CitryStable._apps.values().next().value.mounted.values().next().value.record."
            "eventTimingLifetimes?.size || 0"
        )
        == 0
    )

    page.locator("#pending").click()
    page.evaluate("CitryStable._apps.values().next().value.vueApp.unmount()")
    page.clock.run_for(130)
    page.wait_for_timeout(20)
    assert len(calls) == before + 2
    assert faults == []


@pytest.mark.parametrize(
    "binding_kind",
    [pytest.param("event", id="ordinary-event"), pytest.param("control", id="state-control")],
)
@pytest.mark.parametrize(
    ("first_callback_time", "expects_remainder"),
    [
        pytest.param(2_147_483_647, True, id="exact-deadline"),
        pytest.param(2_147_484_147, False, id="suspended-overshoot"),
    ],
)
def test_native_debounce_long_delay_uses_signed_timeout_chunks(
    page: Any,
    serve_live: Any,
    binding_kind: str,
    first_callback_time: int,
    expects_remainder: bool,
) -> None:
    maximum_timeout = 2_147_483_647
    requested_delay = 2_147_483_648
    engine = Citry(secret="native-long-delay-secret", autodiscover=False)  # noqa: S106 - test-only key
    engine.set_mounted_prefix("/citry")

    if binding_kind == "event":
        template_source = """
        <button
            id="long-delay"
            @c-click.debounce.2147483648ms="record({value: 1})"
        >
            send
        </button>
        """
    else:
        template_source = """
        <input
            id="long-delay"
            :c-query.debounce.2147483648ms="update"
        >
        """

    class LongDelay(Component):
        citry = engine

        @dataclass
        class RecordArgs:
            value: int

        class State:
            query: str = ""

        class Events:
            def record(self, data: LongDelay.RecordArgs):
                return None

            def update(self, state: LongDelay.State):
                return None

        template = template_source

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    # The fake clock makes a two-day delay testable without waiting on wall time.
    page.add_init_script(
        """globalThis.__citryLongDelayClock = {
          now: 0,
          originalDescriptor: Object.getOwnPropertyDescriptor(performance, "now"),
        };
        Object.defineProperty(performance, "now", {
          configurable: true,
          value: () => globalThis.__citryLongDelayClock.now,
        });"""
    )
    page.goto(serve_live(engine, LongDelay().render().serialize(), "") + "/")

    try:
        page.evaluate(
            """() => {
              const timers = [];
              const harness = {
                timers,
                captureOneMillisecond: false,
                originalSetTimeout: globalThis.setTimeout,
                originalClearTimeout: globalThis.clearTimeout,
              };
              globalThis.__citryLongDelayHarness = harness;
              // Keep bridge and transport timers real while capturing only timeout chunks.
              globalThis.setTimeout = (callback, delay, ...args) => {
                if (delay >= 2147483647 || (harness.captureOneMillisecond && delay === 1)) {
                  const timer = {
                    delay,
                    cancelled: false,
                    fired: false,
                    callback: () => callback(...args),
                  };
                  timers.push(timer);
                  return timer;
                }
                return harness.originalSetTimeout(callback, delay, ...args);
              };
              globalThis.clearTimeout = handle => {
                const timer = timers.find(candidate => candidate === handle);
                if (timer) {
                  timer.cancelled = true;
                  return;
                }
                harness.originalClearTimeout(handle);
              };
            }"""
        )

        if binding_kind == "event":
            page.locator("#long-delay").click()
        else:
            page.evaluate(
                """() => {
                  const control = document.querySelector("#long-delay");
                  control.value = "next";
                  control.dispatchEvent(new Event("input", { bubbles: true }));
                }"""
            )
        page.wait_for_timeout(10)
        initial_timers = page.evaluate(
            """() => globalThis.__citryLongDelayHarness.timers.map(
              ({ delay, cancelled, fired }) => ({ delay, cancelled, fired })
            )"""
        )
        assert initial_timers, "debounce did not request a timeout chunk"
        initial_delays = [timer["delay"] for timer in initial_timers]
        assert initial_delays[0] == maximum_timeout
        assert requested_delay not in initial_delays
        assert initial_timers[0]["cancelled"] is False
        assert calls == []

        after_first_chunk = page.evaluate(
            """async ({ clockTime }) => {
              const harness = globalThis.__citryLongDelayHarness;
              const timer = harness.timers[0];
              if (!timer || timer.cancelled) throw new Error("first timeout chunk is unavailable");
              harness.captureOneMillisecond = true;
              globalThis.__citryLongDelayClock.now = clockTime;
              timer.fired = true;
              try {
                timer.callback();
                await Promise.resolve();
                await Promise.resolve();
              } finally {
                harness.captureOneMillisecond = false;
              }
              return harness.timers.map(({ delay, cancelled, fired }) => ({ delay, cancelled, fired }));
            }""",
            {"clockTime": first_callback_time},
        )
        page.wait_for_timeout(10)
        chunk_delays = [timer["delay"] for timer in after_first_chunk]
        assert after_first_chunk[0]["fired"] is True
        assert requested_delay not in chunk_delays

        if expects_remainder:
            assert chunk_delays == [maximum_timeout, 1]
            assert after_first_chunk[1]["cancelled"] is False
            assert calls == []
            after_remainder = page.evaluate(
                """async () => {
                  const harness = globalThis.__citryLongDelayHarness;
                  const timer = harness.timers[1];
                  if (!timer || timer.cancelled) throw new Error("one-millisecond remainder is unavailable");
                  globalThis.__citryLongDelayClock.now = 2147483648;
                  timer.fired = true;
                  timer.callback();
                  await Promise.resolve();
                  await Promise.resolve();
                  return harness.timers.map(({ delay, cancelled, fired }) => ({ delay, cancelled, fired }));
                }"""
            )
            assert after_remainder[1]["fired"] is True
            assert requested_delay not in [timer["delay"] for timer in after_remainder]
        else:
            assert chunk_delays == [maximum_timeout]
    finally:
        # Restore browser globals before waiting for the single request to settle.
        page.evaluate(
            """() => {
              const harness = globalThis.__citryLongDelayHarness;
              if (harness) {
                globalThis.setTimeout = harness.originalSetTimeout;
                globalThis.clearTimeout = harness.originalClearTimeout;
              }
              const clock = globalThis.__citryLongDelayClock;
              if (clock?.originalDescriptor) {
                Object.defineProperty(performance, "now", clock.originalDescriptor);
              } else {
                delete performance.now;
              }
              delete globalThis.__citryLongDelayHarness;
              delete globalThis.__citryLongDelayClock;
            }"""
        )

    page.wait_for_timeout(120)
    assert len(calls) == 1
    call = calls[0]["calls"][0]
    if binding_kind == "event":
        assert call["handlerName"] == "record"
        assert call["args"] == {"value": 1}
    else:
        assert call["handlerName"] == "update"
        assert call["stateUpdates"] == {"query": "next"}
        assert call["args"] == {}


def test_native_state_control_debounces_and_preserves_the_live_draft(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-browser-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Search(Component):
        citry = engine

        class Kwargs:
            query: str = ""

        class State:
            query: str = ""

        class Events:
            def refresh(self, state: Search.State):
                return Search(query=state.query)

        def template_data(self, kwargs, slots):
            return {"query": kwargs.query}

        js = (
            "$component({onServerRender(){globalThis.__controlCallbackValue=document.querySelector('#query')?.value}})"
        )

        template = (
            '<main><input id="query" type="search" :c-query.debounce.25ms="refresh">'
            "<output>{{ query }}</output></main>"
        )

    dispatcher_for(engine)
    base = serve_live(engine, Search().render().serialize(), "")
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(base + "/")
    page.locator("#query").fill("native")
    assert page.locator("#query").input_value() == "native"
    page.wait_for_function("CitryStable._apps.values().next().value.revision === 1")
    assert page.evaluate("globalThis.__controlCallbackValue") == "native"
    assert page.locator("output").text_content() == "native"
    assert page.locator("#query").input_value() == "native"
    assert faults == []


def test_native_state_controls_apply_boolean_list_and_custom_values(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-matrix-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Controls(Component):
        citry = engine

        class State:
            enabled: bool = True
            tags: list[str] = field(default_factory=lambda: ["b"])
            payload: dict[str, object] = field(default_factory=lambda: {"answer": 42})

        class Events:
            def noop(self):
                return None

        template = (
            '<main><input id="enabled" type="checkbox" :c-enabled>'
            '<select id="tags" multiple :c-tags><option value="a">A</option><option value="b">B</option></select>'
            '<x-control id="custom" :c-payload></x-control></main>'
        )

    page.add_init_script(
        "customElements.define('x-control',class extends HTMLElement{"
        "set value(v){this._value=v}get value(){return this._value}})"
    )
    base = serve_live(engine, Controls().render().serialize(), "")
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(base + "/")
    page.wait_for_timeout(100)
    assert faults == [], page.content()
    assert page.locator("#enabled").is_checked()
    assert page.eval_on_selector("#tags", "element => [...element.selectedOptions].map(option => option.value)") == [
        "b"
    ]
    assert page.eval_on_selector("#custom", "element => element.value") == {"answer": 42}


def test_native_control_unmount_cancels_debounce_and_pending_custom_upgrade(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-cleanup-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Cleanup(Component):
        citry = engine

        class State:
            query: str = ""
            custom: str = "seed"

        class Events:
            def refresh(self, state: Cleanup.State):
                return Cleanup()

        template = (
            '<main><input id="cleanup-query" :c-query.debounce.100ms="refresh">'
            '<x-late id="late" :c-custom></x-late></main>'
        )

    dispatcher_for(engine)
    base = serve_live(engine, Cleanup().render().serialize(), "")
    page.goto(base + "/")
    page.locator("#cleanup-query").fill("pending")
    page.evaluate("CitryStable._apps.values().next().value.vueApp.unmount()")
    page.evaluate(
        "customElements.define('x-late',class extends HTMLElement{"
        "set value(v){globalThis.__lateWrites=(globalThis.__lateWrites||0)+1}})"
    )
    page.wait_for_timeout(150)
    assert page.evaluate("globalThis.__lateWrites || 0") == 0
    assert page.evaluate("CitryStable._apps.size") == 0


def test_native_control_recovers_when_live_input_type_becomes_valid_again(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-recovery-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Recovery(Component):
        citry = engine

        class State:
            enabled: bool = True

        class Events:
            def noop(self):
                return None

        template = '<input id="recover" type="checkbox" :c-enabled>'

    base = serve_live(engine, Recovery().render().serialize(), "")
    page.goto(base + "/")
    page.evaluate("""() => {const el=document.querySelector('#recover');el.setAttribute('type','button');
      CitryStable._apps.values().next().value.mounted.values().next().value.component.$forceUpdate()}""")
    page.wait_for_timeout(0)
    page.evaluate("""() => {const el=document.querySelector('#recover');el.setAttribute('type','checkbox');
      CitryStable._apps.values().next().value.mounted.values().next().value.component.$forceUpdate()}""")
    page.wait_for_timeout(0)
    assert page.locator("#recover").is_checked()


def test_custom_control_setter_event_does_not_echo_to_server(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-echo-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Echo(Component):
        citry = engine

        class State:
            value: str = "seed"

        class Events:
            def refresh(self, state: Echo.State):
                return Echo()

        template = '<x-echo id="echo" :c-value.on:change="refresh"></x-echo>'

    dispatcher_for(engine)
    page.add_init_script("""customElements.define('x-echo',class extends HTMLElement{
      set value(value){this._value=value;this.dispatchEvent(new Event('change'))}get value(){return this._value}})""")
    base = serve_live(engine, Echo().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_timeout(100)
    assert page.eval_on_selector("#echo", "element => element.value") == "seed"
    assert page.evaluate("CitryStable._apps.values().next().value.revision") == 0


def test_custom_control_setter_failure_is_local_and_recovers(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-setter-recovery",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Setter(Component):
        citry = engine

        class State:
            value: str = "good"

        class Events:
            def noop(self):
                return None

        template = '<x-setter id="setter" :c-value></x-setter>'

    page.add_init_script("""customElements.define('x-setter',class extends HTMLElement{
      set value(value){if(value==='bad')throw Error('setter rejected');this._value=value}
      get value(){return this._value}})""")
    base = serve_live(engine, Setter().render().serialize(), "")
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(base + "/")
    page.evaluate("""() => {const mounted=CitryStable._apps.values().next().value.mounted.values().next().value;
      mounted.record.state.values.value='bad';mounted.component.$forceUpdate()}""")
    page.wait_for_timeout(0)
    assert page.eval_on_selector("#setter", "element => element.value") == "good"
    page.evaluate("""() => {const mounted=CitryStable._apps.values().next().value.mounted.values().next().value;
      mounted.record.state.values.value='recovered';mounted.component.$forceUpdate()}""")
    page.wait_for_timeout(0)
    assert page.eval_on_selector("#setter", "element => element.value") == "recovered"
    assert faults == []


def test_custom_control_getter_failure_and_non_json_value_do_not_adopt_or_send(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-getter-recovery",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")
    seen: list[str] = []

    class Getter(Component):
        citry = engine

        class State:
            value: str = "seed"

        class Events:
            def refresh(self, state: Getter.State):
                seen.append(state.value)

        template = '<x-getter id="getter" :c-value.on:change="refresh"></x-getter>'

    dispatcher_for(engine)
    page.add_init_script("""customElements.define('x-getter',class extends HTMLElement{
      set value(value){this._value=value}
      get value(){
        if(this.mode==='throw')throw Error('getter rejected');
        if(this.mode==='invalid')return ()=>{};
        return this._value
      }
    })""")
    faults: list[str] = []
    reports: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: reports.append(message.text)
        if "could not adopt control value into State" in message.text
        else None,
    )
    page.goto(serve_live(engine, Getter().render().serialize(), "") + "/")

    page.eval_on_selector("#getter", "element => {element.mode='throw';element.dispatchEvent(new Event('change'))}")
    page.eval_on_selector("#getter", "element => {element.mode='invalid';element.dispatchEvent(new Event('change'))}")
    page.wait_for_timeout(50)
    assert seen == []
    assert (
        page.evaluate(
            "CitryStable._apps.values().next().value.mounted.values().next().value.record.state.values.value"
        )
        == "seed"
    )
    assert len(reports) == 1

    page.eval_on_selector(
        "#getter",
        "element => {element.mode='valid';element._value='recovered';element.dispatchEvent(new Event('change'))}",
    )
    page.wait_for_timeout(100)
    assert seen == ["recovered"]
    assert (
        page.evaluate(
            "CitryStable._apps.values().next().value.mounted.values().next().value.record.state.values.value"
        )
        == "recovered"
    )
    assert faults == []


def test_native_controls_send_checkbox_multiselect_and_custom_values_upward(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-upward-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")
    seen: list[tuple[str, object]] = []

    class Upward(Component):
        citry = engine

        class State:
            enabled: bool = False
            tags: list[str] = field(default_factory=list)
            custom: str = "old"

        class Events:
            def enabled(self, state: Upward.State):
                seen.append(("enabled", state.enabled))

            def tags(self, state: Upward.State):
                seen.append(("tags", state.tags))

            def custom(self, state: Upward.State):
                seen.append(("custom", state.custom))

        template = (
            '<main><input id="up-enabled" type="checkbox" :c-enabled="enabled">'
            '<select id="up-tags" multiple :c-tags="tags">'
            '<option value="a">A</option><option value="b">B</option></select>'
            '<x-up id="up-custom" :c-custom.on:change="custom"></x-up></main>'
        )

    dispatcher_for(engine)
    page.add_init_script(
        "customElements.define('x-up',class extends HTMLElement{"
        "set value(v){this._value=v}get value(){return this._value}})"
    )
    page.goto(serve_live(engine, Upward().render().serialize(), "") + "/")
    page.locator("#up-enabled").check()
    page.locator("#up-tags").select_option(["a", "b"])
    page.eval_on_selector("#up-custom", "element => {element.value='new';element.dispatchEvent(new Event('change'))}")
    page.wait_for_timeout(100)
    assert ("enabled", True) in seen
    assert ("tags", ["a", "b"]) in seen
    assert ("custom", "new") in seen


def test_supplied_slot_control_sends_through_its_lexical_owner(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-control-slot-owner-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")
    seen: list[str] = []

    class Receiver(Component):
        citry = engine
        name = "receiver"
        template = '<section><c-slot name="body" /></section>'

    class Owner(Component):
        citry = engine

        class State:
            query: str = ""

        class Events:
            def refresh(self, state: Owner.State):
                seen.append(state.query)

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query": "refresh"}}

        template = '<c-receiver><c-fill name="body"><input id="slot-query" c-bind="attrs"></c-fill></c-receiver>'

    dispatcher_for(engine)
    page.goto(serve_live(engine, Owner().render().serialize(), "") + "/")
    page.locator("#slot-query").fill("lexical")
    page.wait_for_timeout(100)
    assert seen == ["lexical"]


def test_supplied_slot_poll_uses_live_lexical_caller_scope(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="native-poll-slot-owner-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Receiver(Component):
        citry = engine
        js = "$component({data(){return {value:'receiver'}}});"
        template = '<section><c-slot name="body" /></section>'

    class Owner(Component):
        citry = engine

        @dataclass
        class PollArgs:
            value: str

        class Events:
            def poll(self, data: Owner.PollArgs):
                return None

        js = "$component({data(){return {value:'caller'}}});"
        template = (
            '<c-Receiver><c-fill name="body">'
            '<output id="slot-poll" @c-poll.1s="poll({value:value})" v-text="value"></output>'
            '<button id="slot-poll-update" @click="value=\'caller-next\'">update</button>'
            "</c-fill></c-Receiver>"
        )

    dispatcher_for(engine)
    requests: list[dict[str, Any]] = []
    faults: list[str] = []
    poll_endpoint = re.compile(r"/ext/events/call$")
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: requests.append(request.post_data_json)
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(engine, Owner().render().serialize(), "") + "/")
    page.locator("#slot-poll").wait_for()

    with page.expect_request(poll_endpoint):
        page.clock.run_for(1_000)
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return !app.mounted.get(app.rootId).component.$loading('poll'); }"
    )
    first_calls = [call for request in requests for call in request["calls"]]
    assert [(call["handlerName"], call["args"]["value"]) for call in first_calls] == [("poll", "caller")]

    requests.clear()
    page.locator("#slot-poll-update").click()
    page.wait_for_function("document.querySelector('#slot-poll')?.textContent === 'caller-next'")
    with page.expect_request(poll_endpoint):
        page.clock.run_for(1_000)
    page.wait_for_function(
        "() => { const app=CitryStable._apps.values().next().value; "
        "return !app.mounted.get(app.rootId).component.$loading('poll'); }"
    )
    second_calls = [call for request in requests for call in request["calls"]]
    assert [(call["handlerName"], call["args"]["value"]) for call in second_calls] == [("poll", "caller-next")]
    assert faults == []


def test_checkbox_invalid_state_value_is_local_and_next_boolean_recovers(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="native-checkbox-recovery-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
    )
    engine.set_mounted_prefix("/citry")

    class Checkbox(Component):
        citry = engine

        class State:
            enabled: bool = True

        class Events:
            def noop(self):
                return None

        template = '<input id="checkbox-recovery" type="checkbox" :c-enabled>'

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Checkbox().render().serialize(), "") + "/")
    page.evaluate("""() => {const mounted=CitryStable._apps.values().next().value.mounted.values().next().value;
      mounted.record.state.values.enabled='invalid';mounted.component.$forceUpdate()}""")
    page.wait_for_timeout(0)
    assert page.locator("#checkbox-recovery").is_checked()
    page.evaluate("""() => {const mounted=CitryStable._apps.values().next().value.mounted.values().next().value;
      mounted.record.state.values.enabled=false;mounted.component.$forceUpdate()}""")
    page.wait_for_timeout(0)
    assert not page.locator("#checkbox-recovery").is_checked()
    assert faults == []


def test_extension_styles_accumulate_for_the_app_lifetime_across_revision(page: Any, serve_live: Any) -> None:
    class Probe(Extension):
        name = "probe"

        def browser_plugin(self):
            return BrowserPluginDescriptor(
                1,
                Script(
                    content="CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},prepareRevision(){return{}},activateRevision(){},commitRevision(){},abortRevision(){},rollbackRevision(){},dispose(){}}),[]);"
                ),
            )

        def prepare_browser_render(self, ctx):
            return BrowserRenderContribution(
                1,
                {"revision": ctx.revision},
                scripts=(
                    Script(
                        url=f"/fragment?rev={ctx.revision}",
                        attrs={"type": "text/javascript"},
                    ),
                ),
                styles=(
                    Style(
                        url=f"data:text/css,.asset-probe%7Bcolor:rgb({ctx.revision + 1},2,3)%7D",
                    ),
                ),
            )

    engine = Citry(secret="extension-style-lifetime", autodiscover=False, extensions=[Probe])  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Page(Component):
        citry = engine
        template = '<button id="rev" class="asset-probe" @c-click="refresh">refresh</button>'

        class Events:
            def refresh(self):
                return Page()

    dispatcher_for(engine)
    external_script = (
        "globalThis.__citryExternalRuns=(globalThis.__citryExternalRuns||[]).concat("
        "new URL(document.currentScript.src).searchParams.get('rev'));"
    )
    base = serve_live(engine, Page().render().serialize(), external_script)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(base + "/")
    page.wait_for_function("globalThis.__citryExternalRuns?.join() === '0'")
    assert page.evaluate("globalThis.__citryExternalRuns") == ["0"]
    page.locator("#rev").click()
    page.wait_for_function("CitryStable._apps.values().next().value.revision === 1")
    page.wait_for_function("globalThis.__citryExternalRuns?.join() === '0,1'")
    assert page.evaluate("globalThis.__citryExternalRuns") == ["0", "1"]
    urls = page.locator("style[data-citry-css-url],link[rel=stylesheet]").evaluate_all(
        "items => items.map(item => item.dataset.citryCssUrl || item.getAttribute('href')).filter(Boolean)"
    )
    assert len(set(urls)) == 2
    assert faults == []


def test_external_prepared_asset_integrity_is_optional_and_identity_is_app_scoped(page: Any) -> None:
    vue_root = Path(__file__).parents[2] / "citry" / "_vue"
    page.route(
        "http://citry.test/",
        lambda route: route.fulfill(
            body='<html><head><link rel="stylesheet" href="/external.css">'
            '<link rel="stylesheet" href="/valid.css" '
            'integrity="  sha384-Yn9gruoRjKqWhrcUSTC4fqE3cjrnAdAuALdz9uJuYmtq8SGNk792qXmmVUtrJ0s6   "></head>'
            '<body><div id="a"></div><div id="b"></div><div id="c"></div>'
            '<div id="collision"></div><div id="nonce"></div><div id="d"></div>'
            '<div id="e"></div></body></html>'
        ),
    )
    page.route(
        "http://citry.test/external.css",
        lambda route: route.fulfill(body=".external{color:green}", content_type="text/css"),
    )
    page.route(
        "http://citry.test/valid.css",
        lambda route: route.fulfill(body=".external{color:green}", content_type="text/css"),
    )
    page.goto("http://citry.test/")
    result = page.evaluate(
        """async ({vueSource,clientSource})=>{window.eval(vueSource);window.eval(clientSource);
          const helper=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1],digest='a'.repeat(64),def='d';
          CitryStableDefinitions={[def]:{render(){return Vue.h('p',{class:'external'},'ok')},
            target:'ordinary-vnodes/1',helperContract:helper,dynamicElements:[],directiveSignature:[],
            replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};CitryStable.registerTypeOptions('Root',digest,{});
          CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},prepareRevision(){return{}},
            activateRevision(){},commitRevision(){},abortRevision(){},rollbackRevision(){},dispose(){}}),[]);
          const style=(url,attrs)=>({owner:{kind:'extension',extensionName:'probe'},
            source:{kind:'external',url,attrs},lazyAllowed:true});
          const manifest=(app,id,attrs,url='/external.css',duplicateAttrs=null)=>({
            protocol:'citry-vue-prepared/1',appId:app,
            revision:0,rootId:id,markers:[],
            occurrences:[{id,typeKey:'Root',definitionId:def,parentId:null,placementKey:null,serverData:{},preparedData:{calls:{}}}],
            definitions:[{id:def,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',helperContract:helper,
              dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]}],
            replacements:[],scripts:[],styles:[style(url,attrs),...(duplicateAttrs?[style(url,duplicateAttrs)]:[])],
            typePolicies:[{typeKey:'Root',lazyAllowed:true}],
            extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}});
          const attempt=async(id,attrs,url='/external.css',duplicateAttrs=null)=>{try{await CitryStable.startPrepared({
            manifest:manifest(id,id+'-root',attrs,url,duplicateAttrs),host:'#'+id,tags:{Root:'citry-root'},
            loadInitialAssets:true});return null}catch(error){return error.message}};
          return {noIntegrity:await attempt('a',{rel:'stylesheet'}),
            crossAppIdentity:await attempt('c',{rel:'stylesheet',crossorigin:'use-credentials'}),
            duplicateCollision:await attempt('collision',{rel:'stylesheet'},'/external.css',
              {rel:'stylesheet',crossorigin:'use-credentials'}),
            nonce:await attempt('nonce',{rel:'stylesheet',nonce:'changed'}),
            validIntegrity:await attempt('d',{rel:'stylesheet',integrity:
              '  sha384-Yn9gruoRjKqWhrcUSTC4fqE3cjrnAdAuALdz9uJuYmtq8SGNk792qXmmVUtrJ0s6   '},'/valid.css'),
            malformedIntegrity:await attempt('e',{rel:'stylesheet',integrity:'sha384-AAAA'},'/wrong.css')};
        }""",
        {"vueSource": (vue_root / "vue.js").read_text(), "clientSource": _client_bundle_source(vue_root)},
    )
    assert result == {
        "noIntegrity": None,
        "crossAppIdentity": None,
        "duplicateCollision": "prepared stylesheet URL identity collision",
        "nonce": "invalid prepared asset source attributes",
        "validIntegrity": None,
        "malformedIntegrity": "invalid prepared asset source attributes",
    }


def test_terminal_app_releases_only_its_shared_stylesheet_reference(page: Any) -> None:
    vue_root = Path(__file__).parents[2] / "citry" / "_vue"
    html = (
        '<style data-citry-css-url="/shared.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.css" '
        'data-citry-vue-style-app="first-app">.shared{color:green}</style>'
        '<style data-citry-css-url="/shared.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.css" '
        'data-citry-vue-style-app="second-app">.shared{color:green}</style>'
        '<div id="first"></div><div id="second"></div>'
    )
    page.route("http://citry.test/", lambda route: route.fulfill(body=html, content_type="text/html"))
    page.goto("http://citry.test/")
    result = page.evaluate(
        """async ({vueSource, clientSource}) => {
          window.eval(vueSource); window.eval(clientSource);
          const helper=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='a'.repeat(64), definitionId='style-definition';
          window.CitryStableDefinitions={[definitionId]:{render(){return Vue.h('p',{class:'shared'},'ready')},
            target:'ordinary-vnodes/1',helperContract:helper,dynamicElements:[],directiveSignature:[],
            replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{onServerRender({revision}){
            if(revision===1)throw new Error('intentional stylesheet cleanup failure');
          }});
          const manifest=(appId,id)=>({protocol:'citry-vue-prepared/1',appId,revision:0,rootId:id,markers:[],
            occurrences:[{id,typeKey:'Root',definitionId,parentId:null,placementKey:null,serverData:{},preparedData:{calls:{}}}],
            definitions:[{id:definitionId,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',
              helperContract:helper,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]}],
            replacements:[],scripts:[],styles:[{owner:{kind:'component',typeKey:'Root',occurrenceIds:[id]},
              source:{kind:'owned',url:'/shared.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.css',sha256:digest},lazyAllowed:true}],
            typePolicies:[{typeKey:'Root',lazyAllowed:true}],extensions:{}});
          await CitryStable.startPrepared({manifest:manifest('first-app','first-root'),host:'#first',
            tags:{Root:'citry-root'}});
          await CitryStable.startPrepared({manifest:manifest('second-app','second-root'),host:'#second',
            tags:{Root:'citry-root'}});
          const fail=async(appId,id)=>{const envelope=manifest(appId,id);envelope.revision=1;
            envelope.baseRevision=0;envelope.updatedIds=[id];
            try { await CitryStable.applyEnvelope(appId,envelope); } catch(error) { return error.message; }};
          const firstFailure=await fail('first-app','first-root');
          const sharedCount=document.querySelectorAll('[data-citry-css-url]').length;
          const secondFailure=await fail('second-app','second-root');
          return {firstFailure,secondFailure,sharedCount,
            finalStyleCount:document.querySelectorAll('[data-citry-css-url]').length,
            first:document.querySelector('#first .shared')?.textContent,
            second:document.querySelector('#second .shared')?.textContent};
        }""",
        {
            "vueSource": (vue_root / "vue.js").read_text(encoding="utf-8"),
            "clientSource": _client_bundle_source(vue_root),
        },
    )
    assert result == {
        "firstFailure": "intentional stylesheet cleanup failure",
        "secondFailure": "intentional stylesheet cleanup failure",
        "sharedCount": 1,
        "finalStyleCount": 0,
        "first": None,
        "second": None,
    }


def test_extension_script_loader_retries_and_restarts_same_app_id(page: Any) -> None:
    vue_root = Path(__file__).parents[2] / "citry" / "_vue"
    requests = {"healthy": 0, "failed": 0}

    def route_asset(route: Any) -> None:
        kind = "failed" if route.request.url.endswith("/failed.js") else "healthy"
        requests[kind] += 1
        if kind == "failed":
            route.fulfill(status=404, body="missing")
        else:
            route.fulfill(body="window.__extensionRuns=(window.__extensionRuns||0)+1", content_type="text/javascript")

    page.route("http://citry.test/", lambda route: route.fulfill(body='<div id="host"></div>'))
    page.route("http://citry.test/healthy.js", route_asset)
    page.route("http://citry.test/failed.js", route_asset)
    page.goto("http://citry.test/")
    result = page.evaluate(
        """async ({vueSource,clientSource})=>{
          window.eval(vueSource); window.eval(clientSource);
          const helper=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='a'.repeat(64), definitionId='loader-root';
          CitryStableDefinitions={[definitionId]:{render(){return Vue.h('p','ready')},
            target:'ordinary-vnodes/1',helperContract:helper,dynamicElements:[],directiveSignature:[],
            replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{});
          CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},prepareRevision(){return{}},
            activateRevision(){},commitRevision(){},abortRevision(){},rollbackRevision(){},dispose(){}}),[]);
          let capturedHost;
          window.CitryVueEvents={createVueEventsBridge(configuration){capturedHost=configuration.host;return{send(){}}}};
          const occurrence=(revision)=>({id:'citryOccurrenceRoot',renderId:'server-root',typeKey:'Root',definitionId,
            parentId:null,placementKey:null,serverData:{revision},
            preparedData:{calls:{}},eventContext:{serverRenderId:'server-root',stateToken:'token'}});
          const definition={id:definitionId,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',
            helperContract:helper,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]};
          const extension={schemaVersion:1,payload:{},templateContextNames:[]};
          const script=url=>({owner:{kind:'extension',extensionName:'probe'},source:{kind:'external',url,attrs:{}},
            lazyAllowed:true,registersOptions:false});
          const manifest=(revision,scripts=[])=>({protocol:'citry-vue-prepared/1',appId:'restartable',revision,
            ...(revision?{baseRevision:revision-1,updatedIds:['citryOccurrenceRoot']}:{rootId:'citryOccurrenceRoot'}),
            rootId:'citryOccurrenceRoot',markers:[],
            occurrences:[occurrence(revision)],definitions:[definition],replacements:[],scripts,styles:[],
            typePolicies:[{typeKey:'Root',lazyAllowed:true}],extensions:{probe:extension}});
          const start=async()=>CitryStable.startPrepared({manifest:manifest(0),host:'#host',tags:{Root:'c-root'},
            endpoint:'/events',allowLazyTypeAssets:true});
          const revise=async(url)=>{
            const app=CitryStable._apps.get('restartable'), mounted=app.mounted.get('citryOccurrenceRoot');
            const source={stableId:'citryOccurrenceRoot',generation:mounted.record.generation};
            const prepared=await capturedHost.prepareRender({prepared:manifest(1,[script(url)])},source);
            await capturedHost.commitRender(prepared,source);
          };
          let handle=await start();
          const failure=async()=>{try{await revise('/failed.js');return null}catch(error){return error.message}};
          const failures=[await failure(),await failure()];
          await revise('/healthy.js');
          const nodesAfterFirst=document.querySelectorAll('script[src$="healthy.js"],script[src$="failed.js"]').length;
          handle.app.unmount();
          document.querySelector('#host').replaceChildren();
          handle=await start();
          await revise('/healthy.js');
          const nodesAfterRestart=document.querySelectorAll(
            'script[src$="healthy.js"],script[src$="failed.js"]'
          ).length;
          handle.app.unmount();
          return {failures,runs:window.__extensionRuns,nodesAfterFirst,nodesAfterRestart};
        }""",
        {
            "vueSource": (vue_root / "vue.js").read_text(encoding="utf-8"),
            "clientSource": _client_bundle_source(vue_root),
        },
    )
    assert result == {
        "failures": [
            "Citry Vue type script failed to load: /failed.js",
            "Citry Vue type script failed to load: /failed.js",
        ],
        "runs": 2,
        "nodesAfterFirst": 0,
        "nodesAfterRestart": 0,
    }
    assert requests == {"healthy": 2, "failed": 2}


def test_native_events_prepare_cancellation_releases_attempt_resources(page: Any) -> None:
    page.set_default_timeout(3_000)
    vue_root = Path(__file__).parents[2] / "citry" / "_vue"
    stalled_routes: list[Any] = []
    page.route("http://citry.test/", lambda route: route.fulfill(body='<div id="host"></div>'))
    page.route("http://citry.test/stalled-events.css", lambda route: stalled_routes.append(route))
    page.goto("http://citry.test/")
    page.evaluate(
        """async ({vueSource,clientSource})=>{
          window.eval(vueSource); window.eval(clientSource);
          const helper=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='a'.repeat(64), definitionId='events-root';
          CitryStableDefinitions={[definitionId]:{render(){return Vue.h('p','ready')},
            target:'ordinary-vnodes/1',helperContract:helper,dynamicElements:[],directiveSignature:[],
            replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{});
          window.__pluginAborts=0;
          CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},
            prepareRevision(payload){
              if(payload.phase!=='late'&&payload.phase!=='microtask')return {};
              window.__pluginPreparing=true;
              return new Promise(resolve=>{window.__resolvePlugin=()=>resolve(
                payload.phase==='microtask'?undefined:{late:true})});
            },activateRevision(){},commitRevision(){},abortRevision(){window.__pluginAborts++},
            rollbackRevision(){},dispose(){}}),[]);
          let capturedHost;
          window.CitryVueEvents={createVueEventsBridge(configuration){capturedHost=configuration.host;
            return{send(){},retire(){},dispose(){}}}};
          const occurrence=()=>({id:'citryOccurrenceRoot',renderId:'server-root',typeKey:'Root',definitionId,
            parentId:null,placementKey:null,serverData:{},
            preparedData:{calls:{}},eventContext:{serverRenderId:'server-root',stateToken:'token'}});
          const definition={id:definitionId,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',
            helperContract:helper,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]};
          const manifest=(revision,styles=[],phase='initial')=>({protocol:'citry-vue-prepared/1',appId:'events-app',
            revision,...(revision?{baseRevision:0,updatedIds:['citryOccurrenceRoot']}:{rootId:'citryOccurrenceRoot'}),
            rootId:'citryOccurrenceRoot',markers:[],
            occurrences:[occurrence()],definitions:[definition],replacements:[],scripts:[],styles,
            typePolicies:[{typeKey:'Root',lazyAllowed:true}],
            extensions:{probe:{schemaVersion:1,payload:{phase},templateContextNames:[]}}});
          await CitryStable.startPrepared({manifest:manifest(0),host:'#host',tags:{Root:'c-root'},
            endpoint:'/events',allowLazyTypeAssets:true});
          const mounted=CitryStable._apps.get('events-app').mounted.get('citryOccurrenceRoot');
          window.__eventsSource={stableId:'citryOccurrenceRoot',generation:mounted.record.generation};
          window.__eventsHost=capturedHost;
          const style={owner:{kind:'component',typeKey:'Root',occurrenceIds:['citryOccurrenceRoot']},
            source:{kind:'external',url:'/stalled-events.css',attrs:{rel:'stylesheet'}},lazyAllowed:true};
          window.__eventsController=new AbortController();
          window.__eventsPending=capturedHost.prepareRender({prepared:manifest(1,[style])},__eventsSource,
            __eventsController.signal).then(()=> 'prepared', error=>String(error));
          window.__eventsManifest=manifest;
        }""",
        {
            "vueSource": (vue_root / "vue.js").read_text(encoding="utf-8"),
            "clientSource": _client_bundle_source(vue_root),
        },
    )
    page.wait_for_function("document.querySelector('link[href$=\"/stalled-events.css\"]') !== null")
    page.evaluate("__eventsController.abort()")
    assert "cancelled" in page.evaluate("__eventsPending")
    assert page.locator('link[href$="/stalled-events.css"]').count() == 0
    assert (
        page.evaluate(
            """async()=>{
          const prepared=await __eventsHost.prepareRender({prepared:__eventsManifest(1,[])},__eventsSource,
            new AbortController().signal);
          __eventsHost.abortRender(prepared,__eventsSource);
          return true;
        }"""
        )
        is True
    )
    page.evaluate("window.__pluginAborts = 0")
    page.evaluate(
        """()=>{
          window.__lateController=new AbortController();
          window.__latePending=__eventsHost.prepareRender({prepared:__eventsManifest(1,[],'late')},__eventsSource,
            __lateController.signal).then(()=> 'prepared',error=>String(error));
        }"""
    )
    page.wait_for_function("window.__pluginPreparing === true")
    page.evaluate("__lateController.abort(); __resolvePlugin()")
    assert "cancelled" in page.evaluate("__latePending")
    page.wait_for_function("window.__pluginAborts >= 1", timeout=3_000)
    assert page.evaluate("window.__pluginAborts") == 1
    page.evaluate(
        """()=>{
          window.__pluginPreparing=false;
          window.__microController=new AbortController();
          window.__microPending=__eventsHost.prepareRender(
            {prepared:__eventsManifest(1,[],'microtask')},__eventsSource,__microController.signal
          ).then(()=> 'prepared',error=>String(error));
        }"""
    )
    page.wait_for_function("window.__pluginPreparing === true")
    page.evaluate("__resolvePlugin(); queueMicrotask(()=>__microController.abort())")
    assert "cancelled" in page.evaluate("__microPending")
    page.wait_for_function("window.__pluginAborts >= 2", timeout=3_000)
    assert page.evaluate("window.__pluginAborts") == 2
    assert len(stalled_routes) == 1


def test_disposed_events_commit_cannot_publish_into_reused_app_id(page: Any) -> None:
    page.set_default_timeout(3_000)
    vue_root = Path(__file__).parents[2] / "citry" / "_vue"
    page.route("http://citry.test/", lambda route: route.fulfill(body='<div id="host"></div>'))
    page.route(
        "http://citry.test/*.css",
        lambda route: route.fulfill(body=".ready{color:green}", content_type="text/css"),
    )
    page.goto("http://citry.test/")
    result = page.evaluate(
        """async ({vueSource,clientSource})=>{
          window.eval(vueSource); window.eval(clientSource);
          const helper=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='a'.repeat(64), definitionId='reuse-root';
          CitryStableDefinitions={[definitionId]:{render(){return Vue.h('p',{class:'ready'},'ready')},
            target:'ordinary-vnodes/1',helperContract:helper,dynamicElements:[],directiveSignature:[],
            replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{onServerRender({revision}){
            if(revision===1)queueMicrotask(()=>window.__disposeAtFinalTick())
          }});
          CitryStable.registerBrowserPlugin('probe',1,()=>({install(){},prepareRevision(){return{}},
            activateRevision(){},commitRevision(){
              if(window.__disposeInPluginCommit){window.__disposeInPluginCommit=false;window.__oldHandle.app.unmount()}
            },abortRevision(){},rollbackRevision(){},dispose(){}}),[]);
          let capturedHost;
          window.CitryVueEvents={createVueEventsBridge(configuration){capturedHost=configuration.host;
            return{send(){},retire(){},dispose(){}}}};
          const occurrence=()=>({id:'citryOccurrenceRoot',renderId:'server-root',typeKey:'Root',definitionId,
            parentId:null,placementKey:null,serverData:{},
            preparedData:{calls:{}},eventContext:{serverRenderId:'server-root',stateToken:'token'}});
          const definition={id:definitionId,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',
            helperContract:helper,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]};
          const style=url=>({owner:{kind:'component',typeKey:'Root',occurrenceIds:['citryOccurrenceRoot']},
            source:{kind:'external',url,attrs:{rel:'stylesheet'}},lazyAllowed:true});
          const manifest=(revision,url)=>({protocol:'citry-vue-prepared/1',appId:'reused-app',revision,
            ...(revision?{baseRevision:0,updatedIds:['citryOccurrenceRoot']}:{rootId:'citryOccurrenceRoot'}),
            rootId:'citryOccurrenceRoot',markers:[],occurrences:[occurrence()],
            definitions:[definition],replacements:[],scripts:[],styles:[style(url)],
            typePolicies:[{typeKey:'Root',lazyAllowed:true}],
            extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}});
          const start=url=>CitryStable.startPrepared({manifest:manifest(0,url),host:'#host',tags:{Root:'c-root'},
            endpoint:'/events',allowLazyTypeAssets:true,loadInitialAssets:true});
          let oldHandle=await start('/old.css');
          window.__oldHandle=oldHandle;
          let mounted=CitryStable._apps.get('reused-app').mounted.get('citryOccurrenceRoot');
          let source={stableId:'citryOccurrenceRoot',generation:mounted.record.generation};
          const syncPrepared=await capturedHost.prepareRender({prepared:manifest(1,'/sync.css')},source,
            new AbortController().signal);
          window.__disposeInPluginCommit=true;
          const syncResult=await capturedHost.commitRender(syncPrepared,source)
            .then(()=> 'committed',error=>String(error));
          const syncStyles=[...document.querySelectorAll('[data-citry-css-url]')]
            .map(node=>node.getAttribute('data-citry-css-url'));
          document.querySelector('#host').replaceChildren();
          oldHandle=await start('/old.css');
          window.__oldHandle=oldHandle;
          mounted=CitryStable._apps.get('reused-app').mounted.get('citryOccurrenceRoot');
          source={stableId:'citryOccurrenceRoot',generation:mounted.record.generation};
          const prepared=await capturedHost.prepareRender({prepared:manifest(1,'/old-revision.css')},source,
            new AbortController().signal);
          let resolveReplacement;
          const replacementPending=new Promise(resolve=>{resolveReplacement=resolve});
          window.__disposeAtFinalTick=async()=>{
            oldHandle.app.unmount();
            document.querySelector('#host').replaceChildren();
            resolveReplacement(await start('/replacement.css'));
          };
          const oldCommit=capturedHost.commitRender(prepared,source).then(()=> 'committed',error=>String(error));
          const oldResult=await oldCommit;
          const replacement=await replacementPending;
          const styles=[...document.querySelectorAll('[data-citry-css-url]')]
            .map(node=>node.getAttribute('data-citry-css-url'));
          const alive=CitryStable._apps.get('reused-app')?.vueApp===replacement.app;
          replacement.app.unmount();
          return {syncResult,syncStyles,oldResult,styles,alive};
        }""",
        {
            "vueSource": (vue_root / "vue.js").read_text(encoding="utf-8"),
            "clientSource": _client_bundle_source(vue_root),
        },
    )
    assert "disposed during plugin publication" in result["syncResult"]
    assert result["syncStyles"] == []
    assert "render failed" in result["oldResult"] or "stale" in result["oldResult"]
    assert result["styles"] == ["/replacement.css"]
    assert result["alive"] is True


def test_lazy_native_events_bridge_publishes_reactive_loading_and_error(page: Any) -> None:
    vue_root = Path(__file__).parents[2] / "citry" / "_vue"
    page.route("http://citry.test/", lambda route: route.fulfill(body='<div id="host"></div>'))
    page.goto("http://citry.test/")
    result = page.evaluate(
        """async ({vueSource,clientSource,eventsSource})=>{
          window.eval(vueSource); window.eval(eventsSource);
          const create=CitryVueEvents.createVueEventsBridge;
          window.__bridgeCreates=0;
          window.CitryVueEvents={...CitryVueEvents,createVueEventsBridge:configuration=>{
            window.__bridgeCreates++;
            window.__eventsHost=configuration.host;
            window.__bridge=create({...configuration,fetch:async(_url,init)=>{
              window.__call=JSON.parse(init.body);
              return await new Promise(resolve=>{window.__respond=resolve});
            }});
            return window.__bridge;
          }};
          window.eval(clientSource);
          const helper=clientSource.match(/const HELPER_CONTRACT = "([^"]+)"/)[1];
          const digest='a'.repeat(64),definitionId='lazy-events-root';
          CitryStableDefinitions={[definitionId]:{render(){return Vue.h('div',[
            Vue.h('output',{id:'loading'},String(this.$loading())),
            Vue.h('output',{id:'error'},this.$error()?.message||'')])},
            target:'ordinary-vnodes/1',helperContract:helper,dynamicElements:[],directiveSignature:[],
            replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[]}};
          CitryStable.registerTypeOptions('Root',digest,{onServerRender({component,revision}){
            if(revision===1)window.__callbackSawBridge=window.__bridgeCreates===1&&component.$loading()===false
          }});
          const definition={id:definitionId,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',
            helperContract:helper,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]};
          const occurrence=eventContext=>({id:'root',renderId:'server_1',typeKey:'Root',definitionId,
            parentId:null,placementKey:null,serverData:{},
            preparedData:{calls:{}},...(eventContext?{eventContext}:{})});
          const base={protocol:'citry-vue-prepared/1',appId:'lazy-events-app',revision:0,rootId:'root',markers:[],
            occurrences:[occurrence()],definitions:[definition],replacements:[],scripts:[],styles:[],
            typePolicies:[{typeKey:'Root',lazyAllowed:true}],extensions:{}};
          const handle=await CitryStable.startPrepared({manifest:base,host:'#host',tags:{Root:'c-root'},
            endpoint:'/events',allowLazyTypeAssets:true});
          const before=window.__bridgeCreates;
          const descriptor={componentClassId:'Root_1',eventHandlers:{
            constructor:{httpMethod:'POST',usesState:true},toString:{httpMethod:'POST',usesState:true}},
            writableStateFields:['rows']};
          const context={serverRenderId:'server_1',stateToken:'token',
            publicState:{rows:[{id:1}],locked:{value:1}},
            componentClassId:'Root_1',descriptor};
          await CitryStable.applyEnvelope('lazy-events-app',{...base,revision:1,baseRevision:0,
            updatedIds:['root'],occurrences:[occurrence(context)]});
          const mounted=CitryStable._apps.get('lazy-events-app').mounted.get('root');
          const component=mounted.component,source={stableId:'root',generation:mounted.record.generation};
          const invalidArgsErrors=[];
          for(const invalid of [null,false,0,'',NaN]){
            try{await component.$sendEvent('constructor',invalid)}catch(error){invalidArgsErrors.push(String(error))}
          }
          const invalidArgsFetched=Boolean(window.__call);
          const capturedRows=component.$state.rows;
          let nestedError='',readonlyError='',popError='',spliceError='',descriptorError='',sparseError='';
          try{capturedRows.push({id:2})}catch(error){nestedError=String(error)}
          try{capturedRows.pop()}catch(error){popError=String(error)}
          try{capturedRows.splice(0,1)}catch(error){spliceError=String(error)}
          try{component.$state.locked.value=2}catch(error){readonlyError=String(error)}
          try{Object.getOwnPropertyDescriptor(component.$state,'rows').value[0].id=9}
          catch(error){descriptorError=String(error)}
          const protoValue=JSON.parse('[{"__proto__":{"safe":1}}]');
          component.$state.rows=protoValue;
          const protoSnapshot={keys:Object.keys(component.$state.rows[0]),
            own:Object.prototype.hasOwnProperty.call(component.$state.rows[0],'__proto__'),
            nested:component.$state.rows[0].__proto__.safe,
            prototype:Object.getPrototypeOf(component.$state.rows[0])===Object.prototype};
          let customPrototypeError='';
          const customPrototype=Object.create({poison:true});customPrototype.id=8;
          try{component.$state.rows=[customPrototype]}catch(error){customPrototypeError=String(error)}
          const afterCustomPrototype=component.$state.rows[0].__proto__.safe;
          let preventError='',freezeError='',sealError='',nestedPreventError='';
          try{Object.preventExtensions(component.$state)}catch(error){preventError=String(error)}
          try{Object.freeze(component.$state)}catch(error){freezeError=String(error)}
          try{Object.seal(component.$state)}catch(error){sealError=String(error)}
          try{Object.preventExtensions(component.$state.rows[0])}catch(error){nestedPreventError=String(error)}
          const extensibleAfterRejects={facade:Object.isExtensible(component.$state),
            nested:Object.isExtensible(component.$state.rows[0])};
          const shared={id:4};component.$state.rows=[shared,shared];shared.id=9;
          const repeatedAlias=[...component.$state.rows].map(row=>row.id);
          const sparse=[];sparse[1]={id:5};
          try{component.$state.rows=sparse}catch(error){sparseError=String(error)}
          component.$state.rows=[{id:2}];
          const initialError=component.$error('constructor');
          let unknown='';try{component.$loading('missing')}catch(error){unknown=String(error)}
          let earlyResult=null;
          const pending=window.__bridge.send({source,handler:'constructor'}).then(()=>(earlyResult='ok',''),
            error=>(earlyResult=error?.message||String(error),error?.message||String(error)));
          await new Promise(resolve=>queueMicrotask(resolve));
          for(let count=0;!window.__call&&count<10;count++)await new Promise(resolve=>setTimeout(resolve,0));
          if(!window.__call){handle.app.unmount();return {before,creates:window.__bridgeCreates,
            callbackSawBridge:window.__callbackSawBridge,earlyResult}}
          await Vue.nextTick();
          const loadingDuring=document.querySelector('#loading').textContent;
          const componentLoadingDuring=component.$loading('constructor');
          const call=window.__call.calls[0];
          const firstStateUpdates=call.stateUpdates;
          component.$state.rows=[{id:3}];
          window.__respond(new Response(JSON.stringify({protocol:'citry-events/1',requestId:window.__call.requestId,
            results:[{ok:false,sendSequence:call.sendSequence,
                  error:{status:409,code:'conflict',message:'try again',fieldErrors:{constructor:'blocked'}}}]}),
            {headers:{'Content-Type':'application/json'}}));
          const rejected=await pending;
          await Vue.nextTick();
          const after={loading:document.querySelector('#loading').textContent,
            error:document.querySelector('#error').textContent,specific:component.$error('constructor')};
          const serverContext={...context,publicState:{rows:[{id:99}],locked:{value:2}}};
          await CitryStable.applyEnvelope('lazy-events-app',{...base,revision:2,baseRevision:1,
            updatedIds:['root'],occurrences:[occurrence(serverContext)]});
          const adoptedRows=[...component.$state.rows].map(row=>row.id);
          window.__call=null;
          const successful=component.$sendEvent('constructor');
          while(!window.__call)await new Promise(resolve=>setTimeout(resolve,0));
          const successCall=window.__call.calls[0];
          const omittedArgs=successCall.args;
          const secondStateUpdates=successCall.stateUpdates;
          window.__respond(new Response(JSON.stringify({protocol:'citry-events/1',requestId:window.__call.requestId,
            results:[{ok:true,sendSequence:successCall.sendSequence,actions:[]}]}),
            {headers:{'Content-Type':'application/json'}}));
          await successful;
          const cleared=component.$error('constructor');
          const readonlyContext={...serverContext,publicState:{rows:[{id:10}],locked:{value:3}},
            descriptor:{...descriptor,writableStateFields:[]}};
          await CitryStable.applyEnvelope('lazy-events-app',{...base,revision:3,baseRevision:2,
            updatedIds:['root'],occurrences:[occurrence(readonlyContext)]});
          let wholeReadonlyError='';try{component.$state.rows=[{id:11}]}
          catch(error){wholeReadonlyError=String(error)}
          window.__call=null;
          const stringCall=component.$sendEvent('toString');
          const stringBusy=component.$loading('toString');
          while(!window.__call)await new Promise(resolve=>setTimeout(resolve,0));
          const ownStringCall=window.__call.calls[0];
          const thirdStateUpdates=ownStringCall.stateUpdates;
          window.__respond(new Response(JSON.stringify({protocol:'citry-events/1',requestId:window.__call.requestId,
            results:[{ok:true,sendSequence:ownStringCall.sendSequence,actions:[]}]}),
            {headers:{'Content-Type':'application/json'}}));
          await stringCall;
          const currentRows=[...component.$state.rows].map(row=>({id:row.id}));
          const capturedRowsValue=[...capturedRows].map(row=>({id:row.id}));
          await CitryStable.applyEnvelope('lazy-events-app',{...base,revision:4,baseRevision:3,
            updatedIds:['root'],occurrences:[occurrence()]});
          let lostContextRestore='ok',capturedAfterLoss='';
          try{window.__eventsHost.restorePendingState(source,{rows:[{id:12}]})}
          catch(error){lostContextRestore=String(error)}
          try{void capturedRows[0]}catch(error){capturedAfterLoss=String(error)}
          const inactiveStateKeys=Object.keys(component.$state);
          handle.app.unmount();
          let retiredError='';try{void component.$state.rows}catch(error){retiredError=String(error)}
          return {before,creates:window.__bridgeCreates,callbackSawBridge:window.__callbackSawBridge,
            loadingDuring,componentLoadingDuring,unknown,rejected,after,initialError,cleared,stringBusy,nestedError,readonlyError,
            popError,spliceError,descriptorError,sparseError,repeatedAlias,
            protoSnapshot,customPrototypeError,afterCustomPrototype,preventError,freezeError,sealError,
            nestedPreventError,extensibleAfterRejects,
            invalidArgsErrors,invalidArgsFetched,omittedArgs,
            capturedRows:capturedRowsValue,currentRows,firstStateUpdates,secondStateUpdates,
            thirdStateUpdates:thirdStateUpdates??null,retiredError,adoptedRows,wholeReadonlyError,
            lostContextRestore,capturedAfterLoss,inactiveStateKeys};
        }""",
        {
            "vueSource": (vue_root / "vue.js").read_text(encoding="utf-8"),
            "clientSource": _client_bundle_source(vue_root),
            "eventsSource": (vue_root / "events.js").read_text(encoding="utf-8"),
        },
    )
    assert result["before"] == 0
    assert result["creates"] == 1
    assert result["callbackSawBridge"] is True
    assert "earlyResult" not in result, result.get("earlyResult")
    assert result["componentLoadingDuring"] is True
    assert "Unknown event handler 'missing'" in result["unknown"]
    assert "try again" in result["rejected"]
    assert result["initialError"] is None
    assert result["cleared"] is None
    assert result["stringBusy"] is True
    assert "Nested $state values are read-only" in result["nestedError"]
    assert "Nested $state values are read-only" in result["popError"]
    assert "Nested $state values are read-only" in result["spliceError"]
    assert "Nested $state values are read-only" in result["descriptorError"]
    assert "Nested $state values are read-only" in result["readonlyError"]
    assert "dense JSON arrays" in result["sparseError"]
    assert result["protoSnapshot"] == {"keys": ["__proto__"], "own": True, "nested": 1, "prototype": True}
    assert "strict JSON" in result["customPrototypeError"]
    assert result["afterCustomPrototype"] == 1
    assert "cannot be frozen" in result["preventError"]
    assert "cannot be frozen" in result["freezeError"]
    assert "cannot be frozen" in result["sealError"]
    assert "Nested $state values are read-only" in result["nestedPreventError"]
    assert result["extensibleAfterRejects"] == {"facade": True, "nested": True}
    assert len(result["invalidArgsErrors"]) == 5
    assert all("must be a plain object" in error for error in result["invalidArgsErrors"])
    assert result["invalidArgsFetched"] is False
    assert result["omittedArgs"] == {}
    assert result["repeatedAlias"] == [4, 4]
    assert result["capturedRows"] == [{"id": 1}]
    assert result["currentRows"] == [{"id": 10}]
    assert result["firstStateUpdates"] == {"rows": [{"id": 2}]}
    assert result["secondStateUpdates"] == {"rows": [{"id": 3}]}
    assert result["thirdStateUpdates"] is None
    assert result["adoptedRows"] == [3]
    assert "not client-writable" in result["wholeReadonlyError"]
    assert "stale or retired" in result["retiredError"]
    assert result["lostContextRestore"] == "ok"
    assert "stale or retired" in result["capturedAfterLoss"]
    assert result["inactiveStateKeys"] == []
    assert result["after"]["loading"] == "false"
    assert result["after"]["specific"] == {
        "status": 409,
        "code": "conflict",
        "message": "try again",
        "fieldErrors": {"constructor": "blocked"},
    }


def test_dynamic_element_changes_tag_across_a_prepared_revision(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="dynamic-element-e2e", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class DynamicState:
        tag = "section"

        def render(self):
            return View(tag=self.tag)

    class View(Component):
        citry = engine
        template = (
            '<button id="swap" @c-click="swap">swap</button>'
            '<c-element c-is="tag"><span id="inside">content</span></c-element>'
        )
        State = DynamicState

        class Events:
            def swap(self, state: DynamicState):
                state.tag = "article"
                return state.render()

        def template_data(self, kwargs, slots):
            return {"tag": kwargs["tag"]}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, View(tag="section").render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#inside')?.parentElement?.tagName === 'SECTION'")
    page.locator("#swap").click()
    page.wait_for_function("document.querySelector('#inside')?.parentElement?.tagName === 'ARTICLE'")
    assert faults == []


def test_dynamic_element_keeps_authored_vue_bindings_and_key_across_revision(
    page: Any,
    serve_live: Any,
) -> None:
    engine = Citry(secret="dynamic-element-bindings-e2e", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class DynamicState:
        tag = "section"
        key = "first"

        def render(self):
            return View(tag=self.tag, key=self.key)

    class View(Component):
        citry = engine
        State = DynamicState
        js = "$component({data(){return {label:'ready',clicks:0}}});"
        template = (
            '<main @click="clicks += 100"><button id="swap-bound" @c-click.stop="swap">swap</button>'
            '<c-element c-is="tag" #c-key="key" id="dynamic-bound" '
            '@click.stop="clicks++" :title="`${label}:${clicks}`">content</c-element></main>'
        )

        class Events:
            def swap(self, state: DynamicState):
                state.tag = "article"
                state.key = "second"
                return state.render()

        def template_data(self, kwargs, slots):
            return {"tag": kwargs["tag"], "key": kwargs["key"]}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, View(tag="section", key="first").render().serialize(), "") + "/")
    page.wait_for_selector("section#dynamic-bound[title='ready:0']")
    page.evaluate("window.__firstDynamicElement = document.querySelector('#dynamic-bound')")
    page.locator("#dynamic-bound").click()
    page.wait_for_function("document.querySelector('#dynamic-bound')?.title === 'ready:1'")
    page.locator("#swap-bound").click()
    page.wait_for_function("document.querySelector('#dynamic-bound')?.tagName === 'ARTICLE'")
    assert page.evaluate("window.__firstDynamicElement !== document.querySelector('#dynamic-bound')")
    assert page.locator("#dynamic-bound").get_attribute("title") == "ready:1"
    assert faults == []


def test_cached_dynamic_elements_keep_independent_instance_state(
    page: Any,
    serve_live: Any,
) -> None:
    engine = Citry(secret="dynamic-element-slot-cache-e2e", autodiscover=False)  # noqa: S106

    class CachedOwner(Component):
        citry = engine
        js = "$component({data(){return {label:'cached',clicks:0}}});"

        class Cache:
            enabled = True

        template = (
            '<c-element c-is="tag" class="cached-dynamic" @click="clicks++" '
            ':title="`${label}:${clicks}`">cached</c-element>'
        )

        def template_data(self, kwargs, slots):
            return {"tag": "button"}

    class Page(Component):
        citry = engine
        template = "<main><c-CachedOwner /><c-CachedOwner /></main>"

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    buttons = page.locator(".cached-dynamic")
    page.wait_for_timeout(200)
    assert buttons.count() == 2, (faults, page.content())
    assert buttons.evaluate_all("items => items.map(item => item.title)") == ["cached:0", "cached:0"]
    buttons.nth(0).click()
    page.wait_for_function(
        "() => [...document.querySelectorAll('.cached-dynamic')]"
        ".map(item => item.title).join('|') === 'cached:1|cached:0'"
    )
    assert faults == []


def test_dynamic_element_in_supplied_slot_uses_lexical_caller_scope(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="dynamic-element-slot-owner-e2e", autodiscover=False)  # noqa: S106

    class Receiver(Component):
        citry = engine
        js = "$component({data(){return {label:'receiver',clicks:50}}});"
        template = '<section><c-slot name="body" /></section>'

    class Owner(Component):
        citry = engine
        js = "$component({data(){return {label:'caller',clicks:0}}});"
        template = (
            '<c-Receiver><c-fill name="body">'
            '<c-element c-is="tag" class="slot-dynamic" @click="clicks++" '
            ':title="`${label}:${clicks}`">slot</c-element>'
            "</c-fill></c-Receiver>"
        )

        def template_data(self, kwargs, slots):
            return {"tag": "button"}

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Owner().render().serialize(), "") + "/")
    button = page.locator(".slot-dynamic")
    assert button.get_attribute("title") == "caller:0"
    button.click()
    page.wait_for_function("document.querySelector('.slot-dynamic')?.title === 'caller:1'")
    assert faults == []


def test_dynamic_input_model_type_remounts_from_final_generic_binding(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class DynamicModel(Component):
        citry = engine
        template = (
            '<main><input id="dynamic-model" v-model="value" v-bind="inputAttrs">'
            '<button id="number-model" @click="inputAttrs = {type: \'number\'}">number</button>'
            '<output id="model-kind" v-text="typeof value + \':\' + value"></output></main>'
        )
        js = "$component({data(){return {value:'7',inputAttrs:{type:'text'}};}});"

    page.goto(serve_document(DynamicModel().render().serialize()))
    page.wait_for_selector("#dynamic-model")
    page.evaluate("window.__initialDynamicModel = document.querySelector('#dynamic-model')")
    page.locator("#number-model").click()
    page.wait_for_function("document.querySelector('#dynamic-model')?.type === 'number'")
    assert page.evaluate("window.__initialDynamicModel !== document.querySelector('#dynamic-model')")
    page.locator("#dynamic-model").fill("12")
    assert page.locator("#model-kind").text_content() == "number:12"


def test_dynamic_void_and_namespaced_elements_mount_through_start_prepared(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class View(Component):
        citry = engine
        template = """
          <c-element c-is="void_tag" c-id="input_id" />
          <svg id="svg"><c-element c-is="svg_tag" c-viewBox="view_box"></c-element></svg>
          <math id="math"><c-element c-is="math_tag">x</c-element></math>
          <svg><foreignObject><c-element c-is="html_tag" c-id="html_id">x</c-element></foreignObject></svg>
          <c-element c-is="svg_root_tag" c-id="svg_root_id"><circle id="dynamic-circle"></circle></c-element>
          <c-element c-is="math_root_tag" c-id="math_root_id"><mi id="dynamic-mi">y</mi></c-element>
          <svg><c-element c-is="foreign_root_tag" c-id="foreign_root_id">
            <div id="dynamic-foreign-child">z</div>
          </c-element></svg>
          <textarea id="literal-textarea">a &amp; b</textarea>
          <c-element c-is="textarea_tag" c-id="textarea_id">a &amp; b</c-element>
          <title id="literal-title">c &amp; d</title>
          <c-element c-is="title_tag" c-id="title_id">c &amp; d</c-element>
        """

        def template_data(self, kwargs, slots):
            return {
                "void_tag": "input",
                "svg_tag": "rect",
                "math_tag": "mi",
                "html_tag": "div",
                "view_box": "0 0 2 2",
                "input_id": "dynamic-input",
                "html_id": "foreign-html",
                "svg_root_tag": "svg",
                "svg_root_id": "dynamic-svg-root",
                "math_root_tag": "math",
                "math_root_id": "dynamic-math-root",
                "foreign_root_tag": "foreignObject",
                "foreign_root_id": "dynamic-foreign-root",
                "textarea_tag": "textarea",
                "textarea_id": "dynamic-textarea",
                "title_tag": "title",
                "title_id": "dynamic-title",
            }

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(View().render().serialize()))
    page.wait_for_function("document.querySelector('#dynamic-input') !== null")
    result = page.evaluate(
        """() => ({
          input: document.querySelector('#dynamic-input')?.tagName,
          rectNamespace: document.querySelector('#svg')?.firstElementChild?.namespaceURI,
          viewBox: document.querySelector('#svg')?.firstElementChild?.getAttribute('viewBox'),
          mathNamespace: document.querySelector('#math')?.firstElementChild?.namespaceURI,
          foreignNamespace: document.querySelector('#foreign-html')?.namespaceURI,
          svgRoot: [document.querySelector('#dynamic-svg-root')?.namespaceURI,
            document.querySelector('#dynamic-circle')?.namespaceURI],
          mathRoot: [document.querySelector('#dynamic-math-root')?.namespaceURI,
            document.querySelector('#dynamic-mi')?.namespaceURI],
          foreignRoot: [document.querySelector('#dynamic-foreign-root')?.namespaceURI,
            document.querySelector('#dynamic-foreign-child')?.namespaceURI],
          textarea: [
            document.querySelector('#dynamic-textarea')?.value,
            document.querySelector('#dynamic-textarea')?.textContent,
          ],
          literalTextarea: [
            document.querySelector('#literal-textarea')?.value,
            document.querySelector('#literal-textarea')?.textContent,
          ],
          title: [
            document.querySelector('#dynamic-title')?.text,
            document.querySelector('#dynamic-title')?.textContent,
          ],
          literalTitle: [
            document.querySelector('#literal-title')?.text,
            document.querySelector('#literal-title')?.textContent,
          ],
        })"""
    )
    assert result == {
        "input": "INPUT",
        "rectNamespace": "http://www.w3.org/2000/svg",
        "viewBox": "0 0 2 2",
        "mathNamespace": "http://www.w3.org/1998/Math/MathML",
        "foreignNamespace": "http://www.w3.org/1999/xhtml",
        "svgRoot": ["http://www.w3.org/2000/svg", "http://www.w3.org/2000/svg"],
        "mathRoot": ["http://www.w3.org/1998/Math/MathML", "http://www.w3.org/1998/Math/MathML"],
        "foreignRoot": ["http://www.w3.org/2000/svg", "http://www.w3.org/1999/xhtml"],
        "textarea": ["a & b", "a & b"],
        "literalTextarea": ["a & b", "a & b"],
        "title": ["c & d", "c & d"],
        "literalTitle": ["c & d", "c & d"],
    }
    assert faults == []


def test_component_boundary_citry_event_dispatches_from_vue_child(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="component-boundary-event", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = '<button id="child-emitter" @click="emitChange">emit</button>'
        js = "$component({methods:{emitChange(){this.$emit('change', new Event('change'));}}});"

    class EventState:
        count = 0

        def render(self):
            return Parent(count=self.count)

    class Parent(Component):
        citry = engine
        template = '<output id="component-events">{{ count }}</output><c-Child @c-change="increment" />'
        State = EventState

        class Events:
            def increment(self, state: EventState):
                state.count += 1
                return state.render()

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0)}

    dispatcher_for(engine)
    faults: list[str] = []
    calls: list[dict[str, Any]] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    base = serve_live(engine, Parent(count=0).render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#component-events')?.textContent === '0'")
    page.locator("#child-emitter").click()
    page.wait_for_timeout(500)
    assert page.locator("#component-events").text_content() == "1", (faults, calls, page.content())


def test_prepared_root_markers_and_css_variables_follow_physical_roots_across_revision(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="prepared-css-roots", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = '<div id="css-child" style="color:var(--accent)">child</div>'

    class Receiver(Component):
        citry = engine
        template = "<c-slot />"

    class CssState:
        color = "rgb(0, 128, 0)"

        def render(self):
            return CssPage(color=self.color)

    class CssPage(Component):
        citry = engine
        template = (
            '<div id="css-root" style="color:var(--accent)">root<span id="css-nested">nested</span></div>'
            "<c-Child />"
            '<c-Receiver><span id="css-slot" style="color:var(--accent)">slot</span></c-Receiver>'
            '<button id="css-swap" @c-click="swap">swap</button>'
            '<button id="css-fail" @c-click="fail">fail</button>'
        )
        css = ".unused { color: var(--accent); }"
        State = CssState

        class Events:
            def swap(self, state: CssState):
                state.color = "rgb(128, 0, 128)"
                return state.render()

            def fail(self, state: CssState):
                state.color = "rgb(0, 0, 255)"
                return state.render()

        def css_data(self, kwargs, slots):
            return {"accent": kwargs["color"]}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, CssPage(color="rgb(0, 128, 0)").render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('#css-slot') && "
        "getComputedStyle(document.querySelector('#css-slot')).color === 'rgb(0, 128, 0)'"
    )

    def snapshot() -> dict[str, Any]:
        return page.evaluate(
            r"""() => {
              const ids=['css-root','css-child','css-slot'];
              return {
                colors:Object.fromEntries(ids.map(id => [id,getComputedStyle(document.getElementById(id)).color])),
                markers:Object.fromEntries(ids.map(id => [id,[...document.getElementById(id).attributes]
                  .filter(attr => attr.name.startsWith('data-ccss-')).map(attr => attr.name)])),
                nestedMarkers:[...document.getElementById('css-nested').attributes]
                  .filter(attr => attr.name.startsWith('data-ccss-')).map(attr => attr.name),
                variableSheets:[...document.querySelectorAll('style[data-citry-css-url],link[rel="stylesheet"]')]
                  .map(element => element.getAttribute('data-citry-css-url') || element.getAttribute('href'))
                  .filter(url => url && /\.[0-9a-f]{32}\.css$/.test(url)),
              };
            }"""
        )

    initial = snapshot()
    assert set(initial["colors"].values()) == {"rgb(0, 128, 0)"}
    assert all(len(value) == 1 for value in initial["markers"].values())
    assert initial["nestedMarkers"] == []
    assert len(initial["variableSheets"]) == 1
    page.locator("#css-swap").click()
    page.wait_for_function(
        "document.querySelector('#css-slot') && "
        "getComputedStyle(document.querySelector('#css-slot')).color === 'rgb(128, 0, 128)'"
    )
    revised = snapshot()
    assert set(revised["colors"].values()) == {"rgb(128, 0, 128)"}, (faults, revised, page.content())
    assert all(len(value) == 1 for value in revised["markers"].values())
    assert revised["nestedMarkers"] == []
    assert revised["markers"] != initial["markers"]
    assert len(revised["variableSheets"]) == 1
    assert revised["variableSheets"] != initial["variableSheets"]
    assert faults == []

    page.route(re.compile(r"\.css(?:\?.*)?$"), lambda route: route.fulfill(status=503, body="unavailable"))
    with page.expect_response(lambda response: response.url.endswith(".css") and response.status == 503) as info:
        page.locator("#css-fail").click()
    failed_url = info.value.url
    page.wait_for_function(
        "url => ![...document.querySelectorAll('link[rel=stylesheet]')].some(link => link.href === url)",
        arg=failed_url,
    )
    failed = snapshot()
    assert set(failed["colors"].values()) == {"rgb(128, 0, 128)"}
    assert failed["variableSheets"] == revised["variableSheets"]
