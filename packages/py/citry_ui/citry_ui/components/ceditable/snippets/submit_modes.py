import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class EditableSubmitModes(Component):
    template = """
      <c-CStack>
        <c-CEditable value="Enter or blur" submit_mode="both" c-input_attrs="{'aria-label':'Both'}" />
        <c-CEditable value="Enter only" submit_mode="enter" c-input_attrs="{'aria-label':'Enter only'}" />
        <c-CEditable value="Blur only" submit_mode="blur" c-input_attrs="{'aria-label':'Blur only'}" />
        <c-CEditable value="Buttons only" submit_mode="explicit" c-input_attrs="{'aria-label':'Explicit'}" />
      </c-CStack>
    """


preview = EditableSubmitModes()
preview  # noqa: B018
