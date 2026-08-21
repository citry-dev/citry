"""Browser evidence for Tour modality, navigation, geometry, and cleanup."""

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
    raise RuntimeError("Could not locate repository root for Tour browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Tour evidence</title><c-css /></head>
          <body x-data>
            <button id="target" type="button">Target action</button>
            <c-CTour id="guide">
              <c-fill name="activator" data="{ activator_attrs }">
                <button id="start" c-bind="activator_attrs">Start tour</button>
              </c-fill>
              <c-fill name="default">
                <c-CTourStep value="intro" c-describe="True">
                  <c-fill name="title">Introduction</c-fill>
                  <c-fill name="default">Centered modal introduction.</c-fill>
                </c-CTourStep>
                <c-CTourStep value="target" target_id="target" placement="bottom-end">
                  <c-fill name="title">Target step</c-fill>
                  <c-fill name="default">Target-aware explanation.</c-fill>
                </c-CTourStep>
                <c-CTourStep value="missing" target_id="not-rendered">
                  <c-fill name="title">Missing</c-fill>
                  <c-fill name="default">This step is skipped.</c-fill>
                </c-CTourStep>
                <c-CTourStep value="finish">
                  <c-fill name="title">Finish step</c-fill>
                  <c-fill name="default">Finish and restore focus.</c-fill>
                </c-CTourStep>
              </c-fill>
            </c-CTour>

            <c-CTour
              id="controlled"
              missing_target="close"
              $c-props="{
                open:$store.tour.open,
                active:$store.tour.active,
                onOpenChange:(next,detail)=>{$store.tour.openEvents.push([next,detail.reason,detail.controlled]);if($store.tour.acceptOpen)$store.tour.open=next},
                onActiveChange:(next,detail)=>{$store.tour.activeEvents.push([next,detail.reason,detail.controlled]);if($store.tour.acceptActive)$store.tour.active=next},
              }"
            >
              <c-fill name="activator" data="{ activator_attrs }">
                <button id="controlled-start" c-bind="activator_attrs">Controlled tour</button>
              </c-fill>
              <c-fill name="default">
                <c-CTourStep value="one">
                  <c-fill name="title">Controlled one</c-fill>
                  <c-fill name="default">One.</c-fill>
                </c-CTourStep>
                <c-CTourStep value="two">
                  <c-fill name="title">Controlled two</c-fill>
                  <c-fill name="default">Two.</c-fill>
                </c-CTourStep>
              </c-fill>
            </c-CTour>
          </body></html>
        """
        js = """
          Alpine.store('tour', {
            open:false, active:0, acceptOpen:false, acceptActive:false, openEvents:[], activeEvents:[],
          });
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#guide[data-citry-tour-initialized]")
    page.wait_for_selector("#controlled[data-citry-tour-initialized]")
    return errors


def test_uncontrolled_navigation_target_geometry_skip_and_focus_restore(page: Any) -> None:
    errors = _load(page)
    start = page.locator("#start")
    guide = page.locator("#guide")
    dialog = guide.locator("dialog")

    start.click()
    page.wait_for_function("document.querySelector('#guide dialog').matches(':modal')")
    assert guide.get_attribute("data-active") == "0"
    assert guide.get_attribute("data-value") == "intro"
    assert dialog.get_attribute("aria-describedby") == "guide-description-0"
    assert page.locator("#guide-title-0").evaluate("element => document.activeElement === element")

    guide.locator('[data-citry-tour-action="next"]:visible').click()
    page.wait_for_function("document.querySelector('#guide').dataset.active === '1'")
    page.wait_for_selector("#guide[data-targeted]")
    assert guide.get_attribute("data-value") == "target"
    assert guide.get_attribute("data-targeted") == ""
    assert guide.locator('[data-citry-ui-part="spotlight"]').is_visible()
    assert page.locator("#guide-title-1").evaluate("element => document.activeElement === element")
    surface = guide.locator('[data-citry-ui-part="surface"]')
    target = page.locator("#target")
    surface_box = surface.bounding_box()
    target_box = target.bounding_box()
    assert surface_box is not None
    assert target_box is not None
    assert 0 <= surface_box["x"] <= page.viewport_size["width"] - surface_box["width"]
    assert surface.get_attribute("data-placement") in {"top-start", "bottom-start", "top-end", "bottom-end"}

    guide.locator('[data-citry-tour-action="next"]:visible').click()
    page.wait_for_function("document.querySelector('#guide').dataset.active === '3'")
    assert guide.get_attribute("data-value") == "finish"
    assert page.locator("#guide-title-3").evaluate("element => document.activeElement === element")
    guide.locator('[data-citry-tour-action="finish"]:visible').click()
    page.wait_for_function("!document.querySelector('#guide dialog').open")
    assert start.evaluate("element => document.activeElement === element")
    assert errors == []


def test_controlled_open_and_active_requests_wait_for_acceptance(page: Any) -> None:
    errors = _load(page)
    controlled = page.locator("#controlled")
    page.locator("#controlled-start").click()

    assert controlled.locator("dialog").get_attribute("open") is None
    assert page.evaluate("Alpine.store('tour').openEvents") == [[True, "activator", True]]
    page.evaluate("Alpine.store('tour').acceptOpen = true; Alpine.store('tour').open = true")
    page.wait_for_function("document.querySelector('#controlled dialog').matches(':modal')")

    controlled.locator('[data-citry-tour-action="next"]:visible').click()
    assert controlled.get_attribute("data-active") == "0"
    assert page.evaluate("Alpine.store('tour').activeEvents") == [[1, "next", True]]
    page.evaluate("Alpine.store('tour').acceptActive = true; Alpine.store('tour').active = 1")
    page.wait_for_function("document.querySelector('#controlled').dataset.active === '1'")
    assert controlled.get_attribute("data-value") == "two"
    assert errors == []


def test_escape_shift_tab_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    page.locator("#start").click()
    page.wait_for_function("document.querySelector('#guide dialog').matches(':modal')")
    title = page.locator("#guide-title-0")
    title.focus()
    page.keyboard.press("Shift+Tab")
    assert page.locator('#guide [data-citry-tour-action="next"]:visible').evaluate(
        "element => document.activeElement === element"
    )
    page.keyboard.press("Escape")
    page.wait_for_function("!document.querySelector('#guide dialog').open")

    page.emulate_media(reduced_motion="reduce")
    duration = page.locator('#guide [data-citry-ui-part="surface"]').evaluate(
        "element => getComputedStyle(element).transitionDuration"
    )
    assert duration in {"0s", "0ms"}
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []

    page.locator("#guide").evaluate("element => element.remove()")
    page.wait_for_timeout(50)
    assert page.evaluate("document.documentElement.style.overflow") == ""
    assert errors == []
