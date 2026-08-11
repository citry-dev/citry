"""Styled standalone Disclosure component."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, ClassVar, Literal, TypedDict

from citry import CitryRender, LibraryComponent, SlotInput, const_value
from citry_ui.components._anchored_layer import (
    ANCHORED_LAYER_RUNTIME_DEPENDENCY,
    ANCHORED_LAYER_RUNTIME_JS,
)
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FORM_CONTEXT_KEY
from citry_ui.components._validation import reject_owned_attrs, validate_boolean
from citry_ui.components.cicon.cicon import _resolve_registered_icon

CDisclosureVariant = Literal["outline", "soft", "plain"]
CDisclosureSize = Literal["sm", "md", "lg"]
CDisclosureIndicatorPos = Literal["start", "end"]
CDisclosureHeadingLevel = Literal[2, 3, 4, 5, 6]


class CDisclosureOpenChangeDetail(TypedDict):
    open: bool
    previousOpen: bool
    source: Literal["activation"]
    controlled: bool


class CDisclosureTitleSlotData:
    pass


class CDisclosureDefaultSlotData:
    pass


class CDisclosureActionsSlotData:
    pass


_VARIANTS = ("outline", "soft", "plain")
_SIZES = ("sm", "md", "lg")
_INDICATOR_POSITIONS = ("start", "end")
_HEADING_LEVELS = (2, 3, 4, 5, 6)
_DISCLOSURE_CONTEXT_KEY = "citry_ui_disclosure"
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
        "id",
        "is",
        "role",
        "tabindex",
        "contenteditable",
        "inert",
        "popover",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-description",
        "aria-describedby",
        "aria-details",
        "aria-roledescription",
        "aria-live",
        "aria-atomic",
        "data-citry-ui-part",
        "data-citry-disclosure-root",
        "data-citry-disclosure-initialized",
        "data-variant",
        "data-size",
        "data-state",
        "data-disabled",
        "data-indicator",
        "data-indicator-pos",
    }
)
_HEADING_OWNED_ATTRS = frozenset(
    {
        "is",
        "role",
        "aria-level",
        "tabindex",
        "contenteditable",
        "hidden",
        "inert",
        "popover",
        "x-show",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-description",
        "aria-describedby",
        "aria-details",
        "aria-roledescription",
        "data-citry-ui-part",
    }
)
_TRIGGER_OWNED_ATTRS = frozenset(
    {
        "id",
        "is",
        "type",
        "disabled",
        "role",
        "tabindex",
        "hidden",
        "inert",
        "popover",
        "x-show",
        "command",
        "commandfor",
        "popovertarget",
        "popovertargetaction",
        "aria-controls",
        "aria-disabled",
        "aria-expanded",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "aria-haspopup",
        "aria-pressed",
        "aria-selected",
        "aria-checked",
        "aria-current",
        "aria-activedescendant",
        "aria-autocomplete",
        "aria-multiline",
        "aria-orientation",
        "aria-readonly",
        "aria-required",
        "aria-valuemax",
        "aria-valuemin",
        "aria-valuenow",
        "aria-valuetext",
        "aria-modal",
        "aria-level",
        "aria-posinset",
        "aria-setsize",
        "data-citry-ui-part",
        "data-citry-disclosure-trigger",
        "data-state",
        "data-disabled",
    }
)
_PANEL_OWNED_ATTRS = frozenset(
    {
        "id",
        "is",
        "role",
        "hidden",
        "inert",
        "popover",
        "x-show",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "data-citry-ui-part",
        "data-citry-disclosure-panel",
        "data-state",
    }
)
_ACTIONS_OWNED_ATTRS = frozenset(
    {
        "is",
        "role",
        "tabindex",
        "contenteditable",
        "hidden",
        "inert",
        "popover",
        "x-show",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-description",
        "aria-describedby",
        "aria-details",
        "aria-roledescription",
        "aria-live",
        "aria-atomic",
        "data-citry-ui-part",
    }
)
_TITLE_HTML_ELEMENTS = frozenset(
    {
        "abbr",
        "b",
        "bdi",
        "bdo",
        "br",
        "cite",
        "code",
        "data",
        "del",
        "dfn",
        "em",
        "i",
        "img",
        "ins",
        "kbd",
        "mark",
        "picture",
        "q",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "small",
        "source",
        "span",
        "strong",
        "sub",
        "sup",
        "svg",
        "time",
        "u",
        "var",
        "wbr",
    }
)
_TITLE_SVG_ELEMENTS = frozenset({"svg", "g", "path", "polyline", "line", "circle", "rect", "ellipse", "polygon"})
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
_TITLE_REJECTED_ATTRS = frozenset(
    {
        "role",
        "tabindex",
        "contenteditable",
        "autofocus",
        "href",
        "xlink:href",
        "controls",
        "usemap",
        "form",
        "popover",
        "is",
        "hidden",
        "inert",
        "focusable",
    }
)
_ANCHORED_PARTS = frozenset({"popover", "tooltip", "menu", "popup", "hover-card"})


def _plain_optional_string(input_name: str, value: object) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CDisclosure {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"CDisclosure could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain.replace("\r\n", "\n").replace("\r", "\n")


def _plain_choice(input_name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain_optional_string(input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"CDisclosure {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _plain_id(value: object) -> str | None:
    plain = _plain_optional_string("id", value)
    if plain is None:
        return None
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CDisclosure id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CDisclosure id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _heading_level(value: object) -> int:
    raw = const_value(value)
    if isinstance(raw, str) and raw.isdecimal():
        raw = int(raw)
    if isinstance(raw, bool) or raw not in _HEADING_LEVELS:
        msg = "CDisclosure heading_level must be one of 2, 3, 4, 5, or 6."
        raise ValueError(msg)
    return int(raw)


def _actions_label(value: object) -> str | None:
    plain = _plain_optional_string("actions_label", value)
    if plain is None:
        return None
    if "\0" in plain:
        raise ValueError("CDisclosure actions_label cannot contain U+0000.")
    if not plain.strip():
        raise ValueError("CDisclosure actions_label must contain non-whitespace text.")
    return plain


def _copy_attrs(input_name: str, attrs: Mapping[str, object] | None) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"CDisclosure {input_name} must be a mapping or None, got {attrs!r}."
        raise TypeError(msg)
    return dict(attrs)


def _dynamic_target(attribute: str) -> str | None:
    normalized = attribute.casefold()
    if normalized.startswith("x-bind:"):
        return normalized.removeprefix("x-bind:").split(".", 1)[0]
    if normalized.startswith((":", ".")):
        return normalized[1:].split(".", 1)[0]
    return None


def _validate_attrs(input_name: str, attrs: dict[str, object], owned: frozenset[str]) -> None:
    owner = f"CDisclosure {input_name}"
    reject_owned_attrs(attrs, owned, owner)
    for key in attrs:
        if not isinstance(key, str):
            msg = f"{owner} requires string keys, got {key!r}."
            raise TypeError(msg)
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{owner} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{owner} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if directive in owned:
            msg = f"{owner} cannot use owned directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{owner} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


def _title_attribute_problem(tag: str, attrs: list[tuple[str, str | None]]) -> str | None:
    values = dict(attrs)
    if tag == "img" and ("alt" not in values or values["alt"] not in {None, ""}):
        return '<img> requires alt=""'
    if tag == "svg" and (values.get("aria-hidden") != "true" or values.get("focusable") != "false"):
        return '<svg> requires aria-hidden="true" and focusable="false"'
    for name, value in attrs:
        normalized = name.casefold()
        if tag == "svg" and normalized == "aria-hidden" and value == "true":
            continue
        if tag == "svg" and normalized == "focusable" and value == "false":
            continue
        if normalized in _TITLE_REJECTED_ATTRS or normalized.startswith("aria-"):
            return f"<{tag}> cannot use {name!r}"
        if normalized.startswith(("on", "@", "x-on:")):
            return f"<{tag}> cannot use event attribute {name!r}"
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            return f"<{tag}> cannot use ownership directive {name!r}"
        target = _dynamic_target(normalized)
        if target is not None and (target in _TITLE_REJECTED_ATTRS or target.startswith("aria-")):
            return f"<{tag}> cannot dynamically bind {target!r}"
    return None


class _TitleOutputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.problem: str | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent_svg = self.stack[-1][1] if self.stack else False
        allowed = _TITLE_SVG_ELEMENTS if parent_svg else _TITLE_HTML_ELEMENTS
        if self.problem is None and tag not in allowed:
            self.problem = f"unsupported <{tag}> element"
        if self.problem is None:
            self.problem = _title_attribute_problem(tag, attrs)
        in_svg = parent_svg or tag == "svg"
        if tag not in _VOID_ELEMENTS:
            self.stack.append((tag, in_svg))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in _VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:  # noqa: ARG002
        if self.stack:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1][1]:
            self.text.append(data)


class _ContentOutputParser(HTMLParser):
    def __init__(self, *, actions: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.actions = actions
        self.problem: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.problem is not None:
            return
        values = dict(attrs)
        if tag == "dialog":
            self.problem = "native dialog descendants are not accepted"
            return
        if "-" in tag:
            self.problem = f"unresolved custom element <{tag}> is not accepted"
            return
        if "is" in values:
            self.problem = "customized built-ins using 'is' are not accepted"
            return
        if "popover" in values and not (
            values.get("popover") == "manual" and values.get("data-citry-ui-part") in _ANCHORED_PARTS
        ):
            self.problem = "raw or unrecognized native popovers are not accepted"
            return
        if self.actions and values.get("data-citry-ui-part") in {"disclosure", "accordion"}:
            self.problem = "nested Disclosure or Accordion roots are allowed only in panel content"

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


def _serialized(result: CitryRender, owner: str) -> str:
    try:
        return result.serialize(deps_strategy="ignore")
    except Exception as error:  # pragma: no cover - defensive lifecycle boundary
        msg = f"{owner} could not inspect its completed rendered output."
        raise RuntimeError(msg) from error


def _validate_title_output(result: CitryRender) -> None:
    parser = _TitleOutputParser()
    parser.feed(_serialized(result, "CDisclosure title"))
    parser.close()
    if parser.problem is not None:
        msg = f"CDisclosure title accepts noninteractive phrasing content only: {parser.problem}."
        raise ValueError(msg)
    if not "".join(parser.text).strip(" \t\n\f\r"):
        raise ValueError("CDisclosure title must contain nonempty textual content.")


def _validate_content_output(result: CitryRender, *, actions: bool) -> None:
    parser = _ContentOutputParser(actions=actions)
    parser.feed(_serialized(result, "CDisclosure actions" if actions else "CDisclosure panel"))
    parser.close()
    if parser.problem is not None:
        destination = "actions" if actions else "panel"
        raise ValueError(f"CDisclosure {destination} content is invalid: {parser.problem}.")


class CDisclosure(LibraryComponent):
    class Dependencies:
        js: ClassVar = [ANCHORED_LAYER_RUNTIME_DEPENDENCY]

    @dataclass(slots=True)
    class Kwargs:
        open: bool = False
        disabled: bool = False
        variant: CDisclosureVariant = "outline"
        size: CDisclosureSize = "md"
        indicator: bool = True
        indicator_pos: CDisclosureIndicatorPos = "end"
        heading_level: CDisclosureHeadingLevel = 3
        region: bool = False
        actions_label: str | None = None
        id: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        heading_attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        panel_attrs: Mapping[str, object] | None = None
        actions_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        title: SlotInput[CDisclosureTitleSlotData]
        default: SlotInput[CDisclosureDefaultSlotData]
        actions: SlotInput[CDisclosureActionsSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_disclosure_snapshot", None)
        if cached is not None:
            return cached
        if self.inject(_DISCLOSURE_CONTEXT_KEY, None) is not None:
            msg = "Nested CDisclosure is allowed only inside a CDisclosure panel."
            raise ValueError(msg)
        inside_accordion_item = self.inject(_ACCORDION_ITEM_CONTEXT_KEY, None)
        inside_accordion_panel = self.inject(_ACCORDION_PANEL_CONTEXT_KEY, None)
        if inside_accordion_item is not None and inside_accordion_panel is None:
            msg = "Nested CDisclosure is allowed only inside an Accordion item panel."
            raise ValueError(msg)

        validate_boolean("CDisclosure", "open", kwargs.open)
        validate_boolean("CDisclosure", "disabled", kwargs.disabled)
        validate_boolean("CDisclosure", "indicator", kwargs.indicator)
        validate_boolean("CDisclosure", "region", kwargs.region)
        variant = _plain_choice("variant", kwargs.variant, _VARIANTS)
        size = _plain_choice("size", kwargs.size, _SIZES)
        indicator_pos = _plain_choice(
            "indicator_pos",
            kwargs.indicator_pos,
            _INDICATOR_POSITIONS,
        )
        heading_level = _heading_level(kwargs.heading_level)
        actions_label = _actions_label(kwargs.actions_label)
        has_actions = "actions" in self.raw_slots
        if actions_label is not None and not has_actions:
            raise ValueError("CDisclosure actions_label requires the actions slot.")

        attrs = _copy_attrs("attrs", kwargs.attrs)
        heading_attrs = _copy_attrs("heading_attrs", kwargs.heading_attrs)
        trigger_attrs = _copy_attrs("trigger_attrs", kwargs.trigger_attrs)
        panel_attrs = _copy_attrs("panel_attrs", kwargs.panel_attrs)
        actions_attrs = _copy_attrs("actions_attrs", kwargs.actions_attrs)
        _validate_attrs("attrs", attrs, _ROOT_OWNED_ATTRS)
        _validate_attrs("heading_attrs", heading_attrs, _HEADING_OWNED_ATTRS)
        _validate_attrs("trigger_attrs", trigger_attrs, _TRIGGER_OWNED_ATTRS)
        _validate_attrs("panel_attrs", panel_attrs, _PANEL_OWNED_ATTRS)
        _validate_attrs("actions_attrs", actions_attrs, _ACTIONS_OWNED_ATTRS)
        if actions_attrs and not has_actions:
            raise ValueError("CDisclosure actions_attrs requires the actions slot.")

        root_id = _plain_id(kwargs.id) or f"cui-disclosure-{self.id}"
        trigger_id = f"{root_id}-trigger"
        panel_id = f"{root_id}-panel"
        form = self.inject(FORM_CONTEXT_KEY, None)
        disabled = bool(kwargs.disabled) or bool(form.disabled if form is not None else False)
        self.unprovide(_DISCLOSURE_CONTEXT_KEY)
        self.provide(_DISCLOSURE_CONTEXT_KEY)
        snapshot = {
            "root_id": root_id,
            "trigger_id": trigger_id,
            "panel_id": panel_id,
            "open": bool(kwargs.open),
            "disabled": disabled,
            "own_disabled": bool(kwargs.disabled),
            "variant": variant,
            "size": size,
            "indicator": bool(kwargs.indicator),
            "indicator_pos": indicator_pos,
            "heading_tag": f"h{heading_level}",
            "region": bool(kwargs.region),
            "actions_label": actions_label,
            "has_actions": has_actions,
            "icon": _resolve_registered_icon("chevron-down", "CDisclosure indicator"),
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "heading_attrs": heading_attrs,
            "trigger_attrs": trigger_attrs,
            "panel_attrs": panel_attrs,
            "actions_attrs": actions_attrs,
        }
        self._cui_disclosure_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "open": snapshot["open"],
            "serverFingerprint": "open" if snapshot["open"] else "closed",
            "disabled": snapshot["own_disabled"],
            "variant": snapshot["variant"],
            "size": snapshot["size"],
            "indicator": snapshot["indicator"],
            "indicatorPosition": snapshot["indicator_pos"],
            "rootId": snapshot["root_id"],
            "triggerId": snapshot["trigger_id"],
            "panelId": snapshot["panel_id"],
            "headingTag": snapshot["heading_tag"],
            "region": snapshot["region"],
            "hasActions": snapshot["has_actions"],
            "actionsLabel": snapshot["actions_label"],
        }

    template = """
      <div
        class="cui-disclosure"
        c-id="root_id"
        c-data-variant="variant"
        c-data-size="size"
        c-data-state="'open' if open else 'closed'"
        c-data-disabled="disabled"
        c-data-indicator="indicator"
        c-data-indicator-pos="indicator_pos"
        c-bind="attrs"
        data-citry-disclosure-root
        data-citry-ui-part="disclosure"
      >
        <div
          class="cui-disclosure__header"
          data-citry-ui-part="disclosure-header"
        >
          <c-element
            c-is="heading_tag"
            class="cui-disclosure__heading"
            c-bind="heading_attrs"
            data-citry-ui-part="disclosure-heading"
          >
            <button
              class="cui-disclosure__trigger"
              type="button"
              c-id="trigger_id"
              c-disabled="disabled"
              c-aria-expanded="'true' if open else 'false'"
              c-aria-controls="panel_id"
              c-data-state="'open' if open else 'closed'"
              c-data-disabled="disabled"
              c-bind="trigger_attrs"
              data-citry-disclosure-trigger
              data-citry-ui-part="disclosure-trigger"
            >
              <span
                class="cui-disclosure__title"
                data-citry-ui-part="disclosure-title"
              >
                <c-CInternalDisclosureTitleContent>
                  <c-slot name="title" required />
                </c-CInternalDisclosureTitleContent>
              </span>
              <span
                class="cui-disclosure__indicator"
                c-hidden="not indicator"
                aria-hidden="true"
                data-citry-ui-part="disclosure-indicator"
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
                  {{ icon.markup }}
                </svg>
              </span>
            </button>
          </c-element>
          <c-if cond="has_actions">
            <div
              class="cui-disclosure__actions"
              c-role="'group' if actions_label is not None else None"
              c-aria-label="actions_label"
              c-bind="actions_attrs"
              data-citry-ui-part="disclosure-actions"
            >
              <c-CInternalDisclosureActionsContent>
                <c-slot name="actions" />
              </c-CInternalDisclosureActionsContent>
            </div>
          </c-if>
        </div>
        <div
          class="cui-disclosure__panel"
          c-id="panel_id"
          c-role="'region' if region else None"
          c-aria-labelledby="trigger_id if region else None"
          c-aria-hidden="None if open else 'true'"
          c-hidden="not open"
          c-inert="not open"
          c-data-state="'open' if open else 'closed'"
          c-bind="panel_attrs"
          data-citry-disclosure-panel
          data-citry-ui-part="disclosure-panel"
        >
          <div
            class="cui-disclosure__body"
            data-citry-ui-part="disclosure-body"
          >
            <c-CInternalDisclosurePanelContent>
              <c-slot required />
            </c-CInternalDisclosurePanelContent>
          </div>
        </div>
      </div>
    """

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      $component({
        props: {
          open: {},
          onOpenChange: {},
          disabled: {},
          variant: {},
          size: {},
          indicator: {},
          indicatorPosition: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const rootSelector = "[data-citry-disclosure-root]";
          const form = inject(Symbol.for("citry-ui:form"), null);
          const layerCoordinator = anchoredLayerRuntime.coordinatorFor(root);
          const allowedParts = new Set(["popover", "tooltip", "menu", "popup", "hover-card"]);
          const titleHtml = new Set([
            "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data", "del", "dfn",
            "em", "i", "img", "ins", "kbd", "mark", "picture", "q", "rp", "rt",
            "ruby", "s", "samp", "small", "source", "span", "strong", "sub", "sup",
            "svg", "time", "u", "var", "wbr",
          ]);
          const titleSvg = new Set([
            "svg", "g", "path", "polyline", "line", "circle", "rect", "ellipse", "polygon",
          ]);
          const titleRejected = new Set([
            "role", "tabindex", "contenteditable", "autofocus", "href", "xlink:href",
            "controls", "usemap", "form", "popover", "is", "hidden", "inert", "focusable",
          ]);
          const ownershipDirectives = new Set([
            "x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable",
            "x-teleport", "x-text",
          ]);
          const allowedChoices = {
            variant: ["outline", "soft", "plain"],
            size: ["sm", "md", "lg"],
            indicatorPosition: ["start", "end"],
          };
          const invalidInputs = new Set();
          let anatomy = null;
          let structureValid = false;
          let invalidStructureEpisode = false;
          let activationInstalled = false;
          let fieldsetObserver = null;
          let animation = null;
          let active = true;
          let rawInputs = null;
          let controlled = false;
          let onOpenChange = null;
          let configuration = {
            disabled: data.disabled,
            variant: data.variant,
            size: data.size,
            indicator: data.indicator,
            indicatorPosition: data.indicatorPosition,
          };
          const retained = root.__citryUiDisclosureRuntime ?? null;
          const sameServer = retained?.serverFingerprint === data.serverFingerprint;
          let baselineOpen = sameServer ? Boolean(retained.baselineOpen) : Boolean(data.open);
          let logicalOpen = sameServer ? Boolean(retained.logicalOpen) : baselineOpen;
          const runtimeState = retained ?? {};
          root.__citryUiDisclosureRuntime = runtimeState;
          let reconciledOnce = false;

          const describe = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInput = (name, value, fallback) => {
            if (invalidInputs.has(name)) {
              return;
            }
            invalidInputs.add(name);
            console.error(
              `[citry-ui] CDisclosure ${name} received invalid client value `
                + `${describe(value)}; using ${fallback}.`,
              root,
            );
          };
          const dynamicTarget = (name) => {
            const normalized = name.toLowerCase();
            if (normalized.startsWith("x-bind:")) {
              return normalized.slice(7).split(".", 1)[0];
            }
            if (normalized.startsWith(":") || normalized.startsWith(".")) {
              return normalized.slice(1).split(".", 1)[0];
            }
            return null;
          };
          const nearestRootOwns = (element) => element?.closest?.(rootSelector) === root;
          const directPart = (owner, part) => Array.from(owner?.children ?? []).find(
            (child) => child.getAttribute("data-citry-ui-part") === part,
          ) ?? null;
          const resolveAnatomy = () => {
            const header = directPart(root, "disclosure-header");
            const panel = directPart(root, "disclosure-panel");
            const heading = directPart(header, "disclosure-heading");
            const actions = directPart(header, "disclosure-actions");
            const trigger = directPart(heading, "disclosure-trigger");
            const title = directPart(trigger, "disclosure-title");
            const indicator = directPart(trigger, "disclosure-indicator");
            const body = directPart(panel, "disclosure-body");
            return { header, panel, heading, actions, trigger, title, indicator, body };
          };
          const titleAttributeProblem = (element) => {
            const tag = element.localName;
            for (const attribute of element.attributes) {
              const name = attribute.name.toLowerCase();
              if (tag === "svg" && name === "aria-hidden" && attribute.value === "true") {
                continue;
              }
              if (tag === "svg" && name === "focusable" && attribute.value === "false") {
                continue;
              }
              if (titleRejected.has(name) || name.startsWith("aria-")) {
                return `<${tag}> cannot use ${attribute.name}`;
              }
              if (name.startsWith("on") || name.startsWith("@") || name.startsWith("x-on:")) {
                return `<${tag}> cannot use event attribute ${attribute.name}`;
              }
              const directive = name.split(".", 1)[0];
              if (ownershipDirectives.has(directive)) {
                return `<${tag}> cannot use ownership directive ${attribute.name}`;
              }
              const target = dynamicTarget(name);
              if (target && (titleRejected.has(target) || target.startsWith("aria-"))) {
                return `<${tag}> cannot dynamically bind ${target}`;
              }
            }
            if (tag === "img" && (!element.hasAttribute("alt") || element.getAttribute("alt") !== "")) {
              return "title images require empty alt text";
            }
            if (tag === "svg" && (
              element.getAttribute("aria-hidden") !== "true"
              || element.getAttribute("focusable") !== "false"
            )) {
              return "title SVG requires aria-hidden=true and focusable=false";
            }
            return null;
          };
          const titleProblem = (title) => {
            if (!(title instanceof HTMLElement)) {
              return "the title wrapper is missing";
            }
            let text = "";
            const visit = (node, inSvg = false, hidden = false) => {
              if (node.nodeType === Node.TEXT_NODE) {
                if (!inSvg && !hidden) {
                  text += node.data;
                }
                return null;
              }
              if (node.nodeType !== Node.ELEMENT_NODE) {
                return null;
              }
              const element = node;
              const tag = element.localName;
              const svg = inSvg || tag === "svg";
              if (!(inSvg ? titleSvg : titleHtml).has(tag)) {
                return `unsupported <${tag}> title element`;
              }
              const attributeProblem = titleAttributeProblem(element);
              if (attributeProblem) {
                return attributeProblem;
              }
              const excluded = hidden || element.getAttribute("aria-hidden") === "true";
              for (const child of element.childNodes) {
                const problem = visit(child, svg, excluded);
                if (problem) {
                  return problem;
                }
              }
              return null;
            };
            for (const child of title.childNodes) {
              const problem = visit(child);
              if (problem) {
                return problem;
              }
            }
            return /[^\t\n\f\r ]/.test(text) ? null : "title text is empty";
          };
          const contentProblem = (owner, actions) => {
            if (!owner) {
              return null;
            }
            for (const element of owner.querySelectorAll("*")) {
              const tag = element.localName;
              const part = element.getAttribute("data-citry-ui-part");
              if (actions && (part === "disclosure" || part === "accordion")) {
                return "nested Disclosure or Accordion roots are allowed only in panel content";
              }
              if (tag === "dialog") {
                return "native dialog descendants are not accepted";
              }
              if (tag.includes("-")) {
                return `unresolved custom element <${tag}> is not accepted`;
              }
              if (element.hasAttribute("is")) {
                return "customized built-ins are not accepted";
              }
              if (element.shadowRoot !== null) {
                return "authored ShadowRoot descendants are not accepted";
              }
              if (element.hasAttribute("popover") && !(
                element.getAttribute("popover") === "manual" && allowedParts.has(part)
              )) {
                return "raw or unrecognized native popovers are not accepted";
              }
            }
            return null;
          };
          const structureProblem = () => {
            const next = resolveAnatomy();
            if (
              !(next.header instanceof HTMLDivElement)
              || !(next.panel instanceof HTMLDivElement)
              || !(next.heading instanceof HTMLHeadingElement)
              || !(next.trigger instanceof HTMLButtonElement)
              || !(next.title instanceof HTMLSpanElement)
              || !(next.indicator instanceof HTMLSpanElement)
              || !(next.body instanceof HTMLDivElement)
            ) {
              return "owned anatomy is missing or has the wrong native element";
            }
            if (next.actions !== null && !(next.actions instanceof HTMLDivElement)) {
              return "the actions wrapper has the wrong native element";
            }
            if (
              next.header.parentElement !== root
              || next.panel.parentElement !== root
              || next.heading.parentElement !== next.header
              || next.trigger.parentElement !== next.heading
              || next.title.parentElement !== next.trigger
              || next.indicator.parentElement !== next.trigger
              || next.body.parentElement !== next.panel
              || (next.actions && next.actions.parentElement !== next.header)
            ) {
              return "owned anatomy has an invalid parent relationship";
            }
            if (
              root.id !== data.rootId
              || root.getAttribute("data-citry-ui-part") !== "disclosure"
              || !root.hasAttribute("data-citry-disclosure-root")
              || next.heading.localName !== data.headingTag
              || next.trigger.id !== data.triggerId
              || next.panel.id !== data.panelId
              || Boolean(next.actions) !== data.hasActions
              || root.children.length !== 2
              || root.firstElementChild !== next.header
              || root.lastElementChild !== next.panel
              || next.header.children.length !== (data.hasActions ? 2 : 1)
              || next.header.firstElementChild !== next.heading
              || (next.actions && next.header.lastElementChild !== next.actions)
              || next.heading.children.length !== 1
              || next.trigger.children.length !== 2
              || next.trigger.firstElementChild !== next.title
              || next.trigger.lastElementChild !== next.indicator
              || next.panel.children.length !== 1
              || next.trigger.type !== "button"
              || next.trigger.getAttribute("aria-controls") !== next.panel.id
              || next.trigger.id === ""
            ) {
              return "owned trigger relationship is invalid";
            }
            if (
              data.region
                ? next.panel.getAttribute("role") !== "region"
                  || next.panel.getAttribute("aria-labelledby") !== next.trigger.id
                : next.panel.hasAttribute("role") || next.panel.hasAttribute("aria-labelledby")
            ) {
              return "owned region relationship is invalid";
            }
            if (next.actions && (
              data.actionsLabel === null
                ? next.actions.hasAttribute("role") || next.actions.hasAttribute("aria-label")
                : next.actions.getAttribute("role") !== "group"
                  || next.actions.getAttribute("aria-label") !== data.actionsLabel
            )) {
              return "owned actions relationship is invalid";
            }
            const titleIssue = titleProblem(next.title);
            if (titleIssue) {
              return titleIssue;
            }
            const actionIssue = contentProblem(next.actions, true);
            if (actionIssue) {
              return actionIssue;
            }
            const panelIssue = contentProblem(next.body, false);
            if (panelIssue) {
              return panelIssue;
            }
            anatomy = next;
            return null;
          };

          const durationMs = () => {
            if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
              return 0;
            }
            const raw = getComputedStyle(root)
              .getPropertyValue("--_cui-disclosure-duration")
              .trim();
            if (raw.endsWith("ms")) {
              return Math.max(0, Number.parseFloat(raw) || 0);
            }
            if (raw.endsWith("s")) {
              return Math.max(0, (Number.parseFloat(raw) || 0) * 1000);
            }
            return 0;
          };
          const clearAnimationStyles = () => {
            anatomy?.panel?.style.removeProperty("block-size");
            anatomy?.panel?.style.removeProperty("overflow");
          };
          const cancelAnimation = ({ preserveGeometry = false } = {}) => {
            if (!animation) {
              return;
            }
            const height = anatomy.panel.getBoundingClientRect().height;
            animation.cancel();
            animation = null;
            if (preserveGeometry) {
              anatomy.panel.style.blockSize = `${height}px`;
            } else {
              clearAnimationStyles();
            }
          };
          const settlePresence = (open) => {
            cancelAnimation();
            clearAnimationStyles();
            if (open) {
              anatomy.panel.hidden = false;
              anatomy.panel.inert = false;
              anatomy.panel.removeAttribute("aria-hidden");
            } else {
              anatomy.panel.inert = true;
              anatomy.panel.setAttribute("aria-hidden", "true");
              anatomy.panel.hidden = true;
            }
          };
          const composedParent = (node) => {
            if (node?.parentNode) {
              return node.parentNode;
            }
            if (node instanceof ShadowRoot) {
              return node.host;
            }
            const nodeRoot = node?.getRootNode?.();
            return nodeRoot instanceof ShadowRoot ? nodeRoot.host : null;
          };
          const containingModal = (start) => {
            let current = start;
            while (current) {
              if (current instanceof HTMLDialogElement && current.matches(":modal")) {
                return current;
              }
              current = composedParent(current);
            }
            return null;
          };
          const renderedTrigger = () => {
            if (!anatomy.trigger.isConnected || anatomy.trigger.matches(":disabled")) {
              return false;
            }
            const style = getComputedStyle(anatomy.trigger);
            return style.display !== "none"
              && style.visibility !== "hidden"
              && anatomy.trigger.getClientRects().length > 0;
          };
          const recoverPanelFocus = () => {
            let focused = layerCoordinator.deepActiveElement();
            if (!anchoredLayerRuntime.composedContains(anatomy.panel, focused)) {
              return;
            }
            if (renderedTrigger()) {
              anatomy.trigger.focus({ preventScroll: true });
            }
            focused = layerCoordinator.deepActiveElement();
            if (!anchoredLayerRuntime.composedContains(anatomy.panel, focused)) {
              return;
            }
            const target = containingModal(root) ?? root.ownerDocument.body;
            const prior = target.getAttribute("tabindex");
            if (!target.hasAttribute("tabindex")) {
              target.setAttribute("tabindex", "-1");
            }
            target.focus({ preventScroll: true });
            if (prior === null) {
              target.removeAttribute("tabindex");
            } else {
              target.setAttribute("tabindex", prior);
            }
          };
          const reflectState = () => {
            const state = logicalOpen ? "open" : "closed";
            root.dataset.state = state;
            anatomy.trigger.dataset.state = state;
            anatomy.panel.dataset.state = state;
            anatomy.trigger.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
          };
          const animatePresence = (open) => {
            const panel = anatomy.panel;
            const wasHidden = panel.hidden;
            cancelAnimation({ preserveGeometry: true });
            const start = wasHidden && open ? 0 : panel.getBoundingClientRect().height;
            if (open) {
              panel.hidden = false;
              panel.inert = false;
              panel.removeAttribute("aria-hidden");
            } else {
              panel.inert = true;
              panel.setAttribute("aria-hidden", "true");
            }
            const duration = durationMs();
            if (duration === 0 || typeof panel.animate !== "function") {
              settlePresence(open);
              return;
            }
            if (open && wasHidden) {
              panel.style.blockSize = "auto";
            }
            const end = open ? panel.scrollHeight : 0;
            panel.style.blockSize = `${start}px`;
            panel.style.overflow = "clip";
            const easing = getComputedStyle(root)
              .getPropertyValue("--_cui-disclosure-easing")
              .trim() || "ease-out";
            const current = panel.animate(
              [{ blockSize: `${start}px` }, { blockSize: `${end}px` }],
              { duration, easing },
            );
            animation = current;
            current.finished.then(() => {
              if (!active || animation !== current) {
                return;
              }
              animation = null;
              clearAnimationStyles();
              if (!open) {
                panel.hidden = true;
              }
            }).catch(() => {});
          };
          const commitState = (next, { animate = true } = {}) => {
            if (logicalOpen === next) {
              if (!animate) {
                reflectState();
                settlePresence(next);
              }
              return;
            }
            const ancestorClose = next
              ? null
              : layerCoordinator.beginAncestorClose(anatomy.panel, anatomy.panel);
            try {
              if (!next) {
                recoverPanelFocus();
              }
              logicalOpen = next;
              reflectState();
              if (animate) {
                animatePresence(next);
              } else {
                settlePresence(next);
              }
              ancestorClose?.commit();
            } catch (error) {
              ancestorClose?.cancel();
              throw error;
            }
            runtimeState.logicalOpen = logicalOpen;
            runtimeState.baselineOpen = baselineOpen;
            runtimeState.serverFingerprint = data.serverFingerprint;
          };
          const applyDisabled = () => {
            if (!anatomy?.trigger) {
              return;
            }
            anatomy.trigger.disabled = Boolean(form?.disabled) || configuration.disabled;
            const disabled = anatomy.trigger.matches(":disabled");
            root.toggleAttribute("data-disabled", disabled);
            anatomy.trigger.toggleAttribute("data-disabled", disabled);
          };
          const rebuildFieldsets = () => {
            fieldsetObserver?.disconnect();
            fieldsetObserver = null;
            const fieldsets = [];
            for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
              if (ancestor.matches("fieldset")) {
                fieldsets.push(ancestor);
              }
            }
            if (fieldsets.length === 0) {
              return;
            }
            fieldsetObserver = new MutationObserver(() => {
              if (structureValid) {
                applyDisabled();
              }
            });
            fieldsets.forEach((fieldset) => fieldsetObserver.observe(fieldset, {
              attributes: true,
              attributeFilter: ["disabled"],
              childList: true,
            }));
          };

          const resolveBoolean = (name) => {
            const supplied = rawInputs[name];
            if (supplied === undefined) {
              invalidInputs.delete(name);
              return data[name];
            }
            if (typeof supplied === "boolean") {
              invalidInputs.delete(name);
              return supplied;
            }
            reportInput(name, supplied, "the Python fallback");
            return data[name];
          };
          const resolveChoice = (name) => {
            const supplied = rawInputs[name];
            if (supplied === undefined) {
              invalidInputs.delete(name);
              return data[name];
            }
            if (typeof supplied === "string" && allowedChoices[name].includes(supplied)) {
              invalidInputs.delete(name);
              return supplied;
            }
            reportInput(name, supplied, "the Python fallback");
            return data[name];
          };
          const resolveCallback = () => {
            const supplied = rawInputs.onOpenChange;
            if (supplied === undefined || supplied === null) {
              invalidInputs.delete("onOpenChange");
              return null;
            }
            if (typeof supplied === "function") {
              invalidInputs.delete("onOpenChange");
              return supplied;
            }
            reportInput("onOpenChange", supplied, "no callback");
            return null;
          };
          const resolveOpen = () => {
            const supplied = rawInputs.open;
            if (supplied === undefined || supplied === null) {
              invalidInputs.delete("open");
              return { controlled: false, value: baselineOpen };
            }
            if (typeof supplied === "boolean") {
              invalidInputs.delete("open");
              return { controlled: true, value: supplied };
            }
            reportInput("open", supplied, "the committed baseline");
            return { controlled: false, value: baselineOpen };
          };
          const applyRawInputs = ({ animate = true } = {}) => {
            configuration = {
              disabled: resolveBoolean("disabled"),
              variant: resolveChoice("variant"),
              size: resolveChoice("size"),
              indicator: resolveBoolean("indicator"),
              indicatorPosition: resolveChoice("indicatorPosition"),
            };
            onOpenChange = resolveCallback();
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            root.dataset.indicatorPos = configuration.indicatorPosition;
            root.toggleAttribute("data-indicator", configuration.indicator);
            anatomy.indicator.hidden = !configuration.indicator;
            applyDisabled();
            const requested = resolveOpen();
            controlled = requested.controlled;
            commitState(requested.value, { animate });
          };

          const removeActivation = () => {
            if (!activationInstalled) {
              return;
            }
            root.removeEventListener("click", onClick, true);
            activationInstalled = false;
          };
          const installActivation = () => {
            if (activationInstalled) {
              return;
            }
            root.addEventListener("click", onClick, true);
            activationInstalled = true;
          };
          const enterInvalid = (problem) => {
            if (structureValid) {
              cancelAnimation();
              settlePresence(logicalOpen);
            }
            structureValid = false;
            removeActivation();
            fieldsetObserver?.disconnect();
            fieldsetObserver = null;
            root.removeAttribute("data-citry-disclosure-initialized");
            if (!invalidStructureEpisode) {
              invalidStructureEpisode = true;
              console.error(`[citry-ui] CDisclosure settled structure is invalid: ${problem}.`, root);
            }
          };
          const repair = () => {
            structureValid = true;
            invalidStructureEpisode = false;
            rebuildFieldsets();
            installActivation();
            applyRawInputs({ animate: false });
            reconciledOnce = true;
            root.setAttribute("data-citry-disclosure-initialized", "");
          };
          const preflight = () => {
            const problem = structureProblem();
            if (problem) {
              enterInvalid(problem);
              return false;
            }
            if (!structureValid) {
              repair();
            }
            return true;
          };
          function onClick(event) {
            const trigger = event.target.closest?.("[data-citry-disclosure-trigger]");
            if (trigger !== anatomy?.trigger || !nearestRootOwns(trigger)) {
              return;
            }
            if (!preflight() || anatomy.trigger.matches(":disabled")) {
              return;
            }
            const previous = logicalOpen;
            const next = !previous;
            const requestWasControlled = controlled;
            onOpenChange?.(next, {
              open: next,
              previousOpen: previous,
              source: "activation",
              controlled: requestWasControlled,
            });
            if (!preflight()) {
              return;
            }
            if (!requestWasControlled) {
              baselineOpen = next;
              commitState(next, { animate: true });
            }
          }
          const onBeforeToggle = (event) => {
            if (event.newState !== "open") {
              return;
            }
            const target = event.target;
            if (!(target instanceof Element) || target === root || !root.contains(target)) {
              return;
            }
            const part = target.getAttribute("data-citry-ui-part");
            const forbidden = target.localName === "dialog" || (
              target.hasAttribute("popover")
              && !(target.getAttribute("popover") === "manual" && allowedParts.has(part))
            );
            if (!forbidden) {
              return;
            }
            event.preventDefault();
            enterInvalid(
              target.localName === "dialog"
                ? "a descendant Dialog attempted to open"
                : "a raw descendant popover attempted to open",
            );
          };

          const titleObserver = new MutationObserver(() => {
            if (active) {
              preflight();
            }
          });
          const contentObserver = new MutationObserver(() => {
            if (active) {
              preflight();
            }
          });
          const observeStructure = () => {
            titleObserver.disconnect();
            contentObserver.disconnect();
            const current = resolveAnatomy();
            if (current.title) {
              titleObserver.observe(current.title, {
                attributes: true,
                childList: true,
                characterData: true,
                subtree: true,
              });
            }
            if (current.panel) {
              contentObserver.observe(current.panel, {
                attributes: true,
                attributeFilter: ["popover", "data-citry-ui-part", "is"],
                childList: true,
                subtree: true,
              });
            }
            if (current.actions) {
              contentObserver.observe(current.actions, {
                attributes: true,
                attributeFilter: ["popover", "data-citry-ui-part", "is"],
                childList: true,
                subtree: true,
              });
            }
          };

          root.addEventListener("beforetoggle", onBeforeToggle, true);
          observeStructure();
          const initialProblem = structureProblem();
          if (initialProblem) {
            enterInvalid(initialProblem);
          } else {
            structureValid = true;
            rebuildFieldsets();
            installActivation();
          }
          effect(() => {
            rawInputs = {
              open: props.open,
              onOpenChange: props.onOpenChange,
              disabled: props.disabled,
              variant: props.variant,
              size: props.size,
              indicator: props.indicator,
              indicatorPosition: props.indicatorPosition,
            };
            if (!structureValid || !preflight()) {
              return;
            }
            applyRawInputs({ animate: reconciledOnce });
            reconciledOnce = true;
            root.setAttribute("data-citry-disclosure-initialized", "");
          });

          return () => {
            active = false;
            runtimeState.baselineOpen = baselineOpen;
            runtimeState.logicalOpen = logicalOpen;
            runtimeState.serverFingerprint = data.serverFingerprint;
            removeActivation();
            root.removeEventListener("beforetoggle", onBeforeToggle, true);
            fieldsetObserver?.disconnect();
            titleObserver.disconnect();
            contentObserver.disconnect();
            cancelAnimation();
            clearAnimationStyles();
            root.removeAttribute("data-citry-disclosure-initialized");
          };
        },
      });
    """
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-disclosure) {
          --_cui-disclosure-background: var(--cui-disclosure-background, Canvas);
          --_cui-disclosure-foreground: var(--cui-disclosure-foreground, CanvasText);
          --_cui-disclosure-border-color: var(
            --cui-disclosure-border-color,
            color-mix(in srgb, currentColor 22%, transparent)
          );
          --_cui-disclosure-border-width: var(--cui-disclosure-border-width, 1px);
          --_cui-disclosure-radius: var(--cui-disclosure-radius, 0.75rem);
          --_cui-disclosure-trigger-background: var(
            --cui-disclosure-trigger-background,
            transparent
          );
          --_cui-disclosure-trigger-hover-background: var(
            --cui-disclosure-trigger-hover-background,
            color-mix(in srgb, currentColor 8%, transparent)
          );
          --_cui-disclosure-trigger-open-background: var(
            --cui-disclosure-trigger-open-background,
            color-mix(in srgb, LinkText 9%, transparent)
          );
          --_cui-disclosure-trigger-open-color: var(
            --cui-disclosure-trigger-open-color,
            LinkText
          );
          --_cui-disclosure-focus-color: var(--cui-disclosure-focus-color, Highlight);
          --_cui-disclosure-indicator-color: var(
            --cui-disclosure-indicator-color,
            currentColor
          );
          --_cui-disclosure-trigger-padding-inline: var(
            --cui-disclosure-trigger-padding-inline,
            1rem
          );
          --_cui-disclosure-trigger-padding-block: var(
            --cui-disclosure-trigger-padding-block,
            0.875rem
          );
          --_cui-disclosure-panel-padding-inline: var(
            --cui-disclosure-panel-padding-inline,
            1rem
          );
          --_cui-disclosure-panel-padding-block: var(
            --cui-disclosure-panel-padding-block,
            1rem
          );
          --_cui-disclosure-actions-gap: var(--cui-disclosure-actions-gap, 0.5rem);
          --_cui-disclosure-duration: var(--cui-disclosure-duration, 180ms);
          --_cui-disclosure-easing: var(--cui-disclosure-easing, ease-out);
          display: grid;
          min-inline-size: 0;
          overflow: visible;
          color: var(--_cui-disclosure-foreground);
          font-family: ui-sans-serif, system-ui, sans-serif;
        }

        :where(.cui-disclosure[data-size="sm"]) {
          --_cui-disclosure-trigger-padding-inline: var(
            --cui-disclosure-trigger-padding-inline,
            0.75rem
          );
          --_cui-disclosure-trigger-padding-block: var(
            --cui-disclosure-trigger-padding-block,
            0.625rem
          );
          --_cui-disclosure-panel-padding-inline: var(
            --cui-disclosure-panel-padding-inline,
            0.75rem
          );
          --_cui-disclosure-panel-padding-block: var(
            --cui-disclosure-panel-padding-block,
            0.75rem
          );
          font-size: 0.875rem;
        }

        :where(.cui-disclosure[data-size="lg"]) {
          --_cui-disclosure-trigger-padding-inline: var(
            --cui-disclosure-trigger-padding-inline,
            1.25rem
          );
          --_cui-disclosure-trigger-padding-block: var(
            --cui-disclosure-trigger-padding-block,
            1rem
          );
          --_cui-disclosure-panel-padding-inline: var(
            --cui-disclosure-panel-padding-inline,
            1.25rem
          );
          --_cui-disclosure-panel-padding-block: var(
            --cui-disclosure-panel-padding-block,
            1.25rem
          );
          font-size: 1.0625rem;
        }

        :where(.cui-disclosure[data-variant="outline"]) {
          border: var(--_cui-disclosure-border-width) solid var(--_cui-disclosure-border-color);
          border-radius: var(--_cui-disclosure-radius);
          background: var(--_cui-disclosure-background);
        }

        :where(.cui-disclosure[data-variant="soft"]) {
          border-radius: var(--_cui-disclosure-radius);
          background: color-mix(
            in srgb,
            var(--_cui-disclosure-foreground) 5%,
            var(--_cui-disclosure-background)
          );
        }

        :where(.cui-disclosure[data-variant="plain"]) {
          background: transparent;
        }

        :where(.cui-disclosure > .cui-disclosure__header) {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          min-inline-size: 0;
        }

        :where(.cui-disclosure > .cui-disclosure__header > .cui-disclosure__heading) {
          min-inline-size: 0;
          margin: 0;
          font: inherit;
        }

        :where(
          .cui-disclosure
          > .cui-disclosure__header
          > .cui-disclosure__heading
          > .cui-disclosure__trigger
        ) {
          display: flex;
          inline-size: 100%;
          min-inline-size: 0;
          align-items: center;
          justify-content: space-between;
          gap: 0.75rem;
          padding-block: var(--_cui-disclosure-trigger-padding-block);
          padding-inline: var(--_cui-disclosure-trigger-padding-inline);
          border: 0;
          border-radius: var(--_cui-disclosure-radius);
          background: var(--_cui-disclosure-trigger-background);
          color: inherit;
          font: inherit;
          font-weight: 650;
          line-height: 1.35;
          text-align: start;
          cursor: pointer;
        }

        :where(.cui-disclosure__trigger:not(:disabled):hover) {
          background: var(--_cui-disclosure-trigger-hover-background);
        }

        :where(.cui-disclosure__trigger[data-state="open"]) {
          background: var(--_cui-disclosure-trigger-open-background);
          color: var(--_cui-disclosure-trigger-open-color);
        }

        :where(.cui-disclosure__trigger:focus-visible) {
          position: relative;
          z-index: 1;
          outline: 2px solid var(--_cui-disclosure-focus-color);
          outline-offset: -2px;
        }

        :where(.cui-disclosure__trigger:disabled) {
          cursor: not-allowed;
          opacity: 0.58;
        }

        :where(.cui-disclosure__title) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }

        :where(.cui-disclosure__indicator) {
          display: inline-grid;
          flex: 0 0 auto;
          inline-size: 1.1em;
          block-size: 1.1em;
          place-items: center;
          color: var(--_cui-disclosure-indicator-color);
          transition: transform var(--_cui-disclosure-duration) var(--_cui-disclosure-easing);
        }

        :where(.cui-disclosure__indicator > svg) {
          display: block;
          inline-size: 100%;
          block-size: 100%;
        }

        :where(.cui-disclosure__trigger[data-state="open"] > .cui-disclosure__indicator) {
          transform: rotate(180deg);
        }

        :where(
          .cui-disclosure[data-indicator-pos="start"]
          > .cui-disclosure__header
          > .cui-disclosure__heading
          > .cui-disclosure__trigger
          > .cui-disclosure__indicator
        ) {
          order: -1;
        }

        :where(.cui-disclosure__indicator[hidden]),
        :where(.cui-disclosure__panel[hidden]) {
          display: none !important;
        }

        :where(.cui-disclosure > .cui-disclosure__header > .cui-disclosure__actions) {
          display: flex;
          min-inline-size: 0;
          flex-wrap: wrap;
          align-items: center;
          gap: var(--_cui-disclosure-actions-gap);
          padding-inline-end: var(--_cui-disclosure-trigger-padding-inline);
          overflow-wrap: anywhere;
        }

        :where(.cui-disclosure__actions > *) {
          min-inline-size: 0;
          max-inline-size: 100%;
        }

        :where(.cui-disclosure > .cui-disclosure__panel) {
          min-inline-size: 0;
          overflow: visible;
        }

        :where(.cui-disclosure > .cui-disclosure__panel > .cui-disclosure__body) {
          min-inline-size: 0;
          padding-block: var(--_cui-disclosure-panel-padding-block);
          padding-inline: var(--_cui-disclosure-panel-padding-inline);
          overflow: visible;
          overflow-wrap: anywhere;
          line-height: 1.55;
        }

        :where(.cui-disclosure__body > *) {
          min-inline-size: 0;
          max-inline-size: 100%;
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-disclosure__indicator) {
            transition-duration: 0ms;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-disclosure) {
            --_cui-disclosure-border-color: CanvasText;
            --_cui-disclosure-focus-color: Highlight;
            --_cui-disclosure-trigger-open-color: CanvasText;
          }
        }

        @media print {
          :where(.cui-disclosure) {
            border-color: CanvasText;
            box-shadow: none;
          }

          :where(.cui-disclosure__panel[hidden]) {
            display: block !important;
          }

          :where(.cui-disclosure__panel) {
            block-size: auto !important;
            overflow: visible !important;
          }

          :where(.cui-disclosure__indicator) {
            display: none !important;
          }

          :where(.cui-disclosure__trigger) {
            background: transparent;
            color: CanvasText;
            cursor: default;
          }
        }
      }
    """


class CInternalDisclosureTitleContent(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CDisclosureTitleSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CDisclosure title completed without a render result.")
        _validate_title_output(result)

    template = """
      <c-slot required />
    """


class CInternalDisclosureActionsContent(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CDisclosureActionsSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CDisclosure actions completed without a render result.")
        _validate_content_output(result, actions=True)

    template = """
      <c-slot required />
    """


class CInternalDisclosurePanelContent(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CDisclosureDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        self.unprovide(_DISCLOSURE_CONTEXT_KEY)
        return {}

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CDisclosure panel completed without a render result.")
        _validate_content_output(result, actions=False)

    template = """
      <c-slot required />
    """


__all__ = [
    "CDisclosure",
    "CDisclosureActionsSlotData",
    "CDisclosureDefaultSlotData",
    "CDisclosureHeadingLevel",
    "CDisclosureIndicatorPos",
    "CDisclosureOpenChangeDetail",
    "CDisclosureSize",
    "CDisclosureTitleSlotData",
    "CDisclosureVariant",
]
