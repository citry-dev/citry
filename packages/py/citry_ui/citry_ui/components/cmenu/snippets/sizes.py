import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuSizes(Component):
    template = """
      <section class="archive-size-demo">
        <c-CMenu size="sm">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton size="sm" c-disabled="activator_disabled" c-attrs="activator_attrs">Small</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="index">Pocket index</c-CMenuItem>
            <c-CMenuItem value="notes">Margin notes</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <c-CMenu size="md">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Medium</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="index">Reading index</c-CMenuItem>
            <c-CMenuItem value="notes">Scribe notes</c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <c-CMenu size="lg">
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton size="lg" c-disabled="activator_disabled" c-attrs="activator_attrs">Large</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="index">Grand index</c-CMenuItem>
            <c-CMenuItem value="notes">Archivist notes</c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-size-demo) {
        display: flex;
        flex-wrap: wrap;
        align-items: start;
        gap: 1rem;
        min-block-size: 17rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = MenuSizes()

preview  # noqa: B018
