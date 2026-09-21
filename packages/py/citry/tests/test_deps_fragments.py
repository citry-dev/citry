"""Tests for the ``fragment`` strategy and the mounted ``document`` flow."""

import json
import re

import pytest

from citry import Citry, Component, Extension, Markup
from citry.ext.dependencies import Script
from citry.ext.dependencies.routes import script_url
from citry.util.routing import match_route


def _vue_manifest(html):
    match = re.search(r'<script type="application/json" data-citry-vue-fragment>(.*?)</script>', html, re.DOTALL)
    assert match is not None, "no Vue fragment manifest in output"
    return json.loads(match.group(1))["vue"]["prepared"]["manifest"]


def _widget(c):
    class Widget(Component):
        citry = c
        template = "<span>w</span>"
        js = "$component({ onServerRender({ component }) { component.$el.textContent = component.rows; } });"
        css = ".w { color: var(--row-color); }"

        def js_data(self, kwargs, slots):
            return {"rows": 3}

        def css_data(self, kwargs, slots):
            return {"row-color": "red"}

    return Widget


class TestFragmentStrategy:
    def test_static_css_fragment_emits_stylesheet_without_runtime_manifest(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Summary(Component):
            citry = c
            template = '<section class="summary">summary</section>'
            css = ".summary { border-width: 3px; }"

        html = Summary().render().serialize(deps_strategy="fragment")

        assert script_url(Summary, "css") in html
        assert 'rel="stylesheet"' in html
        assert "data-citry-vue-fragment" not in html
        assert 'type="application/json" data-citry' not in html
        assert "citry.js" not in html

    def test_static_css_document_emits_stylesheet_without_runtime_manifest(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Summary(Component):
            citry = c
            template = '<section class="summary">summary</section>'
            css = ".summary { border-width: 3px; }"

        html = Summary().render().serialize()

        assert script_url(Summary, "css") in html
        assert "<style data-citry-css-class=" in html
        assert "citry.js" not in html
        assert 'type="application/json" data-citry' not in html

    def test_static_fragment_emits_dependency_scripts_in_declared_order(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Summary(Component):
            citry = c
            template = "<section>summary</section>"

            class Dependencies:
                js = [Script(content="window.first = true;"), Script(url="/static/second.js")]

        html = Summary().render().serialize(deps_strategy="fragment")

        assert html.index("window.first = true") < html.index("/static/second.js")
        assert "data-citry-vue-fragment" not in html
        assert 'type="application/json" data-citry' not in html
        assert "citry.js" not in html

    def test_fragment_carries_urls_not_content(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        widget = _widget(c)

        rendered = widget().render()
        html = rendered.serialize(deps_strategy="fragment")

        # A Vue fragment carries one structured native descriptor. Nothing is
        # inlined before the fragment manager accepts it.
        assert "registerComponentData(" not in html
        assert ".w { color" not in html
        manifest = _vue_manifest(html)
        assert manifest["appId"]
        assert len(manifest["occurrences"]) == 1
        assert manifest["occurrences"][0]["preparedData"]["calls"] == {}
        css_urls = [
            item["source"]["attrs"]["data-citry-css-url"]
            for item in manifest["styles"]
            if "data-citry-css-url" in item["source"]["attrs"]
        ]
        assert any(url.startswith(f"/citry/cache/{widget.class_id}.") for url in css_urls)
        assert len(manifest["scripts"]) == 1
        assert len(manifest["styles"]) == 2

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
        manifest = _vue_manifest(rendered.serialize(deps_strategy="fragment"))
        class_styles = [item for item in manifest["styles"] if item["owner"].get("typeKey") == widget.class_id]
        assert len(records) == 2
        assert class_styles[0]["owner"]["occurrenceIds"] == sorted(
            item["id"] for item in manifest["occurrences"] if item["typeKey"] == widget.class_id
        )

    def test_interactive_before_manifest_script_fails_closed_before_output(self):
        class HookAssets(Extension):
            name = "hook_assets"

            def on_dependencies(self, ctx):
                ctx.before_manifest.append(Script(content="globalThis.fragmentLeaked = true;", wrap=False))

        c = Citry(extensions=[HookAssets])
        c.set_mounted_prefix("/citry")
        widget = _widget(c)
        with pytest.raises(RuntimeError, match="before_manifest is unsupported"):
            widget().render().serialize(deps_strategy="fragment")

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

        assert css_url in fragment
        matched = match_route(c.urls, css_url.removeprefix("/citry/"))
        response = matched.route.handler(None, **matched.params)
        assert response.status == 200
        assert '--accent: "red\\"; } body { outline: 99px solid red; } x { color: \\"blue";' in response.content
        assert "\nbody {" not in response.content

    def test_delayed_fragment_rejects_a_replaced_rendering_class(self):
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

        with pytest.raises(ValueError, match="component class changed before Vue metadata preparation"):
            old_render.serialize(deps_strategy="fragment")
        new_manifest = _vue_manifest(new_card().render().serialize(deps_strategy="fragment"))
        assert new_manifest["definitions"]

    def test_vue_fragment_includes_the_runtime_loader(self):
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
        assert "var H = 1;" in html
        assert "data-citry-vue-fragment" not in html

    @pytest.mark.parametrize(
        ("attr", "tag"),
        [
            ("js", Markup("<script>raw()</script>")),
            ("css", Markup("<style>.raw {}</style>")),
        ],
    )
    def test_static_fragment_emits_trusted_prerendered_entries(self, attr, tag):
        c = Citry()
        c.set_mounted_prefix("/citry")
        dependencies = type("Dependencies", (), {attr: [tag]})
        card = type(
            "Card",
            (Component,),
            {"citry": c, "template": "<p>x</p>", "Dependencies": dependencies},
        )

        html = card().render().serialize(deps_strategy="fragment")

        assert str(tag) in html
        assert "data-citry-vue-fragment" not in html
        assert 'type="application/json" data-citry' not in html

    def test_hook_created_static_fragment_dependency_is_direct(self):
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

        html = Bare().render().serialize(deps_strategy="fragment")
        assert '<script src="/hook.js"></script>' in html
        assert "citry.js" not in html

    def test_fragment_escapes_a_quoted_runtime_url(self):
        c = Citry()
        c.set_mounted_prefix('/ci"try')

        class Card(Component):
            citry = c
            template = """
                <p>card</p>
            """

            class Dependencies:
                js = ["/static/card.js"]

        html = Card().render().serialize(deps_strategy="fragment")

        assert '<script src="/static/card.js"></script>' in html
        assert "citry.js" not in html

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
        assert '<script src="/static/card.js"></script>' in fragment
        assert "stylesheet" not in fragment
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

    def test_interactive_document_starts_native_vue_after_runtime_and_options(self):
        c = Citry()
        c.set_mounted_prefix("/citry")
        _widget(c)
        page = type("Page", (Component,), {"citry": c, "template": "<main><c-widget /></main>"})

        rendered = page().render()
        html = rendered.serialize()
        assert html.index("/citry/citry.js") < html.rindex("CitryStable.startPrepared(")
        assert '"loadInitialAssets":true' in html
        assert 'type="application/json" data-citry' not in html

    def test_content_only_mounted_page_emits_css_without_runtime(self):
        c = Citry()
        c.set_mounted_prefix("/citry")

        class Card(Component):
            citry = c
            template = "<span>card</span>"
            css = ".card { color: teal; }"

        page = type("Page", (Component,), {"citry": c, "template": "<main><c-card /></main>"})
        html = str(page())
        assert '<script src="/citry/citry.js"></script>' not in html
        assert "<style data-citry-css-class=" in html
        assert 'type="application/json" data-citry' not in html

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
