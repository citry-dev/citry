"""Strict JSON normalization shared by prepared-value producers and assembly."""

from __future__ import annotations

import math
from collections.abc import Mapping
from html import unescape
from typing import cast

from citry.constness import const_value, is_const


def _json_plain(value: object, _ancestors: set[int] | None = None) -> object:
    """Detach one value into exact JSON scalars, objects, and arrays."""
    if is_const(value):
        return _json_plain(const_value(value), _ancestors)
    from citry.ext.i18n.bindings import CapturedTranslationText  # noqa: PLC0415

    if type(value) is CapturedTranslationText:
        return str(value)
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"data sent to the browser must contain only finite numbers, got {value!r}")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError(
                "data sent to the browser must use only string dict keys, got " + _first_non_string_key(value)
            )
        ancestors = set() if _ancestors is None else _ancestors
        if id(value) in ancestors:
            raise ValueError("data sent to the browser must not contain itself")
        ancestors.add(id(value))
        try:
            return {str(key): _json_plain(item, ancestors) for key, item in value.items()}
        finally:
            ancestors.remove(id(value))
    if isinstance(value, (list, tuple)):
        ancestors = set() if _ancestors is None else _ancestors
        if id(value) in ancestors:
            raise ValueError("data sent to the browser must not contain itself")
        ancestors.add(id(value))
        try:
            return [_json_plain(item, ancestors) for item in value]
        finally:
            ancestors.remove(id(value))
    raise TypeError(
        "data sent to the browser must contain only dicts, lists, strings, numbers, booleans, and None, "
        f"got {type(value).__name__}"
    )


def _first_non_string_key(value: Mapping[object, object]) -> str:
    """Describe the key that broke the string-key rule, so the error names it."""
    key = next(key for key in value if not isinstance(key, str))
    return f"{type(key).__name__} key {key!r}"


# JavaScript numbers hold integers exactly only up to 2**53 - 1.
_JS_SAFE_INTEGER = 2**53 - 1


def _vue_attribute_value(value: object) -> object:
    """
    Return the value Vue should set for one Python-resolved HTML attribute.

    Python's HTML output writes every attribute value as ``str(value)`` (or a
    value's own ``__html__`` markup), while Vue's object binding turns a
    JavaScript value into text its own way: a dict becomes
    ``"[object Object]"``, a list ``"1,2"``, and ``1.0`` becomes ``"1"``. So
    any value whose JavaScript text could differ is sent as the exact text
    the browser reads from Python's HTML. An exact str or a JavaScript-safe
    int already reads the same in both. ``None`` and ``False`` omit the
    attribute. ``True`` is sent unchanged: Vue writes it as the text
    ``true`` on an attribute that is not an HTML boolean attribute, where
    Python's HTML writes only the attribute name.

    ``str()`` and ``__html__()`` run here during the render, and the HTML
    output calls them again when it serializes, so a value whose text
    changes between calls can differ between the two.
    """
    if is_const(value):
        value = const_value(value)
    value_type = type(value)
    if value is None or value_type is bool or value_type is str:
        return value
    if value_type is int:
        if -_JS_SAFE_INTEGER <= cast("int", value) <= _JS_SAFE_INTEGER:
            return value
        try:
            return str(value)
        except ValueError:
            # Past Python's digit limit the int has no text at all. Keep it,
            # so serializing fails with the same error the HTML output gives.
            return value
    html = getattr(value, "__html__", None)
    if html is not None:
        # Python's HTML writes this markup unescaped inside the quotes, so the
        # browser's attribute value is its entity-decoded text. Decoding can
        # produce text such as a javascript: URL; Vue then sets the same value
        # the server HTML already gave the browser.
        return unescape(html())
    return str(value)


def _vue_attribute_map(values: dict[str, object]) -> dict[str, object]:
    """Convert an attribute map for Vue, reusing it when no value needs converting."""
    for value in values.values():
        value_type = type(value)
        if value_type is str or value_type is bool or value is None:
            continue
        if value_type is int and -_JS_SAFE_INTEGER <= cast("int", value) <= _JS_SAFE_INTEGER:
            continue
        return {name: _vue_attribute_value(item) for name, item in values.items()}
    return values


def _copy_evaluated_json(value: object) -> object:
    """
    Copy a value the generated simple JSON evaluator wrote into prepared data.

    That evaluator checks every value it reads before it runs and only writes
    exact str, int, bool, None and finite float scalars, plus dicts with str
    keys and lists it creates itself, so the value is already strict JSON and
    has no cycles. Assembly still needs its own copy, because the leaf and the
    render record holding it still reference the original dicts and lists.
    """
    value_type = type(value)
    if value_type is dict:
        return {key: _copy_evaluated_json(item) for key, item in cast("dict[str, object]", value).items()}
    if value_type is list:
        return [_copy_evaluated_json(item) for item in cast("list[object]", value)]
    return value
