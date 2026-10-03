"""
Tests for the ``data-cid-<id>`` component markers (docs/design/component_rendering_defer.md, Phase B).

``serialize()`` tags each component's root element(s) with a ``data-cid-<id>=""``
marker. When one component's root element is itself another component, that
element carries both markers (the inner component's, then the markers it
inherited from its parent). Render ids are made deterministic per test by the
autouse fixture in conftest.py (``c1``, ``c2``, ... in render order).
"""

# ruff: noqa: ANN

from citry import Citry, Component, Extension, Markup


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


class TestHookReturnsSerializedResult:
    """
    A hook that serializes the component's own result and returns the HTML.
    An ``on_render`` hook wraps that HTML in ``Markup``, since a plain str
    would be escaped as text.

    The returned HTML is the component's new output, so its root tags are
    marked once at the final serialization, exactly like a template's roots.
    """

    def test_on_render_appending_to_str_result_marks_each_root_once(self):
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<b>in</b>"

        class Card(Component):
            citry = c
            template = "<div>body <c-inner /></div>"

            def on_render(self):
                result, _error = yield
                return Markup(str(result) + "<hr>")  # noqa: S704 - serialized render output is trusted HTML

        assert (
            Card().render().serialize() == '<div data-cid-c1="">body <b data-cid-c2="">in</b></div><hr data-cid-c1="">'
        )

    def test_on_render_child_at_root_keeps_marker_order(self):
        # The child's own marker comes first, then the markers it inherits,
        # the same as without the hook.
        c = Citry()

        class Inner(Component):
            citry = c
            template = "<b>in</b>"

        class Card(Component):
            citry = c
            template = "<c-inner />"

            def on_render(self):
                result, _error = yield
                return Markup(str(result) + "<hr>")  # noqa: S704 - serialized render output is trusted HTML

        class Page(Component):
            citry = c
            template = "<c-card />"

        assert Page().render().serialize() == (
            '<b data-cid-c3="" data-cid-c2="" data-cid-c1="">in</b><hr data-cid-c2="" data-cid-c1="">'
        )

    def test_on_render_yielding_serialized_result_twice(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>t</p>"

            def on_render(self):
                result, _error = yield
                result, _error = yield Markup(str(result) + "<hr>")  # noqa: S704 - serialized render output is trusted HTML
                return Markup(str(result) + "<br>")  # noqa: S704 - serialized render output is trusted HTML

        assert Card().render().serialize() == '<p data-cid-c1="">t</p><hr data-cid-c1=""><br data-cid-c1="">'

    def test_on_render_wrapping_result_marks_only_the_new_root(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<p>w</p>"

            def on_render(self):
                result, _error = yield
                return Markup(f"<section>{result}</section>")  # noqa: S704 - serialized render output is trusted HTML

        assert Card().render().serialize() == '<section data-cid-c1=""><p>w</p></section>'

    def test_extension_hook_returning_serialized_result_marks_once(self):
        class AppendRule(Extension):
            name = "append_rule"

            def on_component_rendered(self, ctx):
                if ctx.render is not None:
                    return str(ctx.render) + "<hr>"
                return None

        c = Citry(extensions=[AppendRule])

        class Card(Component):
            citry = c
            template = "<p>e</p>"

        assert Card().render().serialize() == '<p data-cid-c1="">e</p><hr data-cid-c1="">'

    def test_valued_extension_markers_are_written_once(self):
        class Mark(Extension):
            name = "mark"

            def on_component_data(self, ctx):
                if type(ctx.component).__name__ == "Card":
                    ctx.context._add_root_markers(['data-probe="own"', "data-flag"])

        c = Citry(extensions=[Mark])

        class Card(Component):
            citry = c
            template = "<p>v</p>"

            def on_render(self):
                result, _error = yield
                return Markup(str(result) + "<hr>")  # noqa: S704 - serialized render output is trusted HTML

        assert Card().render().serialize() == (
            '<p data-cid-c1="" data-flag="" data-probe="own">v</p><hr data-cid-c1="" data-flag="" data-probe="own">'
        )
