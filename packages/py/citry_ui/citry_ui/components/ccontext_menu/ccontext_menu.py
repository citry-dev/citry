"""Context Menu adapter over Citry UI's one Menu model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, Literal, TypedDict, cast

from citry import LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._anchored_layer import ANCHORED_LAYER_RUNTIME_DEPENDENCY
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import validate_boolean
from citry_ui.components.cmenu.cmenu import (
    _CMENU_SHARED_ASSETS,
    CMenuSize,
    _build_menu_root_snapshot,
)


class CContextMenuTargetSlotData:
    target_attrs: dict[str, object]


class CContextMenuMenuSlotData:
    pass


class CContextMenuOpenChangeDetail(TypedDict):
    reason: Literal[
        "contextmenu",
        "keyboard",
        "long-press",
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
    clientX: float
    clientY: float


_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_OWNERSHIP_DIRECTIVES = frozenset(
    {
        "$c-props",
        "c-bind",
        "c-props",
        "x-bind",
        "x-data",
        "x-effect",
        "x-for",
        "x-html",
        "x-id",
        "x-if",
        "x-ignore",
        "x-init",
        "x-model",
        "x-modelable",
        "x-show",
        "x-teleport",
        "x-text",
    }
)
_ROOT_ATTRS = frozenset({"class", "dir", "lang", "style"})
_ROOT_RESERVED = frozenset(
    {
        "aria-label",
        "aria-labelledby",
        "aria-controls",
        "aria-expanded",
        "aria-disabled",
        "contenteditable",
        "data-disabled",
        "data-invocation",
        "data-open",
        "data-size",
        "disabled",
        "hidden",
        "id",
        "inert",
        "is",
        "popover",
        "role",
        "tabindex",
        "data-citry-ui-part",
    }
)
_TARGET_RESERVED = frozenset(
    {
        "aria-controls",
        "aria-expanded",
        "disabled",
        "hidden",
        "id",
        "inert",
        "is",
        "popover",
        "role",
        "data-citry-context-menu-target",
    }
)
_OWNED_EVENTS = frozenset(
    {
        "blur",
        "contextmenu",
        "focusin",
        "keydown",
        "pointercancel",
        "pointerdown",
        "pointermove",
        "pointerup",
        "scroll",
        "visibilitychange",
    }
)


def _plain_id(value: object, render_id: str) -> str:
    if value is None:
        return f"cui-context-menu-{render_id}"
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CContextMenu id must be a string or None, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain or any(character in "\t\n\f\r " for character in plain):
        msg = "CContextMenu id must be non-empty and cannot contain ASCII whitespace."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CContextMenu id cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _plain_label(value: object) -> str:
    raw = const_value(value)
    if not isinstance(raw, str):
        msg = f"CContextMenu aria_label must be a string, got {raw!r}."
        raise TypeError(msg)
    plain = "".join(raw)
    if not plain.strip():
        msg = "CContextMenu aria_label must contain non-whitespace text."
        raise ValueError(msg)
    if "\0" in plain:
        msg = "CContextMenu aria_label cannot contain U+0000."
        raise ValueError(msg)
    return plain


def _dynamic_target(name: str) -> str | None:
    if name.startswith("x-bind:"):
        return name.removeprefix("x-bind:").split(".", 1)[0]
    if name.startswith((":", ".")):
        return name[1:].split(".", 1)[0]
    return None


def _event_target(name: str) -> str | None:
    if name.startswith("x-on:"):
        return name.removeprefix("x-on:").split(".", 1)[0]
    if name.startswith("@"):
        return name[1:].split(".", 1)[0]
    return None


def _copy_attrs(
    input_name: str,
    value: Mapping[str, object] | None,
    *,
    reserved: frozenset[str],
) -> dict[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        msg = f"CContextMenu {input_name} must be a mapping or None, got {value!r}."
        raise TypeError(msg)
    attrs = dict(value)
    allowed = _ROOT_ATTRS if input_name == "attrs" else None
    seen: set[str] = set()
    for key in attrs:
        if not isinstance(key, str):
            msg = f"CContextMenu {input_name} requires string keys, got {key!r}."
            raise TypeError(msg)
        normalized = key.casefold()
        if normalized in seen:
            msg = f"CContextMenu {input_name} cannot contain duplicate case variants of {key!r}."
            raise ValueError(msg)
        seen.add(normalized)
        native_marker = input_name == "target_attrs" and normalized == "data-citry-context-menu-native"
        root_aria = input_name == "attrs" and normalized.startswith("aria-")
        if (root_aria or normalized.startswith(_RUNTIME_PREFIXES) or normalized in reserved) and not native_marker:
            msg = f"CContextMenu {input_name} cannot override owned attribute {key!r}."
            raise ValueError(msg)
        directive = normalized.split(".", 1)[0]
        if directive in _OWNERSHIP_DIRECTIVES:
            msg = f"CContextMenu {input_name} cannot use ownership directive {key!r}."
            raise ValueError(msg)
        event = _event_target(normalized)
        if event is not None:
            if event in _OWNED_EVENTS:
                msg = f"CContextMenu {input_name} cannot override owned event {event!r}."
                raise ValueError(msg)
            continue
        if normalized.startswith("on"):
            msg = f"CContextMenu {input_name} cannot use raw event attribute {key!r}."
            raise ValueError(msg)
        target = _dynamic_target(normalized)
        if target is not None:
            native_target = input_name == "target_attrs" and target == "data-citry-context-menu-native"
            if (
                (input_name == "attrs" and target.startswith("aria-"))
                or target in reserved
                or target.startswith(_RUNTIME_PREFIXES)
            ) and not native_target:
                msg = f"CContextMenu {input_name} cannot dynamically bind attribute {target!r}."
                raise ValueError(msg)
            if allowed is not None and target not in allowed and not target.startswith(("aria-", "data-")):
                msg = f"CContextMenu {input_name} does not allow attribute {target!r}."
                raise ValueError(msg)
            continue
        if allowed is not None and normalized not in allowed and not normalized.startswith(("aria-", "data-")):
            msg = f"CContextMenu {input_name} does not allow attribute {key!r}."
            raise ValueError(msg)
    return attrs


def _adapt_python_target_slot(
    component: CContextMenu,
    slots: CContextMenu.Slots,
) -> None:
    """Give this family's Python target callback its frozen direct-data shape."""
    target = component.raw_slots.get("target")
    if target is None or target.extra.get("cui_context_target_adapter"):
        return
    content = target.content_func
    if getattr(content, "__module__", "").startswith("citry."):
        return

    adapted = Slot(
        target.contents,
        content_func=lambda context: content(context.data),
        component_name=target.component_name,
        slot_name=target.slot_name,
        source_position=target.source_position,
        extra={**target.extra, "cui_context_target_adapter": True},
    )
    component.raw_slots["target"] = adapted
    slots.target = adapted


@dataclass(slots=True)
class _MenuRootInputs:
    id: str
    open: bool
    disabled: bool
    loop: bool
    placement: Literal["bottom-start"]
    match_width: bool
    close_on_select: bool
    size: CMenuSize
    class_: None
    style: None
    attrs: None


class CContextMenu(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        aria_label: str
        id: str | None = None
        open: bool = False
        disabled: bool = False
        loop: bool = True
        close_on_select: bool = True
        size: CMenuSize = "md"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        target_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        target: SlotInput[CContextMenuTargetSlotData]
        menu: SlotInput[CContextMenuMenuSlotData]

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_context_menu_snapshot", None)
        if cached is not None:
            return cached
        base_id = _plain_id(kwargs.id, self.id)
        aria_label = _plain_label(kwargs.aria_label)
        validate_boolean("CContextMenu", "open", kwargs.open)
        validate_boolean("CContextMenu", "disabled", kwargs.disabled)
        validate_boolean("CContextMenu", "loop", kwargs.loop)
        validate_boolean("CContextMenu", "close_on_select", kwargs.close_on_select)
        size = const_value(kwargs.size)
        if size not in _SIZES:
            msg = f"CContextMenu size must be one of {_SIZES!r}, got {size!r}."
            raise ValueError(msg)
        root_attrs = _copy_attrs("attrs", kwargs.attrs, reserved=_ROOT_RESERVED)
        target_input_attrs = _copy_attrs(
            "target_attrs",
            kwargs.target_attrs,
            reserved=_TARGET_RESERVED,
        )
        surface_id = f"{base_id}-menu"
        menu = _build_menu_root_snapshot(
            self,
            _MenuRootInputs(
                id=surface_id,
                open=kwargs.open,
                disabled=kwargs.disabled,
                loop=kwargs.loop,
                placement="bottom-start",
                match_width=False,
                close_on_select=kwargs.close_on_select,
                size=size,
                class_=None,
                style=None,
                attrs=None,
            ),
            declaration_slot="menu",
            surface_aria_label=aria_label,
            allow_nested_owner=True,
        )
        activator_attrs = cast("dict[str, object]", menu["activator_attrs"])
        activator_style = cast("dict[str, object]", activator_attrs["style"])
        anchor_name = cast("str", activator_style["anchor-name"])
        target_id = f"{base_id}-target"
        point_id = f"{base_id}-point"
        target_attrs = dict(target_input_attrs)
        target_attrs.update(
            {
                "id": target_id,
                "data-citry-context-menu-target": "",
            }
        )
        point_attrs = {
            "id": point_id,
            "style": {
                "anchor-name": anchor_name,
            },
        }
        snapshot = {
            "root_id": base_id,
            "target_id": target_id,
            "point_id": point_id,
            "surface_id": surface_id,
            "aria_label": aria_label,
            "open": bool(kwargs.open) and not bool(kwargs.disabled),
            "disabled": bool(kwargs.disabled),
            "loop": bool(kwargs.loop),
            "close_on_select": bool(kwargs.close_on_select),
            "size": size,
            "root_attrs": merge_root_attrs(root_attrs, kwargs.class_, kwargs.style),
            "target_attrs": target_attrs,
            "point_attrs": point_attrs,
            "point_anchor_name": anchor_name,
            "menu_surface": menu["menu_surface"],
        }
        self._cui_context_menu_snapshot = snapshot
        return snapshot

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, object]:
        _adapt_python_target_slot(self, slots)
        return self._snapshot(kwargs)

    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, object]:
        _adapt_python_target_slot(self, slots)
        snapshot = self._snapshot(kwargs)
        return {
            "rootId": snapshot["root_id"],
            "targetId": snapshot["target_id"],
            "pointId": snapshot["point_id"],
            "surfaceId": snapshot["surface_id"],
            "ariaLabel": snapshot["aria_label"],
            "pointAnchorName": snapshot["point_anchor_name"],
            "serverDefaults": {
                "open": snapshot["open"],
                "disabled": snapshot["disabled"],
                "loop": snapshot["loop"],
                "closeOnSelect": snapshot["close_on_select"],
                "size": snapshot["size"],
            },
        }

    template = """
      <div
        class="cui-context-menu-host"
        c-id="root_id"
        c-data-open="'' if open else None"
        c-data-disabled="'' if disabled else None"
        c-data-size="size"
        c-bind="root_attrs"
        data-citry-context-menu-host
        data-citry-ui-part="context-menu"
      >
        <c-slot
          name="target"
          c-target_attrs="target_attrs"
          required
        />
        <span
          c-bind="point_attrs"
          aria-hidden="true"
          popover="manual"
          data-citry-context-menu-point
        ></span>
        <c-CInternalMenuSurface c-surface="menu_surface">
          <c-slot name="menu" required />
        </c-CInternalMenuSurface>
      </div>
    """

    js_file = "runtime.min.js"
    css = """
      @layer citry-ui.theme {
        :where(.cui-context-menu-host) {
          display: contents;
        }

        :where([data-citry-context-menu-point]) {
          position: fixed;
          inset: auto;
          width: 1px;
          height: 1px;
          margin: 0;
          padding: 0;
          border: 0;
          background: transparent;
          overflow: visible;
          pointer-events: none;
        }

        @media print {
          :where([data-citry-context-menu-point]) {
            display: none !important;
          }
        }
      }
    """


class _CContextMenuDependencies:
    js: ClassVar = [ANCHORED_LAYER_RUNTIME_DEPENDENCY, _CMENU_SHARED_ASSETS.runtime]
    css: ClassVar = [_CMENU_SHARED_ASSETS.style]


CContextMenu.Dependencies = _CContextMenuDependencies


__all__ = [
    "CContextMenu",
    "CContextMenuMenuSlotData",
    "CContextMenuOpenChangeDetail",
    "CContextMenuTargetSlotData",
]
