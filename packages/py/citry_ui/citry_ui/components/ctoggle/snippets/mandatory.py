import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MandatoryToggle(Component):
    template = """
      <c-CToggleGroup label="Coordinate system" value="equatorial" c-mandatory="True">
        <c-CToggle value="equatorial">Equatorial</c-CToggle>
        <c-CToggle value="galactic">Galactic</c-CToggle>
      </c-CToggleGroup>
    """


preview = MandatoryToggle()
preview  # noqa: B018
