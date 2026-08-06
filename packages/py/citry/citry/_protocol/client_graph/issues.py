"""Shared validation errors and strict-JSON utilities for the client graph."""

from __future__ import annotations

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
    return (selected_key is not None, selected)


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


def validate_strict_json(value: Any, path: str = "") -> ValidationIssue | None:
    """Validate one in-memory JSON value without recursion or mutation."""
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
            if is_finite_json_number(current):
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
    return None


def copy_json(value: Any) -> Any:
    """Validate and copy a JSON value without recursion."""
    issue = validate_strict_json(value)
    if issue is not None:
        raise ProtocolValueError(issue)
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


__all__ = [
    "ProtocolValueError",
    "ValidationIssue",
    "copy_json",
    "first_unknown",
    "is_finite_json_number",
    "pointer",
    "utf16_key",
    "validate_strict_json",
]
