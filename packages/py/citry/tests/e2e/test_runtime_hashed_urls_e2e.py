"""
A page links Citry's browser runtime at a URL named by its content hash.

These browser tests check the claims in ``docs/design/runtime_hashed_urls.md``
section 7, the results that would show the design is wrong:

- a second page load reuses the browser's copy of the runtime;
- a page whose runtime the server no longer holds reloads at most once, and
  never when it cannot tell whether it already reloaded, when the app marked
  it as answering a form POST, or when the runtime failed for another reason;
- a missing i18n plugin script follows the same rule;
- a page reopened with the back button runs the runtime its HTML names.

The server is a real WSGI app with Citry's routes mounted under ``/citry``.
It logs every request it receives, so the tests count what reached the server
(including the ``HEAD`` probe) rather than what Playwright saw. Playwright's
``page.route`` turns the browser's HTTP cache off, so the tests that depend on
that cache change answers on the server instead.
"""

from __future__ import annotations

import base64
import hashlib
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
# A well-formed digest that names no runtime this server holds.
UNKNOWN_DIGEST = "0" * 64

# Each page counts as a fresh load only when the browser did not restore it
# from the back/forward cache, which would skip its scripts entirely.
_RECORD_PAGESHOW = "addEventListener('pageshow', e => { window.__pageshowPersisted = e.persisted; });"
_BLOCK_SESSION_STORAGE = """
Object.defineProperty(window, 'sessionStorage', {
  get() { throw new DOMException('blocked by the test', 'SecurityError'); },
});
"""
# Removes both sources the start script reads to tell a reload from a first
# load, as in a browser that offers neither.
_REMOVE_NAVIGATION_TYPE = """
delete Performance.prototype.getEntriesByType;
delete Performance.prototype.navigation;
"""

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


def _get_page(app: Citry) -> str:
    """Render the probe page as the answer to a GET, the only kind of page that may reload itself."""
    return _page_class(app)().render().serialize(request_method="GET")


def _missing(html: str, digest: str = UNKNOWN_DIGEST) -> str:
    """Return a page that links a runtime hash no server holds, as a page from an older deploy does."""
    assert SHARED_RUNTIME.digest in html
    return html.replace(SHARED_RUNTIME.digest, digest)


def _record_console(page: Any) -> tuple[list[str], list[str]]:
    """Collect the runtime-missing errors and every page error, across reloads."""
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
    # A second reload would come after the probe, so keep watching a while.
    page.wait_for_timeout(quiet_ms)
    assert len(items) == count, items


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


# -- 2. A missing runtime reloads the page at most once ----------------------


@pytest.mark.parametrize("variant", ["plain", "session-storage-blocked", "new-hash-on-every-load"])
def test_a_missing_runtime_reloads_the_page_once(page: Any, serve: Callable[..., Server], variant: str) -> None:
    app = _engine("citry")
    html = _get_page(app)
    loads = [0]

    def handler(method: str, path: str) -> Response | None:
        if path != "/page":
            return None
        loads[0] += 1
        # Stands in for a host whose cache answers each load with a page from
        # yet another old deploy.
        digest = f"{loads[0]:064x}" if variant == "new-hash-on-every-load" else UNKNOWN_DIGEST
        return _html(_missing(html, digest))

    if variant == "session-storage-blocked":
        page.add_init_script(_BLOCK_SESSION_STORAGE)
    missing, _ = _record_console(page)
    server = serve(app, handler)

    page.goto(server.url + "/page")
    _wait_for(page, missing, 1)

    assert server.count("GET", "/page") == 2
    heads = [path for method, path in server.log if method == "HEAD"]
    assert len(heads) == 1
    # The reload kept the server HTML; it is still all the user sees.
    assert page.locator(".server").text_content() == "Server copy"
    assert page.locator(".probe").text_content() == "fallback"


def test_a_missing_runtime_reloads_a_sandboxed_frame_with_no_origin_once(
    page: Any, serve: Callable[..., Server]
) -> None:
    app = _engine("citry")
    html = _missing(_get_page(app))
    frame = '<!doctype html><iframe sandbox="allow-scripts" src="/page"></iframe>'
    pages = {"/page": html, "/frame": frame}
    missing, _ = _record_console(page)
    server = serve(app, _pages(pages))

    page.goto(server.url + "/frame")
    _wait_for(page, missing, 1)

    assert page.frames[1].evaluate("self.origin") == "null"
    heads = [path for method, path in server.log if method == "HEAD"]
    assert len(heads) == 1
    assert server.count("GET", "/page") == 2


@pytest.mark.parametrize("variant", ["no-navigation-type", "request-method-post", "no-request-method"])
def test_a_missing_runtime_does_not_reload_when_the_page_must_not(
    page: Any, serve: Callable[..., Server], variant: str
) -> None:
    app = _engine("citry")
    render = _page_class(app)().render()
    if variant == "request-method-post":
        html = render.serialize(request_method="POST")
    elif variant == "no-request-method":
        # Citry cannot tell which method the page answers, so it never reloads.
        html = render.serialize()
    else:
        html = render.serialize(request_method="GET")
        # The page cannot tell a reload from a first load, so it never reloads.
        page.add_init_script(_REMOVE_NAVIGATION_TYPE)
    missing, errors = _record_console(page)
    server = serve(app, _pages({"/page": _missing(html)}))

    page.goto(server.url + "/page")
    _wait_for(page, missing, 1)

    assert server.count("GET", "/page") == 1
    assert [entry for entry in server.log if entry[0] == "HEAD"] == []
    assert page.locator(".server").text_content() == "Server copy"
    assert errors == []


# -- 3. A runtime that fails for another reason never reloads ---------------


@pytest.mark.parametrize("probe", ["answers-200", "aborted"])
def test_a_runtime_that_fails_to_load_without_a_404_keeps_the_server_html(
    page: Any, serve: Callable[..., Server], probe: str
) -> None:
    app = _engine("citry")
    html = _get_page(app)
    missing, _ = _record_console(page)
    server = serve(app, _pages({"/page": html}))

    def route(route: Any) -> None:
        # The runtime itself fails as on a dropped connection; the probe
        # either reaches the server, which holds this runtime, or fails too.
        if route.request.method == "HEAD" and probe == "answers-200":
            route.continue_()
        else:
            route.abort()

    page.route(f"**{RUNTIME_PATH}", route)
    page.goto(server.url + "/page")
    _wait_for(page, missing, 1)

    assert server.count("GET", "/page") == 1
    assert server.count("HEAD", RUNTIME_PATH) == (1 if probe == "answers-200" else 0)
    assert page.locator(".server").text_content() == "Server copy"


# -- 4. A missing i18n plugin script ------------------------------------------


def _i18n_page_html(*, request_method: str | None = None) -> tuple[Citry, str]:
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

    html = Page().render().serialize(request_method=request_method)
    assert I18N_PATH in html
    return app, html


@pytest.mark.parametrize("request_method", ["GET", None, "POST"])
def test_a_missing_i18n_plugin_reloads_a_full_page_once(
    page: Any, serve: Callable[..., Server], request_method: str | None
) -> None:
    app, html = _i18n_page_html(request_method=request_method)
    # The app fails to start with this error on every load, including the
    # first load of a page that then reloads.
    failed_starts: list[str] = []
    page.on("pageerror", lambda error: "browser plugin: i18n" in str(error) and failed_starts.append(str(error)))

    def handler(method: str, path: str) -> Response | None:
        if path == "/page":
            return _html(html)
        # Stands in for a worker on another version that lacks this plugin.
        if path == I18N_PATH:
            return 404, [("Cache-Control", "no-store"), ("Content-Type", "text/plain")], b""
        return None

    server = serve(app, handler)
    # Only a page the app marked as answering a GET may reload.
    expected_loads = 2 if request_method == "GET" else 1
    page.goto(server.url + "/page")
    _wait_for(page, failed_starts, expected_loads)

    assert server.count("GET", "/page") == expected_loads
    assert server.count("HEAD", I18N_PATH) == expected_loads - 1
    assert server.count("HEAD", RUNTIME_PATH) == 0
    assert page.locator(".locale").text_content() == "fallback"


# -- 5. A page that answers a form POST --------------------------------------


_FORM = '<!doctype html><form method="post" action="/submit"><button>send</button></form>'


def _submit(page: Any, server: Server) -> list[str]:
    """Send the form, dismiss any dialog the browser shows, and return the dialogs it showed."""
    dialogs: list[str] = []

    def dismiss(dialog: Any) -> None:
        dialogs.append(f"{dialog.type}: {dialog.message}")
        dialog.dismiss()

    page.on("dialog", dismiss)
    page.goto(server.url + "/form")
    page.locator("button").click()
    return dialogs


@pytest.mark.parametrize("request_method", ["POST", None])
def test_a_page_that_answers_a_post_does_not_reload(
    page: Any, serve: Callable[..., Server], request_method: str | None
) -> None:
    """
    Answer a form POST with a page whose runtime is missing, and check that it never reloads.

    A reload of such a page sends the form again. Playwright's Chromium,
    headless and headed, and Google Chrome resend the POST without asking;
    Firefox asks first and WebKit reloads with a GET. So a page reloads only
    when the app passes ``request_method="GET"`` or ``"HEAD"``, and a page
    rendered without ``request_method`` keeps its server HTML like a POST
    page does.
    """
    app = _engine("citry")
    html = _missing(_page_class(app)().render().serialize(request_method=request_method))
    pages = {("GET", "/form"): _FORM, ("POST", "/submit"): html}
    missing, _ = _record_console(page)
    server = serve(app, lambda method, path: _html(pages[method, path]) if (method, path) in pages else None)

    dialogs = _submit(page, server)
    _wait_for(page, missing, 1, quiet_ms=1500)

    assert server.count("POST", "/submit") == 1
    assert [entry for entry in server.log if entry[0] == "HEAD"] == []
    assert dialogs == []
    assert page.locator(".server").text_content() == "Server copy"


# -- 6. Prerendering -----------------------------------------------------------


# Only Chromium acts on speculation rules.
@pytest.mark.only_browser("chromium")
def test_a_visit_after_prerendering_behaves_like_an_ordinary_load(page: Any, serve: Callable[..., Server]) -> None:
    """
    Prerender a page whose runtime is missing, then follow the link to it.

    Headless Chromium fetches the page for speculation rules before the click
    but runs none of its scripts until the user arrives, so this shows only
    that the visit then costs at most one reload, like any other load. It
    does not reach a reload started inside a prerendered page.
    """
    app = _engine("citry")
    html = _missing(_get_page(app))
    start = (
        '<!doctype html><a href="/page">go</a><script type="speculationrules">'
        '{"prerender": [{"source": "list", "urls": ["/page"]}]}</script>'
    )
    pages = {"/start": start, "/page": html}
    missing, _ = _record_console(page)
    server = serve(app, _pages(pages))

    page.goto(server.url + "/start")
    for _ in range(300):
        if server.count("GET", "/page"):
            break
        page.wait_for_timeout(10)
    assert server.count("GET", "/page") == 1
    assert server.count("GET", RUNTIME_PATH) == 0
    page.locator("a").click()
    _wait_for(page, missing, 1)

    # The visit used the prerendered HTML, probed once, and reloaded once.
    assert server.count("GET", "/page") == 2
    assert server.count("HEAD", f"{PREFIX}/citry.{UNKNOWN_DIGEST}.js") == 1


# -- 7. The back button never pairs a page with another runtime --------------


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
    page_a = _get_page(app)
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
