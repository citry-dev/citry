"""Repeatable field-group controls for one application-owned form."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CFormCollectionSize = Literal["sm", "md", "lg"]
CFormCollectionAction = Literal["add", "remove", "move-up", "move-down"]

_CONTEXT = "citry_ui_form_collection"
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-describedby",
        "contenteditable",
        "data-citry-ui-part",
        "data-count",
        "data-citry-form-collection-initialized",
        "data-disabled",
        "data-size",
        "disabled",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_ITEM_OWNED = frozenset(
    {
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-first",
        "data-last",
        "data-value",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CFormCollectionDefaultSlotData:
    pass


class CFormCollectionItemSlotData(TypedDict):
    value: str
    label: str
    index: int
    count: int
    is_first: bool
    is_last: bool
    disabled: bool


class CFormCollectionActionDetail(TypedDict):
    action: CFormCollectionAction
    value: str | None
    index: int | None
    toIndex: int | None
    sourceEvent: object


@dataclass(frozen=True, slots=True)
class _ItemDeclaration:
    value: str
    label: str
    remove_value: str | None
    move_up_value: str | None
    move_down_value: str | None
    removable: bool
    movable: bool
    disabled: bool
    attrs: dict[str, object]
    content: Slot[CFormCollectionItemSlotData]


@dataclass(slots=True)
class _Registry:
    items: list[_ItemDeclaration] = field(default_factory=list)


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
        raise ValueError(f"{name} must be one of {', '.join(repr(item) for item in allowed)}, got {plain!r}.")
    return cast("str", plain)


def _integer(name: str, value: object, *, minimum: int = 0, optional: bool = False) -> int | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise TypeError(f"{name} must be an integer{' or None' if optional else ''}, got {raw!r}.")
    if raw < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {raw}.")
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


def _registry(component: LibraryComponent) -> _Registry:
    provided = component.inject(_CONTEXT, None)
    if provided is None:
        raise ValueError("CFormCollectionItem must be rendered directly inside CFormCollection.")
    return cast("_Registry", provided.registry)


def _validate_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CFormCollection default content may contain only CFormCollectionItem declarations, formatting "
            "whitespace, and transparent components that produce no other output."
        )


class CFormCollection(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        label: str
        id: str | None = None
        description: str | None = None
        action_name: str | None = None
        add_value: str = "add"
        allow_add: bool = True
        allow_remove: bool = True
        allow_reorder: bool = True
        min_items: int = 0
        max_items: int | None = None
        disabled: bool = False
        size: CFormCollectionSize = "md"
        add_label: str = "Add item"
        remove_label: str = "Remove {item}"
        move_up_label: str = "Move {item} up"
        move_down_label: str = "Move {item} down"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CFormCollectionDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_form_collection_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_CONTEXT, None) is not None:
            raise ValueError(
                "Nested CFormCollection must be rendered inside Item content, not as a direct declaration."
            )
        validate_html_id("CFormCollection", kwargs.id)
        for name in ("allow_add", "allow_remove", "allow_reorder", "disabled"):
            validate_boolean("CFormCollection", name, getattr(kwargs, name))
        minimum = cast("int", _integer("CFormCollection min_items", kwargs.min_items))
        maximum = cast("int | None", _integer("CFormCollection max_items", kwargs.max_items, optional=True))
        if maximum is not None and maximum < minimum:
            raise ValueError("CFormCollection max_items must be greater than or equal to min_items.")
        root_id = kwargs.id or f"cui-form-collection-{self.id}"
        catalog = {
            key: uses_catalog_default(self, f"{key}_label") for key in ("add", "remove", "move_up", "move_down")
        }
        labels = {
            "add": self.i18n.tr("citry-ui-form-collection-add") if catalog["add"] else kwargs.add_label,
            "remove": kwargs.remove_label,
            "move_up": kwargs.move_up_label,
            "move_down": kwargs.move_down_label,
        }
        for key, label in labels.items():
            labels[key] = cast("str", _plain(f"CFormCollection {key}_label", label))
        for key in ("remove", "move_up", "move_down"):
            if not catalog[key] and "{item}" not in labels[key]:
                raise ValueError(f"CFormCollection {key}_label must contain {{item}}.")
        registry = _Registry()
        self.provide(_CONTEXT, registry=registry)
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "legend_id": f"{root_id}-legend",
            "description_id": f"{root_id}-description",
            "label": cast("str", _plain("CFormCollection label", kwargs.label)),
            "description": cast(
                "str | None", _plain("CFormCollection description", kwargs.description, optional=True)
            ),
            "action_name": cast(
                "str | None", _plain("CFormCollection action_name", kwargs.action_name, optional=True)
            ),
            "add_value": cast("str", _plain("CFormCollection add_value", kwargs.add_value)),
            "allow_add": bool(kwargs.allow_add),
            "allow_remove": bool(kwargs.allow_remove),
            "allow_reorder": bool(kwargs.allow_reorder),
            "min_items": minimum,
            "max_items": maximum,
            "disabled": bool(kwargs.disabled),
            "size": _choice("CFormCollection size", kwargs.size, _SIZES),
            "catalog": catalog,
            "labels": labels,
            "attrs": _attrs("CFormCollection", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }
        self._cui_form_collection_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {"disabled": snapshot["disabled"]}

    template = """
      <c-CInternalFormCollectionDeclarations><c-slot /></c-CInternalFormCollectionDeclarations>
      <c-CInternalFormCollection
        c-root_id="root_id" c-legend_id="legend_id" c-description_id="description_id"
        c-label="label" c-description="description" c-action_name="action_name" c-add_value="add_value"
        c-allow_add="allow_add" c-allow_remove="allow_remove" c-allow_reorder="allow_reorder"
        c-min_items="min_items" c-max_items="max_items" c-disabled="disabled" c-size="size"
        c-catalog="catalog" c-labels="labels" c-attrs="attrs" c-registry="registry"
      />
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"

    messages = """
      citry-ui-form-collection-add = Add item
      # @param {str} $item - Application-localized Item label.
      citry-ui-form-collection-remove = Remove { $item }
      # @param {str} $item - Application-localized Item label.
      citry-ui-form-collection-move-up = Move { $item } up
      # @param {str} $item - Application-localized Item label.
      citry-ui-form-collection-move-down = Move { $item } down
    """


class CFormCollectionItem(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        value: str
        label: str
        remove_value: str | None = None
        move_up_value: str | None = None
        move_down_value: str | None = None
        removable: bool = True
        movable: bool = True
        disabled: bool = False
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CFormCollectionItemSlotData]

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if "default" not in self.raw_slots:
            raise ValueError("CFormCollectionItem requires field-group content.")
        for name in ("removable", "movable", "disabled"):
            validate_boolean("CFormCollectionItem", name, getattr(kwargs, name))
        registry = _registry(self)
        value = cast("str", _plain("CFormCollectionItem value", kwargs.value))
        if any(item.value == value for item in registry.items):
            raise ValueError(f"CFormCollectionItem value {value!r} is duplicated.")
        registry.items.append(
            _ItemDeclaration(
                value=value,
                label=cast("str", _plain("CFormCollectionItem label", kwargs.label)),
                remove_value=cast(
                    "str | None", _plain("CFormCollectionItem remove_value", kwargs.remove_value, optional=True)
                ),
                move_up_value=cast(
                    "str | None", _plain("CFormCollectionItem move_up_value", kwargs.move_up_value, optional=True)
                ),
                move_down_value=cast(
                    "str | None", _plain("CFormCollectionItem move_down_value", kwargs.move_down_value, optional=True)
                ),
                removable=bool(kwargs.removable),
                movable=bool(kwargs.movable),
                disabled=bool(kwargs.disabled),
                attrs=_attrs("CFormCollectionItem", kwargs.attrs, _ITEM_OWNED, kwargs.class_, kwargs.style),
                content=cast("Slot[CFormCollectionItemSlotData]", slots.default),
            )
        )
        self.unprovide(_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalFormCollectionDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CFormCollectionDefaultSlotData] | None = None

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CFormCollection declaration collection completed without a render result.")
        _validate_output(result)

    template = "<c-slot />"


class CInternalFormCollection(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        root_id: str
        legend_id: str
        description_id: str
        label: str
        description: str | None
        action_name: str | None
        add_value: str
        allow_add: bool
        allow_remove: bool
        allow_reorder: bool
        min_items: int
        max_items: int | None
        disabled: bool
        size: CFormCollectionSize
        catalog: dict[str, bool]
        labels: dict[str, str]
        attrs: dict[str, object]
        registry: _Registry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        count = len(kwargs.registry.items)
        if count < kwargs.min_items:
            raise ValueError(f"CFormCollection renders {count} Items but min_items is {kwargs.min_items}.")
        if kwargs.max_items is not None and count > kwargs.max_items:
            raise ValueError(f"CFormCollection renders {count} Items but max_items is {kwargs.max_items}.")
        items = []
        for index, declaration in enumerate(kwargs.registry.items):
            data: CFormCollectionItemSlotData = {
                "value": declaration.value,
                "label": declaration.label,
                "index": index,
                "count": count,
                "is_first": index == 0,
                "is_last": index == count - 1,
                "disabled": kwargs.disabled or declaration.disabled,
            }
            items.append(
                {
                    "declaration": declaration,
                    "content": Slot(
                        lambda ctx, item=declaration, slot_data=data: item.content(
                            slot_data, provides=dict(ctx.provides or {})
                        )
                    ),
                    "index": index,
                    "count": count,
                    "item_id": f"{kwargs.root_id}-item-{index}",
                    "label_id": f"{kwargs.root_id}-item-{index}-label",
                    "morph_key": f"form-collection-item-{declaration.value}",
                }
            )
        self.unprovide(_CONTEXT)
        add_disabled = kwargs.disabled or (kwargs.max_items is not None and count >= kwargs.max_items)
        return {
            "attrs": {
                **kwargs.attrs,
                "aria-describedby": kwargs.description_id if kwargs.description is not None else None,
                "data-count": count,
                "data-disabled": True if kwargs.disabled else None,
                "data-size": kwargs.size,
            },
            **{
                field: getattr(kwargs, field)
                for field in (
                    "root_id",
                    "legend_id",
                    "description_id",
                    "label",
                    "description",
                    "action_name",
                    "add_value",
                    "allow_add",
                    "allow_remove",
                    "allow_reorder",
                    "min_items",
                    "disabled",
                    "catalog",
                    "labels",
                )
            },
            "items": items,
            "count": count,
            "button_type": "submit" if kwargs.action_name is not None else "button",
            "add_disabled": add_disabled,
            "catalog_add": kwargs.catalog["add"],
        }

    template = """
      <fieldset class="cui-form-collection" c-bind="attrs" c-id="root_id" data-citry-ui-part="form-collection">
        <legend c-id="legend_id" data-citry-ui-part="legend">{{ label }}</legend>
        <p c-if="description is not None" c-id="description_id" data-citry-ui-part="description">{{ description }}</p>
        <ol data-citry-ui-part="items">
          <c-for each="item in items">
            <c-CInternalFormCollectionItem
              c-item="item" c-action_name="action_name" c-button_type="button_type"
              c-allow_remove="allow_remove" c-allow_reorder="allow_reorder" c-min_items="min_items"
              c-root_disabled="disabled" c-catalog="catalog" c-labels="labels"
            />
          </c-for>
        </ol>
        <button
          c-if="allow_add" c-type="button_type" c-name="action_name" c-value="add_value"
          c-disabled="add_disabled" c-formnovalidate="True if action_name is not None else None"
          data-citry-form-collection-action="add" data-citry-ui-part="add"
          c-$c-tr:citry-ui-form-collection-add="True if catalog_add else None"
        >{{ tr('citry-ui-form-collection-add') if catalog_add else labels['add'] }}</button>
      </fieldset>
    """


class CInternalFormCollectionItem(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        item: dict[str, object]
        action_name: str | None
        button_type: str
        allow_remove: bool
        allow_reorder: bool
        min_items: int
        root_disabled: bool
        catalog: dict[str, bool]
        labels: dict[str, str]

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        item = kwargs.item
        declaration = cast("_ItemDeclaration", item["declaration"])
        index = cast("int", item["index"])
        count = cast("int", item["count"])
        disabled = kwargs.root_disabled or declaration.disabled
        remove_disabled = disabled or count <= kwargs.min_items
        values_expression = "{ item: $el.closest('[data-citry-form-collection-item]').dataset.label }"
        return {
            **item,
            "attrs": {
                **declaration.attrs,
                "data-disabled": True if disabled else None,
                "data-citry-form-collection-item-disabled": True if declaration.disabled else None,
                "data-first": True if index == 0 else None,
                "data-last": True if index == count - 1 else None,
                "data-value": declaration.value,
            },
            "value": declaration.value,
            "label": declaration.label,
            "disabled": disabled,
            "action_name": kwargs.action_name,
            "button_type": kwargs.button_type,
            "formnovalidate": True if kwargs.action_name is not None else None,
            "show_remove": kwargs.allow_remove and declaration.removable,
            "show_reorder": kwargs.allow_reorder and declaration.movable,
            "remove_disabled": remove_disabled,
            "up_disabled": disabled or index == 0,
            "down_disabled": disabled or index == count - 1,
            "remove_value": declaration.remove_value or f"remove:{declaration.value}",
            "move_up_value": declaration.move_up_value or f"move-up:{declaration.value}",
            "move_down_value": declaration.move_down_value or f"move-down:{declaration.value}",
            "remove_label": kwargs.labels["remove"].format(item=declaration.label),
            "move_up_label": kwargs.labels["move_up"].format(item=declaration.label),
            "move_down_label": kwargs.labels["move_down"].format(item=declaration.label),
            "remove_binding": values_expression if kwargs.catalog["remove"] else None,
            "up_binding": values_expression if kwargs.catalog["move_up"] else None,
            "down_binding": values_expression if kwargs.catalog["move_down"] else None,
            "catalog_remove": kwargs.catalog["remove"],
            "catalog_up": kwargs.catalog["move_up"],
            "catalog_down": kwargs.catalog["move_down"],
        }

    template = """
      <li class="cui-form-collection__item" #c-key="morph_key" c-bind="attrs" c-id="item_id"
        c-data-label="label" data-citry-form-collection-item data-citry-ui-part="item">
        <div role="group" c-aria-labelledby="label_id">
          <header data-citry-ui-part="item-header">
            <div c-id="label_id" data-citry-ui-part="item-label">{{ label }}</div>
            <div data-citry-ui-part="item-actions">
            <button c-if="show_reorder" c-type="button_type" c-name="action_name" c-value="move_up_value"
              c-disabled="up_disabled" c-formnovalidate="formnovalidate"
              c-aria-label="tr('citry-ui-form-collection-move-up', item=label) if catalog_up else move_up_label"
              c-$c-tr:citry-ui-form-collection-move-up[aria-label]="up_binding"
              data-citry-form-collection-action="move-up">↑</button>
            <button c-if="show_reorder" c-type="button_type" c-name="action_name" c-value="move_down_value"
              c-disabled="down_disabled" c-formnovalidate="formnovalidate"
              c-aria-label="tr('citry-ui-form-collection-move-down', item=label) if catalog_down else move_down_label"
              c-$c-tr:citry-ui-form-collection-move-down[aria-label]="down_binding"
              data-citry-form-collection-action="move-down">↓</button>
            <button c-if="show_remove" c-type="button_type" c-name="action_name" c-value="remove_value"
              c-disabled="remove_disabled" c-formnovalidate="formnovalidate"
              c-aria-label="tr('citry-ui-form-collection-remove', item=label) if catalog_remove else remove_label"
              c-$c-tr:citry-ui-form-collection-remove[aria-label]="remove_binding"
              data-citry-form-collection-action="remove">&#215;</button>
            </div>
          </header>
          <div data-citry-ui-part="item-content">{{ content }}</div>
        </div>
      </li>
    """


__all__ = [
    "CFormCollection",
    "CFormCollectionAction",
    "CFormCollectionActionDetail",
    "CFormCollectionDefaultSlotData",
    "CFormCollectionItem",
    "CFormCollectionItemSlotData",
    "CFormCollectionSize",
]
