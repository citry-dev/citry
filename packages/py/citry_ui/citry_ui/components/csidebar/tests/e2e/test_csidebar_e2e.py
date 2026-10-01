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
          <body>
            <form>
              <c-CSidebar id="rail" tag="nav" label="Rail navigation" class_="brand-sidebar">
                <c-fill name="header"><strong>Northstar</strong></c-fill>
                <c-fill name="default">
                  <a id="rail-link" href="#rail-destination">Destination</a>
                  <p id="rail-copy">A deliberately long authored explanation inside the narrow rail.</p>
                </c-fill>
              </c-CSidebar>
              <button id="form-submit" type="submit">Submit</button>
            </form>
            <c-CSidebar id="offcanvas" label="Tools" collapsible="offcanvas"
              :collapsed="collapsed"
              :on-collapsed-change="(next,detail)=>{events.push([next,detail.previousCollapsed,detail.controlled]);if(accept)collapsed=next}">
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
        js = """$component({
          data(){return {collapsed:false,accept:false,events:[]}},
          mounted(){globalThis.sidebarEvidence=this},
          unmounted(){if(globalThis.sidebarEvidence===this)delete globalThis.sidebarEvidence},
        })"""

    return str(Page())


def _revision_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-sidebar-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class RevisionSidebar(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return RevisionSidebar(step=state.step)

        template = """
          <section>
            <button id="advance-sidebar" type="button" @c-click="advance">Advance</button>
            <output id="sidebar-step">{{ step }}</output>
            <c-CSidebar
              #c-key="'revision-sidebar'"
              id="revision-sidebar"
              label="Revision navigation"
              c-collapsed="server_collapsed"
            >Revision content</c-CSidebar>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {"step": kwargs.step, "server_collapsed": kwargs.step >= 2}

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><c-css /></head>
          <body><c-revision-sidebar /><c-js /></body></html>
        """

    return app, str(Page())


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
    panel = root.locator('[data-citry-ui-part="panel"]')
    header = root.locator('[data-citry-ui-part="header"]')
    toggle_box = toggle.bounding_box()
    header_box = header.bounding_box()
    assert toggle_box is not None
    assert header_box is not None
    assert abs((toggle_box["y"] + toggle_box["height"] / 2) - (header_box["y"] + header_box["height"] / 2)) < 1
    toggle.click()

    assert root.get_attribute("data-collapsed") == ""
    assert root.get_attribute("data-citry-sidebar-transitioning") == ""
    assert toggle.get_attribute("aria-expanded") == "false"
    assert panel.is_visible()
    assert panel.evaluate("element => getComputedStyle(element).width") == "288px"
    assert root.evaluate("element => getComputedStyle(element).overflowX") in {"hidden", "clip"}
    assert page.url.endswith("#") is False
    page.wait_for_function("!document.querySelector('#rail').hasAttribute('data-citry-sidebar-transitioning')")
    assert root.evaluate("element => getComputedStyle(element).width") == "64px"
    assert panel.evaluate("element => getComputedStyle(element).width") == "64px"
    assert root.evaluate("element => getComputedStyle(element).overflowX") == "visible"
    assert page.locator("#rail-copy").evaluate("element => getComputedStyle(element).whiteSpace") == "nowrap"
    assert root.evaluate("element => element.scrollHeight") < 800
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "0px"
    assert errors == []


def test_controlled_offcanvas_request_acceptance_and_focus_repair(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#offcanvas")
    toggle = root.locator('[data-citry-ui-part="toggle"]')
    link = page.locator("#tool-link")

    toggle.click()
    assert root.get_attribute("data-collapsed") is None
    assert page.evaluate("sidebarEvidence.events") == [[True, False, True]]

    page.evaluate("sidebarEvidence.accept = true")
    link.focus()
    toggle.evaluate("element => element.click()")
    page.wait_for_function("document.querySelector('#offcanvas').hasAttribute('data-collapsed')")
    assert root.locator('[data-citry-ui-part="panel"]').is_hidden()
    assert toggle.get_attribute("aria-expanded") == "false"
    assert toggle.evaluate("element => document.activeElement === element")
    assert page.evaluate("sidebarEvidence.events")[-1] == [True, False, True]

    page.evaluate("sidebarEvidence.collapsed = false")
    page.wait_for_function("!document.querySelector('#offcanvas').hasAttribute('data-collapsed')")
    page.evaluate("sidebarEvidence.collapsed = undefined")
    toggle.click()
    assert root.get_attribute("data-collapsed") == ""
    assert page.evaluate("sidebarEvidence.events.at(-1)") == [True, False, False]
    assert errors == []


def test_landmarks_logical_side_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    assert page.locator("nav[aria-label='Rail navigation']").count() == 1
    assert page.locator("aside[aria-label='Tools']").count() == 1
    rtl = page.locator("#rtl")
    assert rtl.evaluate("element => getComputedStyle(element).borderInlineStartWidth") == "1px"
    assert rtl.evaluate("element => getComputedStyle(element).borderInlineEndWidth") == "0px"
    assert page.evaluate("document.documentElement.scrollHeight") < 1600

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


def test_correlated_revision_preserves_local_state_until_server_baseline_changes(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _revision_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    root = page.locator("#revision-sidebar")
    toggle = root.locator('[data-citry-ui-part="toggle"]')
    page.wait_for_function(
        "document.querySelector('#revision-sidebar')?.hasAttribute('data-citry-sidebar-initialized')"
    )

    toggle.click()
    assert root.get_attribute("data-collapsed") == ""
    page.evaluate("window.__sidebarRevisionRoot = document.querySelector('#revision-sidebar')")

    page.locator("#advance-sidebar").click()
    page.wait_for_function("document.querySelector('#sidebar-step')?.textContent.trim() === '1'")
    assert page.evaluate("document.querySelector('#revision-sidebar') === window.__sidebarRevisionRoot") is True
    assert root.get_attribute("data-collapsed") == ""

    toggle.click()
    assert root.get_attribute("data-collapsed") is None
    page.locator("#advance-sidebar").click()
    page.wait_for_function("document.querySelector('#sidebar-step')?.textContent.trim() === '2'")
    page.wait_for_function("document.querySelector('#revision-sidebar')?.getAttribute('data-collapsed') === ''")
    assert root.get_attribute("data-collapsed") == ""
    assert root.get_attribute("data-collapsed") == ""
