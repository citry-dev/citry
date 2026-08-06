from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _form_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.form-theme) {
            --cui-form-gap: 24px;
          }

          :where(.form-theme [data-citry-ui-part="fieldset"]) {
            align-items: start;
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
              x-data="{
                disabled: false,
                readonly: false,
                submitting: false,
                cancelReset: false,
              }"
            >
              <section class="form-theme">
                <c-CForm
                  id="observation-form"
                  action="/observations"
                  method="post"
                  $c-props="{ disabled, readonly, submitting }"
                  @submit.prevent="window.__acceptedSubmits = (window.__acceptedSubmits || 0) + 1"
                  @reset="cancelReset && $event.preventDefault()"
                >
                  <legend>
                    <input id="legend-probe" name="legend_probe" value="inside" />
                  </legend>
                  <c-CField control_id="target" required>
                    <c-fill name="label">
                      Target
                    </c-fill>
                    <c-fill name="default">
                      <c-CInput id="target" name="target" value="M31" />
                    </c-fill>
                  </c-CField>
                  <c-CButton type="submit">
                    Submit observation
                  </c-CButton>
                  <c-CButton href="/help">
                    Observation help
                  </c-CButton>
                </c-CForm>
              </section>

              <label for="allocation">Allocation code</label>
              <c-CInput
                id="allocation"
                name="allocation"
                value="Q4-NORTH"
                c-attrs="{'form': 'observation-form'}"
              />

              <button id="toggle-disabled" type="button" @click="disabled = !disabled">Disabled</button>
              <button id="toggle-readonly" type="button" @click="readonly = !readonly">Read-only</button>
              <button id="toggle-submitting" type="button" @click="submitting = !submitting">Submitting</button>
              <button id="toggle-cancel-reset" type="button" @click="cancelReset = !cancelReset">Cancel reset</button>
              <button id="invalid-disabled" type="button" @click="disabled = null">Invalid disabled</button>
              <button id="invalid-disabled-string" type="button" @click="disabled = 'bad'">
                Invalid disabled string
              </button>
              <button id="restore-disabled" type="button" @click="disabled = false">Restore disabled</button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


def _load(page) -> None:
    page.set_content(_form_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const form = document.querySelector('#observation-form');
          return form?.hasAttribute('data-citry-form-initialized')
            && document.querySelector('#target')?.hasAttribute('data-citry-input-initialized')
            && document.querySelector('#allocation')?.hasAttribute('data-citry-input-initialized');
        }"""
    )


def test_reactive_configuration_preserves_native_disabled_and_external_ownership(page) -> None:
    _load(page)
    form = page.locator("#observation-form")
    external = page.locator("#allocation")

    assert form.get_attribute("action") == "/observations"
    assert form.get_attribute("method") == "post"
    assert form.locator("fieldset").evaluate("element => getComputedStyle(element).gap") == "24px"
    assert form.locator("fieldset > legend").first.get_attribute("aria-hidden") == "true"

    page.locator("#toggle-disabled").click()
    page.wait_for_function("document.querySelector('#target').disabled")
    assert page.locator("#legend-probe").is_disabled()
    assert page.get_by_role("button", name="Submit observation").is_disabled()
    assert page.get_by_role("button", name="Submit observation").get_attribute("data-disabled") == ""
    help_link = page.locator("a").filter(has_text="Observation help")
    assert help_link.get_attribute("href") is None
    assert help_link.get_attribute("data-disabled") == ""
    assert external.is_enabled()
    assert (
        page.evaluate("Object.fromEntries(new FormData(document.querySelector('#observation-form'))).allocation")
        == "Q4-NORTH"
    )
    assert (
        page.evaluate("Object.fromEntries(new FormData(document.querySelector('#observation-form'))).target") is None
    )

    page.locator("#toggle-disabled").click()
    page.wait_for_function('document.querySelector(\'[data-citry-ui-part="button"][href="/help"]\')')
    assert help_link.get_attribute("data-disabled") is None
    page.locator("#toggle-readonly").click()
    page.wait_for_function("document.querySelector('#target').readOnly")
    assert external.is_editable()


def test_validation_attempt_and_cancelable_reset_follow_native_outcome(page) -> None:
    _load(page)
    form = page.locator("#observation-form")
    target = page.locator("#target")

    target.fill("")
    assert page.evaluate("document.querySelector('#target').reportValidity()") is False
    assert form.get_attribute("data-validation-attempted") == ""

    target.fill("M42")
    page.locator("#toggle-cancel-reset").click()
    page.evaluate("document.querySelector('#observation-form').reset()")
    page.wait_for_timeout(20)
    assert target.input_value() == "M42"
    assert form.get_attribute("data-validation-attempted") == ""

    page.locator("#toggle-cancel-reset").click()
    page.evaluate("document.querySelector('#observation-form').reset()")
    page.wait_for_function(
        "document.querySelector('#target').value === 'M31'"
        " && !document.querySelector('#observation-form').hasAttribute('data-validation-attempted')"
    )


def test_later_canceled_reset_does_not_hide_an_earlier_successful_reset(page) -> None:
    _load(page)
    page.locator("#target").fill("")
    assert page.evaluate("document.querySelector('#target').reportValidity()") is False

    page.evaluate(
        """() => {
          const form = document.querySelector('#observation-form');
          let nested = false;
          const resetAgain = (event) => {
            if (!nested) {
              nested = true;
              form.reset();
              return;
            }
            event.preventDefault();
            form.removeEventListener('reset', resetAgain);
          };
          form.addEventListener('reset', resetAgain);
          form.reset();
        }"""
    )

    page.wait_for_function(
        "document.querySelector('#target').value === 'M31'"
        " && !document.querySelector('#observation-form').hasAttribute('data-validation-attempted')"
    )


def test_successful_reset_does_not_hide_a_newer_validation_attempt(page) -> None:
    _load(page)
    form = page.locator("#observation-form")

    page.evaluate(
        """() => {
          const form = document.querySelector('#observation-form');
          const target = document.querySelector('#target');
          form.reset();
          target.value = '';
          target.reportValidity();
        }"""
    )

    page.wait_for_timeout(20)
    assert form.get_attribute("data-validation-attempted") == ""


def test_submitting_guard_blocks_later_events_without_removing_form_data(page) -> None:
    _load(page)

    page.evaluate("document.querySelector('#observation-form').requestSubmit()")
    assert page.evaluate("window.__acceptedSubmits") == 1

    page.locator("#toggle-submitting").click()
    page.wait_for_function("document.querySelector('#observation-form').hasAttribute('data-submitting')")
    assert page.locator("#target").is_enabled()
    assert page.get_by_role("button", name="Submit observation").is_enabled()
    assert (
        page.evaluate("Object.fromEntries(new FormData(document.querySelector('#observation-form'))).target") == "M31"
    )

    page.evaluate("document.querySelector('#observation-form').requestSubmit()")
    assert page.evaluate("window.__acceptedSubmits") == 1


def test_invalid_client_boolean_reports_once_uses_fallback_and_recovers(page) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)

    page.locator("#invalid-disabled").click()
    page.locator("#invalid-disabled-string").click()
    page.wait_for_timeout(0)
    assert page.locator("#observation-form").get_attribute("data-disabled") is None

    matching = [message for message in errors if "CForm disabled received invalid client value null" in message]
    assert len(matching) == 1

    page.locator("#restore-disabled").click()
    page.locator("#invalid-disabled-string").click()
    page.wait_for_timeout(0)
    matching = [message for message in errors if "CForm disabled received invalid client value" in message]
    assert len(matching) == 2

    page.locator("#restore-disabled").click()
    page.locator("#toggle-disabled").click()
    page.wait_for_function("document.querySelector('#observation-form').hasAttribute('data-disabled')")
