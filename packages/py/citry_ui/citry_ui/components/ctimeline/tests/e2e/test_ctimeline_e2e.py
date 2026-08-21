"""Browser evidence for Timeline semantics and public layout."""

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
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8" /><c-css /></head><body>
            <div style="--cui-timeline-item-gap:21px">
              <c-CTimeline label="History" side="alternate" c-attrs="{'id':'vertical'}">
                <c-CTimelineItem state="complete">
                  <c-fill name="opposite"><time>Yesterday</time></c-fill>
                  <c-fill name="default"><a href="#a">Created</a></c-fill>
                </c-CTimelineItem>
                <c-CTimelineItem state="current"><button type="button">Current action</button></c-CTimelineItem>
                <c-CTimelineItem state="pending">Pending</c-CTimelineItem>
              </c-CTimeline>
            </div>
            <div dir="rtl" style="inline-size:260px">
              <c-CTimeline label="Roadmap" orientation="horizontal" side="alternate" c-attrs="{'id':'horizontal'}">
                <c-CTimelineItem>A long first milestone</c-CTimelineItem>
                <c-CTimelineItem>B</c-CTimelineItem>
                <c-CTimelineItem>C</c-CTimelineItem>
              </c-CTimeline>
            </div>
          </body></html>
        """

    return str(Page())


def test_ordered_list_semantics_current_state_and_native_tab_order(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    timeline = page.locator("#vertical")

    assert timeline.evaluate("el => el.tagName") == "OL"
    assert timeline.locator(":scope > li").count() == 3
    assert timeline.locator("[aria-current='true']").count() == 1
    assert timeline.locator("[data-citry-ui-part='track']").first.get_attribute("aria-hidden") == "true"
    focusable = timeline.locator("a, button")
    assert focusable.all_text_contents() == ["Created", "Current action"]
    focusable.nth(0).focus()
    assert page.evaluate("document.activeElement.textContent") == "Created"
    focusable.nth(1).focus()
    assert page.evaluate("document.activeElement.textContent") == "Current action"


def test_public_spacing_alternate_sides_and_horizontal_overflow_compute(page: Any) -> None:
    page.set_content(_page(), wait_until="load")
    vertical = page.locator("#vertical")
    items = vertical.locator(":scope > li")

    assert items.nth(0).get_attribute("data-side") == "end"
    assert items.nth(1).get_attribute("data-side") == "start"
    assert items.nth(2).get_attribute("data-side") == "end"
    assert (
        items.nth(0).locator("[data-citry-ui-part='content']").evaluate("el => getComputedStyle(el).paddingTop")
        == "21px"
    )

    horizontal = page.locator("#horizontal")
    assert horizontal.evaluate("el => getComputedStyle(el).overflowX") == "auto"
    assert horizontal.evaluate("el => el.scrollWidth > el.clientWidth")
