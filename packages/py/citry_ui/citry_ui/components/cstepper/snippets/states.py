import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class StepperStates(Component):
    template = """
      <c-CStepper label="Checkout" c-active="1" orientation="vertical" variant="outline">
        <c-CStep>
          <c-fill name="default">Delivery address</c-fill>
          <c-fill name="description">Saved</c-fill>
        </c-CStep>
        <c-CStep error>
          <c-fill name="default">Payment</c-fill>
          <c-fill name="description">Check the card number</c-fill>
        </c-CStep>
        <c-CStep optional>
          <c-fill name="default">Gift message</c-fill>
          <c-fill name="description">Optional</c-fill>
        </c-CStep>
      </c-CStepper>
    """


preview = StepperStates()
preview  # noqa: B018
