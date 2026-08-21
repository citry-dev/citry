"""Styled one-dimensional layout components."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CFlowTag = Literal["div", "section", "nav", "ul", "ol"]
CFlowGap = Literal["0", "xs", "sm", "md", "lg", "xl"]
CFlowAlign = Literal["start", "center", "end", "stretch", "baseline"]
CFlowJustify = Literal["start", "center", "end", "between", "around", "evenly"]

_TAGS = ("div", "section", "nav", "ul", "ol")
_GAPS = ("0", "xs", "sm", "md", "lg", "xl")
_ALIGNS = ("start", "center", "end", "stretch", "baseline")
_JUSTIFIES = ("start", "center", "end", "between", "around", "evenly")
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
_STACK_OWNED_ATTRS = frozenset(
    {
        "data-align",
        "data-citry-ui-part",
        "data-gap",
        "data-justify",
        "data-reverse",
    }
)
_GROUP_OWNED_ATTRS = _STACK_OWNED_ATTRS | {"data-wrap"}


class CStackDefaultSlotData:
    pass


class CGroupDefaultSlotData:
    pass


def _plain_choice(
    component_name: str,
    input_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"{component_name} {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"{component_name} could not convert {input_name} to a plain string."
        raise TypeError(msg)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{component_name} {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    component_name: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"{component_name} attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{component_name} attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized in _OWNERSHIP_DIRECTIVES or any(
            normalized.startswith(f"{directive}.") for directive in _OWNERSHIP_DIRECTIVES
        ):
            msg = f"{component_name} attrs cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{component_name} attrs cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)
    return copied


class CStack(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tag: CFlowTag = "div"
        gap: CFlowGap = "md"
        align: CFlowAlign = "stretch"
        justify: CFlowJustify = "start"
        reverse: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CStackDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        tag = _plain_choice("CStack", "tag", kwargs.tag, _TAGS)
        gap = _plain_choice("CStack", "gap", kwargs.gap, _GAPS)
        align = _plain_choice("CStack", "align", kwargs.align, _ALIGNS)
        justify = _plain_choice("CStack", "justify", kwargs.justify, _JUSTIFIES)
        validate_boolean("CStack", "reverse", kwargs.reverse)
        attrs = _copy_attrs("CStack", kwargs.attrs, _STACK_OWNED_ATTRS)
        return {
            "tag": tag,
            "gap": gap,
            "align": align,
            "justify": justify,
            "reverse": bool(kwargs.reverse),
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-stack"
        c-bind="attrs"
        data-citry-ui-part="stack"
        c-data-gap="gap"
        c-data-align="align"
        c-data-justify="justify"
        c-data-reverse="reverse"
      >
        <c-slot />
      </c-element>
    """

    css_file = "runtime.min.css"


class CGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tag: CFlowTag = "div"
        gap: CFlowGap = "sm"
        align: CFlowAlign = "center"
        justify: CFlowJustify = "start"
        reverse: bool = False
        wrap: bool = True
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CGroupDefaultSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        tag = _plain_choice("CGroup", "tag", kwargs.tag, _TAGS)
        gap = _plain_choice("CGroup", "gap", kwargs.gap, _GAPS)
        align = _plain_choice("CGroup", "align", kwargs.align, _ALIGNS)
        justify = _plain_choice("CGroup", "justify", kwargs.justify, _JUSTIFIES)
        validate_boolean("CGroup", "reverse", kwargs.reverse)
        validate_boolean("CGroup", "wrap", kwargs.wrap)
        attrs = _copy_attrs("CGroup", kwargs.attrs, _GROUP_OWNED_ATTRS)
        return {
            "tag": tag,
            "gap": gap,
            "align": align,
            "justify": justify,
            "reverse": bool(kwargs.reverse),
            "wrap": bool(kwargs.wrap),
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-group"
        c-bind="attrs"
        data-citry-ui-part="group"
        c-data-gap="gap"
        c-data-align="align"
        c-data-justify="justify"
        c-data-reverse="reverse"
        c-data-wrap="wrap"
      >
        <c-slot />
      </c-element>
    """

    css_file = "runtime.c-group.min.css"


__all__ = [
    "CFlowAlign",
    "CFlowGap",
    "CFlowJustify",
    "CFlowTag",
    "CGroup",
    "CGroupDefaultSlotData",
    "CStack",
    "CStackDefaultSlotData",
]
