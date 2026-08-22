import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DeterminateProgress(Component):
    template = """
      <c-CCol class_="progress-values">
        <div>
          <c-CRow justify="between"><span>Preparing vessel</span><strong>15%</strong></c-CRow>
          <c-CProgress label="Preparing vessel" c-value="15" />
        </div>
        <div>
          <c-CRow justify="between"><span>Descending</span><strong>50%</strong></c-CRow>
          <c-CProgress label="Descending" c-value="50" />
        </div>
        <div>
          <c-CRow justify="between"><span>Survey complete</span><strong>100%</strong></c-CRow>
          <c-CProgress label="Survey complete" c-value="100" intent="success" />
        </div>
      </c-CCol>
    """
    css = """
      :where(.progress-values) {
        max-inline-size: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.progress-values > div) {
        display: grid;
        gap: 0.4rem;
      }
    """


preview = DeterminateProgress()

preview  # noqa: B018
