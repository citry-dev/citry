import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonAtAGlance(Component):
    template = """
      <section class="button-glance">
        <article class="button-glance__card">
          <header>
            <p>Woodland field guide</p>
            <h2>Follow the fern trail</h2>
          </header>

          <div class="button-glance__actions">
            <c-CButton intent="primary">
              <c-fill name="start">
                <span aria-hidden="true">✦</span>
              </c-fill>
              <c-fill name="default">
                Begin trail
              </c-fill>
            </c-CButton>
            <c-CButton variant="outline" intent="success">
              Log wildflower
            </c-CButton>
            <c-CButton variant="ghost" intent="neutral">
              Open field guide
            </c-CButton>
          </div>
        </article>

        <article class="button-glance__card">
          <header>
            <p>Trail conditions</p>
            <h2>Before you set out</h2>
          </header>

          <div class="button-glance__actions">
            <c-CButton loading intent="warn">
              Checking weather
            </c-CButton>
            <c-CButton disabled variant="outline" intent="neutral">
              North path closed
            </c-CButton>
          </div>
        </article>
      </section>
    """

    css = """
      :where(.button-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-glance__card) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid light-dark(#bbd6c5, #355e48);
        border-radius: 0.875rem;
        background: Canvas;
        box-shadow: 0 0.75rem 2rem rgb(15 23 42 / 10%);
      }

      :where(.button-glance__card header) {
        margin-block-end: 1rem;
      }

      :where(.button-glance__card h2, .button-glance__card p) {
        margin-block: 0;
      }

      :where(.button-glance__card header p) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-glance__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
    """


preview = ButtonAtAGlance()

preview  # noqa: B018
