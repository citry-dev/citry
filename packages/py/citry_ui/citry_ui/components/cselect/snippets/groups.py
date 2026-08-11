import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class GroupedSelect(Component):
    template = """
      <c-CSelect
        c-options="options"
        placeholder="Choose a destination"
        c-trigger_attrs="{'aria-label':'Destination'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CSelectOption("oslo", "Oslo", group="Europe"),
                CSelectOption("prague", "Prague", group="Europe"),
                CSelectOption("kyoto", "Kyoto", group="Asia"),
                CSelectOption("seoul", "Seoul", group="Asia"),
            ]
        }


preview = GroupedSelect()
preview  # noqa: B018
