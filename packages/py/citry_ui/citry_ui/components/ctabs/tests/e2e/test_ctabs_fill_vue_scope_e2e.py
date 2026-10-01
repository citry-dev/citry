"""Browser proof that Vue bindings a page writes inside tabs and panels read the page's data."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e


class PingIn:
    value: str


def _fill_scope_page(received: list[str]) -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-tabs-fill-scope-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        class Events:
            def ping(self, data: PingIn) -> None:
                # The server records what the browser sent, so the test can
                # prove the Events binding in the fill read the page's data.
                received.append(data.value)

        def js_data(self, kwargs, slots):
            return {"label": "Page label", "detail": "Page detail", "count": 0, "text": ""}

        # Every binding inside the tab and panel content reads the page's
        # browser data. The page shows `count` and `text` outside the tabs, so
        # a write that lands on another component stays invisible there.
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <p id="page-count" v-text="count"></p>
              <p id="page-text" v-text="text"></p>
              <c-CTabs
                default_value="one"
                aria_label="Fill scope"
              >
                <c-for each="value in values">
                  <c-CTab
                    #c-key="value"
                    c-value="value"
                  >
                    <span
                      class="tab-label"
                      c-data-tab="value"
                      v-text="label"
                    ></span>
                  </c-CTab>
                </c-for>
                <c-CTabPanel value="one">
                  <b id="panel-one-detail" v-text="detail"></b>
                  <button
                    id="panel-increment"
                    type="button"
                    @click="count++"
                  >
                    Increment
                  </button>
                  <input
                    id="panel-model"
                    v-model="text"
                  />
                  <button
                    id="panel-ping"
                    type="button"
                    @c-click="ping({value: label})"
                  >
                    Ping
                  </button>
                </c-CTabPanel>
                <c-CTabPanel value="two">
                  <b
                    id="panel-two-detail"
                    v-text="detail + ' two'"
                  ></b>
                  <span
                    id="panel-two-count"
                    v-text="count"
                  ></span>
                </c-CTabPanel>
                <c-CTabPanel value="three">
                  <b id="panel-three-label" v-text="label"></b>
                </c-CTabPanel>
              </c-CTabs>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {"values": ("one", "two", "three")}

    dispatcher_for(app)
    return app, str(Page())


def test_tab_and_panel_fills_read_and_write_the_page_vue_data(page: Any, serve_citry_ui_live: Any) -> None:
    received: list[str] = []
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(f"pageerror: {error}"))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    app, html = _fill_scope_page(received)
    page.goto(serve_citry_ui_live(app, html) + "/")
    page.wait_for_function("document.querySelector('[data-citry-tabs-root][data-citry-tabs-initialized]') !== null")

    # Each keyed tab label reads `label` from the page, not from the internal
    # component that draws the tab list.
    page.wait_for_function("document.querySelector('#panel-one-detail').textContent === 'Page detail'")
    labels = page.eval_on_selector_all(
        ".tab-label", "spans => spans.map(span => [span.dataset.tab, span.textContent])"
    )
    assert labels == [["one", "Page label"], ["two", "Page label"], ["three", "Page label"]]

    # A click handler in the panel changes the page's `count`, shown outside the tabs.
    page.locator("#panel-increment").click()
    page.locator("#panel-increment").click()
    page.wait_for_function("document.querySelector('#page-count').textContent === '2'")

    # `v-model` in the panel writes the page's `text`.
    page.locator("#panel-model").fill("typed")
    page.wait_for_function("document.querySelector('#page-text').textContent === 'typed'")

    # The Events binding reads `label` from the page and reaches the server.
    with page.expect_response(lambda response: "/ext/events/" in response.url):
        page.locator("#panel-ping").click()
    assert received == ["Page label"]

    # Switching tabs still works, and the newly shown panel reads the same
    # page state the first panel changed.
    page.locator('[role="tab"][data-value="two"]').click()
    assert page.locator('[role="tab"][data-value="two"]').get_attribute("aria-selected") == "true"
    assert page.locator("#panel-two-detail").is_visible()
    assert page.locator("#panel-two-detail").text_content() == "Page detail two"
    assert page.locator("#panel-two-count").text_content() == "2"

    page.locator('[role="tab"][data-value="three"]').click()
    assert page.locator("#panel-three-label").is_visible()
    assert page.locator("#panel-three-label").text_content() == "Page label"
    assert faults == []
