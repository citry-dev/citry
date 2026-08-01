"""
Tests for rendering griffe type annotations to cross-linked HTML.

These load the real griffe model of ``citry`` and render a few genuine
annotations through a stub resolver, so the assertions lock the exact HTML the
module produces rather than a hand-written guess.
"""

from __future__ import annotations

import griffe

from docs_site._internal.annotation import render_annotation

# The griffe model of citry, loaded once. The symbols below are stable public
# API also relied on by test_reference.py.
PKG = griffe.load("citry", docstring_parser="google")

# The stub resolver hands this out for the single type name it "knows".
FAKE_URL = "/reference/fake/#target"


def resolve_only(known_name):
    """A stub resolver: one type name maps to FAKE_URL, every other name to None."""

    def resolve(name, canonical_path):
        # Keys on the leaf name only; canonical_path is part of the real contract
        # but this stub does not need it to decide.
        assert isinstance(canonical_path, str)
        return FAKE_URL if name == known_name else None

    return resolve


def symbol(dotted_path):
    """Walk ``citry.A.b`` to its griffe object."""
    obj = PKG
    for part in dotted_path.split(".")[1:]:
        obj = obj.members[part]
    return obj


def test_expr_name_becomes_a_link():
    # A bare type name (griffe ExprName) that the resolver knows becomes a link.
    annotation = symbol("citry.format_attrs").returns
    html = render_annotation(annotation, resolve_only("Markup"))
    assert html == '<a class="doc-type-link" href="/reference/fake/#target">Markup</a>'


def test_subscript_links_known_leaf_and_leaves_others_plain():
    # dict[str, Slot]: only Slot is known, so dict and str stay plain text.
    annotation = symbol("citry.Component.raw_slots").annotation
    html = render_annotation(annotation, resolve_only("Slot"))
    assert html == 'dict[str, <a class="doc-type-link" href="/reference/fake/#target">Slot</a>]'
    assert html.count("doc-type-link") == 1  # dict and str were not linked


def test_binop_renders_pep604_union():
    # Component | None: the known left side links, the None stays plain.
    annotation = symbol("citry.Component.parent").annotation
    html = render_annotation(annotation, resolve_only("Component"))
    assert html == '<a class="doc-type-link" href="/reference/fake/#target">Component</a> | None'


def test_unknown_names_stay_plain_escaped_text():
    # With no known name, the whole annotation renders as plain text, no link.
    annotation = symbol("citry.Component.raw_slots").annotation
    html = render_annotation(annotation, resolve_only("NotAType"))
    assert html == "dict[str, Slot]"
    assert "doc-type-link" not in html


def test_str_annotation_is_html_escaped():
    # A plain string annotation is returned as escaped text, never as a link.
    html = render_annotation("dict[str, int] <b>&", resolve_only("x"))
    assert html == "dict[str, int] &lt;b&gt;&amp;"
    assert "doc-type-link" not in html


def test_none_and_empty_inputs_render_empty():
    assert render_annotation(None, resolve_only("x")) == ""
    assert render_annotation("", resolve_only("x")) == ""
