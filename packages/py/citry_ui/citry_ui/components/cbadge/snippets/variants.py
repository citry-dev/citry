import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeVariants(Component):
    template = """
      <c-CCol class_="badge-variants" gap="sm">
        <c-CRow><strong>Soft</strong><c-CBadge intent="primary">Lapis</c-CBadge></c-CRow>
        <c-CRow><strong>Solid</strong><c-CBadge intent="primary" variant="solid">Lapis</c-CBadge></c-CRow>
        <c-CRow><strong>Outline</strong><c-CBadge intent="primary" variant="outline">Lapis</c-CBadge></c-CRow>
      </c-CCol>
    """
    css = """
      :where(.badge-variants) {
        max-inline-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-variants > [data-citry-ui-part="row"]) {
        justify-content: space-between;
        padding: 0.75rem;
        border: 1px solid light-dark(#d4cabc, #514940);
        border-radius: 0.6rem;
      }
    """


preview = BadgeVariants()

preview  # noqa: B018
