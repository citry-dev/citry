# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationOrientation(Component):
    template = """
      <c-CNavigationMenu label="Account navigation" orientation="vertical" variant="surface">
        <c-CNavigationMenuLink href="#profile" c-current="True">Profile</c-CNavigationMenuLink>
        <c-CNavigationMenuItem value="teams"><c-fill name="label">Teams</c-fill><c-fill name="default"><a href="#research">Research</a><br><a href="#operations">Operations</a></c-fill></c-CNavigationMenuItem>
        <c-CNavigationMenuLink href="#billing">Billing</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = NavigationOrientation()
preview  # noqa: B018
