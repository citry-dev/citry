import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class KeyboardSelect(Component):
    template = """
      <c-CSelect
        c-options="options"
        placeholder="Focus and use the keyboard"
        loop
        c-trigger_attrs="{'aria-label':'Planet keyboard example'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CSelectOption("earth", "Earth"),
                CSelectOption("mars", "Mars"),
                CSelectOption("jupiter", "Jupiter"),
            ]
        }


preview = KeyboardSelect()
preview  # noqa: B018
