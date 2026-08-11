import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToggleGlance(Component):
    template = """
      <c-CToggleGroup label="Star map layers" value="constellations" c-mandatory="True">
        <c-CToggle value="constellations">Constellations</c-CToggle>
        <c-CToggle value="planets">Planets</c-CToggle>
        <c-CToggle value="grid">Grid</c-CToggle>
      </c-CToggleGroup>
    """


preview = ToggleGlance()
preview  # noqa: B018
