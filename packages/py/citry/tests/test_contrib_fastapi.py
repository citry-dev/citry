"""End-to-end tests of the web integration: FastAPI + TestClient over citry's mounted routes."""

import json
import re

import pytest

fastapi = pytest.importorskip("fastapi", reason="the web-integration tests need fastapi + httpx2")
pytest.importorskip("httpx2", reason="Starlette's TestClient needs httpx2")

from fastapi.testclient import TestClient  # noqa: E402

from citry import Citry, Component  # noqa: E402
from citry.contrib.fastapi import mount  # noqa: E402


def _build_app(c):
    app = fastapi.FastAPI()
    mount(app, c)
    return TestClient(app)


def _widget(c):
    class Widget(Component):
        citry = c
        template = "<span>w</span>"
        js = "$component({ onServerRender({ component }) { console.log(component.rows); } });"
        css = ".w {}"

        def js_data(self, kwargs, slots):
            return {"rows": 3}

    return Widget


class TestMount:
    def test_mount_records_the_prefix(self):
        c = Citry()
        _build_app(c)
        assert c.mounted_prefix == "/citry"

    def test_custom_prefix(self):
        c = Citry()
        app = fastapi.FastAPI()
        mount(app, c, prefix="/assets/citry")
        assert c.mounted_prefix == "/assets/citry"
        client = TestClient(app)
        assert client.get("/assets/citry/citry.js").status_code == 200


class TestServedEndpoints:
    def test_serves_the_runtime(self):
        c = Citry()
        client = _build_app(c)
        response = client.get("/citry/citry.js")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/javascript")
        assert "Citry interactive runtime." in response.text

    def test_serves_class_scripts(self):
        c = Citry()
        widget = _widget(c)
        client = _build_app(c)
        js = client.get(f"/citry/cache/{widget.class_id}.js")
        assert js.status_code == 200
        # The served Vue Options source is associated with its type and source digest.
        assert f'CitryStable.registerTypeOptions.bind(null, "{widget.class_id}", "' in js.text
        css = client.get(f"/citry/cache/{widget.class_id}.css")
        assert css.status_code == 200
        assert css.text == ".w {}"
        assert css.headers["content-type"].startswith("text/css")

    def test_unknown_paths_404_and_post_405(self):
        c = Citry()
        widget = _widget(c)
        client = _build_app(c)
        assert client.get("/citry/cache/Nope_000000.js").status_code == 404
        assert client.get("/citry/nope").status_code == 404
        assert client.post(f"/citry/cache/{widget.class_id}.js").status_code == 405


class TestFragmentRoundTrip:
    def test_every_url_a_fragment_references_is_servable(self):
        c = Citry()
        app = fastapi.FastAPI()
        mount(app, c)
        client = TestClient(app)
        _widget(c)

        page = type("Page", (Component,), {"citry": c, "template": "<main><c-widget /></main>"})
        fragment = page().render().serialize(deps_strategy="fragment")

        match = re.search(
            r'<script type="application/json" data-citry-vue-fragment>(.*?)</script>', fragment, re.DOTALL
        )
        assert match is not None
        manifest = json.loads(match.group(1))["vue"]["prepared"]["manifest"]
        descriptors = [*manifest["scripts"], *manifest["styles"]]
        urls = [descriptor["source"]["url"] for descriptor in descriptors if "url" in descriptor["source"]]
        assert urls, "fragment references no URLs"
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200, url

        # The preloader's runtime URL is servable too.
        preloader = re.search(r's\.src = "([^"]+)"', fragment)
        assert preloader is not None
        preloader_url = preloader.group(1)
        assert client.get(preloader_url).status_code == 200
