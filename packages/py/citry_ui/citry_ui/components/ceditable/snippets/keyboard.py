import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableKeyboard(Component):
    template = """
      <c-CCol>
        <p>Tab to Edit, press Enter to edit, then Enter to save or Escape to cancel.</p>
        <c-CEditable value="Keyboard friendly" />
        <c-CButton variant="outline">Next focus target</c-CButton>
      </c-CCol>
    """


preview = EditableKeyboard()
preview  # noqa: B018
