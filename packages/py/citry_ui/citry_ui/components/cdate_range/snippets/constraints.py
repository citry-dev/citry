# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ConstrainedDateRange(Component):
    template = """
      <fieldset>
        <legend>Available booking window</legend>
        <p id="range-help">August 20 and 24 are unavailable; a range cannot cross either date.</p>
        <c-CDateRange min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24')" c-attrs="{'aria-describedby':'range-help'}" />
      </fieldset>
    """


preview = ConstrainedDateRange()
preview  # noqa: B018
