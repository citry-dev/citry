"""Accessible single-container Sortable collection."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CSortableLayout = Literal["vertical", "horizontal", "grid"]
CSortableSize = Literal["sm", "md", "lg"]
CSortableChangeSource = Literal["pointer", "keyboard", "reset", "client"]

_CONTEXT = "citry_ui_sortable"
_LAYOUTS = ("vertical", "horizontal", "grid")
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-label",
        "contenteditable",
        "data-citry-sortable-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-dragging",
        "data-layout",
        "data-size",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "aria-disabled",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-moving",
        "data-value",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CSortableDefaultSlotData:
    pass


class CSortableItemSlotData(TypedDict):
    value: str
    label: str
    disabled: bool
    index: int


class CSortableOrderChangeDetail(TypedDict):
    order: list[str]
    previousOrder: list[str]
    value: str
    fromIndex: int
    toIndex: int
    source: CSortableChangeSource
    controlled: bool
    sourceEvent: object | None


@dataclass(frozen=True, slots=True)
class _SortableDeclaration:
    value: str
    label: str
    disabled: bool
    attrs: dict[str, object]
    content: Slot[CSortableItemSlotData] | None
    handle: Slot[CSortableItemSlotData] | None


@dataclass(slots=True)
class _SortableRegistry:
    items: list[_SortableDeclaration] = field(default_factory=list)


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


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"{name} must be one of {expected}, got {plain!r}.")
    return cast("str", plain)


def _order(value: object, *, optional: bool = False) -> tuple[str, ...] | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"CSortable order must be a sequence of strings{' or None' if optional else ''}, got {raw!r}.")
    result = tuple(cast("str", _plain("CSortable order entry", item)) for item in raw)
    if len(result) != len(set(result)):
        raise ValueError("CSortable order must not contain duplicate values.")
    return result


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
    return merge_root_attrs(copied, class_, style)


def _registry(component: LibraryComponent) -> _SortableRegistry:
    provided = component.inject(_CONTEXT, None)
    if provided is None:
        raise ValueError("CSortableItem is a declaration component and must be rendered directly inside CSortable.")
    return cast("_SortableRegistry", provided.registry)


def _validate_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CSortable default content may contain only CSortableItem declarations, formatting whitespace, "
            "and transparent components that produce no other output."
        )


class CSortable(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        order: Sequence[str] | None = None
        name: str | None = None
        form: str | None = None
        layout: CSortableLayout = "vertical"
        disabled: bool = False
        size: CSortableSize = "md"
        label: str = "Reorder items"
        handle_label: str = "Move {item}"
        instructions_label: str = "Press Space or Enter to pick up. Use arrow keys to move. Press Space or Enter to drop, or Escape to cancel."
        picked_up_label: str = "Picked up {item}, position {position} of {total}"
        moved_label: str = "Moved {item} to position {position} of {total}"
        dropped_label: str = "Dropped {item} at position {position} of {total}"
        cancelled_label: str = "Cancelled moving {item}. Position restored to {position} of {total}"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSortableDefaultSlotData]

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_sortable_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_CONTEXT, None) is not None:
            raise ValueError("Nested CSortable must be rendered inside CSortableItem content, not as a declaration.")
        if "default" not in self.raw_slots:
            raise ValueError("CSortable requires at least one CSortableItem declaration.")
        validate_html_id("CSortable", kwargs.id)
        validate_boolean("CSortable", "disabled", kwargs.disabled)
        root_id = kwargs.id or f"cui-sortable-{self.id}"
        name = cast("str | None", _plain("CSortable name", kwargs.name, optional=True))
        form = cast("str | None", _plain("CSortable form", kwargs.form, optional=True))
        validate_html_id("CSortable", form)
        catalog = {"label": uses_catalog_default(self, "label")}
        catalog.update(
            {
                key: uses_catalog_default(self, f"{key}_label")
                for key in ("handle", "instructions", "picked_up", "moved", "dropped", "cancelled")
            }
        )
        labels = {
            "label": self.i18n.tr("citry-ui-sortable-label") if catalog["label"] else kwargs.label,
            "handle": kwargs.handle_label,
            "instructions": (
                self.i18n.tr("citry-ui-sortable-instructions")
                if catalog["instructions"]
                else kwargs.instructions_label
            ),
            "picked_up": kwargs.picked_up_label,
            "moved": kwargs.moved_label,
            "dropped": kwargs.dropped_label,
            "cancelled": kwargs.cancelled_label,
        }
        for key, label in labels.items():
            labels[key] = cast("str", _plain(f"CSortable {key}_label", label))
        required = {
            "handle": ("{item}",),
            "picked_up": ("{item}", "{position}", "{total}"),
            "moved": ("{item}", "{position}", "{total}"),
            "dropped": ("{item}", "{position}", "{total}"),
            "cancelled": ("{item}", "{position}", "{total}"),
        }
        for key, fields in required.items():
            if not catalog[key] and any(field not in labels[key] for field in fields):
                raise ValueError(f"CSortable {key}_label must contain {' and '.join(fields)}.")
        registry = _SortableRegistry()
        self.provide(_CONTEXT, registry=registry)
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "order": _order(kwargs.order, optional=True),
            "name": name,
            "form": form,
            "layout": _choice("CSortable layout", kwargs.layout, _LAYOUTS),
            "disabled": bool(kwargs.disabled),
            "size": _choice("CSortable size", kwargs.size, _SIZES),
            "catalog": catalog,
            "labels": labels,
            "attrs": _attrs("CSortable", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }
        self._cui_sortable_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {key: snapshot[key] for key in ("order", "name", "form", "layout", "disabled", "catalog", "labels")}

    template = """
      <c-CInternalSortableDeclarations><c-slot required /></c-CInternalSortableDeclarations>
      <c-CInternalSortable
        c-root_id="root_id" c-order="order" c-name="name" c-form="form"
        c-layout="layout" c-disabled="disabled" c-size="size"
        c-catalog="catalog" c-labels="labels" c-attrs="attrs" c-registry="registry"
      />
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"

    messages = """
      citry-ui-sortable-label = Reorder items
      # @param {str} $item - Plain item label.
      citry-ui-sortable-handle = Move { $item }
      citry-ui-sortable-instructions = Press Space or Enter to pick up. Use arrow keys to move. Press Space or Enter to drop, or Escape to cancel.
      # @param {str} $item - Plain item label.
      # @param {str} $position - Locale-formatted one-based position.
      # @param {str} $total - Locale-formatted total item count.
      citry-ui-sortable-picked-up = Picked up { $item }, position { $position } of { $total }
      # @param {str} $item - Plain item label.
      # @param {str} $position - Locale-formatted one-based position.
      # @param {str} $total - Locale-formatted total item count.
      citry-ui-sortable-moved = Moved { $item } to position { $position } of { $total }
      # @param {str} $item - Plain item label.
      # @param {str} $position - Locale-formatted one-based position.
      # @param {str} $total - Locale-formatted total item count.
      citry-ui-sortable-dropped = Dropped { $item } at position { $position } of { $total }
      # @param {str} $item - Plain item label.
      # @param {str} $position - Locale-formatted one-based position.
      # @param {str} $total - Locale-formatted total item count.
      citry-ui-sortable-cancelled = Cancelled moving { $item }. Position restored to { $position } of { $total }
    """


class CSortableItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        label: str
        disabled: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSortableItemSlotData] | None = None
        handle: SlotInput[CSortableItemSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        validate_boolean("CSortableItem", "disabled", kwargs.disabled)
        registry = _registry(self)
        value = cast("str", _plain("CSortableItem value", kwargs.value))
        if any(item.value == value for item in registry.items):
            raise ValueError(f"CSortableItem value {value!r} is duplicated.")
        registry.items.append(
            _SortableDeclaration(
                value=value,
                label=cast("str", _plain("CSortableItem label", kwargs.label)),
                disabled=bool(kwargs.disabled),
                attrs=_attrs("CSortableItem", kwargs.attrs, _ITEM_OWNED, kwargs.class_, kwargs.style),
                content=cast("Slot[CSortableItemSlotData] | None", slots.default),
                handle=cast("Slot[CSortableItemSlotData] | None", slots.handle),
            )
        )
        self.unprovide(_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalSortableDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CSortableDefaultSlotData]

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CSortable declaration collection completed without a render result.")
        _validate_declaration_output(result)

    template = "<c-slot required />"


class CInternalSortable(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        root_id: str
        order: tuple[str, ...] | None
        name: str | None
        form: str | None
        layout: CSortableLayout
        disabled: bool
        size: CSortableSize
        catalog: dict[str, bool]
        labels: dict[str, str]
        attrs: dict[str, object]
        registry: _SortableRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        declarations = kwargs.registry.items
        if not declarations:
            raise ValueError("CSortable requires at least one CSortableItem declaration.")
        authored = tuple(item.value for item in declarations)
        order = authored if kwargs.order is None else kwargs.order
        if set(order) != set(authored) or len(order) != len(authored):
            raise ValueError("CSortable order must contain every declared Item value exactly once.")
        by_value = {item.value: item for item in declarations}
        items = []
        for index, value in enumerate(order):
            item = by_value[value]
            data: CSortableItemSlotData = {
                "value": value,
                "label": item.label,
                "disabled": item.disabled,
                "index": index,
            }
            content: object = item.label
            if item.content is not None:
                content = Slot(
                    lambda ctx, declaration=item, slot_data=data: cast(
                        "Slot[CSortableItemSlotData]", declaration.content
                    )(slot_data, provides=dict(ctx.provides or {}))
                )
            handle: object | None = None
            if item.handle is not None:
                handle = Slot(
                    lambda ctx, declaration=item, slot_data=data: cast(
                        "Slot[CSortableItemSlotData]", declaration.handle
                    )(slot_data, provides=dict(ctx.provides or {}))
                )
            handle_label = (
                self.i18n.tr("citry-ui-sortable-handle", item=item.label)
                if kwargs.catalog["handle"]
                else kwargs.labels["handle"].format(item=item.label)
            )
            items.append(
                {
                    "declaration": item,
                    "index": index,
                    "content": content,
                    "handle": handle,
                    "handle_label": handle_label,
                    "item_id": f"{kwargs.root_id}-item-{index}",
                    "morph_key": f"sortable-item-{value}",
                }
            )
        self.unprovide(_CONTEXT)
        return {
            "attrs": {
                **kwargs.attrs,
                "aria-disabled": "true" if kwargs.disabled else "false",
                "data-disabled": True if kwargs.disabled else None,
                "data-layout": kwargs.layout,
                "data-size": kwargs.size,
            },
            "root_id": kwargs.root_id,
            "layout": kwargs.layout,
            "items": items,
            "name": kwargs.name,
            "form": kwargs.form,
            "disabled": kwargs.disabled,
            "catalog_label": kwargs.catalog["label"],
            "label": kwargs.labels["label"],
            "catalog_handle": kwargs.catalog["handle"],
            "instructions": kwargs.labels["instructions"],
        }

    template = """
      <div
        class="cui-sortable" c-bind="attrs" c-id="root_id"
        data-citry-ui-part="sortable"
      >
        <ol
          c-aria-label="tr('citry-ui-sortable-label') if catalog_label else label"
          c-$c-tr:citry-ui-sortable-label[aria-label]="True if catalog_label else None"
          data-citry-sortable-items data-citry-ui-part="items"
        >
          <c-for each="item in items"><c-CInternalSortableItem c-item="item" c-name="name" c-form="form" c-disabled="disabled" c-catalog_handle="catalog_handle" /></c-for>
        </ol>
        <p data-citry-sortable-instructions data-citry-ui-part="instructions">{{ instructions }}</p>
        <div aria-live="polite" aria-atomic="true" data-citry-ui-part="status"></div>
      </div>
    """


class CInternalSortableItem(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        item: dict[str, object]
        name: str | None
        form: str | None
        disabled: bool
        catalog_handle: bool

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        item = kwargs.item
        declaration = cast("_SortableDeclaration", item["declaration"])
        return {
            **item,
            "attrs": {
                **declaration.attrs,
                "aria-disabled": "true" if declaration.disabled else None,
                "data-disabled": True if declaration.disabled else None,
                "data-value": declaration.value,
                "role": "listitem",
            },
            "value": declaration.value,
            "label": declaration.label,
            "button_disabled": kwargs.disabled or declaration.disabled,
            "root_disabled": kwargs.disabled,
            "name": kwargs.name,
            "form": kwargs.form,
            "catalog_handle_attr": True if kwargs.catalog_handle else None,
            "handle_values_expression": (
                "{ item: $el.closest('[data-citry-sortable-item]').dataset.label }" if kwargs.catalog_handle else None
            ),
        }

    template = """
      <li class="cui-sortable__item" #c-key="morph_key" c-bind="attrs" c-id="item_id" c-data-label="label" data-citry-sortable-item data-citry-ui-part="item">
        <button
          type="button" c-disabled="button_disabled"
          c-aria-label="tr('citry-ui-sortable-handle', item=label) if catalog_handle_attr else handle_label"
          c-$c-tr:citry-ui-sortable-handle[aria-label]="handle_values_expression"
          data-citry-sortable-handle data-citry-ui-part="handle"
        ><c-if cond="handle is not None">{{ handle }}</c-if><c-else><span aria-hidden="true">⠿</span></c-else></button>
        <div data-citry-ui-part="content">{{ content }}</div>
        <input c-if="name is not None" type="hidden" c-name="name" c-form="form" c-value="value" c-disabled="root_disabled" data-citry-sortable-input />
      </li>
    """


__all__ = [
    "CSortable",
    "CSortableChangeSource",
    "CSortableDefaultSlotData",
    "CSortableItem",
    "CSortableItemSlotData",
    "CSortableLayout",
    "CSortableOrderChangeDetail",
    "CSortableSize",
]
