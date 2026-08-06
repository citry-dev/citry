import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonBasicActions(Component):
    template = """
      <section class="button-basic">
        <div>
          <p class="button-basic__eyebrow">Fern collection</p>
          <h2>One native action, optional decoration</h2>
        </div>

        <div class="button-basic__actions">
          <c-CButton>
            Record specimen
          </c-CButton>
          <c-CButton variant="outline">
            <c-fill name="start">
              <span aria-hidden="true">+</span>
            </c-fill>
            <c-fill name="default">
              Add observation
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">→</span>
            </c-fill>
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.button-basic) {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 1rem;
        align-items: center;
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#cbd5d0, #40594b);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-basic h2, .button-basic p) {
        margin-block: 0;
      }

      :where(.button-basic__eyebrow) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-basic__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ButtonBasicActions()

preview  # noqa: B018
