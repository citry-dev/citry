"""Shared validation errors and strict-JSON utilities for citry-events/1."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """The first protocol problem found in one value."""

    path: str
    category: str
    message: str

    def as_dict(self) -> dict[str, str]:
        """Return the language-neutral issue record."""
        return {"path": self.path, "category": self.category, "message": self.message}


class ProtocolValueError(ValueError):
    """Raised when a protocol builder receives invalid input."""

    def __init__(self, issue: ValidationIssue) -> None:
        super().__init__(issue.message)
        self.issue = issue


def pointer(parent: str, member: str | int) -> str:
    """Append one RFC 6901 member to a JSON Pointer."""
    escaped = str(member).replace("~", "~0").replace("/", "~1")
    return f"{parent}/{escaped}" if parent else f"/{escaped}"


def utf16_key(value: str) -> bytes:
    """Return the byte key that reproduces JavaScript string ordering."""
    return value.encode("utf-16-be", errors="surrogatepass")


def first_unknown(value: Mapping[Any, Any], allowed: set[str]) -> tuple[bool, Any]:
    """Return the first unknown member in deterministic JavaScript order."""
    selected: Any = None
    selected_key: tuple[int, bytes] | None = None
    for key in value:
        if isinstance(key, str) and key in allowed:
            continue
        candidate_key = (0, utf16_key(key)) if isinstance(key, str) else (1, repr(key).encode())
        if selected_key is None or candidate_key < selected_key:
            selected = key
            selected_key = candidate_key
    if selected_key is None:
        return False, None
    return True, selected


def validate_strict_json(value: Any, path: str = "") -> ValidationIssue | None:
    """Validate one in-memory JSON value without recursion or mutation."""
    if _is_strict_json(value):
        return None
    return _strict_json_issue(value, path)


def is_finite_json_number(value: Any) -> bool:
    """Whether a Python number stays finite when a browser parses it."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int) and value.bit_length() <= 1023:
        return True
    try:
        return math.isfinite(float(value))
    except OverflowError:
        return False


def _is_strict_json(value: Any) -> bool:
    """Fast valid-input path with an iterative fallback for deep values."""
    try:
        return _is_strict_json_shallow(value, set())
    except RecursionError:
        return _is_strict_json_iterative(value)


def _is_strict_json_shallow(value: Any, ancestors: set[int]) -> bool:
    """Check an ordinary shallow JSON tree with minimal allocations."""
    if value is None or isinstance(value, (str, bool)):
        return True
    if isinstance(value, int):
        return is_finite_json_number(value)
    if isinstance(value, float):
        return math.isfinite(value)
    if not isinstance(value, (dict, list)):
        return False
    identity = id(value)
    if identity in ancestors:
        return False
    ancestors.add(identity)
    try:
        if isinstance(value, list):
            for item in value:  # noqa: SIM110 - avoid generator overhead on this hot path
                if not _is_strict_json_shallow(item, ancestors):
                    return False
            return True
        for key, item in value.items():
            if not isinstance(key, str) or not _is_strict_json_shallow(item, ancestors):
                return False
        return True
    finally:
        ancestors.remove(identity)


def _is_strict_json_iterative(value: Any) -> bool:
    """Check a value without relying on the Python recursion limit."""
    stack: list[tuple[Any, bool]] = [(value, False)]
    ancestors: set[int] = set()
    while stack:
        current, leaving = stack.pop()
        if leaving:
            ancestors.remove(id(current))
            continue
        if current is None or isinstance(current, (str, bool)):
            continue
        if isinstance(current, int):
            if not is_finite_json_number(current):
                return False
            continue
        if isinstance(current, float):
            if math.isfinite(current):
                continue
            return False
        if not isinstance(current, (dict, list)):
            return False
        identity = id(current)
        if identity in ancestors:
            return False
        ancestors.add(identity)
        stack.append((current, True))
        if isinstance(current, list):
            stack.extend((item, False) for item in reversed(current))
        else:
            if any(not isinstance(key, str) for key in current):
                return False
            stack.extend((item, False) for item in reversed(current.values()))
    return True


def _pointer_at(path: str, place: tuple[Any, str | int] | None) -> str:
    """
    Return the JSON Pointer of ``place`` below ``path``.

    A place is ``None`` for ``path`` itself. Below it, a place is a pair of
    its parent's place and one more member, which is a key or a list index.
    """
    members: list[str | int] = []
    while place is not None:
        members.append(place[1])
        place = place[0]
    for member in reversed(members):
        path = pointer(path, member)
    return path


def _strict_json_issue(value: Any, path: str) -> ValidationIssue:
    """
    Locate the first strict-JSON problem after the fast path rejects.

    Each entry on the stack holds a pair of its parent's place and its own
    member, and the pointer text is written only for the problem found. A
    long key over many items would otherwise be copied once per item.
    """
    stack: list[tuple[Any, tuple[Any, str | int] | None, bool]] = [(value, None, False)]
    ancestors: set[int] = set()

    while stack:
        current, place, leaving = stack.pop()
        if leaving:
            ancestors.remove(id(current))
            continue
        if current is None or isinstance(current, (str, bool)):
            continue
        if isinstance(current, int):
            try:
                finite = math.isfinite(float(current))
            except OverflowError:
                finite = False
            if finite:
                continue
            return ValidationIssue(
                _pointer_at(path, place), "strict_json", "The integer is outside the browser JSON range."
            )
        if isinstance(current, float):
            if math.isfinite(current):
                continue
            return ValidationIssue(_pointer_at(path, place), "strict_json", "The value contains a non-finite number.")
        if not isinstance(current, (dict, list)):
            return ValidationIssue(_pointer_at(path, place), "strict_json", "The value contains a non-JSON value.")

        identity = id(current)
        if identity in ancestors:
            return ValidationIssue(_pointer_at(path, place), "strict_json", "The value contains a cycle.")
        ancestors.add(identity)
        stack.append((current, place, True))
        if isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append((current[index], (place, index), False))
            continue
        for key in current:
            if not isinstance(key, str):
                return ValidationIssue(_pointer_at(path, place), "strict_json", "A JSON object has a non-string key.")
        for key in sorted(current, key=utf16_key, reverse=True):
            stack.append((current[key], (place, key), False))
    raise AssertionError("strict JSON diagnostic ran for a valid value")


# The deepest nesting of arrays and objects a received JSON text may have.
# Python's own parser and writer stop at a depth that depends on the Python
# version and on how many frames the web framework already uses. A fixed
# bound well below that makes every host answer the same body the same way. Pydantic's JSON reader
# stops just above this depth, so a State value that passes here also
# restores in a Pydantic State.
MAX_JSON_DEPTH = 200


class JsonNestingError(ValueError):
    """Raised when received JSON nests arrays and objects deeper than ``MAX_JSON_DEPTH``."""

    def __init__(self) -> None:
        super().__init__(f"JSON nests arrays and objects more than {MAX_JSON_DEPTH} levels deep.")


def loads_strict_json(data: str | bytes | bytearray) -> Any:
    """
    Parse standard JSON and reject non-finite decoded numbers.

    Raises:
        JsonNestingError: The text nests arrays and objects more than
            ``MAX_JSON_DEPTH`` levels deep.
        ValueError: The text is not valid JSON, or holds a number that is
            not finite.

    """

    def reject_constant(literal: str) -> Any:
        raise ValueError(f"non-standard JSON literal {literal}")

    def finite_float(raw: str) -> float:
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError(f"JSON number out of range for a float: {raw}")
        return value

    def finite_int(raw: str) -> int:
        value = int(raw)
        if not is_finite_json_number(value):
            raise ValueError(f"JSON integer out of browser range: {raw}")
        return value

    # The depth is checked on the text, before Python's parser runs: in a
    # thread with a small stack, CPython 3.12 and 3.13 can crash the whole
    # process on deep text instead of raising RecursionError.
    check_json_depth(data)
    try:
        value = json.loads(data, parse_constant=reject_constant, parse_float=finite_float, parse_int=finite_int)
    except RecursionError as err:
        # Python's parser counts nesting against a recursion limit, so text
        # this deep stops it before the depth check below can run.
        raise JsonNestingError from err
    # Every level opens with a bracket or a brace, so text with at most
    # MAX_JSON_DEPTH of them cannot be deeper, and most requests skip the walk.
    if isinstance(data, str):
        openers = data.count("[") + data.count("{")
    else:
        openers = data.count(b"[") + data.count(b"{")
    if openers > MAX_JSON_DEPTH and _exceeds_depth(value, MAX_JSON_DEPTH):
        raise JsonNestingError
    return value


def _exceeds_depth(value: Any, limit: int) -> bool:
    """Whether a parsed JSON value nests arrays and objects more than ``limit`` levels, walked with a stack."""
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if isinstance(current, dict):
            children: Any = current.values()
        elif isinstance(current, list):
            children = current
        else:
            continue
        if depth > limit:
            return True
        stack.extend((child, depth + 1) for child in children if isinstance(child, (dict, list)))
    return False


def copy_json(value: Any) -> Any:
    """Validate and copy application-owned JSON without recursion."""
    issue = validate_strict_json(value)
    if issue is not None:
        raise ProtocolValueError(issue)
    return _copy_json_unchecked(value)


def _copy_json_unchecked(value: Any) -> Any:
    """Copy a value already proved to contain only JSON containers."""
    if not isinstance(value, (dict, list)):
        return value
    copied: Any = {} if isinstance(value, dict) else [None] * len(value)
    stack: list[tuple[Any, Any]] = [(value, copied)]
    while stack:
        source, target = stack.pop()
        items = source.items() if isinstance(source, dict) else enumerate(source)
        for key, item in items:
            if isinstance(item, dict):
                child: dict[str, Any] | list[Any] = {}
                target[key] = child
                stack.append((item, child))
            elif isinstance(item, list):
                child = [None] * len(item)
                target[key] = child
                stack.append((item, child))
            else:
                target[key] = item
    return copied


# A JSON string, with its escapes. Brackets inside one are text, not nesting,
# so they are removed before counting. A string with no closing quote runs to
# the end of the text, so every match from a quote succeeds and each
# character is read once.
_JSON_STRING = re.compile(r'"(?:[^"\\]|\\.)*"?', re.DOTALL)
_JSON_BRACKET = re.compile(r"[\[\]{}]")


def check_json_depth(data: str | bytes | bytearray, limit: int = MAX_JSON_DEPTH) -> None:
    """
    Refuse JSON text that nests arrays and objects more than ``limit`` levels, before parsing it.

    The check reads the text with two regular expressions and a counter, so it
    uses no recursion and needs no more stack for deeper text. It counts only
    brackets and braces outside strings. Bytes are first decoded the way
    ``json.loads`` decodes them (UTF-8, UTF-16 or UTF-32), so the check sees
    the same characters as the parser. Text that is not valid JSON may pass
    or fail here; the parser that runs next reports it either way.

    Raises:
        JsonNestingError: The text nests more than ``limit`` levels deep.
        UnicodeDecodeError: The bytes are not text in the encoding
            ``json.loads`` would read them in.

    """
    if isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
        text = raw.decode(json.detect_encoding(raw), "surrogatepass")
    elif isinstance(data, str):
        text = data
    else:
        # Not JSON text at all; the parser that runs next refuses it.
        return
    # Text with no more opening brackets than the limit cannot be deeper, so
    # most requests skip the scan below.
    if text.count("[") + text.count("{") <= limit:
        return
    depth = 0
    for match in _JSON_BRACKET.finditer(_JSON_STRING.sub("", text)):
        if match.group() in "[{":
            depth += 1
            if depth > limit:
                raise JsonNestingError
        else:
            depth -= 1
