import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class GridAtAGlance(Component):
    template = """
      <c-CContainer class_="mineral-atlas" size="lg">
        <header class="mineral-atlas__header">
          <p>Field atlas · volcanic collection</p>
          <h2>Minerals born from fire</h2>
        </header>
        <c-CGrid sm="2" lg="4" gap="lg">
          <article class="mineral-atlas__card mineral-atlas__card--olivine">
            <span class="mineral-atlas__sample"></span>
            <h3>Olivine</h3>
            <p>Olive-green crystals found in basalt and mantle rock.</p>
          </article>
          <article class="mineral-atlas__card mineral-atlas__card--obsidian">
            <span class="mineral-atlas__sample"></span>
            <h3>Obsidian</h3>
            <p>Volcanic glass cooled before crystals could form.</p>
          </article>
          <article class="mineral-atlas__card mineral-atlas__card--sulfur">
            <span class="mineral-atlas__sample"></span>
            <h3>Sulfur</h3>
            <p>Bright deposits gathered around volcanic vents.</p>
          </article>
          <article class="mineral-atlas__card mineral-atlas__card--pumice">
            <span class="mineral-atlas__sample"></span>
            <h3>Pumice</h3>
            <p>Foamed lava light enough to float on water.</p>
          </article>
        </c-CGrid>
      </c-CContainer>
    """

    css = """
      :where(.mineral-atlas) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.mineral-atlas__header) {
        margin-block-end: 1.25rem;
      }

      :where(.mineral-atlas__header h2, .mineral-atlas__header p, .mineral-atlas__card h3, .mineral-atlas__card p) {
        margin: 0;
      }

      :where(.mineral-atlas__header p) {
        color: light-dark(#7c3f16, #f4ad74);
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }

      :where(.mineral-atlas__header h2) {
        margin-block-start: 0.25rem;
        font-size: 1.1rem;
      }

      :where(.mineral-atlas__card) {
        padding: 1rem;
        border: 1px solid light-dark(#d7d3c8, #55524b);
        border-radius: 0.8rem;
        background: light-dark(#fffefa, #22211f);
      }

      :where(.mineral-atlas__sample) {
        display: block;
        inline-size: 2.25rem;
        block-size: 2.25rem;
        margin-block-end: 0.8rem;
        border-radius: 0.65rem 1rem 0.5rem 0.9rem;
        background: var(--sample-color);
        box-shadow: inset -0.3rem -0.3rem 0.7rem rgb(0 0 0 / 20%);
        transform: rotate(-7deg);
      }

      :where(.mineral-atlas__card h3) {
        font-size: 0.9rem;
      }

      :where(.mineral-atlas__card p) {
        margin-block-start: 0.35rem;
        color: GrayText;
        font-size: 0.78rem;
        line-height: 1.45;
      }

      :where(.mineral-atlas__card--olivine) {
        --sample-color: #7c9d38;
      }

      :where(.mineral-atlas__card--obsidian) {
        --sample-color: #493e57;
      }

      :where(.mineral-atlas__card--sulfur) {
        --sample-color: #efc928;
      }

      :where(.mineral-atlas__card--pumice) {
        --sample-color: #caa68e;
      }
    """


preview = GridAtAGlance()

preview  # noqa: B018
