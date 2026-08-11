"""Browser evidence for Button Group semantics and joined layout."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _button_group_page() -> str:
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
                .selector [data-citry-ui-part="button-group"] {
                  gap: 11px;
                }
              </style>
              <c-css />
            </head>
            <body>
              <c-CButtonGroup label="Map actions" c-attrs="{'id': 'attached'}">
                <c-CButton variant="outline">Zoom in</c-CButton>
                <c-CButton variant="outline">Zoom out</c-CButton>
              </c-CButtonGroup>
              <div class="selector">
                <c-CButtonGroup
                  label="Vertical actions"
                  orientation="vertical"
                  c-attached="False"
                  c-grow="True"
                  c-attrs="{'id': 'vertical'}"
                >
                  <c-CButton>North</c-CButton>
                  <c-CButton c-disabled="True">South</c-CButton>
                </c-CButtonGroup>
              </div>
            </body>
          </html>
        """

    return str(Page())


def test_group_semantics_and_native_button_order_are_exact(page: Any) -> None:
    page.set_content(_button_group_page(), wait_until="load")
    attached = page.locator("#attached")

    assert attached.get_attribute("role") == "group"
    assert attached.get_attribute("aria-label") == "Map actions"
    assert attached.get_by_role("button").all_inner_texts() == ["Zoom in", "Zoom out"]

    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.textContent.trim()") == "Zoom in"
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.textContent.trim()") == "Zoom out"


def test_attached_and_vertical_geometry_plus_selector_overrides_compute(page: Any) -> None:
    page.set_content(_button_group_page(), wait_until="load")
    attached_buttons = page.locator("#attached > [data-citry-ui-part='button']")
    vertical = page.locator("#vertical")

    assert attached_buttons.nth(1).evaluate("el => getComputedStyle(el).marginInlineStart") == "-1px"
    assert vertical.evaluate("el => getComputedStyle(el).flexDirection") == "column"
    assert vertical.evaluate("el => getComputedStyle(el).inlineSize") == page.locator(".selector").evaluate(
        "el => getComputedStyle(el).inlineSize"
    )
    assert vertical.evaluate("el => getComputedStyle(el).gap") == "11px"
    assert vertical.get_by_role("button", name="South").is_disabled()
