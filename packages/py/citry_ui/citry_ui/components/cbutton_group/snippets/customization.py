import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Customization(Component):
    template = """
      <c-CButtonGroup class_="orbit-group" label="Orbit controls">
        <c-CButton variant="outline">Inner</c-CButton>
        <c-CButton variant="outline">Stable</c-CButton>
        <c-CButton variant="outline">Outer</c-CButton>
      </c-CButtonGroup>
    """
    css = """
      :where(.orbit-group) {
        --cui-button-group-radius: 999px;
        --cui-button-group-border-width: 2px;
      }
    """


preview = Customization()
preview  # noqa: B018
