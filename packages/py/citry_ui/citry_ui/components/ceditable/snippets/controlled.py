import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledEditable(Component):
    template = """
      <div x-data>
        <c-CEditable
          value="Atlas"
          $c-props="{
            value:$store.editableExample.value,
            onValueChange:(next) => $store.editableExample.value = next,
          }"
        />
        <p>Committed: <strong x-text="$store.editableExample.value"></strong></p>
      </div>
    """
    js = "Alpine.store('editableExample', {value:'Atlas'});"


preview = ControlledEditable()
preview  # noqa: B018
