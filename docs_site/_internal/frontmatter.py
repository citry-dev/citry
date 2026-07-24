"""
Parse a markdown page's front matter and body.

A page may begin with a ``---`` fenced block of ``key: value`` lines (title,
description, ...). This splits that block from the body and reads the keys the
layout uses. Two keys fall back to the body when front matter omits them: the
title falls back to the page's first ``# H1``, and the description falls back to
the first real paragraph of the body (markdown formatting stripped, capped at
about 155 chars). A site-level default backfills the description at render time
(see ``docs_site._internal.config``), so every page still emits a meta description.

This is a deliberately small parser for the keys the site uses today; it is not
a full YAML implementation. Nested structures are not needed yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_TRUTHY = {"true", "1", "yes", "on"}
_FALSY = {"false", "0", "no", "off"}

# The first "real" paragraph of a body, used to derive a meta description when
# front matter sets none. It is the first block that is not a heading, image,
# admonition, blockquote, table, code fence, task-list item, tabbed block, or
# horizontal rule: each of those makes a poor description, so the negative
# lookahead skips a block that opens with one of their markers.
_FIRST_PARAGRAPH = re.compile(
    r"(?:^|\n\n)"
    r"(?!#|!|>|\||```|-\s\[|={3}|\?{3}|\*{3})"
    r"([^\n]+(?:\n(?!#|\n)[^\n]+)*)",
)

# Version-change notes ("New in version 0.89", "Changed in version ...") are
# short standalone lines that often sit before the first real prose. They make a
# useless description, so the extractor skips them and walks to the next block.
# Matched after inline formatting is stripped (the note is usually italic).
_VERSION_ANNOTATION = re.compile(r"^(New|Changed|Deprecated|Removed) in version\b", re.IGNORECASE)

# A derived description longer than this is truncated on a word boundary; ~155
# chars is about what a search engine shows in a result snippet.
_DESCRIPTION_CAP = 155


@dataclass
class PageMeta:
    """Front-matter values the ``DocPage`` layout reads, plus the page body."""

    title: str = ""
    description: str = ""
    canonical: str = ""
    noindex: bool = False
    # Social-card image: an absolute URL, or a path under the site root. Empty
    # falls back to the site-level default image.
    og_image: str = ""
    # Whether the page is indexed for search, and an optional search-ranking
    # boost (1.0 is neutral; higher ranks the page above its peers).
    searchable: bool = True
    boost: float = 1.0
    body: str = ""


def parse_page(source: str) -> PageMeta:
    """Split front matter from ``source`` and return the parsed metadata + body."""
    front, body = _split_front_matter(source)
    title = front.get("title", "") or _first_h1(body)
    # Description: front matter, else the first real paragraph of the body. The
    # site-level default (the third tier) is applied at render time, where the
    # config is available (see docs_site._internal.pipeline.render_page).
    description = front.get("description", "") or _extract_first_paragraph(body)
    return PageMeta(
        title=title,
        description=description,
        canonical=front.get("canonical", ""),
        noindex=front.get("noindex", "").lower() in _TRUTHY,
        og_image=front.get("og_image", ""),
        # Indexed by default; only an explicit falsy value opts a page out.
        searchable=front.get("searchable", "").lower() not in _FALSY,
        boost=_parse_float(front.get("boost", ""), default=1.0),
        body=body,
    )


def _parse_float(raw: str, *, default: float) -> float:
    """Parse a float from front matter, falling back to ``default`` on an empty or bad value."""
    try:
        return float(raw)
    except ValueError:
        return default


def _split_front_matter(source: str) -> tuple[dict[str, str], str]:
    """Return ``(front_matter_dict, body)``; the dict is empty when there is no block."""
    if not source.startswith("---"):
        return {}, source
    # A front-matter block is `---` on its own line, key:value lines, then a
    # closing `---`. Anything after the closing fence is the body.
    lines = source.splitlines()
    if lines[0].strip() != "---":
        return {}, source
    front: dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[i + 1 :])
            return front, body.lstrip("\n")
        key, sep, value = line.partition(":")
        if sep:
            front[key.strip()] = value.strip().strip("'\"")
    # No closing fence: treat the whole thing as body (malformed front matter).
    return {}, source


def _first_h1(body: str) -> str:
    """The text of the page's first ``# H1``, or ``""`` if it has none."""
    match = _H1_RE.search(body)
    return match.group(1).strip() if match else ""


def _extract_first_paragraph(body: str) -> str:
    """
    Derive a meta description from the first real paragraph of a markdown body.

    Walks candidate paragraphs in order and returns the first that reads as
    prose, skipping blocks that make a poor description: raw HTML or a ``<c-*>``
    tag, a snippet include (``--8<-- "path"``), and a version-change note
    ("New in version ..."). Markdown formatting (links, bold, italic, code) is
    reduced to plain text and the result is capped on a word boundary. Returns
    ``""`` when no paragraph qualifies (the caller then falls back further).
    """
    for match in _FIRST_PARAGRAPH.finditer(body):
        raw = match.group(1).strip()
        # A block opening with a tag/comment (``<...>``) or a snippet include
        # (``--8<-- "LICENSE"``) is not prose; skip to the next candidate.
        if raw.startswith(("<", "--8<--")):
            continue
        text = _strip_inline_formatting(raw)
        if not text or _VERSION_ANNOTATION.match(text):
            continue
        if len(text) > _DESCRIPTION_CAP:
            # Trim just under the cap, then drop the partial last word so the
            # description ends on a whole word before the ellipsis.
            text = text[: _DESCRIPTION_CAP - 3].rsplit(" ", 1)[0] + "..."
        return text
    return ""


def _strip_inline_formatting(text: str) -> str:
    """Reduce markdown inline syntax (links, bold, italic, code) to plain text."""
    # Drop images: their alt text does not read as description prose.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    # Drop the empty link shell a badge link leaves behind once its image is
    # gone (``[![alt](img)](url)`` becomes ``[](url)``).
    text = re.sub(r"\[\]\([^)]*\)", "", text)
    # Reference cross-refs ``[text][Key]`` -> ``text``.
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    # Inline links ``[text](url)`` -> ``text``.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Drop code, bold, and asterisk-italic markers.
    text = re.sub(r"[`*]", "", text)
    # Drop emphasis underscores but keep snake_case identifiers intact (so
    # ``template_data`` survives): protect any underscore flanked by word chars,
    # remove the rest, then restore the protected ones.
    text = re.sub(r"(?<=\w)_(?=\w)", "\x00", text)
    return text.replace("_", "").replace("\x00", "_").strip()
