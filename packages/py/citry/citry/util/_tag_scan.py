"""
Find the real ``</head>`` and ``</body>`` end tags in rendered HTML, the way a browser reads them.

Citry puts CSS before the page's ``</head>`` and JS before its ``</body>``.
Searching the HTML as text for those strings also finds them inside an
attribute value, a comment, or the text of a ``<script>``, and an
interactive (hydrated) page writes ``<`` and ``>`` raw in attribute values.
A tag inserted there lands inside the attribute, and its own ``"`` ends the
attribute early, so the rest of the value becomes markup.

``scan_document_tags`` reads the HTML token by token with the browser's
tokenizer rules: quoted attribute values, comments, bogus comments, and the
text of raw-text elements such as ``<script>``, ``<style>`` and
``<textarea>`` are skipped. A few regular expressions step over ordinary
tags and text, so Python only runs for the tags that matter here.

Whether ``<style>`` or ``<script>`` starts raw text depends on where the
element sits. Inside SVG and MathML the browser reads them as ordinary
elements, so the scan keeps track of the SVG and MathML elements it is
inside. Inside ``<select>`` or ``<template>`` the browser may ignore a
raw-text element such as ``<style>`` or ``<script>``, or an ``<svg>``. Some markup makes the tracking unreliable: an
HTML element inside SVG, an ``<svg>`` inside ``<select>``, or a fragment
that may be inserted into any element. From there the scan follows both
possible readings of each raw-text element and keeps only the tag
positions that every reading agrees on.

The scan treats output that starts with a doctype or ``<html>`` as a whole
page the browser opens on its own, not as a fragment.

A position the scan is unsure of is left out. Callers then put CSS at the
start of the HTML, which is outside any tag (though CSS before a doctype
switches the page to quirks mode), and JS at its end.
"""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass

# HTML whitespace as the tokenizer sees it. A carriage return is read as a
# line feed before tokenizing, so it counts as whitespace too.
_WS = "\\t\\n\\f\\r "
# A tag name runs to whitespace, "/" or ">". The group is atomic so a tag
# that never closes fails at once instead of retrying shorter names.
_TAG_NAME = rf"(?>[^{_WS}/>]*)"
_NAME_END = rf"(?=[{_WS}/>])"

# The attributes of a start or end tag, up to and including its ``>``.
# Each part follows one tokenizer state, so the match ends exactly where the
# browser ends the tag:
# - ``/`` and whitespace separate attributes;
# - a name runs to whitespace, ``/``, ``>`` or ``=``, and may start with ``=``;
# - after a name, ``=`` (whitespace allowed around it) starts a value, which is
#   double-quoted, single-quoted, or runs unquoted to whitespace or ``>``.
# The groups are atomic, so a tag with no end (a quote that never closes)
# fails at once instead of trying other splits, and the scan stops there,
# as the browser reads the rest of the page as part of that tag.
_ATTRS = (
    rf"(?>(?:[{_WS}/]+"
    rf"|(?>=[^{_WS}/>=]*|[^{_WS}/>=]+)"
    rf"(?>[{_WS}]*=[{_WS}]*(?>\"[^\"]*\"|'[^']*'|[^{_WS}>\"'][^{_WS}>]*|(?=>))|(?![{_WS}]*=))"
    r")*)>"
)
# Ends a start tag that is not self-closing. "a=b/>" is not self-closing
# either, but this rejects it too, and the slower step handles it exactly.
_NOT_SELF_CLOSED = r"(?<=[^/]>)"

# Elements whose start tag switches the tokenizer to raw text (or, for
# ``<plaintext>``, makes the rest of the page text) when they are HTML
# elements.
_RAW_TEXT = ("script", "style", "title", "textarea", "xmp", "iframe", "noembed", "noframes", "noscript", "plaintext")
# SVG and MathML elements whose content the browser reads as HTML.
_INTEGRATION = ("foreignobject", "desc", "title", "annotation-xml", "mi", "mo", "mn", "ms", "mtext")
# Start tags that make the browser leave SVG or MathML and read HTML again.
_BREAKOUT = (
    "b", "big", "blockquote", "body", "br", "center", "code", "dd", "div", "dl", "dt", "em", "embed",
    "h1", "h2", "h3", "h4", "h5", "h6", "head", "hr", "i", "img", "li", "listing", "menu", "meta", "nobr",
    "ol", "p", "pre", "ruby", "s", "small", "span", "strong", "strike", "sub", "sup", "table", "tt", "u",
    "ul", "var", "font",
)  # fmt: skip


def _names(names: tuple[str, ...]) -> str:
    return "|".join(names)


def _start_tags_except(names: tuple[str, ...]) -> str:
    # A lookbehind after the whole tag name checks it against each excluded
    # name; this is cheaper than a lookahead with every name before it.
    excluded = "".join(f"(?<!<{name})" for name in names)
    return rf"<[A-Za-z]{_TAG_NAME}{excluded}{_ATTRS}"


def _end_tags_except(names: tuple[str, ...]) -> str:
    excluded = "".join(f"(?<!</{name})" for name in names)
    return rf"</[A-Za-z]{_TAG_NAME}{excluded}{_ATTRS}"


# Text, then comments and bogus comments: the same in every reading. Each
# pattern tries text, then tags, then these, since tags are far more common.
_TEXT = r"[^<]+"
_COMMENTS = (
    # A comment ends at the first ``-->`` or ``--!>`` after ``<!--``, and
    # ``<!-->`` and ``<!--->`` end at once.
    r"<!--(?>-?>|(?s:.*?)(?:-->|--!>))"
    # A doctype or bogus comment ends at the first ``>``, even inside quotes.
    # ``<![CDATA[`` is matched case-sensitively, as the tokenizer does.
    r"|<!(?!--|(?-i:\[CDATA\[))[^>]*>"
    r"|<\?[^>]*>"
    r"|</>"
    r"|</(?![A-Za-z>])[^>]*>"
    # A ``<`` that starts no tag is text.
    r"|<(?![A-Za-z!/?])"
)
_CDATA = r"(?-i:<!\[CDATA\[)"

# Inside SVG or MathML: tokens that leave the open elements unchanged.
# - A self-closing tag opens nothing. This pattern takes only tags whose
#   attribute values are all quoted or missing, where a "/" before ">" is
#   always the self-closing mark; in "x= />" or "x=a"/>" the "/" belongs to
#   an unquoted value and the element stays open, so such tags go to the
#   exact step in Python.
# - An element whose content is only these tokens is skipped with its end
#   tag, up to two levels deep, so ordinary icons cost no Python steps. Its
#   name must not be one whose start tag makes the browser leave SVG or
#   MathML, or one whose content the browser reads as HTML.
# Every other tag goes to the exact step in Python.
_QUOTED_ATTRS = rf"(?>(?:[{_WS}]+[^{_WS}/>=\"'<]+(?:[{_WS}]*=[{_WS}]*(?:\"[^\"]*\"|'[^']*'))?)*)[{_WS}]*"
_SELF_CLOSED_QUOTED = rf"<[A-Za-z]{_TAG_NAME}" + "".join(f"(?<!<{name})" for name in _BREAKOUT) + rf"{_QUOTED_ATTRS}/>"
_NESTED_NAME_EXCLUDED = "".join(f"(?<!<{name})" for name in (*_BREAKOUT, *_INTEGRATION))
# Each copy of the pattern needs its own group names; re refuses a repeated name.
_names_used = iter(range(1_000_000))


def _foreign_skipped(levels: int) -> str:
    """
    Return the pattern for tokens that leave the open SVG or MathML elements unchanged.

    It includes whole elements nested up to ``levels`` deep.
    """
    pair = f"pair{next(_names_used)}"
    tokens = (
        _TEXT
        + "|"
        + _SELF_CLOSED_QUOTED
        # An element whose content is only text, of any name except those
        # that make the browser leave SVG or MathML; text reads the same even
        # where the browser reads the content as HTML.
        + rf"|<(?P<{pair}>[A-Za-z]{_TAG_NAME})"
        + "".join(f"(?<!<{name})" for name in _BREAKOUT)
        + rf"{_ATTRS}{_NOT_SELF_CLOSED}[^<]*</(?P={pair}){_NAME_END}{_ATTRS}"
        + "|"
        + _COMMENTS
        + rf"|{_CDATA}(?s:.*?)\]\]>"
    )
    if levels > 0:
        nested = f"nest{next(_names_used)}"
        tokens += (
            rf"|<(?P<{nested}>[A-Za-z]{_TAG_NAME}){_NESTED_NAME_EXCLUDED}{_ATTRS}{_NOT_SELF_CLOSED}"
            rf"(?>(?:{_foreign_skipped(levels - 1)})*)</(?P={nested}){_NAME_END}{_ATTRS}"
        )
    return tokens


# Two levels cover icons built from groups of paths; each level adds a copy
# of the pattern, so deeper nesting goes to the exact step instead.
_FOREIGN_SKIPPED_LEVELS = 2

# re.ASCII keeps case-insensitive matching to ASCII letters, as browsers do:
# without it, "\u017f" (long s) would match "s" and "<\u017fcript>" would be
# taken for a script element.
_FLAGS = re.IGNORECASE | re.ASCII

# Each pattern steps over the tokens that change nothing for its reading
# (group "bulk"), then matches the next token that does, if any.
_HEAD_BODY_END = rf"(?P<end></(?P<end_name>head|body){_NAME_END}{_ATTRS})"
# Start tags that change how the rest of the page is read. In plain HTML, a
# simple <svg> or <math> block (closed, holding nothing that leaves it) is
# stepped over in one go, so a page full of icons costs few Python steps.
_HTML_TAGS = (*_RAW_TEXT, "svg", "math", "select", "template", "frameset")
_HTML_SKIPPED = (
    _TEXT
    + "|"
    + _start_tags_except(_HTML_TAGS)
    + "|"
    + _end_tags_except(("head", "body"))
    + "|"
    + _COMMENTS
    + rf"|{_CDATA}[^>]*>"
)
_HTML_TOKENS = rf"{_HEAD_BODY_END}|(?P<start><(?P<start_name>{_names(_HTML_TAGS)}){_NAME_END}{_ATTRS})"
_HTML_TOKEN = rf"(?:{_HTML_TOKENS})?"


def _foreign_block(name: str) -> str:
    skipped = _foreign_skipped(_FOREIGN_SKIPPED_LEVELS)
    return rf"<{name}{_NAME_END}{_ATTRS}{_NOT_SELF_CLOSED}(?>(?:{skipped})*)</{name}{_NAME_END}{_ATTRS}"


_HTML = re.compile(
    rf"(?P<bulk>(?>(?:{_HTML_SKIPPED}|{_foreign_block('svg')}|{_foreign_block('math')})*)){_HTML_TOKEN}",
    _FLAGS,
)
# Inside <select> or <template>, until its end tag. The browser may ignore
# an <svg> there, so SVG and MathML blocks are not stepped over, and the
# end tags that close these elements are tokens of their own.
_HTML_IN_CONTEXT = re.compile(
    r"(?P<bulk>(?>(?:"
    + _TEXT
    + "|"
    + _start_tags_except(_HTML_TAGS)
    + "|"
    + _end_tags_except(("head", "body", "select", "template"))
    + "|"
    + _COMMENTS
    + rf"|{_CDATA}[^>]*>"
    + r")*))"
    + rf"(?:(?P<context_end></(?P<context_name>select|template){_NAME_END}{_ATTRS})|{_HTML_TOKENS})?",
    _FLAGS,
)
# Inside SVG or MathML, before anything makes the tracking unreliable.
_FOREIGN = re.compile(
    rf"(?P<bulk>(?>(?:{_foreign_skipped(_FOREIGN_SKIPPED_LEVELS)})*))"
    rf"(?:(?P<start><(?P<start_name>[A-Za-z]{_TAG_NAME}){_ATTRS})"
    rf"|(?P<end></(?P<end_name>[A-Za-z]{_TAG_NAME}){_ATTRS}))?",
    _FLAGS,
)
# Where the browser may read raw-text elements either way.
_UNSURE = re.compile(
    r"(?P<bulk>(?>(?:"
    + _TEXT
    + "|"
    + _start_tags_except(_RAW_TEXT)
    + "|"
    + _end_tags_except(("head", "body"))
    + "|"
    + _COMMENTS
    + r")*))"
    + rf"(?:{_HEAD_BODY_END}"
    + rf"|(?P<start><(?P<start_name>{_names(_RAW_TEXT)}){_NAME_END}{_ATTRS})"
    + rf"|(?P<cdata>{_CDATA}))?",
    _FLAGS,
)
_TAG_END = re.compile(_ATTRS, _FLAGS)
_END_TAG = {name: re.compile(rf"</{name}{_NAME_END}", _FLAGS) for name in (*_RAW_TEXT, *_INTEGRATION)}
_SCRIPT_TOKEN = re.compile(rf"<!--|-->|<(?P<close>/?)script{_NAME_END}", _FLAGS)
# One attribute or separator of a tag, as in _ATTRS.
_TAG_START = re.compile(rf"<[^{_WS}/>]*")
_ATTR_ITEM = re.compile(
    rf"(?P<sep>[{_WS}/]+)"
    rf"|(?>=[^{_WS}/>=]*|[^{_WS}/>=]+)"
    rf"(?>[{_WS}]*=[{_WS}]*(?>\"[^\"]*\"|'[^']*'|[^{_WS}>\"'][^{_WS}>]*|(?=>))|(?![{_WS}]*=))",
    _FLAGS,
)
# The scan treats output that starts with a doctype or ``<html>`` as a whole
# page the browser opens on its own. Anything else may be a fragment
# inserted into any element, even an SVG element, so it is read in every
# way from the start.
_DOCUMENT_START = re.compile(rf"[{_WS}]*<(?:!doctype[{_WS}>]|html[{_WS}/>])", _FLAGS)

# How the browser may be reading the HTML at a point:
_HTML_MODE = 0  # as HTML, exactly as the scan does;
_HTML_CONTEXT = 1  # as HTML inside <select> or <template>, where raw text may be ignored;
_FOREIGN_MODE = 2  # inside the SVG or MathML elements the reading tracks;
_UNSURE_MODE = 3  # in a way the scan cannot track, so raw text is read both ways.

# Each reading the scan follows costs one more pass over the rest of the
# page until it agrees with another reading again. Past this many at once
# the scan gives up and reports no positions.
_MAX_READINGS = 16
# Readings that went out of step may search the rest of the page again and
# again. Past this many characters read per character of HTML, the scan
# gives up, so it stops in time on a page built to slow it down.
_WORK_PER_CHAR = 24
# Past this many open SVG and MathML elements, or open <select> and
# <template> elements, a reading stops tracking them.
_MAX_FOREIGN_DEPTH = 256
_MAX_CONTEXT_DEPTH = 64
# How many "</" an end-tag search checks one by one before it falls back
# to a regex search over the rest.
_FIND_TRIES = 32


@dataclass(frozen=True, slots=True)
class DocumentTags:
    """Positions of the end tags every reading of the HTML agrees on, in document order."""

    head_ends: tuple[int, ...]
    body_ends: tuple[int, ...]


_EMPTY = DocumentTags((), ())

# One reading: position, mode, the SVG and MathML elements it is inside, a
# tie-breaker for the heap, and the end tags it found as ("/head" or
# "/body", position).
_Events = frozenset[tuple[str, int]]
_Reading = tuple[int, int, tuple[str, ...], _Events]


class _GiveUpError(Exception):
    """The scan went past its work limit."""


class _Scan:
    """The page and the work done on it, shared by every reading."""

    def __init__(self, html: str) -> None:
        self.html = html
        self.budget = _WORK_PER_CHAR * len(html) + 100_000
        # For each end tag name: (searched from, match start, match end), so
        # readings that search from nearby places reuse one search.
        self.found: dict[str, tuple[int, int, int]] = {}

    def spend(self, characters: int) -> None:
        self.budget -= characters
        if self.budget < 0:
            raise _GiveUpError

    def end_tag(self, name: str, pos: int) -> tuple[int, int]:
        """Return (start, end of name) of the first ``</name`` at or after ``pos``, or (-1, -1)."""
        cached = self.found.get(name)
        if cached is not None and cached[0] <= pos and (cached[1] < 0 or pos <= cached[1]):
            return cached[1], cached[2]
        start, end = self._search_end_tag(name, pos)
        self.spend((end if end >= 0 else len(self.html)) - pos)
        self.found[name] = (pos, start, end)
        return start, end

    def _search_end_tag(self, name: str, pos: int) -> tuple[int, int]:
        html = self.html
        pattern = _END_TAG[name]
        # A case-insensitive regex search reads every character in Python's
        # regex engine; str.find jumps between "</" far faster, and script or
        # style text rarely holds many of them.
        for _ in range(_FIND_TRIES):
            found = html.find("</", pos)
            if found < 0:
                return -1, -1
            match = pattern.match(html, found)
            if match is not None:
                return match.start(), match.end()
            pos = found + 2
        match = pattern.search(html, pos)
        return (match.start(), match.end()) if match is not None else (-1, -1)


def scan_document_tags(html: str, *, first_head_end_only: bool = False) -> DocumentTags:
    """
    Return the ``</head>`` and ``</body>`` tags a browser reads as real tags in ``html``.

    A tag inside an attribute value, a comment, or raw text is not reported.
    When the HTML can be read in more than one way (see the module
    docstring), only the tags every reading finds are reported, and when
    the scan cannot tell, nothing is.

    With ``first_head_end_only``, the scan stops as soon as the first real
    ``</head>`` is certain, and only ``head_ends[0]`` is meaningful.
    """
    scan = _Scan(html)
    mode = _HTML_MODE if _DOCUMENT_START.match(html) is not None else _UNSURE_MODE
    # Readings are advanced in position order, so two that reach the same
    # point in the same state are merged, keeping only the tags both found.
    heap: list[tuple[int, int, tuple[str, ...], int, _Events]] = [(0, mode, (), 0, frozenset())]
    finished: list[_Events] = []
    order = 0
    try:
        while heap:
            pos, mode, stack, _, events = heapq.heappop(heap)
            while heap and heap[0][:3] == (pos, mode, stack):
                events &= heapq.heappop(heap)[4]
            for reading in _advance(scan, (pos, mode, stack, events)):
                if reading[0] < 0:
                    finished.append(reading[3])
                else:
                    order += 1
                    heapq.heappush(heap, (reading[0], reading[1], reading[2], order, reading[3]))
            if len(heap) > _MAX_READINGS:
                return _EMPTY
            # With a single reading left, a </head> that it and every finished
            # reading found is the first real one: later tags all come after it.
            if first_head_end_only and len(heap) == 1:
                common = frozenset.intersection(heap[0][4], *finished)
                if any(kind == "/head" for kind, _ in common):
                    return _tags(common)
    except _GiveUpError:
        return _EMPTY
    if not finished:  # pragma: no cover - every reading ends in ``finished``
        return _EMPTY
    return _tags(frozenset.intersection(*finished))


def _tags(common: _Events) -> DocumentTags:
    """Sort the agreed end tags into a ``DocumentTags``."""
    ordered = sorted(common, key=lambda event: event[1])
    return DocumentTags(
        head_ends=tuple(start for kind, start in ordered if kind == "/head"),
        body_ends=tuple(start for kind, start in ordered if kind == "/body"),
    )


def _advance(scan: _Scan, reading: _Reading) -> list[_Reading]:
    """
    Step one reading to its next token that matters and return the readings that follow it.

    A reading at position ``-1`` has finished: the page ended, or the rest
    of it is inside a tag, comment or raw text that never closes.
    """
    pos, mode, stack, events = reading
    pattern = (_HTML, _HTML_IN_CONTEXT, _FOREIGN, _UNSURE)[mode]
    match = pattern.match(scan.html, pos)
    if match is None:  # pragma: no cover - every pattern can match empty, so it always matches
        return [(-1, mode, stack, events)]
    scan.spend(match.end() - pos)
    token_start = match.end("bulk")
    if match.end() == token_start:
        # No token follows: the page ended, or the rest of it is one tag,
        # comment or bogus comment that never closes, so no later tag is real.
        return [(-1, mode, stack, events)]
    # Stop at the start of the token first, so readings that reach the same
    # token from different places merge before either one reads past it.
    if token_start > pos:
        return [(token_start, mode, stack, events)]
    if mode == _FOREIGN_MODE:
        return _advance_foreign(scan, match, stack, events)
    end = match.end()
    if mode == _HTML_CONTEXT and match.group("context_end") is not None:
        return [_leave_context(match.group("context_name").lower(), end, stack, events)]
    if match.group("end") is not None:
        event = ("/" + match.group("end_name").lower(), pos)
        return [(end, mode, stack, events | {event})]
    if mode == _UNSURE_MODE and match.group("cdata") is not None:
        # In HTML content <![CDATA[ is a bogus comment up to ">"; in SVG or
        # MathML it is a CDATA section up to "]]>".
        return [_after(scan.html.find(">", pos), 1, mode, events), _after(scan.html.find("]]>", pos), 3, mode, events)]
    name = match.group("start_name").lower()
    if name in {"svg", "math"}:
        if mode == _HTML_CONTEXT:
            # An <svg> inside <select> may be ignored, which the tracking
            # cannot follow.
            return [(end, _UNSURE_MODE, (), events)]
        if _self_closing(match.group("start")):
            return [(end, mode, stack, events)]
        return [(end, _FOREIGN_MODE, (name,), events)]
    if name in {"select", "template"}:
        if len(stack) >= _MAX_CONTEXT_DEPTH:
            # Copying a very long list of open elements on each step would
            # make the scan slow; such a page is read without the tracking.
            return [(end, _UNSURE_MODE, (), events)]
        return [(end, _HTML_CONTEXT, (*stack, name), events)]
    if name == "frameset":
        return [(end, _UNSURE_MODE, (), events)]
    readings = [_after_raw_text(scan, name, end, mode, stack, events)]
    # In the modes below the element may be read as markup instead (a
    # <template> whose content starts with <col> ignores even <script>), and
    # without scripting the browser reads <noscript> content as markup.
    if mode in {_UNSURE_MODE, _HTML_CONTEXT} or name == "noscript":
        readings.append((end, mode, stack, events))
    return readings


def _advance_foreign(scan: _Scan, match: re.Match[str], stack: tuple[str, ...], events: _Events) -> list[_Reading]:
    """Handle a tag inside SVG or MathML that opens or closes an element, or leaves it."""
    pos, end = match.start(), match.end()
    if match.group("end") is not None:
        name = match.group("end_name").lower()
        if name in stack:
            # The end tag closes the innermost open element of that name and
            # every element inside it, as the browser does.
            stack = stack[: len(stack) - 1 - stack[::-1].index(name)]
            return [(end, _FOREIGN_MODE if stack else _HTML_MODE, stack, events)]
        # An end tag that closes none of them may close an HTML element
        # around the SVG. Read it again without the tracking.
        return [(pos, _UNSURE_MODE, (), events)]
    name = match.group("start_name").lower()
    if name in _BREAKOUT:
        # A start tag such as <div> makes the browser leave SVG, and the HTML
        # around it is unknown here. Read it again without the tracking.
        return [(pos, _UNSURE_MODE, (), events)]
    if _self_closing(match.group("start")):
        return [(end, _FOREIGN_MODE, stack, events)]
    if name in _INTEGRATION:
        # The browser reads the content of these elements as HTML. Content
        # that is only text ends at the element's end tag in every reading;
        # anything else is HTML the tracking cannot follow.
        close, close_name_end = scan.end_tag(name, end)
        if close >= 0 and "<" not in scan.html[end:close]:
            tag_end = _TAG_END.match(scan.html, close_name_end)
            if tag_end is not None:
                return [(tag_end.end(), _FOREIGN_MODE, stack, events)]
        return [(pos, _UNSURE_MODE, (), events)]
    if len(stack) >= _MAX_FOREIGN_DEPTH:
        # Copying a very deep list of open elements on each step would make
        # the scan slow; such a page is read without the tracking.
        return [(pos, _UNSURE_MODE, (), events)]
    return [(end, _FOREIGN_MODE, (*stack, name), events)]


def _self_closing(tag: str) -> bool:
    """
    Whether a start tag sets the tokenizer's self-closing flag.

    The flag is set when a "/" read as a separator comes right before ">".
    A "/" at the end of an unquoted value, as in ``a=b/>``, is part of it.
    """
    pos = _TAG_START.match(tag).end()  # type: ignore[union-attr]
    last_separator = ""
    while tag[pos] != ">":
        item = _ATTR_ITEM.match(tag, pos)
        if item is None:  # pragma: no cover - the tag already matched _ATTRS
            return False
        last_separator = item.group("sep") or ""
        pos = item.end()
    return last_separator.endswith("/")


def _after(found: int, length: int, mode: int, events: _Events) -> _Reading:
    return (found + length, mode, (), events) if found >= 0 else (-1, mode, (), events)


def _leave_context(name: str, end: int, stack: tuple[str, ...], events: _Events) -> _Reading:
    """
    Update the open ``<select>`` and ``<template>`` elements a reading tracks.

    Called when the reading meets ``</select>`` or ``</template>``.
    """
    # </template> closes the innermost template and anything inside it. A
    # </select> counts only when a select is the innermost element tracked:
    # inside template content the browser ignores it, so keeping the stack
    # unchanged errs on the side of reading raw text both ways.
    if name == "template" and "template" in stack:
        stack = stack[: len(stack) - 1 - stack[::-1].index("template")]
    elif name == "select" and stack[-1:] == ("select",):
        stack = stack[:-1]
    return (end, _HTML_CONTEXT if stack else _HTML_MODE, stack, events)


def _after_raw_text(scan: _Scan, name: str, pos: int, mode: int, stack: tuple[str, ...], events: _Events) -> _Reading:
    """Skip the raw text of an HTML ``name`` element that starts at ``pos``; return the reading after its end tag."""
    if name == "plaintext":
        return (-1, mode, stack, events)
    if name == "script":
        close = _script_end(scan, pos)
    else:
        close = scan.end_tag(name, pos)[1]
    if close < 0:
        return (-1, mode, stack, events)
    # The end tag's own attributes are read like a start tag's.
    tag_end = _TAG_END.match(scan.html, close)
    return (tag_end.end(), mode, stack, events) if tag_end is not None else (-1, mode, stack, events)


def _script_end(scan: _Scan, pos: int) -> int:
    """
    Return the position just after ``</script`` that ends the script text at ``pos``, or -1.

    Script text has escape states: after ``<!--`` a ``<script`` makes the
    next ``</script>`` part of the text, until ``-->``.
    """
    html = scan.html
    # Most scripts hold no "<!--" before their end tag; finding the end tag
    # and checking for "<!--" with str.find is much faster than the full
    # token search below.
    first_start, first_end = scan.end_tag("script", pos)
    if first_start >= 0 and html.find("<!--", pos, first_start) < 0:
        return first_end
    start = pos
    state = "data"
    while (found := _SCRIPT_TOKEN.search(html, pos)) is not None:
        text = found.group(0)
        if text == "<!--":
            if state == "data":
                state = "escaped"
            # The dashes of "<!--" can also start "-->", as in "<!-->".
            pos = found.start() + 2
            continue
        pos = found.end()
        if text == "-->":
            state = "data"
        elif found.group("close"):
            if state != "double":
                scan.spend(pos - start)
                return found.end()
            state = "escaped"
        elif state == "escaped":
            state = "double"
    scan.spend(len(html) - start)
    return -1
