"""Shared pytest fixtures for Citry UI browser scenarios."""

from __future__ import annotations

import threading
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry.contrib.wsgi import wsgi_app

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
