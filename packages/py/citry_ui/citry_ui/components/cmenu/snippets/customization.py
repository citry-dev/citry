import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedMenus(Component):
    template = """
      <section class="archive-theme-demo">
        <div class="archive-theme-demo__moon">
          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
              <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Moon archive</c-CButton>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="phases">Moon phases</c-CMenuItem>
              <c-CMenuItem value="eclipses">Eclipse records</c-CMenuItem>
            </c-fill>
          </c-CMenu>
        </div>
        <div class="archive-theme-demo__ember">
          <c-CMenu>
            <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
              <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Ember archive</c-CButton>
            </c-fill>
            <c-fill name="default">
              <c-CMenuItem value="dragons">Dragon chronicles</c-CMenuItem>
              <c-CMenuItem value="ashes" intent="danger">Destroy ash record</c-CMenuItem>
            </c-fill>
          </c-CMenu>
        </div>
      </section>
    """

    css = """
      :where(.archive-theme-demo) {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        min-block-size: 18rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-theme-demo__moon) {
        --cui-menu-background: light-dark(#f4f2ff, #17142d);
        --cui-menu-border-color: light-dark(#8f83c7, #7065aa);
        --cui-menu-focus-background: light-dark(#4c3e92, #b6a9ff);
        --cui-menu-focus-foreground: light-dark(#ffffff, #17142d);
        --cui-menu-radius: 1rem;
      }

      :where(.archive-theme-demo__ember) {
        --cui-menu-background: light-dark(#fff7ed, #2a1710);
        --cui-menu-border-color: light-dark(#d97706, #f59e0b);
        --cui-menu-focus-background: light-dark(#9a3412, #fdba74);
        --cui-menu-focus-foreground: light-dark(#ffffff, #2a1710);
        --cui-menu-danger-color: light-dark(#991b1b, #fecaca);
        --cui-menu-radius: 0.35rem;
      }
    """


preview = CustomizedMenus()

preview  # noqa: B018
