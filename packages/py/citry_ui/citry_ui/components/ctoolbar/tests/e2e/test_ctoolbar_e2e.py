"""Browser evidence for Toolbar roving focus and composition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Toolbar browser tests.")


def _toolbar_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>Toolbar contract</title>
              <style>
                .toolbar-theme {
                  --cui-toolbar-gap: 13px;
                  --cui-toolbar-radius: 17px;
                }
              </style>
              <c-css />
            </head>
            <body x-data="{fieldsetDisabled: false}">
              <button id="before" type="button">Before</button>
              <c-CToolbar
                label="Editor tools"
                variant="soft"
                class_="toolbar-theme"
                c-attrs="{'id': 'editor'}"
                $c-props="{orientation: $store.toolbar.orientation, loop: $store.toolbar.loop}"
              >
                <c-CButton c-attrs="{'id': 'bold'}" @keydown.stop="window.__childKeydown = true">
                  Bold
                </c-CButton>
                <c-CToggle c-attrs="{'id': 'italic'}">Italic</c-CToggle>
                <c-CButtonGroup label="Clipboard">
                  <c-CButton c-attrs="{'id': 'copy'}">Copy</c-CButton>
                  <c-CButton c-attrs="{'id': 'paste'}" c-disabled="True">Paste</c-CButton>
                </c-CButtonGroup>
                <c-CDivider orientation="vertical" decorative />
                <a id="docs" href="#docs">Docs</a>
              </c-CToolbar>

              <div dir="rtl">
                <c-CToolbar label="RTL tools" c-attrs="{'id': 'rtl'}">
                  <button type="button">One</button>
                  <button type="button">Two</button>
                  <button type="button">Three</button>
                </c-CToolbar>
              </div>

              <c-CToolbar
                label="Vertical tools"
                orientation="vertical"
                c-loop="False"
                variant="outline"
                size="lg"
                c-attrs="{'id': 'vertical'}"
              >
                <button type="button">North</button>
                <button type="button">Center</button>
                <button type="button">South</button>
              </c-CToolbar>

              <fieldset id="fieldset" x-bind:disabled="fieldsetDisabled">
                <legend>Fieldset tools</legend>
                <c-CToolbar label="Fieldset tools" c-attrs="{'id': 'fieldset-toolbar'}">
                  <button type="button">First</button>
                  <button type="button">Second</button>
                  <button type="button">Third</button>
                </c-CToolbar>
              </fieldset>
              <button id="after" type="button">After</button>
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {}

        def js_data(self, kwargs, slots):
            return {}

        js = """
          Alpine.store('toolbar', {orientation: 'horizontal', loop: true});
        """

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_toolbar_page(), wait_until="load")
    page.wait_for_selector("#editor[data-citry-toolbar-initialized]")
    page.wait_for_selector("#vertical[data-citry-toolbar-initialized]")
    return errors


def _focused_text(page: Any) -> str:
    return page.evaluate("document.activeElement.textContent.trim()")


def test_horizontal_roving_focus_capture_and_reactive_configuration(page: Any) -> None:
    errors = _load(page)
    editor = page.locator("#editor")
    assert editor.locator('[tabindex="0"]').count() == 1
    assert editor.locator('[tabindex="-1"]').count() == 4

    page.locator("#before").focus()
    page.keyboard.press("Tab")
    assert _focused_text(page) == "Bold"
    page.keyboard.press("ArrowRight")
    assert _focused_text(page) == "Italic"
    assert page.evaluate("window.__childKeydown") is True
    page.keyboard.press("End")
    assert _focused_text(page) == "Docs"
    page.keyboard.press("ArrowRight")
    assert _focused_text(page) == "Bold"

    page.evaluate("Object.assign(Alpine.store('toolbar'), {orientation: 'vertical', loop: false})")
    page.wait_for_function("document.querySelector('#editor').dataset.orientation === 'vertical'")
    assert editor.get_attribute("aria-orientation") == "vertical"
    assert editor.get_attribute("data-loop") is None
    page.keyboard.press("ArrowUp")
    assert _focused_text(page) == "Bold"
    assert errors == []


def test_rtl_vertical_boundaries_and_disabled_controls(page: Any) -> None:
    errors = _load(page)
    rtl = page.locator("#rtl")
    rtl.get_by_role("button", name="One").focus()
    page.keyboard.press("ArrowLeft")
    assert _focused_text(page) == "Two"
    page.keyboard.press("ArrowRight")
    assert _focused_text(page) == "One"

    vertical = page.locator("#vertical")
    vertical.get_by_role("button", name="North").focus()
    page.keyboard.press("ArrowUp")
    assert _focused_text(page) == "North"
    page.keyboard.press("ArrowDown")
    assert _focused_text(page) == "Center"
    page.keyboard.press("End")
    assert _focused_text(page) == "South"

    page.locator("#copy").focus()
    page.locator("#copy").evaluate("element => element.disabled = true")
    page.wait_for_function("document.activeElement.id === 'docs'")
    assert page.locator("#paste").get_attribute("tabindex") == "-1"
    assert errors == []


def test_native_fieldset_css_environment_and_axe(page: Any) -> None:
    errors = _load(page)
    toolbar = page.locator("#fieldset-toolbar")
    toolbar.get_by_role("button", name="Second").focus()
    page.evaluate("Alpine.$data(document.body).fieldsetDisabled = true")
    page.wait_for_function("document.querySelectorAll('#fieldset-toolbar [tabindex=\"0\"]').length === 0")
    assert toolbar.locator('[tabindex="-1"]').count() == 3
    page.evaluate("Alpine.$data(document.body).fieldsetDisabled = false")
    page.wait_for_function("document.querySelectorAll('#fieldset-toolbar [tabindex=\"0\"]').length === 1")

    editor = page.locator("#editor")
    assert editor.evaluate("element => getComputedStyle(element).gap") == "13px"
    assert editor.evaluate("element => getComputedStyle(element).borderRadius") == "17px"
    assert page.locator("#vertical").evaluate("element => getComputedStyle(element).flexDirection") == "column"
    page.emulate_media(reduced_motion="reduce")
    assert editor.evaluate("element => getComputedStyle(element).scrollBehavior") == "auto"

    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file()
    page.add_script_tag(path=str(axe_path))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes: ['violations']})).violations
          .filter((item) => ['serious', 'critical'].includes(item.impact))
          .map((item) => item.id)"""
    )
    assert violations == []
    assert errors == []


def test_invalid_structure_fails_closed_and_recovers(page: Any) -> None:
    errors = _load(page)
    editor = page.locator("#editor")
    editor.evaluate("element => element.append(Object.assign(document.createElement('input'), {id: 'bad'}))")
    page.wait_for_function("!document.querySelector('#editor').hasAttribute('data-citry-toolbar-initialized')")
    assert any("CToolbar structure" in error for error in errors)
    page.locator("#bad").evaluate("element => element.remove()")
    page.wait_for_selector("#editor[data-citry-toolbar-initialized]")
    assert editor.locator('[tabindex="0"]').count() == 1
