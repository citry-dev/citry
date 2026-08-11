"""Shared AlertDialog scenario used by Citry UI quality tools."""

from __future__ import annotations

from citry import Citry, Component


def alert_dialog_states_component(app: Citry) -> type[Component]:
    """Create the reusable AlertDialog state catalog."""

    class CitryUiAlertDialogStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="alert-dialog-states-title"
            x-data="{controlledOpen: false}"
          >
            <h1 id="alert-dialog-states-title">AlertDialog states</h1>
            <c-CAlertDialog
              id="quality-delete-project"
              $c-props="{
                onOpenChange: (open, detail) => {
                  window.__qualityAlertDialogChange = {
                    open,
                    reason: detail.reason,
                    returnValue: detail.returnValue
                  };
                }
              }"
            >
              <c-fill name="activator" data="{activator_attrs}">
                <c-CButton c-attrs="activator_attrs" intent="danger">
                  Delete project
                </c-CButton>
              </c-fill>
              <c-fill name="title">Delete this project?</c-fill>
              <c-fill name="description">
                This permanently removes all project data.
              </c-fill>
              <c-fill name="cancel" data="{cancel_attrs}">
                <c-CButton c-attrs="cancel_attrs" variant="outline">
                  Keep project
                </c-CButton>
              </c-fill>
              <c-fill name="action" data="{action_attrs}">
                <c-CButton c-attrs="action_attrs" intent="danger">
                  Delete
                </c-CButton>
              </c-fill>
            </c-CAlertDialog>

            <c-CAlertDialog
              id="quality-controlled-alert"
              size="lg"
              class_="quality-alert-brand"
              c-style="{
                '--cui-alert-dialog-radius': '1.25rem',
                '--cui-alert-dialog-border-color': '#8b5cf6'
              }"
              $c-props="{
                open: controlledOpen,
                onOpenChange: (open) => controlledOpen = open
              }"
            >
              <c-fill name="activator" data="{activator_attrs}">
                <c-CButton c-attrs="activator_attrs" variant="outline">
                  End expedition
                </c-CButton>
              </c-fill>
              <c-fill name="title">End the expedition?</c-fill>
              <c-fill name="description">
                Active observations will move to the archive.
              </c-fill>
              <c-fill name="default">
                The archive remains available to every collaborator.
              </c-fill>
              <c-fill name="cancel" data="{cancel_attrs}">
                <c-CButton c-attrs="cancel_attrs" variant="outline">
                  Continue expedition
                </c-CButton>
              </c-fill>
              <c-fill name="action" data="{action_attrs}">
                <c-CButton c-attrs="action_attrs">End expedition</c-CButton>
              </c-fill>
            </c-CAlertDialog>
          </section>
        """

    return CitryUiAlertDialogStates
