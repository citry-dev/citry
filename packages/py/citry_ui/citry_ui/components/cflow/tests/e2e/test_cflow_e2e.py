"""Browser evidence for Stack and Group layout contracts."""

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
                .part-override [data-citry-ui-part="group"] {
                  gap: 19px;
                }
              </style>
              <c-css />
            </head>
            <body>
              <c-CStack
                c-attrs="{'id': 'stack'}"
                gap="lg"
                align="center"
                justify="between"
                reverse
              >
                <span>One</span><span>Two</span>
              </c-CStack>
              <div style="--cui-group-gap: 13px">
                <c-CGroup
                  c-attrs="{'id': 'group'}"
                  align="baseline"
                  justify="evenly"
                >
                  <span>Clay</span><span>Glaze</span>
                </c-CGroup>
              </div>
              <div class="part-override">
                <c-CGroup c-attrs="{'id': 'part-group'}"><span>A</span><span>B</span></c-CGroup>
              </div>
              <c-CGroup
                class_="narrow"
                c-attrs="{'id': 'wrap-group'}"
              >
                <span>Porcelain preparation</span>
                <span>Reduction schedule</span>
                <span>Celadon glaze</span>
              </c-CGroup>
              <div dir="rtl">
                <c-CGroup tag="nav" c-attrs="{'id': 'rtl-group', 'aria-label': 'Studio'}">
                  <a href="#one">الطين</a><a href="#two">التزجيج</a>
                </c-CGroup>
              </div>
              <c-CStack c-attrs="{'id': 'nested-stack'}">
                <c-CGroup c-attrs="{'id': 'nested-group'}"><span>Nested</span></c-CGroup>
              </c-CStack>
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

    stack = page.locator("#stack")
    assert stack.evaluate("el => getComputedStyle(el).display") == "flex"
    assert stack.evaluate("el => getComputedStyle(el).flexDirection") == "column-reverse"
    assert stack.evaluate("el => getComputedStyle(el).alignItems") == "center"
    assert stack.evaluate("el => getComputedStyle(el).justifyContent") == "space-between"
    assert stack.evaluate("el => getComputedStyle(el).gap") == "16px"

    group = page.locator("#group")
    assert group.evaluate("el => getComputedStyle(el).flexDirection") == "row"
    assert group.evaluate("el => getComputedStyle(el).flexWrap") == "wrap"
    assert group.evaluate("el => getComputedStyle(el).alignItems") == "baseline"
    assert group.evaluate("el => getComputedStyle(el).justifyContent") == "space-evenly"


def test_public_variable_and_part_selector_overrides_win(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    assert page.locator("#group").evaluate("el => getComputedStyle(el).gap") == "13px"
    assert page.locator("#part-group").evaluate("el => getComputedStyle(el).gap") == "19px"


def test_wrapping_prevents_horizontal_overflow_for_authored_wrappable_content(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    geometry = page.locator("#wrap-group").evaluate(
        "el => ({client: el.clientWidth, scroll: el.scrollWidth, "
        "rows: new Set([...el.children].map(c => c.offsetTop)).size})"
    )
    assert geometry["scroll"] <= geometry["client"]
    assert geometry["rows"] > 1


def test_semantic_and_nested_roots_remain_native(page: Any) -> None:
    page.set_content(_flow_page(), wait_until="load")

    rtl = page.locator("#rtl-group")
    assert rtl.evaluate("el => el.tagName") == "NAV"
    assert rtl.get_attribute("role") is None
    assert rtl.get_attribute("tabindex") is None
    assert rtl.evaluate("el => getComputedStyle(el).direction") == "rtl"
    assert page.locator("#nested-stack > #nested-group").count() == 1
