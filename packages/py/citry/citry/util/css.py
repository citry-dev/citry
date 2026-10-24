"""Serializing Python values into CSS custom-property values (for ``css_data()``)."""

from __future__ import annotations

import re
from math import isfinite

from citry.secret import Secret

# The advice given when a `css_data()` value holds a `Secret`; the caller
# puts the component, the entry name, and "holds a citry.Secret," in front.
SECRET_IN_CSS_DATA_ADVICE = (
    "and Citry never sends a Secret to the browser. "  # noqa: S105 - advice text
    "Read the value with get_secret_value() in server code that needs it and leave it out of css_data()."
)

# A CSS function call: a name followed by an opening parenthesis,
# e.g. `calc(100% - 20px)`, `var(--color)`, `rgba(255, 0, 0, 0.5)`.
_CSS_FUNC_RE = re.compile(r"^[a-zA-Z0-9_-]+\(")
# `{` and `}` are rejected outright below, so only `(` and `[` group here.
_CSS_BLOCK_PAIRS = {"(": ")", "[": "]"}
_CSS_BLOCK_CLOSERS = frozenset(_CSS_BLOCK_PAIRS.values())


def is_css_func(value: str) -> bool:
    """Whether a string is a CSS function call (``calc(...)``, ``var(...)``, ...)."""
    return bool(_CSS_FUNC_RE.match(value.strip()))


def validate_css_var_name(name: str) -> None:
    """Require a safe suffix for the emitted ``--<name>`` custom property."""
    if not name:
        raise ValueError("CSS custom-property names cannot be empty.")

    for index, char in enumerate(name):
        codepoint = ord(char)
        valid_ascii = char.isascii() and (char.isalnum() or char in "-_")
        valid_non_ascii = codepoint >= 0x80 and not 0xD800 <= codepoint <= 0xDFFF
        if valid_ascii or valid_non_ascii:
            continue
        msg = (
            f"CSS custom-property name {name!r} contains invalid character {char!r} "
            f"at offset {index}. Use letters, digits, '-', '_', or non-ASCII identifier characters."
        )
        raise ValueError(msg)


def _serialize_css_string(value: str) -> str:
    """Serialize one Python string using the CSSOM string-escaping rules."""
    parts = ['"']
    for char in value:
        codepoint = ord(char)
        if char == "\0":
            parts.append("\ufffd")
        elif codepoint <= 0x1F or codepoint == 0x7F:
            parts.append(f"\\{codepoint:x} ")
        elif char in {'"', "\\"}:
            parts.append(f"\\{char}")
        else:
            parts.append(char)
    parts.append('"')
    return "".join(parts)


_CSS_WHITESPACE = "\n\r\t\f "


def _consume_css_escape(value: str, index: int) -> int:
    r"""
    Return the index after a CSS escape that starts at the backslash ``index``.

    A backslash followed by a newline is not a valid escape; the caller
    rejects that. A backslash at the very end of the input is a parse error
    the browser would replace with U+FFFD, so the caller rejects it too.
    """
    if index + 1 >= len(value) or value[index + 1] in "\n\r\f":
        raise ValueError(f"CSS value has a backslash that does not start a valid escape at offset {index}.")
    return index + 2


def validate_css_var_value(value: str) -> None:
    """
    Reject text that can escape or structurally corrupt one CSS declaration.

    This walks ``value`` the way the CSS Syntax Level 3 tokenizer does, so a
    custom-property value cannot close the generated declaration, start a new
    rule, or end the ``<style>`` element the browser builds it into. It
    rejects a malformed string or ``url()`` token (the browser's bad-string
    and bad-url cases), a comment, an unbalanced bracket, any ``<`` (so
    ``</style`` and ``<!--`` cannot appear), and a top-level ``;``, ``{``,
    ``}`` or ``!``. It is not a full property-type validator.
    """
    # The HTML parser ends a <style> element only at `</style`, in any letter
    # case, and `<!--` can start a comment state, so both are refused in every
    # token, string and url() included. Other markup such as `<svg></svg>`
    # stays allowed inside a string or url(), where SVG data URLs need it.
    folded = value.lower()
    for marker in ("</style", "<!--"):
        offset = folded.find(marker)
        if offset != -1:
            raise ValueError(f"CSS value contains {marker!r} at offset {offset}.")

    blocks: list[tuple[str, int]] = []
    index = 0
    length = len(value)

    while index < length:
        char = value[index]
        codepoint = ord(char)

        if char == "\0":
            raise ValueError(f"CSS value contains a null character at offset {index}.")
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError(f"CSS value contains a Unicode surrogate at offset {index}.")

        # A comment could hide a declaration break from a reader, and the
        # browser strips it, so neither path should rely on it.
        if char == "/" and index + 1 < length and value[index + 1] == "*":
            raise ValueError(f"CSS value contains a comment at offset {index}.")

        # `<` never begins a CSS token, so it only appears here as the start
        # of `</style` or `<!--`, both of which end or corrupt the element.
        if char == "<":
            raise ValueError(f"CSS value contains '<' at offset {index}.")

        if char in {'"', "'"}:
            index = _scan_css_string(value, index)
            continue

        if char == "\\":
            index = _consume_css_escape(value, index)
            continue

        # `url(` with no quote reads its own token up to the next `)`, where
        # a quote, `(`, or whitespace inside makes the browser's bad-url
        # token. A quoted `url("...")` is an ordinary function plus string,
        # handled by the bracket and string branches.
        if char in "uU" and value[index : index + 4].lower() == "url(" and not _is_quoted_url(value, index):
            index = _scan_css_url(value, index)
            continue

        # A brace never belongs in one custom-property value; it would open or
        # close a rule block in the stylesheet the browser builds.
        if char in "{}":
            raise ValueError(f"CSS value contains {char!r} at offset {index}.")

        expected_closer = _CSS_BLOCK_PAIRS.get(char)
        if expected_closer is not None:
            blocks.append((expected_closer, index))
            index += 1
            continue

        if char in _CSS_BLOCK_CLOSERS:
            if not blocks:
                raise ValueError(f"CSS value contains unmatched {char!r} at offset {index}.")
            expected, opening_index = blocks.pop()
            if char != expected:
                msg = (
                    f"CSS value closes the block opened at offset {opening_index} with {char!r}; "
                    f"expected {expected!r}."
                )
                raise ValueError(msg)
            index += 1
            continue

        # `;`, `{`, `}` and `!` at the top level each end the one declaration
        # this value belongs to or begin another, so none may appear outside
        # a bracketed group such as `calc(...)`.
        if char in ";!" and not blocks:
            raise ValueError(f"CSS value contains a top-level {char!r} at offset {index}.")

        index += 1

    if blocks:
        expected, opening_index = blocks[-1]
        raise ValueError(f"CSS value has an unclosed block at offset {opening_index}; expected {expected!r}.")


def _scan_css_string(value: str, start: int) -> int:
    """Return the index after a well-formed CSS string, or reject a bad-string token."""
    quote = value[start]
    index = start + 1
    length = len(value)
    while index < length:
        char = value[index]
        if char == quote:
            return index + 1
        if char in "\n\r\f":
            # A newline inside a string is the browser's bad-string token; it
            # ends the string early and lets the rest restart the parser.
            raise ValueError(f"CSS string contains an unescaped newline at offset {index}.")
        if char == "\0":
            raise ValueError(f"CSS value contains a null character at offset {index}.")
        if char == "\\":
            if index + 1 < length and value[index + 1] in "\n\r\f":
                # A backslash-newline is a line continuation inside a string.
                index += 2
                continue
            index = _consume_css_escape(value, index)
            continue
        index += 1
    raise ValueError(f"CSS value contains an unclosed {quote!r} string from offset {start}.")


def _is_quoted_url(value: str, start: int) -> bool:
    """Whether ``url(`` at ``start`` is immediately followed (after spaces) by a quote."""
    index = start + 4
    while index < len(value) and value[index] in _CSS_WHITESPACE:
        index += 1
    return index < len(value) and value[index] in {'"', "'"}


def _scan_css_url(value: str, start: int) -> int:
    """Return the index after an unquoted ``url(...)``, or reject a bad-url token."""
    index = start + 4
    length = len(value)
    while index < length:
        char = value[index]
        if char == ")":
            return index + 1
        # A quote, `(`, whitespace in the middle, or a non-printable makes the
        # browser's bad-url token, which swallows text up to the next `)` and
        # can carry a declaration break out of the URL.
        if char in "\"'(" or char == "\0" or ord(char) <= 0x08 or ord(char) == 0x0B or 0x0E <= ord(char) <= 0x1F:
            raise ValueError(f"CSS url() contains {char!r} at offset {index}, which the browser reads as a bad url.")
        if char in _CSS_WHITESPACE:
            while index < length and value[index] in _CSS_WHITESPACE:
                index += 1
            if index >= length or value[index] != ")":
                raise ValueError(f"CSS url() has whitespace before its end at offset {index}.")
            return index + 1
        if char == "\\":
            index = _consume_css_escape(value, index)
            continue
        index += 1
    raise ValueError(f"CSS value contains an unclosed url() from offset {start}.")


def serialize_css_var_value(value: object) -> str:
    """
    Turn one ``css_data()`` scalar into structurally contained CSS text.

    Finite numbers become bare numbers, ``None`` becomes the empty string, and
    strings pass through as written, except that text containing whitespace is
    quoted and escaped unless it begins with a CSS function. Raw values are
    checked for declaration and style-tag breakout, balanced blocks, strings,
    and comments. This is not a full CSS grammar or property-type validator.

    Booleans and structured values are rejected rather than serialized with
    Python ``str()`` representations.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        raise TypeError("CSS data values must be strings, numbers, or None; bool is not supported.")
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("CSS data numbers must be finite.")
        return str(value)
    if isinstance(value, str):
        null_offset = value.find("\0")
        if null_offset != -1:
            raise ValueError(f"CSS value contains a null character at offset {null_offset}.")
        serialized = (
            _serialize_css_string(value) if any(char.isspace() for char in value) and not is_css_func(value) else value
        )
    elif type(value) is Secret:
        # The stylesheet holding these values can be fetched by URL, so a
        # wrapped secret gets its own reason rather than the generic one.
        raise TypeError(f"it holds a citry.Secret, {SECRET_IN_CSS_DATA_ADVICE}")
    else:
        msg = f"CSS data values must be strings, numbers, or None; {type(value).__name__} is not supported."
        raise TypeError(msg)

    validate_css_var_value(serialized)
    return serialized
