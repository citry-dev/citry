"""Browser evidence for Tree Grid hierarchy, selection, navigation, and cleanup."""

# ruff: noqa: E501 - embedded templates and browser expressions remain readable

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")
import citry_ui
from citry import Citry, Component
from citry_ui import CTreeGridColumn, CTreeGridRow

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Tree Grid browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {
                "columns": [CTreeGridColumn("name", "Name", 240), CTreeGridColumn("owner", "Owner")],
                "rows": [
                    CTreeGridRow(
                        "root",
                        "Root",
                        {"name": "Root", "owner": "Ada"},
                        children=[
                            CTreeGridRow("first", "First child", {"name": "First child", "owner": "Mira"}),
                            CTreeGridRow("second", "Second child", {"name": "Second child", "owner": "Noah"}),
                        ],
                    ),
                    CTreeGridRow("locked", "Locked", {"name": "Locked", "owner": "Ivy"}, disabled=True),
                ],
            }

        template = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Tree Grid evidence</title><c-css /></head><body x-data><form><c-CTreeGrid id="grid" c-columns="columns" c-rows="rows" label="Work" c-expanded="['root']" selection="multiple" c-selected="['first']" name="chosen" $c-props="{onExpandedChange:(value,detail)=>$store.t.expanded.push([value,detail.source]),onSelectionChange:(value,detail)=>$store.t.selected.push([value,detail.rowSelected]),onCellActivate:detail=>$store.t.activated.push(detail.columnKey)}" /></form></body></html>"""
        js = "Alpine.store('t',{expanded:[],selected:[],activated:[]});"

    return str(Page())


def _load(page: Any) -> list[str]:
    errors = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#grid[data-citry-tree-grid-initialized]")
    return errors


def test_expand_select_unselect_and_form_output(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#grid")
    root.locator('[data-citry-tree-grid-row][data-row-key="root"] [data-citry-tree-grid-expander]').click()
    assert root.locator('[data-citry-tree-grid-row][data-row-key="first"]').is_hidden()
    root.locator('[data-citry-tree-grid-row][data-row-key="root"] [data-citry-tree-grid-expander]').click()
    cell = root.locator('[data-citry-tree-grid-row][data-row-key="first"] [data-citry-ui-part="cell"]').first
    cell.focus()
    cell.press("Shift+Space")
    assert page.evaluate("Alpine.store('t').selected.at(-1)") == [[], False]
    assert root.locator('input[name="chosen"]').count() == 0
    cell.press("Shift+Space")
    assert page.evaluate("Alpine.store('t').selected.at(-1)") == [["first"], True]
    assert root.locator('input[name="chosen"]').get_attribute("value") == "first"
    assert errors == []


def test_cell_navigation_activation_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#grid")
    first = root.locator('[data-citry-tree-grid-row][data-row-key="root"] [data-citry-ui-part="cell"]').first
    first.focus()
    first.press("ArrowDown")
    assert page.evaluate("document.activeElement.closest('[data-citry-tree-grid-row]').dataset.rowKey") == "first"
    page.keyboard.press("ArrowRight")
    assert page.evaluate("document.activeElement.dataset.columnKey") == "owner"
    page.keyboard.press("Enter")
    assert page.evaluate("Alpine.store('t').activated") == ["owner"]
    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    page.add_script_tag(path=str(_root() / "node_modules" / "axe-core" / "axe.min.js"))
    violations = page.evaluate(
        """async()=> (await axe.run(document,{resultTypes:['violations']})).violations.filter(x=>['serious','critical'].includes(x.impact)).map(x=>x.id)"""
    )
    assert violations == []
    root.evaluate("element=>element.remove()")
    page.wait_for_timeout(30)
    assert errors == []
