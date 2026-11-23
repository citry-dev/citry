"""
Browser e2e for Vue fragments found in a page whose Citry script has no CSP nonce.

On such a page, markup injected into the page can write a fragment data
block as well as the server can. Citry's runtime then starts a block only
when every script it names is a file Citry serves under its own routes on
the page's own origin, its Events and i18n requests go to Citry's own
routes, and it mounts into the element the server writes for it. These
tests try to get past that check with URL tricks, an injected `<base>`
element, a second runtime tag, a copy of the runtime on another site under
a hash-based CSP, and named elements. They also show that the setups the
docs support still start: a sub-path, a CDN that serves only Citry's
runtime at the same path, and component files served with
`local_files = "serve"`.

They also prove that the runtime resolves the URLs of the scripts and
stylesheets it adds against the page's own address, so an injected
`<base>` cannot move them to another site, and that in an `about:srcdoc`
frame it uses the frame's base URL only on the frame's own origin.

Every forged script sets `window.__probe`, so a page where it is set ran
the script. Most pages have no CSP, so the runtime's check is the only
thing between the forged URL and the page. The page's second host name,
`localhost` instead of `127.0.0.1`, stands in for another site.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from html import escape
from typing import TYPE_CHECKING, Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.dependencies import Script
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.e2e

EVIL_JS = "window.__probe = (window.__probe || 0) + 1;"
EVIL_SHA = hashlib.sha256(EVIL_JS.encode()).hexdigest()
WITHOUT_NONCE = "found in a page without a CSP nonce"
# The block's tag carries a `nonce` attribute when the fragment was serialized with one.
BLOCK_RE = re.compile(r'(<script type="application/json" data-citry-vue-fragment[^>]*>)(.*?)(</script>)', re.DOTALL)

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


# One widget class per app: a test that renders it more than once must not register it twice. The
# entry keeps the app alive, so its id cannot be reused by a later test's app.
_WIDGETS: dict[int, tuple[Citry, type[Component]]] = {}


def _widget(app: Citry) -> type[Component]:
    known = _WIDGETS.get(id(app))
    if known is not None and known[0] is app:
        return known[1]

    class NoNonceWidget(Component):
        citry = app
        template = '<button class="no-nonce-widget" v-text="label"></button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"
        css = """
            .no-nonce-widget { color: rgb(1, 2, 3); }
        """

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "fragment ready"}

    _WIDGETS[id(app)] = (app, NoNonceWidget)
    return NoNonceWidget


def _fragment(app: Citry) -> str:
    return _widget(app)().render().serialize(deps_strategy="fragment")


def _rewrite(fragment: str, change: Any) -> str:
    """Return `fragment` with its data block's JSON passed through `change(descriptor)`."""
    match = BLOCK_RE.search(fragment)
    assert match, fragment
    descriptor = json.loads(match.group(2))
    change(descriptor)
    text = json.dumps(descriptor).replace("<", "\\u003c")
    return fragment[: match.start(2)] + text + fragment[match.end(2) :]


def _with_definitions(fragment: str, url: str, sha256: str = EVIL_SHA) -> str:
    def change(descriptor: dict[str, Any]) -> None:
        for definition in descriptor["vue"]["prepared"]["manifest"]["definitions"]:
            definition["url"] = url
            definition["sha256"] = sha256

    return _rewrite(fragment, change)


def _page_html(runtime_src: str, extra_head: str = "") -> str:
    return (
        f"<!doctype html><html><head>{extra_head}</head><body>"
        f'<script src="{runtime_src}"></script><div id="target"></div></body></html>'
    )


def _serve(page: Any, serve_live: Any, app: Citry, *, prefix: str = "/citry") -> str:
    """Start the app's server and return its base URL; the page itself is set by `_open`."""
    url = serve_live(app, "<p>unused</p>", "", prefix=prefix)
    page.add_init_script(_RECORD_REFUSALS)
    return url


def _other(url: str) -> str:
    return url.replace("127.0.0.1", "localhost")


def _evil(route: Any) -> None:
    route.fulfill(body=EVIL_JS, content_type="text/javascript", headers={"Access-Control-Allow-Origin": "*"})


def _open(page: Any, url: str, html: str, policy: str | None = None, *, other_is_cdn: bool = False) -> list[str]:
    """Serve `html` at the page's address and return the list of requests that reach the other site."""
    other = _other(url)
    other_requests: list[str] = []
    headers = {} if policy is None else {"Content-Security-Policy": policy}
    page.route(
        url + "/", lambda route: route.fulfill(body=html, content_type="text/html; charset=utf-8", headers=headers)
    )
    # Anything with "evil" in its path, on either host, is the forged script.
    page.route(re.compile(r".*evil.*"), _evil)
    page.route(re.compile(r"^https://127\.0\.0\.1.*"), _evil)

    def other_site(route: Any) -> None:
        other_requests.append(route.request.url)
        if other_is_cdn:
            # The other host stands in for a CDN that serves the app's own files. The test server
            # listens on 127.0.0.1 only, so fetch from there and answer for the other host name.
            route.fulfill(response=route.fetch(url=route.request.url.replace(other, url)))
        else:
            _evil(route)

    page.route(other + "/**", other_site)
    page.goto(url + "/")
    page.wait_for_function("() => !!window.Citry?.fragments")
    return other_requests


def _insert(page: Any, html: str) -> None:
    # Stands in for an HTML injection: markup the server did not write, added to the page.
    page.evaluate("html => { document.getElementById('target').innerHTML = html; }", html)


def _outcome(page: Any) -> tuple[Any, list[str]]:
    page.wait_for_function("() => window.__probe !== undefined || window.__refusals.length > 0", timeout=10000)
    # Give a refused block's sibling scripts a moment, so a late run would still show.
    page.wait_for_timeout(300)
    return page.evaluate("() => window.__probe"), page.evaluate("() => window.__refusals")


def _start_genuine(page: Any) -> None:
    # The page's own origin, so a <base> element a test injects does not move this request.
    page.evaluate(
        "() => fetch(location.origin + '/genuine-fragment').then((r) => r.text())"
        ".then((html) => { document.getElementById('target').innerHTML = html; })"
    )


def _route_fragment(page: Any, url: str, fragment: str) -> None:
    page.route(
        url + "/genuine-fragment", lambda route: route.fulfill(body=fragment, content_type="text/html; charset=utf-8")
    )


def _wait_mounted_or_refused(page: Any) -> None:
    page.wait_for_function("() => window.__refusals.length > 0 || globalThis.__widgetMounts", timeout=10000)


# Definition URLs that try to leave `<prefix>ext/events/definitions/` after the
# browser normalises them. `{other}` is the other site, `{other_host}` its host.
REFUSED_DEFINITION_URLS = {
    "dot-dot": "/citry/ext/events/definitions/../../../evil/ext/events/definitions/{sha}.js",
    "percent-dots": "/citry/ext/events/definitions/%2e%2e/%2E%2e/%2e%2E/evil/ext/events/definitions/{sha}.js",
    "dot-percent-dot": "/citry/ext/events/definitions/.%2e/.%2E/.%2e/evil/ext/events/definitions/{sha}.js",
    "encoded-slash": "/citry/ext/events/definitions/..%2f..%2f..%2fevil%2fext%2fevents%2fdefinitions%2f{sha}.js",
    "backslash-dot-dot": "\\citry\\ext\\events\\definitions\\..\\..\\..\\evil\\ext\\events\\definitions\\{sha}.js",
    "backslash-host": "\\\\{other_host}\\citry\\ext\\events\\definitions\\{sha}.js",
    "slash-backslash-host": "/\\{other_host}/citry/ext/events/definitions/{sha}.js",
    "protocol-relative": "//{other_host}/citry/ext/events/definitions/{sha}.js",
    "other-origin": "{other}/citry/ext/events/definitions/{sha}.js",
    "other-scheme": "https://127.0.0.1:{port}/citry/ext/events/definitions/{sha}.js",
    "credentials": "http://user:pw@127.0.0.1:{port}/citry/ext/events/definitions/{sha}.js",
    "uppercase-prefix": "/CITRY/ext/events/definitions/{sha}.js",
    "data-url": "data:text/javascript,window.__probe=1",
    "other-origin-blob": "blob:{other}/00000000-0000-0000-0000-000000000000",
    "tab-in-scheme": "jav\tascript:window.__probe=1",
}


@pytest.mark.parametrize("name", REFUSED_DEFINITION_URLS.keys())
def test_definition_url_outside_citrys_routes_is_refused(page: Any, serve_live: Any, name: str) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    port = url.rsplit(":", 1)[1]
    forged_url = REFUSED_DEFINITION_URLS[name].format(
        sha=EVIL_SHA, other=_other(url), other_host=f"localhost:{port}", port=port
    )
    sha = hashlib.sha256(b"window.__probe=1").hexdigest() if name == "data-url" else EVIL_SHA
    _open(page, url, _page_html("/citry/citry.js"))
    _insert(page, _with_definitions(_fragment(app), forged_url, sha))
    probe, refusals = _outcome(page)
    assert probe is None
    assert len(refusals) == 1, refusals
    assert WITHOUT_NONCE in refusals[0], refusals


def test_owned_script_outside_citrys_routes_is_refused(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)

    def change(descriptor: dict[str, Any]) -> None:
        for asset in descriptor["vue"]["prepared"]["manifest"]["scripts"]:
            asset["source"] = {
                "kind": "owned",
                "url": f"/citry/ext/events/definitions/%2e%2e/%2e%2e/%2e%2e/evil/{EVIL_SHA}.js",
                "sha256": EVIL_SHA,
                "attrs": {},
            }

    _open(page, url, _page_html("/citry/citry.js"))
    _insert(page, _rewrite(_fragment(app), change))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals


@pytest.mark.parametrize(
    "endpoint",
    [
        "/citry/ext/events/call/../../../../evil",
        "//localhost:{port}/citry/ext/events/call",
        "/citry/ext/events/call?x=1",
        "/citry/ext/events/call#x",
    ],
    ids=["dot-dot", "protocol-relative", "query", "hash"],
)
def test_events_endpoint_outside_citrys_routes_is_refused(page: Any, serve_live: Any, endpoint: str) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    port = url.rsplit(":", 1)[1]

    def change(descriptor: dict[str, Any]) -> None:
        descriptor["vue"]["prepared"]["endpoint"] = endpoint.format(port=port)

    _open(page, url, _page_html("/citry/citry.js"))
    _insert(page, _rewrite(_fragment(app), change))
    _wait_mounted_or_refused(page)
    refusals = page.evaluate("() => window.__refusals")
    assert refusals, refusals
    assert WITHOUT_NONCE in refusals[0], refusals
    assert page.evaluate("() => globalThis.__widgetMounts") is None


@pytest.mark.parametrize("base", ["{other}/citry/", "/evil/"], ids=["other-origin", "same-origin-other-path"])
def test_forged_relative_definition_after_an_injected_base_is_refused(page: Any, serve_live: Any, base: str) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    _open(page, url, _page_html("/citry/citry.js"))
    # The forged block uses a relative URL, which the injected <base> would move. Against the
    # page's own address it resolves outside Citry's routes.
    page.evaluate(
        "href => document.body.insertAdjacentHTML('afterbegin', `<base href=\"${href}\">`)",
        base.format(other=_other(url)),
    )
    _insert(page, _with_definitions(_fragment(app), f"ext/events/definitions/{EVIL_SHA}.js"))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals


def test_genuine_fragment_after_an_injected_base_loads_from_the_page(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    _route_fragment(page, url, _fragment(app))
    other_requests = _open(page, url, _page_html("/citry/citry.js"))
    page.evaluate(
        "href => document.body.insertAdjacentHTML('afterbegin', `<base href=\"${href}\">`)", _other(url) + "/"
    )
    # The genuine block's URLs are root-relative. The runtime resolves them against the page's
    # address, so the base element cannot move them to the other site.
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.locator("button.no-nonce-widget").text_content() == "fragment ready"
    assert page.evaluate("() => window.__probe") is None
    assert other_requests == []
    stylesheets = page.evaluate("() => [...document.querySelectorAll('link[data-citry-css-url]')].map((l) => l.href)")
    assert stylesheets, "the widget's stylesheet must be one the runtime added"
    assert all(href.startswith(url + "/citry/") for href in stylesheets), stylesheets


def test_second_runtime_tag_inserted_later_does_not_move_the_prefix(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    other = _other(url)
    _open(page, url, _page_html("/citry/citry.js"))
    # innerHTML never runs a script, but the tag is in the page when the block is checked.
    page.evaluate(
        "src => document.body.insertAdjacentHTML('afterbegin', `<script src=\"${src}\"></script>`)",
        other + "/evil/citry.js",
    )
    _insert(page, _with_definitions(_fragment(app), f"{other}/evil/ext/events/definitions/{EVIL_SHA}.js"))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals


def test_second_runtime_tag_blocked_by_csp_does_not_move_the_prefix(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    port = url.rsplit(":", 1)[1]
    other = _other(url)
    # The policy allows the other site only below /evil/ext/, so the forged definition would run
    # if the runtime accepted it, while the runtime-looking tag before Citry's own is blocked.
    policy = f"script-src 'self' http://localhost:{port}/evil/ext/"
    extra = f'<script src="{other}/evil/citry.js"></script>'
    _open(page, url, _page_html("/citry/citry.js", extra), policy)
    _insert(page, _with_definitions(_fragment(app), f"{other}/evil/ext/events/definitions/{EVIL_SHA}.js"))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals


@pytest.mark.parametrize("hashed", [False, True], ids=["stable-url", "hashed-url"])
def test_runtime_on_a_sub_path_accepts_its_fragments(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, *, hashed: bool
) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app, prefix="/shop/citry")
    runtime = app.runtime_url() if hashed else "/shop/citry/citry.js"
    assert runtime.startswith("/shop/citry/citry"), runtime
    fragment = _fragment(app)
    assert "/shop/citry/ext/events/definitions/" in fragment
    _route_fragment(page, url, fragment)
    _open(page, url, _page_html(runtime), "script-src 'self'")
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.locator("button.no-nonce-widget").text_content() == "fragment ready"
    assert page.evaluate("() => window.__refusals") == []


def test_runtime_from_a_cdn_with_the_apps_own_definitions(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    """A CDN that rewrites only the runtime tag; the JSON keeps the app's own URLs."""
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    _route_fragment(page, url, _fragment(app))
    _open(page, url, _page_html(_other(url) + "/citry/citry.js"), other_is_cdn=True)
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.evaluate("() => globalThis.__widgetMounts") == 1
    assert page.evaluate("() => window.__refusals") == []


@pytest.mark.parametrize("nonce", [False, True], ids=["page-without-nonce", "nonce-page"])
def test_runtime_and_files_from_a_cdn_start_only_on_a_nonce_page(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, *, nonce: bool
) -> None:
    """
    A CDN that rewrites every Citry file URL, runtime and JSON alike; Events stay on the app.

    On a page without a nonce the runtime accepts Citry's files only on the page's own origin, so
    the definitions on the CDN are refused. A nonce-based CSP proves the block came from the server,
    so there the same fragment starts.
    """
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    other = _other(url)

    def change(descriptor: dict[str, Any]) -> None:
        prepared = descriptor["vue"]["prepared"]
        for definition in prepared["manifest"]["definitions"]:
            definition["url"] = other + definition["url"]
        for asset in prepared["manifest"]["scripts"]:
            asset["source"]["url"] = other + asset["source"]["url"]
        # The app's Events routes, as a page with event handlers carries them.
        prepared["endpoint"] = "/citry/ext/events/call"
        prepared["eventBaseUrl"] = "/citry/ext/events/e/"

    widget = _widget(app)()
    if nonce:
        fragment = widget.render().serialize_result(deps_strategy="fragment", csp_nonce=NONCE).html
        html = _page_html(other + "/citry/citry.js").replace("<script src=", f'<script nonce="{NONCE}" src=')
        policy: str | None = f"script-src 'nonce-{NONCE}'"
    else:
        fragment = widget.render().serialize(deps_strategy="fragment")
        html = _page_html(other + "/citry/citry.js")
        policy = None
    _route_fragment(page, url, _rewrite(fragment, change))
    _open(page, url, html, policy, other_is_cdn=True)
    _start_genuine(page)
    if nonce:
        wait_for_citry_ready()
        assert page.evaluate("() => globalThis.__widgetMounts") == 1
        assert page.evaluate("() => window.__refusals") == []
    else:
        page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
        [refusal] = page.evaluate("() => window.__refusals")
        assert "a definition URL is not Citry's own" in refusal
        assert page.evaluate("() => globalThis.__widgetMounts") is None


def test_inline_runtime_holds_fragments_to_the_page_origin(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    """An inline runtime has no URL, so a definition must be on the page's origin and end with the route."""
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    with urllib.request.urlopen(url + "/citry/citry.js") as response:  # noqa: S310 - local test server
        runtime = response.read().decode()
    inline = "<script>" + runtime.replace("</script", "<\\/script") + "</script>"
    html = f'<!doctype html><html><head></head><body>{inline}<div id="target"></div></body></html>'
    fragment = _fragment(app)
    _route_fragment(page, url, fragment)
    _open(page, url, html)
    _insert(page, _with_definitions(fragment, f"{_other(url)}/citry/ext/events/definitions/{EVIL_SHA}.js"))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.evaluate("() => globalThis.__widgetMounts") == 1


def _i18n_app(tmp_path: Path) -> tuple[Citry, type[Component]]:
    name = "fragment_no_nonce_catalog_" + tmp_path.name.replace("-", "_")
    package = tmp_path / name
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf8")
    (package / "citry-i18n.toml").write_text(
        'schema_version = 1\nowner = "fragment-e2e"\nsource_locale = "en-US"\n', encoding="utf8"
    )
    for locale, label in (("en-US", "Save"), ("cs-CZ", "Ulozit")):
        root = package / "locales" / locale
        root.mkdir(parents=True)
        (root / "common.ftl").write_text(f"save = {label}\n", encoding="utf8")
    sys.path.insert(0, str(tmp_path))
    app = Citry(
        secret="fragment-e2e-secret-fragment-e2e-secret",  # noqa: S106
        autodiscover=False,
        mode="development",
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US", "cs-CZ"), "catalogs": (name,)}},
    )

    class Switcher(Component):
        citry = app
        template = """
          <c-i18n c-client="True" tag="main">
            <p id="label" $c-tr:save>{{ tr("save") }}</p>
            <button id="switch" @click="$i18n.switchLocale('cs-CZ')">switch</button>
          </c-i18n>
        """

    return app, Switcher


def _i18n_page(page: Any, url: str) -> None:
    # A page that receives i18n fragments links the i18n runtime as well as Citry's own.
    html = _page_html("/citry/citry.js").replace(
        '<div id="target">', '<script src="/citry/ext/i18n/runtime.js"></script><div id="target">'
    )
    _open(page, url, html, "script-src 'self'")


# Forged i18n `messages_url` values. The i18n runtime would POST to it with the page's CSRF token.
FORGED_MESSAGES_URLS: dict[str, str | int] = {
    "same-origin-other-path": "/account/delete",
    "other-origin": "{other}/citry/ext/i18n/messages",
    "protocol-relative": "//localhost:{port}/citry/ext/i18n/messages",
    "query": "/citry/ext/i18n/messages?next=/account/delete",
    "dot-dot": "/citry/ext/i18n/messages/../../../../account/delete",
    "not-a-string": 7,
}


@pytest.mark.parametrize("case", FORGED_MESSAGES_URLS.keys())
def test_forged_i18n_messages_url_is_refused(page: Any, serve_live: Any, tmp_path: Path, case: str) -> None:
    app, switcher = _i18n_app(tmp_path)
    url = _serve(page, serve_live, app)
    port = url.rsplit(":", 1)[1]
    fragment = switcher().render().serialize(deps_strategy="fragment")
    value = FORGED_MESSAGES_URLS[case]
    forged = value.format(other=_other(url), port=port) if isinstance(value, str) else value

    def change(descriptor: dict[str, Any]) -> None:
        payload = descriptor["vue"]["prepared"]["manifest"]["extensions"]["i18n"]["payload"]
        payload["messages_url"] = forged

    posts: list[str] = []
    page.on("request", lambda request: posts.append(request.url) if request.method == "POST" else None)
    _i18n_page(page, url)
    _insert(page, _rewrite(fragment, change))
    page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
    [refusal] = page.evaluate("() => window.__refusals")
    assert "its i18n messages URL is not Citry's own" in refusal
    # The refused fragment never mounts, so there is no switch button and no request.
    assert page.locator("#switch").count() == 0
    assert posts == []


def test_genuine_i18n_fragment_switches_locale_on_a_page_without_a_nonce(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, tmp_path: Path
) -> None:
    app, switcher = _i18n_app(tmp_path)
    url = _serve(page, serve_live, app)
    _route_fragment(page, url, switcher().render().serialize(deps_strategy="fragment"))
    _i18n_page(page, url)
    with page.expect_request(lambda request: request.method == "POST") as message_request:
        _start_genuine(page)
        wait_for_citry_ready()
        page.locator("#switch").click()
    # The checked, absolute URL of Citry's own messages route.
    assert message_request.value.url == url + "/citry/ext/i18n/messages"
    page.wait_for_function("() => document.getElementById('label').textContent.trim() === 'Ulozit'")
    assert page.evaluate("() => window.__refusals") == []


@pytest.mark.parametrize("delay", ["microtask", "timeout-0", "timeout-50"])
def test_base_inserted_between_the_check_and_the_load_moves_nothing(page: Any, serve_live: Any, delay: str) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    other_requests = _open(page, url, _page_html("/citry/citry.js"))
    # Relative to the page at "/", this URL resolves into Citry's prefix, so the check accepts it.
    # The runtime then loads the absolute URL it checked; the file does not exist on the app.
    forged = _with_definitions(_fragment(app), f"citry/ext/events/definitions/{EVIL_SHA}.js")
    page.evaluate(
        """([html, base, delay]) => {
          document.getElementById('target').innerHTML = html;
          const addBase = () => document.body.insertAdjacentHTML('afterbegin', `<base href="${base}">`);
          // The fragment manager checks the block in a MutationObserver callback (a microtask).
          if (delay === 'microtask') queueMicrotask(() => queueMicrotask(addBase));
          else setTimeout(addBase, delay === 'timeout-0' ? 0 : 50);
        }""",
        [forged, _other(url) + "/", delay],
    )
    page.wait_for_function("() => document.querySelector('base') !== null")
    # The definition fails to load from the app, which the manager reports as a discarded fragment.
    page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
    page.wait_for_timeout(300)
    assert page.evaluate("() => window.__probe") is None
    assert other_requests == []


def test_named_elements_do_not_hide_the_runtime_url(page: Any, serve_live: Any) -> None:
    """A clobbered currentScript would leave no prefix, and the weaker same-origin rule would apply."""
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    clobber = '<form name="currentScript"></form><img name="baseURI"><img id="origin"><form name="URL"></form>'
    html = _page_html("/citry/citry.js").replace("<body>", "<body>" + clobber)
    _open(page, url, html)
    # Without a prefix, the same-origin rule would accept this URL; with the prefix it is refused.
    _insert(page, _with_definitions(_fragment(app), f"/uploads/evil/ext/events/definitions/{EVIL_SHA}.js"))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals


def test_local_files_serve_fragment_starts_on_a_page_without_a_nonce(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, tmp_path: Path
) -> None:
    """`local_files = "serve"` writes the component's own file on Citry's asset route."""
    script = tmp_path / "report.js"
    script.write_text("window.__localFileRan = 1;\n", encoding="utf8")
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)

    class ServedWidget(Component):
        citry = app

        class Dependencies:
            local_files = "serve"
            js = [script]

        template = '<button class="served-widget" v-text="label"></button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "served ready"}

    fragment = ServedWidget().render().serialize(deps_strategy="fragment")
    assert "/citry/asset/" in fragment
    _route_fragment(page, url, fragment)
    _open(page, url, _page_html("/citry/citry.js"), "script-src 'self'")
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.evaluate("() => [globalThis.__widgetMounts, window.__localFileRan]") == [1, 1]
    assert page.evaluate("() => window.__refusals") == []


# Host selectors other than `#citry-vue-<appId>`, the only one the server writes.
FORGED_HOSTS = {
    "other-element": "#account",
    "selector-list": "#citry-vue-{id}, #account",
    "descendant": "#account #citry-vue-{id}",
    "upper-case-id": "#citry-vue-{upper}",
    "attribute-selector": "[id=citry-vue-{id}]",
}


@pytest.mark.parametrize("case", FORGED_HOSTS.keys())
def test_forged_fragment_cannot_mount_into_other_page_content(page: Any, serve_live: Any, case: str) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    fragment = _fragment(app)
    app_id = re.search(r'id="citry-vue-([0-9a-f]{32})"', fragment)
    assert app_id, fragment
    host = FORGED_HOSTS[case].format(id=app_id.group(1), upper=app_id.group(1).upper())
    _open(page, url, _page_html("/citry/citry.js"))
    page.evaluate("() => document.body.insertAdjacentHTML('afterbegin', '<form id=\"account\">keep</form>')")

    def change(descriptor: dict[str, Any]) -> None:
        descriptor["vue"]["host"] = host
        descriptor["vue"]["prepared"]["host"] = host
        if case == "upper-case-id":
            # The app id must then match the host, so the shape check is what refuses it.
            descriptor["vue"]["appId"] = app_id.group(1).upper()
            descriptor["vue"]["prepared"]["manifest"]["appId"] = app_id.group(1).upper()

    _insert(page, _rewrite(fragment, change))
    page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
    [refusal] = page.evaluate("() => window.__refusals")
    assert "its host is not the element Citry writes for it" in refusal
    assert page.locator("#account").text_content() == "keep"
    assert page.evaluate("() => globalThis.__widgetMounts") is None


@pytest.mark.parametrize("nonce", [False, True], ids=["page-without-nonce", "nonce-page"])
def test_earlier_element_with_the_fragment_host_id_does_not_win_the_mount(
    page: Any, serve_live: Any, *, nonce: bool
) -> None:
    """An element with id `citry-vue-<appId>` before the genuine host stops the start and never receives the app."""
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    if nonce:
        fragment = _widget(app)().render().serialize_result(deps_strategy="fragment", csp_nonce=NONCE).html
        runtime_tag = f'<script nonce="{NONCE}" src="/citry/citry.js"></script>'
    else:
        fragment = _fragment(app)
        runtime_tag = '<script src="/citry/citry.js"></script>'
    app_id = re.search(r'id="citry-vue-([0-9a-f]{32})"', fragment)
    assert app_id, fragment
    injected = f'<div id="citry-vue-{app_id.group(1)}" class="injected"></div>'
    html = f'<!doctype html><html><head></head><body>{injected}{runtime_tag}<div id="target"></div></body></html>'
    _open(page, url, html)
    _insert(page, fragment)
    page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
    page.wait_for_timeout(300)
    assert "host must resolve once" in page.evaluate("() => window.__refusals")[0]
    assert page.locator("div.injected").inner_html() == ""
    assert page.evaluate("() => globalThis.__widgetMounts") is None


def test_document_app_does_not_mount_into_an_earlier_element_with_its_host_id(page: Any, serve_live: Any) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    html = _widget(app)().render().serialize()
    app_id = re.search(r'data-citry-vue-document="([0-9a-f]{32})"', html)
    assert app_id, html
    # Markup earlier in the page that takes the app's host id would otherwise receive the app.
    injected = f'<div id="citry-vue-{app_id.group(1)}" class="injected"></div>'
    html = f"<html><head></head><body>{injected}{html}</body></html>"
    url = serve_live(app, html, "")
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url + "/")
    page.wait_for_timeout(1000)
    assert page.locator("div.injected").inner_html() == ""
    assert page.evaluate("() => globalThis.__widgetMounts") is None
    assert any("needs one host element" in error for error in errors), errors


NONCE = "bm8tYmFzZS1ub25jZQ"
# The policy the docs recommend, without `base-uri`, so the browser accepts an injected <base>.
NONCE_POLICY_WITHOUT_BASE_URI = (
    f"default-src 'self'; script-src 'self' 'nonce-{NONCE}'; style-src 'self' 'nonce-{NONCE}'"
)


def test_injected_base_does_not_move_a_script_url_dependency(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class WithDependency(Component):
        citry = app

        class Dependencies:
            js = [Script(url="/static/dependency.js")]

        template = '<button class="with-dependency">ready</button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"

    body = WithDependency().render().serialize_result(csp_nonce=NONCE).html
    # The injection lands after Citry's runtime tag, so the runtime itself loads from the app.
    html = f'<!doctype html><html><head></head><body>{body}<base href="http://localhost:{{port}}/sub/"></body></html>'
    url = serve_live(app, "<p>unused</p>", "")
    html = html.replace("{port}", url.rsplit(":", 1)[1])
    other_requests: list[str] = []

    def other_site(route: Any) -> None:
        other_requests.append(route.request.url)
        _evil(route)

    page.route(_other(url) + "/**", other_site)
    page.route(
        url + "/static/dependency.js",
        lambda route: route.fulfill(body="window.__dependency = 'app';", content_type="text/javascript"),
    )
    page.route(
        url + "/",
        lambda route: route.fulfill(
            body=html,
            content_type="text/html; charset=utf-8",
            headers={"Content-Security-Policy": NONCE_POLICY_WITHOUT_BASE_URI},
        ),
    )
    page.goto(url + "/")
    wait_for_citry_ready()
    assert page.evaluate("() => document.baseURI").startswith(_other(url))
    assert page.evaluate("() => [window.__dependency, window.__probe]") == ["app", None]
    assert other_requests == []


# A served local file's URL in a forged block. The page answers every request whose path holds
# "asset" or "evil" with the forged script, so a URL the runtime's check let through would run it
# even where Citry's own route would answer 404. `{name}` is a 12-hex file name.
REFUSED_ASSET_URLS = {
    "other-origin": "{other}/citry/asset/{name}.js",
    "protocol-relative": "//localhost:{port}/citry/asset/{name}.js",
    "upper-case-hex": "/citry/asset/{upper}.js",
    "query": "/citry/asset/{name}.js?x",
    "hash": "/citry/asset/{name}.js#x",
    "dot-dot-after": "/citry/asset/{name}.js/..",
    "trailing-slash": "/citry/asset/{name}.js/",
    "semicolon": "/citry/asset/{name}.js;x",
    "css": "/citry/asset/{name}.css",
    "json": "/citry/asset/{name}.json",
    "thirteen-hex": "/citry/asset/{name}0.js",
    "eleven-hex": "/citry/asset/{short}.js",
    "sub-folder": "/citry/asset/sub/{name}.js",
    "other-prefix": "/evil/asset/{name}.js",
    "dot-dot-out": "/citry/asset/../../evil/asset/{name}.js",
    "percent-dots-out": "/citry/asset/%2e%2e/%2e%2e/evil/asset/{name}.js",
    "encoded-slash": "/citry/asset/..%2f..%2fevil%2fasset%2f{name}.js",
    "backslash-out": "\\citry\\asset\\..\\..\\evil\\asset\\{name}.js",
    "percent-hex": "/citry/asset/%61{tail}.js",
    "percent-dot-extension": "/citry/asset/{name}%2ejs",
}


def _served_widget(app: Citry, tmp_path: Path) -> type[Component]:
    script = tmp_path / "served.js"
    script.write_text("window.__servedRan = 1;\n", encoding="utf8")

    class ServedFileWidget(Component):
        citry = app

        class Dependencies:
            local_files = "serve"
            js = [script]

        template = '<button class="served-widget">served</button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"

    return ServedFileWidget


@pytest.mark.parametrize("case", REFUSED_ASSET_URLS.keys())
def test_served_local_file_url_outside_citrys_asset_route_is_refused(
    page: Any, serve_live: Any, tmp_path: Path, case: str
) -> None:
    app = Citry(autodiscover=False)
    url = _serve(page, serve_live, app)
    port = url.rsplit(":", 1)[1]
    name = "abcdef012345"
    forged = REFUSED_ASSET_URLS[case].format(
        other=_other(url), port=port, name=name, upper=name.upper(), short=name[:11], tail=name[1:]
    )
    fragment = _served_widget(app, tmp_path)().render().serialize(deps_strategy="fragment")

    def change(descriptor: dict[str, Any]) -> None:
        for asset in descriptor["vue"]["prepared"]["manifest"]["scripts"]:
            if asset["source"]["kind"] == "external":
                asset["source"]["url"] = forged
                # The genuine file's integrity would not match the forged script.
                asset["source"]["attrs"] = {}

    page.route(re.compile(r".*asset.*"), _evil)
    _open(page, url, _page_html("/citry/citry.js"))
    _insert(page, _rewrite(fragment, change))
    probe, refusals = _outcome(page)
    assert probe is None
    assert WITHOUT_NONCE in refusals[0], refusals


def test_asset_route_answers_404_for_a_name_citry_did_not_write(serve_live: Any, tmp_path: Path) -> None:
    """The check lets the extension through in any case; Citry's route serves only the name it wrote."""
    app = Citry(autodiscover=False)
    url = serve_live(app, "<p>unused</p>", "")
    fragment = _served_widget(app, tmp_path)().render().serialize(deps_strategy="fragment")
    genuine = re.search(r"/citry/asset/([0-9a-f]{12})\.js", fragment)
    assert genuine, fragment
    for path in (f"/citry/asset/{genuine.group(1)}.JS", f"/citry/asset/{genuine.group(1).upper()}.js"):
        try:
            with urllib.request.urlopen(url + path) as response:  # noqa: S310 - local test server
                status = response.status
        except urllib.error.HTTPError as error:
            status = error.code
        assert status == 404, path


# Under a hash-based CSP with 'strict-dynamic', the browser runs any script whose bytes match an
# allowed hash, from any address. `csp_script_hashes` gives the runtime's own hash, so injected
# markup can run a copy of Citry's genuine runtime from another site, or move Citry's own runtime
# tag there with a <base> element. The runtime must still accept Citry's files only on the page's
# own origin.


def _runtime_tag(html: str) -> tuple[str, str, str]:
    match = re.search(r'<script src="([^"]+)" integrity="([^"]+)" crossorigin="anonymous"></script>', html)
    assert match, html
    return match.group(0), match.group(1), match.group(2)


def _forged_fragment_for(app: Citry, definitions_url: str) -> str:
    # Injected markup carries only the host and the data block, not the preloader.
    fragment = re.sub(r"<script>\(function\(\) \{.*?\}\)\(\);</script>", "", _fragment(app), flags=re.DOTALL)
    return _with_definitions(fragment, definitions_url)


def _other_site_copies_citry(page: Any, url: str) -> list[str]:
    """Serve copies of Citry's public files on the other site, and the forged definition; return its requests."""
    other = _other(url)
    requests: list[str] = []

    def handle(route: Any) -> None:
        requests.append(route.request.url)
        if EVIL_SHA in route.request.url:
            _evil(route)
        else:
            response = route.fetch(url=route.request.url.replace(other, url))
            route.fulfill(response=response, headers={**response.headers, "access-control-allow-origin": "*"})

    page.route(other + "/**", handle)
    return requests


def _route_html(page: Any, url: str, html: str, policy: str) -> None:
    page.route(
        url + "/",
        lambda route: route.fulfill(
            body=html, content_type="text/html; charset=utf-8", headers={"Content-Security-Policy": policy}
        ),
    )


@pytest.mark.parametrize("route", ["runtime-copy", "base-before-runtime-tag", "control"])
def test_runtime_from_another_site_under_a_runtime_hash_policy_does_not_move_the_prefix(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, route: str
) -> None:
    app = Citry(autodiscover=False)
    url = serve_live(app, "<p>unused</p>", "")
    page.add_init_script(_RECORD_REFUSALS)
    tag, src, integrity = _runtime_tag(_widget(app)().render().serialize())
    other = _other(url)
    forged = _forged_fragment_for(app, f"{other}/citry/ext/events/definitions/{EVIL_SHA}.js")
    policy = f"script-src 'strict-dynamic' '{integrity}'; object-src 'none'"
    if route == "runtime-copy":
        # A tag for the genuine runtime bytes on the other site, before Citry's own tag, runs first.
        injected = tag.replace(f'src="{src}"', f'src="{other}{src}"') + forged
        policy += "; base-uri 'none'"
    elif route == "base-before-runtime-tag":
        # The policy has no base-uri, so the browser accepts the injected <base>.
        injected = f'<base href="{other}/">' + forged
    else:
        injected = forged
    requests = _other_site_copies_citry(page, url)
    _route_fragment(page, url, _fragment(app))
    html = f'<!doctype html><html><head></head><body>{injected}{tag}<div id="target"></div></body></html>'
    _route_html(page, url, html, policy)
    page.goto(url + "/")
    try:
        page.wait_for_function("() => !!window.Citry?.fragments", timeout=5000)
    except Exception:  # noqa: BLE001 - an engine that refuses an external script by its hash runs no runtime
        pytest.skip("this engine does not allow an external script by its hash")
    if route != "control":
        assert any(src in request for request in requests), "the runtime must have loaded from the other site"
    page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
    page.wait_for_timeout(300)
    assert page.evaluate("() => window.__probe") is None
    assert "a definition URL is not Citry's own" in page.evaluate("() => window.__refusals")[0]
    assert not any(EVIL_SHA in request for request in requests)
    # The genuine fragment from the app still starts under the same policy.
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.evaluate("() => globalThis.__widgetMounts") == 1


def test_injected_base_does_not_move_the_runtime_a_fragment_preloader_adds(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    """One injection of a <base> and a forged block, before a server-rendered fragment."""
    app = Citry(autodiscover=False)
    url = serve_live(app, "<p>unused</p>", "")
    page.add_init_script(_RECORD_REFUSALS)
    other = _other(url)
    genuine = _fragment(app)
    preloader = re.search(r"<script>(\(function\(\) \{.*?\}\)\(\);)</script>", genuine, flags=re.DOTALL)
    assert preloader, genuine
    digest = base64.b64encode(hashlib.sha256(preloader.group(1).encode()).digest()).decode()
    # A policy that allows the preloader by its hash and has no base-uri.
    policy = f"script-src 'strict-dynamic' 'sha256-{digest}'; object-src 'none'"
    injected = f'<base href="{other}/">' + _forged_fragment_for(
        app, f"{other}/citry/ext/events/definitions/{EVIL_SHA}.js"
    )
    requests = _other_site_copies_citry(page, url)
    html = f'<!doctype html><html><head></head><body>{injected}<div id="target">{genuine}</div></body></html>'
    _route_html(page, url, html, policy)
    page.goto(url + "/")
    wait_for_citry_ready()
    page.wait_for_function("() => window.__refusals.length > 0", timeout=10000)
    page.wait_for_timeout(300)
    assert page.evaluate("() => document.baseURI").startswith(other)
    assert page.evaluate("() => window.__probe") is None
    assert "a definition URL is not Citry's own" in page.evaluate("() => window.__refusals")[0]
    # The preloader loaded the runtime from the page's own address, and the genuine fragment started.
    assert requests == []
    assert page.evaluate("() => globalThis.__widgetMounts") == 1


# An injected <base> before and after start-up must not move any file the runtime adds.


def _record_other(page: Any, url: str) -> list[str]:
    other_requests: list[str] = []

    def other_site(route: Any) -> None:
        other_requests.append(route.request.url)
        _evil(route)

    page.route(_other(url) + "/**", other_site)
    return other_requests


def _serve_page(page: Any, url: str, body: str, policy: str | None = None) -> None:
    headers = {} if policy is None else {"Content-Security-Policy": policy}
    html = f"<!doctype html><html><head></head><body>{body}</body></html>"
    page.route(
        url + "/", lambda route: route.fulfill(body=html, content_type="text/html; charset=utf-8", headers=headers)
    )


def test_base_before_start_up_moves_no_document_file(page: Any, serve_live: Any, wait_for_citry_ready: Any) -> None:
    """A <base> right after the runtime tag, before the page's data block and start script."""
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class Doc(Component):
        citry = app

        class Dependencies:
            js = [Script(url="static/dependency.js")]

        template = '<button class="doc-widget">ready</button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"
        css = """
            .doc-widget { color: rgb(7, 8, 9); }
        """

    body = Doc().render().serialize()
    tag, _, _ = _runtime_tag(body)
    url = serve_live(app, "<p>unused</p>", "")
    body = body.replace(tag, tag + f'<base href="{_other(url)}/sub/">')
    other_requests = _record_other(page, url)
    page.route(
        url + "/static/dependency.js",
        lambda route: route.fulfill(body="window.__dependency = 'app';", content_type="text/javascript"),
    )
    _serve_page(page, url, body)
    page.goto(url + "/")
    wait_for_citry_ready()
    assert page.evaluate("() => document.baseURI").startswith(_other(url))
    assert page.evaluate("() => [globalThis.__widgetMounts, window.__dependency, window.__probe]") == [1, "app", None]
    assert page.locator(".doc-widget").evaluate("n => getComputedStyle(n).color") == "rgb(7, 8, 9)"
    assert other_requests == []


def test_base_after_start_up_moves_nothing_in_a_server_render(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, send_event: Any
) -> None:
    app = Citry(secret="no-nonce-e2e-secret-no-nonce-e2e-secret", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")

    class Child(Component):
        citry = app
        template = '<b class="late-child">late</b>'
        js = "$component(() => { globalThis.__childMounts = (globalThis.__childMounts || 0) + 1; });"
        css = """
            .late-child { color: rgb(4, 5, 6); }
        """

    class Parent(Component):
        citry = app

        class Kwargs:
            show: bool = False

        class Events:
            def show(self) -> Any:
                return actions.Render(Parent(show=True))

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"show": kwargs.show}

        template = """
            <main>
                <button
                    id="show"
                    @c-click="show"
                >show</button>
                <c-Child c-if="show" />
            </main>
        """

    dispatcher_for(app)
    body = Parent().render().serialize()
    url = serve_live(app, "<p>unused</p>", "")
    other_requests = _record_other(page, url)
    _serve_page(page, url, body)
    page.goto(url + "/")
    wait_for_citry_ready()
    page.evaluate("b => document.body.insertAdjacentHTML('afterbegin', `<base href='${b}'>`)", _other(url) + "/x/")
    # The Render adds a component whose script and stylesheet the runtime loads after the <base>.
    send_event(lambda: page.locator("#show").click())
    page.wait_for_function("() => globalThis.__childMounts === 1", timeout=10000)
    assert page.locator(".late-child").evaluate("n => getComputedStyle(n).color") == "rgb(4, 5, 6)"
    assert page.evaluate("() => window.__probe") is None
    assert other_requests == []


def test_base_before_a_fragment_on_a_nonce_page_moves_no_script_url_dependency(
    page: Any, serve_live: Any, wait_for_citry_ready: Any
) -> None:
    app = Citry(autodiscover=False)
    url = serve_live(app, "<p>unused</p>", "")

    class WithRelativeDependency(Component):
        citry = app

        class Dependencies:
            js = [Script(url="static/fragment-dependency.js")]

        template = '<button class="nonce-fragment">ready</button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"

    fragment = WithRelativeDependency().render().serialize_result(deps_strategy="fragment", csp_nonce=NONCE).html
    other_requests = _record_other(page, url)
    _route_fragment(page, url, fragment)
    page.route(
        url + "/static/fragment-dependency.js",
        lambda route: route.fulfill(body="window.__dependency = 'app';", content_type="text/javascript"),
    )
    body = f'<script nonce="{NONCE}" src="/citry/citry.js"></script><div id="target"></div>'
    _serve_page(page, url, body, NONCE_POLICY_WITHOUT_BASE_URI)
    page.goto(url + "/")
    page.wait_for_function("() => !!window.Citry?.fragments")
    page.evaluate("b => document.body.insertAdjacentHTML('afterbegin', `<base href='${b}'>`)", _other(url) + "/x/")
    _start_genuine(page)
    wait_for_citry_ready()
    assert page.evaluate("() => [globalThis.__widgetMounts, window.__dependency, window.__probe]") == [1, "app", None]
    assert other_requests == []


def test_base_after_start_up_moves_no_i18n_message_request_of_a_document_app(
    page: Any, serve_live: Any, wait_for_citry_ready: Any, tmp_path: Path
) -> None:
    app, switcher = _i18n_app(tmp_path)
    app.set_mounted_prefix("/citry")
    body = switcher().render().serialize()
    url = serve_live(app, "<p>unused</p>", "")
    other_requests = _record_other(page, url)
    _serve_page(page, url, body)
    page.goto(url + "/")
    wait_for_citry_ready()
    page.evaluate("b => document.body.insertAdjacentHTML('afterbegin', `<base href='${b}'>`)", _other(url) + "/x/")
    with page.expect_request(lambda request: request.method == "POST") as message_request:
        page.locator("#switch").click()
    assert message_request.value.url == url + "/citry/ext/i18n/messages"
    page.wait_for_function("() => document.getElementById('label').textContent.trim() === 'Ulozit'")
    assert other_requests == []


# An `about:srcdoc` document has no address of its own, so the runtime resolves a relative URL
# against the base URL the document took from the page that created it, which a <base> element
# inside the document also sets. The runtime uses that base only when it is on the page's origin.


@pytest.mark.parametrize("base", [False, True], ids=["no-base", "injected-base"])
def test_srcdoc_document_uses_its_base_url_only_on_its_own_origin(page: Any, serve_live: Any, *, base: bool) -> None:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class InFrame(Component):
        citry = app

        class Dependencies:
            js = [Script(url="/static/dependency.js")]

        template = '<button class="in-frame">ready</button>'
        js = "$component(() => { globalThis.__widgetMounts = (globalThis.__widgetMounts || 0) + 1; });"

    body = InFrame().render().serialize()
    url = serve_live(app, "<p>unused</p>", "")
    # The injection lands after Citry's runtime tag, so the runtime itself loads from the app.
    frame_html = body + (f'<base href="{_other(url)}/sub/">' if base else "")
    other_requests = _record_other(page, url)
    page.route(
        url + "/static/dependency.js",
        lambda route: route.fulfill(body="window.__dependency = 'app';", content_type="text/javascript"),
    )
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    _serve_page(page, url, f'<iframe srcdoc="{escape(frame_html, quote=True)}"></iframe>')
    page.goto(url + "/")
    frame = page.frames[1]
    frame.wait_for_function("() => !!window.Citry")
    if base:
        assert frame.evaluate("() => document.baseURI").startswith(_other(url))
        # The runtime refuses the files and the app does not start. Checking that nothing loads
        # needs a short wait for something that should not happen.
        frame.wait_for_timeout(1500)
        assert frame.evaluate("() => [globalThis.__widgetMounts, window.__dependency, window.__probe]") == [
            None,
            None,
            None,
        ]
        assert any("does not resolve to this page's origin" in error for error in errors), errors
    else:
        frame.wait_for_function("() => globalThis.__widgetMounts === 1", timeout=10000)
        assert frame.evaluate("() => window.__dependency") == "app"
    assert other_requests == []
