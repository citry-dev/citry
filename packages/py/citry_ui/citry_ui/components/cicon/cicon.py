"""Styled Icon component family."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, get_args

from citry import LibraryComponent, Markup, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_choice
from citry_ui.components.cicon._catalog import ICON_GLYPHS

CIconSize = Literal["sm", "md", "lg"]
CIconName = Literal[
    "arrow-down",
    "arrow-left",
    "arrow-right",
    "arrow-up",
    "back",
    "calendar",
    "check",
    "chevron-down",
    "chevron-left",
    "chevron-right",
    "chevron-up",
    "circle-check",
    "circle-help",
    "circle-info",
    "circle-x",
    "clear",
    "clock",
    "close",
    "collapse",
    "copy",
    "danger",
    "download",
    "dropdown",
    "edit",
    "expand",
    "external-link",
    "eye",
    "eye-off",
    "file",
    "folder",
    "forward",
    "heart",
    "home",
    "info",
    "leaf",
    "link",
    "lock",
    "mail",
    "menu",
    "minus",
    "more-horizontal",
    "more-vertical",
    "next",
    "plus",
    "prev",
    "refresh-cw",
    "search",
    "settings",
    "star",
    "success",
    "trash",
    "triangle-alert",
    "unlock",
    "upload",
    "user",
    "warn",
    "x",
]

_SEMANTIC_ALIASES = MappingProxyType(
    {
        "back": "arrow-left",
        "forward": "arrow-right",
        "prev": "chevron-left",
        "next": "chevron-right",
        "close": "x",
        "clear": "x",
        "success": "circle-check",
        "info": "circle-info",
        "warn": "triangle-alert",
        "danger": "circle-x",
        "expand": "chevron-down",
        "collapse": "chevron-up",
        "dropdown": "chevron-down",
    }
)
_LOGICAL_DIRECTION_NAMES = frozenset({"back", "forward", "prev", "next"})
_ICON_NAMES = frozenset(get_args(CIconName))
_ALLOWED_ARIA_ATTRS = frozenset({"aria-describedby", "aria-details"})
_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "data-citry-ui-part",
        "data-name",
        "data-size",
        "fill",
        "focusable",
        "height",
        "href",
        "role",
        "stroke",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-width",
        "tabindex",
        "viewbox",
        "width",
        "xlink:href",
        "xmlns",
    }
)


@dataclass(frozen=True, slots=True)
class _RegisteredIconGlyph:
    name: str
    markup: Markup
    logical: bool


def _resolve_registered_icon(name: object, component_name: str) -> _RegisteredIconGlyph:
    raw_name = const_value(name)
    _reject_trusted_html(raw_name, "name")
    if not isinstance(raw_name, str):
        msg = f"{component_name} name must be a string, got {raw_name!r}."
        raise TypeError(msg)
    plain_name = "".join(raw_name)
    if type(plain_name) is not str:
        msg = f"{component_name} could not convert name to a plain string."
        raise TypeError(msg)
    if plain_name not in _ICON_NAMES:
        msg = f"{component_name} name must be a documented icon name, got {plain_name!r}."
        raise ValueError(msg)
    glyph_name = _SEMANTIC_ALIASES.get(plain_name, plain_name)
    return _RegisteredIconGlyph(
        name=plain_name,
        markup=Markup(ICON_GLYPHS[glyph_name]),  # noqa: S704 - generated package-owned allowlist
        logical=plain_name in _LOGICAL_DIRECTION_NAMES,
    )


def _reject_trusted_html(value: object, input_name: str, seen: set[int] | None = None) -> None:
    if hasattr(value, "__html__"):
        msg = f"CIcon {input_name} cannot contain a trusted HTML value."
        raise ValueError(msg)
    if seen is None:
        seen = set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        for key, item in value.items():
            _reject_trusted_html(key, input_name, seen)
            _reject_trusted_html(item, input_name, seen)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        for item in value:
            _reject_trusted_html(item, input_name, seen)


def _validate_icon_attrs(attrs: Mapping[str, object] | None) -> None:
    if attrs is not None and not isinstance(attrs, Mapping):
        msg = f"CIcon attrs must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    reject_owned_attrs(attrs, _OWNED_ATTRS, "CIcon")
    for key in attrs or {}:
        normalized = key.lower()
        if normalized.startswith("aria-") and normalized not in _ALLOWED_ARIA_ATTRS:
            msg = f"CIcon attrs cannot override owned accessibility attribute {key!r}."
            raise ValueError(msg)
        if normalized.startswith(("data-citry-", "data-cev", "data-cid")):
            msg = f"CIcon attrs cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        if normalized.startswith(("@", ":", ".", "$", "c-", "x-")) or (
            normalized.startswith("on") and len(normalized) > 2
        ):
            msg = f"CIcon attrs cannot contain executable browser attribute {key!r}."
            raise ValueError(msg)


class CIcon(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        name: CIconName
        label: str | None = None
        size: CIconSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        for input_name, value in (
            ("name", kwargs.name),
            ("label", kwargs.label),
            ("size", kwargs.size),
            ("class_", kwargs.class_),
            ("style", kwargs.style),
            ("attrs", kwargs.attrs),
        ):
            _reject_trusted_html(value, input_name)
        resolved_icon = _resolve_registered_icon(kwargs.name, "CIcon")
        if kwargs.label is not None and not isinstance(kwargs.label, str):
            msg = f"CIcon label must be a string or None, got {kwargs.label!r}."
            raise TypeError(msg)
        if kwargs.label is not None and not kwargs.label.strip():
            msg = "CIcon label must contain non-whitespace text when set."
            raise ValueError(msg)
        validate_choice("CIcon", "size", kwargs.size, ("sm", "md", "lg"))
        _validate_icon_attrs(kwargs.attrs)

        return {
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
            "glyph": resolved_icon.markup,
            "label": kwargs.label,
            "role": "img" if kwargs.label is not None else None,
            "aria_hidden": "true" if kwargs.label is None else None,
            "name": resolved_icon.name,
            "size": kwargs.size,
            "logical": resolved_icon.logical,
        }

    template = """
      <svg
        c-class="['cui-icon', {'cui-icon--logical': logical}]"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-linecap="round"
        stroke-linejoin="round"
        focusable="false"
        c-role="role"
        c-aria-label="label"
        c-aria-hidden="aria_hidden"
        c-data-name="name"
        c-data-size="size"
        c-bind="attrs"
        data-citry-ui-part="icon"
      >
        <g class="cui-icon__glyph">
          {{ glyph }}
        </g>
      </svg>
    """

    css_file = "runtime.min.css"


__all__ = ["CIcon", "CIconName", "CIconSize"]
