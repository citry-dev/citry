"""
Tests for ComponentNode rendering (component_rendering.md phase 3).

A parent template references a child component; ComponentNode resolves the
attributes into the child's kwargs, looks the child up in the parent's Citry
registry, and renders it across a context boundary. Body content (slots/fills)
is a later phase.
"""

# ruff: noqa: ANN

import re

import pytest

from citry import Citry, Component, NotRegistered
from citry.nodes import ComponentNode, ExprHtmlAttr


def _component_node(metadata=None):
    return ComponentNode("<c-card />", (0, 10), (), [], (), "card", False, metadata)  # noqa: FBT003


class TestComponentNodeMetadata:
    def test_none_preserves_the_metadata_free_constructor(self):
        node = _component_node()
        assert node.metadata is None
        assert node._metadata_locus is None
        assert node.key is None
        assert node.morph_mode is None

    def test_tagged_tuple_normalizes_once_and_keeps_the_original(self):
        key = ExprHtmlAttr("<c-card />", (0, 1), "#c-key", "item", ("item",))
        metadata = ("range", ("key", key), ("morph", "ignore"))
        node = _component_node(metadata)

        assert node.metadata is metadata
        assert node._metadata_locus == "range"
        assert node.key is key
        assert node.morph_mode == "ignore"

    @pytest.mark.parametrize(
        "metadata",
        [
            ["range"],
            (),
            ("unknown",),
            ("range", "key"),
            ("range", ("unknown", "value")),
            ("range", ("key", "not-an-expression")),
            ("range", ("morph", "replace")),
            ("range", ("morph", "ignore"), ("morph", "ignore")),
            (
                "range",
                ("key", ExprHtmlAttr("", (0, 0), "#c-key", "1", ())),
                ("key", ExprHtmlAttr("", (0, 0), "#c-key", "2", ())),
            ),
        ],
    )
    def test_malformed_metadata_is_rejected(self, metadata):
        with pytest.raises(TypeError):
            _component_node(metadata)


class TestComponentNodeBasic:
    def test_renders_child_component(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>card</span>"

        class Page(Component):
            citry = c
            template = "<main><c-card /></main>"

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">card</span></main>'

    def test_name_lookup_is_case_insensitive(self):
        c = Citry()

        class MyCard(Component):
            citry = c
            template = "<span>ok</span>"

        class Page(Component):
            citry = c
            template = "<main><c-my-card /></main>"

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">ok</span></main>'

    def test_unregistered_tag_raises_not_registered_at_render(self):
        # A component tag is a registry lookup at render time: with nothing
        # registered under the name, the parent's render raises NotRegistered
        # naming the tag, and error tracing appends the template snippet with
        # the offending tag underlined.
        c = Citry()

        class Page(Component):
            citry = c
            template = '<main><c-totally-unknown-tag foo="1" /></main>'

        with pytest.raises(NotRegistered, match="No component registered as 'totally-unknown-tag'") as exc_info:
            Page().render()

        msg = exc_info.value.args[0]
        assert "In template of 'Page' (" in msg
        assert '     1 | <main><c-totally-unknown-tag foo="1" /></main>' in msg
        assert msg.endswith("\n               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")


class TestComponentNodeAttrs:
    def _card_echo(self, c, var):
        """A Card that echoes one kwarg into its template."""

        class Card(Component):
            citry = c
            template = "<span>{{ out }}</span>"

            def template_data(self, kwargs, slots):
                return {"out": kwargs.get(var)}

        return Card

    def test_static_attr_becomes_kwarg(self):
        c = Citry()
        self._card_echo(c, "title")

        class Page(Component):
            citry = c
            template = '<main><c-card title="Hi" /></main>'

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">Hi</span></main>'

    def test_static_input_is_literal_while_c_form_computes(self):
        # A plain attribute's value reaches the child verbatim, so `{{ }}`
        # written there is not interpolated. The `c-` form is what computes it.
        c = Citry()
        self._card_echo(c, "title")

        class Page(Component):
            citry = c
            template = '<main><c-card title="{{ kind }}" /><c-card c-title="kind" /></main>'

            def template_data(self, kwargs, slots):
                return {"kind": "btn"}

        assert Page().render().serialize() == (
            '<main data-cid-c1=""><span data-cid-c2="">{{ kind }}</span><span data-cid-c3="">btn</span></main>'
        )

    def test_dynamic_attr_is_evaluated(self):
        c = Citry()
        self._card_echo(c, "title")

        class Page(Component):
            citry = c
            template = '<main><c-card c-title="who" /></main>'

            def template_data(self, kwargs, slots):
                return {"who": "World"}

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">World</span></main>'

    def test_dynamic_attr_with_escaped_apostrophe_literal(self):
        c = Citry()
        self._card_echo(c, "title")

        class Page(Component):
            citry = c
            template = r"""<main><c-card c-title="'organisation\'s'" /></main>"""

        expected = '<main data-cid-c1=""><span data-cid-c2="">organisation&#39;s</span></main>'
        assert Page().render().serialize() == expected

    def test_dynamic_attr_with_escaped_double_quote_literal(self):
        c = Citry()
        self._card_echo(c, "title")

        class Page(Component):
            citry = c
            template = r"""<main><c-card c-title='"organisation\"s"' /></main>"""

        expected = '<main data-cid-c1=""><span data-cid-c2="">organisation&#34;s</span></main>'
        assert Page().render().serialize() == expected

    def test_boolean_attr_becomes_true(self):
        c = Citry()
        self._card_echo(c, "disabled")

        class Page(Component):
            citry = c
            template = "<main><c-card disabled /></main>"

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">True</span></main>'

    def test_special_character_attr_names_become_kwargs(self):
        # Kwarg names on a component tag are not limited to Python
        # identifiers: hyphenated and `#`-prefixed names land in raw_kwargs
        # under their literal spelling, and the bare `#my-id` becomes True
        # like any other bare attr. Names that are special elsewhere but not
        # to citry (HTML's `data-id`, Vue's `v-if`) pass through the same way.
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = """
                <span>x</span>
            """

            def template_data(self, kwargs, slots):
                seen.update(self.raw_kwargs)
                return {}

        class Page(Component):
            citry = c
            template = """
                <main>
                    <c-card
                        na-me="fzz"
                        data-id="123"
                        v-if="isVisible"
                        #my-id
                    />
                </main>
            """

        Page().render().serialize()
        assert seen == {"na-me": "fzz", "data-id": "123", "v-if": "isVisible", "#my-id": True}

    def test_colon_named_attr_is_a_literal_kwarg(self):
        # A colon in an attr name is not special to citry: the kwarg arrives
        # under its literal spelling "attrs:class". Migration trap when coming
        # from django-components, where `attrs:class="pad-8"` was collected
        # into a single `attrs` dict kwarg; citry does no such grouping, so a
        # leftover `attrs:`-prefixed attr silently becomes one odd-named kwarg
        # instead of erroring.
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = """
                <span>x</span>
            """

            def template_data(self, kwargs, slots):
                seen.update(self.raw_kwargs)
                return {}

        class Page(Component):
            citry = c
            template = """
                <main>
                    <c-card attrs:class="pad-8" />
                </main>
            """

        Page().render().serialize()
        assert seen == {"attrs:class": "pad-8"}

    def test_at_prefixed_attrs_are_events_not_kwargs(self):
        # `@`-prefixed attributes on a component tag are client event handler
        # directives: the events layer captures them for the browser runtime,
        # so they never become kwargs and never appear in the rendered HTML.
        # Migration trap when coming from django-components, where
        # `{% component ... @lol=2 %}` passed `@lol` through to kwargs as a
        # regular key.
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = """
                <span>x</span>
            """

            def template_data(self, kwargs, slots):
                seen.update(self.raw_kwargs)
                return {}

        class Page(Component):
            citry = c
            template = """
                <main>
                    <c-card
                        title="Hi"
                        @click="handleClick()"
                        @lol="doIt()"
                    />
                </main>
            """

        out = Page().render().serialize()
        assert seen == {"title": "Hi"}
        # The event bindings are clientBindings in the ownership manifest, where their
        # keys appear inline), not rendered HTML attributes. Strip the inert
        # JSON script blocks and confirm they never leak into the markup.
        markup = re.sub(r'<script type="application/json"[^>]*>.*?</script>', "", out, flags=re.DOTALL)
        assert "@click" not in markup
        assert "@lol" not in markup

    def test_c_bind_spreads_mapping_into_kwargs(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ a }}-{{ b }}</span>"

            def template_data(self, kwargs, slots):
                return {"a": kwargs["a"], "b": kwargs["b"]}

        class Page(Component):
            citry = c
            template = '<main><c-card c-bind="extra" /></main>'

            def template_data(self, kwargs, slots):
                return {"extra": {"a": 1, "b": 2}}

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">1-2</span></main>'

    def test_kwarg_contributions_apply_left_to_right(self):
        # On a component tag every contribution is last-one-wins in source
        # order, and `class` / `style` get no special treatment (the merging
        # that plain HTML elements do): a later c-bind overwrites an earlier
        # c-bind and an earlier explicit kwarg alike, and an explicit kwarg
        # overwrites an earlier c-bind.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ cls }}|{{ title }}|{{ note }}</span>"

            def template_data(self, kwargs, slots):
                return {"cls": kwargs["class"], "title": kwargs["title"], "note": kwargs["note"]}

        class Page(Component):
            citry = c
            template = '<main><c-card c-bind="first" class="mine" c-bind="second" title="Last" /></main>'

            def template_data(self, kwargs, slots):
                return {
                    "first": {"class": "first-cls", "title": "first-title", "note": "first-note"},
                    "second": {"class": "second-cls", "title": "second-title"},
                }

        # class="mine" is replaced outright by the later c-bind, not merged into
        # "mine second-cls"; title falls to the explicit kwarg written after the
        # last c-bind; note only ever had the one contributor.
        expected = '<main data-cid-c1=""><span data-cid-c2="">second-cls|Last|first-note</span></main>'
        assert Page().render().serialize() == expected

    def test_c_bind_none_contributes_no_kwargs(self):
        # An optional kwargs dict that is None is a no-op (no `or {}` guard
        # needed at the call site), matching the same rule on plain elements
        # and Vue's `v-bind="null"`.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ a }}</span>"

            def template_data(self, kwargs, slots):
                return {"a": kwargs.get("a", "default")}

        class Page(Component):
            citry = c
            template = '<main><c-card c-bind="extra" /></main>'

            def template_data(self, kwargs, slots):
                return {"extra": None}

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">default</span></main>'

    def test_c_bind_non_mapping_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<main><c-card c-bind="bad" /></main>'

            def template_data(self, kwargs, slots):
                return {"bad": 42}

        with pytest.raises(TypeError, match="c-bind on <card> must resolve to a mapping of kwargs"):
            Page().render().serialize()

    def test_c_bind_non_string_kwarg_name_raises(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
                <span>x</span>
            """

        class Page(Component):
            citry = c
            template = """
                <main><c-card c-bind="extra" /></main>
            """

            def template_data(self, kwargs, slots):
                return {"extra": {1: "value"}}

        with pytest.raises(TypeError, match=r"c-bind on <c-card> must use string kwarg names"):
            Page().render().serialize()

    def test_dynamic_attr_value_is_escaped_by_the_child(self):
        # The attr resolves to a raw Python value (unescaped); the child escapes
        # it when rendering it through an ExprNode.
        c = Citry()
        self._card_echo(c, "title")

        class Page(Component):
            citry = c
            template = '<main><c-card c-title="raw" /></main>'

            def template_data(self, kwargs, slots):
                return {"raw": "<b>"}

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">&lt;b&gt;</span></main>'

    def test_template_attr_becomes_rendered_kwarg(self):
        # c-body on a component is a nested template, rendered in the parent's
        # scope, passed to the child as a CitryRender kwarg.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ body }}</span>"

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

        class Page(Component):
            citry = c
            template = '<main><c-card c-body="<b>{{ x }}</b>" /></main>'

            def template_data(self, kwargs, slots):
                return {"x": "hi"}

        # The prop template renders in Page's scope but is interior content of
        # Card's frame: it is no component's root render, so the <b> carries no
        # data-cid marker (only component roots are marked).
        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2=""><b>hi</b></span></main>'

    def test_template_attr_can_hold_a_component_tag(self):
        # The nested template is compiled with the surrounding component's tag
        # rules, so a <c-*> tag inside it resolves like any other component tag:
        # its attributes read Page's scope, and its output lands inside the
        # CitryRender that Card receives as the `body` kwarg. Unlike the plain
        # <b> above, Inner IS a component root, so it does carry a data-cid
        # marker. The marker is numbered last because Card is handed the kwarg
        # before the component tag inside it has rendered.
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<i>{{ label }}</i>"

            def template_data(self, kwargs, slots):
                return {"label": kwargs["label"]}

        class Card(Component):
            citry = c
            template = "<span>{{ body }}</span>"

            def template_data(self, kwargs, slots):
                return {"body": kwargs["body"]}

        class Page(Component):
            citry = c
            template = """<main><c-card c-body="<c-inner c-label='who' />" /></main>"""

            def template_data(self, kwargs, slots):
                return {"who": "hi"}

        expected = '<main data-cid-c1=""><span data-cid-c2=""><i data-cid-c3="">hi</i></span></main>'
        assert Page().render().serialize() == expected


class TestComponentNodeBoundary:
    def test_child_does_not_inherit_parent_variables(self):
        # A parent variable must not leak into the child's render context.
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ x }}</span>"  # no template_data -> no `x`

        class Page(Component):
            citry = c
            template = "<main><c-card /></main>"

            def template_data(self, kwargs, slots):
                return {"x": "parent-only"}

        with pytest.raises(KeyError):
            Page().render().serialize()

    def test_child_parent_and_root_linkage(self):
        c = Citry()
        seen = {}

        class Card(Component):
            citry = c
            template = "<span>x</span>"

            def template_data(self, kwargs, slots):
                seen["parent"] = self.parent
                seen["root"] = self.root
                return {}

        class Page(Component):
            citry = c
            template = "<main><c-card /></main>"

        Page().render().serialize()
        assert isinstance(seen["parent"], Page)
        assert seen["root"] is seen["parent"]  # parent is the root of this tree


class TestComponentNodeBody:
    # Body content becomes the child's slots (docs/design/component_slots.md section 4).
    # A child that never invokes a slot silently ignores its content, matching
    # django-components (surplus fills are not an error). Slot collection and
    # consumption are covered in depth in test_slot_fills.py.
    def test_unused_default_slot_content_is_ignored(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = "<main><c-card>body</c-card></main>"

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">x</span></main>'

    def test_unused_fill_is_ignored(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>x</span>"

        class Page(Component):
            citry = c
            template = '<main><c-card><c-fill name="h">f</c-fill></c-card></main>'

        assert Page().render().serialize() == '<main data-cid-c1=""><span data-cid-c2="">x</span></main>'
