"""
Shared harness for the browser e2e tests (tests/e2e): two small servers on
background threads that Playwright can point a real browser at.

- ``serve_document`` serves one self-contained HTML page. The ``document``
  dependency strategy inlines the runtime and every component's JS/CSS, so the
  page fetches nothing and a plain static server is enough.
- ``serve_live`` runs a real WSGI server that also mounts citry's dependency
  routes (``/citry/...``), so the ``fragment`` strategy can fetch component
  JS/CSS on demand, exactly as it would in a deployed app.

Each is a pytest fixture that yields a factory: call it in a test to start a
server and get its base URL; every server started is shut down at teardown.
Playwright comes from the optional ``e2e`` dependency group; each test module
``importorskip``s it, so the suite is skipped anywhere Playwright is not
installed (the default dev env).

The second half holds the wait helpers. Each one waits for the state that
proves a step finished, because the obvious wait (a short sleep, a value the
server already wrote into the page) can pass before the browser has done the
work. ``packages/py/citry_ui/conftest.py`` holds the same region of
helpers; a test keeps the two copies identical.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sized

    from citry import Citry


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: browser end-to-end test (needs Playwright and a browser binary)")


def _start(server: Any) -> str:
    """Start a server on a daemon thread and return its base URL."""
    # The stdlib default polls every 0.5 seconds, so every fixture teardown can
    # spend half a second waiting for an otherwise idle server to notice
    # shutdown. A short test-only interval keeps the same server behavior while
    # making hundreds of browser-test teardowns substantially cheaper.
    threading.Thread(
        target=server.serve_forever,
        kwargs={"poll_interval": 0.01},
        daemon=True,
    ).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


def _with_doctype(html: str) -> str:
    """Return ``html`` with ``<!DOCTYPE html>`` in front unless it already starts with a doctype."""
    # Many tests serve a rendered fragment as the whole page. Without a
    # doctype the browser renders it in quirks mode, unlike a real app's
    # page, and Firefox logs a warning that the tests' console checks report.
    if html.lstrip().lower().startswith("<!doctype"):
        return html
    return "<!DOCTYPE html>" + html


@pytest.fixture
def serve_document() -> Iterator[Callable[[str], str]]:
    """Yield a function that serves one self-contained HTML page and returns its base URL."""
    servers: list[Any] = []

    def factory(html: str) -> str:
        body = _with_doctype(html).encode()

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args: Any) -> None:  # keep test output quiet
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        servers.append(server)
        return _start(server)

    yield factory
    for server in servers:
        server.shutdown()


@pytest.fixture
def serve_live() -> Iterator[Callable[..., str]]:
    """Yield a function that serves a page + fragment with citry's dependency routes mounted."""
    servers: list[Any] = []

    def factory(citry: Citry, page_html: str, fragment_html: str, prefix: str = "/citry") -> str:
        citry.set_mounted_prefix(prefix)
        page_html = _with_doctype(page_html)
        citry_wsgi = wsgi_app(citry)

        def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            path = environ.get("PATH_INFO", "")
            if path == prefix or path.startswith(prefix + "/"):
                # Emulate a real mount: the prefix moves into SCRIPT_NAME.
                sub = dict(environ)
                sub["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + prefix
                sub["PATH_INFO"] = path[len(prefix) :]
                return list(citry_wsgi(sub, start_response))
            body = (fragment_html if path == "/fragment" else page_html).encode()
            start_response(
                "200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))]
            )
            return [body]

        server = make_server("127.0.0.1", 0, app, server_class=_ThreadingWSGIServer, handler_class=_QuietWSGIHandler)
        servers.append(server)
        return _start(server)

    yield factory
    for server in servers:
        server.shutdown()


@pytest.fixture
def open_citry_page(page: Any, wait_for_citry_ready: Callable[..., None]) -> Callable[..., None]:
    """
    Return a function that navigates to a URL and waits until `apps` Citry apps are ready.

    `page.goto()` returns at the `load` event, which comes before the runtime
    finishes mounting, so a test that acts right after it races the mount.
    See `wait_for_citry_ready` for why other signals are not enough.
    """

    def open_(url: str, *, apps: int = 1) -> None:
        page.goto(url)
        wait_for_citry_ready(apps)

    return open_


# BEGIN shared browser wait helpers
# This region is identical in packages/py/citry/tests/e2e/conftest.py and
# packages/py/citry_ui/conftest.py; packages/py/citry_ui/tests/
# test_e2e_wait_helper_copies.py fails when the two copies differ.

# Record each app's `citry:ready` event. A test may install this twice on one
# page (directly and through a fixture), so a second copy leaves the first
# listener in charge instead of resetting the list.
_RECORD_CITRY_READY = """
(() => {
  if (window.__citryReadyApps) return;
  window.__citryReadyApps = [];
  document.addEventListener('citry:ready', event => {
    window.__citryReadyApps.push(event.detail.appId);
  });
})();
"""


@pytest.fixture
def wait_for_citry_ready(page: Any) -> Callable[..., None]:
    """
    Record each Citry app's `citry:ready` event and return a function that waits for them.

    The runtime dispatches `citry:ready` on `document` once an app has mounted
    and finished its first render; only then are its event handlers attached.
    The obvious checks pass earlier: `__citryRuntime._apps` gains the app when
    its configuration is read, its `revision` is already 0, and the text the
    server wrote is in the page before Vue mounts. A click sent at that point
    reaches plain HTML and does nothing.

    `wait(apps)` waits until `apps` apps are ready and then fails if more than
    `apps` are, so a test that expects one app notices a second. Pass
    `at_least=True` when more apps may legitimately be ready.

    The listener is an init script, so request this fixture before navigating;
    an event dispatched before the listener exists would be lost.
    """
    page.add_init_script(_RECORD_CITRY_READY)

    def wait(apps: int = 1, *, at_least: bool = False) -> None:
        page.wait_for_function("apps => (window.__citryReadyApps?.length ?? 0) >= apps", arg=apps)
        ready = page.evaluate("() => window.__citryReadyApps.length")
        if not at_least and ready != apps:
            pytest.fail(f"expected {apps} ready Citry apps, got {ready}")

    return wait


# Count each finished Events call by handler name. The runtime dispatches
# `citry:events:after` when a call has finished, after it applied the actions
# the call waits for (a Render included) and ran `onServerRender`. The listener
# is on the capture phase so a page that stops the event's propagation cannot
# hide it.
_COUNT_FINISHED_EVENTS = """handler => {
  if (!window.__citryFinishedEvents) {
    window.__citryFinishedEvents = [];
    document.addEventListener('citry:events:after', event => {
      window.__citryFinishedEvents.push(event.detail.event);
    }, true);
  }
  return window.__citryFinishedEvents.filter(name => handler === null || name === handler).length;
}"""


def _is_event_response(response: Any, handler: str | None) -> bool:
    """Return whether `response` answers an Events call, and a call to `handler` when one is given."""
    request = response.request
    if "/ext/events/" not in request.url:
        return False
    if handler is None:
        return True
    # A POST carries the call in its JSON body as `calls[0].handlerName`.
    try:
        body = request.post_data_json
    except ValueError:
        body = None
    if isinstance(body, dict) and body.get("calls"):
        return bool(body["calls"][0].get("handlerName") == handler)
    # A GET call has no body; its URL ends with the handler name instead.
    return unquote(urlsplit(request.url).path.rsplit("/", 1)[-1]) == handler


@pytest.fixture
def send_event(page: Any) -> Callable[..., Any]:
    """
    Return a function that runs an action and waits until the Events call it starts has finished.

    `send(action, handler=None)` runs `action` (a click, a key press), waits
    for the `/ext/events/` response it causes, then waits until the browser
    reports one more finished call. It returns the Playwright response.

    Pass `handler` whenever another call may still be in flight: the wait then
    matches only the response to a call to that handler, and only a finished
    call to it. Without `handler`, the first Events response and the first
    finished call of any handler satisfy the wait.

    The response alone is not enough: the browser applies it afterwards,
    across several microtasks and a Vue update. Two animation frames are not
    enough either on a loaded runner. The `citry:events:after` event fires only
    once the call's actions have been applied, so a check after it sees the
    new page. Without a page reload in between, the counter keeps working for
    later calls on the same page.
    """

    def send(action: Callable[[], object], *, handler: str | None = None) -> Any:
        before = page.evaluate(_COUNT_FINISHED_EVENTS, handler)
        with page.expect_response(lambda response: _is_event_response(response, handler)) as response:
            action()
        page.wait_for_function(
            "([handler, before]) => window.__citryFinishedEvents"
            ".filter(name => handler === null || name === handler).length > before",
            arg=[handler, before],
        )
        return response.value

    return send


@pytest.fixture
def wait_for_count(page: Any) -> Callable[..., None]:
    """
    Return a function that waits until a list filled by a Playwright callback has `count` items.

    Tests collect requests or held routes in a Python list from `page.on()` or
    `page.route()` callbacks. Those callbacks run only while Playwright is
    waiting on the browser, so the loop waits with `page.wait_for_timeout()`
    (which lets them run) rather than `time.sleep()` (which does not). A
    one-shot `assert len(items) == count` right after an action reads the list
    before the callback for a request already in flight has run.

    The final check is exact, but it runs as soon as `count` items arrive, so
    an item that arrives later is not caught. Follow it with a short negative
    check when an extra item is the failure the test guards against.
    """

    def wait(items: Sized, count: int, *, timeout: float = 5.0) -> None:
        deadline = time.monotonic() + timeout
        while len(items) < count and time.monotonic() < deadline:
            page.wait_for_timeout(10)
        if len(items) != count:
            pytest.fail(f"expected {count} items, got {len(items)}: {items!r}")

    return wait


# How far `run_past_deadline()` goes beyond a deadline. A step that lands
# exactly on a deadline tests the timer's boundary rule rather than the
# behavior under test, so steps stop just short of a deadline and then cross
# it by this much.
_PAST_DEADLINE_MS = 10


class FakeClock:
    """Playwright's fake clock for one page, paused before load, with steps that stop short of and cross deadlines."""

    def __init__(self, page: Any) -> None:
        self._page = page

    def install_paused(self) -> None:
        """
        Install the fake clock and pause it; call this before navigating.

        An installed clock follows real time until it is paused, and pausing
        after the page loads leaves a window where a slow load fires a timer
        early. Pausing first means only `run_for()` and the steps below move
        timers, and the page's clock does not move while the test clicks or
        types. Mounting the app does not need timers, so the page still
        becomes ready while the clock is paused.
        """
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._page.clock.install(time=start)
        self._page.clock.pause_at(start + timedelta(seconds=1))

    def run_for(self, ms: int) -> None:
        """Move the paused clock forward by exactly `ms` and fire the timers that fall due."""
        self._page.clock.run_for(ms)

    def run_short_of(self, ms: int) -> None:
        """
        Move the clock to one millisecond before a deadline `ms` away, to check that nothing happened yet.

        The paused clock moves only when the test moves it, so one millisecond
        short is a deterministic "not yet". Pair it with `run_past_deadline()`.
        """
        self._page.clock.run_for(ms - 1)

    def run_past_deadline(self) -> None:
        """After `run_short_of()`, cross the deadline and stop a little after it."""
        self._page.clock.run_for(1 + _PAST_DEADLINE_MS)


@pytest.fixture
def fake_clock(page: Any) -> FakeClock:
    """Return a `FakeClock` for the test's page; call `install_paused()` on it before navigating."""
    return FakeClock(page)


@pytest.fixture
def settle_timers(page: Any) -> Callable[[], None]:
    """
    Return a function that waits for one `setTimeout(0)` and then two animation frames, in one call.

    Use it after a step whose effects the page schedules on a zero-delay timer
    and then paints, for example before a check that something did not happen.
    Separate `evaluate` calls each take a round trip, which spreads the wait
    over unrelated work. This does not work while a fake clock is paused,
    because the page's timers and frames wait for the clock.
    """

    def settle() -> None:
        page.evaluate(
            "() => new Promise(resolve => setTimeout("
            "() => requestAnimationFrame(() => requestAnimationFrame(resolve)), 0))"
        )

    return settle


@pytest.fixture
def wait_for_animations() -> Callable[[Any], None]:
    """
    Return a function that waits until a locator's element and its descendants finish their animations.

    A fixed sleep guesses how long a transition takes and fails when a slow
    runner drops frames. This waits on each animation's `finished` promise
    instead. Animations that repeat forever never finish, so they are skipped,
    and a cancelled animation counts as done.
    """

    def wait(locator: Any) -> None:
        locator.evaluate(
            "element => Promise.all(element.getAnimations({subtree: true})"
            ".filter(animation => animation.effect?.getComputedTiming().iterations !== Infinity)"
            ".map(animation => animation.finished.catch(() => null)))"
        )

    return wait


# END shared browser wait helpers
