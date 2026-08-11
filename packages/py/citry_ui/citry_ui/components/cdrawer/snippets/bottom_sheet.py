import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BottomSheet(Component):
    template = """
      <section class="sheet-example">
        <c-CDrawer placement="block-end" size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open observation actions</c-CButton>
          </c-fill>
          <c-fill name="title">Observation actions</c-fill>
          <c-fill name="default">
            <c-CButton variant="ghost" block>Duplicate note</c-CButton>
            <c-CButton variant="ghost" block>Share coordinates</c-CButton>
          </c-fill>
        </c-CDrawer>
      </section>
    """
    css = """
      :where(.sheet-example) { display:grid; place-items:center; min-block-size:10rem; }
      :where(.sheet-example .cui-drawer__body) { display:grid; gap:.5rem; }
    """


preview = BottomSheet()
preview  # noqa: B018
