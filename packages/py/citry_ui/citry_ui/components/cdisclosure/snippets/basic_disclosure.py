import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class BasicDisclosure(Component):
    template = """
      <c-CCol gap="md">
        <c-CDisclosure open heading_level="2" region>
          <c-fill name="title">Install prerequisites</c-fill>
          <c-fill name="default">
            Install Python, create a virtual environment, then add Citry.
          </c-fill>
        </c-CDisclosure>
        <c-CDisclosure>
          <c-fill name="title">Optional database tools</c-fill>
          <c-fill name="default">
            Add the PostgreSQL client only when the application uses it.
          </c-fill>
        </c-CDisclosure>
      </c-CCol>
    """


preview = BasicDisclosure()
preview  # noqa: B018
