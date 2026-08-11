"""Browser evidence for List semantics, focus, and public styling."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _list_page() -> str:
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
                .selector [data-citry-ui-part="description"] {
                  letter-spacing: 2px;
                }
              </style>
              <c-css />
            </head>
            <body>
              <div class="selector" style="--cui-list-item-padding:21px">
                <c-CList label="Sky catalog" variant="surface" c-attrs="{'id': 'navigation'}">
                  <c-CListItem href="/sky" c-current="True">Sky</c-CListItem>
                  <c-CListItem c-action="True">
                    <c-fill name="default">Meteorite</c-fill>
                    <c-fill name="description">Murchison specimen</c-fill>
                  </c-CListItem>
                  <c-CListItem href="/archive" c-disabled="True">Archive</c-CListItem>
                </c-CList>
              </div>
              <c-CList
                c-ordered="True"
                marker="decimal"
                c-start="3"
                c-reversed="True"
                c-attrs="{'id': 'ordered'}"
              >
                <c-CListItem c-surface_attrs="{'id': 'three-part'}">
                  <c-fill name="start">1</c-fill>
                  <c-fill name="default">Calibrate</c-fill>
                  <c-fill name="end">Ready</c-fill>
                </c-CListItem>
                <c-CListItem>Observe</c-CListItem>
              </c-CList>
            </body>
          </html>
        """

    return str(Page())


def test_native_list_link_button_and_disabled_anatomy_are_exact(page: Any) -> None:
    page.set_content(_list_page(), wait_until="load")
    navigation = page.locator("#navigation")

    assert navigation.evaluate("el => el.tagName") == "UL"
    assert navigation.get_attribute("aria-label") == "Sky catalog"
    assert navigation.locator(":scope > li").count() == 3
    assert navigation.get_by_role("link", name="Sky").get_attribute("aria-current") == "page"
    assert navigation.get_by_role("button", name="Meteorite Murchison specimen").count() == 1
    assert navigation.get_by_text("Archive").evaluate("el => el.closest('a,button') === null")

    ordered = page.locator("#ordered")
    assert ordered.evaluate("el => el.tagName") == "OL"
    assert ordered.get_attribute("start") == "3"
    assert ordered.get_attribute("reversed") is not None


def test_public_variables_selectors_and_native_tab_order_compute(page: Any) -> None:
    page.set_content(_list_page(), wait_until="load")
    action = page.locator("#navigation").get_by_role("button")

    assert action.evaluate("el => getComputedStyle(el).paddingTop") == "21px"
    assert (
        action.locator("[data-citry-ui-part='description']").evaluate("el => getComputedStyle(el).letterSpacing")
        == "2px"
    )
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.textContent.trim()") == "Sky"
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.textContent.includes('Meteorite')")


def test_optional_item_regions_do_not_reserve_empty_grid_tracks(page: Any) -> None:
    page.set_content(_list_page(), wait_until="load")

    three_part = page.locator("#three-part")
    body_only = page.locator("#ordered [data-citry-ui-part='surface']").nth(1)
    assert three_part.evaluate("el => getComputedStyle(el).gridTemplateColumns.split(' ').length") == 3
    assert body_only.evaluate("el => getComputedStyle(el).gridTemplateColumns.split(' ').length") == 1
