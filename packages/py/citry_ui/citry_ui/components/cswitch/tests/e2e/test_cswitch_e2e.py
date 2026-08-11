from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _switch_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.switch-brand) {
            --cui-switch-on-color: rgb(22 101 52);
            --cui-switch-width: 48px;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body x-data="{checked: true, fixed: false, size: 'md'}">
              <form id="switch-form">
                <c-CSwitch
                  name="night"
                  value="enabled"
                  checked
                  class_="switch-brand"
                  $c-props="{checked, size}"
                  @input="checked = $event.target.checked"
                >Night lighting</c-CSwitch>
                <c-CSwitch
                  name="fixed"
                  value="yes"
                  $c-props="{checked: fixed}"
                >Immutable setting</c-CSwitch>
                <button type="reset">Reset</button>
              </form>
              <c-CField control_id="switch-field" required>
                <c-fill name="label">Watering reminders</c-fill>
                <c-fill name="default"><c-CSwitch name="reminders" /></c-fill>
                <c-fill name="description">Send one reminder before sunrise.</c-fill>
                <c-fill name="error">Enable reminders.</c-fill>
              </c-CField>
              <div dir="rtl"><c-CSwitch checked label_pos="start">إضاءة الحديقة</c-CSwitch></div>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def switch_page(page: Any):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_switch_page(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('.cui-switch')].every(
          root => root.hasAttribute('data-citry-switch-initialized')
        )"""
    )
    return page, errors


def test_switch_exposes_native_role_keyboard_form_and_controlled_state(switch_page):
    page, errors = switch_page
    switch = page.get_by_role("switch", name="Night lighting")
    assert switch.is_checked()
    switch.focus()
    page.keyboard.press("Space")
    assert switch.is_checked() is False
    assert page.evaluate("Array.from(new FormData(document.querySelector('#switch-form')).entries())") == []
    page.evaluate("Alpine.$data(document.body).checked = true")
    page.wait_for_function("document.querySelector('input[name=night]').checked")
    assert switch.is_checked()
    assert switch.evaluate("element => element.getAttribute('aria-checked')") is None
    assert errors == []


def test_immutable_control_reset_field_relationship_and_validity(switch_page):
    page, errors = switch_page
    fixed = page.get_by_role("switch", name="Immutable setting")
    fixed.click()
    page.wait_for_function("!document.querySelector('input[name=fixed]').checked")
    assert fixed.is_checked() is False
    field_switch = page.get_by_role("switch", name="Watering reminders")
    assert field_switch.get_attribute("id") == "switch-field"
    assert field_switch.get_attribute("aria-describedby") == "switch-field-description"
    assert field_switch.evaluate("element => element.checkValidity()") is False
    field_switch.click()
    assert field_switch.evaluate("element => element.checkValidity()") is True
    assert errors == []


def test_switch_css_customization_direction_and_focus(switch_page):
    page, errors = switch_page
    root = page.get_by_role("switch", name="Night lighting").locator("xpath=..")
    track = root.locator('[data-citry-ui-part="track"]')
    assert track.evaluate("element => getComputedStyle(element).width") == "48px"
    assert track.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(22, 101, 52)"
    rtl_switch = page.get_by_role("switch", name="إضاءة الحديقة")
    rtl_thumb = rtl_switch.locator("xpath=following-sibling::*").locator('[data-citry-ui-part="thumb"]')
    assert rtl_thumb.evaluate("element => getComputedStyle(element).transform") != "none"
    page.emulate_media(reduced_motion="reduce")
    assert float(rtl_thumb.evaluate("element => parseFloat(getComputedStyle(element).transitionDuration)")) <= 0.00001
    assert errors == []
