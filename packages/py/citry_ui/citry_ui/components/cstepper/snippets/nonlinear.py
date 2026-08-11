import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NonlinearStepper(Component):
    template = """
      <section x-data="{ active: 0 }">
        <c-CStepper
          label="Profile sections"
          interactive
          c-linear="False"
          $c-props="{ active, onActiveChange: (next) => active = next }"
        >
          <c-CStep>Identity</c-CStep>
          <c-CStep>Preferences</c-CStep>
          <c-CStep>Notifications</c-CStep>
        </c-CStepper>
      </section>
    """


preview = NonlinearStepper()
preview  # noqa: B018
