import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgeIcons(Component):
    template = """
      <c-CGroup class_="badge-icons">
        <c-CBadge intent="success">
          <c-fill name="start"><c-CIcon name="check" /></c-fill>
          <c-fill name="default">Verified origin</c-fill>
        </c-CBadge>
        <c-CBadge intent="warn" variant="outline">
          <c-fill name="default">Requires gloves</c-fill>
          <c-fill name="end"><c-CIcon name="triangle-alert" /></c-fill>
        </c-CBadge>
      </c-CGroup>
    """
    css = """
      :where(.badge-icons) {
        max-inline-size: 30rem;
        padding: 1rem;
        background: light-dark(#f4f0e7, #29251f);
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BadgeIcons()

preview  # noqa: B018
