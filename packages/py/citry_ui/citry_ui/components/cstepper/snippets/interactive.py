import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class InteractiveStepper(Component):
    template = """
      <section >
        <c-CStepper
          label="Publication workflow"
          c-active="1"
          interactive
          :active="active" :onActiveChange="(next) => active = next"
        >
          <c-CStep>Draft</c-CStep>
          <c-CStep>Review</c-CStep>
          <c-CStep>Publish</c-CStep>
        </c-CStepper>
        <p>Current zero-based index: <strong v-text="active"></strong></p>
      </section>
    """
    js = """
      $component({
        data() {
          return {
            active: 1
          };
        },
      });
    """


preview = InteractiveStepper()
preview  # noqa: B018
