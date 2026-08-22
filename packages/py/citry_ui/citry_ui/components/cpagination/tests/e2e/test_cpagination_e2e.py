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
              <script>
                document.addEventListener("alpine:init", () => {
                  Alpine.store("paginationTest", {page: 5, details: []});
                });
              </script>
              <c-css />
            </head>
            <body x-data>
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

    current = links.locator('a[data-page="10"]')
    assert current.get_attribute("aria-current") == "page"
    assert current.get_attribute("aria-label") == "Page \u206810\u2069"
    assert links.locator('a[data-kind="page"][data-page="11"]').get_attribute("href") == "?page=11"
    assert links.locator('a[data-kind="first"]').get_attribute("href") == "?page=1"


def test_controlled_and_uncontrolled_buttons_update_the_visible_range(page: Any) -> None:
    page.set_content(_pagination_page(), wait_until="load")
    page.wait_for_selector("#controlled[data-citry-pagination-initialized]")

    controlled = page.locator("#controlled")
    page.wait_for_function("document.querySelector('#controlled [aria-current=page]').dataset.page === '5'")
    assert controlled.locator('[aria-current="page"]').get_attribute("data-page") == "5"
    controlled.get_by_role("button", name="Next page").click()
    page.wait_for_function("Alpine.store('paginationTest').page === 6")
    assert controlled.locator('button[data-kind="page"][data-page="6"]').get_attribute("aria-current") == "page"
    assert page.evaluate("Alpine.store('paginationTest').details.at(-1).previousPage") == 5
    assert page.evaluate("Alpine.store('paginationTest').details.at(-1).kind") == "next"

    uncontrolled = page.locator("#uncontrolled")
    uncontrolled.locator('button[data-kind="page"][data-page="4"]').click()
    assert uncontrolled.locator('button[data-kind="page"][data-page="4"]').get_attribute("aria-current") == "page"


def test_invalid_client_page_reports_once_per_episode_and_retains_the_last_valid_page(page: Any) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.set_content(_pagination_page(), wait_until="load")
    page.wait_for_selector("#controlled[data-citry-pagination-initialized]")
    controlled = page.locator("#controlled")
    page.wait_for_function("document.querySelector('#controlled [aria-current=page]').dataset.page === '5'")

    page.evaluate("Alpine.store('paginationTest').page = 0")
    page.evaluate("Alpine.store('paginationTest').page = 99")
    page.wait_for_timeout(0)
    assert controlled.locator('[aria-current="page"]').get_attribute("data-page") == "5"
    assert len([error for error in errors if "CPagination page" in error]) == 1

    page.evaluate("Alpine.store('paginationTest').page = 6")
    page.wait_for_function("document.querySelector('#controlled [aria-current=page]').dataset.page === '6'")
    page.evaluate("Alpine.store('paginationTest').page = 0")
    page.wait_for_timeout(0)
    assert len([error for error in errors if "CPagination page" in error]) == 2
