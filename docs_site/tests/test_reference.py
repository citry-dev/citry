"""Tests for the griffe API reference and the ``<c-docstring />`` directive."""

from __future__ import annotations

import griffe
from lxml import html as lxml_html

from docs_site._internal.pipeline import render_page
from docs_site._internal.reference import _attributes, extract_symbol


def test_extract_function() -> None:
    data = extract_symbol("citry.format_attrs")
    assert data is not None
    assert data.name == "format_attrs"
    assert data.kind == "function"
    assert "format_attrs(" in data.signature
    assert ">Markup</a>" in data.signature
    assert data.members == []


def test_extract_class_with_members() -> None:
    data = extract_symbol("citry.OnSerializeContext")
    assert data is not None
    assert data.kind == "class"
    member_names = {m.name for m in data.members}
    assert "html" in member_names  # an attribute member
    assert all(not m.name.startswith("_") for m in data.members)


def test_extract_external_markup_without_citry_owned_details() -> None:
    data = extract_symbol("citry.Markup")
    assert data is not None
    assert data.kind == "class"
    assert data.name == "Markup"
    assert data.source_url == ""
    assert data.members == []
    assert 'href="/foo"' not in str(data.description)


def test_extract_first_party_security_error() -> None:
    data = extract_symbol("citry.SecurityError")
    assert data is not None
    assert data.kind == "class"
    assert data.name == "SecurityError"
    assert "packages/py/citry_core/citry_core/safe_eval/eval.py" in data.source_url
    assert data.members == []


def test_extract_unknown_returns_none() -> None:
    assert extract_symbol("citry.Nope") is None
    assert extract_symbol("citry.Component.no_such_method") is None
    assert extract_symbol("notcitry.Thing") is None


def test_docstring_directive_renders_a_class() -> None:
    html = render_page('<c-docstring path="citry.OnSerializeContext" />').html
    assert "<code>OnSerializeContext</code>" in html
    assert "doc-object" in html
    # The directive and the recursive component tag are fully expanded.
    assert "<c-docstring" not in html
    assert "<c-ReferenceSymbol" not in html


def test_docstring_directive_renders_members_recursively() -> None:
    data = extract_symbol("citry.OnSerializeContext")
    assert data is not None

    html = render_page('<c-docstring path="citry.OnSerializeContext" />').html
    document = lxml_html.document_fromstring(html)
    object_names = [
        element.xpath('normalize-space(string(.//span[contains(@class, "doc-object-name")]))')
        for element in document.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " doc-object ")]')
    ]
    expected_names = {data.name, *(member.name for member in data.members)}

    assert len(object_names) == len(expected_names)
    assert set(object_names) == expected_names


def test_docstring_directive_unknown_symbol() -> None:
    html = render_page('<c-docstring path="citry.Nope" />').html
    assert "Unknown symbol: citry.Nope" in html


def test_attribute_rows_get_their_own_anchor() -> None:
    # A guide links to one setting of a nested class, such as a State
    # setting whose `_` name keeps it out of the members list, so each row
    # of an `Attributes:` section needs an anchor under its symbol's.
    docstring = griffe.Docstring(
        "Settings.\n\nAttributes:\n    _max_age (int): How long it lasts.\n",
        parser="google",
    )
    rows = _attributes(docstring.parse(), "citry-thing-state")
    assert [row.anchor for row in rows] == ["citry-thing-state-max-age"]


def test_attribute_row_that_is_also_a_member_gets_no_second_anchor() -> None:
    # The member entry already carries the anchor, and two elements with
    # one id on a page would break links to it.
    docstring = griffe.Docstring(
        "Settings.\n\nAttributes:\n    enabled (bool): Whether it runs.\n",
        parser="google",
    )
    rows = _attributes(docstring.parse(), "citry-thing", frozenset({"enabled"}))
    assert rows[0].anchor is None
