import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardVariants(Component):
    template = """
      <section class="card-variants" aria-label="Card variants">
        <c-CCard variant="elevated">
          <c-fill name="header"><h2>Elevated</h2></c-fill>
          <c-fill name="default">A focal surface for the linen floor lamp.</c-fill>
        </c-CCard>
        <c-CCard variant="outline">
          <c-fill name="header"><h2>Outline</h2></c-fill>
          <c-fill name="default">A clear boundary for the oak side table.</c-fill>
        </c-CCard>
        <c-CCard variant="subtle">
          <c-fill name="header"><h2>Subtle</h2></c-fill>
          <c-fill name="default">A quiet grouping for woven storage baskets.</c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        padding: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-variants h2) {
        margin: 0;
        font-size: 1rem;
      }
    """


preview = CardVariants()

preview  # noqa: B018
