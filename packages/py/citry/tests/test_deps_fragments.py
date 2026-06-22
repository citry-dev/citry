"""Tests for the ``fragment`` strategy and the mounted ``document`` flow."""

import base64
import json
import re

import pytest

from citry import Citry, Component


def _manifest(html):
    match = re.search(r'<script type="application/json" data-citry>(.*?)</script>', html, re.DOTALL)
    assert match is not None, "no manifest in output"
    return json.loads(match.group(1))


def _unb64(value):
    return base64.b64decode(value).decode()


def _widget(c):
    class Widget(Component):
        citry = c
        template = "<span>w</span>"
        js = "$onComponent(({ els, data }) => { els[0].textContent = data.rows; });"
        css = ".w { color: var(--row-color); }"

        def js_data(self, kwargs, slots=None):
            return {"rows": 3}

        def css_data(self, kwargs, slots=None):
            return {"row-color": "red"}

    return Widget


class TestFragmentStrategy:
    def test_fragment_carries_urls_not_content(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        widget = _widget(c)

        rendered = widget().render()
        record = rendered.context.extra["dependencies"][0]
        html = rendered.serialize(deps_strategy="fragment")

        # The content itself, with the data-ccss marker (CSS vars are pure CSS).
        assert re.search(r"<span[^>]*data-ccss-", html)
        # Nothing inlined: no component JS/CSS bodies, no runtime.
        assert "registerComponentData(" not in html
        assert ".w { color" not in html
        assert "client-side dependency manager" not in html

        manifest = _manifest(html)
        fetch_js = [json.loads(_unb64(item)) for item in manifest["fetch"]["js"]]
        fetch_css = [json.loads(_unb64(item)) for item in manifest["fetch"]["css"]]
        js_urls = [item["attrs"]["src"] for item in fetch_js]
        css_urls = [item["attrs"]["href"] for item in fetch_css]
        assert f"/citry/cache/{widget.class_id}.js" in js_urls
        assert f"/citry/cache/{widget.class_id}.{record.js_vars_hash}.js" in js_urls
        assert f"/citry/cache/{widget.class_id}.css" in css_urls
        assert f"/citry/cache/{widget.class_id}.{record.css_vars_hash}.css" in css_urls

        # The instance call rides along; nothing is marked as loaded (the
        # manager marks what it fetches itself).
        calls = [[_unb64(part) if part is not None else None for part in call] for call in manifest["calls"]]
        assert calls == [[widget.class_id, record.component_id, record.js_vars_hash]]
        assert manifest["markLoaded"] == {"js": [], "css": []}

    def test_fragment_includes_the_preloader(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        _widget(c)
        page = type("Page", (Component,), {"citry": c, "template": "<main><c-widget /></main>"})
        html = str(page().render().serialize(deps_strategy="fragment"))
        assert 's.src = "/citry/citry.js"' in html
        assert "document.currentScript.remove()" in html

    def test_fragment_inlines_local_file_entries_as_descriptors(self, tmp_path):
        (tmp_path / "helper.js").write_text("var H = 1;")
        c = Citry(dirs=[tmp_path])
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                js = ["helper.js"]

        html = Card().render().serialize(deps_strategy="fragment")
        fetch_js = [json.loads(_unb64(item)) for item in _manifest(html)["fetch"]["js"]]
        inline = [item for item in fetch_js if item["content"]]
        assert inline
        assert inline[0]["content"] == "var H = 1;"

    def test_fragment_rejects_prerendered_entries(self):
        from citry.util.html import SafeString

        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                js = [SafeString("<script>raw()</script>")]

        with pytest.raises(TypeError, match="pre-rendered"):
            Card().render().serialize(deps_strategy="fragment")


class TestServedLocalFiles:
    def _card(self, c, tmp_path):
        (tmp_path / "theme.css").write_text(".t { color: teal; }")

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                css = "theme.css"

        return Card

    def test_serve_mode_emits_a_fingerprinted_url(self, tmp_path):
        from citry.util.routing import match_route

        c = Citry(dirs=[tmp_path], extensions_defaults={"dependencies": {"local_files": "serve"}})
        c.set_mounted_prefix("/citry")
        card = self._card(c, tmp_path)

        html = str(card())
        match = re.search(r'href="(/citry/asset/([0-9a-f]{12})\.css)"', html)
        assert match is not None, html
        assert ".t { color: teal; }" not in html  # not inlined

        # The emitted URL is servable, with the file's content.
        matched = match_route(c.urls, match.group(1).removeprefix("/citry/"))
        response = matched.route.handler(None, **matched.params)
        assert response.status == 200
        assert response.content == ".t { color: teal; }"
        assert response.content_type == "text/css"

    def test_serve_mode_falls_back_to_inline_when_unmounted(self, tmp_path):
        c = Citry(dirs=[tmp_path], extensions_defaults={"dependencies": {"local_files": "serve"}})
        card = self._card(c, tmp_path)
        html = str(card())
        assert ".t { color: teal; }" in html
        assert "/asset/" not in html

    def test_mode_set_per_component(self, tmp_path):
        (tmp_path / "a.css").write_text(".a {}")
        c = Citry(dirs=[tmp_path])
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                css = "a.css"
                local_files = "serve"

        html = str(Card())
        assert "/citry/asset/" in html

    def test_invalid_mode_raises(self, tmp_path):
        (tmp_path / "a.css").write_text(".a {}")
        c = Citry(dirs=[tmp_path], extensions_defaults={"dependencies": {"local_files": "nope"}})

        class Card(Component):
            citry = c
            template = "<p>x</p>"

            class Dependencies:
                css = "a.css"

        with pytest.raises(ValueError, match="local_files"):
            str(Card())


class TestMountedDocumentFlow:
    def test_runtime_served_by_url_when_mounted(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        _widget(c)
        page = type("Page", (Component,), {"citry": c, "template": "<main><c-widget /></main>"})
        html = str(page())
        assert '<script src="/citry/citry.js"></script>' in html
        assert "client-side dependency manager" not in html  # not inlined

    def test_document_marks_cache_urls_for_later_fragments(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        widget = _widget(c)
        page = type("Page", (Component,), {"citry": c, "template": "<main><c-widget /></main>"})

        rendered = page().render()
        record = next(r for r in rendered.context.extra["dependencies"] if r.class_id == widget.class_id)
        manifest = _manifest(rendered.serialize())
        marked_js = [_unb64(url) for url in manifest["markLoaded"]["js"]]
        marked_css = [_unb64(url) for url in manifest["markLoaded"]["css"]]
        assert f"/citry/cache/{widget.class_id}.js" in marked_js
        assert f"/citry/cache/{widget.class_id}.{record.js_vars_hash}.js" in marked_js
        assert f"/citry/cache/{widget.class_id}.css" in marked_css
