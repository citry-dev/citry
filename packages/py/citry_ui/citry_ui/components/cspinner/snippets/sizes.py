import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CRow class_="spinner-sizes" gap="lg" align="center">
        <c-for each="size in sizes">
          <c-CCol align="center" gap="xs">
            <c-CSpinner c-label="f'{size} star-map load'" c-size="size" />
            <span>{{ size }}</span>
          </c-CCol>
        </c-for>
      </c-CRow>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"sizes": ("sm", "md", "lg")}

    css = """
      :where(.spinner-sizes) {
        min-block-size: 4rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-sizes span) {
        font-size: 0.72rem;
      }
    """


preview = SpinnerSizes()

preview  # noqa: B018
