import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TogglePresentation(Component):
    template = """
      <c-CCol gap="md">
        <c-for each="variant in variants">
          <c-CToggleGroup c-label="variant + ' display'" value="one" c-variant="variant">
            <c-CToggle value="one">One</c-CToggle>
            <c-CToggle value="two">Two</c-CToggle>
          </c-CToggleGroup>
        </c-for>
      </c-CCol>
    """

    def template_data(self, kwargs, slots):  # noqa: ANN001, ANN201, ARG002
        return {"variants": ("soft", "outline", "plain")}


preview = TogglePresentation()
preview  # noqa: B018
