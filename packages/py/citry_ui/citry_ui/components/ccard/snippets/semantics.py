import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CardSemantics(Component):
    template = """
      <section class="card-semantics">
        <article>
          <h2>Neutral group</h2>
          <c-CCard>
            Decorative cushions can sit in an ordinary layout without becoming a document section.
          </c-CCard>
        </article>

        <article>
          <h2>Independent article</h2>
          <c-CCard tag="article" c-attrs="{'aria-labelledby': 'chair-title'}">
            <c-fill name="header"><h3 id="chair-title">The spindle chair returns</h3></c-fill>
            <c-fill name="default">A complete journal note with its own heading and subject.</c-fill>
          </c-CCard>
        </article>

        <section aria-labelledby="materials-title">
          <h2 id="materials-title">Named section</h2>
          <c-CCard tag="section" c-attrs="{'aria-labelledby': 'wool-title'}" variant="outline">
            <c-fill name="header"><h3 id="wool-title">Wool upholstery</h3></c-fill>
            <c-fill name="default">A subsection of the wider materials guide.</c-fill>
          </c-CCard>
        </section>

        <article>
          <h2>List item</h2>
          <ul>
            <c-CCard tag="li" variant="subtle">Oak side table</c-CCard>
            <c-CCard tag="li" variant="subtle">Linen floor lamp</c-CCard>
          </ul>
        </article>
      </section>
    """

    css = """
      :where(.card-semantics) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1.25rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.card-semantics h2, .card-semantics h3) {
        margin-block-start: 0;
      }

      :where(.card-semantics h2) {
        font-size: 1rem;
      }

      :where(.card-semantics h3) {
        margin-block-end: 0;
        font-size: 0.95rem;
      }

      :where(.card-semantics ul) {
        display: grid;
        gap: 0.5rem;
        margin: 0;
        padding: 0;
        list-style: none;
      }
    """


preview = CardSemantics()

preview  # noqa: B018
