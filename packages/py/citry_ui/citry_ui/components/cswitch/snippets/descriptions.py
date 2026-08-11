import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DescribedSwitches(Component):
    template = """
      <c-CStack>
        <c-CSwitch checked>
          <c-fill name="default">Air purifier</c-fill>
          <c-fill name="description">Runs quietly until the room reaches clean-air target.</c-fill>
        </c-CSwitch>
        <c-CSwitch disabled>
          <c-fill name="default">Fireplace fan</c-fill>
          <c-fill name="description">Available while the fireplace is warm.</c-fill>
        </c-CSwitch>
      </c-CStack>
    """


preview = DescribedSwitches()

preview  # noqa: B018
