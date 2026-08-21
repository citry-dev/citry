"""
Tests for the rendered output of the ``#c-*`` framework-metadata channel.

On a plain element, ``#c-key="expr"`` renders as the element-only
``data-citry-key=":<evaluated key>"`` attribute. On a component tag, metadata
lives on the comment-delimited virtual component range and never becomes a
root attribute. Element ``#c-ignore`` renders as
``data-citry-morph="ignore"``; component ``#c-ignore`` becomes graph
``morphMode`` metadata.
The plain ``key`` attribute and the ``key`` / ``c-key`` component inputs stay
completely ordinary. See
docs/design/component_ranges_plan.md; the parse-time rules are covered
by the Rust suite (``tag_parser_meta_attrs.rs``).

Render ids are made deterministic per test by the autouse fixture in
conftest.py (``c1``, ``c2``, ... in render order).
"""

import json

import pytest

from citry import Citry, Component
from citry.constness import Const


def _manifest_of(html: str) -> dict:
    marker = '<script type="application/json" data-citry-graph>'
    return json.loads(html.split(marker, 1)[1].split("</script>", 1)[0])


def _markup_of(html: str) -> str:
    return html.split("<script", 1)[0]


class TestElementKey:
    def test_key_on_plain_element(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="ident">x</div>'

            def template_data(self, kwargs, slots):
                return {"ident": kwargs["ident"]}

        assert Page(ident=7).render().serialize() == '<div data-citry-key=":7" data-cid-c1="">x</div>'

    def test_key_inside_c_for_evaluates_per_item(self):
        c = Citry()

        class KeyedList(Component):
            citry = c
            template = '<ul><c-for each="item in items"><li #c-key="item">x</li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        assert (
            KeyedList(items=[1, 2]).render().serialize()
            == '<ul data-cid-c1=""><li data-citry-key=":1">x</li><li data-citry-key=":2">x</li></ul>'
        )

    def test_key_value_is_html_escaped(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="raw">x</div>'

            def template_data(self, kwargs, slots):
                return {"raw": "a<b>&c"}

        assert Page().render().serialize() == '<div data-citry-key=":a&lt;b&gt;&amp;c" data-cid-c1="">x</div>'

    def test_none_key_omits_element_key(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="missing">x</div>'

            def template_data(self, kwargs, slots):
                return {"missing": None}

        assert Page().render().serialize() == '<div data-cid-c1="">x</div>'

    @pytest.mark.parametrize(
        ("value", "rendered"),
        [
            (False, "False"),
            (0, "0"),
            ("", ""),
        ],
    )
    def test_non_none_falsy_element_key_is_preserved(self, value, rendered):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="key">x</div>'

            def template_data(self, kwargs, slots):
                return {"key": kwargs["key"]}

        assert Page(key=value).render().serialize() == (f'<div data-citry-key=":{rendered}" data-cid-c1="">x</div>')

    def test_optional_keys_inside_c_for_omit_only_none(self):
        c = Citry()

        class KeyedList(Component):
            citry = c
            template = '<ul><c-for each="item in items"><li #c-key="item">x</li></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        assert KeyedList(items=[None, False, 0, ""]).render().serialize() == (
            '<ul data-cid-c1=""><li>x</li><li data-citry-key=":False">x</li>'
            '<li data-citry-key=":0">x</li><li data-citry-key=":">x</li></ul>'
        )

    def test_none_element_key_survives_const_precomputation(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="key">x</div>'

            def template_data(self, kwargs, slots):
                return {"key": Const(None)}

        assert Page().render().serialize() == '<div data-cid-c1="">x</div>'
        assert Page().render().serialize() == '<div data-cid-c2="">x</div>'


class TestElementIgnore:
    def test_ignore_renders_morph_marker(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = "<div><p #c-ignore>chart</p></div>"

        assert Page().render().serialize() == '<div data-cid-c1=""><p data-citry-morph="ignore">chart</p></div>'


class TestComponentKey:
    def test_single_root_child_key_lives_on_the_invocation_range(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>{{ label }}</span>"

            def template_data(self, kwargs, slots):
                return {"label": kwargs.get("label", "?")}

        class Parent(Component):
            citry = c
            template = '<div><c-Row #c-key="1" c-label="\'one\'" /></div>'

        rendered = Parent().render()
        assert rendered.context.ownership.snapshot().component_invocations[0].morph_key == "1"
        html = rendered.serialize()
        assert "data-citry-key" not in _markup_of(html)
        assert _manifest_of(html)["graphs"][0]["nestedComponents"][0]["morphKey"] == "1"

    def test_multi_root_child_uses_one_keyed_range_without_root_stamps(self):
        c = Citry()

        class TwoRoots(Component):
            citry = c
            template = "<div>a</div><p>b</p>"

        class Parent(Component):
            citry = c
            template = "<section><c-TwoRoots #c-key=\"'k1'\" /></section>"

        html = Parent().render().serialize()
        assert "data-citry-key" not in _markup_of(html)
        manifest = _manifest_of(html)
        invocation = manifest["graphs"][0]["nestedComponents"][0]
        assert invocation["morphKey"] == "k1"
        child = next(item for item in manifest["graphs"][0]["componentInstances"] if item["instanceId"] == 2)
        prefix = f"citry:g1:{manifest['revision'][:8]}:0:i:{child['instanceId']}"
        assert html.count(f"<!--{prefix}:s-->") == 1
        assert html.count(f"<!--{prefix}:e-->") == 1

    def test_keyed_children_inside_c_for(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>{{ label }}</span>"

            def template_data(self, kwargs, slots):
                return {"label": kwargs.get("label", "?")}

        class Parent(Component):
            citry = c
            template = '<ul><c-for each="item in items"><c-Row #c-key="item" c-label="item" /></c-for></ul>'

            def template_data(self, kwargs, slots):
                return {"items": kwargs["items"]}

        html = Parent(items=["a", "b"]).render().serialize()
        assert "data-citry-key" not in _markup_of(html)
        assert [item["morphKey"] for item in _manifest_of(html)["graphs"][0]["nestedComponents"]] == ["a", "b"]

    def test_component_key_is_exact_graph_data_and_script_safe(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="raw" /></section>'

            def template_data(self, kwargs, slots):
                return {"raw": '</script><x>&"π'}

        html = Parent().render().serialize()
        graph_text = html.split('<script type="application/json" data-citry-graph>', 1)[1].split("</script>", 1)[0]
        assert "<" not in graph_text
        assert _manifest_of(html)["graphs"][0]["nestedComponents"][0]["morphKey"] == '</script><x>&"π'

    def test_none_key_omits_component_key(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="key" /></section>'

            def template_data(self, kwargs, slots):
                return {"key": None}

        rendered = Parent().render()
        assert rendered.context.ownership.snapshot().component_invocations[0].morph_key is None
        assert rendered.serialize() == '<section data-cid-c1=""><span data-cid-c2="">x</span></section>'

    @pytest.mark.parametrize(
        ("value", "rendered"),
        [
            (False, "False"),
            (0, "0"),
            ("", ""),
        ],
    )
    def test_non_none_falsy_component_key_is_preserved(self, value, rendered):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="key" /></section>'

            def template_data(self, kwargs, slots):
                return {"key": kwargs["key"]}

        component_render = Parent(key=value).render()
        assert component_render.context.ownership.snapshot().component_invocations[0].morph_key == rendered
        html = component_render.serialize()
        assert "data-citry-key" not in _markup_of(html)
        assert _manifest_of(html)["graphs"][0]["nestedComponents"][0]["morphKey"] == rendered

    def test_key_survives_the_const_body_cache(self):
        # A keyed component whose body precomputes (a Const variable) is
        # rebuilt by the const optimization; the key must ride along, on the
        # first render and on a cache-hit render alike.
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = "<div><c-Row #c-key=\"'k'\">{{ label }}</c-Row></div>"

            def template_data(self, kwargs, slots):
                return {"label": Const("hi")}

        for _ in range(2):
            html = Parent().render().serialize()
            assert "data-citry-key" not in _markup_of(html)
            assert _manifest_of(html)["graphs"][0]["nestedComponents"][0]["morphKey"] == "k"

    def test_key_on_transparent_component_uses_its_virtual_range(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-provide key="theme" c-data="{}" #c-key="\'p\'">x</c-provide>'

        html = Page().render().serialize()
        manifest = _manifest_of(html)
        invocation = manifest["graphs"][0]["nestedComponents"][0]
        assert invocation["morphKey"] == "p"
        target = next(
            item
            for item in manifest["graphs"][0]["componentInstances"]
            if item["renderId"] == invocation["targetRenderId"]
        )
        assert target["transparent"] is True
        assert "data-citry-key" not in _markup_of(html)

    def test_key_on_dynamic_component_belongs_to_the_selected_target_range(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-component c-is="target" #c-key="\'k\'" />'

            def template_data(self, kwargs, slots):
                return {"target": Row}

        html = Page().render().serialize()
        invocation = _manifest_of(html)["graphs"][0]["nestedComponents"][0]
        assert invocation["tagName"] == "component"
        assert invocation["targetClassId"] == Row.class_id
        assert invocation["morphKey"] == "k"
        assert "data-citry-key" not in _markup_of(html)

    def test_component_and_its_root_element_have_independent_keys(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span #c-key=\"'own'\">x</span>"

        class Page(Component):
            citry = c
            template = "<c-Row #c-key=\"'component'\" />"

        html = Page().render().serialize()
        assert html.count('data-citry-key=":own"') == 1
        assert f'data-citry-key="{Row.class_id}:component"' not in html
        assert _manifest_of(html)["graphs"][0]["nestedComponents"][0]["morphKey"] == "component"

    def test_empty_component_can_be_keyed(self):
        c = Citry()

        class Blank(Component):
            citry = c
            template = ""

        class Page(Component):
            citry = c
            template = "<main>before<c-Blank #c-key=\"'empty'\" />after</main>"

        html = Page().render().serialize()
        manifest = _manifest_of(html)
        assert manifest["graphs"][0]["nestedComponents"][0]["morphKey"] == "empty"
        assert "before<!--citry:g1:" in html
        assert ":e-->after" in html


class TestComponentIgnore:
    def test_source_range_ignore_reaches_ownership_and_the_manifest(self):
        c = Citry()

        class Child(Component):
            citry = c
            template = "<span>child</span>"

        class Page(Component):
            citry = c
            template = "<c-child #c-ignore />"

        rendered = Page().render()
        invocation = rendered.context.ownership.snapshot().component_invocations[0]
        assert invocation.morph_key is None
        assert invocation.morph_mode == "ignore"

        html = rendered.serialize()
        assert "data-citry-morph" not in _markup_of(html)
        assert _manifest_of(html)["graphs"][0]["nestedComponents"][0]["morphMode"] == "ignore"


class TestTemplateAuthoredOnly:
    def test_key_via_element_spread_is_render_error(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": "5"}}

        with pytest.raises(
            RuntimeError,
            match=r"'#c-key' arrived on <div> through an attribute spread or a dynamic attribute\. "
            r"'#c-\*' framework attributes are template-authored only: "
            r"write the attribute directly on the tag in the template\.",
        ):
            Page().render().serialize()

    def test_key_via_component_spread_is_render_error(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-Row c-bind="attrs" />'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": "5"}}

        with pytest.raises(
            RuntimeError,
            match=r"'#c-key' arrived on <c-row> through an attribute spread or a dynamic attribute\. "
            r"'#c-\*' framework attributes are template-authored only: "
            r"write the attribute directly on the component tag in the template\.",
        ):
            Page().render().serialize()

    def test_none_key_via_element_spread_is_still_render_error(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": None}}

        with pytest.raises(RuntimeError, match=r"'#c-key' arrived on <div> through an attribute spread"):
            Page().render().serialize()

    def test_none_key_via_component_spread_is_still_render_error(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-Row c-bind="attrs" />'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-key": None}}

        with pytest.raises(RuntimeError, match=r"'#c-key' arrived on <c-row> through an attribute spread"):
            Page().render().serialize()

    def test_ignore_via_spread_is_render_error(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div c-bind="attrs">x</div>'

            def template_data(self, kwargs, slots):
                return {"attrs": {"#c-ignore": True}}

        with pytest.raises(RuntimeError, match=r"'#c-ignore' arrived on <div>"):
            Page().render().serialize()


class TestChannelErrorsSurfaceAtTemplateLoad:
    # The parse-time rules live in the Rust suite; these two lock that the
    # errors surface through Python template loading with their message.
    def test_ignore_on_reserved_structural_tag(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-if cond="True" #c-ignore>x</c-if>'

        # The message carries the attribute's real template location.
        with pytest.raises(
            SyntaxError,
            match=r"'#c-ignore' is not supported on '<c-if>' \(line 1, column 19\)",
        ):
            Page().render().serialize()

    def test_unknown_meta_name(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-frobnicate="1">x</div>'

        with pytest.raises(
            SyntaxError,
            match=r"Unknown '#c-\*' attribute '#c-frobnicate'.*'#c-key' and '#c-ignore'",
        ):
            Page().render().serialize()


class TestOrdinaryKeyStaysOrdinary:
    # The channel reserves nothing outside its `#c-` prefix: the plain `key`
    # HTML attribute and the `key` / `c-key` component inputs behave exactly
    # as before.
    def test_plain_key_attribute_on_elements(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = '<input key="" /><input key="v" />'

        # `key=""` normalizes to the boolean attribute, `key="v"` passes through.
        assert Page().render().serialize() == '<input key data-cid-c1=""/><input key="v" data-cid-c1=""/>'

    def test_key_and_c_key_component_inputs(self):
        c = Citry()

        class Guarded(Component):
            citry = c
            template = "<i>{{ key }}</i>"

            def template_data(self, kwargs, slots):
                return {"key": kwargs.get("key")}

        class StaticPage(Component):
            citry = c
            template = '<c-Guarded key="plain" />'

        class DynamicPage(Component):
            citry = c
            template = '<c-Guarded c-key="1 + 1" />'

        assert StaticPage().render().serialize() == '<i data-cid-c2="" data-cid-c1="">plain</i>'
        assert DynamicPage().render().serialize() == '<i data-cid-c4="" data-cid-c3="">2</i>'
