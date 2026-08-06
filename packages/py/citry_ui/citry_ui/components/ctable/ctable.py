"""Styled semantic Table component family."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from citry import LibraryComponent, SlotInput, merge_attrs
from citry_ui.components._attrs import CClassValue, CStyleValue, merge_root_attrs
from citry_ui.components._validation import (
    reject_owned_attrs,
    validate_boolean,
    validate_choice,
    validate_html_id,
    validate_non_empty_string,
)

CTableState = Literal["ready", "loading", "error"]
CTableVariant = Literal["line", "outline"]
CTableDensity = Literal["default", "comfortable", "compact"]
CTableAlign = Literal["start", "center", "end"]
CTableLayout = Literal["auto", "fixed"]
CTableOverflow = Literal["auto", "visible"]
CTableCaptionSide = Literal["top", "bottom"]

_OWNED_TABLE_CELL_ATTRS = frozenset(
    {
        "colspan",
        "data-align",
        "data-citry-ui-part",
        "data-column-key",
        "id",
        "role",
        "rowspan",
        "scope",
    }
)


@dataclass(frozen=True, slots=True)
class CTableColumn:
    key: str
    label: str
    row_header: bool = False
    align: CTableAlign = "start"
    header_attrs: Mapping[str, object] | None = None
    cell_attrs: Mapping[str, object] | None = None
    footer: object | None = None
    footer_attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTableCell:
    value: object
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CTableRow:
    key: str
    cells: Mapping[str, object | CTableCell]
    attrs: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class _ResolvedTableColumn:
    column: CTableColumn
    column_index: int
    header_attrs: Mapping[str, object]
    cell_attrs: Mapping[str, object]
    footer_attrs: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _ResolvedTableCell:
    column: CTableColumn
    cell: CTableCell
    column_index: int
    attrs: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class _ResolvedTableRow:
    row: CTableRow
    cells: tuple[_ResolvedTableCell, ...]
    row_index: int
    attrs: Mapping[str, object]


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


class CTableFooterSlotData:
    column: CTableColumn
    value: object | None
    column_index: int


class CTableEmptySlotData:
    pass


class CTableLoadingSlotData:
    pass


class CTableErrorSlotData:
    pass


class CTable(LibraryComponent):
    @dataclass(slots=True)
    class Kwargs:
        columns: Sequence[CTableColumn]
        rows: Sequence[CTableRow]
        state: CTableState = "ready"
        id: str | None = None
        variant: CTableVariant = "line"
        density: CTableDensity = "comfortable"
        striped: bool = False
        hover: bool = False
        sticky_header: bool = False
        column_borders: bool = False
        layout: CTableLayout = "auto"
        overflow: CTableOverflow = "auto"
        caption_side: CTableCaptionSide = "top"
        scroll_label: str | None = None
        loading_label: str = "Loading data..."
        empty_label: str = "No data."
        error_label: str = "Unable to load data."
        class_: CClassValue | None = None
        style: CStyleValue | None = None
        attrs: Mapping[str, object] | None = None
        table_attrs: Mapping[str, object] | None = None

    @dataclass(slots=True)
    class Slots:
        caption: SlotInput[CTableCaptionSlotData] | None = None
        header: SlotInput[CTableHeaderSlotData] | None = None
        cell: SlotInput[CTableCellSlotData] | None = None
        footer: SlotInput[CTableFooterSlotData] | None = None
        empty: SlotInput[CTableEmptySlotData] | None = None
        loading: SlotInput[CTableLoadingSlotData] | None = None
        error: SlotInput[CTableErrorSlotData] | None = None

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, Any]:
        validate_choice("CTable", "state", kwargs.state, ("ready", "loading", "error"))
        validate_html_id("CTable", kwargs.id)
        validate_choice("CTable", "variant", kwargs.variant, ("line", "outline"))
        validate_choice(
            "CTable",
            "density",
            kwargs.density,
            ("default", "comfortable", "compact"),
        )
        validate_boolean("CTable", "striped", kwargs.striped)
        validate_boolean("CTable", "hover", kwargs.hover)
        validate_boolean("CTable", "sticky_header", kwargs.sticky_header)
        validate_boolean("CTable", "column_borders", kwargs.column_borders)
        validate_choice("CTable", "layout", kwargs.layout, ("auto", "fixed"))
        validate_choice("CTable", "overflow", kwargs.overflow, ("auto", "visible"))
        validate_choice("CTable", "caption_side", kwargs.caption_side, ("top", "bottom"))
        if kwargs.scroll_label is not None:
            validate_non_empty_string("CTable", "scroll_label", kwargs.scroll_label)
        validate_non_empty_string("CTable", "loading_label", kwargs.loading_label)
        validate_non_empty_string("CTable", "empty_label", kwargs.empty_label)
        validate_non_empty_string("CTable", "error_label", kwargs.error_label)
        root_attrs = merge_root_attrs(
            self._validated_attrs(kwargs.attrs, "CTable attrs"),
            kwargs.class_,
            kwargs.style,
        )
        table_attrs = self._validated_attrs(kwargs.table_attrs, "CTable table_attrs")
        reject_owned_attrs(
            root_attrs,
            {
                "data-caption-side",
                "data-citry-ui-part",
                "data-column-borders",
                "data-density",
                "data-hover",
                "data-layout",
                "data-overflow",
                "data-state",
                "data-sticky-header",
                "data-striped",
                "data-variant",
                "id",
                "aria-label",
                "aria-labelledby",
                "role",
                "tabindex",
            },
            "CTable attrs",
        )
        reject_owned_attrs(
            table_attrs,
            {"aria-busy", "data-citry-ui-part", "id", "role"},
            "CTable table_attrs",
        )

        columns = self._normalize_columns(kwargs.columns)
        table_id = kwargs.id or f"cui-table-{self.id}"
        rows = self._normalize_rows(kwargs.rows, columns)
        has_caption = "caption" in self.raw_slots
        caption_id = f"{table_id}-caption"
        table_aria_label = table_attrs.get("aria-label")
        table_aria_labelledby = table_attrs.get("aria-labelledby")
        region_aria_label = kwargs.scroll_label
        region_aria_labelledby: object | None = None
        if region_aria_label is None:
            if has_caption:
                region_aria_labelledby = caption_id
            elif isinstance(table_aria_labelledby, str) and table_aria_labelledby:
                region_aria_labelledby = table_aria_labelledby
            elif isinstance(table_aria_label, str) and table_aria_label:
                region_aria_label = table_aria_label

        has_footer = "footer" in self.raw_slots or any(resolved.column.footer is not None for resolved in columns)
        is_empty = kwargs.state == "ready" and not rows
        announcement = ""
        if kwargs.state == "loading":
            announcement = kwargs.loading_label
        elif kwargs.state == "error":
            announcement = kwargs.error_label
        elif is_empty:
            announcement = kwargs.empty_label

        region_role = None
        if kwargs.overflow == "auto" and (region_aria_label or region_aria_labelledby):
            region_role = "region"
        return {
            "columns": columns,
            "rows": rows,
            "state": kwargs.state,
            "table_id": table_id,
            "caption_id": caption_id,
            "aria_busy": "true" if kwargs.state == "loading" else None,
            "region_role": region_role,
            "region_aria_label": region_aria_label if kwargs.overflow == "auto" else None,
            "region_aria_labelledby": region_aria_labelledby if kwargs.overflow == "auto" else None,
            "variant": kwargs.variant,
            "density": kwargs.density,
            "striped": kwargs.striped,
            "hover": kwargs.hover,
            "sticky_header": kwargs.sticky_header,
            "column_borders": kwargs.column_borders,
            "layout": kwargs.layout,
            "overflow": kwargs.overflow,
            "root_tabindex": 0 if kwargs.overflow == "auto" else None,
            "caption_side": kwargs.caption_side,
            "column_count": len(columns),
            "is_empty": is_empty,
            "has_footer": kwargs.state == "ready" and has_footer,
            "announcement": announcement,
            "loading_label": kwargs.loading_label,
            "empty_label": kwargs.empty_label,
            "error_label": kwargs.error_label,
            "has_caption": has_caption,
            "attrs": root_attrs,
            "table_attrs": table_attrs,
        }

    @staticmethod
    def _validated_attrs(
        value: Mapping[str, object] | None,
        location: str,
    ) -> dict[str, object]:
        if value is not None and not isinstance(value, Mapping):
            msg = f"{location} must be a mapping or None, got {value!r}."
            raise TypeError(msg)
        return dict(value or {})

    @classmethod
    def _normalize_columns(
        cls,
        value: Sequence[CTableColumn],
    ) -> tuple[_ResolvedTableColumn, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            msg = "CTable columns must be a sequence of CTableColumn values."
            raise TypeError(msg)
        columns = tuple(value)
        if not columns:
            msg = "CTable requires at least one column."
            raise ValueError(msg)
        seen: set[str] = set()
        row_header_count = 0
        resolved_columns: list[_ResolvedTableColumn] = []
        for index, column in enumerate(columns):
            if not isinstance(column, CTableColumn):
                msg = f"CTable columns[{index}] must be CTableColumn, got {column!r}."
                raise TypeError(msg)
            validate_non_empty_string("CTableColumn", "key", column.key)
            validate_non_empty_string("CTableColumn", "label", column.label)
            validate_boolean("CTableColumn", "row_header", column.row_header)
            validate_choice(
                "CTableColumn",
                "align",
                column.align,
                ("start", "center", "end"),
            )
            if column.key in seen:
                msg = f"CTable column keys must be unique; {column.key!r} occurs more than once."
                raise ValueError(msg)
            seen.add(column.key)
            row_header_count += int(column.row_header)
            header_attrs = cls._validated_attrs(
                column.header_attrs,
                f"CTable column {column.key!r} header_attrs",
            )
            cell_attrs = cls._validated_attrs(
                column.cell_attrs,
                f"CTable column {column.key!r} cell_attrs",
            )
            footer_attrs = cls._validated_attrs(
                column.footer_attrs,
                f"CTable column {column.key!r} footer_attrs",
            )
            for attrs, location in (
                (header_attrs, f"CTable column {column.key!r} header_attrs"),
                (cell_attrs, f"CTable column {column.key!r} cell_attrs"),
                (footer_attrs, f"CTable column {column.key!r} footer_attrs"),
            ):
                reject_owned_attrs(attrs, _OWNED_TABLE_CELL_ATTRS, location)
            resolved_columns.append(
                _ResolvedTableColumn(
                    column=column,
                    column_index=index,
                    header_attrs=header_attrs,
                    cell_attrs=cell_attrs,
                    footer_attrs=footer_attrs,
                )
            )
        if row_header_count > 1:
            msg = "CTable supports at most one row_header column."
            raise ValueError(msg)
        return tuple(resolved_columns)

    @classmethod
    def _normalize_rows(
        cls,
        value: Sequence[CTableRow],
        columns: tuple[_ResolvedTableColumn, ...],
    ) -> tuple[_ResolvedTableRow, ...]:
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            msg = "CTable rows must be a sequence of CTableRow values."
            raise TypeError(msg)
        rows = tuple(value)
        expected_keys = {resolved.column.key for resolved in columns}
        seen: set[str] = set()
        resolved_rows: list[_ResolvedTableRow] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, CTableRow):
                msg = f"CTable rows[{row_index}] must be CTableRow, got {row!r}."
                raise TypeError(msg)
            validate_non_empty_string("CTableRow", "key", row.key)
            if row.key in seen:
                msg = f"CTable row keys must be unique; {row.key!r} occurs more than once."
                raise ValueError(msg)
            seen.add(row.key)
            if not isinstance(row.cells, Mapping):
                msg = f"CTable row {row.key!r} cells must be a mapping, got {row.cells!r}."
                raise TypeError(msg)
            if any(not isinstance(key, str) for key in row.cells):
                msg = f"CTable row {row.key!r} cell keys must be strings."
                raise TypeError(msg)
            actual_keys = set(row.cells)
            if actual_keys != expected_keys:
                missing = sorted(expected_keys - actual_keys)
                extra = sorted(actual_keys - expected_keys)
                msg = f"CTable row {row.key!r} cells do not match columns; missing={missing!r}, extra={extra!r}."
                raise ValueError(msg)
            row_attrs = cls._validated_attrs(row.attrs, f"CTable row {row.key!r} attrs")
            reject_owned_attrs(
                row_attrs,
                {
                    "data-citry-key",
                    "data-citry-ui-part",
                    "data-row-key",
                    "id",
                    "role",
                },
                f"CTable row {row.key!r} attrs",
            )
            resolved_cells: list[_ResolvedTableCell] = []
            for resolved_column in columns:
                column = resolved_column.column
                raw_cell = row.cells[column.key]
                cell = raw_cell if isinstance(raw_cell, CTableCell) else CTableCell(raw_cell)
                cell_attrs = cls._validated_attrs(
                    cell.attrs,
                    f"CTable row {row.key!r}, column {column.key!r} attrs",
                )
                reject_owned_attrs(
                    cell_attrs,
                    _OWNED_TABLE_CELL_ATTRS,
                    f"CTable row {row.key!r}, column {column.key!r} attrs",
                )
                resolved_cells.append(
                    _ResolvedTableCell(
                        column=column,
                        cell=cell,
                        column_index=resolved_column.column_index,
                        attrs=merge_attrs(resolved_column.cell_attrs, cell_attrs),
                    )
                )
            resolved_rows.append(
                _ResolvedTableRow(
                    row=row,
                    cells=tuple(resolved_cells),
                    row_index=row_index,
                    attrs=row_attrs,
                )
            )
        return tuple(resolved_rows)

    template = """
      <div
        class="cui-table-root"
        c-id="table_id"
        c-role="region_role"
        c-aria-label="region_aria_label"
        c-aria-labelledby="region_aria_labelledby"
        c-tabindex="root_tabindex"
        c-data-state="state"
        c-data-variant="variant"
        c-data-density="density"
        c-data-striped="striped"
        c-data-hover="hover"
        c-data-sticky-header="sticky_header"
        c-data-column-borders="column_borders"
        c-data-layout="layout"
        c-data-overflow="overflow"
        c-data-caption-side="caption_side"
        c-bind="attrs"
        data-citry-ui-part="root"
      >
        <span
          class="cui-table-announcer"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {{ announcement }}
        </span>
        <table
          class="cui-table"
          c-aria-busy="aria_busy"
          c-bind="table_attrs"
          data-citry-ui-part="table"
        >
          <c-if cond="has_caption">
            <caption
              c-id="caption_id"
              data-citry-ui-part="caption"
            >
              <c-slot name="caption" />
            </caption>
          </c-if>
          <thead data-citry-ui-part="header">
            <tr data-citry-ui-part="header-row">
              <th
                c-for="resolved_column in columns"
                scope="col"
                c-data-column-key="resolved_column.column.key"
                c-data-align="resolved_column.column.align"
                c-bind="resolved_column.header_attrs"
                data-citry-ui-part="header-cell"
              >
                <c-slot
                  name="header"
                  c-column="resolved_column.column"
                  c-column_index="resolved_column.column_index"
                >
                  {{ resolved_column.column.label }}
                </c-slot>
              </th>
            </tr>
          </thead>
          <tbody data-citry-ui-part="body">
            <c-if cond="state == 'loading'">
              <tr data-citry-ui-part="state-row">
                <td
                  c-colspan="column_count"
                  data-citry-ui-part="state-cell"
                >
                  <div data-citry-ui-part="loading">
                    <c-slot name="loading">
                      {{ loading_label }}
                    </c-slot>
                  </div>
                </td>
              </tr>
            </c-if>
            <c-elif cond="state == 'error'">
              <tr data-citry-ui-part="state-row">
                <td
                  c-colspan="column_count"
                  data-citry-ui-part="state-cell"
                >
                  <div data-citry-ui-part="error">
                    <c-slot name="error">
                      {{ error_label }}
                    </c-slot>
                  </div>
                </td>
              </tr>
            </c-elif>
            <c-elif cond="is_empty">
              <tr data-citry-ui-part="state-row">
                <td
                  c-colspan="column_count"
                  data-citry-ui-part="state-cell"
                >
                  <div data-citry-ui-part="empty">
                    <c-slot name="empty">
                      {{ empty_label }}
                    </c-slot>
                  </div>
                </td>
              </tr>
            </c-elif>
            <c-else>
              <tr
                c-for="resolved_row in rows"
                #c-key="resolved_row.row.key"
                c-data-row-key="resolved_row.row.key"
                c-bind="resolved_row.attrs"
                data-citry-ui-part="row"
              >
                <c-for each="resolved_cell in resolved_row.cells">
                  <c-if cond="resolved_cell.column.row_header">
                    <th
                      scope="row"
                      c-data-column-key="resolved_cell.column.key"
                      c-data-align="resolved_cell.column.align"
                      c-bind="resolved_cell.attrs"
                      data-citry-ui-part="cell"
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
                    <td
                      c-data-column-key="resolved_cell.column.key"
                      c-data-align="resolved_cell.column.align"
                      c-bind="resolved_cell.attrs"
                      data-citry-ui-part="cell"
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
                    </td>
                  </c-else>
                </c-for>
              </tr>
            </c-else>
          </tbody>
          <c-if cond="has_footer">
            <tfoot data-citry-ui-part="footer">
              <tr data-citry-ui-part="footer-row">
                <c-for each="resolved_column in columns">
                  <c-if cond="resolved_column.column.row_header">
                    <th
                      scope="row"
                      c-data-column-key="resolved_column.column.key"
                      c-data-align="resolved_column.column.align"
                      c-bind="resolved_column.footer_attrs"
                      data-citry-ui-part="footer-cell"
                    >
                      <c-slot
                        name="footer"
                        c-column="resolved_column.column"
                        c-value="resolved_column.column.footer"
                        c-column_index="resolved_column.column_index"
                      >
                        {{ resolved_column.column.footer }}
                      </c-slot>
                    </th>
                  </c-if>
                  <c-else>
                    <td
                      c-data-column-key="resolved_column.column.key"
                      c-data-align="resolved_column.column.align"
                      c-bind="resolved_column.footer_attrs"
                      data-citry-ui-part="footer-cell"
                    >
                      <c-slot
                        name="footer"
                        c-column="resolved_column.column"
                        c-value="resolved_column.column.footer"
                        c-column_index="resolved_column.column_index"
                      >
                        {{ resolved_column.column.footer }}
                      </c-slot>
                    </td>
                  </c-else>
                </c-for>
              </tr>
            </tfoot>
          </c-if>
        </table>
      </div>
    """

    css = """
      @layer citry-ui.theme {
        :where(.cui-table-root) {
          --_cui-table-background: var(--cui-table-background, Canvas);
          --_cui-table-foreground: var(--cui-table-foreground, CanvasText);
          --_cui-table-muted-foreground: var(
            --cui-table-muted-foreground,
            color-mix(in srgb, CanvasText 68%, transparent)
          );
          --_cui-table-border-color: var(
            --cui-table-border-color,
            color-mix(in srgb, CanvasText 22%, transparent)
          );
          --_cui-table-header-background: var(
            --cui-table-header-background,
            color-mix(in srgb, CanvasText 5%, Canvas)
          );
          --_cui-table-footer-background: var(
            --cui-table-footer-background,
            color-mix(in srgb, CanvasText 5%, Canvas)
          );
          --_cui-table-striped-background: var(
            --cui-table-striped-background,
            color-mix(in srgb, CanvasText 3%, Canvas)
          );
          --_cui-table-hover-background: var(
            --cui-table-hover-background,
            color-mix(in srgb, Highlight 9%, Canvas)
          );
          --_cui-table-error-foreground: var(
            --cui-table-error-foreground,
            light-dark(#b42318, #fda29b)
          );
          --_cui-table-focus-color: var(--cui-table-focus-color, Highlight);
          --_cui-table-radius: var(--cui-table-radius, 0.625rem);
          --_cui-table-cell-block-padding: var(--cui-table-cell-block-padding, 0.75rem);
          --_cui-table-cell-inline-padding: var(--cui-table-cell-inline-padding, 1rem);
          --_cui-table-caption-padding: var(--cui-table-caption-padding, 0.75rem 1rem);
          --_cui-table-min-width: var(--cui-table-min-width, 32rem);
          --_cui-table-sticky-offset: var(--cui-table-sticky-offset, 0px);

          max-width: 100%;
          color: var(--_cui-table-foreground);
          background: var(--_cui-table-background);
          border-radius: var(--_cui-table-radius);
        }

        :where(.cui-table-announcer) {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }

        :where(.cui-table-root[data-overflow="auto"]) {
          overflow-x: auto;
          overscroll-behavior-inline: contain;
        }

        :where(.cui-table-root[data-variant="outline"]) {
          border: 1px solid var(--_cui-table-border-color);
        }

        :where(.cui-table) {
          width: 100%;
          min-width: var(--_cui-table-min-width);
          border-spacing: 0;
          border-collapse: separate;
          table-layout: auto;
          color: inherit;
          background: inherit;
        }

        :where(.cui-table-root[data-overflow="visible"] > .cui-table) {
          min-width: 0;
        }

        :where(.cui-table-root[data-layout="fixed"] > .cui-table) {
          table-layout: fixed;
        }

        :where(.cui-table > [data-citry-ui-part="caption"]) {
          padding: var(--_cui-table-caption-padding);
          color: var(--_cui-table-muted-foreground);
          font-weight: 600;
          text-align: start;
          caption-side: top;
        }

        :where(
          .cui-table-root[data-caption-side="bottom"]
          > .cui-table
          > [data-citry-ui-part="caption"]
        ) {
          caption-side: bottom;
        }

        :where(
          .cui-table
          > [data-citry-ui-part="header"]
          > [data-citry-ui-part="header-row"]
          > [data-citry-ui-part="header-cell"]
        ) {
          padding-block: var(--_cui-table-cell-block-padding);
          padding-inline: var(--_cui-table-cell-inline-padding);
          border-block-end: 1px solid var(--_cui-table-border-color);
          color: var(--_cui-table-muted-foreground);
          background: var(--_cui-table-header-background);
          font-size: 0.875em;
          font-weight: 650;
          text-align: start;
          vertical-align: bottom;
        }

        :where(
          .cui-table
          > [data-citry-ui-part="body"]
          > :is([data-citry-ui-part="row"], [data-citry-ui-part="state-row"])
          > :is([data-citry-ui-part="cell"], [data-citry-ui-part="state-cell"]),
          .cui-table
          > [data-citry-ui-part="footer"]
          > [data-citry-ui-part="footer-row"]
          > [data-citry-ui-part="footer-cell"]
        ) {
          padding-block: var(--_cui-table-cell-block-padding);
          padding-inline: var(--_cui-table-cell-inline-padding);
          border-block-end: 1px solid var(--_cui-table-border-color);
          text-align: start;
          vertical-align: top;
        }

        :where(
          .cui-table
          > :is([data-citry-ui-part="header"], [data-citry-ui-part="body"], [data-citry-ui-part="footer"])
          > :is([data-citry-ui-part="header-row"], [data-citry-ui-part="row"], [data-citry-ui-part="footer-row"])
          > [data-align="center"]
        ) {
          text-align: center;
        }

        :where(
          .cui-table
          > :is([data-citry-ui-part="header"], [data-citry-ui-part="body"], [data-citry-ui-part="footer"])
          > :is([data-citry-ui-part="header-row"], [data-citry-ui-part="row"], [data-citry-ui-part="footer-row"])
          > [data-align="end"]
        ) {
          text-align: end;
        }

        :where(.cui-table-root[data-density="default"]) {
          --_cui-table-cell-block-padding: var(--cui-table-cell-block-padding, 1rem);
        }

        :where(.cui-table-root[data-density="compact"]) {
          --_cui-table-cell-block-padding: var(--cui-table-cell-block-padding, 0.5rem);
          --_cui-table-cell-inline-padding: var(--cui-table-cell-inline-padding, 0.75rem);
        }

        :where(
          .cui-table-root[data-column-borders]
          > .cui-table
          > :is([data-citry-ui-part="header"], [data-citry-ui-part="body"], [data-citry-ui-part="footer"])
          > :is(
            [data-citry-ui-part="header-row"],
            [data-citry-ui-part="row"],
            [data-citry-ui-part="footer-row"]
          )
          > :is(
            [data-citry-ui-part="header-cell"],
            [data-citry-ui-part="cell"],
            [data-citry-ui-part="footer-cell"]
          ):not(:last-child)
        ) {
          border-inline-end: 1px solid var(--_cui-table-border-color);
        }

        :where(
          .cui-table-root[data-striped]
          > .cui-table
          > [data-citry-ui-part="body"]
          > [data-citry-ui-part="row"]:nth-child(even)
          > [data-citry-ui-part="cell"]
        ) {
          background: var(--_cui-table-striped-background);
        }

        :where(
          .cui-table-root[data-hover]
          > .cui-table
          > [data-citry-ui-part="body"]
          > [data-citry-ui-part="row"]:hover
          > [data-citry-ui-part="cell"]
        ) {
          background: var(--_cui-table-hover-background);
        }

        :where(
          .cui-table-root[data-sticky-header]
          > .cui-table
          > [data-citry-ui-part="header"]
          > [data-citry-ui-part="header-row"]
          > [data-citry-ui-part="header-cell"]
        ) {
          position: sticky;
          z-index: 1;
          inset-block-start: var(--_cui-table-sticky-offset);
        }

        :where(
          .cui-table
          > [data-citry-ui-part="body"]
          > [data-citry-ui-part="state-row"]
          > [data-citry-ui-part="state-cell"]
        ) {
          color: var(--_cui-table-muted-foreground);
          text-align: center;
        }

        :where(
          .cui-table
          > [data-citry-ui-part="body"]
          > [data-citry-ui-part="state-row"]
          > [data-citry-ui-part="state-cell"]
          > [data-citry-ui-part="error"]
        ) {
          color: var(--_cui-table-error-foreground);
        }

        :where(
          .cui-table
          > [data-citry-ui-part="body"]
          > [data-citry-ui-part="row"]:last-child
          > [data-citry-ui-part="cell"]
        ) {
          border-block-end-color: transparent;
        }

        :where(
          .cui-table
          > [data-citry-ui-part="footer"]
          > [data-citry-ui-part="footer-row"]
          > [data-citry-ui-part="footer-cell"]
        ) {
          border-block-start: 1px solid var(--_cui-table-border-color);
          border-block-end: 0;
          background: var(--_cui-table-footer-background);
          font-weight: 650;
        }

        :where(.cui-table-root[data-overflow="auto"]:focus-visible) {
          outline: 2px solid var(--_cui-table-focus-color);
          outline-offset: 2px;
        }

        @media (forced-colors: active) {
          :where(.cui-table-root[data-variant="outline"]) {
            border-color: CanvasText;
          }

          :where(
            .cui-table
            > :is([data-citry-ui-part="header"], [data-citry-ui-part="body"], [data-citry-ui-part="footer"])
            > :is(
              [data-citry-ui-part="header-row"],
              [data-citry-ui-part="row"],
              [data-citry-ui-part="state-row"],
              [data-citry-ui-part="footer-row"]
            )
            > :is(
              [data-citry-ui-part="header-cell"],
              [data-citry-ui-part="cell"],
              [data-citry-ui-part="state-cell"],
              [data-citry-ui-part="footer-cell"]
            )
          ) {
            border-color: CanvasText;
          }
        }

        @media print {
          :where(.cui-table-root) {
            overflow: visible;
            border-color: CanvasText;
          }

          :where(.cui-table) {
            min-width: 0;
          }

          :where(
            .cui-table-root[data-sticky-header]
            > .cui-table
            > [data-citry-ui-part="header"]
            > [data-citry-ui-part="header-row"]
            > [data-citry-ui-part="header-cell"]
          ) {
            position: static;
          }
        }
      }
    """


__all__ = [
    "CTable",
    "CTableAlign",
    "CTableCaptionSide",
    "CTableCaptionSlotData",
    "CTableCell",
    "CTableCellSlotData",
    "CTableColumn",
    "CTableDensity",
    "CTableEmptySlotData",
    "CTableErrorSlotData",
    "CTableFooterSlotData",
    "CTableHeaderSlotData",
    "CTableLayout",
    "CTableLoadingSlotData",
    "CTableOverflow",
    "CTableRow",
    "CTableState",
    "CTableVariant",
]
