# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NavigationKeyboard(Component):
    template = """
      <c-CCol gap="sm"><p>Tab normally. Use Arrow keys between top-level controls, Down to enter an open panel, and Escape to close it.</p><c-CNavigationMenu label="Keyboard example" loop><c-CNavigationMenuLink href="#start">Start</c-CNavigationMenuLink><c-CNavigationMenuItem value="topics"><c-fill name="label">Topics</c-fill><c-fill name="default"><a href="#accessibility">Accessibility</a></c-fill></c-CNavigationMenuItem><c-CNavigationMenuLink href="#finish">Finish</c-CNavigationMenuLink></c-CNavigationMenu></c-CCol>
    """


preview = NavigationKeyboard()
preview  # noqa: B018
