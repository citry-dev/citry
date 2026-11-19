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
``<textarea>`` are skipped. A single regular expression steps over ordinary
tags and text, so Python only runs for the few tags that matter here.

Whether ``<style>`` or ``<title>`` starts raw text depends on where the
element sits: inside SVG or MathML, inside ``<select>``, in some
``<template>`` contents, and in a fragment inserted into such an element,
the browser reads the same text as markup. Where the reading depends on
that, the scan follows both readings and keeps only the tag positions that
every reading agrees on. A position the scan is unsure of is left out, and
callers then fall back to putting the content at the start or end of the
HTML, which is always outside any tag.
"""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass

# HTML whitespace as the tokenizer sees it. A carriage return is read as a
# line feed before tokenizing, so it counts as whitespace too.
_WS = "\\t\\n\\f\\r "

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

# Elements whose start tag switches the tokenizer to raw text (or, for
# ``<plaintext>``, makes the rest of the page text) when they are HTML
# elements.
_RAW_TEXT = ("script", "style", "title", "textarea", "xmp", "iframe", "noembed", "noframes", "noscript", "plaintext")
# Start tags after which a ``<style>`` or ``<title>`` may be read as markup
# rather than raw text: foreign content, ``<select>``, frameset pages, and
# ``<template>`` contents (a ``<style>`` after ``<template><col>`` is ignored).
_CONTEXT = ("svg", "math", "select", "frameset", "template")
# Start tags the callers need positions for.
_DOCUMENT = ("html", "head", "body")
_INTERESTING = "|".join((*_RAW_TEXT, *_CONTEXT, *_DOCUMENT))

# Tokens that change nothing here, stepped over in bulk.
_BORING = (
    r"[^<]+"
    # A comment ends at the first ``-->`` or ``--!>`` after ``<!--``, and
    # ``<!-->`` and ``<!--->`` end at once.
    r"|<!--(?>-?>|(?s:.*?)(?:-->|--!>))"
    # A doctype or bogus comment ends at the first ``>``, even inside quotes.
    # ``<![CDATA[`` is matched case-sensitively, as the tokenizer does.
    r"|<!(?!--|(?-i:\[CDATA\[))[^>]*>"
    r"|<\?[^>]*>"
    r"|</>"
    r"|</(?![A-Za-z>])[^>]*>"
    rf"|</(?!(?:head|body)[{_WS}/>])[A-Za-z][^{_WS}/>]*" + _ATTRS + ""
    rf"|<(?!(?:{_INTERESTING})[{_WS}/>])[A-Za-z][^{_WS}/>]*" + _ATTRS + ""
    # A ``<`` that starts no tag is text.
    r"|<(?![A-Za-z!/?])"
)

# re.ASCII keeps case-insensitive matching to ASCII letters, as browsers do:
# without it, "\u017f" (long s) would match "s" and "<\u017fcript>" would be
# taken for a script element.
_FLAGS = re.IGNORECASE | re.ASCII
_NEXT = re.compile(
    rf"(?P<bulk>(?>(?:{_BORING})*))"
    rf"(?:(?P<end></(?P<end_name>head|body))(?=[{_WS}/>]){_ATTRS}"
    rf"|<(?P<start>{_INTERESTING})(?=[{_WS}/>]){_ATTRS}"
    r"|(?P<cdata>(?-i:<!\[CDATA\[)))?",
    _FLAGS,
)
_TAG_END = re.compile(_ATTRS, _FLAGS)
_RAW_END = {name: re.compile(rf"</{name}(?=[{_WS}/>])", _FLAGS) for name in _RAW_TEXT}
_SCRIPT_TOKEN = re.compile(rf"<!--|-->|<(?P<close>/?)script(?=[{_WS}/>])", _FLAGS)
# A page the browser opens on its own starts with a doctype or ``<html>``.
# Anything else may be a fragment inserted into any element, even an SVG
# element, so it gets the stricter reading from the start.
_DOCUMENT_START = re.compile(rf"[{_WS}]*<(?:!doctype[{_WS}>]|html[{_WS}/>])", _FLAGS)

# Each reading the scan follows costs one more pass over the rest of the
# page until it agrees with another reading again. Past this many at once
# the scan gives up and reports no positions.
_MAX_READINGS = 16


@dataclass(frozen=True, slots=True)
class DocumentTags:
    """Positions of the tags every reading of the HTML agrees on, in document order."""

    head_ends: tuple[int, ...]
    body_ends: tuple[int, ...]
    # (start, end) of each ``<body>`` start tag.
    body_starts: tuple[tuple[int, int], ...]
    # Whether a doctype or an ``<html>``, ``<head>`` or ``<body>`` start tag was seen.
    is_document: bool


_EMPTY = DocumentTags((), (), (), is_document=False)


def scan_document_tags(html: str, *, first_head_end_only: bool = False) -> DocumentTags:
    """
    Return the ``</head>``, ``</body>`` and ``<body>`` tags a browser reads as real tags in ``html``.

    A tag inside an attribute value, a comment, or raw text is not reported.
    When the HTML can be read in more than one way (see the module
    docstring), only the tags every reading finds are reported.

    With ``first_head_end_only``, the scan stops as soon as the first real
    ``</head>`` is certain, and only ``head_ends[0]`` is meaningful.
    """
    # Each reading is (position, ambiguous, events). ``ambiguous`` says raw
    # text may be markup from here on; ``events`` holds the tags this reading
    # found so far. Readings are advanced in position order, so two that
    # reach the same token in the same state are merged, keeping only the
    # tags both found.
    ambiguous = _DOCUMENT_START.match(html) is None
    heap: list[tuple[int, bool, frozenset[tuple[str, int, int]]]] = [(0, ambiguous, frozenset())]
    finished: list[frozenset[tuple[str, int, int]]] = []
    while heap:
        pos, ambiguous, events = heapq.heappop(heap)
        # Merge every reading waiting at the same point in the same state.
        while heap and heap[0][0] == pos and heap[0][1] == ambiguous:
            events &= heapq.heappop(heap)[2]
        for reading in _advance(html, pos, ambiguous, events):
            if reading[0] < 0:
                finished.append(reading[2])
            else:
                heapq.heappush(heap, reading)
        if len(heap) > _MAX_READINGS:
            return _EMPTY
        # With a single reading left, a </head> that it and every finished
        # reading found is the first real one: later tags all come after it.
        if first_head_end_only and len(heap) == 1:
            common = frozenset.intersection(heap[0][2], *finished)
            if any(kind == "/head" for kind, _, _ in common):
                return _tags(common)
    if not finished:
        return _EMPTY
    return _tags(frozenset.intersection(*finished))


def _tags(common: frozenset[tuple[str, int, int]]) -> DocumentTags:
    """Sort the agreed events into a ``DocumentTags``."""
    ordered = sorted(common, key=lambda event: event[1])
    return DocumentTags(
        head_ends=tuple(start for kind, start, _ in ordered if kind == "/head"),
        body_ends=tuple(start for kind, start, _ in ordered if kind == "/body"),
        body_starts=tuple((start, end) for kind, start, end in ordered if kind == "body"),
        is_document=any(kind in {"doc", "body"} for kind, _, _ in ordered),
    )


_Reading = tuple[int, bool, frozenset[tuple[str, int, int]]]


def _advance(html: str, pos: int, ambiguous: bool, events: frozenset[tuple[str, int, int]]) -> list[_Reading]:
    """
    Step one reading to its next interesting token and return the readings that follow it.

    A reading at position ``-1`` has finished: the page ended, or the rest
    of it is inside a tag, comment or raw text that never closes.
    """
    match = _NEXT.match(html, pos)
    if match is None:  # pragma: no cover - the pattern can match empty, so it always matches
        return [(-1, ambiguous, events)]
    # Stop at the start of the token first, so readings that reach the same
    # token from different places merge before either one reads past it.
    if match.end("bulk") > pos and match.end() > match.end("bulk"):
        return [(match.end("bulk"), ambiguous, events)]
    if match.group("end") is not None:
        name = match.group("end_name").lower()
        return [(match.end(), ambiguous, events | {("/" + name, match.start("end"), match.end())})]
    if match.group("start") is None and match.group("cdata") is None:
        # No token follows: the page ended, or the rest of it is one tag,
        # comment or bogus comment that never closes, so no later tag is real.
        return [(-1, ambiguous, events)]
    if match.group("cdata") is not None:
        start = match.start("cdata")
        readings: list[_Reading] = []
        # In HTML content ``<![CDATA[`` is a bogus comment up to ``>``.
        close = html.find(">", start)
        readings.append((close + 1, ambiguous, events) if close >= 0 else (-1, ambiguous, events))
        if ambiguous:
            # In SVG or MathML it is a CDATA section up to ``]]>``.
            close = html.find("]]>", start)
            readings.append((close + 3, ambiguous, events) if close >= 0 else (-1, ambiguous, events))
        return readings
    name = match.group("start").lower()
    start = match.start("start") - 1
    end = match.end()
    if name in _DOCUMENT:
        event = ("body", start, end) if name == "body" else ("doc", start, end)
        return [(end, ambiguous, events | {event})]
    if name in _CONTEXT:
        return [(end, True, events)]
    readings = [_after_raw_text(html, name, end, ambiguous, events)]
    # Without scripting, the browser reads <noscript> content as markup, and
    # in the contexts above the other elements may be read as markup.
    # <script> is read only as script text: its content never holds data
    # that can write "<" (Citry escapes expressions there, Vue ignores
    # <script> in templates, and the hydrated renderer refuses a body with a
    # script), so a misread script cannot move the scan into a data value.
    # Reading large inline scripts as markup would also keep the two
    # readings from agreeing again for the rest of the page.
    if (ambiguous and name != "script") or name == "noscript":
        readings.append((end, ambiguous, events))
    return readings


def _after_raw_text(
    html: str, name: str, pos: int, ambiguous: bool, events: frozenset[tuple[str, int, int]]
) -> _Reading:
    """Skip the raw text of an HTML ``name`` element that starts at ``pos``; return the reading after its end tag."""
    if name == "plaintext":
        return (-1, ambiguous, events)
    if name == "script":
        close = _script_end(html, pos)
    else:
        found = _RAW_END[name].search(html, pos)
        close = found.end() if found is not None else -1
    if close < 0:
        return (-1, ambiguous, events)
    # The end tag's own attributes are read like a start tag's.
    tag_end = _TAG_END.match(html, close)
    return (tag_end.end(), ambiguous, events) if tag_end is not None else (-1, ambiguous, events)


def _script_end(html: str, pos: int) -> int:
    """
    Return the position just after ``</script`` that ends the script text at ``pos``, or -1.

    Script text has escape states: after ``<!--`` a ``<script`` makes the
    next ``</script>`` part of the text, until ``-->``.
    """
    # Most scripts hold no "<!--" before their end tag; finding the end tag
    # and checking for "<!--" with str.find is much faster than the full
    # token search below.
    first_end = _RAW_END["script"].search(html, pos)
    if first_end is not None and html.find("<!--", pos, first_end.start()) < 0:
        return first_end.end()
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
                return found.end()
            state = "escaped"
        elif state == "escaped":
            state = "double"
    return -1
