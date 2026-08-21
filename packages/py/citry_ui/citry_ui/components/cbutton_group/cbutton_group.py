"""Accessible layout for related Button actions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CButtonGroupOrientation = Literal["horizontal", "vertical"]

_ORIENTATIONS = ("horizontal", "vertical")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_OWNED_ATTRS = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-hidden",
        "aria-orientation",
        "aria-roledescription",
        "contenteditable",
        "data-attached",
        "data-citry-ui-part",
        "data-grow",
        "data-orientation",
        "disabled",
        "form",
        "role",
        "tabindex",
    }
)


class CButtonGroupDefaultSlotData:
    pass


def _plain_label(value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CButtonGroup label must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = "CButtonGroup could not convert label to a plain string."
        raise TypeError(msg)
    if not plain.strip() or "\x00" in plain:
        msg = "CButtonGroup label must be nonempty and cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_orientation(value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CButtonGroup orientation must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if plain not in _ORIENTATIONS:
        msg = f"CButtonGroup orientation must be 'horizontal' or 'vertical', got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CButtonGroup attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CButtonGroup attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CButtonGroup attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CButtonGroup attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if _dynamic_target(normalized) in _OWNED_ATTRS:
            msg = f"CButtonGroup attrs cannot dynamically bind owned attribute {key!r}."
            raise ValueError(msg)
    return copied


class CButtonGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        label: str
        orientation: CButtonGroupOrientation = "horizontal"
        attached: bool = True
        grow: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CButtonGroupDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        label = _plain_label(kwargs.label)
        orientation = _plain_orientation(kwargs.orientation)
        validate_boolean("CButtonGroup", "attached", kwargs.attached)
        validate_boolean("CButtonGroup", "grow", kwargs.grow)
        if "default" not in self.raw_slots:
            msg = "CButtonGroup requires a default slot with related actions."
            raise ValueError(msg)
        return {
            "label": label,
            "orientation": orientation,
            "attached": bool(kwargs.attached),
            "grow": bool(kwargs.grow),
            "attrs": merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style),
        }

    template = """
      <div
        class="cui-button-group"
        c-bind="attrs"
        data-citry-ui-part="button-group"
        c-data-orientation="orientation"
        c-data-attached="attached"
        c-data-grow="grow"
        role="group"
        c-aria-label="label"
      >
        <c-slot />
      </div>
    """

    css_file = "runtime.min.css"
