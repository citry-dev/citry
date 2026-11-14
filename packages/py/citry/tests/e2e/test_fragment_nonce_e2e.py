"""
Browser e2e for the CSP nonce check on Vue fragments.

A page under a nonce-based Content Security Policy runs only the scripts
that carry the page's nonce, so markup injected into it cannot run script.
Citry's fragment manager loads the scripts a Vue fragment data block names
and gives them the page's nonce. These tests prove that it starts only the
blocks the server stamped with the page's nonce, that neither a named
element in the page nor an injected tag left open can get around that
check, and that it refuses a data: script URL.
"""

from __future__ import annotations

import hashlib
import json
from html.parser import HTMLParser
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e

NONCE = "cGFnZS1ub25jZQ"
# No 'self' in script-src: only the nonce lets a script run, as on a strict site.
POLICY = (
    f"script-src 'nonce-{NONCE}'; style-src 'nonce-{NONCE}'; connect-src 'self'; object-src 'none'; base-uri 'none'"
)
# With 'strict-dynamic', a script that a trusted script creates runs without a
# nonce, so the runtime's own check is all that stops a forged fragment.
STRICT_DYNAMIC_POLICY = POLICY.replace("script-src ", "script-src 'strict-dynamic' ", 1)
# What a forged fragment tries to run. A page where this ran has `__forged` set.
EVIL_JS = "window.__forged = (window.__forged || 0) + 1;"

# Counts the fragment manager's refusals, so a test can wait for one instead
# of sleeping. The product reports a refused block with console.error.
_RECORD_REFUSALS = """
window.__refusals = [];
const original = console.error;
console.error = (...args) => {
  if (String(args[0]).includes('discarded Vue fragment')) window.__refusals.push(args.map(String).join(' '));
  return original.apply(console, args);
};
"""


def _widget(app: Citry) -> type[Component]:
    class NonceWidget(Component):
        citry = app
        template = '<button class="nonce-widget" v-text="label"></button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "fragment ready"}

    return NonceWidget


def _page(*, clobber_current_script: bool = False) -> str:
    # A <form name="currentScript"> before the runtime's tag replaces
    # document.currentScript with the form, which has no nonce.
    clobber = '<form name="currentScript"></form>' if clobber_current_script else ""
    return (
        f'<html><head></head><body>{clobber}<script nonce="{NONCE}" src="/citry/citry.js"></script>'
        '<div id="target"></div></body></html>'
    )


def _forge(fragment_html: str, source: dict[str, Any]) -> str:
    """Return a genuine fragment, without its nonce, with every script asset replaced by `source`."""
    text = _manifest_text(fragment_html)
    manifest = json.loads(text)
    scripts = manifest["vue"]["prepared"]["manifest"]["scripts"]
    assert scripts, "the widget must load a component script for the forged one to replace"
    for script in scripts:
        script["source"] = source
    forged = json.dumps(manifest).replace("<", "\\u003c")
    # The parser hands back the script text exactly as written, so it marks where the forged text goes.
    start = fragment_html.index(text)
    return fragment_html[:start] + forged + fragment_html[start + len(text) :]


def _open(page: Any, serve_live: Any, app: Citry, page_html: str, fragment_html: str, policy: str = POLICY) -> str:
    url = serve_live(app, page_html, fragment_html)
    page.add_init_script(_RECORD_REFUSALS)
    # The page itself is served with the policy; the forged script comes from
    # the page's own origin, which the policy does not allow without a nonce.
    page.route(
        url + "/",
        lambda route: route.fulfill(
            body=page_html, content_type="text/html", headers={"Content-Security-Policy": policy}
        ),
    )
    page.route(url + "/evil.js", lambda route: route.fulfill(body=EVIL_JS, content_type="text/javascript"))
    page.goto(url + "/")
    page.wait_for_function("() => !!window.Citry?.fragments")
    return url


def _insert(page: Any, html: str) -> None:
    # Stands in for an HTML injection: markup the server did not stamp, written into the page.
    page.evaluate("html => { document.getElementById('target').innerHTML = html; }", html)


_EVIL_SHA256 = hashlib.sha256(EVIL_JS.encode()).hexdigest()
FORGED_SOURCES = {
    "owned": {"kind": "owned", "url": "/evil.js", "sha256": _EVIL_SHA256},
    "external": {"kind": "external", "url": "/evil.js", "attrs": {}},
    "data-url": {"kind": "external", "url": "data:text/javascript,window.__forged=2", "attrs": {}},
}


@pytest.mark.parametrize("source", FORGED_SOURCES.values(), ids=FORGED_SOURCES.keys())
@pytest.mark.parametrize(
    ("clobber", "policy"),
    [(False, POLICY), (False, STRICT_DYNAMIC_POLICY), (True, STRICT_DYNAMIC_POLICY)],
    ids=["nonce-policy", "strict-dynamic", "strict-dynamic-currentScript-form"],
)
def test_injected_fragment_without_the_page_nonce_does_not_run(
    page: Any, serve_live: Any, source: dict[str, Any], policy: str, *, clobber: bool
) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    fragment = _widget(app)().render().serialize(deps_strategy="fragment")
    _open(page, serve_live, app, _page(clobber_current_script=clobber), fragment, policy)

    _insert(page, _forge(fragment, source))
    # Either outcome ends the wait: the forged script ran, or the manager refused the block.
    page.wait_for_function("() => window.__forged !== undefined || window.__refusals.length > 0")
    assert page.evaluate("() => window.__forged") is None
    [refusal] = page.evaluate("() => window.__refusals")
    assert "does not carry the page's CSP nonce" in refusal
    assert page.evaluate("() => globalThis.__widgetMounts") is None


@pytest.mark.parametrize("clobber", [False, True], ids=["plain-page", "currentScript-form"])
def test_fetched_fragment_with_the_page_nonce_starts(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, *, clobber: bool
) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    fragment = _widget(app)().render().serialize(deps_strategy="fragment", csp_nonce=NONCE)
    _open(page, serve_live, app, _page(clobber_current_script=clobber), fragment)

    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text())"
        ".then((html) => { document.getElementById('target').innerHTML = html; })"
    )
    wait_for_citry_ready()
    assert page.locator("button.nonce-widget").text_content() == "fragment ready"
    assert page.evaluate("() => globalThis.__widgetMounts") == 1
    assert page.evaluate("() => window.__refusals") == []


def _load_from_page_code(page: Any, fragment: str, manifest: dict[str, Any]) -> str:
    """Insert the fragment's host and start `manifest` through the manager's JavaScript API."""
    # Page code that calls the manager directly needs no data block, so only
    # the URL check stands between this manifest and the page's nonce.
    page.evaluate("html => { document.getElementById('target').innerHTML = html; }", fragment.split("<script", 1)[0])
    return page.evaluate(
        "async (manifest) => { try { await Citry.fragments.load(manifest); return 'mounted'; }"
        " catch (error) { return String(error); } }",
        manifest,
    )


class _FragmentManifestReader(HTMLParser):
    """Reads the text of the fragment's manifest script, the one marked `data-citry-vue-fragment`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.chunks: list[str] | None = None
        self._reading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Tag and attribute names arrive lowercased, so the match does not depend on their case.
        if tag == "script" and any(name == "data-citry-vue-fragment" for name, _value in attrs):
            self.chunks = []
            self._reading = True

    def handle_data(self, data: str) -> None:
        if self._reading and self.chunks is not None:
            self.chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._reading = False


def _manifest_text(fragment: str) -> str:
    reader = _FragmentManifestReader()
    reader.feed(fragment)
    reader.close()
    assert reader.chunks is not None, fragment
    return "".join(reader.chunks)


def _manifest(fragment: str) -> dict[str, Any]:
    return json.loads(_manifest_text(fragment))


@pytest.mark.parametrize("kind", ["owned", "external", "definition"])
@pytest.mark.parametrize("clobber_base_uri", [False, True], ids=["plain-page", "baseURI-img"])
def test_fragment_script_url_must_not_use_data(
    page: Any, serve_live: Any, kind: str, *, clobber_base_uri: bool
) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    fragment = _widget(app)().render().serialize(deps_strategy="fragment")
    _open(page, serve_live, app, _page(), fragment)
    if clobber_base_uri:
        # An element named baseURI replaces document.baseURI with itself.
        page.evaluate("() => document.body.insertAdjacentHTML('afterbegin', '<img name=\"baseURI\">')")
        assert page.evaluate("() => document.baseURI instanceof HTMLImageElement")
    manifest = _manifest(fragment)
    script = "window.__forged=3"
    url = f"data:text/javascript,{script}"
    digest = hashlib.sha256(script.encode()).hexdigest()
    prepared = manifest["vue"]["prepared"]["manifest"]
    if kind == "definition":
        for definition in prepared["definitions"]:
            definition["url"] = url
            definition["sha256"] = digest
    else:
        source: dict[str, Any] = {"kind": kind, "url": url}
        source.update({"sha256": digest} if kind == "owned" else {"attrs": {}})
        for asset in prepared["scripts"]:
            asset["source"] = source

    error = _load_from_page_code(page, fragment, manifest)
    assert "a component script must load from an http:, https:, or blob: URL" in error
    assert page.evaluate("() => window.__forged") is None


def test_fragment_script_may_use_a_blob_url_page_code_made(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    fragment = _widget(app)().render().serialize(deps_strategy="fragment")
    _open(page, serve_live, app, _page(), fragment)
    manifest = _manifest(fragment)
    # Only script already running in the page can make a blob: URL, as the
    # docs playground does for the code it runs.
    url = page.evaluate("() => URL.createObjectURL(new Blob(['window.__blobRan = 1;'], {type: 'text/javascript'}))")
    for asset in manifest["vue"]["prepared"]["manifest"]["scripts"]:
        asset["source"] = {"kind": "external", "url": url, "attrs": {}}
        # Only a script Citry published itself carries the finish report, so an
        # external source cannot keep the component script's `finishKey`.
        asset.pop("finishKey", None)

    error = _load_from_page_code(page, fragment, manifest)
    # The script does not register the component's options, which is the only
    # complaint: the URL itself was accepted and the script ran.
    assert "did not register its declared Options" in error
    assert page.evaluate("() => window.__blobRan") == 1


def test_injected_tag_that_takes_a_genuine_nonce_does_not_run(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    fragment = _widget(app)().render().serialize(deps_strategy="fragment")
    _open(page, serve_live, app, _page(), fragment)
    forged = _forge(fragment, FORGED_SOURCES["external"])
    # An injected `<script type=application/json data-citry-vue-fragment a=`
    # left open takes in the genuine `<script nonce=...>` after it, so the
    # forged block ends up with the page's nonce as one of its attributes.
    stolen = forged.replace(
        '<script type="application/json" data-citry-vue-fragment>',
        f'<script type="application/json" data-citry-vue-fragment a=<script nonce="{NONCE}">',
    )
    assert stolen != forged
    _insert(page, stolen)
    page.wait_for_function("() => window.__forged !== undefined || window.__refusals.length > 0")
    assert page.evaluate("() => window.__forged") is None
    [refusal] = page.evaluate("() => window.__refusals")
    assert "does not carry the page's CSP nonce" in refusal


def test_events_render_on_a_nonce_page_starts(page: Any, serve_live: Any, wait_for_citry_ready: Any) -> None:
    # The app tells Citry which nonce the page that sent a call got. Here
    # every page gets the same one; a real app keeps it per page or session.
    app = Citry(autodiscover=False, extensions_defaults={"events": {"_csp_nonce": lambda _request: NONCE}})
    app.set_mounted_prefix("/citry")
    widget = _widget(app)

    class NonceLoader(Component):
        citry = app
        template = "<p>loader</p>"

        class Events:
            def load(self) -> actions.Render:
                return actions.Render(widget(), target="render:slot")

    dispatcher_for(app)
    _open(page, serve_live, app, _page(), "")
    # A client other than Citry's Vue runtime posts the call envelope, asks
    # for an HTML fragment, and inserts it, as html-fragment/1 allows.
    envelope = {
        "protocol": "citry-events/1",
        "requestId": "r1",
        "calls": [{"componentClassId": NonceLoader.class_id, "handlerName": "load", "args": {}}],
    }
    action = page.evaluate(
        "async (envelope) => {"
        " const response = await fetch('/citry/ext/events/call', {method: 'POST',"
        " headers: {'Content-Type': 'application/json', 'X-Citry-Events': '1'}, body: JSON.stringify(envelope)});"
        " const result = await response.json();"
        " if (!result.results?.[0]?.actions) return result; const [render] = result.results[0].actions;"
        " document.getElementById('target').innerHTML = render.html;"
        " return render; }",
        envelope,
    )
    assert action.get("action") == "render", action
    wait_for_citry_ready()
    assert page.locator("button.nonce-widget").text_content() == "fragment ready"
    assert page.evaluate("() => globalThis.__widgetMounts") == 1
    assert page.evaluate("() => window.__refusals") == []
