"""Styled Split Button component family."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, cast

from citry import LibraryComponent, SlotInput, const_value
from citry_ui.components._anchored_layer import ANCHORED_LAYER_RUNTIME_DEPENDENCY
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._context import FORM_CONTEXT_KEY
from citry_ui.components._validation import validate_boolean
from citry_ui.components.cbutton.cbutton import (
    _CBUTTON_RUNTIME_GENERATION,
    _CBUTTON_RUNTIME_KEY,
    _CBUTTON_SHARED_ASSETS,
    CButtonIntent,
    CButtonLoadingPos,
    CButtonSize,
    CButtonType,
    CButtonVariant,
    _build_button_snapshot,
)
from citry_ui.components.cmenu.cmenu import (
    _CMENU_ROOT_RUNTIME_GENERATION,
    _CMENU_ROOT_RUNTIME_KEY,
    _CMENU_SHARED_ASSETS,
    CMenuPlacement,
    _build_menu_root_snapshot,
)
from citry_ui.components.csplitbutton._submit_registry import (
    _SPLIT_BUTTON_SUBMIT_RUNTIME_GENERATION,
    _SPLIT_BUTTON_SUBMIT_RUNTIME_KEY,
    SPLIT_BUTTON_SUBMIT_RUNTIME_DEPENDENCY,
)


class CSplitButtonDefaultSlotData:
    pass


class CSplitButtonStartSlotData:
    pass


class CSplitButtonEndSlotData:
    pass


class CSplitButtonLoadingSlotData:
    pass


class CSplitButtonMenuSlotData:
    pass


_CHOICES = {
    "type": ("button", "submit", "reset"),
    "variant": ("solid", "outline", "ghost"),
    "intent": ("primary", "neutral", "success", "warn", "danger"),
    "size": ("sm", "md", "lg"),
    "loading_pos": ("start", "center", "end"),
    "placement": (
        "top-start",
        "top",
        "top-end",
        "bottom-start",
        "bottom",
        "bottom-end",
    ),
}
_COMMON_ATTRS = {
    "class",
    "style",
    "lang",
    "dir",
    "title",
    "translate",
    "spellcheck",
}
_ROOT_EXTRA_ATTRS = {"aria-describedby", "aria-details", "aria-keyshortcuts"}
_PRIMARY_EXTRA_ATTRS = {
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-details",
    "aria-keyshortcuts",
    "form",
    "formaction",
    "formenctype",
    "formmethod",
    "formnovalidate",
    "formtarget",
    "name",
    "value",
}
_TRIGGER_EXTRA_ATTRS = {"aria-describedby", "aria-details", "aria-keyshortcuts"}
_MENU_EXTRA_ATTRS = {"aria-describedby", "aria-details", "aria-keyshortcuts"}
_OWNERSHIP_DIRECTIVES = {
    "x-data",
    "x-init",
    "x-effect",
    "x-if",
    "x-for",
    "x-teleport",
    "x-ignore",
    "x-id",
    "x-show",
    "x-html",
    "x-text",
    "x-model",
    "x-modelable",
    "x-bind",
    "$c-props",
    "c-bind",
    "c-props",
}
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_ROOT_RESERVED = {
    "id",
    "is",
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-controls",
    "aria-expanded",
    "aria-disabled",
    "aria-busy",
    "tabindex",
    "autofocus",
    "hidden",
    "inert",
    "contenteditable",
    "popover",
    "popovertarget",
    "popovertargetaction",
    "command",
    "commandfor",
    "disabled",
    "href",
    "type",
    "form",
    "formaction",
    "formenctype",
    "formmethod",
    "formnovalidate",
    "formtarget",
    "name",
    "value",
    "data-disabled",
    "data-primary-disabled",
    "data-menu-disabled",
    "data-loading",
    "data-loading-position",
    "data-open",
    "data-variant",
    "data-intent",
    "data-size",
    "data-block",
    "data-citry-ui-part",
}
_PRIMARY_RESERVED = {
    "id",
    "is",
    "type",
    "disabled",
    "href",
    "role",
    "aria-busy",
    "aria-disabled",
    "aria-hidden",
    "aria-haspopup",
    "aria-controls",
    "aria-expanded",
    "aria-pressed",
    "tabindex",
    "autofocus",
    "hidden",
    "inert",
    "contenteditable",
    "popover",
    "popovertarget",
    "popovertargetaction",
    "command",
    "commandfor",
    "data-disabled",
    "data-loading",
    "data-loading-position",
    "data-variant",
    "data-intent",
    "data-size",
    "data-citry-ui-part",
}
_TRIGGER_RESERVED = _PRIMARY_RESERVED | {
    "aria-label",
    "aria-labelledby",
    "form",
    "formaction",
    "formenctype",
    "formmethod",
    "formnovalidate",
    "formtarget",
    "name",
    "value",
}
_MENU_RESERVED = {
    "id",
    "is",
    "role",
    "aria-label",
    "aria-labelledby",
    "aria-roledescription",
    "aria-hidden",
    "tabindex",
    "autofocus",
    "hidden",
    "inert",
    "contenteditable",
    "popover",
    "popovertarget",
    "popovertargetaction",
    "command",
    "commandfor",
    "disabled",
    "href",
    "type",
    "form",
    "formaction",
    "formenctype",
    "formmethod",
    "formnovalidate",
    "formtarget",
    "name",
    "value",
    "data-open",
    "data-placement",
    "data-match-width",
    "data-size",
    "data-citry-ui-part",
}


def _plain_text(input_name: str, value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CSplitButton {input_name} must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain.strip():
        msg = f"CSplitButton {input_name} must contain non-whitespace text."
        raise ValueError(msg)
    if "\0" in plain:
        msg = f"CSplitButton {input_name} cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_id(value: object, render_id: str) -> str:
    if value is None:
        return f"cui-split-button-{render_id}"
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CSplitButton id must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CSplitButton id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CSplitButton id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _dynamic_target(name: str) -> str | None:
    if name.startswith("x-bind:"):
        return name.removeprefix("x-bind:").split(".", 1)[0]
    if name.startswith((":", ".")):
        return name[1:].split(".", 1)[0]
    return None


def _copy_destination_attrs(
    input_name: str,
    value: Mapping[str, object] | None,
    *,
    extra_allowed: set[str],
    reserved: set[str],
) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        msg = f"CSplitButton {input_name} must be a mapping or None, got {value!r}."
        raise TypeError(msg)
    attrs = dict(value)
    seen: set[str] = set()
    allowed = _COMMON_ATTRS | extra_allowed
    for key in attrs:
        if not isinstance(key, str):
            msg = f"CSplitButton {input_name} requires string keys, got {key!r}."
            raise TypeError(msg)
        normalized = key.casefold()
        if normalized in seen:
            msg = f"CSplitButton {input_name} cannot contain duplicate case variants of {key!r}."
            raise ValueError(msg)
        seen.add(normalized)
        if normalized.startswith(_RUNTIME_PREFIXES) or normalized in reserved:
            msg = f"CSplitButton {input_name} cannot override owned attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"CSplitButton {input_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        if normalized.startswith("on"):
            msg = f"CSplitButton {input_name} cannot use raw event attribute {key!r}."
            raise ValueError(msg)
        if normalized.startswith(("@", "x-on:")):
            continue
        target = _dynamic_target(normalized)
        if target is not None:
            if target in reserved or not (target in allowed or target.startswith("data-")):
                msg = f"CSplitButton {input_name} cannot dynamically bind attribute {target!r}."
                raise ValueError(msg)
            continue
        if normalized not in allowed and not normalized.startswith("data-"):
            msg = f"CSplitButton {input_name} does not allow attribute {key!r}."
            raise ValueError(msg)
    return attrs


@dataclass(slots=True)
class _PrimaryButtonInputs:
    type: CButtonType
    href: None
    disabled: bool
    loading: bool
    variant: CButtonVariant
    intent: CButtonIntent
    size: CButtonSize
    block: bool
    loading_pos: CButtonLoadingPos
    class_: None
    style: None
    attrs: Mapping[str, object]


@dataclass(slots=True)
class _MenuRootInputs:
    id: str
    open: bool
    disabled: bool
    loop: bool
    placement: CMenuPlacement
    match_width: bool
    close_on_select: bool
    size: CButtonSize
    class_: None
    style: None
    attrs: Mapping[str, object]


class CSplitButton(LibraryComponent):
    class Dependencies:
        js: ClassVar = [
            ANCHORED_LAYER_RUNTIME_DEPENDENCY,
            _CBUTTON_SHARED_ASSETS.runtime,
            _CMENU_SHARED_ASSETS.runtime,
            SPLIT_BUTTON_SUBMIT_RUNTIME_DEPENDENCY,
        ]
        css: ClassVar = [
            _CBUTTON_SHARED_ASSETS.style,
            _CMENU_SHARED_ASSETS.style,
        ]

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        label: str = ""
        menu_label: str = ""
        type: CButtonType = "button"
        disabled: bool = False
        primary_disabled: bool = False
        menu_disabled: bool = False
        loading: bool = False
        variant: CButtonVariant = "solid"
        intent: CButtonIntent = "primary"
        size: CButtonSize = "md"
        block: bool = False
        loading_pos: CButtonLoadingPos = "center"
        open: bool = False
        loop: bool = True
        placement: CMenuPlacement = "bottom-end"
        match_width: bool = False
        close_on_select: bool = True
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        primary_attrs: Mapping[str, object] | None = None
        trigger_attrs: Mapping[str, object] | None = None
        menu_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSplitButtonDefaultSlotData]
        menu: SlotInput[CSplitButtonMenuSlotData]
        start: SlotInput[CSplitButtonStartSlotData] | None = None
        end: SlotInput[CSplitButtonEndSlotData] | None = None
        loading: SlotInput[CSplitButtonLoadingSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, Any]:
        cached = getattr(self, "_cui_split_button_snapshot", None)
        if cached is not None:
            return cached
        base_id = _plain_id(kwargs.id, self.id)
        label = _plain_text("label", kwargs.label)
        menu_label = _plain_text("menu_label", kwargs.menu_label)
        for input_name in (
            "disabled",
            "primary_disabled",
            "menu_disabled",
            "loading",
            "block",
            "open",
            "loop",
            "match_width",
            "close_on_select",
        ):
            validate_boolean("CSplitButton", input_name, getattr(kwargs, input_name))
        for input_name, allowed in _CHOICES.items():
            value = const_value(getattr(kwargs, input_name))
            if value not in allowed:
                expected = ", ".join(repr(item) for item in allowed)
                msg = f"CSplitButton {input_name} must be one of {expected}, got {value!r}."
                raise ValueError(msg)

        root_input_attrs = _copy_destination_attrs(
            "attrs",
            kwargs.attrs,
            extra_allowed=_ROOT_EXTRA_ATTRS,
            reserved=_ROOT_RESERVED,
        )
        primary_input_attrs = _copy_destination_attrs(
            "primary_attrs",
            kwargs.primary_attrs,
            extra_allowed=_PRIMARY_EXTRA_ATTRS,
            reserved=_PRIMARY_RESERVED,
        )
        trigger_input_attrs = _copy_destination_attrs(
            "trigger_attrs",
            kwargs.trigger_attrs,
            extra_allowed=_TRIGGER_EXTRA_ATTRS,
            reserved=_TRIGGER_RESERVED,
        )
        menu_input_attrs = _copy_destination_attrs(
            "menu_attrs",
            kwargs.menu_attrs,
            extra_allowed=_MENU_EXTRA_ATTRS,
            reserved=_MENU_RESERVED,
        )
        form = self.inject(FORM_CONTEXT_KEY, None)
        contextual_disabled = bool(form.disabled) if form is not None else False
        primary_disabled = contextual_disabled or kwargs.disabled or kwargs.primary_disabled
        menu_disabled = contextual_disabled or kwargs.disabled or kwargs.menu_disabled
        primary = _build_button_snapshot(
            self,
            _PrimaryButtonInputs(
                type=kwargs.type,
                href=None,
                disabled=kwargs.disabled or kwargs.primary_disabled,
                loading=kwargs.loading,
                variant=kwargs.variant,
                intent=kwargs.intent,
                size=kwargs.size,
                block=False,
                loading_pos=kwargs.loading_pos,
                class_=None,
                style=None,
                attrs=primary_input_attrs,
            ),
        )
        surface_id = f"{base_id}-menu"
        menu = _build_menu_root_snapshot(
            self,
            _MenuRootInputs(
                id=surface_id,
                open=kwargs.open,
                disabled=menu_disabled,
                loop=kwargs.loop,
                placement=kwargs.placement,
                match_width=kwargs.match_width,
                close_on_select=kwargs.close_on_select,
                size=kwargs.size,
                class_=None,
                style=None,
                attrs=menu_input_attrs,
            ),
            declaration_slot="menu",
        )
        activator_attrs = cast("dict[str, object]", menu["activator_attrs"])
        activator_style = cast("dict[str, object]", activator_attrs["style"])
        anchor_name = cast("str", activator_style["anchor-name"])
        anchor_style: CStyleValue = {"anchor-name": anchor_name}
        root_style: CStyleValue = anchor_style if kwargs.style is None else (kwargs.style, anchor_style)
        snapshot = {
            "root_id": base_id,
            "primary_id": f"{base_id}-primary",
            "trigger_id": f"{base_id}-menu-trigger",
            "surface_id": surface_id,
            "anchor_name": anchor_name,
            "label": label,
            "menu_label": menu_label,
            "type": kwargs.type,
            "disabled": kwargs.disabled,
            "primary_disabled": primary_disabled,
            "menu_disabled": menu_disabled,
            "loading": kwargs.loading,
            "variant": kwargs.variant,
            "intent": kwargs.intent,
            "size": kwargs.size,
            "block": kwargs.block,
            "loading_pos": kwargs.loading_pos,
            "open": kwargs.open and not menu_disabled,
            "placement": kwargs.placement,
            "match_width": kwargs.match_width,
            "root_attrs": merge_root_attrs(root_input_attrs, kwargs.class_, root_style),
            "primary_attrs": primary["attrs"],
            "primary_disabled_without_js": primary["disabled_without_js"],
            "primary_aria_busy": primary["aria_busy"],
            "primary_aria_disabled": primary["aria_disabled"],
            "has_start": primary["has_start"],
            "has_end": primary["has_end"],
            "trigger_attrs": trigger_input_attrs,
            "menu_surface": menu["menu_surface"],
        }
        self._cui_split_button_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "rootId": snapshot["root_id"],
            "primaryId": snapshot["primary_id"],
            "triggerId": snapshot["trigger_id"],
            "surfaceId": snapshot["surface_id"],
            "anchorName": snapshot["anchor_name"],
            "label": snapshot["label"],
            "menuLabel": snapshot["menu_label"],
            "primaryType": kwargs.type,
            "disabled": kwargs.disabled,
            "primaryDisabled": kwargs.primary_disabled,
            "menuDisabled": kwargs.menu_disabled,
            "loading": kwargs.loading,
            "variant": kwargs.variant,
            "intent": kwargs.intent,
            "size": kwargs.size,
            "block": kwargs.block,
            "loadingPosition": kwargs.loading_pos,
            "open": kwargs.open,
            "loop": kwargs.loop,
            "placement": kwargs.placement,
            "matchWidth": kwargs.match_width,
            "closeOnSelect": kwargs.close_on_select,
        }

    template = """
      <div
        class="cui-split-button"
        c-id="root_id"
        c-aria-label="label"
        c-data-disabled="disabled"
        c-data-primary-disabled="primary_disabled"
        c-data-menu-disabled="menu_disabled"
        c-data-loading="loading"
        c-data-loading-position="loading_pos"
        c-data-open="open"
        c-data-variant="variant"
        c-data-intent="intent"
        c-data-size="size"
        c-data-block="block"
        c-bind="root_attrs"
        role="group"
        data-citry-menu-host
        data-citry-ui-part="split-button"
      >
        <button
          class="cui-button cui-split-button__primary"
          c-id="primary_id"
          c-type="type"
          c-disabled="primary_disabled_without_js"
          c-aria-busy="primary_aria_busy"
          c-aria-disabled="primary_aria_disabled"
          c-data-loading="loading"
          c-data-disabled="primary_disabled"
          c-data-variant="variant"
          c-data-intent="intent"
          c-data-size="size"
          c-data-loading-position="loading_pos"
          c-data-citry-button-has-start="has_start"
          c-data-citry-button-has-end="has_end"
          c-bind="primary_attrs"
          data-citry-ui-part="split-button-primary"
        >
          <span
            class="cui-button__loading"
            aria-hidden="true"
            c-hidden="not loading"
            data-citry-ui-part="split-button-primary-loading-indicator"
          >
            <c-slot name="loading">
              <span class="cui-button__spinner"></span>
            </c-slot>
          </span>
          <c-if cond="has_start">
            <span
              class="cui-button__decoration"
              data-citry-ui-part="split-button-primary-start"
            >
              <c-slot name="start" />
            </span>
          </c-if>
          <span
            class="cui-button__content"
            data-citry-ui-part="split-button-primary-content"
          >
            <c-slot required />
          </span>
          <c-if cond="has_end">
            <span
              class="cui-button__decoration"
              data-citry-ui-part="split-button-primary-end"
            >
              <c-slot name="end" />
            </span>
          </c-if>
        </button>
        <button
          class="cui-button cui-split-button__menu-trigger"
          c-id="trigger_id"
          c-aria-label="menu_label"
          c-aria-controls="surface_id"
          c-aria-expanded="'true' if open else 'false'"
          c-disabled="menu_disabled"
          c-data-disabled="menu_disabled"
          c-data-variant="variant"
          c-data-intent="intent"
          c-data-size="size"
          c-bind="trigger_attrs"
          type="button"
          aria-haspopup="menu"
          data-citry-menu-trigger
          data-citry-ui-part="split-button-menu-trigger"
        >
          <span
            class="cui-split-button__indicator"
            aria-hidden="true"
            data-citry-ui-part="split-button-menu-indicator"
          ></span>
        </button>
        <c-CInternalMenuSurface c-surface="menu_surface">
          <c-slot name="menu" required />
        </c-CInternalMenuSurface>
      </div>
    """

    js = (
        """
      const buttonRuntime = globalThis[Symbol.for("__BUTTON_RUNTIME_KEY__")];
      const menuRuntime = globalThis[Symbol.for("__MENU_RUNTIME_KEY__")];
      const submitRuntime = globalThis[Symbol.for("__SUBMIT_RUNTIME_KEY__")];
      if (buttonRuntime?.generation !== __BUTTON_RUNTIME_GENERATION__) {
        throw new Error("[citry-ui] CSplitButton Button runtime dependency did not load.");
      }
      if (menuRuntime?.generation !== __MENU_RUNTIME_GENERATION__) {
        throw new Error("[citry-ui] CSplitButton Menu runtime dependency did not load.");
      }
      if (submitRuntime?.generation !== __SUBMIT_RUNTIME_GENERATION__) {
        throw new Error("[citry-ui] CSplitButton submit runtime dependency did not load.");
      }

      $component({
        props: {
          open: {},
          disabled: {},
          primaryDisabled: {},
          menuDisabled: {},
          loading: {},
          variant: {},
          intent: {},
          size: {},
          block: {},
          loadingPosition: {},
          loop: {},
          placement: {},
          matchWidth: {},
          closeOnSelect: {},
          onOpenChange: {},
          onAction: {},
        },
        init: (context) => {
          const { els, data, props, effect, inject } = context;
          const root = els[0];
          let submitRegistration = null;
          let controller = null;
          const anatomy = menuRuntime.helpers.createCompoundAnatomy(root, data, () => {
            applyCompoundConfiguration(configuration);
            controller?.repairOwned();
            controller?.refreshRootScope();
            submitRegistration?.refresh();
          });
          const { primary, trigger, surface, indicator } = anatomy;
          const formContext = inject(Symbol.for("citry-ui:form"), null);
          const allowed = {
            variant: ["solid", "outline", "ghost"],
            intent: ["primary", "neutral", "success", "warn", "danger"],
            size: ["sm", "md", "lg"],
            loadingPosition: ["start", "center", "end"],
          };
          const resolver = buttonRuntime.helpers.createResolver(
            "CSplitButton", root, data, props, allowed,
          );
          let configuration = {
            disabled: data.disabled,
            primaryDisabled: data.primaryDisabled,
            menuDisabled: data.menuDisabled,
            loading: data.loading,
            variant: data.variant,
            intent: data.intent,
            size: data.size,
            block: data.block,
            loadingPosition: data.loadingPosition,
          };

          const effectiveFormDisabled = () => Boolean(formContext?.disabled);
          const applyCompoundConfiguration = (next) => {
            configuration = next;
            buttonRuntime.helpers.applyCompoundConfiguration(
              root, primary, trigger, indicator, effectiveFormDisabled(), next,
            );
          };
          const menuData = {
            open: data.open,
            disabled: data.disabled || data.menuDisabled,
            loop: data.loop,
            placement: data.placement,
            matchWidth: data.matchWidth,
            closeOnSelect: data.closeOnSelect,
            size: data.size,
          };
          const menuProps = {};
          Object.defineProperties(menuProps, {
            open: { get: () => props.open },
            disabled: {
              get: () => (
                resolver.boolean("disabled")
                || resolver.boolean("menuDisabled")
                || effectiveFormDisabled()
              ),
            },
            loop: { get: () => resolver.boolean("loop") },
            placement: { get: () => props.placement },
            matchWidth: { get: () => resolver.boolean("matchWidth") },
            closeOnSelect: { get: () => resolver.boolean("closeOnSelect") },
            size: { get: () => props.size },
            onOpenChange: { get: () => props.onOpenChange },
            onAction: { get: () => props.onAction },
          });
          const menuContext = {
            ...context,
            data: menuData,
            props: menuProps,
          };
          controller = menuRuntime.mount(menuContext, {
            anchor: root,
            committedOpen: (open) => root.toggleAttribute("data-open", open),
            componentName: "CSplitButton",
            compound: true,
            controller: true,
            disabledChanged: () => applyCompoundConfiguration(configuration),
            disabledFocusTarget: () => (
              primary.isConnected
              && !primary.matches(":disabled")
              && primary.getClientRects().length > 0
                ? primary
                : null
            ),
            host: root,
            ignoreFocusOutside: (source) => (
              submitRegistration?.consumeInvalidFocus(source) ?? false
            ),
            insideElements: [root],
            ownsTriggerDisabled: true,
            readyChanged: (ready) => {
              root.toggleAttribute("data-citry-split-button-initialized", ready);
            },
            surface,
            trigger,
          });

          const onPrimaryClick = (event) => {
            controller.refreshRootScope();
            submitRegistration?.refresh();
            if (!anatomy.refresh()) {
              event.preventDefault();
              event.stopImmediatePropagation();
              return;
            }
            if (!buttonRuntime.helpers.guardActivation(primary, configuration, event)) {
              return;
            }
            controller.beginPrimaryAction(primary, event);
          };
          primary.addEventListener("click", onPrimaryClick, true);
          if (data.primaryType === "submit") {
            submitRegistration = submitRuntime.register(primary, {
              available: (event) => (
                anatomy.valid()
                && buttonRuntime.helpers.guardActivation(primary, configuration, event)
              ),
              hasAcceptedClick: () => controller.hasPrimaryClickToken(primary),
              observe: (event) => controller.observePrimarySubmit(event),
            });
          }

          effect(() => {
            applyCompoundConfiguration({
              disabled: resolver.boolean("disabled"),
              primaryDisabled: resolver.boolean("primaryDisabled"),
              menuDisabled: resolver.boolean("menuDisabled"),
              loading: resolver.boolean("loading"),
              variant: resolver.choice("variant"),
              intent: resolver.choice("intent"),
              size: resolver.choice("size"),
              block: resolver.boolean("block"),
              loadingPosition: resolver.choice("loadingPosition"),
            });
          });
          return () => {
            root.removeAttribute("data-citry-split-button-initialized");
            primary.removeEventListener("click", onPrimaryClick, true);
            anatomy.cleanup();
            submitRegistration?.cleanup();
            controller.cleanup();
          };
        },
      });
    """.replace("__BUTTON_RUNTIME_KEY__", _CBUTTON_RUNTIME_KEY)
        .replace("__BUTTON_RUNTIME_GENERATION__", str(_CBUTTON_RUNTIME_GENERATION))
        .replace("__MENU_RUNTIME_KEY__", _CMENU_ROOT_RUNTIME_KEY)
        .replace("__MENU_RUNTIME_GENERATION__", str(_CMENU_ROOT_RUNTIME_GENERATION))
        .replace("__SUBMIT_RUNTIME_KEY__", _SPLIT_BUTTON_SUBMIT_RUNTIME_KEY)
        .replace("__SUBMIT_RUNTIME_GENERATION__", str(_SPLIT_BUTTON_SUBMIT_RUNTIME_GENERATION))
    )

    css = """
      @layer citry-ui.theme {
        :where(.cui-split-button) {
          --_cui-split-button-divider-color: var(
            --cui-split-button-divider-color,
            color-mix(in srgb, currentColor 32%, transparent)
          );
          --_cui-split-button-divider-width: var(--cui-split-button-divider-width, 1px);
          --_cui-split-button-menu-inline-size: var(
            --cui-split-button-menu-inline-size,
            var(--_cui-button-height)
          );
          --_cui-split-button-radius: var(
            --cui-split-button-radius,
            var(--cui-button-radius, 0.5rem)
          );

          display: inline-flex;
          max-inline-size: 100%;
          border-radius: var(--_cui-split-button-radius);
          vertical-align: middle;
        }

        :where(.cui-split-button[data-block]) {
          display: flex;
          inline-size: 100%;
        }

        :where(.cui-split-button__primary) {
          min-inline-size: 0;
          border-start-end-radius: 0;
          border-end-end-radius: 0;
        }

        :where(.cui-split-button[data-block] .cui-split-button__primary) {
          flex: 1 1 auto;
        }

        :where(.cui-split-button__menu-trigger) {
          flex: 0 0 var(--_cui-split-button-menu-inline-size);
          inline-size: var(--_cui-split-button-menu-inline-size);
          min-inline-size: var(--_cui-split-button-menu-inline-size);
          margin-inline-start: calc(-1 * var(--_cui-split-button-divider-width));
          padding-inline: 0;
          border-start-start-radius: 0;
          border-end-start-radius: 0;
        }

        :where(.cui-split-button__menu-trigger)::before {
          position: absolute;
          inset-block: 18%;
          inset-inline-start: 0;
          inline-size: var(--_cui-split-button-divider-width);
          background: var(--_cui-split-button-divider-color);
          content: "";
        }

        :where(.cui-split-button > .cui-button:focus-visible) {
          z-index: 1;
        }

        :where(.cui-split-button__indicator) {
          display: block;
          inline-size: 0.5em;
          block-size: 0.5em;
          border-inline-end: 0.125em solid currentColor;
          border-block-end: 0.125em solid currentColor;
          rotate: 45deg;
          translate: 0 -0.125em;
        }

        @media (forced-colors: active) {
          :where(.cui-split-button__menu-trigger)::before {
            background: ButtonText;
          }
        }
      }
    """


__all__ = [
    "CSplitButton",
    "CSplitButtonDefaultSlotData",
    "CSplitButtonEndSlotData",
    "CSplitButtonLoadingSlotData",
    "CSplitButtonMenuSlotData",
    "CSplitButtonStartSlotData",
]
