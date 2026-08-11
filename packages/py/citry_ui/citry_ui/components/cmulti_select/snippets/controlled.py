import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class ControlledMultiSelect(Component):
    template = """
      <div x-data>
        <c-CMultiSelect
          c-options="options"
          placeholder="Choose channels"
          c-value="['email']"
          c-trigger_attrs="{'aria-label':'Notification channels'}"
          $c-props="{
            value:$store.multiSelectExample.value,
            onValueChange:(next) => $store.multiSelectExample.value = next,
          }"
        />
        <p>Current: <strong x-text="$store.multiSelectExample.value.join(', ')"></strong></p>
      </div>
    """
    js = "Alpine.store('multiSelectExample', {value:['email']});"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "options": [
                CMultiSelectOption("email", "Email"),
                CMultiSelectOption("push", "Push"),
                CMultiSelectOption("sms", "SMS"),
            ]
        }


preview = ControlledMultiSelect()
preview  # noqa: B018
