import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StandaloneToggle(Component):
    template = """
      <c-CToggle c-pressed="True">Pin observation</c-CToggle>
    """


preview = StandaloneToggle()
preview  # noqa: B018
