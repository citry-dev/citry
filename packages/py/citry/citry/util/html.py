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
from html import unescape
from html.entities import html5
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


def _decode_attribute_charref(match: re.Match[str]) -> str:
    """Decode one character reference the way a browser does inside an attribute value."""
    name = match.group(1)
    # Numeric references, and names that match exactly, decode as in text.
    if name[0] == "#" or name in html5:
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


def decode_attribute_entities(html: str) -> str:
    """
    Return the attribute value a browser reads from ``html`` written inside quotes.

    This follows the HTML parser's rules for character references in an
    attribute value, which differ from text in one way: a legacy reference
    without ``;`` stays as typed when ``=`` or a letter or digit follows it.
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
