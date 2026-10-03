"""
Pass 0: protect code from the Pass 1 citry render.

Pass 1 renders the markdown body as a citry template so the custom ``<c-*>`` tags
(``<c-version />``, ``<c-example />``, ...) expand. Without this pre-pass, citry
would also try to parse the ``<c-*>`` tags and ``{{ ... }}`` expressions that
appear *inside* documentation code examples. The fix wraps every code region in
``<c-raw>...</c-raw>`` so citry emits it literally; the markdown pass then turns
it into ``<pre>``/``<code>`` (escaping the angle brackets there).

Handles fenced code blocks (``` and ~~~), four-space or tab-indented code, and
inline code spans that contain citry-parseable syntax.

Inline code spans follow Markdown's rules: a span opens with a run of backticks
and closes at the next run of exactly the same length, and it may continue onto
the next line of the same paragraph (Markdown shows that line break as a
space). So the pass collects each paragraph's lines and protects its spans as a
whole; protecting each line separately would leave half a tag for citry to
parse.

Indentation means code only relative to the block a line belongs to. The body
of an admonition (``!!! note``), a collapsible block (``??? note``), a content
tab (``=== "Tab"``), or a list item is indented by four spaces, yet it is prose:
its inline code spans are protected like those of a top-level paragraph, and a
line counts as indented code only when it is indented four more spaces than
that body. As in Markdown, a four-space-indented paragraph straight after a
list item belongs to that item, so it is prose rather than code, and a more
deeply indented line inside a paragraph continues that paragraph rather than
starting code.

A block that starts with an HTML comment, a block-level HTML tag (such as
``<div>``), or a citry component tag is raw HTML to Markdown, which finds no
code spans in it. Its lines are checked one at a time, so a backtick inside a
comment never pairs with one on a later line.

One limitation: a code region whose text is itself ``<c-raw>`` (or a whole
``<c-raw>...</c-raw>``) cannot be protected by wrapping, because the wrapper's
own tag collides with the inner one. A page that shows raw citry syntax that
way (the release notes, built from CHANGELOG.md, which document the ``<c-raw>``
feature) skips this pass entirely by rendering with
``render_page(..., run_citry_pass=False)``; its markdown pass then escapes the
angle brackets on its own.
"""

from __future__ import annotations

import re

from markdown.util import BLOCK_LEVEL_ELEMENTS

# Opening of a fenced block: optional indent, then 3+ backticks or tildes.
_FENCE_OPEN = re.compile(r"^(\s*)(```+|~~~+)")

# Text inside an inline code span that citry would parse: a tag, an
# expression, or a comment. A span holding none of these is left untouched.
_CITRY_INLINE_MARKERS = ("<", "{{", "{#")

# A run of backticks; its length decides which later run closes the span.
_BACKTICK_RUN = re.compile(r"`+")

# A line that opens a block whose body is indented four spaces: an admonition,
# a collapsible block, a content tab, or a list item.
_CONTAINER_OPEN = re.compile(r"^(?:!!!|\?\?\?\+?|===)\s|^(?:[-*+]|\d+\.)\s")

# A horizontal rule such as `* * *` starts like a list item but opens no block.
_THEMATIC_BREAK = re.compile(r"^(?:[-*_][ \t]*){3,}$")

# A `#` heading. It ends a paragraph even without a blank line before it, so
# no code span continues from the line above into it.
_HEADING = re.compile(r"^#{1,6}(?:\s|$)")

# A table row. Markdown reads each row's inline code on its own, but only when
# the row starts a block; inside a paragraph it is ordinary text.
_TABLE_ROW = re.compile(r"^\|")

# The start of a block that Markdown passes through as raw HTML: a comment, a
# block-level tag such as `<div>`, or a citry component tag, which Pass 1
# turns into such HTML. The docs pipeline also treats `<button>` as
# block-level. An inline tag such as `<b>` starts an ordinary paragraph.
_RAW_HTML_BLOCK_OPEN = re.compile(
    r"^(?:<!--|<c-|</?(?:" + "|".join([*BLOCK_LEVEL_ELEMENTS, "button"]) + r")(?=[\s/>]|$))",
    re.IGNORECASE,
)

# Python-Markdown nests block content four spaces deeper than its opener.
_CONTAINER_STEP = 4

# Events compiles @c-* and :c-* by scanning template source before the parser
# sees <c-raw>. Replace only their leading sigil while code is protected, then
# restore it after the Citry render. Private-use characters keep the armored
# source inert without changing what the Markdown code block ultimately shows.
_EVENT_AT_SENTINEL = ""
_STATE_BIND_SENTINEL = ""


def protect_fences(source: str) -> str:
    """Wrap every code region in ``<c-raw>...</c-raw>`` so citry leaves it literal."""
    lines = source.split("\n")
    out: list[str] = []
    in_fence = False
    fence_indent = ""
    fence_char = ""
    fence_len = 0
    # The body indent of each open admonition, tab, or list item, innermost
    # last, with whether it is a list item. Indentation inside a body is
    # measured from its body indent.
    containers: list[tuple[int, bool]] = []
    # The prose lines of the paragraph being read. Its inline code is
    # protected once the paragraph ends, since a span may cross its lines.
    paragraph: list[str] = []
    # Whether the current block began as raw HTML (see _RAW_HTML_BLOCK_OPEN).
    # Markdown finds no code spans in it, so a backtick there must not pair
    # with one on a later line.
    in_html_block = False

    def flush_paragraph() -> None:
        if paragraph:
            out.extend(_protect_inline_code("\n".join(paragraph)).split("\n"))
            paragraph.clear()

    for line in lines:
        if not in_fence:
            stripped = line.lstrip(" \t")
            indent = _indent_width(line)
            if not stripped:
                # A blank line ends the paragraph, and no code span crosses it.
                flush_paragraph()
                in_html_block = False
                out.append(line)
                continue
            # A line indented less than a body has left that block.
            while containers and indent < containers[-1][0]:
                if containers[-1][1] and paragraph:
                    # A list item's paragraph takes less indented lines as
                    # its own (lazy continuation), so the item stays open.
                    break
                containers.pop()
                # An admonition or tab body has no lazy continuation, so its
                # paragraph ends with it.
                flush_paragraph()
            body_indent = containers[-1][0] if containers else 0
            # Markdown treats four more spaces (or a tab) than the enclosing
            # body as code. Check it before fence discovery so an indented ```
            # line is not mistaken for a fenced-block opener. Indented code
            # cannot interrupt a paragraph, so inside one the line is prose.
            if not paragraph and indent - body_indent >= _CONTAINER_STEP:
                out.append(_protect_indented_code(line))
                continue
            if _THEMATIC_BREAK.match(stripped):
                # A rule is a whole block on one line and ends any paragraph.
                flush_paragraph()
                out.append(line)
                continue
            if _CONTAINER_OPEN.match(stripped):
                is_list = stripped[0] not in "!?="
                in_list = bool(containers) and containers[-1][1]
                if paragraph and not (is_list and in_list):
                    # Markdown starts a list or admonition only after a blank
                    # line; inside a paragraph this line is more of its text.
                    # In a list, a new marker starts the next item instead.
                    paragraph.append(line)
                    continue
                # A new block starts here, so the previous paragraph has ended.
                flush_paragraph()
                containers.append((indent + _CONTAINER_STEP, is_list))
                if not is_list:
                    # An admonition or tab title is one line; its body starts below.
                    out.append(_protect_inline_code(line))
                else:
                    # A list item's text continues onto the lines below it.
                    paragraph.append(line)
                continue
            match = _FENCE_OPEN.match(line)
            if match:
                flush_paragraph()
                fence_indent = match.group(1)
                marker = match.group(2)
                fence_char = marker[0]
                fence_len = len(marker)
                out.append("<c-raw>")
                out.append(line)
                in_fence = True
                continue
            if _HEADING.match(stripped) or (not paragraph and _TABLE_ROW.match(stripped)):
                flush_paragraph()
                out.append(_protect_inline_code(line))
                continue
            if in_html_block or (not paragraph and _RAW_HTML_BLOCK_OPEN.match(stripped)):
                # Markdown finds no code spans in raw HTML, so protect each
                # line on its own and never pair backticks across lines.
                in_html_block = True
                out.append(_protect_inline_code(line))
                continue
            paragraph.append(line)
        else:
            out.append(_armor_preparse_bindings(line))
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

    # The last paragraph has no blank line after it to end it.
    flush_paragraph()
    # An unclosed fence: close the raw block so the page still renders.
    if in_fence:
        out.append("</c-raw>")

    return "\n".join(out)


def restore_protected_code(source: str) -> str:
    """Restore binding sigils armored for the Citry template pass."""
    return source.replace(_EVENT_AT_SENTINEL, "@").replace(_STATE_BIND_SENTINEL, ":")


def _indent_width(line: str) -> int:
    """Return the indentation width of a line, counting a tab as four spaces."""
    width = 0
    for char in line:
        if char == " ":
            width += 1
        elif char == "\t":
            width += _CONTAINER_STEP
        else:
            break
    return width


def _protect_inline_code(text: str) -> str:
    """
    Wrap the inline code spans in ``text`` that contain citry syntax in ``<c-raw>``.

    ``text`` is one paragraph, possibly several lines. A span opens at a run of
    backticks that no backslash escapes and closes at the next run of exactly
    the same length, even on a later line. A run with no such closer is plain
    text, as in Markdown.
    """
    # Most paragraphs hold no code or no citry syntax; skip the scan for them.
    if "`" not in text or not any(marker in text for marker in _CITRY_INLINE_MARKERS):
        return text

    result: list[str] = []
    copied = 0
    search_from = 0
    while (opener := _BACKTICK_RUN.search(text, search_from)) is not None:
        start, after_opener = opener.span()
        if _is_backslash_escaped(text, start):
            # An escaped backtick is literal; the rest of its run may still open a span.
            search_from = start + 1
            continue
        width = after_opener - start
        closer = _find_closing_run(text, after_opener, width)
        if closer is None:
            # Markdown shows an unmatched run as literal backticks.
            search_from = after_opener
            continue
        span = text[after_opener:closer]
        if any(marker in span for marker in _CITRY_INLINE_MARKERS):
            ticks = "`" * width
            result.append(text[copied:start])
            result.append(f"<c-raw>{ticks}{_armor_preparse_bindings(span)}{ticks}</c-raw>")
            copied = closer + width
        search_from = closer + width

    result.append(text[copied:])
    return "".join(result)


def _is_backslash_escaped(text: str, index: int) -> bool:
    """Return whether an odd number of backslashes sits right before ``index``."""
    backslashes = 0
    while index - backslashes > 0 and text[index - backslashes - 1] == "\\":
        backslashes += 1
    return backslashes % 2 == 1


def _find_closing_run(text: str, start: int, width: int) -> int | None:
    """Return where the first backtick run of exactly ``width`` starts, searching from ``start``."""
    # A longer or shorter run inside the span is part of its text, not a closer.
    for run in _BACKTICK_RUN.finditer(text, start):
        if run.end() - run.start() == width:
            return run.start()
    return None


def _protect_indented_code(line: str) -> str:
    """Protect Citry syntax on one Markdown indented-code line."""
    if not any(marker in line for marker in ("<c-", "{{", "{#", "@c-", ":c-")):
        return line
    return f"<c-raw>{_armor_preparse_bindings(line)}</c-raw>"


def _armor_preparse_bindings(source: str) -> str:
    """Hide Events binding prefixes from their pre-parser source rewrite."""
    return source.replace("@c-", f"{_EVENT_AT_SENTINEL}c-").replace(":c-", f"{_STATE_BIND_SENTINEL}c-")
