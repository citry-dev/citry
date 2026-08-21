# ruff: noqa: E501 - embedded example markup and CSS stay readable as authored

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StyledDatePicker(Component):
    template = """
      <c-CDatePicker class_="brand-date-picker" value="2026-08-19" c-unavailable_dates="('2026-08-20',)" />
    """
    css = """
      :where(.brand-date-picker){--cui-date-picker-background:#f0fdfa;--cui-date-picker-foreground:#134e4a;--cui-date-picker-border-color:#0f766e;--cui-date-picker-focus-color:#0d9488;--cui-date-picker-radius:1rem;--cui-calendar-selected-background:#0f766e;--cui-calendar-selected-foreground:white;max-inline-size:24rem}
      @media (prefers-color-scheme:dark){:where(.brand-date-picker){--cui-date-picker-background:#132f2d;--cui-date-picker-foreground:#ccfbf1;--cui-date-picker-border-color:#5eead4}}
    """


preview = StyledDatePicker()
preview  # noqa: B018
