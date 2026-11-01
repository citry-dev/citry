"""
Citry's public JS and CSS routes let any page read them; its request routes do not.

Citry puts ``integrity`` and ``crossorigin="anonymous"`` on the files it serves
itself. A page inside a sandboxed iframe has an opaque origin, so the browser
treats every one of those requests as cross-origin and checks the digest only
when the response carries ``Access-Control-Allow-Origin``. These tests drive
the real WSGI and ASGI adapters, so they prove the header reaches the wire and
stays off the routes that run events or read request data. Every one of those
responses, assets and request routes alike, also carries
``X-Content-Type-Options: nosniff``.

Each public file also tells the browser how long it may keep a copy: a URL
that carries a hash of its content is kept for a year, and a URL whose content
can change (``citry.js``, ``cache/<class_id>.js``) is checked with the server
before each use.
"""

from __future__ import annotations

import asyncio
import io
from typing import Any

import pytest

from citry import Citry, Component
from citry._owned_resource import IMMUTABLE_CACHE_CONTROL, OWNED_ASSET_CROSSORIGIN, _OwnedResource
from citry._vue.capture import render_prepared_direct
from citry._vue.events import default_events_producer
from citry._vue.serialization import _manifest_script_preloads
from citry.contrib.asgi import asgi_app
from citry.contrib.wsgi import wsgi_app
from citry.ext.dependencies.emission import _preloader_script
from citry.ext.dependencies.routes import script_url
from citry.ext.dependencies.scripts import cache_asset
from citry.util.routing import RouteHeaders, RouteRequest, RouteResponse, match_route

CORS = "access-control-allow-origin"
NOSNIFF = "x-content-type-options"


def _app() -> Citry:
    app = Citry(
        secret="asset-cors-test-secret",  # noqa: S106
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    app.set_mounted_prefix("/citry")
    return app


def _wsgi(
    app: Citry, method: str, path: str, body: bytes = b"", request_headers: dict[str, str] | None = None
) -> tuple[str, dict[str, str]]:
    captured: dict[str, Any] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        captured["status"] = status
        captured["headers"] = {name.lower(): value for name, value in headers}

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "SCRIPT_NAME": "",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/json" if body else "",
        "CONTENT_LENGTH": str(len(body)) if body else "",
        "wsgi.input": io.BytesIO(body),
        **{f"HTTP_{name.upper().replace('-', '_')}": value for name, value in (request_headers or {}).items()},
    }
    b"".join(wsgi_app(app)(environ, start_response))
    return captured["status"], captured["headers"]


def _asgi(
    app: Citry, method: str, path: str, body: bytes = b"", request_headers: dict[str, str] | None = None
) -> tuple[int, dict[str, str]]:
    messages: list[dict[str, Any]] = []
    sent = False

    async def receive() -> dict[str, Any]:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "root_path": "",
        "query_string": b"",
        "headers": [
            *([(b"content-type", b"application/json")] if body else []),
            *(
                (name.lower().encode("latin-1"), value.encode("latin-1"))
                for name, value in (request_headers or {}).items()
            ),
        ],
    }
    asyncio.run(asgi_app(app)(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    headers = {name.decode("latin-1").lower(): value.decode("latin-1") for name, value in start["headers"]}
    return start["status"], headers


def _asset_paths(app: Citry) -> list[str]:
    """Return one URL for every public asset route, each resolving to real bytes."""

    class Widget(Component):
        citry = app
        template = '<main :data-ready="true">widget</main>'
        js = """
            console.log("widget");
        """
        css = """
            main { color: teal; }
        """

    payload = default_events_producer(app).prepare_from_render(
        render_prepared_direct(Widget()), citry=app, app_id="app", revision=0
    )
    definition = payload["definitions"][0]["url"]
    stylesheet = payload["styles"][0]["source"]["url"]
    return [
        "/citry.js",
        "/ext/events/runtime.js",
        "/ext/i18n/runtime.js",
        script_url(Widget, "js").removeprefix("/citry"),
        script_url(Widget, "css").removeprefix("/citry"),
        f"/cache/{Widget.class_id}.js",
        definition.removeprefix("/citry"),
        stylesheet.removeprefix("/citry"),
    ]


def test_owned_resource_response_always_allows_any_origin() -> None:
    # Every Citry-owned file goes through this one response builder.
    response = _OwnedResource(url="/x.js", content="x", content_type="text/javascript").response()
    assert response.headers == (("Access-Control-Allow-Origin", "*"),)

    # A route's own headers (such as Cache-Control) are kept beside it.
    with_cache = _OwnedResource(
        url="/x.js", content="x", content_type="text/javascript", headers=(("Cache-Control", "no-store"),)
    ).response()
    assert with_cache.headers == (("Access-Control-Allow-Origin", "*"), ("Cache-Control", "no-store"))


@pytest.mark.parametrize("adapter", ["wsgi", "asgi"])
def test_public_asset_routes_send_a_wildcard_cors_header(adapter: str) -> None:
    app = _app()
    paths = _asset_paths(app)
    for path in paths:
        if adapter == "wsgi":
            status, headers = _wsgi(app, "GET", path)
            assert status == "200 OK", path
        else:
            code, headers = _asgi(app, "GET", path)
            assert code == 200, path
        assert headers.get(CORS) == "*", path
        # The wildcard never pairs with credentials, and the value does not
        # depend on the caller, so neither of these headers belongs here.
        assert "access-control-allow-credentials" not in headers, path
        assert "vary" not in headers, path


@pytest.mark.parametrize("adapter", ["wsgi", "asgi"])
def test_request_routes_do_not_send_a_cors_header(adapter: str) -> None:
    app = _app()

    class Clicker(Component):
        citry = app
        template = "<button>go</button>"

        def on_click(self) -> None:
            return None

    # These routes run events or read the request body; the browser must
    # keep refusing another origin's read of their responses.
    requests = [
        ("POST", "/ext/events/call", b"{}"),
        ("POST", f"/ext/events/e/{Clicker.class_id}/on_click", b"{}"),
        ("POST", "/ext/i18n/messages", b"{}"),
        ("POST", f"/ext/events/e/{Clicker.class_id}", b"{}"),
        # Misses on an asset route and on the adapter itself stay plain too.
        ("GET", f"/ext/events/definitions/{'0' * 64}.js", b""),
        ("GET", "/no-such-route", b""),
    ]
    for method, path, body in requests:
        headers = _wsgi(app, method, path, body)[1] if adapter == "wsgi" else _asgi(app, method, path, body)[1]
        assert CORS not in headers, path


@pytest.mark.parametrize("adapter", ["wsgi", "asgi"])
def test_asset_and_request_routes_tell_the_browser_not_to_sniff_the_type(adapter: str) -> None:
    app = _app()

    class Clicker(Component):
        citry = app
        template = "<button>go</button>"

        def on_click(self) -> None:
            return None

    # Every public asset, then the routes that run events, then the misses:
    # the browser must take each response as the type it declares.
    requests = [
        *(("GET", path, b"") for path in _asset_paths(app)),
        ("POST", "/ext/events/call", b"{}"),
        ("POST", f"/ext/events/e/{Clicker.class_id}/on_click", b"{}"),
        ("POST", "/ext/i18n/messages", b"{}"),
        ("GET", f"/ext/events/definitions/{'0' * 64}.js", b""),
        ("GET", "/no-such-route", b""),
    ]
    for method, path, body in requests:
        headers = _wsgi(app, method, path, body)[1] if adapter == "wsgi" else _asgi(app, method, path, body)[1]
        assert headers.get(NOSNIFF) == "nosniff", (method, path)


def test_django_adapter_sends_the_cors_header_on_asset_routes() -> None:
    django = pytest.importorskip("django", reason="the Django adapter test needs django")
    from django.conf import settings

    if not settings.configured:
        settings.configure(ALLOWED_HOSTS=["*"])
        django.setup()
    from django.test import RequestFactory

    from citry.contrib.django import urlpatterns

    app = Citry(autodiscover=False)

    class Widget(Component):
        citry = app
        template = "<span>w</span>"
        js = """
            console.log(1);
        """

    by_name = {pattern.name: pattern for pattern in urlpatterns(app)}
    response = by_name["citry_cached_script"].callback(
        RequestFactory().get(f"/citry/cache/{Widget.class_id}.js"), class_id=Widget.class_id, script_type="js"
    )
    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "*"
    # The same response also tells the browser to take it as the JavaScript it declares.
    assert response["X-Content-Type-Options"] == "nosniff"


def test_preload_hints_request_owned_files_with_the_runtime_crossorigin_value() -> None:
    digest = "a" * 64
    preloads = _manifest_script_preloads(
        {
            "definitions": [{"url": "/citry/ext/events/definitions/d.js", "sha256": digest}],
            "scripts": [
                {"source": {"kind": "owned", "url": "/citry/owned.js", "sha256": digest}},
                # An author's explicit choice stays as written.
                {
                    "source": {
                        "kind": "owned",
                        "url": "/citry/credentialed.js",
                        "sha256": digest,
                        "attrs": {"crossorigin": "use-credentials"},
                    }
                },
                # Third-party URLs keep exactly the attributes the author gave.
                {"source": {"kind": "external", "url": "https://cdn.example.test/lib.js", "attrs": {}}},
            ],
        }
    )
    assert [dict(item.attrs).get("crossorigin") for item in preloads] == [
        OWNED_ASSET_CROSSORIGIN,
        OWNED_ASSET_CROSSORIGIN,
        "use-credentials",
        None,
    ]


def test_integrity_mode_fragment_loader_requests_the_runtime_with_cors() -> None:
    from citry._serialization_security import _ScriptSecurityMaterializer

    app = _app()
    security = _ScriptSecurityMaterializer(collect_integrity=True, csp_nonce=None)
    content = _preloader_script(app, security).content or ""
    # The loader sets both properties before it appends the element, which is
    # when the browser starts the request.
    assert content.index("s.integrity") < content.index('s.crossOrigin = "anonymous"') < content.index("appendChild")

    # Without integrity there is nothing to verify, so the request stays as it was.
    assert "crossOrigin" not in (_preloader_script(app, None).content or "")


def test_integrity_mode_owned_script_tag_requests_cors_unless_declared() -> None:
    from citry._serialization_security import _ScriptSecurityMaterializer
    from citry.ext.dependencies.types import Script

    def owned(attrs: dict[str, str | bool]) -> Script:
        script = Script(url="/citry/citry.js", attrs=attrs)
        script._owned_resource = _OwnedResource(url="/citry/citry.js", content="x", content_type="text/javascript")
        return script

    security = _ScriptSecurityMaterializer(collect_integrity=True, csp_nonce=None)
    assert security._materialize(owned({})).attrs["crossorigin"] == "anonymous"
    kept = security._materialize(owned({"CrossOrigin": "use-credentials"})).attrs
    assert kept["crossorigin"] == "use-credentials"
    assert "CrossOrigin" not in kept

    # A third-party URL with its own integrity keeps the author's attributes.
    external = Script(url="https://cdn.example.test/lib.js", attrs={"integrity": "sha384-" + "A" * 64})
    assert "crossorigin" not in security._materialize(external).attrs


def _get(
    adapter: str, app: Citry, path: str, request_headers: dict[str, str] | None = None
) -> tuple[int, dict[str, str]]:
    """Run one GET through the named adapter and return the numeric status and the headers."""
    if adapter == "wsgi":
        status, headers = _wsgi(app, "GET", path, request_headers=request_headers)
        return int(status.split(" ", 1)[0]), headers
    return _asgi(app, "GET", path, request_headers=request_headers)


@pytest.mark.parametrize("adapter", ["wsgi", "asgi"])
def test_every_public_asset_route_sends_a_cache_policy(adapter: str) -> None:
    app = _app()
    paths = _asset_paths(app)
    # The Events and i18n runtimes keep `no-store`, as the Events plan's
    # runtime-route amendment decided; every other file says how long the
    # browser may keep it.
    expected = {
        "/citry.js": "no-cache",
        "/ext/events/runtime.js": "no-store",
        "/ext/i18n/runtime.js": "no-store",
        paths[3]: IMMUTABLE_CACHE_CONTROL,
        paths[4]: IMMUTABLE_CACHE_CONTROL,
        paths[5]: "no-cache",
        paths[6]: IMMUTABLE_CACHE_CONTROL,
        paths[7]: IMMUTABLE_CACHE_CONTROL,
    }
    assert set(expected) == set(paths)
    for path, cache_control in expected.items():
        status, headers = _get(adapter, app, path)
        assert status == 200, path
        assert headers.get("cache-control") == cache_control, path
        # Only a URL whose content can change needs a tag to check it against.
        assert ("etag" in headers) == (cache_control == "no-cache"), path


@pytest.mark.parametrize("adapter", ["wsgi", "asgi"])
def test_a_current_copy_of_a_changing_url_gets_304(adapter: str) -> None:
    app = _app()
    unhashed = _asset_paths(app)[5]
    for path in ("/citry.js", unhashed):
        status, headers = _get(adapter, app, path)
        etag = headers["etag"]
        # The browser sends back the tag of the copy it holds.
        status, revalidated = _get(adapter, app, path, {"If-None-Match": etag})
        assert status == 304, path
        assert revalidated["etag"] == etag, path
        assert revalidated["cache-control"] == "no-cache", path
        assert revalidated[CORS] == "*", path
        # A copy with another tag is out of date, so the full file comes back.
        status, _ = _get(adapter, app, path, {"If-None-Match": '"0000"'})
        assert status == 200, path


def test_revalidated_response_compares_tags_the_way_http_requires() -> None:
    resource = _OwnedResource(url="/x.js", content="x", content_type="text/javascript")
    full = resource.revalidated_response(None)
    assert full.status == 200
    assert full.content == "x"
    etag = dict(full.headers)["ETag"]

    def status_for(if_none_match: str) -> int:
        request = RouteRequest(headers=RouteHeaders([("If-None-Match", if_none_match)]))
        return resource.revalidated_response(request).status

    assert status_for(etag) == 304
    # A proxy that compresses the body may mark the tag weak; it still names
    # the same content. A list of tags matches when any one of them does.
    assert status_for(f"W/{etag}") == 304
    assert status_for(f'"other", {etag}') == 304
    assert status_for("*") == 304
    assert status_for('"other"') == 200
    assert status_for(etag.strip('"')) == 200
    # A 304 carries no body.
    request = RouteRequest(headers=RouteHeaders([("If-None-Match", etag)]))
    assert resource.revalidated_response(request).body == b""
    # The tag follows the content.
    changed = _OwnedResource(url="/x.js", content="y", content_type="text/javascript")
    assert dict(changed.revalidated_response(None).headers)["ETag"] != etag


def test_served_dependencies_file_is_kept_for_a_year() -> None:
    app = _app()
    # `local_files="serve"` stores each file under its content hash.
    file_name = cache_asset(app, "console.log('served');", "js")
    status, headers = _get("wsgi", app, f"/asset/{file_name}")
    assert status == 200
    assert headers["cache-control"] == IMMUTABLE_CACHE_CONTROL


def _serve(app: Citry, path: str) -> RouteResponse:
    """Run one route handler directly, the way an adapter would, with no request headers."""
    matched = match_route(app.urls, path)
    assert matched is not None, path
    return matched.route.handler(RouteRequest(path=path), **matched.params)


def test_css_data_stylesheet_and_unhashed_css_are_checked_before_each_use() -> None:
    app = _app()

    class Themed(Component):
        citry = app
        template = "<span>w</span>"
        css = """
            .w { color: var(--accent); }
        """

        def css_data(self, kwargs, slots):
            return {"accent": "red"}

    rendered = Themed().render()
    record = next(iter(rendered.context.extra["dependencies"]))
    assert record.css_vars_hash is not None
    # Serializing the page stores the stylesheet its URL serves.
    rendered.serialize()
    # The hash covers the `css_data()` values, not the stylesheet text around
    # them, which a Citry upgrade can change at the same URL.
    variables = _serve(app, f"cache/{Themed.class_id}.{record.css_vars_hash}.css")
    assert variables.status == 200
    assert dict(variables.headers)["Cache-Control"] == "no-cache"
    assert "ETag" in dict(variables.headers)
    unhashed = _serve(app, f"cache/{Themed.class_id}.css")
    assert unhashed.status == 200
    assert dict(unhashed.headers)["Cache-Control"] == "no-cache"


def test_a_missing_file_is_never_kept() -> None:
    app = _app()

    class Widget(Component):
        citry = app
        template = "<span>w</span>"
        js = """
            console.log(1);
        """

    # Another worker may store the file a moment later, so no cache may keep
    # the miss.
    for path in (
        f"cache/{Widget.class_id}.{'a' * 12}.js",
        "cache/Nope_000000.js",
        f"cache/{Widget.class_id}.html",
        "asset/000000000000.js",
    ):
        response = _serve(app, path)
        assert response.status == 404, path
        assert dict(response.headers)["Cache-Control"] == "no-store", path


def test_every_worker_gives_citry_js_the_same_tag() -> None:
    # Two processes behind one load balancer must agree on the tag, or a
    # copy checked against the other worker would be downloaded again.
    first = dict(_serve(_app(), "citry.js").headers)["ETag"]
    second = dict(_serve(_app(), "citry.js").headers)["ETag"]
    assert first == second
