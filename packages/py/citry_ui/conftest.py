"""Shared pytest fixtures for Citry UI browser scenarios."""

from __future__ import annotations

import threading
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry.contrib.wsgi import wsgi_app
from citry_ui.quality.routes import RenderedScenario, build_scenario

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

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
