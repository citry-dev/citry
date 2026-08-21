"""Persistent and collapsible application Sidebars."""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003 - public schema resolves through get_type_hints()
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from citry import LibraryComponent, SlotInput
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs, reject_html_attr_bindings
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CSidebarTag = Literal["aside", "nav"]
CSidebarCollapsible = Literal["rail", "offcanvas", "none"]
CSidebarSide = Literal["inline-start", "inline-end"]
CSidebarVariant = Literal["plain", "floating"]
CSidebarSize = Literal["sm", "md", "lg"]


class CSidebarDefaultSlotData:
    pass


class CSidebarHeaderSlotData:
    pass


class CSidebarFooterSlotData:
    pass


class CSidebarToggleSlotData(TypedDict):
    collapsed: bool


class CSidebarCollapsedChangeDetail(TypedDict):
    collapsed: bool
    previousCollapsed: bool
    controlled: bool
    source: Literal["activation"]
    sourceEvent: object


_ROOT_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "contenteditable",
        "data-citry-sidebar-initialized",
        "data-citry-ui-part",
        "data-collapsed",
        "data-collapsible",
        "data-has-header",
        "data-side",
        "data-size",
        "data-sticky",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
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
_BOUND_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-label",
        "aria-labelledby",
        "data-citry-ui-part",
        "data-collapsed",
        "data-collapsible",
        "data-side",
        "data-size",
        "data-sticky",
        "data-variant",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CSidebar(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        label: str = ""
        tag: CSidebarTag = "aside"
        collapsed: bool = False
        collapsible: CSidebarCollapsible = "rail"
        side: CSidebarSide = "inline-start"
        variant: CSidebarVariant = "plain"
        size: CSidebarSize = "md"
        sticky: bool = False
        expand_label: str = "Expand sidebar"
        collapse_label: str = "Collapse sidebar"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSidebarDefaultSlotData]
        header: SlotInput[CSidebarHeaderSlotData] | None = None
        footer: SlotInput[CSidebarFooterSlotData] | None = None
        toggle: SlotInput[CSidebarToggleSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        validate_html_id("CSidebar", kwargs.id)
        validate_non_empty_string("CSidebar", "label", kwargs.label)
        validate_choice("CSidebar", "tag", kwargs.tag, ("aside", "nav"))
        validate_boolean("CSidebar", "collapsed", kwargs.collapsed)
        validate_choice("CSidebar", "collapsible", kwargs.collapsible, ("rail", "offcanvas", "none"))
        validate_choice("CSidebar", "side", kwargs.side, ("inline-start", "inline-end"))
        validate_choice("CSidebar", "variant", kwargs.variant, ("plain", "floating"))
        validate_choice("CSidebar", "size", kwargs.size, ("sm", "md", "lg"))
        validate_boolean("CSidebar", "sticky", kwargs.sticky)
        if kwargs.collapsed and kwargs.collapsible == "none":
            raise ValueError("CSidebar collapsed=True cannot be used with collapsible='none'.")

        expand_label = (
            kwargs.expand_label if "expand_label" in self.raw_kwargs else self.i18n.tr("citry-ui-sidebar-expand")
        )
        collapse_label = (
            kwargs.collapse_label if "collapse_label" in self.raw_kwargs else self.i18n.tr("citry-ui-sidebar-collapse")
        )
        validate_non_empty_string("CSidebar", "expand_label", expand_label)
        validate_non_empty_string("CSidebar", "collapse_label", collapse_label)
        reject_owned_attrs(kwargs.attrs, _ROOT_OWNED, "CSidebar")
        reject_html_attr_bindings(kwargs.attrs, _BOUND_OWNED, "CSidebar")

        root_id = kwargs.id or f"cui-sidebar-{self.id}"
        panel_id = f"{root_id}-panel"
        collapsed = bool(kwargs.collapsed)
        offcanvas_hidden = collapsed and kwargs.collapsible == "offcanvas"
        return {
            "root_id": root_id,
            "panel_id": panel_id,
            "label": kwargs.label,
            "tag": str(kwargs.tag),
            "collapsed": collapsed,
            "collapsible": kwargs.collapsible,
            "side": kwargs.side,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "sticky": bool(kwargs.sticky),
            "offcanvas_hidden": offcanvas_hidden,
            "expand_label": expand_label,
            "collapse_label": collapse_label,
            "catalog_expand_label": uses_catalog_default(self, "expand_label"),
            "catalog_collapse_label": uses_catalog_default(self, "collapse_label"),
            "has_header": "header" in self.raw_slots,
            "has_footer": "footer" in self.raw_slots,
            "has_toggle": "toggle" in self.raw_slots,
            "attrs": merge_root_attrs(kwargs.attrs, kwargs.class_, kwargs.style),
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        return {
            "collapsed": kwargs.collapsed,
            "collapsible": kwargs.collapsible,
            "side": kwargs.side,
            "variant": kwargs.variant,
            "size": kwargs.size,
            "sticky": kwargs.sticky,
        }

    template = """
      <c-element
        c-is="tag"
        class="cui-sidebar"
        c-id="root_id"
        c-aria-label="label"
        c-bind="attrs"
        c-data-collapsed="collapsed"
        c-data-collapsible="collapsible"
        c-data-has-header="has_header"
        c-data-side="side"
        c-data-variant="variant"
        c-data-size="size"
        c-data-sticky="sticky"
        data-citry-ui-part="sidebar"
      >
        <button
          class="cui-sidebar__toggle"
          type="button"
          c-hidden="collapsible == 'none'"
          c-aria-controls="panel_id"
          c-aria-expanded="'false' if collapsed else 'true'"
          data-citry-ui-part="toggle"
        >
          <span class="cui-sidebar__toggle-icon" aria-hidden="true" data-citry-ui-part="toggle-icon">
            <c-if cond="has_toggle"><c-slot name="toggle" c-collapsed="collapsed" /></c-if>
            <c-else>&#8801;</c-else>
          </span>
          <span
            class="cui-sidebar__toggle-label"
            c-hidden="not collapsed"
            c-$c-tr:citry-ui-sidebar-expand="True if catalog_expand_label else None"
            data-citry-ui-part="toggle-label"
          >{{ tr('citry-ui-sidebar-expand') if catalog_expand_label else expand_label }}</span>
          <span
            class="cui-sidebar__toggle-label"
            c-hidden="collapsed"
            c-$c-tr:citry-ui-sidebar-collapse="True if catalog_collapse_label else None"
            data-citry-ui-part="toggle-label"
          >{{ tr('citry-ui-sidebar-collapse') if catalog_collapse_label else collapse_label }}</span>
        </button>
        <div
          class="cui-sidebar__panel"
          c-id="panel_id"
          c-hidden="offcanvas_hidden"
          c-inert="offcanvas_hidden"
          data-citry-ui-part="panel"
        >
          <c-if cond="has_header">
            <header class="cui-sidebar__header" data-citry-ui-part="header"><c-slot name="header" /></header>
          </c-if>
          <div class="cui-sidebar__content" data-citry-ui-part="content"><c-slot required /></div>
          <c-if cond="has_footer">
            <footer class="cui-sidebar__footer" data-citry-ui-part="footer"><c-slot name="footer" /></footer>
          </c-if>
        </div>
      </c-element>
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"

    messages = """
      citry-ui-sidebar-expand = Expand sidebar
      citry-ui-sidebar-collapse = Collapse sidebar
    """


__all__ = [
    "CSidebar",
    "CSidebarCollapsedChangeDetail",
    "CSidebarCollapsible",
    "CSidebarDefaultSlotData",
    "CSidebarFooterSlotData",
    "CSidebarHeaderSlotData",
    "CSidebarSide",
    "CSidebarSize",
    "CSidebarTag",
    "CSidebarToggleSlotData",
    "CSidebarVariant",
]
