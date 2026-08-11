"""Browser tests for the production Checkbox contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _checkbox_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.checkbox-brand) {
            --cui-checkbox-active-color: rgb(18 112 72);
            --cui-checkbox-radius: 0.6rem;
          }

          :where(.checkbox-part[data-citry-ui-part="checkbox"]) {
            --cui-checkbox-gap: 1.25rem;
          }

          :where(.checkbox-indicator-override) {
            --cui-checkbox-indicator-color: rgb(130 0 130);
          }

          :where(.checkbox-narrow) {
            inline-size: 7.5rem;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('checkboxTest', {
                checked: false,
                mixed: true,
                immutable: false,
                immutableMixed: true,
                requiredChecked: false,
                formDisabled: true,
                events: [],
                clicks: [],
                focuses: [],
              })"
            >
              <c-CCheckbox
                id="controlled-checkbox"
                class_="checkbox-brand checkbox-part"
                indeterminate
                $c-props="{
                  checked: $store.checkboxTest.checked,
                  indeterminate: $store.checkboxTest.mixed,
                }"
                @input="$store.checkboxTest.checked = $event.target.checked; $store.checkboxTest.mixed = false"
              >
                <c-fill name="default">Track fern spores</c-fill>
                <c-fill name="description">Include greenhouse germination notes.</c-fill>
              </c-CCheckbox>

              <c-CCheckbox
                id="immutable-checkbox"
                indeterminate
                $c-props="{
                  checked: $store.checkboxTest.immutable,
                  indeterminate: $store.checkboxTest.immutableMixed,
                }"
                @input="$store.checkboxTest.events.push({
                  type: 'input',
                  checked: $event.target.checked,
                  mixed: $event.target.indeterminate,
                  current: $event.currentTarget.dataset.citryUiPart,
                })"
                @change="$store.checkboxTest.events.push({
                  type: 'change',
                  checked: $event.target.checked,
                  mixed: $event.target.indeterminate,
                  current: $event.currentTarget.dataset.citryUiPart,
                })"
                @click="$store.checkboxTest.clicks.push($event.target.tagName)"
                @focusin="$store.checkboxTest.focuses.push($event.target.tagName)"
              >
                Preserve the immutable specimen
              </c-CCheckbox>

              <c-CForm
                id="garden-form"
                $c-props="{disabled: $store.checkboxTest.formDisabled}"
              >
                <c-CCheckbox
                  id="form-checkbox"
                  name="habitat"
                  value="bog"
                  checked
                  c-disabled="False"
                >
                  Bog habitat
                </c-CCheckbox>
                <c-CCheckbox
                  id="second-form-checkbox"
                  name="habitat"
                  value="woodland"
                  checked
                >
                  Woodland habitat
                </c-CCheckbox>
                <button id="reset-form" type="reset">Reset habitat form</button>
              </c-CForm>

              <c-CField control_id="required-checkbox" required>
                <c-fill name="label">Accept specimen handling rules</c-fill>
                <c-fill name="default">
                  <c-CCheckbox
                    name="rules"
                    $c-props="{checked: $store.checkboxTest.requiredChecked}"
                  />
                </c-fill>
                <c-fill name="description">Required before handling preserved plants.</c-fill>
                <c-fill name="error">Accept the handling rules.</c-fill>
              </c-CField>

              <c-CCheckbox
                id="label-free-checkbox"
                c-input_attrs="{'aria-label': 'Select herbarium row'}"
              />
              <c-CCheckbox id="light-checked" checked>Light checked</c-CCheckbox>
              <c-CCheckbox id="light-mixed" indeterminate>Light mixed</c-CCheckbox>
              <c-CCheckbox
                id="solid-indicator-override"
                class_="checkbox-indicator-override"
                checked
              >
                Solid indicator override
              </c-CCheckbox>
              <c-CCheckbox
                id="outline-indicator-override"
                class_="checkbox-indicator-override"
                variant="outline"
                indeterminate
              >
                Outline indicator override
              </c-CCheckbox>
              <div style="color-scheme: dark">
                <c-CCheckbox id="dark-checked" checked>Dark checked</c-CCheckbox>
                <c-CCheckbox id="dark-mixed" indeterminate>Dark mixed</c-CCheckbox>
              </div>
              <div dir="rtl">
                <c-CCheckbox id="narrow-checkbox" class_="checkbox-narrow">
                  <c-fill name="default">
                    سرخسسرخسسرخسسرخسسرخسسرخسسرخسسرخسسرخسسرخس
                  </c-fill>
                  <c-fill name="description">
                    mossmossmossmossmossmossmossmossmossmossmossmoss
                  </c-fill>
                </c-CCheckbox>
              </div>
              <form id="native-fieldset-form">
                <fieldset id="native-disabled-fieldset" disabled>
                  <legend>Native fieldset</legend>
                  <c-CCheckbox
                    id="native-fieldset-checkbox"
                    name="native-fieldset"
                    value="included"
                    checked
                    c-disabled="False"
                  >
                    Native fieldset choice
                  </c-CCheckbox>
                </fieldset>
              </form>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _checkbox_events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-checkbox-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class SpecimenCheckbox(Component):
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
                return SpecimenCheckbox(step=state.step)

        template = """
          <section data-checkbox-specimen>
            <button class="advance-checkbox" type="button" @c-click="advance">
              Advance
            </button>
            <form id="checkbox-morph-form">
              <c-CCheckbox
                #c-key="'survey-checkbox'"
                id="survey-checkbox"
                name="archived"
                c-checked="server_checked"
                c-indeterminate="server_indeterminate"
              >
                Archive the survey
              </c-CCheckbox>
              <button id="reset-checkbox" type="reset">Reset</button>
            </form>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "server_checked": kwargs.step >= 1,
                "server_indeterminate": kwargs.step == 0,
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-specimen-checkbox />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


@pytest.fixture
def checkbox_page(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_checkbox_page())
    page.wait_for_function(
        """() => {
          const checkboxes = [...document.querySelectorAll('.cui-checkbox')];
          return checkboxes.length === 14
            && checkboxes.every(root => root.hasAttribute('data-citry-checkbox-initialized'));
        }"""
    )
    return page, errors


def test_mixed_state_uses_native_property_and_accessibility_mapping(checkbox_page):
    page, errors = checkbox_page
    native_input = page.locator("#controlled-checkbox")
    root = native_input.locator("xpath=..")

    assert native_input.evaluate("input => input.indeterminate") is True
    assert native_input.get_attribute("aria-checked") is None
    assert root.get_attribute("data-indeterminate") == ""
    client = page.context.new_cdp_session(page)
    nodes = client.send("Accessibility.getFullAXTree")["nodes"]
    checkbox = next(
        node
        for node in nodes
        if node.get("role", {}).get("value") == "checkbox" and node.get("name", {}).get("value") == "Track fern spores"
    )
    checked_property = next(prop for prop in checkbox.get("properties", []) if prop.get("name") == "checked")
    assert checked_property["value"]["value"] == "mixed"
    assert errors == []


def test_label_and_description_are_distinct_accessible_relationships(checkbox_page):
    page, errors = checkbox_page
    native_input = page.locator("#controlled-checkbox")

    assert native_input.get_attribute("aria-describedby") == "controlled-checkbox-description"
    client = page.context.new_cdp_session(page)
    nodes = client.send("Accessibility.getFullAXTree")["nodes"]
    checkbox = next(
        node
        for node in nodes
        if node.get("role", {}).get("value") == "checkbox" and node.get("name", {}).get("value") == "Track fern spores"
    )
    assert checkbox["description"]["value"] == "Include greenhouse germination notes."
    assert errors == []


def test_native_handlers_see_browser_state_before_controlled_restoration(checkbox_page):
    page, errors = checkbox_page
    label = page.get_by_text("Preserve the immutable specimen", exact=True)
    native_input = page.locator("#immutable-checkbox")

    label.click()
    page.wait_for_timeout(30)
    events: list[dict[str, Any]] = page.evaluate("Alpine.store('checkboxTest').events")
    clicks: list[str] = page.evaluate("Alpine.store('checkboxTest').clicks")

    assert events == [
        {"type": "input", "checked": True, "mixed": False, "current": "checkbox"},
        {"type": "change", "checked": True, "mixed": False, "current": "checkbox"},
    ]
    assert clicks == ["LABEL", "INPUT"]
    assert native_input.is_checked() is False
    assert native_input.evaluate("input => input.indeterminate") is True
    assert errors == []


def test_controlled_mirroring_accepts_native_state_without_redundant_reversal(checkbox_page):
    page, errors = checkbox_page
    native_input = page.locator("#controlled-checkbox")

    page.get_by_text("Track fern spores", exact=True).click()
    page.wait_for_timeout(30)

    assert native_input.is_checked() is True
    assert native_input.evaluate("input => input.indeterminate") is False
    assert page.evaluate("Alpine.store('checkboxTest').checked") is True
    assert page.evaluate("Alpine.store('checkboxTest').mixed") is False
    assert native_input.locator("xpath=..").get_attribute("data-checked") == ""
    assert native_input.locator("xpath=..").get_attribute("data-indeterminate") is None
    assert errors == []


def test_form_disabled_dominates_local_false_and_reset_restores_checkedness(checkbox_page):
    page, errors = checkbox_page
    first = page.locator("#form-checkbox")
    second = page.locator("#second-form-checkbox")

    assert first.is_disabled()
    assert first.evaluate("element => getComputedStyle(element).cursor") == "not-allowed"
    assert (
        page.get_by_text("Bog habitat", exact=True).evaluate("element => getComputedStyle(element).cursor")
        == "not-allowed"
    )
    page.evaluate("Alpine.store('checkboxTest').formDisabled = false")
    page.wait_for_timeout(0)
    assert first.is_enabled()
    first.uncheck()
    assert first.is_checked() is False
    data = page.locator("#garden-form").evaluate(
        "form => Array.from(new FormData(form).entries())",
    )
    assert data == [["habitat", "woodland"]]
    page.locator("#reset-form").click()
    page.wait_for_timeout(20)
    assert first.is_checked()
    assert second.is_checked()
    assert errors == []


def test_controlled_required_invalid_episode_uses_final_reconciled_state(checkbox_page):
    page, errors = checkbox_page
    native_input = page.locator("#required-checkbox")
    field = native_input.locator("xpath=../../..")

    assert native_input.evaluate("input => input.reportValidity()") is False
    assert field.get_attribute("data-invalid") == ""
    native_input.click(force=True)
    page.wait_for_timeout(30)
    assert native_input.is_checked() is False
    assert field.get_attribute("data-invalid") == ""

    page.evaluate("Alpine.store('checkboxTest').requiredChecked = true")
    page.wait_for_timeout(0)
    assert native_input.is_checked()
    assert field.get_attribute("data-invalid") is None
    assert errors == []


def test_public_css_variables_and_selector_override_compute(checkbox_page):
    page, errors = checkbox_page
    root = page.locator("#controlled-checkbox").locator("xpath=..")
    native_input = page.locator("#controlled-checkbox")

    assert root.evaluate("root => getComputedStyle(root).gap") == "20px"
    assert native_input.evaluate("input => getComputedStyle(input).borderRadius") == "9.6px"
    assert errors == []


def test_default_indicator_contrast_covers_checked_and_mixed_in_both_schemes(checkbox_page):
    page, errors = checkbox_page
    page.wait_for_timeout(150)

    ratios = page.locator("#light-checked, #light-mixed, #dark-checked, #dark-mixed").evaluate_all(
        r"""elements => {
          const luminance = color => {
            const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number);
            const linear = channels.map(channel => {
              const value = channel / 255;
              return value <= 0.04045
                ? value / 12.92
                : ((value + 0.055) / 1.055) ** 2.4;
            });
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
          };
          return elements.map(element => {
            const style = getComputedStyle(element);
            const foreground = luminance(style.color);
            const background = luminance(style.backgroundColor);
            return (Math.max(foreground, background) + 0.05)
              / (Math.min(foreground, background) + 0.05);
          });
        }"""
    )

    assert all(ratio >= 3 for ratio in ratios)
    assert errors == []


def test_indicator_color_override_applies_to_solid_and_outline_states(checkbox_page):
    page, errors = checkbox_page

    for element_id in ("solid-indicator-override", "outline-indicator-override"):
        assert (
            page.locator(f"#{element_id}").evaluate("element => getComputedStyle(element).color") == "rgb(130, 0, 130)"
        )
    assert errors == []


def test_long_unbroken_label_and_description_wrap_in_narrow_rtl_layout(checkbox_page):
    page, errors = checkbox_page
    root = page.locator("#narrow-checkbox").locator("xpath=..")

    assert root.evaluate("element => element.scrollWidth <= element.clientWidth") is True
    for part in ("label", "description"):
        surface = root.locator(f'[data-citry-ui-part="{part}"]')
        assert surface.evaluate("element => getComputedStyle(element).overflowWrap") == "anywhere"
        assert surface.evaluate("element => element.scrollWidth <= element.clientWidth") is True
    assert errors == []


def test_native_fieldset_disabledness_drives_mirror_style_and_form_success(checkbox_page):
    page, errors = checkbox_page
    fieldset = page.locator("#native-disabled-fieldset")
    native_input = page.locator("#native-fieldset-checkbox")
    root = native_input.locator("xpath=..")
    label = page.get_by_text("Native fieldset choice", exact=True)

    assert native_input.evaluate("element => element.disabled") is False
    assert native_input.evaluate("element => element.matches(':disabled')") is True
    assert root.get_attribute("data-disabled") == ""
    assert label.evaluate("element => getComputedStyle(element).cursor") == "not-allowed"
    assert page.locator("#native-fieldset-form").evaluate("form => Array.from(new FormData(form).entries())") == []

    fieldset.evaluate("element => element.removeAttribute('disabled')")
    page.wait_for_function(
        "!document.querySelector('#native-fieldset-checkbox').parentElement.hasAttribute('data-disabled')"
    )
    assert native_input.evaluate("element => element.matches(':disabled')") is False
    assert label.evaluate("element => getComputedStyle(element).cursor") == "pointer"
    assert page.locator("#native-fieldset-form").evaluate("form => Array.from(new FormData(form).entries())") == [
        ["native-fieldset", "included"]
    ]

    fieldset.evaluate("element => element.setAttribute('disabled', '')")
    page.wait_for_function(
        "document.querySelector('#native-fieldset-checkbox').parentElement.hasAttribute('data-disabled')"
    )
    assert errors == []


def test_label_free_name_and_focus_boundary(checkbox_page):
    page, errors = checkbox_page
    assert page.get_by_role("checkbox", name="Select herbarium row").count() == 1

    page.locator("#immutable-checkbox").focus()
    assert page.evaluate("Alpine.store('checkboxTest').focuses") == ["INPUT"]
    assert errors == []


def test_correlated_morph_preserves_current_state_and_updates_reset_default(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _checkbox_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function(
        "document.querySelector('#survey-checkbox')?.parentElement.hasAttribute('data-citry-checkbox-initialized')"
    )
    checkbox = page.locator("#survey-checkbox")

    checkbox.check()
    page.evaluate("window.__checkboxRoot = document.querySelector('#survey-checkbox').parentElement")
    page.evaluate("() => Citry.events.send(document.querySelector('.advance-checkbox'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-checkbox').defaultChecked === true")
    assert checkbox.is_checked()
    assert checkbox.evaluate("element => element.indeterminate") is False
    assert page.evaluate("document.querySelector('#survey-checkbox').parentElement === window.__checkboxRoot") is True

    checkbox.uncheck()
    checkbox.evaluate("element => { element.indeterminate = true; }")
    page.evaluate("() => Citry.events.send(document.querySelector('.advance-checkbox'), 'advance', {})")
    page.wait_for_function(
        "document.querySelector('#survey-checkbox').parentElement.hasAttribute('data-citry-checkbox-initialized')"
    )
    assert checkbox.is_checked() is False
    assert checkbox.evaluate("element => element.indeterminate") is True

    page.locator("#reset-checkbox").click()
    page.wait_for_timeout(20)
    assert checkbox.is_checked()
    assert checkbox.evaluate("element => element.indeterminate") is True
