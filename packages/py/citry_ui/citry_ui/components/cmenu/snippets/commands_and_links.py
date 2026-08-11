import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuCommandsAndLinks(Component):
    template = """
      <section
        class="archive-command-demo"
        x-data="{lastAction: 'none'}"
      >
        <c-CMenu
          $c-props="{
            onAction: (value) => lastAction = value,
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Folio actions</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="duplicate">Duplicate folio</c-CMenuItem>
            <c-CMenuItem @click="lastAction = 'annotate'">Add annotation</c-CMenuItem>
            <c-CMenuItem href="#restricted-shelf">Visit restricted shelf</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <output x-text="`Last command: ${lastAction}`">Last command: none</output>
      </section>
    """

    css = """
      :where(.archive-command-demo) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;
        min-block-size: 14rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-command-demo output) {
        color: light-dark(#66451f, #dec08f);
      }
    """


preview = MenuCommandsAndLinks()

preview  # noqa: B018
