import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="alert-variants" aria-label="Alert variants">
        <c-for each="variant in variants">
          <c-CAlert intent="warn" c-variant="variant[0]">
            <c-fill name="title">{{ variant[1] }} warning</c-fill>
            <c-fill name="default">
              High cirrus may reduce contrast on faint galaxies.
            </c-fill>
          </c-CAlert>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"variants": (("soft", "Soft"), ("solid", "Solid"), ("outline", "Outline"))}

    css = """
      :where(.alert-variants) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertVariants()

preview  # noqa: B018
