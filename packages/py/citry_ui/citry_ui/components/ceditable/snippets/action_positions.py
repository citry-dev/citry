import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableActionPositions(Component):
    template = """
      <c-CCol>
        <c-CEditable value="Actions inside by default" editing c-input_attrs="{'aria-label':'Inside actions'}" />
        <c-CEditable
          value="Actions beside the input" editing action_position="outside"
          c-input_attrs="{'aria-label':'Outside actions'}"
        />
      </c-CCol>
    """


preview = EditableActionPositions()
preview  # noqa: B018
