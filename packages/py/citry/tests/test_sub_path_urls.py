"""
Tests that the URLs Citry writes into a page start with the sub-path the app is served below.

Most tests serve a small app below ``/shop`` in one of the ways a real
deployment does it, render a page with an interactive component, and ask
the same server for every URL the page names: the runtime, the compiled
definitions and stylesheets, and an event call. A URL without ``/shop``
would make the browser ask the site root, which does not run the app.
"""

# ruff: noqa: ANN

import dataclasses
import json
import re
import types
from typing import Any

import pytest

from citry import Citry, Component
from citry._protocol.events import build_call, build_call_envelope
from citry._sub_path import normalize_sub_path, recording_sub_path, request_sub_path

_SECRET = "s" * 40


@dataclasses.dataclass
class _Bump:
    n: int = 0


def _page_class(engine):
    """A page holding a counter whose button sends an event, so the page names every kind of Citry URL."""

    class Counter(Component):
        citry = engine

        class Kwargs:
            n: int

        class State(Kwargs):
            pass

        class Events:
            def bump(self, data: _Bump, state: Any) -> Any:
                return Counter(n=state.n + 1)

        template = """
<button @c-click="bump">{{ n }}</button>
"""
        js = """
$component({});
"""
        css = """
.counter {
  color: red;
}
"""

    class Page(Component):
        citry = engine
        template = """
<html><head></head><body><c-Counter c-n="1" /></body></html>
"""

    return Page


def _urls_in(text):
    """Return every root-relative URL a page or event response names for the browser."""
    found = set(re.findall(r'(?:src|href)="(/[^"]*)"', text))
    found |= set(re.findall(r'"(?:endpoint|eventBaseUrl|url)":\s*"(/[^"]*)"', text))
    return sorted(found)


def _fetchable(urls):
    # The event endpoint takes POST only, and the event base URL is a prefix
    # for one URL per handler, so neither is fetched with GET.
    return [url for url in urls if not url.endswith(("/ext/events/call", "/ext/events/e/"))]


def _send_bump(post, html):
    """Send the counter's event the way the browser does, and return the response body."""
    document = html.split('data-citry-vue-document="', 1)[1].split(">", 1)[1].split("</script>", 1)[0]
    configuration = json.loads(document)
    manifest = configuration["manifest"]
    owner = next(item for item in manifest["occurrences"] if "eventContext" in item)
    context = owner["eventContext"]
    call = build_call(
        context["componentClassId"],
        "bump",
        {"n": 0},
        caller_render_id=context["serverRenderId"],
        state_token=context["stateToken"],
        send_sequence=1,
    )
    envelope = build_call_envelope(
        "c1", [call], capabilities={"actions": ["render"], "swaps": ["morph"], "renderers": ["vue-prepared/1"]}
    )
    headers = {
        "content-type": "application/citry-events+json",
        "x-citry-events": "1",
        "x-citry-vue-app": manifest["appId"],
        "x-citry-vue-occurrence": owner["id"],
        "x-citry-vue-revision": "0",
    }
    status, body = post(configuration["endpoint"], json.dumps(envelope), headers)
    assert status == 200, body
    return body


def _assert_served_below(prefix, html, get, post):
    """Check that every URL the page and its event response name starts with ``prefix`` and is served."""
    urls = _urls_in(html)
    assert urls, "the page names no Citry URLs"
    response_urls = _urls_in(_send_bump(post, html))
    for url in urls + response_urls:
        assert url.startswith(f"{prefix}/citry/"), url
    fetched = _fetchable(urls + response_urls)
    assert {url: get(url) for url in fetched} == dict.fromkeys(fetched, 200)


class TestFastAPI:
    @pytest.fixture(autouse=True)
    def _needs_fastapi(self):
        pytest.importorskip("fastapi")
        pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")

    def _app(self, engine, *, middleware=None):
        import fastapi
        from fastapi.responses import HTMLResponse, StreamingResponse

        from citry.contrib.fastapi import mount

        page = _page_class(engine)
        app = fastapi.FastAPI()
        if middleware is not None:
            app.add_middleware(middleware)

        @app.get("/sync", response_class=HTMLResponse)
        def sync_view():
            return HTMLResponse(page().render().serialize())

        @app.get("/async", response_class=HTMLResponse)
        async def async_view():
            return HTMLResponse(page().render().serialize())

        @app.get("/stream")
        def stream_view():
            def body():
                yield page().render().serialize()

            return StreamingResponse(body(), media_type="text/html")

        mount(app, engine)
        return app

    def _check(self, client, prefix, view):
        def post(url, content, headers):
            response = client.post(url, content=content, headers=headers)
            return response.status_code, response.text

        html = client.get(f"{prefix}/{view}").text
        _assert_served_below(prefix, html, lambda url: client.get(url).status_code, post)

    @pytest.mark.parametrize("view", ["sync", "async", "stream"])
    @pytest.mark.parametrize("setup", ["setting", "server"])
    def test_a_page_below_a_sub_path_reaches_everything_it_names(self, setup, view):
        from fastapi.testclient import TestClient

        app = self._app(Citry(secret=_SECRET))
        if setup == "setting":
            # FastAPI(root_path=...) states the sub-path in the app.
            app.root_path = "/shop"
            client = TestClient(app)
        else:
            # `uvicorn --root-path /shop`: only the request carries it.
            client = TestClient(app, root_path="/shop")
        with client:
            self._check(client, "/shop", view)

    def test_a_page_at_the_site_root_keeps_its_urls(self):
        from fastapi.testclient import TestClient

        with TestClient(self._app(Citry(secret=_SECRET))) as client:
            self._check(client, "", "sync")

    def test_a_middleware_that_sets_root_path_is_seen_whatever_its_order(self):
        from fastapi.testclient import TestClient

        class FromProxyHeader:
            # Sets root_path from a proxy header, as some deployments do.
            def __init__(self, app):
                self.app = app

            async def __call__(self, scope, receive, send):
                if scope["type"] == "http":
                    headers = dict(scope["headers"])
                    scope = {**scope, "root_path": headers.get(b"x-forwarded-prefix", b"").decode()}
                await self.app(scope, receive, send)

        # Added before mount(), so it would run inside an outermost recorder.
        app = self._app(Citry(secret=_SECRET), middleware=FromProxyHeader)
        with TestClient(app, headers={"x-forwarded-prefix": "/shop"}) as client:
            self._check(client, "/shop", "sync")

    def test_a_plain_starlette_app_below_a_sub_path(self):
        from starlette.applications import Starlette
        from starlette.responses import HTMLResponse
        from starlette.routing import Route
        from starlette.testclient import TestClient

        from citry.contrib.fastapi import mount

        engine = Citry(secret=_SECRET)
        page = _page_class(engine)

        async def home(_request):
            return HTMLResponse(page().render().serialize())

        app = Starlette(routes=[Route("/", home)])
        mount(app, engine)
        with TestClient(app, root_path="/shop") as client:
            self._check(client, "/shop", "")
        # Starlette has no root_path setting, so outside a request the URLs
        # start at the site root.
        assert engine.build_url("citry.js") == "/citry/citry.js"

    def test_outside_a_request_the_urls_use_the_apps_root_path(self):
        engine = Citry(secret=_SECRET)
        app = self._app(engine)
        app.root_path = "/shop/"
        assert engine.build_url("citry.js") == "/shop/citry/citry.js"

    def test_mounting_twice_adds_one_middleware(self):
        from citry.contrib.fastapi import _RecordRootPath, mount

        app = self._app(Citry(secret=_SECRET))
        mount(app, Citry(secret=_SECRET), prefix="/other")
        assert [entry.cls for entry in app.user_middleware].count(_RecordRootPath) == 1

    def test_mounting_after_the_app_started_still_mounts(self):
        import fastapi
        from fastapi.testclient import TestClient

        from citry.contrib.fastapi import mount

        engine = Citry(secret=_SECRET)
        app = fastapi.FastAPI(root_path="/shop")
        with TestClient(app) as client:
            client.get("/missing")
            # Starlette accepts no middleware now; the URLs use root_path.
            mount(app, engine)
            assert client.get("/shop/citry/citry.js").status_code == 200
        assert engine.build_url("citry.js") == "/shop/citry/citry.js"


class TestFlask:
    @pytest.fixture(autouse=True)
    def _needs_flask(self):
        pytest.importorskip("flask")

    def _app(self, engine):
        import flask

        from citry.contrib.flask import mount

        page = _page_class(engine)
        app = flask.Flask("sub_path_flask_app")
        app.add_url_rule("/", "home", lambda: page().render().serialize())

        def streamed():
            def body():
                yield page().render().serialize()

            return flask.Response(flask.stream_with_context(body()), mimetype="text/html")

        app.add_url_rule("/stream", "stream", streamed)
        mount(app, engine)
        engine.initialize()
        return app

    def _check(self, client, prefix, path, headers=None):
        def post(url, content, post_headers):
            response = client.post(url, data=content, headers={**(headers or {}), **post_headers})
            return response.status_code, response.get_data(as_text=True)

        html = client.get(path, headers=headers).get_data(as_text=True)
        _assert_served_below(prefix, html, lambda url: client.get(url, headers=headers).status_code, post)

    @pytest.mark.parametrize("path", ["/shop/", "/shop/stream"])
    def test_a_page_below_a_server_sub_path_reaches_everything_it_names(self, path):
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        from werkzeug.test import Client
        from werkzeug.wrappers import Response

        app = self._app(Citry(secret=_SECRET))
        # The server mounts the app at /shop, as gunicorn's SCRIPT_NAME or a
        # WSGI dispatcher does. The site root does not run the app.
        site = DispatcherMiddleware(lambda environ, start: Response("site", 404)(environ, start), {"/shop": app})
        self._check(Client(site), "/shop", path)

    def test_a_page_below_a_proxy_fix_prefix_reaches_everything_it_names(self):
        from werkzeug.middleware.proxy_fix import ProxyFix
        from werkzeug.test import Client

        app = self._app(Citry(secret=_SECRET))
        # The proxy strips /shop and names it in X-Forwarded-Prefix, which
        # ProxyFix, wrapped around the app before mount(), turns into
        # SCRIPT_NAME. The client asks the app for the path without /shop.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
        client = Client(app)
        headers = {"X-Forwarded-Prefix": "/shop"}

        def strip(url):
            return url.removeprefix("/shop")

        def post(url, content, post_headers):
            response = client.post(strip(url), data=content, headers={**headers, **post_headers})
            return response.status_code, response.get_data(as_text=True)

        html = client.get("/", headers=headers).get_data(as_text=True)
        _assert_served_below("/shop", html, lambda url: client.get(strip(url), headers=headers).status_code, post)

    def test_a_page_at_the_site_root_keeps_its_urls(self):
        self._check(self._app(Citry(secret=_SECRET)).test_client(), "", "/")

    def test_outside_a_request_the_urls_use_application_root(self):
        engine = Citry(secret=_SECRET)
        app = self._app(engine)
        app.config["APPLICATION_ROOT"] = "/shop"
        assert engine.build_url("citry.js") == "/shop/citry/citry.js"


class TestDjango:
    @pytest.fixture
    def project(self):
        """Yield the engine and a function that builds a Django WSGI handler, optionally with FORCE_SCRIPT_NAME."""
        django = pytest.importorskip("django")
        from django.conf import settings

        # Settings are process-wide; configure them only when no other test
        # did, and change everything this test needs through override_settings.
        if not settings.configured:
            settings.configure(ALLOWED_HOSTS=["*"])
            django.setup()
        from django.core.handlers.wsgi import WSGIHandler
        from django.http import HttpResponse
        from django.test.utils import override_settings
        from django.urls import clear_url_caches, include, path, set_script_prefix

        from citry.contrib.django import urlpatterns

        engine = Citry(secret=_SECRET)
        page = _page_class(engine)
        urlconf = types.ModuleType("citry_sub_path_urlconf")
        urlconf.urlpatterns = [
            path("", lambda _request: HttpResponse(page().render().serialize())),
            path("citry/", include(urlpatterns(engine, prefix="/citry"))),
        ]
        engine.initialize()
        overrides = override_settings(ROOT_URLCONF=urlconf, ALLOWED_HOSTS=["*"], MIDDLEWARE=[], DEBUG=False)

        def build(force_script_name):
            overrides.enable()
            settings.FORCE_SCRIPT_NAME = force_script_name
            return WSGIHandler()

        try:
            yield engine, build
        finally:
            overrides.disable()
            clear_url_caches()
            set_script_prefix("/")

    @staticmethod
    def _check(client, prefix, path, to_server=lambda url: url):
        def post(url, content, headers):
            response = client.post(to_server(url), data=content, headers=headers)
            return response.status_code, response.get_data(as_text=True)

        html = client.get(path).get_data(as_text=True)
        _assert_served_below(prefix, html, lambda url: client.get(to_server(url)).status_code, post)

    def test_a_page_below_a_server_sub_path_reaches_everything_it_names(self, project):
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        from werkzeug.test import Client
        from werkzeug.wrappers import Response

        _engine, build = project
        # Django's handler takes the sub-path from SCRIPT_NAME, which the
        # dispatcher sets as a server does.
        site = DispatcherMiddleware(
            lambda environ, start: Response("site", 404)(environ, start), {"/shop": build(None)}
        )
        self._check(Client(site), "/shop", "/shop/")

    def test_a_page_below_force_script_name_reaches_everything_it_names(self, project):
        from werkzeug.test import Client

        _engine, build = project
        # A proxy strips /shop and passes the rest; FORCE_SCRIPT_NAME tells
        # Django where it is served. The client asks for the stripped path.
        self._check(Client(build("/shop")), "/shop", "/", to_server=lambda url: url.removeprefix("/shop"))

    def test_a_page_at_the_site_root_keeps_its_urls(self, project):
        from werkzeug.test import Client

        _engine, build = project
        self._check(Client(build(None)), "", "/")


class TestRenderCache:
    def _engine(self):
        engine = Citry(secret=_SECRET)
        engine.set_mounted_prefix("/citry")
        # The reader an integration's mount() registers, here reading only
        # what the request recorded.
        engine._set_sub_path_reader(lambda: request_sub_path() or "")
        return engine

    def _link_class(self, engine, renders):
        class Link(Component):
            citry = engine
            template = """
<p>{{ url }}</p>
"""

            class Cache:
                enabled = True

                def vary(self, kwargs, slots):
                    return "link"

            def template_data(self, kwargs, slots):
                renders.append(1)
                # A URL built while rendering lands in the cached HTML.
                return {"url": self.citry.build_url("ext/thing")}

        return Link

    def test_the_render_cache_keeps_one_entry_per_sub_path(self):
        engine = self._engine()
        renders: list[int] = []
        link = self._link_class(engine, renders)
        engine.initialize()
        with recording_sub_path("/shop"):
            assert ">/shop/citry/ext/thing</p>" in str(link())
        # Rendered at the site root after the entry below /shop was stored.
        assert ">/citry/ext/thing</p>" in str(link())
        # The same sub-path, spelled with a trailing "/", reuses its entry.
        with recording_sub_path("/shop/"):
            assert ">/shop/citry/ext/thing</p>" in str(link())
        assert renders == [1, 1]

    def test_a_key_built_outside_a_request_names_the_sub_path_it_is_given(self):
        from citry.ext.cache import component_cache_key

        engine = self._engine()
        renders: list[int] = []
        link = self._link_class(engine, renders)
        engine.initialize()
        with recording_sub_path("/shop"):
            str(link())
            inside = component_cache_key(link, vary="link")
        # A background job has no request, so it names the sub-path, and its
        # key finds the entry stored during the /shop request.
        assert component_cache_key(link, vary="link", sub_path="/shop") == inside
        assert engine.cache.get(component_cache_key(link, vary="link", sub_path="/shop")) is not None
        assert component_cache_key(link, vary="link") != inside
        engine.cache.delete(component_cache_key(link, vary="link", sub_path="/shop"))
        with recording_sub_path("/shop"):
            str(link())
        assert renders == [1, 1]

    def test_a_key_function_rejects_a_sub_path_that_is_not_a_url_path(self):
        from citry.ext.cache import component_cache_key

        engine = self._engine()
        link = self._link_class(engine, [])
        engine.initialize()
        # Read from a request this would fall back to the site root, but a
        # value passed on purpose would then name the wrong entry silently.
        with pytest.raises(ValueError, match="sub_path must be"):
            component_cache_key(link, vary="link", sub_path="shop")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/shop", "/shop"),
        ("/shop/", "/shop"),
        ("/", ""),
        ("", ""),
        (None, ""),
        # A value that does not start with one "/" could point the page's
        # scripts at another site, so it counts as the site root.
        ("shop", ""),
        ("//evil.example", ""),
        ("/my shop", "/my%20shop"),
        # Already encoded, and characters a path may hold, stay as they are.
        ("/my%20shop", "/my%20shop"),
        ("/@team", "/@team"),
        ("/o'brien", "/o%27brien"),
    ],
)
def test_a_sub_path_is_read_as_a_url_path(value, expected):
    assert normalize_sub_path(value) == expected
