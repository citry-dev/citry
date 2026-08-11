"""Semantic and decorative Divider component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CDividerOrientation = Literal["horizontal", "vertical"]
CDividerVariant = Literal["solid", "dashed", "dotted"]
CDividerSize = Literal["sm", "md", "lg"]
CDividerInset = Literal["none", "start", "end", "both"]
CDividerLabelPos = Literal["start", "center", "end"]

_ORIENTATIONS = ("horizontal", "vertical")
_VARIANTS = ("solid", "dashed", "dotted")
_SIZES = ("sm", "md", "lg")
_INSETS = ("none", "start", "end", "both")
_LABEL_POSITIONS = ("start", "center", "end")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "x-bind",
        "x-for",
        "x-html",
        "x-if",
        "x-ignore",
        "x-model",
        "x-modelable",
        "x-teleport",
        "x-text",
    }
)
_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-orientation",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "data-decorative",
        "data-inset",
        "data-label-pos",
        "data-labeled",
        "data-orientation",
        "data-size",
        "data-variant",
        "role",
        "tabindex",
    }
)


class CDividerDefaultSlotData:
    pass


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CDivider {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CDivider could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CDivider {input_name} must be one of {expected}, got {plain!r}."
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
        msg = f"CDivider attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CDivider attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CDivider attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CDivider attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _OWNED_ATTRS:
            msg = f"CDivider attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CDivider(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        orientation: CDividerOrientation = "horizontal"
        variant: CDividerVariant = "solid"
        size: CDividerSize = "sm"
        inset: CDividerInset = "none"
        label_pos: CDividerLabelPos = "center"
        decorative: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CDividerDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        orientation = _plain_choice("orientation", kwargs.orientation, _ORIENTATIONS)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)
        inset = _plain_choice("inset", kwargs.inset, _INSETS)
        label_pos = _plain_choice("label_pos", kwargs.label_pos, _LABEL_POSITIONS)
        validate_boolean("CDivider", "decorative", kwargs.decorative)
        has_label = "default" in self.raw_slots
        if has_label and orientation == "vertical":
            msg = "CDivider does not support a label with vertical orientation."
            raise ValueError(msg)
        if not has_label and label_pos != "center":
            msg = "CDivider label_pos requires a default slot."
            raise ValueError(msg)

        decorative = bool(kwargs.decorative)
        return {
            "orientation": orientation,
            "variant": variant,
            "size": size,
            "inset": inset,
            "label_pos": label_pos,
            "has_label": has_label,
            "decorative": decorative,
            "effective_decorative": decorative or has_label,
            "vertical_role": None if decorative else "separator",
            "vertical_aria_orientation": None if decorative else "vertical",
            "attrs": merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style),
        }

    template = """
      <c-if cond="has_label">
        <div
          class="cui-divider cui-divider--labeled"
          c-bind="attrs"
          data-citry-ui-part="divider"
          data-orientation="horizontal"
          c-data-variant="variant"
          c-data-size="size"
          c-data-inset="inset"
          c-data-label-pos="label_pos"
          data-labeled
          data-decorative
        >
          <hr
            class="cui-divider__line"
            data-citry-ui-part="line"
            aria-hidden="true"
          />
          <span class="cui-divider__label" data-citry-ui-part="label">
            <c-slot />
          </span>
          <hr
            class="cui-divider__line"
            data-citry-ui-part="line"
            aria-hidden="true"
          />
        </div>
      </c-if>
      <c-else>
        <c-if cond="orientation == 'horizontal'">
          <hr
            class="cui-divider"
            c-bind="attrs"
            data-citry-ui-part="divider"
            data-orientation="horizontal"
            c-data-variant="variant"
            c-data-size="size"
            c-data-inset="inset"
            c-data-decorative="effective_decorative"
            c-aria-hidden="decorative"
          />
        </c-if>
        <c-else>
          <div
            class="cui-divider"
            c-bind="attrs"
            data-citry-ui-part="divider"
            data-orientation="vertical"
            c-data-variant="variant"
            c-data-size="size"
            c-data-inset="inset"
            c-data-decorative="effective_decorative"
            c-role="vertical_role"
            c-aria-orientation="vertical_aria_orientation"
            c-aria-hidden="decorative"
          ></div>
        </c-else>
      </c-else>
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="divider"]) {
          --_cui-divider-color: var(--cui-divider-color, light-dark(#d6d3d1, #57534e));
          --_cui-divider-thickness: var(--cui-divider-thickness, 1px);
          --_cui-divider-inset: var(--cui-divider-inset, 1.5rem);
          --_cui-divider-label-gap: var(--cui-divider-label-gap, 0.75rem);
          --_cui-divider-label-color: var(--cui-divider-label-color, CanvasText);
          --_cui-divider-label-font-size: var(--cui-divider-label-font-size, 0.875rem);
          --_cui-divider-label-font-weight: var(--cui-divider-label-font-weight, 600);
          --_cui-divider-min-length: var(--cui-divider-min-length, 1em);
          box-sizing: border-box;
          min-inline-size: 0;
          margin: 0;
          padding: 0;
          border: 0;
          color: var(--_cui-divider-color);
        }

        :where([data-citry-ui-part="divider"][data-size="md"]) {
          --_cui-divider-thickness: var(--cui-divider-thickness, 2px);
        }

        :where([data-citry-ui-part="divider"][data-size="lg"]) {
          --_cui-divider-thickness: var(--cui-divider-thickness, 4px);
        }

        :where([data-citry-ui-part="divider"][data-orientation="horizontal"]:not([data-labeled])) {
          inline-size: 100%;
          block-size: 0;
          border-block-start-width: var(--_cui-divider-thickness);
          border-block-start-style: solid;
          border-block-start-color: var(--_cui-divider-color);
        }

        :where([data-citry-ui-part="divider"][data-orientation="vertical"]) {
          align-self: stretch;
          inline-size: 0;
          min-block-size: var(--_cui-divider-min-length);
          border-inline-start-width: var(--_cui-divider-thickness);
          border-inline-start-style: solid;
          border-inline-start-color: var(--_cui-divider-color);
        }

        :where([data-citry-ui-part="divider"][data-variant="dashed"]:not([data-labeled])) {
          border-block-start-style: dashed;
        }

        :where([data-citry-ui-part="divider"][data-orientation="vertical"][data-variant="dashed"]) {
          border-block-start-style: none;
          border-inline-start-style: dashed;
        }

        :where([data-citry-ui-part="divider"][data-variant="dotted"]:not([data-labeled])) {
          border-block-start-style: dotted;
        }

        :where([data-citry-ui-part="divider"][data-orientation="vertical"][data-variant="dotted"]) {
          border-block-start-style: none;
          border-inline-start-style: dotted;
        }

        :where([data-citry-ui-part="divider"][data-orientation="horizontal"][data-inset="start"]) {
          inline-size: calc(100% - var(--_cui-divider-inset));
          margin-inline-start: var(--_cui-divider-inset);
        }

        :where([data-citry-ui-part="divider"][data-orientation="horizontal"][data-inset="end"]) {
          inline-size: calc(100% - var(--_cui-divider-inset));
          margin-inline-end: var(--_cui-divider-inset);
        }

        :where([data-citry-ui-part="divider"][data-orientation="horizontal"][data-inset="both"]) {
          inline-size: calc(100% - var(--_cui-divider-inset) - var(--_cui-divider-inset));
          margin-inline: var(--_cui-divider-inset);
        }

        :where([data-citry-ui-part="divider"][data-orientation="vertical"][data-inset="start"]) {
          min-block-size: 0;
          block-size: calc(100% - var(--_cui-divider-inset));
          margin-block-start: var(--_cui-divider-inset);
        }

        :where([data-citry-ui-part="divider"][data-orientation="vertical"][data-inset="end"]) {
          min-block-size: 0;
          block-size: calc(100% - var(--_cui-divider-inset));
          margin-block-end: var(--_cui-divider-inset);
        }

        :where([data-citry-ui-part="divider"][data-orientation="vertical"][data-inset="both"]) {
          min-block-size: 0;
          block-size: calc(100% - var(--_cui-divider-inset) - var(--_cui-divider-inset));
          margin-block: var(--_cui-divider-inset);
        }

        :where([data-citry-ui-part="divider"][data-labeled]) {
          display: flex;
          inline-size: 100%;
          align-items: center;
          gap: var(--_cui-divider-label-gap);
        }

        :where([data-citry-ui-part="divider"] > [data-citry-ui-part="line"]) {
          box-sizing: border-box;
          min-inline-size: 0;
          flex: 1 1 0;
          margin: 0;
          padding: 0;
          border: 0;
          border-block-start-width: var(--_cui-divider-thickness);
          border-block-start-style: solid;
          border-block-start-color: var(--_cui-divider-color);
        }

        :where([data-citry-ui-part="divider"][data-variant="dashed"] > [data-citry-ui-part="line"]) {
          border-block-start-style: dashed;
        }

        :where([data-citry-ui-part="divider"][data-variant="dotted"] > [data-citry-ui-part="line"]) {
          border-block-start-style: dotted;
        }

        :where([data-citry-ui-part="divider"] > [data-citry-ui-part="label"]) {
          min-inline-size: 0;
          color: var(--_cui-divider-label-color);
          font-size: var(--_cui-divider-label-font-size);
          font-weight: var(--_cui-divider-label-font-weight);
          line-height: 1.3;
          overflow-wrap: anywhere;
        }

        :where([data-citry-ui-part="divider"][data-label-pos="start"] > [data-citry-ui-part="line"]:first-child),
        :where([data-citry-ui-part="divider"][data-label-pos="end"] > [data-citry-ui-part="line"]:last-child) {
          flex: 0 1 8%;
        }

        @media (forced-colors: active) {
          :where([data-citry-ui-part="divider"]) {
            --_cui-divider-color: var(--cui-divider-color, CanvasText);
            --_cui-divider-label-color: var(--cui-divider-label-color, CanvasText);
            forced-color-adjust: auto;
          }
        }

        @media print {
          :where([data-citry-ui-part="divider"]) {
            --_cui-divider-color: var(--cui-divider-color, currentColor);
            --_cui-divider-label-color: var(--cui-divider-label-color, currentColor);
          }
        }
      }
    """


__all__ = [
    "CDivider",
    "CDividerDefaultSlotData",
    "CDividerInset",
    "CDividerLabelPos",
    "CDividerOrientation",
    "CDividerSize",
    "CDividerVariant",
]
