import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToolbarCommands(Component):
    template = """
      <c-CToolbar label="Text formatting" variant="outline">
        <c-CButton>Undo</c-CButton>
        <c-CButton>Redo</c-CButton>
        <c-CToggle c-pressed="True">Bold</c-CToggle>
        <c-CToggle>Italic</c-CToggle>
      </c-CToolbar>
    """


preview = ToolbarCommands()

preview  # noqa: B018
