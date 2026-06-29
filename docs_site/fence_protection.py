"""
Pass 0: protect code from the Pass 1 citry render.

Pass 1 renders the markdown body as a citry template so authoring directives
(``<c-version />``, ``<c-example />``, ...) expand. Without this pre-pass, citry
would also try to parse the ``<c-*>`` tags and ``{{ ... }}`` expressions that
appear *inside* documentation code examples. The fix wraps every code region in
``<c-raw>...</c-raw>`` so citry emits it literally; the markdown pass then turns
it into ``<pre>``/``<code>`` (escaping the angle brackets there).

Handles fenced code blocks (``` and ~~~) and inline code spans that contain
citry-parseable syntax. Four-space indented code blocks are not handled (the
project convention is fenced blocks).
"""

from __future__ import annotations

import re

# Opening of a fenced block: optional indent, then 3+ backticks or tildes.
_FENCE_OPEN = re.compile(r"^(\s*)(```+|~~~+)")

# An inline backtick span that holds citry syntax: a tag/expression/comment.
_CITRY_IN_INLINE = re.compile(r"`[^`]*(<|\{\{|\{#)[^`]*`")


def protect_fences(source: str) -> str:
    """Wrap every code region in ``<c-raw>...</c-raw>`` so citry leaves it literal."""
    lines = source.split("\n")
    out: list[str] = []
    in_fence = False
    fence_indent = ""
    fence_char = ""
    fence_len = 0

    for line in lines:
        if not in_fence:
            match = _FENCE_OPEN.match(line)
            if match:
                fence_indent = match.group(1)
                marker = match.group(2)
                fence_char = marker[0]
                fence_len = len(marker)
                out.append("<c-raw>")
                out.append(line)
                in_fence = True
                continue
            out.append(_protect_inline_code(line))
        else:
            out.append(line)
            stripped = line.lstrip()
            current_indent = line[: len(line) - len(stripped)]
            # Closes the fence: same marker char, at least as many, not a longer
            # run (a nested opener), at the same or lesser indent.
            if (
                stripped.startswith(fence_char * fence_len)
                and not stripped.startswith(fence_char * (fence_len + 1))
                and len(current_indent) <= len(fence_indent)
            ):
                out.append("</c-raw>")
                in_fence = False

    # An unclosed fence: close the raw block so the page still renders.
    if in_fence:
        out.append("</c-raw>")

    return "\n".join(out)


def _protect_inline_code(line: str) -> str:
    """Wrap inline backtick spans that contain citry syntax in ``<c-raw>``."""
    if not _CITRY_IN_INLINE.search(line):
        return line

    result: list[str] = []
    i = 0
    while i < len(line):
        if line[i] == "`":
            end = line.find("`", i + 1)
            if end == -1:
                result.append(line[i:])
                break
            span = line[i + 1 : end]
            if "<" in span or "{{" in span or "{#" in span:
                result.append(f"<c-raw>`{span}`</c-raw>")
            else:
                result.append(f"`{span}`")
            i = end + 1
        else:
            result.append(line[i])
            i += 1

    return "".join(result)
