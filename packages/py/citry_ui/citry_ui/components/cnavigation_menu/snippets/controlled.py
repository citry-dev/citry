# ruff: noqa: E501

import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledNavigation(Component):
    template = """
      <section ><p>Open: <strong v-text="open ?? 'none'"></strong></p>
        <c-CNavigationMenu label="Controlled navigation" :value="open" :onValueChange="(next)=>open=next">
          <c-CNavigationMenuLink href="#home">Home</c-CNavigationMenuLink>
          <c-CNavigationMenuItem value="learn"><c-fill name="label">Learn</c-fill><c-fill name="default"><a href="#tutorials">Tutorials</a></c-fill></c-CNavigationMenuItem>
        </c-CNavigationMenu>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            open:null
          };
        },
      });
    """


preview = ControlledNavigation()
preview  # noqa: B018
