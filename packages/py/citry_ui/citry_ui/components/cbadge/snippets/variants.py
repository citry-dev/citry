import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeVariants(Component):
    template = """
      <c-CStack class_="badge-variants" gap="sm">
        <c-CGroup><strong>Soft</strong><c-CBadge intent="primary">Lapis</c-CBadge></c-CGroup>
        <c-CGroup><strong>Solid</strong><c-CBadge intent="primary" variant="solid">Lapis</c-CBadge></c-CGroup>
        <c-CGroup><strong>Outline</strong><c-CBadge intent="primary" variant="outline">Lapis</c-CBadge></c-CGroup>
      </c-CStack>
    """
    css = """
      :where(.badge-variants) {
        max-inline-size: 20rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-variants > [data-citry-ui-part="group"]) {
        justify-content: space-between;
        padding: 0.75rem;
        border: 1px solid light-dark(#d4cabc, #514940);
        border-radius: 0.6rem;
      }
    """


preview = BadgeVariants()

preview  # noqa: B018
