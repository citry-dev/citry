"""Styled interactive Tabs component family."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Literal, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs

CTabsActivation = Literal["automatic", "manual"]
CTabsOrientation = Literal["horizontal", "vertical"]
CTabsDirection = Literal["ltr", "rtl"]
CTabsAlign = Literal["start", "center", "end"]
CTabsDensity = Literal["default", "comfortable", "compact"]
CTabsVariant = Literal["underline", "pill"]

_TABS_CONTEXT_KEY = "citry_ui_tabs"
_NATIVE_TAB_CONTEXT_KEY = "citry_ui_native_tab"


@dataclass(frozen=True, slots=True)
class _TabDeclaration:
    value: str
    disabled: bool
    attrs: dict[str, object] | None
    content: Slot[CTabDefaultSlotData]


@dataclass(frozen=True, slots=True)
class _TabPanelDeclaration:
    value: str
    attrs: dict[str, object] | None
    content: Slot[CTabPanelDefaultSlotData]


@dataclass(slots=True)
class _TabsRegistry:
    tabs: list[_TabDeclaration] = field(default_factory=list)
    panels: list[_TabPanelDeclaration] = field(default_factory=list)


def _value_token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:12]


def _tabs_context(component: LibraryComponent) -> Any:
    context = component.inject(_TABS_CONTEXT_KEY, None)
    if context is None:
        msg = f"{type(component).__name__} is a declaration component and must be rendered inside CTabs."
        raise ValueError(msg)
    return context


def _validate_tabs_registry(registry: _TabsRegistry, selected_value: str) -> None:
    tab_values = [declaration.value for declaration in registry.tabs]
    panel_values = [declaration.value for declaration in registry.panels]
    if len(set(tab_values)) != len(tab_values):
        msg = "Tabs requires every Tab value to be unique."
        raise ValueError(msg)
    if len(set(panel_values)) != len(panel_values):
        msg = "Tabs requires every TabPanel value to be unique."
        raise ValueError(msg)
    if set(tab_values) != set(panel_values):
        msg = "Tabs requires exactly one matching Tab and TabPanel for every value."
        raise ValueError(msg)
    if selected_value not in tab_values:
        msg = f"Tabs selected value {selected_value!r} does not identify a Tab."
        raise ValueError(msg)
    selected_tab = next(declaration for declaration in registry.tabs if declaration.value == selected_value)
    if selected_tab.disabled:
        msg = f"Tabs selected value {selected_value!r} identifies a disabled Tab."
        raise ValueError(msg)


def _validate_tabs_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        msg = (
            "CTabs default content may contain only CTab and CTabPanel declarations, "
            "formatting whitespace, and transparent components that produce no other output."
        )
        raise ValueError(msg)


def _reject_owned_attrs(
    attrs: dict[str, object] | None,
    owned: set[str],
    location: str,
) -> None:
    for key in attrs or {}:
        if key.lower() in owned:
            msg = f"{location} attrs cannot override owned attribute {key!r}."
            raise ValueError(msg)


def _validate_choice(name: str, value: object, allowed: tuple[object, ...]) -> None:
    if value not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        msg = f"Tabs {name} must be one of {expected}, got {value!r}."
        raise ValueError(msg)


def _validate_boolean(component_name: str, name: str, value: object) -> None:
    # Template constants arrive through Citry's bool-compatible ConstProxy,
    # so isinstance() accepts the framework wrapper while still rejecting
    # Python's integer 0/1 and arbitrary truthy values.
    if not isinstance(value, bool):
        msg = f"{component_name} {name} must be a bool, got {value!r}."
        raise TypeError(msg)


def _validate_explicit_id(value: str | None) -> None:
    if value is None:
        return
    if not value or any(character in "\t\n\f\r " for character in value):
        msg = "Tabs id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)


class CTabsDefaultSlotData:
    pass


class CTabs(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        default_value: str
        value: str | None = None
        activation: CTabsActivation = "automatic"
        orientation: CTabsOrientation = "horizontal"
        direction: CTabsDirection | None = None
        loop: bool = True
        disabled: bool = False
        variant: CTabsVariant = "underline"
        density: CTabsDensity = "default"
        align: CTabsAlign = "start"
        grow: bool = False
        id: str | None = None
        aria_label: str | None = None
        aria_labelledby: str | None = None
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: dict[str, object] | None = None
        tab_list_attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabsDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if self.inject(_NATIVE_TAB_CONTEXT_KEY, None) is not None:
            msg = (
                "Nested Tabs cannot be rendered inside CTab because CTab renders "
                "its content inside a native button. Put nested Tabs inside CTabPanel."
            )
            raise ValueError(msg)
        if self.inject(_TABS_CONTEXT_KEY, None) is not None:
            msg = "Nested Tabs must be rendered inside a Tab or TabPanel."
            raise ValueError(msg)

        selected_value = kwargs.value if kwargs.value is not None else kwargs.default_value
        if not selected_value:
            msg = "Tabs requires a non-empty value or default_value."
            raise ValueError(msg)
        _validate_choice("activation", kwargs.activation, ("automatic", "manual"))
        _validate_choice("orientation", kwargs.orientation, ("horizontal", "vertical"))
        _validate_choice("direction", kwargs.direction, ("ltr", "rtl", None))
        _validate_choice("variant", kwargs.variant, ("underline", "pill"))
        _validate_choice("density", kwargs.density, ("default", "comfortable", "compact"))
        _validate_choice("align", kwargs.align, ("start", "center", "end"))
        _validate_boolean("Tabs", "loop", kwargs.loop)
        _validate_boolean("Tabs", "disabled", kwargs.disabled)
        _validate_boolean("Tabs", "grow", kwargs.grow)
        _validate_explicit_id(kwargs.id)
        if not (kwargs.aria_label and kwargs.aria_label.strip()) and not (
            kwargs.aria_labelledby and kwargs.aria_labelledby.strip()
        ):
            msg = "CTabs requires aria_label or aria_labelledby for an accessible tab-list name."
            raise ValueError(msg)

        _reject_owned_attrs(
            kwargs.attrs,
            {
                "data-activation",
                "data-align",
                "data-citry-tabs-root",
                "data-citry-tabs-initialized",
                "data-citry-ui-part",
                "data-density",
                "data-direction",
                "data-disabled",
                "data-grow",
                "data-loop",
                "data-orientation",
                "data-value",
                "data-variant",
                "dir",
                "id",
            },
            "CTabs",
        )
        _reject_owned_attrs(
            kwargs.tab_list_attrs,
            {
                "aria-disabled",
                "aria-label",
                "aria-labelledby",
                "aria-orientation",
                "data-citry-tabs-list",
                "data-citry-ui-part",
                "data-orientation",
                "role",
            },
            "CTabs tab_list_attrs",
        )

        group_id = kwargs.id or f"cui-tabs-{self.id}"
        registry = _TabsRegistry()
        root_attrs = {
            **merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
            "id": group_id,
            "data-citry-tabs-root": True,
            "data-value": selected_value,
            "data-activation": kwargs.activation,
            "data-orientation": kwargs.orientation,
            "data-direction": kwargs.direction,
            "data-loop": kwargs.loop,
            "data-density": kwargs.density,
            "data-variant": kwargs.variant,
            "data-align": kwargs.align,
            "data-grow": kwargs.grow,
            "data-disabled": kwargs.disabled,
            "dir": kwargs.direction,
        }
        list_attrs = {
            **(kwargs.tab_list_attrs or {}),
            "role": "tablist",
            "aria-disabled": "true" if kwargs.disabled else None,
            "aria-orientation": kwargs.orientation,
            "aria-label": kwargs.aria_label,
            "aria-labelledby": kwargs.aria_labelledby,
            "data-citry-tabs-list": True,
            "data-orientation": kwargs.orientation,
        }
        self.provide(
            _TABS_CONTEXT_KEY,
            registry=registry,
        )
        return {
            "group_id": group_id,
            "selected_value": selected_value,
            "root_disabled": kwargs.disabled,
            "root_attrs": root_attrs,
            "list_attrs": list_attrs,
            "registry": registry,
        }

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "value": kwargs.value if kwargs.value is not None else kwargs.default_value,
            "activation": kwargs.activation,
            "orientation": kwargs.orientation,
            "direction": kwargs.direction,
            "loop": kwargs.loop,
            "disabled": kwargs.disabled,
            "variant": kwargs.variant,
            "density": kwargs.density,
            "align": kwargs.align,
            "grow": kwargs.grow,
        }

    template = """
      <c-CInternalTabsDeclarations>
        <c-slot required />
      </c-CInternalTabsDeclarations>
      <c-CInternalTabs
        c-group_id="group_id"
        c-selected_value="selected_value"
        c-root_disabled="root_disabled"
        c-root_attrs="root_attrs"
        c-list_attrs="list_attrs"
        c-registry="registry"
      />
    """

    js = """
      $component({
        props: {
          value: {},
          onValueChange: {},
          activation: {},
          orientation: {},
          direction: {},
          loop: {},
          disabled: {},
          variant: {},
          density: {},
          align: {},
          grow: {},
        },
        init: ({ els, data, props, effect }) => {
          const root = els[0];
          const rootSelector = "[data-citry-tabs-root]";
          const listSelector = "[data-citry-tabs-list]";
          const tabSelector = "[data-citry-tabs-tab]";
          const panelSelector = "[data-citry-tabs-panel]";
          const allowedValues = {
            activation: ["automatic", "manual"],
            orientation: ["horizontal", "vertical"],
            direction: ["ltr", "rtl", null],
            variant: ["underline", "pill"],
            density: ["default", "comfortable", "compact"],
            align: ["start", "center", "end"],
          };
          const invalidConfigurationEpisodes = new Map();
          // Events can recreate this initializer while preserving the Tabs
          // root. Keep only the focus and ordering history needed to recover
          // from a server-rendered tab removal on that preserved DOM node.
          const runtimeState = root.__citryUiTabsRuntime ?? {
            lastFocusedValue: null,
            lastTabValues: [],
          };
          root.__citryUiTabsRuntime = runtimeState;
          let currentValue = data.value;
          let onValueChange = null;
          let lastFocusedValue = runtimeState.lastFocusedValue;
          let lastTabValues = runtimeState.lastTabValues;
          let configuration = {
            activation: data.activation,
            orientation: data.orientation,
            direction: data.direction,
            loop: data.loop,
            disabled: data.disabled,
            variant: data.variant,
            density: data.density,
            align: data.align,
            grow: data.grow,
          };

          const isOwned = (element) => element?.closest(rootSelector) === root;
          const tabs = () => [...root.querySelectorAll(tabSelector)].filter(isOwned);
          const panels = () => [...root.querySelectorAll(panelSelector)].filter(isOwned);
          const tabList = () => [...root.querySelectorAll(listSelector)].find(isOwned);
          const ownDisabled = (tab) => tab.hasAttribute("data-citry-tabs-own-disabled");
          const isInteractionDisabled = (tab) => configuration.disabled || ownDisabled(tab);
          const enabledTabs = () => tabs().filter((tab) => !isInteractionDisabled(tab));

          const tabForValue = (value) => tabs().find((tab) => tab.dataset.value === value);
          const hasDocumentFallbackFocus = () => (
            document.activeElement === document.body
            || document.activeElement === document.documentElement
          );
          const recordTabValues = () => {
            lastTabValues = tabs().map((tab) => tab.dataset.value);
            runtimeState.lastTabValues = lastTabValues;
          };
          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalidValue = (value) => {
            console.error(
              `[citry-ui] CTabs value ${describeValue(value)} does not identify an enabled tab.`,
              root,
            );
          };
          const reportInvalidConfiguration = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidConfigurationEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidConfigurationEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CTabs ${name} received invalid client value ${describedValue}; `
                + "using the server-rendered fallback.",
              root,
            );
          };
          const resolveCallback = () => {
            const value = props.onValueChange;
            if (value === undefined || typeof value === "function") {
              invalidConfigurationEpisodes.delete("onValueChange");
              return value ?? null;
            }
            const describedValue = describeValue(value);
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidConfigurationEpisodes.get("onValueChange") !== fingerprint) {
              invalidConfigurationEpisodes.set("onValueChange", fingerprint);
              console.error(
                `[citry-ui] CTabs onValueChange received invalid client value ${describedValue}; `
                  + "ignoring the callback.",
                root,
              );
            }
            return null;
          };
          const resolveChoice = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowedValues[name].includes(value)) {
              invalidConfigurationEpisodes.delete(name);
              return value;
            }
            reportInvalidConfiguration(name, value);
            return data[name];
          };
          const resolveBoolean = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (typeof value === "boolean") {
              invalidConfigurationEpisodes.delete(name);
              return value;
            }
            reportInvalidConfiguration(name, value);
            return data[name];
          };

          const setRovingTab = (nextTab) => {
            tabs().forEach((tab) => {
              tab.tabIndex = tab === nextTab && !isInteractionDisabled(tab) ? 0 : -1;
            });
          };

          const applySelection = (value, { preserveFocus = false, scroll = false } = {}) => {
            const selectedTab = tabForValue(value);
            if (!selectedTab || ownDisabled(selectedTab)) {
              reportInvalidValue(value);
              return false;
            }

            const focusedTab = isOwned(document.activeElement) && document.activeElement.matches(tabSelector)
              ? document.activeElement
              : null;
            tabs().forEach((tab) => {
              const selected = tab === selectedTab;
              tab.setAttribute("aria-selected", selected ? "true" : "false");
              tab.dataset.state = selected ? "active" : "inactive";
            });
            panels().forEach((panel) => {
              const selected = panel.dataset.value === value;
              panel.hidden = !selected;
              panel.dataset.state = selected ? "active" : "inactive";
            });
            currentValue = value;
            root.dataset.value = value;
            setRovingTab(preserveFocus && focusedTab ? focusedTab : selectedTab);
            if (scroll) {
              selectedTab.scrollIntoView({ block: "nearest", inline: "nearest" });
            }
            return true;
          };

          const applyDisabled = (disabled) => {
            const focusedTab = isOwned(document.activeElement) && document.activeElement.matches(tabSelector)
              ? document.activeElement
              : null;
            root.toggleAttribute("data-disabled", disabled);
            const list = tabList();
            if (disabled) {
              list?.setAttribute("aria-disabled", "true");
            } else {
              list?.removeAttribute("aria-disabled");
            }
            tabs().forEach((tab) => {
              const tabDisabled = disabled || ownDisabled(tab);
              tab.disabled = tabDisabled;
              tab.toggleAttribute("data-disabled", tabDisabled);
              if (tabDisabled) {
                tab.tabIndex = -1;
              }
            });
            if (!disabled) {
              const selectedTab = tabForValue(currentValue);
              const rovingTab = focusedTab && !isInteractionDisabled(focusedTab)
                ? focusedTab
                : selectedTab;
              if (rovingTab && !isInteractionDisabled(rovingTab)) {
                setRovingTab(rovingTab);
              }
            }
          };

          const applyConfiguration = (next) => {
            configuration = next;
            root.dataset.activation = next.activation;
            root.dataset.orientation = next.orientation;
            root.toggleAttribute("data-loop", next.loop);
            root.dataset.variant = next.variant;
            root.dataset.density = next.density;
            root.dataset.align = next.align;
            root.toggleAttribute("data-grow", next.grow);

            if (next.direction === null) {
              root.removeAttribute("dir");
              root.removeAttribute("data-direction");
            } else {
              root.setAttribute("dir", next.direction);
              root.dataset.direction = next.direction;
            }

            const list = tabList();
            list?.setAttribute("aria-orientation", next.orientation);
            list?.setAttribute("data-orientation", next.orientation);
            applyDisabled(next.disabled);
          };

          const requestSelection = (tab, source) => {
            const value = tab.dataset.value;
            const previousValue = currentValue;
            if (!value || value === previousValue || isInteractionDisabled(tab)) {
              return;
            }
            const detail = { value, previousValue, source };
            onValueChange?.(value, detail);
            if (props.value === undefined) {
              applySelection(value, { preserveFocus: true, scroll: true });
            }
          };

          const fallbackAfterRemoval = (removedValue) => {
            const available = enabledTabs();
            if (available.length === 0) {
              return null;
            }
            const removedIndex = lastTabValues.indexOf(removedValue);
            if (removedIndex < 0) {
              return available[0];
            }
            const currentTabs = tabs();
            for (let offset = 0; offset < currentTabs.length; offset += 1) {
              const after = currentTabs[removedIndex + offset];
              if (after && !isInteractionDisabled(after)) {
                return after;
              }
              const before = currentTabs[removedIndex - offset - 1];
              if (before && !isInteractionDisabled(before)) {
                return before;
              }
            }
            return available[0];
          };

          const reconcileStructure = () => {
            applyDisabled(configuration.disabled);
            const serverValue = root.dataset.value;
            const serverTab = serverValue ? tabForValue(serverValue) : null;
            const currentTab = tabForValue(currentValue);
            const lostFocusedTab = lastFocusedValue !== null && !tabForValue(lastFocusedValue);

            if (serverTab && !isInteractionDisabled(serverTab) && serverValue !== currentValue) {
              applySelection(serverValue, { preserveFocus: true });
              if (lostFocusedTab && hasDocumentFallbackFocus()) {
                serverTab.focus({ preventScroll: true });
              }
            } else if (!currentTab || isInteractionDisabled(currentTab)) {
              const previousValue = currentValue;
              const fallback = fallbackAfterRemoval(previousValue);
              if (fallback) {
                const value = fallback.dataset.value;
                const detail = { value, previousValue, source: "removal" };
                onValueChange?.(value, detail);
                applySelection(value, { scroll: true });
                if (lostFocusedTab && hasDocumentFallbackFocus()) {
                  fallback.focus({ preventScroll: true });
                }
              } else {
                tabs().forEach((tab) => {
                  tab.setAttribute("aria-selected", "false");
                  tab.dataset.state = "inactive";
                  tab.tabIndex = -1;
                });
                panels().forEach((panel) => {
                  panel.hidden = true;
                  panel.dataset.state = "inactive";
                });
                root.removeAttribute("data-value");
              }
            } else {
              applySelection(currentValue, { preserveFocus: true });
            }
            recordTabValues();
          };

          const onClick = (event) => {
            const tab = event.target.closest?.(tabSelector);
            if (!isOwned(tab) || isInteractionDisabled(tab)) {
              return;
            }
            setRovingTab(tab);
            requestSelection(tab, "pointer");
          };

          const onFocusIn = (event) => {
            const tab = event.target.closest?.(tabSelector);
            if (isOwned(tab)) {
              lastFocusedValue = tab.dataset.value;
              runtimeState.lastFocusedValue = lastFocusedValue;
            }
          };

          const onKeydown = (event) => {
            const tab = event.target.closest?.(tabSelector);
            if (!isOwned(tab) || isInteractionDisabled(tab)) {
              return;
            }

            if (configuration.activation === "manual" && (event.key === "Enter" || event.key === " ")) {
              event.preventDefault();
              requestSelection(tab, "keyboard");
              return;
            }

            const available = enabledTabs();
            const index = available.indexOf(tab);
            if (index < 0) {
              return;
            }

            let nextIndex = null;
            if (event.key === "Home") {
              nextIndex = 0;
            } else if (event.key === "End") {
              nextIndex = available.length - 1;
            } else if (configuration.orientation === "vertical" && event.key === "ArrowDown") {
              nextIndex = index + 1;
            } else if (configuration.orientation === "vertical" && event.key === "ArrowUp") {
              nextIndex = index - 1;
            } else if (configuration.orientation === "horizontal" && event.key === "ArrowRight") {
              const rtl = getComputedStyle(root).direction === "rtl";
              nextIndex = index + (rtl ? -1 : 1);
            } else if (configuration.orientation === "horizontal" && event.key === "ArrowLeft") {
              const rtl = getComputedStyle(root).direction === "rtl";
              nextIndex = index + (rtl ? 1 : -1);
            } else {
              return;
            }

            event.preventDefault();
            if (configuration.loop) {
              nextIndex = (nextIndex + available.length) % available.length;
            } else {
              nextIndex = Math.max(0, Math.min(available.length - 1, nextIndex));
            }
            const nextTab = available[nextIndex];
            setRovingTab(nextTab);
            nextTab.focus();
            if (configuration.activation === "automatic") {
              requestSelection(nextTab, "keyboard");
            }
          };

          root.addEventListener("click", onClick);
          root.addEventListener("keydown", onKeydown);
          root.addEventListener("focusin", onFocusIn);
          effect(() => {
            applyConfiguration({
              activation: resolveChoice("activation"),
              orientation: resolveChoice("orientation"),
              direction: resolveChoice("direction"),
              loop: resolveBoolean("loop"),
              disabled: resolveBoolean("disabled"),
              variant: resolveChoice("variant"),
              density: resolveChoice("density"),
              align: resolveChoice("align"),
              grow: resolveBoolean("grow"),
            });
          });
          effect(() => {
            onValueChange = resolveCallback();
          });
          effect(() => {
            const value = props.value;
            if (value !== undefined) {
              applySelection(value, { preserveFocus: true });
            }
          });
          const list = tabList();
          const hasInvalidPhysicalStructure = list?.parentElement !== root
            || tabs().some((tab) => tab.parentElement !== list)
            || panels().some((panel) => panel.parentElement !== root);
          if (hasInvalidPhysicalStructure) {
            console.error(
              "[citry-ui] CTabs requires its generated tab list and TabPanels to be direct "
                + "DOM children of the Tabs root, and Tabs to be direct DOM children of "
                + "the generated tab list. "
                + "Component wrappers are allowed only when they render no extra element.",
              root,
            );
          }
          const focusedValueWasRemoved = lastFocusedValue !== null && !tabForValue(lastFocusedValue);
          const selectedTab = tabForValue(currentValue);
          if (focusedValueWasRemoved && selectedTab && hasDocumentFallbackFocus()) {
            selectedTab.focus({ preventScroll: true });
          }
          recordTabValues();
          const structureObserver = new MutationObserver(reconcileStructure);
          structureObserver.observe(root, { childList: true, subtree: true });
          root.setAttribute("data-citry-tabs-initialized", "");

          return () => {
            structureObserver.disconnect();
            root.removeEventListener("click", onClick);
            root.removeEventListener("keydown", onKeydown);
            root.removeEventListener("focusin", onFocusIn);
            root.removeAttribute("data-citry-tabs-initialized");
          };
        },
      });
    """

    css_file = "runtime.min.css"


class CTabDefaultSlotData:
    value: str
    is_selected: bool
    is_disabled: bool


class CTab(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        if not kwargs.value:
            msg = "Tab value must be non-empty."
            raise ValueError(msg)
        _validate_boolean("Tab", "disabled", kwargs.disabled)
        _reject_owned_attrs(
            kwargs.attrs,
            {
                "aria-controls",
                "aria-selected",
                "data-citry-key",
                "data-citry-tabs-own-disabled",
                "data-citry-tabs-tab",
                "data-citry-ui-part",
                "data-disabled",
                "data-state",
                "data-value",
                "disabled",
                "id",
                "role",
                "tabindex",
                "type",
            },
            "CTab",
        )
        registry = _tabs_context(self).registry
        registry.tabs.append(
            _TabDeclaration(
                value=kwargs.value,
                disabled=kwargs.disabled,
                attrs=merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
                # Citry normalizes every authored SlotInput into Slot before
                # template_data runs. The Slots annotation keeps the broader
                # authoring input contract, while declarations retain the
                # normalized runtime type used by the internal renderer.
                content=cast("Slot[CTabDefaultSlotData]", slots.default),
            )
        )
        self.provide(_NATIVE_TAB_CONTEXT_KEY)
        self.unprovide(_TABS_CONTEXT_KEY)
        return {}

    def on_render(self) -> str:
        return ""


class CTabPanelDefaultSlotData:
    value: str
    is_selected: bool


class CTabPanel(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabPanelDefaultSlotData]

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        if not kwargs.value:
            msg = "TabPanel value must be non-empty."
            raise ValueError(msg)
        _reject_owned_attrs(
            kwargs.attrs,
            {
                "aria-labelledby",
                "data-citry-key",
                "data-citry-tabs-panel",
                "data-citry-ui-part",
                "data-state",
                "data-value",
                "hidden",
                "id",
                "role",
                "tabindex",
            },
            "CTabPanel",
        )
        registry = _tabs_context(self).registry
        registry.panels.append(
            _TabPanelDeclaration(
                value=kwargs.value,
                attrs=merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
                content=cast("Slot[CTabPanelDefaultSlotData]", slots.default),
            )
        )
        self.unprovide(_TABS_CONTEXT_KEY)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalTab(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        group_id: str
        selected_value: str
        root_disabled: bool
        declaration: _TabDeclaration

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        declaration = kwargs.declaration
        disabled = declaration.disabled or kwargs.root_disabled
        selected = declaration.value == kwargs.selected_value
        token = _value_token(declaration.value)
        slot_data = {
            "value": declaration.value,
            "is_selected": selected,
            "is_disabled": disabled,
        }
        self.provide(_NATIVE_TAB_CONTEXT_KEY)
        self.unprovide(_TABS_CONTEXT_KEY)
        return {
            "morph_key": declaration.value,
            "tab_attrs": {
                **(declaration.attrs or {}),
                "id": f"{kwargs.group_id}-tab-{token}",
                "role": "tab",
                "type": "button",
                "aria-controls": f"{kwargs.group_id}-panel-{token}",
                "aria-selected": "true" if selected else "false",
                "tabindex": 0 if selected and not disabled else -1,
                "disabled": disabled,
                "data-citry-tabs-tab": True,
                "data-citry-tabs-own-disabled": declaration.disabled,
                "data-value": declaration.value,
                "data-state": "active" if selected else "inactive",
                "data-disabled": disabled,
            },
            "content": Slot(
                lambda ctx: declaration.content(
                    slot_data,
                    provides=dict(ctx.provides or {}),
                )
            ),
        }

    template = """
      <button
        class="cui-tab"
        #c-key="morph_key"
        c-bind="tab_attrs"
        data-citry-ui-part="tab"
      >
        {{ content }}
      </button>
    """


class CInternalTabPanel(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        group_id: str
        selected_value: str
        declaration: _TabPanelDeclaration

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        declaration = kwargs.declaration
        token = _value_token(declaration.value)
        selected = declaration.value == kwargs.selected_value
        slot_data = {
            "value": declaration.value,
            "is_selected": selected,
        }
        self.unprovide(_TABS_CONTEXT_KEY)
        return {
            "morph_key": declaration.value,
            "panel_attrs": {
                **(declaration.attrs or {}),
                "id": f"{kwargs.group_id}-panel-{token}",
                "role": "tabpanel",
                "aria-labelledby": f"{kwargs.group_id}-tab-{token}",
                "tabindex": 0,
                "hidden": not selected,
                "data-citry-tabs-panel": True,
                "data-value": declaration.value,
                "data-state": "active" if selected else "inactive",
            },
            "content": Slot(
                lambda ctx: declaration.content(
                    slot_data,
                    provides=dict(ctx.provides or {}),
                )
            ),
        }

    template = """
      <div
        class="cui-tab-panel"
        #c-key="morph_key"
        c-bind="panel_attrs"
        data-citry-ui-part="tab-panel"
      >
        {{ content }}
      </div>
    """


class CInternalTabsDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabsDefaultSlotData]

    def on_render(self) -> Any:
        # This component runs before CInternalTabs in the parent's deferred
        # queue. It keeps the otherwise-empty declaration ranges alive as the
        # ownership carriers for the lazy Slots used by the final renderer.
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            msg = "CTabs declaration collection completed without a render result."
            raise RuntimeError(msg)
        _validate_tabs_declaration_output(result)

    template = """
      <c-slot required />
    """


class CInternalTabs(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        group_id: str
        selected_value: str
        root_disabled: bool
        root_attrs: dict[str, object]
        list_attrs: dict[str, object]
        registry: _TabsRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        # The sibling declaration collector is enqueued first. Citry settles
        # it and all CTab/CTabPanel children before this component renders, so
        # this is the first point where the complete family can be validated.
        _validate_tabs_registry(kwargs.registry, kwargs.selected_value)
        self.unprovide(_TABS_CONTEXT_KEY)
        return {
            "group_id": kwargs.group_id,
            "selected_value": kwargs.selected_value,
            "root_disabled": kwargs.root_disabled,
            "root_attrs": kwargs.root_attrs,
            "list_attrs": kwargs.list_attrs,
            "tabs": kwargs.registry.tabs,
            "panels": kwargs.registry.panels,
        }

    template = """
      <div
        class="cui-tabs"
        c-bind="root_attrs"
        data-citry-ui-part="tabs"
      >
        <div
          class="cui-tab-list"
          c-bind="list_attrs"
          data-citry-ui-part="tab-list"
        >
          <c-for each="declaration in tabs">
            <c-CInternalTab
              c-group_id="group_id"
              c-selected_value="selected_value"
              c-root_disabled="root_disabled"
              c-declaration="declaration"
            />
          </c-for>
        </div>
        <c-for each="declaration in panels">
          <c-CInternalTabPanel
            c-group_id="group_id"
            c-selected_value="selected_value"
            c-declaration="declaration"
          />
        </c-for>
      </div>
    """


__all__ = [
    "CTab",
    "CTabDefaultSlotData",
    "CTabPanel",
    "CTabPanelDefaultSlotData",
    "CTabs",
    "CTabsActivation",
    "CTabsAlign",
    "CTabsDefaultSlotData",
    "CTabsDensity",
    "CTabsDirection",
    "CTabsOrientation",
    "CTabsVariant",
]
