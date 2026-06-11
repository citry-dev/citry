"""
HTML attribute values: class/style normalization, merging, and formatting.

This module is the value layer of the attribute-rendering design
(docs/design/html_attrs.md). It knows nothing about templates or nodes; it
only answers "given these attribute values, what HTML attribute string do
they make?". The template-side ``ElementAttrsNode`` and user code in
``template_data()`` both call into it.

The ``class`` and ``style`` attributes accept structured values, following
Vue's ``mergeProps`` semantics (and django-components' port of them):

- ``class``: a plain string, a dict of ``{class_name: enabled_bool}``, or a
  list mixing strings, dicts, and nested lists.
- ``style``: a plain string of inline CSS, a dict of
  ``{css_property: css_value}``, or a list mixing those. Property names are
  written as CSS spells them (kebab-case); values may be strings or numbers.

Semantics carried over from django-components (same author, deliberate
choices, and parity keeps its test suite portable):

- In a ``class`` list, a later falsy dict entry removes a class added
  earlier. (Vue keeps it; this is a documented divergence.)
- In a ``style`` merge, a ``None`` value means "skip, let an earlier value
  stand", while a literal ``False`` removes the property entirely.

All escaping goes through ``citry.util.html`` (markupsafe): values render
escaped unless they carry ``__html__``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

from citry.util.html import SafeString, escape

ClassValue: TypeAlias = "str | Mapping[str, bool] | Sequence[ClassValue]"
"""A ``class`` attribute value: string, ``{class_name: bool}`` dict, or a list of those."""

StyleDict: TypeAlias = Mapping[str, "str | int | float | bool | None"]
"""Inline CSS as a dict. ``None`` skips the entry; ``False`` removes the property."""

StyleValue: TypeAlias = "str | StyleDict | Sequence[StyleValue]"
"""A ``style`` attribute value: inline CSS string, ``StyleDict``, or a list of those."""

# Splits a class string on runs of whitespace.
_whitespace_re = re.compile(r"\s+")
# Matches CSS comments `/* ... */`.
_style_comment_re = re.compile(r"/\*.*?\*/", re.DOTALL)
# Splits CSS declarations on `;`, but not inside parentheses,
# so `url(data:image/png;base64,...)` stays in one piece.
_style_delimiter_re = re.compile(r";(?![^(]*\))", re.DOTALL)
# Splits one CSS declaration into name and value on the first `:`.
_style_property_re = re.compile(r":(.+)", re.DOTALL)


def normalize_class(value: ClassValue) -> str:
    """
    Turn a structured ``class`` value into a plain class string.

    - A string is used as-is (stripped).
    - A dict keeps only the keys whose value is truthy.
    - A list may mix strings, dicts, and nested lists. Each item converts to
      a ``{class_name: bool}`` dict (strings split on whitespace, all
      ``True``) and the dicts merge left to right, so a later falsy entry
      removes a class added earlier.

    Example::

        normalize_class(["btn btn-lg", {"active": True, "hidden": False}])
        # -> "btn btn-lg active"
    """
    if isinstance(value, str):
        return value.strip()

    flattened: dict[str, bool]
    if isinstance(value, (list, tuple)):
        flattened = _flatten_class(value)
    elif isinstance(value, Mapping):
        flattened = dict(value)
    else:
        msg = f"Invalid class value: {value!r}"
        raise TypeError(msg)

    return " ".join(name for name, enabled in flattened.items() if enabled)


def _flatten_class(value: ClassValue) -> dict[str, bool]:
    """Convert any ``class`` value form into one ``{class_name: bool}`` dict."""
    res: dict[str, bool] = {}
    if isinstance(value, str):
        res.update({part: True for part in _whitespace_re.split(value) if part})
    elif isinstance(value, (list, tuple)):
        for item in value:
            res.update(_flatten_class(item))
    elif isinstance(value, Mapping):
        res.update(value)
    else:
        msg = f"Invalid class value: {value!r}"
        raise TypeError(msg)
    return res


def normalize_style(value: StyleValue) -> str:
    """
    Turn a structured ``style`` value into an inline CSS string.

    - A string is used as-is (stripped).
    - A dict renders each entry as ``property: value;``. Property names are
      used as written (kebab-case); numbers render bare (``width: 100``).
    - A list may mix strings, dicts, and nested lists. Strings are parsed
      into property dicts (see ``parse_string_style``) and the dicts merge
      left to right, so the last value of a property wins.

    Two special values steer a merge: ``None`` skips the entry (an earlier
    value for the property stands), and a literal ``False`` removes the
    property entirely, even if set earlier.

    Example::

        normalize_style(["color: red; width: 100px", {"color": "green", "width": False}])
        # -> "color: green;"
    """
    merged: dict[str, Any]
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple, Mapping)):
        merged = _flatten_style(value)
    else:
        msg = f"Invalid style value: {value!r}"
        raise TypeError(msg)

    return " ".join(f"{prop}: {val};" for prop, val in merged.items() if val is not None and val is not False)


def _flatten_style(value: StyleValue) -> dict[str, Any]:
    """Convert any ``style`` value form into one property dict, dropping ``None`` entries."""
    res: dict[str, Any] = {}
    if isinstance(value, str):
        res.update(parse_string_style(value))
    elif isinstance(value, (list, tuple)):
        for item in value:
            res.update(_flatten_style(item))
    elif isinstance(value, Mapping):
        res.update({prop: val for prop, val in value.items() if val is not None})
    else:
        msg = f"Invalid style value: {value!r}"
        raise TypeError(msg)
    return res


def parse_string_style(css_text: str) -> dict[str, Any]:
    """
    Parse an inline CSS string into a property dict.

    Strips ``/* ... */`` comments. Declarations split on ``;`` except inside
    parentheses, so ``url(data:image/png;base64,...)`` survives. A
    declaration without a ``:`` is dropped.

    Example::

        parse_string_style("color: red; width: 100px; /* note */")
        # -> {"color": "red", "width": "100px"}
    """
    css_text = _style_comment_re.sub("", css_text)

    res: dict[str, Any] = {}
    for declaration in _style_delimiter_re.split(css_text):
        if not declaration:
            continue
        parts = _style_property_re.split(declaration)
        if len(parts) > 1:
            res[parts[0].strip()] = parts[1].strip()
    return res


def merge_attrs(*attrs_dicts: Mapping[str, Any]) -> dict[str, Any]:
    """
    Merge attribute dicts left to right into one dict.

    Every key resolves last-one-wins, except ``class`` and ``style``: their
    values from all dicts are collected and combined per ``normalize_class``
    / ``normalize_style``, so several sources can contribute classes and
    style properties without overwriting each other.

    Key order in the result is the order each key was first seen, so a later
    override does not move an attribute.

    Example::

        merge_attrs(
            {"class": "btn", "id": "first"},
            {"class": {"active": True}, "id": "second"},
        )
        # -> {"class": "btn active", "id": "second"}
    """
    result: dict[str, Any] = {}
    classes: list[ClassValue] = []
    styles: list[StyleValue] = []

    for attrs in attrs_dicts:
        for key, value in attrs.items():
            # A `None` class/style contributes nothing (a spread dict often
            # carries an optional class), but still reserves the key's position.
            if key == "class":
                if value is not None:
                    classes.append(value)
                result[key] = None  # placeholder, keeps first-seen position
            elif key == "style":
                if value is not None:
                    styles.append(value)
                result[key] = None  # placeholder, keeps first-seen position
            else:
                result[key] = value

    if classes:
        result["class"] = normalize_class(classes)
    if styles:
        result["style"] = normalize_style(styles)

    return result


def format_attrs(attrs: Mapping[str, Any]) -> SafeString:
    """
    Format an attribute dict into an HTML attribute string.

    - ``True`` renders the bare attribute (``disabled``); ``False`` and
      ``None`` omit the attribute entirely.
    - ``class`` and ``style`` values may use the structured forms; they are
      normalized here, so ``merge_attrs`` output and hand-built dicts render
      the same. When they normalize to an empty string the attribute is
      omitted (an empty ``class=""`` would read as a boolean attribute under
      citry's HTML rules).
    - Everything else renders ``key="value"``, escaped; values with
      ``__html__`` pass through unescaped.

    Example::

        format_attrs({"class": ["btn", {"active": True}], "disabled": True, "data-id": 3})
        # -> 'class="btn active" disabled data-id="3"'
    """
    parts: list[str] = []
    for key, value in attrs.items():
        if key == "class" and value is not None and not isinstance(value, str):
            value = normalize_class(value)  # noqa: PLW2901
            if not value:
                continue
        elif key == "style" and value is not None and not isinstance(value, str):
            value = normalize_style(value)  # noqa: PLW2901
            if not value:
                continue

        if value is None or value is False:
            continue
        if value is True:
            parts.append(escape(key))
        else:
            parts.append(f'{escape(key)}="{escape(value)}"')

    return SafeString(" ".join(parts))
