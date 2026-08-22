import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectStates(Component):
    template = """
      <c-CCol>
        <c-CMultiSelect
          c-options="options" placeholder="Choose" c-value="['active', 'paused']" readonly
          c-trigger_attrs="{'aria-label':'Read-only state'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Choose" disabled
          c-trigger_attrs="{'aria-label':'Disabled state'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Choose" invalid
          c-trigger_attrs="{'aria-label':'Invalid state'}"
        />
      </c-CCol>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CMultiSelectOption("active", "Active"), CMultiSelectOption("paused", "Paused")]}


preview = MultiSelectStates()
preview  # noqa: B018
