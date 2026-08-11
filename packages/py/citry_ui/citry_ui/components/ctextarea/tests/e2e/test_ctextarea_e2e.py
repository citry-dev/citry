"""Browser tests for the production CTextarea contract."""

from __future__ import annotations

import pytest
from markupsafe import Markup

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _textarea_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.textarea-brand) {
            --cui-textarea-background: rgb(241 250 244);
            --cui-textarea-foreground: rgb(20 67 43);
            --cui-textarea-radius: 1rem;
          }

          :where(.textarea-part-override[data-citry-ui-part="textarea"]) {
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
            <body
              x-data
              x-init="Alpine.store('textareaDemo', {
                controlled: true,
                draft: 'Moss and fern',
                immutable: 'Fixed record',
                rows: 4,
                required: false,
                disabled: false,
                readonly: false,
                invalid: false,
                variant: 'outline',
                size: 'md',
                resize: 'vertical',
              })"
            >
              <c-CForm id="journal-form">
                <c-CField control_id="journal-notes">
                  <c-fill name="label">Journal notes</c-fill>
                  <c-fill name="default">
                    <c-CTextarea
                      name="notes"
                      value="Server notes"
                      class_="textarea-brand textarea-part-override"
                      c-attrs="{'minlength': 5, 'maxlength': 80}"
                      $c-props="{
                        value: $store.textareaDemo.controlled
                          ? $store.textareaDemo.draft
                          : undefined,
                        rows: $store.textareaDemo.rows,
                        variant: $store.textareaDemo.variant,
                        size: $store.textareaDemo.size,
                        resize: $store.textareaDemo.resize,
                      }"
                      @input="$store.textareaDemo.draft = $event.target.value"
                    />
                  </c-fill>
                  <c-fill name="description">Record one field observation.</c-fill>
                  <c-fill name="error">Add more detail.</c-fill>
                </c-CField>
                <c-CTextarea
                  id="immutable-notes"
                  value="Server immutable"
                  $c-props="{value: $store.textareaDemo.immutable}"
                />
                <c-CTextarea
                  id="state-notes"
                  $c-props="{
                    required: $store.textareaDemo.required,
                    disabled: $store.textareaDemo.disabled,
                    readonly: $store.textareaDemo.readonly,
                    invalid: $store.textareaDemo.invalid,
                  }"
                />
                <c-CTextarea
                  id="native-newlines"
                  c-value="native_value"
                />
                <c-CTextarea
                  id="hostile-value"
                  c-value="hostile_value"
                  c-placeholder="hostile_placeholder"
                />
                <button id="native-reset" type="reset">Reset</button>
              </c-CForm>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "native_value": "\nfirst\r\nsecond\rthird",
                "hostile_value": Markup('</textarea><script id="escaped-script">bad()</script>'),
                "hostile_placeholder": Markup('write "safely" <here>'),
            }

    return str(Page())


def _load(page) -> None:
    page.set_content(_textarea_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const controls = [...document.querySelectorAll('.cui-textarea')];
          return controls.length === 5
            && controls.every((control) =>
              control.hasAttribute('data-citry-textarea-initialized'));
        }"""
    )


def test_initial_value_parser_security_and_newline_contract(page):
    _load(page)

    assert page.locator("#native-newlines").input_value() == "\nfirst\nsecond\nthird"
    assert page.locator("#native-newlines").evaluate("element => element.defaultValue") == "\nfirst\nsecond\nthird"
    assert page.locator("#hostile-value").input_value() == '</textarea><script id="escaped-script">bad()</script>'
    assert page.locator("#escaped-script").count() == 0
    assert page.locator("#hostile-value").get_attribute("placeholder") == 'write "safely" <here>'
    assert page.evaluate("window.__textareaPwned") is None


def test_mirrored_controlled_input_preserves_middle_insertion_and_caret(page):
    _load(page)
    textarea = page.locator("#journal-notes")

    result = textarea.evaluate(
        """element => {
          element.focus();
          element.setSelectionRange(4, 4);
          element.setRangeText('X', 4, 4, 'end');
          element.dispatchEvent(new InputEvent('input', {
            bubbles: true,
            data: 'X',
            inputType: 'insertText',
          }));
          return {value: element.value, start: element.selectionStart, end: element.selectionEnd};
        }"""
    )
    assert result == {"value": "MossX and fern", "start": 5, "end": 5}

    page.wait_for_timeout(20)
    assert textarea.input_value() == "MossX and fern"
    assert textarea.evaluate("element => [element.selectionStart, element.selectionEnd]") == [5, 5]
    assert page.evaluate("Alpine.store('textareaDemo').draft") == "MossX and fern"


def test_immutable_controlled_value_restores_after_consumer_handlers_settle(page):
    _load(page)
    textarea = page.locator("#immutable-notes")

    textarea.evaluate(
        """element => {
          element.value = 'Browser edit';
          element.dispatchEvent(new InputEvent('input', {bubbles: true, inputType: 'insertText'}));
        }"""
    )
    page.wait_for_function("document.querySelector('#immutable-notes').value === 'Fixed record'")


def test_composition_defers_assignment_and_reads_latest_prop_after_commit(page):
    _load(page)
    textarea = page.locator("#journal-notes")

    textarea.evaluate(
        """element => {
          element.dispatchEvent(new CompositionEvent('compositionstart', {bubbles: true}));
          element.value = 'composing';
        }"""
    )
    page.evaluate("Alpine.store('textareaDemo').draft = 'remote update'")
    page.wait_for_timeout(0)
    assert textarea.input_value() == "composing"

    textarea.evaluate(
        """element => element.dispatchEvent(
          new CompositionEvent('compositionend', {bubbles: true, data: 'composing'}),
        )"""
    )
    page.wait_for_function("document.querySelector('#journal-notes').value === 'remote update'")


def test_mirrored_composition_commit_wins_before_deferred_reconciliation(page):
    _load(page)
    textarea = page.locator("#journal-notes")

    textarea.evaluate(
        """element => {
          element.dispatchEvent(new CompositionEvent('compositionstart', {bubbles: true}));
          element.value = 'moss 苔';
          element.dispatchEvent(
            new CompositionEvent('compositionend', {bubbles: true, data: '苔'}),
          );
          element.dispatchEvent(new InputEvent('input', {
            bubbles: true,
            data: '苔',
            inputType: 'insertCompositionText',
          }));
        }"""
    )
    page.wait_for_timeout(20)

    assert textarea.input_value() == "moss 苔"
    assert page.evaluate("Alpine.store('textareaDemo').draft") == "moss 苔"


def test_release_during_composition_is_immediate_and_reset_uses_server_default(page):
    _load(page)
    textarea = page.locator("#journal-notes")

    textarea.evaluate(
        """element => {
          element.dispatchEvent(new CompositionEvent('compositionstart', {bubbles: true}));
          element.value = 'uncommitted';
        }"""
    )
    page.evaluate("Alpine.store('textareaDemo').controlled = false")
    page.wait_for_timeout(0)
    assert textarea.input_value() == "uncommitted"

    page.locator("#native-reset").click()
    page.wait_for_function("document.querySelector('#journal-notes').value === 'Server notes'")
    textarea.evaluate(
        """element => element.dispatchEvent(
          new CompositionEvent('compositionend', {bubbles: true}),
        )"""
    )
    page.wait_for_timeout(20)
    assert textarea.input_value() == "Server notes"


@pytest.mark.parametrize("canceled_reset", [1, 2])
def test_each_same_turn_reset_keeps_its_own_controlled_restoration(page, canceled_reset):
    _load(page)

    page.evaluate(
        """canceledReset => {
          const form = document.querySelector('#journal-form');
          const textarea = document.querySelector('#journal-notes');
          let resetCount = 0;
          form.addEventListener('reset', event => {
            resetCount += 1;
            if (resetCount === canceledReset) event.preventDefault();
          });
          textarea.value = 'browser edit';
          form.reset();
          form.reset();
        }""",
        canceled_reset,
    )

    page.wait_for_function("document.querySelector('#journal-notes').value === 'Moss and fern'")


def test_client_configuration_reflects_native_state_and_uses_server_fallback(page):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    _load(page)
    textarea = page.locator("#journal-notes")

    page.evaluate(
        """() => Object.assign(Alpine.store('textareaDemo'), {
          rows: 7,
          variant: 'filled',
          size: 'lg',
          resize: 'none',
        })"""
    )
    page.wait_for_function(
        """() => {
          const textarea = document.querySelector('#journal-notes');
          return textarea.rows === 7
            && textarea.dataset.variant === 'filled'
            && textarea.dataset.size === 'lg'
            && textarea.dataset.resize === 'none';
        }"""
    )
    assert textarea.evaluate("element => getComputedStyle(element).resize") == "none"

    page.evaluate(
        """() => Object.assign(Alpine.store('textareaDemo'), {
          rows: 0,
          variant: 'raised',
          size: 'xl',
          resize: 'auto',
        })"""
    )
    page.wait_for_function(
        """() => {
          const textarea = document.querySelector('#journal-notes');
          return textarea.rows === 4
            && textarea.dataset.variant === 'outline'
            && textarea.dataset.size === 'md'
            && textarea.dataset.resize === 'vertical';
        }"""
    )
    assert len([message for message in errors if "CTextarea rows received invalid" in message]) == 1
    assert len([message for message in errors if "CTextarea variant received invalid" in message]) == 1


def test_field_state_relationships_and_public_css_overrides_work_in_browser(page):
    _load(page)
    textarea = page.locator("#journal-notes")
    state_textarea = page.locator("#state-notes")

    assert textarea.get_attribute("aria-describedby") == "journal-notes-description"
    assert textarea.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(241, 250, 244)"
    assert textarea.evaluate("element => getComputedStyle(element).color") == "rgb(20, 67, 43)"
    assert textarea.evaluate("element => getComputedStyle(element).borderRadius") == "16px"
    assert textarea.evaluate("element => getComputedStyle(element).borderTopWidth") == "5px"

    page.evaluate(
        """() => Object.assign(Alpine.store('textareaDemo'), {
          required: true,
          disabled: true,
          readonly: true,
          invalid: true,
        })"""
    )
    page.wait_for_timeout(0)

    assert state_textarea.evaluate("element => element.required") is True
    assert state_textarea.evaluate("element => element.disabled") is True
    assert state_textarea.evaluate("element => element.readOnly") is True
    assert state_textarea.get_attribute("aria-invalid") == "true"
    assert state_textarea.get_attribute("data-required") == ""
    assert state_textarea.get_attribute("data-invalid") == ""
