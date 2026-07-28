"""
Tests for the rendered output of the ``#c-*`` framework-metadata channel.

``#c-key="expr"`` renders as the composite ``data-citry-key`` attribute: on a
plain element the value is ``:<evaluated key>`` (empty scope segment), on a
component tag it is ``<child class_id>:<evaluated key>`` stamped onto every
root marker element of the child. ``#c-ignore`` renders as
``data-citry-morph="ignore"``. The plain ``key`` attribute and the ``key`` /
``c-key`` component inputs stay completely ordinary. See
docs/design/events.md sections 5.1 and 5.3; the parse-time rules are covered
by the Rust suite (``tag_parser_meta_attrs.rs``).

Render ids are made deterministic per test by the autouse fixture in
conftest.py (``c1``, ``c2``, ... in render order).
"""

import pytest

from citry import Citry, Component
from citry.constness import Const


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

    def test_none_key_renders_like_expression_output(self):
        # None stringifies to the empty string, the same rule as {{ expr }}
        # output, so both halves of the channel agree.
        c = Citry()

        class Page(Component):
            citry = c
            template = '<div #c-key="missing">x</div>'

            def template_data(self, kwargs, slots):
                return {"missing": None}

        assert Page().render().serialize() == '<div data-citry-key=":" data-cid-c1="">x</div>'


class TestElementIgnore:
    def test_ignore_renders_morph_marker(self):
        c = Citry()

        class Page(Component):
            citry = c
            template = "<div><p #c-ignore>chart</p></div>"

        assert Page().render().serialize() == '<div data-cid-c1=""><p data-citry-morph="ignore">chart</p></div>'


class TestComponentKey:
    def test_single_root_child_gets_class_scoped_key(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>{{ label }}</span>"

            def template_data(self, kwargs, slots):
                return {"label": kwargs.get("label", "?")}

        class Parent(Component):
            citry = c
            template = '<div><c-Row #c-key="1" c-label="\'one\'" /></div>'

        assert Parent().render().serialize() == (
            f'<div data-cid-c1=""><span data-cid-c2="" data-citry-key="{Row.class_id}:1">one</span></div>'
        )

    def test_multi_root_child_stamps_every_root(self):
        # A multi-root instance is one unit of continuity: all roots carry
        # the key (and the serializer's valued-marker machinery is what
        # stamps them, so this also locks that path).
        c = Citry()

        class TwoRoots(Component):
            citry = c
            template = "<div>a</div><p>b</p>"

        class Parent(Component):
            citry = c
            template = "<section><c-TwoRoots #c-key=\"'k1'\" /></section>"

        assert Parent().render().serialize() == (
            f'<section data-cid-c1=""><div data-cid-c2="" data-citry-key="{TwoRoots.class_id}:k1">a</div>'
            f'<p data-cid-c2="" data-citry-key="{TwoRoots.class_id}:k1">b</p></section>'
        )

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

        assert Parent(items=["a", "b"]).render().serialize() == (
            f'<ul data-cid-c1=""><span data-cid-c2="" data-citry-key="{Row.class_id}:a">a</span>'
            f'<span data-cid-c3="" data-citry-key="{Row.class_id}:b">b</span></ul>'
        )

    def test_component_key_value_is_html_escaped(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Parent(Component):
            citry = c
            template = '<section><c-Row #c-key="raw" /></section>'

            def template_data(self, kwargs, slots):
                return {"raw": 'a<b>&"q'}

        assert Parent().render().serialize() == (
            f'<section data-cid-c1=""><span data-cid-c2="" '
            f'data-citry-key="{Row.class_id}:a&lt;b&gt;&amp;&#34;q">x</span></section>'
        )

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

        expected_key = f'data-citry-key="{Row.class_id}:k"'
        assert expected_key in Parent().render().serialize()
        assert expected_key in Parent().render().serialize()

    def test_key_on_transparent_component_is_pointed_error(self):
        # A transparent component renders no root element, so there is
        # nowhere for the key to land; silence would break the keying.
        c = Citry()

        class Page(Component):
            citry = c
            template = '<c-provide key="theme" c-data="{}" #c-key="\'p\'">x</c-provide>'

        with pytest.raises(
            RuntimeError,
            match=r"#c-key cannot be used on <c-provide>: the component is transparent",
        ):
            Page().render().serialize()

    def test_key_on_dynamic_component_error_names_the_written_tag(self):
        # The dynamic `c-is` path resolves through the transparent
        # <c-component> builtin, whose class name is not its tag name; the
        # error must name the tag the author wrote.
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<c-component c-is="target" #c-key="\'k\'" />'

            def template_data(self, kwargs, slots):
                return {"target": Row}

        with pytest.raises(
            RuntimeError,
            match=r"#c-key cannot be used on <c-component>: the component is transparent",
        ):
            Page().render().serialize()


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
    def test_ignore_on_component_tag(self):
        c = Citry()

        class Row(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = "<c-Row #c-ignore />"

        # The message carries the attribute's real template location.
        with pytest.raises(
            SyntaxError,
            match=r"'#c-ignore' is not supported on '<c-Row>' \(line 1, column 8\)",
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
