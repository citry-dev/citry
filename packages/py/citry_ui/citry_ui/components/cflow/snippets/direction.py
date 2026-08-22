import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FlowDirection(Component):
    template = """
      <section class="flow-direction" aria-label="Direction and long content">
        <c-CCol gap="sm">
          <strong>LTR kiln sequence</strong>
          <c-CRow><span>Load</span><span>Fire</span><span>Cool</span></c-CRow>
        </c-CCol>
        <div dir="rtl">
          <c-CCol gap="sm">
            <strong>تسلسل الفرن</strong>
            <c-CRow><span>تحميل</span><span>حرق</span><span>تبريد</span></c-CRow>
          </c-CCol>
        </div>
        <c-CRow class_="flow-direction__long">
          <strong>Long label</strong>
          <span>celadon-test-series-with-a-deliberately-long-unbroken-identifier</span>
        </c-CRow>
      </section>
    """

    css = """
      :where(.flow-direction) {
        display: grid;
        gap: 1.25rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-direction [data-citry-ui-part="row"]) {
        padding: 0.7rem;
        background: light-dark(#eee0c9, #372d24);
      }

      :where(.flow-direction__long span) {
        min-inline-size: 0;
        overflow-wrap: anywhere;
      }
    """


preview = FlowDirection()

preview  # noqa: B018
