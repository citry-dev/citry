"""
Shared pytest fixtures for Citry UI browser scenarios.

The wait helpers at the end of this file (`wait_for_citry_ready`,
`send_event`, `wait_for_count`, `fake_clock`, `settle_timers`,
`wait_for_animations`) are the same region as in
`packages/py/citry/tests/e2e/conftest.py`; a test keeps the two copies
identical. `open_scenario` uses the region's `_RECORD_CITRY_READY`.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry.contrib.wsgi import wsgi_app
from citry_ui.quality.routes import RenderedScenario, build_scenario

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sized

    from citry import Citry


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


@pytest.fixture
def serve_citry_ui_live() -> Iterator[Callable[[Citry, str], str]]:
    servers: list[WSGIServer] = []

    def factory(citry: Citry, page_html: str) -> str:
        prefix = "/citry"
        citry.set_mounted_prefix(prefix)
        citry_wsgi = wsgi_app(citry)

        def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            path = environ.get("PATH_INFO", "")
            if path == prefix or path.startswith(prefix + "/"):
                sub = dict(environ)
                sub["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + prefix
                sub["PATH_INFO"] = path[len(prefix) :]
                return list(citry_wsgi(sub, start_response))
            body = page_html.encode()
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        server = make_server(
            "127.0.0.1",
            0,
            app,
            server_class=_ThreadingWSGIServer,
            handler_class=_QuietWSGIHandler,
        )
        servers.append(server)
        # Avoid the stdlib's 0.5-second shutdown polling cost for every browser
        # scenario while preserving the same local-server behavior.
        threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.01},
            daemon=True,
        ).start()
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield factory
    for server in servers:
        server.shutdown()


# The runtime appends each component stylesheet to `<head>` when it mounts the
# app, so a stylesheet placed in the served `<head>` always precedes Citry's.
_FRAMEWORK_CSS_LAST = """css => {
  const style = document.createElement('style');
  style.setAttribute('data-quality-external-css', '');
  style.textContent = css;
  document.head.append(style);
}"""
_FRAMEWORK_CSS_ORDER = """() => {
  const external = document.querySelector('[data-quality-external-css]');
  const citry = [...document.querySelectorAll('[data-citry-css-url]')];
  return {
    citry: citry.length,
    citry_after_external: citry.filter(
      element => external.compareDocumentPosition(element) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).length,
  };
}"""


_ALL_DOCUMENT_APPS_READY = """() => {
  const apps = document.querySelectorAll('script[type="application/json"][data-citry-vue-document]').length;
  return (window.__citryReadyApps?.length ?? 0) >= apps;
}"""


@pytest.fixture
def open_scenario(
    page: Any,
    serve_citry_ui_live: Callable[[Citry, str], str],
) -> Callable[..., RenderedScenario]:
    """
    Serve one quality scenario from a live server and navigate the page to it.

    A scenario page loads the Vue runtime, its component definitions, and its
    stylesheets from `/citry/...` URLs. `page.set_content()` leaves the page on
    `about:blank`, where those URLs cannot resolve, so no component would ever
    start. Serving the page and its assets from one origin gives the browser
    the same delivery a real host provides.

    `framework_css` adds a third-party stylesheet either before every Citry
    stylesheet or after all of them, and checks that order before returning.

    It returns once every Citry app on the page has dispatched `citry:ready`.
    `page.goto()` returns at `load`, which comes before the runtime mounts, so
    a click right after it can reach server HTML with no handler attached.
    """

    def open_(
        scenario_id: str,
        *,
        transform: Callable[[str], str] | None = None,
        framework_css: str | None = None,
        framework_css_after_citry: bool = False,
    ) -> RenderedScenario:
        rendered = build_scenario(scenario_id)
        # Tests that add a CSP edit the finished document, so apply the edit
        # before the server hands the page out.
        html = rendered.html if transform is None else transform(rendered.html)
        if framework_css is not None and not framework_css_after_citry:
            if "<head>" not in html:
                pytest.fail("the scenario page has no <head> to hold the framework stylesheet")
            stylesheet = f'<style data-quality-external-css="">{framework_css}</style>'
            html = html.replace("<head>", "<head>" + stylesheet, 1)
        page.add_init_script(_RECORD_CITRY_READY)
        base_url = serve_citry_ui_live(rendered.app, html)
        page.goto(base_url + "/", wait_until="load")
        # Each Citry app on the page starts from one configuration block, so
        # the block count says how many `citry:ready` events to wait for. A
        # scenario without client components has no block and returns at once.
        page.wait_for_function(_ALL_DOCUMENT_APPS_READY)
        if framework_css is None:
            return rendered
        # The app inserts its stylesheets while it mounts; after `citry:ready`
        # every stylesheet the first render needs is in `<head>`. A stylesheet
        # loaded later for new content would still land after this one.
        page.wait_for_selector(rendered.scenario.ready_selector, state="attached")
        if framework_css_after_citry:
            page.evaluate(_FRAMEWORK_CSS_LAST, framework_css)
        order = page.evaluate(_FRAMEWORK_CSS_ORDER)
        # Without a Citry stylesheet the cascade comparison would prove nothing.
        if order["citry"] == 0:
            pytest.fail("the scenario loaded no Citry stylesheet")
        expected_after = 0 if framework_css_after_citry else order["citry"]
        if order["citry_after_external"] != expected_after:
            pytest.fail(f"framework stylesheet is in the wrong cascade position: {order}")
        return rendered

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
