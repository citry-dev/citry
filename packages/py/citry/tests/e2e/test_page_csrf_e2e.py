"""
Citry's browser runtime keeps one CSRF setting for the page.

``Citry.configure({csrf})`` sets it. Event calls read it unless
``Citry.events.configure({csrf})`` gave them their own token, and every
browser plugin reads it through ``host.csrfHeaders(url)``, which gives the
token only for a URL with the page's own origin. The Django locale-switch
tests that use it live in ``test_i18n_django_csrf_e2e.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e

_PROBE_PAGE = """<!doctype html><html><body><div id="app"></div></body></html>"""


def test_events_calls_read_the_page_csrf_setting(page: Any, serve_live: Any, open_citry_page: Any) -> None:
    # Events reads the same core setting: the cookie by default, then
    # Citry.configure, and Citry.events.configure still wins for event calls.
    engine = Citry(secret="page-csrf-events-secret", autodiscover=False)  # noqa: S106
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
    open_citry_page(serve_live(engine, Page(count=0).render().serialize(), "") + "/")
    page.evaluate(
        """() => {
          document.cookie = 'csrftoken=from-cookie; path=/';
          window.__sent = [];
          Citry.events.registerTransport('record', {
            async send(envelope, request) {
              window.__sent.push(Object.fromEntries(
                Object.entries(request.headers).filter(([name]) => !name.startsWith('X-Citry')),
              ));
              const response = await fetch(request.url, {
                method: request.method, headers: request.headers, body: JSON.stringify(envelope),
              });
              return response.json();
            },
          });
          Citry.events.configure({transport: 'record'});
        }"""
    )
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '1'")
    page.evaluate("Citry.configure({csrf: {token: 'from-page', header: 'X-Page-Token'}})")
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '2'")
    page.evaluate("Citry.events.configure({csrf: {token: 'from-events'}})")
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('#refresh')?.textContent === '3'")

    sent = page.evaluate("window.__sent")
    assert sent == [
        {"Content-Type": "application/citry-events+json", "X-CSRFToken": "from-cookie"},
        {"Content-Type": "application/citry-events+json", "X-Page-Token": "from-page"},
        {"Content-Type": "application/citry-events+json", "X-CSRFToken": "from-events"},
    ]


def test_plugin_host_gives_the_token_only_for_the_page_origin(page: Any) -> None:
    # A probe browser plugin keeps the host object the core passes every
    # plugin, so the test can ask it for headers directly.
    root = Path(__file__).parents[2] / "citry" / "_vue"
    page.route("http://citry.test/", lambda route: route.fulfill(body=_PROBE_PAGE, content_type="text/html"))
    page.goto("http://citry.test/")
    page.add_script_tag(content=(root / "runtime.js").read_text(encoding="utf-8"))
    result = page.evaluate(
        """async () => {
          const helperContract = __citryRuntime.compilerRuntime.helperContract;
          const digest = 'a'.repeat(64), definitionId = 'definition';
          window.__citryRuntimeDefinitions = {[definitionId]: {
            render(){ return Vue.h('div'); }, target:'ordinary-vnodes/1', helperContract,
            dynamicElements:[], directiveSignature:[], replacementSites:[], localCalls:[], localCallRuns:[],
            opaqueHtmlSites:[],
          }};
          __citryRuntime.registerTypeOptions('Root', digest, {});
          let host = null;
          __citryRuntime.registerBrowserPlugin('probe', 1, value => {
            host = value;
            return {install(){}, prepareRevision(){ return {}; }, activateRevision(){}, commitRevision(){},
              abortRevision(){}, rollbackRevision(){}, dispose(){}};
          });
          const manifest = {protocol:'citry-vue-prepared/1',appId:'probe-app',revision:0,rootId:'root',markers:[],
            occurrences:[{id:'root',typeKey:'Root',definitionId,parentId:null,placementKey:null,serverData:{},
              preparedData:{calls:{},selectedSlots:{}}}],
            definitions:[{id:definitionId,url:`/definitions/${digest}.js`,sha256:digest,target:'ordinary-vnodes/1',
              helperContract,dynamicElements:[],directiveSignature:[],replacementSites:[],localCalls:[],
              localCallRuns:[],opaqueHtmlSites:[],runtimeEventSites:[]}],
            scripts:[],styles:[],typePolicies:[{typeKey:'Root',lazyAllowed:false}],
            extensions:{probe:{schemaVersion:1,payload:{},templateContextNames:[]}}};
          await __citryRuntime.startPrepared({manifest,host:'#app',tags:{Root:'c-root'}});
          document.cookie = 'csrftoken=cookie-token; path=/';
          const urls = ['/citry/ext/i18n/messages', 'http://citry.test/x', 'https://citry.test/x',
            'http://citry.test:8080/x', 'http://other.test/x', '//other.test/x', '/\\\\other.test/x',
            '\\\\\\\\other.test/x', 'http://user@other.test/x', 'blob:http://other.test/x',
            'data:text/plain,x', 'javascript:alert(1)', 'http://[bad'];
          const headers = () => Object.fromEntries(urls.map(url => [url, host.csrfHeaders(url)]));
          const byCookie = headers();
          Citry.configure({csrf: {token: () => 'page-token', header: 'X-Page'}});
          const byPage = host.csrfHeaders('/x');
          const returned = host.csrfHeaders('/x');
          returned['X-Page'] = 'changed';
          const errors = [];
          for (const options of [{csrff: {}}, {csrf: {tokens: 'x'}}, {csrf: {header: 'bad header'}},
              {csrf: {header: 'Content-Type'}}, {csrf: {cookie: ''}}, {csrf: {token: 1}}, {csrf: []}, []]) {
            try { Citry.configure(options); errors.push(null); } catch (error) { errors.push(error.name); }
          }
          return {byCookie, byPage, afterMutation: host.csrfHeaders('/x'), errors};
        }"""
    )
    same = {"X-CSRFToken": "cookie-token"}
    assert result["byCookie"] == {
        "/citry/ext/i18n/messages": same,
        "http://citry.test/x": same,
        "https://citry.test/x": {},
        "http://citry.test:8080/x": {},
        "http://other.test/x": {},
        "//other.test/x": {},
        "/\\other.test/x": {},
        "\\\\other.test/x": {},
        "http://user@other.test/x": {},
        "blob:http://other.test/x": {},
        "data:text/plain,x": {},
        "javascript:alert(1)": {},
        "http://[bad": {},
    }
    assert result["byPage"] == {"X-Page": "page-token"}
    assert result["afterMutation"] == {"X-Page": "page-token"}
    assert result["errors"] == ["TypeError"] * 8
