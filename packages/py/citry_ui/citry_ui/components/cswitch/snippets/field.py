import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SwitchField(Component):
    template = """
      <c-CField control_id="away-mode" required>
        <c-fill name="label">Away mode</c-fill>
        <c-fill name="default"><c-CSwitch name="away_mode" /></c-fill>
        <c-fill name="description">Lower heating and pause routine lighting.</c-fill>
        <c-fill name="error">Enable away mode before leaving.</c-fill>
      </c-CField>
    """


preview = SwitchField()

preview  # noqa: B018
