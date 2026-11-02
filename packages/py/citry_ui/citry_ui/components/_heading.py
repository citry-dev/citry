"""The heading level shared by components that render their own heading element."""

from __future__ import annotations

from typing import Literal

from citry import const_value

# A template writes `heading_level="2"`, which passes text, and Python code or
# `c-heading_level="2"` passes the number, so both forms name a valid level.
CHeadingLevel = Literal[2, 3, 4, 5, 6, "2", "3", "4", "5", "6"]

# Only the exact values `CHeadingLevel` names map to a level, so text such as
# "02" and numbers such as 2.0 fail here as they fail the type check.
_LEVELS: dict[int | str, int] = {
    **{level: level for level in range(2, 7)},
    **{str(level): level for level in range(2, 7)},
}


def resolve_heading_level(component_name: str, value: object) -> int:
    """Return the heading level as an int, from either form `CHeadingLevel` allows."""
    raw = const_value(value)
    level = None
    # bool is an int subclass, but `True` is not a heading level.
    if isinstance(raw, (int, str)) and not isinstance(raw, bool):
        level = _LEVELS.get(raw)
    if level is None:
        msg = f"{component_name} heading_level must be one of 2, 3, 4, 5, or 6, as a number or as text; got {raw!r}."
        raise ValueError(msg)
    return level
