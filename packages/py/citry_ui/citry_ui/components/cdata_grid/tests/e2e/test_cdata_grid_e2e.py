"""Browser evidence for Data Grid navigation, models, windows, and cleanup."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui import CDataGridColumn, CDataGridEditOption, CDataGridRow

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Data Grid browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <title>Data Grid evidence</title><c-css /></head>
          <body x-data>
            <c-CDataGrid
              id="grid"
              c-columns="columns"
              c-rows="rows"
              label="Project members"
              selection="multiple"
              c-selected="['grace']"
              $c-props="{
                sort:$store.grid.sort,
                selected:$store.grid.selected,
                onSortChange:(next,detail)=>{
                  $store.grid.sortEvents.push({next:[...next],direction:detail.direction});
                  if($store.grid.acceptSort)$store.grid.sort=[...next];
                },
                onSelectionChange:(next,detail)=>{
                  $store.grid.selectionEvents.push({next:[...next],controlled:detail.controlled});
                  if($store.grid.acceptSelection)$store.grid.selected=[...next];
                },
                onCellActivate:(detail)=>$store.grid.activations.push({row:detail.rowKey,column:detail.columnKey}),
              }"
            />
            <c-CDataGrid
              id="windowed"
              c-columns="columns"
              c-rows="window_rows"
              label="Audit records"
              c-total_count="200"
              c-start_index="20"
              c-row_height="40"
              c-viewport_size="200"
              c-initial_index="20"
              $c-props="{onRangeChange:(detail)=>$store.grid.ranges.push({
                startIndex:detail.startIndex,
                endIndex:detail.endIndex,
                visibleStartIndex:detail.visibleStartIndex,
                visibleEndIndex:detail.visibleEndIndex,
                requestId:detail.requestId,
                reason:detail.reason,
              })}"
            />
            <c-CDataGrid
              id="editable"
              c-columns="editable_columns"
              c-rows="editable_rows"
              label="Editable members"
              $c-props="{
                onCellEditStart:(detail)=>$store.grid.editStarts.push([detail.rowKey,detail.columnKey]),
                onCellEditCommit:(value,detail)=>{
                  $store.grid.editCommits.push([value,detail.rowKey,detail.columnKey,detail.reason]);
                  return value !== 'reject';
                },
                onCellEditCancel:(detail)=>$store.grid.editCancels.push([detail.rowKey,detail.columnKey,detail.reason]),
              }"
            />
          </body></html>
        """
        js = """
          Alpine.store('grid', {
            sort:[], selected:['grace'], acceptSort:false, acceptSelection:false,
            sortEvents:[], selectionEvents:[], activations:[], ranges:[],
            editStarts:[], editCommits:[], editCancels:[],
          });
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            columns = (
                CDataGridColumn("name", "Name", sortable=True, width=180),
                CDataGridColumn("role", "Role", sortable=True, width=160),
                CDataGridColumn("score", "Score", width=100, align="end"),
            )
            return {
                "columns": columns,
                "rows": (
                    CDataGridRow("ada", {"name": "Ada", "role": "Engineer", "score": 98}),
                    CDataGridRow("grace", {"name": "Grace", "role": "Admiral", "score": 95}),
                    CDataGridRow("locked", {"name": "Ada", "role": "Security", "score": 90}, disabled=True),
                ),
                "window_rows": tuple(
                    CDataGridRow(
                        f"audit-{index}",
                        {"name": f"Record {index + 1}", "role": "Release", "score": index},
                    )
                    for index in range(20, 34)
                ),
                "editable_columns": (
                    CDataGridColumn("name", "Name", editable=True),
                    CDataGridColumn(
                        "score", "Score", editable=True, editor="number", editor_attrs={"min": 0, "max": 100}
                    ),
                    CDataGridColumn(
                        "role",
                        "Role",
                        editable=True,
                        editor="select",
                        editor_options=(
                            CDataGridEditOption("engineer", "Engineer"),
                            CDataGridEditOption("lead", "Lead"),
                        ),
                    ),
                    CDataGridColumn("active", "Active", editable=True, editor="checkbox"),
                ),
                "editable_rows": (
                    CDataGridRow("ada", {"name": "Ada", "score": 98, "role": "engineer", "active": True}),
                ),
            }

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    for selector in ("#grid", "#windowed", "#editable"):
        page.wait_for_selector(f"{selector}[data-citry-data-grid-initialized]")
    return errors


def test_composite_keyboard_navigation_rtl_and_activation(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#grid")
    first = root.locator('[data-citry-ui-part="cell"]').first

    assert root.locator('[data-citry-ui-part="viewport"]').get_attribute("tabindex") == "-1"
    assert root.locator('[data-citry-ui-part="cell"][tabindex="0"]').count() == 1
    first.focus()
    page.keyboard.press("ArrowRight")
    assert root.locator('[data-row-key="ada"][data-column-key="role"]').evaluate(
        "element => document.activeElement === element"
    )
    page.keyboard.press("ArrowDown")
    assert root.locator('[data-row-key="grace"][data-column-key="role"]').evaluate(
        "element => document.activeElement === element"
    )
    page.keyboard.press("Enter")
    assert page.evaluate("Alpine.store('grid').activations") == [{"row": "grace", "column": "role"}]

    root.evaluate("element => element.dir='rtl'")
    first.focus()
    page.keyboard.press("ArrowLeft")
    assert root.locator('[data-row-key="ada"][data-column-key="role"]').evaluate(
        "element => document.activeElement === element"
    )
    assert errors == []


def test_sort_and_selection_requests_wait_for_controlled_acceptance(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#grid")
    name_header = root.locator('[data-citry-ui-part="header-cell"][data-column-key="name"]')
    role_header = root.locator('[data-citry-ui-part="header-cell"][data-column-key="role"]')
    ada = root.locator('[data-citry-ui-part="row"][data-row-key="ada"]')

    name_header.click()
    assert name_header.get_attribute("aria-sort") is None
    assert page.evaluate("Alpine.store('grid').sortEvents") == [
        {"next": [{"key": "name", "direction": "asc"}], "direction": "asc"}
    ]
    page.evaluate("Alpine.store('grid').acceptSort=true")
    name_header.click()
    page.wait_for_function("document.querySelector('#grid [data-column-key=name]').ariaSort === 'ascending'")
    assert name_header.get_attribute("data-sort") == "asc"
    assert "sorted ascending" in root.locator('[data-citry-ui-part="status"]').text_content()
    assert root.locator('[data-citry-ui-part="row"]').evaluate_all("rows => rows.map(row => row.dataset.rowKey)") == [
        "ada",
        "locked",
        "grace",
    ]

    role_header.click(modifiers=["Shift"])
    page.wait_for_function("document.querySelector('#grid [data-column-key=role]').ariaSort === 'ascending'")
    role_header.click(modifiers=["Shift"])
    page.wait_for_function("document.querySelector('#grid [data-column-key=role]').ariaSort === 'descending'")
    assert name_header.get_attribute("data-sort-priority") == "1"
    assert role_header.get_attribute("data-sort-priority") == "2"
    assert root.locator('[data-citry-ui-part="row"]').evaluate_all("rows => rows.map(row => row.dataset.rowKey)") == [
        "locked",
        "ada",
        "grace",
    ]

    ada.locator('[data-citry-ui-part="cell"]').first.click()
    assert ada.get_attribute("aria-selected") == "false"
    assert page.evaluate("Alpine.store('grid').selectionEvents.at(-1)") == {
        "next": ["ada"],
        "controlled": True,
    }
    page.evaluate("Alpine.store('grid').acceptSelection=true")
    ada.locator('[data-citry-ui-part="cell"]').first.click()
    page.wait_for_function("document.querySelector('#grid [data-row-key=ada]').ariaSelected === 'true'")
    assert page.evaluate("Alpine.store('grid').selected") == ["ada"]
    assert errors == []


def test_window_scroll_requests_range_and_reflects_pending(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#windowed")
    viewport = root.locator(':scope > [data-citry-ui-part="viewport"]')

    assert root.locator('[data-citry-ui-part="row"]').count() == 14
    first_row = root.locator('[data-citry-ui-part="row"][data-row-key="audit-20"]')
    assert first_row.get_attribute("aria-rowindex") == "22"
    assert first_row.get_attribute("data-row-index") == "20"

    viewport.evaluate("element => { element.scrollTop = 4000; element.dispatchEvent(new Event('scroll')); }")
    page.wait_for_function("Alpine.store('grid').ranges.some(event => event.reason === 'scroll')")
    event = page.evaluate("Alpine.store('grid').ranges.filter(event => event.reason === 'scroll').at(-1)")
    assert event["endIndex"] > event["startIndex"]
    assert event["requestId"] >= 1
    assert root.get_attribute("data-pending") == ""
    assert root.locator('[data-citry-ui-part="table"]').get_attribute("aria-busy") == "true"
    assert errors == []


def test_shift_space_toggles_and_pointer_drag_selects_enabled_rows(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#grid")
    page.evaluate("Alpine.store('grid').acceptSelection=true; Alpine.store('grid').selected=[]")
    page.wait_for_function("document.querySelectorAll('#grid [data-selected]').length === 0")

    ada_cell = root.locator('[data-row-key="ada"][data-citry-ui-part="cell"]').first
    grace_cell = root.locator('[data-row-key="grace"][data-citry-ui-part="cell"]').first
    locked_cell = root.locator('[data-row-key="locked"][data-citry-ui-part="cell"]').first
    ada_box = ada_cell.bounding_box()
    locked_box = locked_cell.bounding_box()
    assert ada_box is not None
    assert locked_box is not None
    page.mouse.move(ada_box["x"] + 8, ada_box["y"] + ada_box["height"] / 2)
    page.mouse.down()
    page.mouse.move(locked_box["x"] + 8, locked_box["y"] + locked_box["height"] / 2, steps=6)
    page.mouse.up()
    page.wait_for_function("Alpine.store('grid').selected.join(',') === 'ada,grace'")
    assert root.get_attribute("data-selecting") is None
    assert locked_cell.locator("xpath=..").get_attribute("aria-selected") == "false"

    grace_cell.focus()
    page.keyboard.press("Shift+Space")
    page.wait_for_function("Alpine.store('grid').selected.join(',') === 'ada'")
    assert grace_cell.locator("xpath=..").get_attribute("aria-selected") == "false"
    page.keyboard.press("Shift+Space")
    page.wait_for_function("Alpine.store('grid').selected.join(',') === 'ada,grace'")
    assert grace_cell.locator("xpath=..").get_attribute("aria-selected") == "true"
    assert errors == []


def test_inline_editors_commit_cancel_validate_and_keep_rows_authoritative(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#editable")
    name = root.locator('[data-row-key="ada"][data-column-key="name"]')
    name.focus()
    name.press("Enter")
    editor = name.locator('[data-citry-ui-part="editor"]')
    assert editor.get_attribute("type") == "text"
    editor.fill("Aster")
    editor.press("Enter")
    assert name.inner_text() == "Ada"
    assert page.evaluate("Alpine.store('grid').editCommits.at(-1).slice(0,3)") == ["Aster", "ada", "name"]

    role = root.locator('[data-row-key="ada"][data-column-key="role"]')
    role.dblclick()
    role.locator("select").select_option("lead")
    role.locator("select").press("Enter")
    assert page.evaluate("Alpine.store('grid').editCommits.at(-1)[0]") == "lead"

    score = root.locator('[data-row-key="ada"][data-column-key="score"]')
    score.focus()
    score.press("F2")
    score.locator("input").fill("101")
    score.locator("input").press("Enter")
    assert score.locator("input").get_attribute("aria-invalid") == "true"
    score.locator("input").press("Escape")
    assert page.evaluate("Alpine.store('grid').editCancels.at(-1)") == ["ada", "score", "escape"]

    active = root.locator('[data-row-key="ada"][data-column-key="active"]')
    active.focus()
    active.press("Enter")
    active.locator('input[type="checkbox"]').uncheck()
    active.locator('input[type="checkbox"]').press("Enter")
    assert page.evaluate("Alpine.store('grid').editCommits.at(-1)[0]") is False
    assert errors == []


def test_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#grid")
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = root.evaluate(
        """async element => (await axe.run(element, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []

    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    assert root.locator('[data-citry-ui-part="viewport"]').evaluate(
        "element => getComputedStyle(element).overflowX"
    ) in {"auto", "scroll"}

    root.evaluate("element => element.remove()")
    page.wait_for_timeout(50)
    assert errors == []
