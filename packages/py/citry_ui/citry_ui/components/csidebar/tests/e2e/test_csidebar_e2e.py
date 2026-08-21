"""Browser evidence for Sidebar state, focus, direction, and localization."""

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
    raise RuntimeError("Could not locate repository root for Sidebar browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Sidebar evidence</title><c-css /></head>
          <body x-data>
            <form>
              <c-CSidebar id="rail" tag="nav" label="Rail navigation" class_="brand-sidebar">
                <a id="rail-link" href="#rail-destination">Destination</a>
              </c-CSidebar>
              <button id="form-submit" type="submit">Submit</button>
            </form>
            <c-CSidebar id="offcanvas" label="Tools" collapsible="offcanvas"
              $c-props="{collapsed:$store.sidebar.collapsed,onCollapsedChange:(next,detail)=>{$store.sidebar.events.push([next,detail.previousCollapsed,detail.controlled]);if($store.sidebar.accept)$store.sidebar.collapsed=next}}">
              <a id="tool-link" href="#tool">Tool</a>
            </c-CSidebar>
            <div dir="rtl">
              <c-CSidebar id="rtl" label="RTL tools" side="inline-end" collapsible="none">
                أدوات
              </c-CSidebar>
            </div>
          </body></html>
        """
        css = ".brand-sidebar { --cui-sidebar-width: 18rem; --cui-sidebar-radius: 19px; }"
        js = """
          Alpine.store('sidebar', {collapsed:false,accept:false,events:[]});
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#rail[data-citry-sidebar-initialized]")
    page.wait_for_selector("#offcanvas[data-citry-sidebar-initialized]")
    return errors


def test_uncontrolled_rail_toggle_is_form_safe_and_preserves_panel(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#rail")
    toggle = root.locator('[data-citry-ui-part="toggle"]')
    toggle.click()

    assert root.get_attribute("data-collapsed") == ""
    assert toggle.get_attribute("aria-expanded") == "false"
    assert root.locator('[data-citry-ui-part="panel"]').is_visible()
    assert page.url.endswith("#") is False
    page.wait_for_function("getComputedStyle(document.querySelector('#rail')).width === '64px'")
    assert root.evaluate("element => getComputedStyle(element).width") == "64px"
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "0px"
    assert errors == []


def test_controlled_offcanvas_request_acceptance_and_focus_repair(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#offcanvas")
    toggle = root.locator('[data-citry-ui-part="toggle"]')
    link = page.locator("#tool-link")

    toggle.click()
    assert root.get_attribute("data-collapsed") is None
    assert page.evaluate("Alpine.store('sidebar').events") == [[True, False, True]]

    page.evaluate("Alpine.store('sidebar').accept = true")
    link.focus()
    toggle.evaluate("element => element.click()")
    page.wait_for_function("document.querySelector('#offcanvas').hasAttribute('data-collapsed')")
    assert root.locator('[data-citry-ui-part="panel"]').is_hidden()
    assert toggle.get_attribute("aria-expanded") == "false"
    assert toggle.evaluate("element => document.activeElement === element")
    assert page.evaluate("Alpine.store('sidebar').events")[-1] == [True, False, True]
    assert errors == []


def test_landmarks_logical_side_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    assert page.locator("nav[aria-label='Rail navigation']").count() == 1
    assert page.locator("aside[aria-label='Tools']").count() == 1
    rtl = page.locator("#rtl")
    assert rtl.evaluate("element => getComputedStyle(element).borderInlineStartWidth") == "1px"
    assert rtl.evaluate("element => getComputedStyle(element).borderInlineEndWidth") == "0px"

    page.emulate_media(reduced_motion="reduce")
    assert rtl.evaluate("element => parseFloat(getComputedStyle(element).transitionDuration)") <= 0.001
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
