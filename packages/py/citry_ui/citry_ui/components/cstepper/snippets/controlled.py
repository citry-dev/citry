import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class ControlledStepper(Component):
    template = """
      <section x-data="{ active: 0 }">
        <c-CStepper
          label="Workspace setup"
          interactive
          c-linear="False"
          $c-props="{ active, onActiveChange: (next) => active = next }"
        >
          <c-CStep>Workspace</c-CStep>
          <c-CStep>Members</c-CStep>
          <c-CStep>Permissions</c-CStep>
        </c-CStepper>
        <c-CGroup>
          <c-CButton @click="active = Math.max(0, active - 1)">Previous</c-CButton>
          <c-CButton @click="active = Math.min(2, active + 1)">Next</c-CButton>
        </c-CGroup>
      </section>
    """


preview = ControlledStepper()
preview  # noqa: B018
