"""Shared root-attribute inputs for styled Citry UI components."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias, Union

from citry import merge_attrs

CClassValue: TypeAlias = Union[  # noqa: UP007 - recursive on Python 3.10
    str,
    Mapping[str, bool],
    Sequence["CClassValue"],
]
CStyleDict: TypeAlias = Mapping[
    str,
    Union[str, int, float, bool, None],  # noqa: UP007
]
CStyleValue: TypeAlias = Union[  # noqa: UP007 - recursive on Python 3.10
    str,
    CStyleDict,
    Sequence["CStyleValue"],
]


def _matching_html_attr_keys(attrs: Mapping[str, object], name: str) -> list[str]:
    normalized_name = name.casefold()
    return [key for key in attrs if isinstance(key, str) and key.casefold() == normalized_name]


def get_html_attr(
    attrs: Mapping[str, object],
    name: str,
    *,
    component_name: str,
    default: object = None,
) -> object:
    """Read one case-insensitive HTML attribute and reject duplicate spellings."""
    matches = _matching_html_attr_keys(attrs, name)
    if len(matches) > 1:
        msg = f"{component_name} attrs cannot contain duplicate case variants of {name!r}."
        raise ValueError(msg)
    return attrs[matches[0]] if matches else default


def get_html_form_owner(
    attrs: Mapping[str, object],
    *,
    component_name: str,
    default: object = None,
) -> object:
    """Resolve HTML Form ownership with Citry's omitted-value semantics."""
    value = get_html_attr(
        attrs,
        "form",
        component_name=component_name,
        default=default,
    )
    return default if value is None or value is False else value


def pop_html_attr(
    attrs: dict[str, object],
    name: str,
    *,
    component_name: str,
    default: object = None,
) -> object:
    """Remove one case-insensitive HTML attribute and reject duplicate spellings."""
    matches = _matching_html_attr_keys(attrs, name)
    if len(matches) > 1:
        msg = f"{component_name} attrs cannot contain duplicate case variants of {name!r}."
        raise ValueError(msg)
    return attrs.pop(matches[0]) if matches else default


def reject_html_attr_bindings(
    attrs: Mapping[str, object] | None,
    names: set[str] | frozenset[str],
    component_name: str,
) -> None:
    """Reject Alpine shorthand or longhand bindings to selected HTML attributes."""
    normalized_names = {name.casefold() for name in names}
    for key in attrs or {}:
        if not isinstance(key, str):
            continue
        normalized = key.casefold()
        target = None
        if normalized.startswith("x-bind:"):
            target = normalized.removeprefix("x-bind:").split(".", 1)[0]
        elif normalized.startswith((":", ".")):
            target = normalized[1:].split(".", 1)[0]
        if target in normalized_names:
            msg = f"{component_name} attrs cannot dynamically bind HTML attribute {target!r}."
            raise ValueError(msg)


def merge_root_attrs(
    attrs: Mapping[str, object] | None,
    class_: CClassValue | None,
    style: CStyleValue | None,
) -> dict[str, object]:
    """Merge convenient root class/style inputs with the general attribute map."""
    return merge_attrs(
        attrs or {},
        {
            "class": class_,
            "style": style,
        },
    )


__all__ = [
    "CClassValue",
    "CStyleValue",
    "get_html_attr",
    "get_html_form_owner",
    "merge_root_attrs",
    "pop_html_attr",
    "reject_html_attr_bindings",
]
