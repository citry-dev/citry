import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarAtAGlance(Component):
    template = """
      <c-CToolbar label="Document tools" variant="soft">
        <c-CButton variant="ghost">Undo</c-CButton>
        <c-CToggle>Bold</c-CToggle>
        <c-CToggle>Italic</c-CToggle>
        <c-CDivider orientation="vertical" decorative />
        <a href="#toolbar-preview">Help</a>
      </c-CToolbar>
    """


preview = ToolbarAtAGlance()

preview  # noqa: B018
