import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicRadioGroup(Component):
    template = """
      <c-CRadioGroup name="watering" value="morning">
        <c-fill name="label">Watering time</c-fill>
        <c-fill name="default">
          <c-CRadio value="morning">Early morning</c-CRadio>
          <c-CRadio value="evening">Late evening</c-CRadio>
        </c-fill>
      </c-CRadioGroup>
    """


preview = BasicRadioGroup()

preview  # noqa: B018
