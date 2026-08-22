import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StackSpacing(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="flow-spacing" aria-label="Col gap presets">
        <c-for each="gap in gaps">
          <c-CCol c-gap="gap" class_="flow-spacing__stack">
            <strong>{{ gap }}</strong>
            <span>Clay body</span>
            <span>Glaze test</span>
          </c-CCol>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"gaps": ("0", "xs", "sm", "md", "lg", "xl")}

    css = """
      :where(.flow-spacing) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
        gap: 1rem;
        max-inline-size: 62rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.flow-spacing__stack) {
        padding: 0.85rem;
        border: 1px solid light-dark(#d9c8b2, #62564b);
        border-radius: 0.65rem;
        background: light-dark(#fffaf2, #251f1a);
      }

      :where(.flow-spacing__stack span) {
        padding: 0.35rem;
        border-radius: 0.3rem;
        background: light-dark(#ead8bd, #493b30);
        font-size: 0.8rem;
      }
    """


preview = StackSpacing()

preview  # noqa: B018
