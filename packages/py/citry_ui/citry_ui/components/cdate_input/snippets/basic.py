from datetime import date
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CDateInput

citry.register_library(citry_ui)

# ruff: noqa: E501 - template and CSS lines stay readable in public source examples


class BasicDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_input": CDateInput(value=date(2026, 8, 19), attrs={"aria-label": "Python date"})}

    template = """
      <section class="date-input-demo-grid">
        <c-CField required>
          <c-fill name="label">Arrival date</c-fill>
          <c-fill name="description">Choose your check-in day.</c-fill>
          <c-fill name="default"><c-CDateInput name="arrival" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_input }}</article>
      </section>
    """
    css = ":where(.date-input-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.25rem}"


preview = BasicDateInput()
preview  # noqa: B018
