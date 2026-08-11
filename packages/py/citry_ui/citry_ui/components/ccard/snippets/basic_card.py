import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicCards(Component):
    template = """
      <section class="card-basics">
        <c-CCard>
          The south window gets soft light from breakfast until noon.
        </c-CCard>

        <c-CCard variant="outline">
          <c-fill name="header">
            <h2>Washed linen</h2>
            <p>Warm white · 140 g/m²</p>
          </c-fill>
        </c-CCard>

        <c-CCard variant="subtle">
          <c-fill name="footer">
            Hand-thrown stoneware · one of twelve
          </c-fill>
          <c-fill name="actions">
            <c-CButton size="sm" variant="ghost">Reserve vase</c-CButton>
          </c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-basics) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-basics h2, .card-basics p) {
        margin: 0;
      }

      :where(.card-basics h2) {
        font-size: 1rem;
      }

      :where(.card-basics p) {
        margin-block-start: 0.25rem;
        color: light-dark(#6b6257, #cfc5b8);
        font-size: 0.82rem;
      }
    """


preview = BasicCards()

preview  # noqa: B018
