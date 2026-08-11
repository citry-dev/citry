"""Browser evidence for Container, Grid, and GridItem layout contracts."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _grid_page() -> str:
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
                body {
                  margin: 0;
                }

                .part-override [data-citry-ui-part="grid"] {
                  gap: 19px;
                }

                .class-override {
                  grid-template-columns: repeat(2, minmax(0, 1fr));
                }
              </style>
              <c-css />
            </head>
            <body>
              <c-CGrid
                c-attrs="{'id': 'responsive-grid'}"
                c-sm="2"
                c-lg="4"
                c-xl="5"
                c-xxl="6"
              >
                <span>A</span><span>B</span><span>C</span><span>D</span><span>E</span><span>F</span>
              </c-CGrid>

              <c-CGrid cols="12" c-attrs="{'id': 'span-grid'}">
                <c-CGridItem
                  c-attrs="{'id': 'span-item'}"
                  span="12"
                  sm="6"
                  lg="3"
                  xl="2"
                  xxl="1"
                >
                  Olivine
                </c-CGridItem>
              </c-CGrid>

              <div style="inline-size: 680px">
                <c-CGrid
                  c-attrs="{'id': 'intrinsic-grid'}"
                  min_col="13rem"
                >
                  <span>A</span><span>B</span><span>C</span><span>D</span><span>E</span>
                </c-CGrid>
              </div>

              <div style="inline-size: 680px; --cui-grid-min-column: 7rem">
                <c-CGrid
                  c-attrs="{'id': 'intrinsic-override'}"
                  min_col="13rem"
                >
                  <span>A</span><span>B</span><span>C</span><span>D</span><span>E</span>
                </c-CGrid>
              </div>

              <div style="--cui-grid-gap: 13px">
                <c-CGrid cols="2" c-attrs="{'id': 'variable-grid'}"><span>A</span><span>B</span></c-CGrid>
              </div>
              <div class="part-override">
                <c-CGrid cols="2" c-attrs="{'id': 'part-grid'}"><span>A</span><span>B</span></c-CGrid>
              </div>
              <c-CGrid class_="class-override" cols="4" c-attrs="{'id': 'class-grid'}">
                <span>A</span><span>B</span><span>C</span><span>D</span>
              </c-CGrid>
              <c-CGrid
                cols="12"
                style="--cui-grid-item-span: 7"
                c-attrs="{'id': 'span-variable-grid'}"
              >
                <c-CGridItem span="2" c-attrs="{'id': 'span-variable-item'}">Calcite</c-CGridItem>
              </c-CGrid>

              <c-CGrid cols="1" sm="4" c-attrs="{'id': 'outer-grid'}">
                <c-CGrid cols="2" c-attrs="{'id': 'inner-grid'}">
                  <span>A</span><span>B</span>
                </c-CGrid>
              </c-CGrid>

              <c-CContainer size="sm" c-attrs="{'id': 'fixed-container'}">Fixed</c-CContainer>
              <c-CContainer fluid c-attrs="{'id': 'fluid-container'}">Fluid</c-CContainer>
              <div dir="rtl">
                <c-CContainer gutter="xl" c-attrs="{'id': 'rtl-container'}">RTL</c-CContainer>
              </div>

              <div style="inline-size: 160px">
                <c-CGrid cols="2" c-attrs="{'id': 'narrow-grid'}">
                  <span id="narrow-child">unbreakable-geological-classification-token</span>
                  <span>Basalt</span>
                </c-CGrid>
              </div>

              <c-CContainer tag="main" c-attrs="{'id': 'semantic-container'}">
                <c-CGrid tag="ul" cols="2" c-attrs="{'id': 'semantic-grid'}">
                  <c-CGridItem tag="li" c-attrs="{'id': 'semantic-item'}">Quartz</c-CGridItem>
                </c-CGrid>
              </c-CContainer>
            </body>
          </html>
        """

    return str(Page())


def _track_count(page: Any, selector: str) -> int:
    return page.locator(selector).evaluate(
        "el => getComputedStyle(el).gridTemplateColumns.split(' ').filter(Boolean).length"
    )


@pytest.mark.parametrize(
    ("width", "expected_columns", "expected_span"),
    [
        (639, 1, "span 12"),
        (640, 2, "span 6"),
        (767, 2, "span 6"),
        (768, 2, "span 6"),
        (1023, 2, "span 6"),
        (1024, 4, "span 3"),
        (1280, 5, "span 2"),
        (1536, 6, "span 1"),
    ],
)
def test_mobile_first_breakpoints_and_missing_value_inheritance(
    page: Any,
    width: int,
    expected_columns: int,
    expected_span: str,
) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(_grid_page(), wait_until="load")

    assert _track_count(page, "#responsive-grid") == expected_columns
    assert page.locator("#span-item").evaluate("el => getComputedStyle(el).gridColumnEnd") == expected_span


def test_intrinsic_mode_fits_tracks_and_public_minimum_override_wins(page: Any) -> None:
    page.set_viewport_size({"width": 1100, "height": 900})
    page.set_content(_grid_page(), wait_until="load")

    ordinary_count = _track_count(page, "#intrinsic-grid")
    override_count = _track_count(page, "#intrinsic-override")
    assert ordinary_count == 3
    assert override_count == 5


def test_public_variables_selectors_and_unlayered_classes_win(page: Any) -> None:
    page.set_viewport_size({"width": 1100, "height": 900})
    page.set_content(_grid_page(), wait_until="load")

    assert page.locator("#variable-grid").evaluate("el => getComputedStyle(el).gap") == "13px"
    assert page.locator("#part-grid").evaluate("el => getComputedStyle(el).gap") == "19px"
    assert _track_count(page, "#class-grid") == 2
    assert page.locator("#span-variable-item").evaluate("el => getComputedStyle(el).gridColumnEnd") == "span 7"


def test_nested_grid_resets_private_breakpoint_values(page: Any) -> None:
    page.set_viewport_size({"width": 1100, "height": 900})
    page.set_content(_grid_page(), wait_until="load")

    assert _track_count(page, "#outer-grid") == 4
    assert _track_count(page, "#inner-grid") == 2


def test_container_centering_fluid_width_gutters_and_rtl(page: Any) -> None:
    page.set_viewport_size({"width": 1400, "height": 900})
    page.set_content(_grid_page(), wait_until="load")

    fixed = page.locator("#fixed-container").evaluate(
        "el => ({width: el.getBoundingClientRect().width, left: el.getBoundingClientRect().left, "
        "paddingStart: getComputedStyle(el).paddingInlineStart, "
        "paddingEnd: getComputedStyle(el).paddingInlineEnd})"
    )
    assert fixed == {"width": 640, "left": 380, "paddingStart": "16px", "paddingEnd": "16px"}

    fluid = page.locator("#fluid-container").evaluate(
        "el => ({width: el.getBoundingClientRect().width, max: getComputedStyle(el).maxInlineSize})"
    )
    assert fluid == {"width": 1400, "max": "none"}

    rtl = page.locator("#rtl-container")
    assert rtl.evaluate("el => getComputedStyle(el).direction") == "rtl"
    assert rtl.evaluate("el => getComputedStyle(el).paddingInlineStart") == "24px"
    assert rtl.evaluate("el => getComputedStyle(el).paddingInlineEnd") == "24px"


def test_zero_minimum_tracks_do_not_expand_to_long_content(page: Any) -> None:
    page.set_viewport_size({"width": 1100, "height": 900})
    page.set_content(_grid_page(), wait_until="load")

    geometry = page.locator("#narrow-grid").evaluate(
        "el => ({width: el.getBoundingClientRect().width, "
        "first: el.firstElementChild.getBoundingClientRect().width, "
        "second: el.lastElementChild.getBoundingClientRect().width})"
    )
    assert geometry["width"] == 160
    assert geometry["first"] < 80
    assert geometry["second"] < 80
    assert page.locator("#narrow-child").evaluate("el => getComputedStyle(el).minInlineSize") == "0px"


def test_semantic_roots_remain_native_and_non_focusable(page: Any) -> None:
    page.set_content(_grid_page(), wait_until="load")

    assert page.locator("#semantic-container").evaluate("el => el.tagName") == "MAIN"
    assert page.locator("#semantic-grid").evaluate("el => el.tagName") == "UL"
    assert page.locator("#semantic-item").evaluate("el => el.tagName") == "LI"
    for selector in ("#semantic-container", "#semantic-grid", "#semantic-item"):
        root = page.locator(selector)
        assert root.get_attribute("role") is None
        assert root.get_attribute("tabindex") is None
        assert root.evaluate("el => getComputedStyle(el).position") == "static"
        assert root.evaluate("el => getComputedStyle(el).overflow") == "visible"
