import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioField(Component):
    template = """
      <c-CField control_id="shade-choice" required>
        <c-fill name="label">Preferred shade</c-fill>
        <c-fill name="default">
          <c-CRadioGroup name="shade" orientation="horizontal">
            <c-CRadio value="sun">Full sun</c-CRadio>
            <c-CRadio value="partial">Partial shade</c-CRadio>
            <c-CRadio value="deep">Deep shade</c-CRadio>
          </c-CRadioGroup>
        </c-fill>
        <c-fill name="description">Choose the light available in this bed.</c-fill>
        <c-fill name="error">Choose one shade level.</c-fill>
      </c-CField>
    """


preview = RadioField()

preview  # noqa: B018
