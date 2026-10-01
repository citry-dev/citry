import citry_ui
from citry import Component, citry
from citry_ui import CSelectOption

citry.register_library(citry_ui)


class ControlledSelect(Component):
    template = """
      <div >
        <c-CSelect
          c-options="options"
          placeholder="Choose a status"
          value="draft"
          c-trigger_attrs="{'aria-label':'Status'}"
          :value="value" :onValueChange="(next) => value = next"
        />
        <p>Current: <strong v-text="value"></strong></p>
      </div>
    """
    js = "$component({data(){return {value:'draft'};}});"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {"options": [CSelectOption("draft", "Draft"), CSelectOption("published", "Published")]}


preview = ControlledSelect()
preview  # noqa: B018
