"""Browser proof that Vue bindings a page writes inside transfer list item content read the page's data."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e


def _fill_scope_page() -> tuple[Citry, str]:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def js_data(self, kwargs, slots):
            return {"label": "Page label", "count": 0}

        # The content inside each transfer list item reads `label` and changes `count`,
        # both owned by the page. The page shows `count` outside the transfer list,
        # so a click that lands on another component leaves it unchanged. The
        # handler sits on a span because this family rejects focusable content.
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <p id="page-count" v-text="count"></p>
              <c-CTransferList
                name="reviewers"
                c-value="['grace']"
              >
                <c-CTransferListItem
                  value="ada"
                  label="Ada Lovelace"
                >
                  <span
                    class="fill-label"
                    v-text="label"
                  ></span>
                  <span
                    class="fill-increment"
                    @click="count++"
                  >
                    Increment
                  </span>
                </c-CTransferListItem>
                <c-CTransferListItem
                  value="grace"
                  label="Grace Hopper"
                >
                  <span
                    class="fill-label"
                    v-text="label"
                  ></span>
                  <span
                    class="fill-increment"
                    @click="count++"
                  >
                    Increment
                  </span>
                </c-CTransferListItem>
              </c-CTransferList>
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def test_transfer_list_fill_reads_and_writes_the_page_vue_data(page: Any, serve_citry_ui_live: Any) -> None:
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(f"pageerror: {error}"))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    app, html = _fill_scope_page()
    page.goto(serve_citry_ui_live(app, html) + "/")

    # Every label in the transfer list item content shows the page's `label`, not an empty
    # value read from the component that draws the transfer list.
    page.wait_for_function(
        """() => {
          const spans = [...document.querySelectorAll('.fill-label')];
          return spans.length > 0 && spans.every(span => span.textContent === 'Page label');
        }""",
        timeout=5000,
    )
    assert page.locator(".fill-label").count() == 2

    # A click handler inside the content changes the page's `count`.
    page.locator(".fill-increment").first.click()
    page.wait_for_function("document.querySelector('#page-count').textContent === '1'", timeout=5000)
    assert faults == []
