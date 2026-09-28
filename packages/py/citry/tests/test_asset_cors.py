"""
Citry's public JS and CSS routes let any page read them; its request routes do not.

Citry puts ``integrity`` and ``crossorigin="anonymous"`` on the files it serves
itself. A page inside a sandboxed iframe has an opaque origin, so the browser
treats every one of those requests as cross-origin and checks the digest only
when the response carries ``Access-Control-Allow-Origin``. These tests drive
the real WSGI and ASGI adapters, so they prove the header reaches the wire and
stays off the routes that run events or read request data.
"""

from __future__ import annotations

import asyncio
import io
from typing import Any

import pytest

from citry import Citry, Component
from citry._owned_resource import OWNED_ASSET_CROSSORIGIN, _OwnedResource
from citry._vue.capture import render_prepared_direct
from citry._vue.events import default_events_producer
from citry._vue.serialization import _manifest_script_preloads
from citry.contrib.asgi import asgi_app
from citry.contrib.wsgi import wsgi_app
from citry.ext.dependencies.emission import _preloader_script
from citry.ext.dependencies.routes import script_url

CORS = "access-control-allow-origin"


def _app() -> Citry:
    app = Citry(
        secret="asset-cors-test-secret",  # noqa: S106
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )
    app.set_mounted_prefix("/citry")
    return app


def _wsgi(app: Citry, method: str, path: str, body: bytes = b"") -> tuple[str, dict[str, str]]:
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
    }
    b"".join(wsgi_app(app)(environ, start_response))
    return captured["status"], captured["headers"]


def _asgi(app: Citry, method: str, path: str, body: bytes = b"") -> tuple[int, dict[str, str]]:
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
        "headers": [(b"content-type", b"application/json")] if body else [],
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
