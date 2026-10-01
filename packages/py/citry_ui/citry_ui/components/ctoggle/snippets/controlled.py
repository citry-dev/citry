import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledToggle(Component):
    template = """
      <section >
        <p>Current view: <strong v-text="view"></strong></p>
        <c-CToggleGroup
          label="Observation view"
          value="sky"
          :value="view" :onValueChange="(next) => view = next"
        >
          <c-CToggle value="sky">Sky</c-CToggle>
          <c-CToggle value="spectrum">Spectrum</c-CToggle>
        </c-CToggleGroup>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            view: 'sky'
          };
        },
      });
    """


preview = ControlledToggle()
preview  # noqa: B018
