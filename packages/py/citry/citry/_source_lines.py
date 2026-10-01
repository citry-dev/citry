"""Split source text into lines the way Python's parser and LSP clients count them."""

from __future__ import annotations

import re

# Python's tokenizer and the Language Server Protocol end a line only at
# these three sequences. `str.splitlines()` also ends one at a form feed,
# U+2028, and other separators, which shifts every later line number.
_LINE_BREAK = re.compile(r"\r\n|\r|\n")


def source_lines(source: str) -> list[str]:
    """Return the lines of `source`, each with its own line break, split only at CR LF, CR, and LF."""
    lines: list[str] = []
    start = 0
    for match in _LINE_BREAK.finditer(source):
        lines.append(source[start : match.end()])
        start = match.end()
    if start < len(source):
        lines.append(source[start:])
    return lines


def line_break_count(text: str) -> int:
    """Return how many line breaks `text` contains, counting CR LF as one."""
    return sum(1 for _ in _LINE_BREAK.finditer(text))


__all__ = ["line_break_count", "source_lines"]
