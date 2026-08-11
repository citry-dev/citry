import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedDisclosure(Component):
    template = """
      <section class="disclosure-brands">
        <div class="disclosure-brand disclosure-brand--orchard">
          <c-CDisclosure open indicator_pos="start">
            <c-fill name="title">Orchard operations and seasonal irrigation planning</c-fill>
            <c-fill name="default">Warm surfaces for the harvest handbook.</c-fill>
          </c-CDisclosure>
        </div>
        <div class="disclosure-brand disclosure-brand--harbor" dir="rtl" style="color-scheme:dark">
          <c-CDisclosure variant="soft">
            <c-fill name="title">Harbor operations</c-fill>
            <c-fill name="default">A cool scheme with logical indicator placement.</c-fill>
          </c-CDisclosure>
        </div>
      </section>
    """

    css = """
      :where(.disclosure-brands) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
      }
      :where(.disclosure-brand) { padding: 1rem; border-radius: 1rem; }
      :where(.disclosure-brand--orchard) {
        color-scheme: light dark;
        --cui-disclosure-background: light-dark(#fff7ed, #2b170b);
        --cui-disclosure-foreground: light-dark(#431407, #ffedd5);
        --cui-disclosure-trigger-open-color: light-dark(#9a3412, #fdba74);
      }
      :where(.disclosure-brand--harbor) {
        color-scheme: light dark;
        --cui-disclosure-background: light-dark(#ecfeff, #082f49);
        --cui-disclosure-foreground: light-dark(#164e63, #cffafe);
        --cui-disclosure-trigger-open-color: light-dark(#0369a1, #7dd3fc);
        --cui-disclosure-radius: 1.25rem;
      }
      :where(.disclosure-brand [data-citry-ui-part="disclosure-title"]) {
        letter-spacing: 0.01em;
      }
    """


preview = CustomizedDisclosure()
preview  # noqa: B018
