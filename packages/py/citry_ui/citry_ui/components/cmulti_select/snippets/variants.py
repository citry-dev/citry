import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class MultiSelectVariants(Component):
    template = """
      <c-CStack>
        <c-CMultiSelect
          c-options="options" placeholder="Outline" variant="outline" size="sm"
          c-trigger_attrs="{'aria-label':'Small outline'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Filled" variant="filled"
          c-trigger_attrs="{'aria-label':'Medium filled'}"
        />
        <c-CMultiSelect
          c-options="options" placeholder="Plain" variant="plain" size="lg"
          c-trigger_attrs="{'aria-label':'Large plain'}"
        />
      </c-CStack>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CMultiSelectOption("one", "One"), CMultiSelectOption("two", "Two")]}


preview = MultiSelectVariants()
preview  # noqa: B018
