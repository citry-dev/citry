import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class SelectVariants(Component):
    template = """
      <c-CStack>
        <c-CSelect
          c-options="options" placeholder="Outline" variant="outline" size="sm"
          c-trigger_attrs="{'aria-label':'Small outline'}"
        />
        <c-CSelect
          c-options="options" placeholder="Filled" variant="filled"
          c-trigger_attrs="{'aria-label':'Medium filled'}"
        />
        <c-CSelect
          c-options="options" placeholder="Plain" variant="plain" size="lg"
          c-trigger_attrs="{'aria-label':'Large plain'}"
        />
      </c-CStack>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("one", "One"), CSelectOption("two", "Two")]}


preview = SelectVariants()
preview  # noqa: B018
