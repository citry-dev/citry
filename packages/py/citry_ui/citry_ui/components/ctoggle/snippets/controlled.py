import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledToggle(Component):
    template = """
      <section x-data="{ view: 'sky' }">
        <p>Current view: <strong x-text="view"></strong></p>
        <c-CToggleGroup
          label="Observation view"
          value="sky"
          $c-props="{ value: view, onValueChange: (next) => view = next }"
        >
          <c-CToggle value="sky">Sky</c-CToggle>
          <c-CToggle value="spectrum">Spectrum</c-CToggle>
        </c-CToggleGroup>
      </section>
    """


preview = ControlledToggle()
preview  # noqa: B018
