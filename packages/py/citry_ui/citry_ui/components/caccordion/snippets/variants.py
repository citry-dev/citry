import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AccordionVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="accordion-variants" aria-label="Accordion variants">
        <c-for each="variant in variants">
          <article>
            <h2>{{ variant }}</h2>
            <c-CAccordion c-variant="variant" value="rain">
              <c-CAccordionItem value="rain">
                <c-fill name="title">Rainfall</c-fill>
                <c-fill name="default">Frequent mist keeps the forest green.</c-fill>
              </c-CAccordionItem>
              <c-CAccordionItem value="light">
                <c-fill name="title">Filtered light</c-fill>
                <c-fill name="default">Sunflecks move across the understory.</c-fill>
              </c-CAccordionItem>
            </c-CAccordion>
          </article>
        </c-for>
        <article class="accordion-variants__sizes">
          <h2>Sizes</h2>
          <div class="accordion-variants__size-grid">
            <c-for each="size in sizes">
              <div>
                <h3>{{ size }}</h3>
                <c-CAccordion c-size="size" value="moss" variant="soft">
                  <c-CAccordionItem value="moss">
                    <c-fill name="title">Moss cover</c-fill>
                    <c-fill name="default">Soft ground holds overnight rain.</c-fill>
                  </c-CAccordionItem>
                </c-CAccordion>
              </div>
            </c-for>
          </div>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "variants": ("outline", "soft", "separated", "plain"),
            "sizes": ("sm", "md", "lg"),
        }

    css = """
      :where(.accordion-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1.25rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.accordion-variants article) {
        min-width: 0;
      }

      :where(.accordion-variants__sizes) {
        grid-column: 1 / -1;
      }

      :where(.accordion-variants__size-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
      }

      :where(.accordion-variants h2) {
        margin-block: 0 0.625rem;
        font-size: 0.875rem;
        text-transform: capitalize;
      }

      :where(.accordion-variants h3) {
        margin-block: 0 0.5rem;
        font-size: 0.75rem;
        text-transform: uppercase;
      }
    """


preview = AccordionVariants()

preview  # noqa: B018
