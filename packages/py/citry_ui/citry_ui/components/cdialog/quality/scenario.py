"""Shared Dialog scenario used by Phase 7.5 quality tools."""

from __future__ import annotations

from citry import Citry, Component


def dialog_states_component(app: Citry) -> type[Component]:
    """Create the reusable Dialog state catalog."""

    class CitryUiDialogStates(Component):
        citry = app

        class Kwargs:
            pass

        class Slots:
            pass

        template = """
          <section
            class="citry-ui-quality-stack"
            aria-labelledby="dialog-states-title"
            x-data="{ controlledOpen: false }"
          >
            <h1 id="dialog-states-title">
              Dialog states
            </h1>
            <c-CDialog
              id="quality-dialog"
              $c-props="{
                onOpenChange: (open, detail) => {
                  window.__qualityDialogChange = { open, reason: detail.reason };
                },
              }"
            >
              <c-fill
                name="activator"
                data="{ activator_attrs }"
              >
                <c-CButton c-attrs="activator_attrs">
                  Open observatory log
                </c-CButton>
              </c-fill>
              <c-fill name="title">
                Observatory log
              </c-fill>
              <c-fill name="description">
                Record the latest sky conditions.
              </c-fill>
              <c-fill name="default">
                <c-CForm id="quality-dialog-form">
                  <c-CField required control_id="quality-dialog-name">
                    <c-fill name="label">
                      Observation name
                    </c-fill>
                    <c-fill name="default">
                      <c-CInput
                        id="quality-dialog-name"
                        name="observation_name"
                        value="Aurora arc"
                        c-attrs="{'autofocus': True}"
                      />
                    </c-fill>
                  </c-CField>
                </c-CForm>
                <c-CDialog id="quality-nested-dialog" size="sm">
                  <c-fill
                    name="activator"
                    data="{ activator_attrs }"
                  >
                    <c-CButton variant="outline" c-attrs="activator_attrs">
                      Open star chart
                    </c-CButton>
                  </c-fill>
                  <c-fill name="title">
                    Star chart
                  </c-fill>
                  <c-fill name="default">
                    The northern arc crosses Cassiopeia at 02:10.
                  </c-fill>
                </c-CDialog>
              </c-fill>
              <c-fill
                name="actions"
                data="{ close_attrs }"
              >
                <c-CButton variant="outline" c-attrs="close_attrs">
                  Cancel
                </c-CButton>
                <c-CButton>
                  Record observation
                </c-CButton>
              </c-fill>
            </c-CDialog>
            <c-CDialog
              id="quality-persistent-dialog"
              c-dismissible="False"
              size="lg"
              $c-props="{
                open: controlledOpen,
                onOpenChange: (open) => controlledOpen = open,
              }"
            >
              <c-fill
                name="activator"
                data="{ activator_attrs }"
              >
                <c-CButton variant="outline" c-attrs="activator_attrs">
                  Read expedition protocol
                </c-CButton>
              </c-fill>
              <c-fill name="title">
                Expedition protocol
              </c-fill>
              <c-fill name="default">
                <c-for each="paragraph in paragraphs">
                  <p>
                    {{ paragraph }}
                  </p>
                </c-for>
              </c-fill>
              <c-fill
                name="actions"
                data="{ close_attrs }"
              >
                <c-CButton c-attrs="close_attrs">
                  Acknowledge
                </c-CButton>
              </c-fill>
            </c-CDialog>
          </section>
        """

        def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:  # noqa: ARG002
            return {
                "paragraphs": tuple(
                    f"Log {index}: The ridge observatory recorded a stable horizon and clear sky."
                    for index in range(1, 9)
                ),
            }

    return CitryUiDialogStates
