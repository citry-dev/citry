import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SidebarPresentation(Component):
    template = """
      <c-CSidebar
        label="Sticky tools"
        variant="floating"
        size="lg"
        c-sticky="True"
        c-style="{'--cui-sidebar-sticky-offset':'1rem'}"
      >
        <c-fill name="header"><strong>Inspector</strong></c-fill>
        <c-fill name="default">
          <p>Long tool content scrolls independently between fixed regions.</p>
          <p>Keep adding contextual controls here.</p>
        </c-fill>
        <c-fill name="footer"><c-CButton size="sm">Apply</c-CButton></c-fill>
      </c-CSidebar>
    """


preview = SidebarPresentation()
preview  # noqa: B018
