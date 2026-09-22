"""Browser evidence for Select interaction, forms, and overlays."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui import CSelectOption

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate the repository root for Select browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        js = """
          $component({data(){const select=Citry.vue.reactive({
            value:'earth',open:undefined,disabled:false,readonly:false,loop:false,
            variant:'outline',size:'md',accept:false,acceptOpen:false,
            values:[],opens:[],submits:[],
          }); window.__select=select; return {state:{select}};}});
        """
        css = ".primary-select { inline-size: 18rem; }"
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8"><title>Select evidence</title><c-css /></head>
          <body>
            <form
              id="planet-form"
              @submit.prevent="state.select.submits = Array.from(new window.FormData($event.target).entries())"
            >
              <c-CSelect
                class_="primary-select"
                c-options="options"
                placeholder="Choose a planet"
                name="planet"
                value="earth"
                required
                c-trigger_attrs="{'aria-label': 'Planet'}"
                :value="state.select.value"
                :open="state.select.open"
                :disabled="state.select.disabled"
                :readonly="state.select.readonly"
                :loop="state.select.loop"
                :variant="state.select.variant"
                :size="state.select.size"
                :onValueChange="(next, detail) => {
                    state.select.values.push([next, detail.previousValue, detail.source, detail.controlled]);
                    if (state.select.accept) state.select.value = next;
                  }"
                :onOpenChange="(next, detail) => {
                    state.select.opens.push([next, detail.reason, detail.controlled, detail.forced]);
                    if (state.select.acceptOpen) state.select.open = next;
                  }"
              />
              <button id="submit" type="submit">Submit</button>
              <button id="reset" type="reset">Reset</button>
            </form>

            <fieldset id="locked" disabled>
              <legend>Locked</legend>
              <c-CSelect
                class_="locked-select"
                c-options="options"
                placeholder="Choose"
                c-trigger_attrs="{'aria-label': 'Locked planet'}"
              />
            </fieldset>

            <dialog id="modal"><button autofocus type="button">Modal action</button></dialog>
          </body></html>
        """

        def template_data(self, kwargs, slots):
            return {
                "options": [
                    CSelectOption("earth", "Earth"),
                    CSelectOption("mars", "Mars", "The red planet", group="Rocky"),
                    CSelectOption("venus", "Venus", disabled=True, group="Rocky"),
                    CSelectOption("jupiter", "Jupiter", group="Gas giants"),
                ]
            }

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector(".primary-select[data-citry-select-initialized]")
    return errors


def _control(page: Any) -> Any:
    return page.locator('.primary-select [role="combobox"]')


def _vue_provider_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <main>
            <c-CForm id="select-provider-form" :disabled="formDisabled" :readonly="formReadonly">
              <c-CSelect
                class_="provider-select"
                name="planet"
                placeholder="Choose a planet"
                c-options="options"
                :value="value"
                :readonly="false"
                :onValueChange="acceptValue"
                c-trigger_attrs="{'aria-label': 'Planet'}"
              />
            </c-CForm>
            <button id="toggle-select-form-disabled" @click="formDisabled = !formDisabled">disabled</button>
          </main>
        """
        js = """$component({data(){return {formDisabled:false,formReadonly:true,value:'earth'};},
          methods:{acceptValue(next){this.value=next;}}});"""

        def template_data(self, kwargs, slots):
            return {
                "options": [
                    CSelectOption("earth", "Earth"),
                    CSelectOption("mars", "Mars"),
                ]
            }

    return Page().render().serialize()


def test_vue_native_form_select_provider_keyboard_and_override(page: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_vue_provider_page(), wait_until="load")
    page.wait_for_selector(".provider-select[data-citry-select-initialized]")
    root = page.locator(".provider-select")
    control = root.get_by_role("combobox")
    assert root.get_attribute("data-readonly") is None
    control.focus()
    control.press("ArrowDown")
    page.wait_for_selector('.provider-select [role="option"][data-highlighted]')
    control.press("ArrowDown")
    control.press("Enter")
    assert root.locator("select[data-cui-select-native]").input_value() == "mars"

    page.locator("#toggle-select-form-disabled").click()
    assert root.get_attribute("data-disabled") == ""
    assert control.is_disabled()
    assert errors == []


def _option(page: Any, value: str) -> Any:
    return page.locator(f'.primary-select [role="option"][data-value="{value}"]')


def test_controlled_value_and_open_reject_accept_release(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    control.click()
    assert control.get_attribute("aria-expanded") == "true"
    _option(page, "mars").click()
    assert control.locator('[data-citry-ui-part="value"]').text_content().strip() == "Earth"
    assert page.evaluate("window.__select.values.at(-1)") == ["mars", "earth", "pointer", True]

    page.evaluate("window.__select.accept = true")
    control.click()
    _option(page, "mars").click()
    page.wait_for_function("document.querySelector('.primary-select select').value === 'mars'")
    assert control.locator('[data-citry-ui-part="value"]').text_content().strip() == "Mars"

    page.evaluate("window.__select.value = undefined")
    control.click()
    _option(page, "jupiter").click()
    assert control.locator('[data-citry-ui-part="value"]').text_content().strip() == "Jupiter"

    page.evaluate("window.__select.open = false")
    control.click()
    assert control.get_attribute("aria-expanded") == "false"
    assert page.evaluate("window.__select.opens.at(-1).slice(0,3)") == [True, "trigger", True]
    page.evaluate("window.__select.acceptOpen = true")
    control.click()
    page.wait_for_function("document.querySelector('.primary-select [role=combobox]').ariaExpanded === 'true'")
    assert errors == []


def test_keyboard_typeahead_disabled_options_and_tab_exit(page: Any, browser_name: str) -> None:
    errors = _load(page)
    control = _control(page)
    page.evaluate("window.__select.value = null")
    page.wait_for_function("document.querySelector('.primary-select select').value === ''")
    page.evaluate("window.__select.value = undefined")
    page.wait_for_timeout(20)
    control.focus()
    control.press("ArrowUp")
    assert control.get_attribute("aria-expanded") == "true"
    assert control.get_attribute("aria-activedescendant") == _option(page, "jupiter").get_attribute("id")
    control.press("Home")
    control.press("ArrowDown")
    assert control.get_attribute("aria-activedescendant") == _option(page, "mars").get_attribute("id")
    control.press("ArrowDown")
    assert control.get_attribute("aria-activedescendant") == _option(page, "jupiter").get_attribute("id")
    control.press("m")
    assert control.get_attribute("aria-activedescendant") == _option(page, "mars").get_attribute("id")
    control.press("Enter")
    assert control.locator('[data-citry-ui-part="value"]').text_content().strip() == "Mars"
    control.press("ArrowDown")
    control.press("Tab")
    page.wait_for_function("document.querySelector('.primary-select [role=combobox]').ariaExpanded === 'false'")
    if browser_name != "webkit":
        assert page.evaluate("document.activeElement.id") == "submit"
    assert errors == []


def test_native_form_reset_validation_readonly_fieldset_and_modal_safety(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    page.evaluate("window.__select.value = undefined")
    control.click()
    _option(page, "mars").click()
    page.locator("#submit").click()
    assert page.evaluate("window.__select.submits") == [["planet", "mars"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('.primary-select select').value === 'earth'")

    page.evaluate("window.__select.readonly = true")
    control.click()
    assert control.get_attribute("aria-expanded") == "false"
    page.locator("#submit").click()
    assert page.evaluate("window.__select.submits") == [["planet", "earth"]]

    locked = page.locator('.locked-select [role="combobox"]')
    assert locked.is_disabled()
    page.locator("#locked").evaluate("element => element.disabled = false")
    page.wait_for_function("!document.querySelector('.locked-select [role=combobox]').disabled")
    locked.click()
    assert locked.get_attribute("aria-expanded") == "true"

    page.evaluate("window.__select.readonly = false")
    control.click()
    page.locator("#modal").evaluate("element => element.showModal()")
    page.wait_for_function("document.querySelector('.primary-select [role=combobox]').ariaExpanded === 'false'")
    assert page.evaluate("window.__select.opens.at(-1).slice(1)") == ["ancestor", False, True]
    assert errors == []


def test_css_environment_geometry_and_axe(page: Any) -> None:
    errors = _load(page)
    control = _control(page)
    control.click()
    popup = page.locator('.primary-select [data-citry-ui-part="popup"]')
    page.wait_for_timeout(150)
    assert abs(popup.bounding_box()["width"] - control.bounding_box()["width"]) < 1.5
    page.emulate_media(reduced_motion="reduce")
    assert (
        popup.evaluate(
            "element => parseFloat(getComputedStyle(element).getPropertyValue('--_cui-select-duration')) || 0"
        )
        == 0
    )
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []
    assert errors == []
