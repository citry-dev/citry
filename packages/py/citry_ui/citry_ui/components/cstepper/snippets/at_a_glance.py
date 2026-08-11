import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StepperAtAGlance(Component):
    template = """
      <c-CStepper label="Account setup" c-active="1" variant="soft">
        <c-CStep>Profile</c-CStep>
        <c-CStep>Security</c-CStep>
        <c-CStep>Review</c-CStep>
      </c-CStepper>
    """


preview = StepperAtAGlance()
preview  # noqa: B018
