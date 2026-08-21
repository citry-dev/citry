# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DateRangeLocales(Component):
    template = """
      <section class="date-range-locales">
        <article><h3>Provider locale week</h3><c-CDateRange start="2026-08-19" end="2026-08-23" /></article>
        <article><h3>Explicit Monday start</h3><c-CDateRange start="2026-08-19" end="2026-08-23" c-first_day_of_week="1" /></article>
        <article lang="ar" dir="rtl"><h3>RTL scope</h3><c-CDateRange start="2026-08-19" end="2026-08-23" /></article>
      </section>
    """
    css = ":where(.date-range-locales){display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem}:where(.date-range-locales article){display:grid;align-content:start;gap:.5rem;padding:.75rem}:where(.date-range-locales h3){margin:0}"


preview = DateRangeLocales()
preview  # noqa: B018
