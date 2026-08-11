import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class CustomizedSelect(Component):
    css = """
      .brand-select {
        --cui-select-radius: 1rem;
        --cui-select-selected-background: #53389e;
        --cui-select-selected-foreground: white;
        --cui-select-focus-color: #7f56d9;
        inline-size: min(100%, 22rem);
      }
    """
    template = """
      <c-CSelect
        class_="brand-select"
        c-options="options"
        placeholder="Choose a collection"
        c-trigger_attrs="{'aria-label':'Collection'}"
      />
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("botany", "Botany"), CSelectOption("astronomy", "Astronomy")]}


preview = CustomizedSelect()
preview  # noqa: B018
