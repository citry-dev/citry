"""Semantic content, navigation, and action Lists."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CListMarker = Literal["none", "disc", "decimal"]
CListDensity = Literal["comfortable", "compact"]
CListVariant = Literal["plain", "surface"]

_LIST_CONTEXT_KEY = "citry_ui_list"
_MARKERS = ("none", "disc", "decimal")
_DENSITIES = ("comfortable", "compact")
_VARIANTS = ("plain", "surface")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-teleport", "x-text"}
)
_LIST_OWNED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-density",
        "data-divided",
        "data-marker",
        "data-variant",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-hidden",
        "contenteditable",
        "data-citry-ui-part",
        "data-current",
        "data-disabled",
        "data-interactive",
        "role",
        "tabindex",
    }
)
_SURFACE_OWNED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-current",
        "aria-disabled",
        "aria-hidden",
        "contenteditable",
        "data-cui-list-has-end",
        "data-cui-list-has-start",
        "data-citry-ui-part",
        "disabled",
        "href",
        "hidden",
        "inert",
        "role",
        "tabindex",
        "type",
    }
)


class CListDefaultSlotData:
    pass


class CListItemDefaultSlotData:
    pass


class CListItemStartSlotData:
    pass


class CListItemDescriptionSlotData:
    pass


class CListItemEndSlotData:
    pass


@dataclass(slots=True)
class _ListContext:
    density: str
    variant: str
    count: int = 0


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw)
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{name} must be nonempty and cannot contain U+0000.")
    return plain


def _choice(component: str, name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(f"{component} {name}", value)
    if plain not in allowed:
        raise ValueError(f"{component} {name} must be one of {allowed!r}, got {plain!r}.")
    return plain


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(component: str, value: Mapping[str, object] | None, owned: frozenset[str]) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"{component} attrs must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, f"{component} attrs")
    for key in copied:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{component} attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{component} attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{component} attrs cannot dynamically bind owned attribute {key!r}.")
    return copied


class CList(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        ordered: bool = False
        start: int | None = None
        reversed: bool = False
        marker: CListMarker = "none"
        density: CListDensity = "comfortable"
        variant: CListVariant = "plain"
        divided: bool = False
        label: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CListDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        validate_boolean("CList", "ordered", kwargs.ordered)
        validate_boolean("CList", "reversed", kwargs.reversed)
        validate_boolean("CList", "divided", kwargs.divided)
        ordered = bool(kwargs.ordered)
        if kwargs.start is not None and (isinstance(kwargs.start, bool) or not isinstance(kwargs.start, int)):
            raise TypeError("CList start must be an integer or None.")
        if (kwargs.start is not None or kwargs.reversed) and not ordered:
            raise ValueError("CList start and reversed require ordered=True.")
        marker = _choice("CList", "marker", kwargs.marker, _MARKERS)
        if (marker == "decimal" and not ordered) or (marker == "disc" and ordered):
            raise ValueError("CList decimal marker requires ordered=True and disc requires ordered=False.")
        density = _choice("CList", "density", kwargs.density, _DENSITIES)
        variant = _choice("CList", "variant", kwargs.variant, _VARIANTS)
        context = _ListContext(density=density, variant=variant)
        self.provide(_LIST_CONTEXT_KEY, context=context)
        self._list_context = context
        return {
            "ordered": ordered,
            "start": kwargs.start,
            "reversed": bool(kwargs.reversed),
            "marker": marker,
            "density": density,
            "variant": variant,
            "divided": bool(kwargs.divided),
            "label": _plain("CList label", kwargs.label, optional=True),
            "attrs": merge_root_attrs(_attrs("CList", kwargs.attrs, _LIST_OWNED), kwargs.class_, kwargs.style),
        }

    def on_render(self) -> Any:
        rendered, error = yield
        if error is not None:
            raise error
        if rendered is None:
            raise RuntimeError("CList completed without a render result.")
        if self._list_context.count == 0:
            raise ValueError("CList requires at least one descendant CListItem.")

    template = """
      <c-if cond="ordered">
        <ol
          class="cui-list"
          c-bind="attrs"
          data-citry-ui-part="list"
          c-data-marker="marker"
          c-data-density="density"
          c-data-variant="variant"
          c-data-divided="divided"
          c-start="start"
          c-reversed="reversed"
          c-aria-label="label"
        ><c-slot required /></ol>
      </c-if>
      <c-else>
        <ul
          class="cui-list"
          c-bind="attrs"
          data-citry-ui-part="list"
          c-data-marker="marker"
          c-data-density="density"
          c-data-variant="variant"
          c-data-divided="divided"
          c-aria-label="label"
        ><c-slot required /></ul>
      </c-else>
    """

    css = """
      @layer citry-ui.theme {
        :where([data-citry-ui-part="list"]) {
          --_cui-list-gap: var(--cui-list-gap, 0.25rem);
          --_cui-list-padding: var(--cui-list-padding, 0.35rem);
          --_cui-list-item-padding: var(--cui-list-item-padding, 0.7rem);
          --_cui-list-radius: var(--cui-list-radius, 0.65rem);
          --_cui-list-foreground: var(--cui-list-foreground, CanvasText);
          --_cui-list-muted: var(--cui-list-muted, light-dark(#57534e, #d6d3d1));
          --_cui-list-background: var(--cui-list-background, transparent);
          --_cui-list-hover-background: var(--cui-list-hover-background, light-dark(#f5f5f4, #292524));
          --_cui-list-current-background: var(--cui-list-current-background, light-dark(#dbeafe, #1e3a5f));
          --_cui-list-divider-color: var(--cui-list-divider-color, light-dark(#e7e5e4, #44403c));
          --_cui-list-marker-color: var(--cui-list-marker-color, currentColor);
          --_cui-list-focus-ring: var(--cui-list-focus-ring, Highlight);
          display: grid;
          gap: var(--_cui-list-gap);
          margin: 0;
          padding: var(--_cui-list-padding);
          color: var(--_cui-list-foreground);
          background: var(--_cui-list-background);
          list-style-position: outside;
        }
        :where([data-citry-ui-part="list"][data-marker="none"]) {
          list-style: none;
        }
        :where([data-citry-ui-part="list"][data-marker="disc"]) {
          list-style-type: disc;
          padding-inline-start: calc(var(--_cui-list-padding) + 1.25rem);
        }
        :where([data-citry-ui-part="list"][data-marker="decimal"]) {
          list-style-type: decimal;
          padding-inline-start: calc(var(--_cui-list-padding) + 1.75rem);
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"])::marker {
          color: var(--_cui-list-marker-color);
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]) {
          min-inline-size: 0;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"]) {
          box-sizing: border-box;
          display: grid;
          grid-template-columns: minmax(0, 1fr);
          align-items: center;
          gap: 0.75rem;
          inline-size: 100%;
          min-inline-size: 0;
          padding: var(--_cui-list-item-padding);
          border: 0;
          border-radius: var(--_cui-list-radius);
          color: inherit;
          background: transparent;
          font: inherit;
          text-align: start;
          text-decoration: none;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"][data-cui-list-has-start]) {
          grid-template-columns: auto minmax(0, 1fr);
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"][data-cui-list-has-end]) {
          grid-template-columns: minmax(0, 1fr) auto;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"][data-cui-list-has-start][data-cui-list-has-end]) {
          grid-template-columns: auto minmax(0, 1fr) auto;
        }
        :where([data-citry-ui-part="list"][data-variant="surface"]
          > [data-citry-ui-part="list-item"] > [data-citry-ui-part="surface"]) {
          background: var(--_cui-list-hover-background);
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"][data-current]
          > [data-citry-ui-part="surface"]) {
          background: var(--_cui-list-current-background);
          font-weight: 650;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"][data-interactive]
          > [data-citry-ui-part="surface"]:hover) {
          background: var(--_cui-list-hover-background);
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"][data-disabled]) {
          opacity: 0.55;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"]:focus-visible) {
          outline: 3px solid var(--_cui-list-focus-ring);
          outline-offset: 2px;
        }
        :where([data-citry-ui-part="list"][data-divided]
          > [data-citry-ui-part="list-item"] + [data-citry-ui-part="list-item"]) {
          border-block-start: 1px solid var(--_cui-list-divider-color);
          padding-block-start: var(--_cui-list-gap);
        }
        :where([data-citry-ui-part="list"][data-density="compact"]) {
          --_cui-list-item-padding: 0.45rem 0.6rem;
          --_cui-list-gap: 0.1rem;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"] > [data-citry-ui-part="body"]) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"] > [data-citry-ui-part="body"]
          > [data-citry-ui-part="description"]) {
          display: block;
          margin-block-start: 0.15rem;
          color: var(--_cui-list-muted);
          font-size: 0.875em;
          font-weight: 400;
          overflow-wrap: anywhere;
        }
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"] > [data-citry-ui-part="start"]),
        :where([data-citry-ui-part="list"] > [data-citry-ui-part="list-item"]
          > [data-citry-ui-part="surface"] > [data-citry-ui-part="end"]) {
          min-inline-size: 0;
        }
      }
    """


class CListItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        href: str | None = None
        action: bool = False
        disabled: bool = False
        current: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        surface_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CListItemDefaultSlotData]
        start: SlotInput[CListItemStartSlotData] | None = None
        description: SlotInput[CListItemDescriptionSlotData] | None = None
        end: SlotInput[CListItemEndSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        context_value = self.inject(_LIST_CONTEXT_KEY, None)
        if context_value is None:
            raise ValueError("CListItem must be rendered inside CList.")
        context: _ListContext = context_value.context
        context.count += 1
        validate_boolean("CListItem", "action", kwargs.action)
        validate_boolean("CListItem", "disabled", kwargs.disabled)
        validate_boolean("CListItem", "current", kwargs.current)
        href = _plain("CListItem href", kwargs.href, optional=True)
        if href is not None and kwargs.action:
            raise ValueError("CListItem cannot set both href and action=True.")
        if kwargs.current and (href is None or kwargs.disabled):
            raise ValueError("CListItem current=True requires an enabled href.")
        interactive = (href is not None or bool(kwargs.action)) and not kwargs.disabled
        return {
            "href": href,
            "action": bool(kwargs.action),
            "disabled": bool(kwargs.disabled),
            "current": bool(kwargs.current),
            "interactive": interactive,
            "has_start": "start" in self.raw_slots,
            "has_description": "description" in self.raw_slots,
            "has_end": "end" in self.raw_slots,
            "attrs": merge_root_attrs(_attrs("CListItem", kwargs.attrs, _ITEM_OWNED), kwargs.class_, kwargs.style),
            "surface_attrs": _attrs("CListItem surface", kwargs.surface_attrs, _SURFACE_OWNED),
        }

    template = """
      <li
        class="cui-list-item"
        c-bind="attrs"
        data-citry-ui-part="list-item"
        c-data-current="current"
        c-data-disabled="disabled"
        c-data-interactive="interactive"
      >
        <c-if cond="href is not None and not disabled">
          <a
            c-bind="surface_attrs"
            data-citry-ui-part="surface"
            c-data-cui-list-has-start="has_start"
            c-data-cui-list-has-end="has_end"
            c-href="href"
            c-aria-current="'page' if current else None"
          >
            <c-if cond="has_start">
              <span data-citry-ui-part="start"><c-slot name="start" /></span>
            </c-if>
            <span data-citry-ui-part="body">
              <c-slot required />
              <c-if cond="has_description">
                <span data-citry-ui-part="description"><c-slot name="description" /></span>
              </c-if>
            </span>
            <c-if cond="has_end">
              <span data-citry-ui-part="end"><c-slot name="end" /></span>
            </c-if>
          </a>
        </c-if>
        <c-elif cond="action">
          <button
            c-bind="surface_attrs"
            data-citry-ui-part="surface"
            c-data-cui-list-has-start="has_start"
            c-data-cui-list-has-end="has_end"
            type="button"
            c-disabled="disabled"
          >
            <c-if cond="has_start">
              <span data-citry-ui-part="start"><c-slot name="start" /></span>
            </c-if>
            <span data-citry-ui-part="body">
              <c-slot required />
              <c-if cond="has_description">
                <span data-citry-ui-part="description"><c-slot name="description" /></span>
              </c-if>
            </span>
            <c-if cond="has_end">
              <span data-citry-ui-part="end"><c-slot name="end" /></span>
            </c-if>
          </button>
        </c-elif>
        <c-else>
          <div
            c-bind="surface_attrs"
            data-citry-ui-part="surface"
            c-data-cui-list-has-start="has_start"
            c-data-cui-list-has-end="has_end"
          >
            <c-if cond="has_start">
              <span data-citry-ui-part="start"><c-slot name="start" /></span>
            </c-if>
            <div data-citry-ui-part="body">
              <c-slot required />
              <c-if cond="has_description">
                <div data-citry-ui-part="description"><c-slot name="description" /></div>
              </c-if>
            </div>
            <c-if cond="has_end">
              <span data-citry-ui-part="end"><c-slot name="end" /></span>
            </c-if>
          </div>
        </c-else>
      </li>
    """


__all__ = [
    "CList",
    "CListDefaultSlotData",
    "CListDensity",
    "CListItem",
    "CListItemDefaultSlotData",
    "CListItemDescriptionSlotData",
    "CListItemEndSlotData",
    "CListItemStartSlotData",
    "CListMarker",
    "CListVariant",
]
