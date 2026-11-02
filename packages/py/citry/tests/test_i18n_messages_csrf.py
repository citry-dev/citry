"""
The i18n message route under each host's CSRF rules.

The browser posts to ``/citry/ext/i18n/messages`` when it switches locale.
Django's ``CsrfViewMiddleware`` checks that POST like any other view, so the
request passes only with the page's token in ``X-CSRFToken``, the header the
i18n runtime sends. These tests check the server side of that: the browser
side is proved in ``e2e/test_i18n_django_csrf_e2e.py``. The plain WSGI and
ASGI adapters have no token layer, so the header changes nothing there. The
route's own checks (POST only, an ``application/json`` body) apply on every
host.
"""

import asyncio
import io
import json
import sys
import types
from typing import Any

import pytest

from citry import Citry, Component
from citry.contrib.asgi import asgi_app
from citry.contrib.wsgi import wsgi_app

MESSAGES_PATH = "/ext/i18n/messages"
# A well-formed Django CSRF secret: 32 characters from the allowed alphabet.
CSRF_SECRET = "a" * 32
_URLCONF_NAME = "citry_i18n_messages_csrf_urlconf"


def _app() -> Citry:
    app = Citry(
        secret="i18n-messages-csrf-secret",  # noqa: S106 - deterministic test signing key
        autodiscover=False,
        extensions_defaults={"i18n": {"source_locale": "en-US", "locales": ("en-US",)}},
    )

    class Page(Component):
        citry = app
        template = "Page"
        messages = "client-title = Client title"

    # Rendering once loads the component catalog the route answers from.
    Page().render()
    return app


def _body(app: Citry) -> bytes:
    # The exact body the browser runtime posts (citry-i18n-core.ts fetchArtifact).
    revision = app.extensions.get_extension("i18n").catalog_revision
    return json.dumps(
        {
            "catalog_revision": revision,
            "locale": "en-US",
            "messages": [],
            "outputs": ["client-title"],
            "schema_version": 1,
        }
    ).encode()


@pytest.fixture
def django_client():
    # Django is optional and the WSGI and ASGI tests below must run without
    # it, so its imports wait until a Django test asks for this fixture.
    django = pytest.importorskip("django", reason="the Django CSRF tests need django")
    from django.conf import settings

    if not settings.configured:
        settings.configure(ALLOWED_HOSTS=["*"])
        django.setup()
    from django.test import Client
    from django.test.utils import override_settings
    from django.urls import clear_url_caches, include, path

    from citry.contrib.django import urlpatterns

    overrides = []

    def mount(app: Citry) -> Any:
        module = types.ModuleType(_URLCONF_NAME)
        module.urlpatterns = [path("citry/", include(urlpatterns(app, prefix="/citry")))]  # type: ignore[attr-defined]
        sys.modules[_URLCONF_NAME] = module
        clear_url_caches()
        override = override_settings(
            ROOT_URLCONF=_URLCONF_NAME,
            ALLOWED_HOSTS=["*"],
            MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
        )
        override.enable()
        overrides.append(override)
        # The test client skips CSRF checks unless asked, so ask: the point is
        # what the real middleware does with the browser's request.
        return Client(enforce_csrf_checks=True)

    yield mount
    for override in reversed(overrides):
        override.disable()
    sys.modules.pop(_URLCONF_NAME, None)
    clear_url_caches()


class TestDjango:
    def test_a_post_without_the_token_is_refused_by_django(self, django_client):
        # A POST with only Content-Type.
        app = _app()
        client = django_client(app)
        client.cookies["csrftoken"] = CSRF_SECRET
        response = client.post("/citry" + MESSAGES_PATH, _body(app), content_type="application/json")
        # Django's middleware answered; the route never ran (it answers JSON).
        assert response.status_code == 403
        assert not response["Content-Type"].startswith("application/json")

    def test_a_post_with_the_token_header_gets_the_messages(self, django_client):
        # The request the i18n runtime sends: the cookie's token in X-CSRFToken.
        app = _app()
        client = django_client(app)
        client.cookies["csrftoken"] = CSRF_SECRET
        response = client.post(
            "/citry" + MESSAGES_PATH,
            _body(app),
            content_type="application/json",
            headers={"X-CSRFToken": CSRF_SECRET},
        )
        assert response.status_code == 200
        assert list(response.json()["messages"]) == ["client-title"]

    def test_the_route_keeps_its_own_checks_behind_django(self, django_client):
        app = _app()
        client = django_client(app)
        client.cookies["csrftoken"] = CSRF_SECRET
        token = {"X-CSRFToken": CSRF_SECRET}
        # A valid token does not widen what the route accepts: another body
        # type is still refused, and the route still answers only POST.
        wrong_type = client.post("/citry" + MESSAGES_PATH, _body(app), content_type="text/plain", headers=token)
        assert wrong_type.status_code == 400
        assert wrong_type.json()["error"]["code"] == "I18N_BROWSER_REQUEST_INVALID"
        assert client.get("/citry" + MESSAGES_PATH, headers=token).status_code == 405


def _wsgi(app: Citry, body: bytes, headers: dict[str, str]) -> tuple[str, bytes]:
    captured: dict[str, Any] = {}

    def start_response(status: str, _headers: list[tuple[str, str]]) -> None:
        captured["status"] = status

    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": MESSAGES_PATH,
        "SCRIPT_NAME": "",
        "QUERY_STRING": "",
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
        **{f"HTTP_{name.upper().replace('-', '_')}": value for name, value in headers.items()},
    }
    content = b"".join(wsgi_app(app)(environ, start_response))
    return captured["status"], content


def _asgi(app: Citry, body: bytes, headers: dict[str, str]) -> tuple[int, bytes]:
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
        "method": "POST",
        "path": MESSAGES_PATH,
        "root_path": "",
        "query_string": b"",
        "headers": [
            (b"content-type", b"application/json"),
            *((name.lower().encode("latin-1"), value.encode("latin-1")) for name, value in headers.items()),
        ],
    }
    asyncio.run(asgi_app(app)(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    content = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return start["status"], content


@pytest.mark.parametrize("adapter", [_wsgi, _asgi], ids=["wsgi", "asgi"])
def test_hosts_without_a_token_layer_answer_the_same_with_or_without_the_header(adapter):
    app = _app()
    app.set_mounted_prefix("/citry")
    body = _body(app)
    without = adapter(app, body, {})
    with_token = adapter(app, body, {"X-CSRFToken": CSRF_SECRET})
    assert str(without[0]).startswith("200")
    assert with_token == without
