import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledEditable(Component):
    template = """
      <div >
        <c-CEditable
          value="Atlas"
          :value="value" :onValueChange="(next) => value = next"
        />
        <p>Committed: <strong v-text="value"></strong></p>
      </div>
    """
    js = "$component({data(){return {value:'Atlas'};}});"


preview = ControlledEditable()
preview  # noqa: B018
