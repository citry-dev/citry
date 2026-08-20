from citry import Component

# ruff: noqa: E501 - template and CSS lines stay readable in the public source example


class StyledDateInput(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = '<c-CDateInput c-attrs="{\'aria-label\':\'Brand date\'}" value="2026-08-19" class_="brand-date-input" />'
    css = """
      :where(.brand-date-input){--cui-date-input-background:light-dark(#f0fdf4,#14261d);--cui-date-input-border-color:#16a34a;--cui-date-input-focus-color:#15803d;--cui-date-input-radius:1rem}
    """


preview = StyledDateInput()
preview  # noqa: B018
