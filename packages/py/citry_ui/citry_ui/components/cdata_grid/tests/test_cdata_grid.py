from __future__ import annotations

import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component, ComponentLike
from citry_ui import CDataGrid, CDataGridCell, CDataGridColumn, CDataGridEditOption, CDataGridRow, CDataGridSort


def _render(component: ComponentLike) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        @dataclass(slots=True)
        class Kwargs:
            child: ComponentLike

        template = "<main>{{ child }}</main>"

    return str(Page(child=component))


def _columns() -> tuple[CDataGridColumn, ...]:
    return (
        CDataGridColumn("name", "Name", sortable=True, width=180),
        CDataGridColumn("role", "Role", width=140),
    )


def _rows() -> tuple[CDataGridRow, ...]:
    return (
        CDataGridRow("ada", {"name": "Ada", "role": "Engineer"}),
        CDataGridRow("grace", {"name": "Grace", "role": "Admiral"}),
    )


def test_public_schema_and_registration_are_explicit():
    assert [item.name for item in fields(CDataGrid.Kwargs)] == [
        "columns",
        "rows",
        "label",
        "id",
        "state",
        "sort",
        "multi_sort",
        "selection",
        "selected",
        "disabled",
        "total_count",
        "start_index",
        "row_height",
        "viewport_size",
        "overscan",
        "initial_index",
        "density",
        "striped",
        "column_borders",
        "sticky_header",
        "loading_label",
        "empty_label",
        "error_label",
        "sort_ascending_label",
        "sort_descending_label",
        "sort_cleared_label",
        "selected_one_label",
        "selected_label",
        "edit_label",
        "editing_label",
        "edit_submitted_label",
        "edit_cancelled_label",
        "edit_invalid_label",
        "class_",
        "style",
        "attrs",
        "table_attrs",
    ]
    assert "CDataGridColumn" in str(get_type_hints(CDataGrid.Kwargs)["columns"])
    assert CDataGrid in citry_ui.COMPONENTS


def test_complete_grid_has_native_table_positions_and_one_server_tab_stop():
    html = _render(CDataGrid(columns=_columns(), rows=_rows(), label="People", selection="multiple"))

    assert 'role="grid"' in html
    assert 'aria-label="People"' in html
    assert 'aria-rowcount="3"' in html
    assert 'aria-colcount="2"' in html
    assert html.count('role="columnheader"') == 2
    assert html.count('role="gridcell"') == 4
    assert 'aria-rowindex="2"' in html
    assert 'aria-rowindex="3"' in html
    assert html.count('tabindex="0"') == 1
    assert 'data-row-key="ada"' in html
    assert 'data-column-key="role"' in html


def test_sort_selection_and_cell_records_render_exact_accepted_state():
    rows = (
        CDataGridRow(
            "ada",
            {
                "name": CDataGridCell("Ada", {"data-cell": "name"}),
                "role": "Engineer",
            },
            attrs={"data-row": "ada"},
        ),
    )
    html = _render(
        CDataGrid(
            columns=_columns(),
            rows=rows,
            label="People",
            sort=(CDataGridSort("name", "asc"),),
            selection="single",
            selected=("ada",),
        )
    )

    assert 'aria-sort="ascending"' in html
    assert 'data-sort-priority="1"' in html
    assert 'aria-selected="true"' in html
    assert "data-selected" in html
    assert 'data-row="ada"' in html
    assert 'data-cell="name"' in html


def test_editable_columns_render_checked_editor_descriptors() -> None:
    columns = (
        CDataGridColumn("name", "Name", editable=True, editor_attrs={"maxlength": 40}),
        CDataGridColumn(
            "role",
            "Role",
            editable=True,
            editor="select",
            editor_options=(CDataGridEditOption("engineer", "Engineer"), CDataGridEditOption("lead", "Lead")),
        ),
        CDataGridColumn("active", "Active", editable=True, editor="checkbox"),
    )
    html = _render(
        CDataGrid(
            columns=columns,
            rows=(CDataGridRow("ada", {"name": "Ada", "role": "engineer", "active": True}),),
            label="People",
        )
    )
    assert html.count("data-editable") >= 4
    assert 'data-editor="select"' in html
    assert 'data-editor="checkbox"' in html
    assert CDataGridEditOption("lead", "Lead") in columns[1].editor_options
    assert columns[0].editor_attrs == {"maxlength": 40}


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        (CDataGridColumn("x", "X", editable=True, editor="select"), "x", "requires editor_options"),
        (CDataGridColumn("x", "X", editable=True, editor="number"), "not-number", "must contain an int or float"),
        (CDataGridColumn("x", "X", editable=True, editor="checkbox"), "yes", "must contain a bool"),
        (
            CDataGridColumn("x", "X", editable=True, editor="select", editor_options=(CDataGridEditOption("a", "A"),)),
            "b",
            "not an editor option",
        ),
        (CDataGridColumn("x", "X", editable=True, editor_attrs={"onclick": "bad"}), "x", "cannot contain"),
    ],
)
def test_invalid_editor_configuration_fails_early(column: CDataGridColumn, value: object, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(CDataGrid(columns=(column,), rows=(CDataGridRow("row", {"x": value}),), label="Grid"))


def test_window_geometry_uses_logical_counts_indices_and_spacers():
    html = _render(
        CDataGrid(
            columns=_columns(),
            rows=_rows(),
            label="People",
            total_count=100,
            start_index=10,
            row_height=40,
            viewport_size=320,
            initial_index=10,
        )
    )

    assert 'aria-rowcount="101"' in html
    assert 'aria-rowindex="12"' in html
    assert 'aria-rowindex="13"' in html
    assert "height: 400px" in html
    assert "height: 3520px" in html
    assert "--cui-data-grid-row-height: 40px" in html
    assert "--cui-data-grid-viewport-size: 320px" in html

    self_contained = _render(CDataGrid(columns=_columns(), rows=_rows(), label="People", total_count=2))
    assert 'data-citry-ui-part="spacer-row"' not in self_contained


@pytest.mark.parametrize(
    ("state", "text", "busy"),
    [
        ("loading", "Loading data...", True),
        ("error", "Unable to load data.", False),
    ],
)
def test_loading_and_error_replace_ready_rows(state: str, text: str, busy: bool):
    html = _render(CDataGrid(columns=_columns(), rows=_rows(), label="People", state=state))

    assert text in html
    assert not re.search(r'<tr[^>]+data-citry-ui-part="row"', html)
    table = re.search(r'<table[^>]+data-citry-ui-part="table"[^>]*>', html)
    assert table is not None
    assert ('aria-busy="true"' in table.group(0)) is busy
    assert 'tabindex="0"' in html


def test_ready_zero_rows_becomes_localized_empty_state():
    html = _render(CDataGrid(columns=_columns(), rows=(), label="People"))

    assert 'data-state="empty"' in html
    assert "No data." in html
    assert 'data-citry-ui-part="empty"' in html


@pytest.mark.parametrize(
    ("component", "message"),
    [
        (CDataGrid(columns=(), rows=(), label="People"), "at least one column"),
        (
            CDataGrid(
                columns=(CDataGridColumn("name", "Name"),),
                rows=(CDataGridRow("ada", {"other": "Ada"}),),
                label="People",
            ),
            "cells do not match columns",
        ),
        (
            CDataGrid(
                columns=(CDataGridColumn("name", "Name"),),
                rows=(),
                label="People",
                sort=(CDataGridSort("name", "asc"),),
            ),
            "non-sortable column",
        ),
        (CDataGrid(columns=_columns(), rows=_rows(), label="People", start_index=1), "must be 0"),
        (
            CDataGrid(columns=_columns(), rows=_rows(), label="People", selection="single", selected=("ada", "grace")),
            "at most one",
        ),
    ],
)
def test_invalid_server_configuration_fails_early(component: ComponentLike, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(component)


def test_root_table_column_row_and_cell_attrs_merge_but_owned_attrs_are_rejected():
    html = _render(
        CDataGrid(
            columns=(CDataGridColumn("name", "Name", header_attrs={"data-head": "name"}),),
            rows=(CDataGridRow("ada", {"name": CDataGridCell("Ada", {"data-cell": "name"})}),),
            label="People",
            class_="brand",
            style={"color": "red"},
            attrs={"data-root": "grid"},
            table_attrs={"data-table": "people"},
        )
    )
    assert re.search(r'<div class="cui-data-grid brand"[^>]+data-root="grid"', html)
    assert 'data-table="people"' in html
    assert 'data-head="name"' in html
    assert 'data-cell="name"' in html
    assert "color: red" in html
    assert "--cui-data-grid-row-height: 48px" in html

    with pytest.raises(ValueError, match="owned attribute 'role'"):
        _render(CDataGrid(columns=_columns(), rows=_rows(), label="People", table_attrs={"role": "table"}))
    with pytest.raises(ValueError, match="owned attribute 'aria-colindex'"):
        _render(
            CDataGrid(
                columns=(CDataGridColumn("name", "Name", cell_attrs={"aria-colindex": 9}),),
                rows=(CDataGridRow("ada", {"name": "Ada"}),),
                label="People",
            )
        )


def test_runtime_declares_models_navigation_i18n_range_requests_and_cleanup():
    source = (Path(__file__).parents[1] / "runtime.source.js").read_text(encoding="utf8")
    assert "onSortChange: {}" in source
    assert "onSelectionChange: {}" in source
    assert "onRangeChange: {}" in source
    assert "onCellActivate: {}" in source
    assert "onCellEditCommit: {}" in source
    assert "startEdit" in source
    assert "commitEdit" in source
    assert "getComputedStyle(table).direction === 'rtl'" in source
    assert "new ResizeObserver" in source
    assert "requestAnimationFrame" in source
    assert "citry-ui-data-grid-sort-ascending" in source
    assert "pendingSelection" in source
    assert "pendingSort" in source
    assert "reorderCompleteRows" in source
    assert "new Intl.Collator" in source
    assert "acceptedPending" in source
    assert "pointerSelection" in source
    assert "data-selecting" in source
    assert "event.pointerType !== 'mouse'" in source
    assert "source !== 'keyboard'" in source
    assert "removeEventListener('keydown'" in source
    assert "data-citry-data-grid-initialized" in source


def test_messages_are_final_component_member_and_cover_every_library_output():
    keys = set(re.findall(r"^\s*(citry-ui-data-grid-[a-z-]+)\s*=", CDataGrid.messages, re.MULTILINE))
    assert keys == {
        "citry-ui-data-grid-loading",
        "citry-ui-data-grid-empty",
        "citry-ui-data-grid-error",
        "citry-ui-data-grid-sort-ascending",
        "citry-ui-data-grid-sort-descending",
        "citry-ui-data-grid-sort-cleared",
        "citry-ui-data-grid-selected-one",
        "citry-ui-data-grid-selected",
        "citry-ui-data-grid-edit",
        "citry-ui-data-grid-editing",
        "citry-ui-data-grid-edit-submitted",
        "citry-ui-data-grid-edit-cancelled",
        "citry-ui-data-grid-edit-invalid",
    }
    members = list(CDataGrid.__dict__)
    assert members.index("messages") > members.index("css_file")
