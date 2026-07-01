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
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry.contrib.wsgi import wsgi_app

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from citry import Citry


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: browser end-to-end test (needs Playwright and a browser binary)")


def _start(server: Any) -> str:
    """Start a server on a daemon thread and return its base URL."""
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class _QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:  # keep test output quiet
        pass


@pytest.fixture
def serve_document() -> Iterator[Callable[[str], str]]:
    """Yield a function that serves one self-contained HTML page and returns its base URL."""
    servers: list[Any] = []

    def factory(html: str) -> str:
        body = html.encode()

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
