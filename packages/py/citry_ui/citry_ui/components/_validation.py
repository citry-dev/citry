from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping


def validate_choice(
    component_name: str,
    field_name: str,
    value: object,
    allowed: Collection[object],
) -> None:
    if value not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{component_name} {field_name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)


def validate_boolean(component_name: str, field_name: str, value: object) -> None:
    # Template constants use Citry's bool-compatible ConstProxy. isinstance()
    # accepts that wrapper while still rejecting Python integers and other
    # truthy values.
    if not isinstance(value, bool):
        msg = f"{component_name} {field_name} must be a bool, got {value!r}."
        raise TypeError(msg)


def validate_optional_boolean(component_name: str, field_name: str, value: object) -> None:
    if value is not None:
        validate_boolean(component_name, field_name, value)


def validate_non_empty_string(component_name: str, field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        msg = f"{component_name} {field_name} must be a non-empty string, got {value!r}."
        raise ValueError(msg)


def validate_optional_string(component_name: str, field_name: str, value: object) -> None:
    if value is not None and not isinstance(value, str):
        msg = f"{component_name} {field_name} must be a string or None, got {value!r}."
        raise TypeError(msg)


def reject_owned_attrs(
    attrs: Mapping[str, object] | None,
    owned: Collection[str],
    component_name: str,
) -> None:
    owned_lower = {name.lower() for name in owned}
    for key in attrs or {}:
        if not isinstance(key, str):
            msg = f"{component_name} attrs require string keys, got {key!r}."
            raise TypeError(msg)
        if key.lower() in owned_lower:
            msg = f"{component_name} attrs cannot override owned attribute {key!r}."
            raise ValueError(msg)


def validate_html_id(component_name: str, value: str | None) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        msg = f"{component_name} id must be a string or None, got {value!r}."
        raise TypeError(msg)
    if not value or any(character in "\t\n\f\r " for character in value):
        msg = f"{component_name} id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)


def first_attribute_occurrences(attrs: list[tuple[str, str | None]]) -> list[tuple[str, str | None]]:
    """
    Return the attributes a browser keeps from one start tag that ``HTMLParser`` read.

    A browser keeps the first of two attributes with the same name and
    ignores the rest, so ``<div popover="auto" popover="manual">`` has
    ``popover="auto"``, while ``dict(attrs)`` would keep the last value. The
    checks of rendered output read this list, so they decide on the
    attributes the page really has. ``HTMLParser`` already lowercases names.
    """
    # Citry 0.9.0 and later already hand the start tag handlers this list,
    # but Citry UI also runs on older releases, whose parser keeps every
    # occurrence.
    seen: set[str] = set()
    kept: list[tuple[str, str | None]] = []
    for name, value in attrs:
        if name not in seen:
            seen.add(name)
            kept.append((name, value))
    return kept


def visible_markup_text(text: str) -> str:
    r"""
    Return ``text`` with every unprintable character written as a visible escape such as ``\x1b``.

    Error messages quote tag names from the rendered HTML, and a tag name can
    hold a control character. Written as it is, ESC would reach the
    developer's terminal, where it can start an escape sequence, such as
    one that changes the window title.
    """
    return "".join(char if char.isprintable() else char.encode("unicode_escape").decode("ascii") for char in text)
