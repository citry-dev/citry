import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonNavigation(Component):
    template = """
      <section class="button-navigation">
        <div>
          <p class="button-navigation__eyebrow">Trail library</p>
          <h2>Use link semantics for navigation</h2>
        </div>

        <div class="button-navigation__actions">
          <c-CButton href="https://example.com/field-guide/ferns/">
            Read the fern guide
          </c-CButton>
          <c-CButton
            href="https://example.com/herbarium"
            variant="outline"
            c-attrs="{'target': '_blank', 'rel': 'noreferrer'}"
          >
            <c-fill name="default">
              Visit the herbarium
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">↗</span>
            </c-fill>
          </c-CButton>
        </div>
      </section>
    """

    css = """
      :where(.button-navigation) {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        max-width: 58rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#cbd5d0, #40594b);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-navigation h2, .button-navigation p) {
        margin-block: 0;
      }

      :where(.button-navigation__eyebrow) {
        margin-block-end: 0.35rem;
        color: light-dark(#19704a, #74d9a3);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-navigation__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = ButtonNavigation()

preview  # noqa: B018
