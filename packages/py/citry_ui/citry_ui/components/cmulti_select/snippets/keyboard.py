import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class KeyboardMultiSelect(Component):
    template = """
      <c-CMultiSelect
        c-options="options"
        placeholder="Focus and use the keyboard"
        loop
        c-trigger_attrs="{'aria-label':'Planet keyboard example'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("earth", "Earth"),
                CMultiSelectOption("mars", "Mars"),
                CMultiSelectOption("jupiter", "Jupiter"),
            ]
        }


preview = KeyboardMultiSelect()
preview  # noqa: B018
