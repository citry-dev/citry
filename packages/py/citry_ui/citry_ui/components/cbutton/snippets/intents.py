import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonIntents(Component):
    template = """
      <section class="button-intents">
        <article>
          <h2>Neutral</h2>
          <div>
            <c-CButton intent="neutral">View habitat</c-CButton>
            <c-CButton intent="neutral" variant="outline">View habitat</c-CButton>
          </div>
        </article>
        <article>
          <h2>Accent</h2>
          <div>
            <c-CButton intent="primary">Begin survey</c-CButton>
            <c-CButton intent="primary" variant="outline">Begin survey</c-CButton>
          </div>
        </article>
        <article>
          <h2>Positive</h2>
          <div>
            <c-CButton intent="success">Protect grove</c-CButton>
            <c-CButton intent="success" variant="outline">Protect grove</c-CButton>
          </div>
        </article>
        <article>
          <h2>Warning</h2>
          <div>
            <c-CButton intent="warn">Check conditions</c-CButton>
            <c-CButton intent="warn" variant="outline">Check conditions</c-CButton>
          </div>
        </article>
        <article>
          <h2>Negative</h2>
          <div>
            <c-CButton intent="danger">Remove invasive</c-CButton>
            <c-CButton intent="danger" variant="outline">Remove invasive</c-CButton>
          </div>
        </article>
      </section>
    """

    css = """
      :where(.button-intents) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 0.75rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-intents article) {
        display: grid;
        gap: 0.65rem;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-intents h2) {
        margin-block: 0;
        font-size: 0.875rem;
      }

      :where(.button-intents article div) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }
    """


preview = ButtonIntents()

preview  # noqa: B018
