import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicAlerts(Component):
    template = """
      <section class="basic-alerts" aria-label="Basic Alert anatomy">
        <c-CAlert>
          Comet viewing begins at 22:40.
        </c-CAlert>
        <c-CAlert intent="success">
          <c-fill name="title">Calibration complete</c-fill>
          <c-fill name="default">
            The spectrograph is ready for the first target.
          </c-fill>
        </c-CAlert>
      </section>
    """

    css = """
      :where(.basic-alerts) {
        display: grid;
        gap: 0.875rem;
        max-width: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = BasicAlerts()

preview  # noqa: B018
