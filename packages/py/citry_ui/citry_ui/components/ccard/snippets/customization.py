import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardCustomization(Component):
    template = """
      <section class="card-customization">
        <div class="card-customization__linen">
          <c-CCard class_="card-customization__horizontal">
            <c-fill name="media">
              <div class="card-customization__weave" aria-hidden="true"></div>
            </c-fill>
            <c-fill name="header"><h2>Linen house</h2></c-fill>
            <c-fill name="default">
              Soft edges and warm neutrals made entirely with public variables and parts.
            </c-fill>
            <c-fill name="footer">Natural flax · washed finish</c-fill>
          </c-CCard>
        </div>

        <div class="card-customization__studio" data-theme="dark">
          <c-CCard class_="card-customization__horizontal" variant="outline">
            <c-fill name="media">
              <div class="card-customization__grid" aria-hidden="true"></div>
            </c-fill>
            <c-fill name="header"><h2>Night studio</h2></c-fill>
            <c-fill name="default">
              Crisp geometry and cool contrast adapt through the same stable contract.
            </c-fill>
            <c-fill name="actions">
              <c-CButton size="sm" variant="outline">Open palette</c-CButton>
            </c-fill>
          </c-CCard>
        </div>
      </section>
    """

    css = """
      :where(.card-customization) {
        display: grid;
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-customization > div) {
        padding: 1rem;
        border-radius: 1rem;
      }

      :where(.card-customization__linen) {
        --cui-card-background: #fffaf0;
        --cui-card-foreground: #3d3328;
        --cui-card-border-color: #d8c8ad;
        --cui-card-radius: 1.1rem;
        --cui-card-shadow: 0 0.8rem 2rem rgb(96 71 39 / 14%);
        background: #efe4d0;
      }

      :where(.card-customization__studio) {
        color-scheme: dark;
        --cui-card-background: #182235;
        --cui-card-foreground: #e7eefc;
        --cui-card-border-color: #607aa5;
        --cui-card-radius: 0.35rem;
        --cui-card-shadow: none;
        background: #0d1421;
      }

      :where(.card-customization__horizontal) {
        display: grid;
        grid-template-columns: minmax(8rem, 32%) 1fr;
      }

      :where(.card-customization__horizontal > [data-citry-ui-part="media"]) {
        grid-row: 1 / -1;
        border-start-start-radius: var(--cui-card-radius);
        border-start-end-radius: 0;
        border-end-start-radius: var(--cui-card-radius);
        border-end-end-radius: 0;
      }

      :where(.card-customization__horizontal > :not([data-citry-ui-part="media"])) {
        grid-column: 2;
      }

      :where(.card-customization h2) {
        margin: 0;
        font-size: 1.05rem;
      }

      :where(.card-customization__weave, .card-customization__grid) {
        min-block-size: 100%;
      }

      :where(.card-customization__weave) {
        background:
          repeating-linear-gradient(0deg, rgb(255 255 255 / 20%) 0 2px, transparent 2px 6px),
          #9f7950;
      }

      :where(.card-customization__grid) {
        background:
          linear-gradient(#5b78a8 1px, transparent 1px),
          linear-gradient(90deg, #5b78a8 1px, transparent 1px),
          #24324b;
        background-size: 1.5rem 1.5rem;
      }

      @media (max-width: 36rem) {
        :where(.card-customization__horizontal) {
          display: block;
        }

        :where(.card-customization__horizontal > [data-citry-ui-part="media"]) {
          border-start-start-radius: var(--cui-card-radius, 0.75rem);
          border-start-end-radius: var(--cui-card-radius, 0.75rem);
          border-end-start-radius: 0;
          border-end-end-radius: 0;
        }
      }
    """


preview = CardCustomization()

preview  # noqa: B018
