"""
HTML escaping and the trusted-markup type.

Citry autoescapes the result of template expressions before placing it in the
output, so user data cannot inject markup. A value that is already trusted HTML
(for example the result of rendering a subtree) carries that trust as
``Markup`` and is passed through unescaped between tags. Attribute values
are always escaped (see ``escape_attribute_value``).

Citry's rendering modules import their escaping tools from this thin wrapper so
backend-specific behavior stays in one place. The public package re-exports the
same ``Markup`` class directly.

- ``escape(value)`` returns ``Markup``. It respects the ``__html__``
  protocol, so a value that is already ``Markup`` (or any object with
  ``__html__``) passes through without double-escaping.
- ``escape`` escapes ``& < > ' "``. Escaping all five means the same output is
  safe in both HTML body text and double- or single-quoted attribute values.
  It also writes the ESC control character as ``&#27;``. On a page read as
  ISO-2022-JP, raw ESC bytes can switch the decoder so that a closing quote
  stops being a quote, and a reference is read after the page is decoded.
- ``escape_attribute_value(value)`` escapes a value for an HTML attribute.
  ``Markup`` says a string is safe to insert between tags, while an
  attribute value is plain text, so its HTML is decoded to the text a
  browser reads and then escaped.
- ``Markup`` is exactly ``markupsafe.Markup``, imported unchanged.
  ``Markup(value)`` marks the complete value as trusted HTML; it does not
  sanitize, validate, or escape anything. See
  https://markupsafe.palletsprojects.com/en/stable/escaping/#markupsafe.Markup.
"""

from __future__ import annotations

import functools
import html.parser
import json
import re
import sys
from collections import deque
from html import unescape
from html.entities import html5
from html.parser import HTMLParser
from types import BuiltinFunctionType
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from markupsafe import Markup
from markupsafe import escape as _markupsafe_escape

from citry.util import deep_json

if TYPE_CHECKING:
    from collections.abc import Callable

# A parser method that receives a start tag's name and attributes.
_TagHandler = TypeVar("_TagHandler", bound="Callable[[Any, str, list[tuple[str, str | None]]], None]")

# markupsafe's escaper that returns a plain ``str`` (the same function that
# ``markupsafe.escape`` runs internally before wrapping the result in a
# ``Markup``).
# it lives in the C ``_speedups`` module, with a pure-Python ``_native`` twin;
# we resolve whichever is present and fall back to the public ``escape`` if a
# future markupsafe drops the name, so this stays a one-line behaviour change.
# NOTE: Imports work on 3.X, falls through on 2.X.
_escape_to_str_impl: Callable[[str], str] | None
try:
    from markupsafe._speedups import _escape_inner as _escape_to_str_impl
except ImportError:  # pragma: no cover - depends on the installed wheel
    try:
        from markupsafe._native import _escape_inner as _escape_to_str_impl
    except ImportError:  # pragma: no cover - very old markupsafe
        # v2.X
        _escape_to_str_impl = None


# The browser decodes the page's bytes before it reads references, so ESC
# written this way cannot switch the page's encoding.
_ESC = "\x1b"
_ESC_REFERENCE = "&#27;"


def escape(value: Any) -> Markup:
    """
    Escape ``value`` to ``Markup``, leaving a value with ``__html__`` as it is.

    Same as ``markupsafe.escape``, except that ESC becomes ``&#27;`` (see the
    module docstring). ``markupsafe`` leaves ESC in place, and
    ``Markup.format``, ``%``, ``+`` and ``join`` still call it, so Citry's
    own code passes data through here.
    """
    escaped = _markupsafe_escape(value)
    # Trusted HTML stays exactly as written; the output check reads it.
    if _ESC not in escaped or hasattr(value, "__html__"):
        return escaped
    return Markup(str.replace(escaped, _ESC, _ESC_REFERENCE))  # noqa: S704 - escaped above


def escape_to_str(value: Any) -> str:
    """
    Escape ``value`` to a plain ``str`` (not ``Markup``).

    Same character escaping as :func:`escape`, including the ``__html__``
    pass-through, but it skips allocating a ``Markup`` for the result. Use it
    only where the escaped text is concatenated into a larger string that is
    marked safe as a whole (so the unmarked piece is never re-escaped); for a
    value that becomes output on its own, use :func:`escape`.
    """
    if hasattr(value, "__html__"):
        return str(value.__html__())
    text = str(value)

    # IMPORTANT: we don't use ``escape(text)`` here because that creates a Markup
    # object, which is unnecessary overhead / performance penalty, when the caller
    # is just going to concatenate the result into a larger string.
    # Instead, we call the internal escape function that returns a plain string.
    if _escape_to_str_impl is None:
        return str(escape(text))
    # ``replace`` returns the same string when there is no ESC, which is
    # nearly always, and keeps this one call on the render hot path.
    return _escape_to_str_impl(text).replace(_ESC, _ESC_REFERENCE)


# One character reference, the same pattern Python's html.unescape uses.
_CHARREF = re.compile(r"&(#[0-9]+;?|#[xX][0-9a-fA-F]+;?|[^\t\n\f <&#;]{1,32};?)")

# The most digits, not counting leading zeros, that a numeric reference can
# have and still name a code point at or below U+10FFFF: 1114111 has seven
# decimal digits and 10FFFF six hex digits.
_MAX_DECIMAL_DIGITS = 7
_MAX_HEX_DIGITS = 6


def _short_numeric_reference(name: str) -> str | None:
    """
    Return the reference for ``name`` (``#106`` or ``#x6A``, with or without ``;``) as ``&#...`` without leading zeros.

    None means the number has too many digits to be at or below U+10FFFF,
    which the browser reads as U+FFFD without converting the digits. Python's ``html.unescape`` converts them
    with ``int()``, which refuses more than 4,300 digits, so the reference it
    is given must stay short; dropping leading zeros keeps its value.
    """
    is_hex = name[1:2] in {"x", "X"}
    prefix = name[:2] if is_hex else name[:1]
    digits = name[len(prefix) :]
    semicolon = ";" if digits.endswith(";") else ""
    significant = digits.rstrip(";").lstrip("0")
    if len(significant) > (_MAX_HEX_DIGITS if is_hex else _MAX_DECIMAL_DIGITS):
        return None
    return f"&{prefix}{significant or '0'}{semicolon}"


def _decode_text_numeric_reference(name: str) -> str:
    """Return the character a browser reads in text from the numeric reference ``name`` (``#106`` or ``#x6A;``)."""
    reference = _short_numeric_reference(name)
    # Too many digits to be at or below U+10FFFF.
    if reference is None:
        return "\ufffd"
    is_hex = reference[2:3] in {"x", "X"}
    code_point = int(reference[3 if is_hex else 2 :].rstrip(";"), 16 if is_hex else 10)
    # NUL, a surrogate and a value past U+10FFFF read as U+FFFD, as
    # ``html.unescape`` reads them too.
    if code_point == 0 or 0xD800 <= code_point <= 0xDFFF or code_point > 0x10FFFF:
        return "\ufffd"
    # The HTML standard reads 0x80 to 0x9F as Windows-1252, and keeps the
    # five codes that Windows-1252 leaves undefined (0x81, 0x8D, 0x8F, 0x90,
    # 0x9D) as they are; Python's cp1252 codec refuses exactly those five.
    if 0x80 <= code_point <= 0x9F:
        try:
            return bytes([code_point]).decode("cp1252")
        except UnicodeDecodeError:
            return chr(code_point)
    # The browser keeps every other code point, control characters and
    # noncharacters included, while ``html.unescape`` drops some of them.
    return chr(code_point)


def _decode_text_charref(match: re.Match[str]) -> str:
    """Decode one character reference in text as the browser does."""
    name = match.group(1)
    if name[0] != "#":
        return unescape(match.group(0))
    return _decode_text_numeric_reference(name)


def decode_character_references(html: str) -> str:
    """
    Decode the character references in ``html`` as the browser decodes them in text.

    Named references decode as Python's ``html.unescape`` decodes them.
    Numeric references follow the browser. A numeric reference that
    ``html.unescape`` drops, such as the control character ``&#127;`` or
    the Unicode noncharacter ``&#xfdd0;``, is kept, as the browser keeps
    it. A reference with more digits than Python's ``int()`` accepts reads
    as the browser reads it (``&#`` followed by 5,000 zeros and ``106;``
    gives ``j``) instead of raising ``ValueError``. For an attribute value,
    use ``decode_attribute_entities``.
    """
    if "&" not in html:
        return html
    return _CHARREF.sub(_decode_text_charref, html)


def _decode_attribute_charref(match: re.Match[str]) -> str:
    """Decode one character reference the way a browser does inside an attribute value."""
    name = match.group(1)
    # A numeric reference decodes as in text. ``html.unescape`` would drop
    # ESC, so ``java&#27;script:`` would read as a URL the value did not spell.
    if name[0] == "#":
        return _decode_text_numeric_reference(name)
    # A name that matches exactly decodes as in text.
    if name in html5:
        return unescape(match.group(0))
    # A legacy name without ";" (such as "&copy") decodes from its longest
    # known prefix. Inside an attribute value a browser leaves it as typed
    # when "=" or a letter or digit follows, so "?a=1&copy=2" stays a URL.
    for end in range(len(name) - 1, 1, -1):
        prefix = name[:end]
        if prefix in html5:
            following = name[end]
            if following == "=" or (following.isascii() and following.isalnum()):
                return match.group(0)
            return html5[prefix] + name[end:]
    return match.group(0)


# A reference that decodes to nothing in ``html.unescape`` (U+0001 is one of
# the code points it drops), used to pad a shortened reference back to the
# original length. A browser keeps U+0001, so the padded text is only parsed,
# never written out.
_EMPTY_REFERENCE = "&#1;"
# The reference ``html.unescape`` reads as U+FFFD, for a value past U+10FFFF.
_PAST_UNICODE_REFERENCE = "&#1114112;"
# Compiled patterns that find a decimal reference longer than Python's digit
# limit, one per limit, because a program can change the limit with
# ``sys.set_int_max_str_digits``.
_LONG_DECIMAL_REFERENCE_PATTERNS: dict[int, re.Pattern[str]] = {}
# A reference that may still be unfinished at the end of a chunk: ``&#`` and
# any digits after it, with no ``;`` yet.
_UNFINISHED_DECIMAL_REFERENCE = re.compile(r"&#[0-9]*\Z")
# The patterns ``HTMLParser`` splits a start tag with. ``html.parser``
# defines them but its type stubs leave them out, so they are read with
# ``getattr``; should a later Python drop them, a tag keeps the attribute
# values ``HTMLParser`` gives.
_START_TAG_NAME: re.Pattern[str] | None = getattr(html.parser, "tagfind_tolerant", None)
_ATTRIBUTE: re.Pattern[str] | None = getattr(html.parser, "attrfind_tolerant", None)


def _int_digit_limit() -> int:
    """Return how many decimal digits Python converts to an ``int``, or 0 for no limit."""
    # Python 3.10.0 to 3.10.6 have no limit and no function to read it.
    read_limit = getattr(sys, "get_int_max_str_digits", None)
    return 0 if read_limit is None else int(read_limit())


def _long_decimal_reference_pattern(limit: int) -> re.Pattern[str]:
    """Return the pattern for a decimal reference with more than ``limit`` digits."""
    pattern = _LONG_DECIMAL_REFERENCE_PATTERNS.get(limit)
    if pattern is None:
        pattern = re.compile(rf"&#([0-9]{{{limit + 1},}})(;?)")
        _LONG_DECIMAL_REFERENCE_PATTERNS[limit] = pattern
    return pattern


def _same_length_reference(match: re.Match[str]) -> str:
    """Rewrite one long decimal reference as text of the same length that ``html.unescape`` decodes alike."""
    significant = match.group(1).lstrip("0")
    reference = _short_numeric_reference(f"#{significant or '0'};") or _PAST_UNICODE_REFERENCE
    padding = len(match.group(0)) - len(reference)
    # Pad with references that decode to nothing; the first carries the
    # leftover length as leading zeros. The padding is never below 4: the
    # smallest digit limit Python allows is 640.
    pieces, extra = divmod(padding, len(_EMPTY_REFERENCE))
    return reference + "&#" + "0" * extra + "1;" + _EMPTY_REFERENCE * (pieces - 1)


def bound_long_decimal_references(html: str) -> str:
    """
    Rewrite decimal references too long for Python's ``int()`` so ``html.unescape`` can read them.

    Each reference with more digits than Python converts becomes a string of
    the same length that ``html.unescape`` decodes to the same text: the
    short reference followed by references that decode to nothing (a
    browser would keep those, so use this only on text you parse). Positions
    in ``html`` stay valid, and text without such a reference is returned
    unchanged. A reference at the very end of ``html`` without ``;`` is read
    as complete.
    """
    limit = _int_digit_limit()
    # A limit of 0 means Python converts any number of digits.
    if limit == 0 or "&#" not in html:
        return html
    return _long_decimal_reference_pattern(limit).sub(_same_length_reference, html)


def _with_browser_attributes(handler: _TagHandler) -> _TagHandler:
    """Wrap a start tag handler so it receives the attribute values a browser reads."""

    @functools.wraps(handler)
    def handle(self: LongReferenceSafeParser, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        handler(self, tag, self._browser_attributes(attrs))

    # The marker is the wrapper itself, so a copy of it that ``functools.wraps``
    # makes on another function does not make that function look wrapped.
    handle._citry_browser_attributes = handle  # type: ignore[attr-defined]
    return handle  # type: ignore[return-value]


def _is_wrapped(handler: object) -> bool:
    """Return whether ``handler`` is the wrapper ``_with_browser_attributes`` made."""
    return handler is not None and getattr(handler, "_citry_browser_attributes", None) is handler


# The start tag handlers that receive the attribute values a browser reads.
_START_TAG_HANDLERS = ("handle_starttag", "handle_startendtag")


class LongReferenceSafeParser(HTMLParser):
    """
    An ``HTMLParser`` that reads long decimal references and decodes attribute values as a browser does.

    ``HTMLParser`` decodes attribute values (and text, with
    ``convert_charrefs=True``) with ``html.unescape``, which raises
    ``ValueError`` for a decimal reference with more than 4,300 digits.
    This parser rewrites such a reference before parsing, as
    ``bound_long_decimal_references`` describes, so the decoded text is what
    an unlimited ``html.unescape`` gives. Text the parser does not decode,
    such as ``<script>`` content, comments and ``get_starttag_text()``,
    shows the rewritten form of such a reference, and with
    ``convert_charrefs=False`` ``handle_charref`` receives its pieces. Apart
    from the attribute values described next, input without a long
    reference parses exactly as with ``HTMLParser``.

    A subclass's ``handle_starttag`` and ``handle_startendtag`` receive the
    attribute values a browser reads, decoded from the original input with
    ``decode_attribute_entities``. ``html.unescape`` drops some code points
    that a browser keeps (such as U+0001 and U+FDD0), so the values
    ``HTMLParser`` gives would differ from the page the browser builds. Only
    a handler that a subclass defines in its class body gets these values; a
    handler added later, set on an instance, or defined by a mixin that
    comes before this class gets the values ``HTMLParser`` gives, as does a
    handler for a tag that cannot be lined up with its original text (for
    example when ``sys.set_int_max_str_digits`` changes while a tag is
    split across feeds). With ``convert_charrefs=True``, text is still
    decoded with ``html.unescape``, so a reference such as ``&#1;`` in text
    reads as nothing.
    """

    # A subclass whose handlers never look at attribute values sets this to
    # False, which skips decoding each tag's values a second time from the
    # original text. The setting applies only to the class that sets it, so
    # a subclass that reads values still gets the values a browser reads.
    _reads_attribute_values: ClassVar[bool] = True
    # Whether any class in this class's ancestry has a wrapped start tag
    # handler, which reads the original text, so the parser must keep it. A
    # class that opted out can still reach a wrapped handler of a parent
    # through ``super()``. Set for each subclass.
    _keeps_source: ClassVar[bool] = False

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__dict__.get("_reads_attribute_values", True):
            # Wrap only the handlers this class defines; an inherited handler
            # keeps what its own class gave it: wrapped, or left alone when
            # that class opted out.
            for name in _START_TAG_HANDLERS:
                handler = cls.__dict__.get(name)
                if handler is not None and not _is_wrapped(handler):
                    setattr(cls, name, _with_browser_attributes(handler))
        # A parser with no wrapped handler anywhere in its ancestry never
        # reads the original text, so it must not hold on to the input.
        cls._keeps_source = any(
            _is_wrapped(vars(base).get(name)) for base in cls.__mro__ for name in _START_TAG_HANDLERS
        )

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        # The end of the last chunk when it may be the start of a reference
        # whose digits continue in the next chunk.
        self._held_reference = ""

    def reset(self) -> None:
        super().reset()
        self._held_reference = ""
        # The input as given, before long references are rewritten, kept in
        # the chunks it arrived in, for a parser whose handlers read
        # attribute values. The first chunk starts at ``_source_start``
        # characters into the whole input, and ``_fed`` counts the
        # characters handed to ``HTMLParser`` so far.
        self._source: deque[str] = deque()
        self._source_start = 0
        self._fed = 0
        # Where the start tag being parsed begins in the whole input, and
        # whether its handler has yet to receive the browser's values.
        self._tag_start = 0
        self._tag_needs_values = False

    def parse_starttag(self, i: int) -> int:
        # ``HTMLParser`` joins any input it buffered into ``rawdata`` before
        # parsing, so ``rawdata`` ends where the input fed so far ends. That
        # turns ``i`` into a position in the whole input. The rewrite keeps
        # the text the same length, so it is also the tag's position in the
        # original text.
        self._tag_start = self._fed - len(self.rawdata) + i
        # Chunks that end before this tag are never read again, so drop them.
        while self._source and self._source_start + len(self._source[0]) <= self._tag_start:
            self._source_start += len(self._source.popleft())
        # Only the handler call this method makes gets the browser's values;
        # a handler that calls another handler passes its own values on.
        self._tag_needs_values = True
        try:
            return super().parse_starttag(i)
        finally:
            self._tag_needs_values = False

    def _parse(self, text: str) -> None:
        """Feed ``text`` to ``HTMLParser`` with long references rewritten, keeping the original text."""
        if self._keeps_source:
            self._source.append(text)
        self._fed += len(text)
        super().feed(bound_long_decimal_references(text))

    def _browser_attributes(self, attrs: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
        """Return the current start tag's attributes with the values a browser reads."""
        if not self._tag_needs_values:
            return attrs
        self._tag_needs_values = False
        tag_text = self.get_starttag_text()
        # A tag with no ``&`` has no reference, so ``HTMLParser`` and
        # ``decode_attribute_entities`` give the same values; skip decoding
        # it again.
        if tag_text is None or "&" not in tag_text or _START_TAG_NAME is None or _ATTRIBUTE is None:
            return attrs
        offset = self._tag_start - self._source_start
        if len(self._source) > 1:
            # The tag starts in the first chunk and ends in a later one. Join
            # only the text from this tag on, so input fed in many chunks is
            # not copied again for every tag.
            self._source[0] = self._source[0][offset:]
            self._source_start = self._tag_start
            offset = 0
            joined = "".join(self._source)
            self._source.clear()
            self._source.append(joined)
        source = self._source[0][offset : offset + len(tag_text)] if self._source else ""
        # The rewrite keeps the text the same length, so ``source``, the same
        # tag in the original text, lines up character for character with
        # ``tag_text``. If it does not rewrite to ``tag_text``, it is not the
        # same text (for example, a different digit limit rewrote it), and
        # pairing its values with these names would be wrong.
        if bound_long_decimal_references(source) != tag_text:
            return attrs
        # Split ``tag_text`` as ``HTMLParser`` did, so the names are exactly
        # the ones it found, and read each value from the same span of
        # ``source``, where a long reference is still written out in full.
        match = _START_TAG_NAME.match(tag_text, 1)
        if match is None:
            return attrs
        decoded: list[tuple[str, str | None]] = []
        position = match.end()
        while position < len(tag_text):
            found = _ATTRIBUTE.match(tag_text, position)
            if found is None:
                break
            name, rest = found.group(1, 2)
            value: str | None = None
            if rest:
                value = source[found.start(3) : found.end(3)]
                if value[:1] == "'" == value[-1:] or value[:1] == '"' == value[-1:]:
                    value = value[1:-1]
                if value:
                    value = decode_attribute_entities(value)
            decoded.append((name.lower(), value))
            position = found.end()
        # Should a later Python split the tag differently, keep its reading
        # rather than pair values with the wrong names.
        if [name for name, _ in decoded] != [name for name, _ in attrs]:
            return attrs
        return decoded

    def feed(self, data: str) -> None:
        # Hold back a possibly unfinished reference, so the rewrite always
        # sees whole references, and let HTMLParser.feed do the rest.
        text = self._held_reference + data
        held = _UNFINISHED_DECIMAL_REFERENCE.search(text)
        if held is None:
            self._held_reference = ""
        else:
            self._held_reference = text[held.start() :]
            text = text[: held.start()]
        if text:
            self._parse(text)

    def close(self) -> None:
        # At the end of the input, a held reference without ";" is complete.
        held, self._held_reference = self._held_reference, ""
        if held:
            self._parse(held)
        super().close()


def decode_attribute_entities(html: str) -> str:
    """
    Return the attribute value a browser reads from ``html`` written inside quotes.

    This follows the HTML parser's rule for a legacy reference in an
    attribute value: a named reference written without ``;`` stays as typed
    when ``=`` or a letter or digit follows it, so ``?a=1&copy=2`` stays a
    URL. A numeric reference decodes as the browser decodes it, the same as
    in ``decode_character_references``, so ``a&#1;b`` keeps its U+0001
    between the two letters.
    """
    if "&" not in html:
        return html
    return _CHARREF.sub(_decode_attribute_charref, html)


def escape_attribute_value(value: Any) -> str:
    """
    Escape ``value`` as the text of a double-quoted HTML attribute value, to a plain ``str``.

    Unlike :func:`escape_to_str`, an object with ``__html__`` (such as
    ``Markup``) is escaped too. ``Markup`` says a string is safe to insert
    between tags, and inserting it raw here would let a ``"`` in it end the
    attribute. Its HTML is first decoded to the value a browser would read
    from it, then escaped, so ``Markup("Tom &amp; Jerry")`` still reads as
    ``Tom & Jerry``. Interactive pages send Vue the same decoded value, so
    both kinds of page show the same attribute.
    """
    # An exact str is the common case and has no __html__ to look up.
    if type(value) is not str:
        html = getattr(value, "__html__", None)
        if html is not None:
            return escape_to_str(decode_attribute_entities(str(html())))
    return escape_to_str(value)


# Formatting caches must recognize the defining implementation, including
# replacements installed before the first render. Custom/Python backends keep
# executing on each call; only the known C escaper supplies cached output.
_DEFAULT_ESCAPE_TO_STR = escape_to_str
_DEFAULT_ESCAPE_ATTRIBUTE_VALUE = escape_attribute_value
_DEFAULT_ESCAPE_TO_STR_IMPL = _escape_to_str_impl
_CACHEABLE_ESCAPE_BACKEND = (
    type(_escape_to_str_impl) is BuiltinFunctionType
    and _escape_to_str_impl.__module__ == "markupsafe._speedups"
    and _escape_to_str_impl.__name__ == "_escape_inner"
)


def script_json(value: object, *, sort_keys: bool = False, ensure_ascii: bool = True) -> str:
    r"""
    Serialize ``value`` as JSON text that is safe inside a ``<script>`` element.

    The HTML parser reads a script element's text until the first ``</script``
    and treats ``<!--`` followed by ``<script`` as a nested comment that can hide
    the real end tag. Both sequences start with ``<``, and in JSON text a ``<``
    can only occur inside a string, so writing every ``<`` as the escape
    ``\u003c`` keeps the element intact while ``JSON.parse`` (or a JavaScript
    parser) still reads the same value. ``ensure_ascii`` also escapes U+2028 and
    U+2029, which older JavaScript parsers reject inside a string literal.

    Non-finite numbers are rejected, because ``JSON.parse`` cannot read them.
    """
    try:
        text = json.dumps(
            value, allow_nan=False, separators=(",", ":"), sort_keys=sort_keys, ensure_ascii=ensure_ascii
        )
    except RecursionError:
        # On Python 3.11 and PyPy the encoder counts each nested container
        # against the recursion limit, and later CPython versions against a
        # fixed limit of their own, so deep enough data stops it. Writing the
        # same text with a stack uses a fixed number of frames.
        text = deep_json.dumps(value, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    return text.replace("<", "\\u003c")


__all__ = [
    "Markup",
    "decode_attribute_entities",
    "escape",
    "escape_attribute_value",
    "escape_to_str",
    "script_json",
]


# Tags whose contents or attributes the browser does not treat as ordinary
# page text and markup: it runs or loads them (script, iframe, object), reads
# them as raw text without decoding `&lt;` (style, xmp), or changes how the
# rest of the page is read (base, meta, plaintext). Citry escapes an element's
# body as HTML text, which is not right for these tags, so a `<c-element>` with
# `c-is` or `c-bind` refuses them, compared in any letter case, however the
# page is rendered. `textarea` and `title` are allowed: the browser reads tags
# inside them as text but still decodes character references, so Citry's
# escaped text comes out as written and cannot close the element early.
_REFUSED_DYNAMIC_ELEMENT_TAGS: frozenset[str] = frozenset(
    {
        "applet",
        "base",
        "embed",
        "frame",
        "frameset",
        "iframe",
        "link",
        "meta",
        "noembed",
        "noframes",
        "noscript",
        "object",
        "plaintext",
        "script",
        "style",
        "template",
        "xmp",
    }
)
