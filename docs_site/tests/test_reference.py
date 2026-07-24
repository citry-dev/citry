"""Tests for the griffe API reference and the ``<c-docstring />`` directive."""

from __future__ import annotations

from docs_site._internal.pipeline import render_page
from docs_site._internal.reference import extract_symbol


def test_extract_function() -> None:
    data = extract_symbol("citry.format_attrs")
    assert data is not None
    assert data.name == "format_attrs"
    assert data.kind == "function"
    assert "format_attrs(" in data.signature
    assert "-> SafeString" in data.signature
    assert data.members == []


def test_extract_class_with_members() -> None:
    data = extract_symbol("citry.OnSerializeContext")
    assert data is not None
    assert data.kind == "class"
    member_names = {m.name for m in data.members}
    assert "html" in member_names  # an attribute member
    assert all(not m.name.startswith("_") for m in data.members)


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
    # A class plus its members each become a doc-object block. Match the wrapper
    # class exactly so the doc-object-name span (added for the TOC) is not counted.
    html = render_page('<c-docstring path="citry.OnSerializeContext" />').html
    assert html.count('class="doc-object"') == 7  # the class + its 6 attributes


def test_docstring_directive_unknown_symbol() -> None:
    html = render_page('<c-docstring path="citry.Nope" />').html
    assert "Unknown symbol: citry.Nope" in html
