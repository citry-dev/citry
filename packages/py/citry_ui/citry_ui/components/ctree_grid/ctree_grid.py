"""Finite hierarchical records in an interactive tabular grid."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, SlotInput, const_value, merge_attrs
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CTreeGridSelection = Literal["none", "single", "multiple"]
CTreeGridDensity = Literal["compact", "comfortable", "spacious"]
CTreeGridAlign = Literal["start", "center", "end"]
CTreeGridSource = Literal["pointer", "keyboard", "reset"]

_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "contenteditable",
        "data-citry-tree-grid-initialized",
        "data-citry-ui-part",
        "data-density",
        "data-disabled",
        "data-selection",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_TABLE_OWNED = frozenset(
    {"aria-colcount", "aria-disabled", "aria-label", "aria-rowcount", "data-citry-ui-part", "role"}
)
_ROW_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-expanded",
        "aria-level",
        "aria-posinset",
        "aria-rowindex",
        "aria-selected",
        "aria-setsize",
        "data-citry-ui-part",
        "data-disabled",
        "data-expanded",
        "data-level",
        "data-parent-key",
        "data-row-key",
        "data-selected",
        "hidden",
        "id",
        "inert",
        "role",
    }
)
_CELL_OWNED = frozenset(
    {
        "aria-colindex",
        "data-align",
        "data-citry-ui-part",
        "data-column-index",
        "data-column-key",
        "data-row-key",
        "id",
        "role",
        "tabindex",
    }
)


@dataclass(frozen=True, slots=True)
class CTreeGridColumn:
    key: str
    label: str
    width: int = 160
    align: CTreeGridAlign = "start"
    header_attrs: Mapping[str, object] | None = None
    cell_attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTreeGridCell:
    value: object
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTreeGridRow:
    key: str
    label: str
    cells: Mapping[str, object | CTreeGridCell]
    children: Sequence[CTreeGridRow] = ()
    disabled: bool = False
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _Column:
    source: CTreeGridColumn
    index: int
    header_attrs: dict[str, object]
    cell_attrs: dict[str, object]


@dataclass(frozen=True, slots=True)
class _Cell:
    source: CTreeGridCell
    column: CTreeGridColumn
    index: int
    attrs: dict[str, object]


@dataclass(frozen=True, slots=True)
class _Row:
    source: CTreeGridRow
    cells: tuple[_Cell, ...]
    index: int
    level: int
    parent_key: str | None
    position: int
    set_size: int
    branch: bool
    visible: bool
    expanded: bool
    selected: bool
    attrs: dict[str, object]


class CTreeGridCaptionSlotData:
    pass


class CTreeGridToolbarSlotData:
    pass


class CTreeGridHeaderSlotData(TypedDict):
    column: CTreeGridColumn
    column_index: int


class CTreeGridCellSlotData(TypedDict):
    row: CTreeGridRow
    column: CTreeGridColumn
    cell: CTreeGridCell
    row_index: int
    column_index: int
    level: int
    expanded: bool
    selected: bool


class CTreeGridExpandedChangeDetail(TypedDict):
    expanded: list[str]
    previousExpanded: list[str]
    rowKey: str
    rowExpanded: bool
    controlled: bool
    source: CTreeGridSource
    sourceEvent: object


class CTreeGridSelectionChangeDetail(TypedDict):
    selected: list[str]
    previousSelected: list[str]
    rowKey: str
    rowSelected: bool
    controlled: bool
    source: CTreeGridSource
    sourceEvent: object


class CTreeGridCellActivateDetail(TypedDict):
    rowKey: str
    columnKey: str
    rowIndex: int
    columnIndex: int
    sourceEvent: object


def _dynamic_target(key: str) -> str | None:
    if key.startswith("x-bind:"):
        return key.removeprefix("x-bind:").split(".", 1)[0]
    if key.startswith((":", ".")):
        return key[1:].split(".", 1)[0]
    return None


def _attrs(
    owner: str,
    value: Mapping[str, object] | None,
    owned: frozenset[str],
    class_: CClassValue | None = None,
    style: CStyleValue | None = None,
) -> dict[str, object]:
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"{owner} must be a mapping or None, got {value!r}.")
    copied = dict(value or {})
    reject_owned_attrs(copied, owned, owner)
    for key in copied:
        if not isinstance(key, str):
            raise TypeError(f"{owner} requires string keys, got {key!r}.")
        normalized = key.casefold()
        if normalized.startswith(_RUNTIME_PREFIXES):
            raise ValueError(f"{owner} cannot contain Citry runtime attribute {key!r}.")
        if normalized.split(".", 1)[0] in _DIRECTIVES:
            raise ValueError(f"{owner} cannot use ownership directive {key!r}.")
        if _dynamic_target(normalized) in owned:
            raise ValueError(f"{owner} cannot dynamically bind owned attribute {key!r}.")
    return merge_root_attrs(copied, class_, style)


def _sequence(name: str, value: object) -> tuple[object, ...]:
    raw = const_value(value)
    if isinstance(raw, str | bytes | bytearray | Mapping) or not isinstance(raw, Sequence):
        raise TypeError(f"{name} must be a sequence, got {raw!r}.")
    return tuple(raw)


class CTreeGrid(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        columns: Sequence[CTreeGridColumn]
        rows: Sequence[CTreeGridRow]
        label: str
        id: str | None = None
        expanded: Sequence[str] = ()
        selection: CTreeGridSelection = "none"
        selected: Sequence[str] = ()
        name: str | None = None
        form: str | None = None
        disabled: bool = False
        density: CTreeGridDensity = "comfortable"
        expand_label: str = "Expand {row}"
        collapse_label: str = "Collapse {row}"
        expanded_label: str = "Expanded {row}"
        collapsed_label: str = "Collapsed {row}"
        selected_label: str = "Selected {row}"
        unselected_label: str = "Unselected {row}"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        table_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        caption: SlotInput[CTreeGridCaptionSlotData] | None = None
        toolbar: SlotInput[CTreeGridToolbarSlotData] | None = None
        header: SlotInput[CTreeGridHeaderSlotData] | None = None
        cell: SlotInput[CTreeGridCellSlotData] | None = None

    def _snapshot(self, kwargs: Kwargs) -> dict[str, object]:
        cached = getattr(self, "_cui_tree_grid_snapshot", None)
        if cached is not None:
            return cast("dict[str, object]", cached)
        validate_html_id("CTreeGrid", kwargs.id)
        validate_non_empty_string("CTreeGrid", "label", kwargs.label)
        for field_name in ("name", "form"):
            field_value = const_value(getattr(kwargs, field_name))
            if field_value is not None:
                validate_non_empty_string("CTreeGrid", field_name, field_value)
        validate_choice("CTreeGrid", "selection", kwargs.selection, ("none", "single", "multiple"))
        validate_choice("CTreeGrid", "density", kwargs.density, ("compact", "comfortable", "spacious"))
        validate_boolean("CTreeGrid", "disabled", kwargs.disabled)
        raw_columns = _sequence("CTreeGrid columns", kwargs.columns)
        if not raw_columns:
            raise ValueError("CTreeGrid requires at least one Column.")
        columns: list[_Column] = []
        keys: set[str] = set()
        for index, raw in enumerate(raw_columns):
            if not isinstance(raw, CTreeGridColumn):
                raise TypeError(f"CTreeGrid columns[{index}] must be CTreeGridColumn, got {raw!r}.")
            validate_non_empty_string("CTreeGridColumn", "key", raw.key)
            validate_non_empty_string("CTreeGridColumn", "label", raw.label)
            validate_choice("CTreeGridColumn", "align", raw.align, ("start", "center", "end"))
            if isinstance(raw.width, bool) or not isinstance(raw.width, int) or not 40 <= raw.width <= 2000:
                raise ValueError(f"CTreeGrid Column {raw.key!r} width must be an integer from 40 through 2000.")
            if raw.key in keys:
                raise ValueError(f"CTreeGrid Column key {raw.key!r} is duplicated.")
            keys.add(raw.key)
            columns.append(
                _Column(
                    raw,
                    index,
                    _attrs(f"CTreeGrid Column {raw.key!r} header_attrs", raw.header_attrs, _CELL_OWNED),
                    _attrs(f"CTreeGrid Column {raw.key!r} cell_attrs", raw.cell_attrs, _CELL_OWNED),
                )
            )
        expanded = tuple(cast("str", item) for item in _sequence("CTreeGrid expanded", kwargs.expanded))
        selected = tuple(cast("str", item) for item in _sequence("CTreeGrid selected", kwargs.selected))
        for name, values in (("expanded", expanded), ("selected", selected)):
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise TypeError(f"CTreeGrid {name} must contain nonempty strings.")
            if len(values) != len(set(values)):
                raise ValueError(f"CTreeGrid {name} cannot contain duplicates.")
        if kwargs.selection == "none" and selected:
            raise ValueError("CTreeGrid selected must be empty when selection is none.")
        if kwargs.selection == "single" and len(selected) > 1:
            raise ValueError("CTreeGrid single selection accepts at most one Row.")
        flat: list[_Row] = []
        seen: set[str] = set()
        branches: set[str] = set()
        disabled_rows: set[str] = set()

        def walk(values: object, level: int, parent_key: str | None, ancestors_visible: bool) -> None:
            siblings = _sequence("CTreeGrid rows", values)
            size = len(siblings)
            for position, raw in enumerate(siblings, 1):
                if not isinstance(raw, CTreeGridRow):
                    raise TypeError(f"CTreeGrid rows must contain CTreeGridRow, got {raw!r}.")
                validate_non_empty_string("CTreeGridRow", "key", raw.key)
                validate_non_empty_string("CTreeGridRow", "label", raw.label)
                validate_boolean("CTreeGridRow", "disabled", raw.disabled)
                if raw.key in seen:
                    raise ValueError(f"CTreeGrid Row key {raw.key!r} is duplicated.")
                seen.add(raw.key)
                if not isinstance(raw.cells, Mapping) or set(raw.cells) != keys:
                    raise ValueError(f"CTreeGrid Row {raw.key!r} cells must exactly match Column keys.")
                children = _sequence(f"CTreeGrid Row {raw.key!r} children", raw.children)
                branch = bool(children)
                if branch:
                    branches.add(raw.key)
                if raw.disabled:
                    disabled_rows.add(raw.key)
                cells: list[_Cell] = []
                for column in columns:
                    value = raw.cells[column.source.key]
                    cell = value if isinstance(value, CTreeGridCell) else CTreeGridCell(value)
                    cells.append(
                        _Cell(
                            cell,
                            column.source,
                            column.index,
                            merge_attrs(
                                column.cell_attrs,
                                _attrs(
                                    f"CTreeGrid Row {raw.key!r} Cell {column.source.key!r} attrs",
                                    cell.attrs,
                                    _CELL_OWNED,
                                ),
                            ),
                        )
                    )
                row_attrs = _attrs(f"CTreeGrid Row {raw.key!r} attrs", raw.attrs, _ROW_OWNED)
                is_expanded = raw.key in expanded
                flat.append(
                    _Row(
                        raw,
                        tuple(cells),
                        len(flat),
                        level,
                        parent_key,
                        position,
                        size,
                        branch,
                        ancestors_visible,
                        is_expanded,
                        raw.key in selected,
                        row_attrs,
                    )
                )
                walk(children, level + 1, raw.key, ancestors_visible and is_expanded)

        roots = _sequence("CTreeGrid rows", kwargs.rows)
        if not roots:
            raise ValueError("CTreeGrid requires at least one Row.")
        walk(roots, 1, None, ancestors_visible=True)
        unknown_expanded = set(expanded) - branches
        unknown_selected = set(selected) - seen
        if unknown_expanded:
            raise ValueError(f"CTreeGrid expanded contains unknown or leaf Rows: {sorted(unknown_expanded)!r}.")
        if unknown_selected:
            raise ValueError(f"CTreeGrid selected contains unknown Rows: {sorted(unknown_selected)!r}.")
        if set(selected) & disabled_rows:
            raise ValueError("CTreeGrid selected cannot contain disabled Rows.")
        catalog = {
            key: uses_catalog_default(self, f"{key}_label")
            for key in ("expand", "collapse", "expanded", "collapsed", "selected", "unselected")
        }
        labels = {key: getattr(kwargs, f"{key}_label") for key in catalog}
        for key, value in labels.items():
            validate_non_empty_string("CTreeGrid", f"{key}_label", value)
            if not catalog[key] and "{row}" not in value:
                raise ValueError(f"CTreeGrid {key}_label must contain {{row}}.")
        root_id = kwargs.id or f"cui-tree-grid-{self.id}"
        snapshot: dict[str, object] = {
            "root_id": root_id,
            "columns": tuple(columns),
            "rows": tuple(flat),
            "label": kwargs.label,
            "row_count": len(flat),
            "column_count": len(columns),
            "expanded": expanded,
            "selection": kwargs.selection,
            "selected": selected,
            "name": const_value(kwargs.name),
            "form": const_value(kwargs.form),
            "disabled": bool(kwargs.disabled),
            "density": kwargs.density,
            "catalog": catalog,
            "labels": labels,
            "has_toolbar": "toolbar" in self.raw_slots,
            "has_caption": "caption" in self.raw_slots,
            "attrs": merge_attrs(
                _attrs("CTreeGrid attrs", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
                {"style": {"--cui-tree-grid-min-width": f"{sum(item.source.width for item in columns)}px"}},
            ),
            "table_attrs": _attrs("CTreeGrid table_attrs", kwargs.table_attrs, _TABLE_OWNED),
        }
        self._cui_tree_grid_snapshot = snapshot
        return snapshot

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return self._snapshot(kwargs)

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
        data = self._snapshot(kwargs)
        return {
            key: data[key]
            for key in ("expanded", "selection", "selected", "name", "form", "disabled", "catalog", "labels")
        }

    template = """
      <div class="cui-tree-grid" c-id="root_id" c-bind="attrs" c-data-density="density" c-data-selection="selection" c-data-disabled="True if disabled else None" c-aria-disabled="'true' if disabled else 'false'" data-citry-ui-part="tree-grid">
        <div c-if="has_toolbar" data-citry-ui-part="toolbar"><c-slot name="toolbar" /></div>
        <span role="status" aria-live="polite" aria-atomic="true" data-citry-ui-part="status"></span>
        <div data-citry-ui-part="viewport">
          <table c-bind="table_attrs" role="treegrid" c-aria-label="label" c-aria-disabled="'true' if disabled else 'false'" c-aria-rowcount="row_count + 1" c-aria-colcount="column_count" data-citry-ui-part="table">
            <c-if cond="has_caption"><caption data-citry-ui-part="caption"><c-slot name="caption" /></caption></c-if>
            <colgroup><c-for each="column in columns"><col c-style="{'width': f'{column.source.width}px'}" /></c-for></colgroup>
            <thead data-citry-ui-part="header"><tr aria-rowindex="1"><c-for each="column in columns"><th c-bind="column.header_attrs" c-aria-colindex="column.index + 1" c-data-column-key="column.source.key" c-data-column-index="column.index" c-data-align="column.source.align" tabindex="-1" data-citry-ui-part="header-cell"><c-slot name="header" c-column="column.source" c-column_index="column.index">{{ column.source.label }}</c-slot></th></c-for></tr></thead>
            <tbody data-citry-ui-part="body">
              <c-for each="row in rows"><tr #c-key="row.source.key" c-bind="row.attrs" c-hidden="not row.visible" c-inert="True if not row.visible else None" c-aria-rowindex="row.index + 2" c-aria-level="row.level" c-aria-posinset="row.position" c-aria-setsize="row.set_size" c-aria-expanded="('true' if row.expanded else 'false') if row.branch else None" c-aria-selected="('true' if row.selected else 'false') if selection != 'none' else None" c-aria-disabled="'true' if row.source.disabled else 'false'" c-data-row-key="row.source.key" c-data-label="row.source.label" c-data-parent-key="row.parent_key" c-data-level="row.level" c-data-expanded="True if row.expanded else None" c-data-selected="True if row.selected else None" c-data-disabled="True if row.source.disabled else None" data-citry-tree-grid-row data-citry-ui-part="row">
                <c-for each="cell in row.cells"><td c-bind="cell.attrs" c-aria-colindex="cell.index + 1" c-data-row-key="row.source.key" c-data-column-key="cell.column.key" c-data-column-index="cell.index" c-data-align="cell.column.align" c-tabindex="0 if row.index == 0 and cell.index == 0 and not disabled else -1" data-citry-ui-part="cell">
                  <div c-if="cell.index == 0" c-style="{'--cui-tree-grid-level': row.level}" data-citry-ui-part="hierarchy">
                    <button c-if="row.branch" type="button" tabindex="-1" c-disabled="disabled or row.source.disabled" c-aria-label="tr('citry-ui-tree-grid-collapse', row=row.source.label) if row.expanded and catalog['collapse'] else tr('citry-ui-tree-grid-expand', row=row.source.label) if catalog['expand'] else labels['collapse'].format(row=row.source.label) if row.expanded else labels['expand'].format(row=row.source.label)" data-citry-tree-grid-expander data-citry-ui-part="expander"><span aria-hidden="true">&#8250;</span></button>
                    <span c-if="not row.branch" aria-hidden="true" data-citry-ui-part="indent"></span>
                    <span data-citry-ui-part="cell-content"><c-slot name="cell" c-row="row.source" c-column="cell.column" c-cell="cell.source" c-row_index="row.index" c-column_index="cell.index" c-level="row.level" c-expanded="row.expanded" c-selected="row.selected">{{ cell.source.value }}</c-slot></span>
                  </div>
                  <span c-if="cell.index != 0" data-citry-ui-part="cell-content"><c-slot name="cell" c-row="row.source" c-column="cell.column" c-cell="cell.source" c-row_index="row.index" c-column_index="cell.index" c-level="row.level" c-expanded="row.expanded" c-selected="row.selected">{{ cell.source.value }}</c-slot></span>
                </td></c-for>
              </tr></c-for>
            </tbody>
          </table>
        </div>
        <span hidden data-citry-ui-part="inputs"><c-for each="key in selected"><input type="hidden" c-name="name" c-value="key" c-form="form" c-disabled="disabled or name is None" /></c-for></span>
      </div>
    """

    js_file = "runtime.min.js"
    css_file = "runtime.min.css"

    messages = """
      # @param {str} $row - Application-localized Row label.
      citry-ui-tree-grid-expand = Expand { $row }
      # @param {str} $row - Application-localized Row label.
      citry-ui-tree-grid-collapse = Collapse { $row }
      # @param {str} $row - Application-localized Row label.
      citry-ui-tree-grid-expanded = Expanded { $row }
      # @param {str} $row - Application-localized Row label.
      citry-ui-tree-grid-collapsed = Collapsed { $row }
      # @param {str} $row - Application-localized Row label.
      citry-ui-tree-grid-selected = Selected { $row }
      # @param {str} $row - Application-localized Row label.
      citry-ui-tree-grid-unselected = Unselected { $row }
    """


__all__ = [
    "CTreeGrid",
    "CTreeGridAlign",
    "CTreeGridCaptionSlotData",
    "CTreeGridCell",
    "CTreeGridCellActivateDetail",
    "CTreeGridCellSlotData",
    "CTreeGridColumn",
    "CTreeGridDensity",
    "CTreeGridExpandedChangeDetail",
    "CTreeGridHeaderSlotData",
    "CTreeGridRow",
    "CTreeGridSelection",
    "CTreeGridSelectionChangeDetail",
    "CTreeGridSource",
    "CTreeGridToolbarSlotData",
]
