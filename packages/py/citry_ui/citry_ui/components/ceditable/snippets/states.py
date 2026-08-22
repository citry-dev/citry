import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableStates(Component):
    template = """
      <c-CCol>
        <c-CEditable value="Available" c-input_attrs="{'aria-label':'Available title'}" />
        <c-CEditable value="Read only" readonly c-input_attrs="{'aria-label':'Read-only title'}" />
        <c-CEditable value="Disabled" disabled c-input_attrs="{'aria-label':'Disabled title'}" />
        <c-CEditable value="Needs review" invalid c-input_attrs="{'aria-label':'Invalid title'}" />
        <c-CEditable placeholder="Empty value" c-input_attrs="{'aria-label':'Empty title'}" />
      </c-CCol>
    """


preview = EditableStates()
preview  # noqa: B018
