"""Form-capable, progressively enhanced Transfer List."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast

from citry import CitryRender, LibraryComponent, Slot, SlotInput, const_value
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import reject_owned_attrs, validate_boolean, validate_html_id

CTransferListSize = Literal["sm", "md", "lg"]
CTransferListChangeSource = Literal[
    "add",
    "add-all",
    "remove",
    "remove-all",
    "move-top",
    "move-up",
    "move-down",
    "move-bottom",
    "reset",
    "client",
]

_TRANSFER_CONTEXT = "citry_ui_transfer_list"
_SIZES = ("sm", "md", "lg")
_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-invalid",
        "contenteditable",
        "data-available-empty",
        "data-chosen-empty",
        "data-citry-transfer-list-initialized",
        "data-citry-ui-part",
        "data-disabled",
        "data-enhanced",
        "data-invalid",
        "data-required",
        "data-size",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_OPTION_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-selected",
        "contenteditable",
        "data-citry-ui-part",
        "data-disabled",
        "data-selected",
        "data-value",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)


class CTransferListDefaultSlotData:
    pass


class CTransferListItemDefaultSlotData(TypedDict):
    value: str
    label: str
    disabled: bool
    in_target: bool
    index: int


class CTransferListChangeDetail(TypedDict):
    value: list[str]
    previousValue: list[str]
    moved: list[str]
    source: CTransferListChangeSource
    controlled: bool
    sourceEvent: object | None


@dataclass(frozen=True, slots=True)
class _TransferDeclaration:
    value: str
    label: str
    disabled: bool
    attrs: dict[str, object]
    content: Slot[CTransferListItemDefaultSlotData] | None


@dataclass(slots=True)
class _TransferRegistry:
    items: list[_TransferDeclaration] = field(default_factory=list)


def _plain(name: str, value: object, *, optional: bool = False, single_line: bool = False) -> str | None:
    raw = const_value(value)
    if raw is None and optional:
        return None
    if not isinstance(raw, str):
        raise TypeError(f"{name} must be a string{' or None' if optional else ''}, got {raw!r}.")
    plain = "".join(raw).replace("\r\n", "\n").replace("\r", "\n")
    if not plain.strip() or "\x00" in plain or (single_line and "\n" in plain):
        suffix = ", CR, or LF" if single_line else ""
        raise ValueError(f"{name} must be nonempty and cannot contain U+0000{suffix}.")
    return plain


def _choice(name: str, value: object, allowed: tuple[str, ...]) -> str:
    plain = _plain(name, value)
    if plain not in allowed:
        expected = ", ".join(repr(item) for item in allowed)
        raise ValueError(f"{name} must be one of {expected}, got {plain!r}.")
    return cast("str", plain)


def _string_list(name: str, value: object) -> tuple[str, ...]:
    raw = const_value(value)
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise TypeError(f"{name} must be a sequence of strings, got {raw!r}.")
    result = tuple(cast("str", _plain(f"{name} item", item, single_line=True)) for item in raw)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicate values.")
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


def _registry(component: LibraryComponent) -> _TransferRegistry:
    provided = component.inject(_TRANSFER_CONTEXT, None)
    if provided is None:
        raise ValueError(
            "CTransferListItem is a declaration component and must be rendered directly inside CTransferList."
        )
    return cast("_TransferRegistry", provided.registry)


def _validate_declaration_output(result: CitryRender) -> None:
    if result.serialize(deps_strategy="ignore").strip():
        raise ValueError(
            "CTransferList default content may contain only CTransferListItem declarations, formatting whitespace, "
            "and transparent components that produce no other output."
        )


class CTransferList(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        id: str | None = None
        value: Sequence[str] = ()
        name: str | None = None
        form: str | None = None
        required: bool = False
        disabled: bool = False
        show_move_all: bool = True
        show_reorder: bool = True
        size: CTransferListSize = "md"
        available_label: str = "Available items"
        chosen_label: str = "Chosen items"
        available_empty_label: str = "No available items"
        chosen_empty_label: str = "No chosen items"
        count_label: str = "{selected} of {total} selected"
        transfer_controls_label: str = "Transfer controls"
        add_label: str = "Add selected"
        add_all_label: str = "Add all"
        remove_label: str = "Remove selected"
        remove_all_label: str = "Remove all"
        reorder_controls_label: str = "Chosen item order"
        move_top_label: str = "Move to top"
        move_up_label: str = "Move up"
        move_down_label: str = "Move down"
        move_bottom_label: str = "Move to bottom"
        added_label: str = "{count} items added"
        removed_label: str = "{count} items removed"
        reordered_label: str = "{count} items reordered"
        required_label: str = "Choose at least one item"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTransferListDefaultSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_transfer_list_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        if self.inject(_TRANSFER_CONTEXT, None) is not None:
            raise ValueError(
                "Nested CTransferList must be rendered inside CTransferListItem content, not as a direct declaration."
            )
        validate_html_id("CTransferList", kwargs.id)
        for name in ("required", "disabled", "show_move_all", "show_reorder"):
            validate_boolean("CTransferList", name, getattr(kwargs, name))
        root_id = kwargs.id or f"cui-transfer-list-{self.id}"
        form_name = cast("str | None", _plain("CTransferList name", kwargs.name, optional=True, single_line=True))
        form = cast("str | None", _plain("CTransferList form", kwargs.form, optional=True, single_line=True))
        validate_html_id("CTransferList", form)
        catalog = {
            name: uses_catalog_default(self, f"{name}_label")
            for name in (
                "available",
                "chosen",
                "available_empty",
                "chosen_empty",
                "count",
                "transfer_controls",
                "add",
                "add_all",
                "remove",
                "remove_all",
                "reorder_controls",
                "move_top",
                "move_up",
                "move_down",
                "move_bottom",
                "added",
                "removed",
                "reordered",
                "required",
            )
        }
        labels = {
            "available": self.i18n.tr("citry-ui-transfer-list-available")
            if catalog["available"]
            else kwargs.available_label,
            "chosen": self.i18n.tr("citry-ui-transfer-list-chosen") if catalog["chosen"] else kwargs.chosen_label,
            "available_empty": self.i18n.tr("citry-ui-transfer-list-available-empty")
            if catalog["available_empty"]
            else kwargs.available_empty_label,
            "chosen_empty": self.i18n.tr("citry-ui-transfer-list-chosen-empty")
            if catalog["chosen_empty"]
            else kwargs.chosen_empty_label,
            "count": kwargs.count_label,
            "transfer_controls": self.i18n.tr("citry-ui-transfer-list-transfer-controls")
            if catalog["transfer_controls"]
            else kwargs.transfer_controls_label,
            "add": self.i18n.tr("citry-ui-transfer-list-add") if catalog["add"] else kwargs.add_label,
            "add_all": self.i18n.tr("citry-ui-transfer-list-add-all") if catalog["add_all"] else kwargs.add_all_label,
            "remove": self.i18n.tr("citry-ui-transfer-list-remove") if catalog["remove"] else kwargs.remove_label,
            "remove_all": self.i18n.tr("citry-ui-transfer-list-remove-all")
            if catalog["remove_all"]
            else kwargs.remove_all_label,
            "reorder_controls": self.i18n.tr("citry-ui-transfer-list-reorder-controls")
            if catalog["reorder_controls"]
            else kwargs.reorder_controls_label,
            "move_top": self.i18n.tr("citry-ui-transfer-list-move-top")
            if catalog["move_top"]
            else kwargs.move_top_label,
            "move_up": self.i18n.tr("citry-ui-transfer-list-move-up") if catalog["move_up"] else kwargs.move_up_label,
            "move_down": self.i18n.tr("citry-ui-transfer-list-move-down")
            if catalog["move_down"]
            else kwargs.move_down_label,
            "move_bottom": self.i18n.tr("citry-ui-transfer-list-move-bottom")
            if catalog["move_bottom"]
            else kwargs.move_bottom_label,
            "added": kwargs.added_label,
            "removed": kwargs.removed_label,
            "reordered": kwargs.reordered_label,
            "required": self.i18n.tr("citry-ui-transfer-list-required")
            if catalog["required"]
            else kwargs.required_label,
        }
        for name, label in labels.items():
            labels[name] = cast("str", _plain(f"CTransferList {name}_label", label))
        for name in ("count", "added", "removed", "reordered"):
            required_fields = ("{selected}", "{total}") if name == "count" else ("{count}",)
            if not catalog[name] and any(field not in labels[name] for field in required_fields):
                fields = " and ".join(required_fields)
                raise ValueError(f"CTransferList {name}_label must contain {fields}.")
        registry = _TransferRegistry()
        self.provide(_TRANSFER_CONTEXT, registry=registry)
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "native_id": f"{root_id}-native",
            "available_title_id": f"{root_id}-available-title",
            "chosen_title_id": f"{root_id}-chosen-title",
            "value": _string_list("CTransferList value", kwargs.value),
            "name": form_name,
            "form": form,
            "required": bool(kwargs.required),
            "disabled": bool(kwargs.disabled),
            "show_move_all": bool(kwargs.show_move_all),
            "show_reorder": bool(kwargs.show_reorder),
            "size": _choice("CTransferList size", kwargs.size, _SIZES),
            "labels": labels,
            "catalog": catalog,
            "attrs": _attrs("CTransferList", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            "registry": registry,
        }
        self._cui_transfer_list_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        snapshot = self._snapshot(kwargs)
        return {
            "value": snapshot["value"],
            "name": snapshot["name"],
            "form": snapshot["form"],
            "required": snapshot["required"],
            "disabled": snapshot["disabled"],
            "catalog": snapshot["catalog"],
            "labels": snapshot["labels"],
        }

    template = """
      <c-CInternalTransferListDeclarations><c-slot /></c-CInternalTransferListDeclarations>
      <c-CInternalTransferList
        c-root_id="root_id"
        c-native_id="native_id"
        c-available_title_id="available_title_id"
        c-chosen_title_id="chosen_title_id"
        c-value="value"
        c-name="name"
        c-form="form"
        c-required="required"
        c-disabled="disabled"
        c-show_move_all="show_move_all"
        c-show_reorder="show_reorder"
        c-size="size"
        c-labels="labels"
        c-catalog="catalog"
        c-attrs="attrs"
        c-registry="registry"
      />
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"

    messages = """
      citry-ui-transfer-list-available = Available items
      citry-ui-transfer-list-chosen = Chosen items
      citry-ui-transfer-list-available-empty = No available items
      citry-ui-transfer-list-chosen-empty = No chosen items
      # @param {str} $selected - Locale-formatted number of selected options in this pane.
      # @param {str} $total - Locale-formatted total number of options in this pane.
      citry-ui-transfer-list-count = { $selected } of { $total } selected
      citry-ui-transfer-list-transfer-controls = Transfer controls
      citry-ui-transfer-list-add = Add selected
      citry-ui-transfer-list-add-all = Add all
      citry-ui-transfer-list-remove = Remove selected
      citry-ui-transfer-list-remove-all = Remove all
      citry-ui-transfer-list-reorder-controls = Chosen item order
      citry-ui-transfer-list-move-top = Move to top
      citry-ui-transfer-list-move-up = Move up
      citry-ui-transfer-list-move-down = Move down
      citry-ui-transfer-list-move-bottom = Move to bottom
      citry-ui-transfer-list-added-one = One item added
      # @param {str} $count - Locale-formatted number of options added.
      citry-ui-transfer-list-added = { $count } items added
      citry-ui-transfer-list-removed-one = One item removed
      # @param {str} $count - Locale-formatted number of options removed.
      citry-ui-transfer-list-removed = { $count } items removed
      citry-ui-transfer-list-reordered-one = One item reordered
      # @param {str} $count - Locale-formatted number of options reordered.
      citry-ui-transfer-list-reordered = { $count } items reordered
      citry-ui-transfer-list-required = Choose at least one item
    """


class CTransferListItem(LibraryComponent):
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
        default: SlotInput[CTransferListItemDefaultSlotData] | None = None

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        validate_boolean("CTransferListItem", "disabled", kwargs.disabled)
        registry = _registry(self)
        value = cast("str", _plain("CTransferListItem value", kwargs.value, single_line=True))
        if any(item.value == value for item in registry.items):
            raise ValueError(f"CTransferListItem value {value!r} is duplicated.")
        registry.items.append(
            _TransferDeclaration(
                value=value,
                label=cast("str", _plain("CTransferListItem label", kwargs.label)),
                disabled=bool(kwargs.disabled),
                attrs=_attrs("CTransferListItem", kwargs.attrs, _OPTION_OWNED, kwargs.class_, kwargs.style),
                content=(cast("Slot[CTransferListItemDefaultSlotData]", slots.default) if slots.default else None),
            )
        )
        self.unprovide(_TRANSFER_CONTEXT)
        return {}

    def on_render(self) -> str:
        return ""


class CInternalTransferListDeclarations(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        pass

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTransferListDefaultSlotData] | None = None

    def on_render(self) -> Any:
        result, error = yield
        if error is not None:
            raise error
        if result is None:
            raise RuntimeError("CTransferList declaration collection completed without a render result.")
        _validate_declaration_output(result)

    template = "<c-slot />"


class CInternalTransferList(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        root_id: str
        native_id: str
        available_title_id: str
        chosen_title_id: str
        value: tuple[str, ...]
        name: str | None
        form: str | None
        required: bool
        disabled: bool
        show_move_all: bool
        show_reorder: bool
        size: CTransferListSize
        labels: dict[str, str]
        catalog: dict[str, bool]
        attrs: dict[str, object]
        registry: _TransferRegistry

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        declarations = kwargs.registry.items
        known = {item.value for item in declarations}
        unknown = [value for value in kwargs.value if value not in known]
        if unknown:
            raise ValueError(f"CTransferList value contains unknown item values: {unknown!r}.")
        chosen = set(kwargs.value)
        items: list[dict[str, object]] = []
        for authored_index, declaration in enumerate(declarations):
            in_target = declaration.value in chosen
            pane_values = (
                kwargs.value if in_target else tuple(item.value for item in declarations if item.value not in chosen)
            )
            index = pane_values.index(declaration.value)
            slot_data: CTransferListItemDefaultSlotData = {
                "value": declaration.value,
                "label": declaration.label,
                "disabled": declaration.disabled,
                "in_target": in_target,
                "index": index,
            }
            content: object = declaration.label
            if declaration.content is not None:
                content = Slot(
                    lambda ctx, item=declaration, data=slot_data: cast(
                        "Slot[CTransferListItemDefaultSlotData]", item.content
                    )(data, provides=dict(ctx.provides or {}))
                )
            items.append(
                {
                    "declaration": declaration,
                    "authored_index": authored_index,
                    "in_target": in_target,
                    "index": index,
                    "content": content,
                    "option_id": f"{kwargs.root_id}-option-{authored_index}",
                }
            )
        self.unprovide(_TRANSFER_CONTEXT)
        available_total = sum(not cast("bool", item["in_target"]) for item in items)
        chosen_total = len(kwargs.value)
        count_available = (
            self.i18n.tr("citry-ui-transfer-list-count", selected=str(0), total=str(available_total))
            if kwargs.catalog["count"]
            else kwargs.labels["count"].format(selected=0, total=available_total)
        )
        count_chosen = (
            self.i18n.tr("citry-ui-transfer-list-count", selected=str(0), total=str(chosen_total))
            if kwargs.catalog["count"]
            else kwargs.labels["count"].format(selected=0, total=chosen_total)
        )
        native_size = min(10, max(4, len(items)))
        return {
            **{
                field: getattr(kwargs, field)
                for field in (
                    "root_id",
                    "native_id",
                    "available_title_id",
                    "chosen_title_id",
                    "name",
                    "form",
                    "required",
                    "disabled",
                    "show_move_all",
                    "show_reorder",
                    "size",
                    "labels",
                    "catalog",
                    "attrs",
                )
            },
            "items": items,
            "available_items": [item for item in items if not item["in_target"]],
            "chosen_items": sorted(
                (item for item in items if item["in_target"]), key=lambda item: cast("int", item["index"])
            ),
            "native_items": [item for item in items if not item["in_target"]]
            + sorted((item for item in items if item["in_target"]), key=lambda item: cast("int", item["index"])),
            "available_total": available_total,
            "chosen_total": chosen_total,
            "count_available": count_available,
            "count_chosen": count_chosen,
            "native_size": native_size,
            "ae_catalog": kwargs.catalog["available_empty"],
            "ae_label": kwargs.labels["available_empty"],
            "catalog_move_bottom": kwargs.catalog["move_bottom"],
            "move_bottom_label": kwargs.labels["move_bottom"],
        }

    template = """
      <div
        class="cui-transfer-list"
        c-bind="attrs"
        c-id="root_id"
        c-data-required="True if required else None"
        c-data-disabled="True if disabled else None"
        c-data-available-empty="True if available_total == 0 else None"
        c-data-chosen-empty="True if chosen_total == 0 else None"
        c-data-size="size"
        c-aria-disabled="'true' if disabled else 'false'"
        data-citry-ui-part="transfer-list"
      >
        <label data-citry-transfer-native-fallback>
          <span
            c-$c-tr:citry-ui-transfer-list-chosen="True if catalog['chosen'] else None"
          >{{ tr('citry-ui-transfer-list-chosen') if catalog['chosen'] else labels['chosen'] }}</span>
          <select
            c-id="native_id"
            c-name="name"
            c-form="form"
            c-required="required"
            c-disabled="disabled"
            c-size="native_size"
            multiple
            data-citry-transfer-list-native
            data-citry-ui-part="native"
          >
            <c-for each="item in native_items">
              <option
                c-if="item['in_target'] and item['declaration'].disabled"
                c-value="item['declaration'].value"
                c-label="item['declaration'].label"
                selected
                hidden
                data-citry-transfer-disabled-value-proxy
              ></option>
              <option
                c-value="item['declaration'].value"
                c-selected="item['in_target']"
                c-disabled="item['declaration'].disabled"
              >{{ item['declaration'].label }}</option>
            </c-for>
          </select>
        </label>
        <span hidden data-citry-transfer-list-transport></span>
        <div hidden data-citry-ui-part="control">
          <div data-citry-transfer-pane="available" data-citry-ui-part="pane">
            <header data-citry-ui-part="pane-header">
              <div c-id="available_title_id" data-citry-ui-part="pane-title">
                <span c-$c-tr:citry-ui-transfer-list-available="True if catalog['available'] else None"
                >{{ tr('citry-ui-transfer-list-available') if catalog['available'] else labels['available'] }}</span>
              </div>
              <span data-citry-ui-part="count">{{ count_available }}</span>
            </header>
            <div
              c-aria-labelledby="available_title_id"
              c-aria-disabled="'true' if disabled else 'false'"
              role="listbox"
              aria-multiselectable="true"
              tabindex="0"
              data-citry-transfer-listbox="available"
              data-citry-ui-part="listbox"
            >
              <c-for each="item in available_items"><c-CInternalTransferListItem c-item="item" /></c-for>
            </div>
            <p
              c-hidden="available_total != 0"
              c-$c-tr:citry-ui-transfer-list-available-empty="True if catalog['available_empty'] else None"
              data-citry-ui-part="empty"
            >{{ tr('citry-ui-transfer-list-available-empty') if ae_catalog else ae_label }}</p>
          </div>
          <div
            c-aria-label="
              tr('citry-ui-transfer-list-transfer-controls')
              if catalog['transfer_controls'] else labels['transfer_controls']
            "
            c-$c-tr:citry-ui-transfer-list-transfer-controls[aria-label]="
              True if catalog['transfer_controls'] else None
            "
            role="toolbar"
            data-citry-ui-part="transfer-controls"
          >
            <button type="button" disabled data-citry-transfer-action="add" data-citry-ui-part="button"
              c-$c-tr:citry-ui-transfer-list-add="True if catalog['add'] else None"
            >{{ tr('citry-ui-transfer-list-add') if catalog['add'] else labels['add'] }}</button>
            <button c-hidden="not show_move_all" type="button" disabled data-citry-transfer-action="add-all"
              data-citry-ui-part="button" c-$c-tr:citry-ui-transfer-list-add-all="True if catalog['add_all'] else None"
            >{{ tr('citry-ui-transfer-list-add-all') if catalog['add_all'] else labels['add_all'] }}</button>
            <button
              type="button" disabled data-citry-transfer-action="remove" data-citry-ui-part="button"
              c-$c-tr:citry-ui-transfer-list-remove="True if catalog['remove'] else None"
            >{{ tr('citry-ui-transfer-list-remove') if catalog['remove'] else labels['remove'] }}</button>
            <button c-hidden="not show_move_all" type="button" disabled data-citry-transfer-action="remove-all"
              data-citry-ui-part="button"
              c-$c-tr:citry-ui-transfer-list-remove-all="True if catalog['remove_all'] else None"
            >{{ tr('citry-ui-transfer-list-remove-all') if catalog['remove_all'] else labels['remove_all'] }}</button>
          </div>
          <div data-citry-transfer-pane="chosen" data-citry-ui-part="pane">
            <header data-citry-ui-part="pane-header">
              <div c-id="chosen_title_id" data-citry-ui-part="pane-title">
                <span c-$c-tr:citry-ui-transfer-list-chosen="True if catalog['chosen'] else None"
                >{{ tr('citry-ui-transfer-list-chosen') if catalog['chosen'] else labels['chosen'] }}</span>
              </div>
              <span data-citry-ui-part="count">{{ count_chosen }}</span>
            </header>
            <div
              c-aria-labelledby="chosen_title_id"
              c-aria-disabled="'true' if disabled else 'false'"
              role="listbox"
              aria-multiselectable="true"
              tabindex="0"
              data-citry-transfer-listbox="chosen"
              data-citry-ui-part="listbox"
            >
              <c-for each="item in chosen_items"><c-CInternalTransferListItem c-item="item" /></c-for>
            </div>
            <p c-hidden="chosen_total != 0"
              c-$c-tr:citry-ui-transfer-list-chosen-empty="True if catalog['chosen_empty'] else None"
              data-citry-ui-part="empty"
            >{{ tr('citry-ui-transfer-list-chosen-empty') if catalog['chosen_empty'] else labels['chosen_empty'] }}</p>
            <div
              c-hidden="not show_reorder"
              c-aria-label="
                tr('citry-ui-transfer-list-reorder-controls')
                if catalog['reorder_controls'] else labels['reorder_controls']
              "
              c-$c-tr:citry-ui-transfer-list-reorder-controls[aria-label]="
                True if catalog['reorder_controls'] else None
              "
              role="toolbar"
              data-citry-ui-part="reorder-controls"
            >
              <button type="button" disabled data-citry-transfer-action="move-top" data-citry-ui-part="button"
                c-$c-tr:citry-ui-transfer-list-move-top="True if catalog['move_top'] else None"
              >{{ tr('citry-ui-transfer-list-move-top') if catalog['move_top'] else labels['move_top'] }}</button>
              <button type="button" disabled data-citry-transfer-action="move-up" data-citry-ui-part="button"
                c-$c-tr:citry-ui-transfer-list-move-up="True if catalog['move_up'] else None"
              >{{ tr('citry-ui-transfer-list-move-up') if catalog['move_up'] else labels['move_up'] }}</button>
              <button type="button" disabled data-citry-transfer-action="move-down" data-citry-ui-part="button"
                c-$c-tr:citry-ui-transfer-list-move-down="True if catalog['move_down'] else None"
              >{{ tr('citry-ui-transfer-list-move-down') if catalog['move_down'] else labels['move_down'] }}</button>
              <button type="button" disabled data-citry-transfer-action="move-bottom" data-citry-ui-part="button"
                c-$c-tr:citry-ui-transfer-list-move-bottom="True if catalog['move_bottom'] else None"
              >{{ tr('citry-ui-transfer-list-move-bottom') if catalog_move_bottom else move_bottom_label }}</button>
            </div>
          </div>
        </div>
        <div aria-live="polite" aria-atomic="true" data-citry-ui-part="status"></div>
      </div>
    """


class CInternalTransferListItem(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        item: dict[str, object]

    @dataclass(slots=True)
    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        item = kwargs.item
        declaration = cast("_TransferDeclaration", item["declaration"])
        return {
            "attrs": {
                **declaration.attrs,
                "aria-disabled": "true" if declaration.disabled else None,
                "aria-selected": "false",
                "data-disabled": True if declaration.disabled else None,
                "data-value": declaration.value,
            },
            "content": item["content"],
            "label": declaration.label,
            "option_id": item["option_id"],
            "morph_key": f"transfer-list-item-{declaration.value}",
        }

    template = """
      <div
        class="cui-transfer-list__option"
        #c-key="morph_key"
        c-bind="attrs"
        c-id="option_id"
        c-data-label="label"
        role="option"
        data-citry-transfer-option
        data-citry-ui-part="option"
      >{{ content }}</div>
    """


__all__ = [
    "CTransferList",
    "CTransferListChangeDetail",
    "CTransferListChangeSource",
    "CTransferListDefaultSlotData",
    "CTransferListItem",
    "CTransferListItemDefaultSlotData",
    "CTransferListSize",
]
