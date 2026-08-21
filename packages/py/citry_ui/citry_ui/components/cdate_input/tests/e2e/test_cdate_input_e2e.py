"""Browser evidence for the native DateInput contract."""

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
              <title>DateInput browser contract</title>
              <script>window.__dateEvents=[];window.__dateSubmits=[];</script>
              <c-css />
              <style>.date-brand { --cui-date-input-focus-color: rgb(124 58 237); }</style>
            </head>
            <body x-data="{day:'2026-08-19',accept:false,min:'2026-08-01',variant:'outline'}">
              <form id="booking" @submit.prevent="window.__dateSubmits.push(Array.from(new FormData($event.target).entries()))">
                <c-CField control_id="arrival" required>
                  <c-fill name="label">Arrival date</c-fill>
                  <c-fill name="description">Choose an alternating August day.</c-fill>
                  <c-fill name="default"><c-CDateInput id="arrival" name="arrival" form="booking" value="2026-08-19" min="2026-08-01" max="2026-08-31" c-step="2" class_="date-brand" @input="window.__dateEvents.push(['input',$event.currentTarget.value])" @change="window.__dateEvents.push(['change',$event.currentTarget.value])" /></c-fill>
                  <c-fill name="error">Choose a valid arrival date.</c-fill>
                </c-CField>
                <button id="submit" type="submit">Submit</button><button id="reset" type="reset">Reset</button>
              </form>
              <c-CDateInput id="controlled" value="2026-08-19" c-attrs="{'aria-label':'Controlled date'}" $c-props="{value:day,min:min,variant:variant}" @input="window.__dateEvents.push(['controlled',$event.currentTarget.value]);if(accept)day=$event.currentTarget.value" />
              <button id="accept" type="button" @click="accept=true">Accept</button>
              <button id="configure" type="button" @click="min='2026-08-15';variant='filled'">Configure</button>
              <form id="states">
                <c-CDateInput id="readonly" name="readonly" value="2026-08-20" readonly c-attrs="{'aria-label':'Readonly date'}" />
                <c-CDateInput id="disabled" name="disabled" value="2026-08-21" disabled c-attrs="{'aria-label':'Disabled date'}" />
              </form>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def date_page(page: Any):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="date-input"]')]
          .every(input => input.hasAttribute('data-citry-date-input-initialized'))"""
    )
    return page, errors


def test_native_edit_form_submission_and_reset(date_page) -> None:
    page, errors = date_page
    arrival = page.locator("#arrival")
    assert arrival.input_value() == "2026-08-19"
    arrival.fill("2026-08-21")
    assert page.evaluate("window.__dateEvents.slice(-2)") == [
        ["input", "2026-08-21"],
        ["change", "2026-08-21"],
    ]
    page.locator("#submit").click()
    assert page.evaluate("window.__dateSubmits.at(-1)") == [["arrival", "2026-08-21"]]
    page.locator("#reset").click()
    page.wait_for_function("document.querySelector('#arrival').value === '2026-08-19'")
    assert arrival.input_value() == "2026-08-19"
    assert errors == []


def test_controlled_request_refusal_acceptance_and_reactive_configuration(date_page) -> None:
    page, errors = date_page
    controlled = page.locator("#controlled")
    controlled.fill("2026-08-22")
    page.wait_for_function("document.querySelector('#controlled').value === '2026-08-19'")
    assert page.evaluate("window.__dateEvents.filter(item => item[0] === 'controlled').at(-1)") == [
        "controlled",
        "2026-08-22",
    ]
    page.locator("#accept").click()
    controlled.fill("2026-08-22")
    page.wait_for_function("document.querySelector('#controlled').value === '2026-08-22'")
    page.locator("#configure").click()
    page.wait_for_function("document.querySelector('#controlled').dataset.variant === 'filled'")
    assert controlled.get_attribute("min") == "2026-08-15"
    assert errors == []


def test_native_states_formdata_field_relationships_and_brand_style(date_page) -> None:
    page, errors = date_page
    arrival = page.locator("#arrival")
    assert arrival.get_attribute("aria-describedby") == "arrival-description"
    assert arrival.get_attribute("required") == ""
    assert arrival.get_attribute("step") == "2"
    assert page.evaluate("Array.from(new FormData(document.querySelector('#states')).entries())") == [
        ["readonly", "2026-08-20"],
    ]
    assert page.locator("#readonly").is_editable() is False
    assert page.locator("#readonly").is_enabled()
    assert page.locator("#disabled").is_disabled()
    assert (
        arrival.evaluate(
            "element => getComputedStyle(element).getPropertyValue('--_cui-date-input-focus-color').trim()"
        )
        == "rgb(124 58 237)"
    )
    assert errors == []


def test_required_invalid_submission_marks_field_and_focuses_native_input(date_page) -> None:
    page, errors = date_page
    arrival = page.locator("#arrival")
    arrival.fill("")
    page.locator("#submit").click()
    page.wait_for_function("document.querySelector('#arrival').getAttribute('aria-invalid') === 'true'")
    page.wait_for_function("document.activeElement?.id === 'arrival'")
    assert arrival.get_attribute("aria-errormessage") == "arrival-error"
    assert errors == []
