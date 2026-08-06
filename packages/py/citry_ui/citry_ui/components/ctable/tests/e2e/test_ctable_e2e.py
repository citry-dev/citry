"""Browser tests for the production semantic CTable."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def _static_page() -> tuple[Citry, str]:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = """
          :where(.table-brand) {
            --cui-table-background: rgb(21 43 65);
            --cui-table-foreground: rgb(245 246 247);
            --cui-table-border-color: rgb(99 140 181);
            --cui-table-header-background: rgb(31 59 87);
            --cui-table-footer-background: rgb(38 71 102);
            --cui-table-focus-color: rgb(250 204 21);
            --cui-table-min-width: 60rem;
          }

          :where(.table-brand [data-citry-ui-part="header-cell"]) {
            font-weight: 700;
          }
        """
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <section
                class="table-brand"
                style="width: 20rem; color-scheme: dark"
              >
                <p id="table-description">
                  Current project delivery status.
                </p>
                <c-CTable
                  id="project-table"
                  c-columns="columns"
                  c-rows="rows"
                  variant="outline"
                  density="compact"
                  striped
                  hover
                  sticky_header
                  column_borders
                  layout="fixed"
                  caption_side="bottom"
                  style="max-block-size: 12rem"
                  c-attrs="root_attrs"
                  c-table_attrs="table_attrs"
                >
                  <c-fill name="caption">
                    Project delivery
                  </c-fill>
                  <c-fill name="header" data="{ column }">
                    {{ column.label }} column
                  </c-fill>
                  <c-fill name="cell" data="{ row, column, cell }">
                    <c-if cond="column.key == 'action'">
                      <button
                        c-aria-label="'Open ' + row.key"
                        type="button"
                      >
                        Open
                      </button>
                    </c-if>
                    <c-else>
                      {{ cell.value }}
                    </c-else>
                  </c-fill>
                </c-CTable>
              </section>
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "columns": (
                    citry_ui.CTableColumn(
                        "project",
                        "Project",
                        row_header=True,
                        footer="Total",
                        footer_attrs={"class": "summary-label"},
                    ),
                    citry_ui.CTableColumn("owner", "Owner", footer="12 projects"),
                    citry_ui.CTableColumn(
                        "budget",
                        "Budget",
                        align="end",
                        cell_attrs={"style": {"font-variant-numeric": "tabular-nums"}},
                        footer="$4,380,000",
                    ),
                    citry_ui.CTableColumn("action", "Action", align="center", footer=""),
                ),
                "rows": tuple(
                    citry_ui.CTableRow(
                        key,
                        {
                            "project": label,
                            "owner": owner,
                            "budget": f"${(index + 3) * 100_000:,}",
                            "action": None,
                        },
                    )
                    for index, (key, label, owner) in enumerate(
                        (
                            ("apollo", "Apollo", "Ada Lovelace"),
                            ("mercury", "Mercury", "Grace Hopper"),
                            ("gemini", "Gemini", "Katherine Johnson"),
                            ("voyager", "Voyager", "Margaret Hamilton"),
                            ("cassini", "Cassini", "Annie Easley"),
                            ("juno", "Juno", "Dorothy Vaughan"),
                            ("galileo", "Galileo", "Mary Jackson"),
                            ("hubble", "Hubble", "Nancy Roman"),
                            ("kepler", "Kepler", "Vera Rubin"),
                            ("webb", "Webb", "Joan Feynman"),
                            ("new-horizons", "New Horizons", "Judith Resnik"),
                            ("parker", "Parker", "Yvonne Brill"),
                        )
                    )
                ),
                "root_attrs": {"data-workflow": "delivery"},
                "table_attrs": {"aria-describedby": "table-description"},
            }

    return app, str(Page())


def _events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-table-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class Inventory(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step += 1
                return Inventory(step=state.step)

        template = """
          <section data-inventory>
            <button
              class="advance"
              type="button"
              @c-click="advance"
            >
              Advance
            </button>
            <c-CTable
              #c-key="'inventory-table'"
              id="inventory-table"
              c-columns="columns"
              c-rows="rows"
            >
              <c-fill name="caption">
                Editable inventory
              </c-fill>
              <c-fill name="cell" data="{ row, column, cell }">
                <c-if cond="column.key == 'quantity'">
                  <input
                    c-name="row.key"
                    c-value="cell.value"
                    c-aria-label="row.key + ' quantity'"
                  />
                </c-if>
                <c-else>
                  {{ cell.value }}
                </c-else>
              </c-fill>
            </c-CTable>
          </section>
        """

        def template_data(self, kwargs, slots):
            all_rows = (
                citry_ui.CTableRow("alpha", {"name": "Alpha", "quantity": "10"}),
                citry_ui.CTableRow("beta", {"name": "Beta", "quantity": "20"}),
            )
            rows = all_rows if kwargs.step == 0 else tuple(reversed(all_rows)) if kwargs.step == 1 else all_rows[:1]
            return {
                "columns": (
                    citry_ui.CTableColumn("name", "Item", row_header=True),
                    citry_ui.CTableColumn("quantity", "Quantity"),
                ),
                "rows": rows,
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-inventory />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _nested_and_page_sticky_page() -> tuple[Citry, str]:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    nested = citry_ui.CTable(
        id="nested-table",
        columns=(citry_ui.CTableColumn("moon", "Moon"),),
        rows=(citry_ui.CTableRow("europa", {"moon": "Europa"}),),
        density="default",
        overflow="visible",
        slots={"caption": "Nested moons"},
    )

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-CTable
                id="outer-table"
                c-columns="outer_columns"
                c-rows="outer_rows"
                density="compact"
                striped
                overflow="visible"
              >
                <c-fill name="caption">
                  Planetary systems
                </c-fill>
              </c-CTable>
              <div style="block-size: 40rem"></div>
              <c-CTable
                id="page-sticky-table"
                c-columns="sticky_columns"
                c-rows="sticky_rows"
                overflow="visible"
                sticky_header
              >
                <c-fill name="caption">
                  Page-sticky moons
                </c-fill>
              </c-CTable>
              <div style="block-size: 80rem"></div>
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "outer_columns": (
                    citry_ui.CTableColumn("planet", "Planet", row_header=True),
                    citry_ui.CTableColumn("moons", "Moons"),
                ),
                "outer_rows": (
                    citry_ui.CTableRow("mars", {"planet": "Mars", "moons": "2"}),
                    citry_ui.CTableRow("jupiter", {"planet": "Jupiter", "moons": nested}),
                ),
                "sticky_columns": (citry_ui.CTableColumn("moon", "Moon"),),
                "sticky_rows": tuple(
                    citry_ui.CTableRow(f"moon-{index}", {"moon": f"Moon {index}"}) for index in range(20)
                ),
            }

    return app, str(Page())


def _state_events_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-table-state-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class Survey(Component):
        citry = app

        class Kwargs:
            step: int = 0

        class State(Kwargs):
            pass

        class Slots:
            pass

        class Events:
            def advance(self, state):
                state.step = (state.step + 1) % 4
                return Survey(step=state.step)

        template = """
          <section>
            <button class="advance-state" type="button" @c-click="advance">
              Advance state
            </button>
            <c-CTable
              #c-key="'survey-table'"
              id="survey-table"
              c-columns="columns"
              c-rows="rows"
              c-state="state"
              loading_label="Receiving survey..."
              error_label="Survey unavailable."
              empty_label="No signals found."
            >
              <c-fill name="caption">
                Signal survey
              </c-fill>
            </c-CTable>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
            state = ("ready", "loading", "error", "ready")[kwargs.step]
            rows = (citry_ui.CTableRow("signal", {"signal": "Hydrogen line"}),) if kwargs.step == 0 else ()
            return {
                "columns": (citry_ui.CTableColumn("signal", "Signal"),),
                "rows": rows,
                "state": state,
            }

    class Page(Component):
        citry = app
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <c-css />
            </head>
            <body>
              <c-survey />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def test_native_semantics_scoped_slots_and_public_identity(page: Any) -> None:
    app, html = _static_page()
    page.set_content(html, wait_until="load")

    table = page.get_by_role("table", name="Project delivery")
    assert table.locator("caption").inner_text().strip() == "Project delivery"
    assert table.locator('th[scope="col"]').all_inner_texts() == [
        "Project column",
        "Owner column",
        "Budget column",
        "Action column",
    ]
    assert table.locator('tbody th[scope="row"]').count() == 12
    assert table.locator('[data-row-key="apollo"]').count() == 1
    assert table.locator('[data-row-key="mercury"]').count() == 1
    assert table.locator('[data-column-key="budget"]').first.get_attribute("data-align") == "end"
    assert page.get_by_role("button", name="Open apollo").count() == 1
    assert table.locator("tfoot").get_attribute("data-citry-ui-part") == "footer"
    assert table.locator('tfoot th[scope="row"]').inner_text().strip() == "Total"
    assert table.locator('tfoot [data-column-key="budget"]').inner_text().strip() == "$4,380,000"
    assert page.get_by_role("region", name="Project delivery").count() == 1
    assert app.get_library_installation("citry-ui")[citry_ui.CTable].get_js() is None


def test_theme_overrides_parts_and_configuration_reach_computed_styles(page: Any) -> None:
    _, html = _static_page()
    page.set_content(html, wait_until="load")

    root = page.locator('[data-citry-ui-part="root"]')
    table = page.locator('[data-citry-ui-part="table"]')
    header = page.locator('[data-citry-ui-part="header-cell"]').first
    footer = page.locator('[data-citry-ui-part="footer-cell"]').first
    caption = page.locator('[data-citry-ui-part="caption"]')

    assert root.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(21, 43, 65)"
    assert table.evaluate("element => getComputedStyle(element).color") == "rgb(245, 246, 247)"
    assert header.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(31, 59, 87)"
    assert footer.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(38, 71, 102)"
    assert header.evaluate("element => getComputedStyle(element).fontWeight") == "700"
    assert caption.evaluate("element => getComputedStyle(element).captionSide") == "bottom"
    assert root.get_attribute("data-variant") == "outline"
    assert root.get_attribute("data-density") == "compact"
    assert root.get_attribute("data-sticky-header") == ""
    assert root.get_attribute("data-column-borders") == ""


def test_scroll_container_and_sticky_header_remain_focus_reachable(page: Any) -> None:
    _, html = _static_page()
    page.set_content(html, wait_until="load")

    root = page.locator('[data-citry-ui-part="root"]')
    header = page.locator('[data-citry-ui-part="header-cell"]').first
    assert root.get_attribute("tabindex") == "0"
    assert root.evaluate("element => element.scrollWidth > element.clientWidth") is True
    assert root.evaluate("element => element.scrollHeight > element.clientHeight") is True
    assert header.evaluate("element => getComputedStyle(element).position") == "sticky"

    root.focus()
    assert root.evaluate("element => document.activeElement === element") is True
    assert root.evaluate("element => getComputedStyle(element).outlineColor") == "rgb(250, 204, 21)"


def test_nested_tables_isolate_structural_css_and_page_sticky_mode_has_no_scroll_tab_stop(page: Any) -> None:
    _, html = _nested_and_page_sticky_page()
    page.set_content(html, wait_until="load")

    outer_second_cell = page.locator(
        '#outer-table > table > tbody > [data-row-key="jupiter"] > [data-column-key="moons"]'
    )
    nested_cell = page.locator('#nested-table > table > tbody > tr > [data-column-key="moon"]')
    assert outer_second_cell.evaluate("element => getComputedStyle(element).backgroundColor") != "rgba(0, 0, 0, 0)"
    assert nested_cell.evaluate("element => getComputedStyle(element).backgroundColor") == "rgba(0, 0, 0, 0)"
    assert outer_second_cell.evaluate("element => getComputedStyle(element).paddingBlockStart") == "8px"
    assert nested_cell.evaluate("element => getComputedStyle(element).paddingBlockStart") == "16px"

    page_sticky = page.locator("#page-sticky-table")
    sticky_header = page_sticky.locator('[data-citry-ui-part="header-cell"]')
    assert page_sticky.get_attribute("tabindex") is None
    assert page_sticky.get_attribute("role") is None
    assert sticky_header.evaluate("element => getComputedStyle(element).position") == "sticky"


def test_events_reorder_preserves_a_focused_edit_and_removal_drops_the_keyed_row(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function(READY)

    beta = page.get_by_role("textbox", name="beta quantity")
    beta.fill("draft 27")
    beta.focus()
    outcome = page.evaluate(
        """() => {
          window.__betaInput = document.querySelector('input[name="beta"]');
          window.__betaRow = document.querySelector('[data-row-key="beta"]');
          return Citry.events.send(document.querySelector('.advance'), 'advance', {}).then(
            () => ({ ok: true }),
            (error) => ({
              ok: false,
              code: error?.code,
              message: error?.message,
              detail: error?.detail,
            }),
          );
        }"""
    )
    assert outcome == {"ok": True}
    page.wait_for_function(
        "document.querySelector('[data-row-key=beta]') === document.querySelectorAll('[data-row-key]')[0]"
    )

    assert beta.input_value() == "draft 27"
    replacement = page.evaluate(
        """() => ({
          focused: document.activeElement === document.querySelector('input[name=beta]'),
          activeTag: document.activeElement?.tagName,
          activeName: document.activeElement?.getAttribute('name'),
          rowPreserved: document.querySelector('[data-row-key=beta]') === window.__betaRow,
          inputPreserved: document.querySelector('input[name=beta]') === window.__betaInput,
        })"""
    )
    assert replacement == {
        "focused": True,
        "activeTag": "INPUT",
        "activeName": "beta",
        "rowPreserved": True,
        "inputPreserved": True,
    }

    page.evaluate("() => Citry.events.send(document.querySelector('.advance'), 'advance', {})")
    page.wait_for_function("!document.querySelector('[data-row-key=beta]')")
    assert page.locator('[data-row-key="beta"]').count() == 0
    assert page.get_by_role("textbox", name="alpha quantity").count() == 1
    assert page.evaluate("document.activeElement?.isConnected") is True


def test_state_replacement_preserves_the_live_region_outside_the_busy_table(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _state_events_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function(READY)

    page.evaluate("window.__tableAnnouncer = document.querySelector('.cui-table-announcer')")
    advance = page.locator(".advance-state")

    advance.click()
    page.wait_for_function("document.querySelector('.cui-table-announcer').textContent.includes('Receiving survey')")
    assert page.locator("#survey-table > table").get_attribute("aria-busy") == "true"

    advance.click()
    page.wait_for_function("document.querySelector('.cui-table-announcer').textContent.includes('Survey unavailable')")
    assert page.locator("#survey-table > table").get_attribute("aria-busy") is None

    advance.click()
    page.wait_for_function("document.querySelector('.cui-table-announcer').textContent.includes('No signals found')")
    assert page.evaluate("document.querySelector('.cui-table-announcer') === window.__tableAnnouncer") is True
    assert page.locator('#survey-table [data-citry-ui-part="state-cell"]').get_attribute("role") is None
