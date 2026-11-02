"""
Templates nest at most 512 tags and 256 logic levels; one more is a clean error.

The limits are read from the parser's own private constants, so the tests
and the parser cannot disagree. Going one level past either limit raises
``SyntaxError`` with the ``citry.parse.too-deep`` diagnostic code, pointing
at the tag that goes too deep, from both the parser and the formatter.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry_core import _rust
from citry_core.template_formatter import TemplateFormatError, format_template
from citry_core.template_parser import compile_template, parse_template

MAX_TAG_NESTING = _rust.template_parser._MAX_TAG_NESTING
MAX_LOGIC_NESTING = _rust.template_parser._MAX_LOGIC_NESTING


def _nest(open_tag: str, close_tag: str, depth: int) -> str:
    return open_tag * depth + "x" + close_tag * depth


def test_the_limits_are_512_and_256() -> None:
    assert (MAX_TAG_NESTING, MAX_LOGIC_NESTING) == (512, 256)


@pytest.mark.parametrize(
    ("open_tag", "close_tag", "limit", "wording"),
    [
        ("<div>", "</div>", MAX_TAG_NESTING, "is nested 513 levels deep"),
        ('<c-if cond="x">', "</c-if>", MAX_LOGIC_NESTING, "is 257 Citry logic levels deep"),
    ],
)
def test_one_level_past_a_limit_is_a_too_deep_syntax_error(
    open_tag: str, close_tag: str, limit: int, wording: str
) -> None:
    compile_template(parse_template(_nest(open_tag, close_tag, limit)))
    source = _nest(open_tag, close_tag, limit + 1)
    with pytest.raises(SyntaxError, match=wording) as raised:
        parse_template(source)
    diagnostic = raised.value.diagnostic
    assert diagnostic.code == "citry.parse.too-deep"
    # The error points at the tag one level past the limit.
    tag = len(open_tag) * limit
    assert diagnostic.start_index == tag
    assert (diagnostic.start_line, diagnostic.start_column) == (1, tag + 1)


@pytest.mark.parametrize(
    ("open_tag", "close_tag", "limit"),
    [
        ("<div>", "</div>", MAX_TAG_NESTING),
        ('<c-if cond="x">', "</c-if>", MAX_LOGIC_NESTING),
    ],
)
def test_the_formatter_formats_a_template_at_the_limit(open_tag: str, close_tag: str, limit: int) -> None:
    # The formatter puts each nested tag on its own indented line, and the
    # result must still parse, so formatting never pushes a template over.
    formatted = format_template(_nest(open_tag, close_tag, limit))
    assert formatted.count(open_tag) == limit
    parse_template(formatted)


def test_the_formatter_reports_the_parser_diagnostic() -> None:
    source = "<p>" + _nest('<c-if cond="x">', "</c-if>", MAX_LOGIC_NESTING + 1) + "</p>"
    with pytest.raises(TemplateFormatError) as raised:
        format_template(source)
    error = raised.value
    assert error.code == "citry.format.syntax"
    assert error.diagnostic is not None
    assert error.diagnostic.code == "citry.parse.too-deep"


def _hand_built_tree(depth: int) -> _rust.template_parser.Template:
    """A tree of `depth` nested <div> tags, built in Python rather than parsed."""
    template = parse_template("<div>x</div>")
    node = template.elements[0]._0
    for _ in range(depth - 1):
        node = _rust.template_parser.Node.WithBody(
            start_tag=node.start_tag,
            end_tag=node.end_tag,
            body=_rust.template_parser.Template(
                elements=[_rust.template_parser.TemplateElement.Node(node)],
                comments=[],
                used_variables=[],
                slots=[],
            ),
            used_variables=[],
            introduced_variables=[],
            comments=[],
            contains_fills=False,
        )
    return _rust.template_parser.Template(
        elements=[_rust.template_parser.TemplateElement.Node(node)], comments=[], used_variables=[], slots=[]
    )


@pytest.mark.parametrize(
    "compile_",
    [_rust.template_parser.compile_template, _rust.template_parser._compile_prepared_template],
    ids=["compile_template", "compile_prepared_template"],
)
def test_compiling_a_hand_built_tree_past_the_limit_is_a_syntax_error(compile_: Any) -> None:
    # The parser never builds such a tree, but Python code can.
    compile_(_hand_built_tree(MAX_TAG_NESTING))
    with pytest.raises(SyntaxError, match="nested 513 levels deep"):
        compile_(_hand_built_tree(MAX_TAG_NESTING + 1))
