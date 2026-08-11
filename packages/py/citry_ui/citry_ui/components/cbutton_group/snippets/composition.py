import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Composition(Component):
    template = """
      <c-CButtonGroup label="Expedition actions">
        <c-CButton intent="primary">Save route</c-CButton>
        <c-CButton variant="outline" href="/preview">Preview</c-CButton>
        <c-CButton variant="ghost" intent="danger">Discard</c-CButton>
      </c-CButtonGroup>
    """


preview = Composition()
preview  # noqa: B018
