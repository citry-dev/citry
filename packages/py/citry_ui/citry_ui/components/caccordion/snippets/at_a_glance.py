import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AccordionAtAGlance(Component):
    template = """
      <section class="forest-guide" aria-labelledby="forest-guide-title">
        <header>
          <p>Temperate rainforest</p>
          <h2 id="forest-guide-title">Layers of the forest</h2>
        </header>
        <c-CAccordion value="canopy" variant="separated">
          <c-CAccordionItem value="canopy">
            <c-fill name="title">Canopy</c-fill>
            <c-fill name="default">
              Interlocking crowns collect most sunlight and shelter the layers below.
            </c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="understory">
            <c-fill name="title">Understory</c-fill>
            <c-fill name="default">
              Ferns, saplings, and mosses thrive in filtered green light.
            </c-fill>
          </c-CAccordionItem>
          <c-CAccordionItem value="floor">
            <c-fill name="title">Forest floor</c-fill>
            <c-fill name="default">
              Fungi and invertebrates return fallen wood to the soil.
            </c-fill>
          </c-CAccordionItem>
        </c-CAccordion>
      </section>
    """

    css = """
      :where(.forest-guide) {
        display: grid;
        gap: 1rem;
        max-width: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.forest-guide h2, .forest-guide p) {
        margin: 0;
      }

      :where(.forest-guide header > p) {
        color: light-dark(#2f6b45, #86d29e);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    """


preview = AccordionAtAGlance()

preview  # noqa: B018
