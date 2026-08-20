"""Browser evidence for Rating interaction contracts."""

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
              <title>Rating browser contract</title>
              <script>window.__ratingEvents=[];window.__ratingSubmits=[];</script>
              <c-css />
              <style>.rating-brand { --cui-rating-fill-color: rgb(5 150 105); }</style>
            </head>
            <body x-data="{controlled:'2',accept:false}">
              <form id="review" @submit.prevent="window.__ratingSubmits.push(Array.from(new FormData($event.target).entries()))">
                <c-CRating
                  id="rating"
                  name="rating"
                  form="review"
                  label="Article rating"
                  value="1.5"
                  precision="0.5"
                  required
                  allow_clear
                  class_="rating-brand"
                  $c-props="{
                    onValueChange:(next,detail)=>window.__ratingEvents.push(['value',next,detail.source]),
                    onHoverChange:(next,detail)=>window.__ratingEvents.push(['hover',next]),
                  }"
                />
                <button id="submit" type="submit">Submit</button>
                <button id="reset" type="reset">Reset</button>
              </form>
              <c-CRating
                id="controlled"
                label="Controlled rating"
                value="2"
                $c-props="{
                  value:controlled,
                  onValueChange:(next,detail)=>{
                    window.__ratingEvents.push(['controlled',next,detail.source]);
                    if(accept) controlled=next;
                  },
                }"
              />
              <button id="accept" type="button" @click="accept=true">Accept</button>
              <form id="readonly-form">
                <c-CRating id="readonly" name="readonly" label="Readonly rating" value="4" readonly />
                <c-CRating id="disabled" name="disabled" label="Disabled rating" value="3" disabled />
              </form>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def rating_page(page: Any):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="rating"]')]
          .every(root => root.hasAttribute('data-citry-rating-initialized'))"""
    )
    return page, errors


def _input(page: Any, root_id: str, value: str):
    return page.locator(f"#{root_id} [data-citry-ui-part=input][value='{value}']")


def _choice(page: Any, root_id: str, value: str):
    return page.locator(f"#{root_id} [data-citry-ui-part=choice][data-value='{value}']")


def test_native_radio_keyboard_form_submission_and_reset(rating_page) -> None:
    page, errors = rating_page
    root = page.locator("#rating-root")
    selected = _input(page, "rating-root", "1.5")
    assert selected.is_checked()
    selected.focus()
    selected.press("ArrowRight")
    assert _input(page, "rating-root", "2").is_checked()
    assert page.evaluate("window.__ratingEvents.filter(item => item[0] === 'value').at(-1)") == [
        "value", "2", "keyboard",
    ]
    page.locator("#submit").click()
    assert page.evaluate("window.__ratingSubmits.at(-1)") == [["rating", "2"]]
    page.locator("#reset").click()
    page.wait_for_function(
        "document.querySelector('#rating-root input[value=\"1.5\"]').checked "
        "&& document.querySelector('#rating-root').style.getPropertyValue('--_cui-rating-ratio') === '30%'"
    )
    assert selected.is_checked()
    assert root.get_attribute("style").find("30%") >= 0
    assert errors == []


def test_clear_hover_and_controlled_request_behavior(rating_page) -> None:
    page, errors = rating_page
    root = page.locator("#rating-root")
    _choice(page, "rating-root", "2.5").hover()
    assert root.get_attribute("data-hovering") == ""
    assert page.evaluate("window.__ratingEvents.at(-1)") == ["hover", "2.5"]
    page.mouse.move(0, 0)
    assert root.get_attribute("data-hovering") is None

    _choice(page, "rating-root", "1.5").click()
    page.wait_for_function("![...document.querySelectorAll('#rating-root input[type=radio]')].some(input => input.checked)")
    assert page.evaluate("new FormData(document.querySelector('#review')).has('rating')") is False
    assert page.evaluate("window.__ratingEvents.filter(item => item[0] === 'value').at(-1)") == [
        "value", None, "pointer",
    ]

    _choice(page, "controlled-root", "4").click()
    assert _input(page, "controlled-root", "2").is_checked()
    assert page.evaluate("window.__ratingEvents.at(-1)") == ["controlled", "4", "pointer"]
    page.locator("#accept").click()
    _choice(page, "controlled-root", "4").click()
    page.wait_for_function("document.querySelector('#controlled-4').checked")
    assert errors == []


def test_readonly_submits_disabled_does_not_and_styles_are_customizable(rating_page) -> None:
    page, errors = rating_page
    assert page.evaluate("Array.from(new FormData(document.querySelector('#readonly-form')).entries())") == [
        ["readonly", "4"]
    ]
    assert page.locator("#readonly-root").get_attribute("tabindex") == "0"
    assert page.locator("#disabled-root").get_attribute("tabindex") is None
    fill_color = page.locator("#rating-root").evaluate(
        "element => getComputedStyle(element).getPropertyValue('--_cui-rating-fill-color').trim()"
    )
    assert fill_color == "rgb(5 150 105)"
    assert errors == []
