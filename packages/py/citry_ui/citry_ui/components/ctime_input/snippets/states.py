import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TimeInputStates(Component):
    template = """
      <section style="display:grid;grid-template-columns:repeat(auto-fit,minmax(12rem,1fr));gap:1rem">
        <label>Outline <c-CTimeInput value="09:00" /></label>
        <label>Filled <c-CTimeInput value="10:15" variant="filled" size="sm" /></label>
        <label>Plain readonly <c-CTimeInput value="11:30" variant="plain" size="lg" readonly /></label>
        <label>Invalid <c-CTimeInput value="12:45" invalid /></label>
        <label>Disabled <c-CTimeInput value="13:00" disabled /></label>
      </section>
    """


preview = TimeInputStates()
preview  # noqa: B018
