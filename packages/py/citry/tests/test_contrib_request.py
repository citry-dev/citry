"""
Cross-adapter tests of the framework-neutral request/response contract.

Every web adapter hands route handlers the same ``RouteRequest`` (readable
body, case-insensitive headers, repeated query keys, the host object as
``native``) and forwards ``RouteResponse.headers`` back to the client. The
ASGI adapter additionally awaits ``async def`` handlers and runs sync
handlers in a worker thread; the sync adapters (WSGI, Django) reject async
handlers with an error naming the fix. Design: docs/design/events.md
section 12, items 1 to 3.
"""

import asyncio
import io
import json
import threading
import time
from contextlib import contextmanager

import pytest

from citry import Citry, Extension, RouteHeaders, RouteRequest, RouteResponse, URLRoute
from citry.util.routing import call_maybe_sync


def _engine(*routes):
    """A Citry instance serving the given routes under ``ext/probe/``."""

    class Probe(Extension):
        name = "probe"
        urls = list(routes)

    return Citry(extensions=[Probe])


# Handlers shared by the per-adapter suites, so each adapter proves the same
# contract.


def _echo(request):
    """Read the JSON body and send it back, along with the content type seen."""
    payload = json.loads(request.body.decode())
    return RouteResponse(
        content=json.dumps({"echo": payload, "content_type": request.content_type}),
        content_type="application/json",
    )


def _query(request):
    return RouteResponse(
        content=json.dumps({key: list(values) for key, values in request.query.items()}),
        content_type="application/json",
    )


def _with_headers(_request):
    return RouteResponse(content="ok", headers=(("X-Citry-Probe", "42"), ("Cache-Control", "no-store")))


def _with_repeated_headers(_request):
    """Two Set-Cookie lines: the canonical header a response sends repeatedly."""
    return RouteResponse(content="ok", headers=(("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")))


class TestRouteHeaders:
    def test_lookup_ignores_case(self):
        headers = RouteHeaders([("Content-Type", "text/html"), ("X-Thing", "1")])
        assert headers["content-type"] == "text/html"
        assert headers["CONTENT-TYPE"] == "text/html"
        assert headers.get("x-thing") == "1"
        assert "X-THING" in headers
        assert headers.get("missing") is None

    def test_repeated_headers_join_with_commas(self):
        headers = RouteHeaders([("Accept", "text/html"), ("accept", "application/json")])
        assert headers["accept"] == "text/html, application/json"

    def test_iterates_lowercased_names(self):
        headers = RouteHeaders([("X-B", "2"), ("X-A", "1")])
        assert list(headers) == ["x-b", "x-a"]
        assert len(headers) == 2
        assert dict(headers.items()) == {"x-b": "2", "x-a": "1"}


class TestRouteRequest:
    def test_defaults_describe_an_empty_get(self):
        request = RouteRequest()
        assert request.method == "GET"
        assert request.path == ""
        assert dict(request.query) == {}
        assert len(request.headers) == 0
        assert request.body == b""
        assert request.content_type == ""
        assert request.native is None

    def test_is_frozen(self):
        with pytest.raises(AttributeError):
            RouteRequest().method = "POST"


class TestCallMaybeSync:
    def test_awaits_async_functions(self):
        async def double(value, *, offset=0):
            return value * 2 + offset

        assert asyncio.run(call_maybe_sync(double, 3, offset=1)) == 7

    def test_runs_sync_functions_in_a_worker_thread(self):
        def which_thread(value, *, offset=0):
            return (threading.get_ident(), value * 2 + offset)

        thread_id, result = asyncio.run(call_maybe_sync(which_thread, 3, offset=1))
        assert result == 7
        assert thread_id != threading.get_ident()


class TestAsgiAdapter:
    """The neutral request under FastAPI/Starlette, through the mounted ASGI app."""

    @pytest.fixture
    def client_factory(self):
        fastapi = pytest.importorskip("fastapi", reason="the web-integration tests need fastapi + httpx")
        pytest.importorskip("httpx", reason="Starlette's TestClient needs httpx")
        from fastapi.testclient import TestClient

        from citry.contrib.fastapi import mount

        def build(engine):
            app = fastapi.FastAPI()
            mount(app, engine)
            return TestClient(app)

        return build

    def test_post_handler_reads_and_echoes_a_json_body(self, client_factory):
        client = client_factory(_engine(URLRoute("echo", handler=_echo, methods=("POST",))))
        response = client.post("/citry/ext/probe/echo", json={"n": 1, "s": "x"})
        assert response.status_code == 200
        assert response.json() == {"echo": {"n": 1, "s": "x"}, "content_type": "application/json"}

    def test_response_headers_reach_the_client(self, client_factory):
        client = client_factory(_engine(URLRoute("headers", handler=_with_headers)))
        response = client.get("/citry/ext/probe/headers")
        assert response.status_code == 200
        assert response.headers["x-citry-probe"] == "42"
        assert response.headers["cache-control"] == "no-store"

    def test_repeated_response_headers_all_reach_the_client(self, client_factory):
        client = client_factory(_engine(URLRoute("cookies", handler=_with_repeated_headers)))
        response = client.get("/citry/ext/probe/cookies")
        assert response.status_code == 200
        assert response.headers.get_list("set-cookie") == ["a=1", "b=2"]

    def test_repeated_query_keys_survive(self, client_factory):
        client = client_factory(_engine(URLRoute("query", handler=_query)))
        response = client.get("/citry/ext/probe/query?a=1&a=2&b=3")
        assert response.json() == {"a": ["1", "2"], "b": ["3"]}

    def test_native_is_the_asgi_scope(self, client_factory):
        captured = {}

        def capture(request):
            captured["request"] = request
            return RouteResponse(content="ok")

        client = client_factory(_engine(URLRoute("capture", handler=capture)))
        client.get("/citry/ext/probe/capture", headers={"X-Probe-In": "yes"})
        request = captured["request"]
        assert request.native["type"] == "http"
        assert request.native["method"] == "GET"
        assert request.method == "GET"
        assert request.path == "/citry/ext/probe/capture"
        # Header lookup ignores case, whatever casing the client sent.
        assert request.headers["x-probe-in"] == "yes"
        assert request.headers["X-PROBE-IN"] == "yes"

    def test_async_handler_is_awaited(self, client_factory):
        async def async_handler(_request):
            await asyncio.sleep(0)
            return RouteResponse(content="from-async")

        client = client_factory(_engine(URLRoute("async", handler=async_handler)))
        response = client.get("/citry/ext/probe/async")
        assert response.status_code == 200
        assert response.text == "from-async"


class TestAsgiSyncOffload:
    """Sync handlers run in a worker thread, so they cannot block the event loop."""

    def test_sync_handler_does_not_block_the_loop(self):
        from citry.contrib.asgi import asgi_app

        finished = []

        def slow(_request):
            time.sleep(0.5)
            finished.append("slow")
            return RouteResponse(content="slow")

        def fast(_request):
            finished.append("fast")
            return RouteResponse(content="fast")

        engine = _engine(URLRoute("slow", handler=slow), URLRoute("fast", handler=fast))
        app = asgi_app(engine)

        async def hit(path):
            messages = []

            async def receive():
                return {"type": "http.request"}

            async def send(message):
                messages.append(message)

            scope = {"type": "http", "method": "GET", "path": path, "headers": [], "query_string": b""}
            await app(scope, receive, send)
            return b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")

        async def race():
            slow_task = asyncio.create_task(hit("/ext/probe/slow"))
            await asyncio.sleep(0.1)  # give the slow handler time to enter its sleep
            fast_body = await hit("/ext/probe/fast")
            slow_body = await slow_task
            return fast_body, slow_body

        fast_body, slow_body = asyncio.run(race())
        assert fast_body == b"fast"
        assert slow_body == b"slow"
        # The fast request completed while the slow handler was still sleeping:
        # the sync handler ran off the loop instead of blocking it.
        assert finished == ["fast", "slow"]


class TestAsgiBodyStream:
    """Raw ASGI drives of the body-reading paths a TestClient cannot produce."""

    def _run(self, engine, scope, receive_messages):
        """Drive the ASGI app with scripted ``receive()`` messages; return what it sent."""
        from citry.contrib.asgi import asgi_app

        app = asgi_app(engine)
        pending = list(receive_messages)
        sent = []

        async def receive():
            return pending.pop(0)

        async def send(message):
            sent.append(message)

        asyncio.run(app(scope, receive, send))
        return sent

    def test_chunked_body_is_joined(self):
        captured = {}

        def capture(request):
            captured["body"] = request.body
            return RouteResponse(content="ok")

        engine = _engine(URLRoute("echo", handler=capture, methods=("POST",)))
        scope = {"type": "http", "method": "POST", "path": "/ext/probe/echo", "headers": [], "query_string": b""}
        sent = self._run(
            engine,
            scope,
            [
                {"type": "http.request", "body": b"first,", "more_body": True},
                {"type": "http.request", "body": b" second"},
            ],
        )
        assert captured["body"] == b"first, second"
        assert sent[0]["status"] == 200

    def test_get_request_never_drains_receive(self):
        # Locks the bodyless-method gate: some servers deliver only
        # http.disconnect for GET, so draining receive() could hang.
        from citry.contrib.asgi import asgi_app

        engine = _engine(URLRoute("probe", handler=lambda _request: RouteResponse(content="ok"), methods=("GET",)))
        scope = {"type": "http", "method": "GET", "path": "/ext/probe/probe", "headers": [], "query_string": b""}
        sent = []

        async def receive():
            raise AssertionError("receive() must not be called for a GET request")

        async def send(message):
            sent.append(message)

        asyncio.run(asgi_app(engine)(scope, receive, send))
        assert sent[0]["status"] == 200

    def test_disconnect_mid_body_aborts_without_a_response(self):
        calls = []

        def handler(request):
            calls.append(request)
            return RouteResponse(content="never")

        engine = _engine(URLRoute("echo", handler=handler, methods=("POST",)))
        scope = {"type": "http", "method": "POST", "path": "/ext/probe/echo", "headers": [], "query_string": b""}
        sent = self._run(engine, scope, [{"type": "http.disconnect"}])
        # The client is gone, so the handler never runs and nothing is sent.
        assert calls == []
        assert sent == []


class TestWsgiAdapter:
    """The neutral request under plain WSGI, driven with a hand-built environ."""

    def _call(self, engine, environ):
        from citry.contrib.wsgi import wsgi_app

        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        body = b"".join(wsgi_app(engine)(environ, start_response))
        return captured["status"], captured["headers"], body

    def test_post_handler_reads_and_echoes_a_json_body(self):
        engine = _engine(URLRoute("echo", handler=_echo, methods=("POST",)))
        payload = json.dumps({"n": 1, "s": "x"}).encode()
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/ext/probe/echo",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(payload)),
            "wsgi.input": io.BytesIO(payload),
        }
        status, _headers, body = self._call(engine, environ)
        assert status == "200 OK"
        assert json.loads(body) == {"echo": {"n": 1, "s": "x"}, "content_type": "application/json"}

    def test_response_headers_reach_the_client(self):
        engine = _engine(URLRoute("headers", handler=_with_headers))
        _status, headers, _body = self._call(engine, {"REQUEST_METHOD": "GET", "PATH_INFO": "/ext/probe/headers"})
        assert ("X-Citry-Probe", "42") in headers
        assert ("Cache-Control", "no-store") in headers

    def test_repeated_response_headers_all_reach_the_client(self):
        engine = _engine(URLRoute("cookies", handler=_with_repeated_headers))
        _status, headers, _body = self._call(engine, {"REQUEST_METHOD": "GET", "PATH_INFO": "/ext/probe/cookies"})
        assert [pair for pair in headers if pair[0] == "Set-Cookie"] == [("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")]

    def test_invalid_content_length_means_no_body(self):
        captured = {}

        def capture(request):
            captured["request"] = request
            return RouteResponse(content="ok")

        engine = _engine(URLRoute("capture", handler=capture, methods=("POST",)))
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/ext/probe/capture",
            "CONTENT_LENGTH": "abc",
            "wsgi.input": io.BytesIO(b"ignored"),
        }
        status, _headers, _body = self._call(engine, environ)
        assert status == "200 OK"
        assert captured["request"].body == b""

    def test_repeated_query_keys_survive(self):
        engine = _engine(URLRoute("query", handler=_query))
        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/ext/probe/query", "QUERY_STRING": "a=1&a=2&b=3"}
        _status, _headers, body = self._call(engine, environ)
        assert json.loads(body) == {"a": ["1", "2"], "b": ["3"]}

    def test_native_is_the_wsgi_environ(self):
        captured = {}

        def capture(request):
            captured["request"] = request
            return RouteResponse(content="ok")

        engine = _engine(URLRoute("capture", handler=capture))
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/ext/probe/capture",
            "SCRIPT_NAME": "/citry",
            "HTTP_X_PROBE_IN": "yes",
        }
        self._call(engine, environ)
        request = captured["request"]
        assert request.native is environ
        assert request.method == "GET"
        # SCRIPT_NAME (the mount prefix) is part of the full request path.
        assert request.path == "/citry/ext/probe/capture"
        assert request.headers["x-probe-in"] == "yes"
        assert request.headers["X-PROBE-IN"] == "yes"
        assert request.body == b""

    def test_async_handler_is_rejected_with_the_deployment_fix(self):
        async def async_handler(_request):
            return RouteResponse(content="never")

        engine = _engine(URLRoute("async", handler=async_handler))
        with pytest.raises(TypeError) as excinfo:
            self._call(engine, {"REQUEST_METHOD": "GET", "PATH_INFO": "/ext/probe/async"})
        message = str(excinfo.value)
        assert "'async def' handler" in message
        assert "WSGI adapter cannot run" in message
        assert "citry.contrib.asgi.asgi_app" in message


class TestDjangoAdapter:
    """The neutral request under Django, through the test client."""

    @pytest.fixture(autouse=True)
    def _django(self):
        django = pytest.importorskip("django", reason="the Django adapter tests need django")
        from django.conf import settings

        if not settings.configured:
            settings.configure(ALLOWED_HOSTS=["*"])
            django.setup()
        return django

    @contextmanager
    def _serving(self, engine):
        """A Django test client whose urlconf mounts the engine's routes at /citry/."""
        import types

        from django.test import Client
        from django.test.utils import override_settings
        from django.urls import include, path

        from citry.contrib.django import urlpatterns

        urlconf = types.ModuleType("citry_test_urlconf")
        urlconf.urlpatterns = [path("citry/", include(urlpatterns(engine, prefix="/citry")))]
        with override_settings(ROOT_URLCONF=urlconf):
            yield Client()

    def test_post_handler_reads_and_echoes_a_json_body(self):
        engine = _engine(URLRoute("echo", handler=_echo, methods=("POST",)))
        with self._serving(engine) as client:
            response = client.post(
                "/citry/ext/probe/echo", data=json.dumps({"n": 1, "s": "x"}), content_type="application/json"
            )
        assert response.status_code == 200
        assert json.loads(response.content) == {"echo": {"n": 1, "s": "x"}, "content_type": "application/json"}

    def test_response_headers_reach_the_client(self):
        engine = _engine(URLRoute("headers", handler=_with_headers))
        with self._serving(engine) as client:
            response = client.get("/citry/ext/probe/headers")
        assert response.status_code == 200
        assert response["X-Citry-Probe"] == "42"
        assert response["Cache-Control"] == "no-store"

    def test_repeated_response_headers_are_rejected(self):
        # Django's response object holds one value per header name, so the
        # adapter refuses a repeated name instead of dropping all but the last.
        engine = _engine(URLRoute("cookies", handler=_with_repeated_headers))
        with self._serving(engine) as client, pytest.raises(ValueError, match="one value per header name") as excinfo:
            client.get("/citry/ext/probe/cookies")
        message = str(excinfo.value)
        assert "repeats the response header 'Set-Cookie'" in message
        assert "ASGI or WSGI adapter" in message

    def test_repeated_query_keys_survive(self):
        engine = _engine(URLRoute("query", handler=_query))
        with self._serving(engine) as client:
            response = client.get("/citry/ext/probe/query?a=1&a=2&b=3")
        assert json.loads(response.content) == {"a": ["1", "2"], "b": ["3"]}

    def test_native_is_the_django_request(self):
        from django.http import HttpRequest

        captured = {}

        def capture(request):
            captured["request"] = request
            return RouteResponse(content="ok")

        engine = _engine(URLRoute("capture", handler=capture))
        with self._serving(engine) as client:
            client.get("/citry/ext/probe/capture", headers={"X-Probe-In": "yes"})
        request = captured["request"]
        assert isinstance(request.native, HttpRequest)
        assert request.method == "GET"
        assert request.path == "/citry/ext/probe/capture"
        assert request.headers["x-probe-in"] == "yes"
        assert request.headers["X-PROBE-IN"] == "yes"

    def test_async_handler_is_rejected_at_urlconf_build(self):
        from citry.contrib.django import urlpatterns

        async def async_handler(_request):
            return RouteResponse(content="never")

        engine = _engine(URLRoute("async", handler=async_handler))
        with pytest.raises(TypeError) as excinfo:
            urlpatterns(engine)
        message = str(excinfo.value)
        assert "'async def' handler" in message
        assert "Django view adapter cannot run" in message
        assert "citry.contrib.asgi.asgi_app" in message
