"""Browser evidence for the production Progress contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _progress_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.progress-brand) {
            --cui-progress-track-color: rgb(232 221 246);
            --cui-progress-range-color: rgb(88 28 135);
            --cui-progress-height: 18px;
            --cui-progress-radius: 9px;
          }

          :where(.progress-part[data-citry-ui-part="progress"]) {
            inline-size: 240px;
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
              x-init="Alpine.store('progressTest', {
                value: 25,
                label: 'Mapping seabed',
                valueText: 'One quarter mapped',
                intent: 'primary',
                size: 'md',
                shape: 'rounded',
              })"
            >
              <c-CProgress
                class_="progress-brand progress-part"
                label="Mapping seabed"
                c-value="25"
                $c-props="{
                  value: $store.progressTest.value,
                  label: $store.progressTest.label,
                  valueText: $store.progressTest.valueText,
                  intent: $store.progressTest.intent,
                  size: $store.progressTest.size,
                  shape: $store.progressTest.shape,
                }"
              />
              <c-CProgress label="Contacting research vessel" shape="pill" />
              <div dir="rtl">
                <c-CProgress label="مسح قاع البحر" c-value="68" intent="success" />
              </div>
              <c-js />
            </body>
          </html>
        """

    return str(Page())


@pytest.fixture
def progress_page(page: Any):
    errors: list[str] = []
    page.on(
        "console",
        lambda message: errors.append(message.text) if message.type == "error" else None,
    )
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_progress_page(), wait_until="load")
    page.wait_for_function(
        """() => {
          const roots = [...document.querySelectorAll('.cui-progress')];
          return roots.length === 3
            && roots.every(root => root.hasAttribute('data-citry-progress-initialized'));
        }"""
    )
    return page, errors


def test_native_determinate_and_indeterminate_semantics(progress_page):
    page, errors = progress_page
    determinate = page.get_by_role("progressbar", name="Mapping seabed")
    indeterminate = page.get_by_role("progressbar", name="Contacting research vessel")

    assert determinate.evaluate("element => element.tagName") == "PROGRESS"
    assert determinate.evaluate("element => element.value") == 25
    assert determinate.evaluate("element => element.max") == 100
    assert determinate.evaluate("element => element.position") == 0.25
    assert determinate.get_attribute("aria-valuetext") == "One quarter mapped"
    assert indeterminate.get_attribute("value") is None
    assert indeterminate.evaluate("element => element.position") == -1
    assert indeterminate.get_attribute("data-state") == "indeterminate"
    assert errors == []


def test_client_inputs_update_native_and_public_surfaces(progress_page):
    page, errors = progress_page
    root = page.locator(".cui-progress").first

    page.evaluate(
        """() => Object.assign(Alpine.store('progressTest'), {
          value: null,
          label: 'Waiting for sonar',
          valueText: null,
          intent: 'warn',
          size: 'lg',
          shape: 'pill',
        })"""
    )
    page.wait_for_timeout(0)
    assert root.get_attribute("value") is None
    assert root.get_attribute("aria-label") == "Waiting for sonar"
    assert root.get_attribute("aria-valuetext") is None
    assert root.get_attribute("data-state") == "indeterminate"
    assert root.get_attribute("data-intent") == "warn"
    assert root.get_attribute("data-size") == "lg"
    assert root.get_attribute("data-shape") == "pill"

    page.evaluate("Alpine.store('progressTest').value = 72")
    page.wait_for_timeout(0)
    assert root.get_attribute("value") == "72"
    assert root.evaluate("element => element.position") == 0.72
    assert root.get_attribute("data-state") == "determinate"
    assert errors == []


def test_invalid_client_values_report_once_per_episode(progress_page):
    page, errors = progress_page
    root = page.locator(".cui-progress").first

    page.evaluate("Alpine.store('progressTest').value = 140")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('progressTest').value = 'unknown'")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('progressTest').intent = 'info'")
    page.wait_for_timeout(0)
    assert root.get_attribute("value") == "25"
    assert root.get_attribute("data-intent") == "primary"
    assert sum("CProgress value received invalid client value" in error for error in errors) == 1
    assert sum("CProgress intent received invalid client value" in error for error in errors) == 1

    page.evaluate("Alpine.store('progressTest').value = 60")
    page.wait_for_timeout(0)
    page.evaluate("Alpine.store('progressTest').value = -1")
    page.wait_for_timeout(0)
    assert sum("CProgress value received invalid client value" in error for error in errors) == 2


def test_public_css_hooks_direction_and_environment_contract(progress_page):
    page, errors = progress_page
    root = page.locator(".cui-progress").first
    indeterminate = page.locator(".cui-progress").nth(1)
    rtl = page.locator(".cui-progress").nth(2)

    assert root.evaluate("element => getComputedStyle(element).height") == "18px"
    assert root.evaluate("element => getComputedStyle(element).borderRadius") == "9px"
    assert root.evaluate("element => getComputedStyle(element).width") == "240px"
    assert root.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(232, 221, 246)"
    assert rtl.evaluate("element => getComputedStyle(element).direction") == "rtl"

    page.emulate_media(reduced_motion="reduce")
    assert indeterminate.evaluate("element => getComputedStyle(element).animationName") == "none"
    page.emulate_media(reduced_motion="no-preference", forced_colors="active")
    assert root.evaluate("element => getComputedStyle(element).borderTopStyle") == "solid"
    page.emulate_media(forced_colors="none", media="print")
    assert indeterminate.evaluate("element => getComputedStyle(element).animationName") == "none"
    assert errors == []
