import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonDecorations(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="button-decorations">
        <article>
          <h2>Logical start and end</h2>
          <div class="button-decorations__actions">
            <c-CButton variant="outline">
              <c-fill name="start">
                <span aria-hidden="true">✿</span>
              </c-fill>
              <c-fill name="default">
                Identify bloom
              </c-fill>
            </c-CButton>
            <c-CButton variant="outline">
              <c-fill name="default">
                Continue upstream
              </c-fill>
              <c-fill name="end">
                <span aria-hidden="true">→</span>
              </c-fill>
            </c-CButton>
            <c-CButton>
              <c-fill name="start">
                <span aria-hidden="true">+</span>
              </c-fill>
              <c-fill name="default">
                Add sighting
              </c-fill>
              <c-fill name="end">
                <span aria-hidden="true">✓</span>
              </c-fill>
            </c-CButton>
          </div>
        </article>

        <article dir="rtl">
          <h2>Right-to-left flow</h2>
          <c-CButton variant="outline">
            <c-fill name="start">
              <span aria-hidden="true">✿</span>
            </c-fill>
            <c-fill name="default">
              فحص الزهرة
            </c-fill>
            <c-fill name="end">
              <span aria-hidden="true">←</span>
            </c-fill>
          </c-CButton>
        </article>

        <article class="button-decorations__icon-only">
          <h2>Icon-only content</h2>
          <p>The accessible name comes from <code>aria-label</code>.</p>
          <c-CButton c-attrs="icon_attrs" variant="outline">
            <span aria-hidden="true">★</span>
          </c-CButton>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"icon_attrs": {"aria-label": "Mark specimen as notable"}}

    css = """
      :where(.button-decorations) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-decorations article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#d5ddd8, #40594b);
        border-radius: 0.75rem;
        background: Canvas;
      }

      :where(.button-decorations h2, .button-decorations p) {
        margin-block: 0;
      }

      :where(.button-decorations p) {
        color: color-mix(in srgb, currentColor 68%, transparent);
        font-size: 0.8125rem;
      }

      :where(
        .button-decorations__icon-only > [data-citry-ui-part="button"]
      ) {
        justify-self: start;
      }

      :where(.button-decorations__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.button-decorations article[dir="rtl"] [data-citry-ui-part="button"]) {
        justify-self: start;
      }
    """


preview = ButtonDecorations()

preview  # noqa: B018
