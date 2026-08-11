import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarCustomization(Component):
    template = """
      <c-CToolbar
        label="Forest tools"
        variant="soft"
        c-style="{
          '--cui-toolbar-gap': '0.75rem',
          '--cui-toolbar-radius': '1.25rem',
          '--cui-toolbar-background': '#eef8ec',
          '--cui-toolbar-border-color': '#497a43'
        }"
      >
        <c-CButton variant="ghost">Canopy</c-CButton>
        <c-CButton variant="ghost">Understory</c-CButton>
        <c-CButton variant="ghost">Soil</c-CButton>
      </c-CToolbar>
    """


preview = ToolbarCustomization()

preview  # noqa: B018
