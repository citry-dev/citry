import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToggleGroups(Component):
    template = """
      <c-CCol gap="lg">
        <c-CToggleGroup label="Chart scale" value="linear">
          <c-CToggle value="linear">Linear</c-CToggle>
          <c-CToggle value="log">Log</c-CToggle>
        </c-CToggleGroup>
        <c-CToggleGroup label="Visible layers" c-value="['stars', 'labels']" c-multiple="True">
          <c-CToggle value="stars">Stars</c-CToggle>
          <c-CToggle value="labels">Labels</c-CToggle>
          <c-CToggle value="grid">Grid</c-CToggle>
        </c-CToggleGroup>
      </c-CCol>
    """


preview = ToggleGroups()
preview  # noqa: B018
