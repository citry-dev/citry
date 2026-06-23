"""
Tests for the control-flow nodes: IfNode and ForNode (rendering.md control-flow
phase).

Covers both authoring forms (the explicit ``<c-if cond=...>``/``<c-for
each=...>`` tags and the ``c-if=``/``c-for=`` shorthand attributes on plain HTML
elements), branch selection, the loop's comprehension semantics (multi-target
unpacking and ``if`` filters), the empty branch, the loop variable scope, and
escaping of loop output.
"""

import pytest

from citry import Citry, Component


def _html(template, **data):
    """Render a component whose template_data returns `data`; return the HTML."""
    c = Citry()

    class Comp(Component):
        citry = c

        def template_data(self, kwargs, slots=None):
            return dict(data)

    Comp.template = template
    return Comp().render().serialize()


class TestIfNode:
    def test_if_true_renders_body(self):
        assert _html('<c-if cond="x">yes</c-if>', x=True) == "yes"

    def test_if_false_renders_nothing(self):
        assert _html('<c-if cond="x">yes</c-if>', x=False) == ""

    def test_if_else_takes_else_when_false(self):
        assert _html('<c-if cond="x">yes</c-if><c-else>no</c-else>', x=False) == "no"

    def test_if_else_takes_if_when_true(self):
        assert _html('<c-if cond="x">yes</c-if><c-else>no</c-else>', x=True) == "yes"

    def test_elif_first_truthy_branch_wins(self):
        tpl = '<c-if cond="a">A</c-if><c-elif cond="b">B</c-elif><c-else>C</c-else>'
        assert _html(tpl, a=False, b=True) == "B"
        assert _html(tpl, a=True, b=True) == "A"
        assert _html(tpl, a=False, b=False) == "C"

    def test_cond_is_an_expression(self):
        assert _html('<c-if cond="n > 2">big</c-if><c-else>small</c-else>', n=5) == "big"
        assert _html('<c-if cond="n > 2">big</c-if><c-else>small</c-else>', n=1) == "small"

    def test_truthiness_not_identity(self):
        # A non-empty list is truthy; an empty one is not.
        assert _html('<c-if cond="items">has</c-if><c-else>none</c-else>', items=[0]) == "has"
        assert _html('<c-if cond="items">has</c-if><c-else>none</c-else>', items=[]) == "none"

    def test_body_renders_expressions(self):
        assert _html('<c-if cond="x"><b>{{ msg }}</b></c-if>', x=True, msg="hi") == '<b data-cid-c1="">hi</b>'

    def test_shorthand_attribute_form(self):
        assert _html('<p c-if="x">hi</p>', x=True) == '<p data-cid-c1="">hi</p>'
        assert _html('<p c-if="x">hi</p>', x=False) == ""

    def test_branches_group_across_whitespace(self):
        # Whitespace-only text between branches is formatting: the branches
        # group as if written back to back, and the whitespace is dropped.
        tpl = '<c-if cond="x">yes</c-if>\n  <c-else>no</c-else>'
        assert _html(tpl, x=True) == "yes"
        assert _html(tpl, x=False) == "no"

        tpl3 = '<c-if cond="a">A</c-if>\n<c-elif cond="b">B</c-elif>\n<c-else>C</c-else>'
        assert _html(tpl3, a=False, b=True) == "B"
        assert _html(tpl3, a=False, b=False) == "C"

    def test_content_between_branches_is_a_parse_error(self):
        with pytest.raises(SyntaxError, match="must follow one of"):
            _html('<c-if cond="x">yes</c-if>text<c-else>no</c-else>', x=True)


class TestForNode:
    def test_simple_loop(self):
        assert _html('<c-for each="i in items">[{{ i }}]</c-for>', items=[1, 2, 3]) == "[1][2][3]"

    def test_empty_iterable_renders_nothing(self):
        assert _html('<c-for each="i in items">[{{ i }}]</c-for>', items=[]) == ""

    def test_empty_branch_used_when_no_items(self):
        tpl = '<c-for each="i in items">[{{ i }}]</c-for><c-empty>none</c-empty>'
        assert _html(tpl, items=[]) == "none"
        assert _html(tpl, items=[1]) == "[1]"

    def test_empty_branch_groups_across_whitespace(self):
        # Same rule as if/else: whitespace-only text between the branches is
        # formatting and is dropped when the branches group.
        tpl = '<c-for each="i in items">[{{ i }}]</c-for>\n<c-empty>none</c-empty>'
        assert _html(tpl, items=[]) == "none"
        assert _html(tpl, items=[1, 2]) == "[1][2]"

    def test_multi_target_unpacking(self):
        tpl = '<c-for each="k, v in pairs">{{ k }}={{ v }};</c-for>'
        assert _html(tpl, pairs=[("a", 1), ("b", 2)]) == "a=1;b=2;"

    def test_dict_items(self):
        tpl = '<c-for each="k, v in d.items()">{{ k }}:{{ v }} </c-for>'
        assert _html(tpl, d={"x": 1, "y": 2}) == "x:1 y:2 "

    def test_comprehension_if_filter(self):
        tpl = '<c-for each="x in xs if x % 2 == 0">{{ x }}</c-for>'
        assert _html(tpl, xs=[1, 2, 3, 4]) == "24"

    def test_single_target_binds_whole_item(self):
        # A single target over tuples binds the whole tuple, not its first element.
        assert _html('<c-for each="p in pairs">{{ p }}</c-for>', pairs=[(1, 2), (3, 4)]) == "(1, 2)(3, 4)"

    def test_loop_variable_does_not_leak_outside(self):
        # `i` is only bound inside the loop body; the surrounding `i` is unchanged.
        tpl = '<c-for each="i in items">{{ i }}</c-for>-{{ i }}'
        assert _html(tpl, items=[1, 2], i="outer") == "12-outer"

    def test_outer_variable_visible_in_body(self):
        tpl = '<c-for each="i in items">{{ i }}{{ sep }}</c-for>'
        assert _html(tpl, items=[1, 2], sep="|") == "1|2|"

    def test_loop_output_is_escaped(self):
        assert _html('<c-for each="x in xs">{{ x }}</c-for>', xs=["<b>"]) == "&lt;b&gt;"

    def test_shorthand_attribute_form(self):
        assert (
            _html('<li c-for="i in items">{{ i }}</li>', items=["a", "b"])
            == '<li data-cid-c1="">a</li><li data-cid-c1="">b</li>'
        )

    def test_shorthand_empty(self):
        assert _html('<li c-for="i in items">{{ i }}</li>', items=[]) == ""

    def test_loop_var_used_in_same_element_attribute(self):
        # The loop variable is in scope for the same element's other
        # attributes, so it can feed a c-bind on that element. Regression for
        # a parser bug that rejected this as variable shadowing.
        out = _html('<li c-for="i in rows" c-bind="i">x</li>', rows=[{"data-n": 1}, {"data-n": 2}])
        assert out == '<li data-n="1" data-cid-c1="">x</li><li data-n="2" data-cid-c1="">x</li>'

    def test_loop_var_in_same_element_attribute_on_void_element(self):
        # Same case on a void element (the self-closing parser path).
        out = _html('<img c-for="a in items" c-bind="a" />', items=[{"src": "a.png"}, {"src": "b.png"}])
        assert out == '<img src="a.png" data-cid-c1=""/><img src="b.png" data-cid-c1=""/>'


class TestNestedControlFlow:
    def test_for_inside_if(self):
        tpl = '<c-if cond="show"><c-for each="i in items">{{ i }}</c-for></c-if>'
        assert _html(tpl, show=True, items=[1, 2]) == "12"
        assert _html(tpl, show=False, items=[1, 2]) == ""

    def test_if_inside_for(self):
        tpl = '<c-for each="i in items"><c-if cond="i > 1">{{ i }}</c-if></c-for>'
        assert _html(tpl, items=[1, 2, 3]) == "23"

    def test_shorthand_if_and_for_on_same_element(self):
        # IF wraps FOR: when the condition is false, nothing renders.
        tpl = '<li c-if="show" c-for="i in items">{{ i }}</li>'
        assert _html(tpl, show=True, items=["a", "b"]) == '<li data-cid-c1="">a</li><li data-cid-c1="">b</li>'
        assert _html(tpl, show=False, items=["a", "b"]) == ""
