import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="alert-sizes" aria-label="Alert sizes">
        <c-for each="size in sizes">
          <c-CAlert c-size="size[0]">
            <c-fill name="title">{{ size[1] }} Alert</c-fill>
            <c-fill name="default">The northern camera is ready.</c-fill>
          </c-CAlert>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"sizes": (("sm", "Small"), ("md", "Medium"), ("lg", "Large"))}

    css = """
      :where(.alert-sizes) {
        display: grid;
        gap: 0.75rem;
        max-width: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertSizes()

preview  # noqa: B018
