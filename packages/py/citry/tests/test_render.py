"""
Tests for the CitryRender / CitryContext rendering structs (skeleton).

These cover the three-phase pipeline shape (see docs/design/component_rendering.md):
``Component(...) -> CitryElement``, ``.render() -> CitryRender``,
``.serialize() -> str``, plus the convenience coercions. Node rendering and
the dependency flow are later phases.
"""

# ruff: noqa: ANN

from dataclasses import FrozenInstanceError

import pytest

from citry import Citry, CitryContext, CitryElement, CitryRender, Component, Extension, RenderFrame
from citry.citry_render import Placeholder


def _card(template="<p>hi</p>"):
    """Build a CitryElement for a single-template component (fresh Citry each call)."""
    c = Citry()

    class Card(Component):
        citry = c

    Card.template = template
    return Card()


class TestRenderReturnsCitryRender:
    def test_render_returns_citry_render(self):
        rendered = _card().render()
        assert isinstance(rendered, CitryRender)

    def test_render_is_not_a_string(self):
        # The whole point of the split: render() yields an object, not HTML.
        assert not isinstance(_card().render(), str)

    def test_citry_render_carries_context(self):
        rendered = _card().render()
        assert isinstance(rendered.context, CitryContext)

    def test_each_render_is_a_fresh_object(self):
        el = _card()
        assert el.render() is not el.render()

    def test_live_render_carries_an_immutable_identity_frame(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = """
            <p>card</p>
            """

        rendered = Card().render()
        assert rendered.frame == RenderFrame(
            render_id=rendered.context.component.id,
            class_id=Card.class_id,
            class_name="Card",
            is_component_root=True,
            root_markers=(),
        )
        with pytest.raises(FrozenInstanceError):
            rendered.frame.render_id = "changed"

    def test_anonymous_render_still_has_an_empty_frame(self):
        rendered = CitryRender(parts=["text"], context=CitryContext())
        assert rendered.frame == RenderFrame(
            render_id=None,
            class_id=None,
            class_name=None,
            is_component_root=False,
            root_markers=(),
        )


class TestSerialize:
    def test_serialize_joins_static_template(self):
        assert _card("<p>hi</p>").render().serialize() == '<p data-cid-c1="">hi</p>'

    def test_repeated_serialization_preserves_live_render_id(self):
        element = _card("<p>hi</p>")
        rendered = element.render()

        assert rendered.serialize() == '<p data-cid-c1="">hi</p>'
        assert rendered.serialize() == '<p data-cid-c1="">hi</p>'
        assert element.render().serialize() == '<p data-cid-c2="">hi</p>'

    def test_serialize_joins_multiple_parts(self):
        # A CitryRender joins its parts in order...
        ctx = CitryContext()
        rendered = CitryRender(parts=["<div>", "a", "b", "</div>"], context=ctx)
        assert rendered.serialize() == "<div>ab</div>"

    def test_serialize_recurses_into_nested_render(self):
        # ...and a nested CitryRender part is serialized recursively (this is
        # how an embedded pre-rendered subtree inlines its HTML).
        ctx = CitryContext()
        inner = CitryRender(parts=["<span>inner</span>"], context=ctx)
        outer = CitryRender(parts=["<p>", inner, "</p>"], context=ctx)
        assert outer.serialize() == "<p><span>inner</span></p>"

    def test_detached_frame_serializes_without_a_live_component(self):
        rendered = CitryRender(
            parts=["<span>cached</span>"],
            context=CitryContext(),
            frame=RenderFrame(
                render_id="replayed-1",
                class_id="example.Card",
                class_name="Card",
                is_component_root=True,
                root_markers=('data-citry-key="example.Card:7"',),
            ),
        )
        assert rendered.serialize(deps_strategy="ignore") == (
            '<span data-cid-replayed-1="" data-citry-key="example.Card:7">cached</span>'
        )

    def test_unresolved_placeholder_serializes_empty_without_component(self):
        rendered = CitryRender(parts=["left", Placeholder("missing"), "right"], context=CitryContext())
        assert rendered.serialize() == "leftright"

    def test_unresolved_placeholder_does_not_remove_authored_lookalike(self):
        authored = '<template c-render-id="missing:1"></template>'
        rendered = CitryRender(parts=[authored, Placeholder("missing")], context=CitryContext())
        assert rendered.serialize() == authored

    def test_unresolved_root_placeholder_drops_spliced_component_marker(self):
        c = Citry()

        class PlaceholderRoot(Component):
            citry = c

            def on_render(self):
                return CitryRender(parts=[Placeholder("missing")], context=CitryContext())

        assert str(PlaceholderRoot()) == ""

    def test_serialize_hook_copies_of_unresolved_placeholder_all_serialize_empty(self):
        class Duplicate(Extension):
            name = "duplicate"

            def on_serialize(self, ctx):
                return ctx.html + ctx.html

        c = Citry(extensions=[Duplicate])

        class PlaceholderRoot(Component):
            citry = c

            def on_render(self):
                return CitryRender(parts=["x", Placeholder("missing"), "y"], context=CitryContext())

        html = str(PlaceholderRoot())
        assert html == "xyxy"
        assert "c-render-id" not in html


class TestCoercions:
    def test_str_of_render_serializes(self):
        rendered = _card("<p>hi</p>").render()
        assert str(rendered) == '<p data-cid-c1="">hi</p>'

    def test_bytes_of_render_serializes(self):
        rendered = _card("<p>hi</p>").render()
        assert bytes(rendered) == b'<p data-cid-c1="">hi</p>'

    def test_str_of_element_runs_full_chain(self):
        # str(Component(...)) goes element -> render -> serialize with defaults.
        el = _card("<p>hi</p>")
        assert isinstance(el, CitryElement)
        assert str(el) == '<p data-cid-c1="">hi</p>'


class TestContext:
    def test_context_holds_template_variables(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>hi</p>"

            def template_data(self, kwargs, slots):
                return {"title": "Hello", "count": 3}

        rendered = Card(x=1).render()
        assert rendered.context.variables == {"title": "Hello", "count": 3}

    def test_extra_starts_empty(self):
        # The tree-wide extension scratch space is empty in this skeleton.
        rendered = _card().render()
        assert rendered.context.extra == {}

    def test_no_template_yields_empty_render(self):
        c = Citry()

        class Templateless(Component):
            citry = c

        rendered = Templateless().render()
        assert isinstance(rendered, CitryRender)
        assert rendered.serialize() == ""
