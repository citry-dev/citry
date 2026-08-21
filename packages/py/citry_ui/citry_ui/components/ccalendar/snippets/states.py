from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class CalendarStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="calendar-demo-grid">
        <article><h3>Small plain</h3><c-CCalendar label="Small plain calendar" value="2026-08-19" size="sm" variant="plain" /></article>
        <article><h3>Readonly</h3><c-CCalendar label="Readonly calendar" value="2026-08-19" readonly /></article>
        <article><h3>Disabled</h3><c-CCalendar label="Disabled calendar" value="2026-08-19" disabled /></article>
        <article><h3>Invalid large</h3><c-CCalendar label="Invalid calendar" value="2026-08-19" invalid size="lg" /></article>
      </section>
    """
    css = ":where(.calendar-demo-grid){display:grid;grid-template-columns:repeat(auto-fit,minmax(20rem,1fr));align-items:start;gap:1.25rem}:where(.calendar-demo-grid article){display:grid;gap:.5rem}:where(.calendar-demo-grid h3){margin:0}"


preview = CalendarStates()
preview  # noqa: B018
