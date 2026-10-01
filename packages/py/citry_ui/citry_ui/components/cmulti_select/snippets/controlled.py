import citry_ui
from citry import Component, citry
from citry_ui import CMultiSelectOption

citry.register_library(citry_ui)


class ControlledMultiSelect(Component):
    template = """
      <div >
        <c-CMultiSelect
          c-options="options"
          placeholder="Choose channels"
          c-value="['email']"
          c-trigger_attrs="{'aria-label':'Notification channels'}"
          :value="value" :onValueChange="(next) => value = next"
        />
        <p>Current: <strong v-text="value.join(', ')"></strong></p>
      </div>
    """
    js = "$component({data(){return {value:['email']};}});"

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
