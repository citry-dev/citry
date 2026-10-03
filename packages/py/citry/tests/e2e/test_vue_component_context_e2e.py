"""
Browser tests for the `$component` initializer context and the version-skew prompt.

An initializer written for 0.5.1 destructures `state`, `sendEvent`, `loading`,
`error`, `i18n`, `els`, and `id` from its context, and may register itself as
`$component({init})`. These tests check that such an initializer still runs and
reads the same values the instance helpers give, and that an async initializer
neither holds up the page nor stops it when it fails. The last tests check what
the page does when a call fails because the page's State token no longer
verifies, which is what a deploy does to a page that stays open, and what the
`citry:events:*` notifications report when the calling component is gone.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events import EventError, actions
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")

_RELOAD_PROMPT = "This page and the server are running different versions of the app. Reload to get back in sync?"


def _collect_page_errors(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


@pytest.mark.e2e
def test_initializer_context_exposes_the_instance_helpers_under_their_0_5_1_names(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-context-aliases-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Page(Component):
        citry = engine
        State = PageState
        # The `bump` render adds a second top-level element, so the component's
        # roots change between the first and second run.
        template = """
            <main id="aliases"><output id="count">{{ count }}</output></main>
            <aside id="extra" c-if="count > 0">bumped</aside>
        """
        # Each run records what the context fields read, then the first run
        # drives one successful and one failing call through `sendEvent`.
        js = """$component(function (context) {
          const {component, revision, id, els, state, sendEvent, loading, error, i18n} = context;
          globalThis.__firstEls ||= els;
          (globalThis.__contextRuns ||= []).push({revision, id, els: els.map(el => el.id), count: state.count,
            sameEls: els === globalThis.__firstEls,
            sameState: state === component.$state, loading: loading(), error: error(), i18n,
            idWritable: Object.getOwnPropertyDescriptor(context, 'id').set !== undefined});
          if (revision === 0) {
            sendEvent('bump').then(value => { globalThis.__bumpResult = value; });
          }
          if (revision === 1) {
            sendEvent('fail').catch(reason => {
              globalThis.__failReason = reason;
              globalThis.__failRead = {loading: loading('fail'), error: error('fail'), latest: error()};
            });
          }
        });"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def bump(self, state: PageState):
                state.count += 1
                return [state.render(), actions.Data({"bumped": state.count})]

            def fail(self):
                raise EventError("Deliberate failure.")

    dispatcher_for(engine)
    errors = _collect_page_errors(page)
    page.add_init_script(
        """
        window.__renderIds = [];
        document.addEventListener('citry:events:before', event => window.__renderIds.push(event.detail.instance));
        """
    )
    page.goto(serve_live(engine, Page(count=0).render().serialize(), "") + "/")
    page.wait_for_function("globalThis.__failRead !== undefined")

    runs = page.evaluate("globalThis.__contextRuns")
    render_ids = page.evaluate("window.__renderIds")
    assert [run["revision"] for run in runs] == [0, 1]
    # `id` is the server render ID that the Events lifecycle reports as `instance`.
    assert runs[0]["id"]
    assert runs[0]["id"] == render_ids[0]
    # The second run happens while `bump`, the call whose render it applies, is still settling.
    assert [run["loading"] for run in runs] == [False, True]
    assert [run["els"] for run in runs] == [["aliases"], ["aliases", "extra"]]
    # `els` is one array that Citry refills after each server render, so the
    # array the first run destructured now holds the new roots.
    assert page.evaluate("globalThis.__firstEls.map(el => el.id)") == ["aliases", "extra"]
    for run in runs:
        assert run["sameEls"] is True
        assert run["sameState"] is True
        assert run["error"] is None
        assert run["i18n"] is None
        assert run["idWritable"] is False
    assert [run["count"] for run in runs] == [0, 1]
    assert page.evaluate("globalThis.__bumpResult") == {"bumped": 1}
    fail_reason = page.evaluate("globalThis.__failReason")
    assert fail_reason["code"] == "invalid_args"
    assert page.evaluate("globalThis.__failRead") == {
        "loading": False,
        "error": fail_reason,
        "latest": fail_reason,
    }
    assert errors == []


@pytest.mark.e2e
def test_initializer_context_on_a_component_without_events_matches_0_5_1(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Plain(Component):
        citry = engine
        template = '<section id="plain">plain</section>'
        # 0.5.1 gave a component without Events a null `state`, `false` and
        # `null` from `loading()` and `error()`, a rejected `sendEvent`, and a
        # `$onEvent` that returned an unsubscribe function doing nothing.
        js = """$component(({component, state, sendEvent, loading, error, els, id}) => {
          const report = {state, loading: loading(), error: error(), els: els.map(el => el.id), id};
          try {
            const off = component.$onEvent('saved', () => {});
            report.onEvent = typeof off === 'function' ? String(off()) : typeof off;
          } catch (reason) { report.onEvent = 'threw: ' + String(reason); }
          let threw = null;
          let returned;
          try { returned = component.$sendEvent('save'); } catch (reason) { threw = String(reason); }
          report.instanceThrew = threw;
          report.instanceReturnedPromise = returned instanceof Promise;
          Promise.allSettled([sendEvent('save'), returned]).then(results => {
            report.rejections = results.map(result => [result.status, String(result.reason)]);
            globalThis.__plainContext = report;
          });
        });"""

    errors = _collect_page_errors(page)
    page.goto(serve_document(Plain().render().serialize()))
    page.wait_for_function("globalThis.__plainContext !== undefined")
    report = page.evaluate("globalThis.__plainContext")
    assert report["state"] is None
    assert report["loading"] is False
    assert report["error"] is None
    assert report["els"] == ["plain"]
    assert report["onEvent"] == "undefined"
    assert report["instanceThrew"] is None
    assert report["instanceReturnedPromise"] is True
    for status, reason in report["rejections"]:
        assert status == "rejected"
        assert "declares no Events class" in reason
        assert "$sendEvent('save')" in reason
    assert errors == []


@pytest.mark.e2e
def test_init_option_runs_as_the_server_render_initializer(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Legacy(Component):
        citry = engine
        template = '<button id="legacy" @click="clicks += 1" v-text="clicks"></button>'
        js = """$component({
          data() { return {clicks: 0}; },
          init({component, revision, els}) {
            globalThis.__initRun = {revision, els: els.map(el => el.id), clicks: component.clicks};
          },
        });"""

    errors = _collect_page_errors(page)
    page.goto(serve_document(Legacy().render().serialize()))
    page.wait_for_function("globalThis.__initRun !== undefined")
    assert page.evaluate("globalThis.__initRun") == {"revision": 0, "els": ["legacy"], "clicks": 0}
    page.locator("#legacy").click()
    page.wait_for_function("document.querySelector('#legacy')?.textContent === '1'")
    assert errors == []


@pytest.mark.e2e
def test_init_option_beside_on_server_render_is_rejected(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Ambiguous(Component):
        citry = engine
        template = '<p id="ambiguous">ambiguous</p>'
        js = """$component({
          init() { globalThis.__ambiguousRan = 'init'; },
          onServerRender() { globalThis.__ambiguousRan = 'onServerRender'; },
        });"""

    errors = _collect_page_errors(page)
    # The definition fails when its script runs, which the page reports as an error.
    with page.expect_event("pageerror"):
        page.goto(serve_document(Ambiguous().render().serialize()))
    assert any("both `init` and `onServerRender`" in error for error in errors), errors
    assert page.evaluate("globalThis.__ambiguousRan ?? null") is None


def _stale_token_page(engine: Citry) -> type[Component]:
    class SkewState:
        count: int = 0

        def render(self):
            return Skew(count=self.count)

    class Skew(Component):
        citry = engine
        State = SkewState
        template = '<button id="skew" @c-click="bump">{{ count }}</button>'

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def bump(self, state: SkewState):
                state.count += 1
                return state.render()

    return Skew


def _sign_tokens_with_an_unknown_secret(page: Any) -> None:
    # A deploy that changes the signing secret leaves the open page holding a
    # token whose signature no current secret matches. Rewriting the signature
    # segment in flight gives the real server exactly that token.
    def reroute(route: Any) -> None:
        body = route.request.post_data_json
        for call in body["calls"]:
            prefix, payload, signature = call["stateToken"].split(".")
            call["stateToken"] = f"{prefix}.{payload}.{'A' * len(signature)}"
        route.continue_(post_data=body)

    page.route("**/ext/events/call", reroute)


@pytest.mark.e2e
def test_stale_state_after_a_deploy_asks_once_to_reload(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-version-skew-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    skew = _stale_token_page(engine)
    dispatcher_for(engine)
    errors = _collect_page_errors(page)
    dialogs: list[str] = []

    def decline(dialog: Any) -> None:
        dialogs.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", decline)
    page.add_init_script(
        """
        window.__skewEvents = [];
        for (const name of ['stale', 'error'])
          document.addEventListener(`citry:events:${name}`, event => window.__skewEvents.push({
            name, reason: event.detail.reason ?? null, code: event.detail.error?.code ?? null,
            cancelable: event.cancelable}));
        """
    )
    page.goto(serve_live(engine, skew(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#skew')?.textContent === '0'")
    _sign_tokens_with_an_unknown_secret(page)

    page.locator("#skew").click()
    page.wait_for_function("window.__skewEvents.length === 2")
    page.locator("#skew").click()
    page.wait_for_function("window.__skewEvents.length === 4")

    stale = {"name": "stale", "reason": "version", "code": None, "cancelable": True}
    error = {"name": "error", "reason": None, "code": "stale_state", "cancelable": False}
    assert page.evaluate("window.__skewEvents") == [stale, error, stale, error]
    # The user declined the first prompt; the second failure must not ask again.
    assert dialogs == [_RELOAD_PROMPT]
    assert page.locator("#skew").text_content() == "0"
    # A declarative call reports its failure; nothing escapes as a page error.
    assert errors == []


@pytest.mark.e2e
def test_cancelling_the_version_notification_suppresses_the_reload_prompt(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-version-skew-cancel-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    skew = _stale_token_page(engine)
    dispatcher_for(engine)
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
    page.add_init_script(
        """
        window.__handledSkew = 0;
        window.__skewFinished = false;
        document.addEventListener('citry:events:stale', event => {
          if (event.detail.reason !== 'version') return;
          event.preventDefault();
          window.__handledSkew += 1;
        });
        document.addEventListener('citry:events:after', () => { window.__skewFinished = true; });
        """
    )
    page.goto(serve_live(engine, skew(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#skew')?.textContent === '0'")
    _sign_tokens_with_an_unknown_secret(page)
    page.locator("#skew").click()
    # Citry decides on the prompt right after the `stale` listeners return and
    # before `after` fires, so once `after` has fired no dialog can still come.
    page.wait_for_function("window.__skewFinished === true")
    assert page.evaluate("window.__handledSkew") == 1
    assert dialogs == []


@pytest.mark.e2e
def test_a_call_whose_component_is_gone_still_notifies_document_listeners(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-version-skew-gone-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    skew = _stale_token_page(engine)
    dispatcher_for(engine)
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
    # The listener cancels every cancellable notification, as a page that shows its
    # own update banner would, and records what arrives at `document`.
    page.add_init_script(
        """
        window.__goneEvents = [];
        for (const name of ['before', 'stale', 'error', 'after'])
          document.addEventListener(`citry:events:${name}`, event => {
            window.__goneEvents.push({
              name, instance: event.detail.instance, class: event.detail.class, event: event.detail.event,
              reason: event.detail.reason ?? null, ok: event.detail.ok ?? null});
            if (event.cancelable && name === 'stale') event.preventDefault();
          });
        """
    )
    page.goto(serve_live(engine, skew(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#skew')?.textContent === '0'")

    # Hold the call at the network layer so the component can be unmounted while
    # the call is still in flight, then let the stale token reach the server.
    held: list[Any] = []

    def hold(route: Any) -> None:
        held.append(route)

    page.route("**/ext/events/call", hold)
    page.locator("#skew").click()
    page.wait_for_function("window.__goneEvents.length === 1")
    deadline = 50
    while not held and deadline:
        page.wait_for_timeout(20)
        deadline -= 1
    assert held, "the event call never reached the network"
    page.evaluate("__citryRuntime._apps.values().next().value.vueApp.unmount()")
    held[0].continue_()
    page.wait_for_function("window.__goneEvents.some(item => item.name === 'after')")

    events = page.evaluate("window.__goneEvents")
    assert [item["name"] for item in events] == ["before", "stale", "after"]
    instance, component_class = events[0]["instance"], events[0]["class"]
    assert instance is not None
    assert component_class is not None
    # The page hears why the call's result was dropped even though no component
    # is left to start the event from, and the detail still names the component.
    assert events[1] == {
        "name": "stale",
        "instance": instance,
        "class": component_class,
        "event": "bump",
        "reason": "disposed",
        "ok": None,
    }
    assert events[2] == {
        "name": "after",
        "instance": instance,
        "class": component_class,
        "event": "bump",
        "reason": None,
        "ok": False,
    }
    assert dialogs == []


@pytest.mark.e2e
def test_async_initializer_runs_beside_the_page_and_its_cleanup_still_runs(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-async-init-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class AsyncState:
        count: int = 0

        def render(self):
            return AsyncInit(count=self.count)

    class AsyncInit(Component):
        citry = engine
        State = AsyncState
        template = """
            <button id="async-bump" @c-click="bump">{{ count }}</button>
        """
        # Runs 0 and 2 wait for the test to release them; run 1 fails after its
        # first await. Every step lands in one log, so the order is visible.
        js = """
            $component({
              async init({revision}) {
                const log = (window.__asyncLog ||= []);
                log.push('start:' + revision);
                if (revision === 0 || revision === 2)
                  await new Promise(resolve => { window['__release' + revision] = resolve; });
                else await null;
                log.push('end:' + revision);
                if (revision === 1) throw new Error('async init failed on purpose');
                return () => log.push('cleanup:' + revision);
              },
            });
        """

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def bump(self, state: AsyncState):
                state.count += 1
                return state.render()

    dispatcher_for(engine)
    errors = _collect_page_errors(page)
    console_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.add_init_script(
        """
        document.addEventListener('citry:ready', () => {
          window.__readyLog = [...(window.__asyncLog || [])];
        });
        """
    )
    page.goto(serve_live(engine, AsyncInit(count=0).render().serialize(), "") + "/")
    page.wait_for_function("window.__readyLog !== undefined")
    # The page became ready while the first run was still waiting.
    assert page.evaluate("window.__readyLog") == ["start:0"]
    page.evaluate("window.__release0()")
    page.wait_for_function("window.__asyncLog.includes('end:0')")

    # Server render 1: the resolved cleanup of run 0 runs first; run 1 then fails.
    page.locator("#async-bump").click()
    page.wait_for_function("window.__asyncLog.includes('end:1')")
    page.wait_for_function("document.querySelector('#async-bump')?.textContent === '1'")
    # Server render 2 starts a run that waits; render 3 replaces it before it resolves.
    page.locator("#async-bump").click()
    page.wait_for_function("window.__asyncLog.includes('start:2')")
    page.locator("#async-bump").click()
    page.wait_for_function("window.__asyncLog.includes('end:3')")
    # Run 2 is over, so the cleanup it resolves to runs at once instead of being kept.
    page.evaluate("window.__release2()")
    page.wait_for_function("window.__asyncLog.includes('cleanup:2')")

    assert page.evaluate("window.__asyncLog") == [
        "start:0",
        "end:0",
        "cleanup:0",
        "start:1",
        "end:1",
        "start:2",
        "start:3",
        "end:3",
        "end:2",
        "cleanup:2",
    ]
    assert page.locator("#async-bump").text_content() == "3"
    # The failed run is logged and does not stop the app or escape as a page error.
    assert any(text.startswith("[Citry] an async onServerRender callback failed:") for text in console_errors)
    assert errors == []


def _record_lifecycle_at_document() -> str:
    # Records every `citry:events:*` notification that reaches `document`, and
    # whether it started there rather than bubbling up from a component element.
    return """
        window.__lifecycle = [];
        for (const name of ['before', 'stale', 'error', 'after'])
          document.addEventListener(`citry:events:${name}`, event => window.__lifecycle.push({
            name, instance: event.detail.instance, class: event.detail.class,
            reason: event.detail.reason ?? null, startedAtDocument: event.target === document}));
        """


def _hold_event_calls(page: Any) -> list[Any]:
    held: list[Any] = []

    def hold(route: Any) -> None:
        held.append(route)

    page.route("**/ext/events/call", hold)
    return held


def _release_with_an_unknown_signature(route: Any) -> None:
    body = route.request.post_data_json
    for call in body["calls"]:
        prefix, payload, signature = call["stateToken"].split(".")
        call["stateToken"] = f"{prefix}.{payload}.{'A' * len(signature)}"
    route.continue_(post_data=body)


@pytest.mark.e2e
def test_a_stale_state_answer_for_a_component_without_elements_prompts_from_document(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="vue-version-skew-hidden-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class HiddenState:
        count: int = 0

        def render(self):
            return Hidden(count=self.count)

    class Hidden(Component):
        citry = engine
        State = HiddenState
        # A browser-only toggle removes the component's only element while it
        # stays mounted, so its Events notifications have no element to start from.
        template = """
            <button
                id="hidden-skew"
                v-if="shown"
                @c-click="bump"
            >{{ count }}</button>
        """
        js = """
            $component({
              data() { return {shown: true}; },
              mounted() { window.__hidden = this; },
            });
        """

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def bump(self, state: HiddenState):
                state.count += 1
                return state.render()

    dispatcher_for(engine)
    errors = _collect_page_errors(page)
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
    page.add_init_script(_record_lifecycle_at_document())
    page.goto(serve_live(engine, Hidden(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#hidden-skew')?.textContent === '0'")
    held = _hold_event_calls(page)
    page.locator("#hidden-skew").click()
    page.wait_for_function("window.__lifecycle.length === 1")
    page.evaluate("window.__hidden.shown = false")
    page.wait_for_function("document.querySelector('#hidden-skew') === null")
    assert len(held) == 1
    _release_with_an_unknown_signature(held[0])
    page.wait_for_function("window.__lifecycle.some(item => item.name === 'after')")

    events = page.evaluate("window.__lifecycle")
    instance = events[0]["instance"]
    assert instance is not None
    assert [(item["name"], item["reason"], item["startedAtDocument"]) for item in events] == [
        ("before", None, False),
        ("stale", "version", True),
        ("error", None, True),
        ("after", None, True),
    ]
    assert {item["instance"] for item in events} == {instance}
    # No listener cancelled the `stale` event at `document`, so Citry asked to reload.
    assert dialogs == [_RELOAD_PROMPT]
    assert errors == []


@pytest.mark.e2e
def test_an_unmounted_component_keeps_its_id_and_its_dropped_call_does_not_prompt(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-version-skew-unmounted-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class ChildState:
        count: int = 0

        def render(self):
            return SkewChild(count=self.count)

    class SkewChild(Component):
        citry = engine
        State = ChildState
        template = """
            <button id="child-skew" @c-click="bump">{{ count }}</button>
        """

        def template_data(self, kwargs, slots):
            return {"count": kwargs.get("count", 0)}

        class Events:
            def bump(self, state: ChildState):
                state.count += 1
                return state.render()

    engine.register(SkewChild)

    class Holder(Component):
        citry = engine
        template = """
            <main>
                <button id="drop-child" @click="show = false">drop</button>
                <template v-if="show"><c-skew-child /></template>
            </main>
        """
        js = """
            $component({
              data() { return {show: true}; },
            });
        """

    dispatcher_for(engine)
    errors = _collect_page_errors(page)
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
    page.add_init_script(_record_lifecycle_at_document())
    page.goto(serve_live(engine, Holder().render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#child-skew')?.textContent === '0'")
    held = _hold_event_calls(page)
    page.locator("#child-skew").click()
    page.wait_for_function("window.__lifecycle.length === 1")
    # Unmounting the child cancels its call, while the app and its Events bridge stay live.
    page.locator("#drop-child").click()
    page.wait_for_function("window.__lifecycle.some(item => item.name === 'after')")
    assert len(held) == 1
    # The server would answer `stale_state`, but the browser already dropped the call.
    _release_with_an_unknown_signature(held[0])

    events = page.evaluate("window.__lifecycle")
    instance, component_class = events[0]["instance"], events[0]["class"]
    assert instance is not None
    assert [(item["name"], item["reason"], item["startedAtDocument"]) for item in events] == [
        ("before", None, False),
        ("stale", "retired", True),
        ("after", None, True),
    ]
    assert {(item["instance"], item["class"]) for item in events} == {(instance, component_class)}
    assert dialogs == []
    assert errors == []
