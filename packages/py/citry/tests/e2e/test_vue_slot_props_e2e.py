"""
Browser tests for Vue slot props: `<c-slot :row="...">` passes browser data to a fill's `v-slot`.

The component that renders the slot computes each row in the browser, so only
Vue can supply it. These tests check that the fill reads the prop together
with its author's own Vue data and its Python slot data, and that the fill
follows the prop when the component's data changes.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component

pytest.importorskip("playwright.sync_api")


def _collect_page_errors(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    return errors


def _engine() -> tuple[Citry, type[Component]]:
    engine = Citry(autodiscover=False)

    class FilteredList(Component):
        citry = engine
        template = """
            <ul class="rows">
              <template
                  v-for="row in visible"
                  :key="row.id"
              >
                <li><c-slot name="item" :row="row" :row-index="row.id" c-label="'Py'" /></li>
              </template>
            </ul>
        """
        js = """
            $component({
              mounted() {
                window.__list = this;
              },
              data() {
                return { query: "" };
              },
              computed: {
                visible() {
                  return this.rows.filter((row) => row.title.includes(this.query));
                },
              },
            });
        """

        def js_data(self, kwargs, slots):
            return {"rows": [{"id": 1, "title": "Apple"}, {"id": 2, "title": "Banana"}]}

    class Page(Component):
        citry = engine
        template = """
            <main>
              <c-FilteredList>
                <c-fill name="item" v-slot="{ row, rowIndex }" data="{ label }">
                  <span class="cell" v-text="prefix + rowIndex + ':' + row.title"></span>-{{ label }}
                </c-fill>
              </c-FilteredList>
            </main>
        """
        js = """
            $component({
              data() {
                return { prefix: "#" };
              },
            });
        """

    return engine, Page


@pytest.mark.e2e
def test_a_fill_reads_vue_slot_props_with_its_authors_data_and_python_slot_data(page: Any, serve_live: Any) -> None:
    engine, page_component = _engine()
    errors = _collect_page_errors(page)
    page.goto(serve_live(engine, page_component().render().serialize(), "") + "/")
    page.wait_for_function("window.__list !== undefined")

    cells = page.locator("li").all_inner_texts()
    assert [cell.strip() for cell in cells] == ["#1:Apple-Py", "#2:Banana-Py"]

    # The prop follows the component's own browser data.
    page.evaluate("window.__list.query = 'Ban'")
    page.wait_for_function("document.querySelectorAll('li').length === 1")
    assert [cell.strip() for cell in page.locator("li").all_inner_texts()] == ["#2:Banana-Py"]
    assert errors == []
