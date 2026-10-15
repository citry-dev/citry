"""
Shared pytest fixtures for Citry UI browser scenarios.

The wait helpers below (`send_event`, `wait_for_count`, `fake_clock`,
`settle_timers`, `wait_for_animations`) are a copy of the ones in
`packages/py/citry/tests/e2e/conftest.py`, which explains why each obvious
wait is not enough. Change both together.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
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


# Record each app's `citry:ready` event. Both fixtures below may install it on
# one page, so a second copy leaves the first listener in charge.
_RECORD_CITRY_READY = """
(() => {
  if (window.__citryReadyApps) return;
  window.__citryReadyApps = [];
  document.addEventListener('citry:ready', event => {
    window.__citryReadyApps.push(event.detail.appId);
  });
})();
"""

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
        if framework_css is not None:
            page.add_init_script(_RECORD_CITRY_READY)
        base_url = serve_citry_ui_live(rendered.app, html)
        page.goto(base_url + "/", wait_until="load")
        if framework_css is None:
            return rendered
        # The app inserts its stylesheets while it mounts; after `citry:ready`
        # every stylesheet the first render needs is in `<head>`. A stylesheet
        # loaded later for new content would still land after this one.
        page.wait_for_function("() => window.__citryReadyApps.length > 0")
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


@pytest.fixture
def wait_for_citry_ready(page: Any) -> Callable[..., None]:
    """
    Record each Citry app's `citry:ready` event and return a function that waits for them.

    The runtime dispatches `citry:ready` on `document` once an app has mounted
    and finished its first render, which is the point where page code may use
    `Citry.events`. The listener is an init script, so request this fixture
    before navigating; an event dispatched before the listener exists would be
    lost and the wait would time out.
    """
    page.add_init_script(_RECORD_CITRY_READY)

    def wait(apps: int = 1) -> None:
        page.wait_for_function("apps => window.__citryReadyApps.length >= apps", arg=apps)

    return wait


# Count each finished Events call by handler name. The runtime dispatches
# `citry:events:after` when a call has finished, after it applied the server's
# actions (a Render included) and ran `onServerRender`. The listener is on the
# capture phase so a page that stops the event's propagation cannot hide it.
_COUNT_FINISHED_EVENTS = """handler => {
  if (!window.__citryFinishedEvents) {
    window.__citryFinishedEvents = [];
    document.addEventListener('citry:events:after', event => {
      window.__citryFinishedEvents.push(event.detail.event);
    }, true);
  }
  return window.__citryFinishedEvents.filter(name => handler === null || name === handler).length;
}"""


@pytest.fixture
def send_event(page: Any) -> Callable[..., Any]:
    """
    Return a function that runs an action and waits until the Events call it starts has finished.

    `send(action, handler=None)` runs `action` (a click, a key press), waits
    for the `/ext/events/` response it causes, then waits until the browser
    reports one more finished call (for `handler` only, when given). It
    returns the Playwright response.

    The response alone is not enough: the browser applies it afterwards,
    across several microtasks and a Vue update. Two animation frames are not
    enough either on a loaded runner. The `citry:events:after` event fires only
    once the call's actions have been applied, so a check after it sees the
    new page. Without a page reload in between, the counter keeps working for
    later calls on the same page.
    """

    def send(action: Callable[[], object], *, handler: str | None = None) -> Any:
        before = page.evaluate(_COUNT_FINISHED_EVENTS, handler)
        with page.expect_response(lambda response: "/ext/events/" in response.url) as response:
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

    The final check is exact, so an extra item is still a failure.
    """

    def wait(items: Sized, count: int, *, timeout: float = 5.0) -> None:
        deadline = time.monotonic() + timeout
        while len(items) < count and time.monotonic() < deadline:
            page.wait_for_timeout(10)
        if len(items) != count:
            pytest.fail(f"expected {count} items, got {len(items)}: {items!r}")

    return wait


# How far each fake-clock step stays from a timer deadline. Handling a DOM
# event can move the fake clock by a fraction of a millisecond, so a step that
# lands exactly on a deadline may or may not fire the timer.
_DEADLINE_MARGIN_MS = 10


class FakeClock:
    """Playwright's fake clock for one page, paused, with steps that keep a margin from timer deadlines."""

    def __init__(self, page: Any) -> None:
        self._page = page

    def install_paused(self) -> None:
        """
        Install the fake clock and pause it; call this before navigating.

        An installed clock follows real time until it is paused, and pausing
        after the page loads leaves a window where a slow load fires a timer
        early. Pausing first means only `run_for()` and the steps below move
        timers. Mounting the app does not need timers, so the page still
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
        Move the clock to a little before a deadline `ms` away, to check that nothing happened yet.

        Pair it with `run_past_deadline()`. Stepping to one millisecond short
        and then one more lands on the deadline itself, where a fraction of a
        millisecond decides whether the timer fires.
        """
        self._page.clock.run_for(ms - _DEADLINE_MARGIN_MS)

    def run_past_deadline(self) -> None:
        """After `run_short_of()`, cross the deadline and stop the same margin after it."""
        self._page.clock.run_for(2 * _DEADLINE_MARGIN_MS)


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
