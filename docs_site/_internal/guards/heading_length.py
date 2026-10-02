"""
Heading-length guard.

The "On this page" sidebar shows each ``##`` and ``###`` heading on one short
line and cuts off the rest, so a long heading loses the words that tell a
reader what the section is about. This guard reports every such heading whose
visible text is longer than ``MAX_HEADING_CHARS``, with the Markdown source and
line, so the author can shorten it. The writing guide explains how
(docs/best-practices/writing-docs.md, "Write short headings").

Findings are informational: a heading may stay long when the cut-off tail is
still obvious, so the guard never fails a build, not even under ``--strict``.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult
from docs_site._internal.guards.fence_validator import _source_files, scan_fences

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Roughly how many characters fit on one sidebar line before the text is cut off.
MAX_HEADING_CHARS = 24

# The page title (``#``) is not in the sidebar. ``####`` and deeper are listed
# too but are rare in the content pages, so the check stays on the two levels
# that make up almost every sidebar. Python-Markdown also accepts a heading
# with no space after the hashes, so the space is optional here.
_HEADING = re.compile(r"^(#{2,3})(?!#)[ \t]*(.+?)[ \t]*$")
# A trailing ``{ #anchor }`` attribute list sets the id and is not shown.
_ATTR_LIST = re.compile(r"\s*\{[^{}]*\}\s*$")
# Optional closing hashes, as in ``## Title ##``, are not shown either.
_CLOSING_HASHES = re.compile(r"[ \t]+#+$")
# A Markdown link, inline or a ``[text][citry.Symbol]`` cross-reference, shows only its text.
_INLINE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_REFERENCE_LINK = re.compile(r"\[([^\]]*)\]\[[^\]]*\]")
# Outside code spans, inline HTML tags such as ``<br/>`` and emphasis markers
# take no room. Inside a code span, ``<c-if>`` is shown as written.
_CODE_SPAN = re.compile(r"(`[^`]*`)")
_HTML_TAG = re.compile(r"<[^<>]+>")
_EMPHASIS = re.compile(r"\*\*|__|\*")


def visible_heading_text(raw: str) -> str:
    """Return the heading text a reader sees, without anchors, link targets, tags, or markup."""
    # The attribute list sits after any closing hashes, so it goes first.
    text = _ATTR_LIST.sub("", raw)
    text = _CLOSING_HASHES.sub("", text)
    text = _INLINE_LINK.sub(r"\1", text)
    text = _REFERENCE_LINK.sub(r"\1", text)
    parts = [
        part.strip("`") if part.startswith("`") else _EMPHASIS.sub("", _HTML_TAG.sub("", part))
        for part in _CODE_SPAN.split(text)
    ]
    return " ".join("".join(parts).split())


def _fenced_lines(text: str) -> set[int]:
    """Return the 1-based line numbers inside fenced code blocks, fences included."""
    lines: set[int] = set()
    for fence in scan_fences(text):
        # A comment line such as "## step" inside a code block is not a heading.
        end = fence.close_line if fence.close_line is not None else len(text.split("\n"))
        lines.update(range(fence.open_line, end + 1))
    return lines


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        fenced = _fenced_lines(text)
        for lineno, line in enumerate(text.split("\n"), start=1):
            if lineno in fenced:
                continue
            match = _HEADING.match(line)
            if match is None:
                continue
            visible = visible_heading_text(match.group(2))
            if len(visible) > MAX_HEADING_CHARS:
                yield GuardResult.info(
                    guard="heading_length",
                    message=(
                        f"Heading has {len(visible)} characters, over {MAX_HEADING_CHARS}, so the "
                        f"'On this page' sidebar cuts it off: {visible!r}"
                    ),
                    source=label,
                    line=lineno,
                )
