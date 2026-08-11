# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RichNavigationPanels(Component):
    template = """
      <c-CNavigationMenu label="Product navigation" value="platform">
        <c-CNavigationMenuLink href="#home">Home</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="platform">
          <c-fill name="label">Platform</c-fill>
          <c-fill name="default"><c-CGrid cols="2" gap="sm"><c-CCard variant="subtle"><c-fill name="header"><strong>Observe</strong></c-fill><c-fill name="default">Capture field signals.</c-fill></c-CCard><c-CCard variant="subtle"><c-fill name="header"><strong>Coordinate</strong></c-fill><c-fill name="default">Keep teams aligned.</c-fill></c-CCard></c-CGrid></c-fill>
        </c-CNavigationMenuItem>
        <c-CNavigationMenuLink href="#company">Company</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = RichNavigationPanels()
preview  # noqa: B018
