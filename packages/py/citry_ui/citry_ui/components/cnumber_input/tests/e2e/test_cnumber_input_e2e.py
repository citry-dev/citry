"""Browser evidence for CNumberInput exact editing and form behavior."""

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
              <title>NumberInput browser contract</title>
              <script>window.__numberEvents=[];window.__numberSubmits=[];</script>
              <c-css />
            </head>
            <body x-data="{ controlledValue: '2', accept: false, wheelEnabled: false }">
              <form
                id="quantity-form"
                @submit.prevent="window.__numberSubmits.push(new FormData($event.target).get('quantity'))"
              >
                <c-CNumberInput
                  id="quantity"
                  name="quantity"
                  form="quantity-form"
                  value="1.5"
                  min="0"
                  max="3"
                  step="0.25"
                  required
                  c-input_attrs="quantity_label"
                  $c-props="{
                    wheel: wheelEnabled,
                    onValueChange: (next, detail) => window.__numberEvents.push(['value', next, detail.source]),
                    onInputValueChange: (next, detail) => window.__numberEvents.push(['input', next, detail.status]),
                  }"
                />
                <button id="submit" type="submit">Submit</button>
                <button id="reset" type="reset">Reset</button>
              </form>
              <c-CNumberInput
                id="controlled"
                value="2"
                step="0.5"
                c-input_attrs="controlled_label"
                $c-props="{
                  value: controlledValue,
                  onValueChange: (next, detail) => {
                    window.__numberEvents.push(['controlled', next, detail.source]);
                    if (accept) controlledValue = next;
                  },
                }"
              />
              <button id="accept" type="button" @click="accept=true">Accept</button>
              <button id="wheel" type="button" @click="wheelEnabled=true">Enable wheel</button>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "quantity_label": {"aria-label": "Quantity"},
                "controlled_label": {"aria-label": "Controlled quantity"},
            }

    return str(Page())


@pytest.fixture
def number_page(page: Any):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="number-input"]')]
          .every(root => root.hasAttribute('data-citry-number-input-initialized'))"""
    )
    return page, errors


def test_exact_buttons_keyboard_form_submission_and_reset(number_page) -> None:
    page, errors = number_page
    editor = page.locator("#quantity")
    root = page.locator(".cui-number-input:has(#quantity)")
    transport = page.locator("#quantity-transport")

    assert editor.input_value() == "1.5"
    assert editor.get_attribute("name") in (None, "")
    assert transport.get_attribute("name") == "quantity"
    root.locator('[data-citry-ui-part="increment"]').click()
    assert editor.input_value() == "1.75"
    editor.press("ArrowDown")
    assert editor.input_value() == "1.5"
    editor.fill("2.25")
    editor.press("Enter")
    assert transport.input_value() == "2.25"
    assert page.evaluate("window.__numberSubmits") == ["2.25"]
    page.locator("#reset").click()
    page.wait_for_function(
        "document.querySelector('#quantity').value === '1.5'"
        " && document.querySelector('#quantity-transport').value === '1.5'"
    )
    assert transport.input_value() == "1.5"
    assert errors == []


def test_draft_status_validation_and_controlled_request(number_page) -> None:
    page, errors = number_page
    editor = page.locator("#quantity")
    editor.fill("-")
    assert editor.get_attribute("aria-invalid") == "true"
    assert page.evaluate("window.__numberEvents.at(-1)") == ["input", "-", "incomplete"]
    editor.fill("4")
    editor.press("Enter")
    assert editor.input_value() == "4"
    assert editor.get_attribute("aria-invalid") == "true"

    controlled = page.locator("#controlled")
    controlled.press("ArrowUp")
    assert controlled.input_value() == "2"
    assert page.evaluate("window.__numberEvents.at(-1)") == ["controlled", "2.5", "increment"]
    page.locator("#accept").click()
    controlled.press("ArrowUp")
    page.wait_for_function("document.querySelector('#controlled').value === '2.5'")
    assert errors == []


def test_wheel_is_dormant_until_explicitly_enabled(number_page) -> None:
    page, errors = number_page
    editor = page.locator("#quantity")
    editor.focus()
    editor.dispatch_event("wheel", {"deltaY": -100})
    assert editor.input_value() == "1.5"
    page.locator("#wheel").click()
    editor.focus()
    editor.dispatch_event("wheel", {"deltaY": -100})
    assert editor.input_value() == "1.75"
    assert errors == []
