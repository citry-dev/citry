# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DateRangeStates(Component):
    template = """
      <section class="date-range-states">
        <fieldset><legend>Optional</legend><c-CDateRange start="2026-08-19" end="2026-08-23" clearable /></fieldset>
        <fieldset><legend>Readonly</legend><c-CDateRange start="2026-08-19" end="2026-08-23" readonly variant="filled" size="sm" /></fieldset>
        <fieldset><legend>Disabled</legend><c-CDateRange start="2026-08-19" end="2026-08-23" disabled /></fieldset>
        <fieldset><legend>Invalid</legend><c-CDateRange start="2026-08-19" end="2026-08-23" invalid variant="plain" size="lg" /></fieldset>
      </section>
    """
    css = ":where(.date-range-states){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}:where(.date-range-states fieldset){min-inline-size:0}"


preview = DateRangeStates()
preview  # noqa: B018
