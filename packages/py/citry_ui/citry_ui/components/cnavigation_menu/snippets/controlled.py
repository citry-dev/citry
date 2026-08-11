# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledNavigation(Component):
    template = """
      <section x-data="{open:null}"><p>Open: <strong x-text="open ?? 'none'"></strong></p>
        <c-CNavigationMenu label="Controlled navigation" $c-props="{value:open,onValueChange:(next)=>open=next}">
          <c-CNavigationMenuLink href="#home">Home</c-CNavigationMenuLink>
          <c-CNavigationMenuItem value="learn"><c-fill name="label">Learn</c-fill><c-fill name="default"><a href="#tutorials">Tutorials</a></c-fill></c-CNavigationMenuItem>
        </c-CNavigationMenu>
      </section>
    """


preview = ControlledNavigation()
preview  # noqa: B018
