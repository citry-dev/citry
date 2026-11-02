"""Canonical date helpers shared by Citry UI date families."""

from __future__ import annotations

import re
from datetime import date
from typing import Literal, cast

from citry import const_value

_CANONICAL_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def canonical_date(
    component_name: str,
    input_name: str,
    value: object,
    *,
    optional: bool = False,
) -> str | None:
    """Normalize one exact Python date or canonical HTML date string."""
    value = const_value(value)
    if value is None:
        if optional:
            return None
        raise TypeError(f"{component_name} {input_name} cannot be None.")
    if type(value) is date:
        return cast("date", value).isoformat()
    if type(value) is not str:
        suffix = " or None" if optional else ""
        raise TypeError(
            f"{component_name} {input_name} must be an exact date, canonical YYYY-MM-DD string{suffix}, got {value!r}."
        )
    raw = cast("str", value)
    if not _CANONICAL_DATE.fullmatch(raw):
        raise ValueError(f"{component_name} {input_name} must use canonical YYYY-MM-DD syntax, got {raw!r}.")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as error:
        raise ValueError(f"{component_name} {input_name} must name a real calendar date, got {raw!r}.") from error
    if parsed.isoformat() != raw:
        raise ValueError(f"{component_name} {input_name} must use canonical YYYY-MM-DD syntax, got {raw!r}.")
    return raw


# A template writes `first_day_of_week="1"`, which passes text, and Python code
# or `c-first_day_of_week="1"` passes the number, so both forms name a weekday.
# 1 is Monday and 7 is Sunday, as in ISO 8601.
CFirstDayOfWeek = Literal[1, 2, 3, 4, 5, 6, 7, "1", "2", "3", "4", "5", "6", "7"]

_FIRST_DAYS: dict[int | str, int] = {
    **{day: day for day in range(1, 8)},
    **{str(day): day for day in range(1, 8)},
}


def first_day_of_week(component_name: str, value: object) -> int | None:
    """Return the week's first day as an int, or None to follow the locale."""
    value = const_value(value)
    if value is None:
        return None
    # bool is an int subclass, but `True` (a bare attribute) is not a weekday.
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        msg = (
            f"{component_name} first_day_of_week must be a number from 1 through 7, "
            f'the same number as text such as "1", or None; got {value!r}.'
        )
        raise TypeError(msg)
    day = _FIRST_DAYS.get(value)
    if day is None:
        msg = f"{component_name} first_day_of_week must be from 1 through 7, where 1 is Monday; got {value!r}."
        raise ValueError(msg)
    return day


__all__ = ["CFirstDayOfWeek", "canonical_date", "first_day_of_week"]
