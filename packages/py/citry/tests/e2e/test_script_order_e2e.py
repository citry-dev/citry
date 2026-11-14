"""
Browser e2e for how component scripts load and fail (issue #145).

A standalone page is HTML written while no web integration is mounted, so
every script is an inline tag and the browser runs them as it parses. A
mounted page has `set_mounted_prefix` called, and Citry's browser code adds
each component script as a `<script src>` tag, one at a time. Each rule below
is proved on the page kinds it applies to.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.browser_render import BrowserPluginDescriptor
from citry.ext.dependencies import Script
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for
from citry.extension import Extension

pytestmark = pytest.mark.e2e

# A browser plugin that installs nothing. The runtime refuses to start a page
# whose server data names a plugin the page never registered, so the plugin
# script registers it. It also writes its place in the page's script order.
_PLUGIN_SCRIPT = """
(window.__order = window.__order || []).push('plugin');
__citryRuntime.registerBrowserPlugin('probe', 1, () => ({
  install() {},
  prepareRevision() { return {}; },
  activateRevision() {},
  commitRevision() {},
  abortRevision() {},
  rollbackRevision() {},
  dispose() {},
}), []);
"""

# Records every error the page reports, including the ones a script catches
# and reports again, and the error that stops a failed start. The listener is
# an init script so no error reaches the page before it exists.
_RECORD_ERRORS = """
(() => {
  window.__errors = [];
  window.addEventListener('error', event => {
    const error = event.error;
    window.__errors.push({
      name: error ? String(error.name) : null,
      message: error ? String(error.message) : String(event.message),
      cause: error?.cause ? String(error.cause.message) : null,
    });
  });
})();
"""


class _Probe(Extension):
    name = "probe"

    def browser_plugin(self) -> BrowserPluginDescriptor:
        return BrowserPluginDescriptor(1, Script(content=_PLUGIN_SCRIPT, wrap=False))


def _engine(*, mounted: bool, with_plugin: bool = False) -> Citry:
    engine = Citry(
        secret="script-order-e2e-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
        extensions=[_Probe] if with_plugin else [],
    )
    # The prefix must be set before the page renders, because it decides
    # whether the page's scripts are inline tags or URLs.
    if mounted:
        engine.set_mounted_prefix("/citry")
    return engine


@pytest.fixture
def open_page(page: Any, serve_document: Any, serve_live: Any, wait_for_citry_ready: Any) -> Any:
    """Return a function that serves rendered HTML as a standalone or a mounted page and opens it."""
    # Both listeners are init scripts, so each is in place before any page script runs.
    page.add_init_script(_RECORD_ERRORS)

    def open_(engine: Citry, html: str, *, mounted: bool, fragment_html: str = "") -> None:
        base = serve_live(engine, html, fragment_html) if mounted else serve_document(html)
        page.goto(base + "/")

    return open_


def _error_messages(page: Any) -> list[str]:
    return [item["message"] for item in page.evaluate("() => window.__errors")]


@pytest.mark.parametrize("mounted", [False, True], ids=["standalone", "mounted"])
def test_browser_plugin_script_runs_before_component_scripts(
    page: Any, open_page: Any, wait_for_citry_ready: Any, mounted: bool
) -> None:
    engine = _engine(mounted=mounted, with_plugin=True)

    class Widget(Component):
        citry = engine
        template = """
            <p>widget</p>
        """
        js = """
        (window.__order = window.__order || []).push('component');
        $component({
          onServerRender() {
            window.__order.push('callback');
          },
        });
        """

    open_page(engine, Widget().render().serialize(), mounted=mounted)
    wait_for_citry_ready()

    # The plugin script ran first, then the component's own, and the callback ran once the app started.
    assert page.evaluate("() => window.__order") == ["plugin", "component", "callback"]
    assert _error_messages(page) == []


# Each builder defines one `Widget` whose `js` fails in a different way. The `js` is a literal in
# each class so the test reads the way a component author would write it.
def _widget_that_throws_before_registering(engine: Citry) -> type[Component]:
    class Widget(Component):
        citry = engine
        template = """
            <p>widget</p>
        """
        js = """
            throw new Error('script boom');
        """

    return Widget


def _widget_that_throws_after_registering(engine: Citry) -> type[Component]:
    class Widget(Component):
        citry = engine
        template = """
            <p>widget</p>
        """
        # `$component` has already registered the type's options when the script throws, so a
        # check that only asked whether the options registered would let this start go on.
        js = """
            $component({
              onServerRender() {
                window.__callbackRan = true;
              },
            });
            throw new Error('script boom');
        """

    return Widget


def _widget_with_a_syntax_error(engine: Citry) -> type[Component]:
    class Widget(Component):
        citry = engine
        template = """
            <p>widget</p>
        """
        js = """
            const = ;
            $component({
              onServerRender() {
                window.__callbackRan = true;
              },
            });
        """

    return Widget


@pytest.mark.parametrize("mounted", [False, True], ids=["standalone", "mounted"])
@pytest.mark.parametrize(
    ("build_widget", "original_name", "original_message", "startup_error", "cause"),
    [
        (
            _widget_that_throws_before_registering,
            "Error",
            "script boom",
            "Citry Vue component script threw while it ran: Widget_",
            "script boom",
        ),
        (
            _widget_that_throws_after_registering,
            "Error",
            "script boom",
            "Citry Vue component script threw while it ran: Widget_",
            "script boom",
        ),
        (
            _widget_with_a_syntax_error,
            # Each browser words a syntax error its own way, so only its type is checked.
            "SyntaxError",
            None,
            "Citry Vue component script did not run to its end: Widget_",
            None,
        ),
    ],
    ids=["throws-before-registering", "throws-after-registering", "syntax-error"],
)
def test_failing_component_script_stops_startup(
    page: Any,
    open_page: Any,
    mounted: bool,
    build_widget: Any,
    original_name: str,
    original_message: str | None,
    startup_error: str,
    cause: str | None,
) -> None:
    engine = _engine(mounted=mounted)
    widget = build_widget(engine)

    open_page(engine, widget().render().serialize(), mounted=mounted)
    # The page's own `error` event sees the script's error first, then the error that stops the start.
    page.wait_for_function("() => window.__errors.length >= 2")
    # A third error would be a second start attempt or a leaked callback error; give it a moment to show.
    page.wait_for_timeout(200)

    errors = page.evaluate("() => window.__errors")
    assert len(errors) == 2
    assert errors[0]["name"] == original_name
    assert errors[0]["cause"] is None
    if original_message is not None:
        assert errors[0]["message"] == original_message
    assert errors[1]["message"].startswith(startup_error)
    assert errors[1]["cause"] == cause
    assert page.evaluate("() => window.__citryReadyApps.length") == 0
    # A callback that a failed script registered never runs, because the app never starts.
    assert page.evaluate("() => window.__callbackRan") is None


@pytest.mark.parametrize("mounted", [False, True], ids=["standalone", "mounted"])
def test_throwing_dependencies_file_does_not_stop_startup(
    page: Any, open_page: Any, wait_for_citry_ready: Any, mounted: bool
) -> None:
    engine = _engine(mounted=mounted)

    class Widget(Component):
        citry = engine

        class Dependencies:
            js = [
                Script(
                    content="""
                    throw new Error('extra boom');
                    """,
                    wrap=False,
                ),
            ]

        template = """
            <p>widget</p>
        """
        js = """
        window.__order = ['component'];
        $component({
          onServerRender() {
            window.__order.push('callback');
          },
        });
        """

    open_page(engine, Widget().render().serialize(), mounted=mounted)
    wait_for_citry_ready()

    # The file's error reaches the page's `error` event like any uncaught error, and nothing stops the
    # app: the component script that comes after the file runs, and so does its callback.
    assert _error_messages(page) == ["extra boom"]
    assert page.evaluate("() => window.__order") == ["component", "callback"]


@pytest.mark.parametrize(
    ("script_url", "route", "stops"),
    [
        ("http://third-party.test/analytics.js", "http://third-party.test/analytics.js", False),
        ("/same-origin.js", "**/same-origin.js", True),
    ],
    ids=["other-origin-skipped", "same-origin-stops"],
)
def test_failed_script_url_is_skipped_only_for_another_origin(
    page: Any, open_page: Any, script_url: str, route: str, stops: bool
) -> None:
    engine = _engine(mounted=True)
    warnings: list[str] = []
    page.on(
        "console",
        lambda message: warnings.append(message.text) if message.text.startswith("[Citry]") else None,
    )
    # The browser reports a blocked request and a network failure the same way.
    page.route(route, lambda handler: handler.abort("blockedbyclient"))

    class Widget(Component):
        citry = engine

        class Dependencies:
            js = [Script(url=script_url)]

        template = """
            <p>widget</p>
        """
        js = """
        window.__componentRan = true;
        """

    open_page(engine, Widget().render().serialize(), mounted=True)
    if stops:
        page.wait_for_function("() => window.__errors.some(error => error.message.includes('failed to load'))")
        assert "Citry Vue type script failed to load: /same-origin.js" in _error_messages(page)
        assert page.evaluate("() => window.__citryReadyApps.length") == 0
        assert page.evaluate("() => window.__componentRan") is None
    else:
        page.wait_for_function("() => window.__citryReadyApps.length === 1")
        assert _error_messages(page) == []
        assert page.evaluate("() => window.__componentRan") is True
        [warning] = [text for text in warnings if script_url in text]
        # The warning names the file and says what the page lacks and what to do about it.
        assert warning.startswith(f"[Citry] skipped a script from another origin that failed to load: {script_url}. ")
        assert "The page started without it" in warning


def test_skipped_third_party_script_is_tried_again_by_a_later_fragment(
    page: Any, open_page: Any, wait_for_citry_ready: Any, wait_for_count: Any, browser_name: str
) -> None:
    engine = _engine(mounted=True)
    # Citry writes this warning once per failed attempt, so it counts the attempts in every browser.
    # Other warnings (Firefox words its own about the blocked URL) are not counted.
    skips: list[str] = []
    page.on(
        "console",
        lambda message: skips.append(message.text) if message.text.startswith("[Citry] skipped") else None,
    )
    requests: list[str] = []

    def refuse(route: Any) -> None:
        requests.append(route.request.url)
        route.abort()

    page.route("http://third-party.test/analytics.js", refuse)

    class Widget(Component):
        citry = engine

        class Dependencies:
            js = [Script(url="http://third-party.test/analytics.js")]

        template = """
            <p>widget</p>
        """
        js = """
        window.__componentRan = true;
        """

    fragment_html = Widget().render().serialize(deps_strategy="fragment")
    open_page(engine, Widget().render().serialize(), mounted=True, fragment_html=fragment_html)
    wait_for_citry_ready()
    wait_for_count(skips, 1)

    # The fragment lists the same file. The page kept no record of the skipped one, so the browser asks again.
    page.evaluate(
        """async () => {
          const html = await (await fetch('/fragment')).text();
          const target = document.createElement('div');
          document.body.append(target);
          target.innerHTML = html;
        }"""
    )
    wait_for_count(skips, 2)
    page.wait_for_function("() => window.__citryReadyApps.length === 2")
    assert _error_messages(page) == []
    # In WebKit, Playwright answers a repeated request for a routed URL without calling the route again,
    # so the route sees every attempt only in the other browsers.
    if browser_name != "webkit":
        assert len(requests) == 2


def test_failed_other_origin_file_listed_by_two_components_is_requested_once(
    page: Any, open_page: Any, wait_for_citry_ready: Any, wait_for_count: Any
) -> None:
    engine = _engine(mounted=True)
    url = "http://third-party.test/analytics.js"
    skips: list[str] = []
    page.on(
        "console",
        lambda message: skips.append(message.text) if message.text.startswith("[Citry] skipped") else None,
    )
    requests: list[str] = []

    def refuse(route: Any) -> None:
        requests.append(route.request.url)
        route.abort()

    page.route(url, refuse)

    class Alpha(Component):
        citry = engine

        class Dependencies:
            js = [Script(url=url)]

        template = """
            <b>alpha</b>
        """
        # Only a component with its own `js` starts a browser app that reads the file list.
        js = """
            window.__ran = (window.__ran || 0) + 1;
        """

    class Beta(Component):
        citry = engine

        class Dependencies:
            js = [Script(url=url)]

        template = """
            <i>beta</i>
        """
        # Only a component with its own `js` starts a browser app that reads the file list.
        js = """
            window.__ran = (window.__ran || 0) + 1;
        """

    class Page(Component):
        citry = engine
        template = """
            <main>
                <c-Alpha />
                <c-Beta />
            </main>
        """

    html = Page().render().serialize()
    # The server lists the shared file once for each component type that owns it. Without two
    # entries the page below would prove nothing, because a single entry is always requested once.
    assert html.count(f'"url":"{url}"') == 2, html

    open_page(engine, html, mounted=True)
    wait_for_citry_ready()
    wait_for_count(skips, 1)
    # A second request or warning would come right after the first, so give it a moment to show.
    page.wait_for_timeout(200)

    # The app started without the file, and the browser asked for it once and the page warned once.
    assert len(skips) == 1
    assert len(requests) == 1
    assert _error_messages(page) == []


def test_failed_other_origin_file_listed_twice_in_a_server_render_is_requested_once(
    page: Any, open_page: Any, wait_for_citry_ready: Any, wait_for_count: Any, send_event: Any
) -> None:
    engine = _engine(mounted=True)
    url = "http://third-party.test/analytics.js"
    skips: list[str] = []
    page.on(
        "console",
        lambda message: skips.append(message.text) if message.text.startswith("[Citry] skipped") else None,
    )
    requests: list[str] = []

    def refuse(route: Any) -> None:
        requests.append(route.request.url)
        route.abort("blockedbyclient")

    page.route(url, refuse)

    class Alpha(Component):
        citry = engine

        class Dependencies:
            js = [Script(url=url)]

        template = """
            <b>alpha</b>
        """
        # The two scripts differ, so the last assertion shows that each component's own script ran.
        js = """
            window.__alphaRan = true;
        """

    class Beta(Component):
        citry = engine

        class Dependencies:
            js = [Script(url=url)]

        template = """
            <i>beta</i>
        """
        js = """
            window.__betaRan = true;
        """

    class Page(Component):
        citry = engine

        class Kwargs:
            show: bool = False

        class Events:
            # The page starts without the two components, so the file reaches the browser only
            # in the server render that this handler causes.
            def show(self) -> Any:
                return actions.Render(Page(show=True))

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"show": kwargs.show}

        template = """
            <main>
                <button
                    id="show"
                    @c-click="show"
                >show</button>
                <c-Alpha c-if="show" />
                <c-Beta c-if="show" />
            </main>
        """
        # The page needs a script of its own, so that a browser app starts and can receive the server render.
        js = """
            window.__pageRan = true;
        """

    dispatcher_for(engine)
    html = Page().render().serialize()
    # The page itself does not mention the file.
    assert url not in html, html
    open_page(engine, html, mounted=True)
    wait_for_citry_ready()
    assert skips == []
    assert requests == []
    listed: list[int] = []

    def allow_lazy_types(route: Any) -> None:
        # The server marks a component type that lists a file (`Dependencies`) as not allowed to join
        # a page late, so the browser would reject this render. This test is about how the browser
        # loads such a file, so the response marks every file and type in it as allowed. A real
        # response never allows it, so this guards the browser's behavior, not a path an app can take.
        response = route.fetch()
        body = response.json()
        for result in body["results"]:
            for action in result["actions"]:
                prepared = action.get("prepared")
                if not prepared:
                    continue
                # The server lists the file once for each of the two component types that own it.
                listed.append([item["source"].get("url") for item in prepared["scripts"]].count(url))
                for item in [*prepared["scripts"], *prepared["typePolicies"]]:
                    item["lazyAllowed"] = True
        route.fulfill(response=response, body=json.dumps(body))

    page.route("**/ext/events/call", allow_lazy_types)
    send_event(lambda: page.locator("#show").click())
    assert listed == [2]

    # The server render went on without the file: both components are on the page. The browser
    # asked for the file once and the page warned once.
    assert page.locator("b").count() == 1
    assert page.locator("i").count() == 1
    wait_for_count(skips, 1)
    # The event has finished, so the server render's file loop is done; the pause is a last check
    # that no late second request or warning follows.
    page.wait_for_timeout(200)
    assert len(skips) == 1
    assert len(requests) == 1
    # The two component scripts ran, so the page works without the file.
    assert page.evaluate("() => [window.__pageRan, window.__alphaRan, window.__betaRan]") == [True, True, True]
    assert _error_messages(page) == []
