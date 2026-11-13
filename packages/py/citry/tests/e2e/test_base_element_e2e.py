"""
A `<base>` element cannot swap Citry's runtime script.

Site B answers every URL with a script that leaves a visible mark. Both servers
send CORS headers, so only the `integrity` check can stop the script. The
Citry settings stay at their defaults: the tag must carry it on its own. The
unit tests in `test_owned_file_integrity.py` show the other tags carry it too.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any

import pytest

from citry import Citry, Component

if TYPE_CHECKING:
    from collections.abc import Iterator

pytest.importorskip("playwright.sync_api")

pytestmark = pytest.mark.e2e

MARK = b"document.documentElement.setAttribute('data-from-other', '1');"
NONCE = "base-element-nonce"


class _Server(BaseHTTPRequestHandler):
    bodies: dict[str, tuple[bytes, str]]
    headers_to_send: dict[str, str]
    seen: list[str]

    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass

    def do_GET(self) -> None:
        self.seen.append(self.path)
        body, content_type = self.bodies.get(self.path, (MARK, "text/javascript"))
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        for name, value in self.headers_to_send.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def _start(
    bodies: dict[str, tuple[bytes, str]], headers: dict[str, str]
) -> tuple[ThreadingHTTPServer, str, list[str]]:
    seen: list[str] = []
    handler = type("Handler", (_Server,), {"bodies": bodies, "headers_to_send": headers, "seen": seen})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}", seen


@pytest.fixture
def other_site() -> Iterator[tuple[str, list[str]]]:
    server, url, seen = _start({}, {})
    yield url, seen
    server.shutdown()


def _page_html(base_url: str, *, nonce: str | None) -> str:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class Page(Component):
        citry = app
        template = """
            <html>
              <head><title>t</title></head>
              <body><button @click="open = true">open</button></body>
            </html>
        """

    html = Page().render().serialize(csp_nonce=nonce)
    return html.replace("<body>", f'<body><base href="{base_url}/">', 1)


@pytest.mark.parametrize("nonce", [None, NONCE])
def test_runtime_from_another_site_does_not_run(
    page: Any, other_site: tuple[str, list[str]], nonce: str | None
) -> None:
    other_url, other_seen = other_site
    headers = {} if nonce is None else {"Content-Security-Policy": f"script-src 'nonce-{nonce}'"}
    html = _page_html(other_url, nonce=nonce).encode()
    server, url, _ = _start({"/": (html, "text/html; charset=utf-8")}, headers)
    try:
        page.goto(url)
        page.wait_for_load_state("load")
        # The request does reach the other site, so this also proves the
        # base element took effect and the browser refused the answer.
        page.wait_for_function("() => performance.getEntriesByType('resource').length > 0")
        assert "/citry/citry.js" in other_seen
        assert page.evaluate("document.documentElement.getAttribute('data-from-other')") is None
    finally:
        server.shutdown()
