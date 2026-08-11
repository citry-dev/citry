"""Browser evidence for native-link and controlled Pagination behavior."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _pagination_page() -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body
              x-data
              x-init="Alpine.store('paginationTest', {page: 5, details: []})"
            >
              <c-CPagination
                c-pages="20"
                c-page="10"
                href="?page={page}"
                c-show_edges="True"
                c-attrs="{'id': 'links'}"
              />
              <c-CPagination
                c-pages="12"
                c-page="4"
                c-attrs="{'id': 'controlled'}"
                $c-props="{
                  page: $store.paginationTest.page,
                  onPageChange: (value, detail) => {
                    $store.paginationTest.details.push(detail);
                    $store.paginationTest.page = value;
                  }
                }"
              />
              <c-CPagination c-pages="8" c-page="3" c-attrs="{'id': 'uncontrolled'}" />
            </body>
          </html>
        """

    return str(Page())


def test_native_links_keep_urls_and_current_page_semantics(page: Any) -> None:
    page.set_content(_pagination_page(), wait_until="load")
    page.wait_for_selector("#links[data-citry-pagination-initialized]")
    links = page.locator("#links")

    assert links.get_by_role("link", name="Page 10").get_attribute("aria-current") == "page"
    assert links.get_by_role("link", name="Page 11").get_attribute("href") == "?page=11"
    assert links.get_by_role("link", name="First page").get_attribute("href") == "?page=1"


def test_controlled_and_uncontrolled_buttons_update_the_visible_range(page: Any) -> None:
    page.set_content(_pagination_page(), wait_until="load")
    page.wait_for_selector("#controlled[data-citry-pagination-initialized]")

    controlled = page.locator("#controlled")
    assert controlled.get_by_role("button", name="Page 5").get_attribute("aria-current") == "page"
    controlled.get_by_role("button", name="Next page").click()
    page.wait_for_function("Alpine.store('paginationTest').page === 6")
    assert controlled.get_by_role("button", name="Page 6").get_attribute("aria-current") == "page"
    assert page.evaluate("Alpine.store('paginationTest').details.at(-1).previousPage") == 5
    assert page.evaluate("Alpine.store('paginationTest').details.at(-1).kind") == "next"

    uncontrolled = page.locator("#uncontrolled")
    uncontrolled.get_by_role("button", name="Page 4").click()
    assert uncontrolled.get_by_role("button", name="Page 4").get_attribute("aria-current") == "page"


def test_invalid_client_page_reports_once_per_episode_and_retains_the_last_valid_page(page: Any) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.set_content(_pagination_page(), wait_until="load")
    page.wait_for_selector("#controlled[data-citry-pagination-initialized]")
    controlled = page.locator("#controlled")

    page.evaluate("Alpine.store('paginationTest').page = 0")
    page.evaluate("Alpine.store('paginationTest').page = 99")
    page.wait_for_timeout(0)
    assert controlled.get_by_role("button", name="Page 5").get_attribute("aria-current") == "page"
    assert len([error for error in errors if "CPagination page" in error]) == 1

    page.evaluate("Alpine.store('paginationTest').page = 6")
    page.wait_for_function("document.querySelector('#controlled [aria-current=page]').dataset.page === '6'")
    page.evaluate("Alpine.store('paginationTest').page = 0")
    page.wait_for_timeout(0)
    assert len([error for error in errors if "CPagination page" in error]) == 2
