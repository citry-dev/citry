"""Semantic server-rendered Breadcrumbs component."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CBreadcrumbsSize = Literal["sm", "md", "lg"]

_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_ROOT_OWNED_ATTRS = frozenset({"aria-hidden", "aria-label", "data-citry-ui-part", "data-size", "data-wrap", "role"})
_LIST_OWNED_ATTRS = frozenset({"aria-hidden", "data-citry-ui-part", "role"})
_ITEM_OWNED_ATTRS = frozenset({"aria-current", "aria-hidden", "data-citry-ui-part", "href", "role"})


@dataclass(frozen=True, slots=True)
class CBreadcrumbItem:
    label: str
    href: str | None = None
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CBreadcrumbsItemSlotData:
    item: CBreadcrumbItem
    index: int
    is_current: bool
    attrs: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CBreadcrumbsSeparatorSlotData:
    index: int


@dataclass(frozen=True, slots=True)
class _ResolvedBreadcrumb:
    item: CBreadcrumbItem
    index: int
    is_current: bool
    attrs: Mapping[str, object]


def _plain_string(input_name: str, value: object, *, allow_none: bool = False) -> str | None:
    if value is None and allow_none:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CBreadcrumbs {input_name} must be a string{' or None' if allow_none else ''}, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if type(plain) is not str:
        raise TypeError(f"CBreadcrumbs could not convert {input_name} to a plain string.")
    if "\0" in plain:
        raise ValueError(f"CBreadcrumbs {input_name} cannot contain U+0000.")
    return plain


def _plain_nonempty(input_name: str, value: object) -> str:
    plain = _plain_string(input_name, value)
    if not plain or not plain.strip():
        raise ValueError(f"CBreadcrumbs {input_name} must be non-empty.")
    return plain


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        raise TypeError(f"CBreadcrumbs {input_name} must be a mapping or None, got {attrs!r}.")
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    if attribute.startswith("x-bind:"):
        return attribute.removeprefix("x-bind:").split(".", 1)[0]
    if attribute.startswith((":", ".")):
        return attribute[1:].split(".", 1)[0]
    return None


def _validate_attrs(input_name: str, attrs: dict[str, object], owned: frozenset[str]) -> None:
    component_name = f"CBreadcrumbs {input_name}"
    reject_owned_attrs(attrs, owned, component_name)
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{component_name} cannot contain reserved Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _OWNERSHIP_DIRECTIVES:
            raise ValueError(f"{component_name} cannot use ownership directive {key!r}.")
        target = _dynamic_target(normalized)
        if target in owned:
            raise ValueError(f"{component_name} cannot dynamically bind owned attribute {target!r}.")


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"CBreadcrumbs {input_name} must be one of {expected}, got {plain!r}.")
    return plain


class CBreadcrumbs(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        items: Sequence[CBreadcrumbItem]
        label: str = "Breadcrumbs"
        separator: str = "/"
        size: CBreadcrumbsSize = "md"
        wrap: bool = True
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        list_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        item: SlotInput[CBreadcrumbsItemSlotData] | None = None
        separator: SlotInput[CBreadcrumbsSeparatorSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        if isinstance(kwargs.items, (str, bytes, bytearray)) or not isinstance(kwargs.items, Sequence):
            raise TypeError("CBreadcrumbs items must be a sequence of CBreadcrumbItem values.")
        snapshot = tuple(kwargs.items)
        if not snapshot:
            raise ValueError("CBreadcrumbs requires at least one item.")
        catalog_label = uses_catalog_default(self, "label")
        label = _plain_nonempty(
            "label",
            self.i18n.tr("citry-ui-breadcrumbs-label") if catalog_label else kwargs.label,
        )
        separator = _plain_string("separator", kwargs.separator)
        size = _plain_choice("size", kwargs.size, _SIZES)
        validate_boolean("CBreadcrumbs", "wrap", kwargs.wrap)
        attrs = _copy_attrs("attrs", kwargs.attrs)
        list_attrs = _copy_attrs("list_attrs", kwargs.list_attrs)
        _validate_attrs("attrs", attrs, _ROOT_OWNED_ATTRS)
        _validate_attrs("list_attrs", list_attrs, _LIST_OWNED_ATTRS)
        resolved: list[_ResolvedBreadcrumb] = []
        for index, item in enumerate(snapshot):
            if not isinstance(item, CBreadcrumbItem):
                raise TypeError(f"CBreadcrumbs items[{index}] must be CBreadcrumbItem, got {item!r}.")
            item_label = _plain_nonempty(f"items[{index}].label", item.label)
            href = _plain_string(f"items[{index}].href", item.href, allow_none=True)
            if href == "":
                raise ValueError(f"CBreadcrumbs items[{index}].href must be non-empty when supplied.")
            item_attrs = _copy_attrs(f"items[{index}].attrs", item.attrs)
            _validate_attrs(f"items[{index}].attrs", item_attrs, _ITEM_OWNED_ATTRS)
            current = index == len(snapshot) - 1
            normalized = CBreadcrumbItem(label=item_label, href=href, attrs=item_attrs)
            link_attrs = dict(item_attrs)
            if href is not None:
                link_attrs["href"] = href
            if current:
                link_attrs["aria-current"] = "page"
            resolved.append(
                _ResolvedBreadcrumb(
                    item=normalized,
                    index=index,
                    is_current=current,
                    attrs=link_attrs,
                )
            )
        return {
            "items": tuple(resolved),
            "label": label,
            "catalog_label": catalog_label,
            "separator": separator,
            "size": size,
            "wrap": kwargs.wrap,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "list_attrs": list_attrs,
        }

    template = """
      <nav
        class="cui-breadcrumbs"
        c-aria-label="tr('citry-ui-breadcrumbs-label') if catalog_label else label"
        c-$c-tr:citry-ui-breadcrumbs-label[aria-label]="True if catalog_label else None"
        c-data-size="size"
        c-data-wrap="wrap"
        c-bind="attrs"
        data-citry-ui-part="breadcrumbs"
      >
        <ol c-bind="list_attrs" data-citry-ui-part="list">
          <li c-for="resolved in items" data-citry-ui-part="item">
            <c-slot
              name="item"
              c-item="resolved.item"
              c-index="resolved.index"
              c-is_current="resolved.is_current"
              c-attrs="resolved.attrs"
            >
              <c-if cond="resolved.item.href is not None">
                <a c-bind="resolved.attrs" data-citry-ui-part="link">
                  {{ resolved.item.label }}
                </a>
              </c-if>
              <c-else>
                <span c-bind="resolved.attrs" data-citry-ui-part="current">
                  {{ resolved.item.label }}
                </span>
              </c-else>
            </c-slot>
            <c-if cond="not resolved.is_current">
              <span aria-hidden="true" data-citry-ui-part="separator">
                <c-slot name="separator" c-index="resolved.index">
                  {{ separator }}
                </c-slot>
              </span>
            </c-if>
          </li>
        </ol>
      </nav>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-breadcrumbs) {
          --_cui-breadcrumbs-foreground: var(--cui-breadcrumbs-foreground, CanvasText);
          --_cui-breadcrumbs-link-color: var(--cui-breadcrumbs-link-color, LinkText);
          --_cui-breadcrumbs-current-color: var(--cui-breadcrumbs-current-color, CanvasText);
          --_cui-breadcrumbs-separator-color: var(
            --cui-breadcrumbs-separator-color,
            color-mix(in srgb, CanvasText 54%, transparent)
          );
          --_cui-breadcrumbs-gap: var(--cui-breadcrumbs-gap, 0.5rem);
          --_cui-breadcrumbs-focus-color: var(--cui-breadcrumbs-focus-color, Highlight);
          color: var(--_cui-breadcrumbs-foreground);
          font: inherit;
          font-size: 0.875rem;
        }

        :where(.cui-breadcrumbs[data-size="sm"]) {
          font-size: 0.75rem;
        }

        :where(.cui-breadcrumbs[data-size="lg"]) {
          font-size: 1rem;
        }

        :where(.cui-breadcrumbs > [data-citry-ui-part="list"]) {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: var(--_cui-breadcrumbs-gap);
          min-inline-size: 0;
          margin: 0;
          padding: 0;
          list-style: none;
        }

        :where(.cui-breadcrumbs:not([data-wrap]) > [data-citry-ui-part="list"]) {
          flex-wrap: nowrap;
          overflow-x: auto;
          scrollbar-width: thin;
        }

        :where(
          .cui-breadcrumbs
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
        ) {
          display: inline-flex;
          align-items: center;
          min-inline-size: 0;
          gap: var(--_cui-breadcrumbs-gap);
        }

        :where(
          .cui-breadcrumbs
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
          > [data-citry-ui-part="link"]
        ) {
          color: var(--_cui-breadcrumbs-link-color);
          text-decoration-thickness: 0.08em;
          text-underline-offset: 0.16em;
          overflow-wrap: anywhere;
        }

        :where(
          .cui-breadcrumbs
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
          > [data-citry-ui-part="link"]:focus-visible
        ) {
          outline: 0.1875rem solid color-mix(in srgb, var(--_cui-breadcrumbs-focus-color) 44%, transparent);
          outline-offset: 0.125rem;
          border-radius: 0.15rem;
        }

        :where(
          .cui-breadcrumbs
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
          > [data-citry-ui-part="current"]
        ) {
          color: var(--_cui-breadcrumbs-current-color);
          font-weight: 600;
          overflow-wrap: anywhere;
        }

        :where(
          .cui-breadcrumbs
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
          > [data-citry-ui-part="separator"]
        ) {
          color: var(--_cui-breadcrumbs-separator-color);
          user-select: none;
        }

        :where(
          .cui-breadcrumbs:not([data-wrap])
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
          > [data-citry-ui-part="link"]
        ),
        :where(
          .cui-breadcrumbs:not([data-wrap])
          > [data-citry-ui-part="list"]
          > [data-citry-ui-part="item"]
          > [data-citry-ui-part="current"]
        ) {
          white-space: nowrap;
        }

        @media (forced-colors: active) {
          :where(
            .cui-breadcrumbs
            > [data-citry-ui-part="list"]
            > [data-citry-ui-part="item"]
            > [data-citry-ui-part="separator"]
          ) {
            color: CanvasText;
          }
        }

        @media print {
          :where(
            .cui-breadcrumbs
            > [data-citry-ui-part="list"]
            > [data-citry-ui-part="item"]
            > [data-citry-ui-part="link"]
          ) {
            color: currentColor;
          }
        }
      }
    """

    messages = """
      citry-ui-breadcrumbs-label = Breadcrumbs
    """


__all__ = [
    "CBreadcrumbItem",
    "CBreadcrumbs",
    "CBreadcrumbsItemSlotData",
    "CBreadcrumbsSeparatorSlotData",
    "CBreadcrumbsSize",
]
