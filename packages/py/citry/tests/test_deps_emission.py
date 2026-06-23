"""Tests for dependency emission: collection during render, ``<c-js>``/``<c-css>``, strategies, placement."""

import pytest

from citry import Citry, Component, Extension, Script, Style
from citry.util.html import SafeString

PAGE_TEMPLATE = "<html><head><title>t</title></head><body><p>hi</p></body></html>"


def _page(c, js=None, css=None, deps=None, template=PAGE_TEMPLATE):
    """Define a Page component with the given assets on the given Citry instance."""
    attrs = {"citry": c, "template": template, "js": js, "css": css}
    if deps is not None:
        attrs["Dependencies"] = deps
    return type("Page", (Component,), attrs)


class TestDocumentEmission:
    def test_js_and_css_land_in_default_locations(self):
        c = Citry()
        page = _page(c, js="console.log(1);", css=".x { color: red; }")

        html = str(page())
        # CSS before </head>, JS (wrapped in a self-executing function) before </body>.
        assert "<style>.x { color: red; }</style></head>" in html
        assert "<script>(function() {\nconsole.log(1);\n})();</script></body>" in html

    def test_component_without_assets_renders_unchanged(self):
        c = Citry()
        page = _page(c)
        assert str(page()) == '<html data-cid-c1=""><head><title>t</title></head><body><p>hi</p></body></html>'

    def test_child_component_deps_bubble_to_the_page(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log('widget');"
            css = ".w {}"

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        html = str(page())
        assert "<style>.w {}</style></head>" in html
        assert "console.log('widget');" in html
        assert html.index("console.log") < html.index("</body>")

    def test_same_component_rendered_twice_emits_once(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log('widget');"

        page = _page(c, template="<html><head></head><body><c-widget /><c-widget /></body></html>")
        html = str(page())
        assert html.count("console.log('widget');") == 1

    def test_resolve_records_dedupes_duplicate_records(self, monkeypatch):
        # A record bubbles up through every ancestor, so on a deeply nested page
        # the same instance's record can arrive many times. Resolution must
        # collapse duplicates first, or the per-record script lookups are
        # quadratic in tree depth (a real slowdown the large benchmark surfaced).
        from citry.extensions.dependencies import emission
        from citry.extensions.dependencies.types import DependencyRecord

        c = Citry()

        class Widget(Component):
            citry = c
            js = "console.log('w');"

        lookups = []
        real = emission.get_component_script

        def counting_lookup(script_type, comp_cls):
            lookups.append(script_type)
            return real(script_type, comp_cls)

        monkeypatch.setattr(emission, "get_component_script", counting_lookup)

        record = DependencyRecord(
            class_id=Widget.class_id, component_id="cid-1", js_vars_hash=None, css_vars_hash=None
        )
        resolved = emission._resolve_records(c, [record] * 500, with_client_js=True)

        # 500 duplicates collapse to one instance: one js + one css lookup, not 500.
        assert lookups.count("js") == 1
        assert lookups.count("css") == 1
        assert any("console.log('w');" in (s.content or "") for s in resolved.scripts)

    def test_collection_records_in_root_extra(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = ".w {}"

        page = _page(c, js="console.log(1);", template="<main><c-widget /></main>")
        rendered = page().render()
        records = rendered.context.extra["dependencies"]
        assert [r.class_id for r in records] == [page.class_id, Widget.class_id]
        assert all(r.js_vars_hash is None and r.css_vars_hash is None for r in records)


class TestPlaceholders:
    def test_c_js_and_c_css_mark_the_spots(self):
        c = Citry()
        page = _page(
            c,
            js="console.log(1);",
            css=".x {}",
            template="<html><head><c-css /></head><body><p>hi</p><c-js /></body></html>",
        )
        html = str(page())
        assert html == (
            '<html data-cid-c1=""><head><style>.x {}</style></head>'
            "<body><p>hi</p><script>(function() {\nconsole.log(1);\n})();</script></body></html>"
        )

    def test_first_placeholder_wins_later_ones_render_nothing(self):
        c = Citry()
        page = _page(
            c,
            css=".x {}",
            template="<html><head><c-css /></head><body><c-css /></body></html>",
        )
        html = str(page())
        assert html.count("<style>.x {}</style>") == 1
        assert "<style>.x {}</style></head>" in html
        assert "<body></body>" in html

    def test_placeholders_removed_even_without_deps(self):
        c = Citry()
        page = _page(c, template="<html><head><c-css /></head><body><c-js /></body></html>")
        html = str(page())
        assert "template" not in html
        assert "<head></head>" in html

    def test_c_js_rejects_attributes_and_body(self):
        c = Citry()
        bad_attrs = _page(c, template="<main><c-js foo='1' /></main>")
        with pytest.raises(ValueError, match="takes no attributes"):
            str(bad_attrs())

        c2 = Citry()
        bad_body = _page(c2, template="<main><c-js>text</c-js></main>")
        with pytest.raises(ValueError, match="takes no body"):
            str(bad_body())


class TestDefaultPlacementFallbacks:
    def test_no_head_or_body_prepends_css_and_appends_js(self):
        c = Citry()
        page = _page(c, js="console.log(1);", css=".x {}", template="<main>fragmentish</main>")
        html = str(page())
        assert html.startswith("<style>.x {}</style>")
        assert html.endswith("console.log(1);\n})();</script>")


class TestStrategiesAndPositions:
    def test_ignore_inserts_nothing_and_drops_placeholders(self):
        c = Citry()
        page = _page(
            c,
            js="console.log(1);",
            css=".x {}",
            template="<html><head><c-css /></head><body><c-js /></body></html>",
        )
        html = page().render().serialize(deps_strategy="ignore")
        assert "style" not in html
        assert "script" not in html
        assert "template" not in html

    def test_simple_matches_document_for_now(self):
        c = Citry()
        page = _page(c, css=".x {}")
        rendered = page().render()
        assert rendered.serialize(deps_strategy="simple") == rendered.serialize(deps_strategy="document")

    def test_prepend_and_append_positions(self):
        c = Citry()
        page = _page(c, js="console.log(1);", css=".x {}", template="<main>m</main>")
        prepended = page().render().serialize(deps_position="prepend")
        assert prepended.startswith("<script>")
        assert prepended.endswith("</main>")
        appended = page().render().serialize(deps_position="append")
        assert appended.startswith("<main")
        assert appended.endswith("</style>")

    def test_fragment_requires_a_mounted_integration(self):
        c = Citry()
        page = _page(c, js="console.log(1);")
        with pytest.raises(RuntimeError, match="mounted web integration"):
            page().render().serialize(deps_strategy="fragment")

    def test_fragment_without_deps_needs_no_integration(self):
        c = Citry()
        page = _page(c, template="<main>m</main>")
        assert page().render().serialize(deps_strategy="fragment") == '<main data-cid-c1="">m</main>'

    def test_invalid_values_raise(self):
        c = Citry()
        page = _page(c)
        with pytest.raises(ValueError, match="deps_strategy"):
            page().render().serialize(deps_strategy="nope")
        with pytest.raises(ValueError, match="deps_position"):
            page().render().serialize(deps_position="nope")


class TestDependenciesEntries:
    def test_url_entries_emit_src_and_href_tags(self):
        c = Citry()

        class Deps:
            js = ["https://cdn.example.com/lib.js"]
            css = {"all": ["/static/theme.css"]}

        page = _page(c, deps=Deps)
        html = str(page())
        assert '<script src="https://cdn.example.com/lib.js"></script>' in html
        assert '<link rel="stylesheet" href="/static/theme.css"/>' in html

    def test_local_files_are_inlined(self, tmp_path):
        (tmp_path / "vendor.js").write_text("var LIB = 1;")
        (tmp_path / "print.css").write_text("@page {}")
        c = Citry(dirs=[tmp_path])

        class Deps:
            js = ["vendor.js"]
            css = {"print": "print.css"}

        page = _page(c, deps=Deps)
        html = str(page())
        # Inlined unwrapped, so a vendored lib's top-level `var` stays global.
        assert "<script>var LIB = 1;</script>" in html
        assert '<style media="print">@page {}</style>' in html

    def test_script_and_style_objects_control_the_tag(self):
        c = Citry()

        class Deps:
            js = [Script(url="/cdn/chart.js", attrs={"defer": True})]
            css = {"print": Style(url="/static/p.css")}

        page = _page(c, deps=Deps)
        html = str(page())
        assert '<script defer src="/cdn/chart.js"></script>' in html
        # The media type from the Dependencies dict is stamped onto the tag.
        assert '<link media="print" rel="stylesheet" href="/static/p.css"/>' in html

    def test_prerendered_tags_emit_verbatim(self):
        c = Citry()
        tag = SafeString('<script type="speculationrules">{}</script>')

        class Deps:
            js = [tag]

        page = _page(c, deps=Deps)
        assert '<script type="speculationrules">{}</script>' in str(page())

    def test_dependencies_load_before_component_js(self):
        c = Citry()

        class Deps:
            js = ["/static/lib.js"]

        page = _page(c, js="console.log(1);", deps=Deps)
        html = str(page())
        assert html.index('src="/static/lib.js"') < html.index("console.log(1);")


class TestOnDependenciesHooks:
    def test_component_classmethod_filters_its_own_entries(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log('widget');"

            class Dependencies:
                js = ["/static/lib.js"]

            @classmethod
            def on_dependencies(cls, scripts, styles):
                kept = [s for s in scripts if s.url != "/static/lib.js"]
                return kept, styles

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        html = str(page())
        assert "/static/lib.js" not in html
        assert "console.log('widget');" in html

    def test_extension_hook_adjusts_the_final_lists(self):
        class Analytics(Extension):
            name = "analytics"

            def on_dependencies(self, ctx):
                ctx.scripts.append(Script(url="/static/analytics.js", kind="extra"))

        c = Citry(extensions=[Analytics])
        page = _page(c, js="console.log(1);")
        html = str(page())
        assert '<script src="/static/analytics.js"></script>' in html


class TestScriptCacheLifecycle:
    def test_reset_files_evicts_and_repopulates(self, tmp_path):
        (tmp_path / "card.js").write_text("console.log('one');")
        c = Citry(dirs=[tmp_path])
        page = _page(c, template="<main>m</main>")
        page.js = None
        page.js_file = "card.js"

        assert "console.log('one');" in str(page())
        # The file changes; the cached script (and loaded content) keep the
        # old version until reset.
        (tmp_path / "card.js").write_text("console.log('two');")
        assert "console.log('one');" in str(page())
        page.reset_files()
        assert "console.log('two');" in str(page())
