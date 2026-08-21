import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarCustomization(Component):
    template = """
      <c-CSidebar label="Custom navigation" variant="floating" side="inline-end" c-class_="['ocean-sidebar']">
        <c-fill name="toggle"><c-CIcon name="menu" /></c-fill>
        <c-fill name="header"><strong>Ocean lab</strong></c-fill>
        <c-fill name="default"><p>Public variables and parts customize the stable landmark.</p></c-fill>
      </c-CSidebar>
    """
    css = """
      :where(.ocean-sidebar) {
        --cui-sidebar-background: light-dark(#eff8ff, #102a43);
        --cui-sidebar-border-color: light-dark(#84caff, #2e90fa);
        --cui-sidebar-width: 18rem;
      }
    """


preview = SidebarCustomization()
preview  # noqa: B018
