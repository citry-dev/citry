"""Server-rendered Virtual List with complete-DOM and controlled-window strategies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import reject_owned_attrs, validate_boolean

CVirtualListStrategy = Literal["content-visibility", "window"]
CVirtualListRangeReason = Literal["initial", "scroll", "resize", "configuration"]

_VIRTUAL_LIST_CONTEXT = "citry_ui_virtual_list"
_MAX_EXTENT = 16_000_000
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-busy",
        "aria-hidden",
        "aria-label",
        "contenteditable",
        "data-citry-ui-part",
        "data-pending",
        "data-start-index",
        "data-strategy",
        "data-total-count",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "aria-hidden",
        "aria-posinset",
        "aria-setsize",
        "contenteditable",
        "data-citry-ui-part",
        "data-index",
        "data-item-key",
        "hidden",
        "inert",
        "role",
        "tabindex",
    }
)


class CVirtualListDefaultSlotData:
    pass


class CVirtualListItemDefaultSlotData(TypedDict):
    index: int
    item_key: str
    set_size: int
    strategy: CVirtualListStrategy


class CVirtualListRangeChangeDetail(TypedDict):
    startIndex: int
    endIndex: int
    visibleStartIndex: int
    visibleEndIndex: int
    requestId: int
    reason: CVirtualListRangeReason
    sourceEvent: object | None


@dataclass(frozen=True, slots=True)
class _VirtualListDeclaration:
    item_key: str
    attrs: dict[str, object]
    content: Slot[CVirtualListItemDefaultSlotData]


@dataclass(slots=True)
class _VirtualListRegistry:
    items: list[_VirtualListDeclaration] = field(default_factory=list)


def _plain(name: str, value: object, *, optional: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain:
        raise ValueError(f"{name} must be nonempty and cannot contain U+0000.")
    return plain


def _integer(name: str, value: object, *, minimum: int, maximum: int | None = None) -> int:
    raw = const_value(value)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"{name} must be an integer, got {raw!r}.")
    if raw < minimum or (maximum is not None and raw > maximum):
        bound = f"between {minimum} and {maximum}" if maximum is not None else f"at least {minimum}"
        raise ValueError(f"{name} must be {bound}, got {raw!r}.")
    return raw


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    owner: str,
    attrs: Mapping[str, object] | None,
    owned: frozenset[str],
    class_: CClassValue | None,
    style: CStyleValue | None,
    *,
    owned_style: CStyleValue | None = None,
) -> dict[str, object]:
    if attrs is not None and not isinstance(attrs, Mapping):
        raise TypeError(f"{owner} attrs must be a mapping or None, got {attrs!r}.")
    copied = dict(attrs or {})
    reject_owned_attrs(copied, owned, f"{owner} attrs")
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"{owner} attrs require string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{owner} attrs cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{owner} attrs cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{owner} attrs cannot dynamically bind owned attribute {key!r}.")
    merged_style = style if owned_style is None else (style, owned_style) if style is not None else owned_style
    return merge_root_attrs(copied, class_, merged_style)


def _registry(component: LibraryComponent) -> _VirtualListRegistry:
    provided = component.inject(_VIRTUAL_LIST_CONTEXT, None)
    if provided is None:
        raise ValueError(
            "CVirtualListItem is a declaration component and must be rendered directly inside CVirtualList "
            "or CVirtualWindow."
        )
    return cast("_VirtualListRegistry", provided.registry)


def _validate_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CVirtualList default content may contain only CVirtualListItem declarations, formatting whitespace, "
            "and transparent components that produce no other output."
        )


class CVirtualList(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        aria_label: str | None = None
        estimated_item_size: int = 48
        viewport_size: int = 400
        focusable: bool = True
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CVirtualListDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_virtual_list_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_VIRTUAL_LIST_CONTEXT, None) is not None:
            raise ValueError(
                "Nested CVirtualList must be rendered inside CVirtualListItem content, not as a direct declaration."
            )
        estimated_item_size = _integer(
            "CVirtualList estimated_item_size", kwargs.estimated_item_size, minimum=1, maximum=_MAX_EXTENT
        )
        viewport_size = _integer("CVirtualList viewport_size", kwargs.viewport_size, minimum=1, maximum=_MAX_EXTENT)
        validate_boolean("CVirtualList", "focusable", kwargs.focusable)
        registry = _VirtualListRegistry()
        self.provide(_VIRTUAL_LIST_CONTEXT, registry=registry)
        snapshot: dict[str, object] = {
            "strategy": "content-visibility",
            "aria_label": _plain("CVirtualList aria_label", kwargs.aria_label, optional=True),
            "estimated_item_size": estimated_item_size,
            "viewport_size": viewport_size,
            "overscan": 0,
            "total_count": None,
            "start_index": 0,
            "item_size": None,
            "initial_index": 0,
            "focusable": bool(kwargs.focusable),
            "registry": registry,
            "attrs": _attrs(
                "CVirtualList",
                kwargs.attrs,
                _ROOT_OWNED,
                kwargs.class_,
                kwargs.style,
                owned_style={
                    "--cui-virtual-list-viewport-size": f"{viewport_size}px",
                    "--cui-virtual-list-item-size": f"{estimated_item_size}px",
                },
            ),
        }
        self._cui_virtual_list_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    template = """
      <c-CInternalVirtualListDeclarations><c-slot /></c-CInternalVirtualListDeclarations>
      <c-CInternalVirtualList
        strategy="content-visibility"
        c-aria_label="aria_label"
        c-estimated_item_size="estimated_item_size"
        c-viewport_size="viewport_size"
        c-overscan="0"
        c-total_count="None"
        c-start_index="0"
        c-item_size="None"
        c-initial_index="0"
        c-focusable="focusable"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    css_file = "runtime.min.css"


class CVirtualListItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        item_key: str
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CVirtualListItemDefaultSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if "default" not in self.raw_slots:
            raise ValueError("CVirtualListItem requires a default content slot.")
        registry = _registry(self)
        registry.items.append(
            _VirtualListDeclaration(
                item_key=cast("str", _plain("CVirtualListItem item_key", kwargs.item_key)),
                attrs=_attrs("CVirtualListItem", kwargs.attrs, _ITEM_OWNED, kwargs.class_, kwargs.style),
                content=cast("Slot[CVirtualListItemDefaultSlotData]", slots.default),
            )
        )
        self.unprovide(_VIRTUAL_LIST_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalVirtualListDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CVirtualListDefaultSlotData] | None = None

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CVirtualList declaration collection completed without a render result.")
        _validate_declaration_output(result)

    template = "<c-slot />"


class CInternalVirtualList(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        strategy: CVirtualListStrategy
        aria_label: str | None
        estimated_item_size: int
        viewport_size: int
        overscan: int
        total_count: int | None
        start_index: int
        item_size: int | None
        initial_index: int
        focusable: bool
        attrs: dict[str, object]
        registry: _VirtualListRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        declarations = kwargs.registry.items
        keys = [item.item_key for item in declarations]
        if len(keys) != len(set(keys)):
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            raise ValueError(f"CVirtualListItem item_key values must be unique; duplicates: {duplicates!r}.")
        total_count = len(declarations) if kwargs.strategy == "content-visibility" else cast("int", kwargs.total_count)
        if kwargs.strategy == "window" and kwargs.start_index + len(declarations) > total_count:
            raise ValueError("CVirtualList supplied items cannot extend beyond total_count.")
        if total_count == 0:
            initial_index = 0
        else:
            initial_index = min(kwargs.initial_index, total_count - 1)
        item_size = kwargs.item_size or kwargs.estimated_item_size
        end_index = kwargs.start_index + len(declarations)
        self.unprovide(_VIRTUAL_LIST_CONTEXT)
        return {
            "attrs": {
                **kwargs.attrs,
                "aria-label": kwargs.aria_label,
                "data-strategy": kwargs.strategy,
                "data-pending": None,
                "data-start-index": kwargs.start_index if kwargs.strategy == "window" else None,
                "data-total-count": total_count if kwargs.strategy == "window" else None,
                "tabindex": 0 if kwargs.focusable else None,
            },
            "strategy": kwargs.strategy,
            "items": [
                {
                    "declaration": declaration,
                    "index": kwargs.start_index + offset,
                }
                for offset, declaration in enumerate(declarations)
            ],
            "total_count": total_count,
            "before_size": kwargs.start_index * item_size if kwargs.strategy == "window" else 0,
            "after_size": max(0, total_count - end_index) * item_size if kwargs.strategy == "window" else 0,
            "initial_index": initial_index,
            "overscan": kwargs.overscan,
            "item_size": item_size,
            "start_index": kwargs.start_index,
        }

    template = """
      <c-if cond="strategy == 'window'">
        <c-CInternalVirtualListWindow
          c-attrs="attrs"
          c-items="items"
          c-total_count="total_count"
          c-before_size="before_size"
          c-after_size="after_size"
          c-start_index="start_index"
          c-item_size="item_size"
          c-initial_index="initial_index"
          c-overscan="overscan"
        />
      </c-if>
      <c-else>
        <c-CInternalVirtualListStatic c-attrs="attrs" c-items="items" c-total_count="total_count" />
      </c-else>
    """


class CInternalVirtualListStatic(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        attrs: dict[str, object]
        items: list[dict[str, object]]
        total_count: int

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"attrs": kwargs.attrs, "items": kwargs.items, "total_count": kwargs.total_count}

    template = """
      <div class="cui-virtual-list" c-bind="attrs" role="list" data-citry-ui-part="virtual-list">
        <div class="cui-virtual-list__track" data-citry-ui-part="track">
          <c-for each="item in items">
            <c-CInternalVirtualListItem
              c-declaration="item['declaration']"
              c-index="item['index']"
              c-total_count="total_count"
              strategy="content-visibility"
            />
          </c-for>
        </div>
      </div>
    """


class CInternalVirtualListWindow(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        attrs: dict[str, object]
        items: list[dict[str, object]]
        total_count: int
        before_size: int
        after_size: int
        start_index: int
        item_size: int
        initial_index: int
        overscan: int

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "attrs": kwargs.attrs,
            "items": kwargs.items,
            "total_count": kwargs.total_count,
            "before_size": kwargs.before_size,
            "after_size": kwargs.after_size,
        }

    template = """
      <div class="cui-virtual-list" c-bind="attrs" role="list" data-citry-ui-part="virtual-list">
        <div class="cui-virtual-list__track" data-citry-ui-part="track">
          <div
            aria-hidden="true"
            role="presentation"
            c-style="{'block-size': f'{before_size}px'}"
            data-citry-virtual-list-spacer="before"
            data-citry-ui-part="spacer"
          ></div>
          <c-for each="item in items">
            <c-CInternalVirtualListItem
              c-declaration="item['declaration']"
              c-index="item['index']"
              c-total_count="total_count"
              strategy="window"
            />
          </c-for>
          <div
            aria-hidden="true"
            role="presentation"
            c-style="{'block-size': f'{after_size}px'}"
            data-citry-virtual-list-spacer="after"
            data-citry-ui-part="spacer"
          ></div>
        </div>
      </div>
    """


class CVirtualWindow(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        total_count: int
        start_index: int = 0
        item_size: int = 48
        viewport_size: int = 400
        overscan: int = 3
        initial_index: int = 0
        aria_label: str | None = None
        focusable: bool = True
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CVirtualListDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_virtual_window_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_VIRTUAL_LIST_CONTEXT, None) is not None:
            raise ValueError(
                "Nested CVirtualWindow must be rendered inside CVirtualListItem content, not as a direct declaration."
            )
        total_count = _integer("CVirtualWindow total_count", kwargs.total_count, minimum=0)
        start_index = _integer("CVirtualWindow start_index", kwargs.start_index, minimum=0)
        item_size = _integer("CVirtualWindow item_size", kwargs.item_size, minimum=1, maximum=_MAX_EXTENT)
        viewport_size = _integer("CVirtualWindow viewport_size", kwargs.viewport_size, minimum=1, maximum=_MAX_EXTENT)
        overscan = _integer("CVirtualWindow overscan", kwargs.overscan, minimum=0, maximum=100)
        initial_index = _integer("CVirtualWindow initial_index", kwargs.initial_index, minimum=0)
        validate_boolean("CVirtualWindow", "focusable", kwargs.focusable)
        if total_count * item_size > _MAX_EXTENT:
            raise ValueError(
                f"CVirtualWindow total_count multiplied by item_size cannot exceed {_MAX_EXTENT:,} CSS pixels."
            )
        if start_index > total_count:
            raise ValueError("CVirtualWindow start_index cannot exceed total_count.")
        registry = _VirtualListRegistry()
        self.provide(_VIRTUAL_LIST_CONTEXT, registry=registry)
        snapshot: dict[str, object] = {
            "strategy": "window",
            "aria_label": _plain("CVirtualWindow aria_label", kwargs.aria_label, optional=True),
            "estimated_item_size": item_size,
            "viewport_size": viewport_size,
            "overscan": overscan,
            "total_count": total_count,
            "start_index": start_index,
            "item_size": item_size,
            "initial_index": initial_index,
            "focusable": bool(kwargs.focusable),
            "registry": registry,
            "attrs": _attrs(
                "CVirtualWindow",
                kwargs.attrs,
                _ROOT_OWNED,
                kwargs.class_,
                kwargs.style,
                owned_style={
                    "--cui-virtual-list-viewport-size": f"{viewport_size}px",
                    "--cui-virtual-list-item-size": f"{item_size}px",
                },
            ),
        }
        self._cui_virtual_window_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "totalCount": snapshot["total_count"],
            "startIndex": snapshot["start_index"],
            "itemSize": snapshot["item_size"],
            "initialIndex": snapshot["initial_index"],
            "overscan": snapshot["overscan"],
        }

    template = """
      <c-CInternalVirtualListDeclarations><c-slot /></c-CInternalVirtualListDeclarations>
      <c-CInternalVirtualList
        strategy="window"
        c-aria_label="aria_label"
        c-estimated_item_size="estimated_item_size"
        c-viewport_size="viewport_size"
        c-overscan="overscan"
        c-total_count="total_count"
        c-start_index="start_index"
        c-item_size="item_size"
        c-initial_index="initial_index"
        c-focusable="focusable"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"


class CInternalVirtualListItem(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        declaration: _VirtualListDeclaration
        index: int
        total_count: int
        strategy: CVirtualListStrategy

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        declaration = kwargs.declaration
        slot_data: CVirtualListItemDefaultSlotData = {
            "index": kwargs.index,
            "item_key": declaration.item_key,
            "set_size": kwargs.total_count,
            "strategy": kwargs.strategy,
        }
        self.unprovide(_VIRTUAL_LIST_CONTEXT)
        return {
            "attrs": {
                **declaration.attrs,
                "aria-posinset": kwargs.index + 1 if kwargs.strategy == "window" else None,
                "aria-setsize": kwargs.total_count if kwargs.strategy == "window" else None,
                "data-index": kwargs.index,
                "data-item-key": declaration.item_key,
            },
            "morph_key": f"virtual-list-item-{declaration.item_key}",
            "content": Slot(lambda ctx: declaration.content(slot_data, provides=dict(ctx.provides or {}))),
        }

    template = """
      <div
        class="cui-virtual-list__item"
        #c-key="morph_key"
        c-bind="attrs"
        role="listitem"
        data-citry-ui-part="item"
      >{{ content }}</div>
    """


__all__ = [
    "CVirtualList",
    "CVirtualListDefaultSlotData",
    "CVirtualListItem",
    "CVirtualListItemDefaultSlotData",
    "CVirtualListRangeChangeDetail",
    "CVirtualListRangeReason",
    "CVirtualListStrategy",
    "CVirtualWindow",
]
