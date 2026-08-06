"""
Tests for the API-reference enrichers: cross-linked signatures, base classes,
source links, external-inventory resolution, and the docstring example / note
blocks that used to be dropped.

Assertions lock internal (``/reference/...``) links, which resolve with or
without network; stdlib links to docs.python.org are a network-dependent
enhancement and are asserted only where the inventory is monkeypatched.
"""

from __future__ import annotations

import griffe
from lxml import html as lxml_html

from docs_site._internal import crossrefs
from docs_site._internal.crossrefs import make_type_resolver, resolve_external_url
from docs_site._internal.pipeline import render_page
from docs_site._internal.reference import _description, extract_symbol


def _member(data, name):
    """The extracted member with this name, or ``None``."""
    return next((m for m in data.members if m.name == name), None)


# --- external inventory resolution (crossrefs) --------------------------------


def test_resolve_external_url_shortens_module_path(monkeypatch) -> None:
    # griffe hands us the definition module path; the inventory keys the public
    # re-export, so dropping the innermost module segment must still match.
    monkeypatch.setattr(
        crossrefs, "external_inventory", lambda: {"django.http.HttpRequest": "https://ext/#HttpRequest"}
    )
    assert resolve_external_url("HttpRequest", "django.http.request.HttpRequest") == "https://ext/#HttpRequest"


def test_resolve_external_url_matches_bare_builtin(monkeypatch) -> None:
    monkeypatch.setattr(crossrefs, "external_inventory", lambda: {"dict": "https://py/#dict"})
    assert resolve_external_url("dict", "dict") == "https://py/#dict"


def test_resolve_external_url_unknown_is_none(monkeypatch) -> None:
    monkeypatch.setattr(crossrefs, "external_inventory", dict)
    assert resolve_external_url("Nope", "a.b.Nope") is None


def test_make_type_resolver_prefers_internal_then_external(monkeypatch) -> None:
    monkeypatch.setattr(crossrefs, "external_inventory", lambda: {"pathlib.Path": "https://py/#Path"})
    resolve = make_type_resolver()
    # Internal symbol resolves to its root-absolute reference URL.
    assert resolve("Slot", "citry.slots.Slot") == "/reference/slots/#citry-slot"
    # An unknown-internal type falls through to the external inventory.
    assert resolve("Path", "pathlib.Path") == "https://py/#Path"
    # Undocumented anywhere -> no link.
    assert resolve("Nope", "x.y.Nope") is None


# --- base classes (4.x bases line) --------------------------------------------


def test_class_shows_linked_bases() -> None:
    data = extract_symbol("citry.ComponentNode")
    assert data is not None
    joined = "".join(str(b) for b in data.bases)
    # The runtime base is Node; it links to the nodes reference page.
    assert '<code><a class="doc-type-link" href="/reference/nodes/#citry-node">Node</a></code>' in joined


def test_object_only_class_has_no_bases() -> None:
    # Component's only runtime base is object, which is dropped, so no bases line.
    data = extract_symbol("citry.Component")
    assert data is not None
    assert data.bases == []


def test_bases_render_on_the_page() -> None:
    html = render_page('<c-docstring path="citry.ComponentNode" />').html
    assert 'class="doc-class-bases"' in html
    assert 'href="/reference/nodes/#citry-node"' in html


# --- source links (4.x view source) -------------------------------------------


def test_symbol_carries_source_url() -> None:
    data = extract_symbol("citry.format_attrs")
    assert data is not None
    assert data.source_url.startswith("https://github.com/citry-dev/citry/blob/main/")
    assert "attrs.py" in data.source_url
    assert "#L" in data.source_url  # a line anchor into the file


def test_source_link_renders_on_the_page() -> None:
    html = render_page('<c-docstring path="citry.format_attrs" />').html
    document = lxml_html.document_fromstring(html)
    links = document.xpath('//a[contains(@class, "doc-source-link")]')
    data = extract_symbol("citry.format_attrs")

    assert data is not None
    assert len(links) == 1
    assert links[0].text_content().strip() == "View source"
    assert links[0].get("href") == data.source_url


# --- cross-linked signatures (4.x) --------------------------------------------


def test_attribute_signature_links_internal_type() -> None:
    data = extract_symbol("citry.Component")
    assert data is not None
    raw_slots = _member(data, "raw_slots")
    assert raw_slots is not None
    # dict[str, Slot]: the internal Slot type links to its reference page.
    assert '<a class="doc-type-link" href="/reference/slots/#citry-slot">Slot</a>' in str(raw_slots.signature)


def test_union_signature_links_left_and_keeps_none_plain() -> None:
    data = extract_symbol("citry.Component")
    parent = _member(data, "parent")
    assert parent is not None
    sig = str(parent.signature)
    assert '<a class="doc-type-link" href="/reference/component/#citry-component">Component</a>' in sig
    assert sig.endswith(" | None")  # the None operand stays plain text


def test_function_signature_still_reads_plainly() -> None:
    # The call form and the linked return type survive extraction.
    data = extract_symbol("citry.format_attrs")
    sig = str(data.signature)
    assert sig.startswith("format_attrs(")
    assert sig.endswith('-> <a class="doc-type-link" href="/reference/rendering/#citry-markup">Markup</a>')


# --- docstring example / admonition blocks (4.39 + 4.40, previously dropped) ---


def test_admonition_section_now_appears() -> None:
    # citry.citry's docstring has an "Example" admonition that the old text-only
    # description silently dropped; it must now render as a callout.
    data = extract_symbol("citry.citry")
    desc = str(data.description)
    assert 'class="doc-admonition"' in desc
    assert 'class="doc-admonition-title"' in desc


def test_examples_section_now_appears() -> None:
    data = extract_symbol("citry.ExtensionManager")
    emit = _member(data, "emit")
    assert emit is not None
    desc = str(emit.description)
    assert 'class="doc-examples"' in desc
    assert 'class="doc-section-title">Example' in desc


def test_other_docstring_sections_are_not_dropped() -> None:
    # A section citry has no dedicated field for (here Yields) must still render,
    # not vanish like examples/admonitions used to. Guards the whole content-loss
    # class, not just the two kinds that were originally fixed.
    doc = griffe.Docstring("Summary line.\n\nYields:\n    int: the next value in the sequence.", parser="google")
    html = str(_description(doc.parsed))
    assert "Yields" in html
    assert "the next value in the sequence." in html


# --- offline safety -----------------------------------------------------------


def test_signatures_render_offline_with_internal_links(monkeypatch) -> None:
    # With no external inventory, stdlib types render plain but internal types
    # still link and nothing raises.
    monkeypatch.setattr(crossrefs, "external_inventory", dict)
    data = extract_symbol("citry.Component")
    assert data is not None
    raw_slots = _member(data, "raw_slots")
    sig = str(raw_slots.signature)
    assert "/reference/slots/#citry-slot" in sig  # internal link survives offline
    assert "docs.python.org" not in sig  # no stdlib links without the inventory
