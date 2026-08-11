import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DrawerAtAGlance(Component):
    template = """
      <section class="drawer-sampler">
        <c-CDrawer placement="inline-start" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="outline" c-attrs="activator_attrs">Leading Drawer</c-CButton>
          </c-fill>
          <c-fill name="title">Atlas index</c-fill>
          <c-fill name="default">Browse nearby observations.</c-fill>
        </c-CDrawer>
        <c-CDrawer placement="inline-end">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Trailing Drawer</c-CButton>
          </c-fill>
          <c-fill name="title">Field note</c-fill>
          <c-fill name="default">Edit the selected observation.</c-fill>
        </c-CDrawer>
        <c-CDrawer placement="block-end" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton variant="ghost" c-attrs="activator_attrs">Bottom Sheet</c-CButton>
          </c-fill>
          <c-fill name="title">Quick actions</c-fill>
          <c-fill name="default">Choose an action for this record.</c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.drawer-sampler) { display:flex; flex-wrap:wrap; gap:.75rem; padding:2rem 1rem; }
    """


preview = DrawerAtAGlance()
preview  # noqa: B018
