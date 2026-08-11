import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuGroups(Component):
    template = """
      <section class="archive-group-demo">
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Archive sections</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuGroup>
              <c-fill name="label">Public halls</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="maps">Star maps</c-CMenuItem>
                <c-CMenuItem value="herbals">Moonlit herbals</c-CMenuItem>
              </c-fill>
            </c-CMenuGroup>
            <c-CMenuSeparator />
            <c-CMenuGroup>
              <c-fill name="label">Restricted vaults</c-fill>
              <c-fill name="default">
                <c-CMenuItem value="prophecies">Sealed prophecies</c-CMenuItem>
                <c-CMenuItem value="curses" disabled>Curses under glass</c-CMenuItem>
              </c-fill>
            </c-CMenuGroup>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-group-demo) {
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = MenuGroups()

preview  # noqa: B018
