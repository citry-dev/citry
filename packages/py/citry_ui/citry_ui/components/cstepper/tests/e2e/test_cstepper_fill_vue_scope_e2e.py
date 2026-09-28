"""Browser proof that Vue bindings a page writes inside step content read the page's data."""

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

        # The content inside each step reads `label` and changes `count`,
        # both owned by the page. The page shows `count` outside the stepper,
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
              <c-CStepper
                label="Account setup"
                c-active="0"
              >
                <c-CStep>
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
                </c-CStep>
                <c-CStep>
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
                </c-CStep>
              </c-CStepper>
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def test_stepper_fill_reads_and_writes_the_page_vue_data(page: Any, serve_citry_ui_live: Any) -> None:
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(f"pageerror: {error}"))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    app, html = _fill_scope_page()
    page.goto(serve_citry_ui_live(app, html) + "/")

    # Every label in the step content shows the page's `label`, not an empty
    # value read from the component that draws the stepper.
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
