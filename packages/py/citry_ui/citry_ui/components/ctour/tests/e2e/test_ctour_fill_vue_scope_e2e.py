"""Browser proof that Vue bindings a page writes inside tour step content read the page's data."""

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

        # The content inside each tour step reads `label` and changes `count`,
        # both owned by the page. The page shows `count` outside the tour,
        # so a click that lands on another component leaves it unchanged.
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <p id="page-count" v-text="count"></p>
              <c-CTour id="guide">
                <c-fill
                  name="activator"
                  data="{ activator_attrs }"
                >
                  <button
                    id="start"
                    c-bind="activator_attrs"
                  >
                    Start tour
                  </button>
                </c-fill>
                <c-fill name="default">
                  <c-CTourStep value="intro">
                    <c-fill name="title">Introduction</c-fill>
                    <c-fill name="default">
                      <span
                        class="fill-label"
                        v-text="label"
                      ></span>
                      <button
                        class="fill-increment"
                        type="button"
                        @click="count++"
                      >
                        Increment
                      </button>
                    </c-fill>
                  </c-CTourStep>
                  <c-CTourStep value="finish">
                    <c-fill name="title">Finish</c-fill>
                    <c-fill name="default">Last step.</c-fill>
                  </c-CTourStep>
                </c-fill>
              </c-CTour>
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def test_tour_fill_reads_and_writes_the_page_vue_data(page: Any, serve_citry_ui_live: Any) -> None:
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(f"pageerror: {error}"))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    app, html = _fill_scope_page()
    page.goto(serve_citry_ui_live(app, html) + "/")

    # A step's content renders only while the tour is open.
    page.locator("#start").click()
    page.wait_for_function("document.querySelector('#guide dialog').open", timeout=5000)

    # Every label in the tour step content shows the page's `label`, not an empty
    # value read from the component that draws the tour.
    page.wait_for_function(
        """() => {
          const spans = [...document.querySelectorAll('.fill-label')];
          return spans.length > 0 && spans.every(span => span.textContent === 'Page label');
        }""",
        timeout=5000,
    )
    assert page.locator(".fill-label").count() == 1

    # A click handler inside the content changes the page's `count`.
    page.locator(".fill-increment").first.click()
    page.wait_for_function("document.querySelector('#page-count').textContent === '1'", timeout=5000)
    assert faults == []
