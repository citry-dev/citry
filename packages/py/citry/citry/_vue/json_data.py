"""Strict JSON normalization shared by prepared-value producers and assembly."""

from __future__ import annotations

import json
import math
from collections.abc import Iterator, Mapping
from typing import cast

from citry.constness import const_value, is_const
from citry.ext.i18n.bindings import CapturedTranslationText
from citry.secret import Secret
from citry.util.html import decode_attribute_entities


class _SecretInBrowserDataError(TypeError):
    """
    Raised when data bound for the browser holds a ``citry.Secret``.

    A subclass of the ``TypeError`` every other non-JSON value raises, so
    existing handlers keep working, while a caller that knows the component
    can tell this case apart and name the key that holds the secret.
    """


# How many levels of nested data `_json_plain` and `_copy_evaluated_json`
# copy with direct calls before they hand the rest of a value to a stack
# walk. Direct calls are faster on the shallow data a render usually sends,
# and the bound keeps their Python frames to about 100 however deeply the
# data nests.
_DIRECT_JSON_DEPTH = 32


def _json_plain(value: object, _ancestors: set[int] | None = None) -> object:
    """
    Detach one value into exact JSON scalars, objects, and arrays.

    The first `_DIRECT_JSON_DEPTH` levels are copied with direct calls, and
    anything deeper goes to `_json_plain_walk`, which uses a stack, so the
    number of Python frames stays bounded however deeply the data nests.
    Both visit values in the same order, so the first value refused, and the
    error raised, do not depend on where the walk switches.
    """
    if is_const(value):
        return _json_plain(const_value(value), _ancestors)
    if type(value) is CapturedTranslationText:
        return str(value)
    if type(value) in _PLAIN_SCALARS:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"data sent to the browser must contain only finite numbers, got {value!r}")
        return value
    if isinstance(value, Mapping):
        # Inlined rather than a `_check_string_keys` call, which costs every
        # render a little; the stack walk makes the same check through it.
        if any(not isinstance(key, str) for key in value):
            raise TypeError(
                "data sent to the browser must use only string dict keys, got " + _first_non_string_key(value)
            )
        ancestors = set() if _ancestors is None else _ancestors
        if id(value) in ancestors:
            raise ValueError(_LOOP_MESSAGE)
        ancestors.add(id(value))
        try:
            # `ancestors` holds this container and the ones around it, so its
            # size is this container's depth.
            if len(ancestors) > _DIRECT_JSON_DEPTH:
                return _json_plain_walk(value, ancestors)
            # An exact str, int, bool or None is copied as it is, which
            # skips a call for most items and more than pays for the depth
            # check above.
            return {
                str(key): item if type(item) in _PLAIN_SCALARS else _json_plain(item, ancestors)
                for key, item in value.items()
            }
        finally:
            ancestors.remove(id(value))
    if isinstance(value, (list, tuple)):
        ancestors = set() if _ancestors is None else _ancestors
        if id(value) in ancestors:
            raise ValueError(_LOOP_MESSAGE)
        ancestors.add(id(value))
        try:
            if len(ancestors) > _DIRECT_JSON_DEPTH:
                return _json_plain_walk(value, ancestors)
            return [item if type(item) in _PLAIN_SCALARS else _json_plain(item, ancestors) for item in value]
        finally:
            ancestors.remove(id(value))
    # Checked only after every JSON type, so ordinary data pays nothing. A
    # Secret is not a str, so without this branch it would still be refused,
    # but by a message that does not say why or what to do.
    if type(value) is Secret:
        raise _SecretInBrowserDataError(
            "data sent to the browser must not contain a citry.Secret; read the value on the server instead"
        )
    raise TypeError(
        "data sent to the browser must contain only dicts, lists, strings, numbers, booleans, and None, "
        f"got {type(value).__name__}"
    )


# The exact types `_json_plain` returns as they are.
_PLAIN_SCALARS = frozenset({type(None), bool, int, str})

_LOOP_MESSAGE = "data sent to the browser must not contain itself; return a copy without the loop"


def _check_string_keys(value: Mapping[object, object]) -> None:
    """Refuse a dict whose keys are not all strings, before any of its values is read."""
    if any(not isinstance(key, str) for key in value):
        raise TypeError("data sent to the browser must use only string dict keys, got " + _first_non_string_key(value))


def _json_plain_walk(
    source: Mapping[object, object] | list[object] | tuple[object, ...], ancestors: set[int]
) -> object:
    """
    Copy a container `_json_plain` has already checked and entered, with a stack instead of nested calls.

    ``ancestors`` already holds ``source``, and the caller removes it again.
    """
    root = _OpenContainer(source)
    # Each entry is a container being copied, innermost last.
    pending: list[_OpenContainer] = [root]
    while pending:
        current = pending[-1]
        entry = next(current.items, _END_OF_ITEMS)
        if entry is _END_OF_ITEMS:
            pending.pop()
            # The caller entered the root, so it also leaves it.
            if pending:
                ancestors.remove(current.source_id)
            continue
        if current.is_object:
            key, item = cast("tuple[object, object]", entry)
            # A dict comprehension computes the key before its value, and a
            # str subclass may define __str__, so the key comes first here too.
            name = str(key)
        else:
            item = entry
        if is_const(item):
            item = const_value(item)
        if isinstance(item, (Mapping, list, tuple)):
            # The same checks, in the same order, as `_json_plain` makes
            # when it enters a container.
            if isinstance(item, Mapping):
                _check_string_keys(item)
            if id(item) in ancestors:
                raise ValueError(_LOOP_MESSAGE)
            ancestors.add(id(item))
            child = _OpenContainer(item)
            pending.append(child)
            plain: object = child.copy
        else:
            # A scalar, or a value `_json_plain` refuses with its own error.
            plain = _json_plain(item)
        if current.is_object:
            cast("dict[str, object]", current.copy)[name] = plain
        else:
            cast("list[object]", current.copy).append(plain)
    return root.copy


class _OpenContainer:
    """A mapping, list or tuple that `_json_plain_walk` has started to copy."""

    __slots__ = ("copy", "is_object", "items", "source_id")

    def __init__(self, source: object) -> None:
        self.source_id = id(source)
        self.is_object = isinstance(source, Mapping)
        if self.is_object:
            self.copy: dict[str, object] | list[object] = {}
            self.items: Iterator[object] = iter(cast("Mapping[object, object]", source).items())
        else:
            self.copy = []
            self.items = iter(cast("list[object]", source))


# Marks the end of a container's items in the stack walks of this module.
_END_OF_ITEMS = object()


def _secret_key_path(value: object) -> str | None:
    """
    Return where the first ``citry.Secret`` sits inside data bound for the browser, or None when there is none.

    The path is written the way Python reads it back, such as
    ``["config"]["token"]`` or ``["rows"][0]``, and is empty for a Secret at
    the top. It walks the same containers in the same order as
    ``_json_plain``, so after ``_json_plain`` raised for a Secret this finds
    that same Secret. It runs only after that error, so rendering never
    pays for it.
    """
    found = _secret_key_parts(value)
    return None if found is None else "".join(f"[{json.dumps(part, ensure_ascii=False)}]" for part in found)


def _secret_key_parts(value: object) -> list[str | int] | None:
    """Return the keys leading to the first Secret, innermost last, or None."""
    # Each entry is a container being searched: its id, its (key, item)
    # pairs still to read, and the key that led to it from its parent. A
    # stack keeps the number of Python frames the same however deeply the
    # data nests.
    pending: list[tuple[int, Iterator[tuple[str | int, object]], str | int]] = []
    ancestors: set[int] = set()
    key: str | int = ""
    while True:
        if is_const(value):
            value = const_value(value)
        if type(value) is Secret:
            # The root's own entry has no key, and the Secret's key comes last.
            return [entry[2] for entry in pending[1:]] + ([key] if pending else [])
        items: list[tuple[str | int, object]] | None = None
        if isinstance(value, Mapping):
            items = [(str(item_key), item) for item_key, item in value.items()]
        elif isinstance(value, (list, tuple)):
            items = list(enumerate(value))
        # A container that holds itself would loop forever; _json_plain
        # reports the loop itself, so here it only skips the container.
        if items is not None and id(value) not in ancestors:
            ancestors.add(id(value))
            pending.append((id(value), iter(items), key))
        # Move on to the next item of the innermost container that has one.
        while pending:
            entry = next(pending[-1][1], None)
            if entry is not None:
                key, value = entry
                break
            ancestors.remove(pending.pop()[0])
        else:
            return None


def _first_non_string_key(value: Mapping[object, object]) -> str:
    """Describe the key that broke the string-key rule, so the error names it."""
    key = next(key for key in value if not isinstance(key, str))
    return f"{type(key).__name__} key {key!r}"


# JavaScript numbers hold integers exactly only up to 2**53 - 1.
_JS_SAFE_INTEGER = 2**53 - 1


def _vue_attribute_value(value: object) -> object:
    """
    Return the value Vue should set for one Python-resolved HTML attribute.

    Python's HTML output writes every attribute value as ``str(value)`` (or,
    for a value with ``__html__``, the text a browser decodes from that
    markup), escaped, while Vue's object binding turns a
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
        # Python's HTML writes this markup's decoded text, escaped, so the
        # browser's attribute value is that decoded text. Decoding can
        # produce text such as a javascript: URL; Vue then sets the same value
        # the server HTML already gave the browser.
        return decode_attribute_entities(str(html()))
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


def _copy_evaluated_json(value: object, _depth: int = 0) -> object:
    """
    Copy a value the generated simple JSON evaluator wrote into prepared data.

    That evaluator checks every value it reads before it runs and only writes
    exact str, int, bool, None and finite float scalars, plus dicts with str
    keys and lists it creates itself, so the value is already strict JSON and
    has no cycles. Assembly still needs its own copy, because the leaf and the
    render record holding it still reference the original dicts and lists.

    As in `_json_plain`, levels past `_DIRECT_JSON_DEPTH` are copied with a
    stack, so the number of Python frames stays bounded.
    """
    value_type = type(value)
    if value_type is dict:
        if _depth >= _DIRECT_JSON_DEPTH:
            return _copy_evaluated_json_walk(value)
        depth = _depth + 1
        # A scalar is returned as it is without a call, which pays for
        # passing the depth to the containers.
        return {
            key: _copy_evaluated_json(item, depth) if type(item) in _COPIED_CONTAINERS else item
            for key, item in cast("dict[str, object]", value).items()
        }
    if value_type is list:
        if _depth >= _DIRECT_JSON_DEPTH:
            return _copy_evaluated_json_walk(value)
        depth = _depth + 1
        return [
            _copy_evaluated_json(item, depth) if type(item) in _COPIED_CONTAINERS else item
            for item in cast("list[object]", value)
        ]
    return value


# The containers `_copy_evaluated_json` copies; every other value it returns as it is.
_COPIED_CONTAINERS = frozenset({dict, list})


def _copy_evaluated_json_walk(value: object) -> object:
    """Copy an exact dict or list from the simple JSON evaluator with a stack instead of nested calls."""
    root: dict[str, object] | list[object] = {} if type(value) is dict else []
    # Each entry pairs a source container's remaining items with its copy.
    pending: list[tuple[Iterator[object], dict[str, object] | list[object]]] = [(_copy_items(value), root)]
    while pending:
        items, copy = pending[-1]
        entry = next(items, _END_OF_ITEMS)
        if entry is _END_OF_ITEMS:
            pending.pop()
            continue
        if type(copy) is dict:
            key, item = cast("tuple[str, object]", entry)
        else:
            item = entry
        item_type = type(item)
        child: object = item
        if item_type is dict or item_type is list:
            child = {} if item_type is dict else []
            pending.append((_copy_items(item), cast("dict[str, object] | list[object]", child)))
        if type(copy) is dict:
            cast("dict[str, object]", copy)[key] = child
        else:
            cast("list[object]", copy).append(child)
    return root


def _copy_items(value: object) -> Iterator[object]:
    """Return a dict's (key, value) pairs or a list's items, for `_copy_evaluated_json_walk`."""
    if type(value) is dict:
        return iter(cast("dict[str, object]", value).items())
    return iter(cast("list[object]", value))
