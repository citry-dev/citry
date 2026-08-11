import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledDrawer(Component):
    template = """
      <section class="controlled-drawer" x-data="{open:false, accept:true, log:'No request yet'}">
        <c-CDrawer $c-props="{open, onOpenChange:(next, detail) => {
          log = `${detail.reason}: ${next ? 'open' : 'closed'}`; if (accept) open = next;
        }}">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Controlled archive</c-CButton>
          </c-fill>
          <c-fill name="title">Controlled archive</c-fill>
          <c-fill name="default">The owner may accept or decline visibility requests.</c-fill>
        </c-CDrawer>
        <label><input type="checkbox" x-model="accept" /> Accept requests</label>
        <output x-text="log"></output>
      </section>
    """
    css = """
      :where(.controlled-drawer) { display:grid; gap:.75rem; justify-items:start; padding:1rem; }
    """


preview = ControlledDrawer()
preview  # noqa: B018
