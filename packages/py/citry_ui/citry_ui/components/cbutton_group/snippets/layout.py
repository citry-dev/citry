import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Layout(Component):
    template = """
      <c-CStack gap="lg">
        <c-CButtonGroup label="Time range" c-grow="True">
          <c-CButton variant="outline">Night</c-CButton>
          <c-CButton variant="outline">Week</c-CButton>
          <c-CButton variant="outline">Month</c-CButton>
        </c-CButtonGroup>
        <c-CButtonGroup label="Export format" orientation="vertical">
          <c-CButton variant="outline">Star chart</c-CButton>
          <c-CButton variant="outline">Observation log</c-CButton>
        </c-CButtonGroup>
      </c-CStack>
    """


preview = Layout()
preview  # noqa: B018
