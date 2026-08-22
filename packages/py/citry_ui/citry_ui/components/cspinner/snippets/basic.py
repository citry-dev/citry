import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicSpinners(Component):
    template = """
      <c-CRow class_="spinner-basic" gap="lg">
        <c-CSpinner label="Loading lunar atlas" />
        <c-CSpinner label="Aligning telescope mount" intent="success" />
        <c-CSpinner label="Reconnecting weather station" intent="warn" />
      </c-CRow>
    """
    css = """
      :where(.spinner-basic) {
        padding: 1.25rem;
        color: CanvasText;
      }
    """


preview = BasicSpinners()

preview  # noqa: B018
