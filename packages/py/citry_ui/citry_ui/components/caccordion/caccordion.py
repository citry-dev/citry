"""Styled interactive Accordion component family."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any, Literal, TypedDict

from citry import CitryRender, LibraryComponent, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean
from citry_ui.components.cicon.cicon import _resolve_registered_icon

CAccordionVariant = Literal["outline", "soft", "separated", "plain"]
CAccordionSize = Literal["sm", "md", "lg"]
CAccordionIndicatorPos = Literal["start", "end"]
CAccordionHeadingLevel = Literal[2, 3, 4, 5, 6]


class CAccordionValueChangeDetail(TypedDict):
    value: str | list[str] | None
    previousValue: str | list[str] | None
    itemValue: str | None
    removedValues: list[str]
    expanded: bool
    source: Literal["activation", "removal"]


_VARIANTS = ("outline", "soft", "separated", "plain")
_SIZES = ("sm", "md", "lg")
_INDICATOR_POSITIONS = ("start", "end")
_HEADING_LEVELS = (2, 3, 4, 5, 6)
_ACCORDION_CONTEXT_KEY = "citry_ui_accordion"
_ACCORDION_ITEM_CONTEXT_KEY = "citry_ui_accordion_item"
_ACCORDION_PANEL_CONTEXT_KEY = "citry_ui_accordion_panel"
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
_ROOT_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-accordion-initialized",
        "data-citry-accordion-root",
        "data-citry-ui-part",
        "data-collapsible",
        "data-disabled",
        "data-indicator",
        "data-indicator-pos",
        "data-loop",
        "data-multiple",
        "data-size",
        "data-variant",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-accordion-item",
        "data-citry-accordion-item-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-state",
        "data-value",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
        "x-show",
    }
)
_HEADING_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-level",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
        "x-show",
    }
)
_TRIGGER_OWNED_ATTRS = frozenset(
    {
        "aria-controls",
        "aria-disabled",
        "aria-expanded",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "command",
        "commandfor",
        "data-citry-accordion-trigger",
        "data-citry-ui-part",
        "data-disabled",
        "data-state",
        "disabled",
        "hidden",
        "inert",
        "popover",
        "popovertarget",
        "popovertargetaction",
        "role",
        "tabindex",
        "type",
        "x-show",
    }
)
_PANEL_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "data-citry-accordion-panel",
        "data-citry-ui-part",
        "data-state",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "x-show",
    }
)
_ACTIONS_OWNED_ATTRS = frozenset(
    {
        "aria-atomic",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-live",
        "aria-roledescription",
        "contenteditable",
        "data-citry-ui-part",
        "role",
        "tabindex",
    }
)


class CAccordionDefaultSlotData:
    pass


class CAccordionItemTitleSlotData:
    pass


class CAccordionItemDefaultSlotData:
    pass


class CAccordionItemActionsSlotData:
    pass


@dataclass(slots=True)
class _AccordionItemRegistration:
    value: str
    disabled: bool
    render_id: str


@dataclass(slots=True)
class _AccordionRegistry:
    items: list[_AccordionItemRegistration] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _AccordionServerContext:
    registry: _AccordionRegistry
    group_id: str
    open_values: frozenset[str]
    heading_level: int
    region: bool
    group_disabled: bool
    indicator: bool


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CAccordion {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CAccordion could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain.replace("\r\n", "\n").replace("\r", "\n")


def _plain_required_string(component_name: str, input_name: str, value: object) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain is None:
        msg = f"{component_name} {input_name} must be a string."
        raise TypeError(msg)
    if not plain:
        msg = f"{component_name} {input_name} must be non-empty."
        raise ValueError(msg)
    if "\0" in plain:
        msg = f"{component_name} {input_name} cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_required_string("CAccordion", input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CAccordion {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _plain_id(value: object) -> str | None:
    plain = _plain_optional_string("id", value)
    if plain is None:
        return None
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CAccordion id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CAccordion id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _heading_level(value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, str) and raw.isdecimal():
        raw = int(raw)
    if isinstance(raw, bool) or raw not in _HEADING_LEVELS:
        msg = "CAccordion heading_level must be one of 2, 3, 4, 5, or 6."
        raise ValueError(msg)
    return int(raw)


def _plain_actions_label(value: object) -> str | None:
    plain = _plain_optional_string("actions_label", value)
    if plain is None:
        return None
    if "\0" in plain:
        msg = "CAccordionItem actions_label cannot contain U+0000."
        raise ValueError(msg)
    if not plain.strip():
        msg = "CAccordionItem actions_label must contain non-whitespace text."
        raise ValueError(msg)
    return plain


def _normalize_server_value(value: object, *, multiple: bool) -> tuple[str, ...]:
    if value is None:
        return ()
    if multiple:
        if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
            msg = "CAccordion value must be a sequence of strings or None in multiple mode."
            raise TypeError(msg)
        normalized = tuple(_plain_required_string("CAccordion", "value item", item) for item in value)
        if len(set(normalized)) != len(normalized):
            msg = "CAccordion multiple value cannot contain duplicates."
            raise ValueError(msg)
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, str):
        msg = "CAccordion value must be a string or None in single mode."
        raise TypeError(msg)
    return (_plain_required_string("CAccordion", "value", value),)


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CAccordionItem {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _validate_attrs(
    component_name: str,
    attrs: dict[str, object],
    owned: frozenset[str],
) -> None:
    reject_owned_attrs(attrs, owned, component_name)
    for key in attrs:
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{component_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if directive in owned:
            msg = f"{component_name} cannot use owned directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{component_name} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


def _value_token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:16]


def _server_value_fingerprint(values: tuple[str, ...], *, multiple: bool) -> str:
    payload = json.dumps(
        {"multiple": multiple, "value": list(values)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode()).hexdigest()


def _validate_registry(registry: _AccordionRegistry, open_values: tuple[str, ...]) -> None:
    values = [item.value for item in registry.items]
    if not values:
        msg = "CAccordion requires at least one direct CAccordionItem."
        raise ValueError(msg)
    if len(set(values)) != len(values):
        msg = "CAccordion requires every item value to be unique."
        raise ValueError(msg)
    unknown = [value for value in open_values if value not in values]
    if unknown:
        msg = f"CAccordion value contains unknown item value {unknown[0]!r}."
        raise ValueError(msg)


_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


class _DirectItemParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.active_render_id: str | None = None
        self.active_root_count = 0
        self.item_render_ids: list[str] = []
        self.invalid = False
        self.pending: list[str] = []

    def feed_text(self, value: str) -> None:
        self.pending.append(value)

    def flush(self) -> None:
        if not self.pending:
            return
        self.feed("".join(self.pending))
        self.pending.clear()

    def enter_item(self, render_id: str) -> None:
        self.flush()
        if self.depth != 0 or self.active_render_id is not None:
            self.invalid = True
        self.active_render_id = render_id
        self.active_root_count = 0

    def exit_item(self, render_id: str) -> None:
        self.flush()
        if self.depth != 0 or self.active_render_id != render_id or self.active_root_count != 1:
            self.invalid = True
        self.item_render_ids.append(render_id)
        self.active_render_id = None
        self.active_root_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if self.depth == 0:
            if self.active_render_id is None:
                self.invalid = True
            else:
                self.active_root_count += 1
                if tag != "div":
                    self.invalid = True
        if tag not in _VOID_ELEMENTS:
            self.depth += 1

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:  # noqa: ARG002
        if self.depth == 0:
            self.invalid = True
            return
        self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth == 0 and data.strip():
            self.invalid = True

    def handle_comment(self, data: str) -> None:  # noqa: ARG002
        if self.depth == 0:
            self.invalid = True

    def handle_decl(self, decl: str) -> None:  # noqa: ARG002
        if self.depth == 0:
            self.invalid = True


def _feed_item_output(
    parser: _DirectItemParser,
    part: object,
    expected_render_ids: frozenset[str],
) -> None:
    while hasattr(part, "region_id") and hasattr(part, "part"):
        part = part.part
    if isinstance(part, str):
        parser.feed_text(part)
        return
    if not isinstance(part, CitryRender):
        parser.invalid = True
        return

    render_id = part.frame.render_id
    is_item_root = part.is_component_root and render_id is not None and render_id in expected_render_ids
    if is_item_root and render_id is not None:
        parser.enter_item(render_id)
    for child in part.parts:
        _feed_item_output(parser, child, expected_render_ids)
    if is_item_root and render_id is not None:
        parser.exit_item(render_id)


def _validate_direct_item_output(result: CitryRender, registry: _AccordionRegistry) -> None:
    parser = _DirectItemParser()
    expected_render_ids = [item.render_id for item in registry.items]
    _feed_item_output(parser, result, frozenset(expected_render_ids))
    parser.flush()
    parser.close()
    if parser.invalid or parser.item_render_ids != expected_render_ids:
        msg = (
            "CAccordion default content may contain only direct CAccordionItem components, "
            "formatting whitespace, and transparent components that add no element."
        )
        raise ValueError(msg)


class CAccordion(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str | Sequence[str] | None = None
        multiple: bool = False
        collapsible: bool = True
        disabled: bool = False
        loop: bool = True
        variant: CAccordionVariant = "outline"
        size: CAccordionSize = "md"
        indicator: bool = True
        indicator_pos: CAccordionIndicatorPos = "end"
        heading_level: CAccordionHeadingLevel = 3
        region: bool = False
        id: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CAccordionDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        inside_item = self.inject(_ACCORDION_ITEM_CONTEXT_KEY, None)
        inside_panel = self.inject(_ACCORDION_PANEL_CONTEXT_KEY, None)
        if inside_item is not None and inside_panel is None:
            msg = "Nested CAccordion is allowed only inside a CAccordionItem panel."
            raise ValueError(msg)

        validate_boolean("CAccordion", "multiple", kwargs.multiple)
        validate_boolean("CAccordion", "collapsible", kwargs.collapsible)
        validate_boolean("CAccordion", "disabled", kwargs.disabled)
        validate_boolean("CAccordion", "loop", kwargs.loop)
        validate_boolean("CAccordion", "indicator", kwargs.indicator)
        validate_boolean("CAccordion", "region", kwargs.region)
        if kwargs.multiple and not kwargs.collapsible:
            msg = "CAccordion collapsible must remain true in multiple mode."
            raise ValueError(msg)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)
        indicator_pos = _plain_choice(
            "indicator_pos",
            kwargs.indicator_pos,
            _INDICATOR_POSITIONS,
        )
        heading_level = _heading_level(kwargs.heading_level)
        group_id = _plain_id(kwargs.id) or f"cui-accordion-{self.id}"
        open_values = _normalize_server_value(kwargs.value, multiple=bool(kwargs.multiple))
        # The template and browser initializer must consume the same copy even
        # when a caller supplies a mutable or side-effecting Sequence.
        self._accordion_open_values = open_values
        attrs = _copy_attrs("attrs", kwargs.attrs)
        _validate_attrs("CAccordion attrs", attrs, _ROOT_OWNED_ATTRS)

        form = self.inject(FORM_CONTEXT_KEY, None)
        effective_disabled = bool(kwargs.disabled) or bool(form.disabled if form is not None else False)
        registry = _AccordionRegistry()
        context = _AccordionServerContext(
            registry=registry,
            group_id=group_id,
            open_values=frozenset(open_values),
            heading_level=heading_level,
            region=bool(kwargs.region),
            group_disabled=effective_disabled,
            indicator=bool(kwargs.indicator),
        )
        self.unprovide(_ACCORDION_ITEM_CONTEXT_KEY)
        self.unprovide(_ACCORDION_PANEL_CONTEXT_KEY)
        self.provide(_ACCORDION_CONTEXT_KEY, context=context)
        return {
            "group_id": group_id,
            "multiple": bool(kwargs.multiple),
            "collapsible": bool(kwargs.collapsible),
            "disabled": effective_disabled,
            "loop": bool(kwargs.loop),
            "variant": variant,
            "size": size,
            "indicator": bool(kwargs.indicator),
            "indicator_pos": indicator_pos,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "registry": registry,
            "open_values": open_values,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        open_values = self._accordion_open_values
        return {
            "value": list(open_values) if kwargs.multiple else open_values[0] if open_values else None,
            "serverFingerprint": _server_value_fingerprint(
                open_values,
                multiple=bool(kwargs.multiple),
            ),
            "multiple": bool(kwargs.multiple),
            "collapsible": bool(kwargs.collapsible),
            "disabled": bool(kwargs.disabled),
            "loop": bool(kwargs.loop),
            "variant": _plain_choice("variant", kwargs.variant, _VARIANTS),
            "size": _plain_choice("size", kwargs.size, _SIZES),
            "indicator": bool(kwargs.indicator),
            "indicatorPosition": _plain_choice(
                "indicator_pos",
                kwargs.indicator_pos,
                _INDICATOR_POSITIONS,
            ),
        }

    template = """
      <div
        class="cui-accordion"
        c-id="group_id"
        c-data-multiple="multiple"
        c-data-collapsible="collapsible"
        c-data-disabled="disabled"
        c-data-loop="loop"
        c-data-variant="variant"
        c-data-size="size"
        c-data-indicator="indicator"
        c-data-indicator-pos="indicator_pos"
        c-bind="attrs"
        data-citry-accordion-root
        data-citry-ui-part="accordion"
      >
        <c-CInternalAccordionItems
          c-registry="registry"
          c-open_values="open_values"
        >
          <c-slot required />
        </c-CInternalAccordionItems>
      </div>
    """

    js = r"""
      $component({
        props: {
          value: {},
          onValueChange: {},
          collapsible: {},
          disabled: {},
          loop: {},
          variant: {},
          size: {},
          indicator: {},
          indicatorPosition: {},
        },
        init: ({ els, data, props, effect, inject, provide }) => {
          const root = els[0];
          const form = inject(Symbol.for("citry-ui:form"), null);
          const rootSelector = "[data-citry-accordion-root]";
          const itemSelector = "[data-citry-accordion-item]";
          const triggerSelector = "[data-citry-accordion-trigger]";
          const panelSelector = "[data-citry-accordion-panel]";
          const allowedValues = {
            variant: ["outline", "soft", "separated", "plain"],
            size: ["sm", "md", "lg"],
            indicatorPosition: ["start", "end"],
          };
          const invalidEpisodes = new Set();
          const registrations = new Map();
          const animations = new Map();
          let reconciliationTimer = null;
          const runtimeState = root.__citryUiAccordionRuntime ?? {
            value: null,
            itemOrder: [],
            focusedValue: null,
            serverFingerprint: null,
            reconciliations: 0,
          };
          root.__citryUiAccordionRuntime = runtimeState;
          const initialPublicValue = runtimeState.serverFingerprint === data.serverFingerprint
            ? runtimeState.value
            : data.value;
          let currentValue = data.multiple
            ? Array.isArray(initialPublicValue) ? [...initialPublicValue] : []
            : typeof initialPublicValue === "string" ? [initialPublicValue] : [];
          let itemOrder = Array.isArray(runtimeState.itemOrder)
            ? [...runtimeState.itemOrder]
            : [];
          let focusedValue = runtimeState.focusedValue;
          let controlled = false;
          let onValueChange = null;
          let configuration = {
            collapsible: data.collapsible,
            disabled: data.disabled,
            loop: data.loop,
            variant: data.variant,
            size: data.size,
            indicator: data.indicator,
            indicatorPosition: data.indicatorPosition,
          };

          const isOwned = (element) => element?.closest(rootSelector) === root;
          const orderedItems = () => Array.from(root.querySelectorAll(itemSelector))
            .filter(isOwned)
            .map((element) => registrations.get(element))
            .filter(Boolean);
          const itemForValue = (value, items = orderedItems()) => (
            items.find((item) => item.value === value)
          );
          const values = () => orderedItems().map((item) => item.value);
          const publicValue = (normalized) => data.multiple
            ? [...normalized]
            : normalized[0] ?? null;
          const normalizeCurrent = (value, itemValues = values()) => {
            const available = new Set(itemValues);
            const sequence = Array.isArray(value)
              ? value
              : typeof value === "string"
                ? [value]
                : [];
            if (data.multiple) {
              return itemValues.filter(
                (itemValue) => sequence.includes(itemValue) && available.has(itemValue),
              );
            }
            return sequence.length > 0 && available.has(sequence[0]) ? [sequence[0]] : [];
          };

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value, fallback, episode = name) => {
            if (invalidEpisodes.has(episode)) {
              return;
            }
            invalidEpisodes.add(episode);
            console.error(
              `[citry-ui] CAccordion ${name} received invalid client value `
                + `${describeValue(value)}; ${fallback}.`,
              root,
            );
          };
          const resolveBoolean = (name, fallback = data[name]) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return fallback;
          };
          const resolveChoice = (name, fallback = data[name]) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return fallback;
          };
          const resolveCallback = () => {
            const value = props.onValueChange;
            if (value === undefined || typeof value === "function") {
              invalidEpisodes.delete("onValueChange");
              return value ?? null;
            }
            reportInvalid("onValueChange", value, "ignoring the callback");
            return null;
          };
          const canonicalizeClientString = (value) => {
            if (typeof value !== "string" || value.includes("\0")) {
              return null;
            }
            return value.replace(/\r\n?/g, "\n");
          };
          const normalizeClientValue = (value, itemValues = values()) => {
            const available = new Set(itemValues);
            if (data.multiple) {
              if (value === null) {
                return [];
              }
              if (!Array.isArray(value)) {
                return null;
              }
              const canonical = value.map(canonicalizeClientString);
              if (
                canonical.some((item) => item === null)
                || new Set(canonical).size !== canonical.length
                || canonical.some((item) => !available.has(item))
              ) {
                return null;
              }
              return itemValues.filter((item) => canonical.includes(item));
            }
            if (value === null) {
              return [];
            }
            const canonical = canonicalizeClientString(value);
            return canonical !== null && available.has(canonical) ? [canonical] : null;
          };

          const durationMs = () => {
            if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
              return 0;
            }
            const raw = getComputedStyle(root).getPropertyValue("--_cui-accordion-duration").trim();
            if (raw.endsWith("ms")) {
              return Math.max(0, Number.parseFloat(raw));
            }
            if (raw.endsWith("s")) {
              return Math.max(0, Number.parseFloat(raw) * 1000);
            }
            return 0;
          };
          const cancelAnimation = (item) => {
            const animation = animations.get(item.root);
            if (!animation) {
              return;
            }
            const height = item.panel.getBoundingClientRect().height;
            animation.cancel();
            animations.delete(item.root);
            item.panel.style.blockSize = `${height}px`;
          };
          const settlePanel = (item, open) => {
            item.panel.style.removeProperty("block-size");
            item.panel.style.removeProperty("overflow");
            if (!open) {
              item.panel.hidden = true;
            }
          };
          const animatePanel = (item, open) => {
            cancelAnimation(item);
            const duration = durationMs();
            // A hidden panel has no measurable box, so opening starts at zero
            // before the panel is revealed long enough to measure its content.
            const wasHidden = item.panel.hidden;
            const start = wasHidden && open
              ? 0
              : item.panel.getBoundingClientRect().height;
            if (open) {
              item.panel.hidden = false;
              item.panel.inert = false;
              item.panel.removeAttribute("aria-hidden");
              if (wasHidden) {
                item.panel.style.blockSize = "auto";
              }
            } else {
              item.panel.inert = true;
              item.panel.setAttribute("aria-hidden", "true");
            }
            if (duration === 0 || typeof item.panel.animate !== "function") {
              settlePanel(item, open);
              return;
            }
            const end = open ? item.panel.scrollHeight : 0;
            item.panel.style.blockSize = `${start}px`;
            item.panel.style.overflow = "clip";
            const easing = getComputedStyle(root)
              .getPropertyValue("--_cui-accordion-easing")
              .trim() || "ease-out";
            const animation = item.panel.animate(
              [{ blockSize: `${start}px` }, { blockSize: `${end}px` }],
              { duration, easing },
            );
            animations.set(item.root, animation);
            animation.finished.then(() => {
              if (animations.get(item.root) !== animation) {
                return;
              }
              animations.delete(item.root);
              settlePanel(item, open);
            }).catch(() => {});
          };
          const nearestEnabled = (fromValue, items = orderedItems()) => {
            const enabled = items.filter((item) => !item.effectiveDisabled);
            if (enabled.length === 0) {
              return null;
            }
            const oldIndex = itemOrder.indexOf(fromValue);
            if (oldIndex < 0) {
              return enabled[0];
            }
            for (let offset = 0; offset <= items.length; offset += 1) {
              const afterValue = itemOrder[oldIndex + offset];
              const after = itemForValue(afterValue, items);
              if (after && !after.effectiveDisabled) {
                return after;
              }
              const beforeValue = itemOrder[oldIndex - offset - 1];
              const before = itemForValue(beforeValue, items);
              if (before && !before.effectiveDisabled) {
                return before;
              }
            }
            return enabled[0];
          };
          const applyConfiguration = () => {
            const requestedCollapsible = resolveBoolean("collapsible");
            configuration = {
              collapsible: data.multiple && !requestedCollapsible ? true : requestedCollapsible,
              disabled: Boolean(form?.disabled) || resolveBoolean("disabled"),
              loop: resolveBoolean("loop"),
              variant: resolveChoice("variant"),
              size: resolveChoice("size"),
              indicator: resolveBoolean("indicator"),
              indicatorPosition: resolveChoice("indicatorPosition"),
            };
            if (data.multiple && !requestedCollapsible) {
              reportInvalid(
                "collapsible",
                false,
                "multiple mode always remains collapsible",
                "collapsible:multiple",
              );
            } else {
              invalidEpisodes.delete("collapsible:multiple");
            }
            root.toggleAttribute("data-multiple", data.multiple);
            root.toggleAttribute("data-collapsible", configuration.collapsible);
            root.toggleAttribute("data-loop", configuration.loop);
            root.toggleAttribute("data-indicator", configuration.indicator);
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.dataset.indicatorPos = configuration.indicatorPosition;
          };
          const applyState = ({ animate = false, items = orderedItems() } = {}) => {
            if (items.length === 0) {
              return;
            }
            const itemValues = items.map((item) => item.value);
            const normalized = normalizeCurrent(currentValue, itemValues);
            currentValue = normalized;
            const open = new Set(normalized);
            const previouslyFocused = document.activeElement;
            let disabledFocusedValue = null;
            for (const item of items) {
              const localDisabled = configuration.disabled || item.ownDisabled;
              item.trigger.disabled = localDisabled;
              const nativeDisabled = item.trigger.matches(":disabled");
              item.effectiveDisabled = nativeDisabled;
              if (previouslyFocused === item.trigger && nativeDisabled) {
                disabledFocusedValue = item.value;
              }
            }
            const groupNativeDisabled = items.some(
              (item) => item.trigger.matches(":disabled") && !item.ownDisabled,
            );
            root.toggleAttribute("data-disabled", configuration.disabled || groupNativeDisabled);
            for (const item of items) {
              const expanded = open.has(item.value);
              const wasExpanded = item.trigger.getAttribute("aria-expanded") === "true";
              if (!expanded && wasExpanded && item.panel.contains(document.activeElement)) {
                item.trigger.focus({ preventScroll: true });
              }
              item.root.dataset.state = expanded ? "open" : "closed";
              item.trigger.dataset.state = expanded ? "open" : "closed";
              item.panel.dataset.state = expanded ? "open" : "closed";
              item.root.toggleAttribute("data-disabled", item.effectiveDisabled);
              item.trigger.toggleAttribute("data-disabled", item.effectiveDisabled);
              item.trigger.setAttribute("aria-expanded", expanded ? "true" : "false");
              const fixedOpen = !data.multiple && !configuration.collapsible && expanded;
              if (fixedOpen && !item.effectiveDisabled) {
                item.trigger.setAttribute("aria-disabled", "true");
              } else {
                item.trigger.removeAttribute("aria-disabled");
              }
              item.indicator.hidden = !configuration.indicator;
              if (animate && wasExpanded !== expanded) {
                animatePanel(item, expanded);
              } else {
                cancelAnimation(item);
                if (expanded) {
                  item.panel.hidden = false;
                  item.panel.inert = false;
                  item.panel.removeAttribute("aria-hidden");
                } else {
                  item.panel.inert = true;
                  item.panel.setAttribute("aria-hidden", "true");
                  item.panel.hidden = true;
                }
                settlePanel(item, expanded);
              }
            }
            if (disabledFocusedValue !== null) {
              nearestEnabled(disabledFocusedValue)?.trigger.focus({ preventScroll: true });
            }
            runtimeState.value = publicValue(currentValue);
            runtimeState.itemOrder = itemValues;
            runtimeState.focusedValue = focusedValue;
            runtimeState.serverFingerprint = data.serverFingerprint;
          };

          const callbackDetail = (next, previous, options) => ({
            value: publicValue(next),
            previousValue: publicValue(previous),
            itemValue: options.itemValue,
            removedValues: [...options.removedValues],
            expanded: options.expanded,
            source: options.source,
          });
          const commitRequest = (item) => {
            if (item.effectiveDisabled) {
              return;
            }
            const previous = [...currentValue];
            const isOpen = previous.includes(item.value);
            if (isOpen && !data.multiple && !configuration.collapsible) {
              return;
            }
            let next;
            const itemValues = values();
            if (data.multiple) {
              const requested = new Set(previous);
              if (isOpen) {
                requested.delete(item.value);
              } else {
                requested.add(item.value);
              }
              next = itemValues.filter((value) => requested.has(value));
            } else {
              next = isOpen ? [] : [item.value];
            }
            onValueChange?.(
              publicValue(next),
              callbackDetail(next, previous, {
                itemValue: item.value,
                removedValues: [],
                expanded: !isOpen,
                source: "activation",
              }),
            );
            if (!controlled) {
              currentValue = next;
              applyState({ animate: true });
            }
          };
          const readControlledValue = (itemValues = values()) => {
            const supplied = props.value;
            if (supplied === undefined) {
              controlled = false;
              invalidEpisodes.delete("value");
              return false;
            }
            if (itemValues.length === 0) {
              return false;
            }
            const normalized = normalizeClientValue(supplied, itemValues);
            if (normalized === null) {
              reportInvalid("value", supplied, "retaining the current valid state");
              return false;
            }
            invalidEpisodes.delete("value");
            controlled = true;
            currentValue = normalized;
            return true;
          };
          const reconcileStructure = () => {
            applyConfiguration();
            const items = orderedItems();
            const itemValues = items.map((item) => item.value);
            const seenValues = new Set();
            const duplicate = items.find((item) => {
              if (seenValues.has(item.value)) {
                return true;
              }
              seenValues.add(item.value);
              return false;
            });
            if (duplicate) {
              reportInvalid("items", duplicate.value, "item values must remain unique");
              return;
            }
            invalidEpisodes.delete("items");
            readControlledValue(itemValues);
            const available = new Set(itemValues);
            const previous = [...currentValue];
            const removedValues = previous.filter((value) => !available.has(value));
            let next = previous.filter((value) => available.has(value));
            if (!data.multiple && !configuration.collapsible && removedValues.length > 0 && next.length === 0) {
              const fallback = nearestEnabled(removedValues[0], items);
              next = fallback ? [fallback.value] : [];
            }
            if (removedValues.length > 0) {
              onValueChange?.(
                publicValue(next),
                callbackDetail(next, previous, {
                  itemValue: null,
                  removedValues,
                  expanded: false,
                  source: "removal",
                }),
              );
              currentValue = next;
              const fallbackFocus = focusedValue && removedValues.includes(focusedValue)
                ? nearestEnabled(focusedValue, items)
                : null;
              applyState({ items });
              if (fallbackFocus && (
                document.activeElement === document.body
                || document.activeElement === document.documentElement
              )) {
                fallbackFocus.trigger.focus({ preventScroll: true });
              }
            } else {
              currentValue = itemValues.filter((value) => next.includes(value));
              applyState({ items });
            }
            itemOrder = itemValues;
            runtimeState.reconciliations = (runtimeState.reconciliations ?? 0) + 1;
            root.setAttribute("data-citry-accordion-initialized", "");
          };
          const scheduleReconcile = () => {
            // Parent and item initializers all run in one batch. One pending
            // task absorbs their register and disabled-state updates.
            if (reconciliationTimer !== null) {
              return;
            }
            reconciliationTimer = setTimeout(() => {
              reconciliationTimer = null;
              reconcileStructure();
            }, 0);
          };
          const context = {
            registerItem(item) {
              registrations.set(item.root, item);
              scheduleReconcile();
              return () => {
                if (registrations.get(item.root) !== item) {
                  return;
                }
                registrations.delete(item.root);
                scheduleReconcile();
              };
            },
            updateItem(item, disabled) {
              if (registrations.get(item.root) !== item) {
                return;
              }
              item.ownDisabled = disabled;
              scheduleReconcile();
            },
          };
          provide(Symbol.for("citry-ui:accordion"), context);

          const onClick = (event) => {
            const trigger = event.target.closest?.(triggerSelector);
            if (!isOwned(trigger)) {
              return;
            }
            const itemRoot = trigger.closest(itemSelector);
            const item = registrations.get(itemRoot);
            if (item && item.trigger === trigger) {
              commitRequest(item);
            }
          };
          const onKeydown = (event) => {
            const trigger = event.target.closest?.(triggerSelector);
            if (!isOwned(trigger)) {
              return;
            }
            const item = registrations.get(trigger.closest(itemSelector));
            if (!item || item.effectiveDisabled) {
              return;
            }
            const enabled = orderedItems().filter((candidate) => !candidate.effectiveDisabled);
            const index = enabled.indexOf(item);
            if (index < 0) {
              return;
            }
            let nextIndex = null;
            if (event.key === "ArrowDown") {
              nextIndex = index + 1;
            } else if (event.key === "ArrowUp") {
              nextIndex = index - 1;
            } else if (event.key === "Home") {
              nextIndex = 0;
            } else if (event.key === "End") {
              nextIndex = enabled.length - 1;
            } else {
              return;
            }
            event.preventDefault();
            if (configuration.loop) {
              nextIndex = (nextIndex + enabled.length) % enabled.length;
            } else {
              nextIndex = Math.max(0, Math.min(enabled.length - 1, nextIndex));
            }
            enabled[nextIndex].trigger.focus();
          };
          const onFocusIn = (event) => {
            const item = orderedItems().find((candidate) => candidate.root.contains(event.target));
            if (!item) {
              return;
            }
            // The outer item remains the focus owner when focus enters one of
            // its actions, panel controls, or a nested Accordion.
            focusedValue = item.value;
            runtimeState.focusedValue = focusedValue;
          };

          // Capture keeps group behavior alive when a trusted descendant
          // listener stops the same event during its target or bubble phase.
          root.addEventListener("click", onClick, true);
          root.addEventListener("keydown", onKeydown, true);
          root.addEventListener("focusin", onFocusIn, true);
          effect(() => {
            applyConfiguration();
            onValueChange = resolveCallback();
            applyState();
          });
          effect(() => {
            if (readControlledValue()) {
              applyState({ animate: true });
            }
          });

          const ancestorFieldsets = [];
          for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
            if (ancestor.matches("fieldset")) {
              ancestorFieldsets.push(ancestor);
            }
          }
          const fieldsetObserver = ancestorFieldsets.length === 0
            ? null
            : new MutationObserver(() => applyState());
          ancestorFieldsets.forEach((fieldset) => {
            // Direct legend order changes the native disabled exception even
            // when the fieldset's own disabled attribute does not change.
            fieldsetObserver?.observe(fieldset, {
              attributes: true,
              attributeFilter: ["disabled"],
              childList: true,
            });
          });
          return () => {
            runtimeState.value = publicValue(currentValue);
            runtimeState.itemOrder = values();
            runtimeState.focusedValue = focusedValue;
            runtimeState.serverFingerprint = data.serverFingerprint;
            fieldsetObserver?.disconnect();
            root.removeEventListener("click", onClick, true);
            root.removeEventListener("keydown", onKeydown, true);
            root.removeEventListener("focusin", onFocusIn, true);
            animations.forEach((animation) => animation.cancel());
            animations.clear();
            if (reconciliationTimer !== null) {
              clearTimeout(reconciliationTimer);
              reconciliationTimer = null;
            }
            registrations.clear();
            root.removeAttribute("data-citry-accordion-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


class CAccordionItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        actions_label: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        heading_attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        panel_attrs: Mapping[str, object] | None = None
        actions_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CAccordionItemTitleSlotData]
        default: SlotInput[CAccordionItemDefaultSlotData]
        actions: SlotInput[CAccordionItemActionsSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        provided = self.inject(_ACCORDION_CONTEXT_KEY, None)
        if provided is None:
            msg = "CAccordionItem must be rendered as a direct child of CAccordion."
            raise ValueError(msg)
        context: _AccordionServerContext = provided.context
        value = _plain_required_string("CAccordionItem", "value", kwargs.value)
        validate_boolean("CAccordionItem", "disabled", kwargs.disabled)
        actions_label = _plain_actions_label(kwargs.actions_label)
        has_actions = "actions" in self.raw_slots
        if actions_label is not None and not has_actions:
            msg = "CAccordionItem actions_label requires the actions slot."
            raise ValueError(msg)

        attrs = _copy_attrs("attrs", kwargs.attrs)
        heading_attrs = _copy_attrs("heading_attrs", kwargs.heading_attrs)
        trigger_attrs = _copy_attrs("trigger_attrs", kwargs.trigger_attrs)
        panel_attrs = _copy_attrs("panel_attrs", kwargs.panel_attrs)
        actions_attrs = _copy_attrs("actions_attrs", kwargs.actions_attrs)
        _validate_attrs("CAccordionItem attrs", attrs, _ITEM_OWNED_ATTRS)
        _validate_attrs("CAccordionItem heading_attrs", heading_attrs, _HEADING_OWNED_ATTRS)
        _validate_attrs("CAccordionItem trigger_attrs", trigger_attrs, _TRIGGER_OWNED_ATTRS)
        _validate_attrs("CAccordionItem panel_attrs", panel_attrs, _PANEL_OWNED_ATTRS)
        _validate_attrs("CAccordionItem actions_attrs", actions_attrs, _ACTIONS_OWNED_ATTRS)
        if actions_attrs and not has_actions:
            msg = "CAccordionItem actions_attrs requires the actions slot."
            raise ValueError(msg)

        context.registry.items.append(
            _AccordionItemRegistration(
                value=value,
                disabled=bool(kwargs.disabled),
                render_id=self.id,
            ),
        )
        token = _value_token(value)
        trigger_id = f"{context.group_id}-trigger-{token}"
        panel_id = f"{context.group_id}-panel-{token}"
        expanded = value in context.open_values
        disabled = context.group_disabled or bool(kwargs.disabled)
        indicator = _resolve_registered_icon("chevron-down", "CAccordion indicator")
        self.unprovide(_ACCORDION_CONTEXT_KEY)
        self.provide(_ACCORDION_ITEM_CONTEXT_KEY, value=value)
        return {
            "value": value,
            "expanded": expanded,
            "disabled": disabled,
            "own_disabled": bool(kwargs.disabled),
            "heading_tag": f"h{context.heading_level}",
            "trigger_id": trigger_id,
            "panel_id": panel_id,
            "region": context.region,
            "indicator_visible": context.indicator,
            "indicator": indicator,
            "actions_label": actions_label,
            "has_actions": has_actions,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "heading_attrs": heading_attrs,
            "trigger_attrs": trigger_attrs,
            "panel_attrs": panel_attrs,
            "actions_attrs": actions_attrs,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "value": _plain_required_string("CAccordionItem", "value", kwargs.value),
            "disabled": bool(kwargs.disabled),
        }

    template = """
      <div
        class="cui-accordion__item"
        #c-key="value"
        c-data-value="value"
        c-data-state="'open' if expanded else 'closed'"
        c-data-disabled="disabled"
        c-bind="attrs"
        data-citry-accordion-item
        data-citry-ui-part="accordion-item"
      >
        <div
          class="cui-accordion__header"
          data-citry-ui-part="accordion-header"
        >
          <c-element
            c-is="heading_tag"
            class="cui-accordion__heading"
            c-bind="heading_attrs"
            data-citry-ui-part="accordion-heading"
          >
            <button
              class="cui-accordion__trigger"
              type="button"
              c-id="trigger_id"
              c-disabled="disabled"
              c-aria-expanded="'true' if expanded else 'false'"
              c-aria-controls="panel_id"
              c-data-state="'open' if expanded else 'closed'"
              c-data-disabled="disabled"
              c-bind="trigger_attrs"
              data-citry-accordion-trigger
              data-citry-ui-part="accordion-trigger"
            >
              <span
                class="cui-accordion__title"
                data-citry-ui-part="accordion-title"
              >
                <c-slot name="title" required />
              </span>
              <span
                class="cui-accordion__indicator"
                c-hidden="not indicator_visible"
                aria-hidden="true"
                data-citry-ui-part="accordion-indicator"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  focusable="false"
                  aria-hidden="true"
                >
                  {{ indicator.markup }}
                </svg>
              </span>
            </button>
          </c-element>
          <c-if cond="has_actions">
            <div
              class="cui-accordion__actions"
              c-role="'group' if actions_label is not None else None"
              c-aria-label="actions_label"
              c-bind="actions_attrs"
              data-citry-ui-part="accordion-actions"
            >
              <c-slot name="actions" />
            </div>
          </c-if>
        </div>
        <div
          class="cui-accordion__panel"
          c-id="panel_id"
          c-role="'region' if region else None"
          c-aria-labelledby="trigger_id if region else None"
          c-aria-hidden="None if expanded else 'true'"
          c-hidden="not expanded"
          c-inert="not expanded"
          c-data-state="'open' if expanded else 'closed'"
          c-bind="panel_attrs"
          data-citry-accordion-panel
          data-citry-ui-part="accordion-panel"
        >
          <div
            class="cui-accordion__body"
            data-citry-ui-part="accordion-body"
          >
            <c-CInternalAccordionPanelContent>
              <c-slot required />
            </c-CInternalAccordionPanelContent>
          </div>
        </div>
      </div>
    """

    js = """
      $component({
        props: {
          disabled: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const context = inject(Symbol.for("citry-ui:accordion"), null);
          if (!context) {
            console.error(
              "[citry-ui] CAccordionItem requires the nearest CAccordion client context.",
              root,
            );
            return;
          }
          const direct = (selector) => root.querySelector(`:scope > ${selector}`);
          const header = direct('[data-citry-ui-part="accordion-header"]');
          const trigger = header?.querySelector(
            ':scope > [data-citry-ui-part="accordion-heading"] '
              + '> [data-citry-accordion-trigger]',
          );
          const panel = direct("[data-citry-accordion-panel]");
          const indicator = trigger?.querySelector(':scope > [data-citry-ui-part="accordion-indicator"]');
          if (!trigger || !panel || !indicator) {
            console.error("[citry-ui] CAccordionItem could not resolve its owned anatomy.", root);
            return;
          }
          const invalidEpisodes = new Set();
          const item = {
            root,
            trigger,
            panel,
            indicator,
            value: data.value,
            ownDisabled: data.disabled,
            effectiveDisabled: trigger.matches(":disabled"),
          };
          const unregister = context.registerItem(item);
          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          effect(() => {
            const value = props.disabled === undefined ? data.disabled : props.disabled;
            if (typeof value === "boolean") {
              invalidEpisodes.delete("disabled");
              context.updateItem(item, value);
              return;
            }
            if (!invalidEpisodes.has("disabled")) {
              invalidEpisodes.add("disabled");
              console.error(
                `[citry-ui] CAccordionItem disabled received invalid client value `
                  + `${describeValue(value)}; using the server-rendered fallback.`,
                root,
              );
            }
            context.updateItem(item, data.disabled);
          });
          root.setAttribute("data-citry-accordion-item-initialized", "");
          return () => {
            unregister();
            root.removeAttribute("data-citry-accordion-item-initialized");
          };
        },
      });
    """


class CInternalAccordionItems(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        registry: _AccordionRegistry
        open_values: tuple[str, ...]

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CAccordionDefaultSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            msg = "CAccordion item collection completed without a render result."
            raise RuntimeError(msg)
        _validate_registry(self.kwargs.registry, self.kwargs.open_values)
        _validate_direct_item_output(result, self.kwargs.registry)

    template = """
      <c-slot required />
    """


class CInternalAccordionPanelContent(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CAccordionItemDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        self.provide(_ACCORDION_PANEL_CONTEXT_KEY)
        return {}

    template = """
      <c-slot required />
    """


__all__ = [
    "CAccordion",
    "CAccordionDefaultSlotData",
    "CAccordionHeadingLevel",
    "CAccordionIndicatorPos",
    "CAccordionItem",
    "CAccordionItemActionsSlotData",
    "CAccordionItemDefaultSlotData",
    "CAccordionItemTitleSlotData",
    "CAccordionSize",
    "CAccordionValueChangeDetail",
    "CAccordionVariant",
]
