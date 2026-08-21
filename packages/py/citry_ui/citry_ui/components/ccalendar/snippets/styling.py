from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class StyledCalendar(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CCalendar class_="brand-calendar" label="Brand calendar" value="2026-08-19" c-unavailable_dates="('2026-08-20',)" />
    """
    css = """
      :where(.brand-calendar){--cui-calendar-background:#fff8eb;--cui-calendar-border-color:#9a6700;--cui-calendar-focus-color:#6f42c1;--cui-calendar-selected-background:#7c3aed;--cui-calendar-selected-foreground:white;--cui-calendar-today-color:#9a3412;--cui-calendar-radius:1rem}
      @media (prefers-color-scheme:dark){:where(.brand-calendar){--cui-calendar-background:#211a10;--cui-calendar-foreground:#fff7e6}}
    """


preview = StyledCalendar()
preview  # noqa: B018
