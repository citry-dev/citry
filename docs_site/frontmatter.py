"""
Parse a markdown page's front matter and body.

A page may begin with a ``---`` fenced block of ``key: value`` lines (title,
description, ...). This splits that block from the body and reads the keys the
layout uses. The title falls back to the page's first ``# H1`` when front
matter does not set one.

This is a deliberately small parser for the keys the site uses today; it is not
a full YAML implementation. Nested structures are not needed yet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_TRUTHY = {"true", "1", "yes", "on"}


@dataclass
class PageMeta:
    """Front-matter values the ``DocPage`` layout reads, plus the page body."""

    title: str = ""
    description: str = ""
    canonical: str = ""
    noindex: bool = False
    body: str = ""


def parse_page(source: str) -> PageMeta:
    """Split front matter from ``source`` and return the parsed metadata + body."""
    front, body = _split_front_matter(source)
    title = front.get("title", "") or _first_h1(body)
    return PageMeta(
        title=title,
        description=front.get("description", ""),
        canonical=front.get("canonical", ""),
        noindex=front.get("noindex", "").lower() in _TRUTHY,
        body=body,
    )


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
