"""Styled and headless semantic Table component definitions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence  # noqa: TC003
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput

CTableState = Literal["ready", "loading", "error"]
CTableDensity = Literal["comfortable", "compact"]


@dataclass(frozen=True, slots=True)
class CTableColumn:
    """One semantic Table column."""

    key: str
    label: str
    row_header: bool = False
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTableCell:
    """One Table cell with optional span and native attributes."""

    value: object
    colspan: int = 1
    rowspan: int = 1
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTableRow:
    """One keyed Table row whose cells are addressed by column key."""

    key: str
    cells: Mapping[str, object | CTableCell]
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTableResolvedColumn:
    """A validated column paired with its stable index."""

    column: CTableColumn
    column_index: int


@dataclass(frozen=True, slots=True)
class CTableResolvedCell:
    """A validated cell paired with its column and stable index."""

    column: CTableColumn
    cell: CTableCell
    column_index: int


@dataclass(frozen=True, slots=True)
class CTableResolvedRow:
    """A validated row with cells in declared column order."""

    row: CTableRow
    cells: tuple[CTableResolvedCell, ...]
    row_index: int


class CTableHeadlessDefaultSlotData:
    columns: tuple[CTableResolvedColumn, ...]
    rows: tuple[CTableResolvedRow, ...]
    state: CTableState
    root_attrs: dict[str, object]
    table_attrs: dict[str, object]
    column_count: int
    is_empty: bool


def _validate_part_attrs(
    attrs: Mapping[str, object] | None,
    *,
    location: str,
    reserved: frozenset[str],
) -> None:
    for key in attrs or {}:
        if not isinstance(key, str):
            msg = f"{location} attributes require string keys, got {key!r}."
            raise TypeError(msg)
        if key.lower() in reserved:
            msg = f"{location} attributes cannot override semantic attribute {key!r}."
            raise ValueError(msg)


def _normalize_table(kwargs: CTableHeadless.Kwargs) -> dict[str, object]:
    columns = tuple(kwargs.columns)
    rows = tuple(kwargs.rows)
    if kwargs.state not in {"ready", "loading", "error"}:
        msg = f"Table state must be 'ready', 'loading', or 'error', got {kwargs.state!r}."
        raise ValueError(msg)
    if not columns:
        msg = "Table requires at least one column."
        raise ValueError(msg)

    column_keys = [column.key for column in columns]
    if any(not key for key in column_keys) or len(set(column_keys)) != len(column_keys):
        msg = "Table column keys must be non-empty and unique."
        raise ValueError(msg)
    for column in columns:
        _validate_part_attrs(
            column.attrs,
            location=f"Table column {column.key!r}",
            reserved=frozenset({"colspan", "role", "rowspan", "scope"}),
        )

    row_keys = [row.key for row in rows]
    if any(not key for key in row_keys) or len(set(row_keys)) != len(row_keys):
        msg = "Table row keys must be non-empty and unique."
        raise ValueError(msg)

    expected_keys = set(column_keys)
    resolved_rows: list[CTableResolvedRow] = []
    for row_index, row in enumerate(rows):
        _validate_part_attrs(
            row.attrs,
            location=f"Table row {row.key!r}",
            reserved=frozenset({"data-row-key"}),
        )
        actual_keys = set(row.cells)
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            msg = f"Table row {row.key!r} cells do not match columns; missing={missing!r}, extra={extra!r}."
            raise ValueError(msg)
        resolved_cells: list[CTableResolvedCell] = []
        for column_index, column in enumerate(columns):
            raw_cell = row.cells[column.key]
            cell = raw_cell if isinstance(raw_cell, CTableCell) else CTableCell(raw_cell)
            if cell.colspan != 1 or cell.rowspan != 1:
                msg = (
                    f"Table row {row.key!r}, column {column.key!r} uses a cell span. "
                    "The semantic Table pressure component does not support spans yet."
                )
                raise ValueError(msg)
            _validate_part_attrs(
                cell.attrs,
                location=f"Table row {row.key!r}, column {column.key!r}",
                reserved=frozenset({"colspan", "role", "rowspan", "scope"}),
            )
            resolved_cells.append(CTableResolvedCell(column=column, cell=cell, column_index=column_index))
        resolved_rows.append(CTableResolvedRow(row=row, cells=tuple(resolved_cells), row_index=row_index))

    return {
        "columns": tuple(
            CTableResolvedColumn(column=column, column_index=index) for index, column in enumerate(columns)
        ),
        "rows": tuple(resolved_rows),
        "state": kwargs.state,
        "root_attrs": {
            **dict(kwargs.attrs or {}),
            "data-state": kwargs.state,
            "aria-busy": "true" if kwargs.state == "loading" else None,
        },
        "table_attrs": dict(kwargs.table_attrs or {}),
        "column_count": len(columns),
        "is_empty": kwargs.state == "ready" and not rows,
    }


class CTableHeadless(LibraryComponent):
    transparent = True

    @dataclass(slots=True)
    class Kwargs:
        columns: Sequence[CTableColumn]
        rows: Sequence[CTableRow]
        state: CTableState = "ready"
        attrs: Mapping[str, object] | None = None
        table_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        default: SlotInput[CTableHeadlessDefaultSlotData]

    def template_data(
        self,
        kwargs: CTableHeadless.Kwargs,
        slots: CTableHeadless.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        return {"slot_data": _normalize_table(kwargs)}

    template = """
      <c-slot
        name="default"
        required
        c-bind="slot_data"
      />
    """


class CTableCaptionSlotData:
    pass


class CTableHeaderSlotData:
    column: CTableColumn
    column_index: int


class CTableCellSlotData:
    row: CTableRow
    column: CTableColumn
    cell: CTableCell
    row_index: int
    column_index: int


class CTableEmptySlotData:
    pass


class CTableLoadingSlotData:
    pass


class CTableErrorSlotData:
    pass


class CTable(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs(CTableHeadless.Kwargs):
        density: CTableDensity = "comfortable"
        striped: bool = False
        hover: bool = False
        sticky_header: bool = False

    @dataclass(slots=True)
    class Slots:
        caption: SlotInput[CTableCaptionSlotData] | None = None
        header: SlotInput[CTableHeaderSlotData] | None = None
        cell: SlotInput[CTableCellSlotData] | None = None
        empty: SlotInput[CTableEmptySlotData] | None = None
        loading: SlotInput[CTableLoadingSlotData] | None = None
        error: SlotInput[CTableErrorSlotData] | None = None

    def template_data(
        self,
        kwargs: CTable.Kwargs,
        slots: CTable.Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        classes = ["cui-table-wrap", f"cui-table-wrap--{kwargs.density}"]
        if kwargs.striped:
            classes.append("cui-table-wrap--striped")
        if kwargs.hover:
            classes.append("cui-table-wrap--hover")
        if kwargs.sticky_header:
            classes.append("cui-table-wrap--sticky-header")
        return {
            "columns": kwargs.columns,
            "rows": kwargs.rows,
            "state": kwargs.state,
            "attrs": kwargs.attrs,
            "table_attrs": kwargs.table_attrs,
            "root_class": " ".join(classes),
            "has_caption": "caption" in self.raw_slots,
        }

    template = """
      <c-CTableHeadless
        c-columns="columns"
        c-rows="rows"
        c-state="state"
        c-attrs="attrs"
        c-table_attrs="table_attrs"
      >
        <c-fill name="default" data="data">
          <div
            c-class="root_class"
            c-bind="data.root_attrs"
            data-citry-ui-part="table-root"
          >
            <table
              class="cui-table"
              c-bind="data.table_attrs"
              data-citry-ui-part="table"
            >
              <c-if cond="has_caption">
                <caption>
                  <c-slot name="caption" />
                </caption>
              </c-if>
              <thead>
                <tr>
                  <c-for each="resolved_column in data.columns">
                    <th
                      scope="col"
                      c-bind="resolved_column.column.attrs or {}"
                    >
                      <c-slot
                        name="header"
                        c-column="resolved_column.column"
                        c-column_index="resolved_column.column_index"
                      >
                        {{ resolved_column.column.label }}
                      </c-slot>
                    </th>
                  </c-for>
                </tr>
              </thead>
              <tbody>
                <c-if cond="data.state == 'loading'">
                  <tr>
                    <td c-colspan="data.column_count">
                      <c-slot name="loading">
                        Loading
                      </c-slot>
                    </td>
                  </tr>
                </c-if>
                <c-elif cond="data.state == 'error'">
                  <tr>
                    <td c-colspan="data.column_count">
                      <c-slot name="error">
                        Unable to load data
                      </c-slot>
                    </td>
                  </tr>
                </c-elif>
                <c-elif cond="data.is_empty">
                  <tr>
                    <td c-colspan="data.column_count">
                      <c-slot name="empty">
                        No data
                      </c-slot>
                    </td>
                  </tr>
                </c-elif>
                <c-else>
                  <c-for each="resolved_row in data.rows">
                    <tr
                      c-bind="resolved_row.row.attrs or {}"
                      c-data-row-key="resolved_row.row.key"
                    >
                      <c-for each="resolved_cell in resolved_row.cells">
                        <c-if cond="resolved_cell.column.row_header">
                          <th
                            scope="row"
                            c-bind="resolved_cell.cell.attrs or {}"
                          >
                            <c-slot
                              name="cell"
                              c-row="resolved_row.row"
                              c-column="resolved_cell.column"
                              c-cell="resolved_cell.cell"
                              c-row_index="resolved_row.row_index"
                              c-column_index="resolved_cell.column_index"
                            >
                              {{ resolved_cell.cell.value }}
                            </c-slot>
                          </th>
                        </c-if>
                        <c-else>
                          <td c-bind="resolved_cell.cell.attrs or {}">
                            <c-slot
                              name="cell"
                              c-row="resolved_row.row"
                              c-column="resolved_cell.column"
                              c-cell="resolved_cell.cell"
                              c-row_index="resolved_row.row_index"
                              c-column_index="resolved_cell.column_index"
                            >
                              {{ resolved_cell.cell.value }}
                            </c-slot>
                          </td>
                        </c-else>
                      </c-for>
                    </tr>
                  </c-for>
                </c-else>
              </tbody>
            </table>
          </div>
        </c-fill>
      </c-CTableHeadless>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-table-wrap) {
          max-width: 100%;
          overflow-x: auto;
        }

        :where(.cui-table) {
          width: 100%;
          border-collapse: collapse;
          color: CanvasText;
        }

        :where(.cui-table th, .cui-table td) {
          border-block-end: 1px solid #d0d5dd;
          padding: 0.75rem;
          text-align: start;
          vertical-align: top;
        }

        :where(.cui-table-wrap--compact .cui-table th, .cui-table-wrap--compact .cui-table td) {
          padding: 0.375rem 0.5rem;
        }

        :where(.cui-table-wrap--striped .cui-table tbody tr:nth-child(even)) {
          background: #f9fafb;
        }

        :where(.cui-table-wrap--hover .cui-table tbody tr:hover) {
          background: #f2f4f7;
        }

        :where(.cui-table-wrap--sticky-header .cui-table thead) {
          position: sticky;
          inset-block-start: 0;
          background: Canvas;
        }
      }
    """


__all__ = [
    "CTable",
    "CTableCaptionSlotData",
    "CTableCell",
    "CTableCellSlotData",
    "CTableColumn",
    "CTableDensity",
    "CTableEmptySlotData",
    "CTableErrorSlotData",
    "CTableHeaderSlotData",
    "CTableHeadless",
    "CTableHeadlessDefaultSlotData",
    "CTableLoadingSlotData",
    "CTableResolvedCell",
    "CTableResolvedColumn",
    "CTableResolvedRow",
    "CTableRow",
    "CTableState",
]
