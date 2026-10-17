"""
Browser proof that an interactive page's content is in its served HTML by default.

With the default settings a page the server can write for Vue hydrates, and a
page it cannot write that way carries Citry's ordinary server HTML inside the
Vue host. Vue's client mount clears the host before it builds the page, so
that HTML is only what the browser shows (and a crawler reads) until then.
These tests load each kind of page in Chromium and check what the browser
shows before and after Vue starts.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

# Record what the host holds while the browser parses it (before any script
# runs Vue) and the first time the DOM changes after that. The mount clears
# the host and builds the page in one task, so the first change the observer
# reports must already show the finished page, never an empty host.
_WATCH_HOST_SCRIPT = """<script>(() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  window.__servedText = host.textContent;
  window.__servedElements = [...host.querySelectorAll('*')];
  new MutationObserver((_, observer) => {
    window.__firstChangeText = host.textContent;
    observer.disconnect();
  }).observe(host, {childList: true, subtree: true});
})();</script>"""


def _with_watch(html: str) -> str:
    """Insert the watch script right before the script that starts the app."""
    bootstrap = html.rfind("<script", 0, html.index('<script type="application/json" data-citry-vue-document='))
    return html[:bootstrap] + _WATCH_HOST_SCRIPT + html[bootstrap:]


def _open(page: Any, url: str) -> tuple[list[str], list[str]]:
    """Load one page, wait until its app is ready, and return its page errors and console problems."""
    faults: list[str] = []
    console: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: console.append(message.text) if message.type in {"warning", "error"} else None)
    # The listener must exist before the runtime dispatches citry:ready.
    page.add_init_script(
        "window.__citryReadyApps = [];"
        "document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));"
    )
    page.goto(url)
    page.wait_for_function("window.__citryReadyApps?.length === 1")
    return faults, console


def _counter_page(engine: Citry) -> type[Component]:
    """A small interactive page with Python text, a child component, and local Vue state."""

    class Note(Component):
        citry = engine
        template = """
<p id="note">Written by {{ author }}</p>
"""

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"author": "Ada"}

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Counter</title></head>
  <body>
    <main>
      <h1 id="title">Served heading</h1>
      <c-Note />
      <button
        id="add"
        type="button"
        @click="count++"
      >Add</button>
      <output id="count" v-text="count"></output>
    </main>
  </body>
</html>
"""
        js = """
$component({data(){return {count: 0};}});
"""

    return Page


def test_small_page_hydrates_by_default_and_adopts_every_served_element(page: Any, serve_document: Any) -> None:
    rendered = _counter_page(Citry(autodiscover=False))().render()
    html = rendered.serialize()

    # The content is in the served HTML, written for Vue to adopt.
    assert '"hydrate":true' in html
    assert "Served heading" in html.split("<script", 1)[0]
    assert "Written by Ada" in html.split("<script", 1)[0]
    admission = hydration_admission(rendered)
    assert admission is not None
    assert (admission.hydrated, admission.shell_count) == (True, 0)

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    faults, console = _open(page, serve_document(html))
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    assert report["replacedElementCount"] == 0, report

    # Events and local state work on the adopted nodes.
    page.click("#add")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    assert faults == [], faults
    assert console == [], console


# Record the document's parse state each time the runtime starts an app. The
# runtime assigns window.__citryRuntime once while it loads, so a setter wraps
# startDocument before the start script can call it.
_RECORD_START_STATE_SCRIPT = """
window.__startStates = [];
let stable;
Object.defineProperty(window, '__citryRuntime', {
  configurable: true,
  get() { return stable; },
  set(value) {
    const start = value.startDocument;
    value.startDocument = (...args) => {
      window.__startStates.push(document.readyState);
      return start(...args);
    };
    stable = value;
  },
});
"""


@pytest.mark.parametrize("nonce", [None, "cmVxdWVzdE5vbmNl"])
def test_app_starts_after_the_browser_has_parsed_the_served_page(
    page: Any, serve_document: Any, nonce: str | None
) -> None:
    # Starting the app takes tens of milliseconds on a large page. The start
    # script is a module script so that work waits until the whole page is
    # parsed and never holds back the first paint of the served HTML.
    engine = Citry(autodiscover=False, security_csp="strict") if nonce else Citry(autodiscover=False)
    html = _counter_page(engine)().render().serialize(csp_nonce=nonce)
    # A strict CSP page serves its content for Vue to replace instead of
    # hydrating it (see the CSP tests below); both kinds start the same way.
    assert ('"hydrate":true' in html) is (nonce is None)
    url = serve_document(html)
    if nonce:
        # A nonce policy must still let the module start script run.
        policy = f"default-src 'self'; script-src 'nonce-{nonce}'; style-src 'self' 'nonce-{nonce}'"
        page.route(
            url,
            lambda route: route.fulfill(
                body=html, content_type="text/html", headers={"Content-Security-Policy": policy}
            ),
        )

    page.add_init_script(_RECORD_START_STATE_SCRIPT)
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    faults, console = _open(page, url)
    # "interactive" means parsing has finished; a classic script at the end
    # of the body would see "loading".
    assert page.evaluate("window.__startStates") == ["interactive"]
    assert page.evaluate("[...document.scripts].filter(script => script.type === 'module').length") == 1
    if nonce is None:
        page.wait_for_function("window.__citryHydrationReport !== undefined")
        report = page.evaluate("window.__citryHydrationReport")
        assert report["mountError"] is None, report
        assert report["mismatchCount"] == 0, report

    # Events and local state still work after the later start.
    page.click("#add")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    assert faults == [], faults
    assert console == [], console


def test_threshold_opt_out_sends_an_empty_host_and_mounts_in_the_browser(page: Any, serve_document: Any) -> None:
    rendered = _counter_page(Citry(autodiscover=False, ssr_element_threshold=1_000))().render()
    html = rendered.serialize()

    # Below the chosen size the page is sent without its content.
    assert '"hydrate":true' not in html
    assert re.search(r'<div id="citry-vue-[^"]+"></div>', html)
    admission = hydration_admission(rendered)
    assert admission is not None
    assert (admission.reason, admission.server_html) == ("below-threshold", False)

    faults, console = _open(page, serve_document(_with_watch(html)))
    assert page.evaluate("window.__servedText") == ""
    assert page.text_content("#title") == "Served heading"
    page.click("#add")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    assert faults == [], faults
    assert console == [], console


def _host_root_page(engine: Citry) -> type[Component]:
    """A page that cannot hydrate: a browser-only v-if sits directly in the body."""

    class Note(Component):
        citry = engine
        template = """
<p id="note">Written by {{ author }}</p>
"""

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"author": "Ada"}

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Counter</title></head>
  <body>
    <p
      id="banner"
      v-if="count > 0"
    >Clicked</p>
    <h1 id="title">Served heading</h1>
    <c-Note />
    <button
      id="add"
      type="button"
      @click="count++"
    >Add</button>
    <output id="count" v-text="count"></output>
  </body>
</html>
"""
        js = """
$component({data(){return {count: 0};}});
"""

    return Page


def _assert_mounted_over_served_html(page: Any) -> None:
    """Check the served content, the replace, and the page's behavior after Vue mounts."""
    # Before Vue ran, the host already showed the page's content.
    served = page.evaluate("window.__servedText")
    assert "Served heading" in served
    assert "Written by Ada" in served
    # The first DOM change already shows the finished page: Vue cleared the
    # host and built the page in one task, so no empty host was painted.
    assert "Served heading" in page.evaluate("window.__firstChangeText")
    # Vue replaced every served element rather than adopting it, and no id
    # appears twice.
    assert page.evaluate("() => window.__servedElements.every(element => !element.isConnected)"), (
        "a served element survived the mount"
    )
    for element_id in ("title", "note", "add", "count"):
        assert page.locator(f"#{element_id}").count() == 1, element_id
    # The v-if branch the served HTML showed is gone until state selects it.
    assert page.locator("#banner").count() == 0
    # Events and local state work after the mount.
    page.click("#add")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    assert page.locator("#banner").count() == 1


def test_page_that_cannot_hydrate_serves_its_content_and_works_after_mount(page: Any, serve_document: Any) -> None:
    rendered = _host_root_page(Citry(autodiscover=False))().render()
    html = rendered.serialize()

    assert '"hydrate":true' not in html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert (admission.reason, admission.server_html) == ("host-root", True)

    faults, console = _open(page, serve_document(_with_watch(html)))
    _assert_mounted_over_served_html(page)
    assert faults == [], faults
    assert console == [], console


def test_served_content_is_readable_without_javascript(browser: Any, serve_document: Any) -> None:
    html = _host_root_page(Citry(autodiscover=False))().render().serialize()
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(serve_document(html))
        assert page.text_content("#title") == "Served heading"
        assert page.text_content("#note") == "Written by Ada"
    finally:
        context.close()


def test_csp_page_serves_its_content_and_works_under_a_nonce_policy(page: Any, serve_document: Any) -> None:
    nonce = "cmVxdWVzdE5vbmNl"
    rendered = _host_root_page(Citry(autodiscover=False, security_csp="strict"))().render()
    html = rendered.serialize(csp_nonce=nonce)
    admission = hydration_admission(rendered)
    assert admission is not None
    assert (admission.reason, admission.server_html) == ("security-policy", True)

    # The watch script needs the nonce too, or the policy blocks it.
    watched = _with_watch(html).replace(
        _WATCH_HOST_SCRIPT, _WATCH_HOST_SCRIPT.replace("<script>", f'<script nonce="{nonce}">')
    )
    url = serve_document(watched)
    policy = f"default-src 'self'; script-src 'nonce-{nonce}'; style-src 'self' 'nonce-{nonce}'"
    page.route(
        url,
        lambda route: route.fulfill(
            body=watched,
            content_type="text/html",
            headers={"Content-Security-Policy": policy},
        ),
    )
    faults, console = _open(page, url)
    # The browser hides a nonce from getAttribute once a policy uses it, so
    # this shows the policy was active while Citry's scripts ran.
    assert page.evaluate("() => [...document.scripts].every(script => script.nonce && !script.getAttribute('nonce'))")
    _assert_mounted_over_served_html(page)
    assert faults == [], faults
    assert console == [], console


def test_csp_page_blocks_inline_styles_in_the_served_html_until_vue_applies_them(
    page: Any, serve_document: Any
) -> None:
    nonce = "cmVxdWVzdE5vbmNl"
    engine = Citry(autodiscover=False, security_csp="strict")

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Styled</title></head>
  <body>
    <p v-if="shown">browser only</p>
    <h1
      id="title"
      style="color: rgb(200, 0, 0)"
    >Styled heading</h1>
  </body>
</html>
"""
        js = """
$component({data(){return {shown: false};}});
"""

    html = Page().render().serialize(csp_nonce=nonce)
    url = serve_document(html)
    policy = f"default-src 'self'; script-src 'nonce-{nonce}'; style-src 'self' 'nonce-{nonce}'"
    page.route(
        url,
        lambda route: route.fulfill(body=html, content_type="text/html", headers={"Content-Security-Policy": policy}),
    )
    faults, console = _open(page, url)
    # A policy without 'unsafe-inline' blocks the style attribute the browser
    # parsed from the served HTML and reports it once. Vue then sets the same
    # style through the DOM, which the policy allows.
    assert faults == [], faults
    assert len(console) == 1, console
    assert "style" in console[0]
    assert page.evaluate("getComputedStyle(document.querySelector('#title')).color") == "rgb(200, 0, 0)"


# Record what the page shows while the browser parses it, before any script
# runs Vue, and put focus on an element outside every shell.
_WATCH_SHELLS_SCRIPT = """<script>(() => {
  const host = document.querySelector('[id^="citry-vue-"]');
  window.__servedText = host.textContent;
  window.__servedPanelElements = [...document.querySelectorAll('#panel *')];
  window.__servedScriptRuns = window.__shellScriptRuns;
  document.querySelector('#outside').focus();
})();</script>"""


def _shell_page(engine: Citry) -> type[Component]:
    """A hydrated page with two shells: one whose Citry HTML is served, one holding a script."""

    class Note(Component):
        citry = engine
        template = """
<p id="note">Written by {{ author }}</p>
"""

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"author": "Ada"}

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Shells</title></head>
  <body>
    <main>
      <input
        id="outside"
        type="text"
        aria-label="Outside"
      />
      <div id="panel">
        <p
          v-if="open"
          id="opened"
          class="a"
        >Opened panel</p>
        <p
          v-else
          id="closed"
          class="b"
        >Closed panel</p>
        <c-Note />
      </div>
      <div id="scripted">
        <p v-if="open">Open extra</p>
        <c-raw><script>window.__shellScriptRuns = (window.__shellScriptRuns || 0) + 1;</script><b>raw</b></c-raw>
      </div>
      <button
        id="toggle"
        type="button"
        @click="open = !open"
      >Toggle</button>
    </main>
  </body>
</html>
"""
        js = """
$component({data(){return {open: false};}});
"""

    return Page


def test_shell_contents_are_served_then_rebuilt_by_vue(page: Any, serve_document: Any) -> None:
    rendered = _shell_page(Citry(autodiscover=False))().render()
    html = rendered.serialize()

    assert '"hydrate":true' in html
    assert '"emptyShells":true' in html
    admission = hydration_admission(rendered)
    assert admission is not None
    # The panel shows Citry's HTML until Vue builds it; the other shell stays
    # empty, because its HTML holds a script the browser would run.
    assert [(item.shell_tag, item.shell_content) for item in admission.declines] == [
        ("div", True),
        ("div", False),
    ]

    watched = html.replace("<script", _WATCH_SHELLS_SCRIPT + "<script", 1)
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    faults, console = _open(page, serve_document(watched))
    page.wait_for_function("window.__citryHydrationReport !== undefined")

    # Before Vue ran, the page showed both branches and the child, as
    # the server writes for a shell, and no script from a shell ran.
    served = page.evaluate("window.__servedText")
    for text in ("Opened panel", "Closed panel", "Written by Ada"):
        assert text in served
    assert "raw" not in served
    assert page.evaluate("window.__servedScriptRuns") is None
    assert page.evaluate("window.__shellScriptRuns") is None

    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    assert report["replacedElementCount"] == 0, report
    # Vue built the panel anew: the branch its state selects, with that
    # branch's own attributes, and none of the served elements.
    assert page.locator("#opened").count() == 0
    assert page.get_attribute("#closed", "class") == "b"
    assert page.evaluate("() => window.__servedPanelElements.every(element => !element.isConnected)")
    for element_id in ("closed", "note", "outside", "toggle"):
        assert page.locator(f"#{element_id}").count() == 1, element_id
    # Vue inserts the raw HTML with its script, which never runs.
    assert page.text_content("#scripted b") == "raw"
    # Focus outside the shells stays where the reader put it.
    assert page.evaluate("document.activeElement.id") == "outside"

    # Events and local state work in the rebuilt shells.
    page.click("#toggle")
    page.wait_for_selector("#opened")
    assert page.get_attribute("#opened", "class") == "a"
    assert page.locator("#closed").count() == 0
    assert page.evaluate("window.__shellScriptRuns") is None
    assert faults == [], faults
    assert console == [], console


def test_shell_contents_are_readable_without_javascript(browser: Any, serve_document: Any) -> None:
    html = _shell_page(Citry(autodiscover=False))().render().serialize()
    context = browser.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(serve_document(html))
        assert page.text_content("#closed") == "Closed panel"
        assert page.text_content("#note") == "Written by Ada"
    finally:
        context.close()


def test_shell_style_attributes_are_blocked_by_a_page_policy_until_vue_applies_them(
    page: Any, serve_document: Any
) -> None:
    engine = Citry(autodiscover=False)

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Styled shell</title></head>
  <body>
    <main>
      <div id="shell">
        <p v-if="shown">browser only</p>
        <h1
          id="title"
          style="color: rgb(200, 0, 0)"
        >Styled heading</h1>
      </div>
    </main>
  </body>
</html>
"""
        js = """
$component({data(){return {shown: false};}});
"""

    html = Page().render().serialize()
    assert '"hydrate":true' in html
    url = serve_document(html)
    # The site sends a policy Citry was not told about; Citry's inline
    # scripts are allowed, inline styles are not.
    policy = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'"
    page.route(
        url,
        lambda route: route.fulfill(body=html, content_type="text/html", headers={"Content-Security-Policy": policy}),
    )
    faults, console = _open(page, url)
    # The browser blocks the style attribute it parsed from the shell's
    # served HTML and reports it once. Vue then builds the heading and sets
    # the same style through the DOM, which the policy allows.
    assert faults == [], faults
    assert len(console) == 1, console
    assert "style" in console[0]
    assert page.evaluate("getComputedStyle(document.querySelector('#title')).color") == "rgb(200, 0, 0)"
