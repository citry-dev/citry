import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class CustomizedMultiSelect(Component):
    css = """
      .brand-select {
        --cui-multi-select-radius: 1rem;
        --cui-multi-select-selected-background: #53389e;
        --cui-multi-select-selected-foreground: white;
        --cui-multi-select-focus-color: #7f56d9;
        inline-size: min(100%, 22rem);
      }
    """
    template = """
      <c-CMultiSelect
        class_="brand-select"
        c-options="options"
        placeholder="Choose a collection"
        c-trigger_attrs="{'aria-label':'Collection'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CMultiSelectOption("botany", "Botany"), CMultiSelectOption("astronomy", "Astronomy")]}


preview = CustomizedMultiSelect()
preview  # noqa: B018
