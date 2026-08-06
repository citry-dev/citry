"""Private ARIA relationship helpers shared by form controls."""

from __future__ import annotations


def idrefs(value: object) -> list[str]:
    if value is None or value is False:
        return []
    if not isinstance(value, str):
        msg = f"ARIA relationship attributes must be strings, got {value!r}."
        raise TypeError(msg)
    return value.split()


def merge_idrefs(*values: object) -> str | None:
    merged = dict.fromkeys(token for value in values for token in idrefs(value))
    return " ".join(merged) or None


__all__ = ["idrefs", "merge_idrefs"]
