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
_CSS_NULL_OR_SURROGATE_RE = re.compile(r"[\x00\ud800-\udfff]")
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
_CSS_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _consume_css_escape(value: str, index: int) -> int:
    r"""
    Return the index after a CSS escape that starts at the backslash ``index``.

    Raise ``ValueError`` for a backslash followed by a newline, which is not a
    valid escape, or for a backslash at the very end of the input.
    """
    if index + 1 >= len(value) or value[index + 1] in "\n\r\f":
        raise ValueError(f"CSS value has a backslash that does not start a valid escape at offset {index}.")
    index += 1
    if value[index] not in _CSS_HEX_DIGITS:
        return index + 1
    # A hex escape is up to six hex digits plus one whitespace, which the
    # browser reads as part of the escape; CRLF counts as one newline.
    end = index
    while end < len(value) and end - index < 6 and value[end] in _CSS_HEX_DIGITS:
        end += 1
    if value.startswith("\r\n", end):
        return end + 2
    if end < len(value) and value[end] in _CSS_WHITESPACE:
        return end + 1
    return end


def validate_css_var_value(value: str) -> None:
    """
    Reject text that can escape or structurally corrupt one CSS declaration.

    This walks ``value`` the way the CSS Syntax Level 3 tokenizer does, so a
    custom-property value cannot close the generated declaration, start a new
    rule, or end the ``<style>`` element the browser builds it into. It
    rejects a malformed string or ``url()`` token (the browser's bad-string
    and bad-url cases), a comment, an unbalanced bracket, a brace, a ``<`` or
    backslash outside a string or ``url()``, a null or surrogate character,
    ``</style``, or ``<!--`` anywhere, and a top-level ``;`` or ``!``. It is
    not a full property-type validator.
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

    # A null character or lone surrogate is refused everywhere, strings and
    # url() included, so check the whole value once before scanning it.
    unreadable = _CSS_NULL_OR_SURROGATE_RE.search(value)
    if unreadable is not None:
        kind = "a null character" if unreadable.group() == "\0" else "a Unicode surrogate"
        raise ValueError(f"CSS value contains {kind} at offset {unreadable.start()}.")

    blocks: list[tuple[str, int]] = []
    index = 0
    length = len(value)

    while index < length:
        char = value[index]

        # The browser drops a comment before it reads the value, so a value
        # with one would not mean what it appears to say.
        if char == "/" and index + 1 < length and value[index + 1] == "*":
            raise ValueError(f"CSS value contains a comment at offset {index}.")

        # A value never needs `<` outside a string or url(), so refuse it
        # here rather than judge what follows it.
        if char == "<":
            raise ValueError(f"CSS value contains '<' at offset {index}.")

        if char in {'"', "'"}:
            index = _scan_css_string(value, index)
            continue

        # A `css_data()` value never needs a backslash outside a string, and
        # refusing it keeps every name in the value readable as written.
        if char == "\\":
            raise ValueError(f"CSS value contains a backslash outside a string at offset {index}.")

        # `url(` with no quote reads its own token up to the next `)`, where
        # a quote, `(`, or whitespace inside makes the browser's bad-url
        # token. A quoted `url("...")` is an ordinary function plus string,
        # handled by the bracket and string branches.
        # `url(` starts a url token only where a new token starts; after a
        # name character, or a `#`, `@` or `\` that joins the next name, it is
        # part of that name (`xurl(`, `#url(`), not a url token.
        previous = value[index - 1] if index else ""
        # `previous` is empty at the start of the value, which is a token start.
        at_token_start = previous == "" or not (previous.isalnum() or previous in "-_#@\\" or ord(previous) >= 0x80)
        if (
            char in "uU"
            and at_token_start
            and value[index : index + 4].lower() == "url("
            and not _is_quoted_url(value, index)
        ):
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

        # `;` and `!` at the top level end this declaration or change its
        # priority, so neither may appear outside a bracketed group such as
        # `calc(...)`.
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
            # ends the string early, so the rest would be read as more CSS.
            raise ValueError(f"CSS string contains an unescaped newline at offset {index}.")
        if char == "\\":
            if index + 1 < length and value[index + 1] in "\n\r\f":
                # A backslash-newline is a line continuation inside a string;
                # CRLF counts as one newline.
                index += 3 if value.startswith("\r\n", index + 1) else 2
                continue
            index = _consume_css_escape(value, index)
            continue
        index += 1
    raise ValueError(f"CSS value contains an unclosed {quote!r} string from offset {start}.")


def _is_quoted_url(value: str, start: int) -> bool:
    """Whether ``url(`` at ``start`` is followed by a quote, after any whitespace."""
    index = start + 4
    while index < len(value) and value[index] in _CSS_WHITESPACE:
        index += 1
    return index < len(value) and value[index] in {'"', "'"}


def _scan_css_url(value: str, start: int) -> int:
    """Return the index after an unquoted ``url(...)``, or reject a bad-url token."""
    index = start + 4
    length = len(value)
    # The browser skips whitespace before the address starts.
    while index < length and value[index] in _CSS_WHITESPACE:
        index += 1
    while index < length:
        char = value[index]
        if char == ")":
            return index + 1
        # A quote, `(`, whitespace in the middle, or a non-printable (DEL, or
        # a control character other than tab, newline, form feed and carriage
        # return) makes the browser's bad-url token, which drops the rest of
        # the value up to the next `)`.
        code = ord(char)
        if char in "\"'(" or code <= 0x08 or code in {0x0B, 0x7F} or 0x0E <= code <= 0x1F:
            # A quote inside the URL still needs a backslash after the URL is quoted.
            advice = " A quote inside a quoted URL needs a backslash before it." if char in "\"'" else ""
            msg = (
                f"CSS url() contains {char!r} at offset {index}, which the browser cannot read in an unquoted URL. "
                f'Quote the URL, as in url("...").{advice}'
            )
            raise ValueError(msg)
        if char in _CSS_WHITESPACE:
            whitespace_start = index
            while index < length and value[index] in _CSS_WHITESPACE:
                index += 1
            if index >= length or value[index] != ")":
                msg = (
                    f"CSS url() has whitespace inside it at offset {whitespace_start}. "
                    'Quote the URL, as in url("...").'
                )
                raise ValueError(msg)
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
