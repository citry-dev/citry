from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import pytest

from citry import Citry, Component, Extension
from citry.ext.events import EventError, actions, event
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
_PlaywrightTimeoutError = pytest.importorskip("playwright.sync_api").TimeoutError


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
                definitions: Object.fromEntries(Object.entries(window.CitryStableDefinitions || {})
                    .map(([id, value]) => [id, {
                        directiveSignature: value.directiveSignature,
                        replacementSites: value.replacementSites,
                        localCalls: value.localCalls,
                        localCallRuns: value.localCallRuns,
                        opaqueHtmlSites: value.opaqueHtmlSites,
                        runtimeEventSites: value.runtimeEventSites,
                    }])),
                declared: (() => {
                    const script = [...document.scripts].find(item =>
                        item.textContent.includes('CitryStable.startPrepared('),
                    );
                    if (!script) return 'no bootstrap script';
                    const text = script.textContent;
                    const start = text.indexOf('CitryStable.startPrepared(') + 'CitryStable.startPrepared('.length;
                    const end = text.indexOf(').catch', start);
                    try { return JSON.parse(text.slice(start, end)).manifest.definitions; }
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
          const app=[...CitryStable._apps.values()][0];
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
        js = """$component({onServerRender({component, revision}){
          component.$onEvent('ping', detail => (globalThis.__vueEventSeen ||= []).push({revision, detail}));
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
                  const app=[...CitryStable._apps.values()][0];
                  const component=app?.mounted.get(app.rootId)?.component;
                  return Boolean(component) && !app.busy && !component.$loading('refresh');
                }""",
                timeout=5_000,
            )
        except _PlaywrightTimeoutError as error:
            state = page.evaluate(
                """() => {
                  const app=[...CitryStable._apps.values()][0];
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
            appCount:globalThis.CitryStable?._apps?.size})"""
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
            appCount:globalThis.CitryStable?._apps?.size})"""
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
        """() => { const app=[...CitryStable._apps.values()][0];
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
                """() => { const app=[...CitryStable._apps.values()][0];
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
            """() => { const app=[...CitryStable._apps.values()][0];
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
        """() => { const app=[...CitryStable._apps.values()][0];
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
        """() => { const app=[...CitryStable._apps.values()][0];
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

    with page.expect_response("**/ext/events/call") as remove_response_info:
        page.locator("#remove-a").click()
    remove_response = remove_response_info.value
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
        pytest.fail(
            f"remove response {remove_response.status}: {remove_response.text()}; "
            f"render ids: {render_ids}; page errors: {faults}; page state: {page_state}"
        )
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
    assert "CitryStable.startPrepared" in html
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
    assert page.evaluate("[...CitryStable._apps.values()][0].terminal") is False
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
    page.wait_for_function("globalThis.CitryStable._apps.size === 0")
    assert faults == ["The Vue Events bridge was disposed."]


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
          (globalThis.__citryVueIdentities ??= []).push(CitryStable.compilerRuntime);
          return {setup(){return {count: CitryStable.compilerRuntime.ref(0)};}};
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
        "globalThis.__citryVueAfterFirst=globalThis.CitryStable.compilerRuntime;</script>"
        f'<section id="second-app">{second_html}</section>'
        "</body></html>"
    )
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(html))
    page.wait_for_timeout(500)
    assert page.evaluate("__vueAfterFirst === Vue && __citryVueAfterFirst === CitryStable.compilerRuntime")
    assert page.evaluate(
        "__citryVueIdentities.length >= 1 && __citryVueIdentities.every(x => x === CitryStable.compilerRuntime)"
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
    page.clock.pause_at(page.evaluate("new Date().toISOString()"))

    def timing_snapshot() -> dict[str, Any]:
        return page.evaluate(
            """() => {
              const app=CitryStable._apps.values().next().value;
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
          const app = [...CitryStable._apps.values()][0];
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
        """()=>{const app=[...CitryStable._apps.values()][0];return [...app.mounted.values()]
          .find(item=>item.record.occurrenceId!==app.rootId).record.generation}"""
    )
    page.locator("#slow-child").click()
    page.locator("#toggle-slow-child").click()
    assert page.locator("#slow-child").count() == 0
    page.locator("#toggle-slow-child").click()
    page.wait_for_function("document.querySelector('#slow-child')?.textContent === '0'")
    page.wait_for_function(
        "window.__citryGenerationSettled === true && [...CitryStable._apps.values()][0]?.busy === false"
    )
    assert page.locator("#slow-child").text_content() == "0"
    assert len(requests) == 1
    app_state = page.evaluate(
        """()=>{const app=[...CitryStable._apps.values()][0];const child=[...app.mounted.values()]
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
          const app = [...CitryStable._apps.values()][0];
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
          const app = [...CitryStable._apps.values()][0];
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
          const app = [...CitryStable._apps.values()][0];
          const retained = globalThis.__retainedRuns['0'];
          return [...app.mounted].find(([, value]) => value.component.$el === retained.element)?.[0];
        }"""
        )
        == retained["0"]
    )
    assert page.evaluate("[__firstChildRuns, __secondChildRuns]") == [1, 1]
    assert faults == []
    assert console == []
