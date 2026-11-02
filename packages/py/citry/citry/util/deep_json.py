r"""
Read and write JSON with a stack instead of one Python call per nesting level.

``json.dumps`` and ``json.loads`` count each nested array and object against
a recursion limit: Python's own on 3.11 and PyPy, and a fixed limit of their
own on later CPython versions (about 10,000 levels on 3.13). Data a page
sends the browser can nest hundreds of levels deep, and on 3.11 the frames a
web framework already uses leave room for fewer levels than that. Citry
calls the standard functions first, because they are fast, and only when
one raises ``RecursionError`` does it call ``dumps`` or ``loads``
here, which give the same result with a fixed number of frames.

- ``dumps`` writes, byte for byte, what ``json.dumps`` writes with
  ``allow_nan=False`` and compact separators, and raises the same errors.
- ``loads`` reads JSON text into the same value ``json.loads`` gives, with
  the same ``object_pairs_hook`` and ``parse_constant`` behavior. For text
  that is not valid JSON it raises ``json.JSONDecodeError``, though its
  message can differ from the standard one. On PyPy, where the standard
  library's string reader is its pure-Python one, ``loads`` accepts a ``\u``
  escape whose four characters ``int(text, 16)`` reads, such as a space
  before ``0e9``, ``+0e9`` or ``0_e9``, which PyPy's own decoder refuses,
  and raises ``ValueError`` for one with a sign such as ``-0e9``.
"""

from __future__ import annotations

import json
import json.decoder
import math
import re
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable


def dumps(value: object, *, sort_keys: bool, ensure_ascii: bool) -> str:
    """
    Write what ``json.dumps(value, allow_nan=False, separators=(",", ":"), ...)`` writes, with a stack.

    It follows the standard library's encoder step by step and writes each
    scalar with ``json.dumps`` itself. For the exact JSON types and their
    plain subclasses that Citry passes, it writes the same text and raises
    the same errors as ``json.dumps``. Values that change how they are read,
    such as a dict subclass whose ``items()`` returns lists, can differ, as
    can the notes Python 3.14 adds to an error and, on PyPy, the text for a
    dict subclass and the error for keys that cannot be sorted.
    """
    encode_str = json.encoder.encode_basestring_ascii if ensure_ascii else json.encoder.encode_basestring
    pieces: list[str] = []
    # The ids of the containers being written, so a container that holds
    # itself raises the encoder's own error rather than looping.
    markers: set[int] = set()
    # Each entry is a container being written: its id, whether it is a dict,
    # its items still to write, and whether one has been written yet.
    pending: list[list[Any]] = []
    while True:
        container = _json_container_entry(value, markers, sort_keys=sort_keys)
        if container is None:
            pieces.append(_json_scalar_text(value, encode_str))
        elif container[2] is None:
            # An empty container, which the encoder writes before it checks for a loop.
            pieces.append("{}" if container[1] else "[]")
        else:
            pieces.append("{" if container[1] else "[")
            pending.append(container)
        # Move on to the next item of the innermost container that has one.
        while pending:
            current = pending[-1]
            entry = next(current[2], _END_OF_JSON_ITEMS)
            if entry is _END_OF_JSON_ITEMS:
                pending.pop()
                markers.remove(current[0])
                pieces.append("}" if current[1] else "]")
                continue
            if current[3]:
                pieces.append(",")
            current[3] = True
            if current[1]:
                key, value = cast("tuple[object, object]", entry)
                pieces.append(_json_key_text(key, encode_str))
                pieces.append(":")
            else:
                value = entry
            break
        else:
            return "".join(pieces)


# Marks the end of a container's items in `dumps`.
_END_OF_JSON_ITEMS = object()


def _json_container_entry(value: object, markers: set[int], *, sort_keys: bool) -> list[Any] | None:
    """
    Start writing a list, tuple or dict, or return None for any other value.

    The returned entry holds the container's id, whether it is a dict, an
    iterator over its items (None for an empty container), and whether an
    item has been written yet.
    """
    # The encoder tests str, None, True, False, int and float first, and
    # none of them is a list, tuple or dict, so testing those here first
    # gives the same order.
    is_dict = isinstance(value, dict)
    if not is_dict and not isinstance(value, (list, tuple)):
        return None
    # The encoder reads a list's or tuple's items before it checks for
    # emptiness, and a dict's stored size, which a subclass cannot change.
    items: list[Any] = [] if is_dict else list(cast("list[object]", value))
    if (dict.__len__(cast("dict[object, object]", value)) if is_dict else len(items)) == 0:
        return [id(value), is_dict, None, False]
    if id(value) in markers:
        raise ValueError("Circular reference detected")
    markers.add(id(value))
    if is_dict:
        items = list(cast("dict[object, object]", value).items())
        if sort_keys:
            items.sort()
    return [id(value), is_dict, iter(items), False]


def _json_scalar_text(value: object, encode_str: Callable[[str], str]) -> str:
    """Write one value that is not a container, as the encoder does."""
    if isinstance(value, str):
        return encode_str(value)
    if value is None or value is True or value is False or isinstance(value, (int, float)):
        # The standard encoder writes these, and raises for a float it refuses.
        return json.dumps(value, allow_nan=False)
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def _json_key_text(key: object, encode_str: Callable[[str], str]) -> str:
    """Write one dict key, as the encoder does."""
    if isinstance(key, str):
        return encode_str(key)
    if isinstance(key, float):
        # A float key is written as its JSON number, inside quotes.
        return encode_str(json.dumps(key, allow_nan=False))
    if key is True:
        return '"true"'
    if key is False:
        return '"false"'
    if key is None:
        return '"null"'
    if isinstance(key, int):
        return encode_str(int.__repr__(key))
    raise TypeError(f"keys must be str, int, float, bool or None, not {key.__class__.__name__}")


# The standard library's string reader (its C version when available),
# which ``json.loads`` uses for every string and key. The type stubs do not
# list it.
_scanstring: Callable[[str, int], tuple[str, int]] = json.decoder.scanstring  # type: ignore[attr-defined]

# The JSON whitespace characters, which ``json.loads`` skips between tokens.
_WHITESPACE = " \t\n\r"

# A JSON number, as ``json.scanner.NUMBER_RE`` matches it, with ASCII digits
# only: on Python 3.11 that pattern uses ``\d``, which also matches other
# scripts' digits, while the C decoder ``json.loads`` uses does not.
_NUMBER = re.compile(r"(-?(?:0|[1-9][0-9]*))(\.[0-9]+)?([eE][-+]?[0-9]+)?")

# The values ``json.loads`` gives the three constants it accepts by default.
_CONSTANTS: dict[str, float] = {"NaN": math.nan, "Infinity": math.inf, "-Infinity": -math.inf}


def loads(
    text: str | bytes | bytearray,
    *,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
    parse_constant: Callable[[str], Any] | None = None,
) -> Any:
    """
    Read JSON text as ``json.loads(text, object_pairs_hook=..., parse_constant=...)`` reads it, with a stack.

    Strings are read by the standard library's own string reader, and
    numbers by the rules its C scanner follows, so a valid document gives
    the same value. ``object_pairs_hook`` is called with each object's pairs
    once the object is read, innermost first, as ``json.loads`` calls it.

    Raises:
        json.JSONDecodeError: for text that is not valid JSON. The message
            and position can differ from what ``json.loads`` reports.
        ValueError: for an integer with more digits than Python converts,
            as ``json.loads`` raises.
        UnicodeDecodeError: for bytes that do not decode.
        TypeError: when ``text`` is not a str, bytes or bytearray.

    """
    if isinstance(text, (bytes, bytearray)):
        text = text.decode(json.detect_encoding(text), "surrogatepass")
    if not isinstance(text, str):
        raise TypeError(f"the JSON object must be str, bytes or bytearray, not {text.__class__.__name__}")
    if text.startswith("\ufeff"):
        raise json.JSONDecodeError("Unexpected UTF-8 BOM (decode using utf-8-sig)", text, 0)
    constant = parse_constant if parse_constant is not None else _CONSTANTS.__getitem__
    # Each entry is an array (a list of its items) or an object (a list of
    # its pairs and the key the next value goes under), innermost last.
    open_containers: list[list[Any]] = []
    position = _skip_whitespace(text, 0)
    while True:
        value, position, opened = _read_value(text, position, constant)
        if opened is not None:
            open_containers.append(opened)
            position = _skip_whitespace(text, position)
            # An empty array or object closes at once; anything else starts
            # with its first value or key.
            closer = "]" if opened[0] == "array" else "}"
            if text.startswith(closer, position):
                value, position = _close(open_containers, position + 1, object_pairs_hook)
            elif opened[0] == "object":
                position = _read_key(text, position, opened)
                continue
            else:
                continue
        # Put the finished value into the container around it, closing every
        # container that ends right after it.
        while True:
            if not open_containers:
                position = _skip_whitespace(text, position)
                if position != len(text):
                    raise json.JSONDecodeError("Extra data", text, position)
                return value
            current = open_containers[-1]
            if current[0] == "array":
                current[1].append(value)
            else:
                current[1].append((current[2], value))
            position = _skip_whitespace(text, position)
            if text.startswith(",", position):
                position = _skip_whitespace(text, position + 1)
                if current[0] == "object":
                    position = _read_key(text, position, current)
                break
            if text.startswith("]" if current[0] == "array" else "}", position):
                value, position = _close(open_containers, position + 1, object_pairs_hook)
                continue
            expected = "','" if current[0] == "array" else "',' or '}'"
            raise json.JSONDecodeError(f"Expecting {expected} delimiter", text, position)


def _skip_whitespace(text: str, position: int) -> int:
    while position < len(text) and text[position] in _WHITESPACE:
        position += 1
    return position


def _close(
    open_containers: list[list[Any]],
    position: int,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None,
) -> tuple[Any, int]:
    """Finish the innermost container and return its value."""
    kind, items, _key = open_containers.pop()
    if kind == "array":
        return items, position
    return (object_pairs_hook(items) if object_pairs_hook is not None else dict(items)), position


def _read_key(text: str, position: int, current: list[Any]) -> int:
    """Read an object's key and the ``:`` after it, and remember the key for its value."""
    if not text.startswith('"', position):
        raise json.JSONDecodeError("Expecting property name enclosed in double quotes", text, position)
    key, position = _scanstring(text, position + 1)
    position = _skip_whitespace(text, position)
    if not text.startswith(":", position):
        raise json.JSONDecodeError("Expecting ':' delimiter", text, position)
    current[2] = key
    return _skip_whitespace(text, position + 1)


def _read_value(text: str, position: int, constant: Callable[[str], Any]) -> tuple[Any, int, list[Any] | None]:
    """
    Read the value at ``position``.

    Returns the value and the position after it, or, for ``[`` and ``{``, a
    new open container and the position after the bracket.
    """
    character = text[position : position + 1]
    if character == '"':
        value, end = _scanstring(text, position + 1)
        return value, end, None
    if character == "[":
        return None, position + 1, ["array", [], None]
    if character == "{":
        return None, position + 1, ["object", [], None]
    literals: tuple[tuple[str, object], ...] = (("null", None), ("true", True), ("false", False))
    for literal, literal_value in literals:
        if text.startswith(literal, position):
            return literal_value, position + len(literal), None
    for name in ("NaN", "Infinity", "-Infinity"):
        if text.startswith(name, position):
            return constant(name), position + len(name), None
    match = _NUMBER.match(text, position)
    if match is None:
        raise json.JSONDecodeError("Expecting value", text, position)
    integer, fraction, exponent = match.groups()
    if fraction or exponent:
        return float(integer + (fraction or "") + (exponent or "")), match.end(), None
    return int(integer), match.end(), None
