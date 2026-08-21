# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DatePickerPlacement(Component):
    template = """
      <section class="date-picker-placement">
        <article><h3>Bottom start and matched</h3><c-CDatePicker value="2026-08-19" /></article>
        <article><h3>Top end and intrinsic</h3><c-CDatePicker value="2026-08-20" placement="top-end" c-match_width="False" /></article>
      </section>
    """
    css = ":where(.date-picker-placement){display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:3rem;min-block-size:28rem;align-items:center}:where(.date-picker-placement article){display:grid;gap:.5rem}:where(.date-picker-placement h3){margin:0}"


preview = DatePickerPlacement()
preview  # noqa: B018
