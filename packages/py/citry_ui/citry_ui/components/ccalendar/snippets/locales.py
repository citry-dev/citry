from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class CalendarLocales(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="calendar-demo-grid">
        <article><h3>Locale week start</h3><c-CCalendar label="Locale week start" visible_date="2026-08-19" /></article>
        <article><h3>Explicit Monday</h3><c-CCalendar label="Monday week start" visible_date="2026-08-19" c-first_day_of_week="1" /></article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));gap:1.25rem}:where(.calendar-demo-grid article){display:grid;align-content:start;gap:.5rem}:where(.calendar-demo-grid h3){margin:0}"


preview = CalendarLocales()
preview  # noqa: B018
