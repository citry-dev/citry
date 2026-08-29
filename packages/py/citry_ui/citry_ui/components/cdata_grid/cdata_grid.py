"""Interactive, server-rendered Data Grid."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, TypedDict, cast

from citry import LibraryComponent, SlotInput, merge_attrs
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._i18n import uses_catalog_default
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CDataGridState = Literal["ready", "loading", "error"]
CDataGridDensity = Literal["comfortable", "compact", "spacious"]
CDataGridSelection = Literal["none", "single", "multiple"]
CDataGridAlign = Literal["start", "center", "end"]
CDataGridSortDirection = Literal["asc", "desc"]
CDataGridSortSource = Literal["pointer", "keyboard", "client"]
CDataGridSelectionSource = Literal["pointer", "keyboard", "client"]
CDataGridRangeReason = Literal["initial", "scroll", "resize", "configuration", "navigation"]
CDataGridEditor = Literal["text", "number", "checkbox", "select"]
CDataGridEditSource = Literal["pointer", "keyboard"]

_RUNTIME_PREFIXES = ("data-citry-", "data-cev", "data-cid")
_DIRECTIVES = frozenset(
    {"x-bind", "x-for", "x-html", "x-if", "x-ignore", "x-model", "x-modelable", "x-show", "x-teleport", "x-text"}
)
_ROOT_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-busy",
        "data-citry-data-grid-initialized",
        "data-citry-ui-part",
        "data-column-borders",
        "data-density",
        "data-disabled",
        "data-editable",
        "data-editing",
        "data-pending",
        "data-selection",
        "data-selecting",
        "data-state",
        "data-sticky-header",
        "data-striped",
        "hidden",
        "id",
        "inert",
        "role",
        "tabindex",
    }
)
_TABLE_OWNED = frozenset(
    {"aria-busy", "aria-colcount", "aria-disabled", "aria-label", "aria-rowcount", "data-citry-ui-part", "role"}
)
_CELL_OWNED = frozenset(
    {
        "aria-colindex",
        "aria-rowindex",
        "aria-sort",
        "data-align",
        "data-column-index",
        "data-citry-ui-part",
        "data-column-key",
        "data-row-index",
        "data-row-key",
        "data-sort",
        "data-sort-priority",
        "data-sortable",
        "data-editable",
        "data-editing",
        "data-editor",
        "id",
        "role",
        "tabindex",
    }
)
_ROW_OWNED = frozenset(
    {
        "aria-disabled",
        "aria-rowindex",
        "aria-selected",
        "data-citry-key",
        "data-citry-ui-part",
        "data-disabled",
        "data-row-index",
        "data-row-key",
        "data-selected",
        "id",
        "role",
    }
)
_MAX_EXTENT = 16_000_000
_EDITOR_ATTRS = {
    "text": frozenset({"autocomplete", "inputmode", "maxlength", "minlength", "pattern", "placeholder", "required"}),
    "number": frozenset({"max", "min", "placeholder", "required", "step"}),
    "checkbox": frozenset(),
    "select": frozenset({"required"}),
}


@dataclass(frozen=True, slots=True)
class CDataGridColumn:
    key: str
    label: str
    sortable: bool = False
    width: int = 160
    align: CDataGridAlign = "start"
    header_attrs: Mapping[str, object] | None = None
    cell_attrs: Mapping[str, object] | None = None
    editable: bool = False
    editor: CDataGridEditor = "text"
    editor_options: Sequence[CDataGridEditOption] = ()
    editor_attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CDataGridCell:
    value: object
    attrs: Mapping[str, object] | None = None
    editable: bool | None = None


@dataclass(frozen=True, slots=True)
class CDataGridEditOption:
    value: str
    label: str
    disabled: bool = False


@dataclass(frozen=True, slots=True)
class CDataGridRow:
    key: str
    cells: Mapping[str, object | CDataGridCell]
    disabled: bool = False
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CDataGridSort:
    key: str
    direction: CDataGridSortDirection


@dataclass(frozen=True, slots=True)
class _ResolvedColumn:
    column: CDataGridColumn
    index: int
    header_attrs: Mapping[str, object]
    cell_attrs: Mapping[str, object]
    sort_direction: CDataGridSortDirection | None
    sort_priority: int | None
    editor_options: tuple[CDataGridEditOption, ...]
    editor_attrs: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _ResolvedCell:
    cell: CDataGridCell
    column: CDataGridColumn
    column_index: int
    attrs: Mapping[str, object]
    editable: bool
    edit_value: str | float | bool | None


@dataclass(frozen=True, slots=True)
class _ResolvedRow:
    row: CDataGridRow
    cells: tuple[_ResolvedCell, ...]
    supplied_index: int
    logical_index: int
    attrs: Mapping[str, object]
    selected: bool


class CDataGridCaptionSlotData:
    pass


class CDataGridToolbarSlotData:
    pass


class CDataGridHeaderSlotData(TypedDict):
    column: CDataGridColumn
    column_index: int
    sort_direction: CDataGridSortDirection | None
    sort_priority: int | None


class CDataGridCellSlotData(TypedDict):
    row: CDataGridRow
    column: CDataGridColumn
    cell: CDataGridCell
    row_index: int
    column_index: int
    selected: bool


class CDataGridLoadingSlotData:
    pass


class CDataGridEmptySlotData:
    pass


class CDataGridErrorSlotData:
    pass


class CDataGridSortChangeDetail(TypedDict):
    sort: list[dict[str, str]]
    previousSort: list[dict[str, str]]
    columnKey: str
    direction: CDataGridSortDirection | None
    source: CDataGridSortSource
    sourceEvent: object | None


class CDataGridSelectionChangeDetail(TypedDict):
    selected: list[str]
    previousSelected: list[str]
    changed: list[str]
    rowKey: str | None
    selectedRow: bool | None
    controlled: bool
    source: CDataGridSelectionSource
    sourceEvent: object | None


class CDataGridRangeChangeDetail(TypedDict):
    startIndex: int
    endIndex: int
    visibleStartIndex: int
    visibleEndIndex: int
    requestId: int
    reason: CDataGridRangeReason
    sourceEvent: object | None


class CDataGridCellActivateDetail(TypedDict):
    rowKey: str
    columnKey: str
    rowIndex: int
    columnIndex: int
    source: Literal["keyboard", "pointer"]
    sourceEvent: object


class CDataGridCellEditDetail(TypedDict):
    rowKey: str
    columnKey: str
    rowIndex: int
    columnIndex: int
    editor: CDataGridEditor
    previousValue: str | float | bool
    source: CDataGridEditSource
    reason: str
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
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{name} must be a sequence, got {value!r}.")
    return tuple(value)


def _positive_int(name: str, value: object, *, zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < (0 if zero else 1):
        relation = "nonnegative" if zero else "positive"
        raise ValueError(f"{name} must be a {relation} integer, got {value!r}.")
    return value


def _editor_attrs(column: CDataGridColumn) -> dict[str, str | int | float | bool]:
    value = column.editor_attrs
    if value is not None and not isinstance(value, Mapping):
        raise TypeError(f"CDataGrid column {column.key!r} editor_attrs must be a mapping or None, got {value!r}.")
    copied: dict[str, str | int | float | bool] = {}
    allowed = _EDITOR_ATTRS[column.editor]
    for key, raw in dict(value or {}).items():
        if not isinstance(key, str) or key.casefold() not in allowed:
            raise ValueError(
                f"CDataGrid column {column.key!r} editor_attrs cannot contain {key!r} for editor={column.editor!r}."
            )
        if not isinstance(raw, (str, int, float, bool)):
            raise TypeError(
                f"CDataGrid column {column.key!r} editor_attrs[{key!r}] must be a string, number, or bool."
            )
        if isinstance(raw, float) and not math.isfinite(raw):
            raise ValueError(f"CDataGrid column {column.key!r} editor_attrs[{key!r}] must be finite.")
        copied[key.casefold()] = raw
    return copied


def _editor_options(column: CDataGridColumn) -> tuple[CDataGridEditOption, ...]:
    values = _sequence(f"CDataGrid column {column.key!r} editor_options", column.editor_options)
    if column.editor != "select" and values:
        raise ValueError(f"CDataGrid column {column.key!r} editor_options require editor='select'.")
    if column.editor == "select" and not values:
        raise ValueError(f"CDataGrid select column {column.key!r} requires editor_options.")
    result: list[CDataGridEditOption] = []
    seen: set[str] = set()
    for index, raw in enumerate(values):
        if not isinstance(raw, CDataGridEditOption):
            raise TypeError(
                f"CDataGrid column {column.key!r} editor_options[{index}] must be CDataGridEditOption, got {raw!r}."
            )
        validate_non_empty_string("CDataGridEditOption", "value", raw.value)
        validate_non_empty_string("CDataGridEditOption", "label", raw.label)
        validate_boolean("CDataGridEditOption", "disabled", raw.disabled)
        if raw.value in seen:
            raise ValueError(f"CDataGrid column {column.key!r} editor option {raw.value!r} is duplicated.")
        seen.add(raw.value)
        result.append(raw)
    return tuple(result)


def _edit_value(column: CDataGridColumn, cell: CDataGridCell, *, editable: bool) -> str | float | bool | None:
    if not editable:
        return None
    value = cell.value
    if column.editor in {"text", "select"}:
        if not isinstance(value, str):
            raise TypeError(
                f"Editable {column.editor} cell in column {column.key!r} must contain a string, got {value!r}."
            )
        if column.editor == "select" and value not in {option.value for option in column.editor_options}:
            raise ValueError(
                f"Editable select cell in column {column.key!r} has value {value!r}, which is not an editor option."
            )
        return value
    if column.editor == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                f"Editable number cell in column {column.key!r} must contain an int or float, got {value!r}."
            )
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f"Editable number cell in column {column.key!r} must contain a finite value.")
        return result
    if not isinstance(value, bool):
        raise TypeError(f"Editable checkbox cell in column {column.key!r} must contain a bool, got {value!r}.")
    return value


class CDataGrid(LibraryComponent):
    class I18n:
        messages_locale = "en-US"

    @dataclass(slots=True)
    class Kwargs:
        columns: Sequence[CDataGridColumn]
        rows: Sequence[CDataGridRow]
        label: str
        id: str | None = None
        state: CDataGridState = "ready"
        sort: Sequence[CDataGridSort] = ()
        multi_sort: bool = True
        selection: CDataGridSelection = "none"
        selected: Sequence[str] = ()
        disabled: bool = False
        total_count: int | None = None
        start_index: int = 0
        row_height: int = 48
        viewport_size: int = 400
        overscan: int = 3
        initial_index: int = 0
        density: CDataGridDensity = "comfortable"
        striped: bool = False
        column_borders: bool = False
        sticky_header: bool = True
        loading_label: str = "Loading data..."
        empty_label: str = "No data."
        error_label: str = "Unable to load data."
        sort_ascending_label: str = "{column} sorted ascending"
        sort_descending_label: str = "{column} sorted descending"
        sort_cleared_label: str = "Sort cleared for {column}"
        selected_one_label: str = "One row selected"
        selected_label: str = "{count} rows selected"
        edit_label: str = "Edit {column}"
        editing_label: str = "Editing {column}"
        edit_submitted_label: str = "Changes submitted for {column}"
        edit_cancelled_label: str = "Changes cancelled for {column}"
        edit_invalid_label: str = "Enter a valid value for {column}"
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        table_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        caption: SlotInput[CDataGridCaptionSlotData] | None = None
        toolbar: SlotInput[CDataGridToolbarSlotData] | None = None
        header: SlotInput[CDataGridHeaderSlotData] | None = None
        cell: SlotInput[CDataGridCellSlotData] | None = None
        loading: SlotInput[CDataGridLoadingSlotData] | None = None
        empty: SlotInput[CDataGridEmptySlotData] | None = None
        error: SlotInput[CDataGridErrorSlotData] | None = None

    @classmethod
    def _columns(
        cls, value: Sequence[CDataGridColumn], sort: tuple[CDataGridSort, ...]
    ) -> tuple[_ResolvedColumn, ...]:
        columns = _sequence("CDataGrid columns", value)
        if not columns:
            raise ValueError("CDataGrid requires at least one column.")
        sort_positions = {item.key: (item.direction, index + 1) for index, item in enumerate(sort)}
        seen: set[str] = set()
        resolved: list[_ResolvedColumn] = []
        for index, raw in enumerate(columns):
            if not isinstance(raw, CDataGridColumn):
                raise TypeError(f"CDataGrid columns[{index}] must be CDataGridColumn, got {raw!r}.")
            validate_non_empty_string("CDataGridColumn", "key", raw.key)
            validate_non_empty_string("CDataGridColumn", "label", raw.label)
            validate_boolean("CDataGridColumn", "sortable", raw.sortable)
            validate_boolean("CDataGridColumn", "editable", raw.editable)
            validate_choice("CDataGridColumn", "align", raw.align, ("start", "center", "end"))
            validate_choice("CDataGridColumn", "editor", raw.editor, ("text", "number", "checkbox", "select"))
            width = _positive_int(f"CDataGrid column {raw.key!r} width", raw.width)
            if not 40 <= width <= 2_000:
                raise ValueError(f"CDataGrid column {raw.key!r} width must be from 40 through 2000 pixels.")
            if raw.key in seen:
                raise ValueError(f"CDataGrid column keys must be unique; {raw.key!r} occurs more than once.")
            seen.add(raw.key)
            direction, priority = sort_positions.get(raw.key, (None, None))
            resolved.append(
                _ResolvedColumn(
                    column=raw,
                    index=index,
                    header_attrs=_attrs(f"CDataGrid column {raw.key!r} header_attrs", raw.header_attrs, _CELL_OWNED),
                    cell_attrs=_attrs(f"CDataGrid column {raw.key!r} cell_attrs", raw.cell_attrs, _CELL_OWNED),
                    sort_direction=direction,
                    sort_priority=priority,
                    editor_options=_editor_options(raw),
                    editor_attrs=_editor_attrs(raw),
                )
            )
        return tuple(resolved)

    @staticmethod
    def _sort(value: Sequence[CDataGridSort]) -> tuple[CDataGridSort, ...]:
        values = _sequence("CDataGrid sort", value)
        result: list[CDataGridSort] = []
        seen: set[str] = set()
        for index, raw in enumerate(values):
            if not isinstance(raw, CDataGridSort):
                raise TypeError(f"CDataGrid sort[{index}] must be CDataGridSort, got {raw!r}.")
            validate_non_empty_string("CDataGridSort", "key", raw.key)
            validate_choice("CDataGridSort", "direction", raw.direction, ("asc", "desc"))
            if raw.key in seen:
                raise ValueError(f"CDataGrid sort keys must be unique; {raw.key!r} occurs more than once.")
            seen.add(raw.key)
            result.append(raw)
        return tuple(result)

    @classmethod
    def _rows(
        cls,
        value: Sequence[CDataGridRow],
        columns: tuple[_ResolvedColumn, ...],
        start_index: int,
        selected: frozenset[str],
    ) -> tuple[_ResolvedRow, ...]:
        rows = _sequence("CDataGrid rows", value)
        keys = {resolved.column.key for resolved in columns}
        seen: set[str] = set()
        result: list[_ResolvedRow] = []
        for supplied_index, raw in enumerate(rows):
            if not isinstance(raw, CDataGridRow):
                raise TypeError(f"CDataGrid rows[{supplied_index}] must be CDataGridRow, got {raw!r}.")
            validate_non_empty_string("CDataGridRow", "key", raw.key)
            validate_boolean("CDataGridRow", "disabled", raw.disabled)
            if raw.key in seen:
                raise ValueError(f"CDataGrid row keys must be unique; {raw.key!r} occurs more than once.")
            seen.add(raw.key)
            if not isinstance(raw.cells, Mapping):
                raise TypeError(f"CDataGrid row {raw.key!r} cells must be a mapping, got {raw.cells!r}.")
            if any(not isinstance(key, str) for key in raw.cells):
                raise TypeError(f"CDataGrid row {raw.key!r} cells must use string column keys.")
            if set(raw.cells) != keys:
                missing = sorted(keys - set(raw.cells))
                extra = sorted(set(raw.cells) - keys)
                raise ValueError(
                    f"CDataGrid row {raw.key!r} cells do not match columns; missing={missing!r}, extra={extra!r}."
                )
            row_attrs = _attrs(f"CDataGrid row {raw.key!r} attrs", raw.attrs, _ROW_OWNED)
            cells: list[_ResolvedCell] = []
            for column in columns:
                raw_cell = raw.cells[column.column.key]
                cell = raw_cell if isinstance(raw_cell, CDataGridCell) else CDataGridCell(raw_cell)
                if cell.editable is not None:
                    validate_boolean(
                        f"CDataGrid row {raw.key!r}, column {column.column.key!r}", "editable", cell.editable
                    )
                editable = column.column.editable if cell.editable is None else cell.editable
                cell_attrs = _attrs(
                    f"CDataGrid row {raw.key!r}, column {column.column.key!r} attrs", cell.attrs, _CELL_OWNED
                )
                cells.append(
                    _ResolvedCell(
                        cell=cell,
                        column=column.column,
                        column_index=column.index,
                        attrs=merge_attrs(column.cell_attrs, cell_attrs),
                        editable=editable,
                        edit_value=_edit_value(column.column, cell, editable=editable),
                    )
                )
            result.append(
                _ResolvedRow(
                    row=raw,
                    cells=tuple(cells),
                    supplied_index=supplied_index,
                    logical_index=start_index + supplied_index,
                    attrs=row_attrs,
                    selected=raw.key in selected,
                )
            )
        return tuple(result)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        validate_html_id("CDataGrid", kwargs.id)
        validate_non_empty_string("CDataGrid", "label", kwargs.label)
        validate_choice("CDataGrid", "state", kwargs.state, ("ready", "loading", "error"))
        validate_choice("CDataGrid", "selection", kwargs.selection, ("none", "single", "multiple"))
        validate_choice("CDataGrid", "density", kwargs.density, ("comfortable", "compact", "spacious"))
        for name in ("multi_sort", "disabled", "striped", "column_borders", "sticky_header"):
            validate_boolean("CDataGrid", name, getattr(kwargs, name))
        start_index = _positive_int("CDataGrid start_index", kwargs.start_index, zero=True)
        row_height = _positive_int("CDataGrid row_height", kwargs.row_height)
        viewport_size = _positive_int("CDataGrid viewport_size", kwargs.viewport_size)
        overscan = _positive_int("CDataGrid overscan", kwargs.overscan, zero=True)
        if overscan > 100:
            raise ValueError("CDataGrid overscan must be from 0 through 100.")
        initial_index = _positive_int("CDataGrid initial_index", kwargs.initial_index, zero=True)
        sort = self._sort(kwargs.sort)
        selected_values = cast("tuple[str, ...]", _sequence("CDataGrid selected", kwargs.selected))
        if any(not isinstance(item, str) or not item for item in selected_values):
            raise TypeError("CDataGrid selected must contain nonempty strings.")
        if len(selected_values) != len(set(selected_values)):
            raise ValueError("CDataGrid selected must not contain duplicate row keys.")
        if kwargs.selection == "none" and selected_values:
            raise ValueError("CDataGrid selected must be empty when selection='none'.")
        if kwargs.selection == "single" and len(selected_values) > 1:
            raise ValueError("CDataGrid selection='single' accepts at most one selected row key.")
        columns = self._columns(kwargs.columns, sort)
        known_columns = {item.column.key: item.column for item in columns}
        for item in sort:
            column = known_columns.get(item.key)
            if column is None:
                raise ValueError(f"CDataGrid sort references unknown column {item.key!r}.")
            if not column.sortable:
                raise ValueError(f"CDataGrid sort references non-sortable column {item.key!r}.")
        rows = self._rows(kwargs.rows, columns, start_index, frozenset(selected_values))
        known_rows = {item.row.key for item in rows}
        unknown_selected = [item for item in selected_values if item not in known_rows]
        if unknown_selected:
            raise ValueError(f"CDataGrid selected contains unknown supplied row keys: {unknown_selected!r}.")
        total_count = (
            len(rows)
            if kwargs.total_count is None
            else _positive_int("CDataGrid total_count", kwargs.total_count, zero=True)
        )
        if kwargs.total_count is None and start_index != 0:
            raise ValueError("CDataGrid start_index must be 0 when total_count is omitted.")
        if start_index + len(rows) > total_count:
            raise ValueError("CDataGrid supplied row range exceeds total_count.")
        if total_count * row_height > _MAX_EXTENT:
            raise ValueError(f"CDataGrid total row extent cannot exceed {_MAX_EXTENT} CSS pixels.")
        initial_index = min(initial_index, max(0, total_count - 1))
        catalog = {
            name: uses_catalog_default(self, f"{name}_label")
            for name in (
                "loading",
                "empty",
                "error",
                "sort_ascending",
                "sort_descending",
                "sort_cleared",
                "selected_one",
                "selected",
                "edit",
                "editing",
                "edit_submitted",
                "edit_cancelled",
                "edit_invalid",
            )
        }
        labels = {
            "loading": self.i18n.tr("citry-ui-data-grid-loading") if catalog["loading"] else kwargs.loading_label,
            "empty": self.i18n.tr("citry-ui-data-grid-empty") if catalog["empty"] else kwargs.empty_label,
            "error": self.i18n.tr("citry-ui-data-grid-error") if catalog["error"] else kwargs.error_label,
            "sort_ascending": kwargs.sort_ascending_label,
            "sort_descending": kwargs.sort_descending_label,
            "sort_cleared": kwargs.sort_cleared_label,
            "selected_one": kwargs.selected_one_label,
            "selected": kwargs.selected_label,
            "edit": kwargs.edit_label,
            "editing": kwargs.editing_label,
            "edit_submitted": kwargs.edit_submitted_label,
            "edit_cancelled": kwargs.edit_cancelled_label,
            "edit_invalid": kwargs.edit_invalid_label,
        }
        for name, value in labels.items():
            validate_non_empty_string("CDataGrid", f"{name}_label", value)
        for name in (
            "sort_ascending",
            "sort_descending",
            "sort_cleared",
            "edit",
            "editing",
            "edit_submitted",
            "edit_cancelled",
            "edit_invalid",
        ):
            if not catalog[name] and "{column}" not in labels[name]:
                raise ValueError(f"CDataGrid {name}_label must contain {{column}}.")
        if not catalog["selected"] and "{count}" not in labels["selected"]:
            raise ValueError("CDataGrid selected_label must contain {count}.")
        editors = [
            {
                "rowKey": row.row.key,
                "columnKey": cell.column.key,
                "rowIndex": row.logical_index,
                "columnIndex": cell.column_index,
                "editor": cell.column.editor,
                "value": cell.edit_value,
                "columnLabel": cell.column.label,
                "options": [
                    {"value": option.value, "label": option.label, "disabled": option.disabled}
                    for option in next(item for item in columns if item.column.key == cell.column.key).editor_options
                ],
                "attrs": dict(next(item for item in columns if item.column.key == cell.column.key).editor_attrs),
            }
            for row in rows
            for cell in row.cells
            if cell.editable
        ]
        root_id = kwargs.id or f"cui-data-grid-{self.id}"
        root_attrs = merge_attrs(
            _attrs("CDataGrid attrs", kwargs.attrs, _ROOT_OWNED, kwargs.class_, kwargs.style),
            {
                "style": {
                    "--cui-data-grid-viewport-size": f"{viewport_size}px",
                    "--cui-data-grid-row-height": f"{row_height}px",
                    "--cui-data-grid-min-width": f"{sum(item.column.width for item in columns)}px",
                }
            },
        )
        table_attrs = _attrs("CDataGrid table_attrs", kwargs.table_attrs, _TABLE_OWNED)
        before_size = start_index * row_height
        after_size = max(0, total_count - start_index - len(rows)) * row_height
        state_output: CDataGridState | Literal["empty"] = kwargs.state
        if kwargs.state == "ready" and total_count == 0:
            state_output = "empty"
        return {
            "root_id": root_id,
            "columns": columns,
            "column_labels": {item.column.key: item.column.label for item in columns},
            "rows": rows,
            "label": kwargs.label,
            "state": kwargs.state,
            "state_output": state_output,
            "sort": [{"key": item.key, "direction": item.direction} for item in sort],
            "selection": kwargs.selection,
            "selected": selected_values,
            "disabled": kwargs.disabled,
            "multi_sort": kwargs.multi_sort,
            "total_count": total_count,
            "start_index": start_index,
            "row_height": row_height,
            "viewport_size": viewport_size,
            "overscan": overscan,
            "initial_index": initial_index,
            "density": kwargs.density,
            "striped": kwargs.striped,
            "column_borders": kwargs.column_borders,
            "sticky_header": kwargs.sticky_header,
            "column_count": len(columns),
            "before_size": before_size,
            "after_size": after_size,
            "has_before": before_size > 0 and kwargs.state == "ready",
            "has_after": after_size > 0 and kwargs.state == "ready",
            "is_ready": kwargs.state == "ready" and total_count > 0,
            "has_editable": bool(editors),
            "editors": editors,
            "lc": catalog["loading"],
            "ll": labels["loading"],
            "lb": {"$c-tr:citry-ui-data-grid-loading": True if catalog["loading"] else None},
            "ec": catalog["empty"],
            "el": labels["empty"],
            "eb": {"$c-tr:citry-ui-data-grid-empty": True if catalog["empty"] else None},
            "xc": catalog["error"],
            "xl": labels["error"],
            "xb": {"$c-tr:citry-ui-data-grid-error": True if catalog["error"] else None},
            "labels": labels,
            "catalog": catalog,
            "attrs": root_attrs,
            "table_attrs": table_attrs,
            "has_caption": "caption" in self.raw_slots,
            "has_toolbar": "toolbar" in self.raw_slots,
        }

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
        data = self.template_data(kwargs, slots)
        return {
            key: data[key]
            for key in (
                "sort",
                "selection",
                "selected",
                "disabled",
                "multi_sort",
                "total_count",
                "start_index",
                "row_height",
                "viewport_size",
                "overscan",
                "initial_index",
                "is_ready",
                "column_labels",
                "labels",
                "catalog",
                "editors",
            )
        }

    template = """
      <div
        class="cui-data-grid"
        c-bind="attrs"
        c-id="root_id"
        c-data-state="state_output"
        c-data-density="density"
        c-data-striped="True if striped else None"
        c-data-column-borders="True if column_borders else None"
        c-data-sticky-header="True if sticky_header else None"
        c-data-selection="selection"
        c-data-editable="True if has_editable else None"
        c-data-disabled="True if disabled else None"
        c-aria-disabled="'true' if disabled else 'false'"
        data-citry-ui-part="data-grid"
      >
        <div c-if="has_toolbar" data-citry-ui-part="toolbar"><c-slot name="toolbar" /></div>
        <span
          role="status"
          aria-live="polite"
          aria-atomic="true"
          data-citry-ui-part="status"
        ></span>
        <div c-tabindex="-1 if is_ready else 0" data-citry-ui-part="viewport">
          <table
            c-bind="table_attrs"
            c-aria-label="label"
            c-aria-busy="'true' if state == 'loading' else None"
            c-aria-disabled="'true' if disabled or not is_ready else 'false'"
            c-aria-rowcount="total_count + 1"
            c-aria-colcount="column_count"
            role="grid"
            data-citry-ui-part="table"
          >
            <c-if cond="has_caption"><caption data-citry-ui-part="caption"><c-slot name="caption" /></caption></c-if>
            <colgroup>
              <c-for each="resolved in columns">
                <col c-style="{'width': f'{resolved.column.width}px'}" />
              </c-for>
            </colgroup>
            <thead data-citry-ui-part="header">
              <tr aria-rowindex="1" data-citry-ui-part="header-row">
                <c-for each="resolved in columns">
                  <th
                    c-bind="resolved.header_attrs"
                    c-id="f'{root_id}-header-{resolved.index}'"
                    c-data-column-key="resolved.column.key"
                    c-data-column-index="resolved.index"
                    c-data-align="resolved.column.align"
                    c-data-sortable="True if resolved.column.sortable else None"
                    c-data-sort="resolved.sort_direction"
                    c-data-sort-priority="resolved.sort_priority"
                    c-aria-sort="(
                      'ascending' if resolved.sort_direction == 'asc'
                      else 'descending' if resolved.sort_direction == 'desc'
                      else None
                    )"
                    c-aria-colindex="resolved.index + 1"
                    tabindex="-1"
                    data-citry-ui-part="header-cell"
                  >
                    <c-slot
                      name="header"
                      c-column="resolved.column"
                      c-column_index="resolved.index"
                      c-sort_direction="resolved.sort_direction"
                      c-sort_priority="resolved.sort_priority"
                    >{{ resolved.column.label }}</c-slot>
                    <span aria-hidden="true" data-citry-ui-part="sort-indicator">{{
                      '↑' if resolved.sort_direction == 'asc' else '↓' if resolved.sort_direction == 'desc' else ''
                    }}</span>
                  </th>
                </c-for>
              </tr>
            </thead>
            <tbody data-citry-ui-part="body">
              <c-if cond="state == 'ready'">
                <tr c-if="has_before" aria-hidden="true" data-citry-ui-part="spacer-row">
                  <td c-colspan="column_count" c-style="{'height': f'{before_size}px'}"></td>
                </tr>
                <c-for each="resolved_row in rows">
                  <tr
                    #c-key="resolved_row.row.key"
                    c-bind="resolved_row.attrs"
                    c-id="f'{root_id}-row-{resolved_row.supplied_index}'"
                    c-data-row-key="resolved_row.row.key"
                    c-data-row-index="resolved_row.logical_index"
                    c-data-disabled="True if resolved_row.row.disabled else None"
                    c-data-selected="True if resolved_row.selected else None"
                    c-aria-disabled="'true' if resolved_row.row.disabled else None"
                    c-aria-selected="(
                      'true' if resolved_row.selected else 'false'
                    ) if selection != 'none' else None"
                    c-aria-rowindex="resolved_row.logical_index + 2"
                    data-citry-ui-part="row"
                  >
                    <c-for each="resolved_cell in resolved_row.cells">
                      <td
                        c-bind="resolved_cell.attrs"
                        c-id="f'{root_id}-cell-{resolved_row.supplied_index}-{resolved_cell.column_index}'"
                        c-data-row-key="resolved_row.row.key"
                        c-data-row-index="resolved_row.logical_index"
                        c-data-column-key="resolved_cell.column.key"
                        c-data-column-index="resolved_cell.column_index"
                        c-data-align="resolved_cell.column.align"
                        c-data-editable="True if resolved_cell.editable else None"
                        c-data-editor="resolved_cell.column.editor if resolved_cell.editable else None"
                        c-aria-colindex="resolved_cell.column_index + 1"
                        c-tabindex="0 if resolved_row.supplied_index == 0 and resolved_cell.column_index == 0 else -1"
                        data-citry-ui-part="cell"
                      >
                        <c-slot
                          name="cell"
                          c-row="resolved_row.row"
                          c-column="resolved_cell.column"
                          c-cell="resolved_cell.cell"
                          c-row_index="resolved_row.logical_index"
                          c-column_index="resolved_cell.column_index"
                          c-selected="resolved_row.selected"
                        >{{ resolved_cell.cell.value }}</c-slot>
                      </td>
                    </c-for>
                  </tr>
                </c-for>
                <tr c-if="has_after" aria-hidden="true" data-citry-ui-part="spacer-row">
                  <td c-colspan="column_count" c-style="{'height': f'{after_size}px'}"></td>
                </tr>
                <tr c-if="state_output == 'empty'" aria-rowindex="2" data-citry-ui-part="state-row">
                  <td c-colspan="column_count" data-citry-ui-part="empty">
                    <c-slot name="empty">
                      <div role="status" aria-live="polite">
                        <span c-bind="eb">{{ tr('citry-ui-data-grid-empty') if ec else el }}</span>
                      </div>
                    </c-slot>
                  </td>
                </tr>
              </c-if>
              <tr c-if="state == 'loading'" aria-rowindex="2" data-citry-ui-part="state-row">
                <td c-colspan="column_count" data-citry-ui-part="loading">
                  <c-slot name="loading">
                    <div role="status" aria-live="polite">
                      <span c-bind="lb">{{ tr('citry-ui-data-grid-loading') if lc else ll }}</span>
                    </div>
                  </c-slot>
                </td>
              </tr>
              <tr c-if="state == 'error'" aria-rowindex="2" data-citry-ui-part="state-row">
                <td c-colspan="column_count" data-citry-ui-part="error">
                  <c-slot name="error">
                    <div role="status" aria-live="polite">
                      <span c-bind="xb">{{ tr('citry-ui-data-grid-error') if xc else xl }}</span>
                    </div>
                  </c-slot>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    """

    js_file = "runtime.min.js"

    css_file = "runtime.min.css"

    messages = """
      citry-ui-data-grid-loading = Loading data...
      citry-ui-data-grid-empty = No data.
      citry-ui-data-grid-error = Unable to load data.
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-sort-ascending = { $column } sorted ascending
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-sort-descending = { $column } sorted descending
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-sort-cleared = Sort cleared for { $column }
      citry-ui-data-grid-selected-one = One row selected
      # @param {str} $count - Locale-formatted selected supplied-row count.
      citry-ui-data-grid-selected = { $count } rows selected
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-edit = Edit { $column }
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-editing = Editing { $column }
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-edit-submitted = Changes submitted for { $column }
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-edit-cancelled = Changes cancelled for { $column }
      # @param {str} $column - Application-localized column label.
      citry-ui-data-grid-edit-invalid = Enter a valid value for { $column }
    """


__all__ = [
    "CDataGrid",
    "CDataGridAlign",
    "CDataGridCaptionSlotData",
    "CDataGridCell",
    "CDataGridCellActivateDetail",
    "CDataGridCellEditDetail",
    "CDataGridCellSlotData",
    "CDataGridColumn",
    "CDataGridDensity",
    "CDataGridEditOption",
    "CDataGridEditSource",
    "CDataGridEditor",
    "CDataGridEmptySlotData",
    "CDataGridErrorSlotData",
    "CDataGridHeaderSlotData",
    "CDataGridLoadingSlotData",
    "CDataGridRangeChangeDetail",
    "CDataGridRangeReason",
    "CDataGridRow",
    "CDataGridSelection",
    "CDataGridSelectionChangeDetail",
    "CDataGridSelectionSource",
    "CDataGridSort",
    "CDataGridSortChangeDetail",
    "CDataGridSortDirection",
    "CDataGridSortSource",
    "CDataGridState",
    "CDataGridToolbarSlotData",
]
