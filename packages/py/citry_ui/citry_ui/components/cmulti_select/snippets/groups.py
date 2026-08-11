import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class GroupedMultiSelect(Component):
    template = """
      <c-CMultiSelect
        c-options="options"
        placeholder="Choose a destination"
        c-trigger_attrs="{'aria-label':'Destination'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("oslo", "Oslo", group="Europe"),
                CMultiSelectOption("prague", "Prague", group="Europe"),
                CMultiSelectOption("kyoto", "Kyoto", group="Asia"),
                CMultiSelectOption("seoul", "Seoul", group="Asia"),
            ]
        }


preview = GroupedMultiSelect()
preview  # noqa: B018
