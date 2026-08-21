"""Styled Card component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs

CCardTag = Literal["div", "article", "section", "li"]
CCardVariant = Literal["elevated", "outline", "subtle"]
CCardSize = Literal["sm", "md", "lg"]

_RESERVED_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_ROOT_OWNED_ATTRS = frozenset({"data-citry-ui-part", "data-size", "data-variant"})
_PART_OWNED_ATTRS = frozenset({"data-citry-ui-part"})


class CCardMediaSlotData:
    pass


class CCardHeaderSlotData:
    pass


class CCardHeaderActionsSlotData:
    pass


class CCardDefaultSlotData:
    pass


class CCardFooterSlotData:
    pass


class CCardActionsSlotData:
    pass


def _validate_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if not isinstance(value, str):
        msg = f"CCard {input_name} must be a string, got {value!r}."
        raise TypeError(msg)
    if value not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CCard {input_name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)


def _copy_attrs(
    input_name: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CCard {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    reject_owned_attrs(attrs, owned, f"CCard {input_name}")
    for key in attrs or {}:
        normalized = key.lower()
        if normalized.startswith(_RESERVED_RUNTIME_PREFIXES):
            msg = f"CCard {input_name} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
    return dict(attrs or {})


def _reject_attrs_without_destination(
    input_name: str,
    attrs: Mapping[str, object],
    destination_exists: bool,
) -> None:
    if attrs and not destination_exists:
        msg = f"CCard {input_name} requires the corresponding Card section."
        raise ValueError(msg)


class CCard(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        tag: CCardTag = "div"
        variant: CCardVariant = "elevated"
        size: CCardSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        media_attrs: Mapping[str, object] | None = None
        header_attrs: Mapping[str, object] | None = None
        header_actions_attrs: Mapping[str, object] | None = None
        body_attrs: Mapping[str, object] | None = None
        footer_attrs: Mapping[str, object] | None = None
        actions_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        media: SlotInput[CCardMediaSlotData] | None = None
        header: SlotInput[CCardHeaderSlotData] | None = None
        header_actions: SlotInput[CCardHeaderActionsSlotData] | None = None
        default: SlotInput[CCardDefaultSlotData] | None = None
        footer: SlotInput[CCardFooterSlotData] | None = None
        actions: SlotInput[CCardActionsSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        _validate_choice("tag", kwargs.tag, ("div", "article", "section", "li"))
        _validate_choice("variant", kwargs.variant, ("elevated", "outline", "subtle"))
        _validate_choice("size", kwargs.size, ("sm", "md", "lg"))

        has_media = "media" in self.raw_slots
        has_header = "header" in self.raw_slots
        has_header_actions = "header_actions" in self.raw_slots
        has_default = "default" in self.raw_slots
        has_footer = "footer" in self.raw_slots
        has_actions = "actions" in self.raw_slots
        if not any((has_media, has_header, has_header_actions, has_default, has_footer, has_actions)):
            msg = "CCard requires at least one supplied slot."
            raise ValueError(msg)

        attrs = _copy_attrs("attrs", kwargs.attrs, _ROOT_OWNED_ATTRS)
        media_attrs = _copy_attrs("media_attrs", kwargs.media_attrs, _PART_OWNED_ATTRS)
        header_attrs = _copy_attrs("header_attrs", kwargs.header_attrs, _PART_OWNED_ATTRS)
        header_actions_attrs = _copy_attrs(
            "header_actions_attrs",
            kwargs.header_actions_attrs,
            _PART_OWNED_ATTRS,
        )
        body_attrs = _copy_attrs("body_attrs", kwargs.body_attrs, _PART_OWNED_ATTRS)
        footer_attrs = _copy_attrs("footer_attrs", kwargs.footer_attrs, _PART_OWNED_ATTRS)
        actions_attrs = _copy_attrs("actions_attrs", kwargs.actions_attrs, _PART_OWNED_ATTRS)

        _reject_attrs_without_destination("media_attrs", media_attrs, has_media)
        _reject_attrs_without_destination("header_attrs", header_attrs, has_header or has_header_actions)
        _reject_attrs_without_destination(
            "header_actions_attrs",
            header_actions_attrs,
            has_header_actions,
        )
        _reject_attrs_without_destination("body_attrs", body_attrs, has_default)
        _reject_attrs_without_destination("footer_attrs", footer_attrs, has_footer or has_actions)
        _reject_attrs_without_destination("actions_attrs", actions_attrs, has_actions)

        return {
            "tag": str(kwargs.tag),
            "variant": str(kwargs.variant),
            "size": str(kwargs.size),
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "media_attrs": media_attrs,
            "header_attrs": header_attrs,
            "header_actions_attrs": header_actions_attrs,
            "body_attrs": body_attrs,
            "footer_attrs": footer_attrs,
            "actions_attrs": actions_attrs,
            "has_media": has_media,
            "has_header": has_header,
            "has_header_actions": has_header_actions,
            "has_header_row": has_header or has_header_actions,
            "has_default": has_default,
            "has_footer": has_footer,
            "has_actions": has_actions,
            "has_footer_row": has_footer or has_actions,
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-card"
        c-data-variant="variant"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="card"
      >
        <c-if cond="has_media">
          <div
            class="cui-card__media"
            c-bind="media_attrs"
            data-citry-ui-part="media"
          >
            <c-slot name="media" />
          </div>
        </c-if>
        <c-if cond="has_header_row">
          <div
            c-class="[
              'cui-card__header',
              {'cui-card__row--split': has_header and has_header_actions},
            ]"
            c-bind="header_attrs"
            data-citry-ui-part="header"
          >
            <c-if cond="has_header">
              <div class="cui-card__header-content">
                <c-slot name="header" />
              </div>
            </c-if>
            <c-if cond="has_header_actions">
              <div
                class="cui-card__header-actions"
                c-bind="header_actions_attrs"
                data-citry-ui-part="header-actions"
              >
                <c-slot name="header_actions" />
              </div>
            </c-if>
          </div>
        </c-if>
        <c-if cond="has_default">
          <div
            class="cui-card__body"
            c-bind="body_attrs"
            data-citry-ui-part="body"
          >
            <c-slot />
          </div>
        </c-if>
        <c-if cond="has_footer_row">
          <div
            c-class="[
              'cui-card__footer',
              {'cui-card__row--split': has_footer and has_actions},
            ]"
            c-bind="footer_attrs"
            data-citry-ui-part="footer"
          >
            <c-if cond="has_footer">
              <div class="cui-card__footer-content">
                <c-slot name="footer" />
              </div>
            </c-if>
            <c-if cond="has_actions">
              <div
                class="cui-card__actions"
                c-bind="actions_attrs"
                data-citry-ui-part="actions"
              >
                <c-slot name="actions" />
              </div>
            </c-if>
          </div>
        </c-if>
      </c-element>
    """

    css_file = "runtime.min.css"


__all__ = [
    "CCard",
    "CCardActionsSlotData",
    "CCardDefaultSlotData",
    "CCardFooterSlotData",
    "CCardHeaderActionsSlotData",
    "CCardHeaderSlotData",
    "CCardMediaSlotData",
    "CCardSize",
    "CCardTag",
    "CCardVariant",
]
