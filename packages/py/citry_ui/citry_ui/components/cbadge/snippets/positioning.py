import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BadgePositioning(Component):
    template = """
      <div class="badge-positioning">
        <c-CButton c-attrs="{'aria-label': 'Field notes, 7 unread'}">
          Field notes
          <c-CBadge intent="danger" shape="pill">7</c-CBadge>
        </c-CButton>
      </div>
    """
    css = """
      :where(.badge-positioning) {
        min-block-size: 7rem;
        padding: 1.5rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-positioning [data-citry-ui-part="button"]) {
        position: relative;
      }

      :where(.badge-positioning [data-citry-ui-part="badge"]) {
        position: absolute;
        inset-block-start: 0;
        inset-inline-end: 0;
        translate: 45% -45%;
      }
    """


preview = BadgePositioning()

preview  # noqa: B018
