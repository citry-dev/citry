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


# Vue reads a name starting with one of these as a directive or binding:
# `v-if`, `v-bind:x`, `:x`, `.x` (sets a DOM property), `^x` (forces an
# attribute), `@x` (listener) and `#x` (slot).
_VUE_DIRECTIVE_PREFIXES = ("v-", ":", ".", "^", "@", "#")


def is_vue_directive_attribute(name: str) -> bool:
    """Return whether an attribute name uses Vue directive syntax."""
    # HTML attribute names are case-insensitive, so `V-IF` must not slip past
    # a check that only knows the lowercase spelling.
    return name.casefold().startswith(_VUE_DIRECTIVE_PREFIXES)


def reject_vue_directive_attrs(
    attrs: Mapping[str, object] | None,
    component_name: str,
) -> None:
    """
    Reject Vue directive syntax in a Python-owned attribute mapping.

    A component's `attrs` input is data. A Vue directive written there could
    replace the component's own bindings, structure, or listeners, so the
    component rejects it here with its own name in the message. Authored Vue
    attributes in a template go through the Vue compiler and are not affected.
    """
    for key in attrs or {}:
        if isinstance(key, str) and is_vue_directive_attribute(key):
            msg = (
                f"{component_name} attrs cannot contain the Vue directive {key!r}; "
                "author Vue bindings and listeners in a template instead."
            )
            raise ValueError(msg)


# Citry UI's browser code finds its elements by `data-citry-*` names, such as
# `data-citry-dialog-close`, some of which it builds at run time from a part or
# action name. Core Citry's browser code and render cache read `data-cev*` and
# `data-cid*` names. The whole `data-citry-` prefix is reserved, rather than a
# list of today's names, so a name a later release starts reading is already
# covered.
_RESERVED_ATTR_PREFIXES = ("data-citry-", "data-cev", "data-cid")
# Only these names can carry a value Citry UI wrote; see `CitryUiOwnedValue`.
_OWNED_VALUE_PREFIX = "data-citry-"
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


class CitryUiOwnedValue(str):
    """
    The value of a `data-citry-*` attribute that Citry UI itself wrote into slot data.

    A Citry UI component hands some of its own marker attributes to the caller,
    such as `activator_attrs` with `data-citry-dialog-trigger`, so the caller
    can spread them onto a `<c-CButton>`. The receiving component's check
    accepts a reserved name only when its value is one of these. Data read from
    a request or from storage is a plain `str`, so it cannot make one.
    """

    __slots__ = ()


def citry_ui_owned_value(value: str = "") -> CitryUiOwnedValue:
    """Return `value` marked as written by Citry UI, for a `data-citry-*` name a component hands out."""
    return CitryUiOwnedValue(value)


def reject_citry_ui_reserved_attr(
    name: object,
    value: object,
    *,
    where: str,
    extra_prefixes: tuple[str, ...] = (),
) -> None:
    """
    Raise `ValueError` when an attribute map from Python sets a name Citry UI's browser code reads.

    Every Citry UI `attrs=` and `*_attrs=` input calls this for each name. The
    reserved names are every `data-citry-*` name, and the `data-cev*` and
    `data-cid*` names core Citry reads. A component may pass `extra_prefixes`
    for names only it reads.

    Args:
        name: The attribute name to check. A non-string name is left to the caller's own type check.
        value: The value set for it. A `data-citry-*` name passes only with a `CitryUiOwnedValue`, or with
            `None` or `False`, which write no attribute.
        where: The component and input, such as `"CButton attrs"`, for the message.
        extra_prefixes: More reserved prefixes, in lowercase.

    Raises:
        ValueError: When `name` starts with a reserved prefix, in any ASCII letter case.

    """
    if not isinstance(name, str):
        return
    # Browsers compare attribute names after lowercasing ASCII letters only,
    # so `DATA-CITRY-X` is the same attribute and a non-ASCII lookalike is not.
    folded = name.translate(_ASCII_LOWER)
    if not folded.startswith(_RESERVED_ATTR_PREFIXES + extra_prefixes):
        return
    # A `None` or `False` value renders no attribute at all, so it is harmless.
    if value is None or value is False:
        return
    # The one way through: a value a Citry UI component wrote into slot data.
    if folded.startswith(_OWNED_VALUE_PREFIX) and isinstance(value, CitryUiOwnedValue):
        return
    prefixes = ", ".join(repr(prefix) for prefix in _RESERVED_ATTR_PREFIXES + extra_prefixes)
    msg = (
        f"{where} cannot set {name!r}. Attribute names that start with {prefixes} are reserved for the browser "
        "code of Citry and Citry UI, which would act on the element as if Citry had written it. Pass the attrs a "
        "Citry UI slot hands you (such as activator_attrs) as they are, or choose another name."
    )
    raise ValueError(msg)


def reject_citry_ui_reserved_attrs(
    attrs: Mapping[object, object] | None,
    where: str,
    *,
    extra_prefixes: tuple[str, ...] = (),
) -> None:
    """Run `reject_citry_ui_reserved_attr` on every name in an attribute map."""
    for name, value in (attrs or {}).items():
        reject_citry_ui_reserved_attr(name, value, where=where, extra_prefixes=extra_prefixes)


def html_attr_binding_target(name: str) -> str | None:
    """Return the attribute a `:name`, `.name`, or `v-bind:name` binding sets, or None for any other name."""
    normalized = name.casefold()
    if normalized.startswith("v-bind:"):
        target = normalized.split(":", 1)[1].split(".", 1)[0]
    elif normalized.startswith((":", ".")):
        target = normalized[1:].split(".", 1)[0]
    else:
        return None
    # A dynamic argument such as `:[name]` picks its attribute in the browser,
    # so no fixed target can be checked; callers treat it as unknown.
    return None if target.startswith("[") else target


def is_executable_event_attribute(name: str) -> bool:
    """
    Return whether a resolved attribute would install browser code.

    Python-owned attribute mappings are data. They must never smuggle a
    framework event directive or an inline DOM event handler into the Vue
    template assembled from that data. Authored Vue attributes still go
    through the template compiler and are intentionally outside this check.
    """
    normalized = name.casefold()
    return normalized.startswith(("on", "@", "v-on"))


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
    "CitryUiOwnedValue",
    "citry_ui_owned_value",
    "get_html_attr",
    "get_html_form_owner",
    "html_attr_binding_target",
    "is_executable_event_attribute",
    "is_vue_directive_attribute",
    "merge_root_attrs",
    "pop_html_attr",
    "reject_citry_ui_reserved_attr",
    "reject_citry_ui_reserved_attrs",
    "reject_vue_directive_attrs",
]
