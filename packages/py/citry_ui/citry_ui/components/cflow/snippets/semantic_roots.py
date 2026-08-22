import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowSemanticRoots(Component):
    template = """
      <c-CCol class_="flow-semantics" gap="lg">
        <c-CRow tag="nav" c-attrs="{'aria-label': 'Ceramics notebook'}">
          <a href="#clay">Clay</a><a href="#glaze">Glaze</a><a href="#kilns">Kilns</a>
        </c-CRow>
        <c-CCol tag="ol" gap="sm" class_="flow-semantics__list">
          <li>Wedge the porcelain.</li>
          <li>Center it on the wheel.</li>
          <li>Pull the walls evenly.</li>
        </c-CCol>
      </c-CCol>
    """

    css = """
      :where(.flow-semantics) {
        max-inline-size: 36rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-semantics a) {
        color: light-dark(#8a3f24, #f0a47c);
      }

      :where(.flow-semantics__list) {
        margin: 0;
        padding-inline-start: 1.4rem;
      }
    """


preview = FlowSemanticRoots()

preview  # noqa: B018
