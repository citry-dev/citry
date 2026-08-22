import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ProgressIntents(Component):
    template = """
      <c-CCol class_="progress-intents" gap="sm">
        <c-for each="item in items">
          <div><span>{{ item[1] }}</span><c-CProgress c-label="item[1]" c-value="62" c-intent="item[0]" /></div>
        </c-for>
      </c-CCol>
    """

    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "items": (
                ("neutral", "Equipment check"),
                ("primary", "Survey pass"),
                ("success", "Samples secured"),
                ("warn", "Current increasing"),
                ("danger", "Pressure limit"),
            )
        }

    css = """
      :where(.progress-intents) {
        max-inline-size: 32rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-intents > div) {
        display: grid;
        gap: 0.3rem;
      }

      :where(.progress-intents span) {
        font-size: 0.8rem;
      }
    """


preview = ProgressIntents()

preview  # noqa: B018
