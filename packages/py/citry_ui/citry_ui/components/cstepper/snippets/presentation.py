import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StepperPresentation(Component):
    template = """
      <c-CStack>
        <c-CStepper label="Small plain" size="sm">
          <c-CStep>Start</c-CStep><c-CStep>Finish</c-CStep>
        </c-CStepper>
        <c-CStepper label="Medium soft" variant="soft" c-active="1">
          <c-CStep>Start</c-CStep><c-CStep>Finish</c-CStep>
        </c-CStepper>
        <c-CStepper label="Large vertical outline" orientation="vertical" variant="outline" size="lg">
          <c-CStep>Start</c-CStep><c-CStep>Finish</c-CStep>
        </c-CStepper>
      </c-CStack>
    """


preview = StepperPresentation()
preview  # noqa: B018
