import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class AlertIntents(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="alert-intents" aria-label="Alert intents">
        <c-for each="item in alerts">
          <c-CAlert c-intent="item[0]">
            <c-fill name="title">{{ item[1] }}</c-fill>
            <c-fill name="default">{{ item[2] }}</c-fill>
          </c-CAlert>
        </c-for>
      </section>
    """

    def template_data(
        self,
        kwargs: Kwargs,  # noqa: ARG002
        slots: Slots,  # noqa: ARG002
    ) -> dict[str, object]:
        return {
            "alerts": (
                ("info", "Night plan ready", "Six targets fit the darkness window."),
                ("success", "Guide star acquired", "Tracking has settled on Vega."),
                ("warn", "Humidity rising", "Review the dome limit before continuing."),
                ("error", "Dome drive stopped", "Close the shutter manually."),
            )
        }

    css = """
      :where(.alert-intents) {
        display: grid;
        gap: 0.75rem;
        max-width: 52rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = AlertIntents()

preview  # noqa: B018
