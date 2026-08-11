import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuItemContent(Component):
    template = """
      <section class="archive-content-demo">
        <c-CMenu>
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Catalog tools</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="search">
              <c-fill name="start"><c-CIcon name="search" /></c-fill>
              <c-fill name="default">Search illuminated texts</c-fill>
              <c-fill name="description">Find titles, scribes, and sigils.</c-fill>
              <c-fill name="end"><kbd>⌘ K</kbd></c-fill>
            </c-CMenuItem>
            <c-CMenuItem value="bookmark">
              <c-fill name="start"><c-CIcon name="star" /></c-fill>
              <c-fill name="default">Mark this passage</c-fill>
              <c-fill name="end"><kbd>M</kbd></c-fill>
            </c-CMenuItem>
          </c-fill>
        </c-CMenu>
      </section>
    """

    css = """
      :where(.archive-content-demo) {
        min-block-size: 15rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-content-demo kbd) {
        padding: 0.1rem 0.35rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.3rem;
        font: inherit;
        font-size: 0.75rem;
      }
    """


preview = MenuItemContent()

preview  # noqa: B018
