# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationStates(Component):
    template = """
      <c-CNavigationMenu label="Navigation states">
        <c-CNavigationMenuLink href="#home" c-current="True">Current page</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="available"><c-fill name="label">Available</c-fill><c-fill name="default">Ready to explore.</c-fill></c-CNavigationMenuItem>
        <c-CNavigationMenuItem value="locked" disabled><c-fill name="label">Unavailable</c-fill><c-fill name="default">Hidden panel.</c-fill></c-CNavigationMenuItem>
      </c-CNavigationMenu>
    """


preview = NavigationStates()
preview  # noqa: B018
