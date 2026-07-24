"""
Catch unclosed code fences, and provide the shared fence scanner.

This runs over the markdown source (before any rendering) and reports an
unclosed code fence, which would otherwise throw off the whole pipeline: the
fence-protection pass would wrap everything after the opening fence as one
unbounded verbatim block.

``scan_fences()`` is the shared primitive the code-language and lexer-alias
guards use too, so all three agree on what a fence is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from docs_site._internal.guards.base import GuardResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docs_site._internal.guards.base import GuardContext

# Opening of a fenced block: optional indent plus three or more backticks or
# tildes. Mirrors the fence-protection pass so the validator and protector agree.
_FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True)
class Fence:
    """A fenced code block found in markdown source."""

    info_string: str  # text after the marker on the opening line, stripped
    lang: str  # first whitespace-delimited token of info_string ("" if none)
    open_line: int  # 1-based line number of the opening fence
    closed: bool
    body: str = ""  # the lines between the opening and closing fence, joined by "\n"


def scan_fences(source: str) -> list[Fence]:
    """Return every fenced code block in the source, flagging unclosed ones."""
    fences: list[Fence] = []
    in_fence = False
    fence_indent = ""
    fence_char = ""
    fence_len = 0
    info_string = ""
    open_line = 0
    body_lines: list[str] = []

    for lineno, line in enumerate(source.split("\n"), start=1):
        if not in_fence:
            m = _FENCE_OPEN.match(line)
            if m:
                fence_indent = m.group(1)
                marker = m.group(2)
                fence_char = marker[0]
                fence_len = len(marker)
                info_string = m.group(3).strip()
                open_line = lineno
                in_fence = True
                body_lines = []
            continue

        # Inside a fence: a closing line is the same char repeated at least
        # fence_len times, at most the opening indent, and not a longer run
        # (which would open a nested fence).
        stripped = line.lstrip()
        current_indent = line[: len(line) - len(stripped)]
        if (
            stripped.startswith(fence_char * fence_len)
            and not stripped.startswith(fence_char * (fence_len + 1))
            and len(current_indent) <= len(fence_indent)
        ):
            lang = info_string.split()[0] if info_string else ""
            fences.append(
                Fence(info_string=info_string, lang=lang, open_line=open_line, closed=True, body="\n".join(body_lines))
            )
            in_fence = False
        else:
            body_lines.append(line)  # an inner line: part of the fence body

    if in_fence:
        lang = info_string.split()[0] if info_string else ""
        fences.append(
            Fence(info_string=info_string, lang=lang, open_line=open_line, closed=False, body="\n".join(body_lines))
        )

    return fences


def _source_files(ctx: GuardContext) -> Iterator[tuple[str, str]]:
    """Yield (relative_label, text) for every markdown source file."""
    for md in sorted(ctx.content_dir.rglob("*.md")):
        yield str(md.relative_to(ctx.content_dir)), md.read_text(encoding="utf-8")


def check(ctx: GuardContext) -> Iterator[GuardResult]:
    for label, text in _source_files(ctx):
        for fence in scan_fences(text):
            if not fence.closed:
                yield GuardResult.error(
                    guard="fence_validator",
                    message=f"Unclosed code fence (opened at line {fence.open_line})",
                    source=label,
                    line=fence.open_line,
                )
