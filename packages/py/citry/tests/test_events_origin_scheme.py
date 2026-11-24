"""
The Events CSRF check refuses an ``http:`` Origin on a request that arrived over https.

Each adapter reports the scheme its host gives it (the WSGI environ's
``wsgi.url_scheme``, the ASGI scope's ``scheme``, Django's
``request.scheme``), and the same call runs through all three. The proxy
case is a request the app sees as http while the browser, which talked
https to a proxy that ends TLS, sends an ``https:`` Origin: it must pass.
"""

from __future__ import annotations

import io
import json
import sys
import types
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

import pytest

django = pytest.importorskip("django", reason="the Django case needs Django")
pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")

from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(ALLOWED_HOSTS=["*"])
    django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from django.urls import clear_url_caches, include, path  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from citry import Citry, Component  # noqa: E402
from citry.contrib.asgi import asgi_app  # noqa: E402
from citry.contrib.django import urlpatterns as django_urlpatterns  # noqa: E402
from citry.contrib.wsgi import wsgi_app  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterator

SIGNING_KEY = "events-origin-scheme-secret"
ENVELOPE_CONTENT_TYPE = "application/citry-events+json"
HOST = "app.example"

# (the scheme the host reports, the browser's Origin, the expected status)
CASES = [
    # A page on plain http on the same host calls the https app: refused.
    pytest.param("https", f"http://{HOST}", 403, id="https-request-http-origin"),
    pytest.param("https", f"https://{HOST}", 200, id="https-request-https-origin"),
    # Behind a proxy that ends TLS: the app sees http, the browser sends https.
    pytest.param("http", f"https://{HOST}", 200, id="proxy-http-request-https-origin"),
    pytest.param("http", f"http://{HOST}", 200, id="http-request-http-origin"),
]


class _EchoIn:
    text: str = ""


def _engine() -> tuple[Citry, type[Component]]:
    engine = Citry(secret=SIGNING_KEY)
    engine.set_mounted_prefix("/citry")

    class OriginScheme(Component):
        # Each engine owns its own copy of the class.
        citry = engine

        template = """
            <p>origin scheme</p>
        """

        class Events:
            def echo(self, data: _EchoIn) -> dict[str, str]:
                return {"text": data.text}

    return engine, OriginScheme


def _envelope(component: type[Component]) -> bytes:
    return json.dumps(
        {
            "protocol": "citry-events/1",
            "requestId": "r1",
            "calls": [{"componentClassId": component.class_id, "handlerName": "echo", "args": {"text": "hi"}}],
        }
    ).encode()


def _wsgi_status(scheme: str, origin: str) -> int:
    citry, component = _engine()
    body = _envelope(component)
    environ: dict[str, Any] = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": f"/ext/events/e/{component.class_id}/echo",
        "SCRIPT_NAME": "",
        "QUERY_STRING": "",
        "CONTENT_TYPE": ENVELOPE_CONTENT_TYPE,
        "CONTENT_LENGTH": str(len(body)),
        "HTTP_HOST": HOST,
        "HTTP_ORIGIN": origin,
        "HTTP_X_CITRY_EVENTS": "1",
        "wsgi.url_scheme": scheme,
        "wsgi.input": io.BytesIO(body),
    }
    sent: dict[str, str] = {}

    def start_response(status: str, headers: list[tuple[str, str]]) -> None:
        sent["status"] = status

    b"".join(wsgi_app(citry)(environ, start_response))
    return int(sent["status"].split()[0])


def _asgi_status(scheme: str, origin: str) -> int:
    citry, component = _engine()
    # Starlette's TestClient copies the base URL's scheme into the ASGI scope.
    with TestClient(asgi_app(citry), base_url=f"{scheme}://{HOST}") as client:
        response = client.post(
            f"/ext/events/e/{component.class_id}/echo",
            content=_envelope(component),
            headers={"Content-Type": ENVELOPE_CONTENT_TYPE, "Origin": origin, "X-Citry-Events": "1"},
        )
    return response.status_code


_urlconf_serial = 0


@contextmanager
def _django_client(**setting_overrides: Any) -> Iterator[tuple[Client, type[Component]]]:
    global _urlconf_serial  # noqa: PLW0603 - Django needs an importable module name
    _urlconf_serial += 1
    module_name = f"citry_events_origin_scheme_urls_{_urlconf_serial}"
    citry, component = _engine()
    module = types.ModuleType(module_name)
    module.urlpatterns = [path("citry/", include(django_urlpatterns(citry, prefix="/citry")))]  # type: ignore[attr-defined]
    sys.modules[module_name] = module
    clear_url_caches()
    override = override_settings(ROOT_URLCONF=module_name, ALLOWED_HOSTS=["*"], MIDDLEWARE=[], **setting_overrides)
    override.enable()
    try:
        yield Client(), component
    finally:
        override.disable()
        sys.modules.pop(module_name, None)
        clear_url_caches()


def _django_post(client: Client, component: type[Component], origin: str, **extra: Any) -> int:
    response = client.post(
        f"/citry/ext/events/e/{component.class_id}/echo",
        data=_envelope(component),
        content_type=ENVELOPE_CONTENT_TYPE,
        headers={"Host": HOST, "Origin": origin, "X-Citry-Events": "1"},
        **extra,
    )
    return response.status_code


def _django_status(scheme: str, origin: str) -> int:
    with _django_client() as (client, component):
        # Django's test client sets wsgi.url_scheme to https for secure=True.
        return _django_post(client, component, origin, secure=scheme == "https")


@pytest.mark.parametrize(("scheme", "origin", "expected"), CASES)
@pytest.mark.parametrize("status_of", [_wsgi_status, _asgi_status, _django_status], ids=["wsgi", "asgi", "django"])
def test_each_adapter_checks_the_origin_scheme_against_the_request_scheme(
    status_of: Any, scheme: str, origin: str, expected: int
) -> None:
    assert status_of(scheme, origin) == expected


def test_django_reads_the_scheme_the_proxy_forwards() -> None:
    # With SECURE_PROXY_SSL_HEADER set, Django reports https for a call the
    # proxy marks as https, so an http Origin is refused there too.
    with _django_client(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https")) as (client, component):
        forwarded = {"HTTP_X_FORWARDED_PROTO": "https"}
        assert _django_post(client, component, f"http://{HOST}", **forwarded) == 403
        assert _django_post(client, component, f"https://{HOST}", **forwarded) == 200
        # Without the forwarded header the request is http, and the proxy's
        # https Origin still passes.
        assert _django_post(client, component, f"https://{HOST}") == 200


def test_csrf_failed_is_the_wire_error_for_the_refused_scheme() -> None:
    citry, component = _engine()
    with TestClient(asgi_app(citry), base_url=f"https://{HOST}") as client:
        response = client.post(
            f"/ext/events/e/{component.class_id}/echo",
            content=_envelope(component),
            headers={"Content-Type": ENVELOPE_CONTENT_TYPE, "Origin": f"http://{HOST}", "X-Citry-Events": "1"},
        )
    assert response.json()["results"][0]["error"]["code"] == "csrf_failed"
