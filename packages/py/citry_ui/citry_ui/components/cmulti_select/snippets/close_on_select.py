import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class CloseOnSelectMultiSelect(Component):
    template = """
      <c-CMultiSelect
        c-options="options"
        placeholder="Choose a delivery method"
        close_on_select
        c-trigger_attrs="{'aria-label':'Delivery methods'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("courier", "Courier"),
                CMultiSelectOption("pickup", "Pickup"),
                CMultiSelectOption("locker", "Parcel locker"),
            ]
        }


preview = CloseOnSelectMultiSelect()
preview  # noqa: B018
