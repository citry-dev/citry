"""
Fold raw-HTML headings into the table of contents.

python-markdown's ``toc`` extension only sees markdown headings (``#``, ``##``).
The API reference emits its symbol headings as raw HTML (through ``<c-docstring>``,
passed on by ``md_in_html``), so the toc extension never sees them and the
right-rail TOC would miss every symbol.

This rebuilds the toc token tree from the rendered HTML when, and only when, such
headings are present, so a normal content page (whose headings are all markdown)
is returned untouched. It also lifts each symbol's members into the tree and
records the symbol *kind* (class / function / attribute / ...) so the rail can
show the type badge and nest members under their class.

Every token this module returns carries its heading text in two forms: ``name``
is plain, unescaped text (the template escapes it once when it renders), and
``label`` is that same text split into ``(text, is_code)`` parts, so the rail can
show a heading's code spans as code without trusting any other heading markup.
"""

from __future__ import annotations

import html
import re

import lxml.html  # type: ignore[import-untyped]

# Heading levels the right-rail TOC tracks. H1 (the page title) is kept in the
# tree but unwrapped by the flattener so it is not listed.
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def merge_html_headings_into_toc(content_html: str, toc_tokens: list) -> list:
    """
    Return a toc token tree that also covers raw-HTML headings in the content.

    Keeps the page-structural headings: the ones markdown already tracked, plus
    raw headings that opt in with ``toc-heading`` and reference symbol headings.
    Headings that live inside a docstring body are left out. Returns
    ``toc_tokens`` unchanged when there is nothing raw to add.
    """
    # python-markdown hands over ``name`` already HTML-escaped. Convert it to plain
    # text first, so every name in the tree has one form and the template's own
    # escaping is the only escaping (otherwise "<c-if>" shows as "&lt;c-if&gt;").
    toc_tokens = _normalize_markdown_tokens(toc_tokens)
    existing_ids = _collect_ids(toc_tokens)
    dom_headings = _extract_headings(content_html)
    kept = [
        (lvl, hid, label, kind)
        for (lvl, hid, label, cls, kind) in dom_headings
        if hid in existing_ids or "toc-heading" in cls or "doc-heading" in cls or "doc-member-heading" in cls
    ]

    # Nothing raw to add (every kept heading is already in the markdown toc).
    if all(hid in existing_ids for (_, hid, _, _) in kept):
        return toc_tokens

    # A heading markdown already tracked keeps its markdown label, which honors
    # an author's ``data-toc-label`` override.
    existing_labels = _collect_labels(toc_tokens)
    enriched = [(lvl, hid, existing_labels.get(hid, label), kind) for (lvl, hid, label, kind) in kept]
    return _build_tree(enriched)


def _normalize_markdown_tokens(tokens: list) -> list:
    """Copy python-markdown's toc tokens with a plain-text ``name`` and a ``label``."""
    normalized = []
    for token in tokens:
        if token.get("data-toc-label"):
            # The author's override wins, and the toc extension already reduced
            # it to escaped text, so it has no code spans to keep.
            label = _clean_parts([(html.unescape(token.get("name", "")), False)])
        else:
            # ``html`` is the heading's rendered inner markup, ``<code>`` and all.
            label = _label_parts(lxml.html.fragment_fromstring(token.get("html", ""), create_parent="div"))
        normalized.append(
            {
                **token,
                "name": _label_text(label),
                "label": label,
                "children": _normalize_markdown_tokens(token.get("children", [])),
            }
        )
    return normalized


def _label_parts(el: lxml.html.HtmlElement) -> list[tuple[str, bool]]:
    """
    Split an element's text into ``(text, is_code)`` parts.

    A ``<code>`` element becomes one code part. Every other element contributes
    only its text, so links, emphasis, or any raw HTML in a heading cannot reach
    the rail as markup.
    """
    parts: list[tuple[str, bool]] = []

    def walk(node: lxml.html.HtmlElement) -> None:
        parts.append((node.text or "", False))
        for child in node:
            # Comments and processing instructions have a non-string tag and no
            # visible text, but the text after them still belongs to the heading.
            if isinstance(child.tag, str):
                if child.tag == "code":
                    parts.append((child.text_content(), True))
                elif child.tag in {"script", "style"}:
                    # Their text is code for the browser, not words a reader sees.
                    pass
                else:
                    walk(child)
            parts.append((child.tail or "", False))

    walk(el)
    return _clean_parts(parts)


def _clean_parts(parts: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    """Join neighboring text parts, collapse whitespace like a browser would, and trim the ends."""
    # Join first, so whitespace on both sides of an element boundary collapses as one run.
    joined: list[tuple[str, bool]] = []
    for text, is_code in parts:
        if joined and not is_code and not joined[-1][1]:
            joined[-1] = (joined[-1][0] + text, False)
        else:
            joined.append((text, is_code))

    cleaned: list[tuple[str, bool]] = []
    for raw_text, is_code in joined:
        # Only ASCII whitespace collapses in HTML; a non-breaking space must survive.
        text = re.sub(r"[ \t\n\r\f]+", " ", raw_text)
        # A space that follows a space across a code boundary would show twice in plain text.
        if cleaned and cleaned[-1][0].endswith(" "):
            text = text.lstrip(" ")
        if text:
            cleaned.append((text, is_code))
    # Trim the label's outer whitespace, dropping a part that becomes empty.
    if cleaned:
        cleaned[0] = (cleaned[0][0].lstrip(), cleaned[0][1])
        cleaned[-1] = (cleaned[-1][0].rstrip(), cleaned[-1][1])
    return [(text, is_code) for text, is_code in cleaned if text]


def _label_text(label: list[tuple[str, bool]]) -> str:
    return "".join(text for text, _ in label)


def _extract_headings(content_html: str) -> list[tuple[int, str, list[tuple[str, bool]], str, str]]:
    """Document-order (level, id, label parts, class, kind) for every id'd h1-h6 in the HTML."""
    if not content_html.strip():
        return []

    # Wrap in a single root so multi-element fragments parse whole (fragment
    # parsing otherwise stops at the first top-level element).
    frag = lxml.html.fromstring(f"<div>{content_html}</div>")

    # Materialize first: we mutate each heading below (dropping its permalink), and
    # mutating the tree while iterating it would abort the iteration.
    heading_els = [el for el in frag.iter() if isinstance(el.tag, str) and el.tag in _HEADING_TAGS and el.get("id")]

    headings: list[tuple[int, str, list[tuple[str, bool]], str, str]] = []
    for el in heading_els:
        # Drop the permalink anchor so its glyph does not end up in the label.
        for anchor in el.findall(".//a"):
            if "headerlink" in (anchor.get("class") or ""):
                anchor.drop_tree()
        headings.append((int(el.tag[1]), el.get("id"), _heading_label(el), el.get("class") or "", _heading_kind(el)))
    return headings


def _heading_label(el: lxml.html.HtmlElement) -> list[tuple[str, bool]]:
    """
    The heading's label parts: the ``doc-object-name`` span's text when present
    (so a member label is just its name, without the type badge), otherwise the
    heading's own text with its code spans kept as code.
    """
    for span in el.iter("span"):
        if "doc-object-name" in (span.get("class") or "").split():
            return _clean_parts([(span.text_content(), False)])
    return _label_parts(el)


def _heading_kind(el: lxml.html.HtmlElement) -> str:
    """
    The symbol kind (class / function / attribute / ...) read from the badge span's
    ``doc-symbol-{kind}`` class, or ``""`` for a plain content heading.
    """
    for span in el.iter("span"):
        for cls in (span.get("class") or "").split():
            if cls.startswith("doc-symbol-") and cls != "doc-symbol-heading":
                return cls.removeprefix("doc-symbol-")
    return ""


def _collect_ids(tokens: list) -> set[str]:
    ids: set[str] = set()
    for token in tokens:
        if token.get("id"):
            ids.add(token["id"])
        ids |= _collect_ids(token.get("children", []))
    return ids


def _collect_labels(tokens: list) -> dict[str, list[tuple[str, bool]]]:
    labels: dict[str, list[tuple[str, bool]]] = {}
    for token in tokens:
        if token.get("id"):
            labels[token["id"]] = token["label"]
        labels.update(_collect_labels(token.get("children", [])))
    return labels


def _build_tree(headings: list[tuple[int, str, list[tuple[str, bool]], str]]) -> list:
    """Build a nested toc tree from a flat document-order heading list."""
    root: list = []
    stack: list[tuple[int, dict]] = []  # (level, node)
    for level, hid, label, kind in headings:
        node = {"id": hid, "name": _label_text(label), "label": label, "level": level, "kind": kind, "children": []}
        while stack and stack[-1][0] >= level:
            stack.pop()
        (stack[-1][1]["children"] if stack else root).append(node)
        stack.append((level, node))
    return root
