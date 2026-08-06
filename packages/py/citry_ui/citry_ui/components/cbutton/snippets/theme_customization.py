import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ButtonThemeCustomization(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="button-theme">
        <article class="button-theme__card button-theme__card--day">
          <header>
            <p>Day garden</p>
            <h2>Herbarium walk</h2>
          </header>
          <c-CButton>
            Follow sunlit path
          </c-CButton>
          <c-CButton variant="outline" c-attrs="rounded_attrs">
            Open plant index
          </c-CButton>
        </article>

        <article class="button-theme__card button-theme__card--night">
          <header>
            <p>Night garden</p>
            <h2>After-dark blooms</h2>
          </header>
          <c-CButton>
            Watch moonflowers
          </c-CButton>
          <c-CButton variant="outline">
            Find fireflies
          </c-CButton>
        </article>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "rounded_attrs": {
                "style": "--cui-button-radius: 999px;",
            }
        }

    css = """
      :where(.button-theme) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 64rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.button-theme__card) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid;
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.button-theme__card header) {
        flex-basis: 100%;
        margin-block-end: 0.25rem;
      }

      :where(.button-theme__card h2, .button-theme__card p) {
        margin-block: 0;
      }

      :where(.button-theme__card header p) {
        margin-block-end: 0.35rem;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.button-theme__card--day) {
        --cui-button-background: #166534;
        --cui-button-foreground: #ffffff;
        --cui-button-border-color: #166534;
        --cui-button-hover-background: #14532d;
        --cui-button-active-background: #052e16;
        --cui-button-focus-color: #7c3aed;
        color-scheme: light;
        border-color: #bbd6c5;
      }

      :where(.button-theme__card--day header p) {
        color: #166534;
      }

      :where(.button-theme__card--night) {
        --cui-button-background: #a7f3d0;
        --cui-button-foreground: #052e16;
        --cui-button-border-color: #6ee7b7;
        --cui-button-hover-background: #6ee7b7;
        --cui-button-active-background: #34d399;
        --cui-button-focus-color: #f0abfc;
        color-scheme: dark;
        border-color: #355e48;
      }

      :where(.button-theme__card--night header p) {
        color: #6ee7b7;
      }

      :where(.button-theme__card--night [data-citry-ui-part="content"]) {
        letter-spacing: 0.025em;
      }
    """


preview = ButtonThemeCustomization()

preview  # noqa: B018
