import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridCustomization(Component):
    template = """
      <section class="grid-custom" aria-labelledby="grid-custom-title">
        <h2 id="grid-custom-title">Custom field trays</h2>
        <div class="grid-custom__brand">
          <c-CGrid class_="grid-custom__variable-grid">
            <span>Granite</span><span>Gabbro</span><span>Rhyolite</span>
          </c-CGrid>
        </div>
        <div class="grid-custom__query-box">
          <c-CGrid class_="grid-custom__query-grid">
            <span>Slate</span><span>Schist</span><span>Gneiss</span>
          </c-CGrid>
        </div>
        <div dir="rtl" class="grid-custom__rtl">
          <c-CContainer gutter="xl">
            Logical gutters follow the reading direction without a separate RTL input.
          </c-CContainer>
        </div>
      </section>
    """

    css = """
      :where(.grid-custom) {
        max-inline-size: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.grid-custom h2) {
        margin: 0 0 0.75rem;
        font-size: 0.95rem;
      }

      :where(.grid-custom__brand) {
        --cui-grid-columns: 3;
        --cui-grid-gap: 0.35rem;
        padding: 0.75rem;
        border-radius: 0.55rem;
        background: light-dark(#e9f0f7, #1d2e3e);
      }

      :where(.grid-custom__brand [data-citry-ui-part="grid"] > span) {
        padding: 0.55rem;
        border-radius: 0.3rem;
        background: light-dark(#ffffff, #2c4357);
        font-size: 0.74rem;
        text-align: center;
      }

      :where(.grid-custom__query-box) {
        container-type: inline-size;
        margin-block-start: 0.75rem;
        padding: 0.75rem;
        border: 1px solid light-dark(#b9af9d, #6c6254);
        border-radius: 0.55rem;
      }

      :where(.grid-custom__query-grid > span) {
        padding: 0.5rem;
        background: light-dark(#f4eadb, #3a2d22);
        font-size: 0.74rem;
        text-align: center;
      }

      @container (min-width: 28rem) {
        :where(.grid-custom__query-grid) {
          --cui-grid-columns: 3;
        }
      }

      :where(.grid-custom__rtl) {
        margin-block-start: 0.75rem;
        border-inline-start: 0.25rem solid #7f5baa;
        background: light-dark(#f6efff, #332541);
        font-size: 0.74rem;
      }
    """


preview = GridCustomization()

preview  # noqa: B018
