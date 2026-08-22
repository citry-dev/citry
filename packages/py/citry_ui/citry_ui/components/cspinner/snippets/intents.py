import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class SpinnerIntents(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <c-CRow class_="spinner-intents" gap="lg" wrap>
        <c-for each="intent in intents">
          <c-CCol c-attrs="{'data-spinner-intent-example': intent}" align="center" gap="xs">
            <c-CSpinner c-label="f'{intent} observatory task'" c-intent="intent" />
            <span>{{ intent }}</span>
          </c-CCol>
        </c-for>
      </c-CRow>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {"intents": ("neutral", "primary", "success", "warn", "danger")}

    css = """
      :where(.spinner-intents) {
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.spinner-intents span) {
        font-size: 0.72rem;
      }
    """


preview = SpinnerIntents()

preview  # noqa: B018
