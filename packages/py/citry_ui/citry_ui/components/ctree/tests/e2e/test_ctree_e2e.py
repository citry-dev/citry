"""Browser evidence for Tree interaction and accessibility."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Tree browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          .brand-tree {
            --cui-tree-radius: 19px;
            --cui-tree-selected-background: rgb(92 45 145);
            --cui-tree-selected-color: white;
          }
        """
        template = """
          <!doctype html>
          <html lang="en"><head><meta charset="utf-8"><title>Tree evidence</title><c-css /></head>
          <body x-data>
            <form @submit.prevent="$store.tree.submits += 1">
              <c-CTree
                label="Controlled files"
                c-expanded="['src']"
                c-selected="['app']"
                class_="brand-tree"
                variant="outline"
                $c-props="{
                  expanded: $store.tree.expanded,
                  selected: $store.tree.selected,
                  selectionMode: $store.tree.mode,
                  disabled: $store.tree.disabled,
                  onExpandedChange: (next, detail) => {
                    $store.tree.events.push(['expanded', detail.value, detail.expanded, detail.controlled]);
                    if ($store.tree.accept) $store.tree.expanded = next;
                  },
                  onSelectionChange: (next, detail) => {
                    $store.tree.events.push(['selected', detail.value, detail.selected, detail.controlled]);
                    if ($store.tree.accept) $store.tree.selected = next;
                  },
                  onAction: (value) => $store.tree.actions.push(value),
                }"
              >
                <c-CTreeItem value="src" label="Source">
                  <c-CTreeItem value="app" label="App" />
                  <c-CTreeItem value="assets" label="Assets" disabled />
                </c-CTreeItem>
                <c-CTreeItem value="tests" label="Tests">
                  <c-CTreeItem value="unit" label="Unit" />
                </c-CTreeItem>
                <c-CTreeItem value="readme" label="Readme" />
              </c-CTree>
              <button id="submit" type="submit">Submit</button>
            </form>
            <fieldset id="fieldset" disabled>
              <legend>Locked</legend>
              <c-CTree label="Locked Tree">
                <c-CTreeItem value="locked-a" label="A" />
                <c-CTreeItem value="locked-b" label="B" />
              </c-CTree>
            </fieldset>
            <div dir="rtl" style="inline-size:130px">
              <c-CTree label="RTL Tree" variant="soft">
                <c-CTreeItem value="rtl-a" label="عنصرطويلللغاية" />
                <c-CTreeItem value="rtl-b" label="عنصرثانطويلللغاية" />
              </c-CTree>
            </div>
          </body></html>
        """
        js = """
          Alpine.store('tree', {
            expanded: ['src'], selected: ['app'], mode: 'single', disabled: false,
            accept: false, events: [], actions: [], submits: 0,
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector(".brand-tree[data-citry-tree-initialized]")
    return errors


def _item(page: Any, value: str) -> Any:
    return page.locator(f'.brand-tree [role="treeitem"][data-value="{value}"]')


def test_controlled_expansion_selection_action_and_release(page: Any) -> None:
    errors = _load(page)
    source = _item(page, "src")
    source.locator(':scope > [data-citry-ui-part="row"] > [data-citry-ui-part="indicator"]').click()
    assert source.get_attribute("aria-expanded") == "true"
    assert page.evaluate("Alpine.store('tree').events")[-1] == ["expanded", "src", False, True]

    page.evaluate("Alpine.store('tree').accept = true")
    source.locator(':scope > [data-citry-ui-part="row"] > [data-citry-ui-part="indicator"]').click()
    page.wait_for_function(
        "document.querySelector('.brand-tree [data-value=src]').getAttribute('aria-expanded') === 'false'"
    )
    source.locator(':scope > [data-citry-ui-part="row"] > [data-citry-ui-part="indicator"]').click()
    page.wait_for_function(
        "document.querySelector('.brand-tree [data-value=src]').getAttribute('aria-expanded') === 'true'"
    )
    _item(page, "readme").click()
    page.wait_for_function(
        "document.querySelector('.brand-tree [data-value=readme]').getAttribute('aria-selected') === 'true'"
    )
    _item(page, "readme").press("Enter")
    assert page.evaluate("Alpine.store('tree').actions") == ["readme"]
    assert page.evaluate("Alpine.store('tree').submits") == 0

    page.evaluate("Alpine.store('tree').selected = null")
    page.wait_for_timeout(20)
    _item(page, "app").click()
    assert _item(page, "app").get_attribute("aria-selected") == "true"
    assert errors == []


def test_keyboard_navigation_typeahead_collapse_focus_and_disabled(page: Any) -> None:
    errors = _load(page)
    page.evaluate("Alpine.store('tree').accept = true")
    app = _item(page, "app")
    app.focus()
    app.press("ArrowDown")
    assert _item(page, "assets").evaluate("element => document.activeElement === element")
    _item(page, "assets").press(" ")
    assert _item(page, "assets").get_attribute("aria-selected") == "false"
    _item(page, "assets").press("ArrowDown")
    assert _item(page, "tests").evaluate("element => document.activeElement === element")
    _item(page, "tests").press("ArrowRight")
    page.wait_for_function(
        "document.querySelector('.brand-tree [data-value=tests]').getAttribute('aria-expanded') === 'true'"
    )
    _item(page, "tests").press("ArrowRight")
    assert _item(page, "unit").evaluate("element => document.activeElement === element")
    _item(page, "unit").press("ArrowLeft")
    assert _item(page, "tests").evaluate("element => document.activeElement === element")
    _item(page, "tests").press("r")
    assert _item(page, "readme").evaluate("element => document.activeElement === element")
    _item(page, "readme").press("Home")
    assert _item(page, "src").evaluate("element => document.activeElement === element")
    assert errors == []


def test_fieldset_structure_environment_narrow_rtl_and_axe(page: Any) -> None:
    errors = _load(page)
    locked = page.locator('[aria-label="Locked Tree"]')
    assert locked.locator('[role="treeitem"]').nth(0).get_attribute("tabindex") == "-1"
    page.locator("#fieldset").evaluate("element => element.disabled = false")
    page.wait_for_function("document.querySelector('[aria-label=\"Locked Tree\"] [role=treeitem]').tabIndex === 0")

    root = page.locator(".brand-tree")
    root.evaluate("element => element.append(document.createElement('input'))")
    page.wait_for_function("!document.querySelector('.brand-tree').hasAttribute('data-citry-tree-initialized')")
    assert any("CTree structure" in error for error in errors)
    root.locator(":scope > input").evaluate("element => element.remove()")
    page.wait_for_selector(".brand-tree[data-citry-tree-initialized]")

    assert page.locator('[aria-label="RTL Tree"]').evaluate("element => element.scrollWidth <= element.clientWidth")
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "19px"
    page.emulate_media(reduced_motion="reduce")
    assert (
        root.locator('[data-citry-ui-part="indicator"]').first.evaluate(
            "element => parseFloat(getComputedStyle(element).transitionDuration) || 0"
        )
        <= 0.001
    )
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert [error for error in errors if "CTree structure" not in error] == []
