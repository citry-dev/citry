"""Strict canonical wall-clock helpers shared by time controls."""

from __future__ import annotations

import re
from datetime import time
from typing import cast

from citry import const_value

_CANONICAL_TIME = re.compile(r"^(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2})(?::(?P<second>[0-9]{2}))?$")


def canonical_time(
    owner: str,
    name: str,
    value: object,
    *,
    optional: bool,
) -> str | None:
    """Return an exact HTML time string or raise a component-facing error."""
    value = const_value(value)
    if value is None:
        if optional:
            return None
        raise TypeError(f"{owner} {name} must be a time or canonical time string, got None.")
    if type(value) is time:
        value = cast("time", value)
        if value.tzinfo is not None:
            raise ValueError(f"{owner} {name} must be a zone-free wall-clock time, got {value!r}.")
        if value.microsecond:
            raise ValueError(f"{owner} {name} does not support fractional seconds, got {value!r}.")
        return value.strftime("%H:%M:%S" if value.second else "%H:%M")
    if type(value) is not str:
        raise TypeError(f"{owner} {name} must be a time or canonical time string, got {value!r}.")
    value = cast("str", value)
    match = _CANONICAL_TIME.fullmatch(value)
    if match is None:
        raise ValueError(f"{owner} {name} must use canonical HH:MM or HH:MM:SS notation, got {value!r}.")
    hour = int(match.group("hour"))
    minute = int(match.group("minute"))
    second = int(match.group("second") or 0)
    if hour > 23 or minute > 59 or second > 59:
        raise ValueError(f"{owner} {name} must be a real wall-clock time, got {value!r}.")
    return value


def time_seconds(value: str) -> int:
    """Convert a checked canonical time to seconds after midnight."""
    parts = [int(part) for part in value.split(":")]
    return parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) == 3 else 0)


__all__ = ["canonical_time", "time_seconds"]
