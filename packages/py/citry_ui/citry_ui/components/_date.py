"""Canonical date helpers shared by Citry UI date families."""

from __future__ import annotations

import re
from datetime import date
from typing import cast

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


__all__ = ["canonical_date"]
