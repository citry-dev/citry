"""Split source text into lines the way Python's parser and LSP clients count them."""

from __future__ import annotations

import bisect
import functools
import re

# Python's tokenizer and the Language Server Protocol end a line only at
# these three sequences. `str.splitlines()` also ends one at a form feed,
# U+2028, and other separators, which shifts every later line number.
_LINE_BREAK = re.compile(r"\r\n|\r|\n")
# The same three line breaks, matched in UTF-8 bytes. Both break characters
# are ASCII, so a byte match never splits a character.
_LINE_BREAK_BYTES = re.compile(rb"\r\n|\r|\n")
# The other characters `str.splitlines()` ends a line at. Source rarely has
# them, and without them the fast built-in split gives the same lines.
_OTHER_SPLITLINES_BREAKS = re.compile("[\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]")


def source_lines(source: str) -> list[str]:
    """Return the lines of `source`, each with its own line break, split only at CR LF, CR, and LF."""
    if _OTHER_SPLITLINES_BREAKS.search(source) is None:
        return source.splitlines(keepends=True)
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


@functools.lru_cache(maxsize=8)
def _byte_line_starts(source: str) -> tuple[bytes, tuple[int, ...]]:
    """Return `source` as UTF-8 and the byte offset where each of its lines starts."""
    encoded = source.encode("utf-8")
    # The checker asks for many positions in the same source, one per
    # finding. Finding each line start once makes the cost grow with the
    # source's length, not with its length times the number of findings.
    starts = (0, *(match.end() for match in _LINE_BREAK_BYTES.finditer(encoded)))
    return encoded, starts


def byte_offset_position(source: str, offset: int) -> tuple[int, int]:
    """
    Return the line and column of a UTF-8 byte offset in `source`.

    Both count from 0. Lines end at CR LF, CR, or LF, and the column counts
    UTF-16 code units, as the Language Server Protocol does. A negative
    offset counts as 0 and an offset past the end of `source` counts as the
    end. An offset inside a multi-byte character raises `UnicodeDecodeError`.
    """
    encoded, starts = _byte_line_starts(source)
    # Clamping keeps every answer a valid editor position.
    offset = max(0, min(offset, len(encoded)))
    line = bisect.bisect_right(starts, offset) - 1
    # The CR ends a line on its own, so an offset between the CR and the LF
    # of a CR LF is at column 0 of the next line, as `line_break_count`
    # counts the text before it.
    if offset > starts[line] and encoded[offset - 1 : offset] == b"\r":
        return line + 1, 0
    text = encoded[starts[line] : offset].decode("utf-8")
    return line, len(text.encode("utf-16-le")) // 2


__all__ = ["byte_offset_position", "line_break_count", "source_lines"]
