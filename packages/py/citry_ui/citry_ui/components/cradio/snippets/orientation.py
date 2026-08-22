import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class RadioOrientation(Component):
    template = """
      <c-CCol gap="xl">
        <c-CRadioGroup name="season-vertical" value="spring">
          <c-fill name="label">Vertical</c-fill>
          <c-fill name="default">
            <c-CRadio value="spring">Spring</c-CRadio>
            <c-CRadio value="autumn">Autumn</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
        <c-CRadioGroup name="season-horizontal" value="spring" orientation="horizontal">
          <c-fill name="label">Horizontal</c-fill>
          <c-fill name="default">
            <c-CRadio value="spring">Spring</c-CRadio>
            <c-CRadio value="autumn">Autumn</c-CRadio>
          </c-fill>
        </c-CRadioGroup>
      </c-CCol>
    """


preview = RadioOrientation()

preview  # noqa: B018
