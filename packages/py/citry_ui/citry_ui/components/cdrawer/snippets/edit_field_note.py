import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditFieldNote(Component):
    template = """
      <section class="drawer-example">
        <p>Northern ridge · 01:42</p>
        <c-CDrawer>
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Edit field note</c-CButton>
          </c-fill>
          <c-fill name="title">Aurora field note</c-fill>
          <c-fill name="description">Update the observation saved at the northern ridge.</c-fill>
          <c-fill name="default">
            <label for="drawer-note">Observation</label>
            <textarea id="drawer-note" rows="7">Green arcs above the eastern horizon.</textarea>
          </c-fill>
          <c-fill name="actions" data="{ close_attrs }">
            <c-CButton variant="ghost" c-attrs="close_attrs">Cancel</c-CButton>
            <c-CButton c-attrs="close_attrs">Save note</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.drawer-example) { display:grid; gap:.75rem; justify-items:start; padding:1.5rem; }
      :where(.drawer-example p) { margin:0; color:color-mix(in srgb, CanvasText 68%, transparent); }
      :where(.cui-drawer__body label, .cui-drawer__body textarea) { display:block; inline-size:100%; }
      :where(.cui-drawer__body textarea) { box-sizing:border-box; margin-block-start:.4rem; padding:.75rem; }
    """


preview = EditFieldNote()
preview  # noqa: B018
