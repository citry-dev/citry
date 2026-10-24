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

import json
import re
import sys
from html import unescape
from html.entities import html5
from html.parser import HTMLParser
from types import BuiltinFunctionType
from typing import TYPE_CHECKING, Any

from markupsafe import Markup, escape

if TYPE_CHECKING:
    from collections.abc import Callable

# markupsafe's escaper that returns a plain ``str`` (the same function that
# ``escape`` runs internally before wrapping the result in a ``Markup``).
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
    return _escape_to_str_impl(text)


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
    # A numeric reference decodes as ``html.unescape`` reads it.
    if name[0] == "#":
        reference = _short_numeric_reference(name)
        return "\ufffd" if reference is None else unescape(reference)
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


class LongReferenceSafeParser(HTMLParser):
    """
    An ``HTMLParser`` that reads decimal references of any length.

    ``HTMLParser`` decodes attribute values (and text, with
    ``convert_charrefs=True``) with ``html.unescape``, which raises
    ``ValueError`` for a decimal reference with more than 4,300 digits.
    This parser rewrites such a reference before parsing, as
    ``bound_long_decimal_references`` describes, so the decoded attribute
    values and text are what an unlimited ``html.unescape`` gives. Text the
    parser does not decode, such as ``<script>`` content, comments and
    ``get_starttag_text()``, shows the rewritten form of such a reference,
    and with ``convert_charrefs=False`` ``handle_charref`` receives its
    pieces. Input without one parses exactly as with ``HTMLParser``.
    """

    def __init__(self, *, convert_charrefs: bool = True) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        # The end of the last chunk when it may be the start of a reference
        # whose digits continue in the next chunk.
        self._held_reference = ""

    def reset(self) -> None:
        super().reset()
        self._held_reference = ""

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
            super().feed(bound_long_decimal_references(text))

    def close(self) -> None:
        # At the end of the input, a held reference without ";" is complete.
        held, self._held_reference = self._held_reference, ""
        if held:
            super().feed(bound_long_decimal_references(held))
        super().close()


def decode_attribute_entities(html: str) -> str:
    """
    Return the attribute value a browser reads from ``html`` written inside quotes.

    This follows the HTML parser's rule for a legacy reference in an
    attribute value: a named reference written without ``;`` stays as typed
    when ``=`` or a letter or digit follows it, so ``?a=1&copy=2`` stays a
    URL.
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
    text = json.dumps(value, allow_nan=False, separators=(",", ":"), sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    return text.replace("<", "\\u003c")


__all__ = [
    "Markup",
    "decode_attribute_entities",
    "escape",
    "escape_attribute_value",
    "escape_to_str",
    "script_json",
]
