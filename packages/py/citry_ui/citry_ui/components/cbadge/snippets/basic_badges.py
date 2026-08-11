import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicBadges(Component):
    template = """
      <div class="badge-basic">
        <p>Fluorite <c-CBadge>New</c-CBadge></p>
        <p>Cabinet 7 <c-CBadge shape="pill">24</c-CBadge></p>
        <p>Catalog record <c-CBadge variant="outline">Draft</c-CBadge></p>
      </div>
    """
    css = """
      :where(.badge-basic) {
        display: grid;
        gap: 0.75rem;
        max-inline-size: 24rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.badge-basic p) {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: 0;
        padding-block-end: 0.5rem;
        border-block-end: 1px solid light-dark(#d8d2c6, #4f4a42);
      }
    """


preview = BasicBadges()

preview  # noqa: B018
