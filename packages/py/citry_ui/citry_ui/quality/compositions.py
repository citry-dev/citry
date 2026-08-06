"""Reusable composed Citry UI scenarios for repository qualification."""

from __future__ import annotations

import citry_ui
from citry import Citry, Component

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
    letter-spacing: 0.02rem;
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
  }

  :where(.brand-ledger [data-citry-ui-part="header-cell"]) {
    font-weight: 700;
    text-transform: uppercase;
  }
"""


def orbit_access_component(app: Citry) -> type[Component]:
    """Create the representative light account-access composition."""

    class CitryUiOrbitAccess(Component):
        citry = app
        css = BRAND_CSS

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="brand-orbit citry-ui-quality-stack"
            aria-labelledby="orbit-access-title"
          >
            <p>
              Orbit Cloud
            </p>
            <h1 id="orbit-access-title">
              Build your secure workspace
            </h1>
            <p>
              Start with a team plan and invite collaborators later.
            </p>
            <c-CForm
              id="orbit-access-form"
              action="/access-requests"
              method="post"
            >
              <c-CField required control_id="orbit-name">
                <c-fill name="label">
                  Full name
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="orbit-name"
                    name="name"
                    autocomplete="name"
                    placeholder="Ada Lovelace"
                  />
                </c-fill>
              </c-CField>
              <c-CField required control_id="orbit-email">
                <c-fill name="label">
                  Work email
                </c-fill>
                <c-fill name="description">
                  We use this only for workspace access.
                </c-fill>
                <c-fill name="default">
                  <c-CInput
                    id="orbit-email"
                    name="email"
                    type="email"
                    autocomplete="email"
                    placeholder="ada@example.com"
                  />
                </c-fill>
              </c-CField>
              <c-CField required control_id="orbit-plan">
                <c-fill name="label">
                  Plan
                </c-fill>
                <c-fill name="default">
                  <c-CCombobox
                    id="orbit-plan"
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
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "plans": (
                    citry_ui.CComboboxOption("starter", "Starter"),
                    citry_ui.CComboboxOption("business", "Business"),
                    citry_ui.CComboboxOption("enterprise", "Enterprise"),
                ),
            }

    return CitryUiOrbitAccess


def ledger_dashboard_component(app: Citry) -> type[Component]:
    """Create the representative dark operations-dashboard composition."""

    class CitryUiLedgerDashboard(Component):
        citry = app
        css = BRAND_CSS

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="brand-ledger citry-ui-quality-stack"
            aria-labelledby="ledger-dashboard-title"
          >
            <p>
              Ledger Operations
            </p>
            <h1 id="ledger-dashboard-title">
              Delivery dashboard
            </h1>
            <c-CDialog
              id="ledger-report-dialog"
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
                <c-CField required control_id="ledger-report-name">
                  <c-fill name="label">
                    Report name
                  </c-fill>
                  <c-fill name="default">
                    <c-CInput
                      id="ledger-report-name"
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
                <c-CButton variant="outline" c-attrs="close_attrs">
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
                  id="ledger-delivery-table"
                  c-columns="columns"
                  c-rows="rows"
                  variant="outline"
                  density="compact"
                  striped
                  hover
                  sticky_header
                  c-table_attrs="{'aria-label': 'Active delivery work'}"
                >
                  <c-fill name="caption">
                    Active delivery work
                  </c-fill>
                </c-CTable>
              </c-CTabPanel>
              <c-CTabPanel value="activity">
                <h2>
                  Recent activity
                </h2>
                <p>
                  Security review completed for Apollo.
                </p>
              </c-CTabPanel>
            </c-CTabs>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
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
            }

    return CitryUiLedgerDashboard


def repeatable_contacts_component(app: Citry) -> type[Component]:
    """Create a client-heavy repeatable contact workflow for standalone tools."""

    class CitryUiRepeatableContacts(Component):
        citry = app

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="repeatable-contacts-title"
            x-data="{
              nextId: 3,
              contacts: [
                { id: 1, name: 'Ada Lovelace', email: 'ada@example.com' },
                { id: 2, name: 'Grace Hopper', email: '' },
              ],
            }"
          >
            <h1 id="repeatable-contacts-title">
              Escalation contacts
            </h1>
            <c-CForm
              id="repeatable-contacts-form"
              action="/contacts"
              method="post"
            >
              <template x-for="contact in contacts" :key="contact.id">
                <fieldset>
                  <legend x-text="contact.name"></legend>
                  <label>
                    Work email
                    <input
                      type="email"
                      required
                      :name="`contacts[${contact.id}][email]`"
                      x-model="contact.email"
                    />
                  </label>
                  <button
                    type="button"
                    @click="contacts = contacts.filter((item) => item.id !== contact.id)"
                  >
                    Remove
                  </button>
                </fieldset>
              </template>
              <c-CButton
                type="button"
                variant="outline"
                @click="contacts.push({ id: nextId++, name: 'New contact', email: '' })"
              >
                Add contact
              </c-CButton>
              <c-CButton
                type="button"
                variant="ghost"
                @click="contacts.reverse()"
              >
                Reverse order
              </c-CButton>
              <c-CButton type="submit">
                Save contacts
              </c-CButton>
            </c-CForm>
          </section>
        """

    return CitryUiRepeatableContacts
