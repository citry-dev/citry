from citry import Component


class CalendarConstraints(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCalendar
        label="Book an appointment"
        visible_date="2026-08-19"
        min="2026-08-10"
        max="2026-09-15"
        c-unavailable_dates="('2026-08-18', '2026-08-20', '2026-08-24')"
      />
    """


preview = CalendarConstraints()
preview  # noqa: B018
