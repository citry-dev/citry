import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuAtAGlance(Component):
    template = """
      <section class="archive-menu-demo">
        <p>Enchanted archive</p>
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Open archive menu</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="rename">Rename folio</c-CMenuItem>
            <c-CMenuItem href="#moon-catalog">Open moon catalog</c-CMenuItem>
            <c-CMenuSubmenu value="send-to">
              <c-fill name="label">Send to collection</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="astronomy">Astronomy</c-CMenuItem>
                <c-CMenuItem value="mythology">Mythology</c-CMenuItem>
              </c-fill>
            </c-CMenuSubmenu>
            <c-CMenuSeparator />
            <c-CMenuItem value="banish" intent="danger">Banish folio</c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-menu-demo) {
        display: grid;
        gap: 0.75rem;
        justify-items: start;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-menu-demo > p) {
        margin: 0;
        color: light-dark(#7a4b18, #e8bd76);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = MenuAtAGlance()

preview  # noqa: B018
