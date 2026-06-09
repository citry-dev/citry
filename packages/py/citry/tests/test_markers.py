"""
Tests for the ``data-cid-<id>`` component markers (docs/design/deferred_rendering.md, Phase B).

``serialize()`` tags each component's root element(s) with a ``data-cid-<id>=""``
marker. When one component's root element is itself another component, that
element carries both markers (the inner component's, then the markers it
inherited from its parent). Render ids are made deterministic per test by the
autouse fixture in conftest.py (``c1``, ``c2``, ... in render order).
"""

# ruff: noqa: ANN

from citry import Citry, Component


class TestSingleComponent:
    def test_root_element_gets_marker(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<div>x</div>"

        assert Card().render().serialize() == '<div data-cid-c1="">x</div>'

    def test_multiple_root_elements_each_get_marker(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<div>a</div><span>b</span>"

        assert Card().render().serialize() == '<div data-cid-c1="">a</div><span data-cid-c1="">b</span>'

    def test_text_only_component_has_no_marker(self):
        # No HTML element means nowhere to put the marker.
        c = Citry()

        class Plain(Component):
            citry = c
            template = "hello"

        assert Plain().render().serialize() == "hello"

    def test_id_is_fresh_each_render(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>x</p>"

        el = Card()
        first = el.render().serialize()
        second = el.render().serialize()
        assert first == '<p data-cid-c1="">x</p>'
        assert second == '<p data-cid-c2="">x</p>'


class TestNestedNotAtRoot:
    def test_child_inside_an_element_does_not_inherit(self):
        # The child sits inside the parent's <div>, so the parent's <div> is the
        # root, not the child. Each element carries only its own marker.
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<span>x</span>"

        class Outer(Component):
            citry = c
            template = "<div><c-inner /></div>"

        assert Outer().render().serialize() == '<div data-cid-c1=""><span data-cid-c2="">x</span></div>'


class TestChildIsParentRoot:
    def test_two_level_stacking(self):
        # Outer's whole template is the child, so Inner's <div> is Outer's root
        # element and carries both markers.
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<div>x</div>"

        class Outer(Component):
            citry = c
            template = "<c-inner />"

        assert Outer().render().serialize() == '<div data-cid-c2="" data-cid-c1="">x</div>'

    def test_three_level_stacking(self):
        c = Citry()

        class A(Component):
            citry = c
            template = "<div>x</div>"

        class B(Component):
            citry = c
            template = "<c-a />"

        class C(Component):
            citry = c
            template = "<c-b />"

        assert C().render().serialize() == '<div data-cid-c3="" data-cid-c2="" data-cid-c1="">x</div>'

    def test_multiple_root_children_each_inherit(self):
        # Both children are at the root of the parent, so each inherits the
        # parent's marker on top of its own.
        c = Citry()

        class A(Component):
            citry = c
            template = "<i>a</i>"

        class B(Component):
            citry = c
            template = "<i>b</i>"

        class Root(Component):
            citry = c
            template = "<c-a /><c-b />"

        assert (
            Root().render().serialize()
            == '<i data-cid-c2="" data-cid-c1="">a</i><i data-cid-c3="" data-cid-c1="">b</i>'
        )
