import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class HomeSettings(Component):
    template = """
      <c-CStack>
        <c-CSwitch checked>Porch light</c-CSwitch>
        <c-CSwitch>Robot vacuum schedule</c-CSwitch>
        <c-CSwitch checked>Door chime</c-CSwitch>
      </c-CStack>
    """


preview = HomeSettings()

preview  # noqa: B018
