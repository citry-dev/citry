from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class CalendarNaturalWeeks(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="calendar-demo-grid">
        <article><h3>Fixed six rows</h3><c-CCalendar label="Fixed weeks" visible_date="2026-02-01" /></article>
        <article><h3>Natural rows</h3><c-CCalendar label="Natural weeks" visible_date="2026-02-01" c-fixed_weeks="False" c-show_adjacent_days="False" /></article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));align-items:start;gap:1.25rem}:where(.calendar-demo-grid article){display:grid;gap:.5rem}:where(.calendar-demo-grid h3){margin:0}"


preview = CalendarNaturalWeeks()
preview  # noqa: B018
