from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            return {
                "items": (
                    citry_ui.CBreadcrumbItem("Home", "/"),
                    citry_ui.CBreadcrumbItem("Library", "/library"),
                    citry_ui.CBreadcrumbItem("The green room"),
                )
            }

        css = """
          :where(.trail-brand) {
            --cui-breadcrumbs-link-color: rgb(21 128 61);
            --cui-breadcrumbs-gap: 18px;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head><meta charset="utf-8" /><c-css /></head>
            <body>
              <c-CBreadcrumbs c-items="items" label="Room location" class_="trail-brand" />
              <div style="inline-size: 160px">
                <c-CBreadcrumbs c-items="items" label="Scrollable location" c-wrap="False" />
              </div>
              <div dir="rtl"><c-CBreadcrumbs c-items="items" label="موقع الغرفة" separator="←" /></div>
            </body>
          </html>
        """

    return str(Page())


def test_breadcrumbs_native_semantics_focus_and_css(page: Any):
    page.set_content(_page(), wait_until="load")
    nav = page.get_by_role("navigation", name="Room location")
    assert nav.locator("ol > li").count() == 3
    assert nav.get_by_role("link").count() == 2
    current = nav.locator('[aria-current="page"]')
    assert current.text_content().strip() == "The green room"
    assert nav.locator('[data-citry-ui-part="separator"]').count() == 2
    assert (
        nav.locator('[data-citry-ui-part="link"]').first.evaluate("element => getComputedStyle(element).color")
        == "rgb(21, 128, 61)"
    )
    assert nav.locator("ol").evaluate("element => getComputedStyle(element).gap") == "18px"
    page.keyboard.press("Tab")
    assert nav.get_by_role("link", name="Home").evaluate("element => document.activeElement === element")


def test_nowrap_scroll_and_rtl_are_browser_native(page: Any):
    page.set_content(_page(), wait_until="load")
    scroll = page.get_by_role("navigation", name="Scrollable location").locator("ol")
    assert scroll.evaluate("element => getComputedStyle(element).flexWrap") == "nowrap"
    assert scroll.evaluate("element => getComputedStyle(element).overflowX") == "auto"
    assert scroll.evaluate("element => element.scrollWidth >= element.clientWidth")
    rtl = page.get_by_role("navigation", name="موقع الغرفة")
    assert rtl.evaluate("element => getComputedStyle(element).direction") == "rtl"
    assert rtl.locator('[data-citry-ui-part="separator"]').first.text_content().strip() == "←"
