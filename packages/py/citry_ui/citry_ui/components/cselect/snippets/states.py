import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectStates(Component):
    template = """
      <c-CCol>
        <c-CSelect
          c-options="options" placeholder="Choose" value="active" readonly
          c-trigger_attrs="{'aria-label':'Read-only state'}"
        />
        <c-CSelect
          c-options="options" placeholder="Choose" disabled
          c-trigger_attrs="{'aria-label':'Disabled state'}"
        />
        <c-CSelect c-options="options" placeholder="Choose" invalid c-trigger_attrs="{'aria-label':'Invalid state'}" />
      </c-CCol>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("active", "Active"), CSelectOption("paused", "Paused")]}


preview = SelectStates()
preview  # noqa: B018
