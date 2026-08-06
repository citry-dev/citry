"""Representative Phase 7 pages and public customization contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

BRAND_CSS = """
  :where(.brand-orbit) {
    color-scheme: light;
    background-color: Canvas;
    color: CanvasText;
    --cui-button-background: rgb(0 88 83);
    --cui-button-foreground: rgb(255 255 255);
    --cui-button-border-color: rgb(0 88 83);
    --cui-button-hover-background: rgb(0 68 64);
    --cui-button-radius: 999px;
    --cui-field-label-color: rgb(20 55 52);
    --cui-input-background: rgb(248 255 253);
    --cui-input-foreground: rgb(15 47 44);
    --cui-input-border-color: rgb(86 130 125);
    --cui-input-focus-color: rgb(0 88 83);
    --cui-input-radius: 12px;
    --cui-combobox-background: rgb(248 255 253);
    --cui-combobox-foreground: rgb(15 47 44);
    --cui-combobox-border-color: rgb(86 130 125);
    --cui-combobox-focus-color: rgb(0 88 83);
    --cui-combobox-radius: 12px;
  }

  :where(.brand-orbit [data-citry-ui-part="content"]) {
    letter-spacing: 0.32px;
  }

  :where(.brand-ledger) {
    color-scheme: dark;
    background-color: Canvas;
    color: CanvasText;
    --cui-button-background: rgb(109 40 217);
    --cui-button-foreground: rgb(255 255 255);
    --cui-button-border-color: rgb(167 139 250);
    --cui-button-hover-background: rgb(91 33 182);
    --cui-button-radius: 6px;
    --cui-tabs-accent: rgb(196 181 253);
    --cui-tabs-active-background: rgb(46 36 74);
    --cui-tabs-border-color: rgb(92 77 128);
    --cui-table-background: rgb(24 24 32);
    --cui-table-foreground: rgb(244 244 247);
    --cui-table-border-color: rgb(76 75 90);
    --cui-table-header-background: rgb(35 34 48);
    --cui-table-min-width: 48rem;
    --cui-dialog-background: rgb(32 31 44);
    --cui-dialog-foreground: rgb(250 250 252);
    --cui-dialog-border-color: rgb(92 77 128);
    --cui-dialog-radius: 6px;
    --cui-input-background: rgb(24 24 32);
    --cui-input-foreground: rgb(244 244 247);
    --cui-input-border-color: rgb(92 91 108);
  }

  :where(.brand-ledger [data-citry-ui-part="header-cell"]) {
    font-weight: 700;
    text-transform: uppercase;
  }
"""


def _repository_root() -> Path:
    for directory in Path(__file__).resolve().parents:
        if (directory / "package.json").is_file() and (directory / "pyproject.toml").is_file():
            return directory
    msg = "Could not find the Citry repository root from the e2e test path."
    raise RuntimeError(msg)


def _composition_page() -> tuple[Citry, str]:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        css = BRAND_CSS
        template = """
          <!doctype html>
          <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>Citry UI Phase 7 compositions</title>
              <c-css />
            </head>
            <body>
              <main>
                <section class="brand-orbit" aria-labelledby="access-title">
                  <p>Orbit Cloud</p>
                  <h1 id="access-title">Build your secure workspace</h1>
                  <p>Start with a team plan and invite collaborators later.</p>
                  <c-CForm
                    id="access-form"
                    action="/access-requests"
                    method="post"
                  >
                    <c-CField required control_id="access-name">
                      <c-fill name="label">
                        Full name
                      </c-fill>
                      <c-fill name="default">
                        <c-CInput
                          name="name"
                          autocomplete="name"
                          placeholder="Ada Lovelace"
                        />
                      </c-fill>
                    </c-CField>
                    <c-CField required control_id="access-email">
                      <c-fill name="label">
                        Work email
                      </c-fill>
                      <c-fill name="default">
                        <c-CInput
                          name="email"
                          type="email"
                          autocomplete="email"
                          placeholder="ada@example.com"
                        />
                      </c-fill>
                      <c-fill name="description">
                        We use this only for workspace access.
                      </c-fill>
                    </c-CField>
                    <c-CField required control_id="access-plan">
                      <c-fill name="label">
                        Plan
                      </c-fill>
                      <c-fill name="default">
                        <c-CCombobox
                          name="plan"
                          c-options="plans"
                          value="starter"
                        />
                      </c-fill>
                    </c-CField>
                    <c-CButton type="submit">
                      Request access
                    </c-CButton>
                  </c-CForm>
                </section>

                <section class="brand-ledger" aria-labelledby="dashboard-title">
                  <p>Ledger Operations</p>
                  <h1 id="dashboard-title">Delivery dashboard</h1>
                  <c-CDialog
                    id="report-dialog"
                  >
                    <c-fill
                      name="activator"
                      data="{ activator_attrs }"
                    >
                      <c-CButton c-attrs="activator_attrs">
                        Create report
                      </c-CButton>
                    </c-fill>
                    <c-fill name="title">
                      Create delivery report
                    </c-fill>
                    <c-fill name="description">
                      Choose a clear name for the saved report.
                    </c-fill>
                    <c-fill name="default">
                      <c-CField required control_id="report-name">
                        <c-fill name="label">
                          Report name
                        </c-fill>
                        <c-fill name="default">
                          <c-CInput
                            name="report_name"
                            c-attrs="{'autofocus': True}"
                          />
                        </c-fill>
                      </c-CField>
                    </c-fill>
                    <c-fill
                      name="actions"
                      data="{ close_attrs }"
                    >
                      <c-CButton
                        variant="outline"
                        c-attrs="close_attrs"
                      >
                        Cancel
                      </c-CButton>
                      <c-CButton>
                        Create
                      </c-CButton>
                    </c-fill>
                  </c-CDialog>
                  <c-CTabs
                    default_value="overview"
                    aria_label="Dashboard views"
                  >
                    <c-CTab value="overview">
                      Overview
                    </c-CTab>
                    <c-CTab value="activity">
                      Activity
                    </c-CTab>
                    <c-CTabPanel value="overview">
                      <c-CTable
                        id="delivery-table"
                        c-columns="columns"
                        c-rows="rows"
                        variant="outline"
                        density="compact"
                        striped
                        hover
                        sticky_header
                        c-table_attrs="table_attrs"
                      >
                        <c-fill name="caption">
                          Active delivery work
                        </c-fill>
                      </c-CTable>
                    </c-CTabPanel>
                    <c-CTabPanel value="activity">
                      <h2>Recent activity</h2>
                      <p>Security review completed for Apollo.</p>
                    </c-CTabPanel>
                  </c-CTabs>
                </section>
              </main>
              <c-js />
            </body>
          </html>
        """

        def template_data(self, kwargs, slots):
            return {
                "plans": (
                    citry_ui.CComboboxOption("starter", "Starter"),
                    citry_ui.CComboboxOption("business", "Business"),
                    citry_ui.CComboboxOption("enterprise", "Enterprise"),
                ),
                "columns": (
                    citry_ui.CTableColumn("project", "Project", row_header=True),
                    citry_ui.CTableColumn("owner", "Owner"),
                    citry_ui.CTableColumn("stage", "Stage"),
                    citry_ui.CTableColumn("health", "Health"),
                ),
                "rows": (
                    citry_ui.CTableRow(
                        "apollo",
                        {
                            "project": "Apollo",
                            "owner": "Ada Lovelace",
                            "stage": "Security review",
                            "health": "On track",
                        },
                    ),
                    citry_ui.CTableRow(
                        "mercury",
                        {
                            "project": "Mercury",
                            "owner": "Grace Hopper",
                            "stage": "Rollout",
                            "health": "Needs attention",
                        },
                    ),
                ),
                "table_attrs": {"aria-label": "Active delivery work"},
            }

    return app, str(Page())


def test_two_brands_use_only_public_customization_and_reach_computed_styles(page: Any) -> None:
    assert ".cui-" not in BRAND_CSS
    assert "--_cui-" not in BRAND_CSS
    assert "!important" not in BRAND_CSS
    assert BRAND_CSS.replace("data-citry-ui-part", "").find("data-citry-") == -1

    _, html = _composition_page()
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        """() => (
          document.querySelectorAll('[data-citry-button-initialized]').length >= 4
          && document.querySelector('[data-citry-tabs-root]')
          && document.querySelector('[data-citry-dialog-initialized]')
        )"""
    )

    orbit_button = page.get_by_role("button", name="Request access")
    ledger_button = page.get_by_role("button", name="Create report")
    orbit_content = orbit_button.locator('[data-citry-ui-part="content"]')
    table = page.get_by_role("table", name="Active delivery work")
    header = table.locator('[data-citry-ui-part="header-cell"]').first

    assert orbit_button.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(0, 88, 83)"
    assert orbit_button.evaluate("element => getComputedStyle(element).borderRadius") == "999px"
    assert orbit_content.evaluate("element => getComputedStyle(element).letterSpacing") == "0.32px"
    assert ledger_button.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(109, 40, 217)"
    assert ledger_button.evaluate("element => getComputedStyle(element).borderRadius") == "6px"
    assert table.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(24, 24, 32)"
    assert header.evaluate("element => getComputedStyle(element).textTransform") == "uppercase"
    assert header.evaluate("element => getComputedStyle(element).fontWeight") == "700"


def test_public_form_dashboard_and_dialog_work_as_complete_compositions(page: Any) -> None:
    _, html = _composition_page()
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        """() => (
          document.querySelector('#access-form')?.hasAttribute('data-citry-form-initialized')
          && document.querySelector('[data-citry-tabs-root]')?.hasAttribute('data-citry-tabs-initialized')
        )"""
    )

    page.evaluate(
        """() => {
          const form = document.querySelector('#access-form');
          form.addEventListener('submit', (event) => {
            event.preventDefault();
            window.__accessSubmission = Object.fromEntries(new FormData(form));
          });
        }"""
    )
    page.get_by_role("textbox", name="Full name").fill("Lin Chen")
    page.get_by_role("textbox", name="Work email").fill("lin@example.com")
    page.get_by_role("button", name="Request access").click()
    page.wait_for_function("window.__accessSubmission?.plan === 'starter'")
    assert page.evaluate("window.__accessSubmission") == {
        "name": "Lin Chen",
        "email": "lin@example.com",
        "plan": "starter",
    }

    activity = page.get_by_role("tab", name="Activity")
    activity.click()
    assert page.get_by_role("tabpanel", name="Activity").is_visible()
    assert page.get_by_role("tabpanel", name="Overview").is_hidden()
    page.get_by_role("tab", name="Overview").click()
    assert page.get_by_role("table", name="Active delivery work").is_visible()

    trigger = page.get_by_role("button", name="Create report")
    trigger.click()
    page.wait_for_function("document.querySelector('#report-dialog').open")
    dialog = page.locator("#report-dialog")
    report_name = page.locator("#report-name")
    assert report_name.evaluate("element => document.activeElement === element") is True
    assert dialog.evaluate("element => getComputedStyle(element).backgroundColor") == "rgb(32, 31, 44)"
    page.get_by_role("button", name="Cancel").click()
    page.wait_for_function("!document.querySelector('#report-dialog').open")
    assert trigger.evaluate("element => document.activeElement === element") is True

    page.set_viewport_size({"width": 360, "height": 760})
    table_root = page.locator('[data-citry-ui-part="root"]').last
    assert table_root.evaluate("element => element.scrollWidth > element.clientWidth") is True
    table_root.focus()
    assert table_root.evaluate("element => document.activeElement === element") is True


def test_representative_page_has_no_serious_or_critical_axe_violations(page: Any) -> None:
    _, html = _composition_page()
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        """() => (
          document.querySelector('#access-form')?.hasAttribute('data-citry-form-initialized')
          && document.querySelector('[data-citry-tabs-root]')?.hasAttribute('data-citry-tabs-initialized')
        )"""
    )

    axe_path = _repository_root() / "node_modules" / "axe-core" / "axe.min.js"
    assert axe_path.is_file(), "run `pnpm install` at the repository root before Citry UI axe tests"
    page.add_script_tag(path=str(axe_path))

    def serious_or_critical() -> list[dict[str, object]]:
        result = page.evaluate(
            """async () => {
              const result = await axe.run(document, {
                resultTypes: ['violations'],
              });
              return result.violations.filter(
                (violation) => violation.impact === 'serious' || violation.impact === 'critical',
              );
            }"""
        )
        return result

    assert serious_or_critical() == []

    page.get_by_role("button", name="Create report").click()
    page.wait_for_function("document.querySelector('#report-dialog').open")
    assert serious_or_critical() == []


def test_local_tabs_interaction_stays_inside_desktop_and_narrow_viewport_budgets(page: Any) -> None:
    _, html = _composition_page()
    page.set_content(html, wait_until="load")
    page.wait_for_function(
        "document.querySelector('[data-citry-tabs-root]')?.hasAttribute('data-citry-tabs-initialized')"
    )

    def p95_for_thirty_selections() -> float:
        durations = page.evaluate(
            """() => {
              const tabs = [...document.querySelectorAll('[data-citry-tabs-tab]')];
              const durations = [];
              for (let index = 0; index < 30; index += 1) {
                const start = performance.now();
                tabs[index % tabs.length].click();
                durations.push(performance.now() - start);
              }
              return durations.sort((left, right) => left - right);
            }"""
        )
        return durations[28]

    assert p95_for_thirty_selections() <= 50
    page.set_viewport_size({"width": 360, "height": 760})
    assert p95_for_thirty_selections() <= 100
