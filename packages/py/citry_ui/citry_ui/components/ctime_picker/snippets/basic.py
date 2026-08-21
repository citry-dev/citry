import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicTimePicker(Component):
    template = """
      <c-CField required>
        <c-fill name="label">Appointment time</c-fill>
        <c-fill name="description">Choose a fifteen-minute slot.</c-fill>
        <c-fill name="default"><c-CTimePicker name="appointment" min="09:00" max="12:00" value="09:30" /></c-fill>
      </c-CField>
    """


preview = BasicTimePicker()
preview  # noqa: B018
