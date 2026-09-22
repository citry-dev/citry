"""Browser tests for the production Native Select contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui import CNativeSelectGroup, CNativeSelectOption

pytestmark = pytest.mark.e2e


def _vue_native_select_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        js = """
          $component({data(){const nativeSelectDemo=Citry.vue.reactive({
            value:'reef',immutable:'reef',nullValue:null,standaloneRequired:true,
            standaloneVariant:'outline',unsupportedRequired:false,variant:'outline',size:'md',
          }); window.__nativeSelectDemo=nativeSelectDemo; return {
            state:{nativeSelectDemo}, value:'reef', required:false, invalid:false,
            formDisabled:false,
          };}});
        """
        template = """
          <main>
            <c-CForm id="vue-native-select-form" :disabled="formDisabled">
              <c-CField control_id="vue-native-select" :required="required" :invalid="invalid">
                <c-fill name="label">Habitat</c-fill>
                <c-fill name="default">
                  <c-CNativeSelect
                    c-options="options"
                    placeholder="Choose"
                    :value="value"
                    @input="value = $event.target.value"
                  />
                </c-fill>
                <c-fill name="error">Choose a habitat.</c-fill>
              </c-CField>
            </c-CForm>
            <button id="native-select-required" @click="required = !required">required</button>
            <button id="native-select-invalid" @click="invalid = !invalid">invalid</button>
            <button id="native-select-disabled" @click="formDisabled = !formDisabled">disabled</button>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {
                "options": [
                    CNativeSelectOption("reef", "{{ 1 + 1 }} <b>Reef</b>"),
                    CNativeSelectOption("kelp", "Kelp"),
                ]
            }

    return Page().render().serialize()


def test_vue_native_select_provider_input_focus_and_validation(page: Any) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_vue_native_select_page(), wait_until="load")
    select = page.locator("#vue-native-select")
    page.wait_for_selector("#vue-native-select[data-citry-native-select-initialized]")
    assert select.locator('option[value="reef"]').text_content() == "{{ 1 + 1 }} <b>Reef</b>"
    assert select.locator("option b").count() == 0
    select.focus()
    select.select_option("kelp")
    assert select.input_value() == "kelp"
    assert select.evaluate("element => document.activeElement === element") is True
    page.locator("#native-select-required").click()
    assert select.evaluate("element => element.required") is True
    page.locator("#native-select-invalid").click()
    assert select.get_attribute("aria-invalid") == "true"
    page.locator("#native-select-disabled").click()
    assert select.is_disabled()
    assert errors == []


def _native_select_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        js = """
          $component({data(){const nativeSelectDemo=Citry.vue.reactive({
            value:'reef',immutable:'reef',nullValue:null,standaloneRequired:true,
            standaloneVariant:'outline',unsupportedRequired:false,variant:'outline',size:'md',
          }); window.__nativeSelectDemo=nativeSelectDemo; return {state:{nativeSelectDemo}};}});
        """
        css = """
          :where(.select-brand) {
            --cui-native-select-background: rgb(232 248 248);
            --cui-native-select-foreground: rgb(13 73 77);
            --cui-native-select-radius: 1rem;
          }

          :where(.select-part[data-citry-ui-part="native-select"]) {
            border-width: 5px;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-CForm id="survey-form">
                <c-CField
                  control_id="habitat-select"
                  required
                >
                  <c-fill name="label">Habitat</c-fill>
                  <c-fill name="default">
                    <c-CNativeSelect
                      name="habitat"
                      c-options="options"
                      placeholder="Choose a habitat"
                      value="reef"
                      class_="select-brand select-part"
                      c-attrs="{
                        'ARIA-DESCRIBEDBY': 'external-help',
                        'FORM': 'survey-form',
                      }"
                      :value="state.nativeSelectDemo.value"
                      :variant="state.nativeSelectDemo.variant"
                      :size="state.nativeSelectDemo.size"
                      @input="state.nativeSelectDemo.value = $event.target.value"
                    />
                  </c-fill>
                  <c-fill name="description">Choose one marine habitat.</c-fill>
                  <c-fill name="error">Choose a habitat.</c-fill>
                </c-CField>
                <c-CField
                  control_id="invalid-controlled"
                  required
                >
                  <c-fill name="label">Required controlled habitat</c-fill>
                  <c-fill name="default">
                    <c-CNativeSelect
                      c-options="options"
                      placeholder="Choose"
                      :value="state.nativeSelectDemo.immutable"
                    />
                  </c-fill>
                  <c-fill name="error">Required.</c-fill>
                </c-CField>
                <c-CField
                  control_id="unsupported-required"
                  :required="state.nativeSelectDemo.unsupportedRequired"
                >
                  <c-fill name="label">Optional research zone</c-fill>
                  <c-fill name="default">
                    <c-CNativeSelect c-options="flat_options" />
                  </c-fill>
                </c-CField>
                <c-CNativeSelect
                  id="null-controlled"
                  c-options="flat_options"
                  :value="state.nativeSelectDemo.nullValue"
                  :required="state.nativeSelectDemo.standaloneRequired"
                  :variant="state.nativeSelectDemo.standaloneVariant"
                  c-attrs="{'aria-label': 'Nullable zone'}"
                />
                <button id="reset-survey" type="reset">Reset</button>
              </c-CForm>
              <div id="external-help">External guidance.</div>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "options": [
                    CNativeSelectOption("reef", "Coral reef"),
                    CNativeSelectGroup(
                        "Open ocean",
                        [
                            CNativeSelectOption("pelagic", "Pelagic"),
                            CNativeSelectOption("abyss", "Abyss", disabled=True),
                        ],
                    ),
                    CNativeSelectGroup(
                        "Protected",
                        [CNativeSelectOption("nursery", "Nursery")],
                        disabled=True,
                    ),
                ],
                "flat_options": [
                    CNativeSelectOption("reef", "Coral reef"),
                    CNativeSelectOption("pelagic", "Pelagic"),
                ],
            }

    return str(Page())


def _native_select_events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-native-select-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class SurveySelect(Component):
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
                return SurveySelect(step=state.step)

        template = """
          <section data-native-select-survey>
            <button class="advance-select" type="button" @c-click="advance">
              Advance
            </button>
            <c-CNativeSelect
              #c-key="'survey-native-select'"
              id="survey-native-select"
              c-options="options"
              c-value="server_value"
              c-attrs="{'aria-label': 'Survey habitat'}"
            />
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            reef = CNativeSelectOption("reef", "Coral reef")
            kelp = CNativeSelectOption("kelp", "Kelp forest")
            pelagic = CNativeSelectOption("pelagic", "Pelagic zone")
            options = (
                (reef, kelp, pelagic)
                if kwargs.step == 0
                else (
                    CNativeSelectGroup("Offshore", (pelagic, reef)),
                    kelp,
                )
                if kwargs.step == 1
                else (pelagic, reef)
            )
            return {
                "options": options,
                "server_value": "reef" if kwargs.step == 0 else "pelagic",
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
              <c-survey-select />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _load(page) -> None:
    page.set_content(_native_select_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const controls = [...document.querySelectorAll('.cui-native-select')];
          return controls.length === 4
            && controls.every((control) =>
              control.hasAttribute('data-citry-native-select-initialized'));
        }"""
    )


def test_native_root_options_forms_and_field_relationships(page):
    _load(page)
    select = page.locator("#habitat-select")

    assert select.evaluate("element => element.tagName") == "SELECT"
    assert select.locator("option").count() == 5
    assert select.locator("optgroup").count() == 2
    assert select.input_value() == "reef"
    assert select.evaluate("element => element.required") is True
    assert select.get_attribute("aria-describedby") == "habitat-select-description external-help"
    assert select.locator('option[value="abyss"]').is_disabled()
    assert select.locator('optgroup[label="Protected"]').is_disabled()
    assert page.evaluate("[...new FormData(document.querySelector('#survey-form'))]") == [["habitat", "reef"]]


def test_native_event_mirror_handles_placeholder_empty_string_and_controlled_changes(page):
    _load(page)
    select = page.locator("#habitat-select")

    select.select_option("")
    page.wait_for_function("window.__nativeSelectDemo.value === ''")
    assert select.input_value() == ""
    assert select.get_attribute("data-empty") == ""
    assert select.evaluate("element => element.validity.valueMissing") is True

    select.select_option("pelagic")
    page.wait_for_function("window.__nativeSelectDemo.value === 'pelagic'")
    assert select.input_value() == "pelagic"
    assert select.get_attribute("data-empty") is None


def test_immutable_control_restores_and_null_without_placeholder_means_no_selection(page):
    _load(page)
    immutable = page.locator("#invalid-controlled")
    nullable = page.locator("#null-controlled")

    immutable.select_option("pelagic")
    page.wait_for_function("document.querySelector('#invalid-controlled').value === 'reef'")

    assert nullable.evaluate("element => element.selectedIndex") == -1
    nullable.evaluate(
        """element => {
          element.value = 'reef';
          element.dispatchEvent(new Event('input', {bubbles: true}));
        }"""
    )
    page.wait_for_function("document.querySelector('#null-controlled').selectedIndex === -1")


def test_unsupported_dynamic_required_keeps_field_and_native_state_coherent(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)
    field = page.locator("#unsupported-required-field")
    select = page.locator("#unsupported-required")

    page.evaluate("window.__nativeSelectDemo.unsupportedRequired = true")
    page.wait_for_timeout(0)

    assert select.evaluate("element => element.required") is False
    assert field.get_attribute("data-required") is None
    assert len([message for message in errors if "CField required=true is not supported" in message]) == 1


def test_unsupported_standalone_required_reports_once_across_unrelated_updates(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)
    select = page.locator("#null-controlled")

    assert select.evaluate("element => element.required") is False
    page.evaluate("window.__nativeSelectDemo.standaloneVariant = 'filled'")
    page.wait_for_function("document.querySelector('#null-controlled').dataset.variant === 'filled'")
    page.evaluate("window.__nativeSelectDemo.standaloneVariant = 'plain'")
    page.wait_for_function("document.querySelector('#null-controlled').dataset.variant === 'plain'")

    assert len([message for message in errors if "required=true requires a placeholder" in message]) == 1


def test_controlled_native_invalid_episode_clears_only_after_final_value_settles(page):
    _load(page)
    select = page.locator("#invalid-controlled")
    field = page.locator("#invalid-controlled-field")

    page.evaluate("window.__nativeSelectDemo.immutable = ''")
    page.wait_for_function("document.querySelector('#invalid-controlled').value === ''")
    select.evaluate("element => element.dispatchEvent(new Event('invalid', {bubbles: false}))")
    assert field.get_attribute("data-invalid") == ""

    select.select_option("pelagic")
    page.wait_for_function("document.querySelector('#invalid-controlled').value === ''")
    assert field.get_attribute("data-invalid") == ""

    page.evaluate("window.__nativeSelectDemo.immutable = 'pelagic'")
    page.wait_for_function("document.querySelector('#invalid-controlled').value === 'pelagic'")
    assert field.get_attribute("data-invalid") is None


@pytest.mark.parametrize("cancel_second", [True, False], ids=["uncanceled-then-canceled", "canceled-then-uncanceled"])
def test_each_reset_event_keeps_its_own_deferred_outcome(page, cancel_second):
    _load(page)
    page.evaluate(
        """cancelSecond => {
          const form = document.querySelector('#survey-form');
          const select = document.querySelector('#habitat-select');
          let count = 0;
          form.addEventListener('reset', event => {
            count += 1;
            if ((cancelSecond && count === 2) || (!cancelSecond && count === 1)) {
              event.preventDefault();
            }
          });
          select.value = 'pelagic';
          form.dispatchEvent(new Event('reset', {cancelable: true}));
          form.dispatchEvent(new Event('reset', {cancelable: true}));
        }""",
        cancel_second,
    )
    page.wait_for_function("document.querySelector('#habitat-select').value === 'reef'")


def test_client_presentation_and_public_css_overrides(page):
    _load(page)
    select = page.locator("#habitat-select")

    assert select.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(232, 248, 248)"
    assert select.evaluate("element => getComputedStyle(element).color") == "rgb(13, 73, 77)"
    assert select.evaluate("element => getComputedStyle(element).borderRadius") == "16px"
    assert select.evaluate("element => getComputedStyle(element).borderTopWidth") == "5px"

    page.evaluate(
        """() => Object.assign(window.__nativeSelectDemo, {
          variant: 'filled',
          size: 'lg',
        })"""
    )
    page.wait_for_function(
        """() => {
          const select = document.querySelector('#habitat-select');
          return select.dataset.variant === 'filled' && select.dataset.size === 'lg';
        }"""
    )
    assert select.evaluate("element => getComputedStyle(element).fontSize") == "17px"


def test_correlated_morph_preserves_semantic_selection_then_uses_structural_fallback(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _native_select_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_selector("#survey-native-select[data-citry-native-select-initialized]")
    select = page.locator("#survey-native-select")

    select.select_option("kelp")
    page.evaluate("window.__nativeSelectRoot = document.querySelector('#survey-native-select')")
    page.evaluate("() => Citry.events.send(document.querySelector('.advance-select'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-native-select').value === 'kelp'")
    assert page.evaluate("document.querySelector('#survey-native-select') === window.__nativeSelectRoot") is True

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-select'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-native-select').value === 'pelagic'")
    assert select.locator('option[value="kelp"]').count() == 0


def test_correlated_morph_preserves_a_selected_option_when_it_moves_into_a_group(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _native_select_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_selector("#survey-native-select[data-citry-native-select-initialized]")

    page.evaluate("() => Citry.events.send(document.querySelector('.advance-select'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-native-select').value === 'reef'")
    assert (
        page.locator('#survey-native-select option[value="reef"]').evaluate("element => element.parentElement.label")
        == "Offshore"
    )


def test_correlated_morph_preserves_semantic_no_selection(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _native_select_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_selector("#survey-native-select[data-citry-native-select-initialized]")

    page.evaluate("document.querySelector('#survey-native-select').selectedIndex = -1")
    page.evaluate("() => Citry.events.send(document.querySelector('.advance-select'), 'advance', {})")
    page.wait_for_function("document.querySelector('#survey-native-select').selectedIndex === -1")
