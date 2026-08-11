"""Shared Toolbar scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def toolbar_states_component(app: Citry) -> type[Component]:
    class CitryUiToolbarStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-toolbar-ready>
            <h1>Toolbar states</h1>
            <c-CToolbar label="Plain tools">
              <c-CButton>Cut</c-CButton><c-CButton>Copy</c-CButton><c-CButton>Paste</c-CButton>
            </c-CToolbar>
            <c-CToolbar label="Soft tools" variant="soft" size="sm">
              <c-CToggle>Bold</c-CToggle><c-CToggle>Italic</c-CToggle><c-CToggle>Underline</c-CToggle>
            </c-CToolbar>
            <c-CToolbar label="Vertical tools" orientation="vertical" variant="outline" size="lg">
              <c-CButton>North</c-CButton><c-CButton c-disabled="True">Center</c-CButton><c-CButton>South</c-CButton>
            </c-CToolbar>
            <div dir="rtl">
              <c-CToolbar label="RTL tools" variant="outline">
                <c-CButton>First</c-CButton><c-CButton>Second</c-CButton><c-CButton>Third</c-CButton>
              </c-CToolbar>
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CToolbar label="Dark tools" variant="soft">
                <c-CButton>Night</c-CButton><c-CButton>Dawn</c-CButton><a href="#quality">Help</a>
              </c-CToolbar>
            </div>
          </section>
        """

    return CitryUiToolbarStates
