"""End-to-end tests of the web integration: FastAPI + TestClient over citry's mounted routes."""

import base64
import json
import re

import pytest

fastapi = pytest.importorskip("fastapi", reason="the web-integration tests need fastapi + httpx")
pytest.importorskip("httpx", reason="Starlette's TestClient needs httpx")

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
        js = "$onComponent(({ els, data }) => { els[0].textContent = data.rows; });"
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
        assert "client-side dependency manager" in response.text

    def test_serves_class_scripts(self):
        c = Citry()
        widget = _widget(c)
        client = _build_app(c)
        js = client.get(f"/citry/cache/{widget.class_id}.js")
        assert js.status_code == 200
        # The served form carries the $onComponent expansion.
        assert f'registerComponent("{widget.class_id}"' in js.text
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
        widget = _widget(c)

        page = type("Page", (Component,), {"citry": c, "template": "<main><c-widget /></main>"})
        fragment = page().render().serialize(deps_strategy="fragment")

        match = re.search(r'<script type="application/json" data-citry>(.*?)</script>', fragment, re.DOTALL)
        manifest = json.loads(match.group(1))
        descriptors = [
            json.loads(base64.b64decode(item).decode())
            for item in [*manifest["fetch"]["js"], *manifest["fetch"]["css"]]
        ]
        urls = [d["attrs"].get("src") or d["attrs"].get("href") for d in descriptors]
        assert urls, "fragment references no URLs"
        for url in urls:
            response = client.get(url)
            assert response.status_code == 200, url

        # The preloader's runtime URL is servable too.
        preloader_url = re.search(r's\.src = "([^"]+)"', fragment).group(1)
        assert client.get(preloader_url).status_code == 200
        del widget
