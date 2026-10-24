"""
Deeply nested templates render the same as the same template nested less.

CPython refuses a statement with more than 200 open brackets, and each
``<c-if>`` adds four nested brackets to the code Citry generates. So once a
template nests about 25 ``<c-if>`` or ``<c-for>`` tags, the compiler moves
some parts of the node tree into local variables (``_n1 = ...``) that
earlier statements assign.

Each template below holds one ``{{ hole }}``, with other nodes on both
sides of it. These tests put ``k`` levels of ``<c-if cond="show">`` around
that hole and check two things:

- The rendered HTML equals the HTML of the template with no levels added,
  on the native and Python render paths and in prepared mode.
- The generated code still builds the nodes in the same order. Some node
  constructors raise, so a changed order could change which error a broken
  template reports.

``show`` is a template variable rather than the literal ``True``: Citry
computes a literal condition ahead of time, which would skip the render
path these tests need.
"""

from __future__ import annotations

import re
import textwrap
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.capture import render_prepared
from citry_core.template_parser import _compile_prepared_template, compile_template, parse_template

# Levels added around the hole. Around plain text, 24 levels still fit one
# statement and 25 do not, and a hole the template already nests reaches
# the budget sooner. When a subtree moves, every constructor to its left in
# the same statement moves too, so each of these depths moves a different
# set of the template's own nodes. At 120, some moved subtrees refer to
# other moved subtrees.
DEPTHS = (20, 24, 25, 26, 30, 120)

DATA: dict[str, Any] = {
    "show": True,
    "hole": "H",
    "name": "World",
    "n": 2,
    "items": [1, 2, 3],
    "cls": "c",
    "a": "A",
}

HOLE = "{{ hole }}"
OPEN = '<c-if cond="show">'
CLOSE = "</c-if>"

# Each template comes from a pattern the other test files already cover:
# text and expressions, every control-flow tag, dynamic element attributes
# with a key, and a component whose fill a slot shows.
TEMPLATES = {
    "text_and_expression": """
        <p class="x">Hello {{ name }} {{ hole }} and {{ name }}</p>
    """,
    "if_elif_else": """
        <c-if cond="n > 2">big</c-if>
        <c-elif cond="n > 1">mid {{ n }} {{ hole }} {{ n }}</c-elif>
        <c-else>small</c-else>
    """,
    "for_with_empty": """
        <c-for each="i in items">[{{ i }} {{ hole }} {{ i }}]</c-for>
        <c-empty>none</c-empty>
        <c-for each="i in []">never</c-for>
        <c-empty>empty</c-empty>
    """,
    "element_attributes_and_key": """
        <ul>
          <li
            c-for="i in items"
            #c-key="i"
            c-class="cls"
          >
            {{ i }} {{ hole }} <b c-class="cls">{{ i }}</b>
          </li>
        </ul>
    """,
    "component_fill_and_slot": """
        <c-card>
          <c-fill name="body">
            <b>{{ a }}</b> {{ hole }} <c-card />
          </c-fill>
        </c-card>
    """,
    "nested_logic": """
        <c-for each="i in items">
          <c-if cond="i % 2">odd {{ i }}</c-if>
          <c-else>
            <c-card>
              <c-fill name="body">
                <c-if cond="a">{{ a }} {{ hole }} {{ a }}</c-if>
              </c-fill>
            </c-card>
          </c-else>
        </c-for>
    """,
}

# Render ids count up across one test, so the wrapped and unwrapped renders
# get different ids for the same markup.
_RENDER_ID = re.compile(r"data-cid-\w+")

# Constructor calls in generated code. A match inside template text only
# adds an unused name to the namespace.
_CALL = re.compile(r"\b([A-Z]\w*)\(")


def _template(name: str) -> str:
    # Citry strips a component template's common indentation. Starting
    # from text with none keeps the added tags from changing it.
    return textwrap.dedent(TEMPLATES[name]).strip()


def _deepen(template: str, depth: int) -> str:
    """Put `depth` levels of `<c-if cond="show">` around the hole."""
    return template.replace(HOLE, OPEN * depth + HOLE + CLOSE * depth)


def _page(template: str) -> Component:
    app = Citry(autodiscover=False)

    class Card(Component):
        citry = app
        template = """
            <div><c-slot name="body">no body</c-slot></div>
        """

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return dict(DATA)

    Page.template = template
    return Page()


def _render(template: str, *, prepared: bool) -> str:
    page = _page(template)
    if prepared:
        html = render_prepared(page).serialize(deps_strategy="ignore", security_javascript="omit")
    else:
        html = page.render().serialize()
    return _RENDER_ID.sub("data-cid", html)


@pytest.mark.parametrize("prepared", [False, True], ids=["html", "prepared"])
@pytest.mark.parametrize("depth", DEPTHS)
@pytest.mark.parametrize("name", TEMPLATES)
def test_deep_template_renders_the_same(render_path: str, name: str, depth: int, prepared: bool) -> None:
    template = _template(name)
    assert _render(_deepen(template, depth), prepared=prepared) == _render(template, prepared=prepared)


# One recorded constructor call: the class name, its string arguments
# (attribute names, expressions, text), and its source span.
Call = tuple[str, tuple[str, ...], "tuple[int, int] | None"]


def _construction_log(template: str, depth: int, *, prepared: bool) -> list[Call]:
    """
    Run the code generated for `_deepen(template, depth)` with constructors that record their calls.

    Spans are given in the coordinates of `template` itself, so the log of a
    deep version can be compared with the log of the template with no
    levels added. The added `show` attributes get no span.
    """
    source = _deepen(template, depth)
    compile_fn = _compile_prepared_template if prepared else compile_template
    code = compile_fn(parse_template(source))
    log: list[Call] = []

    # Where the added tags sit in `source`: the opening tags right where the
    # hole was, then the hole, then the closing tags.
    hole_start = template.index(HOLE)
    hole_end = hole_start + len(OPEN) * depth + len(HOLE)
    rest_start = hole_end + len(CLOSE) * depth

    def original_position(position: int) -> int:
        if position <= hole_start:
            return position
        if position >= rest_start:
            return position - (len(OPEN) + len(CLOSE)) * depth
        return position - len(OPEN) * depth

    def recorder(name: str) -> Any:
        def construct(*args: Any) -> object:
            # Most nodes get the whole template as their first argument,
            # which says nothing about order.
            strings = tuple(arg for arg in args if isinstance(arg, str) and arg is not source)
            spans = [
                arg
                for arg in args
                if isinstance(arg, tuple) and len(arg) == 2 and all(isinstance(x, int) for x in arg)
            ]
            span = None
            if spans and strings != ("cond", "show"):
                span = (original_position(spans[0][0]), original_position(spans[0][1]))
            log.append((name, strings, span))
            return object()

        return construct

    namespace: dict[str, Any] = {"source": source}
    namespace.update({name: recorder(name) for name in set(_CALL.findall(code))})
    exec(code, namespace)  # noqa: S102 - the code is Citry's own compiler output
    namespace["generate_template"]()
    return log


@pytest.mark.parametrize("prepared", [False, True], ids=["html", "prepared"])
@pytest.mark.parametrize("depth", DEPTHS)
@pytest.mark.parametrize("name", TEMPLATES)
def test_deep_template_builds_its_nodes_in_the_same_order(name: str, depth: int, prepared: bool) -> None:
    template = _template(name)
    shallow = _construction_log(template, 0, prepared=prepared)
    # Python builds the added `show` attributes, then the hole's expression,
    # then the added `IfNode`s, all where it built the hole's expression
    # before. The added calls log identical entries, so their order among
    # themselves is left to the Rust printer tests, which check it exactly.
    hole = next(index for index, call in enumerate(shallow) if call[1][:1] == ("hole ",))
    added_attributes: list[Call] = [("ExprHtmlAttr", ("cond", "show"), None)] * depth
    added_ifs: list[Call] = [("IfNode", (), None)] * depth
    expected = shallow[:hole] + added_attributes + [shallow[hole]] + added_ifs + shallow[hole + 1 :]
    assert _construction_log(template, depth, prepared=prepared) == expected
