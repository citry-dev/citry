import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class CustomizedStepper(Component):
    css = """
      .orchid-stepper {
        --cui-stepper-active-color: #7f56d9;
        --cui-stepper-complete-color: #039855;
        --cui-stepper-radius: 1.25rem;
      }
      .orchid-stepper [data-citry-ui-part="label"] { letter-spacing: 0.02em; }
    """
    template = """
      <c-CStepper label="Orchid order" c-active="1" variant="outline" class_="orchid-stepper">
        <c-CStep>Choose</c-CStep><c-CStep>Prepare</c-CStep><c-CStep>Deliver</c-CStep>
      </c-CStepper>
    """


preview = CustomizedStepper()
preview  # noqa: B018
