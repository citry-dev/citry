import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonVariants(Component):
    template = """
      <section class="button-variants">
        <article>
          <h2>Solid</h2>
          <p>Primary action in the current view.</p>
          <c-CButton variant="solid">
            Begin trail
          </c-CButton>
        </article>
        <article>
          <h2>Outline</h2>
          <p>Visible alternative with less emphasis.</p>
          <c-CButton variant="outline">
            Compare tracks
          </c-CButton>
        </article>
        <article>
          <h2>Ghost</h2>
          <p>Quiet action near stronger controls.</p>
          <c-CButton variant="ghost">
            Read field notes
          </c-CButton>
        </article>
      </section>
    """

    css = """
      :where(.button-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-variants article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-width: 0;
        padding: 1.1rem;
        border: 1px solid light-dark(#cbd5d0, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-variants h2, .button-variants p) {
        margin-block: 0;
      }

      :where(.button-variants p) {
        color: color-mix(in srgb, currentColor 68%, transparent);
      }

      :where(.button-variants [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview = ButtonVariants()

preview  # noqa: B018
