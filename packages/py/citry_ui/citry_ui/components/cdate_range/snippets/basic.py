import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicDateRange(Component):
    template = """
      <fieldset>
        <legend>Travel dates</legend>
        <c-CDateRange start_name="arrival" end_name="departure" start="2026-08-19" end="2026-08-23" />
      </fieldset>
    """


preview = BasicDateRange()
preview  # noqa: B018
