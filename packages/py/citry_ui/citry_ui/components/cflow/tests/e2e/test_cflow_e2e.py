"""Browser evidence for Col and Row layout contracts."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _flow_page() -> str:
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
                .part-override [data-citry-ui-part="row"] {
                  gap: 19px;
                }
              </style>
              <c-css />
            </head>
            <body>
              <c-CCol
                c-attrs="{'id': 'col'}"
                gap="lg"
                align="center"
                justify="between"
                reverse
              >
                <span>One</span><span>Two</span>
              </c-CCol>
              <div style="--cui-row-gap: 13px">
                <c-CRow
                  c-attrs="{'id': 'row'}"
                  align="baseline"
                  justify="evenly"
                >
                  <span>Clay</span><span>Glaze</span>
                </c-CRow>
              </div>
              <div class="part-override">
                <c-CRow c-attrs="{'id': 'part-row'}"><span>A</span><span>B</span></c-CRow>
              </div>
              <c-CRow
                class_="narrow"
                c-attrs="{'id': 'wrap-row'}"
              >
                <span>Porcelain preparation</span>
                <span>Reduction schedule</span>
                <span>Celadon glaze</span>
              </c-CRow>
              <div dir="rtl">
                <c-CRow tag="nav" c-attrs="{'id': 'rtl-row', 'aria-label': 'Studio'}">
                  <a href="#one">الطين</a><a href="#two">التزجيج</a>
                </c-CRow>
              </div>
              <c-CCol c-attrs="{'id': 'nested-col'}">
                <c-CRow c-attrs="{'id': 'nested-row'}"><span>Nested</span></c-CRow>
              </c-CCol>
            </body>
          </html>
        """
        css = """
          :where(.narrow) {
            inline-size: 150px;
          }

          :where(.narrow > span) {
            max-inline-size: 100%;
            overflow-wrap: anywhere;
          }
        """

    return str(Page())


def test_stack_and_group_compute_the_requested_flex_contract(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    col = page.locator("#col")
    assert col.evaluate("el => getComputedStyle(el).display") == "flex"
    assert col.evaluate("el => getComputedStyle(el).flexDirection") == "column-reverse"
    assert col.evaluate("el => getComputedStyle(el).alignItems") == "center"
    assert col.evaluate("el => getComputedStyle(el).justifyContent") == "space-between"
    assert col.evaluate("el => getComputedStyle(el).gap") == "16px"

    row = page.locator("#row")
    assert row.evaluate("el => getComputedStyle(el).flexDirection") == "row"
    assert row.evaluate("el => getComputedStyle(el).flexWrap") == "wrap"
    assert row.evaluate("el => getComputedStyle(el).alignItems") == "baseline"
    assert row.evaluate("el => getComputedStyle(el).justifyContent") == "space-evenly"


def test_public_variable_and_part_selector_overrides_win(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    assert page.locator("#row").evaluate("el => getComputedStyle(el).gap") == "13px"
    assert page.locator("#part-row").evaluate("el => getComputedStyle(el).gap") == "19px"


def test_wrapping_prevents_horizontal_overflow_for_authored_wrappable_content(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    geometry = page.locator("#wrap-row").evaluate(
        "el => ({client: el.clientWidth, scroll: el.scrollWidth, "
        "rows: new Set([...el.children].map(c => c.offsetTop)).size})"
    )
    assert geometry["scroll"] <= geometry["client"]
    assert geometry["rows"] > 1


def test_semantic_and_nested_roots_remain_native(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    rtl = page.locator("#rtl-row")
    assert rtl.evaluate("el => el.tagName") == "NAV"
    assert rtl.get_attribute("role") is None
    assert rtl.get_attribute("tabindex") is None
    assert rtl.evaluate("el => getComputedStyle(el).direction") == "rtl"
    assert page.locator("#nested-col > #nested-row").count() == 1
