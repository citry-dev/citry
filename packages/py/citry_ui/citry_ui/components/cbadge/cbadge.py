"""Static inline Badge component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CBadgeVariant = Literal["soft", "solid", "outline"]
CBadgeIntent = Literal["neutral", "primary", "success", "warn", "danger"]
CBadgeSize = Literal["sm", "md", "lg"]
CBadgeShape = Literal["rounded", "pill"]

_VARIANTS = ("soft", "solid", "outline")
_INTENTS = ("neutral", "primary", "success", "warn", "danger")
_SIZES = ("sm", "md", "lg")
_SHAPES = ("rounded", "pill")
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
        "contenteditable",
        "data-citry-ui-part",
        "data-intent",
        "data-shape",
        "data-size",
        "data-variant",
        "role",
        "tabindex",
    }
)


class CBadgeDefaultSlotData:
    pass


class CBadgeStartSlotData:
    pass


class CBadgeEndSlotData:
    pass


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CBadge {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CBadge could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CBadge {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _copy_attrs(attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CBadge attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, _OWNED_ATTRS, "CBadge attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"CBadge attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"CBadge attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in _OWNED_ATTRS:
            msg = f"CBadge attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CBadge(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        variant: CBadgeVariant = "soft"
        intent: CBadgeIntent = "neutral"
        size: CBadgeSize = "md"
        shape: CBadgeShape = "rounded"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CBadgeDefaultSlotData] | None = None
        start: SlotInput[CBadgeStartSlotData] | None = None
        end: SlotInput[CBadgeEndSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if "default" not in self.raw_slots:
            msg = "CBadge requires a default slot."
            raise ValueError(msg)
        return {
            "variant": _plain_choice("variant", kwargs.variant, _VARIANTS),
            "intent": _plain_choice("intent", kwargs.intent, _INTENTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "shape": _plain_choice("shape", kwargs.shape, _SHAPES),
            "attrs": merge_root_attrs(_copy_attrs(kwargs.attrs), kwargs.class_, kwargs.style),
            "has_start": "start" in self.raw_slots,
            "has_end": "end" in self.raw_slots,
        }

    template = """
      <span
        class="cui-badge"
        c-bind="attrs"
        data-citry-ui-part="badge"
        c-data-variant="variant"
        c-data-intent="intent"
        c-data-size="size"
        c-data-shape="shape"
      >
        <c-if cond="has_start">
          <span class="cui-badge__start" data-citry-ui-part="start">
            <c-slot name="start" />
          </span>
        </c-if>
        <span class="cui-badge__label" data-citry-ui-part="label">
          <c-slot />
        </span>
        <c-if cond="has_end">
          <span class="cui-badge__end" data-citry-ui-part="end">
            <c-slot name="end" />
          </span>
        </c-if>
      </span>
    """

    css_file = "runtime.min.css"


__all__ = [
    "CBadge",
    "CBadgeDefaultSlotData",
    "CBadgeEndSlotData",
    "CBadgeIntent",
    "CBadgeShape",
    "CBadgeSize",
    "CBadgeStartSlotData",
    "CBadgeVariant",
]
