import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarOrientation(Component):
    template = """
      <div style="display:grid; grid-template-columns:1fr auto; gap:1rem; align-items:start">
        <c-CToolbar label="Horizontal tools" c-loop="False">
          <c-CButton>Previous</c-CButton>
          <c-CButton>Current</c-CButton>
          <c-CButton>Next</c-CButton>
        </c-CToolbar>
        <c-CToolbar label="Vertical tools" orientation="vertical" variant="outline">
          <c-CButton>Up</c-CButton>
          <c-CButton>Center</c-CButton>
          <c-CButton>Down</c-CButton>
        </c-CToolbar>
      </div>
    """


preview = ToolbarOrientation()

preview  # noqa: B018
