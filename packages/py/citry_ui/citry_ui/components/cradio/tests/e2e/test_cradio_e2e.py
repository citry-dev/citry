"""Browser evidence for the production Radio contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _radio_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.radio-brand) {
            --cui-radio-active-color: rgb(88 28 135);
            --cui-radio-control-size: 24px;
            --cui-radio-group-gap: 18px;
          }

          :where(.radio-part [data-citry-ui-part="label"]) {
            letter-spacing: 2px;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body
              x-data
              x-init="Alpine.store('radioTest', {
                value: 'moon',
                immutable: 'moon',
                orientation: 'vertical',
                variant: 'solid',
                size: 'md',
              })"
            >
              <form id="mission-form">
                <c-CRadioGroup
                  name="destination"
                  value="moon"
                  required
                  class_="radio-brand radio-part"
                  $c-props="{
                    value: $store.radioTest.value,
                    orientation: $store.radioTest.orientation,
                    variant: $store.radioTest.variant,
                    size: $store.radioTest.size,
                  }"
                  @input="$store.radioTest.value = $event.target.value"
                >
                  <c-fill name="label">Destination</c-fill>
                  <c-fill name="default">
                    <c-CRadio value="moon">Moon</c-CRadio>
                    <c-CRadio value="mars">
                      <c-fill name="default">Mars</c-fill>
                      <c-fill name="description">A longer transfer window.</c-fill>
                    </c-CRadio>
                    <c-CRadio value="europa" disabled>Europa</c-CRadio>
                  </c-fill>
                </c-CRadioGroup>

                <c-CRadioGroup
                  name="immutable"
                  value="moon"
                  $c-props="{value: $store.radioTest.immutable}"
                >
                  <c-fill name="label">Immutable destination</c-fill>
                  <c-fill name="default">
                    <c-CRadio value="moon">Moon</c-CRadio>
                    <c-CRadio value="mars">Mars</c-CRadio>
                  </c-fill>
                </c-CRadioGroup>
                <button id="reset-mission" type="reset">Reset</button>
              </form>

              <c-CField control_id="signal-band" required>
                <c-fill name="label">Signal band</c-fill>
                <c-fill name="default">
                  <c-CRadioGroup name="signal">
                    <c-CRadio value="x">X band</c-CRadio>
                    <c-CRadio value="ka">Ka band</c-CRadio>
                  </c-CRadioGroup>
                </c-fill>
                <c-fill name="description">Choose one downlink band.</c-fill>
                <c-fill name="error">Choose a signal band.</c-fill>
              </c-CField>
              <div dir="rtl">
                <c-CRadioGroup name="rtl" value="east" orientation="horizontal" label_pos="start">
                  <c-fill name="label">اتجاه الهوائي</c-fill>
                  <c-fill name="default">
                    <c-CRadio value="east">شرق</c-CRadio>
                    <c-CRadio value="west">غرب</c-CRadio>
                  </c-fill>
                </c-CRadioGroup>
              </div>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def radio_page(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_radio_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const groups = [...document.querySelectorAll('.cui-radio-group')];
          return groups.length === 4
            && groups.every(root => root.hasAttribute('data-citry-radio-group-initialized'));
        }"""
    )
    return page, errors


def test_native_group_labels_form_data_and_keyboard_selection(radio_page):
    page, errors = radio_page
    group = page.get_by_role("group", name="Destination", exact=True)
    moon = group.get_by_role("radio", name="Moon")
    mars = group.get_by_role("radio", name="Mars")
    europa = group.get_by_role("radio", name="Europa")

    assert moon.is_checked()
    assert europa.is_disabled()
    moon.focus()
    page.keyboard.press("ArrowDown")
    assert mars.is_checked()
    assert group.get_attribute("data-value") == "mars"
    assert page.evaluate("Array.from(new FormData(document.querySelector('#mission-form')).entries())") == [
        ["destination", "mars"],
        ["immutable", "moon"],
    ]
    assert errors == []


def test_controlled_radio_restores_after_native_input_and_reset(radio_page):
    page, errors = radio_page
    immutable = page.get_by_role("group", name="Immutable destination")
    mars = immutable.get_by_role("radio", name="Mars")
    moon = immutable.get_by_role("radio", name="Moon")

    mars.click()
    page.wait_for_function("document.querySelector('input[name=immutable][value=moon]').checked")
    assert moon.is_checked()
    page.evaluate("Alpine.store('radioTest').value = 'mars'")
    page.wait_for_timeout(0)
    selected = page.get_by_role("group", name="Destination", exact=True)
    assert selected.get_by_role("radio", name="Mars").is_checked()
    page.locator("#reset-mission").click()
    page.wait_for_function("document.querySelector('input[name=destination][value=mars]').checked")
    assert selected.get_by_role("radio", name="Mars").is_checked()
    assert errors == []


def test_field_relationship_and_native_required_validation(radio_page):
    page, errors = radio_page
    field = page.locator('[data-citry-ui-part="field"]')
    group = field.locator('[data-citry-ui-part="radio-group"]')
    radios = group.get_by_role("radio")

    assert group.get_attribute("aria-labelledby") == "signal-band-label"
    assert group.get_attribute("aria-describedby") == "signal-band-description"
    assert group.get_attribute("data-citry-field-control") == ""
    assert group.get_attribute("id") == "signal-band-group"
    assert radios.first.get_attribute("id") == "signal-band"
    assert field.locator(':scope > [data-citry-ui-part="label"]').get_attribute("for") == "signal-band"
    assert radios.first.get_attribute("required") == ""
    assert radios.first.evaluate("element => element.checkValidity()") is False
    radios.nth(1).click()
    assert radios.first.evaluate("element => element.checkValidity()") is True
    assert errors == []


def test_client_configuration_invalid_episode_css_and_direction(radio_page):
    page, errors = radio_page
    group = page.get_by_role("group", name="Destination", exact=True)

    page.evaluate(
        """() => Object.assign(Alpine.store('radioTest'), {
          orientation: 'horizontal',
          variant: 'outline',
          size: 'lg',
        })"""
    )
    page.wait_for_timeout(0)
    assert group.get_attribute("data-orientation") == "horizontal"
    assert group.get_attribute("data-variant") == "outline"
    assert group.get_attribute("data-size") == "lg"
    assert group.evaluate("element => getComputedStyle(element).gap") == "18px"
    assert group.get_by_role("radio", name="Moon").evaluate("element => getComputedStyle(element).width") == "24px"
    assert (
        group.locator('[data-citry-ui-part="label"]').first.evaluate(
            "element => getComputedStyle(element).letterSpacing"
        )
        == "2px"
    )

    page.evaluate("Alpine.store('radioTest').value = 'venus'")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('radioTest').value = 42")
    page.wait_for_timeout(0)
    assert sum("CRadioGroup value received invalid client value" in error for error in errors) == 1

    rtl = page.get_by_role("group", name="اتجاه الهوائي")
    assert rtl.evaluate("element => getComputedStyle(element).direction") == "rtl"
    page.emulate_media(forced_colors="active")
    assert rtl.get_by_role("radio").first.evaluate("element => getComputedStyle(element).borderTopStyle") == "solid"
