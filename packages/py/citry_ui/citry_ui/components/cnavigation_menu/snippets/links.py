import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationLinks(Component):
    template = """
      <c-CNavigationMenu label="Documentation">
        <c-CNavigationMenuLink href="#guide" c-current="True">Guide</c-CNavigationMenuLink>
        <c-CNavigationMenuLink href="#reference">Reference</c-CNavigationMenuLink>
        <c-CNavigationMenuLink href="#examples">Examples</c-CNavigationMenuLink>
      </c-CNavigationMenu>
    """


preview = NavigationLinks()
preview  # noqa: B018
