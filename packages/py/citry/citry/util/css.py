"""Serializing Python values into CSS custom-property values (for ``css_data()``)."""

from __future__ import annotations

import re
from math import isfinite

# A CSS function call: a name followed by an opening parenthesis,
# e.g. `calc(100% - 20px)`, `var(--color)`, `rgba(255, 0, 0, 0.5)`.
_CSS_FUNC_RE = re.compile(r"^[a-zA-Z0-9_-]+\(")
_CSS_BLOCK_PAIRS = {"(": ")", "[": "]", "{": "}"}
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


def validate_css_var_value(value: str) -> None:
    """Reject text that can escape or structurally corrupt one CSS declaration."""
    if "</style" in value.lower():
        raise ValueError("CSS values cannot contain a '</style' end tag.")

    blocks: list[tuple[str, int]] = []
    quote: tuple[str, int] | None = None
    index = 0

    while index < len(value):
        char = value[index]
        codepoint = ord(char)

        if char == "\0":
            raise ValueError(f"CSS value contains a null character at offset {index}.")
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValueError(f"CSS value contains a Unicode surrogate at offset {index}.")

        if quote is not None:
            if char == "\\":
                if index + 1 >= len(value):
                    raise ValueError(f"CSS value ends with a dangling escape at offset {index}.")
                index += 2
                continue
            if char == quote[0]:
                quote = None
            elif char in "\n\r\f":
                raise ValueError(f"CSS string contains an unescaped newline at offset {index}.")
            index += 1
            continue

        if char == "/" and index + 1 < len(value) and value[index + 1] == "*":
            comment_end = value.find("*/", index + 2)
            if comment_end == -1:
                raise ValueError(f"CSS value contains an unclosed comment at offset {index}.")
            index = comment_end + 2
            continue

        if char in {'"', "'"}:
            quote = (char, index)
            index += 1
            continue

        if char == "\\":
            if index + 1 >= len(value):
                raise ValueError(f"CSS value ends with a dangling escape at offset {index}.")
            index += 2
            continue

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

        if char == ";" and not blocks:
            raise ValueError(f"CSS value contains a top-level ';' at offset {index}.")

        index += 1

    if quote is not None:
        raise ValueError(f"CSS value contains an unclosed {quote[0]!r} string from offset {quote[1]}.")
    if blocks:
        expected, opening_index = blocks[-1]
        raise ValueError(f"CSS value has an unclosed block at offset {opening_index}; expected {expected!r}.")


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
    else:
        msg = f"CSS data values must be strings, numbers, or None; {type(value).__name__} is not supported."
        raise TypeError(msg)

    validate_css_var_value(serialized)
    return serialized
