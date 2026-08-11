import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class Attachment(Component):
    template = """
      <c-CStack gap="md">
        <c-CButtonGroup label="Attached view controls">
          <c-CButton variant="outline">Map</c-CButton>
          <c-CButton variant="outline">Sky</c-CButton>
        </c-CButtonGroup>
        <c-CButtonGroup label="Spaced view controls" c-attached="False">
          <c-CButton variant="outline">Map</c-CButton>
          <c-CButton variant="outline">Sky</c-CButton>
        </c-CButtonGroup>
      </c-CStack>
    """


preview = Attachment()
preview  # noqa: B018
