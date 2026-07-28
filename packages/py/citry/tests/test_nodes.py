"""
Tests for the value nodes: ExprNode and TemplateNode (component_rendering.md phase 2).

Covers expression evaluation via safe_eval, autoescaping in both body-text and
attribute positions, the None/SafeString rules, and the embedded-CitryRender /
CitryElement detection. Also covers the value layer underneath rendering, where
`ExprNode.evaluate` and `ExprHtmlAttr.resolve` hand back the Python value
untouched. The remaining HTML-attr nodes (StaticHtmlAttr/TemplateHtmlAttr) are
phase 3 (they resolve to component kwargs).
"""

# ruff: noqa: ANN

from citry import Citry, CitryContext, Component, Const
from citry import nodes as nodes_module
from citry.constness import is_const
from citry.nodes import ExprHtmlAttr, ExprNode
from citry.util.html import SafeString

# The nodes keep `source` and `position` only for error messages, so any
# stand-in works when a test builds a node by hand.
_SOURCE = "<p>{{ x }}</p>"


def _html(template, **data):
    """Render a component whose template_data returns `data`; return the HTML."""
    c = Citry()

    class Comp(Component):
        citry = c

        def template_data(self, kwargs, slots):
            return dict(data)

    Comp.template = template
    return Comp().render().serialize()


def _count_compiles(monkeypatch):
    """Swap in a counting expression compiler; return the list it records each compiled expression in."""
    compiled = []
    real = nodes_module.compile_expr

    def counting_compile(expr, *, sandboxed=True):
        compiled.append(expr)
        return real(expr, sandboxed=sandboxed)

    monkeypatch.setattr(nodes_module, "compile_expr", counting_compile)
    return compiled


class TestExprNodeEval:
    def test_renders_variable(self):
        assert _html("<p>{{ x }}</p>", x="hello") == '<p data-cid-c1="">hello</p>'

    def test_evaluates_expression(self):
        assert _html("<p>{{ a + b }}</p>", a=2, b=3) == '<p data-cid-c1="">5</p>'

    def test_repeated_render_is_stable(self):
        c = Citry()

        class Comp(Component):
            citry = c
            template = "<p>{{ x }}</p>"

            def template_data(self, kwargs, slots):
                return {"x": "v"}

        el = Comp()
        # Each render mints a fresh id, so the data-cid marker differs
        # between the two renders even though the structure is identical.
        assert el.render().serialize() == '<p data-cid-c1="">v</p>'
        assert el.render().serialize() == '<p data-cid-c2="">v</p>'


class TestExprNodeEscaping:
    def test_escapes_body_text(self):
        assert (
            _html("<p>{{ x }}</p>", x="<b>hi & 'bye'</b>")
            == '<p data-cid-c1="">&lt;b&gt;hi &amp; &#39;bye&#39;&lt;/b&gt;</p>'
        )

    def test_escapes_in_attribute_position(self):
        # c-href becomes a dynamic attribute; the value must be quote-safe.
        assert _html('<a c-href="x">l</a>', x='a"b & c') == '<a href="a&#34;b &amp; c" data-cid-c1="">l</a>'

    def test_none_renders_as_empty_string(self):
        assert _html("<p>{{ x }}</p>", x=None) == '<p data-cid-c1=""></p>'

    def test_safestring_passes_through_unescaped(self):
        assert _html("<p>{{ x }}</p>", x=SafeString("<b>bold</b>")) == '<p data-cid-c1=""><b>bold</b></p>'

    def test_const_value_is_escaped_transparently(self):
        # Const is a transparent proxy: escape sees the underlying value.
        assert _html("<p>{{ x }}</p>", x=Const("<i>")) == '<p data-cid-c1="">&lt;i&gt;</p>'


class TestExprRawValue:
    # `evaluate` and `resolve` are the value layer under rendering: they hand
    # back the Python object the expression produced, with no escaping and no
    # str(). Escaping happens above them, in `ExprNode.render`.

    def test_evaluate_returns_the_string_unescaped(self):
        node = ExprNode(_SOURCE, (0, 0), "x", ("x",))
        raw = "<b>hi & 'bye'</b>"
        assert node.evaluate({"x": raw}) is raw
        # The same node, rendered, escapes that very same value.
        assert node.render(CitryContext(variables={"x": raw})) == "&lt;b&gt;hi &amp; &#39;bye&#39;&lt;/b&gt;"

    def test_evaluate_preserves_the_python_type(self):
        node = ExprNode(_SOURCE, (0, 0), "a + b", ("a", "b"))
        value = node.evaluate({"a": 2, "b": 3})
        assert value == 5
        assert type(value) is int

    def test_evaluate_returns_the_same_object(self):
        node = ExprNode(_SOURCE, (0, 0), "item", ("item",))
        item = {"id": 1}
        # Not a copy and not a string: the caller gets back the very object it passed in.
        assert node.evaluate({"item": item}) is item

    def test_evaluate_returns_none_unchanged(self):
        node = ExprNode(_SOURCE, (0, 0), "x", ("x",))
        assert node.evaluate({"x": None}) is None
        # Rendering is what turns None into the empty string.
        assert node.render(CitryContext(variables={"x": None})) == ""

    def test_evaluate_returns_safestring_unchanged(self):
        node = ExprNode(_SOURCE, (0, 0), "x", ("x",))
        safe = SafeString("<b>bold</b>")
        assert node.evaluate({"x": safe}) is safe

    def test_evaluate_compiles_the_expression_once(self, monkeypatch):
        compiled = _count_compiles(monkeypatch)
        node = ExprNode(_SOURCE, (0, 0), "x", ("x",))
        assert [node.evaluate({"x": n}) for n in (1, 2, 3)] == [1, 2, 3]
        # The node is cached across renders, so the expression compiles once.
        assert compiled == ["x"]

    def test_resolve_returns_the_string_unescaped(self):
        attr = ExprHtmlAttr(_SOURCE, (0, 0), "c-title", "x", ("x",))
        raw = 'a"b & c'
        # The value becomes a component kwarg; the child escapes it when it renders.
        assert attr.resolve(CitryContext(variables={"x": raw})) is raw

    def test_resolve_returns_the_same_object(self):
        attr = ExprHtmlAttr(_SOURCE, (0, 0), "c-item", "item", ("item",))
        item = {"id": 1}
        assert attr.resolve(CitryContext(variables={"item": item})) is item

    def test_resolve_does_not_add_the_const_marker(self):
        # A literal written in the template uses no variables, but the marking
        # happens where the value becomes a component input, not here.
        attr = ExprHtmlAttr(_SOURCE, (0, 0), "c-title", "'lit'", ())
        value = attr.resolve(CitryContext())
        assert value == "lit"
        assert not is_const(value)

    def test_resolve_compiles_the_expression_once(self, monkeypatch):
        compiled = _count_compiles(monkeypatch)
        attr = ExprHtmlAttr(_SOURCE, (0, 0), "c-n", "n", ("n",))
        assert attr.resolve(CitryContext(variables={"n": 1})) == 1
        assert attr.resolve(CitryContext(variables={"n": 2})) == 2
        assert compiled == ["n"]

    def test_boolean_attr_resolves_to_true_without_evaluating(self, monkeypatch):
        # Node classes are public API: an extension building an ExprHtmlAttr by
        # hand may pass `True` as the boolean form. There is nothing to compile,
        # and compiling `True` would raise, so nothing may reach the compiler.
        compiled = _count_compiles(monkeypatch)
        attr = ExprHtmlAttr(_SOURCE, (0, 0), "c-foo", True, ())  # noqa: FBT003 (the compiler emits positional args)
        assert attr.resolve(CitryContext()) is True
        assert compiled == []


class TestExprNodeEmbedding:
    def _card(self):
        c = Citry()

        class Card(Component):
            citry = c
            template = "<span>{{ label }}</span>"

            def template_data(self, kwargs, slots):
                return {"label": "IN"}

        return Card

    def test_embeds_pre_rendered_citry_render(self):
        rendered = self._card()().render()  # a CitryRender
        # Inlined as trusted HTML (the inner <span> tags are NOT re-escaped).
        assert (
            _html("<main>{{ c }}</main>", c=rendered) == '<main data-cid-c2=""><span data-cid-c1="">IN</span></main>'
        )

    def test_auto_renders_a_citry_element(self):
        element = self._card()()  # a CitryElement (not yet rendered)
        assert _html("<main>{{ c }}</main>", c=element) == '<main data-cid-c1=""><span data-cid-c2="">IN</span></main>'


class TestTemplateNode:
    def test_renders_nested_template(self):
        # c-body holds a nested template; it renders against the same context.
        assert (
            _html('<div c-body="<span>{{ x }}</span>">end</div>', x="hi")
            == '<div body="<span>hi</span>" data-cid-c1="">end</div>'
        )

    def test_nested_template_escapes_inner_expression(self):
        assert (
            _html('<div c-body="<span>{{ x }}</span>">end</div>', x="<i>")
            == '<div body="<span>&lt;i&gt;</span>" data-cid-c1="">end</div>'
        )
