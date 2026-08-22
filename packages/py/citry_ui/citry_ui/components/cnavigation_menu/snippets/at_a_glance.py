# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationMenuAtAGlance(Component):
    template = """
      <c-CNavigationMenu label="Main navigation" variant="surface">
        <c-CNavigationMenuLink href="#overview" c-current="True">Overview</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="products">
          <c-fill name="label">Products</c-fill>
          <c-fill name="default"><c-CCol gap="sm"><strong>Explore products</strong><a href="#analytics">Analytics</a><a href="#automations">Automations</a></c-CCol></c-fill>
        </c-CNavigationMenuItem>
        <c-CNavigationMenuLink href="#pricing">Pricing</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = NavigationMenuAtAGlance()
preview  # noqa: B018
