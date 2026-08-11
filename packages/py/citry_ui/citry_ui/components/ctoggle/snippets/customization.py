import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ToggleCustomization(Component):
    template = """
      <c-CToggleGroup class_="nebula-toggle" label="Nebula filter" value="oxygen">
        <c-CToggle value="oxygen">Oxygen</c-CToggle>
        <c-CToggle value="hydrogen">Hydrogen</c-CToggle>
      </c-CToggleGroup>
    """
    css = """
      :where(.nebula-toggle) {
        --cui-toggle-pressed-background: light-dark(#7c3aed, #a78bfa);
        --cui-toggle-pressed-foreground: white;
        --cui-toggle-radius: 999px;
      }
    """


preview = ToggleCustomization()
preview  # noqa: B018
