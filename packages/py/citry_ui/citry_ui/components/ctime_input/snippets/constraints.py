import citry_ui
from citry import Component, citry

# ruff: noqa: E501 - embedded Citry templates remain readable

citry.register_library(citry_ui)


class TimeInputConstraints(Component):
    template = """
      <section style="display:grid;gap:1rem;max-width:22rem">
        <label>Office appointment <c-CTimeInput name="office" min="09:00" max="17:00" c-step="900" value="09:30" /></label>
        <label>Overnight window <c-CTimeInput name="overnight" min="23:00" max="02:00" value="23:30" /></label>
      </section>
    """


preview = TimeInputConstraints()
preview  # noqa: B018
