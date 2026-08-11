"""Styled application Menu component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any, ClassVar, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, SlotInput, const_value
from citry_ui.components._anchored_layer import (
    ANCHORED_LAYER_RUNTIME_DEPENDENCY,
    ANCHORED_LAYER_RUNTIME_JS,
)
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_optional_boolean,
)
from citry_ui.components.cicon.cicon import _resolve_registered_icon

CMenuPlacement = Literal[
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
]
CMenuSize = Literal["sm", "md", "lg"]
CMenuIntent = Literal["default", "danger"]
CMenuChecked = bool | Literal["mixed"]


class CMenuOpenChangeDetail(TypedDict):
    reason: Literal[
        "trigger",
        "escape",
        "outside",
        "focus-outside",
        "tab",
        "action",
        "native",
        "disabled",
        "ancestor",
    ]
    controlled: bool
    forced: bool
    source: object | None


class CMenuActionDetail(TypedDict):
    kind: Literal["command", "checkbox", "radio"]
    item: object
    event: object
    path: list[str]


class CMenuCheckedChangeDetail(TypedDict):
    checked: bool
    previousChecked: CMenuChecked
    controlled: bool
    item: object
    event: object
    path: list[str]


class CMenuRadioChangeDetail(TypedDict):
    value: str
    previousValue: str
    reason: Literal["activation", "removal"]
    controlled: bool
    item: object | None
    event: object | None
    path: list[str]


class CMenuActivatorSlotData:
    activator_attrs: dict[str, object]
    activator_disabled: bool


class CMenuDefaultSlotData:
    pass


class CMenuItemStartSlotData:
    pass


class CMenuItemDefaultSlotData:
    pass


class CMenuItemDescriptionSlotData:
    pass


class CMenuItemEndSlotData:
    pass


class CMenuGroupLabelSlotData:
    pass


class CMenuGroupDefaultSlotData:
    pass


class CMenuRadioGroupLabelSlotData:
    pass


class CMenuRadioGroupDefaultSlotData:
    pass


class CMenuSubmenuStartSlotData:
    pass


class CMenuSubmenuLabelSlotData:
    pass


class CMenuSubmenuDescriptionSlotData:
    pass


class CMenuSubmenuEndSlotData:
    pass


class CMenuSubmenuDefaultSlotData:
    pass


_PLACEMENTS = (
    "top-start",
    "top",
    "top-end",
    "bottom-start",
    "bottom",
    "bottom-end",
)
_SIZES = ("sm", "md", "lg")
_INTENTS = ("default", "danger")
_MENU_CONTEXT_KEY = "citry_ui_menu"
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
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_SURFACE_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-menu-exiting",
        "data-citry-menu-initialized",
        "data-citry-menu-root",
        "data-citry-ui-part",
        "data-match-width",
        "data-open",
        "data-placement",
        "data-size",
        "hidden",
        "id",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED_ATTRS = frozenset(
    {
        "aria-checked",
        "aria-controls",
        "aria-describedby",
        "aria-disabled",
        "aria-expanded",
        "aria-haspopup",
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "command",
        "commandfor",
        "contenteditable",
        "data-checked",
        "data-citry-menu-entry",
        "data-citry-menu-href",
        "data-citry-ui-part",
        "data-disabled",
        "data-intent",
        "disabled",
        "hidden",
        "href",
        "id",
        "inert",
        "popover",
        "popovertarget",
        "popovertargetaction",
        "role",
        "tabindex",
        "type",
    }
)
_GROUP_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-menu-group",
        "data-citry-ui-part",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_SEPARATOR_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-orientation",
        "aria-roledescription",
        "contenteditable",
        "data-citry-menu-entry",
        "data-citry-ui-part",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)
_SUBMENU_OWNED_ATTRS = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "aria-roledescription",
        "contenteditable",
        "data-citry-menu-entry",
        "data-citry-menu-submenu",
        "data-citry-ui-part",
        "data-open",
        "hidden",
        "inert",
        "popover",
        "role",
        "tabindex",
    }
)


@dataclass(slots=True)
class _MenuRegistration:
    kind: Literal[
        "item",
        "checkbox",
        "radio-group",
        "radio",
        "group",
        "separator",
        "submenu",
    ]
    render_id: str
    root_tag: str
    value: str | None = None
    children: _MenuRegistry | None = None
    selected_value: str | None = None


@dataclass(slots=True)
class _MenuRegistry:
    kind: Literal["menu", "group", "radio"]
    entries: list[_MenuRegistration] = field(default_factory=list)
    selected_value: str | None = None


@dataclass(frozen=True, slots=True)
class _MenuServerContext:
    registry: _MenuRegistry
    menu_id: str
    level_path: tuple[str, ...]
    selected_value: str | None = None


def _plain_optional_string(
    component_name: str,
    input_name: str,
    value: object,
) -> str | None:
    if value is None:
        return None
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"{component_name} {input_name} must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if type(plain) is not str:
        msg = f"{component_name} could not convert {input_name} to a plain string."
        raise TypeError(msg)
    return plain.replace("\r\n", "\n").replace("\r", "\n")


def _plain_identity(component_name: str, input_name: str, value: object) -> str:
    plain = _plain_optional_string(component_name, input_name, value)
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


def _plain_html_id(value: object) -> str | None:
    plain = _plain_optional_string("CMenu", "id", value)
    if plain is None:
        return None
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CMenu id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CMenu id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_choice(
    component_name: str,
    input_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> str:
    plain = _plain_identity(component_name, input_name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"{component_name} {input_name} must be one of {expected}, got {plain!r}."
        raise ValueError(msg)
    return plain


def _checked(component_name: str, value: object) -> CMenuChecked:
    raw = const_value(value)
    if isinstance(raw, bool) or raw == "mixed":
        return raw
    msg = f"{component_name} checked must be false, true, or 'mixed', got {raw!r}."
    raise ValueError(msg)


def _copy_attrs(
    component_name: str,
    input_name: str,
    attrs: Mapping[str, object] | None,
) -> dict[str, object]:
    if attrs is None:
        return {}
    if not isinstance(attrs, Mapping):
        msg = f"{component_name} {input_name} must be a mapping or None, got {attrs!r}."
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
    normalized_keys: set[str] = set()
    for key in attrs:
        normalized = key.casefold()
        if normalized in normalized_keys:
            msg = f"{component_name} cannot contain duplicate case variants of {key!r}."
            raise ValueError(msg)
        normalized_keys.add(normalized)
        if normalized.startswith(_RUNTIME_PREFIXES):
            msg = f"{component_name} cannot contain reserved Citry runtime attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"{component_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target in owned:
            msg = f"{component_name} cannot dynamically bind owned attribute {target!r}."
            raise ValueError(msg)


def _value_token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:16]


def _flatten_level(registry: _MenuRegistry) -> list[_MenuRegistration]:
    result: list[_MenuRegistration] = []
    for entry in registry.entries:
        if entry.kind in {"group", "radio-group"} and entry.children is not None:
            result.extend(_flatten_level(entry.children))
        elif entry.kind != "separator":
            result.append(entry)
    return result


def _validate_registry(registry: _MenuRegistry) -> None:
    if not registry.entries:
        owner = "CMenuRadioGroup" if registry.kind == "radio" else "Menu collection"
        msg = f"{owner} requires at least one direct declaration."
        raise ValueError(msg)

    if registry.entries[0].kind == "separator" or registry.entries[-1].kind == "separator":
        msg = "CMenuSeparator must appear between actionable declarations."
        raise ValueError(msg)
    for previous, current in zip(registry.entries, registry.entries[1:], strict=False):
        if previous.kind == current.kind == "separator":
            msg = "CMenuSeparator cannot be consecutive."
            raise ValueError(msg)

    if registry.kind == "radio":
        if any(entry.kind != "radio" for entry in registry.entries):
            msg = "CMenuRadioGroup may contain only direct CMenuRadioItem declarations."
            raise ValueError(msg)
        values = [entry.value for entry in registry.entries]
        if len(set(values)) != len(values):
            msg = "CMenuRadioGroup requires every radio value to be unique."
            raise ValueError(msg)
        if registry.selected_value not in values:
            msg = "CMenuRadioGroup value must identify one direct CMenuRadioItem."
            raise ValueError(msg)
        return

    flattened = _flatten_level(registry)
    if not flattened:
        msg = "Menu collection requires at least one actionable declaration."
        raise ValueError(msg)
    values = [entry.value for entry in flattened if entry.value is not None]
    if len(set(values)) != len(values):
        msg = "Menu values must be unique within the current menu level."
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


class _DirectMenuParser(HTMLParser):
    def __init__(self, expected: Mapping[str, str]) -> None:
        super().__init__(convert_charrefs=True)
        self.expected = expected
        self.depth = 0
        self.active_render_id: str | None = None
        self.active_root_count = 0
        self.render_ids: list[str] = []
        self.invalid = False
        self.pending: list[str] = []

    def feed_text(self, value: str) -> None:
        self.pending.append(value)

    def flush(self) -> None:
        if not self.pending:
            return
        self.feed("".join(self.pending))
        self.pending.clear()

    def enter(self, render_id: str) -> None:
        self.flush()
        if self.depth != 0 or self.active_render_id is not None:
            self.invalid = True
        self.active_render_id = render_id
        self.active_root_count = 0

    def exit(self, render_id: str) -> None:
        self.flush()
        if self.depth != 0 or self.active_render_id != render_id or self.active_root_count != 1:
            self.invalid = True
        self.render_ids.append(render_id)
        self.active_render_id = None
        self.active_root_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if self.depth == 0:
            if self.active_render_id is None:
                self.invalid = True
            else:
                self.active_root_count += 1
                if tag != self.expected[self.active_render_id]:
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


def _feed_menu_output(
    parser: _DirectMenuParser,
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
    is_expected_root = part.is_component_root and render_id is not None and render_id in expected_render_ids
    if is_expected_root and render_id is not None:
        parser.enter(render_id)
    for child in part.parts:
        _feed_menu_output(parser, child, expected_render_ids)
    if is_expected_root and render_id is not None:
        parser.exit(render_id)


def _validate_direct_output(result: CitryRender, registry: _MenuRegistry) -> None:
    expected = {entry.render_id: entry.root_tag for entry in registry.entries}
    parser = _DirectMenuParser(expected)
    _feed_menu_output(parser, result, frozenset(expected))
    parser.flush()
    parser.close()
    if parser.invalid or parser.render_ids != list(expected):
        msg = (
            "Menu collections may contain only valid direct Menu declarations, "
            "formatting whitespace, and transparent components that add no element."
        )
        raise ValueError(msg)


def _register(
    context: _MenuServerContext,
    *,
    kind: Literal[
        "item",
        "checkbox",
        "radio-group",
        "radio",
        "group",
        "separator",
        "submenu",
    ],
    render_id: str,
    root_tag: str,
    value: str | None = None,
    children: _MenuRegistry | None = None,
    selected_value: str | None = None,
) -> None:
    context.registry.entries.append(
        _MenuRegistration(
            kind=kind,
            render_id=render_id,
            root_tag=root_tag,
            value=value,
            children=children,
            selected_value=selected_value,
        )
    )


def _context(component: LibraryComponent, component_name: str) -> _MenuServerContext:
    provided = component.inject(_MENU_CONTEXT_KEY, None)
    if provided is None:
        msg = f"{component_name} must be rendered in a valid CMenu declaration collection."
        raise ValueError(msg)
    return provided.context


def _item_snapshot(
    component: LibraryComponent,
    component_name: str,
    kwargs: CMenuItem.Kwargs | CMenuCheckboxItem.Kwargs | CMenuRadioItem.Kwargs,
    *,
    kind: Literal["item", "checkbox", "radio"],
) -> dict[str, object]:
    cached = getattr(component, "_cui_menu_item_snapshot", None)
    if cached is not None:
        return cached

    context = _context(component, component_name)
    if kind == "radio" and context.registry.kind != "radio":
        msg = "CMenuRadioItem must be a direct child of CMenuRadioGroup."
        raise ValueError(msg)
    if kind != "radio" and context.registry.kind == "radio":
        msg = "CMenuRadioGroup may contain only direct CMenuRadioItem declarations."
        raise ValueError(msg)

    value = _plain_optional_string(component_name, "value", kwargs.value)
    href = None
    checked: CMenuChecked | None = None
    if kind == "item":
        item_kwargs = cast("CMenuItem.Kwargs", kwargs)
        href = _plain_optional_string(component_name, "href", item_kwargs.href)
        if href is not None and "\0" in href:
            msg = "CMenuItem href cannot contain U+0000."
            raise ValueError(msg)
        if value is not None:
            value = _plain_identity(component_name, "value", value)
        if value is not None and href is not None:
            msg = "CMenuItem value cannot be combined with href."
            raise ValueError(msg)
    else:
        value = _plain_identity(component_name, "value", kwargs.value)
        if kind == "checkbox":
            checkbox_kwargs = cast("CMenuCheckboxItem.Kwargs", kwargs)
            checked = _checked(component_name, checkbox_kwargs.checked)
        else:
            checked = context.selected_value == value

    validate_boolean(component_name, "disabled", kwargs.disabled)
    validate_optional_boolean(component_name, "close_on_select", kwargs.close_on_select)
    intent = _plain_choice(component_name, "intent", item_kwargs.intent, _INTENTS) if kind == "item" else "default"
    text_value = _plain_optional_string(component_name, "text_value", kwargs.text_value)
    if text_value is not None and "\0" in text_value:
        msg = f"{component_name} text_value cannot contain U+0000."
        raise ValueError(msg)
    attrs = _copy_attrs(component_name, "attrs", kwargs.attrs)
    _validate_attrs(f"{component_name} attrs", attrs, _ITEM_OWNED_ATTRS)

    root_tag = "a" if href is not None else "button"
    _register(
        context,
        kind=kind,
        render_id=component.id,
        root_tag=root_tag,
        value=value,
    )
    token = _value_token(value or component.id)
    label_id = f"{context.menu_id}-label-{token}"
    description_id = f"{context.menu_id}-description-{token}"
    has_description = "description" in component.raw_slots
    component.unprovide(_MENU_CONTEXT_KEY)
    snapshot: dict[str, object] = {
        "kind": kind,
        "root_tag": root_tag,
        "value": value,
        "href": href,
        "disabled": bool(kwargs.disabled),
        "close_on_select": kwargs.close_on_select,
        "intent": intent,
        "text_value": text_value,
        "checked": checked,
        "checked_text": str(checked).lower() if checked is not None else None,
        "label_id": label_id,
        "description_id": description_id,
        "described_by": description_id if has_description else None,
        "has_start": "start" in component.raw_slots,
        "has_description": has_description,
        "has_end": "end" in component.raw_slots,
        "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
    }
    dynamic_component = cast("Any", component)
    dynamic_component._cui_menu_item_snapshot = snapshot
    return snapshot


class CMenu(LibraryComponent):
    class Dependencies:
        js: ClassVar = [ANCHORED_LAYER_RUNTIME_DEPENDENCY]

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        open: bool = False
        disabled: bool = False
        loop: bool = True
        placement: CMenuPlacement = "bottom-start"
        match_width: bool = False
        close_on_select: bool = True
        size: CMenuSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        activator: SlotInput[CMenuActivatorSlotData]
        default: SlotInput[CMenuDefaultSlotData]

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_menu_snapshot", None)
        if cached is not None:
            return cached

        if self.inject(_MENU_CONTEXT_KEY, None) is not None:
            msg = "CMenu cannot be rendered as a Menu declaration."
            raise ValueError(msg)
        menu_id = _plain_html_id(kwargs.id) or f"cui-menu-{self.id}"
        validate_boolean("CMenu", "open", kwargs.open)
        validate_boolean("CMenu", "disabled", kwargs.disabled)
        validate_boolean("CMenu", "loop", kwargs.loop)
        validate_boolean("CMenu", "match_width", kwargs.match_width)
        validate_boolean("CMenu", "close_on_select", kwargs.close_on_select)
        placement = _plain_choice("CMenu", "placement", kwargs.placement, _PLACEMENTS)
        size = _plain_choice("CMenu", "size", kwargs.size, _SIZES)
        attrs = _copy_attrs("CMenu", "attrs", kwargs.attrs)
        _validate_attrs("CMenu attrs", attrs, _SURFACE_OWNED_ATTRS)
        anchor_name = f"--_cui-menu-anchor-ref-{self.id}"
        generated_anchor_style = {"--_cui-menu-anchor": anchor_name}
        surface_style: CStyleValue = (
            generated_anchor_style if kwargs.style is None else (kwargs.style, generated_anchor_style)
        )
        registry = _MenuRegistry(kind="menu")
        self.provide(
            _MENU_CONTEXT_KEY,
            context=_MenuServerContext(
                registry=registry,
                menu_id=menu_id,
                level_path=(),
            ),
        )
        snapshot = {
            "menu_id": menu_id,
            "open": bool(kwargs.open),
            "disabled": bool(kwargs.disabled),
            "loop": bool(kwargs.loop),
            "placement": placement,
            "match_width": bool(kwargs.match_width),
            "close_on_select": bool(kwargs.close_on_select),
            "size": size,
            "registry": registry,
            "activator_attrs": {
                "id": f"{menu_id}-trigger",
                "aria-haspopup": "menu",
                "aria-controls": menu_id,
                "aria-expanded": "true" if kwargs.open and not kwargs.disabled else "false",
                "data-citry-menu-trigger": "",
                "style": {"anchor-name": anchor_name},
            },
            "activator_disabled": bool(kwargs.disabled),
            "attrs": merge_root_attrs(attrs, kwargs.class_, surface_style),
        }
        self._cui_menu_snapshot = snapshot
        return snapshot

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return self._snapshot(kwargs)

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        snapshot = self._snapshot(kwargs)
        return {
            "open": snapshot["open"],
            "disabled": snapshot["disabled"],
            "loop": snapshot["loop"],
            "placement": snapshot["placement"],
            "matchWidth": snapshot["match_width"],
            "closeOnSelect": snapshot["close_on_select"],
            "size": snapshot["size"],
        }

    template = """
      <div
        class="cui-menu-host"
        data-citry-menu-host
      >
        <c-CInternalMenuContent>
          <c-slot
            name="activator"
            c-activator_attrs="activator_attrs"
            c-activator_disabled="activator_disabled"
            required
          />
        </c-CInternalMenuContent>
        <div
          class="cui-menu"
          c-id="menu_id"
          c-aria-labelledby="menu_id + '-trigger'"
          c-inert="not open or disabled"
          c-data-open="open and not disabled"
          c-data-placement="placement"
          c-data-match-width="match_width"
          c-data-size="size"
          c-bind="attrs"
          popover="manual"
          role="menu"
          data-citry-menu-root
          data-citry-ui-part="menu"
        >
          <c-CInternalMenuCollection c-registry="registry">
            <c-slot required />
          </c-CInternalMenuCollection>
        </div>
      </div>
    """

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      $component({
        props: {
          open: {},
          disabled: {},
          loop: {},
          placement: {},
          matchWidth: {},
          closeOnSelect: {},
          size: {},
          onOpenChange: {},
          onAction: {},
        },
        init: ({ els, data, props, effect, provide }) => {
          const host = els[0];
          const hostSelector = "[data-citry-menu-host]";
          const nearestHost = (element) => element?.closest?.(hostSelector) ?? null;
          const surface = [...host.querySelectorAll("[data-citry-menu-root]")]
            .find((candidate) => nearestHost(candidate) === host);
          const triggers = [...host.querySelectorAll("[data-citry-menu-trigger]")]
            .filter((candidate) => nearestHost(candidate) === host);
          if (!surface || triggers.length !== 1 || !(triggers[0] instanceof HTMLButtonElement)) {
            throw new Error(
              "[citry-ui] CMenu activator must spread activator_attrs onto exactly one native Button.",
            );
          }
          const trigger = triggers[0];
          // Server HTML may advertise an initially open Menu. Until the
          // settled declaration tree and activator are validated, expose no
          // interactive surface to assistive technology or pointer input.
          surface.inert = true;
          surface.removeAttribute("data-open");
          surface.removeAttribute("data-citry-menu-exiting");
          surface.removeAttribute("data-citry-menu-initialized");
          trigger.setAttribute("aria-expanded", "false");
          const unsafeInitialTriggerType = trigger.type !== "button";
          if (unsafeInitialTriggerType) {
            // Normalize before reporting so a malformed native activator can
            // never submit an enclosing Form while initialization fails.
            trigger.type = "button";
            console.error(
              "[citry-ui] CMenu activator must be a native Button with type=\"button\".",
              trigger,
            );
          }
          if (!trigger.id) {
            trigger.id = `${surface.id}-trigger`;
          }
          surface.setAttribute("aria-labelledby", trigger.id);
          const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
          const anchorName = getComputedStyle(surface)
            .getPropertyValue("--_cui-menu-anchor")
            .trim();
          if (!anchorName.startsWith("--")) {
            throw new Error("[citry-ui] CMenu could not resolve its CSS anchor name.");
          }
          trigger.style.setProperty("anchor-name", anchorName);
          surface.style.setProperty("position-anchor", anchorName);

          const allowed = {
            placement: [
              "top-start",
              "top",
              "top-end",
              "bottom-start",
              "bottom",
              "bottom-end",
            ],
            size: ["sm", "md", "lg"],
          };
          const entrySelector = "[data-citry-menu-entry]";
          const invalidEpisodes = new Set();
          const registrations = new Map();
          const submenus = new Set();
          const scheduledTasks = new Set();
          let reconciliationTimer = null;
          let active = true;
          let logicalOpen = false;
          let structureValid = false;
          let internalOpen = data.open;
          let controlled = false;
          let structuralSuppressed = false;
          let previousControlledOpen = null;
          let onOpenChange = null;
          let onAction = null;
          let pendingOpenRequest = null;
          let currentEntry = null;
          let typeahead = "";
          let typeaheadTimer = null;
          let tabTransition = false;
          let actionTransaction = false;
          let pendingForcedCloseNotice = null;
          let deferredFocusOutside = null;
          let exitAnimation = null;
          let generation = 0;
          let refreshNativeDisabledObserver = () => {};
          let authorDirectDisabled = trigger.disabled && !data.disabled;
          let committedEffectiveDisabled = trigger.matches(":disabled");
          const retainedRuntimeState = surface.__citryUiMenuRuntime ?? null;
          let handoffRecoveryReady = !retainedRuntimeState;
          let handoffRecoveryScheduled = false;
          const runtimeState = retainedRuntimeState ?? {
            open: data.open,
            currentKey: null,
            currentValue: null,
            currentIdentity: null,
            currentOrder: [],
            currentRoot: null,
            currentRoots: [],
            currentSurface: null,
            currentLevelOrder: [],
            currentLevelRoots: [],
            openSubmenuPaths: [],
            radioGroups: {},
            serverOpen: data.open,
            effectiveDisabled: false,
          };
          surface.__citryUiMenuRuntime = runtimeState;
          const sameServerOpen = runtimeState.serverOpen === data.open;
          if (retainedRuntimeState && sameServerOpen) {
            internalOpen = Boolean(runtimeState.open);
          }
          let retainedOpenSubmenuPaths = retainedRuntimeState && sameServerOpen
            ? [...(runtimeState.openSubmenuPaths ?? [])]
            : [];
          let pendingDisabledHandoff = Boolean(
            retainedRuntimeState
            && sameServerOpen
            && runtimeState.open
            && !runtimeState.effectiveDisabled
          );
          let pendingRemovedEntry = null;
          let configuration = {
            disabled: data.disabled,
            loop: data.loop,
            placement: data.placement,
            matchWidth: data.matchWidth,
            closeOnSelect: data.closeOnSelect,
            size: data.size,
          };
          const radioStateClaims = new Map();

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value, fallback) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CMenu ${name} received invalid client value `
                + `${describeValue(value)}; ${fallback}.`,
              surface,
            );
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return data[name];
          };
          const resolveChoice = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowed[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return data[name];
          };
          const resolveCallback = (name) => {
            const value = props[name];
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete(name);
              return value ?? null;
            }
            reportInvalid(name, value, "ignoring the callback");
            return null;
          };
          const scheduleTask = (callback, delay = 0) => {
            const task = setTimeout(() => {
              scheduledTasks.delete(task);
              if (active) {
                callback();
              }
            }, delay);
            scheduledTasks.add(task);
          };
          const ownsEntry = (entry) => (
            registrations.get(entry?.root) === entry
            && entry.root.isConnected
          );
          const directEntries = (container) => [...registrations.values()]
            .filter((entry) => entry.container === container && entry.root.isConnected)
            .sort((left, right) => {
              if (left.root === right.root) {
                return 0;
              }
              return left.root.compareDocumentPosition(right.root)
                & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
            });
          const flattenEntries = (container) => {
            const flattened = [];
            for (const entry of directEntries(container)) {
              if (entry.kind === "group" || entry.kind === "radio-group") {
                flattened.push(...flattenEntries(entry.root));
              } else if (entry.kind !== "separator") {
                flattened.push(entry);
              }
            }
            return flattened;
          };
          const entriesForSurface = (menuSurface) => flattenEntries(menuSurface);
          const stableIdentity = (entry) => ({
            kind: entry.kind,
            path: [...(entry.path ?? [])],
            value: entry.value,
          });
          const samePath = (left, right) => (
            left.length === right.length
            && left.every((value, index) => value === right[index])
          );
          const sameIdentity = (entry, identity) => Boolean(
            identity
            && entry.kind === identity.kind
            && entry.value === identity.value
            && samePath(entry.path ?? [], identity.path ?? [])
          );
          const identityToken = (entry) => JSON.stringify(stableIdentity(entry));
          const allActionableEntries = () => [...registrations.values()].filter((entry) => (
            entry.element && entry.kind !== "separator" && ownsEntry(entry)
          ));
          const uniqueSemanticEntry = (identity) => {
            const matches = allActionableEntries().filter((entry) => sameIdentity(entry, identity));
            return matches.length === 1 ? matches[0] : null;
          };
          const entryFromTarget = (target) => {
            const root = target?.closest?.(entrySelector);
            return root ? registrations.get(root) ?? null : null;
          };
          const isInsideTree = (target) => {
            if (!(target instanceof Node)) {
              return false;
            }
            if (
              anchoredLayerRuntime.composedContains(trigger, target)
              || anchoredLayerRuntime.composedContains(surface, target)
            ) {
              return true;
            }
            return [...submenus].some((submenu) => (
              anchoredLayerRuntime.composedContains(submenu.childSurface, target)
            ));
          };
          const updateCurrent = (entry) => {
            if (!entry || !ownsEntry(entry)) {
              return;
            }
            currentEntry = entry;
            runtimeState.currentKey = entry.key;
            runtimeState.currentValue = entry.value;
            runtimeState.currentIdentity = stableIdentity(entry);
            runtimeState.currentRoot = entry.root;
            runtimeState.currentSurface = entry.surface;
            for (const candidate of registrations.values()) {
              if (candidate.element) {
                candidate.element.tabIndex = candidate === entry ? 0 : -1;
              }
            }
          };
          const focusEntry = (entry, scroll = true) => {
            if (!entry?.element?.isConnected) {
              return;
            }
            updateCurrent(entry);
            entry.element.focus({ preventScroll: true });
            if (scroll) {
              entry.element.scrollIntoView({ block: "nearest", inline: "nearest" });
            }
          };
          const focusBoundary = (menuSurface, boundary) => {
            const entries = entriesForSurface(menuSurface);
            const entry = boundary === "last" ? entries.at(-1) : entries[0];
            if (entry) {
              focusEntry(entry);
            }
          };
          const nearestEntry = (removed, entries = entriesForSurface(removed.surface)) => {
            if (entries.length === 0) {
              return null;
            }
            const removedIdentity = stableIdentity(removed);
            const sameRoot = entries.find((entry) => (
              entry.root === removed.root && sameIdentity(entry, removedIdentity)
            ));
            if (sameRoot) {
              return sameRoot;
            }
            const oldRoots = removed.lastRoots ?? [];
            const oldOrder = removed.lastOrder ?? [];
            const oldRootIndex = oldRoots.indexOf(removed.root);
            const semanticMatches = entries.filter((entry) => (
              sameIdentity(entry, removedIdentity)
            ));
            const identityWasAmbiguous = oldOrder.filter((token) => (
              token === identityToken(removed)
            )).length > 1;
            if (!identityWasAmbiguous && semanticMatches.length === 1) {
              return semanticMatches[0];
            }
            const oldIndex = oldRootIndex >= 0
              ? oldRootIndex
              : oldOrder.indexOf(identityToken(removed));
            for (let distance = 1; distance <= oldOrder.length; distance += 1) {
              // Resolve each historical distance as a unit so a far physical
              // predecessor cannot beat a closer logical successor whose DOM
              // root was legitimately replaced by the correlated morph.
              for (const index of [oldIndex + distance, oldIndex - distance]) {
                const expectedToken = oldOrder[index];
                if (expectedToken === undefined) {
                  continue;
                }
                const physical = entries.find((entry) => (
                  entry.root === oldRoots[index]
                  && identityToken(entry) === expectedToken
                ));
                if (physical) {
                  return physical;
                }
                // Indistinguishable anonymous declarations cannot establish
                // which sibling survived by semantic token alone.
                if (identityWasAmbiguous && expectedToken === identityToken(removed)) {
                  continue;
                }
                const logical = entries.filter((entry) => (
                  identityToken(entry) === expectedToken
                ));
                if (logical.length === 1) {
                  return logical[0];
                }
              }
            }
            return oldOrder.length > 0 ? null : entries[0];
          };
          const deepestRetainedAncestor = (identity) => {
            if (!identity?.path?.length) {
              return null;
            }
            return allActionableEntries()
              .filter((entry) => entry.kind === "submenu")
              .filter((entry) => {
                const entryPath = [...entry.path, entry.value];
                return entryPath.length <= identity.path.length
                  && entryPath.every((value, index) => value === identity.path[index]);
              })
              .sort((left, right) => right.path.length - left.path.length)[0] ?? null;
          };
          const resetTypeahead = () => {
            typeahead = "";
            if (typeaheadTimer !== null) {
              clearTimeout(typeaheadTimer);
              typeaheadTimer = null;
            }
          };
          const composedParent = (node) => {
            if (node?.parentNode) {
              return node.parentNode;
            }
            const root = node?.getRootNode?.();
            return root instanceof ShadowRoot ? root.host : null;
          };
          const inheritedLanguage = (element) => {
            let current = element;
            while (current) {
              if (current instanceof Element && current.getAttribute("lang")?.trim()) {
                return current.getAttribute("lang").trim();
              }
              current = composedParent(current);
            }
            return surface.ownerDocument.documentElement.lang || undefined;
          };
          const normalizeText = (value, element) => {
            const collapsed = String(value ?? "")
              .normalize("NFKC")
              .replace(/\s+/gu, " ")
              .trim();
            try {
              return collapsed.toLocaleLowerCase(inheritedLanguage(element));
            } catch {
              return collapsed.toLowerCase();
            }
          };
          const entryText = (entry) => normalizeText(
            entry.textValue ?? entry.label?.textContent ?? "",
            entry.element,
          );
          const handleTypeahead = (event, entry) => {
            const altGraph = event.getModifierState?.("AltGraph") ?? false;
            if (
              event.isComposing
              || event.key.length !== 1
              || event.metaKey
              || (!altGraph && (event.ctrlKey || event.altKey))
            ) {
              return false;
            }
            const key = normalizeText(event.key, entry.element);
            if (!key) {
              return false;
            }
            const repeated = typeahead && [...typeahead].every((character) => character === key);
            typeahead = repeated ? key : `${typeahead}${key}`;
            if (typeaheadTimer !== null) {
              clearTimeout(typeaheadTimer);
            }
            typeaheadTimer = setTimeout(resetTypeahead, 500);
            const entries = entriesForSurface(entry.surface);
            const start = entries.indexOf(entry);
            const candidates = configuration.loop
              ? [...entries.slice(start + 1), ...entries.slice(0, start + 1)]
              : entries.slice(start + 1);
            const match = candidates.find((candidate) => entryText(candidate).startsWith(typeahead));
            if (!match) {
              return false;
            }
            focusEntry(match);
            return true;
          };

          const closeSubmenu = (submenu, options = {}) => {
            if (!submenu?.open) {
              return;
            }
            for (const child of [...submenus].filter((candidate) => candidate.parent === submenu)) {
              closeSubmenu(child, { restore: false });
            }
            submenu.open = false;
            submenu.wrapper.removeAttribute("data-open");
            submenu.trigger.setAttribute("aria-expanded", "false");
            submenu.childSurface.inert = true;
            submenu.childSurface.removeAttribute("data-open");
            if (submenu.childSurface.matches(":popover-open")) {
              submenu.childSurface.hidePopover();
            }
            layerCoordinator.unregister(submenu.layer, { cascade: true });
            submenu.stopGeometry?.();
            submenu.cancelIntent?.();
            if (options.restore && submenu.trigger.isConnected) {
              focusEntry(submenu);
            }
          };
          const closeAllSubmenus = () => {
            const open = [...submenus].filter((submenu) => submenu.open);
            for (let index = open.length - 1; index >= 0; index -= 1) {
              closeSubmenu(open[index], { restore: false });
            }
          };
          const updateTrigger = () => {
            trigger.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
            const desiredDisabled = configuration.disabled || authorDirectDisabled;
            if (trigger.disabled !== desiredDisabled) {
              trigger.disabled = desiredDisabled;
            }
          };
          const focusFallback = () => {
            if (trigger.isConnected && !trigger.matches(":disabled")) {
              trigger.focus({ preventScroll: true });
              return;
            }
            const nearestContainingModal = (start) => {
              let current = start;
              while (current) {
                if (current instanceof HTMLDialogElement && current.matches(":modal")) {
                  return current;
                }
                current = composedParent(current);
              }
              return null;
            };
            // `document.querySelectorAll()` cannot see an open ShadowRoot's
            // modal Dialog. Walk the composed ancestors so both a Dialog
            // outside the Menu's shadow and one inside it are eligible.
            const modal = nearestContainingModal(surface) ?? nearestContainingModal(trigger);
            const target = modal ?? surface.ownerDocument.body;
            const hadTabIndex = target.hasAttribute("tabindex");
            if (!hadTabIndex) {
              target.tabIndex = -1;
            }
            target.focus({ preventScroll: true });
            if (!hadTabIndex) {
              target.addEventListener("blur", () => target.removeAttribute("tabindex"), { once: true });
            }
          };
          const restoreAfterClose = (reason, source) => {
            if (["outside", "focus-outside", "tab", "ancestor"].includes(reason)) {
              return;
            }
            if (source instanceof HTMLAnchorElement) {
              return;
            }
            const activeElement = layerCoordinator.deepActiveElement();
            if (
              !isInsideTree(activeElement)
              && activeElement !== surface.ownerDocument.body
              && activeElement !== trigger
            ) {
              return;
            }
            focusFallback();
          };
          const normalizeRootClosed = (reason = "ancestor", source = surface) => {
            closeAllSubmenus();
            logicalOpen = false;
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-menu-exiting");
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            layerCoordinator.unregister(layer, { reason, source, cascade: true });
            updateTrigger();
          };
          const finishExit = (currentGeneration) => {
            if (!active || logicalOpen || currentGeneration !== generation) {
              return;
            }
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            surface.removeAttribute("data-citry-menu-exiting");
          };
          const applyRootOpen = (nextOpen, context = {}) => {
            if (nextOpen === logicalOpen) {
              return;
            }
            generation += 1;
            const currentGeneration = generation;
            exitAnimation?.cancel();
            exitAnimation = null;
            if (nextOpen) {
              if (
                !structureValid
                || structuralSuppressed
                || configuration.disabled
                || trigger.matches(":disabled")
              ) {
                normalizeRootClosed("ancestor", surface);
                return;
              }
              if (!layerCoordinator.mayOpen(layer)) {
                structuralSuppressed = true;
                if (!invalidEpisodes.has("ancestor-open")) {
                  invalidEpisodes.add("ancestor-open");
                  notifyOpen(false, "ancestor", surface, true);
                }
                normalizeRootClosed("ancestor", surface);
                return;
              }
              invalidEpisodes.delete("ancestor-open");
              try {
                if (!surface.matches(":popover-open")) {
                  surface.showPopover();
                }
              } catch (error) {
                console.error("[citry-ui] CMenu could not enter the top layer:", error, surface);
                normalizeRootClosed("ancestor", surface);
                return;
              }
              logicalOpen = true;
              surface.inert = false;
              surface.removeAttribute("data-citry-menu-exiting");
              surface.setAttribute("data-open", "");
              if (!layerCoordinator.register(layer)) {
                logicalOpen = false;
                surface.hidePopover();
                surface.inert = true;
                surface.removeAttribute("data-open");
                updateTrigger();
                return;
              }
              updateTrigger();
              queueMicrotask(() => {
                if (active && logicalOpen && currentGeneration === generation) {
                  context.restore?.();
                  if (context.focus === "current") {
                    if (currentEntry) {
                      focusEntry(currentEntry);
                    }
                  } else if (context.focus) {
                    focusBoundary(surface, context.focus ?? "first");
                  }
                }
              });
              return;
            }
            closeAllSubmenus();
            resetTypeahead();
            logicalOpen = false;
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.setAttribute("data-citry-menu-exiting", "");
            layerCoordinator.unregister(layer, {
              reason: context.reason ?? "ancestor",
              source: context.source ?? surface,
              cascade: true,
            });
            updateTrigger();
            restoreAfterClose(context.reason, context.source);
            const rawDuration = getComputedStyle(surface)
              .getPropertyValue("--_cui-menu-duration")
              .trim();
            const duration = rawDuration.endsWith("ms")
              ? Number.parseFloat(rawDuration)
              : rawDuration.endsWith("s")
                ? Number.parseFloat(rawDuration) * 1000
                : 0;
            if (!duration || typeof surface.animate !== "function") {
              finishExit(currentGeneration);
              return;
            }
            exitAnimation = surface.animate(
              [{ opacity: 1, transform: "none" }, { opacity: 0, transform: "scale(0.98)" }],
              {
                duration,
                easing: getComputedStyle(surface)
                  .getPropertyValue("--_cui-menu-easing")
                  .trim() || "ease",
              },
            );
            exitAnimation.finished.catch(() => {}).finally(() => {
              exitAnimation = null;
              finishExit(currentGeneration);
            });
          };
          const notifyOpen = (nextOpen, reason, source, forced = false) => {
            onOpenChange?.(nextOpen, {
              reason,
              controlled,
              forced,
              source,
            });
          };
          const requestRootOpen = (nextOpen, reason, source, focus = "first") => {
            if (nextOpen === logicalOpen) {
              return;
            }
            if (nextOpen) {
              structuralSuppressed = false;
              layerCoordinator.clearSuppression(layer);
              invalidEpisodes.delete("ancestor-open");
            }
            if (controlled) {
              pendingOpenRequest = { nextOpen, reason, source, focus };
              const repairEntry = currentEntry;
              notifyOpen(nextOpen, reason, source);
              if (!nextOpen && ["trigger", "escape"].includes(reason)) {
                queueMicrotask(() => {
                  if (
                    active
                    && logicalOpen
                    && controlled
                    && repairEntry?.element?.isConnected
                    && [trigger, surface.ownerDocument.body].includes(
                      layerCoordinator.deepActiveElement(),
                    )
                  ) {
                    focusEntry(repairEntry);
                  }
                });
              }
              return;
            }
            internalOpen = nextOpen;
            applyRootOpen(nextOpen, { reason, source, focus });
            if (logicalOpen === nextOpen) {
              notifyOpen(nextOpen, reason, source);
            }
          };
          const forceRootClose = (reason, source) => {
            const publicReason = reason === "modal" ? "ancestor" : reason;
            const wasOpen = logicalOpen;
            structuralSuppressed = true;
            if (!controlled) {
              internalOpen = false;
            }
            pendingOpenRequest = null;
            if (wasOpen) {
              applyRootOpen(false, { reason: publicReason, source });
              if (actionTransaction) {
                pendingForcedCloseNotice ??= { reason: publicReason, source };
              } else {
                notifyOpen(false, publicReason, source, true);
              }
            } else {
              normalizeRootClosed(publicReason, source);
            }
          };
          const layer = {
            surface,
            trigger,
            isEligible: () => !trigger.matches(":disabled") && structureValid,
            isOpen: () => active && logicalOpen,
            requestDismiss: (reason, source) => {
              if (actionTransaction && reason === "focus-outside") {
                deferredFocusOutside = source;
                return;
              }
              requestRootOpen(false, reason, source);
            },
            forceClose: (reason, source) => forceRootClose(reason, source),
            insideElements: [host],
          };

          const openSubmenu = (submenu, options = {}) => {
            if (
              !submenu
              || submenu.effectiveDisabled
              || !logicalOpen
              || !layerCoordinator.mayOpen(submenu.layer)
            ) {
              return;
            }
            for (const sibling of submenus) {
              if (sibling !== submenu && sibling.parent === submenu.parent && sibling.open) {
                closeSubmenu(sibling, { restore: false });
              }
            }
            if (!submenu.open) {
              submenu.choosePlacement?.();
              // Set the logical state before showPopover(). Some engines can
              // deliver the native toggle synchronously for nested popovers.
              submenu.open = true;
              try {
                submenu.childSurface.showPopover();
              } catch (error) {
                submenu.open = false;
                console.error(
                  "[citry-ui] CMenuSubmenu could not enter the top layer:",
                  error,
                  submenu.childSurface,
                );
                return;
              }
              submenu.wrapper.setAttribute("data-open", "");
              submenu.childSurface.inert = false;
              submenu.childSurface.setAttribute("data-open", "");
              submenu.trigger.setAttribute("aria-expanded", "true");
              if (!layerCoordinator.register(submenu.layer)) {
                closeSubmenu(submenu, { restore: false });
                return;
              }
              submenu.startGeometry?.();
            }
            if (options.focus) {
              focusBoundary(submenu.childSurface, options.focus);
            }
          };
          const dismissFromSubmenu = (submenu, reason, source) => {
            if (reason === "escape") {
              closeSubmenu(submenu, { restore: true });
              return;
            }
            requestRootOpen(false, reason, source);
          };
          const requestChoice = (entry, event, path) => {
            if (entry.kind === "checkbox") {
              return entry.requestChecked?.(event, path) ?? false;
            }
            if (entry.kind === "radio") {
              return entry.radioGroup?.requestValue?.(entry, event, path) ?? false;
            }
            return true;
          };
          const activate = (entry, event) => {
            if (!ownsEntry(entry) || entry.effectiveDisabled) {
              event.preventDefault();
              event.stopImmediatePropagation();
              return;
            }
            if (entry.kind === "submenu") {
              event.preventDefault();
              openSubmenu(entry, { focus: "first" });
              return;
            }
            if (entry.kind === "link") {
              if (entry.closeOnSelect ?? configuration.closeOnSelect) {
                scheduleTask(() => {
                  if (ownsEntry(entry)) {
                    requestRootOpen(false, "action", entry.element);
                  }
                });
              }
              return;
            }
            const path = [...entry.path];
            const callback = onAction;
            actionTransaction = true;
            deferredFocusOutside = null;
            let accepted = false;
            try {
              accepted = requestChoice(entry, event, path);
              if (!accepted) {
                return;
              }
              if (entry.value !== null && entry.value !== undefined) {
                callback?.(entry.value, {
                  kind: entry.kind === "item" ? "command" : entry.kind,
                  item: entry.element,
                  event,
                  path,
                });
              }
            } finally {
              actionTransaction = false;
              const forcedNotice = pendingForcedCloseNotice;
              pendingForcedCloseNotice = null;
              if (forcedNotice && active) {
                notifyOpen(false, forcedNotice.reason, forcedNotice.source, true);
              }
            }
            if (!accepted) {
              return;
            }
            if (!active || !ownsEntry(entry)) {
              return;
            }
            if (entry.closeOnSelect ?? configuration.closeOnSelect) {
              requestRootOpen(false, "action", entry.element);
            } else if (deferredFocusOutside) {
              const source = deferredFocusOutside;
              deferredFocusOutside = null;
              requestRootOpen(false, "focus-outside", source);
            }
          };
          const move = (entry, delta) => {
            const entries = entriesForSurface(entry.surface);
            const index = entries.indexOf(entry);
            if (index < 0 || entries.length === 0) {
              return;
            }
            let next = index + delta;
            if (configuration.loop) {
              next = (next + entries.length) % entries.length;
            } else {
              next = Math.max(0, Math.min(entries.length - 1, next));
            }
            focusEntry(entries[next]);
          };
          const onClick = (event) => {
            if (event.target === trigger || trigger.contains(event.target)) {
              refreshNativeDisabledObserver();
              if (trigger.type !== "button") {
                event.preventDefault();
                trigger.type = "button";
                structureValid = false;
                structuralSuppressed = true;
                normalizeRootClosed("ancestor", trigger);
                reportInvalid(
                  "activator-structure",
                  "submit",
                  'the activator requires type="button"',
                );
                return;
              }
              if (trigger.matches(":disabled")) {
                return;
              }
              requestRootOpen(!logicalOpen, "trigger", trigger);
              return;
            }
            const entry = entryFromTarget(event.target);
            if (!entry) {
              return;
            }
            activate(entry, event);
          };
          const onKeydown = (event) => {
            if (event.target === trigger || trigger.contains(event.target)) {
              if (["ArrowDown", "ArrowUp"].includes(event.key)) {
                event.preventDefault();
                requestRootOpen(true, "trigger", trigger, event.key === "ArrowUp" ? "last" : "first");
              }
              return;
            }
            const entry = entryFromTarget(event.target);
            if (!entry || entry.element !== event.target) {
              return;
            }
            const direction = getComputedStyle(entry.element).direction;
            const forward = direction === "rtl" ? "ArrowLeft" : "ArrowRight";
            const reverse = direction === "rtl" ? "ArrowRight" : "ArrowLeft";
            if (event.key === "ArrowDown") {
              event.preventDefault();
              move(entry, 1);
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              move(entry, -1);
            } else if (event.key === "Home") {
              event.preventDefault();
              focusBoundary(entry.surface, "first");
            } else if (event.key === "End") {
              event.preventDefault();
              focusBoundary(entry.surface, "last");
            } else if (event.key === forward && entry.kind === "submenu") {
              event.preventDefault();
              openSubmenu(entry, { focus: "first" });
            } else if (event.key === reverse && entry.parent) {
              event.preventDefault();
              closeSubmenu(entry.parent, { restore: true });
            } else if (event.key === "Escape" && entry.parent) {
              event.preventDefault();
              event.stopPropagation();
              closeSubmenu(entry.parent, { restore: true });
            } else if (event.key === "Tab") {
              tabTransition = true;
              scheduleTask(() => {
                tabTransition = false;
              });
              requestRootOpen(false, "tab", entry.element);
            } else if (
              event.key === " "
              && entry.element instanceof HTMLAnchorElement
              && !entry.effectiveDisabled
            ) {
              event.preventDefault();
              entry.element.click();
            } else if (event.key !== " " && handleTypeahead(event, entry)) {
              event.preventDefault();
            }
          };
          const onFocusIn = (event) => {
            if (tabTransition && !isInsideTree(event.target)) {
              tabTransition = false;
              return;
            }
            const entry = entryFromTarget(event.target);
            if (entry && entry.element === event.target) {
              updateCurrent(entry);
            }
          };
          const pointerCanHover = (event) => (
            event.pointerType === "mouse"
            || (event.pointerType === "pen" && event.buttons === 0 && event.pressure === 0)
          );
          const onPointerOver = (event) => {
            if (!pointerCanHover(event)) {
              return;
            }
            const entry = entryFromTarget(event.target);
            if (!entry || entry.effectiveDisabled) {
              return;
            }
            if (entry.element.contains(event.relatedTarget)) {
              return;
            }
            focusEntry(entry, false);
            if (entry.kind === "submenu") {
              entry.scheduleOpen?.();
            } else {
              for (const submenu of submenus) {
                if (submenu.parent === entry.parent && submenu.open) {
                  closeSubmenu(submenu, { restore: false });
                }
              }
            }
          };
          const onPointerOut = (event) => {
            if (!pointerCanHover(event)) {
              return;
            }
            const entry = entryFromTarget(event.target);
            if (entry?.element?.contains(event.relatedTarget)) {
              return;
            }
            if (entry?.kind === "submenu") {
              if (entry.open) {
                entry.beginIntent?.(event);
              } else {
                entry.cancelIntent?.();
              }
            }
          };

          const validateActivator = () => {
            const interactive = [...host.querySelectorAll(
              "button, a[href], input, select, textarea, "
                + "[contenteditable]:not([contenteditable='false']), "
                + "[tabindex]:not([tabindex='-1'])",
            )].filter((candidate) => (
              nearestHost(candidate) === host
              && !anchoredLayerRuntime.composedContains(surface, candidate)
            ));
            if (
              unsafeInitialTriggerType
              || interactive.length !== 1
              || interactive[0] !== trigger
              || trigger.type !== "button"
            ) {
              if (!invalidEpisodes.has("activator-structure")) {
                invalidEpisodes.add("activator-structure");
                console.error(
                  "[citry-ui] CMenu activator must contain exactly one native "
                    + "Button with type=\"button\" and no additional interactive content.",
                  host,
                );
              }
              return false;
            }
            invalidEpisodes.delete("activator-structure");
            return true;
          };

          const restoreRetainedSubmenus = () => {
            const paths = retainedOpenSubmenuPaths;
            retainedOpenSubmenuPaths = [];
            for (const path of paths.sort((left, right) => left.length - right.length)) {
              const submenu = [...submenus].find((entry) => (
                samePath([...entry.path, entry.value], path)
              ));
              if (submenu) {
                openSubmenu(submenu, { focus: null });
              }
            }
            // A correlated rerender can retain a focused leaf while making
            // one of its ancestor submenu declarations unavailable. Never
            // focus back into that now-inert child surface: collapse to the
            // first unavailable submenu trigger in the root-to-leaf chain.
            const ancestors = [];
            for (let parent = currentEntry?.parent; parent; parent = parent.parent) {
              ancestors.unshift(parent);
            }
            const unavailableAncestor = ancestors.find((submenu) => (
              submenu.effectiveDisabled || !submenu.open
            ));
            if (unavailableAncestor) {
              updateCurrent(unavailableAncestor);
            }
          };

          const reconcile = () => {
            const rootEntries = entriesForSurface(surface);
            let invalid = !validateActivator();
            if (rootEntries.length === 0) {
              reportInvalid("items", null, "a Menu requires at least one actionable item");
              invalid = true;
            } else {
              invalidEpisodes.delete("items");
            }
            const values = new Set();
            for (const entry of registrations.values()) {
              entry.refresh?.();
              if (entry.value !== null && entry.value !== undefined) {
                const level = `${entry.surface.id}:${entry.value}`;
                if (values.has(level)) {
                  invalid = true;
                }
                values.add(level);
              }
              entry.lastOrder = entriesForSurface(entry.surface).map(identityToken);
              entry.lastRoots = entriesForSurface(entry.surface).map((candidate) => candidate.root);
              if (entry.validate?.() === false) {
                invalid = true;
              }
            }
            if (invalid) {
              const wasOpen = logicalOpen;
              reportInvalid("structure", null, "the settled Menu structure is invalid");
              structureValid = false;
              structuralSuppressed = true;
              pendingOpenRequest = null;
              if (!controlled) {
                internalOpen = false;
              }
              surface.removeAttribute("data-citry-menu-initialized");
              normalizeRootClosed("ancestor", surface);
              if (wasOpen) {
                notifyOpen(false, "ancestor", surface, true);
              }
              return;
            }
            structureValid = true;
            invalidEpisodes.delete("structure");
            if (!currentEntry || !ownsEntry(currentEntry)) {
              const identity = runtimeState.currentIdentity;
              const priorIdentityOrder = runtimeState.currentLevelOrder?.length
                ? runtimeState.currentLevelOrder
                : runtimeState.currentOrder;
              const identityWasAmbiguous = identity && priorIdentityOrder
                ?.filter((token) => token === JSON.stringify(identity)).length > 1;
              const retainedLevelEntries = runtimeState.currentSurface?.isConnected
                ? entriesForSurface(runtimeState.currentSurface)
                : [];
              if (identity && !handoffRecoveryReady) {
                currentEntry = allActionableEntries().find((entry) => (
                  entry.root === runtimeState.currentRoot
                  && sameIdentity(entry, identity)
                )) ?? null;
                if (!currentEntry && !handoffRecoveryScheduled) {
                  // A portable correlated range can register replacement
                  // declarations over several queued client jobs. Preserve an
                  // exact retained root immediately, but defer nearest-sibling
                  // recovery for one frame so a partial collection cannot win.
                  handoffRecoveryScheduled = true;
                  scheduleTask(() => {
                    handoffRecoveryReady = true;
                    scheduleReconcile();
                  }, 16);
                }
              } else {
                currentEntry = allActionableEntries().find((entry) => (
                  entry.root === runtimeState.currentRoot
                  && sameIdentity(entry, identity)
                ))
                  ?? allActionableEntries().find((entry) => (
                    entry.key === runtimeState.currentKey
                    && sameIdentity(entry, identity)
                  ))
                  ?? (identityWasAmbiguous ? null : uniqueSemanticEntry(identity))
                  ?? (
                    pendingRemovedEntry
                      ? nearestEntry(
                        pendingRemovedEntry,
                        pendingRemovedEntry.surface.isConnected
                          ? entriesForSurface(pendingRemovedEntry.surface)
                          : rootEntries,
                      )
                      : null
                  )
                  ?? (
                    identity && retainedLevelEntries.length > 0
                      ? nearestEntry(
                        {
                          ...identity,
                          key: runtimeState.currentKey,
                          root: runtimeState.currentRoot,
                          lastOrder: runtimeState.currentLevelOrder,
                          lastRoots: runtimeState.currentLevelRoots,
                          surface: runtimeState.currentSurface,
                        },
                        retainedLevelEntries,
                      )
                      : null
                  )
                  ?? deepestRetainedAncestor(identity)
                  ?? (
                    identity && runtimeState.currentOrder?.length
                      ? nearestEntry(
                        {
                          ...identity,
                          key: runtimeState.currentKey,
                          root: runtimeState.currentRoot,
                          lastOrder: runtimeState.currentOrder,
                          lastRoots: runtimeState.currentRoots,
                          surface,
                        },
                        rootEntries,
                      )
                      : null
                  )
                  ?? uniqueSemanticEntry(identity)
                  ?? rootEntries.find((entry) => (
                    runtimeState.currentValue !== null
                    && entry.value === runtimeState.currentValue
                  ))
                  ?? rootEntries.find((entry) => (
                    entry.key === runtimeState.currentKey
                    && sameIdentity(entry, identity)
                  ))
                  ?? rootEntries[0];
              }
            }
            pendingRemovedEntry = null;
            updateCurrent(currentEntry);
            surface.setAttribute("data-citry-menu-initialized", "");
            const desiredOpen = controlled ? Boolean(props.open) : internalOpen;
            const retainedFocus = runtimeState.currentValue !== null
              || runtimeState.currentKey !== null;
            applyRootOpen(
              desiredOpen,
              pendingOpenRequest ?? {
                focus: retainedFocus ? "current" : "first",
                restore: restoreRetainedSubmenus,
              },
            );
            if (desiredOpen && logicalOpen) {
              scheduleTask(() => {
                restoreRetainedSubmenus();
                if (currentEntry) {
                  focusEntry(currentEntry);
                }
              });
            }
            pendingOpenRequest = null;
          };
          const scheduleReconcile = () => {
            if (reconciliationTimer !== null) {
              return;
            }
            reconciliationTimer = setTimeout(() => {
              reconciliationTimer = null;
              reconcile();
            }, 0);
          };
          const context = {
            surface,
            container: surface,
            path: [],
            parentSubmenu: null,
            radioGroup: null,
            rootLayer: layer,
            register(entry) {
              registrations.set(entry.root, entry);
              scheduleReconcile();
              return () => {
                if (registrations.get(entry.root) !== entry) {
                  return;
                }
                if (entry.kind === "submenu") {
                  closeSubmenu(entry, { restore: false });
                  submenus.delete(entry);
                }
                const wasCurrent = currentEntry === entry;
                registrations.delete(entry.root);
                if (wasCurrent) {
                  runtimeState.currentIdentity = stableIdentity(entry);
                  pendingRemovedEntry = entry;
                  currentEntry = null;
                }
                scheduleReconcile();
              };
            },
            update() {
              scheduleReconcile();
            },
            child(options) {
              return {
                ...context,
                ...options,
                register: context.register,
                update: context.update,
                child: context.child,
              };
            },
            entries: directEntries,
            addSubmenu(submenu) {
              submenus.add(submenu);
            },
            openSubmenu,
            closeSubmenu,
            dismissFromSubmenu,
            size: () => configuration.size,
            defer: scheduleTask,
            claimRadioState(serverValue, path) {
              const base = JSON.stringify([path, serverValue]);
              const index = radioStateClaims.get(base) ?? 0;
              radioStateClaims.set(base, index + 1);
              const key = `${base}:${index}`;
              runtimeState.radioGroups[key] ??= {
                current: serverValue,
                serverValue,
                priorOrder: [],
                pendingRemoval: null,
                controlled: false,
              };
              return runtimeState.radioGroups[key];
            },
          };
          provide(Symbol.for("citry-ui:menu"), context);

          host.addEventListener("click", onClick, true);
          host.addEventListener("keydown", onKeydown, true);
          host.addEventListener("focusin", onFocusIn, true);
          host.addEventListener("pointerover", onPointerOver, true);
          host.addEventListener("pointerout", onPointerOut, true);
          const onToggle = (event) => {
            if (event.target !== surface) {
              return;
            }
            const nativeOpen = surface.matches(":popover-open");
            if (nativeOpen === logicalOpen || (!logicalOpen && exitAnimation)) {
              return;
            }
            if (nativeOpen) {
              surface.hidePopover();
              notifyOpen(true, "native", surface);
              return;
            }
            if (controlled) {
              if (!structureValid || !layerCoordinator.mayOpen(layer)) {
                structuralSuppressed = true;
                normalizeRootClosed(
                  layerCoordinator.blockedReason(layer) ?? "ancestor",
                  surface,
                );
              } else {
                try {
                  surface.showPopover();
                } catch {
                  structuralSuppressed = true;
                  normalizeRootClosed("ancestor", surface);
                }
              }
              notifyOpen(false, "native", surface);
              return;
            }
            internalOpen = false;
            logicalOpen = false;
            closeAllSubmenus();
            surface.inert = true;
            surface.removeAttribute("data-open");
            layerCoordinator.unregister(layer, { cascade: true });
            updateTrigger();
            notifyOpen(false, "native", surface);
          };
          surface.addEventListener("toggle", onToggle);

          effect(() => {
            const suppliedOpen = props.open;
            if (suppliedOpen === undefined || suppliedOpen === null) {
              if (controlled) {
                internalOpen = logicalOpen;
              }
              controlled = false;
              previousControlledOpen = null;
              structuralSuppressed = false;
              layerCoordinator.clearSuppression(layer);
              invalidEpisodes.delete("open");
            } else if (typeof suppliedOpen === "boolean") {
              if (previousControlledOpen === false && suppliedOpen) {
                structuralSuppressed = false;
                layerCoordinator.clearSuppression(layer);
              }
              controlled = true;
              previousControlledOpen = suppliedOpen;
              invalidEpisodes.delete("open");
            } else {
              reportInvalid("open", suppliedOpen, "releasing control from the committed state");
              controlled = false;
              previousControlledOpen = null;
              internalOpen = logicalOpen;
            }
            configuration = {
              disabled: resolveBoolean("disabled"),
              loop: resolveBoolean("loop"),
              placement: resolveChoice("placement"),
              matchWidth: resolveBoolean("matchWidth"),
              closeOnSelect: resolveBoolean("closeOnSelect"),
              size: resolveChoice("size"),
            };
            onOpenChange = resolveCallback("onOpenChange");
            onAction = resolveCallback("onAction");
            surface.dataset.placement = configuration.placement;
            surface.dataset.size = configuration.size;
            surface.toggleAttribute("data-match-width", configuration.matchWidth);
            updateTrigger();
            const effectiveDisabled = trigger.matches(":disabled");
            if (pendingDisabledHandoff && effectiveDisabled) {
              pendingDisabledHandoff = false;
              if (!controlled) {
                internalOpen = false;
              }
              normalizeRootClosed("disabled", trigger);
              focusFallback();
              notifyOpen(false, "disabled", trigger, true);
            } else if (effectiveDisabled && logicalOpen) {
              if (!controlled) {
                internalOpen = false;
              }
              applyRootOpen(false, { reason: "disabled", source: trigger });
              notifyOpen(false, "disabled", trigger, true);
            }
            pendingDisabledHandoff = false;
            committedEffectiveDisabled = effectiveDisabled;
            scheduleReconcile();
          });

          const reconcileNativeDisabled = (records = []) => {
            if (
              records.some((record) => record.type === "attributes" && record.target === trigger)
              && trigger.disabled !== (configuration.disabled || authorDirectDisabled)
            ) {
              authorDirectDisabled = trigger.disabled;
            }
            updateTrigger();
            const effectiveDisabled = trigger.matches(":disabled");
            if (effectiveDisabled && logicalOpen) {
              if (!controlled) {
                internalOpen = false;
              }
              applyRootOpen(false, { reason: "disabled", source: trigger });
              notifyOpen(false, "disabled", trigger, true);
            } else if (!effectiveDisabled && (controlled ? props.open === true : internalOpen)) {
              applyRootOpen(true, { reason: "disabled", source: trigger, focus: "first" });
            }
            committedEffectiveDisabled = effectiveDisabled;
          };
          const registerNativeDisabled = () => {
            anchoredLayerRuntime.menuDisabledObservers ??= new WeakMap();
            const rootNode = trigger.getRootNode();
            let manager = anchoredLayerRuntime.menuDisabledObservers.get(rootNode);
            if (!manager) {
              const entries = new Map();
              const observer = new MutationObserver((records) => {
                for (const [registeredTrigger, callback] of entries) {
                  const affected = records.filter((record) => {
                    if (record.target === registeredTrigger) {
                      return true;
                    }
                    if (record.target instanceof Element && record.target.contains(registeredTrigger)) {
                      return true;
                    }
                    return [...record.addedNodes, ...record.removedNodes].some((node) => (
                      node === registeredTrigger
                      || (node instanceof Element && node.contains(registeredTrigger))
                    ));
                  });
                  if (affected.length > 0) {
                    callback(affected);
                  }
                }
              });
              observer.observe(rootNode, {
                subtree: true,
                childList: true,
                attributes: true,
                attributeFilter: ["disabled"],
              });
              manager = { entries, observer };
              anchoredLayerRuntime.menuDisabledObservers.set(rootNode, manager);
            }
            manager.entries.set(trigger, reconcileNativeDisabled);
            return () => {
              manager.entries.delete(trigger);
              if (manager.entries.size === 0) {
                manager.observer.disconnect();
                anchoredLayerRuntime.menuDisabledObservers.delete(rootNode);
              }
            };
          };
          let nativeDisabledRoot = null;
          let unregisterNativeDisabled = () => {};
          refreshNativeDisabledObserver = () => {
            const nextRoot = trigger.getRootNode();
            if (nextRoot === nativeDisabledRoot) {
              return;
            }
            unregisterNativeDisabled();
            nativeDisabledRoot = nextRoot;
            unregisterNativeDisabled = registerNativeDisabled();
          };
          refreshNativeDisabledObserver();
          const structureObserver = new MutationObserver((records) => {
            const affectsAuthoredContent = records.some((record) => {
              if (record.type !== "attributes") {
                return true;
              }
              const entry = registrations.get(record.target);
              if (entry?.element === record.target) {
                return !(
                  record.attributeName === "tabindex"
                  || (record.attributeName === "href" && entry.kind === "link")
                );
              }
              return true;
            });
            if (affectsAuthoredContent) {
              scheduleReconcile();
            }
          });
          structureObserver.observe(host, {
            subtree: true,
            childList: true,
            attributes: true,
            attributeFilter: ["contenteditable", "href", "role", "tabindex", "type"],
          });

          return () => {
            active = false;
            runtimeState.open = logicalOpen;
            runtimeState.currentKey = currentEntry?.key ?? null;
            runtimeState.currentValue = currentEntry?.value ?? null;
            runtimeState.currentIdentity = currentEntry
              ? stableIdentity(currentEntry)
              : runtimeState.currentIdentity;
            runtimeState.currentOrder = entriesForSurface(surface).map(identityToken);
            runtimeState.currentRoots = entriesForSurface(surface).map((entry) => entry.root);
            if (currentEntry?.surface?.isConnected) {
              runtimeState.currentSurface = currentEntry.surface;
              runtimeState.currentLevelOrder = entriesForSurface(currentEntry.surface).map(identityToken);
              runtimeState.currentLevelRoots = entriesForSurface(currentEntry.surface)
                .map((entry) => entry.root);
            }
            runtimeState.openSubmenuPaths = [...submenus]
              .filter((submenu) => submenu.open)
              .map((submenu) => [...submenu.path, submenu.value]);
            runtimeState.serverOpen = data.open;
            // Read this generation's committed configuration, not the live
            // retained Button attribute: a correlated morph may already have
            // applied the next generation's server-disabled attribute before
            // this cleanup runs.
            runtimeState.effectiveDisabled = committedEffectiveDisabled;
            unregisterNativeDisabled();
            structureObserver.disconnect();
            host.removeEventListener("click", onClick, true);
            host.removeEventListener("keydown", onKeydown, true);
            host.removeEventListener("focusin", onFocusIn, true);
            host.removeEventListener("pointerover", onPointerOver, true);
            host.removeEventListener("pointerout", onPointerOut, true);
            surface.removeEventListener("toggle", onToggle);
            closeAllSubmenus();
            generation += 1;
            exitAnimation?.cancel();
            resetTypeahead();
            if (reconciliationTimer !== null) {
              clearTimeout(reconciliationTimer);
            }
            for (const task of scheduledTasks) {
              clearTimeout(task);
            }
            scheduledTasks.clear();
            layerCoordinator.unregister(layer, { cascade: true });
            if (surface.matches(":popover-open")) {
              surface.hidePopover();
            }
            surface.inert = true;
            surface.removeAttribute("data-open");
            surface.removeAttribute("data-citry-menu-exiting");
            surface.removeAttribute("data-citry-menu-initialized");
            trigger.setAttribute("aria-expanded", "false");
            registrations.clear();
            submenus.clear();
          };
        },
      });
    """
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-menu-host) {
          display: contents;
        }

        :where(.cui-menu) {
          --_cui-menu-background: var(--cui-menu-background, Canvas);
          --_cui-menu-foreground: var(--cui-menu-foreground, CanvasText);
          --_cui-menu-muted-color: var(
            --cui-menu-muted-color,
            color-mix(in srgb, var(--_cui-menu-foreground) 72%, transparent)
          );
          --_cui-menu-border-color: var(
            --cui-menu-border-color,
            color-mix(in srgb, CanvasText 18%, transparent)
          );
          --_cui-menu-border-width: var(--cui-menu-border-width, 1px);
          --_cui-menu-radius: var(--cui-menu-radius, 0.75rem);
          --_cui-menu-shadow: var(
            --cui-menu-shadow,
            0 0.75rem 2rem rgb(15 23 42 / 18%)
          );
          --_cui-menu-submenu-shadow: var(
            --cui-menu-submenu-shadow,
            0 1rem 2.5rem rgb(15 23 42 / 22%)
          );
          --_cui-menu-inline-size: var(--cui-menu-inline-size, 14rem);
          --_cui-menu-min-inline-size: var(--cui-menu-min-inline-size, 10rem);
          --_cui-menu-max-inline-size: var(
            --cui-menu-max-inline-size,
            calc(100dvi - 1rem)
          );
          --_cui-menu-max-block-size: var(
            --cui-menu-max-block-size,
            min(24rem, calc(100dvb - 1rem))
          );
          --_cui-menu-padding: var(--cui-menu-padding, 0.375rem);
          --_cui-menu-item-block-size: var(--cui-menu-item-block-size, 2.25rem);
          --_cui-menu-item-padding-inline: var(
            --cui-menu-item-padding-inline,
            0.625rem
          );
          --_cui-menu-item-gap: var(--cui-menu-item-gap, 0.625rem);
          --_cui-menu-item-radius: var(--cui-menu-item-radius, 0.5rem);
          --_cui-menu-hover-background: var(
            --cui-menu-hover-background,
            color-mix(in srgb, CanvasText 8%, transparent)
          );
          --_cui-menu-focus-background: var(
            --cui-menu-focus-background,
            light-dark(#175cd3, #84adff)
          );
          --_cui-menu-focus-foreground: var(
            --cui-menu-focus-foreground,
            light-dark(#ffffff, #101828)
          );
          --_cui-menu-focus-outline-color: var(
            --cui-menu-focus-outline-color,
            light-dark(#175cd3, #84adff)
          );
          --_cui-menu-danger-color: var(
            --cui-menu-danger-color,
            light-dark(#b42318, #fda29b)
          );
          --_cui-menu-disabled-opacity: var(--cui-menu-disabled-opacity, 0.5);
          --_cui-menu-offset: var(--cui-menu-offset, 0.375rem);
          --_cui-menu-submenu-offset: var(--cui-menu-submenu-offset, 0.25rem);
          --_cui-menu-duration: var(--cui-menu-duration, 120ms);
          --_cui-menu-easing: var(
            --cui-menu-easing,
            cubic-bezier(0.2, 0.8, 0.2, 1)
          );

          box-sizing: border-box;
          position: fixed;
          position-anchor: var(--_cui-menu-anchor);
          position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
          position-visibility: anchors-visible;
          display: block;
          inline-size: min(
            var(--_cui-menu-inline-size),
            var(--_cui-menu-max-inline-size)
          );
          max-inline-size: var(--_cui-menu-max-inline-size);
          max-block-size: var(--_cui-menu-max-block-size);
          margin: 0;
          padding: var(--_cui-menu-padding);
          overflow: auto;
          border: var(--_cui-menu-border-width) solid var(--_cui-menu-border-color);
          border-radius: var(--_cui-menu-radius);
          background: var(--_cui-menu-background);
          color: var(--_cui-menu-foreground);
          box-shadow: var(--_cui-menu-shadow);
          font-family: ui-sans-serif, system-ui, sans-serif;
          line-height: 1.35;
          overscroll-behavior: contain;
        }

        :where(.cui-menu[data-size="sm"]) {
          --_cui-menu-item-block-size: var(--cui-menu-item-block-size, 2rem);
          --_cui-menu-item-padding-inline: var(
            --cui-menu-item-padding-inline,
            0.5rem
          );
          font-size: 0.875rem;
        }

        :where(.cui-menu[data-size="lg"]) {
          --_cui-menu-item-block-size: var(--cui-menu-item-block-size, 2.5rem);
          --_cui-menu-item-padding-inline: var(
            --cui-menu-item-padding-inline,
            0.75rem
          );
          font-size: 1.0625rem;
        }

        :where(
          .cui-menu:not(:popover-open):not([data-open]):not([data-citry-menu-exiting])
        ) {
          display: none;
        }

        :where(.cui-menu[data-open]:not(:popover-open)) {
          position: static;
          display: block;
          inline-size: min(100%, var(--_cui-menu-max-inline-size));
          margin-block: 0.5rem;
        }

        :where(.cui-menu[data-citry-menu-exiting]) {
          pointer-events: none;
          user-select: none;
        }

        :where(.cui-menu[data-placement="bottom-start"]) {
          position-area: block-end span-inline-end;
          margin-block-start: var(--_cui-menu-offset);
        }

        :where(.cui-menu[data-placement="bottom"]) {
          position-area: block-end;
          margin-block-start: var(--_cui-menu-offset);
        }

        :where(.cui-menu[data-placement="bottom-end"]) {
          position-area: block-end span-inline-start;
          margin-block-start: var(--_cui-menu-offset);
        }

        :where(.cui-menu[data-placement="top-start"]) {
          position-area: block-start span-inline-end;
          margin-block-end: var(--_cui-menu-offset);
        }

        :where(.cui-menu[data-placement="top"]) {
          position-area: block-start;
          margin-block-end: var(--_cui-menu-offset);
        }

        :where(.cui-menu[data-placement="top-end"]) {
          position-area: block-start span-inline-start;
          margin-block-end: var(--_cui-menu-offset);
        }

        :where(.cui-menu[data-match-width]) {
          inline-size: min(anchor-size(width), var(--_cui-menu-max-inline-size));
          min-inline-size: 0;
        }

        :where(.cui-menu--submenu) {
          box-shadow: var(--_cui-menu-submenu-shadow);
        }

        :where(.cui-menu--submenu[data-citry-menu-side="inline-end"]) {
          position-area: inline-end span-block-end;
          margin-inline-start: var(--_cui-menu-submenu-offset);
        }

        :where(.cui-menu--submenu[data-citry-menu-side="inline-start"]) {
          position-area: inline-start span-block-end;
          margin-inline-end: var(--_cui-menu-submenu-offset);
        }

        :where(.cui-menu--submenu[data-citry-menu-side="block-end"]) {
          position-area: block-end;
          margin-block-start: var(--_cui-menu-submenu-offset);
        }

        :where(.cui-menu--submenu[data-citry-menu-side="block-start"]) {
          position-area: block-start;
          margin-block-end: var(--_cui-menu-submenu-offset);
        }

        :where(.cui-menu__item),
        :where(.cui-menu__submenu-trigger) {
          box-sizing: border-box;
          display: grid;
          grid-template-areas: "copy";
          grid-template-columns: minmax(0, 1fr);
          inline-size: 100%;
          min-inline-size: 0;
          min-block-size: var(--_cui-menu-item-block-size);
          align-items: center;
          gap: var(--_cui-menu-item-gap);
          padding-block: 0.375rem;
          padding-inline: var(--_cui-menu-item-padding-inline);
          border: 0;
          border-radius: var(--_cui-menu-item-radius);
          background: transparent;
          color: inherit;
          font: inherit;
          line-height: inherit;
          text-align: start;
          text-decoration: none;
          cursor: default;
        }

        :where(.cui-menu__item, .cui-menu__submenu-trigger):has(
          > .cui-menu__item-start
        ):not(:has(> .cui-menu__choice-indicator)):not(:has(> .cui-menu__item-end)) {
          grid-template-areas: "start copy";
          grid-template-columns: auto minmax(0, 1fr);
        }

        :where(.cui-menu__item, .cui-menu__submenu-trigger):has(
          > .cui-menu__item-end
        ):not(:has(> .cui-menu__choice-indicator)):not(:has(> .cui-menu__item-start)) {
          grid-template-areas: "copy end";
          grid-template-columns: minmax(0, 1fr) auto;
        }

        :where(.cui-menu__item, .cui-menu__submenu-trigger):has(
          > .cui-menu__item-start
        ):has(> .cui-menu__item-end):not(:has(> .cui-menu__choice-indicator)) {
          grid-template-areas: "start copy end";
          grid-template-columns: auto minmax(0, 1fr) auto;
        }

        :where(.cui-menu__item):has(> .cui-menu__choice-indicator) {
          grid-template-areas: "choice copy";
          grid-template-columns: auto minmax(0, 1fr);
        }

        :where(.cui-menu__item):has(> .cui-menu__choice-indicator):has(
          > .cui-menu__item-start
        ):not(:has(> .cui-menu__item-end)) {
          grid-template-areas: "choice start copy";
          grid-template-columns: auto auto minmax(0, 1fr);
        }

        :where(.cui-menu__item):has(> .cui-menu__choice-indicator):has(
          > .cui-menu__item-end
        ):not(:has(> .cui-menu__item-start)) {
          grid-template-areas: "choice copy end";
          grid-template-columns: auto minmax(0, 1fr) auto;
        }

        :where(.cui-menu__item):has(> .cui-menu__choice-indicator):has(
          > .cui-menu__item-start
        ):has(> .cui-menu__item-end) {
          grid-template-areas: "choice start copy end";
          grid-template-columns: auto auto minmax(0, 1fr) auto;
        }

        :where(.cui-menu__item:hover),
        :where(.cui-menu__submenu-trigger:hover) {
          background: var(--_cui-menu-hover-background);
        }

        :where(.cui-menu__item:focus),
        :where(.cui-menu__submenu-trigger:focus) {
          outline: 2px solid var(--_cui-menu-focus-outline-color);
          outline-offset: -2px;
          background: var(--_cui-menu-focus-background);
          color: var(--_cui-menu-focus-foreground);
        }

        :where(.cui-menu__item[data-intent="danger"]),
        :where(.cui-menu__submenu-trigger[data-intent="danger"]) {
          color: var(--_cui-menu-danger-color);
        }

        :where(.cui-menu__item[data-disabled]),
        :where(.cui-menu__submenu-trigger[data-disabled]) {
          opacity: var(--_cui-menu-disabled-opacity);
          cursor: not-allowed;
        }

        :where(.cui-menu__item-copy) {
          display: grid;
          grid-area: copy;
          min-inline-size: 0;
          gap: 0.125rem;
        }

        :where(.cui-menu__item-label) {
          min-inline-size: 0;
          overflow-wrap: anywhere;
        }

        :where(.cui-menu__item-description),
        :where(.cui-menu__group-label),
        :where(.cui-menu__item-end) {
          color: var(--_cui-menu-muted-color);
          font-size: 0.8125em;
        }

        :where(.cui-menu__item:focus),
        :where(.cui-menu__submenu-trigger:focus),
        :where(.cui-menu__item:focus .cui-menu__item-description),
        :where(.cui-menu__item:focus .cui-menu__item-end),
        :where(.cui-menu__submenu-trigger:focus .cui-menu__item-description),
        :where(.cui-menu__submenu-trigger:focus .cui-menu__item-end) {
          color: var(--_cui-menu-focus-foreground);
        }

        :where(.cui-menu__item-start),
        :where(.cui-menu__item-end),
        :where(.cui-menu__choice-indicator) {
          display: inline-grid;
          flex: none;
          inline-size: 1.125em;
          block-size: 1.125em;
          place-items: center;
        }

        :where(.cui-menu__item-start) {
          grid-area: start;
        }

        :where(.cui-menu__item-end) {
          grid-area: end;
        }

        :where(.cui-menu__choice-indicator) {
          grid-area: choice;
        }

        :where(.cui-menu__item-start > svg),
        :where(.cui-menu__item-end > svg),
        :where(.cui-menu__choice-indicator > svg) {
          display: block;
          inline-size: 100%;
          block-size: 100%;
        }

        :where(.cui-menu__choice-indicator) {
          visibility: hidden;
        }

        :where(.cui-menu__item[data-checked="true"] > .cui-menu__choice-indicator),
        :where(.cui-menu__item[data-checked="mixed"] > .cui-menu__choice-indicator) {
          visibility: visible;
        }

        :where(.cui-menu__item[data-checked="mixed"] > .cui-menu__choice-indicator > svg) {
          transform: rotate(45deg) scale(0.65);
        }

        :where(.cui-menu__choice-indicator--radio) {
          border: 0.125rem solid currentColor;
          border-radius: 50%;
        }

        :where(
          .cui-menu__item[data-checked="true"] > .cui-menu__choice-indicator--radio
        )::after {
          inline-size: 0.4em;
          block-size: 0.4em;
          border-radius: 50%;
          background: currentColor;
          content: "";
        }

        :where(.cui-menu__group),
        :where(.cui-menu__radio-group) {
          display: grid;
          min-inline-size: 0;
        }

        :where(.cui-menu__group-label) {
          padding-block: 0.5rem 0.25rem;
          padding-inline: var(--_cui-menu-item-padding-inline);
          font-weight: 700;
          overflow-wrap: anywhere;
        }

        :where(.cui-menu__separator) {
          block-size: var(--_cui-menu-border-width);
          margin-block: 0.375rem;
          margin-inline: 0.25rem;
          border: 0;
          background: var(--_cui-menu-border-color);
        }

        :where(.cui-menu__submenu) {
          display: contents;
        }

        :where(.cui-menu__measurement) {
          position: absolute;
          inline-size: var(--_cui-menu-min-inline-size);
          block-size: 0;
          overflow: hidden;
          visibility: hidden;
          pointer-events: none;
        }

        :where(
          .cui-menu__submenu[data-citry-menu-physical-side="inline-start"]
          > .cui-menu__submenu-trigger
          .cui-menu__submenu-chevron
        ) {
          transform: rotate(180deg);
        }

        :where(
          .cui-menu__submenu[data-citry-menu-physical-side="block-start"]
          > .cui-menu__submenu-trigger
          .cui-menu__submenu-chevron
        ) {
          transform: rotate(-90deg);
        }

        :where(
          .cui-menu__submenu[data-citry-menu-physical-side="block-end"]
          > .cui-menu__submenu-trigger
          .cui-menu__submenu-chevron
        ) {
          transform: rotate(90deg);
        }

        @media (prefers-reduced-motion: reduce) {
          :where(.cui-menu) {
            --_cui-menu-duration: 0ms;
          }
        }

        @media (forced-colors: active) {
          :where(.cui-menu) {
            --_cui-menu-border-color: CanvasText;
            --_cui-menu-hover-background: Canvas;
            --_cui-menu-focus-background: Highlight;
            --_cui-menu-focus-foreground: HighlightText;
            box-shadow: none;
          }

          :where(.cui-menu__choice-indicator--radio) {
            forced-color-adjust: none;
          }
        }

        @media print {
          :where(.cui-menu) {
            position: static;
            display: none;
            inline-size: auto;
            max-inline-size: none;
            max-block-size: none;
            margin-block: 1rem;
            overflow: visible;
            border-color: currentColor;
            background: transparent;
            color: #000000;
            box-shadow: none;
          }

          :where(.cui-menu[data-open]) {
            display: block;
          }
        }
      }
    """


_MENU_ITEM_JS = r"""
      $component({
        props: {
          disabled: {},
          closeOnSelect: {},
          intent: {},
          textValue: {},
          checked: {},
          onCheckedChange: {},
        },
        init: ({ els, data, props, effect, inject }) => {
          const root = els[0];
          const context = inject(Symbol.for("citry-ui:menu"), null);
          if (!context) {
            console.error(
              `[citry-ui] ${data.componentName} requires the nearest CMenu client context.`,
              root,
            );
            return;
          }
          const label = root.querySelector(
            ':scope > .cui-menu__item-copy > [data-citry-ui-part="menu-item-label"]',
          );
          const description = root.querySelector(
            ':scope > .cui-menu__item-copy > '
              + '[data-citry-ui-part="menu-item-description"]',
          );
          const contentRegions = [
            root.querySelector(':scope > [data-citry-ui-part="menu-item-start"]'),
            label,
            description,
            root.querySelector(':scope > [data-citry-ui-part="menu-item-end"]'),
          ].filter(Boolean);
          if (!label) {
            console.error(`[citry-ui] ${data.componentName} could not resolve its label.`, root);
            return;
          }
          const invalidEpisodes = new Set();
          let controlledChecked = false;
          const runtimeState = root.__citryUiMenuItemRuntime ?? {
            checked: data.checked,
            serverChecked: data.checked,
          };
          root.__citryUiMenuItemRuntime = runtimeState;
          let committedChecked = runtimeState.serverChecked === data.checked
            ? runtimeState.checked
            : data.checked;
          let onCheckedChange = null;

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value, fallback) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] ${data.componentName} ${name} received invalid client value `
                + `${describeValue(value)}; ${fallback}.`,
              root,
            );
          };
          const booleanValue = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value, "using the server-rendered fallback");
            return fallback;
          };
          const optionalBoolean = () => {
            const value = props.closeOnSelect === undefined
              ? data.closeOnSelect
              : props.closeOnSelect;
            if (value === null || typeof value === "boolean") {
              invalidEpisodes.delete("closeOnSelect");
              return value;
            }
            reportInvalid("closeOnSelect", value, "using the server-rendered fallback");
            return data.closeOnSelect;
          };
          const intentValue = () => {
            const value = props.intent === undefined ? data.intent : props.intent;
            if (["default", "danger"].includes(value)) {
              invalidEpisodes.delete("intent");
              return value;
            }
            reportInvalid("intent", value, "using the server-rendered fallback");
            return data.intent;
          };
          const textValue = () => {
            const value = props.textValue === undefined ? data.textValue : props.textValue;
            if (value === null) {
              invalidEpisodes.delete("textValue");
              return value;
            }
            const normalized = canonicalString(value);
            if (normalized !== null) {
              invalidEpisodes.delete("textValue");
              return normalized;
            }
            reportInvalid("textValue", value, "using the server-rendered fallback");
            return data.textValue;
          };
          const checkedValue = () => {
            const supplied = props.checked;
            if (supplied === undefined || supplied === null) {
              if (controlledChecked) {
                committedChecked = entry.checked;
              }
              controlledChecked = false;
              invalidEpisodes.delete("checked");
              return committedChecked;
            }
            if (typeof supplied === "boolean" || supplied === "mixed") {
              controlledChecked = true;
              invalidEpisodes.delete("checked");
              return supplied;
            }
            reportInvalid("checked", supplied, "releasing control from the committed state");
            controlledChecked = false;
            return committedChecked;
          };
          const callbackValue = () => {
            const value = props.onCheckedChange;
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete("onCheckedChange");
              return value ?? null;
            }
            reportInvalid("onCheckedChange", value, "ignoring the callback");
            return null;
          };
          const canonicalString = (value) => (
            typeof value === "string" && !value.includes("\0")
              ? value.replace(/\r\n?/g, "\n")
              : null
          );
          const applyState = () => {
            root.toggleAttribute("data-disabled", entry.effectiveDisabled);
            if (entry.effectiveDisabled) {
              root.setAttribute("aria-disabled", "true");
              if (root instanceof HTMLAnchorElement) {
                root.removeAttribute("href");
              }
            } else {
              root.removeAttribute("aria-disabled");
              if (root instanceof HTMLAnchorElement && data.href !== null) {
                root.setAttribute("href", data.href);
              }
            }
            if (entry.kind === "item" || entry.kind === "link") {
              root.dataset.intent = entry.intent;
            }
            if (entry.kind === "checkbox") {
              root.setAttribute("aria-checked", String(entry.checked));
              root.dataset.checked = String(entry.checked);
            }
            if (entry.kind === "radio") {
              root.setAttribute("aria-checked", entry.checked ? "true" : "false");
              root.dataset.checked = entry.checked ? "true" : "false";
            }
          };
          const forbiddenContent = () => {
            const selector = [
              "a[href]",
              "button",
              "input",
              "select",
              "textarea",
              "[contenteditable]:not([contenteditable='false'])",
              "[tabindex]:not([tabindex='-1'])",
              "[role='menuitem']",
              "[role='menuitemcheckbox']",
              "[role='menuitemradio']",
            ].join(",");
            return contentRegions.some((region) => region.querySelector(selector));
          };
          const entry = {
            root,
            element: root,
            label,
            description,
            key: data.key,
            kind: data.kind === "item" && data.href !== null ? "link" : data.kind,
            value: data.value,
            href: data.href,
            surface: context.surface,
            container: context.container,
            path: [...context.path],
            parent: context.parentSubmenu,
            radioGroup: context.radioGroup,
            ownDisabled: data.disabled,
            effectiveDisabled: data.disabled,
            closeOnSelect: data.closeOnSelect,
            intent: data.intent,
            textValue: data.textValue,
            checked: data.checked,
            refresh() {
              entry.effectiveDisabled = booleanValue("disabled", data.disabled);
              entry.closeOnSelect = optionalBoolean();
              entry.textValue = textValue();
              if (entry.kind === "item" || entry.kind === "link") {
                entry.intent = intentValue();
              }
              if (entry.kind === "checkbox") {
                entry.checked = checkedValue();
                onCheckedChange = callbackValue();
              }
              applyState();
            },
            validate() {
              if (forbiddenContent()) {
                console.error(
                  `[citry-ui] ${data.componentName} content must remain noninteractive.`,
                  root,
                );
                return false;
              }
              return true;
            },
            requestChecked(event, path) {
              if (entry.kind !== "checkbox") {
                return true;
              }
              const previous = entry.checked;
              const requested = previous === "mixed" ? true : !previous;
              const callback = onCheckedChange;
              if (!controlledChecked) {
                committedChecked = requested;
                entry.checked = requested;
                applyState();
              }
              callback?.(requested, {
                checked: requested,
                previousChecked: previous,
                controlled: controlledChecked,
                item: root,
                event,
                path: [...path],
              });
              return true;
            },
            setRadioChecked(checked) {
              entry.checked = checked;
              applyState();
            },
          };
          const unregister = context.register(entry);
          effect(() => {
            entry.refresh();
            context.update(entry);
          });
          return () => {
            if (entry.kind === "checkbox") {
              runtimeState.checked = entry.checked;
              runtimeState.serverChecked = data.checked;
            }
            unregister();
          };
        },
      });
    """


class CMenuItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str | None = None
        href: str | None = None
        disabled: bool = False
        close_on_select: bool | None = None
        intent: CMenuIntent = "default"
        text_value: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CMenuItemDefaultSlotData]
        start: SlotInput[CMenuItemStartSlotData] | None = None
        description: SlotInput[CMenuItemDescriptionSlotData] | None = None
        end: SlotInput[CMenuItemEndSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return _item_snapshot(self, "CMenuItem", kwargs, kind="item")

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = _item_snapshot(self, "CMenuItem", kwargs, kind="item")
        return {
            "componentName": "CMenuItem",
            "key": self.id,
            "kind": "item",
            "value": snapshot["value"],
            "href": snapshot["href"],
            "disabled": snapshot["disabled"],
            "closeOnSelect": snapshot["close_on_select"],
            "intent": snapshot["intent"],
            "textValue": snapshot["text_value"],
            "checked": None,
        }

    template = """
      <c-element
        c-is="root_tag"
        class="cui-menu__item"
        c-type="'button' if root_tag == 'button' else None"
        c-href="href if not disabled else None"
        role="menuitem"
        tabindex="-1"
        c-aria-labelledby="label_id"
        c-aria-describedby="described_by"
        c-aria-disabled="'true' if disabled else None"
        c-data-disabled="disabled"
        c-data-intent="intent"
        c-bind="attrs"
        data-citry-menu-entry
        data-citry-ui-part="menu-item"
      >
        <c-if cond="has_start">
          <span
            class="cui-menu__item-start"
            aria-hidden="true"
            data-citry-ui-part="menu-item-start"
          >
            <c-slot name="start" />
          </span>
        </c-if>
        <span class="cui-menu__item-copy">
          <span
            class="cui-menu__item-label"
            c-id="label_id"
            data-citry-ui-part="menu-item-label"
          >
            <c-slot required />
          </span>
          <c-if cond="has_description">
            <span
              class="cui-menu__item-description"
              c-id="description_id"
              data-citry-ui-part="menu-item-description"
            >
              <c-slot name="description" />
            </span>
          </c-if>
        </span>
        <c-if cond="has_end">
          <span
            class="cui-menu__item-end"
            aria-hidden="true"
            data-citry-ui-part="menu-item-end"
          >
            <c-slot name="end" />
          </span>
        </c-if>
      </c-element>
    """

    js = _MENU_ITEM_JS


class CMenuCheckboxItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        checked: CMenuChecked = False
        disabled: bool = False
        close_on_select: bool | None = None
        text_value: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CMenuItemDefaultSlotData]
        start: SlotInput[CMenuItemStartSlotData] | None = None
        description: SlotInput[CMenuItemDescriptionSlotData] | None = None
        end: SlotInput[CMenuItemEndSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        snapshot = _item_snapshot(self, "CMenuCheckboxItem", kwargs, kind="checkbox")
        snapshot["indicator"] = _resolve_registered_icon("check", "CMenuCheckboxItem indicator")
        return snapshot

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = _item_snapshot(self, "CMenuCheckboxItem", kwargs, kind="checkbox")
        return {
            "componentName": "CMenuCheckboxItem",
            "key": self.id,
            "kind": "checkbox",
            "value": snapshot["value"],
            "href": None,
            "disabled": snapshot["disabled"],
            "closeOnSelect": snapshot["close_on_select"],
            "intent": "default",
            "textValue": snapshot["text_value"],
            "checked": snapshot["checked"],
        }

    template = """
      <button
        class="cui-menu__item"
        type="button"
        role="menuitemcheckbox"
        tabindex="-1"
        c-aria-labelledby="label_id"
        c-aria-describedby="described_by"
        c-aria-disabled="'true' if disabled else None"
        c-aria-checked="checked_text"
        c-data-disabled="disabled"
        c-data-checked="checked_text"
        c-bind="attrs"
        data-citry-menu-entry
        data-citry-ui-part="menu-item"
      >
        <span
          class="cui-menu__choice-indicator"
          aria-hidden="true"
          data-citry-ui-part="menu-choice-indicator"
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
        <c-if cond="has_start">
          <span
            class="cui-menu__item-start"
            aria-hidden="true"
            data-citry-ui-part="menu-item-start"
          >
            <c-slot name="start" />
          </span>
        </c-if>
        <span class="cui-menu__item-copy">
          <span
            class="cui-menu__item-label"
            c-id="label_id"
            data-citry-ui-part="menu-item-label"
          >
            <c-slot required />
          </span>
          <c-if cond="has_description">
            <span
              class="cui-menu__item-description"
              c-id="description_id"
              data-citry-ui-part="menu-item-description"
            >
              <c-slot name="description" />
            </span>
          </c-if>
        </span>
        <c-if cond="has_end">
          <span
            class="cui-menu__item-end"
            aria-hidden="true"
            data-citry-ui-part="menu-item-end"
          >
            <c-slot name="end" />
          </span>
        </c-if>
      </button>
    """

    js = _MENU_ITEM_JS


class CMenuRadioItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        close_on_select: bool | None = None
        text_value: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CMenuItemDefaultSlotData]
        start: SlotInput[CMenuItemStartSlotData] | None = None
        description: SlotInput[CMenuItemDescriptionSlotData] | None = None
        end: SlotInput[CMenuItemEndSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return _item_snapshot(self, "CMenuRadioItem", kwargs, kind="radio")

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = _item_snapshot(self, "CMenuRadioItem", kwargs, kind="radio")
        return {
            "componentName": "CMenuRadioItem",
            "key": self.id,
            "kind": "radio",
            "value": snapshot["value"],
            "href": None,
            "disabled": snapshot["disabled"],
            "closeOnSelect": snapshot["close_on_select"],
            "intent": "default",
            "textValue": snapshot["text_value"],
            "checked": snapshot["checked"],
        }

    template = """
      <button
        class="cui-menu__item"
        type="button"
        role="menuitemradio"
        tabindex="-1"
        c-aria-labelledby="label_id"
        c-aria-describedby="described_by"
        c-aria-disabled="'true' if disabled else None"
        c-aria-checked="'true' if checked else 'false'"
        c-data-disabled="disabled"
        c-data-checked="'true' if checked else 'false'"
        c-bind="attrs"
        data-citry-menu-entry
        data-citry-ui-part="menu-item"
      >
        <span
          class="cui-menu__choice-indicator cui-menu__choice-indicator--radio"
          aria-hidden="true"
          data-citry-ui-part="menu-choice-indicator"
        ></span>
        <c-if cond="has_start">
          <span
            class="cui-menu__item-start"
            aria-hidden="true"
            data-citry-ui-part="menu-item-start"
          >
            <c-slot name="start" />
          </span>
        </c-if>
        <span class="cui-menu__item-copy">
          <span
            class="cui-menu__item-label"
            c-id="label_id"
            data-citry-ui-part="menu-item-label"
          >
            <c-slot required />
          </span>
          <c-if cond="has_description">
            <span
              class="cui-menu__item-description"
              c-id="description_id"
              data-citry-ui-part="menu-item-description"
            >
              <c-slot name="description" />
            </span>
          </c-if>
        </span>
        <c-if cond="has_end">
          <span
            class="cui-menu__item-end"
            aria-hidden="true"
            data-citry-ui-part="menu-item-end"
          >
            <c-slot name="end" />
          </span>
        </c-if>
      </button>
    """

    js = _MENU_ITEM_JS


class CMenuGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        label: SlotInput[CMenuGroupLabelSlotData]
        default: SlotInput[CMenuGroupDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        context = _context(self, "CMenuGroup")
        if context.registry.kind == "radio":
            msg = "CMenuRadioGroup may contain only direct CMenuRadioItem declarations."
            raise ValueError(msg)
        if context.registry.kind == "group":
            msg = "CMenuGroup cannot be nested inside another CMenuGroup."
            raise ValueError(msg)
        attrs = _copy_attrs("CMenuGroup", "attrs", kwargs.attrs)
        _validate_attrs("CMenuGroup attrs", attrs, _GROUP_OWNED_ATTRS)
        registry = _MenuRegistry(kind="group")
        _register(
            context,
            kind="group",
            render_id=self.id,
            root_tag="div",
            children=registry,
        )
        label_id = f"{context.menu_id}-group-{self.id}-label"
        self.unprovide(_MENU_CONTEXT_KEY)
        self.provide(
            _MENU_CONTEXT_KEY,
            context=_MenuServerContext(
                registry=registry,
                menu_id=context.menu_id,
                level_path=context.level_path,
            ),
        )
        return {
            "key": self.id,
            "label_id": label_id,
            "registry": registry,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"key": self.id}

    template = """
      <div
        class="cui-menu__group"
        role="group"
        c-aria-labelledby="label_id"
        c-bind="attrs"
        data-citry-menu-group
        data-citry-ui-part="menu-group"
      >
        <div
          class="cui-menu__group-label"
          c-id="label_id"
          data-citry-ui-part="menu-group-label"
        >
          <c-CInternalMenuContent>
            <c-slot name="label" required />
          </c-CInternalMenuContent>
        </div>
        <c-CInternalMenuCollection c-registry="registry">
          <c-slot required />
        </c-CInternalMenuCollection>
      </div>
    """

    js = r"""
      $component({
        init: ({ els, data, inject, provide }) => {
          const root = els[0];
          const context = inject(Symbol.for("citry-ui:menu"), null);
          if (!context) {
            console.error(
              "[citry-ui] CMenuGroup requires the nearest CMenu client context.",
              root,
            );
            return;
          }
          const label = root.querySelector(':scope > [data-citry-ui-part="menu-group-label"]');
          const entry = {
            root,
            key: data.key,
            kind: "group",
            value: null,
            surface: context.surface,
            container: context.container,
            validate() {
              const forbidden = label?.querySelector(
                "a[href], button, input, select, textarea, [contenteditable], [tabindex]",
              );
              if (forbidden) {
                console.error("[citry-ui] CMenuGroup label must remain noninteractive.", root);
                return false;
              }
              return context.entries(root).length > 0;
            },
          };
          const unregister = context.register(entry);
          provide(Symbol.for("citry-ui:menu"), context.child({ container: root }));
          return () => unregister();
        },
      });
    """


class CMenuRadioGroup(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CMenuRadioGroupDefaultSlotData]
        label: SlotInput[CMenuRadioGroupLabelSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_menu_radio_group_snapshot", None)
        if cached is not None:
            return cached
        context = _context(self, "CMenuRadioGroup")
        if context.registry.kind == "radio":
            msg = "CMenuRadioGroup cannot be nested inside another CMenuRadioGroup."
            raise ValueError(msg)
        value = _plain_identity("CMenuRadioGroup", "value", kwargs.value)
        attrs = _copy_attrs("CMenuRadioGroup", "attrs", kwargs.attrs)
        _validate_attrs("CMenuRadioGroup attrs", attrs, _GROUP_OWNED_ATTRS)
        registry = _MenuRegistry(kind="radio", selected_value=value)
        _register(
            context,
            kind="radio-group",
            render_id=self.id,
            root_tag="div",
            children=registry,
            selected_value=value,
        )
        label_id = f"{context.menu_id}-radio-{self.id}-label"
        self.unprovide(_MENU_CONTEXT_KEY)
        self.provide(
            _MENU_CONTEXT_KEY,
            context=_MenuServerContext(
                registry=registry,
                menu_id=context.menu_id,
                level_path=context.level_path,
                selected_value=value,
            ),
        )
        snapshot = {
            "key": self.id,
            "value": value,
            "label_id": label_id,
            "has_label": "label" in self.raw_slots,
            "registry": registry,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }
        self._cui_menu_radio_group_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "key": self.id,
            "value": snapshot["value"],
        }

    template = """
      <div
        class="cui-menu__radio-group"
        role="group"
        c-aria-labelledby="label_id if has_label else None"
        c-bind="attrs"
        data-citry-ui-part="menu-radio-group"
      >
        <c-if cond="has_label">
          <div
            class="cui-menu__group-label"
            c-id="label_id"
            data-citry-ui-part="menu-group-label"
          >
            <c-CInternalMenuContent>
              <c-slot name="label" />
            </c-CInternalMenuContent>
          </div>
        </c-if>
        <c-CInternalMenuCollection c-registry="registry">
          <c-slot required />
        </c-CInternalMenuCollection>
      </div>
    """

    js = r"""
      $component({
        props: {
          value: {},
          onValueChange: {},
        },
        init: ({ els, data, props, effect, inject, provide }) => {
          const root = els[0];
          const context = inject(Symbol.for("citry-ui:menu"), null);
          if (!context) {
            console.error(
              "[citry-ui] CMenuRadioGroup requires the nearest CMenu client context.",
              root,
            );
            return;
          }
          const label = root.querySelector(
            ':scope > [data-citry-ui-part="menu-group-label"]',
          );
          const invalidEpisodes = new Set();
          const runtimeState = context.claimRadioState(data.value, context.path);
          root.__citryUiMenuRadioGroupRuntime = runtimeState;
          let controlled = runtimeState.serverValue === data.value
            ? Boolean(runtimeState.controlled)
            : false;
          let committed = runtimeState.serverValue === data.value
            ? runtimeState.current
            : data.value;
          let current = committed;
          let onValueChange = null;
          let priorOrder = runtimeState.serverValue === data.value
            ? [...(runtimeState.priorOrder ?? [])]
            : [];
          let pendingRemoval = runtimeState.serverValue === data.value
            ? runtimeState.pendingRemoval
            : null;

          const reportInvalid = (name, value, fallback) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CMenuRadioGroup ${name} received invalid client value `
                + `${JSON.stringify(value)}; ${fallback}.`,
              root,
            );
          };
          const canonical = (value) => (
            typeof value === "string" && value.length > 0 && !value.includes("\0")
              ? value.replace(/\r\n?/g, "\n")
              : null
          );
          const radios = () => context.entries(root).filter((entry) => entry.kind === "radio");
          const apply = () => {
            for (const radio of radios()) {
              radio.setRadioChecked?.(radio.value === current);
            }
          };
          const notify = (requested, previous, reason, item, event, path) => {
            onValueChange?.(requested, {
              value: requested,
              previousValue: previous,
              reason,
              controlled,
              item,
              event,
              path: [...path],
            });
          };
          const removalFallback = (removed, values) => {
            const oldIndex = priorOrder.indexOf(removed);
            if (oldIndex < 0) {
              return values[0];
            }
            for (let distance = 1; distance <= priorOrder.length; distance += 1) {
              const following = priorOrder[oldIndex + distance];
              if (values.includes(following)) {
                return following;
              }
              const preceding = priorOrder[oldIndex - distance];
              if (values.includes(preceding)) {
                return preceding;
              }
            }
            return values[0];
          };
          const entry = {
            root,
            key: data.key,
            kind: "radio-group",
            value: null,
            surface: context.surface,
            container: context.container,
            requestValue(radio, event, path) {
              if (radio.value === current) {
                // Re-activating the selected radio is still an accepted Menu
                // action. It skips only the value-change callback.
                return true;
              }
              const previous = current;
              if (!controlled) {
                committed = radio.value;
                current = radio.value;
                apply();
              }
              notify(radio.value, previous, "activation", radio.element, event, path);
              return true;
            },
            refresh() {
              const available = radios();
              const values = available.map((radio) => radio.value);
              const supplied = props.value;
              const callback = props.onValueChange;
              // Child components register later in the same client activation
              // turn. Defer membership checks until that collection exists.
              if (values.length === 0) {
                return;
              }
              if (supplied === undefined || supplied === null) {
                if (controlled || pendingRemoval) {
                  committed = pendingRemoval?.requested ?? current;
                }
                controlled = false;
                current = committed;
                pendingRemoval = null;
                invalidEpisodes.delete("value");
              } else {
                const normalized = canonical(supplied);
                if (normalized !== null && values.includes(normalized)) {
                  controlled = true;
                  current = normalized;
                  pendingRemoval = null;
                  invalidEpisodes.delete("value");
                  invalidEpisodes.delete("removal");
                } else if (
                  pendingRemoval
                  && normalized === pendingRemoval.removed
                ) {
                  // A controlled owner may acknowledge a removal after a
                  // later render. Preserve the one requested fallback and do
                  // not drift or repeat the callback while waiting.
                  controlled = true;
                  current = "";
                  invalidEpisodes.delete("value");
                } else if (controlled && normalized !== null && normalized === current) {
                  // The previously valid controlled selection disappeared in
                  // this settled collection. The removal branch below owns
                  // the single fallback request and diagnostic semantics.
                  invalidEpisodes.delete("value");
                } else {
                  reportInvalid("value", supplied, "retaining the last valid selection");
                }
              }
              if (callback === undefined || callback === null || typeof callback === "function") {
                onValueChange = callback ?? null;
                invalidEpisodes.delete("onValueChange");
              } else {
                reportInvalid("onValueChange", callback, "ignoring the callback");
                onValueChange = null;
              }
              if (values.length > 0 && !values.includes(current)) {
                if (!pendingRemoval) {
                  const previous = current;
                  const requested = removalFallback(previous, values);
                  if (!controlled) {
                    committed = requested;
                    current = requested;
                  } else {
                    pendingRemoval = { removed: previous, requested };
                    current = "";
                  }
                  invalidEpisodes.add("removal");
                  context.defer(() => {
                    notify(requested, previous, "removal", null, null, context.path);
                  });
                }
              } else if (values.includes(current)) {
                invalidEpisodes.delete("removal");
                pendingRemoval = null;
              }
              priorOrder = values;
              apply();
            },
            validate() {
              const forbidden = label?.querySelector(
                "a[href], button, input, select, textarea, [contenteditable], [tabindex]",
              );
              if (forbidden) {
                console.error(
                  "[citry-ui] CMenuRadioGroup label must remain noninteractive.",
                  root,
                );
                return false;
              }
              return radios().length > 0;
            },
          };
          const unregister = context.register(entry);
          provide(
            Symbol.for("citry-ui:menu"),
            context.child({ container: root, radioGroup: entry }),
          );
          effect(() => {
            // Root reconciliation runs after all direct radio registrations in
            // this activation turn, so a valid controlled value is never
            // diagnosed merely because its child registered later.
            void props.value;
            void props.onValueChange;
            context.update(entry);
          });
          return () => {
            runtimeState.current = current || committed;
            runtimeState.serverValue = data.value;
            runtimeState.priorOrder = priorOrder;
            runtimeState.pendingRemoval = pendingRemoval;
            runtimeState.controlled = controlled;
            unregister();
          };
        },
      });
    """


class CMenuSeparator(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        context = _context(self, "CMenuSeparator")
        if context.registry.kind == "radio":
            msg = "CMenuRadioGroup may contain only direct CMenuRadioItem declarations."
            raise ValueError(msg)
        attrs = _copy_attrs("CMenuSeparator", "attrs", kwargs.attrs)
        _validate_attrs("CMenuSeparator attrs", attrs, _SEPARATOR_OWNED_ATTRS)
        _register(
            context,
            kind="separator",
            render_id=self.id,
            root_tag="hr",
        )
        return {
            "key": self.id,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {"key": self.id}

    template = """
      <hr
        class="cui-menu__separator"
        role="separator"
        c-bind="attrs"
        data-citry-menu-entry
        data-citry-ui-part="menu-separator"
      />
    """

    js = r"""
      $component({
        init: ({ els, data, inject }) => {
          const root = els[0];
          const context = inject(Symbol.for("citry-ui:menu"), null);
          if (!context) {
            console.error(
              "[citry-ui] CMenuSeparator requires the nearest CMenu client context.",
              root,
            );
            return;
          }
          const unregister = context.register({
            root,
            key: data.key,
            kind: "separator",
            value: null,
            surface: context.surface,
            container: context.container,
          });
          return () => unregister();
        },
      });
    """


class CMenuSubmenu(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        intent: CMenuIntent = "default"
        text_value: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        menu_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        label: SlotInput[CMenuSubmenuLabelSlotData]
        default: SlotInput[CMenuSubmenuDefaultSlotData]
        start: SlotInput[CMenuSubmenuStartSlotData] | None = None
        description: SlotInput[CMenuSubmenuDescriptionSlotData] | None = None
        end: SlotInput[CMenuSubmenuEndSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_menu_submenu_snapshot", None)
        if cached is not None:
            return cached

        context = _context(self, "CMenuSubmenu")
        if context.registry.kind == "radio":
            msg = "CMenuRadioGroup may contain only direct CMenuRadioItem declarations."
            raise ValueError(msg)
        value = _plain_identity("CMenuSubmenu", "value", kwargs.value)
        validate_boolean("CMenuSubmenu", "disabled", kwargs.disabled)
        intent = _plain_choice("CMenuSubmenu", "intent", kwargs.intent, _INTENTS)
        text_value = _plain_optional_string("CMenuSubmenu", "text_value", kwargs.text_value)
        if text_value is not None and "\0" in text_value:
            msg = "CMenuSubmenu text_value cannot contain U+0000."
            raise ValueError(msg)
        attrs = _copy_attrs("CMenuSubmenu", "attrs", kwargs.attrs)
        trigger_attrs = _copy_attrs("CMenuSubmenu", "trigger_attrs", kwargs.trigger_attrs)
        menu_attrs = _copy_attrs("CMenuSubmenu", "menu_attrs", kwargs.menu_attrs)
        _validate_attrs("CMenuSubmenu attrs", attrs, _SUBMENU_OWNED_ATTRS)
        _validate_attrs("CMenuSubmenu trigger_attrs", trigger_attrs, _ITEM_OWNED_ATTRS)
        _validate_attrs("CMenuSubmenu menu_attrs", menu_attrs, _SURFACE_OWNED_ATTRS)

        registry = _MenuRegistry(kind="menu")
        _register(
            context,
            kind="submenu",
            render_id=self.id,
            root_tag="div",
            value=value,
            children=registry,
        )
        token = _value_token(value)
        trigger_id = f"{context.menu_id}-submenu-trigger-{token}"
        menu_id = f"{context.menu_id}-submenu-{token}"
        label_id = f"{context.menu_id}-submenu-label-{token}"
        description_id = f"{context.menu_id}-submenu-description-{token}"
        has_description = "description" in self.raw_slots
        anchor_name = f"--_cui-menu-submenu-anchor-ref-{self.id}"
        menu_attrs_with_anchor = merge_root_attrs(
            menu_attrs,
            None,
            {"--_cui-menu-anchor": anchor_name},
        )
        self.unprovide(_MENU_CONTEXT_KEY)
        self.provide(
            _MENU_CONTEXT_KEY,
            context=_MenuServerContext(
                registry=registry,
                menu_id=menu_id,
                level_path=(*context.level_path, value),
            ),
        )
        snapshot = {
            "key": self.id,
            "value": value,
            "disabled": bool(kwargs.disabled),
            "intent": intent,
            "text_value": text_value,
            "trigger_id": trigger_id,
            "menu_id": menu_id,
            "label_id": label_id,
            "description_id": description_id,
            "described_by": description_id if has_description else None,
            "has_start": "start" in self.raw_slots,
            "has_description": has_description,
            "has_end": "end" in self.raw_slots,
            "indicator": _resolve_registered_icon("chevron-right", "CMenuSubmenu indicator"),
            "anchor_name": anchor_name,
            "registry": registry,
            "attrs": merge_root_attrs(attrs, kwargs.class_, kwargs.style),
            "trigger_attrs": merge_root_attrs(trigger_attrs, None, {"anchor-name": anchor_name}),
            "menu_attrs": menu_attrs_with_anchor,
        }
        self._cui_menu_submenu_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "key": self.id,
            "value": snapshot["value"],
            "disabled": snapshot["disabled"],
            "intent": snapshot["intent"],
            "textValue": snapshot["text_value"],
        }

    template = """
      <div
        class="cui-menu__submenu"
        role="none"
        c-bind="attrs"
        data-citry-menu-entry
        data-citry-menu-submenu
        data-citry-ui-part="menu-submenu"
      >
        <button
          class="cui-menu__item cui-menu__submenu-trigger"
          type="button"
          c-id="trigger_id"
          role="menuitem"
          tabindex="-1"
          aria-haspopup="menu"
          aria-expanded="false"
          c-aria-controls="menu_id"
          c-aria-labelledby="label_id"
          c-aria-describedby="described_by"
          c-aria-disabled="'true' if disabled else None"
          c-data-disabled="disabled"
          c-data-intent="intent"
          c-bind="trigger_attrs"
          data-citry-ui-part="menu-submenu-trigger"
        >
          <c-if cond="has_start">
            <span
              class="cui-menu__item-start"
              aria-hidden="true"
              data-citry-ui-part="menu-item-start"
            >
              <c-CInternalMenuContent>
                <c-slot name="start" />
              </c-CInternalMenuContent>
            </span>
          </c-if>
          <span class="cui-menu__item-copy">
            <span
              class="cui-menu__item-label"
              c-id="label_id"
              data-citry-ui-part="menu-item-label"
            >
              <c-CInternalMenuContent>
                <c-slot name="label" required />
              </c-CInternalMenuContent>
            </span>
            <c-if cond="has_description">
              <span
                class="cui-menu__item-description"
                c-id="description_id"
                data-citry-ui-part="menu-item-description"
              >
                <c-CInternalMenuContent>
                  <c-slot name="description" />
                </c-CInternalMenuContent>
              </span>
            </c-if>
          </span>
          <span
            class="cui-menu__item-end cui-menu__submenu-chevron"
            aria-hidden="true"
            data-citry-ui-part="menu-item-end"
          >
            <c-if cond="has_end">
              <c-CInternalMenuContent>
                <c-slot name="end" />
              </c-CInternalMenuContent>
            </c-if>
            <c-else>
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
            </c-else>
          </span>
        </button>
        <div
          class="cui-menu cui-menu--submenu"
          c-id="menu_id"
          c-aria-labelledby="trigger_id"
          inert
          c-bind="menu_attrs"
          popover="manual"
          role="menu"
          data-citry-ui-part="menu"
        >
          <c-CInternalMenuCollection c-registry="registry">
            <c-slot required />
          </c-CInternalMenuCollection>
        </div>
        <span
          class="cui-menu__measurement"
          aria-hidden="true"
          data-citry-menu-measure
        ></span>
      </div>
    """

    js = (
        ANCHORED_LAYER_RUNTIME_JS
        + r"""
      $component({
        props: {
          disabled: {},
          intent: {},
          textValue: {},
        },
        init: ({ els, data, props, effect, inject, provide }) => {
          const wrapper = els[0];
          const context = inject(Symbol.for("citry-ui:menu"), null);
          if (!context) {
            console.error(
              "[citry-ui] CMenuSubmenu requires the nearest CMenu client context.",
              wrapper,
            );
            return;
          }
          const trigger = wrapper.querySelector(
            ':scope > [data-citry-ui-part="menu-submenu-trigger"]',
          );
          const surface = wrapper.querySelector(':scope > [data-citry-ui-part="menu"]');
          const label = trigger?.querySelector(
            ':scope > .cui-menu__item-copy > [data-citry-ui-part="menu-item-label"]',
          );
          const description = trigger?.querySelector(
            ':scope > .cui-menu__item-copy > '
              + '[data-citry-ui-part="menu-item-description"]',
          );
          const probe = wrapper.querySelector(":scope > [data-citry-menu-measure]");
          if (!trigger || !surface || !label || !probe) {
            console.error("[citry-ui] CMenuSubmenu could not resolve its owned anatomy.", wrapper);
            return;
          }
          const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
          const anchorName = getComputedStyle(surface)
            .getPropertyValue("--_cui-menu-anchor")
            .trim();
          trigger.style.setProperty("anchor-name", anchorName);
          surface.style.setProperty("position-anchor", anchorName);
          const invalidEpisodes = new Set();
          let openTimer = null;
          let intentCleanup = null;
          let geometryStop = null;
          let latestGeometry = null;

          const reportInvalid = (name, value, fallback) => {
            if (invalidEpisodes.has(name)) {
              return;
            }
            invalidEpisodes.add(name);
            console.error(
              `[citry-ui] CMenuSubmenu ${name} received invalid client value `
                + `${JSON.stringify(value)}; ${fallback}.`,
              wrapper,
            );
          };
          const resolveBoolean = () => {
            const value = props.disabled === undefined ? data.disabled : props.disabled;
            if (typeof value === "boolean") {
              invalidEpisodes.delete("disabled");
              return value;
            }
            reportInvalid("disabled", value, "using the server-rendered fallback");
            return data.disabled;
          };
          const resolveIntent = () => {
            const value = props.intent === undefined ? data.intent : props.intent;
            if (["default", "danger"].includes(value)) {
              invalidEpisodes.delete("intent");
              return value;
            }
            reportInvalid("intent", value, "using the server-rendered fallback");
            return data.intent;
          };
          const resolveTextValue = () => {
            const value = props.textValue === undefined ? data.textValue : props.textValue;
            if (value === null) {
              invalidEpisodes.delete("textValue");
              return value;
            }
            if (typeof value === "string" && !value.includes("\0")) {
              invalidEpisodes.delete("textValue");
              return value.replace(/\r\n?/g, "\n");
            }
            reportInvalid("textValue", value, "using the server-rendered fallback");
            return data.textValue;
          };
          const choosePlacement = () => {
            const rect = trigger.getBoundingClientRect();
            const viewport = surface.ownerDocument.defaultView?.visualViewport;
            const left = viewport?.offsetLeft ?? 0;
            const top = viewport?.offsetTop ?? 0;
            const right = left + (viewport?.width ?? innerWidth);
            const bottom = top + (viewport?.height ?? innerHeight);
            const minimum = probe.getBoundingClientRect().width;
            const rtl = getComputedStyle(trigger).direction === "rtl";
            const inlineEnd = rtl ? rect.left - left : right - rect.right;
            const inlineStart = rtl ? right - rect.right : rect.left - left;
            let side;
            if (inlineEnd >= minimum) {
              side = "inline-end";
            } else if (inlineStart >= minimum) {
              side = "inline-start";
            } else {
              side = bottom - rect.bottom >= rect.top - top ? "block-end" : "block-start";
            }
            surface.dataset.citryMenuSide = side;
          };
          const updateGeometry = () => {
            if (!entry.open) {
              return;
            }
            const triggerRect = trigger.getBoundingClientRect();
            const surfaceRect = surface.getBoundingClientRect();
            const gap = 2;
            let side;
            if (surfaceRect.right <= triggerRect.left + gap) {
              side = "inline-start";
            } else if (surfaceRect.left >= triggerRect.right - gap) {
              side = "inline-end";
            } else if (surfaceRect.bottom <= triggerRect.top + gap) {
              side = "block-start";
            } else {
              side = "block-end";
            }
            latestGeometry = { trigger: triggerRect, surface: surfaceRect, side };
            wrapper.dataset.citryMenuPhysicalSide = side;
          };
          const geometryRuntime = (() => {
            anchoredLayerRuntime.menuGeometry ??= new WeakMap();
            const ownerDocument = surface.ownerDocument;
            let runtime = anchoredLayerRuntime.menuGeometry.get(ownerDocument);
            if (runtime) {
              return runtime;
            }
            runtime = {
              entries: new Set(),
              frame: null,
              start(item) {
                runtime.entries.add(item);
                if (runtime.frame !== null) {
                  return;
                }
                const sample = () => {
                  runtime.frame = null;
                  for (const candidate of runtime.entries) {
                    candidate.updateGeometry();
                  }
                  if (runtime.entries.size > 0) {
                    runtime.frame = requestAnimationFrame(sample);
                  }
                };
                runtime.frame = requestAnimationFrame(sample);
              },
              stop(item) {
                runtime.entries.delete(item);
                if (runtime.entries.size === 0 && runtime.frame !== null) {
                  cancelAnimationFrame(runtime.frame);
                  runtime.frame = null;
                }
              },
            };
            anchoredLayerRuntime.menuGeometry.set(ownerDocument, runtime);
            return runtime;
          })();
          const pointInPolygon = (point, points) => {
            let inside = false;
            for (let index = 0, previous = points.length - 1; index < points.length; previous = index++) {
              const currentPoint = points[index];
              const previousPoint = points[previous];
              const crosses = (currentPoint.y > point.y) !== (previousPoint.y > point.y)
                && point.x < (previousPoint.x - currentPoint.x)
                  * (point.y - currentPoint.y)
                  / (previousPoint.y - currentPoint.y)
                  + currentPoint.x;
              if (crosses) {
                inside = !inside;
              }
            }
            return inside;
          };
          const corridor = (start, geometry) => {
            const rect = geometry.surface;
            const pad = 8;
            if (geometry.side === "inline-start") {
              return [
                start,
                { x: rect.right + pad, y: rect.top - pad },
                { x: rect.right + pad, y: rect.bottom + pad },
              ];
            }
            if (geometry.side === "inline-end") {
              return [start, { x: rect.left - pad, y: rect.top - pad }, { x: rect.left - pad, y: rect.bottom + pad }];
            }
            if (geometry.side === "block-start") {
              return [
                start,
                { x: rect.left - pad, y: rect.bottom + pad },
                { x: rect.right + pad, y: rect.bottom + pad },
              ];
            }
            return [start, { x: rect.left - pad, y: rect.top - pad }, { x: rect.right + pad, y: rect.top - pad }];
          };
          const cancelIntent = () => {
            if (openTimer !== null) {
              clearTimeout(openTimer);
              openTimer = null;
            }
            intentCleanup?.();
            intentCleanup = null;
          };
          const entry = {
            root: wrapper,
            wrapper,
            element: trigger,
            trigger,
            label,
            key: data.key,
            kind: "submenu",
            value: data.value,
            surface: context.surface,
            childSurface: surface,
            container: context.container,
            path: [...context.path],
            parent: context.parentSubmenu,
            radioGroup: null,
            open: false,
            ownDisabled: data.disabled,
            effectiveDisabled: data.disabled,
            intent: data.intent,
            textValue: data.textValue,
            choosePlacement,
            updateGeometry,
            startGeometry() {
              geometryRuntime.start(entry);
              geometryStop = () => geometryRuntime.stop(entry);
            },
            stopGeometry() {
              geometryStop?.();
              geometryStop = null;
            },
            scheduleOpen() {
              if (openTimer !== null) {
                return;
              }
              openTimer = setTimeout(() => {
                openTimer = null;
                context.openSubmenu(entry, { focus: null });
              }, 120);
            },
            cancelIntent,
            beginIntent(event) {
              cancelIntent();
              if (!latestGeometry) {
                context.closeSubmenu(entry, { restore: false });
                return;
              }
              const start = { x: event.clientX, y: event.clientY };
              const targetRoot = surface.getRootNode();
              const onMove = (moveEvent) => {
                if (moveEvent.pointerType !== event.pointerType) {
                  cancelIntent();
                  context.closeSubmenu(entry, { restore: false });
                  return;
                }
                if (
                  surface.contains(moveEvent.target)
                  || pointInPolygon(
                    { x: moveEvent.clientX, y: moveEvent.clientY },
                    corridor(start, latestGeometry),
                  )
                ) {
                  return;
                }
                cancelIntent();
                context.closeSubmenu(entry, { restore: false });
              };
              targetRoot.addEventListener("pointermove", onMove, true);
              const timeout = setTimeout(() => {
                cancelIntent();
                if (!surface.matches(":hover")) {
                  context.closeSubmenu(entry, { restore: false });
                }
              }, 300);
              intentCleanup = () => {
                clearTimeout(timeout);
                targetRoot.removeEventListener("pointermove", onMove, true);
              };
            },
            refresh() {
              const childHadFocus = entry.open && anchoredLayerRuntime.composedContains(
                surface,
                layerCoordinator.deepActiveElement(),
              );
              entry.effectiveDisabled = resolveBoolean();
              entry.intent = resolveIntent();
              entry.textValue = resolveTextValue();
              surface.dataset.size = context.size();
              trigger.toggleAttribute("data-disabled", entry.effectiveDisabled);
              trigger.toggleAttribute("aria-disabled", entry.effectiveDisabled);
              if (entry.effectiveDisabled) {
                trigger.setAttribute("aria-disabled", "true");
                context.closeSubmenu(entry, { restore: childHadFocus });
              } else {
                trigger.removeAttribute("aria-disabled");
              }
              trigger.dataset.intent = entry.intent;
            },
            validate() {
              const regions = [
                trigger.querySelector(':scope > [data-citry-ui-part="menu-item-start"]'),
                label,
                description,
                trigger.querySelector(':scope > [data-citry-ui-part="menu-item-end"]'),
              ].filter(Boolean);
              const forbidden = regions.some((region) => region.querySelector(
                "a[href], button, input, select, textarea, [contenteditable], [tabindex]",
              ));
              if (forbidden) {
                console.error("[citry-ui] CMenuSubmenu label must remain noninteractive.", wrapper);
                return false;
              }
              return context.entries(surface).filter((candidate) => candidate.kind !== "separator").length > 0;
            },
          };
          entry.layer = {
            surface,
            trigger,
            logicalParent: context.parentSubmenu?.layer ?? context.rootLayer,
            isEligible: () => (
              !entry.effectiveDisabled
              && !trigger.matches('[aria-disabled="true"]')
            ),
            isOpen: () => entry.open,
            requestDismiss: (reason, source) => context.dismissFromSubmenu(entry, reason, source),
            forceClose: (reason, source) => context.closeSubmenu(entry, {
              restore: false,
              reason,
              source,
            }),
            insideElements: [wrapper],
          };
          context.addSubmenu(entry);
          const unregister = context.register(entry);
          provide(
            Symbol.for("citry-ui:menu"),
            context.child({
              surface,
              container: surface,
              path: [...context.path, data.value],
              parentSubmenu: entry,
              radioGroup: null,
            }),
          );
          effect(() => {
            entry.refresh();
            context.update(entry);
          });
          const onToggle = (event) => {
            if (event.target !== surface) {
              return;
            }
            const nativeOpen = surface.matches(":popover-open");
            if (nativeOpen === entry.open) {
              return;
            }
            if (nativeOpen) {
              surface.hidePopover();
              return;
            }
            context.closeSubmenu(entry, { restore: false });
          };
          surface.addEventListener("toggle", onToggle);
          return () => {
            if (openTimer !== null) {
              clearTimeout(openTimer);
            }
            cancelIntent();
            entry.stopGeometry();
            surface.removeEventListener("toggle", onToggle);
            context.closeSubmenu(entry, { restore: false });
            unregister();
          };
        },
      });
    """
    )


class CInternalMenuCollection(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        registry: _MenuRegistry

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[object]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            msg = "Menu declaration collection completed without a render result."
            raise RuntimeError(msg)
        _validate_registry(self.kwargs.registry)
        _validate_direct_output(result, self.kwargs.registry)

    template = """
      <c-slot required />
    """


class CInternalMenuContent(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[object]

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        self.unprovide(_MENU_CONTEXT_KEY)
        return {}

    template = """
      <c-slot required />
    """


__all__ = [
    "CMenu",
    "CMenuActionDetail",
    "CMenuActivatorSlotData",
    "CMenuCheckboxItem",
    "CMenuChecked",
    "CMenuCheckedChangeDetail",
    "CMenuDefaultSlotData",
    "CMenuGroup",
    "CMenuGroupDefaultSlotData",
    "CMenuGroupLabelSlotData",
    "CMenuIntent",
    "CMenuItem",
    "CMenuItemDefaultSlotData",
    "CMenuItemDescriptionSlotData",
    "CMenuItemEndSlotData",
    "CMenuItemStartSlotData",
    "CMenuOpenChangeDetail",
    "CMenuPlacement",
    "CMenuRadioChangeDetail",
    "CMenuRadioGroup",
    "CMenuRadioGroupDefaultSlotData",
    "CMenuRadioGroupLabelSlotData",
    "CMenuRadioItem",
    "CMenuSeparator",
    "CMenuSize",
    "CMenuSubmenu",
    "CMenuSubmenuDefaultSlotData",
    "CMenuSubmenuDescriptionSlotData",
    "CMenuSubmenuEndSlotData",
    "CMenuSubmenuLabelSlotData",
    "CMenuSubmenuStartSlotData",
]
