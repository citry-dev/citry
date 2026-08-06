"""Shared Button scenario used by Phase 7.5 quality tools."""

from __future__ import annotations

from citry import Citry, Component


def button_states_component(app: Citry) -> type[Component]:
    """Create the reusable Button state catalog for one Citry instance."""

    class CitryUiButtonStates(Component):
        citry = app

        template = """
          <section
            class="citry-ui-quality-grid"
            aria-labelledby="button-states-title"
            x-data="{ clientLoading: false }"
          >
            <h1 id="button-states-title">
              Button states
            </h1>
            <form
              @submit.prevent="window.__qualityButtonSubmit = $event.submitter?.value"
              @reset="window.__qualityButtonReset = true"
            >
              <c-CButton
                type="submit"
                c-attrs="{'name': 'action', 'value': 'save'}"
              >
                Save changes
              </c-CButton>
            <c-CButton type="reset" variant="outline">
              Reset form
            </c-CButton>
          </form>
          <c-CButton href="/field-guide" variant="outline">
            Open field guide
          </c-CButton>
          <c-CButton variant="solid" intent="primary" size="sm">
              Solid primary
            </c-CButton>
            <c-CButton variant="outline" intent="neutral" size="md">
              Outline neutral
            </c-CButton>
            <c-CButton variant="outline" intent="success" size="md">
              Outline success
            </c-CButton>
            <c-CButton variant="solid" intent="warn" size="md">
              Solid warn
            </c-CButton>
            <c-CButton variant="ghost" intent="danger" size="lg">
              Ghost danger
            </c-CButton>
            <c-CButton disabled>
              Disabled action
            </c-CButton>
            <c-CButton loading loading_pos="start">
              <c-fill name="loading">
                ◌
              </c-fill>
              <c-fill name="default">
                Loading at start
              </c-fill>
            </c-CButton>
            <c-CButton loading loading_pos="center">
              Loading at center
            </c-CButton>
            <c-CButton loading loading_pos="end">
              Loading at end
            </c-CButton>
            <c-CButton block>
              <c-fill name="start">
                +
              </c-fill>
              <c-fill name="default">
                Slotted action
              </c-fill>
              <c-fill name="end">
                →
              </c-fill>
            </c-CButton>
            <c-CButton
              variant="outline"
              $c-props="{ loading: clientLoading }"
              @click="clientLoading = true"
            >
              Client-controlled loading
            </c-CButton>
          </section>
        """

    return CitryUiButtonStates
