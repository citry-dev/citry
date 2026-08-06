import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonSizesAndLayout(Component):
    template = """
      <section class="button-sizes">
        <div class="button-sizes__row">
          <c-CButton size="sm">
            Mark moss
          </c-CButton>
          <c-CButton size="md">
            Map meadow
          </c-CButton>
          <c-CButton size="lg">
            Explore canopy
          </c-CButton>
        </div>

        <article>
          <p>Field kit for a narrow trail</p>
          <c-CButton block variant="outline">
            Record the flowering plants along this shaded riverbank
          </c-CButton>
        </article>
      </section>
    """

    css = """
      :where(.button-sizes) {
        display: grid;
        gap: 1rem;
        max-width: 54rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-sizes__row) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-sizes article) {
        display: grid;
        gap: 0.75rem;
        inline-size: min(100%, 24rem);
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-sizes article p) {
        margin-block: 0;
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }
    """


preview = ButtonSizesAndLayout()

preview  # noqa: B018
