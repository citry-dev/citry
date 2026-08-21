import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarCollapseModes(Component):
    template = """
      <div class="sidebar-modes">
        <c-CSidebar label="Rail example" c-collapsed="True" collapsible="rail" size="sm">
          <strong>Rail content remains available.</strong>
        </c-CSidebar>
        <c-CSidebar label="Offcanvas example" c-collapsed="True" collapsible="offcanvas" size="sm">
          <strong>The panel starts hidden.</strong>
        </c-CSidebar>
        <c-CSidebar label="Permanent example" collapsible="none" size="sm">
          <strong>No toggle is rendered.</strong>
        </c-CSidebar>
      </div>
    """
    css = ":where(.sidebar-modes){display:flex;align-items:flex-start;gap:1rem;min-block-size:14rem}"


preview = SidebarCollapseModes()
preview  # noqa: B018
