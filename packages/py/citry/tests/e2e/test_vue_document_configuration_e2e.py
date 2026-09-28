"""
Browser proof for how a document app receives its start configuration.

The server sends each document app's configuration as a JSON data block
(``<script type="application/json" data-citry-vue-document="...">``) and
a one-line module script that asks the runtime to start that app. These
tests load such pages in Chromium and check that the app starts at the
documented point (after parsing, before ``DOMContentLoaded``), that
page data cannot break out of the block, and that nonce and hash based
Content Security Policies accept the page without listing the data block.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from citry import Citry, Component

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

NONCE = "cmVxdWVzdE5vbmNl"

# Values that would end the data block or open a new script element if the
# server wrote them into the JSON unescaped.
HOSTILE = {
    "close": "</script><script>window.__pwned = 1</script>",
    "comment": "<!--<script>",
    "separators": "a\u2028b\u2029c",
}

# Record, the first time the runtime starts a document app, whether parsing
# has finished and whether DOMContentLoaded has fired yet. The runtime assigns
# window.__citryRuntime once while it loads, so a setter wraps startDocument
# before the start script calls it. Also collect CSP violations and the ids
# of apps that reported citry:ready.
_RECORD_SCRIPT = """
window.__starts = [];
window.__violations = [];
window.__ready = [];
window.__domContentLoaded = false;
document.addEventListener('DOMContentLoaded', () => { window.__domContentLoaded = true; });
document.addEventListener('securitypolicyviolation', event => {
  window.__violations.push(event.violatedDirective + ' ' + event.blockedURI);
});
document.addEventListener('citry:ready', event => window.__ready.push(event.detail.appId));
let stable;
Object.defineProperty(window, '__citryRuntime', {
  configurable: true,
  get: () => stable,
  set: value => {
    const start = value.startDocument;
    value.startDocument = (...args) => {
      window.__starts.push({
        appId: args[0],
        readyState: document.readyState,
        domContentLoaded: window.__domContentLoaded,
      });
      return start(...args);
    };
    stable = value;
  },
});
"""


def _page_class(engine: Citry) -> type[Component]:
    """A page that shows the hostile values through Vue and has local state."""

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Configuration</title></head>
  <body>
    <main>
      <p
        id="close"
        v-text="hostile.close"
      ></p>
      <p
        id="comment"
        v-text="hostile.comment"
      ></p>
      <p
        id="separators"
        v-text="hostile.separators"
      ></p>
      <button
        id="add"
        type="button"
        @click="count++"
      >Add</button>
      <output
        id="count"
        v-text="count"
      ></output>
    </main>
  </body>
</html>
"""
        js = """
$component({data(){return {count: 0};}});
"""

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, object]:
            return {"hostile": HOSTILE}

    return Page


def _widget_class(engine: Citry, name: str) -> type[Component]:
    """A component without a document shell, so several can share one page."""
    return type(
        name,
        (Component,),
        {
            "citry": engine,
            "template": f"""
<div class="{name}">
  <button
    type="button"
    @click="count++"
  >Add</button>
  <output v-text="count"></output>
</div>
""",
            "js": """
$component({data(){return {count: 0};}});
""",
        },
    )


def _open(page: Any, url: str, *, apps: int = 1) -> tuple[list[str], list[str]]:
    """Load one page, wait until its apps are ready, and return page errors and console problems."""
    faults: list[str] = []
    console: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text) if message.type in {"warning", "error"} else None)
    page.add_init_script(_RECORD_SCRIPT)
    page.goto(url)
    page.wait_for_function(f"window.__ready.length === {apps}")
    return faults, console


def _serve_with_policy(page: Any, serve_document: Any, html: str, policy: str) -> str:
    """Serve ``html`` with a Content-Security-Policy header and return its URL."""
    url = serve_document(html)
    page.route(
        url,
        lambda route: route.fulfill(body=html, content_type="text/html", headers={"Content-Security-Policy": policy}),
    )
    return url


def _assert_page_works(page: Any) -> None:
    """The hostile values arrive as text, nothing they contain ran, and events work."""
    assert page.text_content("#close") == HOSTILE["close"]
    assert page.text_content("#comment") == HOSTILE["comment"]
    assert page.text_content("#separators") == HOSTILE["separators"]
    assert page.evaluate("window.__pwned") is None
    # Exactly one data block and one start script: the values opened nothing new.
    assert page.evaluate("document.querySelectorAll('script[data-citry-vue-document]').length") == 1
    assert page.evaluate("[...document.scripts].filter(script => script.type === 'module').length") == 1
    page.click("#add")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")


@pytest.mark.parametrize("ssr", [True, False], ids=["hydrating", "client-mount"])
def test_app_starts_after_parsing_and_before_domcontentloaded(page: Any, serve_document: Any, ssr: bool) -> None:
    html = _page_class(Citry(autodiscover=False))().render().serialize(ssr=ssr)
    assert ('"hydrate":true' in html) is ssr

    faults, console = _open(page, serve_document(html))
    [start] = page.evaluate("window.__starts")
    # "interactive" means the browser finished parsing; DOMContentLoaded has
    # not fired yet because it waits for module scripts.
    assert start["readyState"] == "interactive"
    assert start["domContentLoaded"] is False
    assert page.evaluate("window.__ready") == [start["appId"]]
    _assert_page_works(page)
    assert faults == [], faults
    assert console == [], console


def test_nonce_policy_runs_the_start_script_and_ignores_the_data_block(page: Any, serve_document: Any) -> None:
    html = _page_class(Citry(autodiscover=False, security_csp="strict"))().render().serialize(csp_nonce=NONCE)
    policy = f"default-src 'self'; script-src 'nonce-{NONCE}'; style-src 'self' 'nonce-{NONCE}'"

    faults, console = _open(page, _serve_with_policy(page, serve_document, html, policy))
    # The browser hides a nonce from getAttribute once a policy uses it, so
    # this shows the policy was active while Citry's scripts ran.
    assert page.evaluate("[...document.scripts].every(script => script.nonce && !script.getAttribute('nonce'))")
    _assert_page_works(page)
    assert page.evaluate("window.__violations") == []
    assert faults == [], faults
    assert console == [], console


def test_data_block_needs_no_nonce_but_the_runtime_refuses_one_without_it(page: Any, serve_document: Any) -> None:
    html = _page_class(Citry(autodiscover=False, security_csp="strict"))().render().serialize(csp_nonce=NONCE)
    # Remove the nonce from the data block only, as injected markup would lack it.
    stripped, count = re.subn(
        r'(<script type="application/json" data-citry-vue-document="[^"]+") nonce="[^"]+"', r"\1", html
    )
    assert count == 1
    policy = f"default-src 'self'; script-src 'nonce-{NONCE}'; style-src 'self' 'nonce-{NONCE}'"
    url = _serve_with_policy(page, serve_document, stripped, policy)

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.add_init_script(_RECORD_SCRIPT)
    page.goto(url)
    page.wait_for_function("window.__starts.length === 1")
    page.wait_for_function("document.readyState === 'complete'")
    # The policy did not block or report the data block: a data block is not
    # a script the browser runs, so CSP never applies to it.
    assert page.evaluate("window.__violations") == []
    configuration = page.evaluate("JSON.parse(document.querySelector('script[data-citry-vue-document]').textContent)")
    assert configuration["manifest"]["appId"] == page.evaluate("window.__starts[0].appId")
    # The runtime itself refuses a block without the page nonce.
    assert any("does not carry the page's CSP nonce" in fault for fault in faults), faults
    assert page.evaluate("window.__ready") == []


def test_hash_policy_lists_the_start_script_but_not_the_data_block(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False, security_script_integrity="citry")
    result = _page_class(engine)().render().serialize_result()
    hashes = result.security.csp_script_hashes
    policy = f"script-src {' '.join(hashes)}"
    # Only executable scripts are listed: the inline runtime, the component
    # code, and the one-line start script.
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]+">(.*?)</script>', result.html, re.DOTALL
    )
    assert match is not None
    assert len(match.group(1)) > 1_000
    assert len(hashes) == result.html.count("<script") - 1

    faults, console = _open(page, _serve_with_policy(page, serve_document, result.html, policy))
    _assert_page_works(page)
    assert page.evaluate("window.__violations") == []
    assert faults == [], faults
    assert console == [], console


def test_several_apps_on_one_page_each_start_from_their_own_block(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)
    first = _widget_class(engine, "first")().render().serialize()
    second = _widget_class(engine, "second")().render().serialize()
    html = f"<!doctype html><html><head></head><body>{first}{second}</body></html>"
    assert html.count("data-citry-vue-document=") == 2

    faults, console = _open(page, serve_document(html), apps=2)
    starts = page.evaluate("window.__starts")
    assert len({start["appId"] for start in starts}) == 2
    assert sorted(page.evaluate("window.__ready")) == sorted(start["appId"] for start in starts)
    # Each app owns its own state: clicking one leaves the other alone.
    page.click(".first button")
    page.wait_for_function("document.querySelector('.first output').textContent === '1'")
    assert page.text_content(".second output") == "0"
    assert faults == [], faults
    assert console == [], console


def test_fragment_inserted_into_a_document_page_starts_beside_it(page: Any, serve_live: Any) -> None:
    engine = Citry(autodiscover=False)
    engine.set_mounted_prefix("/citry")
    page_html = _page_class(engine)().render().serialize()
    fragment_html = _widget_class(engine, "fragment")().render().serialize(deps_strategy="fragment")
    # The fragment keeps its own descriptor format; only documents use the
    # data block that the start script names.
    assert "data-citry-vue-fragment" in fragment_html
    assert "data-citry-vue-document" not in fragment_html

    faults, console = _open(page, serve_live(engine, page_html, fragment_html) + "/")
    _assert_page_works(page)
    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text()).then((html) => {"
        " const target = document.createElement('div'); target.id = 'target';"
        " document.body.append(target); target.innerHTML = html; })"
    )
    page.wait_for_function("window.__ready.length === 2")
    page.click(".fragment button")
    page.wait_for_function("document.querySelector('.fragment output').textContent === '1'")
    # The fragment started through the fragment manager, not startDocument.
    assert len(page.evaluate("window.__starts")) == 1
    assert faults == [], faults
    assert console == [], console
