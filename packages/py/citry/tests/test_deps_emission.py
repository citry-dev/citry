"""Tests for dependency emission: collection during render, ``<c-js>``/``<c-css>``, strategies, placement."""

import pytest

from citry import Citry, Component, Extension, InMemoryCache, Markup
from citry._inline_assets import normalize_inline_asset
from citry.ext.dependencies import Script, Style
from citry.ext.dependencies.scripts import (
    component_script_hash,
    gen_cache_key,
    gen_component_cache_key,
    get_component_script,
)

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
        # The Component.css sheet carries its class marker, which is how the
        # client-side manager's cleanup finds the sheet (dependencies.md 8.4).
        assert f'<style data-citry-css-class="{page.class_id}">.x {{ color: red; }}</style></head>' in html
        assert "<script>(function() {\nconsole.log(1);\n})();</script></body>" in html

    def test_component_without_assets_renders_unchanged(self):
        c = Citry()
        page = _page(c)
        assert str(page()) == '<html data-cid-c1=""><head><title>t</title></head><body><p>hi</p></body></html>'

    @pytest.mark.parametrize("asset_kind", ["js", "css"])
    @pytest.mark.parametrize("mounted", [False, True], ids=["unmounted", "mounted"])
    def test_whitespace_only_component_assets_are_absent(self, asset_kind, mounted):
        c = Citry()
        if mounted:
            c.set_mounted_prefix("/citry")
        blank_asset = """
            \x20\t
        """
        blank = type(
            "Blank",
            (Component,),
            {
                "citry": c,
                "template": """
                    <p>blank</p>
                """,
                asset_kind: blank_asset,
            },
        )

        rendered = blank().render()
        assert not rendered.context.extra.get("dependencies")
        document = rendered.serialize()
        fragment = rendered.serialize(deps_strategy="fragment")

        assert fragment == document
        assert "<p" in document
        for html in (document, fragment):
            assert "<script" not in html
            assert "<style" not in html
            assert "/cache/" not in html
            assert "data-citry" not in html

    def test_child_component_deps_bubble_to_the_page(self):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log('widget');"
            css = ".w {}"

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        html = str(page())
        assert f'<style data-citry-css-class="{Widget.class_id}">.w {{}}</style></head>' in html
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
        from citry.ext.dependencies import emission
        from citry.ext.dependencies.types import DependencyRecord

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

    def test_nested_components_dedupe_and_keep_first_seen_order(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<span>inner</span>"
            js = "console.log('inner');"
            css = ".inner {}"

        class Other(Component):
            citry = c
            template = "<b>other</b>"
            js = "console.log('other');"
            css = ".other {}"

        class Outer(Component):
            citry = c
            template = "<div><c-inner /><c-other /><c-inner /></div>"  # Inner rendered twice
            css = ".outer {}"

        page = _page(c, template="<html><head></head><body><c-outer /></body></html>")
        html = str(page())
        # Each class-level asset appears once, even though Inner renders twice.
        assert html.count(".inner {}") == 1
        assert html.count(".other {}") == 1
        assert html.count("console.log('inner');") == 1
        # First-seen document order: Inner is reached before Other.
        assert html.index(".inner {}") < html.index(".other {}")
        # `simple` and `document` agree for a tree with no client-side calls.
        rendered = page().render()
        assert rendered.serialize(deps_strategy="simple") == rendered.serialize(deps_strategy="document")

    def test_nested_url_dependencies_emit_once_in_first_seen_order(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<span>inner</span>"
            js = "window.__innerComponent = true;"
            css = ".inner-component {}"

            class Dependencies:
                js = ["/static/shared.js", "/static/inner.js"]
                css = ["/static/shared.css", "/static/inner.css"]

        class Other(Component):
            citry = c
            template = "<b>other</b>"
            js = "window.__otherComponent = true;"
            css = ".other-component {}"

            class Dependencies:
                js = ["/static/other.js", "/static/shared.js"]
                css = ["/static/other.css", "/static/shared.css"]

        class Outer(Component):
            citry = c
            template = "<main><c-inner /><c-other /></main>"
            js = "window.__outerComponent = true;"
            css = ".outer-component {}"

            class Dependencies:
                js = ["/static/outer.js", "/static/shared.js"]
                css = ["/static/outer.css", "/static/shared.css"]

        page = _page(c, template="<html><head></head><body><c-outer /></body></html>")
        html = str(page())

        js_urls = ["outer.js", "shared.js", "inner.js", "other.js"]
        css_urls = ["outer.css", "shared.css", "inner.css", "other.css"]
        assert [html.index(f"/static/{name}") for name in js_urls] == sorted(
            html.index(f"/static/{name}") for name in js_urls
        )
        assert [html.index(f"/static/{name}") for name in css_urls] == sorted(
            html.index(f"/static/{name}") for name in css_urls
        )
        assert all(html.count(f"/static/{name}") == 1 for name in [*js_urls, *css_urls])

        # All ``Dependencies`` entries precede all Component.js/css entries;
        # component assets then retain first-seen parent/child/sibling order.
        assert html.index("other.js") < html.index("__outerComponent")
        assert html.index("__outerComponent") < html.index("__innerComponent") < html.index("__otherComponent")
        assert html.index("other.css") < html.index(".outer-component")
        assert html.index(".outer-component") < html.index(".inner-component") < html.index(".other-component")


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
            f'<html data-cid-c1=""><head><style data-citry-css-class="{page.class_id}">.x {{}}</style></head>'
            "<body><p>hi</p><script>(function() {\nconsole.log(1);\n})();</script></body></html>"
        )

    @pytest.mark.parametrize(
        "template",
        [
            "<html><head><c-css /></head><body><p>hi</p></body></html>",
            "<html><head></head><body><p>hi</p><c-js /></body></html>",
        ],
        ids=["css-placeholder-only", "js-placeholder-only"],
    )
    def test_one_placeholder_does_not_suppress_the_other_asset_kind(self, template):
        c = Citry()
        page = _page(c, js="console.log(1);", css=".x {}", template=template)

        assert str(page()) == (
            f'<html data-cid-c1=""><head><style data-citry-css-class="{page.class_id}">.x {{}}</style></head>'
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
        style_tag = f'<style data-citry-css-class="{page.class_id}">.x {{}}</style>'
        assert html.count(style_tag) == 1
        assert style_tag + "</head>" in html
        assert "<body></body>" in html

    def test_placeholders_removed_even_without_deps(self):
        c = Citry()
        page = _page(c, template="<html><head><c-css /></head><body><c-js /></body></html>")
        html = str(page())
        assert "template" not in html
        assert "<head></head>" in html

    def test_registered_but_unrendered_components_emit_no_assets(self):
        c = Citry()

        class UnusedOne(Component):
            citry = c
            js = "window.__unusedOne = true;"
            css = ".unused-one {}"

            class Dependencies:
                js = ["/static/unused-one.js"]
                css = ["/static/unused-one.css"]

        class UnusedTwo(Component):
            citry = c
            js = "window.__unusedTwo = true;"
            css = ".unused-two {}"

            class Dependencies:
                js = ["/static/unused-two.js"]
                css = ["/static/unused-two.css"]

        page = _page(c, template="<html><head><c-css /></head><body><c-js /></body></html>")
        html = str(page())

        assert html == '<html data-cid-c1=""><head></head><body></body></html>'
        assert "unused" not in html

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
        assert html.startswith(f'<style data-citry-css-class="{page.class_id}">.x {{}}</style>')
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
        tag = Markup('<script type="speculationrules">{}</script>')

        class Deps:
            js = [tag]

        page = _page(c, deps=Deps)
        assert '<script type="speculationrules">{}</script>' in str(page())

    @pytest.mark.parametrize(
        "tag",
        [
            Markup('<link href="safe.css" rel="stylesheet">'),
            type(
                "HtmlTag",
                (),
                {"__html__": lambda _self: '<style data-source="object">.object {}</style>'},
            )(),
        ],
        ids=["string-subclass", "object"],
    )
    def test_prerendered_css_forms_emit_verbatim(self, tag):
        c = Citry()

        class Deps:
            css = [tag]

        page = _page(c, deps=Deps)
        assert str(tag.__html__()) in str(page())

    @pytest.mark.parametrize(
        ("attr", "entry", "match"),
        [
            ("js", Style(content=".wrong {}"), r"Dependencies\.js of Page contains a Style entry"),
            ("css", Script(content="wrong();"), r"Dependencies\.css of Page contains a Script entry"),
        ],
    )
    def test_cross_kind_entries_raise_with_guidance(self, attr, entry, match):
        c = Citry()
        deps = type("Deps", (), {attr: [entry]})
        page = _page(c, deps=deps)

        with pytest.raises(TypeError, match=match):
            str(page())

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

    def test_returning_none_keeps_the_component_assets(self):
        # The hook returns None (the default) to mean "no change": the
        # component's own js and css must survive untouched.
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log('kept');"
            css = ".kept {}"

            @classmethod
            def on_dependencies(cls, scripts, styles):
                return None

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        html = str(page())
        assert "console.log('kept');" in html
        assert f'<style data-citry-css-class="{Widget.class_id}">.kept {{}}</style>' in html

    def test_component_classmethod_can_add_an_extra_entry(self):
        # Returning the lists with an extra ``kind="extra"`` Script/Style adds
        # them to the page; a ``wrap=False`` script renders unwrapped.
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = "console.log('own');"
            css = ".own {}"

            @classmethod
            def on_dependencies(cls, scripts, styles):
                extra_js = Script(content="console.log('hook');", wrap=False)
                extra_css = Style(content=".hook {}")
                return [*scripts, extra_js], [*styles, extra_css]

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        html = str(page())
        # The component's own assets survive.
        assert "console.log('own');" in html
        assert f'<style data-citry-css-class="{Widget.class_id}">.own {{}}</style>' in html
        # The extras are emitted; the wrap=False script is not wrapped. An
        # extra Style added by the hook is not a Component.css sheet, so it
        # carries no class marker.
        assert "<script>console.log('hook');</script>" in html
        assert "<style>.hook {}</style>" in html


class TestComponentAssetEndTagGuard:
    """A component's inline JS/CSS may not contain its own closing tag."""

    # ``</script>`` inside JS (or ``</style>`` inside CSS) would terminate the
    # inlined tag early in the browser, so emission refuses it and names the
    # offending component. django-components raised RuntimeError here; citry
    # raises ValueError with a different message (divergence #5 in
    # docs/design/migration_djc_tests.md).

    @pytest.mark.parametrize("closing_tag", ["</script>", "</ScRiPt>"])
    def test_component_js_containing_its_end_tag_raises(self, closing_tag):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            js = f"""
                console.log({closing_tag!r});
            """

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        with pytest.raises(ValueError, match=r"contains a '</script>' end tag") as excinfo:
            str(page())
        # The error names the offending component so the author can find it.
        assert Widget.class_id in str(excinfo.value)

    @pytest.mark.parametrize("closing_tag", ["</style>", "</STYLE>"])
    def test_component_css_containing_its_end_tag_raises(self, closing_tag):
        c = Citry()

        class Widget(Component):
            citry = c
            template = "<span>w</span>"
            css = f"""
                /* {closing_tag} */
            """

        page = _page(c, template="<html><head></head><body><c-widget /></body></html>")
        with pytest.raises(ValueError, match=r"contains a '</style>' end tag") as excinfo:
            str(page())
        assert Widget.class_id in str(excinfo.value)


class TestScriptCacheLifecycle:
    def test_class_assets_are_derived_once_per_exact_class(self, monkeypatch):
        from citry.ext.dependencies import scripts

        calls = {"js": 0, "css": 0}
        original = scripts._component_content

        def counting_content(script_type, comp_cls):
            calls[script_type] += 1
            return original(script_type, comp_cls)

        monkeypatch.setattr(scripts, "_component_content", counting_content)
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>card</p>"
            js = "$component(() => {});"
            css = ".card { color: red; }"

        for _ in range(10):
            str(Card())

        assert calls == {"js": 1, "css": 1}

    @pytest.mark.parametrize("script_type", ["js", "css"])
    def test_class_capture_repairs_evicted_shared_cache(self, script_type):
        c = Citry()

        class Card(Component):
            citry = c
            js = "console.log('card');"
            css = ".card { color: red; }"

        expected = get_component_script(script_type, Card)
        content_hash = component_script_hash(script_type, Card)
        assert expected is not None
        assert content_hash is not None

        stable_key = gen_cache_key(Card.class_id, script_type)
        versioned_key = gen_component_cache_key(Card.class_id, script_type, content_hash)
        c.cache.delete(stable_key)
        c.cache.delete(versioned_key)

        repaired = get_component_script(script_type, Card)

        assert repaired == expected
        assert c.cache.has(stable_key)
        assert c.cache.has(versioned_key)

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

    def test_replacement_class_with_same_id_uses_its_own_js_and_css(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
            <p>old</p>
            """
            js = """
            console.log("old");
            """
            css = """
            .old { color: red; }
            """

        str(Card())
        class_id = Card.class_id
        assert get_component_script("js", Card).content == normalize_inline_asset(Card.js)
        assert get_component_script("css", Card).content == normalize_inline_asset(Card.css)

        c.unregister(Card)

        class Card(Component):
            citry = c
            template = """
            <p>new</p>
            """
            js = """
            console.log("new");
            """
            css = """
            .new { color: blue; }
            """

        assert Card.class_id == class_id
        str(Card())
        assert get_component_script("js", Card).content == normalize_inline_asset(Card.js)
        assert get_component_script("css", Card).content == normalize_inline_asset(Card.css)

    def test_retired_class_cannot_poison_same_id_assets_in_shared_cache(self):
        cache = InMemoryCache()
        old_citry = Citry(cache=cache)
        new_citry = Citry(cache=cache)

        def make_card(engine, label):
            class Card(Component):
                citry = engine
                js = f'console.log("{label}");'
                css = f".{label} {{ color: red; }}"

            return Card

        old_card = make_card(old_citry, "old")
        assert get_component_script("js", old_card).content == old_card.js
        assert get_component_script("css", old_card).content == old_card.css
        old_citry.unregister(old_card)

        # A plugin can retain its old class and use it after unregistering.
        # That must not make a replacement with the same deterministic ID
        # trust the old payload, including when processes share a backend.
        assert get_component_script("js", old_card).content == old_card.js
        assert get_component_script("css", old_card).content == old_card.css

        new_card = make_card(new_citry, "new")
        assert new_card.class_id == old_card.class_id
        assert get_component_script("js", new_card).content == new_card.js
        assert get_component_script("css", new_card).content == new_card.css

        # Old and new workers may alternate during a rolling deployment. Each
        # lookup must return the payload belonging to its own class version.
        assert get_component_script("js", old_card).content == old_card.js
        assert get_component_script("js", new_card).content == new_card.js
        assert get_component_script("css", old_card).content == old_card.css
        assert get_component_script("css", new_card).content == new_card.css

    def test_delayed_serialization_uses_the_rendering_class_version(self):
        c = Citry()

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

        html = old_render.serialize()

        assert ">old</p>" in html
        assert old_card.js in html
        assert old_card.css in html
        assert new_card.js not in html
        assert new_card.css not in html

    def test_removing_one_alias_keeps_the_registered_class_scripts(self):
        c = Citry()

        class MyCard(Component):
            citry = c
            template = """
            <p>card</p>
            """
            js = """
            console.log("card");
            """
            css = """
            .card { color: red; }
            """

        str(MyCard())
        js_key = gen_cache_key(MyCard.class_id, "js")
        css_key = gen_cache_key(MyCard.class_id, "css")
        assert c.cache.has(js_key)
        assert c.cache.has(css_key)

        c.unregister("mycard")

        assert c.get("my-card") is MyCard
        assert c.cache.has(js_key)
        assert c.cache.has(css_key)

    def test_rejected_foreign_registration_does_not_touch_either_script_cache(self):
        source = Citry()
        target = Citry()

        class Card(Component):
            citry = source
            js = "console.log('card');"
            css = ".card {}"

        assert get_component_script("js", Card).content == normalize_inline_asset(Card.js)
        assert get_component_script("css", Card).content == normalize_inline_asset(Card.css)
        js_key = gen_cache_key(Card.class_id, "js")
        css_key = gen_cache_key(Card.class_id, "css")
        target.cache.set(js_key, "target js")
        target.cache.set(css_key, "target css")

        with pytest.raises(ValueError, match="only be registered with its owning Citry instance"):
            target.register(Card, "foreign-card")

        assert source.cache.has(js_key)
        assert source.cache.has(css_key)
        assert target.cache.get(js_key) == "target js"
        assert target.cache.get(css_key) == "target css"

    def test_component_without_assets_writes_no_cache_entries(self):
        c = Citry()

        class Plain(Component):
            citry = c
            template = """
            <span>plain</span>
            """

        class Styled(Component):
            citry = c
            template = """
            <span>styled</span>
            """
            js = """
            console.log("styled");
            """
            css = """
            .styled { color: red; }
            """

        page = _page(c, template="<html><head></head><body><c-plain /><c-styled /></body></html>")
        str(page())

        # Only components that carry assets reach the cache; a markup-only
        # component leaves no empty entries in a user's shared store.
        assert c.cache.has(gen_cache_key(Styled.class_id, "js"))
        assert c.cache.has(gen_cache_key(Styled.class_id, "css"))
        assert not c.cache.has(gen_cache_key(Plain.class_id, "js"))
        assert not c.cache.has(gen_cache_key(Plain.class_id, "css"))
