import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ChoiceSemantics(Component):
    template = """
      <c-CCol>
        <c-CSwitch checked>
          <c-fill name="default">Automatic hallway lighting</c-fill>
          <c-fill name="description">Takes effect immediately.</c-fill>
        </c-CSwitch>
        <c-CCheckbox>
          <c-fill name="default">Include spare keys in the move checklist</c-fill>
          <c-fill name="description">A selection, not an immediate setting.</c-fill>
        </c-CCheckbox>
      </c-CCol>
    """


preview = ChoiceSemantics()

preview  # noqa: B018
