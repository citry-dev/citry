from datetime import date
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCalendar

citry.register_library(citry_ui)

# ruff: noqa: E501 - template and CSS lines stay readable in public source examples


class BasicCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_calendar": CCalendar(value=date(2026, 8, 19), label="Python-composed calendar")}

    template = """
      <section class="calendar-demo-grid">
        <c-CField required>
          <c-fill name="label">Arrival date</c-fill>
          <c-fill name="description">Choose your check-in day.</c-fill>
          <c-fill name="default"><c-CCalendar name="arrival" value="2026-08-19" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_calendar }}</article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1.25rem}:where(.calendar-demo-grid article){display:grid;align-content:start;gap:.75rem}:where(.calendar-demo-grid h3){margin:0}"


preview = BasicCalendar()
preview  # noqa: B018
