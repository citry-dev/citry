"""Browser tests for CForm, CField, and CInput."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui.quality.routes import render_scenario

pytestmark = pytest.mark.e2e


def _form_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.form-brand) {
            --cui-field-label-color: rgb(18 52 86);
            --cui-input-background: rgb(21 43 65);
            --cui-input-foreground: rgb(245 246 247);
            --cui-input-placeholder-color: rgb(203 213 225);
            --cui-input-radius: 1rem;
          }

          :where(.form-brand [data-citry-ui-part="error"]) {
            font-weight: 700;
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
              x-init="Alpine.store('formDemo', {
                controlled: true,
                controlledValue: 'owner@example.com',
                formDisabled: false,
                formReadonly: false,
                submitting: false,
                fieldRequired: true,
                fieldInvalid: false,
                inputRequired: undefined,
                variant: 'outline',
              })"
            >
              <section
                class="form-brand"
                style="color-scheme: dark"
              >
                <c-CForm
                  id="profile-form"
                  action="/profiles"
                  method="post"
                  c-attrs="form_attrs"
                  $c-props="{
                    disabled: $store.formDemo.formDisabled,
                    readonly: $store.formDemo.formReadonly,
                    submitting: $store.formDemo.submitting,
                  }"
                >
                  <c-CField
                    control_id="email-control"
                    $c-props="{
                      required: $store.formDemo.fieldRequired,
                      invalid: $store.formDemo.fieldInvalid,
                    }"
                  >
                    <c-fill name="label">
                      Work email
                    </c-fill>
                    <c-fill name="default">
                      <c-CInput
                        name="profile.email"
                        type="email"
                        value="server@example.com"
                        autocomplete="email"
                        placeholder="name@example.com"
                        c-attrs="email_attrs"
                        $c-props="{
                          value: $store.formDemo.controlled
                            ? $store.formDemo.controlledValue
                            : undefined,
                          required: $store.formDemo.inputRequired,
                          variant: $store.formDemo.variant,
                        }"
                      />
                      <span
                        hidden
                        data-nested-error
                        data-citry-ui-part="error"
                      >
                        Nested control error
                      </span>
                    </c-fill>
                    <c-fill name="description">
                      Used for account notifications.
                    </c-fill>
                    <c-fill name="error">
                      Enter a valid email address.
                    </c-fill>
                  </c-CField>
                  <c-CField
                    required
                    c-attrs="extra_field_attrs"
                  >
                    <c-fill name="label">
                      Approval code
                    </c-fill>
                    <c-fill name="default">
                      <c-CInput
                        name="profile.approval_code"
                        c-attrs="extra_attrs"
                      />
                    </c-fill>
                  </c-CField>
                </c-CForm>
              </section>
              <button
                id="toggle-disabled"
                type="button"
                @click="$store.formDemo.formDisabled = !$store.formDemo.formDisabled"
              >
                Toggle disabled
              </button>
              <button
                id="toggle-readonly"
                type="button"
                @click="$store.formDemo.formReadonly = !$store.formDemo.formReadonly"
              >
                Toggle readonly
              </button>
              <button
                id="toggle-required"
                type="button"
                @click="$store.formDemo.fieldRequired = !$store.formDemo.fieldRequired"
              >
                Toggle required
              </button>
              <button
                id="toggle-invalid"
                type="button"
                @click="$store.formDemo.fieldInvalid = !$store.formDemo.fieldInvalid"
              >
                Toggle invalid
              </button>
              <button
                id="toggle-submitting"
                type="button"
                @click="$store.formDemo.submitting = !$store.formDemo.submitting"
              >
                Toggle submitting
              </button>
              <button
                id="release-control"
                type="button"
                @click="$store.formDemo.controlled = false"
              >
                Release control
              </button>
              <button
                id="set-controlled"
                type="button"
                @click="
                  $store.formDemo.controlledValue = 'next@example.com';
                  $store.formDemo.controlled = true;
                "
              >
                Set controlled value
              </button>
              <button
                id="set-invalid-props"
                type="button"
                @click="$store.formDemo.variant = 'raised'"
              >
                Set invalid props
              </button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "form_attrs": {
                    "data-workflow": "profile",
                },
                "email_attrs": {
                    "data-probe": "email",
                },
                "extra_field_attrs": {
                    "data-extra-field": "",
                },
                "extra_attrs": {
                    "data-probe": "approval-code",
                },
            }

    return str(Page())


def _load(page) -> None:
    page.set_content(_form_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const form = document.querySelector('#profile-form');
          const inputs = document.querySelectorAll('.cui-input');
          return form?.hasAttribute('data-citry-form-initialized')
            && inputs.length === 2
            && [...inputs].every((input) => input.hasAttribute('data-citry-input-initialized'));
        }"""
    )


def test_native_relationships_form_configuration_and_theme_are_preserved(page):
    _load(page)
    form = page.locator("#profile-form")
    field = page.locator("#email-control-field")
    input_value = page.locator("#email-control")

    assert form.get_attribute("method") == "post"
    assert form.get_attribute("action") == "/profiles"
    assert form.get_attribute("data-workflow") == "profile"
    assert input_value.get_attribute("name") == "profile.email"
    assert input_value.get_attribute("aria-describedby") == "email-control-description"
    assert page.locator('label[for="email-control"]').count() == 1
    assert field.get_attribute("data-required") == ""
    assert input_value.get_attribute("data-required") == ""
    assert input_value.input_value() == "owner@example.com"
    assert input_value.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(21, 43, 65)"
    assert (
        page.locator('[data-citry-ui-part="label"]').first.evaluate("element => getComputedStyle(element).color")
        == "rgb(18, 52, 86)"
    )
    assert input_value.evaluate("element => getComputedStyle(element).borderRadius") == "16px"
    assert input_value.evaluate("element => getComputedStyle(element, '::placeholder').color") == "rgb(203, 213, 225)"


def test_reactive_form_and_field_configuration_inherits_into_native_input(page):
    _load(page)
    input_value = page.locator("#email-control")
    field = page.locator("#email-control-field")

    page.locator("#toggle-disabled").click()
    page.wait_for_function("document.querySelector('#email-control').disabled")
    assert page.locator("#profile-form fieldset").evaluate("element => element.disabled") is True
    assert field.get_attribute("data-disabled") == ""
    assert field.evaluate("element => getComputedStyle(element).opacity") == "1"

    page.locator("#toggle-disabled").click()
    page.locator("#toggle-readonly").click()
    page.wait_for_function("document.querySelector('#email-control').readOnly")
    assert field.get_attribute("data-readonly") == ""

    page.locator("#toggle-required").click()
    page.wait_for_function("!document.querySelector('#email-control').required")
    assert field.get_attribute("data-required") is None
    assert input_value.get_attribute("data-required") is None


def test_native_validation_updates_field_error_and_form_aggregate_state(page):
    _load(page)
    input_value = page.locator("#email-control")
    error = page.locator("#email-control-error")

    page.locator("#release-control").click()
    input_value.fill("not-an-email")
    assert page.evaluate("document.querySelector('#email-control').reportValidity()") is False
    page.wait_for_function("document.querySelector('#email-control-field').hasAttribute('data-invalid')")
    assert input_value.get_attribute("aria-invalid") == "true"
    assert input_value.get_attribute("aria-errormessage") == "email-control-error"
    assert error.is_visible()

    input_value.fill("valid@example.com")
    page.wait_for_function("!document.querySelector('#email-control-field').hasAttribute('data-invalid')")
    assert input_value.get_attribute("aria-invalid") is None
    assert error.is_hidden()


def test_field_status_lookup_does_not_capture_a_nested_component_part(page):
    _load(page)
    nested_error = page.locator("[data-nested-error]")

    page.locator("#toggle-invalid").click()
    page.wait_for_function("document.querySelector('#email-control-field').hasAttribute('data-invalid')")

    assert nested_error.is_hidden()
    assert page.locator("#email-control-error").is_visible()


def test_controlled_and_uncontrolled_values_follow_native_reset_semantics(page):
    _load(page)
    input_value = page.locator("#email-control")

    input_value.fill("attempted@example.com")
    page.wait_for_function("document.querySelector('#email-control').value === 'owner@example.com'")

    page.locator("#release-control").click()
    input_value.fill("edited@example.com")
    page.wait_for_timeout(0)
    assert input_value.input_value() == "edited@example.com"

    page.evaluate("document.querySelector('#profile-form').reset()")
    page.wait_for_function("document.querySelector('#email-control').value === 'server@example.com'")

    page.locator("#set-controlled").click()
    page.wait_for_function("document.querySelector('#email-control').value === 'next@example.com'")
    page.evaluate("document.querySelector('#profile-form').reset()")
    page.wait_for_function("document.querySelector('#email-control').value === 'next@example.com'")


def test_dynamic_controls_follow_native_validity_and_cleanup(page):
    _load(page)
    assert page.locator("#profile-form").evaluate("element => element.matches(':invalid')") is True

    page.evaluate("document.querySelector('[data-extra-field]').remove()")
    assert page.locator("#profile-form").evaluate("element => element.matches(':valid')") is True

    page.evaluate("document.querySelector('#email-control-field').remove()")
    assert page.locator("[data-citry-input-initialized]").count() == 0


def test_submitting_blocks_duplicate_submit_without_disabling_form_data(page):
    _load(page)
    page.locator("[data-extra-field]").evaluate("element => element.remove()")
    page.evaluate(
        """() => {
          const form = document.querySelector('#profile-form');
          form.addEventListener('submit', (event) => {
            event.preventDefault();
            window.__nativeSubmits = (window.__nativeSubmits || 0) + 1;
          });
        }"""
    )

    page.evaluate("document.querySelector('#profile-form').requestSubmit()")
    assert page.evaluate("window.__nativeSubmits") == 1

    page.locator("#toggle-submitting").click()
    page.wait_for_function("document.querySelector('#profile-form').hasAttribute('data-submitting')")
    assert page.locator("#email-control").is_enabled()
    form_data = page.evaluate(
        "Object.fromEntries(new FormData(document.querySelector('#profile-form')))['profile.email']"
    )
    assert form_data == "owner@example.com"
    page.evaluate("document.querySelector('#profile-form').requestSubmit()")
    assert page.evaluate("window.__nativeSubmits") == 1


def test_invalid_client_configuration_uses_server_fallback_and_logs_once(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)

    page.locator("#set-invalid-props").click()
    page.wait_for_function("document.querySelector('#email-control').dataset.variant === 'outline'")
    page.locator("#set-invalid-props").click()

    matching = [message for message in errors if "CInput variant received invalid client value" in message]
    assert len(matching) == 1


def test_field_owns_nested_input_client_state(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)

    page.evaluate("Alpine.store('formDemo').inputRequired = false")
    page.wait_for_timeout(0)
    assert page.locator("#email-control").evaluate("element => element.required") is True

    page.locator("#toggle-required").click()
    page.wait_for_function("!document.querySelector('#email-control').required")
    page.evaluate("Alpine.store('formDemo').inputRequired = true")
    page.wait_for_timeout(0)
    assert page.locator("#email-control").evaluate("element => element.required") is False

    matching = [message for message in errors if "CInput required is controlled by its enclosing CField" in message]
    assert len(matching) == 2


def test_invalid_controlled_value_keeps_previous_mode_and_recovers(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)

    page.evaluate("Alpine.store('formDemo').controlledValue = null")
    page.wait_for_function("""() => document.querySelector('#email-control').value === 'owner@example.com'""")
    page.evaluate("Alpine.store('formDemo').controlledValue = 'recovered@example.com'")
    page.wait_for_function("""() => document.querySelector('#email-control').value === 'recovered@example.com'""")

    matching = [message for message in errors if "CInput value received invalid client value null" in message]
    assert len(matching) == 1


def test_controlled_input_defers_restoration_during_ime_composition(page):
    _load(page)

    page.evaluate(
        """() => {
          const input = document.querySelector('#email-control');
          input.dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
          input.value = 'composing';
          input.dispatchEvent(new InputEvent('input', {
            bubbles: true,
            data: 'g',
            inputType: 'insertCompositionText',
            isComposing: true,
          }));
        }"""
    )
    page.wait_for_timeout(0)
    assert page.locator("#email-control").input_value() == "composing"

    page.evaluate("Alpine.store('formDemo').controlledValue = 'updated during composition'")
    page.wait_for_timeout(0)
    assert page.locator("#email-control").input_value() == "composing"

    page.evaluate(
        """document.querySelector('#email-control').dispatchEvent(
          new CompositionEvent('compositionend', { bubbles: true, data: 'composing' }),
        )"""
    )
    page.wait_for_function("document.querySelector('#email-control').value === 'updated during composition'")


def test_change_clears_a_finished_native_invalid_episode(page):
    _load(page)
    page.locator("#release-control").click()
    input_value = page.locator("#email-control")
    input_value.fill("not-an-email")
    assert page.evaluate("document.querySelector('#email-control').reportValidity()") is False
    page.wait_for_function("document.querySelector('#email-control-field').hasAttribute('data-invalid')")

    page.evaluate(
        """() => {
          const input = document.querySelector('#email-control');
          input.value = 'valid@example.com';
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }"""
    )
    page.wait_for_function("!document.querySelector('#email-control-field').hasAttribute('data-invalid')")


def test_field_input_quality_route_initializes_and_proves_control_reset_and_form_state(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.set_content(render_scenario("field-input.states"), wait_until="load")
    page.wait_for_function(
        """() => {
          const fields = [...document.querySelectorAll('[data-citry-field-root]')];
          const inputs = [...document.querySelectorAll('.cui-input')];
          return document.querySelector('#quality-field-form')?.hasAttribute('data-citry-form-initialized')
            && fields.length === 4
            && inputs.length === 4
            && fields.every((field) => field.hasAttribute('data-citry-field-initialized'))
            && inputs.every((input) => input.hasAttribute('data-citry-input-initialized'));
        }"""
    )

    controlled = page.get_by_role("textbox", name="Controlled species note")
    controlled.fill("x")
    page.wait_for_function(
        """() => document.querySelector('#quality-controlled').value === 'x'
          && document.querySelector('#quality-controlled-field').hasAttribute('data-invalid')"""
    )

    page.locator("#quality-release-control").click()
    controlled.fill("edited in browser")
    page.locator("#quality-reset-field-form").click()
    page.wait_for_function("document.querySelector('#quality-controlled').value === ''")

    page.locator("#quality-restore-control").click()
    page.wait_for_function("document.querySelector('#quality-controlled').value === 'Giant green anemone'")
    page.locator("#quality-reset-field-form").click()
    page.wait_for_function("document.querySelector('#quality-controlled').value === 'Giant green anemone'")

    page.locator("#quality-toggle-form-disabled").click()
    page.wait_for_function(
        """() => [...document.querySelectorAll('.cui-input')].every((input) => input.disabled)
          && [...document.querySelectorAll('[data-citry-field-root]')]
            .every((field) => field.hasAttribute('data-disabled'))"""
    )
    assert errors == []
