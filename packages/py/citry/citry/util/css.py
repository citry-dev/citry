"""Serializing Python values into CSS custom-property values (for ``css_data()``)."""

from __future__ import annotations

import re

# A CSS function call: a name followed by an opening parenthesis,
# e.g. `calc(100% - 20px)`, `var(--color)`, `rgba(255, 0, 0, 0.5)`.
_CSS_FUNC_RE = re.compile(r"^[a-zA-Z0-9_-]+\(")


def is_css_func(value: str) -> bool:
    """Whether a string is a CSS function call (``calc(...)``, ``var(...)``, ...)."""
    return bool(_CSS_FUNC_RE.match(value.strip()))


def serialize_css_var_value(value: object) -> str:
    """
    Turn one ``css_data()`` value into valid CSS custom-property text.

    Numbers become bare numbers, ``None`` becomes the empty string, and
    strings pass through as written, except that a string with spaces is
    quoted (so ``"Helvetica Neue"`` stays one value) unless it is a CSS
    function call, which must stay unquoted to work.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if " " in value and not is_css_func(value):
            return f'"{value}"'
        return value
    return str(value)
