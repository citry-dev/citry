import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ScrollAreaCustomization(Component):
    template = """
      <section class="scroll-area-customization">
        <article class="scroll-area-brand scroll-area-brand--orchard">
          <h3>Orchard notes</h3>
          <c-CScrollArea
            class_="brand-scroll"
            aria_label="Orchard notes"
            scrollbar_width="thin"
            scrollbar_gutter="stable"
          >
            <div class="scroll-area-customization__notes">
              <p>Pear block: pollinator rows checked.</p>
              <p>North field: irrigation pressure normal.</p>
              <p>West field: pruning review scheduled.</p>
              <p>Harvest window: seven days remaining.</p>
              <p>Cold store: capacity confirmed.</p>
            </div>
          </c-CScrollArea>
        </article>

        <article
          class="scroll-area-brand scroll-area-brand--harbor"
          style="color-scheme:dark"
        >
          <h3>Harbor notes</h3>
          <c-CScrollArea
            class_="brand-scroll"
            aria_label="Harbor notes"
            scrollbar_gutter="stable-both-edges"
          >
            <div class="scroll-area-customization__notes">
              <p>North berth: loading complete.</p>
              <p>East pier: tide window confirmed.</p>
              <p>Customs desk: manifest approved.</p>
              <p>Harbor pilot: departure booked.</p>
              <p>Weather station: visibility clear.</p>
            </div>
          </c-CScrollArea>
        </article>
      </section>
    """

    css = """
      :where(.scroll-area-customization) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.scroll-area-brand) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.scroll-area-brand h3) {
        margin: 0;
      }

      :where(.scroll-area-brand--orchard) {
        background: #f5f0df;
        color: #203422;
        --cui-scroll-area-max-block-size: 10rem;
        --cui-scroll-area-background: #fffdf5;
        --cui-scroll-area-foreground: #203422;
        --cui-scroll-area-border-color: #78916d;
        --cui-scroll-area-focus-color: #315f37;
        --cui-scroll-area-radius: 1rem;
      }

      :where(.scroll-area-brand--harbor) {
        background: #102b38;
        color: #eefaff;
        --cui-scroll-area-max-block-size: 10rem;
        --cui-scroll-area-background: #173c4c;
        --cui-scroll-area-foreground: #eefaff;
        --cui-scroll-area-border-color: #72b5ce;
        --cui-scroll-area-focus-color: #c6ecff;
        --cui-scroll-area-scrollbar-color: #9eddf4 #173c4c;
      }

      .scroll-area-brand
      .brand-scroll[data-citry-ui-part="scroll-area"] {
        border-width: 2px;
      }

      :where(.scroll-area-customization__notes) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
      }

      :where(.scroll-area-customization__notes p) {
        margin: 0;
      }

      @media (forced-colors: active) {
        :where(.scroll-area-brand) {
          border: 1px solid CanvasText;
        }
      }

      @media print {
        :where(.scroll-area-brand) {
          background: transparent;
          color: black;
        }
      }
    """


preview = ScrollAreaCustomization()

preview  # noqa: B018
