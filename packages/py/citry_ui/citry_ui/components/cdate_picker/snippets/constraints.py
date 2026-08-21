# ruff: noqa: E501 - embedded example markup stays readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerConstraints(Component):
    template = """
      <c-CField>
        <c-fill name="label">Workshop day</c-fill>
        <c-fill name="description">August 20, 24, and 27 are already booked.</c-fill>
        <c-fill name="default">
          <c-CDatePicker value="2026-08-19" min="2026-08-10" max="2026-09-15" c-unavailable_dates="('2026-08-20','2026-08-24','2026-08-27')" />
        </c-fill>
      </c-CField>
    """


preview = DatePickerConstraints()
preview  # noqa: B018
