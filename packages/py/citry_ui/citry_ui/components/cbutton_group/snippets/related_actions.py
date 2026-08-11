import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RelatedActions(Component):
    template = """
      <c-CButtonGroup label="Map controls">
        <c-CButton variant="outline">Zoom in</c-CButton>
        <c-CButton variant="outline">Reset</c-CButton>
        <c-CButton variant="outline">Zoom out</c-CButton>
      </c-CButtonGroup>
    """


preview = RelatedActions()
preview  # noqa: B018
