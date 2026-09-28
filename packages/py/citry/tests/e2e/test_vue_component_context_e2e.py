"""
Browser tests for the `$component` initializer context and the version-skew prompt.

An initializer written for 0.5.1 destructures `state`, `sendEvent`, `loading`,
`error`, `i18n`, `els`, and `id` from its context, and may register itself as
`$component({init})`. These tests check that such an initializer still runs and
reads the same values the instance helpers give. The last tests check what the
page does when a call fails because the page's State token no longer verifies,
which is what a deploy does to a page that stays open.
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
        template = '<main id="aliases"><output id="count">{{ count }}</output></main>'
        # Each run records what the context fields read, then the first run
        # drives one successful and one failing call through `sendEvent`.
        js = """$component(function (context) {
          const {component, revision, id, els, state, sendEvent, loading, error, i18n} = context;
          (globalThis.__contextRuns ||= []).push({revision, id, els: els.map(el => el.id), count: state.count,
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
    for run in runs:
        assert run["els"] == ["aliases"]
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
        # `null` from `loading()` and `error()`, and a rejected `sendEvent`.
        js = """$component(({component, state, sendEvent, loading, error, els, id}) => {
          const report = {state, loading: loading(), error: error(), els: els.map(el => el.id), id};
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
    page.goto(serve_document(Ambiguous().render().serialize()))
    page.wait_for_timeout(500)
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
        document.addEventListener('citry:events:stale', event => {
          if (event.detail.reason !== 'version') return;
          event.preventDefault();
          window.__handledSkew += 1;
        });
        """
    )
    page.goto(serve_live(engine, skew(count=0).render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#skew')?.textContent === '0'")
    _sign_tokens_with_an_unknown_secret(page)
    page.locator("#skew").click()
    page.wait_for_function("window.__handledSkew === 1")
    page.wait_for_timeout(200)
    assert dialogs == []
