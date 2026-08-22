import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeSizesAndShapes(Component):
    template = """
      <c-CCol class_="badge-sizes">
        <c-CRow align="baseline">
          <c-CBadge size="sm">Small</c-CBadge>
          <c-CBadge>Medium</c-CBadge>
          <c-CBadge size="lg">Large</c-CBadge>
        </c-CRow>
        <c-CRow>
          <c-CBadge shape="rounded" intent="success">Rounded</c-CBadge>
          <c-CBadge shape="pill" intent="success">Pill</c-CBadge>
        </c-CRow>
      </c-CCol>
    """
    css = """
      :where(.badge-sizes) {
        max-inline-size: 28rem;
        padding: 1rem;
        border: 1px solid light-dark(#cbd5d9, #475a62);
        border-radius: 0.75rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BadgeSizesAndShapes()

preview  # noqa: B018
