"""
Browser e2e for how component scripts load and fail (issue #145).

A standalone page is HTML written while no web integration is mounted, so
every script is an inline tag and the browser runs them as it parses. A
mounted page has `set_mounted_prefix` called, and Citry's browser code adds
each component script as a `<script src>` tag, one at a time. Each rule below
is proved on the page kinds it applies to.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.browser_render import BrowserPluginDescriptor
from citry.ext.dependencies import Script
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
        template = "<p>widget</p>"
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


@pytest.mark.parametrize("mounted", [False, True], ids=["standalone", "mounted"])
@pytest.mark.parametrize(
    ("body", "original_name", "original_message", "startup_error", "cause"),
    [
        (
            "throw new Error('script boom');",
            "Error",
            "script boom",
            "Citry Vue component script threw while it ran: Widget_",
            "script boom",
        ),
        (
            "const = ;",
            # Each browser words a syntax error its own way, so only its type is checked.
            "SyntaxError",
            None,
            "Citry Vue component script did not run to its end (it may have failed to parse): Widget_",
            None,
        ),
    ],
    ids=["throws", "syntax-error"],
)
def test_failing_component_script_stops_startup(
    page: Any,
    open_page: Any,
    mounted: bool,
    body: str,
    original_name: str,
    original_message: str | None,
    startup_error: str,
    cause: str | None,
) -> None:
    engine = _engine(mounted=mounted)

    class Widget(Component):
        citry = engine
        template = "<p>widget</p>"
        js = (
            body
            + """
        $component({
          onServerRender() {
            window.__callbackRan = true;
          },
        });
        """
        )

    open_page(engine, Widget().render().serialize(), mounted=mounted)
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

        template = "<p>widget</p>"
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

        template = "<p>widget</p>"
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
        assert [text for text in warnings if script_url in text] == [
            f"[Citry] skipped a third-party script that failed to load: {script_url}"
        ]


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

        template = "<p>widget</p>"
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
