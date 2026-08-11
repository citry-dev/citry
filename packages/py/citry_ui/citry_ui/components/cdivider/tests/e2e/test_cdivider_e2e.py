"""Browser evidence for the production Divider contract."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _divider_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <style>
                .selector-override [data-citry-ui-part="label"] {
                  letter-spacing: 3px;
                }
              </style>
              <c-css />
            </head>
            <body>
              <c-CDivider c-attrs="{'id': 'semantic'}" />
              <c-CDivider c-attrs="{'id': 'decorative'}" c-decorative="True" />
              <div id="vertical-row" style="display:flex; block-size:80px; gap:12px">
                <span>North</span>
                <c-CDivider
                  c-attrs="{'id': 'vertical'}"
                  orientation="vertical"
                  variant="dashed"
                  size="md"
                />
                <span>South</span>
              </div>
              <c-CDivider c-attrs="{'id': 'label-start'}" label_pos="start">Inner planets</c-CDivider>
              <div class="selector-override">
                <c-CDivider c-attrs="{'id': 'label-center'}" variant="dotted" size="lg">Asteroid belt</c-CDivider>
              </div>
              <c-CDivider c-attrs="{'id': 'inset-start'}" inset="start" c-decorative="True" />
              <div dir="rtl">
                <c-CDivider c-attrs="{'id': 'rtl-start'}" inset="start" c-decorative="True" />
              </div>
              <div
                style="--cui-divider-color: rgb(124 58 237);
                  --cui-divider-thickness: 7px;
                  --cui-divider-label-gap: 19px"
              >
                <c-CDivider c-attrs="{'id': 'brand'}">Deep sky</c-CDivider>
              </div>
              <div style="inline-size:120px">
                <c-CDivider c-attrs="{'id': 'long'}">Exceptionallylongunbrokenconstellationcatalogname</c-CDivider>
              </div>
              <div style="color-scheme:dark">
                <c-CDivider c-attrs="{'id': 'dark'}" />
              </div>
            </body>
          </html>
        """

    return str(Page())


def test_native_semantics_and_labelled_anatomy_are_exact(page: Any) -> None:
    page.set_content(_divider_page(), wait_until="load")

    semantic = page.locator("#semantic")
    decorative = page.locator("#decorative")
    vertical = page.locator("#vertical")
    labelled = page.locator("#label-center")

    assert semantic.evaluate("el => el.tagName") == "HR"
    assert semantic.get_attribute("role") is None
    assert decorative.get_attribute("aria-hidden") is not None
    assert vertical.evaluate("el => el.tagName") == "DIV"
    assert vertical.get_attribute("role") == "separator"
    assert vertical.get_attribute("aria-orientation") == "vertical"
    assert labelled.evaluate("el => el.tagName") == "DIV"
    assert labelled.get_attribute("role") is None
    assert labelled.locator(":scope > [data-citry-ui-part='line']").count() == 2
    assert labelled.locator(":scope > [data-citry-ui-part='label']").count() == 1
    assert labelled.locator(":scope > [data-citry-ui-part='line']").evaluate_all(
        "els => els.every(el => el.getAttribute('aria-hidden') === 'true')"
    )


def test_variants_sizes_vertical_stretch_and_public_overrides_compute(page: Any) -> None:
    page.set_content(_divider_page(), wait_until="load")

    vertical = page.locator("#vertical")
    labelled = page.locator("#label-center")
    brand = page.locator("#brand")

    assert vertical.evaluate("el => getComputedStyle(el).borderInlineStartStyle") == "dashed"
    assert vertical.evaluate("el => getComputedStyle(el).borderInlineStartWidth") == "2px"
    assert vertical.evaluate("el => el.getBoundingClientRect().height") == pytest.approx(80, abs=0.5)
    assert (
        labelled.locator("[data-citry-ui-part='line']").first.evaluate(
            "el => getComputedStyle(el).borderBlockStartStyle"
        )
        == "dotted"
    )
    assert (
        labelled.locator("[data-citry-ui-part='line']").first.evaluate(
            "el => getComputedStyle(el).borderBlockStartWidth"
        )
        == "4px"
    )
    assert (
        brand.locator("[data-citry-ui-part='line']").first.evaluate("el => getComputedStyle(el).borderBlockStartColor")
        == "rgb(124, 58, 237)"
    )
    assert (
        brand.locator("[data-citry-ui-part='line']").first.evaluate("el => getComputedStyle(el).borderBlockStartWidth")
        == "7px"
    )
    assert brand.evaluate("el => getComputedStyle(el).columnGap") == "19px"
    assert (
        page.locator("#label-center > [data-citry-ui-part='label']").evaluate(
            "el => getComputedStyle(el).letterSpacing"
        )
        == "3px"
    )


def test_logical_insets_and_label_position_follow_direction(page: Any) -> None:
    page.set_content(_divider_page(), wait_until="load")

    ltr = page.locator("#inset-start").evaluate(
        """el => ({
          left: el.getBoundingClientRect().left,
          parent: el.parentElement.getBoundingClientRect().left,
          width: el.getBoundingClientRect().width
        })"""
    )
    rtl = page.locator("#rtl-start").evaluate(
        """el => ({
          right: el.getBoundingClientRect().right,
          parent: el.parentElement.getBoundingClientRect().right,
          width: el.getBoundingClientRect().width
        })"""
    )
    assert ltr["left"] - ltr["parent"] == pytest.approx(24, abs=0.5)
    assert rtl["parent"] - rtl["right"] == pytest.approx(24, abs=0.5)
    assert ltr["width"] == pytest.approx(rtl["width"], abs=0.5)

    start = page.locator("#label-start > [data-citry-ui-part='line']")
    assert start.first.evaluate("el => el.getBoundingClientRect().width") < start.nth(1).evaluate(
        "el => el.getBoundingClientRect().width"
    )


def test_long_label_wraps_and_environment_modes_keep_a_visible_line(page: Any) -> None:
    page.set_content(_divider_page(), wait_until="load")

    geometry = page.locator("#long").evaluate("el => ({client: el.clientWidth, scroll: el.scrollWidth})")
    assert geometry["scroll"] <= geometry["client"]
    assert page.locator("#dark").evaluate("el => getComputedStyle(el).borderBlockStartColor") == "rgb(87, 83, 78)"

    page.emulate_media(forced_colors="active")
    assert page.locator("#semantic").evaluate("el => getComputedStyle(el).borderBlockStartColor") == "rgb(0, 0, 0)"
    page.emulate_media(forced_colors="none", media="print")
    assert page.locator("#semantic").evaluate("el => getComputedStyle(el).borderBlockStartStyle") == "solid"
