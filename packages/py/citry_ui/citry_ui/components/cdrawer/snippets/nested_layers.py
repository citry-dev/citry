import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NestedLayers(Component):
    template = """
      <section>
        <c-CDrawer>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open archive tools</c-CButton>
          </c-fill>
          <c-fill name="title">Archive tools</c-fill>
          <c-fill name="default">
            <c-CMenu>
              <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
                <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Choose action</c-CButton>
              </c-fill>
              <c-fill name="default">
                <c-CMenuItem value="duplicate">Duplicate record</c-CMenuItem>
                <c-CMenuItem value="export">Export coordinates</c-CMenuItem>
              </c-fill>
            </c-CMenu>
          </c-fill>
        </c-CDrawer>
      </section>
    """


preview = NestedLayers()
preview  # noqa: B018
