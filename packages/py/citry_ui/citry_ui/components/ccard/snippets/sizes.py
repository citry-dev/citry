import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardSizes(Component):
    template = """
      <section class="card-sizes" aria-label="Card sizes">
        <c-CCard size="sm" variant="outline">
          <c-fill name="header"><h2>Small</h2></c-fill>
          <c-fill name="default">Cedar drawer label and finish sample.</c-fill>
          <c-fill name="actions"><c-CButton size="sm" variant="ghost">Open</c-CButton></c-fill>
        </c-CCard>
        <c-CCard size="md" variant="outline">
          <c-fill name="header"><h2>Medium</h2></c-fill>
          <c-fill name="default">A balanced surface for a lamp, book, and cup.</c-fill>
          <c-fill name="actions"><c-CButton size="sm" variant="ghost">Open</c-CButton></c-fill>
        </c-CCard>
        <c-CCard size="lg" variant="outline">
          <c-fill name="header"><h2>Large</h2></c-fill>
          <c-fill name="default">Room for textile notes, dimensions, and a longer material story.</c-fill>
          <c-fill name="actions"><c-CButton size="sm" variant="ghost">Open</c-CButton></c-fill>
        </c-CCard>
      </section>
    """

    css = """
      :where(.card-sizes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 14rem), 1fr));
        gap: 1rem;
        align-items: start;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-sizes h2) {
        margin: 0;
        font-size: 1rem;
      }
    """


preview = CardSizes()

preview  # noqa: B018
