# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationVariants(Component):
    template = """
      <c-CCol gap="lg"><c-CNavigationMenu label="Small plain" size="sm"><c-CNavigationMenuLink href="#one">Small</c-CNavigationMenuLink><c-CNavigationMenuItem value="more"><c-fill name="label">More</c-fill><c-fill name="default">Small panel</c-fill></c-CNavigationMenuItem></c-CNavigationMenu><c-CNavigationMenu label="Large surface" variant="surface" size="lg"><c-CNavigationMenuLink href="#two">Large</c-CNavigationMenuLink><c-CNavigationMenuItem value="details"><c-fill name="label">Details</c-fill><c-fill name="default">Large panel</c-fill></c-CNavigationMenuItem></c-CNavigationMenu></c-CCol>
    """


preview = NavigationVariants()
preview  # noqa: B018
