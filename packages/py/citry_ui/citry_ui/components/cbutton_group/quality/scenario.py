"""Shared Button Group scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def button_group_states_component(app: Citry) -> type[Component]:
    class CitryUiButtonGroupStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-button-group-ready>
            <h1>Button Group states</h1>
            <c-CButtonGroup label="Attached actions">
              <c-CButton variant="outline">Previous</c-CButton>
              <c-CButton variant="outline">Center</c-CButton>
              <c-CButton variant="outline">Next</c-CButton>
            </c-CButtonGroup>
            <c-CButtonGroup label="Spaced actions" c-attached="False">
              <c-CButton intent="primary">Save</c-CButton>
              <c-CButton variant="ghost">Cancel</c-CButton>
            </c-CButtonGroup>
            <c-CButtonGroup label="Vertical actions" orientation="vertical">
              <c-CButton variant="outline">Map</c-CButton>
              <c-CButton variant="outline" c-disabled="True">Archive</c-CButton>
            </c-CButtonGroup>
            <div dir="rtl">
              <c-CButtonGroup label="RTL actions">
                <c-CButton>First</c-CButton>
                <c-CButton>Last</c-CButton>
              </c-CButtonGroup>
            </div>
            <div
              style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem"
            >
              <c-CButtonGroup label="Dark actions">
                <c-CButton variant="outline">Night</c-CButton>
                <c-CButton variant="outline">Dawn</c-CButton>
              </c-CButtonGroup>
            </div>
          </section>
        """

    return CitryUiButtonGroupStates
