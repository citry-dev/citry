import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonGroupGlance(Component):
    template = """
      <c-CButtonGroup label="Telescope controls">
        <c-CButton variant="outline">Previous</c-CButton>
        <c-CButton variant="outline">Center</c-CButton>
        <c-CButton variant="outline">Next</c-CButton>
      </c-CButtonGroup>
    """


preview = ButtonGroupGlance()
preview  # noqa: B018
