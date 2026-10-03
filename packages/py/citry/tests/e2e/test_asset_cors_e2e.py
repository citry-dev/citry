"""
A Citry page mounts inside a sandboxed iframe that has an opaque origin.

A frame sandboxed without ``allow-same-origin`` makes every request cross-origin,
even to its own server. The browser then checks ``integrity`` only on a CORS
response, so these tests prove the whole chain: the tags ask for CORS, the
asset routes allow it, and the page mounts with its styles. They also pin the
ordinary top-level page (each asset downloaded once, preload hints reused) and
the failure a host sees when a proxy strips the CORS header.
"""

from __future__ import annotations

import threading
from collections import Counter
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry import Citry, Component
from citry.contrib.wsgi import wsgi_app
from citry.ext.events.renderers import dispatcher_for

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

pytest.importorskip("playwright.sync_api")

pytestmark = pytest.mark.e2e

PREFIX = "/citry"


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


def _page_html(integrity: str) -> str:
    app = Citry(secret="asset-cors-e2e-secret", autodiscover=False, security_script_integrity=integrity)  # noqa: S106
    app.set_mounted_prefix(PREFIX)
    dispatcher_for(app)

    class Page(Component):
        citry = app
        template = """
            <html>
              <head><title>probe</title></head>
              <body><output class="probe" v-text="label">fallback</output></body>
            </html>
        """
        css = """
            .probe { color: rgb(12, 34, 56); }
        """

        def js_data(self, kwargs, slots):
            return {"label": "mounted"}

    return str(Page()), app


@pytest.fixture
def serve() -> Iterator[Callable[..., str]]:
    """Serve ``/page`` (a Citry document), ``/frame`` (the page in a sandbox), and Citry's routes."""
    servers: list[Any] = []

    def factory(page_html: str, app: Citry, *, send_cors: bool = True) -> str:
        citry_wsgi = wsgi_app(app)

        def wsgi(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            path = environ.get("PATH_INFO", "")
            if path.startswith(PREFIX + "/"):
                # Stands in for a proxy that drops the header, which is the
                # failure a host should recognize.
                def filtered(status: str, headers: list[tuple[str, str]], *rest: Any) -> Any:
                    kept = [item for item in headers if send_cors or item[0].lower() != "access-control-allow-origin"]
                    return start_response(status, kept, *rest)

                sub = {**environ, "SCRIPT_NAME": PREFIX, "PATH_INFO": path[len(PREFIX) :]}
                return list(citry_wsgi(sub, filtered))
            if path == "/frame":
                body = b'<!doctype html><iframe sandbox="allow-scripts" src="/page"></iframe>'
            else:
                body = page_html.encode()
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")])
            return [body]

        server = make_server("127.0.0.1", 0, wsgi, server_class=_ThreadingWSGIServer, handler_class=_QuietHandler)
        servers.append(server)
        threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
        return f"http://127.0.0.1:{server.server_address[1]}"

    yield factory
    for server in servers:
        server.shutdown()


def _probe(frame: Any) -> dict[str, str]:
    return frame.evaluate(
        """() => {
            const probe = document.querySelector('.probe');
            return probe ? {text: probe.textContent, color: getComputedStyle(probe).color} : {text: '', color: ''};
        }"""
    )


@pytest.mark.parametrize("integrity", ["off", "citry"])
def test_page_mounts_with_styles_inside_an_opaque_origin_sandbox(
    page: Any, serve: Callable[..., str], integrity: str
) -> None:
    html, app = _page_html(integrity)
    if integrity == "citry":
        # The runtime tag itself carries integrity here, which is the case
        # that needs CORS even before the runtime starts.
        assert 'integrity="sha384-' in html
        assert 'crossorigin="anonymous"' in html
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: message.type == "error" and errors.append(message.text))
    page.goto(serve(html, app) + "/frame", wait_until="networkidle")

    frame = page.frames[1]
    # An opaque origin is the condition under test, not an incidental detail.
    assert frame.evaluate("self.origin") == "null"
    frame.wait_for_function("document.querySelector('.probe')?.textContent === 'mounted'", timeout=5000)
    assert _probe(frame) == {"text": "mounted", "color": "rgb(12, 34, 56)"}
    assert errors == []


@pytest.mark.parametrize("integrity", ["off", "citry"])
def test_top_level_page_downloads_each_asset_once(page: Any, serve: Callable[..., str], integrity: str) -> None:
    html, app = _page_html(integrity)
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    base = serve(html, app)
    page.goto(base + "/page", wait_until="networkidle")

    assert _probe(page.main_frame) == {"text": "mounted", "color": "rgb(12, 34, 56)"}
    assets = Counter(url for url in requests if url.startswith(base + PREFIX + "/"))
    # Runtime, definition, and stylesheet each load once: the preload hints
    # carry the same crossorigin value as the tags that use them.
    assert len(assets) == 3
    assert set(assets.values()) == {1}


def test_served_page_paints_with_its_component_styles_before_the_runtime_runs(
    page: Any, serve: Callable[..., str]
) -> None:
    html, app = _page_html("off")
    # Read the style while the browser parses the page, before any Citry
    # script has run.
    probe = (
        "<script>window.__firstPaint = {color: getComputedStyle(document.querySelector('.probe')).color, "
        "runtime: typeof __citryRuntime !== 'undefined'};</script>"
    )
    html = html.replace("<script", probe + "<script", 1)
    page.goto(serve(html, app) + "/page", wait_until="networkidle")
    assert page.evaluate("window.__firstPaint") == {"color": "rgb(12, 34, 56)", "runtime": False}
    page.wait_for_function("document.querySelector('.probe')?.textContent === 'mounted'")
    # The runtime adopted the stylesheet the page linked instead of adding
    # a second one.
    assert page.locator("link[data-citry-css-url]").count() == 1
    assert _probe(page.main_frame) == {"text": "mounted", "color": "rgb(12, 34, 56)"}


def test_a_served_stylesheet_that_fails_to_load_is_reported(page: Any, serve: Callable[..., str]) -> None:
    html, app = _page_html("off")
    base = serve(html, app)
    # The stylesheet's route answers with an error status, which still gives
    # the served link a sheet; the runtime must not adopt it as loaded.
    page.route("**/*.css", lambda route: route.fulfill(status=404, body="missing", content_type="text/plain"))
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base + "/page", wait_until="networkidle")
    page.wait_for_timeout(200)
    assert any("stylesheet failed to load" in error for error in errors), errors
    assert _probe(page.main_frame)["text"] != "mounted"


def test_sandboxed_page_does_not_mount_when_a_proxy_strips_the_cors_header(
    page: Any, serve: Callable[..., str]
) -> None:
    html, app = _page_html("off")
    page.goto(serve(html, app, send_cors=False) + "/frame", wait_until="networkidle")
    frame = page.frames[1]
    page.wait_for_timeout(300)
    # Without the header the browser blocks each integrity-checked response,
    # so the owned assets never load.
    assert _probe(frame)["text"] != "mounted"
