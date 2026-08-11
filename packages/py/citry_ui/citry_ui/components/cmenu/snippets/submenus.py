import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedMenus(Component):
    template = """
      <section class="archive-submenu-demo">
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Choose a collection</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuSubmenu value="skies">
              <c-fill name="label">Celestial archives</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="constellations">Constellations</c-CMenuItem>
                <c-CMenuSubmenu value="moons">
                  <c-fill name="label">Moon records</c-fill>
                  <c-fill name="default">
                    <c-CMenuItem value="silver">Silver moon</c-CMenuItem>
                    <c-CMenuItem value="ember">Ember moon</c-CMenuItem>
                  </c-fill>
                </c-CMenuSubmenu>
              </c-fill>
            </c-CMenuSubmenu>
            <c-CMenuSubmenu value="seas">
              <c-fill name="label">Sunken archives</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="tides">Tide almanacs</c-CMenuItem>
                <c-CMenuItem value="leviathans">Leviathan sightings</c-CMenuItem>
              </c-fill>
            </c-CMenuSubmenu>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-submenu-demo) {
        display: grid;
        place-items: start center;
        min-block-size: 22rem;
        padding-inline: 5rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NestedMenus()

preview  # noqa: B018
