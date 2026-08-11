"""Browser evidence for the production Spinner contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _spinner_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.spinner-brand) {
            --cui-spinner-color: rgb(88 28 135);
            --cui-spinner-track-color: rgb(221 214 254);
            --cui-spinner-size: 40px;
            --cui-spinner-thickness: 5px;
            --cui-spinner-duration: 1.2s;
          }

          :where(.spinner-part[data-citry-ui-part="spinner"]) {
            margin-inline: 7px;
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
              x-init="Alpine.store('spinnerTest', {
                label: 'Loading star catalog',
                intent: 'primary',
                size: 'md',
              })"
            >
              <c-CSpinner
                class_="spinner-brand spinner-part"
                label="Loading star catalog"
                $c-props="{
                  label: $store.spinnerTest.label,
                  intent: $store.spinnerTest.intent,
                  size: $store.spinnerTest.size,
                }"
              />
              <c-CSpinner label="Aligning telescope" size="sm" intent="success" />
              <div dir="rtl"><c-CSpinner label="تحديث فهرس النجوم" size="lg" /></div>
              <button id="after-spinner" type="button">Continue</button>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def spinner_page(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_spinner_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const roots = [...document.querySelectorAll('.cui-spinner')];
          return roots.length === 3
            && roots.every(root => root.hasAttribute('data-citry-spinner-initialized'));
        }"""
    )
    return page, errors


def test_spinner_is_labelled_indeterminate_and_unfocusable(spinner_page):
    page, errors = spinner_page
    root = page.get_by_role("progressbar", name="Loading star catalog")

    assert root.evaluate("element => element.tagName") == "SPAN"
    assert root.get_attribute("aria-valuenow") is None
    assert root.get_attribute("tabindex") is None
    page.locator("body").press("Tab")
    assert page.locator("#after-spinner").evaluate("element => element === document.activeElement")
    assert errors == []


def test_client_inputs_update_and_invalid_episodes_fall_back(spinner_page):
    page, errors = spinner_page
    root = page.locator(".cui-spinner").first

    page.evaluate(
        """() => Object.assign(Alpine.store('spinnerTest'), {
          label: 'Calibrating spectrograph',
          intent: 'warn',
          size: 'lg',
        })"""
    )
    page.wait_for_timeout(0)
    assert root.get_attribute("aria-label") == "Calibrating spectrograph"
    assert root.get_attribute("data-intent") == "warn"
    assert root.get_attribute("data-size") == "lg"

    page.evaluate("Alpine.store('spinnerTest').intent = 'info'")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('spinnerTest').intent = 42")
    page.wait_for_timeout(0)
    assert root.get_attribute("data-intent") == "primary"
    assert sum("CSpinner intent received invalid client value" in error for error in errors) == 1

    page.evaluate("Alpine.store('spinnerTest').intent = 'success'")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('spinnerTest').intent = null")
    page.wait_for_timeout(0)
    assert sum("CSpinner intent received invalid client value" in error for error in errors) == 2


def test_public_css_hooks_sizes_and_direction_compute(spinner_page):
    page, errors = spinner_page
    root = page.locator(".cui-spinner").first
    small = page.locator(".cui-spinner").nth(1)
    rtl = page.locator(".cui-spinner").nth(2)

    assert root.evaluate("element => getComputedStyle(element).width") == "40px"
    assert root.evaluate("element => getComputedStyle(element).borderTopWidth") == "5px"
    assert root.evaluate("element => getComputedStyle(element).borderTopColor") == "rgb(88, 28, 135)"
    assert root.evaluate("element => getComputedStyle(element).marginLeft") == "7px"
    assert small.evaluate("element => getComputedStyle(element).width") == "16px"
    assert rtl.evaluate("element => getComputedStyle(element).width") == "28px"
    assert rtl.evaluate("element => getComputedStyle(element).direction") == "rtl"
    assert errors == []


def test_reduced_motion_forced_colors_and_print_stop_or_preserve_the_cue(spinner_page):
    page, errors = spinner_page
    root = page.locator(".cui-spinner").first

    assert root.evaluate("element => getComputedStyle(element).animationName") == "cui-spinner-rotate"
    page.emulate_media(reduced_motion="reduce")
    assert root.evaluate("element => getComputedStyle(element).animationName") == "none"
    assert root.evaluate("element => getComputedStyle(element).borderRightColor") == "rgb(88, 28, 135)"
    page.emulate_media(reduced_motion="no-preference", forced_colors="active")
    assert root.evaluate("element => getComputedStyle(element).borderTopStyle") == "solid"
    page.emulate_media(forced_colors="none", media="print")
    assert root.evaluate("element => getComputedStyle(element).animationName") == "none"
    assert errors == []
