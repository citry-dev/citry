"""Browser evidence for Slider and RangeSlider interaction contracts."""

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
              <title>Slider browser contract</title>
              <script>window.__sliderEvents=[];window.__sliderSubmits=[];</script>
              <c-css />
            </head>
            <body x-data="{controlled:'2',accept:false,gap:2}">
              <form
                id="slider-form"
                @submit.prevent="window.__sliderSubmits.push(Array.from(new FormData($event.target).entries()))"
              >
                <c-CSlider
                  id="volume"
                  name="volume"
                  form="slider-form"
                  value="1.5"
                  min="0"
                  max="3"
                  step="0.25"
                  c-input_attrs="volume_label"
                  $c-props="{
                    onValueChange:(next,detail)=>window.__sliderEvents.push(['value',next,detail.source,detail.phase]),
                    onValueChangeEnd:(next,detail)=>window.__sliderEvents.push(['end',next,detail.source,detail.phase]),
                  }"
                />
                <c-CRangeSlider
                  id="price"
                  name="price"
                  c-value="(2, 8)"
                  min="0"
                  max="10"
                  step="1"
                  c-min_steps_between_thumbs="2"
                  $c-props="{minStepsBetweenThumbs:gap}"
                />
                <button id="submit" type="submit">Submit</button>
                <button id="reset" type="reset">Reset</button>
              </form>
              <c-CSlider
                id="controlled"
                value="2"
                min="0"
                max="5"
                step="0.5"
                c-input_attrs="controlled_label"
                $c-props="{
                  value:controlled,
                  onValueChange:(next,detail)=>{
                    window.__sliderEvents.push(['controlled',next,detail.source,detail.phase]);
                    if(accept) controlled=next;
                  },
                  onValueChangeEnd:(next,detail)=>window.__sliderEvents.push(['controlled-end',next,detail.source,detail.phase]),
                }"
              />
              <button id="accept" type="button" @click="accept=true">Accept</button>
              <button id="tighten" type="button" @click="gap=4">Tighten range</button>
              <div dir="rtl">
                <c-CSlider id="rtl" value="4" min="0" max="10" c-input_attrs="rtl_label" />
              </div>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "volume_label": {"aria-label": "Volume"},
                "controlled_label": {"aria-label": "Controlled volume"},
                "rtl_label": {"aria-label": "RTL volume"},
            }

    return str(Page())


@pytest.fixture
def slider_page(page: Any):
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page_html(), wait_until="load")
    page.wait_for_function(
        """() => [...document.querySelectorAll('[data-citry-ui-part="slider"], [data-citry-ui-part="range-slider"]')]
          .every(root => root.hasAttribute('data-citry-slider-initialized'))"""
    )
    return page, errors


def _thumb(page: Any, root_id: str, index: int = 0):
    return page.locator(f"#{root_id}").locator('[data-citry-ui-part="thumb"]').nth(index)


def test_exact_keyboard_callbacks_form_submission_and_reset(slider_page) -> None:
    page, errors = slider_page
    thumb = page.locator('.cui-slider:has(#volume) [data-citry-ui-part="thumb"]')
    native = page.locator("#volume")

    assert thumb.get_attribute("aria-valuenow") == "1.5"
    thumb.press("ArrowRight")
    assert thumb.get_attribute("aria-valuenow") == "1.75"
    thumb.press("PageUp")
    assert thumb.get_attribute("aria-valuenow") == "3"
    assert page.evaluate("window.__sliderEvents.slice(-2)") == [
        ["value", "3", "keyboard", "change"],
        ["end", "3", "keyboard", "end"],
    ]
    page.locator("#submit").click()
    assert page.evaluate("window.__sliderSubmits.at(-1)") == [
        ["volume", "3"],
        ["price", "2"],
        ["price", "8"],
    ]
    page.locator("#reset").click()
    page.wait_for_function(
        """document.querySelector('.cui-slider:has(#volume) [data-citry-ui-part=thumb]')
          .getAttribute('aria-valuenow') === '1.5'"""
    )
    assert thumb.get_attribute("aria-valuenow") == "1.5"
    assert native.input_value() == "1.5"
    assert errors == []


def test_range_keeps_thumb_identity_tab_order_and_collision_gap(slider_page, browser_name: str) -> None:
    page, errors = slider_page
    lower = _thumb(page, "price-root", 0)
    upper = _thumb(page, "price-root", 1)

    assert lower.get_attribute("aria-valuenow") == "2"
    assert upper.get_attribute("aria-valuenow") == "8"
    page.locator("#tighten").click()
    page.wait_for_function(
        "document.querySelector('#price-root [role=slider][data-thumb=lower]').getAttribute('aria-valuemax') === '4'"
    )
    assert lower.get_attribute("aria-valuemax") == "4"
    lower.press("End")
    assert lower.get_attribute("aria-valuenow") == "4"
    assert upper.get_attribute("aria-valuenow") == "8"
    upper.press("Home")
    assert upper.get_attribute("aria-valuenow") == "8"
    lower.focus()
    page.keyboard.press("Tab")
    if browser_name != "webkit":
        assert page.evaluate("document.activeElement?.dataset.thumb") == "upper"
    assert errors == []


def test_controlled_requests_do_not_move_until_owner_accepts(slider_page) -> None:
    page, errors = slider_page
    thumb = page.locator('.cui-slider:has(#controlled) [data-citry-ui-part="thumb"]')
    thumb.press("ArrowUp")
    assert thumb.get_attribute("aria-valuenow") == "2"
    assert page.evaluate("window.__sliderEvents.slice(-2)") == [
        ["controlled", "2.5", "keyboard", "change"],
        ["controlled-end", "2.5", "keyboard", "end"],
    ]
    page.locator("#accept").click()
    thumb.press("ArrowUp")
    page.wait_for_function(
        """document.querySelector('.cui-slider:has(#controlled) [data-citry-ui-part=thumb]')
          .getAttribute('aria-valuenow') === '2.5'"""
    )
    assert errors == []


def test_pointer_geometry_and_rtl_keyboard_are_deterministic(slider_page) -> None:
    page, errors = slider_page
    control = page.locator('.cui-slider:has(#volume) [data-citry-ui-part="control"]')
    box = control.bounding_box()
    assert box is not None
    page.mouse.click(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
    thumb = page.locator('.cui-slider:has(#volume) [data-citry-ui-part="thumb"]')
    assert thumb.get_attribute("aria-valuenow") == "1.5"

    rtl = page.locator('.cui-slider:has(#rtl) [data-citry-ui-part="thumb"]')
    rtl.press("ArrowRight")
    assert rtl.get_attribute("aria-valuenow") == "5"
    rtl_root = page.locator(".cui-slider:has(#rtl)")
    rtl_control = rtl_root.locator('[data-citry-ui-part="control"]')
    rtl_box = rtl_control.bounding_box()
    assert rtl_box is not None
    page.mouse.click(rtl_box["x"] + rtl_box["width"] * 0.1, rtl_box["y"] + rtl_box["height"] * 0.5)
    assert rtl.get_attribute("aria-valuenow") == "9"
    assert errors == []
