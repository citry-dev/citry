"""Tests for the ``fragment`` strategy and the mounted ``document`` flow."""

import base64
import json
import re

import pytest

from citry import Citry, Component, Extension, Markup
from citry.ext.dependencies import Script
from citry.ext.dependencies.routes import script_url
from citry.util.routing import match_route


def _manifest(html):
    match = re.search(r'<script type="application/json" data-citry>(.*?)</script>', html, re.DOTALL)
    assert match is not None, "no manifest in output"
    return json.loads(match.group(1))


def _unb64(value):
    return base64.b64decode(value).decode()


def _fetch_descriptors(manifest, kind):
    return [json.loads(_unb64(item[0] if isinstance(item, list) else item)) for item in manifest["fetch"][kind]]


def _widget(c):
    class Widget(Component):
        citry = c
        template = "<span>w</span>"
        js = "$component(({ els, data }) => { els[0].textContent = data.rows; });"
        css = ".w { color: var(--row-color); }"

        def js_data(self, kwargs, slots):
            return {"rows": 3}

        def css_data(self, kwargs, slots):
            return {"row-color": "red"}

    return Widget


class TestFragmentStrategy:
    def test_fragment_carries_urls_not_content(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        widget = _widget(c)

        rendered = widget().render()
        record = next(iter(rendered.context.extra["dependencies"]))
        html = rendered.serialize(deps_strategy="fragment")

        # The content itself, with the data-ccss marker (CSS vars are pure CSS).
        assert re.search(r"<span[^>]*data-ccss-", html)
        # Nothing inlined: no component JS/CSS bodies, no runtime.
        assert "registerComponentData(" not in html
        assert ".w { color" not in html
        assert "client-side dependency manager" not in html

        manifest = _manifest(html)
        fetch_js = _fetch_descriptors(manifest, "js")
        fetch_css = _fetch_descriptors(manifest, "css")
        js_urls = [item["attrs"]["src"] for item in fetch_js]
        css_urls = [item["attrs"]["href"] for item in fetch_css]
        assert script_url(widget, "js") in js_urls
        assert f"/citry/cache/{widget.class_id}.{record.js_vars_hash}.js" in js_urls
        assert script_url(widget, "css") in css_urls
        assert f"/citry/cache/{widget.class_id}.{record.css_vars_hash}.css" in css_urls

        # The instance call rides along; nothing is marked as loaded (the
        # manager marks what it fetches itself).
        calls = [
            [_unb64(call[0]), _unb64(call[1]), None if call[2] is None else _unb64(call[2]), call[3]]
            for call in manifest["calls"]
        ]
        assert calls == [[widget.class_id, record.component_id, record.js_vars_hash, "init"]]
        assert manifest["markLoaded"] == {"js": [], "css": []}

    def test_graph_fetches_union_sorted_component_owners(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        widget = _widget(c)

        class Page(Component):
            citry = c
            template = """
                <main><c-widget /><c-widget /></main>
            """

        rendered = Page().render()
        records = [record for record in rendered.context.extra["dependencies"] if record.class_id == widget.class_id]
        manifest = _manifest(rendered.serialize(deps_strategy="fragment"))
        class_url = script_url(widget, "js")
        entries = []
        for descriptor_encoded, owners_encoded in manifest["fetch"]["js"]:
            descriptor = json.loads(_unb64(descriptor_encoded))
            if descriptor["attrs"].get("src") == class_url:
                entries.append([_unb64(owner) for owner in owners_encoded])

        assert entries == [sorted(record.component_id for record in records)]

    def test_graph_before_manifest_dependencies_stay_inert_in_the_wire(self):
        class HookAssets(Extension):
            name = "hook_assets"

            def on_dependencies(self, ctx):
                ctx.before_manifest.append(Script(content="globalThis.fragmentLeaked = true;", wrap=False))

        c = Citry(extensions=[HookAssets])
        c.set_mounted_prefix("/citry")
        widget = _widget(c)
        html = widget().render().serialize(deps_strategy="fragment")
        manifest = _manifest(html)

        assert "<script>globalThis.fragmentLeaked = true;</script>" not in html
        assert len(manifest["beforeManifest"]) == 1
        descriptor = json.loads(_unb64(manifest["beforeManifest"][0]))
        assert descriptor == {"tag": "script", "attrs": {}, "content": "globalThis.fragmentLeaked = true;"}

    def test_fragment_serves_contained_css_variables(self):
        payload = 'red"; } body { outline: 99px solid red; } x { color: "blue'
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = '<span class="card">card</span>'
            css = ".card { color: var(--accent); }"

            def css_data(self, kwargs, slots):
                return {"accent": payload}

        rendered = Card().render()
        record = next(iter(rendered.context.extra["dependencies"]))
        fragment = rendered.serialize(deps_strategy="fragment")
        css_url = f"/citry/cache/{Card.class_id}.{record.css_vars_hash}.css"

        assert css_url in [item["attrs"]["href"] for item in _fetch_descriptors(_manifest(fragment), "css")]
        matched = match_route(c.urls, css_url.removeprefix("/citry/"))
        response = matched.route.handler(None, **matched.params)
        assert response.status == 200
        assert '--accent: "red\\"; } body { outline: 99px solid red; } x { color: \\"blue";' in response.content
        assert "\nbody {" not in response.content

    def test_delayed_fragment_uses_the_rendering_class_version_urls(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        def make_card(label):
            class Card(Component):
                citry = c
                template = f"<p>{label}</p>"
                js = f'console.log("{label}");'
                css = f".{label} {{ color: red; }}"

            return Card

        old_card = make_card("old")
        old_render = old_card().render()
        c.unregister(old_card)
        new_card = make_card("new")
        assert new_card.class_id == old_card.class_id

        manifest = _manifest(old_render.serialize(deps_strategy="fragment"))
        js_urls = [item["attrs"]["src"] for item in _fetch_descriptors(manifest, "js")]
        css_urls = [item["attrs"]["href"] for item in _fetch_descriptors(manifest, "css")]

        assert script_url(old_card, "js") in js_urls
        assert script_url(old_card, "css") in css_urls
        assert script_url(new_card, "js") not in js_urls
        assert script_url(new_card, "css") not in css_urls

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
        fetch_js = _fetch_descriptors(_manifest(html), "js")
        inline = [item for item in fetch_js if item["content"]]
        assert inline
        assert inline[0]["content"] == "var H = 1;"

    @pytest.mark.parametrize(
        ("attr", "tag"),
        [
            ("js", Markup("<script>raw()</script>")),
            ("css", Markup("<style>.raw {}</style>")),
        ],
    )
    def test_fragment_rejects_prerendered_entries(self, attr, tag):
        c = Citry()
        c.set_mounted_prefix("/citry")
        dependencies = type("Dependencies", (), {attr: [tag]})
        card = type(
            "Card",
            (Component,),
            {
                "citry": c,
                "template": """
                    <p>x</p>
                """,
                "Dependencies": dependencies,
            },
        )

        with pytest.raises(TypeError, match="pre-rendered"):
            card().render().serialize(deps_strategy="fragment")

    def test_hook_created_fragment_dependency_requires_mounting(self):
        class HookAssets(Extension):
            name = "hook_assets"

            def on_dependencies(self, ctx):
                ctx.scripts.append(Script(url="/hook.js"))

        c = Citry(extensions=[HookAssets])

        class Bare(Component):
            citry = c
            template = """
                <p>bare</p>
            """

        with pytest.raises(RuntimeError, match="needs a mounted web integration"):
            Bare().render().serialize(deps_strategy="fragment")

    def test_fragment_rejects_a_quoted_runtime_url(self):
        c = Citry()
        c.set_mounted_prefix('/ci"try')

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """

            class Dependencies:
                js = ["/static/card.js"]

        with pytest.raises(ValueError, match="runtime URL cannot contain quotes"):
            Card().render().serialize(deps_strategy="fragment")

    def test_whitespace_css_creates_no_variables_or_fragment_css(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """
            css = """
                \x20\t
            """

            class Dependencies:
                js = ["/static/card.js"]

            def css_data(self, kwargs, slots):
                return {"accent": "teal"}

        rendered = Card().render()
        record = next(iter(rendered.context.extra["dependencies"]))
        assert record.css_vars_hash is None
        assert "data-ccss-" not in rendered.serialize()

        fragment = rendered.serialize(deps_strategy="fragment")
        manifest = _manifest(fragment)
        fetch_js = _fetch_descriptors(manifest, "js")
        fetch_css = _fetch_descriptors(manifest, "css")
        assert [item["attrs"]["src"] for item in fetch_js] == ["/static/card.js"]
        assert fetch_css == []
        assert manifest["cssInstances"] == []
        assert "data-ccss-" not in fragment


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

    def test_serve_mode_emits_stable_fingerprinted_js_url(self, tmp_path):
        source = "globalThis.vendorLoaded = true;"
        (tmp_path / "vendor.js").write_text(source)
        c = Citry(dirs=[tmp_path], extensions_defaults={"dependencies": {"local_files": "serve"}})
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """

            class Dependencies:
                js = "vendor.js"

        first_html = str(Card())
        second_html = str(Card())
        pattern = r'src="(/citry/asset/[0-9a-f]{12}\.js)"'
        first_url = re.search(pattern, first_html)
        second_url = re.search(pattern, second_html)
        assert first_url is not None
        assert second_url is not None
        assert first_url.group(1) == second_url.group(1)
        assert source not in first_html

        matched = match_route(c.urls, first_url.group(1).removeprefix("/citry/"))
        assert matched is not None
        response = matched.route.handler(None, **matched.params)
        assert response.status == 200
        assert response.content == source
        assert response.content_type == "text/javascript"

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
        assert script_url(widget, "js") in marked_js
        assert f"/citry/cache/{widget.class_id}.{record.js_vars_hash}.js" in marked_js
        assert script_url(widget, "css") in marked_css

    def test_content_only_mounted_page_still_marks_its_assets(self):
        # A mounted page with component CSS but NO $component must still ship
        # the runtime and a markLoaded manifest naming its cache URLs, so a
        # fragment inserted later dedups against them instead of re-fetching
        # (otherwise the shared component's CSS lands on the page twice).
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<span>card</span>"
            css = ".card { color: teal; }"

        page = type("Page", (Component,), {"citry": c, "template": "<main><c-card /></main>"})
        html = str(page())
        assert '<script src="/citry/citry.js"></script>' in html  # runtime shipped
        manifest = _manifest(html)
        marked_css = [_unb64(url) for url in manifest["markLoaded"]["css"]]
        assert script_url(Card, "css") in marked_css
        assert manifest["calls"] == []  # no per-instance JS to run

    def test_component_less_mounted_page_stays_lean(self):
        # Leanness guard: a mounted page whose components carry no assets has
        # nothing for a fragment to dedup against, so it ships no runtime and no
        # manifest.
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Bare(Component):
            citry = c
            template = "<span>bare</span>"

        page = type("Page", (Component,), {"citry": c, "template": "<main><c-bare /></main>"})
        html = str(page())
        assert "citry.js" not in html
        assert "data-citry" not in html
