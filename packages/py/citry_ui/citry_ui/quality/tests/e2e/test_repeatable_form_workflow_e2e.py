"""Phase 7 repeatable business-form composition and lifecycle test."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component

pytestmark = pytest.mark.e2e

READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def _workflow_page() -> tuple[Citry, str]:
    app = Citry(secret="citry-ui-repeatable-form-e2e", autodiscover=False)  # noqa: S106
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)

    class EscalationTeam(Component):
        citry = app

        class Kwargs:
            order: str = "primary,secondary"
            next_id: int = 3
            focus_id: str = ""

        class State(Kwargs):
            pass

        class RowActionIn:
            row_id: str = ""

        class Events:
            def add(self, state):
                row_id = f"contact-{state.next_id}"
                state.next_id += 1
                state.order = ",".join((*state.order.split(","), row_id))
                state.focus_id = row_id
                return EscalationTeam(
                    order=state.order,
                    next_id=state.next_id,
                    focus_id=state.focus_id,
                )

            def reverse(self, state):
                state.order = ",".join(reversed(state.order.split(",")))
                state.focus_id = ""
                return EscalationTeam(
                    order=state.order,
                    next_id=state.next_id,
                    focus_id=state.focus_id,
                )

            def remove(self, data: RowActionIn, state):  # noqa: F821
                order = state.order.split(",") if state.order else []
                if data.row_id not in order:
                    return None
                removed_index = order.index(data.row_id)
                remaining = [row_id for row_id in order if row_id != data.row_id]
                state.order = ",".join(remaining)
                if remaining:
                    state.focus_id = remaining[min(removed_index, len(remaining) - 1)]
                else:
                    state.focus_id = "__add__"
                return EscalationTeam(
                    order=state.order,
                    next_id=state.next_id,
                    focus_id=state.focus_id,
                )

        def template_data(self, kwargs, slots):
            contacts = {
                "primary": {
                    "id": "primary",
                    "label": "Primary responder",
                    "email": "ada@example.com",
                    "role": "owner",
                },
                "secondary": {
                    "id": "secondary",
                    "label": "Secondary responder",
                    "email": "",
                    "role": "editor",
                },
            }
            order = tuple(value for value in kwargs.order.split(",") if value)
            rows = tuple(
                contacts.get(
                    row_id,
                    {
                        "id": row_id,
                        "label": f"Additional responder {row_id.removeprefix('contact-')}",
                        "email": "",
                        "role": "viewer",
                    },
                )
                for row_id in order
            )
            return {
                "rows": rows,
                "roles": (
                    citry_ui.CComboboxOption("owner", "Owner"),
                    citry_ui.CComboboxOption("editor", "Editor"),
                    citry_ui.CComboboxOption("viewer", "Viewer"),
                ),
                "form_attrs": {
                    "data-escalation-form": "",
                },
            }

        def js_data(self, kwargs, slots):
            return {"focusId": kwargs.focus_id}

        template = """
          <section data-escalation-team>
            <h1>Escalation team</h1>
            <p>Contacts are notified in the order shown.</p>
            <c-CForm
              #c-key="'escalation-team-form'"
              id="escalation-team-form"
              action="/escalation-team"
              method="post"
              c-attrs="form_attrs"
            >
              <c-for each="row in rows">
                <section
                  #c-key="row['id']"
                  c-data-contact-id="row['id']"
                >
                  <h2>{{ row["label"] }}</h2>
                  <c-CField
                    #c-key="row['id'] + '-email-field'"
                    c-control_id="row['id'] + '-email'"
                    required
                  >
                    <c-fill name="label">
                      Work email
                    </c-fill>
                    <c-fill name="default">
                      <c-CInput
                        #c-key="row['id'] + '-email-input'"
                        c-name="'contacts[' + row['id'] + '][email]'"
                        type="email"
                        c-value="row['email']"
                        autocomplete="email"
                        c-attrs="{'data-contact-email': row['id']}"
                      />
                    </c-fill>
                    <c-fill name="description">
                      Receives alerts for this escalation position.
                    </c-fill>
                    <c-fill name="error">
                      Enter a valid work email.
                    </c-fill>
                  </c-CField>
                  <c-CField
                    #c-key="row['id'] + '-role-field'"
                    c-control_id="row['id'] + '-role'"
                    required
                  >
                    <c-fill name="label">
                      Access role
                    </c-fill>
                    <c-fill name="default">
                      <c-CCombobox
                        #c-key="row['id'] + '-role-combobox'"
                        c-name="'contacts[' + row['id'] + '][role]'"
                        c-options="roles"
                        c-value="row['role']"
                        c-input_attrs="{'data-contact-role': row['id']}"
                      />
                    </c-fill>
                  </c-CField>
                  <c-CButton
                    #c-key="row['id'] + '-remove-button'"
                    type="button"
                    variant="ghost"
                    intent="danger"
                    c-attrs="{
                      'aria-label': 'Remove ' + row['label'],
                      'data-remove-contact': row['id'],
                    }"
                    @c-click="remove({row_id: $el.dataset.removeContact})"
                  >
                    Remove
                  </c-CButton>
                </section>
              </c-for>
              <div>
                <c-CButton
                  type="button"
                  variant="outline"
                  c-attrs="{'data-add-contact': ''}"
                  @c-click="add"
                >
                  Add contact
                </c-CButton>
                <c-CButton
                  type="button"
                  variant="ghost"
                  c-attrs="{'data-reverse-contacts': ''}"
                  @c-click="reverse"
                >
                  Reverse order
                </c-CButton>
                <c-CButton
                  type="submit"
                  c-attrs="{'data-save-team': ''}"
                >
                  Save escalation team
                </c-CButton>
              </div>
            </c-CForm>
          </section>
        """

        js = """
          $component({
            init: ({ els, data }) => {
              const root = els[0];
              if (!data.focusId) {
                return;
              }
              // A replacement component initializes before its new root is
              // necessarily connected. Wait for the browser commit before
              // focusing a newly added descendant.
              requestAnimationFrame(() => {
                const target = data.focusId === "__add__"
                  ? root.querySelector("[data-add-contact]")
                  : [...root.querySelectorAll("[data-contact-email]")]
                    .find((input) => input.dataset.contactEmail === data.focusId);
                target?.focus({ preventScroll: true });
              });
            },
          });
        """

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
              <c-escalation-team />
              <c-js />
            </body>
          </html>
        """

    return app, str(Page())


def _send(page: Any, event: str) -> None:
    page.evaluate(
        "event => Citry.events.send(document.querySelector('[data-escalation-team]'), event, {})",
        event,
    )


def test_repeatable_workflow_preserves_edits_identity_validation_and_submission(
    page: Any,
    serve_citry_ui_live: Any,
) -> None:
    app, html = _workflow_page()
    base = serve_citry_ui_live(app, html)
    page.goto(base + "/")
    page.wait_for_function(READY)

    form = page.locator("#escalation-team-form")
    secondary_email = page.locator('[data-contact-email="secondary"]')
    assert form.evaluate("element => element.matches(':invalid')") is True

    page.evaluate(
        """() => {
          const form = document.querySelector('#escalation-team-form');
          form.addEventListener('submit', (event) => {
            event.preventDefault();
            window.__teamSubmit = [...new FormData(form).entries()];
          });
        }"""
    )
    page.locator("[data-save-team]").click()
    assert page.evaluate("window.__teamSubmit") is None
    assert form.get_attribute("data-validation-attempted") == ""
    assert secondary_email.evaluate("element => document.activeElement === element") is True

    secondary_email.fill("grace@example.com")
    primary_email = page.locator('[data-contact-email="primary"]')
    primary_email.fill("ada+draft@example.com")
    primary_email.focus()
    page.evaluate(
        """() => {
          window.__primaryEmail = document.querySelector('[data-contact-email="primary"]');
          window.__primaryRow = document.querySelector('[data-contact-id="primary"]');
        }"""
    )
    _send(page, "reverse")
    page.wait_for_function("document.querySelectorAll('[data-contact-id]')[0].dataset.contactId === 'secondary'")

    assert primary_email.input_value() == "ada+draft@example.com"
    assert primary_email.evaluate("element => document.activeElement === element") is True
    assert (
        page.evaluate(
            """() => (
          document.querySelector('[data-contact-email="primary"]') === window.__primaryEmail
          && document.querySelector('[data-contact-id="primary"]') === window.__primaryRow
        )"""
        )
        is True
    )

    page.locator("[data-add-contact]").click()
    page.wait_for_function(
        """() => document.querySelectorAll('[data-contact-id]').length === 3
          && document.activeElement?.dataset.contactEmail === 'contact-3'"""
    )
    added_email = page.locator('[data-contact-email="contact-3"]')
    assert added_email.evaluate("element => document.activeElement === element") is True
    added_email.fill("lin@example.com")

    page.locator('[data-remove-contact="primary"]').click()
    page.wait_for_function(
        """() => !document.querySelector('[data-contact-id=primary]')
          && document.activeElement?.dataset.contactEmail === 'contact-3'"""
    )
    assert added_email.evaluate("element => document.activeElement === element") is True
    assert page.locator('[name="contacts[primary][email]"]').count() == 0
    assert page.locator('[name="contacts[primary][role]"]').count() == 0

    page.locator("[data-save-team]").click()
    page.wait_for_function("Array.isArray(window.__teamSubmit)")
    assert page.evaluate("window.__teamSubmit") == [
        ["contacts[secondary][email]", "grace@example.com"],
        ["contacts[secondary][role]", "editor"],
        ["contacts[contact-3][email]", "lin@example.com"],
        ["contacts[contact-3][role]", "viewer"],
    ]
    assert form.evaluate("element => element.matches(':valid')") is True

    page.evaluate(
        """() => {
          window.__removedTeam = document.querySelector('[data-escalation-team]');
          window.__removedTeam.remove();
        }"""
    )
    page.wait_for_function(
        """() => (
          !window.__removedTeam.querySelector('[data-citry-form-initialized]')
          && !window.__removedTeam.querySelector('[data-citry-input-initialized]')
          && !window.__removedTeam.querySelector('[data-citry-combobox-initialized]')
        )"""
    )
