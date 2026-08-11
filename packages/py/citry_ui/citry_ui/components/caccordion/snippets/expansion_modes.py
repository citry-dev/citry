import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ExpansionModes(Component):
    template = """
      <section class="expansion-modes" aria-label="Accordion expansion modes">
        <article>
          <h2>One section, always open</h2>
          <c-CAccordion value="roots" c-collapsible="False" variant="soft">
            <c-CAccordionItem value="roots">
              <c-fill name="title">Root network</c-fill>
              <c-fill name="default">Roots trade nutrients with underground fungi.</c-fill>
            </c-CAccordionItem>
            <c-CAccordionItem value="soil">
              <c-fill name="title">Living soil</c-fill>
              <c-fill name="default">A pinch of soil can hold billions of organisms.</c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        </article>
        <article>
          <h2>Several sections</h2>
          <c-CAccordion c-value="('cedar', 'hemlock')" multiple variant="soft">
            <c-CAccordionItem value="cedar">
              <c-fill name="title">Western red cedar</c-fill>
              <c-fill name="default">Scale-like leaves stay green through winter.</c-fill>
            </c-CAccordionItem>
            <c-CAccordionItem value="hemlock">
              <c-fill name="title">Western hemlock</c-fill>
              <c-fill name="default">Drooping leaders distinguish its young crowns.</c-fill>
            </c-CAccordionItem>
          </c-CAccordion>
        </article>
      </section>
    """

    css = """
      :where(.expansion-modes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.expansion-modes article) {
        min-width: 0;
      }

      :where(.expansion-modes h2) {
        margin-block: 0 0.625rem;
        font-size: 1rem;
      }
    """


preview = ExpansionModes()

preview  # noqa: B018
