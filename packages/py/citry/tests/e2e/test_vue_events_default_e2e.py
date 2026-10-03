from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import pytest

from citry import Citry, Component, Extension
from citry._vue.serialization import hydration_admission
from citry.ext.events import EventError, actions, event
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
_PlaywrightTimeoutError = pytest.importorskip("playwright.sync_api").TimeoutError


def _pause_fake_clock(page: Any) -> None:
    # Clock calls are separate protocol commands. Choose an explicit future
    # virtual timestamp, then set Date to it before pausing at that timestamp,
    # so the target cannot become stale between the two commands.
    target = page.evaluate("new Date(Date.now() + 1_000).toISOString()")
    page.clock.set_fixed_time(target)
    page.clock.pause_at(target)


def _watch_citry_ready(page: Any) -> None:
    page.add_init_script(
        """
        window.__citryReadyApps = [];
        document.addEventListener('citry:ready', event => {
          window.__citryReadyApps.push(event.detail.appId);
        });
        """
    )


def _wait_for_citry_ready(page: Any) -> None:
    page.wait_for_function("window.__citryReadyApps?.length === 1")


def _wait_for_two_runtime_rows(page: Any, faults: list[str], console_errors: list[str], status: int | None) -> None:
    try:
        page.wait_for_selector(".runtime-row", timeout=5000)
        page.wait_for_function("document.querySelectorAll('.runtime-row').length === 2", timeout=5000)
    except _PlaywrightTimeoutError:
        page_state = page.evaluate(
            """() => ({
                body: document.body?.innerHTML,
                main: document.querySelector('main')?.outerHTML,
                buttons: document.querySelectorAll('button').length,
                ready: document.readyState,
                definitions: Object.fromEntries(Object.entries(window.__citryRuntimeDefinitions || {})
                    .map(([id, value]) => [id, {
                        directiveSignature: value.directiveSignature,
                        replacementSites: value.replacementSites,
                        localCalls: value.localCalls,
                        localCallRuns: value.localCallRuns,
                        opaqueHtmlSites: value.opaqueHtmlSites,
                        runtimeEventSites: value.runtimeEventSites,
                    }])),
                declared: (() => {
                    const block = document.querySelector(
                        'script[type="application/json"][data-citry-vue-document]',
                    );
                    if (!block) return 'no configuration block';
                    try { return JSON.parse(block.textContent).manifest.definitions; }
                    catch (error) { return String(error); }
                })(),
            })"""
        )
        pytest.fail(
            f"runtime rows did not mount; response status: {status}; page errors: {faults}; "
            f"console errors: {console_errors}; page: {page_state}"
        )


def _grouped_marker_page(engine: Citry, shape: str) -> type[Component]:
    class Payload(Component):
        citry = engine
        template = '<output class="group-payload" c-id="output_id">{{ value }}</output>'
        css = ".group-payload { color: rgb(12, 34, 56); }"

        def template_data(self, kwargs, slots):
            return kwargs

    class UnstyledPayload(Component):
        citry = engine
        template = '<output c-id="output_id">{{ value }}</output>'

        def template_data(self, kwargs, slots):
            return kwargs

    class GroupState:
        count: int = 0

    if shape == "overlap":
        markers = (
            '<c-mark name="outer"><section id="outer-value">outer-0'
            '<c-mark name="inner"><output id="inner-value">inner-0</output></c-mark>'
            "</section></c-mark>"
        )
        left_name, right_name = "outer", "inner"
    else:
        markers = (
            '<c-mark name="left"><output id="left-value">left-0</output></c-mark>'
            '<c-mark name="right"><output id="right-value">right-0</output></c-mark>'
        )
        left_name, right_name = "left", "right"

    class GroupPage(Component):
        citry = engine
        State = GroupState
        js = """$component({onServerRender({revision}){
          (globalThis.__groupLifecycle ||= []).push(['run', revision]);
          return ()=>globalThis.__groupLifecycle.push(['cleanup', revision]);
        }});"""

        template = (
            '<main><button id="group-refresh" @c-click="refresh">refresh</button>'
            + markers
            + '<c-i18n c-client="True" tag="aside">'
            '<output id="group-locale" v-text="$i18n.context.locale"></output>'
            "</c-i18n></main>"
        )

        class Events:
            def refresh(self, state: GroupState):
                state.count += 1
                value = state.count
                if shape == "success" and value == 4:
                    return actions.Render(
                        UnstyledPayload(output_id="left-value", value=f"left-{value}"),
                        target=f"mark:{left_name}",
                    )
                left = actions.Render(
                    Payload(output_id=f"{left_name}-value", value=f"left-{value}"),
                    target=f"mark:{left_name}",
                )
                right = actions.Render(
                    Payload(output_id=f"{right_name}-value", value=f"right-{value}"),
                    target=f"mark:{right_name}",
                )
                if shape == "overlap":
                    return [left, right]
                if shape == "interleaved":
                    return [
                        actions.Dispatch("pair:observe", {"phase": "before"}),
                        left,
                        actions.Dispatch("pair:observe", {"phase": "middle"}),
                        right,
                        actions.Dispatch("pair:observe", {"phase": "after"}),
                    ]
                if shape == "deferred":
                    return [
                        actions.Dispatch("pair:observe", {"phase": "before"}),
                        left,
                        actions.Render(
                            right.element,
                            target=right.target,
                            wait=False,
                        ),
                        actions.Dispatch("pair:observe", {"phase": "after"}),
                    ]
                return [
                    actions.Dispatch("pair:observe", {"phase": "before"}),
                    left,
                    right,
                    actions.Dispatch("pair:observe", {"phase": "after"}),
                ]

    return GroupPage


def _grouped_marker_state(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const app=[...__citryRuntime._apps.values()][0];
          const occurrence=app?.occurrences.get(app.rootId);
          const component=app?.mounted.get(app.rootId)?.component;
          const read=id=>document.querySelector(`#${id}`)?.textContent ?? null;
          const color=id=>{const node=document.querySelector(`#${id}`);return node?getComputedStyle(node).color:null;};
          return {token:occurrence?.eventContext?.stateToken,
            revision:app?.revision, plugins:app?.browserPlugins?.length, busy:app?.busy,
            loading:component?.$loading('refresh'), lifecycle:globalThis.__groupLifecycle || [],
            left:read('left-value'), right:read('right-value'),
            leftColor:color('left-value'), rightColor:color('right-value'),
            ownedStyles:document.querySelectorAll('[data-citry-vue-style-app][data-citry-css-url]').length,
            outer:read('outer-value'), inner:read('inner-value'),
            html:document.querySelector('main')?.innerHTML ?? null};
        }"""
    )


@pytest.mark.e2e
def test_public_events_renderer_mounts_and_applies_a_real_render(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-public-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class CounterState:
        count: int = 0

        def render(self):
            return Counter(count=self.count)

    class Counter(Component):
        citry = engine
        template = '<button id="counter" @c-click="increment">{{ count }}</button>'

        State = CounterState

        class Events:
            def increment(self, state: CounterState):
                state.count += 1
                return state.render()

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0)}

    dispatcher_for(engine)
    html = Counter(count=0).render().serialize()
    faults: list[str] = []
    console: list[str] = []
    calls: list[dict[str, Any]] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text))
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    page.wait_for_timeout(500)
    assert page.locator("#counter").count() == 1, (faults, page.content())
    assert page.locator("#counter").text_content() == "0"
    page.locator("#counter").click()
    page.wait_for_function("document.querySelector('#counter')?.textContent === '1'")
    page.locator("#counter").click()
    page.wait_for_function("document.querySelector('#counter')?.textContent === '2'")
    assert len(calls) == 2
    assert calls[0]["calls"][0]["stateToken"] != calls[1]["calls"][0]["stateToken"]
    assert faults == []


@pytest.mark.e2e
def test_vue_events_callback_subscriptions_and_root_lifecycle_do_not_stale_or_stack(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="vue-events-public-compat-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Page(Component):
        citry = engine
        State = PageState
        template = '<main><button id="refresh" @c-click="refresh">{{ count }}</button></main>'
        # `$onEvent` inside the run and the run's own `onEvent` are both released
        # with the run, and the returned cleanup runs before the next run starts.
        js = """$component({onServerRender({component, revision, onEvent}){
          (globalThis.__vueCallbackTimeline ||= []).push(['run', revision]);
          component.$onEvent('ping', detail => (globalThis.__vueEventSeen ||= []).push({revision, detail}));
          const stop = onEvent('ping', detail => {
            globalThis.__vueCallbackTimeline.push(['event', revision, detail]);
          });
          return ()=>{
            stop();
            globalThis.__vueCallbackTimeline.push(['cleanup', revision]);
          };
        }});"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return [state.render(), actions.Dispatch("ping", {"count": state.count})]

    dispatcher_for(engine)
    page_errors: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.add_init_script(
        """
        window.__vueEventLifecycle = [];
        for (const name of ['before', 'swapped', 'after'])
          document.addEventListener(`citry:events:${name}`, event =>
            window.__vueEventLifecycle.push({name, detail: event.detail, els: event.detail?.els?.length ?? null}));
        """
    )
    page.goto(serve_live(engine, Page(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '0'")

    applied = page.evaluate(
        """async () => {
          let detail = null;
          const stop = Citry.events.on('public-ping', value => { detail = value; });
          const data = await Citry.events.applyActions([
            {action: 'event', eventName: 'public-ping', detail: {source: 'global'}},
            {action: 'data', value: 9},
          ]);
          stop();
          return {data, detail};
        }"""
    )
    assert applied == {"data": 9, "detail": {"source": "global"}}

    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '1'")
    try:
        page.wait_for_function("globalThis.__vueEventSeen?.length === 1")
    except _PlaywrightTimeoutError as error:
        pytest.fail(
            f"first event subscription did not fire: {error}; seen={page.evaluate('globalThis.__vueEventSeen')}; "
            f"lifecycle={page.evaluate('globalThis.__vueEventLifecycle')}; page_errors={page_errors}; "
            f"console_errors={console_errors}",
            pytrace=False,
        )
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '2'")
    page.wait_for_function("globalThis.__vueEventSeen?.length === 2")

    assert page.evaluate("globalThis.__vueEventSeen") == [
        {"revision": 1, "detail": {"count": 1}},
        {"revision": 2, "detail": {"count": 2}},
    ]
    assert page.evaluate("globalThis.__vueCallbackTimeline") == [
        ["run", 0],
        ["cleanup", 0],
        ["run", 1],
        ["event", 1, {"count": 1}],
        ["cleanup", 1],
        ["run", 2],
        ["event", 2, {"count": 2}],
    ]
    lifecycle = page.evaluate("globalThis.__vueEventLifecycle")
    assert [entry["name"] for entry in lifecycle] == [
        "before",
        "swapped",
        "after",
        "before",
        "swapped",
        "after",
    ]
    for entry in lifecycle:
        assert entry["detail"]["event"] == "refresh"
        assert entry["detail"]["class"]
        assert entry["detail"]["instance"]
    assert all(entry["els"] is not None and entry["els"] > 0 for entry in lifecycle if entry["name"] == "swapped")


@pytest.mark.e2e
def test_custom_transport_forwards_request_context_for_a_render(page: Any, serve_live: Any) -> None:
    # A custom transport that relays the envelope with the request it is given
    # must be able to receive a Render of the component on screen, which the
    # server can only build from the Vue app, occurrence and revision headers.
    engine = Citry(secret="vue-events-custom-transport-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Page(Component):
        citry = engine
        State = PageState
        template = '<main><button id="refresh" @c-click="refresh">{{ count }}</button></main>'

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return state.render()

    dispatcher_for(engine)
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_live(engine, Page(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '0'")
    page.evaluate(
        """() => {
          window.__relayed = [];
          Citry.events.registerTransport('relay', {
            async send(envelope, request) {
              window.__relayed.push({
                method: request.method,
                vueHeaders: Object.keys(request.headers).filter(name => name.startsWith('X-Citry-Vue-')).sort(),
                signal: request.signal instanceof AbortSignal,
              });
              const response = await fetch(request.url, {
                method: request.method,
                headers: request.headers,
                body: JSON.stringify(envelope),
                signal: request.signal,
              });
              return response.json();
            },
          });
          Citry.events.configure({transport: 'relay'});
        }"""
    )

    for count in (1, 2):
        page.locator("#refresh").click()
        page.wait_for_function(f"document.querySelector('#refresh')?.textContent === '{count}'")

    assert (
        page.evaluate("window.__relayed")
        == [
            {
                "method": "POST",
                "vueHeaders": ["X-Citry-Vue-App", "X-Citry-Vue-Occurrence", "X-Citry-Vue-Revision"],
                "signal": True,
            },
        ]
        * 2
    )
    assert page_errors == []


@pytest.mark.e2e
def test_instance_on_event_listeners_outlive_server_renders(page: Any, serve_live: Any) -> None:
    # Only a listener added while onServerRender runs (its `onEvent`, or
    # `$onEvent` called synchronously inside it) is released with that run.
    # One added later from a hook, method or timer lives as long as the
    # instance, and an `onEvent` from a run that already ended adds nothing.
    engine = Citry(secret="vue-events-instance-listener-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Page(Component):
        citry = engine
        State = PageState
        template = '<main><button id="refresh" @c-click="refresh">{{ count }}</button></main>'
        js = """$component({
          mounted() {
            this.$onEvent('ping', detail => (globalThis.__mountedSeen ||= []).push(detail.count));
          },
          onServerRender({component, revision, onEvent}) {
            (globalThis.__runOnEvents ||= []).push(onEvent);
            onEvent('ping', detail => (globalThis.__runSeen ||= []).push({revision, count: detail.count}));
            if (revision === 0) {
              queueMicrotask(() => component.$onEvent(
                'ping', detail => (globalThis.__laterSeen ||= []).push(detail.count)));
            }
          },
        });"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return [state.render(), actions.Dispatch("ping", {"count": state.count})]

    dispatcher_for(engine)
    page_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(serve_live(engine, Page(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '0'")

    for count in (1, 2):
        page.locator("#refresh").click()
        page.wait_for_function(f"document.querySelector('#refresh')?.textContent === '{count}'")
        page.wait_for_function(f"globalThis.__runSeen?.length === {count}")

    # A late call through the first run's onEvent must not subscribe.
    page.evaluate("globalThis.__runOnEvents[0]('ping', () => (globalThis.__staleSeen ||= []).push(1))")
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '3'")
    page.wait_for_function("globalThis.__runSeen?.length === 3")

    assert page.evaluate("globalThis.__mountedSeen") == [1, 2, 3]
    assert page.evaluate("globalThis.__laterSeen") == [1, 2, 3]
    assert page.evaluate("globalThis.__runSeen") == [
        {"revision": 1, "count": 1},
        {"revision": 2, "count": 2},
        {"revision": 3, "count": 3},
    ]
    assert page.evaluate("globalThis.__staleSeen ?? null") is None
    assert page_errors == []


@pytest.mark.e2e
def test_marker_render_repeats_owner_callback_and_cleans_previous_scope_once(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-marker-callback-cleanup-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Payload(Component):
        citry = engine
        template = '<output id="marker-value">{{ value }}</output>'

        def template_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

    class PageState:
        count: int = 0

    class Page(Component):
        citry = engine
        template = (
            '<main><button id="refresh" @c-click="refresh">refresh</button>'
            '<c-mark name="summary"><output id="marker-value">initial</output></c-mark></main>'
        )
        js = """$component({onServerRender({revision}){
          (globalThis.__markerLifecycle ||= []).push(['run', revision]);
          return ()=>globalThis.__markerLifecycle.push(['cleanup', revision]);
        }});"""
        State = PageState

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return actions.Render(Payload(value=state.count), target="mark:summary")

    dispatcher_for(engine)
    faults: list[str] = []
    console_errors: list[str] = []
    calls: list[dict[str, Any] | None] = []
    responses: list[tuple[int, str, str]] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    page.on(
        "response",
        lambda response: responses.append((response.status, response.url, response.text()))
        if response.url.endswith("/ext/events/call")
        else None,
    )
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.wait_for_function("globalThis.__markerLifecycle?.length === 1")
    assert page.evaluate("globalThis.__markerLifecycle") == [["run", 0]]

    def wait_for_event_idle() -> None:
        try:
            page.wait_for_function(
                """() => {
                  const app=[...__citryRuntime._apps.values()][0];
                  const component=app?.mounted.get(app.rootId)?.component;
                  return Boolean(component) && !app.busy && !component.$loading('refresh');
                }""",
                timeout=5_000,
            )
        except _PlaywrightTimeoutError as error:
            state = page.evaluate(
                """() => {
                  const app=[...__citryRuntime._apps.values()][0];
                  const component=app?.mounted.get(app.rootId)?.component;
                  const occurrence=app?.occurrences.get(app.rootId);
                  let loading, loadingError;
                  try { loading=component?.$loading('refresh'); } catch(error) { loadingError=String(error); }
                  return {busy:app?.busy, count:component?.$state.count, loading, loadingError,
                    revision:app?.revision, stateToken:occurrence?.eventContext?.stateToken,
                    lifecycle:globalThis.__markerLifecycle};
                }"""
            )
            pytest.fail(
                f"marker event did not become idle: {error}; state={state}; calls={calls}; responses={responses}",
                pytrace=False,
            )

    page.locator("#refresh").click()
    try:
        page.wait_for_function(
            "document.querySelector('#marker-value')?.textContent === '1' && "
            "globalThis.__markerLifecycle?.length === 3",
            timeout=5_000,
        )
    except _PlaywrightTimeoutError as error:
        page_state = page.evaluate(
            """() => ({text:document.querySelector('#marker-value')?.textContent,
            lifecycle:globalThis.__markerLifecycle, html:document.querySelector('main')?.outerHTML,
            appCount:globalThis.__citryRuntime?._apps?.size})"""
        )
        pytest.fail(
            f"marker update did not apply: {error}; state={page_state}; faults={faults}; "
            f"console={console_errors}; calls={calls}; responses={responses}",
            pytrace=False,
        )
    assert page.evaluate("globalThis.__markerLifecycle") == [["run", 0], ["cleanup", 0], ["run", 1]]
    wait_for_event_idle()

    page.locator("#refresh").click()
    try:
        page.wait_for_function(
            "document.querySelector('#marker-value')?.textContent === '2' && "
            "globalThis.__markerLifecycle?.length === 5",
            timeout=5_000,
        )
    except _PlaywrightTimeoutError as error:
        page_state = page.evaluate(
            """() => ({text:document.querySelector('#marker-value')?.textContent,
            lifecycle:globalThis.__markerLifecycle, html:document.querySelector('main')?.outerHTML,
            appCount:globalThis.__citryRuntime?._apps?.size})"""
        )
        pytest.fail(
            f"second marker update did not apply: {error}; state={page_state}; faults={faults}; "
            f"console={console_errors}; calls={calls}; responses={responses}",
            pytrace=False,
        )
    wait_for_event_idle()

    assert page.evaluate("globalThis.__markerLifecycle") == [
        ["run", 0],
        ["cleanup", 0],
        ["run", 1],
        ["cleanup", 1],
        ["run", 2],
    ]
    assert calls[0]["calls"][0]["stateToken"] != calls[1]["calls"][0]["stateToken"]
    assert faults == []


@pytest.mark.e2e
def test_disjoint_marker_group_commits_together_and_deduplicates_owner_work(page: Any, serve_live: Any) -> None:
    engine = Citry(
        secret="vue-marker-group-commit-secret",  # noqa: S106
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    engine.set_mounted_prefix("/citry")
    group_page = _grouped_marker_page(engine, "success")
    dispatcher_for(engine)

    calls: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    faults: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    page.on(
        "response",
        lambda response: responses.append(response.json()) if response.url.endswith("/ext/events/call") else None,
    )
    page.add_init_script(
        """globalThis.__pairObservations=[];
        document.addEventListener('pair:observe',event=>{
          globalThis.__pairObservations.push({phase:event.detail.phase,
            left:document.querySelector('#left-value')?.textContent ?? null,
            right:document.querySelector('#right-value')?.textContent ?? null});
        });"""
    )
    page.goto(serve_live(engine, group_page().render().serialize(), "") + "/")
    page.wait_for_function(
        """() => { const app=[...__citryRuntime._apps.values()][0];
          return app?.browserPlugins?.length === 1 &&
            document.querySelector('#group-locale')?.textContent === 'en-US' &&
            globalThis.__groupLifecycle?.length === 1; }""",
        timeout=5_000,
    )
    initial = _grouped_marker_state(page)
    assert (initial["left"], initial["right"], initial["revision"]) == ("left-0", "right-0", 0)
    assert initial["token"]
    assert initial["plugins"] == 1

    def wait_for_group(value: int, observations: int, lifecycle: int) -> None:
        try:
            page.wait_for_function(
                """expected => document.querySelector('#left-value')?.textContent === `left-${expected.value}` &&
                  document.querySelector('#right-value')?.textContent === `right-${expected.value}` &&
                  getComputedStyle(document.querySelector('#left-value')).color === 'rgb(12, 34, 56)' &&
                  getComputedStyle(document.querySelector('#right-value')).color === 'rgb(12, 34, 56)' &&
                  globalThis.__pairObservations?.length === expected.observations &&
                  globalThis.__groupLifecycle?.length === expected.lifecycle""",
                arg={"value": value, "observations": observations, "lifecycle": lifecycle},
                timeout=5_000,
            )
            page.wait_for_function(
                """() => { const app=[...__citryRuntime._apps.values()][0];
                  const component=app?.mounted.get(app.rootId)?.component;
                  return Boolean(app) && !app.busy && !component?.$loading('refresh'); }""",
                timeout=5_000,
            )
        except _PlaywrightTimeoutError as error:
            pytest.fail(
                f"marker group {value} did not settle: {error}; state={_grouped_marker_state(page)}; "
                f"observations={page.evaluate('globalThis.__pairObservations')}; calls={calls}; "
                f"responses={responses}; faults={faults}; console={console_errors}",
                pytrace=False,
            )

    page.locator("#group-refresh").click()
    wait_for_group(1, 2, 3)
    page.locator("#group-refresh").click()
    wait_for_group(2, 4, 5)
    page.locator("#group-refresh").click()
    wait_for_group(3, 6, 7)

    assert _grouped_marker_state(page)["ownedStyles"] == 1
    page.locator("#group-refresh").click()
    try:
        page.wait_for_function(
            "document.querySelector('#left-value')?.textContent === 'left-4' && "
            "document.querySelector('#right-value')?.textContent === 'right-3' && "
            "getComputedStyle(document.querySelector('#right-value')).color === 'rgb(12, 34, 56)' && "
            "document.querySelectorAll('[data-citry-vue-style-app][data-citry-css-url]').length === 1 && "
            "globalThis.__groupLifecycle?.length === 9",
            timeout=5_000,
        )
        page.wait_for_function(
            """() => { const app=[...__citryRuntime._apps.values()][0];
              const component=app?.mounted.get(app.rootId)?.component;
              return Boolean(app) && !app.busy && !component?.$loading('refresh'); }""",
            timeout=5_000,
        )
    except _PlaywrightTimeoutError as error:
        pytest.fail(
            f"single-marker replacement lost the sibling stylesheet owner: {error}; "
            f"state={_grouped_marker_state(page)}; calls={calls}; responses={responses}; "
            f"faults={faults}; console={console_errors}",
            pytrace=False,
        )
    assert _grouped_marker_state(page)["ownedStyles"] == 1

    assert page.evaluate("globalThis.__pairObservations") == [
        {"phase": "before", "left": "left-0", "right": "right-0"},
        {"phase": "after", "left": "left-1", "right": "right-1"},
        {"phase": "before", "left": "left-1", "right": "right-1"},
        {"phase": "after", "left": "left-2", "right": "right-2"},
        {"phase": "before", "left": "left-2", "right": "right-2"},
        {"phase": "after", "left": "left-3", "right": "right-3"},
    ]
    assert page.evaluate("globalThis.__groupLifecycle") == [
        ["run", 0],
        ["cleanup", 0],
        ["run", 1],
        ["cleanup", 1],
        ["run", 2],
        ["cleanup", 2],
        ["run", 3],
        ["cleanup", 3],
        ["run", 4],
    ]
    request_tokens = [call["calls"][0]["stateToken"] for call in calls]
    state_tokens = [
        next(action["stateToken"] for action in response["results"][0]["actions"] if action["action"] == "state")
        for response in responses
    ]
    assert request_tokens == [initial["token"], state_tokens[0], state_tokens[1], state_tokens[2]]
    assert state_tokens[0] != request_tokens[0]
    assert state_tokens[1] != state_tokens[0]
    assert state_tokens[2] != state_tokens[1]
    assert state_tokens[3] != state_tokens[2]
    final_state = _grouped_marker_state(page)
    assert final_state["revision"] == 4
    assert final_state["leftColor"] != "rgb(12, 34, 56)"
    assert final_state["rightColor"] == "rgb(12, 34, 56)"
    for response in responses[:3]:
        result_actions = response["results"][0]["actions"]
        render_indexes = [index for index, item in enumerate(result_actions) if item["action"] == "render"]
        assert len(render_indexes) == 2
        assert render_indexes[1] == render_indexes[0] + 1
        assert [result_actions[index]["target"].rsplit(":", 1)[-1] for index in render_indexes] == ["left", "right"]
    last_actions = responses[3]["results"][0]["actions"]
    last_renders = [item for item in last_actions if item["action"] == "render"]
    assert len(last_renders) == 1
    assert last_renders[0]["target"].endswith(":left")
    assert faults == []
    assert console_errors == []


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("malformed-second", "stale or malformed envelope"),
        ("stale-second", "stale or malformed envelope"),
        ("foreign-app", "stale or malformed envelope"),
        ("definition-conflict", "prepared definitions identity conflicts across Render targets"),
        ("duplicate-target", "multiple prepared Render actions target the same occurrence"),
        ("overlap", "prepared Render targets overlap"),
        ("interleaved", "multiple prepared Render actions must be one immediate blocking contiguous group"),
        ("deferred", "multiple prepared Render actions must be one immediate blocking contiguous group"),
    ],
)
def test_marker_group_rejections_leave_state_and_dom_uncommitted(
    page: Any, serve_live: Any, failure: str, message: str
) -> None:
    shape = failure if failure in {"overlap", "interleaved", "deferred"} else "success"
    engine = Citry(
        secret=f"vue-marker-group-{failure}-secret",
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    engine.set_mounted_prefix("/citry")
    group_page = _grouped_marker_page(engine, shape)
    dispatcher_for(engine)

    calls: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    page_errors: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.on("console", lambda event: console_errors.append(event.text) if event.type == "error" else None)
    page.on(
        "request",
        lambda request: calls.append(request.post_data_json) if request.url.endswith("/ext/events/call") else None,
    )
    page.on(
        "response",
        lambda response: responses.append(response.json()) if response.url.endswith("/ext/events/call") else None,
    )
    page.add_init_script(
        """globalThis.__groupErrors=[];globalThis.__pairObservations=[];
        document.addEventListener('pair:observe',event=>globalThis.__pairObservations.push(event.detail.phase));
        addEventListener('error',event=>globalThis.__groupErrors.push(String(event.error||event.message)));
        addEventListener('unhandledrejection',event=>{
          globalThis.__groupErrors.push(String(event.reason?.message||event.reason));event.preventDefault();
        });"""
    )

    if failure in {
        "malformed-second",
        "stale-second",
        "foreign-app",
        "definition-conflict",
        "duplicate-target",
    }:

        def corrupt_second(route: Any) -> None:
            response = route.fetch()
            payload = response.json()
            render_actions = [action for action in payload["results"][0]["actions"] if action["action"] == "render"]
            assert len(render_actions) == 2
            second_envelope = render_actions[1]["prepared"]
            if failure == "malformed-second":
                second_envelope.pop("markers", None)
            elif failure == "stale-second":
                second_envelope["baseRevision"] = -1
            elif failure == "foreign-app":
                second_envelope["appId"] = "foreign-app"
            elif failure == "definition-conflict":
                first_definitions = render_actions[0]["prepared"]["definitions"]
                second_definitions = render_actions[1]["prepared"]["definitions"]
                second_by_id = {definition["id"]: definition for definition in second_definitions}
                shared_id = next(
                    definition["id"] for definition in first_definitions if definition["id"] in second_by_id
                )
                digest = second_by_id[shared_id]["sha256"]
                second_by_id[shared_id]["sha256"] = ("0" if digest[0] != "0" else "1") + digest[1:]
            else:
                render_actions[1]["target"] = render_actions[0]["target"]
            route.fulfill(
                status=response.status,
                headers=response.headers,
                body=json.dumps(payload),
                content_type="application/citry-events+json",
            )

        page.route("**/ext/events/call", corrupt_second)

    page.goto(serve_live(engine, group_page().render().serialize(), "") + "/")
    page.wait_for_function("globalThis.__groupLifecycle?.length === 1", timeout=5_000)
    initial = _grouped_marker_state(page)
    assert initial["token"]
    assert initial["revision"] == 0
    initial_html = initial["html"]

    with page.expect_request("**/ext/events/call"):
        page.locator("#group-refresh").click()
    try:
        page.wait_for_function(
            "message => globalThis.__groupErrors?.some(value => value.includes(message))",
            arg=message,
            timeout=5_000,
        )
    except _PlaywrightTimeoutError as error:
        pytest.fail(
            f"{failure} marker group was not rejected: {error}; state={_grouped_marker_state(page)}; "
            f"groupErrors={page.evaluate('globalThis.__groupErrors')}; calls={calls}; responses={responses}; "
            f"page_errors={page_errors}; console={console_errors}",
            pytrace=False,
        )

    page.wait_for_function(
        """() => { const app=[...__citryRuntime._apps.values()][0];
          const component=app?.mounted.get(app.rootId)?.component;
          return Boolean(app) && !app.busy && !component?.$loading('refresh'); }""",
        timeout=5_000,
    )
    after = _grouped_marker_state(page)
    assert len(calls) == 1
    assert len(responses) == 1
    response_actions = responses[0]["results"][0]["actions"]
    response_state_token = next(action["stateToken"] for action in response_actions if action["action"] == "state")
    assert response_state_token != initial["token"]
    assert after["revision"] == initial["revision"]
    assert after["html"] == initial_html
    assert after["lifecycle"] == [["run", 0]]
    assert page.evaluate("globalThis.__pairObservations") == []
    assert any(message in item for item in page.evaluate("globalThis.__groupErrors"))

    with page.expect_request("**/ext/events/call"):
        page.locator("#group-refresh").click()
    try:
        page.wait_for_function(
            "message => globalThis.__groupErrors?.filter(value => value.includes(message)).length >= 2",
            arg=message,
            timeout=5_000,
        )
    except _PlaywrightTimeoutError as error:
        pytest.fail(
            f"rejected {failure} group did not leave the owner usable: {error}; "
            f"state={_grouped_marker_state(page)}; groupErrors={page.evaluate('globalThis.__groupErrors')}; "
            f"calls={calls}; responses={responses}; page_errors={page_errors}; console={console_errors}",
            pytrace=False,
        )
    page.wait_for_function(
        """() => { const app=[...__citryRuntime._apps.values()][0];
          const component=app?.mounted.get(app.rootId)?.component;
          return Boolean(app) && !app.busy && !component?.$loading('refresh'); }""",
        timeout=5_000,
    )
    assert len(calls) == 2
    assert len(responses) == 2
    assert [call["calls"][0]["stateToken"] for call in calls] == [initial["token"], initial["token"]]
    assert _grouped_marker_state(page)["html"] == initial_html
    assert _grouped_marker_state(page)["revision"] == initial["revision"]


@pytest.mark.e2e
def test_same_type_render_can_target_a_mounted_sibling(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-sibling-target-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    target_render_id = ""

    class Panel(Component):
        citry = engine
        template = '<button c-id="dom_id" @c-click="refresh">{{ label }}</button>'

        class Events:
            def refresh(self):
                return actions.Render(
                    Panel(dom_id="right", label="updated"),
                    target=f"render:{target_render_id}",
                )

        def template_data(self, kwargs, slots):
            nonlocal target_render_id
            if kwargs.get("dom_id") == "right" and kwargs.get("label") == "right":
                target_render_id = self.id
            return kwargs

    left = Panel(dom_id="left", label="left")
    right = Panel(dom_id="right", label="right")

    class Page(Component):
        citry = engine
        template = "<main>{{ left }}{{ right }}</main>"

        def template_data(self, kwargs, slots):
            return {"left": left, "right": right}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    page.locator("#left").click()
    page.wait_for_function("document.querySelector('#right')?.textContent === 'updated'")

    assert page.locator("#left").text_content() == "left"
    assert page.locator("#right").text_content() == "updated"
    assert faults == []


@pytest.mark.e2e
def test_events_render_targets_reorder_and_remove_keyed_v_model_children(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-passive-target-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    target_render_id = ""
    render_ids: list[tuple[tuple[str, ...], str]] = []

    class Row(Component):
        citry = engine
        template = """
            <label c-data-key="value">
                <input v-model="local">
                <output class="local-value" v-text="local"></output>
            </label>
        """
        js = "$component({data(){return {local: this.value}}});"

        def js_data(self, kwargs, slots):
            return {"value": kwargs["value"]}

        def template_data(self, kwargs, slots):
            return kwargs

    class Rows(Component):
        citry = engine
        template = """
            <section id="rows">
                <c-for each="value in values">
                    <c-Row #c-key="value" c-value="value" />
                </c-for>
            </section>
        """
        js = """
            $component({
                updated() {
                    if (!globalThis.__focusAwayDuringRender) return;
                    globalThis.__focusAwayDuringRender = false;
                    document.querySelector('#focus-sentinel')?.focus();
                },
            });
        """

        def template_data(self, kwargs, slots):
            nonlocal target_render_id
            values = tuple(kwargs.get("values", ()))
            render_ids.append((values, self.id))
            target_render_id = self.id
            return kwargs

    class Controller(Component):
        citry = engine
        template = """
            <div>
                <button id="reorder" @c-click="refresh">reorder</button>
                <button id="remove-a" @c-click="remove_a">remove a</button>
                <button id="focus-sentinel" type="button">focus sentinel</button>
            </div>
        """

        class Events:
            def refresh(self):
                return actions.Render(Rows(values=["b", "a"]), target=f"render:{target_render_id}")

            def remove_a(self):
                return actions.Render(Rows(values=["b"]), target=f"render:{target_render_id}")

    target = Rows(values=["a", "b"])

    class Page(Component):
        citry = engine
        template = """
            <main>{{ controller }}{{ target }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"controller": Controller(), "target": target}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(), "") + "/")
    for key in ("a", "b"):
        page.locator(f'[data-key="{key}"] input').fill(f"local-{key}")
        page.wait_for_function(
            '({key, value}) => document.querySelector(`[data-key="${key}"] .local-value`)?.textContent === value',
            arg={"key": key, "value": f"local-{key}"},
        )
    page.evaluate("""() => {
      globalThis.__keyedRows = Object.fromEntries(
        [...document.querySelectorAll('#rows label')].map(label => {
          const input = label.querySelector('input');
          return [label.dataset.key, {input, instance: input.__vueParentComponent}];
        }),
      );
    }""")
    page.locator("#reorder").click()
    page.wait_for_function(
        "() => [...document.querySelectorAll('#rows label')].map(label => label.dataset.key).join(',') === 'b,a'"
    )
    page.wait_for_function("[...__citryRuntime._apps.values()][0].revision === 1", timeout=5000)
    assert [page.locator("#rows label").nth(index).get_attribute("data-key") for index in range(2)] == ["b", "a"]
    assert [page.locator(f'[data-key="{key}"] input').input_value() for key in ("a", "b")] == [
        "local-a",
        "local-b",
    ]
    assert (
        page.evaluate("""() => ['a', 'b'].every(key => {
      const input = document.querySelector(`[data-key="${key}"] input`);
      return input === globalThis.__keyedRows[key].input
        && input.__vueParentComponent === globalThis.__keyedRows[key].instance;
    })""")
        is True
    )

    page.evaluate(
        """() => {
          const input = document.querySelector('[data-key="a"] input');
          input.focus();
          input.setSelectionRange(2, 6, 'backward');
          document.querySelector('#reorder').dispatchEvent(new MouseEvent('click', {bubbles: true}));
        }"""
    )
    page.wait_for_function(
        "[...__citryRuntime._apps.values()][0].revision === 2 && ![...__citryRuntime._apps.values()][0].busy",
        timeout=5000,
    )
    focus_state = page.evaluate(
        """() => {
          const input = globalThis.__keyedRows.a.input;
          const current = document.querySelector('[data-key="a"] input');
          return {
            sameNode: current === input,
            focused: document.activeElement === current,
            start: current.selectionStart,
            end: current.selectionEnd,
            direction: current.selectionDirection,
          };
        }"""
    )
    assert focus_state == {
        "sameNode": True,
        "focused": True,
        "start": 2,
        "end": 6,
        "direction": "backward",
    }

    page.evaluate(
        """() => {
          document.querySelector('[data-key="a"] input').focus();
          document.querySelector('[data-key="a"] input').setSelectionRange(1, 5);
          globalThis.__focusAwayDuringRender = true;
          document.querySelector('#reorder').dispatchEvent(new MouseEvent('click', {bubbles: true}));
        }"""
    )
    page.wait_for_function(
        "[...__citryRuntime._apps.values()][0].revision === 3 && ![...__citryRuntime._apps.values()][0].busy",
        timeout=3000,
    )
    assert page.evaluate("document.activeElement?.id") == "focus-sentinel"

    page.locator("#remove-a").click()
    page.wait_for_function(
        "[...__citryRuntime._apps.values()][0].revision === 4 && ![...__citryRuntime._apps.values()][0].busy",
        timeout=5000,
    )
    try:
        page.wait_for_function(
            "() => [...document.querySelectorAll('#rows label')].map(label => label.dataset.key).join(',') === 'b'",
            timeout=3000,
        )
    except _PlaywrightTimeoutError:
        page_state = page.evaluate(
            """() => ({
                rows: [...document.querySelectorAll('#rows label')].map(label => label.dataset.key),
                html: document.querySelector('#rows')?.innerHTML,
            })"""
        )
        pytest.fail(f"render ids: {render_ids}; page errors: {faults}; page state: {page_state}")
    assert page.locator('[data-key="a"]').count() == 0
    assert page.locator('[data-key="b"] input').input_value() == "local-b"
    assert (
        page.evaluate("""() => !globalThis.__keyedRows.a.input.isConnected
      && document.querySelector('[data-key="b"] input') === globalThis.__keyedRows.b.input
      && document.querySelector('[data-key="b"] input').__vueParentComponent === globalThis.__keyedRows.b.instance""")
        is True
    )
    assert faults == []


@pytest.mark.e2e
def test_template_v_for_keyed_model_nodes_reorder_and_remove(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class KeyedPlainRows(Component):
        citry = engine
        template = """
            <main>
                <button id="reverse-plain-rows" @click="reverseRows">reverse</button>
                <button id="remove-plain-a" @click="removeA">remove a</button>
                <div id="plain-rows">
                    <template v-for="row in rows" :key="row.id">
                        <input class="plain-row" :data-row="row.id" v-model="row.value">
                    </template>
                </div>
                <output id="plain-row-model" v-text="rows.map(row => row.id + ':' + row.value).join(',')"></output>
            </main>
        """
        js = """
            $component({
                data() {
                    return {rows: [
                        {id: 'a', value: 'local-a'},
                        {id: 'b', value: 'local-b'},
                    ]};
                },
                methods: {
                    reverseRows() { this.rows.reverse(); },
                    removeA() { this.rows = this.rows.filter(row => row.id !== 'a'); },
                },
            });
        """

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(KeyedPlainRows().render().serialize()))
    page.wait_for_function("document.querySelectorAll('.plain-row').length === 2")
    for row, value in (("a", "typed-a"), ("b", "typed-b")):
        page.locator(f'.plain-row[data-row="{row}"]').fill(value)
    page.wait_for_function("document.querySelector('#plain-row-model')?.textContent === 'a:typed-a,b:typed-b'")

    page.evaluate(
        """() => {
          globalThis.__plainRows = Object.fromEntries(
            [...document.querySelectorAll('.plain-row')].map(input => [input.dataset.row, input]),
          );
        }"""
    )
    page.locator("#reverse-plain-rows").click()
    page.wait_for_function(
        "() => [...document.querySelectorAll('.plain-row')].map(input => input.dataset.row).join(',') === 'b,a'"
    )
    assert [page.locator(".plain-row").nth(index).get_attribute("data-row") for index in range(2)] == ["b", "a"]
    assert page.locator('.plain-row[data-row="a"]').input_value() == "typed-a"
    assert page.locator('.plain-row[data-row="b"]').input_value() == "typed-b"
    assert page.locator("#plain-row-model").text_content() == "b:typed-b,a:typed-a"
    page.locator('.plain-row[data-row="a"]').fill("after-a")
    page.wait_for_function("document.querySelector('#plain-row-model')?.textContent === 'b:typed-b,a:after-a'")
    assert (
        page.evaluate(
            """() => ['a', 'b'].every(row =>
              document.querySelector(`.plain-row[data-row="${row}"]`) === globalThis.__plainRows[row])"""
        )
        is True
    )

    page.locator("#remove-plain-a").click()
    page.wait_for_function(
        "() => [...document.querySelectorAll('.plain-row')].map(input => input.dataset.row).join(',') === 'b'"
    )
    assert page.locator('.plain-row[data-row="a"]').count() == 0
    assert page.locator('.plain-row[data-row="b"]').input_value() == "typed-b"
    assert (
        page.evaluate(
            """() => !globalThis.__plainRows.a.isConnected
              && document.querySelector('.plain-row[data-row="b"]') === globalThis.__plainRows.b"""
        )
        is True
    )
    assert faults == []


@pytest.mark.e2e
def test_accepted_ancestor_render_can_retire_event_caller(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-ancestor-target-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    ancestor_render_id = ""

    class Branch(Component):
        citry = engine
        template = '<section c-id="dom_id"><span class="status">{{ label }}</span>{{ child }}</section>'

        def template_data(self, kwargs, slots):
            nonlocal ancestor_render_id
            if kwargs.get("label") == "old":
                ancestor_render_id = self.id
            return kwargs

    class Caller(Component):
        citry = engine
        template = '<button id="replace-ancestor" @c-click="replace_ancestor">replace</button>'

        class Events:
            def replace_ancestor(self):
                return actions.Render(
                    Branch(dom_id="ancestor", label="done", child=None),
                    target=f"render:{ancestor_render_id}",
                )

    child = Caller()
    ancestor = Branch(dom_id="ancestor", label="old", child=child)
    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, ancestor.render().serialize(), "") + "/")
    page.locator("#replace-ancestor").click()
    page.wait_for_function("document.querySelector('#ancestor .status')?.textContent === 'done'")

    assert page.locator("#replace-ancestor").count() == 0
    assert page.locator("#ancestor .status").text_content() == "done"
    assert faults == []


@pytest.mark.e2e
def test_unmounted_component_js_app_runs_without_events_routes(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class LocalCounter(Component):
        citry = engine
        template = '<button id="local-counter" @click="local += 1" v-text="local"></button>'
        js = "$component({data(){return {local: 0};}});"

    html = LocalCounter().render().serialize()
    assert "ext/events/call" not in html
    assert "data-citry-vue-document" in html
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(html))
    page.wait_for_timeout(500)
    assert page.locator("#local-counter").text_content() == "0", (
        faults,
        page.locator("#local-counter").evaluate("el => el.__vueParentComponent?.proxy?.$data"),
        page.content(),
    )
    page.locator("#local-counter").click()
    page.wait_for_function("document.querySelector('#local-counter')?.textContent === '1'")
    assert page.locator("#local-counter").text_content() == "1"
    assert faults == []


@pytest.mark.e2e
def test_imperative_send_preserves_structured_event_error_for_caller(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-imperative-error-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Form(Component):
        citry = engine
        template = '<button id="imperative-error" @click="submit">submit</button>'
        js = """$component({methods:{async submit(){
          try{await this.$sendEvent('submit',{email:'bad'})}
          catch(error){globalThis.__imperativeError=error}
        }}});"""

        class Input:
            email: str

        class Events:
            def submit(self, data: "Form.Input"):  # noqa: UP037
                raise EventError("Invalid form.", fields={"email": "Use a valid address."})

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Form().render().serialize(), "") + "/")
    page.locator("#imperative-error").click()
    page.wait_for_function("globalThis.__imperativeError !== undefined")
    assert page.evaluate("globalThis.__imperativeError") == {
        "status": 422,
        "code": "invalid_args",
        "message": "Invalid form.",
        "fieldErrors": {"email": "Use a valid address."},
    }
    assert page.evaluate("[...__citryRuntime._apps.values()][0].terminal") is False
    assert faults == []


@pytest.mark.e2e
def test_server_render_callback_failure_remains_terminal(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-terminal-callback-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Broken(Component):
        citry = engine
        template = '<button id="break-callback" @c-click="refresh">refresh</button>'
        js = """$component({onServerRender({revision}){
          if(revision>0)throw new Error('deliberate callback failure');
        }});"""

        class Events:
            def refresh(self):
                return actions.Render(Broken())

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Broken().render().serialize(), "") + "/")
    page.locator("#break-callback").click()
    page.wait_for_function("globalThis.__citryRuntime._apps.size === 0")
    assert len(faults) == 1
    assert faults[0].startswith("The Vue Events bridge was disposed")


@pytest.mark.e2e
def test_dispatch_uses_one_canonical_live_root_for_every_vue_root_shape(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-dispatch-roots-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class DispatchEvents:
        def ping(self):
            return actions.Dispatch("shape:ping")

    callback = """$component({onServerRender({component}){
      const name=component.$options.name;
      (globalThis.__shapeSend ||= {})[name]=()=>component.$sendEvent('ping');
      const receive=()=>{(globalThis.__local ||= []).push(name)};
      component.$el.addEventListener('shape:ping',receive);
      return ()=>component.$el.removeEventListener('shape:ping',receive);
    }});"""

    class MultiRoot(Component):
        citry = engine
        Events = DispatchEvents
        template = (
            '<section id="multi-first"><span id="multi-descendant">first</span></section>'
            '<button id="multi-second">second</button>'
        )
        js = callback

    class LeadingText(Component):
        citry = engine
        Events = DispatchEvents
        template = 'leading text <span id="leading-element">element</span>'
        js = callback

    class TextRoot(Component):
        citry = engine
        Events = DispatchEvents
        template = "text only"
        js = callback

    class EmptyRoot(Component):
        citry = engine
        Events = DispatchEvents
        template = ""
        js = callback

    class Root(Component):
        citry = engine
        template = "<main><c-MultiRoot /><c-LeadingText /><c-TextRoot /><c-EmptyRoot /></main>"

    dispatcher_for(engine)
    page.add_init_script(
        """globalThis.__documentEvents=[];
        document.addEventListener('shape:ping',event=>__documentEvents.push(event.target.id||event.target.nodeName));"""
    )
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Root().render().serialize(), "") + "/")
    page.wait_for_function("Object.keys(globalThis.__shapeSend || {}).length === 4")
    page.evaluate(
        """()=>{globalThis.__secondRootEvents=0;globalThis.__descendantEvents=0;
        document.querySelector('#multi-second').addEventListener('shape:ping',()=>__secondRootEvents++);
        document.querySelector('#multi-descendant').addEventListener('shape:ping',()=>__descendantEvents++);}"""
    )
    names = page.evaluate("Object.keys(__shapeSend)")
    for name in names:
        page.evaluate("name => __shapeSend[name]()", name)
    page.wait_for_function("globalThis.__documentEvents.length === 4")

    assert sorted(page.evaluate("globalThis.__documentEvents")) == [
        "#comment",
        "#text",
        "leading-element",
        "multi-first",
    ]
    assert page.evaluate("globalThis.__secondRootEvents") == 0
    assert page.evaluate("globalThis.__descendantEvents") == 0
    assert faults == []


@pytest.mark.e2e
def test_a_removed_component_comes_back_with_its_stylesheet(page: Any, serve_live: Any) -> None:
    page.set_default_timeout(5_000)
    engine = Citry(secret="vue-returning-style-owner-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    # A component with its own Dependencies may not load assets the page never
    # had. This one was on the first page, so it may come back.
    class Badge(Component):
        citry = engine
        template = """
            <p id="badge" class="returning-owner">badge</p>
        """

        class Dependencies:
            css = ["/returning-owner.css"]

    class Panel(Component):
        citry = engine

        class Kwargs:
            shown: bool = True

        class State(Kwargs):
            pass

        class Events:
            def toggle(self, state):
                state.shown = not state.shown
                return Panel(shown=state.shown)

        def template_data(self, kwargs, slots):
            return {"shown": kwargs.shown}

        template = """
            <main>
              <button id="toggle" @c-click="toggle">toggle</button>
              <c-if cond="shown"><c-badge /></c-if>
            </main>
        """

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.route(
        "**/returning-owner.css",
        lambda route: route.fulfill(body=".returning-owner{color:rgb(12, 34, 56)}", content_type="text/css"),
    )
    page.goto(serve_live(engine, Panel().render().serialize(), "") + "/")
    sheet = '[data-citry-css-url="/returning-owner.css"]'
    color = "element => getComputedStyle(element).color"
    page.locator("#badge").wait_for()
    assert page.locator("#badge").evaluate(color) == "rgb(12, 34, 56)"

    # Removing the last owner removes its stylesheet from the page.
    page.locator("#toggle").click()
    page.locator("#badge").wait_for(state="detached")
    page.locator(sheet).wait_for(state="detached")

    # Bringing the component back loads the same stylesheet again.
    page.locator("#toggle").click()
    page.locator("#badge").wait_for()
    assert page.locator(sheet).count() == 1
    assert page.locator("#badge").evaluate(color) == "rgb(12, 34, 56)"
    assert faults == []


@pytest.mark.e2e
def test_shared_stylesheet_survives_until_its_last_occurrence_owner_is_removed(page: Any, serve_live: Any) -> None:
    page.set_default_timeout(5_000)
    engine = Citry(secret="vue-shared-style-owner-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class StyledFirst(Component):
        citry = engine
        template = '<p id="first-owner" class="shared-owner">first</p>'

        class Dependencies:
            css = ["/shared-owner.css"]

    class StyledSecond(Component):
        citry = engine
        template = '<p id="second-owner" class="shared-owner">second</p>'

        class Dependencies:
            css = ["/shared-owner.css"]

    class RootState:
        show_first: bool = True
        show_second: bool = True

        def render(self):
            return Root(show_first=self.show_first, show_second=self.show_second)

    class Root(Component):
        citry = engine
        State = RootState
        template = """
          <main>
            <button id="remove-first" @c-click="remove_first">remove first</button>
            <button id="remove-second" @c-click="remove_second">remove second</button>
            <c-if cond="show_first"><c-StyledFirst /></c-if>
            <c-if cond="show_second"><c-StyledSecond /></c-if>
          </main>
        """
        js = """$component({onServerRender(){
          globalThis.__sharedCallbacks=(globalThis.__sharedCallbacks||0)+1;
          const child=document.getElementById('second-owner');
          if(child)globalThis.__secondCallbackColor=getComputedStyle(child).color;
        }});"""

        class Events:
            def remove_first(self, state: RootState):
                state.show_first = False
                return state.render()

            def remove_second(self, state: RootState):
                state.show_second = False
                return state.render()

        def template_data(self, kwargs, slots):
            return {
                "show_first": kwargs.get("show_first", True),
                "show_second": kwargs.get("show_second", True),
            }

    dispatcher_for(engine)
    html = Root().render().serialize()
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.route(
        "**/shared-owner.css",
        lambda route: route.fulfill(body=".shared-owner{color:rgb(12, 34, 56)}", content_type="text/css"),
    )
    _watch_citry_ready(page)
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    _wait_for_citry_ready(page)
    page.locator("#second-owner").wait_for()
    sheet = '[data-citry-css-url="/shared-owner.css"]'
    assert page.locator(sheet).count() == 1
    assert page.locator("#second-owner").evaluate("element => getComputedStyle(element).color") == "rgb(12, 34, 56)"

    page.locator("#remove-first").click()
    page.locator("#first-owner").wait_for(state="detached")
    assert page.locator("#second-owner").count() == 1, (faults, page.content())
    assert page.locator(sheet).count() == 1
    assert page.locator("#second-owner").evaluate("element => getComputedStyle(element).color") == "rgb(12, 34, 56)"
    assert page.evaluate("globalThis.__secondCallbackColor") == "rgb(12, 34, 56)"

    page.locator("#remove-second").click()
    page.locator("#second-owner").wait_for(state="detached")
    page.locator(sheet).wait_for(state="detached")
    assert page.locator(sheet).count() == 0
    assert faults == []


@pytest.mark.e2e
def test_native_get_and_attachment_use_the_per_event_routes(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-http-selection-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/tenant/citry")

    class HttpActions(Component):
        citry = engine
        template = """
          <main>
            <button id="run-search" @click="runSearch">search</button>
            <output id="search-result" v-text="result"></output>
            <button id="run-download" @click="$sendEvent('download')">download</button>
          </main>
        """
        js = """$component({
          data(){return {result:''}},
          methods:{runSearch(){this.$sendEvent('search',{q:'a/b',tags:['x','y']})
            .then(value=>{this.result=value.value})}}
        });"""

        class Search:
            q: str
            tags: list[str]

        class Events:
            @event(methods=("GET",))
            def search(self, data: Search):  # noqa: F821
                return {"value": f"{data.q}:{','.join(data.tags)}"}

            @event(bundle=False)
            def download(self):
                return actions.Download("download-body", "report.txt", content_type="text/plain")

    dispatcher_for(engine)
    html = HttpActions().render().serialize()
    requests: list[Any] = []
    faults: list[str] = []
    page.on("request", lambda request: requests.append(request) if "/ext/events/e/" in request.url else None)
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, html, "", prefix="/tenant/citry")
    page.goto(base + "/")
    page.locator("#run-search").click()
    page.wait_for_function("document.querySelector('#search-result')?.textContent === 'a/b:x,y'")
    search_request = next(request for request in requests if request.method == "GET")
    assert "/tenant/citry/ext/events/e/" in search_request.url
    assert "q=a%2Fb" in search_request.url
    assert search_request.url.count("tags=") == 2
    assert "_citry_protocol=citry-events%2F1" in search_request.url

    with page.expect_download() as download_info:
        page.locator("#run-download").click()
    download = download_info.value
    assert download.suggested_filename == "report.txt"
    assert download.path().read_text() == "download-body"
    post_request = next(request for request in requests if request.method == "POST")
    assert post_request.url.endswith(f"/ext/events/e/{HttpActions.class_id}/download")
    assert faults == []


@pytest.mark.e2e
def test_two_serialized_vue_apps_share_runtime_without_reset(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class LocalCounter(Component):
        citry = engine
        template = '<button class="local-counter" @click="count += 1" v-text="count"></button>'
        js = """$component((()=>{
          (globalThis.__citryVueIdentities ??= []).push(__citryRuntime.compilerRuntime);
          return {setup(){return {count: __citryRuntime.compilerRuntime.ref(0)};}};
        })());"""

    first = LocalCounter().render()
    first_html = first.serialize()
    assert first.serialize() == first_html
    second_html = LocalCounter().render().serialize()
    assert (
        first_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
        != second_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    )
    html = (
        "<!doctype html><html><body>"
        f'<section id="first-app">{first_html}</section>'
        "<script>globalThis.__vueAfterFirst=globalThis.Vue;"
        "globalThis.__citryVueAfterFirst=globalThis.__citryRuntime.compilerRuntime;</script>"
        f'<section id="second-app">{second_html}</section>'
        "</body></html>"
    )
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(html))
    page.wait_for_timeout(500)
    assert page.evaluate("__vueAfterFirst === Vue && __citryVueAfterFirst === __citryRuntime.compilerRuntime")
    assert page.evaluate(
        "__citryVueIdentities.length >= 1 && __citryVueIdentities.every(x => x === __citryRuntime.compilerRuntime)"
    )
    assert page.locator("#first-app .local-counter").text_content() == "0", (faults, page.content())
    assert page.locator("#second-app .local-counter").text_content() == "0", (faults, page.content())
    page.locator("#first-app .local-counter").click()
    page.locator("#second-app .local-counter").click()
    page.wait_for_function(
        "document.querySelector('#first-app .local-counter')?.textContent === '1'"
        " && document.querySelector('#second-app .local-counter')?.textContent === '1'"
    )
    assert faults == []


@pytest.mark.e2e
def test_selected_static_hydration_reuses_one_parent_leaf_root(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)
    calls = {"parent": 0, "leaf": 0}

    class Leaf(Component):
        citry = engine
        template = '<span class="leaf-card" title="Leaf title" aria-label="Leaf accessible name">leaf value</span>'
        js = "$component({});"

        def template_data(self, kwargs, slots):
            calls["leaf"] += 1
            return {"label": "leaf value"}

    class Parent(Component):
        citry = engine
        template = (
            '<main class="page-shell" title="Page title" aria-label="Page content" '
            'style="color: red; margin-top: 2px" data-note="A &quot;quoted&quot; &amp; marked">'
            "a \n  b<c-leaf /></main>"
        )

        def template_data(self, kwargs, slots):
            calls["parent"] += 1
            return {}

    control_render = Parent().render()
    assert calls == {"parent": 1, "leaf": 1}
    control_html = control_render.serialize(ssr=False)
    assert calls == {"parent": 1, "leaf": 1}
    assert '"hydrate":true' not in control_html
    warnings: list[str] = []
    faults: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.on("pageerror", lambda error: faults.append(str(error)))
    _watch_citry_ready(page)
    page.goto(serve_document(control_html))
    _wait_for_citry_ready(page)
    control_dom = page.evaluate(
        """() => {
          const node = document.querySelector('[id^="citry-vue-"]').firstElementChild;
          const facts = [node, ...node.querySelectorAll('*')].map(element => ({
            tag: element.tagName.toLowerCase(),
            attrs: [...element.attributes]
              .filter(attr => !attr.name.startsWith('data-cid-') && attr.name !== 'style')
              .map(attr => [attr.name, attr.value])
              .sort(([left], [right]) => left.localeCompare(right)),
            text: element.textContent,
          }));
          const style = getComputedStyle(node);
          return {facts, style: {raw: node.getAttribute('style'), color: style.color, marginTop: style.marginTop}};
        }"""
    )
    assert warnings == [], warnings
    assert faults == [], faults
    warnings.clear()
    faults.clear()

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    rendered = Parent().render()
    assert calls == {"parent": 2, "leaf": 2}
    html = rendered.serialize(ssr=True)
    assert calls == {"parent": 2, "leaf": 2}
    assert '"hydrate":true' in html
    assert "a b<span" in html
    assert "a \n  b" not in html
    app_id = html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    before_bootstrap = html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = html.rfind("<script", 0, before_bootstrap)
    capture = (
        f'<script>window.__hydrationRoot=document.querySelector("#citry-vue-{app_id}").firstElementChild;'
        f'window.__hydrationBody=document.querySelector("#citry-vue-{app_id}").innerHTML;</script>'
    )
    html = html[:bootstrap_tag] + capture + html[bootstrap_tag:]
    page.goto(serve_document(html))
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    parity = page.evaluate(
        """control => {
          const host = document.querySelector('[id^="citry-vue-"]');
          const domFacts = node => [node, ...node.querySelectorAll('*')].map(element => ({
            tag: element.tagName.toLowerCase(),
            attrs: [...element.attributes]
              .filter(attr => !attr.name.startsWith('data-cid-') && attr.name !== 'style')
              .map(attr => [attr.name, attr.value])
              .sort(([left], [right]) => left.localeCompare(right)),
            text: element.textContent,
          }));
          const current = domFacts(host.firstElementChild);
          const style = getComputedStyle(host.firstElementChild);
          return {sameNode: host.firstElementChild === window.__hydrationRoot,
            sameDom: JSON.stringify(current) === JSON.stringify(control.facts),
            style: {raw: host.firstElementChild.getAttribute('style'), color: style.color,
              marginTop: style.marginTop},
            controlStyle: control.style,
            initialHtml: window.__hydrationBody, currentHtml: host.innerHTML,
            probe: window.__citryHydrationReport,
            rootAttrs: [host.firstElementChild.getAttribute('class'),
              host.firstElementChild.getAttribute('title'),
              host.firstElementChild.getAttribute('aria-label'),
              host.firstElementChild.getAttribute('data-note')],
            leafAttrs: [host.querySelector('span')?.getAttribute('class'),
              host.querySelector('span')?.getAttribute('title'),
              host.querySelector('span')?.getAttribute('aria-label')]};
        }""",
        control_dom,
    )
    assert parity["sameNode"], (parity, warnings, faults)
    assert parity["sameDom"], (parity, warnings, faults)
    assert "a b" in parity["initialHtml"]
    assert "a \n  b" not in parity["initialHtml"]
    assert parity["probe"]["mountError"] is None
    assert parity["probe"]["mismatchCount"] == 0
    assert parity["probe"]["reusedElementCount"] == 2
    assert parity["probe"]["replacedElementCount"] == 0
    assert parity["rootAttrs"] == [
        "page-shell",
        "Page title",
        "Page content",
        'A "quoted" & marked',
    ]
    assert parity["style"]["color"] == parity["controlStyle"]["color"] == "rgb(255, 0, 0)"
    assert parity["style"]["marginTop"] == parity["controlStyle"]["marginTop"] == "2px"
    assert parity["style"]["raw"] == "color: red; margin-top: 2px"
    assert parity["controlStyle"]["raw"] == "color: red; margin-top: 2px;"
    assert parity["leafAttrs"] == ["leaf-card", "Leaf title", "Leaf accessible name"]
    assert page.locator("main > span").text_content() == "leaf value"
    # Hydrated HTML carries no data-cid-<id> markers, like the client-mounted host.
    assert f"data-cid-{rendered.frame.render_id}" not in parity["currentHtml"]
    leaf_render = next(part for part in rendered.parts if hasattr(part, "frame"))
    assert f"data-cid-{leaf_render.frame.render_id}" not in parity["currentHtml"]
    assert warnings == [], warnings
    assert faults == [], faults


@pytest.mark.e2e
def test_static_physical_document_shell_hydrates_with_csr_parity(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)
    calls = {"page": 0, "leaf": 0}

    class Page(Component):
        citry = engine
        template = (
            "<!doctype html><html lang='en'><head><title>document shell</title></head>"
            '<body class="page-body" data-shell="A &quot;B&quot;">'
            "<main><span>stable body</span><c-leaf /></main></body></html>"
        )
        js = """$component({onServerRender(){
          (globalThis.__documentScopes ||= []).push('page');
        }});"""

        def template_data(self, kwargs, slots):
            calls["page"] += 1
            return {}

    class Leaf(Component):
        citry = engine
        template = "<em>leaf body</em>"
        js = """$component({onServerRender(){
          (globalThis.__documentScopes ||= []).push('leaf');
        }});"""

        def template_data(self, kwargs, slots):
            calls["leaf"] += 1
            return {}

    rendered = Page().render()
    assert calls == {"page": 1, "leaf": 1}
    leaf_render = next(part for part in rendered.parts if hasattr(part, "frame"))
    control_html = rendered.serialize(ssr=False)
    assert calls == {"page": 1, "leaf": 1}
    warnings: list[str] = []
    faults: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.on("pageerror", lambda error: faults.append(str(error)))
    _watch_citry_ready(page)
    page.goto(serve_document(control_html))
    _wait_for_citry_ready(page)
    control_dom = page.evaluate(
        """() => {
          const root = document.querySelector('[id^="citry-vue-"]').firstElementChild;
          return [root, ...root.querySelectorAll('*')].map(element => ({
            tag: element.tagName.toLowerCase(), text: element.textContent,
            attrs: [...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([left], [right]) => left.localeCompare(right)),
          }));
        }"""
    )
    warnings.clear()
    faults.clear()

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    hydrated_html = rendered.serialize(ssr=True)
    assert calls == {"page": 1, "leaf": 1}
    assert '"hydrate":true' in hydrated_html
    assert hydrated_html.startswith("<!doctype html>")
    assert "<head><title>document shell</title></head>" in hydrated_html
    assert "<body " in hydrated_html
    assert "</body></html>" in hydrated_html
    # The page's <html> sits outside the Vue host, so both serializations mark
    # it the same way; only the host's own contents drop the data-cid markers.
    page_marker = f"<html lang='en' data-cid-{rendered.frame.render_id}=\"\">"
    assert page_marker in control_html
    assert page_marker in hydrated_html
    host_body = hydrated_html.split('id="citry-vue-', 1)[1].split("</div>", 1)[0]
    assert "data-cid-" not in host_body
    assert f"data-cid-{leaf_render.frame.render_id}" not in hydrated_html
    app_id = hydrated_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    before_bootstrap = hydrated_html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = hydrated_html.rfind("<script", 0, before_bootstrap)
    capture = (
        f'<script>window.__hydrationRoot=document.querySelector("#citry-vue-{app_id}").firstElementChild;'
        f'window.__hydrationNodes=[window.__hydrationRoot,...window.__hydrationRoot.querySelectorAll("*")];'
        f'window.__hydrationBody=document.querySelector("#citry-vue-{app_id}").innerHTML;</script>'
    )
    hydrated_html = hydrated_html[:bootstrap_tag] + capture + hydrated_html[bootstrap_tag:]
    page.goto(serve_document(hydrated_html))
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    result = page.evaluate(
        """control => {
          const host = document.querySelector('[id^="citry-vue-"]');
          const currentNodes = [host.firstElementChild, ...host.firstElementChild.querySelectorAll('*')];
          const facts = currentNodes.map(element => ({tag: element.tagName.toLowerCase(),
            text: element.textContent,
            attrs: [...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([left], [right]) => left.localeCompare(right))}));
          return {sameNode: host.firstElementChild === window.__hydrationRoot,
            sameNodes: currentNodes.length === window.__hydrationNodes.length
              && currentNodes.every((node, index) => node === window.__hydrationNodes[index]),
            sameDom: JSON.stringify(facts) === JSON.stringify(control),
            initialHtml: window.__hydrationBody,
            probe: window.__citryHydrationReport,
            shell: {doctype: document.doctype?.name,
              htmlLang: document.documentElement.getAttribute('lang'),
              headTitle: document.head.querySelector('title')?.textContent,
              bodyClass: document.body.getAttribute('class'),
              bodyShell: document.body.getAttribute('data-shell'),
              scopes: window.__documentScopes || []}};
        }""",
        control_dom,
    )
    assert result["sameNode"], result
    assert result["sameNodes"], result
    assert result["sameDom"], result
    assert result["probe"]["mountError"] is None
    assert result["probe"]["mismatchCount"] == 0
    assert result["probe"]["reusedElementCount"] >= 3
    assert result["probe"]["replacedElementCount"] == 0
    assert result["shell"] == {
        "doctype": "html",
        "htmlLang": "en",
        "headTitle": "document shell",
        "bodyClass": "page-body",
        "bodyShell": 'A "B"',
        "scopes": ["leaf", "page"],
    }
    assert page.locator('[id^="citry-vue-"] main > span').text_content() == "stable body"
    assert page.locator('[id^="citry-vue-"] main > em').text_content() == "leaf body"
    assert f"data-cid-{leaf_render.frame.render_id}" not in page.locator('[id^="citry-vue-"]').inner_html()
    assert warnings == [], warnings
    assert faults == [], faults


@pytest.mark.e2e
def test_plain_python_text_hydrates_with_csr_parity(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)
    calls = 0
    escaped_calls = 0

    class Page(Component):
        citry = engine
        template = "<main>{{ label }}</main>"
        js = "$component({});"

        def template_data(self, kwargs, slots):
            nonlocal calls
            calls += 1
            return {"label": "hello"}

    rendered = Page().render()
    assert calls == 1
    control_html = rendered.serialize(ssr=False)
    page.on("pageerror", lambda error: pytest.fail(str(error)))
    _watch_citry_ready(page)
    page.goto(serve_document(control_html))
    _wait_for_citry_ready(page)
    control_facts = page.evaluate(
        """() => [document.querySelector('[id^="citry-vue-"]').firstElementChild,
          ...document.querySelector('[id^="citry-vue-"]').firstElementChild.querySelectorAll('*')]
          .map(element => ({tag: element.tagName.toLowerCase(), text: element.textContent,
            attrs: [...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b))}))"""
    )

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    hydrated_html = rendered.serialize(ssr=True)
    assert calls == 1
    assert '"hydrate":true' in hydrated_html
    assert "hello</main>" in hydrated_html
    app_id = hydrated_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    before_bootstrap = hydrated_html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = hydrated_html.rfind("<script", 0, before_bootstrap)
    capture = (
        f'<script>window.__hydrationRoot=document.querySelector("#citry-vue-{app_id}").firstElementChild;'
        f'window.__hydrationHtml=document.querySelector("#citry-vue-{app_id}").innerHTML;</script>'
    )
    hydrated_html = hydrated_html[:bootstrap_tag] + capture + hydrated_html[bootstrap_tag:]
    warnings: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.goto(serve_document(hydrated_html))
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    result = page.evaluate(
        """control => {
          const host = document.querySelector('[id^="citry-vue-"]');
          const facts = [host.firstElementChild, ...host.firstElementChild.querySelectorAll('*')]
            .map(element => ({tag: element.tagName.toLowerCase(), text: element.textContent,
              attrs: [...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
                .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b))}));
          return {sameNode: host.firstElementChild === window.__hydrationRoot,
            sameDom: JSON.stringify(facts) === JSON.stringify(control),
            initialHtml: window.__hydrationHtml,
            text: host.firstElementChild.textContent,
            probe: window.__citryHydrationReport};
        }""",
        control_facts,
    )
    assert result["sameNode"], result
    assert result["sameDom"], result
    assert "hello</main>" in result["initialHtml"]
    assert result["text"] == "hello"
    assert result["probe"]["mountError"] is None
    assert result["probe"]["mismatchCount"] == 0
    assert result["probe"]["reusedElementCount"] >= 1
    assert result["probe"]["replacedElementCount"] == 0
    assert warnings == [], warnings

    class EscapedPage(Component):
        citry = engine
        template = "<main>{{ label }}</main>"
        js = "$component({});"

        def template_data(self, kwargs, slots):
            nonlocal escaped_calls
            escaped_calls += 1
            return {"label": "Python & entity text <b>unsafe</b>"}

    escaped_render = EscapedPage().render()
    assert escaped_calls == 1
    # Text with markup characters is written escaped, exactly as Vue would set
    # it, so the page still hydrates and the characters never become elements.
    escaped_html = escaped_render.serialize(ssr=True)
    assert '"hydrate":true' in escaped_html
    assert "<b>unsafe</b>" not in escaped_html
    assert "<main>Python &amp; entity text &lt;b&gt;unsafe&lt;/b&gt;</main>" in escaped_html
    page.goto(serve_document(escaped_html))
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    escaped_result = page.evaluate(
        """() => {
          const main = document.querySelector('[id^="citry-vue-"] main');
          return {text: main.textContent, html: main.innerHTML,
            unexpectedElement: main.querySelector('b') !== null,
            hydrationProbe: window.__citryHydrationReport};
        }"""
    )
    assert escaped_result["text"] == "Python & entity text <b>unsafe</b>"
    assert escaped_result["html"] == "Python &amp; entity text &lt;b&gt;unsafe&lt;/b&gt;"
    assert escaped_result["unexpectedElement"] is False
    assert escaped_result["hydrationProbe"]["mountError"] is None
    assert escaped_result["hydrationProbe"]["mismatchCount"] == 0
    assert escaped_result["hydrationProbe"]["replacedElementCount"] == 0
    assert escaped_result["hydrationProbe"]["reusedElementCount"] == 1
    assert escaped_calls == 1
    assert warnings == [], warnings


@pytest.mark.e2e
def test_events_page_hydrates_then_renders_updated_summary(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="events-ssr-revision-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    calls = {"page": 0, "summary": 0}
    event_calls: list[int] = []

    class Summary(Component):
        citry = engine
        template = """\
<section id="summary"><h4>Total</h4><span id="value">{{ value }}</span></section>\
"""

        def template_data(self, kwargs, slots):
            calls["summary"] += 1
            return kwargs

    class Page(Component):
        citry = engine
        template = """\
<main><button id="advance" @c-click="advance">advance</button>\
<c-summary c-value="value" />\
<aside id="neighbor">Keep</aside></main>\
"""

        class State:
            value: int = 10

        class Events:
            def advance(self, state: Page.State):
                event_calls.append(state.value)
                state.value += 1
                return actions.Render(Page(value=state.value))

        def template_data(self, kwargs, slots):
            calls["page"] += 1
            return {"value": int(kwargs.get("value", 10))}

    dispatcher_for(engine)
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    faults: list[str] = []
    console_faults: list[str] = []
    event_requests: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: console_faults.append(message.text) if message.type in {"warning", "error"} else None,
    )
    page.on(
        "request",
        lambda request: event_requests.append(request.url) if request.url.endswith("/ext/events/call") else None,
    )

    rendered = Page(value=10).render()
    assert calls == {"page": 1, "summary": 1}
    html = rendered.serialize(ssr=True)
    assert calls == {"page": 1, "summary": 1}
    assert '"hydrate":true' in html
    app_id = html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    bootstrap_call = html.index('<script type="application/json" data-citry-vue-document=')
    bootstrap_tag = html.rfind("<script", 0, bootstrap_call)
    capture = f"""<script>
      const host=document.querySelector('#citry-vue-{app_id}');
      const main=host.querySelector('main');
      window.__eventsSsrNodes={{main,button:main.querySelector('#advance'),
        summary:main.querySelector('#summary'),value:main.querySelector('#value'),
        neighbor:main.querySelector('#neighbor')}};
      window.__eventsSsrHtml=host.innerHTML;
    </script>"""
    html = html[:bootstrap_tag] + capture + html[bootstrap_tag:]

    _watch_citry_ready(page)
    page.goto(serve_live(engine, html, "") + "/")
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    initial = page.evaluate(
        """() => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.querySelector('main');
          const current={main,button:main.querySelector('#advance'),
            summary:main.querySelector('#summary'),value:main.querySelector('#value'),
            neighbor:main.querySelector('#neighbor')};
          return {sameNodes:Object.keys(current).every(key =>
              current[key] === window.__eventsSsrNodes[key]),
            hasSourceEventAttribute:current.button.hasAttribute('@c-click'),
            html:window.__eventsSsrHtml, probe:window.__citryHydrationReport};
        }"""
    )
    assert initial["sameNodes"], initial
    assert initial["hasSourceEventAttribute"] is False
    assert '<span id="value">10</span>' in initial["html"]
    assert initial["probe"]["mountError"] is None
    assert initial["probe"]["mismatchCount"] == 0
    assert initial["probe"]["reusedElementCount"] >= 4
    assert page.locator("#neighbor").text_content() == "Keep"

    with page.expect_response("**/ext/events/call") as response:
        page.locator("#advance").click()
    assert response.value.ok, response.value.text()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 1")
    page.wait_for_function("document.querySelector('#value')?.textContent === '11'")
    updated = page.evaluate(
        """() => ({summary:document.querySelector('#summary').outerHTML,
          main:document.querySelector('[id^="citry-vue-"] main').outerHTML,
          neighborStable:document.querySelector('#neighbor') === window.__eventsSsrNodes.neighbor,
          probe:window.__citryHydrationReport})"""
    )
    assert updated["summary"] == '<section id="summary"><h4>Total</h4><span id="value">11</span></section>'
    assert '<aside id="neighbor">Keep</aside>' in updated["main"]
    assert updated["neighborStable"] is True
    assert updated["probe"]["mountError"] is None
    assert updated["probe"]["mismatchCount"] == 0
    assert event_requests
    assert len(event_requests) == 1, event_requests
    assert event_calls == [10]
    assert calls == {"page": 2, "summary": 2}
    assert console_faults == [], console_faults
    assert faults == [], faults


@pytest.mark.e2e
def test_recorded_python_if_for_nested_page_hydrates_with_csr_parity(page: Any, serve_live: Any) -> None:
    engine = Citry(autodiscover=False)
    calls = {"page": 0, "leaf": 0}

    class Leaf(Component):
        citry = engine
        template = """\
<section id="group">\
<span id="branch" c-if="show">{{ label }}</span>\
<c-for each="item in items"><strong class="item">{{ item }}</strong></c-for>\
</section>\
"""
        js = "$component({});"

        def template_data(self, _kwargs, _slots):
            calls["leaf"] += 1
            return {"show": True, "label": "before raw", "items": ["first item"]}

    class Page(Component):
        citry = engine
        template = "<main><c-leaf /></main>"
        js = "$component({});"

        def template_data(self, _kwargs, _slots):
            calls["page"] += 1
            return {}

    faults: list[str] = []
    console_faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: console_faults.append(message.text) if message.type in {"warning", "error"} else None,
    )

    rendered = Page().render()
    assert calls == {"page": 1, "leaf": 1}
    control_html = rendered.serialize(ssr=False)
    assert calls == {"page": 1, "leaf": 1}
    _watch_citry_ready(page)
    page.goto(serve_live(engine, control_html, "") + "/")
    _wait_for_citry_ready(page)
    control = page.evaluate(
        """() => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.querySelector('main');
          const group=main.querySelector('#group');
          const facts=[main, ...main.querySelectorAll('*')].map(element => ({
            tag:element.tagName.toLowerCase(),
            attrs:[...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b)),
            text:element.textContent,
          }));
          return {facts, group:group.outerHTML};
        }"""
    )
    assert '<span id="branch">before raw</span>' in control["group"]
    assert '<strong class="item">first item</strong>' in control["group"]
    assert console_faults == [], console_faults
    assert faults == [], faults
    console_faults.clear()
    faults.clear()

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    html = rendered.serialize(ssr=True)
    assert calls == {"page": 1, "leaf": 1}
    assert '"hydrate":true' in html
    # The configuration block opens the start tags, and its JSON starts right
    # after its opening tag.
    bootstrap_tag = html.index('<script type="application/json" data-citry-vue-document="')
    payload_start = html.index(">", bootstrap_tag) + 1
    configuration, _ = json.JSONDecoder().raw_decode(html[payload_start:])
    manifest = configuration["manifest"]
    # The component renders as ordinary Vue output: no definition declares a
    # block of Python HTML, and no occurrence carries one.
    assert all(not definition["opaqueHtmlSites"] for definition in manifest["definitions"])
    assert all("opaqueHtml" not in occurrence["preparedData"] for occurrence in manifest["occurrences"])
    app_id = html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    capture = f"""<script>
      const host=document.querySelector('#citry-vue-{app_id}');
      const main=host.querySelector('main');
      window.__pythonGroupControlFacts={json.dumps(control["facts"])};
      window.__pythonGroupServerNodes={{main,group:main.querySelector('#group'),
        branch:main.querySelector('#branch'),item:main.querySelector('.item')}};
    </script>"""
    html = html[:bootstrap_tag] + capture + html[bootstrap_tag:]
    page.goto(serve_live(engine, html, "") + "/")
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    result = page.evaluate(
        """() => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.querySelector('main');
          const current={main,group:main.querySelector('#group'),
            branch:main.querySelector('#branch'),item:main.querySelector('.item')};
          const facts=[main, ...main.querySelectorAll('*')].map(element => ({
            tag:element.tagName.toLowerCase(),
            attrs:[...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b)),
            text:element.textContent,
          }));
          return {sameNodes:Object.keys(current).every(key =>
              current[key]===window.__pythonGroupServerNodes[key]),
            sameDom:JSON.stringify(facts)===JSON.stringify(window.__pythonGroupControlFacts),
            probe:window.__citryHydrationReport};
        }"""
    )
    assert result["sameNodes"], result
    assert result["sameDom"], result
    assert result["probe"]["mountError"] is None
    assert result["probe"]["mismatchCount"] == 0
    assert result["probe"]["reusedElementCount"] >= 3
    assert calls == {"page": 1, "leaf": 1}
    assert console_faults == [], console_faults
    assert faults == [], faults


@pytest.mark.e2e
def test_recorded_python_if_for_group_renders_complete_update_after_event(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="python-branch-loop-ssr-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    calls = {"page": 0, "leaf": 0}
    leaf_render_id = ""
    event_calls = 0

    class Leaf(Component):
        citry = engine
        template = """\
<section id="group">\
<c-if cond="show"><span id="branch">{{ label }}</span></c-if>\
<c-else><strong id="branch">{{ label }}</strong></c-else>\
<c-for each="item in items"><strong class="item">{{ item }}</strong></c-for>\
</section>\
"""

        def template_data(self, kwargs, _slots):
            nonlocal leaf_render_id
            calls["leaf"] += 1
            leaf_render_id = self.id
            return kwargs

    class Page(Component):
        citry = engine
        template = """\
<main><button id="advance" @c-click="advance">advance</button>{{ leaf }}<aside id="neighbor">keep</aside></main>\
"""

        class Events:
            def advance(self):
                nonlocal event_calls
                event_calls += 1
                return actions.Render(
                    Leaf(show=False, label="after & <raw>", items=[]),
                    target=f"render:{leaf_render_id}",
                )

        def template_data(self, _kwargs, _slots):
            calls["page"] += 1
            return {
                "leaf": Leaf(show=True, label="before & <raw>", items=["first & <b>"]),
            }

    dispatcher_for(engine)
    faults: list[str] = []
    console_faults: list[str] = []
    event_requests: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: console_faults.append(message.text) if message.type in {"warning", "error"} else None,
    )
    page.on(
        "request",
        lambda request: event_requests.append(request.url) if request.url.endswith("/ext/events/call") else None,
    )

    rendered = Page().render()
    assert calls == {"page": 1, "leaf": 1}
    control_html = rendered.serialize(ssr=False)
    assert calls == {"page": 1, "leaf": 1}
    _watch_citry_ready(page)
    page.goto(serve_live(engine, control_html, "") + "/")
    _wait_for_citry_ready(page)
    control = page.evaluate(
        """() => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.querySelector('main');
          const facts=[main, ...main.querySelectorAll('*')].map(element => ({
            tag:element.tagName.toLowerCase(),
            attrs:[...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b)),
            text:element.textContent,
          }));
          return {facts, group:main.querySelector('#group').outerHTML};
        }"""
    )
    assert control["group"].startswith('<section id="group"')
    assert '<span id="branch">before &amp; &lt;raw&gt;</span>' in control["group"]
    assert '<strong class="item">first &amp; &lt;b&gt;</strong>' in control["group"]
    assert console_faults == [], console_faults
    assert faults == [], faults
    console_faults.clear()
    faults.clear()

    html = rendered.serialize(ssr=False)
    assert calls == {"page": 1, "leaf": 1}
    assert '"hydrate":true' not in html
    # The configuration block opens the start tags, and its JSON starts right
    # after its opening tag.
    bootstrap_tag = html.index('<script type="application/json" data-citry-vue-document="')
    payload_start = html.index(">", bootstrap_tag) + 1
    configuration, _ = json.JSONDecoder().raw_decode(html[payload_start:])
    manifest = configuration["manifest"]
    # The component renders as ordinary Vue output: no definition declares a
    # block of Python HTML, and no occurrence carries one.
    assert all(not definition["opaqueHtmlSites"] for definition in manifest["definitions"])
    assert all("opaqueHtml" not in occurrence["preparedData"] for occurrence in manifest["occurrences"])
    app_id = html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    assert f'<div id="citry-vue-{app_id}"></div>' in html
    capture = f"""<script>
      window.__pythonGroupControlFacts={json.dumps(control["facts"])};
    </script>"""
    html = html[:bootstrap_tag] + capture + html[bootstrap_tag:]
    # Ask for the hydration report, so its absence below shows the page
    # mounted in the browser rather than that nobody asked.
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(serve_live(engine, html, "") + "/")
    _wait_for_citry_ready(page)
    initial = page.evaluate(
        """() => {
          const host=document.querySelector('[id^="citry-vue-"]');
          const main=host.querySelector('main');
          const current={main,button:main.querySelector('#advance'),
            group:main.querySelector('#group'),branch:main.querySelector('#branch'),
            item:main.querySelector('.item'),neighbor:main.querySelector('#neighbor')};
          window.__pythonGroupInitialNodes=current;
          const facts=[main, ...main.querySelectorAll('*')].map(element => ({
            tag:element.tagName.toLowerCase(),
            attrs:[...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b)),
            text:element.textContent,
          }));
          return {sameDom:JSON.stringify(facts) === JSON.stringify(window.__pythonGroupControlFacts),
            group:current.group.outerHTML,probe:window.__citryHydrationReport ?? null};
        }"""
    )
    assert initial["sameDom"], initial
    assert '<span id="branch">before &amp; &lt;raw&gt;</span>' in initial["group"]
    assert '<strong class="item">first &amp; &lt;b&gt;</strong>' in initial["group"]
    assert initial["probe"] is None

    with page.expect_response("**/ext/events/call") as response:
        page.locator("#advance").click()
    assert response.value.ok, response.value.text()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 1")
    page.wait_for_function("document.querySelector('#branch')?.tagName === 'STRONG'")
    updated = page.evaluate(
        """() => {
          const group=document.querySelector('#group');
          const clean=group.cloneNode(true);
          for(const node of [clean, ...clean.querySelectorAll('*')])
            for(const attr of [...node.attributes])
              if(attr.name.startsWith('data-cid-')) node.removeAttribute(attr.name);
          return {html:clean.outerHTML,itemCount:group.querySelectorAll('.item').length,
            neighborStable:document.querySelector('#neighbor')===window.__pythonGroupInitialNodes.neighbor,
            probe:window.__citryHydrationReport ?? null};
        }"""
    )
    assert updated["html"] == '<section id="group"><strong id="branch">after &amp; &lt;raw&gt;</strong></section>'
    assert updated["html"] != initial["group"]
    assert updated["itemCount"] == 0
    assert updated["neighborStable"] is True
    assert updated["probe"] is None
    assert calls == {"page": 1, "leaf": 2}
    assert event_calls == 1
    assert len(event_requests) == 1, event_requests
    assert console_faults == [], console_faults
    assert faults == [], faults


@pytest.mark.e2e
def test_plain_component_root_preserves_parent_fallthrough_in_csr_and_ssr(page: Any, serve_live: Any) -> None:
    engine = Citry(autodiscover=False)
    parent_js = """\
$component({
      data(){return {label:'Initial title',visible:true};},
      methods:{updateTitle(){this.label='Updated title';
              globalThis.__fallthroughUpdates=(globalThis.__fallthroughUpdates||0)+1;},
            onChildClick(){this.label='Clicked title';
              globalThis.__fallthroughClicks=(globalThis.__fallthroughClicks||0)+1;}},
      mounted(){globalThis.__fallthroughUpdates=0;globalThis.__fallthroughClicks=0;
        globalThis.__fallthroughUpdateTitle=()=>this.updateTitle();
        globalThis.__fallthroughSetVisible=value=>{this.visible=value;}}
    });"""

    class PlainChild(Component):
        citry = engine
        template = """\
<section>child</section>"""

    class OrdinaryChild(Component):
        citry = engine
        template = """\
<section v-show="visible">child</section>"""
        js = """\
$component({data(){return {visible:true};}});"""

    class NoInheritChild(Component):
        citry = engine
        template = """\
<section>child</section>"""
        js = """\
$component({inheritAttrs:false});"""

    class PlainPage(Component):
        citry = engine
        template = """\
<main>
  <c-plain-child
    :title="label"
    @click="onChildClick"
  />
</main>"""
        js = parent_js

    class OrdinaryPage(Component):
        citry = engine
        template = """\
<main>
  <c-ordinary-child
    :title="label"
    @click="onChildClick"
  />
</main>"""
        js = parent_js

    class NoInheritPage(Component):
        citry = engine
        template = """\
<main>
  <c-no-inherit-child
    :title="label"
    @click="onChildClick"
  />
</main>"""
        js = parent_js

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    _watch_citry_ready(page)
    faults: list[str] = []
    console_faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: console_faults.append(message.text) if message.type in {"warning", "error"} else None,
    )
    observations: dict[str, dict[str, Any]] = {}

    for page_type, ssr_modes in (
        (PlainPage, (False, True)),
        (OrdinaryPage, (False, True)),
        (NoInheritPage, (False,)),
    ):
        for use_ssr in ssr_modes:
            rendered = page_type().render()
            html = rendered.serialize(ssr=use_ssr)
            hydrates = '"hydrate":true' in html
            if use_ssr:
                # Both children are called with fallthrough attributes and a
                # listener, which the server does not write, so <main> is written as a shell and Vue builds the
                # child inside it while the rest of the page hydrates. Until then the shell shows Citry's HTML.
                assert hydrates, html[:500]
                assert re.search(r'<main data-allow-mismatch="children">.+</main>', html, re.DOTALL)
                assert '"emptyShells":true' in html
                admission = hydration_admission(rendered)
                assert admission is not None
                assert admission.shell_count == 1, admission
                assert [(item.code, item.outcome, item.shell_tag) for item in admission.declines] == [
                    ("component-attrs", "shell", "main")
                ], admission
            else:
                assert hydrates is False

            server_root_capture = ""
            if use_ssr and hydrates:
                app_id = html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
                bootstrap_tag = html.index('<script type="application/json" data-citry-vue-document="')
                server_root_capture = (
                    f"<script>window.__fallthroughServerRoot="
                    f"document.querySelector('#citry-vue-{app_id} section');</script>"
                )
                html = html[:bootstrap_tag] + server_root_capture + html[bootstrap_tag:]

            console_start = len(console_faults)
            fault_start = len(faults)
            page.goto(serve_live(engine, html, "") + "/")
            _wait_for_citry_ready(page)
            if hydrates:
                page.wait_for_function("window.__citryHydrationReport !== undefined")
            initial = page.evaluate(
                """() => {
                  const root=document.querySelector('main section');
                  window.__fallthroughMountedRoot=root;
                  return {title:root?.getAttribute('title'),id:root?.id,
                    text:root?.textContent,rootHtml:root?.outerHTML,
                    sameServerRoot:window.__fallthroughServerRoot === root,
                    serverRootMissing:window.__fallthroughServerRoot === null,
                    probe:window.__citryHydrationReport ?? null};
                }"""
            )
            page.locator("main section").click()
            page.wait_for_timeout(50)
            after_initial_click = page.evaluate(
                """() => ({title:document.querySelector('main section')?.getAttribute('title'),
                  clickCount:window.__fallthroughClicks,
                  sameRoot:document.querySelector('main section')===window.__fallthroughMountedRoot})"""
            )
            page.evaluate("window.__fallthroughUpdateTitle()")
            page.wait_for_function("window.__fallthroughUpdates === 1")
            page.wait_for_timeout(50)
            after_data_update = page.evaluate(
                """() => ({title:document.querySelector('main section')?.getAttribute('title'),
                  updateCount:window.__fallthroughUpdates,
                  sameRoot:document.querySelector('main section')===window.__fallthroughMountedRoot})"""
            )
            observations[f"{page_type.__name__} ssr={use_ssr}"] = {
                "initial": initial,
                "afterInitialClick": after_initial_click,
                "afterDataUpdate": after_data_update,
                "hydrated": hydrates,
                "errors": faults[fault_start:],
                "warnings": console_faults[console_start:],
            }

    for name, observed in observations.items():
        assert observed["initial"]["text"] == "child", (name, observed)
        assert observed["afterDataUpdate"]["updateCount"] == 1, (name, observed)
        assert observed["afterInitialClick"]["sameRoot"] is True, (name, observed)
        if name.startswith("NoInheritPage"):
            assert observed["initial"]["title"] is None, (name, observed)
            assert observed["afterInitialClick"]["title"] is None, (name, observed)
            assert observed["afterInitialClick"]["clickCount"] == 0, (name, observed)
            assert observed["afterDataUpdate"]["title"] is None, (name, observed)
        else:
            assert observed["initial"]["title"] == "Initial title", (name, observed)
            assert observed["afterInitialClick"]["title"] == "Clicked title", (name, observed)
            assert observed["afterInitialClick"]["clickCount"] == 1, (name, observed)
            assert observed["afterDataUpdate"]["title"] == "Updated title", (name, observed)
        assert observed["errors"] == [], (name, observed)
        assert observed["warnings"] == [], (name, observed)
        if observed["hydrated"]:
            # The <main> shell arrives with Citry's HTML for the child, which
            # the runtime removes before Vue hydrates, so Vue builds each
            # child root itself and keeps the shell with no mismatch and no
            # replaced element.
            assert observed["initial"]["serverRootMissing"] is False, (name, observed)
            assert observed["initial"]["sameServerRoot"] is False, (name, observed)
            assert observed["initial"]["probe"]["mountError"] is None, (name, observed)
            assert observed["initial"]["probe"]["mismatchCount"] == 0, (name, observed)
            assert observed["initial"]["probe"]["replacedElementCount"] == 0, (name, observed)
        else:
            assert observed["initial"]["probe"] is None, (name, observed)

    assert observations["PlainPage ssr=True"]["hydrated"] is True
    assert observations["OrdinaryPage ssr=True"]["hydrated"] is True


@pytest.mark.e2e
@pytest.mark.parametrize("use_ssr", [False, True], ids=["mounted", "hydrated"])
def test_caller_v_show_controls_component_root(page: Any, serve_live: Any, use_ssr: bool) -> None:
    engine = Citry(secret="vue-show-component-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Child(Component):
        citry = engine
        template = """\
<section>child {{ count }}</section>"""

        def template_data(self, kwargs, slots):
            return kwargs

    class Page(Component):
        citry = engine
        State = PageState
        template = """\
<main>
  <button id="refresh" @c-click="refresh">refresh</button>
  <c-child v-show="visible" c-count="count" />
</main>"""
        js = """\
$component({
  data(){return {visible:true};},
  mounted(){globalThis.__setVisible=value=>{this.visible=value;};}
});"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return state.render()

    dispatcher_for(engine)
    faults: list[str] = []
    warnings: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None,
    )
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    rendered = Page(count=0).render()
    html = rendered.serialize(ssr=use_ssr)
    assert ('"hydrate":true' in html) is use_ssr
    if use_ssr:
        # The shown value lives in browser data, so the server leaves the
        # call to Vue: <main> is a shell and Vue builds its content.
        admission = hydration_admission(rendered)
        assert admission is not None
        assert [(item.code, item.outcome, item.shell_tag) for item in admission.declines] == [
            ("unsupported-directive", "shell", "main")
        ], admission

    _watch_citry_ready(page)
    page.goto(serve_live(engine, html, "") + "/")
    _wait_for_citry_ready(page)
    if use_ssr:
        page.wait_for_function("window.__citryHydrationReport !== undefined")
        probe = page.evaluate("window.__citryHydrationReport")
        assert probe["mountError"] is None, probe
        assert probe["mismatchCount"] == 0, probe
        assert probe["replacedElementCount"] == 0, probe
    root_state = """() => {
      const root=document.querySelector('main section');
      return {text:root?.textContent, display:root?.style.display,
        shown:root ? root.getClientRects().length > 0 : null,
        sameRoot:root === window.__vShowRoot};
    }"""
    page.evaluate("window.__vShowRoot=document.querySelector('main section')")
    initial = page.evaluate(root_state)
    assert initial == {"text": "child 0", "display": "", "shown": True, "sameRoot": True}

    page.evaluate("window.__setVisible(false)")
    page.wait_for_function("document.querySelector('main section')?.style.display === 'none'")
    assert page.evaluate(root_state) == {"text": "child 0", "display": "none", "shown": False, "sameRoot": True}

    page.evaluate("window.__setVisible(true)")
    page.wait_for_function("document.querySelector('main section')?.style.display === ''")
    assert page.evaluate(root_state) == {"text": "child 0", "display": "", "shown": True, "sameRoot": True}

    # A server Render replaces the child's content but keeps the caller's
    # browser value, so a hidden child stays hidden and can be shown again.
    page.evaluate("window.__setVisible(false)")
    page.wait_for_function("document.querySelector('main section')?.style.display === 'none'")
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('main section')?.textContent === 'child 1'")
    assert page.evaluate(root_state) == {"text": "child 1", "display": "none", "shown": False, "sameRoot": True}
    page.evaluate("window.__setVisible(true)")
    page.wait_for_function("document.querySelector('main section')?.style.display === ''")
    assert page.evaluate(root_state) == {"text": "child 1", "display": "", "shown": True, "sameRoot": True}
    assert faults == [], faults
    assert warnings == [], warnings


@pytest.mark.e2e
def test_server_render_switches_between_shown_and_plain_calls(page: Any, serve_live: Any) -> None:
    # Python picks a different authored call on each render. Each call has
    # its own Vue key, so Vue replaces the child instead of carrying the old
    # call's hidden root over to the plain call.
    engine = Citry(secret="vue-show-switch-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        shown: bool = True

        def render(self):
            return Page(shown=self.shown)

    class Child(Component):
        citry = engine
        template = """\
<section>child</section>"""

    class Page(Component):
        citry = engine
        State = PageState
        template = """\
<main>
  <button id="flip" @c-click="flip">flip</button>
  <c-if cond="shown">
    <c-child v-show="visible" />
  </c-if>
  <c-else>
    <c-child />
  </c-else>
</main>"""
        js = """\
$component({data(){return {visible:false};}});"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def flip(self, state: PageState):
                state.shown = not state.shown
                return state.render()

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    _watch_citry_ready(page)
    page.goto(serve_live(engine, Page(shown=True).render().serialize(ssr=False), "") + "/")
    _wait_for_citry_ready(page)
    display = "() => document.querySelector('main section')?.style.display"
    assert page.evaluate(display) == "none"
    page.locator("#flip").click()
    page.wait_for_function(f"({display})() === ''")
    page.locator("#flip").click()
    page.wait_for_function(f"({display})() === 'none'")
    assert faults == [], faults


@pytest.mark.e2e
def test_caller_v_show_through_a_component_root_rejects_a_several_root_leaf(page: Any, serve_live: Any) -> None:
    # The server sees only that Child's root is another component, so the
    # browser reports the several-root Leaf that Vue would silently skip.
    engine = Citry(autodiscover=False)

    class Leaf(Component):
        citry = engine
        template = """\
<p>first</p>
<p>second</p>"""

    class Child(Component):
        citry = engine
        template = """\
<c-leaf />"""

    class Page(Component):
        citry = engine
        template = """\
<main>
  <c-child v-show="visible" />
</main>"""
        js = """\
$component({data(){return {visible:false};}});"""

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Page().render().serialize(ssr=False), "") + "/")
    deadline = time.monotonic() + 5
    while not faults and time.monotonic() < deadline:
        page.wait_for_timeout(50)
    assert any(
        "A 'v-show' or custom directive on a Citry component needs one root element, but component Leaf_" in fault
        for fault in faults
    ), faults


@pytest.mark.e2e
def test_static_component_site_hydrates_with_sibling_and_csr_parity(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)
    calls = {"page": 0, "summary": 0}

    class Summary(Component):
        citry = engine
        template = """\
<section title="face 😀" id="summary"><h4>Summary 😀</h4></section>"""

        @staticmethod
        def js_data(_kwargs, _slots):
            return {"ready": True}

        def template_data(self, kwargs, slots):
            calls["summary"] += 1
            return {}

    class Page(Component):
        citry = engine
        template = """\
<main>
  <c-summary />
  <aside id="following">Next</aside>
</main>"""

        def template_data(self, kwargs, slots):
            calls["page"] += 1
            return {}

    rendered = Page().render()
    assert calls == {"page": 1, "summary": 1}
    control_html = rendered.serialize(ssr=False)
    assert '"hydrate":true' not in control_html
    assert calls == {"page": 1, "summary": 1}

    control_warnings: list[str] = []
    control_faults: list[str] = []
    page.on(
        "console",
        lambda message: control_warnings.append(message.text) if message.type in {"warning", "error"} else None,
    )
    page.on("pageerror", lambda error: control_faults.append(str(error)))
    _watch_citry_ready(page)
    page.goto(serve_document(control_html))
    _wait_for_citry_ready(page)
    control_dom = page.evaluate(
        """() => {
          const main = document.querySelector('[id^="citry-vue-"] main');
          const facts = [main, ...main.querySelectorAll('*')].map(element => ({
            tag: element.tagName.toLowerCase(),
            attrs: [...element.attributes]
              .filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b)),
            text: element.textContent,
          }));
          return {facts, children: [...main.children].map(element => element.id)};
        }"""
    )
    assert control_warnings == [], control_warnings
    assert control_faults == [], control_faults
    assert control_dom["children"] == ["summary", "following"]

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    hydrated_html = rendered.serialize(ssr=True)
    assert calls == {"page": 1, "summary": 1}
    assert '"hydrate":true' in hydrated_html
    assert '<section title="face 😀" id="summary">' in hydrated_html
    assert '<aside id="following">Next</aside>' in hydrated_html

    # The configuration block opens the start tags, and its JSON starts right
    # after its opening tag.
    bootstrap_tag = hydrated_html.index('<script type="application/json" data-citry-vue-document="')
    payload_start = hydrated_html.index(">", bootstrap_tag) + 1
    configuration, _ = json.JSONDecoder().raw_decode(hydrated_html[payload_start:])
    manifest = configuration["manifest"]
    # The component renders as ordinary Vue output: no definition declares a
    # block of Python HTML, and no occurrence carries one.
    assert all(not definition["opaqueHtmlSites"] for definition in manifest["definitions"])
    assert all("opaqueHtml" not in occurrence["preparedData"] for occurrence in manifest["occurrences"])

    app_id = hydrated_html.split('id="citry-vue-', 1)[1].split('"', 1)[0]
    capture = f"""<script>
      const host = document.querySelector('#citry-vue-{app_id}');
      const main = host.querySelector('main');
      window.__summaryServerNodes = {{main, summary:main.querySelector('#summary'),
        heading:main.querySelector('#summary h4'), sibling:main.querySelector('#following')}};
      window.__summaryServerHtml = host.innerHTML;
    </script>"""
    hydrated_html = hydrated_html[:bootstrap_tag] + capture + hydrated_html[bootstrap_tag:]
    control_warnings.clear()
    control_faults.clear()
    page.goto(serve_document(hydrated_html))
    _wait_for_citry_ready(page)
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    result = page.evaluate(
        """control => {
          const host = document.querySelector('[id^="citry-vue-"]');
          const main = host.querySelector('main');
          const nodes = [main, ...main.querySelectorAll('*')];
          const facts = nodes.map(element => ({tag: element.tagName.toLowerCase(),
            attrs: [...element.attributes].filter(attr => !attr.name.startsWith('data-cid-'))
              .map(attr => [attr.name, attr.value]).sort(([a], [b]) => a.localeCompare(b)),
            text: element.textContent}));
          const current = {main, summary:main.querySelector('#summary'),
            heading:main.querySelector('#summary h4'), sibling:main.querySelector('#following')};
          return {sameNodes: Object.keys(current).every(key =>
              current[key] === window.__summaryServerNodes[key]),
            sameDom: JSON.stringify(facts) === JSON.stringify(control.facts),
            childIds: [...main.children].map(element => element.id),
            siblingAlignment: current.summary.nextElementSibling === current.sibling
              && current.sibling.parentElement === main,
            serverHtml: window.__summaryServerHtml, probe: window.__citryHydrationReport};
        }""",
        control_dom,
    )
    assert result["sameNodes"], result
    assert result["sameDom"], result
    assert result["childIds"] == control_dom["children"] == ["summary", "following"]
    assert result["siblingAlignment"], result
    assert '<section title="face 😀" id="summary">' in result["serverHtml"]
    assert '<aside id="following">Next</aside>' in result["serverHtml"]
    assert result["probe"]["mountError"] is None
    assert result["probe"]["mismatchCount"] == 0
    assert result["probe"]["replacedElementCount"] == 0
    assert control_warnings == [], control_warnings
    assert control_faults == [], control_faults


@pytest.mark.e2e
def test_child_render_selects_fallback_instead_of_retained_parent_slot(page: Any, serve_live: Any) -> None:
    page.set_default_timeout(3000)
    engine = Citry(secret="vue-slot-subtree-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = (
            '<section><button id="reset-slot" @c-click="reset">reset</button>'
            '<c-slot><span id="fallback-slot">fallback</span></c-slot></section>'
        )

        class Events:
            def reset(self):
                return Child()

    engine.register(Child)

    class Parent(Component):
        citry = engine
        template = '<main><c-child><span id="supplied-slot">supplied</span></c-child><p id="sibling">keep</p></main>'

    dispatcher_for(engine)
    html = Parent().render().serialize()
    faults: list[str] = []
    console: list[str] = []
    calls: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text))
    page.on("request", lambda request: calls.append(request.url) if request.url.endswith("/ext/events/call") else None)
    page.add_init_script(
        """
        window.__citryReplies = [];
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
          const response = await originalFetch(...args);
          if (String(args[0]).endsWith('/ext/events/call')) window.__citryReplies.push(await response.clone().json());
          return response;
        };
        """
    )
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    page.locator("#supplied-slot").wait_for()
    page.locator("#reset-slot").click()
    page.locator("#fallback-slot").wait_for()
    assert page.get_by_text("fallback", exact=True).count() == 1, (
        calls,
        page.evaluate("window.__citryReplies"),
        faults,
        console,
        page.content(),
    )
    assert page.locator("#supplied-slot").count() == 0
    assert page.locator("#sibling").text_content() == "keep"
    assert faults == []


@pytest.mark.e2e
def test_supplied_slot_event_dispatches_to_lexical_parent(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-slot-lexical-events-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class ParentState:
        count: int = 0

        def render(self):
            return Parent(count=self.count)

    class Receiver(Component):
        citry = engine
        template = "<section><c-slot /></section>"

    engine.register(Receiver)

    class Parent(Component):
        citry = engine
        template = (
            '<main><c-receiver><button id="lexical-event" @c-click="increment({amount: localAmount})">'
            "{{ count }}</button></c-receiver></main>"
        )
        js = "$component({data(){return {localAmount: 2};}});"
        State = ParentState

        class Increment:
            amount: int = 0

        class Events:
            def increment(self, data: Increment, state: ParentState):  # noqa: F821
                state.count += data.amount
                return state.render()

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0)}

    dispatcher_for(engine)
    html = Parent(count=0).render().serialize()
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    page.locator("#lexical-event").click()
    page.wait_for_function("document.querySelector('#lexical-event')?.textContent === '2'")
    assert faults == []


@pytest.mark.e2e
def test_native_event_args_use_lexical_vue_scope(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-native-event-args-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class ChoiceState:
        chosen: int = 0

        def render(self):
            return Choices(chosen=self.chosen)

    class Choices(Component):
        citry = engine
        template = (
            '<main><button class="choice" v-for="row in [3, 4]" :key="row" '
            '@c-click="choose({value: row})" v-text="row"></button>'
            '<output id="chosen">{{ chosen }}</output></main>'
        )
        State = ChoiceState

        class Choice:
            value: int = 0

        class Events:
            def choose(self, data: Choice, state: ChoiceState):  # noqa: F821
                state.chosen = data.value
                return state.render()

        def template_data(self, kwargs, slots):
            return {"chosen": kwargs.get("chosen", 0)}

    dispatcher_for(engine)
    html = Choices(chosen=0).render().serialize()
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    page.locator(".choice").nth(1).click()
    page.wait_for_function("document.querySelector('#chosen')?.textContent === '4'")
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_spread_coexists_with_an_authored_timed_event(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-coexist-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Mixed(Component):
        citry = engine
        template = (
            '<button id="mixed" class="mixed-static" style="color: red;" formnovalidate '
            '@c-click.debounce.30ms="authored" c-bind="attrs">run</button>'
        )

        class Events:
            def authored(self):
                return None

            def from_runtime(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-keydown": "from_runtime"}}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Mixed().render().serialize(), "") + "/")
    button = page.locator("#mixed")
    assert button.get_attribute("class") == "mixed-static"
    assert button.evaluate("element => element.style.color") == "red"
    assert button.get_attribute("formnovalidate") == ""

    with page.expect_request("**/ext/events/call") as authored_request:
        button.click()
    with page.expect_request("**/ext/events/call") as runtime_request:
        button.press("ArrowRight")

    assert authored_request.value.post_data_json["calls"][0]["handlerName"] == "authored"
    assert runtime_request.value.post_data_json["calls"][0]["handlerName"] == "from_runtime"
    assert faults == []


@pytest.mark.e2e
def test_component_runtime_event_spread_uses_declared_emit_from_multiple_roots(page: Any, serve_live: Any) -> None:
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")

    class Result(Component):
        citry = engine
        template = '<output id="component-runtime-result">handled</output>'

    class Child(Component):
        citry = engine
        template = (
            '<button class="component-runtime-trigger" @click="$emit(\'confirm\')">go</button>'
            '<button class="component-authored-trigger" '
            "@click=\"$emit('custom', {value: 'from-child'})\">custom</button>"
            '<form class="component-form" @submit.prevent="$emit(\'form\', $event)">'
            '<input name="value" value="from-form"><button type="submit">form</button></form><span>second</span>'
        )
        js = "$component({emits:['confirm', 'custom', 'form']});"

    class Parent(Component):
        citry = engine

        @dataclass
        class CustomArgs:
            value: str

        class Events:
            def go(self):
                return actions.Render(Result(), target="mark:result")

            def custom(self, data: Parent.CustomArgs):
                return None

            def form(self, data: Parent.CustomArgs):
                return None

        def template_data(self, kwargs, slots):
            return {"listeners": {"@c-confirm": "go"}}

        template = (
            '<main><c-Child c-bind="listeners"></c-Child>'
            '<c-Child @c-custom="custom({value: $event.value})"></c-Child>'
            '<c-Child @c-form="form"></c-Child>'
            '<c-mark name="result">waiting</c-mark></main>'
        )

    dispatcher_for(engine)
    faults: list[str] = []
    requests: list[Any] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("request", lambda request: requests.append(request))
    page.goto(serve_live(engine, Parent().render().serialize(), "") + "/")
    with page.expect_request("**/ext/events/call") as authored_request:
        page.locator(".component-authored-trigger").nth(1).click()
    assert authored_request.value.post_data_json["calls"][0]["handlerName"] == "custom"
    assert authored_request.value.post_data_json["calls"][0]["args"] == {"value": "from-child"}

    with page.expect_request("**/ext/events/call") as form_request:
        page.locator(".component-form").nth(2).locator("button").click()
    assert form_request.value.post_data_json["calls"][0]["handlerName"] == "form"
    assert form_request.value.post_data_json["calls"][0]["args"] == {"value": "from-form"}

    page.locator(".component-runtime-trigger").first.click()
    page.wait_for_timeout(500)
    event_requests = [request for request in requests if request.url.endswith("/ext/events/call")]
    assert faults == [], (faults, page.content())
    assert len(event_requests) == 3, page.content()
    assert event_requests[2].post_data_json["calls"][0]["handlerName"] == "go"
    assert event_requests[2].post_data_json["calls"][0]["args"] == {}
    page.wait_for_selector("#component-runtime-result")
    assert page.locator("#component-runtime-result").text_content() == "handled"
    assert faults == []


@pytest.mark.e2e
def test_multi_root_wrapper_forwards_attrs_and_object_events_to_a_chosen_child(page: Any, serve_live: Any) -> None:
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = """
            <button id="forwarded-child" @click="fire">
                child
            </button>
        """
        js = """
            $component({
                emits: ["object-event", "undeclared-event"],
                methods: {
                    fire() {
                        this.$emit("object-event", "object-value");
                        this.$emit("undeclared-event", "undeclared-value");
                    },
                },
            });
        """

    class Wrapper(Component):
        citry = engine
        template = """
            <section id="wrapper-observation">
                <output
                    id="wrapper-attrs"
                    v-text="Object.keys($attrs).sort().join(',')"
                ></output>
                <output id="wrapper-prop" v-text="declaredProp"></output>
            </section>
            <c-Child
                v-bind="$attrs"
                v-on="listeners"
            />
            <button
                id="wrapper-declared"
                @click="$emit('declared-event')"
            >
                declared
            </button>
            <output id="wrapper-object" v-text="objectValue"></output>
        """
        js = """
            $component({
                inheritAttrs: false,
                props: { declaredProp: String },
                emits: ["declared-event"],
                data() {
                    return { objectValue: "waiting" };
                },
                computed: {
                    listeners() {
                        return { "object-event": this.captureObject };
                    },
                },
                methods: {
                    captureObject(value) {
                        this.objectValue = value;
                    },
                },
            });
        """

    class Parent(Component):
        citry = engine
        template = """
            <main>
                <c-Wrapper
                    :data-forwarded="'from-parent'"
                    :declared-prop="'declared-value'"
                    @undeclared-event="recordUndeclared"
                    @declared-event="recordDeclared"
                />
                <output id="parent-declared" v-text="declaredCount"></output>
                <output id="parent-undeclared" v-text="undeclaredCount"></output>
            </main>
        """
        js = """
            $component({
                data() {
                    return { declaredCount: 0, undeclaredCount: 0 };
                },
                methods: {
                    recordDeclared() {
                        this.declaredCount += 1;
                    },
                    recordUndeclared() {
                        this.undeclaredCount += 1;
                    },
                },
            });
        """

    engine.register(Child)
    engine.register(Wrapper)
    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Parent().render().serialize(), "") + "/")
    try:
        page.locator("#forwarded-child").wait_for(timeout=5_000)
    except _PlaywrightTimeoutError:
        pytest.fail(f"forwarding wrapper did not mount: faults={faults}; page={page.content()}")

    assert page.locator("#forwarded-child").get_attribute("data-forwarded") == "from-parent"
    attrs = page.locator("#wrapper-attrs").text_content()
    assert attrs is not None
    assert "data-forwarded" in attrs
    assert "onUndeclaredEvent" in attrs
    assert "declaredProp" not in attrs
    assert "onDeclaredEvent" not in attrs
    assert page.locator("#wrapper-prop").text_content() == "declared-value"

    page.locator("#forwarded-child").click()
    page.wait_for_function("document.querySelector('#wrapper-object')?.textContent === 'object-value'")
    page.wait_for_function("document.querySelector('#parent-undeclared')?.textContent === '1'")
    page.locator("#wrapper-declared").click()
    page.wait_for_function("document.querySelector('#parent-declared')?.textContent === '1'")
    assert faults == [], page.content()


@pytest.mark.parametrize("force_direct", [False, True], ids=["leaf", "direct"])
@pytest.mark.e2e
def test_runtime_spread_preserves_empty_source_attributes_and_dynamic_true(
    page: Any, serve_live: Any, force_direct: bool
) -> None:
    extensions = []
    if force_direct:

        class ForceDirectRenderer(Extension):
            name = "force_runtime_spread_empty_source_attrs_direct_renderer"

            def on_attrs_resolved(self, ctx):
                return None

        extensions = [ForceDirectRenderer]

    engine = Citry(
        secret=f"runtime-spread-empty-source-attrs-{force_direct}",
        autodiscover=False,
        extensions=extensions,
    )
    engine.set_mounted_prefix("/citry")

    class Surface(Component):
        citry = engine
        template = '<button id="source-values" data-bare data-empty="" c-bind="attrs">run</button>'

        class Events:
            def save(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-click": "save", "data-runtime-flag": True}}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    _watch_citry_ready(page)
    page.goto(serve_live(engine, Surface().render().serialize(), "") + "/")
    _wait_for_citry_ready(page)

    button = page.locator("#source-values")
    assert button.get_attribute("data-bare") == ""
    assert button.get_attribute("data-empty") == ""
    assert button.get_attribute("data-runtime-flag") == "true"
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_spread_loop_rows_dispatch_to_their_owning_component(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-loop-owner-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Rows(Component):
        citry = engine
        template = '<main><button class="runtime-row" c-for="attrs in handlers" c-bind="attrs">run</button></main>'

        class Events:
            def first(self):
                return None

            def second(self):
                return None

        def template_data(self, kwargs, slots):
            return {
                "handlers": [
                    {"@c-click": "first"},
                    {"@c-click": "second"},
                ]
            }

    dispatcher_for(engine)
    faults: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    response = page.goto(serve_live(engine, Rows().render().serialize(), "") + "/")
    rows = page.locator(".runtime-row")
    _wait_for_two_runtime_rows(page, faults, console_errors, response.status if response else None)

    with page.expect_request("**/ext/events/call") as first_request:
        rows.nth(0).click()
    with page.expect_request("**/ext/events/call") as second_request:
        rows.nth(1).click()

    first_call = first_request.value.post_data_json["calls"][0]
    second_call = second_request.value.post_data_json["calls"][0]
    assert [first_call["handlerName"], second_call["handlerName"]] == ["first", "second"]
    assert first_call["callerRenderId"] == second_call["callerRenderId"]
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_spread_selected_branch_loop_routes_dispatch_correctly(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="vue-runtime-event-selected-loop-route-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Rows(Component):
        citry = engine
        template = (
            '<main><c-if cond="True">'
            '<button class="runtime-row" c-for="attrs in handlers" c-bind="attrs">run</button>'
            '</c-if><c-else><p id="unselected-branch">empty</p></c-else></main>'
        )

        class Events:
            def first(self):
                return None

            def second(self):
                return None

        def template_data(self, kwargs, slots):
            return {"handlers": [{"@c-click": "first"}, {"@c-click": "second"}]}

    dispatcher_for(engine)
    faults: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    response = page.goto(serve_live(engine, Rows().render().serialize(), "") + "/")
    rows = page.locator(".runtime-row")
    _wait_for_two_runtime_rows(page, faults, console_errors, response.status if response else None)
    assert page.locator("#unselected-branch").count() == 0

    with page.expect_request("**/ext/events/call") as first_request:
        rows.nth(0).click()
    with page.expect_request("**/ext/events/call") as second_request:
        rows.nth(1).click()

    calls = [
        first_request.value.post_data_json["calls"][0],
        second_request.value.post_data_json["calls"][0],
    ]
    assert [call["handlerName"] for call in calls] == ["first", "second"]
    assert calls[0]["callerRenderId"] == calls[1]["callerRenderId"]
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_modifiers_apply_key_self_and_once(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-modifiers-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Surface(Component):
        citry = engine
        template = (
            '<main><div id="surface" tabindex="0" c-bind="attrs">'
            '<button id="surface-child" type="button">child</button></div>'
            '<div id="runtime-once-filtered" tabindex="0" c-bind="filtered_once_attrs"></div>'
            '<div id="authored-once-filtered" tabindex="0" '
            '@c-keydown.enter.self.once="authored_filtered"></div>'
            '<div id="runtime-once-valid" tabindex="0" c-bind="valid_once_attrs"></div></main>'
        )

        class Events:
            def activated(self):
                return None

            def runtime_filtered(self):
                return None

            def authored_filtered(self):
                return None

            def runtime_valid(self):
                return None

        def template_data(self, kwargs, slots):
            return {
                "attrs": {"@c-keydown.enter.self": "activated"},
                "filtered_once_attrs": {"@c-keydown.enter.self.once": "runtime_filtered"},
                "valid_once_attrs": {"@c-keydown.enter.self.once": "runtime_valid"},
            }

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, Surface().render().serialize(), "") + "/")
    page.locator("#surface").press("x")
    page.locator("#surface-child").press("Enter")
    page.wait_for_timeout(60)
    assert calls == []

    with page.expect_request("**/ext/events/call") as activated_request:
        page.locator("#surface").press("Enter")
    page.locator("#surface").press("Enter")
    page.wait_for_timeout(60)

    assert activated_request.value.post_data_json["calls"][0]["handlerName"] == "activated"
    assert [call["handlerName"] for call in calls] == ["activated", "activated"]

    # Vue's native once listener is consumed by the first keydown even when
    # the key guard declines it; authored and runtime-spread bindings agree.
    page.locator("#runtime-once-filtered").press("x")
    page.locator("#runtime-once-filtered").press("Enter")
    page.locator("#authored-once-filtered").press("x")
    page.locator("#authored-once-filtered").press("Enter")
    page.wait_for_timeout(60)
    assert [call["handlerName"] for call in calls] == ["activated", "activated"]

    with page.expect_request("**/ext/events/call") as valid_once_request:
        page.locator("#runtime-once-valid").press("Enter")
    page.locator("#runtime-once-valid").press("Enter")
    page.wait_for_timeout(60)
    assert valid_once_request.value.post_data_json["calls"][0]["handlerName"] == "runtime_valid"
    assert [call["handlerName"] for call in calls] == ["activated", "activated", "runtime_valid"]
    assert faults == []


@pytest.mark.e2e
def test_key_filtered_binding_checks_the_key_before_prevent(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-key-before-prevent-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class KeyedInput(Component):
        citry = engine
        template = """
            <main>
              <input
                id="authored"
                @c-keydown.prevent.enter="authored"
              />
              <input id="runtime" c-bind="attrs" />
            </main>
        """

        class Events:
            def authored(self):
                return None

            def runtime(self):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-keydown.prevent.enter": "runtime"}}

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, KeyedInput().render().serialize(), "") + "/")
    # Record, after the binding ran, whether each key's default was prevented.
    page.evaluate(
        "window.prevented = [];"
        "document.addEventListener('keydown', e => window.prevented.push([e.target.id, e.key, e.defaultPrevented]));"
    )

    for field_id, handler in (("authored", "authored"), ("runtime", "runtime")):
        field = page.locator(f"#{field_id}")
        # Any other key types as usual: `.prevent` applies only after the
        # key matches, as with Vue's `@keydown.prevent.enter`.
        field.press_sequentially("ab")
        page.wait_for_timeout(60)
        assert field.input_value() == "ab"
        assert not any(call["handlerName"] == handler for call in calls)
        with page.expect_request("**/ext/events/call") as request:
            field.press("Enter")
        assert request.value.post_data_json["calls"][0]["handlerName"] == handler

    assert page.evaluate("window.prevented") == [
        ["authored", "a", False],
        ["authored", "b", False],
        ["authored", "Enter", True],
        ["runtime", "a", False],
        ["runtime", "b", False],
        ["runtime", "Enter", True],
    ]
    assert faults == []


@pytest.mark.e2e
def test_vue_listener_with_two_keys_sends_for_either_key(page: Any, serve_live: Any) -> None:
    # An `@c-*` binding takes one key filter, and its load error points to a
    # Vue listener instead. Prove that listener calls the handler for both
    # keys and for no other key.
    engine = Citry(secret="vue-two-key-listener-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class EitherKey(Component):
        citry = engine
        template = """
            <main>
              <input
                id="field"
                @keydown.enter.escape="$sendEvent('go')"
              />
            </main>
        """

        class Events:
            def go(self):
                return None

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, EitherKey().render().serialize(), "") + "/")
    field = page.locator("#field")
    field.press_sequentially("ab")
    page.wait_for_timeout(60)
    assert calls == []
    for key in ("Enter", "Escape"):
        with page.expect_request("**/ext/events/call") as request:
            field.press(key)
        assert request.value.post_data_json["calls"][0]["handlerName"] == "go"
    assert faults == []


@pytest.mark.e2e
def test_key_filtered_state_binding_sends_only_for_that_key(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-state-key-filter-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Search(Component):
        citry = engine
        template = """
            <main>
              <input
                id="authored"
                :c-query.on:keydown.enter="authored"
              />
              <input id="runtime" c-bind="attrs" />
            </main>
        """

        class State:
            query: str = ""

        class Events:
            def authored(self, state):
                return None

            def runtime(self, state):
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {":c-query.on:keyup.enter": "runtime"}}

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, Search().render().serialize(), "") + "/")

    for field_id, handler, text in (("authored", "authored", "ab"), ("runtime", "runtime", "cd")):
        field = page.locator(f"#{field_id}")
        # Typing fires the keyboard update event for every key, but only
        # Enter passes the key filter, so nothing is sent before it.
        field.press_sequentially(text)
        page.wait_for_timeout(60)
        assert not any(call["handlerName"] == handler for call in calls)
        with page.expect_request("**/ext/events/call") as request:
            field.press("Enter")
        [call] = request.value.post_data_json["calls"]
        assert call["handlerName"] == handler
        # The call carries the value typed before Enter.
        assert call["stateUpdates"] == {"query": text}

    assert sorted(call["handlerName"] for call in calls) == ["authored", "runtime"]
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_once_survives_unrelated_binding_revisions_and_replaces_changed_handler(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="vue-runtime-event-once-revision-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class RevisionState:
        revision: int = 0

        def render(self):
            return RuntimeEvents(revision=self.revision)

    class RuntimeEvents(Component):
        citry = engine
        State = RevisionState
        template = (
            '<main><button id="advance" @c-click="advance">advance</button>'
            '<button id="runtime-once" c-bind="attrs">runtime</button>'
            '<output id="revision">{{ revision }}</output></main>'
        )

        class Events:
            def advance(self, state: RevisionState):
                state.revision += 1
                return state.render()

            def first(self):
                return None

            def keyboard(self):
                return None

            def replacement(self):
                return None

        def template_data(self, kwargs, slots):
            revision = kwargs.get("revision", 0)
            if revision == 0:
                attrs = {"@c-click.once": "first"}
            elif revision == 1:
                # The existing once binding moves behind an unrelated new binding.
                attrs = {"@c-keydown": "keyboard", "@c-click.once": "first"}
            else:
                # A real semantic change gets a new binding identity and listener.
                attrs = {"@c-click.once": "replacement", "@c-keydown": "keyboard"}
            return {"attrs": attrs, "revision": revision}

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.goto(serve_live(engine, RuntimeEvents(revision=0).render().serialize(), "") + "/")

    with page.expect_request("**/ext/events/call") as initial_once:
        page.locator("#runtime-once").click()
    assert initial_once.value.post_data_json["calls"][0]["handlerName"] == "first"

    with page.expect_request("**/ext/events/call") as first_revision:
        page.locator("#advance").click()
    assert first_revision.value.post_data_json["calls"][0]["handlerName"] == "advance"
    page.wait_for_function("document.querySelector('#revision')?.textContent === '1'")

    with page.expect_request("**/ext/events/call") as unrelated_binding:
        page.locator("#runtime-once").press("ArrowRight")
    assert unrelated_binding.value.post_data_json["calls"][0]["handlerName"] == "keyboard"
    page.locator("#runtime-once").click()
    page.wait_for_timeout(60)
    assert [call["handlerName"] for call in calls] == ["first", "advance", "keyboard"]

    with page.expect_request("**/ext/events/call") as second_revision:
        page.locator("#advance").click()
    assert second_revision.value.post_data_json["calls"][0]["handlerName"] == "advance"
    page.wait_for_function("document.querySelector('#revision')?.textContent === '2'")

    with page.expect_request("**/ext/events/call") as changed_binding:
        page.locator("#runtime-once").click()
    assert changed_binding.value.post_data_json["calls"][0]["handlerName"] == "replacement"
    page.locator("#runtime-once").click()
    page.wait_for_timeout(60)
    assert [call["handlerName"] for call in calls] == [
        "first",
        "advance",
        "keyboard",
        "advance",
        "replacement",
    ]
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_arguments_include_form_fields(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-form-args-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Contact(Component):
        citry = engine
        template = (
            '<form id="runtime-form" c-bind="attrs">'
            '<input name="email" type="text"><button type="submit">send</button></form>'
        )

        class Input:
            email: str

        class Events:
            def submit(self, data: Input):  # noqa: F821
                return None

        def template_data(self, kwargs, slots):
            return {"attrs": {"@c-submit.prevent": "submit"}}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Contact().render().serialize(), "") + "/")
    page.locator('#runtime-form input[name="email"]').fill("person@example.test")

    with page.expect_request("**/ext/events/call") as submitted:
        page.locator('#runtime-form button[type="submit"]').click()

    assert submitted.value.post_data_json["calls"][0]["handlerName"] == "submit"
    assert submitted.value.post_data_json["calls"][0]["args"] == {"email": "person@example.test"}
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_revision_cancels_pending_debounce_work(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-debounce-revision-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class RevisionState:
        revision: int = 0

        def render(self):
            return DebouncedRuntimeEvents(revision=self.revision)

    class DebouncedRuntimeEvents(Component):
        citry = engine
        State = RevisionState
        template = (
            '<main><button id="replace-handler" @c-click="replace_handler">replace</button>'
            '<button id="runtime-debounce" c-bind="attrs">runtime</button>'
            '<output id="revision">{{ revision }}</output></main>'
        )

        class Events:
            def replace_handler(self, state: RevisionState):
                state.revision += 1
                return state.render()

            def delayed(self):
                return None

            def immediate(self):
                return None

        def template_data(self, kwargs, slots):
            revision = kwargs.get("revision", 0)
            attrs = {"@c-click.debounce.120ms": "delayed"} if revision == 0 else {"@c-click": "immediate"}
            return {"attrs": attrs, "revision": revision}

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(engine, DebouncedRuntimeEvents(revision=0).render().serialize(), "") + "/")
    page.locator("#runtime-debounce").click()

    with page.expect_request("**/ext/events/call") as replacement:
        page.locator("#replace-handler").click()
    assert replacement.value.post_data_json["calls"][0]["handlerName"] == "replace_handler"
    page.wait_for_function("document.querySelector('#revision')?.textContent === '1'")
    page.clock.run_for(200)
    assert [call["handlerName"] for call in calls] == ["replace_handler"]

    with page.expect_request("**/ext/events/call") as new_handler:
        page.locator("#runtime-debounce").click()
    assert new_handler.value.post_data_json["calls"][0]["handlerName"] == "immediate"
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_debounce_keeps_pending_work_across_reordered_revision(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-debounce-retained-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class RevisionState:
        revision: int = 0

        def render(self):
            return RetainedDebounce(revision=self.revision)

    class RetainedDebounce(Component):
        citry = engine
        State = RevisionState

        @dataclass
        class FormData:
            value: str

        template = """
            <main>
                <button id="advance-debounce" @c-click="advance">advance</button>
                <form id="runtime-debounce" c-bind="attrs">
                    <input id="debounce-field" name="value">
                    <button id="debounce-trigger" type="button">send</button>
                </form>
                <output id="debounce-revision">{{ revision }}</output>
            </main>
        """

        class Events:
            def advance(self, state: RevisionState):
                state.revision += 1
                return state.render()

            def delayed(self, data: RetainedDebounce.FormData):
                return None

            def key_first(self, data: RetainedDebounce.FormData):
                return None

            def key_second(self, data: RetainedDebounce.FormData):
                return None

        def template_data(self, kwargs, slots):
            revision = kwargs.get("revision", 0)
            attrs = (
                {"@c-click.debounce.120ms": "delayed", "@c-keydown": "key_first"}
                if revision == 0
                else {"@c-keydown": "key_second", "@c-click.debounce.120ms": "delayed"}
            )
            return {"attrs": attrs, "revision": revision}

    dispatcher_for(engine)
    calls: list[dict[str, Any]] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: calls.extend(request.post_data_json["calls"])
        if request.url.endswith("/ext/events/call") and request.post_data_json
        else None,
    )
    page.clock.install()
    page.goto(serve_live(engine, RetainedDebounce(revision=0).render().serialize(), "") + "/")
    page.evaluate("window.__retainedDebounceElement=document.querySelector('#runtime-debounce')")
    _pause_fake_clock(page)

    def timing_snapshot() -> dict[str, Any]:
        return page.evaluate(
            """() => {
              const app=__citryRuntime._apps.values().next().value;
              const record=app.mounted.get(app.rootId).record;
              return {revision:app.revision,generation:record.generation,terminal:app.terminal,
                sameElement:document.querySelector('#runtime-debounce')===window.__retainedDebounceElement,
                lifetimes:[...(record.eventTimingLifetimes || [])].map(lifetime =>
                  ({event:lifetime.binding.event,handler:lifetime.binding.handler,
                    debounce:lifetime.binding.debounce,timer:Boolean(lifetime.timer)}))};
            }"""
        )

    page.locator("#debounce-field").fill("captured")
    page.locator("#debounce-trigger").click()
    page.locator("#debounce-field").fill("after-submit")
    page.clock.run_for(60)
    before_revision_timing = timing_snapshot()

    with page.expect_request("**/ext/events/call") as revision_request:
        page.locator("#advance-debounce").click()
    assert revision_request.value.post_data_json["calls"][0]["handlerName"] == "advance"
    page.wait_for_function("document.querySelector('#debounce-revision')?.textContent === '1'")
    after_revision_timing = timing_snapshot()
    page.clock.run_for(59)
    before_deadline_timing = timing_snapshot()
    assert [call["handlerName"] for call in calls] == ["advance"]

    page.clock.run_for(1)
    page.wait_for_timeout(20)
    delayed_calls = [call for call in calls if call["handlerName"] == "delayed"]
    after_deadline_timing = timing_snapshot()
    assert len(delayed_calls) == 1, (
        f"before revision={before_revision_timing}, after revision={after_revision_timing}, "
        f"before deadline={before_deadline_timing}, after deadline={after_deadline_timing}, "
        f"calls={calls}, faults={faults}"
    )
    assert delayed_calls[0]["args"] == {"value": "captured"}
    page.locator("#debounce-field").fill("after-revision")
    with page.expect_request("**/ext/events/call") as new_key_request:
        page.locator("#debounce-trigger").press("ArrowRight")
    assert new_key_request.value.post_data_json["calls"][0]["handlerName"] == "key_second"
    assert new_key_request.value.post_data_json["calls"][0]["args"] == {"value": "after-revision"}
    assert [call["handlerName"] for call in calls] == ["advance", "delayed", "key_second"]
    assert faults == []


@pytest.mark.e2e
def test_native_runtime_event_dispatch_errors_reach_vue_error_handler(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-runtime-event-error-routing-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class BrokenDispatch(Component):
        citry = engine
        template = (
            '<main><button id="sync-error" c-bind="sync_attrs">sync</button>'
            '<button id="async-error" c-bind="async_attrs">async</button></main>'
        )

        class Events:
            def sync_failure(self):
                return None

            def async_failure(self):
                return None

        def template_data(self, kwargs, slots):
            return {
                "sync_attrs": {"@c-click": "sync_failure"},
                "async_attrs": {"@c-click": "async_failure"},
            }

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.add_init_script(
        """
        globalThis.__runtimeEventVueErrors = [];
        globalThis.__runtimeEventUnhandled = [];
        addEventListener('unhandledrejection', event => {
          __runtimeEventUnhandled.push(String(event.reason));
          event.preventDefault();
        });
        """
    )
    page.goto(serve_live(engine, BrokenDispatch().render().serialize(), "") + "/")
    page.locator("#async-error").wait_for()
    page.evaluate(
        """() => {
          const app = [...__citryRuntime._apps.values()][0];
          app.vueApp.config.errorHandler = (error, _instance, info) => {
            __runtimeEventVueErrors.push({message: error.message, info});
          };
          app.eventDispatch = (_record, bindingId) => {
            const name = app.occurrences.get(app.rootId).preparedData.eventBindings[bindingId].handler;
            if (name === 'sync_failure') throw new Error('sync dispatch failure');
            return Promise.reject(new Error('async dispatch failure'));
          };
        }"""
    )

    page.locator("#sync-error").click()
    page.locator("#async-error").click()
    page.wait_for_function("globalThis.__runtimeEventVueErrors.length === 2")

    assert page.evaluate("globalThis.__runtimeEventVueErrors") == [
        {"message": "sync dispatch failure", "info": "Citry runtime event"},
        {"message": "async dispatch failure", "info": "Citry runtime event"},
    ]
    assert page.evaluate("globalThis.__runtimeEventUnhandled") == []
    assert faults == []


@pytest.mark.e2e
def test_hidden_logical_child_remounts_with_latest_revision_data(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-hidden-child-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = '<output id="hidden-child">{{ value }}</output>'

        def template_data(self, kwargs, slots):
            return {"value": kwargs.get("value", 0)}

    engine.register(Child)

    class ParentState:
        value: int = 0

        def render(self):
            return Parent(value=self.value)

    class Parent(Component):
        citry = engine
        template = (
            '<main><button id="toggle-hidden-child" @click="show = !show">toggle</button>'
            '<button id="revise-hidden-child" @c-click="revise">revise</button>'
            '<template v-if="show"><c-child c-value="value" /></template></main>'
        )
        js = "$component({data(){return {show: false};}});"
        State = ParentState

        class Events:
            def revise(self, state: ParentState):
                state.value += 1
                return state.render()

        def template_data(self, kwargs, slots):
            return {"value": kwargs.get("value", 0)}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Parent(value=0).render().serialize(), "") + "/")
    page.wait_for_timeout(200)
    assert page.locator("#revise-hidden-child").count() == 1, (faults, page.content())
    assert page.locator("#hidden-child").count() == 0

    page.locator("#revise-hidden-child").click()
    page.wait_for_timeout(200)
    assert page.locator("#hidden-child").count() == 0
    page.locator("#toggle-hidden-child").click()
    page.wait_for_timeout(200)
    assert page.locator("#hidden-child").text_content() == "1", (faults, page.content())
    assert faults == []


@pytest.mark.e2e
def test_event_response_is_rejected_after_source_generation_changes(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-source-generation-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class ChildState:
        count: int = 0

        def render(self):
            return Child(count=self.count)

    class Child(Component):
        citry = engine
        template = '<button id="slow-child" @click="send">{{ count }}</button>'
        State = ChildState
        js = """$component({methods:{send(){
          return this.$sendEvent('increment')
            .catch(()=>undefined)
            .finally(()=>{globalThis.__citryGenerationSettled=true;});
        }}});"""

        class Events:
            def increment(self, state: ChildState):
                time.sleep(0.3)
                state.count += 1
                return actions.Dispatch("stale:ping", {"count": state.count})

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0)}

    engine.register(Child)

    class Parent(Component):
        citry = engine
        template = (
            '<main><button id="toggle-slow-child" @click="show = !show">toggle</button>'
            '<template v-if="show"><c-child /></template></main>'
        )
        js = "$component({data(){return {show: true};}});"

    dispatcher_for(engine)
    faults: list[str] = []
    requests: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "request",
        lambda request: requests.append(request.url) if request.url.endswith("/ext/events/call") else None,
    )
    page.add_init_script(
        """
        window.__citryRejections = [];
        window.__staleDispatches = 0;
        document.addEventListener('stale:ping', () => { window.__staleDispatches += 1; });
        window.addEventListener('unhandledrejection', event => {
          window.__citryRejections.push(String(event.reason?.message || event.reason));
          event.preventDefault();
        });
        """
    )
    _watch_citry_ready(page)
    page.goto(serve_live(engine, Parent().render().serialize(), "") + "/")
    _wait_for_citry_ready(page)
    initial_generation = page.evaluate(
        """()=>{const app=[...__citryRuntime._apps.values()][0];return [...app.mounted.values()]
          .find(item=>item.record.occurrenceId!==app.rootId).record.generation}"""
    )
    page.locator("#slow-child").click()
    page.locator("#toggle-slow-child").click()
    assert page.locator("#slow-child").count() == 0
    page.locator("#toggle-slow-child").click()
    page.wait_for_function("document.querySelector('#slow-child')?.textContent === '0'")
    page.wait_for_function(
        "window.__citryGenerationSettled === true && [...__citryRuntime._apps.values()][0]?.busy === false"
    )
    assert page.locator("#slow-child").text_content() == "0"
    assert len(requests) == 1
    app_state = page.evaluate(
        """()=>{const app=[...__citryRuntime._apps.values()][0];const child=[...app.mounted.values()]
          .find(item=>item.record.occurrenceId!==app.rootId);
          return {revision:app.revision,generation:child.record.generation}}"""
    )
    assert app_state == {"revision": 0, "generation": initial_generation + 1}
    assert page.evaluate("window.__staleDispatches") == 0
    assert faults == []


@pytest.mark.e2e
def test_empty_call_run_adds_a_component_with_options_and_events(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-empty-call-run-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class ChildState:
        count: int = 0

        def render(self):
            return Child(count=self.count)

    class Child(Component):
        citry = engine
        template = (
            '<button class="run-child" data-citry-occurrence="authored" '
            'c-data-item="item" :data-local="local" @c-click="increment">'
            "{{ count }}</button>"
        )
        js = (
            "globalThis.__firstChildRuns = (globalThis.__firstChildRuns || 0) + 1; "
            "const sharedName = 7; $component({data(){return {local: sharedName};}});"
        )
        css = ".run-child { color: rgb(1, 2, 3); }"
        State = ChildState

        class Events:
            def increment(self, state: ChildState):
                state.count += 1
                return state.render()

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0), "item": kwargs.get("item")}

    engine.register(Child)

    class SecondChild(Component):
        citry = engine
        template = '<output class="second-run-child" :data-local="local" v-text="local"></output>'
        js = (
            "globalThis.__secondChildRuns = (globalThis.__secondChildRuns || 0) + 1; "
            "const sharedName = 8; $component({data(){return {local: sharedName};}});"
        )

    engine.register(SecondChild)

    class ParentState:
        items: list[int]
        second_items: list[int]

        def render(self):
            return Parent(items=self.items, second_items=self.second_items)

    class Parent(Component):
        citry = engine
        template = (
            '<main><button id="add-run-child" @c-click="add">add</button>'
            '<button id="reverse-run-children" @c-click="reverse">reverse</button>'
            '<c-for each="item in items"><c-child #c-key="item" c-item="item" /></c-for>'
            '<c-for each="item in second_items"><c-second-child #c-key="item" /></c-for></main>'
        )
        State = ParentState

        class Events:
            def add(self, state: ParentState):
                state.items = [*state.items, len(state.items)]
                state.second_items = [*state.second_items, len(state.second_items)]
                return state.render()

            def reverse(self, state: ParentState):
                state.items = list(reversed(state.items))
                state.second_items = list(reversed(state.second_items))
                return state.render()

        def template_data(self, kwargs, slots):
            return {"items": kwargs.get("items", []), "second_items": kwargs.get("second_items", [])}

    dispatcher_for(engine)
    html = Parent(items=[], second_items=[]).render().serialize()
    faults: list[str] = []
    console: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text) if message.type == "error" else None)
    base = serve_live(engine, html, "")
    page.goto(base + "/")
    assert page.locator(".run-child").count() == 0
    assert page.evaluate("[globalThis.__firstChildRuns || 0, globalThis.__secondChildRuns || 0]") == [0, 0]
    page.locator("#add-run-child").click()
    page.locator(".run-child").wait_for()
    assert page.locator(".run-child").get_attribute("data-local") == "7"
    assert page.locator(".run-child").get_attribute("data-citry-occurrence") == "authored"
    assert page.locator(".second-run-child").get_attribute("data-local") == "8"
    assert page.evaluate("[__firstChildRuns, __secondChildRuns]") == [1, 1]
    assert page.locator(".run-child").evaluate("element => getComputedStyle(element).color") == "rgb(1, 2, 3)"
    assert page.locator(".run-child").text_content() == "0"
    page.locator(".run-child").click()
    page.wait_for_function("document.querySelector('.run-child')?.textContent === '1'")
    assert page.evaluate("[__firstChildRuns, __secondChildRuns]") == [1, 1]
    page.locator("#add-run-child").click()
    page.wait_for_function("document.querySelectorAll('.run-child').length === 2")
    retained = page.evaluate(
        """() => {
          const app = [...__citryRuntime._apps.values()][0];
          globalThis.__retainedRuns = Object.fromEntries(
            [...document.querySelectorAll('.run-child')].map(element => {
              const mounted = [...app.mounted].find(([, value]) => value.component.$el === element);
              if (!mounted) throw new Error('run child has no mounted occurrence');
              return [element.dataset.item, {element, stableId: mounted[0]}];
            }),
          );
          return Object.fromEntries(
            Object.entries(globalThis.__retainedRuns).map(([item, value]) => [item, value.stableId]),
          );
        }"""
    )
    assert len(retained) == 2
    assert all(retained.values())
    page.locator("#reverse-run-children").click()
    page.wait_for_function("document.querySelector('.run-child')?.dataset.item === '1'")
    assert (
        page.evaluate(
            """() => {
          const app = [...__citryRuntime._apps.values()][0];
          return Object.fromEntries(
            [...document.querySelectorAll('.run-child')].map(element => {
              const retained = globalThis.__retainedRuns[element.dataset.item];
              const mounted = [...app.mounted].find(([, value]) => value.component.$el === element);
              return [element.dataset.item, retained?.element === element ? mounted?.[0] : null];
            }),
          );
        }"""
        )
        == retained
    )
    assert page.evaluate("__retainedRuns['0'].element.textContent") == "0"
    page.locator('.run-child[data-item="0"]').click()
    page.wait_for_function("__retainedRuns['0'].element.textContent === '1'")
    assert (
        page.evaluate(
            """() => {
          const app = [...__citryRuntime._apps.values()][0];
          const retained = globalThis.__retainedRuns['0'];
          return [...app.mounted].find(([, value]) => value.component.$el === retained.element)?.[0];
        }"""
        )
        == retained["0"]
    )
    assert page.evaluate("[__firstChildRuns, __secondChildRuns]") == [1, 1]
    assert faults == []
    assert console == []


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("leaf_template", "leaf_text"),
    [
        # Vue compiles every leaf and condenses its whitespace, so client
        # mount and hydration show the same condensed text whatever the tags.
        ("<section><strong>leaf \n  text</strong></section>", "leaf text"),
        ("<section><p>leaf \n  text</p></section>", "leaf text"),
    ],
)
def test_nested_leaf_whitespace_matches_client_mount_after_hydration(
    page: Any, serve_live: Any, leaf_template: str, leaf_text: str
) -> None:
    engine = Citry(autodiscover=False)

    class Leaf(Component):
        citry = engine
        template = leaf_template
        js = "$component({});"

    class Page(Component):
        citry = engine
        template = "<article>root \n  text<c-leaf /></article>"

    engine.set_mounted_prefix("/citry")
    rendered = Page().render()
    warnings: list[str] = []
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    _watch_citry_ready(page)
    observed = {}
    for ssr in (False, True):
        if ssr:
            page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
        html = rendered.serialize(ssr=ssr)
        assert ('"hydrate":true' in html) is ssr
        page.goto(serve_live(engine, html, "") + "/")
        page.wait_for_function("window.__citryReadyApps?.length === 1")
        observed[ssr] = page.evaluate(
            """() => ({leaf: document.querySelector('section').firstElementChild.textContent,
              probe: window.__citryHydrationReport || null})"""
        )
    assert observed[False]["leaf"] == observed[True]["leaf"] == leaf_text
    assert observed[True]["probe"]["mismatchCount"] == 0
    assert observed[True]["probe"]["replacedElementCount"] == 0
    assert warnings == [], warnings
