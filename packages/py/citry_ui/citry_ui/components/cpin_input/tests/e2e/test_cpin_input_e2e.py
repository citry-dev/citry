"""Browser evidence for PinInput interaction contracts."""

# ruff: noqa: E501 - embedded template and browser expressions remain readable

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _page_html() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <title>PinInput browser contract</title>
              <script>window.__pinEvents=[];window.__pinSubmits=[];</script>
              <c-css />
              <style>.pin-brand { --cui-pin-input-focus-color: rgb(124 58 237); }</style>
            </head>
            <body x-data="{controlled:'12',accept:false}">
              <form id="verify" @submit.prevent="window.__pinSubmits.push(Array.from(new FormData($event.target).entries()))">
                <c-CPinInput
                  id="code"
                  name="code"
                  form="verify"
                  label="Verification code"
                  value="01"
                  c-length="6"
                  required
                  class_="pin-brand"
                  $c-props="{
                    onValueChange:(next,detail)=>window.__pinEvents.push(['value',next,detail.source]),
                    onComplete:(next,detail)=>window.__pinEvents.push(['complete',next,detail.source]),
                    onValueInvalid:(detail)=>window.__pinEvents.push(['invalid',detail.rejected,detail.source]),
                    onFocusChange:(focused)=>window.__pinEvents.push(['focus',focused]),
                  }"
                />
                <button id="submit" type="submit">Submit</button>
                <button id="reset" type="reset">Reset</button>
              </form>
              <c-CPinInput
                id="controlled"
                label="Controlled code"
                value="12"
                c-length="4"
                $c-props="{
                  value:controlled,
                  onValueChange:(next,detail)=>{
                    window.__pinEvents.push(['controlled',next,detail.source]);
                    if(accept) controlled=next;
                  },
                }"
              />
              <button id="accept" type="button" @click="accept=true">Accept</button>
              <form id="states">
                <c-CPinInput id="masked" name="masked" label="Masked code" value="9876" c-length="4" mask />
                <c-CPinInput id="readonly" name="readonly" label="Readonly code" value="2468" c-length="4" readonly />
                <c-CPinInput id="disabled" name="disabled" label="Disabled code" value="1357" c-length="4" disabled />
              </form>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def pin_page(page: Any):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="pin-input"]')]
          .every(root => root.hasAttribute('data-citry-pin-input-initialized'))"""
    )
    return page, errors


def test_typing_completion_form_submission_and_reset(pin_page) -> None:
    page, errors = pin_page
    input_ = page.locator("#code")
    input_.focus()
    input_.fill("012345")
    assert input_.input_value() == "012345"
    assert page.locator("#code-root").get_attribute("data-complete") == ""
    complete_event = page.evaluate("window.__pinEvents.filter(item => item[0] === 'complete').at(-1)")
    assert complete_event[:2] == ["complete", "012345"]
    # Playwright's native `fill()` is exposed as an IME composition by Firefox.
    assert complete_event[2] in {"input", "composition"}
    page.locator("#submit").click()
    assert page.evaluate("window.__pinSubmits.at(-1)") == [["code", "012345"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#code').value === '01'")
    assert input_.input_value() == "01"
    assert errors == []


def test_invalid_paste_is_filtered_and_cell_pointer_moves_selection(pin_page) -> None:
    page, errors = pin_page
    input_ = page.locator("#code")
    input_.evaluate(
        """input => {
          input.value='9x87';
          input.dispatchEvent(new InputEvent('input', {bubbles:true, inputType:'insertFromPaste'}));
        }"""
    )
    assert input_.input_value() == "987"
    assert page.evaluate("window.__pinEvents.filter(item => item[0] === 'invalid').at(-1)") == [
        "invalid",
        "x",
        "paste",
    ]
    page.locator('#code-root [data-citry-ui-part="cell"][data-index="1"]').click()
    assert page.evaluate(
        "[document.querySelector('#code').selectionStart, document.querySelector('#code').selectionEnd]"
    ) == [1, 2]
    assert page.locator('#code-root [data-citry-ui-part="cell"][data-index="1"]').get_attribute("data-active") == ""
    assert errors == []


def test_controlled_requests_masking_and_native_submission_states(pin_page) -> None:
    page, errors = pin_page
    controlled = page.locator("#controlled")
    controlled.fill("1234")
    assert controlled.input_value() == "12"
    controlled_event = page.evaluate("window.__pinEvents.filter(item => item[0] === 'controlled').at(-1)")
    assert controlled_event[:2] == ["controlled", "1234"]
    assert controlled_event[2] in {"input", "composition"}
    page.locator("#accept").click()
    controlled.fill("1234")
    page.wait_for_function("document.querySelector('#controlled').value === '1234'")
    assert controlled.input_value() == "1234"

    assert page.locator('#masked-root [data-citry-ui-part="character"]').all_text_contents() == ["•", "•", "•", "•"]
    states = page.evaluate("Array.from(new FormData(document.querySelector('#states')).entries())")
    assert states == [["masked", "9876"], ["readonly", "2468"]]
    assert page.locator("#readonly").is_editable() is False
    assert page.locator("#readonly").is_enabled()
    assert page.locator("#disabled").is_disabled()
    assert errors == []
