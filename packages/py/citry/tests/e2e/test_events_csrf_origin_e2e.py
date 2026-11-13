"""
Event calls send the page's CSRF token only to the page's own origin.

The runtime resolves an event call's URL against the page's own address,
so a ``<base href>`` that points at another site does not move the call,
and it does not follow an HTTP redirect, so a server answering with one
cannot pass the token on. A second server on another port stands in for
the other site and records every request that reaches it.
"""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING, Any
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

import pytest

from citry import Citry, Component
from citry.contrib.wsgi import wsgi_app
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

pytest.importorskip("pytest_playwright")

pytestmark = pytest.mark.e2e

# A harmless value that is easy to spot in the other server's log.
_TOKEN = "harmless-csrf-probe"  # noqa: S105 - a visible test value, not a secret


class _Quiet(WSGIRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass


class _ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    # One thread per request, so the page can load its runtime while an
    # event call is in flight.
    daemon_threads = True


def _start(server: Any) -> str:
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


@pytest.fixture
def other_site() -> Iterator[tuple[str, list[tuple[str, str, dict[str, str]]]]]:
    """Serve a second origin that approves every CORS request and records what it receives."""
    seen: list[tuple[str, str, dict[str, str]]] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:
            pass

        def _answer(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(length)
            seen.append((self.command, self.path, dict(self.headers)))
            # Approving the preflight is what a hostile site would do; without
            # it the browser would never send the header at all.
            self.send_response(204 if self.command == "OPTIONS" else 200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*, x-csrftoken, content-type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_OPTIONS(self) -> None:
            self._answer()

        def do_POST(self) -> None:
            self._answer()

        def do_GET(self) -> None:
            self._answer()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    base = _start(server)
    yield base, seen
    server.shutdown()


@pytest.fixture
def serve_app() -> Iterator[Callable[..., str]]:
    """Serve a page, Citry's routes below `prefix`, and `/bounce/...`, which redirects to `redirect_to`."""
    servers: list[Any] = []

    def factory(engine: Citry, html: str, *, prefix: str, redirect_to: str = "") -> str:
        citry_app = wsgi_app(engine)
        body = ("<!DOCTYPE html>" + html).encode()

        def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            path = environ.get("PATH_INFO", "")
            if path.startswith("/bounce/"):
                # A 307 keeps the method and body, so the browser would send
                # the same POST, with its headers, to the new address.
                start_response("307 Temporary Redirect", [("Location", redirect_to + path), ("Content-Length", "0")])
                return [b""]
            if path.startswith(prefix + "/"):
                sub = dict(environ)
                sub["SCRIPT_NAME"] = prefix
                sub["PATH_INFO"] = path[len(prefix) :]
                return list(citry_app(sub, start_response))
            headers = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))]
            start_response("200 OK", headers)
            return [body]

        server = make_server("127.0.0.1", 0, app, server_class=_ThreadingWSGIServer, handler_class=_Quiet)
        servers.append(server)
        return _start(server)

    yield factory
    for server in servers:
        server.shutdown()


def _counter_page(prefix: str) -> tuple[Citry, str]:
    engine = Citry(secret="events-csrf-origin-secret", autodiscover=False)  # noqa: S106
    # The page renders before the server starts, so name the prefix now:
    # the event URLs in the page start with it.
    engine.set_mounted_prefix(prefix)

    class CounterState:
        count: int = 0

        def render(self):
            return Counter(count=self.count)

    class Counter(Component):
        citry = engine
        State = CounterState
        template = """
          <main>
            <button id="bump" @c-click="bump">{{ count }}</button>
            <button id="leave" @c-click="leave">leave</button>
          </main>
        """

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def bump(self, state: CounterState):
                state.count += 1
                return state.render()

            def leave(self, state: CounterState):
                return actions.Redirect("/thanks")

    dispatcher_for(engine)
    return engine, Counter(count=0).render().serialize()


def _record_requests(page: Any) -> list[tuple[str, str, dict[str, str]]]:
    sent: list[tuple[str, str, dict[str, str]]] = []
    page.on("request", lambda request: sent.append((request.method, request.url, request.headers)))
    return sent


def _set_cookie(page: Any) -> None:
    page.evaluate(f"document.cookie = 'csrftoken={_TOKEN}; path=/'")


@pytest.mark.parametrize(("prefix", "page_path"), [("/citry", "/"), ("/shop/citry", "/shop/cart?x=1")])
def test_event_call_ignores_an_injected_base_href(
    page: Any, serve_app: Any, other_site: Any, wait_for_citry_ready: Any, prefix: str, page_path: str
) -> None:
    other, seen = other_site
    engine, html = _counter_page(prefix)
    base = serve_app(engine, html, prefix=prefix)
    page.goto(base + page_path)
    wait_for_citry_ready()
    _set_cookie(page)
    sent = _record_requests(page)
    # Markup that changes the page's base URL to the other site.
    page.evaluate(
        """(other) => {
          const element = document.createElement('base');
          element.href = other + '/';
          document.head.prepend(element);
        }""",
        other,
    )
    assert page.evaluate("document.baseURI") == other + "/"

    page.locator("#bump").click()
    page.wait_for_function("document.querySelector('#bump')?.textContent.trim() === '1'")

    calls = [(method, url, headers) for method, url, headers in sent if "/ext/events/" in url]
    assert len(calls) == 1
    method, url, headers = calls[0]
    assert (method, url) == ("POST", base + prefix + "/ext/events/call")
    assert headers.get("x-csrftoken") == _TOKEN
    assert seen == []


def test_event_call_does_not_follow_a_redirect_to_another_origin(
    page: Any, serve_app: Any, other_site: Any, wait_for_citry_ready: Any
) -> None:
    other, seen = other_site
    engine, html = _counter_page("/citry")
    base = serve_app(engine, html, prefix="/citry", redirect_to=other)
    page.goto(base + "/")
    wait_for_citry_ready()
    _set_cookie(page)
    page.evaluate(
        """() => {
          window.__errors = [];
          document.addEventListener('citry:events:error', event => window.__errors.push(event.detail.error));
          // An app's own events URL on this origin, which the server answers with a redirect.
          Citry.events.configure({url: '/bounce/ext/events/'});
        }"""
    )
    page.locator("#bump").click()
    page.wait_for_function("window.__errors.length === 1")

    errors = page.evaluate("window.__errors")
    assert "redirect" in errors[0]["message"]
    # The count stays, and nothing reached the other site: no preflight, no call.
    assert page.locator("#bump").text_content().strip() == "0"
    assert seen == []


def test_redirect_action_ignores_an_injected_base_href(
    page: Any, serve_app: Any, other_site: Any, wait_for_citry_ready: Any
) -> None:
    # A relative Redirect lands on the page's own origin, as the
    # no-JavaScript 303 does, whatever the page's base URL says.
    other, seen = other_site
    engine, html = _counter_page("/citry")
    base = serve_app(engine, html, prefix="/citry")
    page.goto(base + "/shop/cart")
    wait_for_citry_ready()
    page.evaluate(
        """(other) => {
          const element = document.createElement('base');
          element.href = other + '/';
          document.head.prepend(element);
        }""",
        other,
    )
    page.locator("#leave").click()
    page.wait_for_url(base + "/thanks")
    assert seen == []
