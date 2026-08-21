# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

from datetime import date
from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CDatePicker

citry.register_library(citry_ui)


class BasicDatePicker(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {"python_picker": CDatePicker(value=date(2026, 8, 19))}

    template = """
      <section class="date-picker-demo-grid">
        <c-CField required>
          <c-fill name="label">Arrival date</c-fill>
          <c-fill name="description">Choose your check-in day.</c-fill>
          <c-fill name="default"><c-CDatePicker name="arrival" value="2026-08-19" /></c-fill>
        </c-CField>
        <article><h3>Python composition</h3>{{ python_picker }}</article>
      </section>
    """
    css = ":where(.date-picker-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1.25rem}:where(.date-picker-demo-grid article){display:grid;align-content:start;gap:.75rem}:where(.date-picker-demo-grid h3){margin:0}"


preview = BasicDatePicker()
preview  # noqa: B018
