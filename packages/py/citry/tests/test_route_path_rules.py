"""
Every host adapter routes the same request paths and methods.

An app often guards Citry's routes with a rule in its host framework, such as
middleware that checks `path.startswith("/citry/ext/events")`. That rule only
works when Citry routes exactly the paths and methods the host sees. These
tests send the spellings that must not reach a handler (an extra `/` after the
prefix, a trailing newline, HEAD on a POST-only route) through each adapter,
and check that the handler never runs while the ordinary request still does.
"""

from __future__ import annotations

import asyncio
import io
import json
import types
from typing import Any

import pytest

from citry import Citry, Component, Extension, RouteResponse, URLRoute
from citry.contrib.asgi import asgi_app
from citry.contrib.wsgi import wsgi_app
from citry.util.routing import match_path_below_mount, match_route, route_allows_method

# Request paths below the `/citry` prefix that must answer 404. The decoded
# `%2F` and `%0a` spellings are what servers put in the path they hand on.
# A server passes a request line without its leading `/` through unchanged,
# and under an ASGI `root_path` of `/citry` the same remainder comes from
# `/citryext/probe/hit`.
_REJECTED_PATHS = (
    "ext/probe/hit",
    "//ext/probe/hit",
    "///ext/probe/hit",
    "/ext/probe/hit\n",
    "/ext/probe//hit",
)


def _counting_engine() -> tuple[Citry, list[str]]:
    """A Citry instance with a POST-only route and a GET route that record each call."""
    calls: list[str] = []

    def hit(request: Any) -> RouteResponse:
        calls.append(f"hit {request.method}")
        return RouteResponse(content="hit")

    def page(request: Any) -> RouteResponse:
        calls.append(f"page {request.method}")
        return RouteResponse(content="page")

    class Probe(Extension):
        name = "probe"
        urls = [
            URLRoute("hit", handler=hit, methods=("POST",)),
            URLRoute("page", handler=page),
        ]

    return Citry(extensions=[Probe]), calls


class TestSharedRule:
    """The functions every adapter calls."""

    def test_only_one_leading_slash_is_removed(self):
        routes = [URLRoute("", handler=lambda _r: RouteResponse()), URLRoute("call", handler=lambda _r: None)]
        matched = match_path_below_mount(routes, "/call")
        assert matched is not None
        assert matched.full_path == "call"
        assert match_path_below_mount(routes, "//call") is None
        # A remainder without its leading `/` is a path the host saw differently.
        assert match_path_below_mount(routes, "call") is None
        # The mount point itself, with or without its trailing `/`, is the empty route.
        for path in ("", "/"):
            matched = match_path_below_mount(routes, path)
            assert matched is not None
            assert matched.full_path == ""

    def test_the_whole_path_must_match(self):
        routes = [URLRoute("call", handler=lambda _r: RouteResponse()), URLRoute("e/{name}", handler=lambda _r: None)]
        assert match_route(routes, "call") is not None
        # A pattern ending in `$` also matches before a final newline; the
        # route must not.
        assert match_route(routes, "call\n") is None
        assert match_route(routes, "/call") is None
        # A newline inside a parameter stays in its value, where the built-in
        # handlers find no component or event by that name.
        matched = match_route(routes, "e/x\n")
        assert matched is not None
        assert matched.params == {"name": "x\n"}

    @pytest.mark.parametrize(
        ("methods", "method", "allowed"),
        [
            (("GET",), "GET", True),
            (("GET",), "HEAD", True),
            (("POST",), "POST", True),
            (("POST",), "HEAD", False),
            (("POST", "PUT"), "HEAD", False),
            (("HEAD",), "HEAD", True),
            (("GET",), "POST", False),
        ],
    )
    def test_head_is_allowed_only_where_get_is(self, methods, method, allowed):
        route = URLRoute("x", handler=lambda _r: RouteResponse(), methods=methods)
        assert route_allows_method(route, method) is allowed


def _asgi_status(app: Any, method: str, path: str, root_path: str, *, path_keeps_prefix: bool = True) -> int:
    """Send one bodyless request to an ASGI app and return the response status."""
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "method": method,
        # Starlette keeps the prefix in `path` and other servers drop it; the
        # adapter must route both shapes the same way.
        "path": root_path + path if path_keeps_prefix else path,
        "root_path": root_path,
        "query_string": b"",
        "headers": [],
    }
    asyncio.run(app(scope, receive, send))
    return next(message["status"] for message in sent if message["type"] == "http.response.start")


class TestAsgiAdapter:
    @pytest.mark.parametrize("path_keeps_prefix", [True, False])
    @pytest.mark.parametrize("root_path", ["/citry", ""])
    @pytest.mark.parametrize("path", _REJECTED_PATHS)
    def test_other_spellings_answer_404(self, root_path, path, path_keeps_prefix):
        engine, calls = _counting_engine()
        app = asgi_app(engine)
        assert _asgi_status(app, "POST", path, root_path, path_keeps_prefix=path_keeps_prefix) == 404
        assert calls == []

    @pytest.mark.parametrize("path_keeps_prefix", [True, False])
    @pytest.mark.parametrize("root_path", ["/citry", ""])
    def test_ordinary_paths_still_route(self, root_path, path_keeps_prefix):
        engine, calls = _counting_engine()
        app = asgi_app(engine)
        shape = {"path_keeps_prefix": path_keeps_prefix}
        assert _asgi_status(app, "POST", "/ext/probe/hit", root_path, **shape) == 200
        assert _asgi_status(app, "HEAD", "/ext/probe/page", root_path, **shape) == 200
        assert calls == ["hit POST", "page HEAD"]

    def test_head_on_a_post_only_route_answers_405(self):
        engine, calls = _counting_engine()
        assert _asgi_status(asgi_app(engine), "HEAD", "/ext/probe/hit", "/citry") == 405
        assert calls == []


def _wsgi_status(app: Any, method: str, path_info: str, body: bytes = b"", **extra: str) -> str:
    """Send one request to a WSGI app and return its status line."""
    captured: list[str] = []
    environ = {
        "REQUEST_METHOD": method,
        "SCRIPT_NAME": "/citry",
        "PATH_INFO": path_info,
        "QUERY_STRING": "",
        "CONTENT_LENGTH": str(len(body)),
        "HTTP_HOST": "testserver",
        "wsgi.input": io.BytesIO(body),
        **extra,
    }
    b"".join(app(environ, lambda status, _headers, *_exc: captured.append(status)))
    return captured[0]


class TestWsgiAdapter:
    @pytest.mark.parametrize("path", _REJECTED_PATHS)
    def test_other_spellings_answer_404(self, path):
        engine, calls = _counting_engine()
        assert _wsgi_status(wsgi_app(engine), "POST", path) == "404 Not Found"
        assert calls == []

    def test_ordinary_paths_still_route(self):
        engine, calls = _counting_engine()
        app = wsgi_app(engine)
        assert _wsgi_status(app, "POST", "/ext/probe/hit") == "200 OK"
        assert _wsgi_status(app, "HEAD", "/ext/probe/page") == "200 OK"
        assert calls == ["hit POST", "page HEAD"]

    def test_head_on_a_post_only_route_answers_405(self):
        engine, calls = _counting_engine()
        assert _wsgi_status(wsgi_app(engine), "HEAD", "/ext/probe/hit", b'{"a": 1}') == "405 Method Not Allowed"
        assert calls == []


class TestFlaskMount:
    @pytest.fixture
    def client_and_calls(self):
        flask = pytest.importorskip("flask", reason="the Flask mount tests need flask")
        from citry.contrib.flask import mount

        engine, calls = _counting_engine()
        app = flask.Flask(__name__)
        mount(app, engine)
        return app.test_client(), calls

    @pytest.mark.parametrize("path", ["/citry//ext/probe/hit", "/citry/%2Fext/probe/hit", "/citry/ext/probe/hit%0a"])
    def test_other_spellings_answer_404(self, client_and_calls, path):
        client, calls = client_and_calls
        assert client.post(path).status_code == 404
        assert calls == []

    def test_methods_follow_the_shared_rule(self, client_and_calls):
        client, calls = client_and_calls
        assert client.head("/citry/ext/probe/hit", data=b'{"a": 1}').status_code == 405
        assert client.post("/citry/ext/probe/hit").status_code == 200
        assert client.head("/citry/ext/probe/page").status_code == 200
        assert calls == ["hit POST", "page HEAD"]


class TestFastApiMount:
    @pytest.fixture
    def client_and_calls(self):
        fastapi = pytest.importorskip("fastapi", reason="the FastAPI mount tests need fastapi")
        pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")
        from fastapi.testclient import TestClient

        from citry.contrib.fastapi import mount

        engine, calls = _counting_engine()
        app = fastapi.FastAPI()
        mount(app, engine)
        return TestClient(app), calls

    @pytest.mark.parametrize("path", ["/citry//ext/probe/hit", "/citry/%2Fext/probe/hit", "/citry/ext/probe/hit%0a"])
    def test_other_spellings_answer_404(self, client_and_calls, path):
        client, calls = client_and_calls
        assert client.post(path).status_code == 404
        assert calls == []

    def test_methods_follow_the_shared_rule(self, client_and_calls):
        client, calls = client_and_calls
        assert client.request("HEAD", "/citry/ext/probe/hit").status_code == 405
        assert client.post("/citry/ext/probe/hit").status_code == 200
        assert client.head("/citry/ext/probe/page").status_code == 200
        assert calls == ["hit POST", "page HEAD"]


class TestDjangoPatterns:
    @pytest.fixture
    def client_and_calls(self):
        django = pytest.importorskip("django", reason="the Django adapter tests need django")
        from django.conf import settings

        if not settings.configured:
            settings.configure(ALLOWED_HOSTS=["*"])
            django.setup()
        from django.test import Client
        from django.test.utils import override_settings
        from django.urls import include, path

        from citry.contrib.django import urlpatterns

        engine, calls = _counting_engine()
        urlconf = types.ModuleType("citry_route_path_rules_urlconf")
        urlconf.urlpatterns = [path("citry/", include(urlpatterns(engine, prefix="/citry")))]
        # CsrfViewMiddleware runs, as in a real project, so a test can show
        # which requests its token check lets through.
        middleware = ["django.middleware.csrf.CsrfViewMiddleware"]
        with override_settings(ROOT_URLCONF=urlconf, MIDDLEWARE=middleware):
            yield Client(), calls

    def test_other_spellings_answer_404(self, client_and_calls):
        client, calls = client_and_calls
        for path in ("/citry//ext/probe/hit", "/citry/ext/probe/hit%0a"):
            assert client.post(path).status_code == 404
        assert calls == []

    def test_head_does_not_skip_the_csrf_check(self, client_and_calls):
        from django.test import Client

        _client, calls = client_and_calls
        client = Client(enforce_csrf_checks=True)
        # The token check refuses a POST without a token...
        assert client.post("/citry/ext/probe/hit").status_code == 403
        # ...but skips HEAD, so only the method rule keeps HEAD from the handler.
        assert client.generic("HEAD", "/citry/ext/probe/hit", b'{"a": 1}', "application/json").status_code == 405
        assert calls == []

    def test_methods_follow_the_shared_rule(self, client_and_calls):
        client, calls = client_and_calls
        assert client.generic("HEAD", "/citry/ext/probe/hit", b'{"a": 1}', "application/json").status_code == 405
        assert client.post("/citry/ext/probe/hit").status_code == 200
        assert client.head("/citry/ext/probe/page").status_code == 200
        assert calls == ["hit POST", "page HEAD"]


class TestEventsBatchRoute:
    """The built-in batch route names its target in the body, so it reaches any handler."""

    @pytest.fixture
    def engine_and_calls(self):
        engine = Citry(secret="s" * 40)
        calls: list[str] = []

        class Target(Component):
            citry = engine
            template = """
                <p>t</p>
            """

            class Events:
                def bump(self) -> None:
                    calls.append("bump")

        engine.set_mounted_prefix("/citry")
        body = json.dumps(
            {
                "protocol": "citry-events/1",
                "requestId": "r",
                "calls": [{"componentClassId": Target.class_id, "handlerName": "bump", "args": {}}],
            }
        ).encode()
        return engine, calls, body

    def _post(self, app: Any, method: str, path_info: str, body: bytes) -> str:
        return _wsgi_status(app, method, path_info, body, CONTENT_TYPE="application/json", HTTP_X_CITRY_EVENTS="1")

    def test_only_the_ordinary_post_runs_the_handler(self, engine_and_calls):
        engine, calls, body = engine_and_calls
        app = wsgi_app(engine)
        assert self._post(app, "HEAD", "/ext/events/call", body) == "405 Method Not Allowed"
        assert self._post(app, "POST", "//ext/events/call", body) == "404 Not Found"
        assert self._post(app, "POST", "/ext/events/call\n", body) == "404 Not Found"
        assert calls == []
        # The check above means something only if the ordinary request runs the handler.
        assert self._post(app, "POST", "/ext/events/call", body) == "200 OK"
        assert calls == ["bump"]
