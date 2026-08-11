import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InteractiveStepper(Component):
    template = """
      <section x-data="{ active: 1 }">
        <c-CStepper
          label="Publication workflow"
          c-active="1"
          interactive
          $c-props="{ active, onActiveChange: (next) => active = next }"
        >
          <c-CStep>Draft</c-CStep>
          <c-CStep>Review</c-CStep>
          <c-CStep>Publish</c-CStep>
        </c-CStepper>
        <p>Current zero-based index: <strong x-text="active"></strong></p>
      </section>
    """


preview = InteractiveStepper()
preview  # noqa: B018
