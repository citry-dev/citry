import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimePickerStates(Component):
    template = """
      <section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:1rem">
        <c-CTimePicker value="09:00" min="08:00" max="12:00" />
        <c-CTimePicker value="10:15" min="08:00" max="12:00" variant="filled" size="sm" />
        <c-CTimePicker value="11:30" min="08:00" max="12:00" variant="plain" size="lg" readonly />
        <c-CTimePicker value="12:00" min="08:00" max="12:00" invalid />
        <c-CTimePicker value="08:30" min="08:00" max="12:00" disabled />
      </section>
    """


preview = TimePickerStates()
preview  # noqa: B018
