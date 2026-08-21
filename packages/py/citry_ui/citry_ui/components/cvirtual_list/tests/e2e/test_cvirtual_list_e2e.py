"""Browser evidence for complete-DOM and controlled Virtual List behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    raise RuntimeError("Could not locate repository root for Virtual List browser tests.")


def _page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html><html lang="en"><head><meta charset="utf-8">
          <title>Virtual List evidence</title><c-css /></head>
          <body x-data>
            <c-CVirtualList
              aria_label="Complete activity"
              c-viewport_size="160"
              c-attrs="{'id':'complete'}"
            >
              <c-for each="index in complete_indexes">
                <c-CVirtualListItem c-item_key="f'complete-{index}'">Activity {{ index + 1 }}</c-CVirtualListItem>
              </c-for>
            </c-CVirtualList>

            <c-CVirtualWindow
              aria_label="Windowed records"
              c-total_count="200"
              c-start_index="36"
              c-item_size="40"
              c-viewport_size="200"
              c-overscan="2"
              c-initial_index="40"
              c-attrs="{'id':'window'}"
              $c-props="{
                itemSize:$store.virtual.itemSize,
                overscan:$store.virtual.overscan,
                onRangeChange:(detail)=>$store.virtual.events.push({
                  startIndex:detail.startIndex,
                  endIndex:detail.endIndex,
                  visibleStartIndex:detail.visibleStartIndex,
                  visibleEndIndex:detail.visibleEndIndex,
                  requestId:detail.requestId,
                  reason:detail.reason,
                }),
              }"
            >
              <c-for each="index in window_indexes">
                <c-CVirtualListItem c-item_key="f'window-{index}'">Record {{ index + 1 }}</c-CVirtualListItem>
              </c-for>
            </c-CVirtualWindow>
          </body></html>
        """
        js = """
          Alpine.store('virtual', {itemSize:40,overscan:2,events:[]});
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "complete_indexes": list(range(48)),
                "window_indexes": list(range(36, 50)),
            }

    return str(Page())


def _load(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_page(), wait_until="load")
    page.wait_for_selector("#window[data-citry-virtual-window-initialized]")
    page.wait_for_function("document.querySelector('#window').scrollTop === 1600")
    return errors


def test_complete_dom_keeps_all_items_and_uses_browser_containment(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#complete")
    items = root.locator(':scope > [data-citry-ui-part="track"] > [data-citry-ui-part="item"]')

    assert items.count() == 48
    assert root.get_attribute("data-citry-virtual-list-initialized") is None
    assert items.first.evaluate("element => getComputedStyle(element).contentVisibility") == "auto"
    assert items.nth(47).get_attribute("data-item-key") == "complete-47"
    assert items.nth(47).get_attribute("aria-posinset") is None
    assert errors == []


def test_window_geometry_scroll_requests_and_reactive_inputs(page: Any) -> None:
    errors = _load(page)
    root = page.locator("#window")
    items = root.locator(':scope > [data-citry-ui-part="track"] > [data-citry-ui-part="item"]')
    before = root.locator('[data-citry-virtual-list-spacer="before"]')
    after = root.locator('[data-citry-virtual-list-spacer="after"]')

    assert items.count() == 14
    assert items.first.get_attribute("data-index") == "36"
    assert items.first.get_attribute("aria-posinset") == "37"
    assert items.first.get_attribute("aria-setsize") == "200"
    assert before.evaluate("element => element.style.blockSize") == "1440px"
    assert after.evaluate("element => element.style.blockSize") == "6000px"
    assert root.get_attribute("data-pending") is None

    root.evaluate("element => { element.scrollTop = 4000; element.dispatchEvent(new Event('scroll')); }")
    page.wait_for_function("Alpine.store('virtual').events.length > 0")
    event = page.evaluate("Alpine.store('virtual').events.at(-1)")
    assert event["startIndex"] == 98
    assert event["endIndex"] == 107
    assert event["visibleStartIndex"] == 100
    assert event["visibleEndIndex"] == 105
    assert event["requestId"] >= 1
    assert event["reason"] == "scroll"
    assert root.get_attribute("data-pending") == ""
    assert root.get_attribute("aria-busy") == "true"

    page.evaluate("Alpine.store('virtual').itemSize = 50; Alpine.store('virtual').overscan = 4")
    page.wait_for_function(
        "document.querySelector('#window').style.getPropertyValue('--cui-virtual-list-item-size') === '50px'"
    )
    assert before.evaluate("element => element.style.blockSize") == "1800px"
    assert after.evaluate("element => element.style.blockSize") == "7500px"
    assert errors == []


def test_keyboard_scroll_surface_environment_axe_and_cleanup(page: Any) -> None:
    errors = _load(page)
    complete = page.locator("#complete")
    complete.focus()
    page.keyboard.press("PageDown")
    page.wait_for_function("document.querySelector('#complete').scrollTop > 0")

    page.emulate_media(forced_colors="active", reduced_motion="reduce")
    assert complete.evaluate("element => getComputedStyle(element).overflowY") in {"auto", "scroll"}
    axe = _root() / "node_modules" / "axe-core" / "axe.min.js"
    page.add_script_tag(path=str(axe))
    violations = page.evaluate(
        """async () => (await axe.run(document, {resultTypes:['violations']})).violations
          .filter(item => ['serious','critical'].includes(item.impact)).map(item => item.id)"""
    )
    assert violations == []

    page.locator("#window").evaluate("element => element.remove()")
    page.wait_for_timeout(50)
    assert errors == []
