import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class ControlledSelect(Component):
    template = """
      <div x-data>
        <c-CSelect
          c-options="options"
          placeholder="Choose a status"
          value="draft"
          c-trigger_attrs="{'aria-label':'Status'}"
          $c-props="{
            value:$store.selectExample.value,
            onValueChange:(next) => $store.selectExample.value = next,
          }"
        />
        <p>Current: <strong x-text="$store.selectExample.value"></strong></p>
      </div>
    """
    js = "Alpine.store('selectExample', {value:'draft'});"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("draft", "Draft"), CSelectOption("published", "Published")]}


preview = ControlledSelect()
preview  # noqa: B018
