# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerStates(Component):
    template = """
      <section class="date-picker-states">
        <article><h3>Optional and clearable</h3><c-CDatePicker value="2026-08-19" /></article>
        <article><h3>Required</h3><c-CDatePicker value="2026-08-20" required /></article>
        <article><h3>Readonly</h3><c-CDatePicker value="2026-08-21" readonly /></article>
        <article><h3>Disabled</h3><c-CDatePicker value="2026-08-22" disabled /></article>
        <article><h3>Invalid large</h3><c-CDatePicker value="2026-08-23" invalid size="lg" /></article>
        <article><h3>Small filled</h3><c-CDatePicker value="2026-08-24" variant="filled" size="sm" /></article>
      </section>
    """
    css = ":where(.date-picker-states){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1rem}:where(.date-picker-states article){display:grid;align-content:start;gap:.5rem}:where(.date-picker-states h3){margin:0;font-size:.9rem}"


preview = DatePickerStates()
preview  # noqa: B018
