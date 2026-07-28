"""Server-rendered styled and headless Tabs compound components."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Literal

from citry import LibraryComponent, SlotInput

CTabsActivation = Literal["automatic", "manual"]
CTabsOrientation = Literal["horizontal", "vertical"]
CTabsDirection = Literal["ltr", "rtl"]

_TABS_CONTEXT_KEY = "citry_ui_tabs"
_TAB_LIST_CONTEXT_KEY = "citry_ui_tab_list"
_NATIVE_TAB_CONTEXT_KEY = "citry_ui_native_tab"


@dataclass(slots=True)
class _TabsRegistry:
    tab_lists: int = 0
    tabs: list[tuple[str, bool]] = field(default_factory=list)
    panels: list[str] = field(default_factory=list)


def _value_token(value: str) -> str:
    return sha256(value.encode()).hexdigest()[:12]


def _tabs_context(component: LibraryComponent) -> Any:
    context = component.inject(_TABS_CONTEXT_KEY, None)
    if context is None:
        msg = "Tab, TabList, and TabPanel must be rendered inside a Tabs root."
        raise ValueError(msg)
    return context


def _tab_list_context(component: LibraryComponent) -> Any:
    context = component.inject(_TAB_LIST_CONTEXT_KEY, None)
    if context is None:
        msg = "Tab must be rendered inside a TabList belonging to the same Tabs root."
        raise ValueError(msg)
    return context


def _validate_tabs_registry(registry: _TabsRegistry, selected_value: str) -> None:
    tab_values = [value for value, disabled in registry.tabs]
    panel_values = registry.panels
    if registry.tab_lists != 1:
        msg = f"Tabs requires exactly one TabList, found {registry.tab_lists}."
        raise ValueError(msg)
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
    if dict(registry.tabs)[selected_value]:
        msg = f"Tabs selected value {selected_value!r} identifies a disabled Tab."
        raise ValueError(msg)


class CTabsHeadlessDefaultSlotData:
    root_attrs: dict[str, object]
    group_id: str
    selected_value: str
    activation: CTabsActivation
    orientation: CTabsOrientation
    direction: CTabsDirection
    loop: bool


class CTabsHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        default_value: str
        value: str | None = None
        activation: CTabsActivation = "automatic"
        orientation: CTabsOrientation = "horizontal"
        direction: CTabsDirection = "ltr"
        loop: bool = True
        id: str | None = None
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabsHeadlessDefaultSlotData]

    _tabs_registry: _TabsRegistry
    _tabs_selected_value: str

    def template_data(
        self,
        kwargs: CTabsHeadless.Kwargs,
        slots: CTabsHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if self.inject(_NATIVE_TAB_CONTEXT_KEY, None) is not None:
            msg = (
                "Nested Tabs cannot be rendered inside CTab because CTab renders "
                "its content inside a native button. Put nested Tabs inside CTabPanel "
                "or use headless components with valid custom markup."
            )
            raise ValueError(msg)
        if self.inject(_TABS_CONTEXT_KEY, None) is not None:
            msg = "Nested Tabs must be rendered inside a Tab or TabPanel."
            raise ValueError(msg)
        selected_value = kwargs.value or kwargs.default_value
        if not selected_value:
            msg = "Tabs requires a non-empty value or default_value."
            raise ValueError(msg)
        if kwargs.activation not in {"automatic", "manual"}:
            msg = f"Tabs activation must be 'automatic' or 'manual', got {kwargs.activation!r}."
            raise ValueError(msg)
        if kwargs.orientation not in {"horizontal", "vertical"}:
            msg = f"Tabs orientation must be 'horizontal' or 'vertical', got {kwargs.orientation!r}."
            raise ValueError(msg)
        if kwargs.direction not in {"ltr", "rtl"}:
            msg = f"Tabs direction must be 'ltr' or 'rtl', got {kwargs.direction!r}."
            raise ValueError(msg)

        group_id = kwargs.id or f"cui-tabs-{self.id}"
        registry = _TabsRegistry()
        self._tabs_registry = registry
        self._tabs_selected_value = selected_value
        self.unprovide(_TAB_LIST_CONTEXT_KEY)
        self.provide(
            _TABS_CONTEXT_KEY,
            group_id=group_id,
            selected_value=selected_value,
            activation=kwargs.activation,
            orientation=kwargs.orientation,
            direction=kwargs.direction,
            loop=kwargs.loop,
            registry=registry,
        )
        return {
            "slot_data": {
                "root_attrs": {
                    **(kwargs.attrs or {}),
                    "id": group_id,
                    "data-citry-tabs-root": True,
                    "data-selected-value": selected_value,
                    "data-activation": kwargs.activation,
                    "data-orientation": kwargs.orientation,
                    "dir": kwargs.direction,
                },
                "group_id": group_id,
                "selected_value": selected_value,
                "activation": kwargs.activation,
                "orientation": kwargs.orientation,
                "direction": kwargs.direction,
                "loop": kwargs.loop,
            }
        }

    def on_render(self) -> Any:
        _, error = yield
        if error is not None:
            raise error
        _validate_tabs_registry(self._tabs_registry, self._tabs_selected_value)
        return None

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CTabsDefaultSlotData:
    pass


class CTabs(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CTabsHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabsDefaultSlotData]

    template = """
      <c-CTabsHeadless
        c-default_value="default_value"
        c-value="value"
        c-activation="activation"
        c-orientation="orientation"
        c-direction="direction"
        c-loop="loop"
        c-id="id"
        c-attrs="attrs"
      >
        <c-fill name="default" data="data">
          <div
            class="cui-tabs"
            c-bind="data.root_attrs"
            data-citry-ui-part="tabs"
          >
            <c-slot required />
          </div>
        </c-fill>
      </c-CTabsHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-tabs) {
          display: grid;
          gap: 1rem;
        }
      }
    """


class CTabListHeadlessDefaultSlotData:
    list_attrs: dict[str, object]
    orientation: CTabsOrientation


class CTabListHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        aria_label: str | None = None
        aria_labelledby: str | None = None
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabListHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: CTabListHeadless.Kwargs,
        slots: CTabListHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if not kwargs.aria_label and not kwargs.aria_labelledby:
            msg = "TabList requires aria_label or aria_labelledby for an accessible name."
            raise ValueError(msg)
        context = _tabs_context(self)
        context.registry.tab_lists += 1
        self.provide(_TAB_LIST_CONTEXT_KEY, group_id=context.group_id)
        return {
            "slot_data": {
                "list_attrs": {
                    **(kwargs.attrs or {}),
                    "role": "tablist",
                    "aria-orientation": context.orientation,
                    "aria-label": kwargs.aria_label,
                    "aria-labelledby": kwargs.aria_labelledby,
                    "data-citry-tabs-list": True,
                },
                "orientation": context.orientation,
            }
        }

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CTabListDefaultSlotData:
    pass


class CTabList(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CTabListHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabListDefaultSlotData]

    template = """
      <c-CTabListHeadless
        c-aria_label="aria_label"
        c-aria_labelledby="aria_labelledby"
        c-attrs="attrs"
      >
        <c-fill name="default" data="data">
          <div
            class="cui-tab-list"
            c-bind="data.list_attrs"
            data-citry-ui-part="tab-list"
          >
            <c-slot required />
          </div>
        </c-fill>
      </c-CTabListHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-tab-list) {
          display: flex;
          gap: 0.25rem;
          border-block-end: 1px solid #d0d5dd;
        }

        :where(.cui-tab-list[aria-orientation="vertical"]) {
          flex-direction: column;
          border-block-end: 0;
          border-inline-end: 1px solid #d0d5dd;
        }
      }
    """


class CTabHeadlessDefaultSlotData:
    tab_attrs: dict[str, object]
    value: str
    is_selected: bool
    is_disabled: bool


class CTabHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        value: str
        disabled: bool = False
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: CTabHeadless.Kwargs,
        slots: CTabHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if not kwargs.value:
            msg = "Tab value must be non-empty."
            raise ValueError(msg)
        context = _tabs_context(self)
        _tab_list_context(self)
        context.registry.tabs.append((kwargs.value, kwargs.disabled))
        token = _value_token(kwargs.value)
        selected = kwargs.value == context.selected_value
        self.unprovide(_TABS_CONTEXT_KEY)
        self.unprovide(_TAB_LIST_CONTEXT_KEY)
        return {
            "slot_data": {
                "tab_attrs": {
                    **(kwargs.attrs or {}),
                    "id": f"{context.group_id}-tab-{token}",
                    "role": "tab",
                    "type": "button",
                    "aria-controls": f"{context.group_id}-panel-{token}",
                    "aria-selected": "true" if selected else "false",
                    "tabindex": 0 if selected and not kwargs.disabled else -1,
                    "disabled": kwargs.disabled,
                    "data-citry-tabs-tab": kwargs.value,
                    "data-selected": selected,
                },
                "value": kwargs.value,
                "is_selected": selected,
                "is_disabled": kwargs.disabled,
            }
        }

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CTabDefaultSlotData:
    value: str
    is_selected: bool
    is_disabled: bool


class CTab(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CTabHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabDefaultSlotData]

    def template_data(
        self,
        kwargs: CTab.Kwargs,
        slots: CTab.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        self.provide(_NATIVE_TAB_CONTEXT_KEY)
        return {
            "value": kwargs.value,
            "disabled": kwargs.disabled,
            "attrs": kwargs.attrs,
        }

    template = """
      <c-CTabHeadless
        c-value="value"
        c-disabled="disabled"
        c-attrs="attrs"
      >
        <c-fill name="default" data="data">
          <button
            class="cui-tab"
            c-bind="data.tab_attrs"
            data-citry-ui-part="tab"
          >
            <c-slot
              c-value="data.value"
              c-is_selected="data.is_selected"
              c-is_disabled="data.is_disabled"
              required
            />
          </button>
        </c-fill>
      </c-CTabHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-tab) {
          border: 0;
          border-block-end: 0.1875rem solid transparent;
          background: transparent;
          color: inherit;
          font: inherit;
          padding: 0.625rem 0.875rem;
        }

        :where(.cui-tab[aria-selected="true"]) {
          border-color: #175cd3;
          color: #175cd3;
        }

        :where(.cui-tab:focus-visible) {
          outline: 0.1875rem solid Highlight;
          outline-offset: -0.1875rem;
        }
      }
    """


class CTabPanelHeadlessDefaultSlotData:
    panel_attrs: dict[str, object]
    value: str
    is_selected: bool


class CTabPanelHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        value: str
        attrs: dict[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabPanelHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: CTabPanelHeadless.Kwargs,
        slots: CTabPanelHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        if not kwargs.value:
            msg = "TabPanel value must be non-empty."
            raise ValueError(msg)
        context = _tabs_context(self)
        if self.inject(_TAB_LIST_CONTEXT_KEY, None) is not None:
            msg = "TabPanel must be rendered outside TabList."
            raise ValueError(msg)
        context.registry.panels.append(kwargs.value)
        token = _value_token(kwargs.value)
        selected = kwargs.value == context.selected_value
        self.unprovide(_TABS_CONTEXT_KEY)
        self.unprovide(_TAB_LIST_CONTEXT_KEY)
        return {
            "slot_data": {
                "panel_attrs": {
                    **(kwargs.attrs or {}),
                    "id": f"{context.group_id}-panel-{token}",
                    "role": "tabpanel",
                    "aria-labelledby": f"{context.group_id}-tab-{token}",
                    "tabindex": 0,
                    "hidden": not selected,
                    "data-citry-tabs-panel": kwargs.value,
                    "data-selected": selected,
                },
                "value": kwargs.value,
                "is_selected": selected,
            }
        }

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CTabPanelDefaultSlotData:
    value: str
    is_selected: bool


class CTabPanel(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CTabPanelHeadless.Kwargs):
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTabPanelDefaultSlotData]

    template = """
      <c-CTabPanelHeadless
        c-value="value"
        c-attrs="attrs"
      >
        <c-fill name="default" data="data">
          <div
            class="cui-tab-panel"
            c-bind="data.panel_attrs"
            data-citry-ui-part="tab-panel"
          >
            <c-slot
              c-value="data.value"
              c-is_selected="data.is_selected"
              required
            />
          </div>
        </c-fill>
      </c-CTabPanelHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-tab-panel) {
          padding-block: 1rem;
        }

        :where(.cui-tab-panel:focus-visible) {
          outline: 0.1875rem solid Highlight;
          outline-offset: 0.125rem;
        }
      }
    """


__all__ = [
    "CTab",
    "CTabDefaultSlotData",
    "CTabHeadless",
    "CTabHeadlessDefaultSlotData",
    "CTabList",
    "CTabListDefaultSlotData",
    "CTabListHeadless",
    "CTabListHeadlessDefaultSlotData",
    "CTabPanel",
    "CTabPanelDefaultSlotData",
    "CTabPanelHeadless",
    "CTabPanelHeadlessDefaultSlotData",
    "CTabs",
    "CTabsActivation",
    "CTabsDefaultSlotData",
    "CTabsDirection",
    "CTabsHeadless",
    "CTabsHeadlessDefaultSlotData",
    "CTabsOrientation",
]
