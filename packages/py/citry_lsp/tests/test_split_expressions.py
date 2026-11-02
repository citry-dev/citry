"""
The editor reads a template expression split across lines as Citry runs it.

Citry wraps each template expression in parentheses of its own before parsing
it, so an author may break one across lines without writing any, or start it
on an indented line.
These checks pin each editor feature that parses such text to the same result
as the one-line spelling, with positions that still point into the source.
"""

from __future__ import annotations

from types import SimpleNamespace

from citry_lsp import engine


def test_a_split_expression_is_not_taken_for_an_assignment() -> None:
    # A split expression must not count as a `:=` or lambda assignment, which
    # would turn off type information for this and every later expression.
    query = SimpleNamespace(source="a\n + b\n  ", host_kind="interpolation")

    assert engine._query_contains_named_expression(query) is False  # type: ignore[arg-type]
    assert engine._query_contains_lambda_named_expression(query) is False  # type: ignore[arg-type]


def test_translation_calls_in_a_split_expression_are_found_at_their_offsets() -> None:
    source = "tr('a') if x\n else tr('b') "

    uses = engine._python_i18n_uses(source, template=True)

    assert [(use[1], source[use[6] : use[7]]) for use in uses] == [("a", "a"), ("b", "b")]


def test_trans_value_keys_are_read_from_an_indented_value() -> None:
    source = "\n  {'n': 1}\n"

    assert engine._literal_trans_value_spans(source) == (("n", 5, 6),)


def test_a_name_on_a_later_line_of_a_split_expression_is_found() -> None:
    source = "a\n + b"

    assert engine._python_name_at(source, source.index("b")) is True
    assert engine._python_name_at(source, source.index("+")) is False
