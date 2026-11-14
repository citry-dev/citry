"""
A page links Citry's browser runtime at a URL named by its content hash.

These browser tests check the claims in ``docs/design/runtime_hashed_urls.md``
section 7, the results that would show the design is wrong:

- a second page load reuses the browser's copy of the runtime;
- a page whose runtime the server no longer holds keeps its server HTML,
  writes exactly one console error that names the runtime URL (also on a page
  with two apps), sends no request of its own, and does not reload;
- a missing i18n plugin script gives the runtime's own plugin error and the
  page does not reload;
- a page reopened with the back button runs the runtime its HTML names.

The server is a real WSGI app with Citry's routes mounted under ``/citry``.
It logs every request it receives, so the tests count what reached the server
rather than what Playwright saw. Playwright's ``page.route`` turns the
browser's HTTP cache off, so the tests that depend on that cache change
answers on the server instead.
"""

from __future__ import annotations

import base64
import hashlib
import re
import threading
from collections.abc import Callable
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry import Citry, Component
from citry.contrib.wsgi import wsgi_app
from citry.ext.dependencies.routes import SHARED_RUNTIME
from citry.ext.i18n.emission import I18N_RUNTIME

if TYPE_CHECKING:
    from collections.abc import Iterator

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e

PREFIX = "/citry"
RUNTIME_PATH = f"{PREFIX}/{SHARED_RUNTIME.hashed_path}"
I18N_PATH = f"{PREFIX}/{I18N_RUNTIME.hashed_path}"
MISSING_MESSAGE = "Citry could not load its runtime"
PLUGIN_ERROR = "missing or incompatible Citry browser plugin: i18n"
# A well-formed digest that names no runtime this server holds.
UNKNOWN_DIGEST = "0" * 64
MISSING_PATH = f"{PREFIX}/citry.{UNKNOWN_DIGEST}.js"

# Each page counts as a fresh load only when the browser did not restore it
# from the back/forward cache, which would skip its scripts entirely.
_RECORD_PAGESHOW = "addEventListener('pageshow', e => { window.__pageshowPersisted = e.persisted; });"
# Page markup can take over plain window names, so these two elements answer
# `window.__citryRuntime` and `window.__citryRuntimeMissing` until a script
# sets a property of that name.
_TAKEOVER_MARKUP = '<div id="__citryRuntime"></div><div id="__citryRuntimeMissing"></div>'

Response = tuple[int, list[tuple[str, str]], bytes]
Handler = Callable[[str, str], "Response | None"]


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


class Server:
    """A live server: test pages and Citry's mounted routes, with a log of each request."""

    def __init__(self, app: Citry, handler: Handler) -> None:
        self.log: list[tuple[str, str]] = []
        self._citry = wsgi_app(app)
        self._handler = handler
        self._server = make_server(
            "127.0.0.1", 0, self._wsgi, server_class=_ThreadingWSGIServer, handler_class=_QuietHandler
        )
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"

    def count(self, method: str, path: str) -> int:
        """Return how many requests with this method reached this path."""
        return sum(1 for entry in self.log if entry == (method, path))

    def _wsgi(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ["REQUEST_METHOD"]
        path = environ.get("PATH_INFO", "")
        self.log.append((method, path))
        # The test's handler answers first, so it can stand in for a worker
        # that lacks a runtime or holds another version of it.
        answer = self._handler(method, path)
        if answer is not None:
            status, headers, body = answer
            start_response(f"{status} X", headers)
            return [] if method == "HEAD" else [body]
        if path.startswith(PREFIX + "/"):
            sub = {**environ, "SCRIPT_NAME": PREFIX, "PATH_INFO": path[len(PREFIX) :]}
            return list(self._citry(sub, start_response))
        start_response("404 Not Found", [("Content-Type", "text/plain")])
        return [b""]

    def shutdown(self) -> None:
        self._server.shutdown()


@pytest.fixture
def serve() -> Iterator[Callable[[Citry, Handler], Server]]:
    servers: list[Server] = []

    def factory(app: Citry, handler: Handler) -> Server:
        server = Server(app, handler)
        servers.append(server)
        return server

    yield factory
    for server in servers:
        server.shutdown()


def _html(body: str, *headers: tuple[str, str]) -> Response:
    return 200, [("Content-Type", "text/html; charset=utf-8"), *headers], body.encode()


def _pages(pages: dict[str, str]) -> Handler:
    """Return a handler that answers each path in `pages` with its HTML, whatever the method."""
    return lambda _method, path: _html(pages[path]) if path in pages else None


def _engine(integrity: str = "off", **options: Any) -> Citry:
    app = Citry(secret="runtime-hashed-urls-e2e", autodiscover=False, security_script_integrity=integrity, **options)  # noqa: S106
    app.set_mounted_prefix(PREFIX)
    return app


def _page_class(app: Citry) -> type[Component]:
    class Page(Component):
        citry = app
        template = """
            <html>
              <head><title>probe</title></head>
              <body>
                <h1 class="server">Server copy</h1>
                <output class="probe" v-text="label">fallback</output>
              </body>
            </html>
        """

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"label": "mounted"}

    return Page


def _page_html(app: Citry) -> str:
    """Render the probe page as a full document, the way a host sends it."""
    return _page_class(app)().render().serialize()


def _missing(html: str, digest: str = UNKNOWN_DIGEST) -> str:
    """Return a page that links a runtime hash no server holds, as a page from an older deploy does."""
    assert SHARED_RUNTIME.digest in html
    return html.replace(SHARED_RUNTIME.digest, digest)


def _record_console(page: Any) -> tuple[list[str], list[str]]:
    """Collect the runtime-missing console errors and every page error."""
    missing: list[str] = []
    errors: list[str] = []
    page.on("console", lambda m: m.type == "error" and MISSING_MESSAGE in m.text and missing.append(m.text))
    page.on("pageerror", lambda error: errors.append(str(error)))
    return missing, errors


def _wait_for(page: Any, items: list[Any], count: int, *, quiet_ms: int = 600) -> None:
    """Wait until `items` holds `count` entries, then wait `quiet_ms` more and check that nothing else arrived."""
    for _ in range(500):
        if len(items) >= count:
            break
        page.wait_for_timeout(10)
    # A second report or a reload would come after the first, so keep watching a while.
    page.wait_for_timeout(quiet_ms)
    assert len(items) == count, items


def _requests_other_than_get(server: Server) -> list[tuple[str, str]]:
    """Return every request the server saw that was not a GET; a page that only loads and starts sends none."""
    return [entry for entry in server.log if entry[0] != "GET"]


# -- 1. Repeat loads ---------------------------------------------------------


@pytest.mark.parametrize("integrity", ["off", "citry"])
def test_a_second_page_reuses_the_browsers_copy_of_the_runtime(
    page: Any, serve: Callable[..., Server], wait_for_citry_ready: Any, integrity: str
) -> None:
    app = _engine(integrity)
    html = str(_page_class(app)())
    if integrity == "citry":
        assert 'integrity="sha384-' in html
    pages = {"/one": html, "/two": html}
    server = serve(app, _pages(pages))

    page.goto(server.url + "/one")
    wait_for_citry_ready(1)
    page.goto(server.url + "/two")
    wait_for_citry_ready(1)

    # The preload hint and the script tag share one crossorigin value and the
    # answer is immutable, so the second page asks the server for nothing.
    assert server.count("GET", RUNTIME_PATH) == 1
    assert server.count("GET", f"{PREFIX}/citry.js") == 0


# -- 2. A missing runtime keeps the server HTML and says so once --------------


@pytest.mark.parametrize("failure", ["not-found", "aborted"])
def test_a_missing_runtime_keeps_the_server_html_and_says_so_once(
    page: Any, serve: Callable[..., Server], failure: str
) -> None:
    app = _engine("citry")
    html = _page_html(app)
    url = RUNTIME_PATH
    if failure == "not-found":
        # A page from an older deploy names a hash that no worker holds, so the
        # server answers 404 for it.
        html = _missing(html)
        url = MISSING_PATH
    else:
        # The same message when the request fails as on a dropped connection:
        # the start script only sees that the runtime never defined its name.
        page.route(f"**{RUNTIME_PATH}", lambda route: route.abort())
    missing, errors = _record_console(page)
    server = serve(app, _pages({"/page": html}))

    page.goto(server.url + "/page")
    _wait_for(page, missing, 1)

    assert missing == [f"{MISSING_MESSAGE}: {url}"]
    # The page asked for itself once, never reloaded, and sent no request of its own.
    assert server.count("GET", "/page") == 1
    assert _requests_other_than_get(server) == []
    if failure == "not-found":
        # The 404 is stored nowhere, so a second request for the file would
        # show that the page retries it, or that its preload hint and script
        # tag disagree.
        assert server.count("GET", url) == 1
    assert page.evaluate("performance.getEntriesByType('navigation')[0].type") == "navigate"
    assert page.evaluate("sessionStorage.length") == 0
    # The server HTML is still all the visitor sees, and the report is the only failure.
    assert page.locator(".server").text_content() == "Server copy"
    assert page.locator(".probe").text_content() == "fallback"
    assert errors == []


def test_a_sandboxed_frame_with_no_origin_reports_a_missing_runtime_once(
    page: Any, serve: Callable[..., Server], browser_name: str
) -> None:
    app = _engine("citry")
    html = _missing(_page_html(app))
    # A sandboxed frame has no origin, so its storage throws and every request
    # it sends is cross-origin. The start script must still report once.
    frame = '<!doctype html><iframe sandbox="allow-scripts" src="/page"></iframe>'
    pages = {"/page": html, "/frame": frame}
    missing, errors = _record_console(page)
    console: list[str] = []
    page.on("console", lambda message: console.append(message.text))
    server = serve(app, _pages(pages))

    page.goto(server.url + "/frame")
    _wait_for(page, missing, 1)

    assert page.frames[1].evaluate("self.origin") == "null"
    assert missing == [f"{MISSING_MESSAGE}: {MISSING_PATH}"]
    if browser_name != "firefox":
        # The 404 allows any origin, so the browser reports the missing file
        # itself and not a CORS failure that would hide it. Firefox words a
        # blocked script as a CORS failure even then, so it is left out.
        assert [text for text in console if re.search(r"cors|cross-origin|access-control", text, re.IGNORECASE)] == []
    assert server.count("GET", "/page") == 1
    assert _requests_other_than_get(server) == []
    assert errors == []


def test_two_apps_on_one_page_report_a_missing_runtime_once(page: Any, serve: Callable[..., Server]) -> None:
    app = _engine("citry")
    # Two documents joined into one page, as a host layout might, give two
    # start scripts; the first one to find the runtime missing reports for both.
    page_class = _page_class(app)
    html = _missing(page_class().render().serialize() + page_class().render().serialize())
    missing, errors = _record_console(page)
    server = serve(app, _pages({"/page": html}))

    page.goto(server.url + "/page")
    _wait_for(page, missing, 1)

    assert page.locator(".server").count() == 2
    assert html.count('data-citry-vue-document="') == 2
    assert missing == [f"{MISSING_MESSAGE}: {MISSING_PATH}"]
    assert server.count("GET", "/page") == 1
    assert errors == []


@pytest.mark.parametrize("runtime", ["present", "missing"])
def test_markup_that_takes_the_runtime_names_does_not_change_the_outcome(
    page: Any, serve: Callable[..., Server], wait_for_citry_ready: Any, runtime: str
) -> None:
    app = _engine("citry")
    html = _page_html(app).replace("<body>", f"<body>{_TAKEOVER_MARKUP}", 1)
    assert _TAKEOVER_MARKUP in html
    if runtime == "missing":
        html = _missing(html)
    missing, errors = _record_console(page)
    server = serve(app, _pages({"/page": html}))

    page.goto(server.url + "/page")
    if runtime == "present":
        # The elements answer the plain names, but the start script reads
        # only window's own properties, so it still finds the runtime and
        # starts the app.
        wait_for_citry_ready(1)
        assert page.locator(".probe").text_content() == "mounted"
        assert missing == []
    else:
        # It also still finds that the runtime is missing, and the elements do
        # not stand in for it or for the flag that keeps the report to one.
        _wait_for(page, missing, 1)
        assert missing == [f"{MISSING_MESSAGE}: {MISSING_PATH}"]
        assert page.locator(".probe").text_content() == "fallback"
    assert errors == []


# -- 3. A missing i18n plugin script ------------------------------------------


def _i18n_page_html() -> tuple[Citry, str]:
    app = _engine(extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}})

    class Page(Component):
        citry = app
        template = """
            <html>
              <head><title>probe</title></head>
              <body>
                <c-i18n c-client="True" tag="section">
                  <output class="locale" v-text="$i18n.context.locale">fallback</output>
                </c-i18n>
              </body>
            </html>
        """

    html = Page().render().serialize()
    assert I18N_PATH in html
    return app, html


def test_a_missing_i18n_plugin_gives_the_runtimes_plugin_error_and_no_reload(
    page: Any, serve: Callable[..., Server]
) -> None:
    app, html = _i18n_page_html()
    plugin_errors: list[str] = []
    other_errors: list[str] = []
    page.on(
        "pageerror",
        lambda error: (plugin_errors if PLUGIN_ERROR in str(error) else other_errors).append(str(error)),
    )
    missing, _ = _record_console(page)

    def handler(_method: str, path: str) -> Response | None:
        if path == "/page":
            return _html(html)
        # Stands in for a worker on another version that lacks this plugin.
        if path == I18N_PATH:
            return 404, [("Cache-Control", "no-store"), ("Content-Type", "text/plain")], b""
        return None

    server = serve(app, handler)
    page.goto(server.url + "/page")
    _wait_for(page, plugin_errors, 1)

    # The runtime loaded, so the only report is its own plugin error.
    assert missing == []
    assert other_errors == []
    assert server.count("GET", "/page") == 1
    assert _requests_other_than_get(server) == []
    assert page.evaluate("performance.getEntriesByType('navigation')[0].type") == "navigate"
    assert page.evaluate("sessionStorage.length") == 0
    assert page.locator(".locale").text_content() == "fallback"


# -- 4. Prerendering -----------------------------------------------------------


# Only Chromium acts on speculation rules.
@pytest.mark.only_browser("chromium")
def test_a_visit_after_prerendering_reports_a_missing_runtime_once(page: Any, serve: Callable[..., Server]) -> None:
    """
    Prerender a page whose runtime is missing, then follow the link to it.

    Headless Chromium fetches the page for speculation rules before the click
    but runs none of its scripts until the user arrives, so this shows only
    that the visit then reports once and fetches the page no second time. It
    does not reach a script started inside a prerendered page.
    """
    app = _engine("citry")
    html = _missing(_page_html(app))
    start = (
        '<!doctype html><a href="/page">go</a><script type="speculationrules">'
        '{"prerender": [{"source": "list", "urls": ["/page"]}]}</script>'
    )
    pages = {"/start": start, "/page": html}
    missing, errors = _record_console(page)
    server = serve(app, _pages(pages))

    page.goto(server.url + "/start")
    for _ in range(300):
        if server.count("GET", "/page"):
            break
        page.wait_for_timeout(10)
    assert server.count("GET", "/page") == 1
    assert server.count("GET", MISSING_PATH) == 0
    page.locator("a").click()
    _wait_for(page, missing, 1)

    # The visit used the prerendered HTML and did not ask for the page again.
    assert missing == [f"{MISSING_MESSAGE}: {MISSING_PATH}"]
    assert server.count("GET", "/page") == 1
    assert _requests_other_than_get(server) == []
    assert errors == []


# -- 5. The back button never pairs a page with another runtime --------------


@pytest.mark.parametrize("integrity", ["off", "citry"])
def test_a_page_reopened_with_the_back_button_runs_the_runtime_its_html_names(
    page: Any, serve: Callable[..., Server], wait_for_citry_ready: Any, integrity: str
) -> None:
    """
    Upgrade the runtime between two pages, go back, and check which runtime the first page runs.

    The runtime is read once per process, so the test plays the upgraded
    worker on the server side: page B links a second runtime whose bytes end
    with a marker, and once B is requested the server answers ``404`` for the
    first runtime and sends the second one at both the stable URL and its own
    hash, as a worker on the next version would. Page A then must run the
    first runtime from the browser's copy, never the second one.
    """
    app = _engine(integrity)
    page_a = _page_html(app)
    upgraded_bytes = SHARED_RUNTIME.content.encode() + b"\nwindow.__citryRuntimeMarker = 'upgraded';\n"
    upgraded_digest = hashlib.sha256(upgraded_bytes).hexdigest()
    page_b = page_a.replace(SHARED_RUNTIME.digest, upgraded_digest)
    # The runtime tag carries its integrity with every setting, so page B
    # names the upgraded bytes' digest as a page from that worker would.
    old = "sha384-" + base64.b64encode(hashlib.sha384(SHARED_RUNTIME.content.encode()).digest()).decode()
    new = "sha384-" + base64.b64encode(hashlib.sha384(upgraded_bytes).digest()).decode()
    assert old in page_b
    page_b = page_b.replace(old, new)
    upgraded = [False]
    javascript = [("Content-Type", "text/javascript; charset=utf-8")]

    def handler(method: str, path: str) -> Response | None:
        if path == "/a":
            return _html(page_a)
        if path == "/b":
            upgraded[0] = True
            return _html(page_b)
        if path == f"{PREFIX}/citry.{upgraded_digest}.js":
            return 200, [*javascript, ("Cache-Control", "public, max-age=31536000, immutable")], upgraded_bytes
        if upgraded[0] and path == RUNTIME_PATH:
            return 404, [("Cache-Control", "no-store"), ("Content-Type", "text/plain")], b""
        if upgraded[0] and path == f"{PREFIX}/citry.js":
            return 200, [*javascript, ("Cache-Control", "no-store")], upgraded_bytes
        return None

    page.add_init_script(_RECORD_PAGESHOW)
    missing, errors = _record_console(page)
    server = serve(app, handler)

    page.goto(server.url + "/a")
    wait_for_citry_ready(1)
    page.goto(server.url + "/b")
    wait_for_citry_ready(1)
    assert page.evaluate("window.__citryRuntimeMarker") == "upgraded"
    page.go_back()
    wait_for_citry_ready(1)

    state = page.evaluate(
        "({marker: window.__citryRuntimeMarker ?? null, persisted: window.__pageshowPersisted,"
        " type: performance.getEntriesByType('navigation')[0].type})"
    )
    # A page restored from the back/forward cache would not run any script,
    # so the check below would prove nothing.
    assert state == {"marker": None, "persisted": False, "type": "back_forward"}
    assert page.locator(".probe").text_content() == "mounted"
    assert server.count("GET", RUNTIME_PATH) == 1
    assert missing == []
    assert errors == []
