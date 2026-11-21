"""
Browser e2e for the page nonce that a host's own requests send.

A visitor has the same page open in two tabs, each loaded with its own CSP
nonce. Page code in each tab asks the host for a fragment the way htmx
does, sending `Citry.pageNonce()` in the `X-Citry-Page-Nonce` header, and
swaps the answer in with `innerHTML`. The host reads the header with
`page_nonce_from_headers()`, so each fragment carries its own tab's nonce
and starts there. A fragment written with the other tab's nonce is still
refused, so the runtime's nonce check is unchanged. An Events `Render`
answers with the header's nonce on its own when the app sets no
`_csp_nonce`.
"""

from __future__ import annotations

import threading
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, page_nonce_from_headers
from citry.contrib.wsgi import wsgi_app
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.e2e

# The Events component whose handler answers with a Render, and the server's base URL.
_Host = tuple[type[Component], str]

TAB_NONCES = ("dGFiLW9uZS1ub25jZQ", "dGFiLXR3by1ub25jZQ")

# Counts the fragment manager's refusals, so a test can wait for one instead of sleeping.
_RECORD_REFUSALS = """
window.__refusals = [];
const original = console.error;
console.error = (...args) => {
  if (String(args[0]).includes('discarded Vue fragment')) window.__refusals.push(args.map(String).join(' '));
  return original.apply(console, args);
};
"""

# What htmx does for a swap: ask the host for HTML and put it into the target. The
# header is the documented one, filled from the runtime, and sent only to the page's
# own origin.
_SWAP = """
async ({url, nonce}) => {
  const headers = {};
  const sent = nonce === undefined ? Citry.pageNonce() : nonce;
  if (sent) headers['X-Citry-Page-Nonce'] = sent;
  const response = await fetch(url, {headers});
  document.getElementById('target').innerHTML = await response.text();
  return {cacheControl: response.headers.get('cache-control'), vary: response.headers.get('vary')};
}
"""


def _policy(nonce: str) -> str:
    # No 'self' in script-src: only the nonce lets a script run, as on a strict site.
    return f"script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; connect-src 'self'; object-src 'none'"


def _page(nonce: str) -> str:
    return (
        f'<!DOCTYPE html><html><head></head><body><script nonce="{nonce}" src="/citry/citry.js"></script>'
        '<div id="target"></div></body></html>'
    )


class _Server(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _Quiet(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def host() -> Iterator[_Host]:
    """Serve a host app: Citry's routes, and a `/partial` view that answers like an htmx partial."""
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class NonceWidget(Component):
        citry = app
        template = '<button class="nonce-widget" v-text="label"></button>'

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "fragment ready"}

    class NonceLoader(Component):
        citry = app
        template = "<p>loader</p>"

        class Events:
            def load(self) -> actions.Render:
                return actions.Render(NonceWidget(), target="render:slot")

    dispatcher_for(app)
    citry_wsgi = wsgi_app(app)

    def wsgi(environ: dict[str, Any], start_response: Any) -> list[bytes]:
        path = environ.get("PATH_INFO", "")
        if path.startswith("/citry/"):
            sub = dict(environ, SCRIPT_NAME="/citry", PATH_INFO=path[len("/citry") :])
            return list(citry_wsgi(sub, start_response))
        # The host view: the documented recipe for a fragment that a page's own request loads.
        headers = {key[5:].replace("_", "-"): value for key, value in environ.items() if key.startswith("HTTP_")}
        nonce = page_nonce_from_headers(headers)
        body = NonceWidget().render().serialize(deps_strategy="fragment", csp_nonce=nonce).encode()
        sent = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))]
        if nonce is not None:
            sent += [("Cache-Control", "no-store"), ("Vary", "X-Citry-Page-Nonce")]
        start_response("200 OK", sent)
        return [body]

    server = make_server("127.0.0.1", 0, wsgi, server_class=_Server, handler_class=_Quiet)
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    yield NonceLoader, f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def _open_tab(context: Any, url: str, nonce: str) -> Any:
    tab = context.new_page()
    tab.add_init_script(_RECORD_REFUSALS)
    tab.route(
        url + "/",
        lambda route: route.fulfill(
            body=_page(nonce), content_type="text/html", headers={"Content-Security-Policy": _policy(nonce)}
        ),
    )
    tab.goto(url + "/")
    tab.wait_for_function("() => !!window.Citry?.fragments")
    return tab


def _started(tab: Any) -> None:
    tab.wait_for_function("() => document.querySelector('button.nonce-widget')?.textContent === 'fragment ready'")


def test_an_htmx_style_swap_in_each_tab_carries_that_tabs_nonce(context: Any, host: _Host) -> None:
    _app, url = host
    tabs = [_open_tab(context, url, nonce) for nonce in TAB_NONCES]
    for tab, nonce in zip(tabs, TAB_NONCES, strict=True):
        assert tab.evaluate("() => Citry.pageNonce()") == nonce
    # The older tab swaps last, which is where a nonce kept per session went wrong.
    for tab in reversed(tabs):
        marks = tab.evaluate(_SWAP, {"url": "/partial"})
        assert marks == {"cacheControl": "no-store", "vary": "X-Citry-Page-Nonce"}
    for tab in tabs:
        _started(tab)
        assert tab.evaluate("() => window.__refusals") == []


def test_a_fragment_with_the_other_tabs_nonce_is_still_refused(context: Any, host: _Host) -> None:
    _app, url = host
    tab = _open_tab(context, url, TAB_NONCES[0])
    tab.evaluate(_SWAP, {"url": "/partial", "nonce": TAB_NONCES[1]})
    tab.wait_for_function("() => window.__refusals.length === 1")
    assert "does not carry the page's CSP nonce" in tab.evaluate("() => window.__refusals[0]")
    assert tab.locator("button.nonce-widget").count() == 0


def test_an_events_render_answers_with_the_nonce_the_call_sent(context: Any, host: _Host) -> None:
    loader, url = host
    tabs = [_open_tab(context, url, nonce) for nonce in TAB_NONCES]
    for tab in tabs:
        # A client other than Citry's Vue runtime asks for an HTML fragment, as html-fragment/1 allows,
        # and sends its page's nonce; the app sets no `_csp_nonce`.
        action = tab.evaluate(
            "async (classId) => {"
            " const envelope = {protocol: 'citry-events/1', requestId: 'r1',"
            "   calls: [{componentClassId: classId, handlerName: 'load', args: {}}]};"
            " const response = await fetch('/citry/ext/events/call', {method: 'POST', headers: {"
            "   'Content-Type': 'application/json', 'X-Citry-Events': '1',"
            "   'X-Citry-Page-Nonce': Citry.pageNonce()}, body: JSON.stringify(envelope)});"
            " const [render] = (await response.json()).results[0].actions;"
            " document.getElementById('target').innerHTML = render.html;"
            " return {action: render.action, vary: response.headers.get('vary')}; }",
            loader.class_id,
        )
        assert action == {"action": "render", "vary": "X-Citry-Page-Nonce"}
    for tab in tabs:
        _started(tab)
        assert tab.evaluate("() => window.__refusals") == []
