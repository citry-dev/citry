"""Host adapters render the same representative Citry UI scenarios."""

from __future__ import annotations

import io
import re
import sys
from types import ModuleType

import pytest

from citry.contrib.asgi import asgi_app
from citry.contrib.wsgi import wsgi_app
from citry_ui.quality.routes import build_scenario

_REPRESENTATIVE_SCENARIOS = (
    "composition.orbit-access",
    "composition.ledger-dashboard",
)


def _asset_urls(html: str, prefix: str) -> tuple[str, ...]:
    values = re.findall(r'(?:src|href)="([^"]+)"', html)
    return tuple(value for value in values if value.startswith(prefix))


@pytest.mark.parametrize("scenario_id", _REPRESENTATIVE_SCENARIOS)
def test_fastapi_serves_shared_page_and_every_referenced_citry_asset(scenario_id):
    fastapi = pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.responses import HTMLResponse
    from fastapi.testclient import TestClient

    from citry.contrib.fastapi import mount

    host = fastapi.FastAPI()
    rendered = build_scenario(
        scenario_id,
        configure_app=lambda app: mount(host, app, prefix="/assets/citry"),
    )

    @host.get("/quality", response_class=HTMLResponse)
    def quality_page():
        return rendered.html

    client = TestClient(host)
    response = client.get("/quality")
    assert response.status_code == 200
    assert f'data-citry-ui-scenario="{scenario_id}"' in response.text
    asset_urls = _asset_urls(response.text, "/assets/citry/")
    assert asset_urls
    assert all(client.get(url).status_code == 200 for url in asset_urls)


@pytest.mark.parametrize("scenario_id", _REPRESENTATIVE_SCENARIOS)
def test_django_serves_shared_page_and_every_referenced_citry_asset(scenario_id):
    django = pytest.importorskip("django")
    from django.conf import settings
    from django.http import HttpResponse
    from django.test import Client, override_settings
    from django.urls import clear_url_caches, include, path

    from citry.contrib.django import urlpatterns as citry_urlpatterns

    if not settings.configured:
        settings.configure(ALLOWED_HOSTS=["testserver"], SECRET_KEY="citry-ui-quality")  # noqa: S106
        django.setup()

    patterns = []

    def configure(app):
        patterns.extend(citry_urlpatterns(app, prefix="/assets/citry"))

    rendered = build_scenario(scenario_id, configure_app=configure)
    module_name = f"citry_ui_quality_urls_{scenario_id.replace('.', '_').replace('-', '_')}"
    urlconf = ModuleType(module_name)

    def django_quality_page(request):
        return HttpResponse(rendered.html)

    urlconf.urlpatterns = [
        path("quality", django_quality_page),
        path("assets/citry/", include(patterns)),
    ]
    sys.modules[module_name] = urlconf
    try:
        with override_settings(ROOT_URLCONF=module_name):
            clear_url_caches()
            client = Client()
            response = client.get("/quality")
            assert response.status_code == 200
            html = response.content.decode()
            assert f'data-citry-ui-scenario="{scenario_id}"' in html
            asset_urls = _asset_urls(html, "/assets/citry/")
            assert asset_urls
            assert all(client.get(url).status_code == 200 for url in asset_urls)
    finally:
        clear_url_caches()
        sys.modules.pop(module_name, None)


def test_generic_asgi_adapter_serves_assets_for_the_shared_tabs_scenario():
    pytest.importorskip("httpx")
    from starlette.testclient import TestClient

    rendered = build_scenario(
        "tabs.overview",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    assert _asset_urls(rendered.html, "/citry/")

    with TestClient(asgi_app(rendered.app)) as client:
        response = client.get("/citry.js")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/javascript")


def test_generic_wsgi_adapter_serves_assets_for_the_shared_tabs_scenario():
    rendered = build_scenario(
        "tabs.overview",
        configure_app=lambda app: app.set_mounted_prefix("/citry"),
    )
    assert _asset_urls(rendered.html, "/citry/")
    captured: dict[str, object] = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(
        wsgi_app(rendered.app)(
            {
                "PATH_INFO": "/citry.js",
                "SCRIPT_NAME": "/citry",
                "REQUEST_METHOD": "GET",
                "QUERY_STRING": "",
                "wsgi.input": io.BytesIO(),
            },
            start_response,
        ),
    )
    assert captured["status"] == "200 OK"
    assert b"client-side dependency manager" in body
