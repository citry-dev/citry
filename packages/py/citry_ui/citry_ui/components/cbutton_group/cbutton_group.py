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

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="button-group"]) {
          --_cui-button-group-gap: var(--cui-button-group-gap, 0.5rem);
          --_cui-button-group-radius: var(--cui-button-group-radius, 0.55rem);
          --_cui-button-group-border-width: var(--cui-button-group-border-width, 1px);
          display: inline-flex;
          flex-direction: row;
          align-items: stretch;
          gap: var(--_cui-button-group-gap);
          min-inline-size: 0;
          max-inline-size: 100%;
          vertical-align: middle;
        }

        :where([data-citry-ui-part="button-group"][data-orientation="vertical"]) {
          flex-direction: column;
        }

        :where([data-citry-ui-part="button-group"][data-grow]) {
          display: flex;
          inline-size: 100%;
        }

        :where([data-citry-ui-part="button-group"][data-grow]) > :where([data-citry-ui-part="button"]) {
          flex: 1 1 0;
          min-inline-size: 0;
        }

        :where([data-citry-ui-part="button-group"][data-attached]) {
          gap: 0;
        }

        :where([data-citry-ui-part="button-group"][data-attached]) > :where([data-citry-ui-part="button"]) {
          position: relative;
          border-radius: 0;
        }

        :where([data-citry-ui-part="button-group"][data-attached][data-orientation="horizontal"])
          > :where([data-citry-ui-part="button"]:first-child) {
          border-start-start-radius: var(--_cui-button-group-radius);
          border-end-start-radius: var(--_cui-button-group-radius);
        }

        :where([data-citry-ui-part="button-group"][data-attached][data-orientation="horizontal"])
          > :where([data-citry-ui-part="button"]:last-child) {
          border-start-end-radius: var(--_cui-button-group-radius);
          border-end-end-radius: var(--_cui-button-group-radius);
        }

        :where([data-citry-ui-part="button-group"][data-attached][data-orientation="horizontal"])
          > :where([data-citry-ui-part="button"] + [data-citry-ui-part="button"]) {
          margin-inline-start: calc(-1 * var(--_cui-button-group-border-width));
        }

        :where([data-citry-ui-part="button-group"][data-attached][data-orientation="vertical"])
          > :where([data-citry-ui-part="button"]:first-child) {
          border-start-start-radius: var(--_cui-button-group-radius);
          border-start-end-radius: var(--_cui-button-group-radius);
        }

        :where([data-citry-ui-part="button-group"][data-attached][data-orientation="vertical"])
          > :where([data-citry-ui-part="button"]:last-child) {
          border-end-start-radius: var(--_cui-button-group-radius);
          border-end-end-radius: var(--_cui-button-group-radius);
        }

        :where([data-citry-ui-part="button-group"][data-attached][data-orientation="vertical"])
          > :where([data-citry-ui-part="button"] + [data-citry-ui-part="button"]) {
          margin-block-start: calc(-1 * var(--_cui-button-group-border-width));
        }

        :where([data-citry-ui-part="button-group"]) > :where([data-citry-ui-part="button"]:focus-visible) {
          z-index: 1;
        }
      }
    """
