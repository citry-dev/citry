# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomNavigation(Component):
    template = """
      <c-CNavigationMenu label="Aurora navigation" class_="aurora-nav" variant="surface"><c-CNavigationMenuLink href="#mission">Mission</c-CNavigationMenuLink><c-CNavigationMenuItem value="field-notes"><c-fill name="label">Field notes</c-fill><c-fill name="default"><strong>Fresh observations</strong><p>Follow the latest work from the field.</p></c-fill></c-CNavigationMenuItem></c-CNavigationMenu>
    """
    css = """
      .aurora-nav { --cui-navigation-menu-trigger-open-background:#dbeafe; --cui-navigation-menu-radius:1rem; --cui-navigation-menu-panel-inline-size:20rem; }
    """


preview = CustomNavigation()
preview  # noqa: B018
