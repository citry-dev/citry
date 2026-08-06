"""Shared validation errors and strict-JSON utilities for citry-events/1."""

from __future__ import annotations

import json
import math
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


def _strict_json_issue(value: Any, path: str) -> ValidationIssue:
    """Locate the first strict-JSON problem after the fast path rejects."""
    stack: list[tuple[Any, str, bool]] = [(value, path, False)]
    ancestors: set[int] = set()

    while stack:
        current, current_path, leaving = stack.pop()
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
            return ValidationIssue(current_path, "strict_json", "The integer is outside the browser JSON range.")
        if isinstance(current, float):
            if math.isfinite(current):
                continue
            return ValidationIssue(current_path, "strict_json", "The value contains a non-finite number.")
        if not isinstance(current, (dict, list)):
            return ValidationIssue(current_path, "strict_json", "The value contains a non-JSON value.")

        identity = id(current)
        if identity in ancestors:
            return ValidationIssue(current_path, "strict_json", "The value contains a cycle.")
        ancestors.add(identity)
        stack.append((current, current_path, True))
        if isinstance(current, list):
            for index in range(len(current) - 1, -1, -1):
                stack.append((current[index], pointer(current_path, index), False))
            continue
        for key in current:
            if not isinstance(key, str):
                return ValidationIssue(current_path, "strict_json", "A JSON object has a non-string key.")
        for key in sorted(current, key=utf16_key, reverse=True):
            stack.append((current[key], pointer(current_path, key), False))
    raise AssertionError("strict JSON diagnostic ran for a valid value")


def loads_strict_json(data: str | bytes | bytearray) -> Any:
    """Parse standard JSON and reject non-finite decoded numbers."""

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

    return json.loads(data, parse_constant=reject_constant, parse_float=finite_float, parse_int=finite_int)


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
