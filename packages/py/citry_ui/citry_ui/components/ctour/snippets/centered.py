import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourCentered(Component):
    template = """
      <div class="tour-centered-preview">
        <c-CTour size="sm">
          <c-fill name="activator" data="{ activator_attrs }">
            <c-CButton c-attrs="activator_attrs">Open introduction</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CTourStep value="intro" c-describe="True">
              <c-fill name="title">A focused introduction</c-fill>
              <c-fill name="default">Centered steps do not require a page target.</c-fill>
            </c-CTourStep>
            <c-CTourStep value="finish">
              <c-fill name="title">You are ready</c-fill>
              <c-fill name="default">Finish closes the Tour and restores focus.</c-fill>
            </c-CTourStep>
          </c-fill>
        </c-CTour>
      </div>
    """
    css = ":where(.tour-centered-preview) { min-block-size: 22rem; }"


preview = TourCentered()
preview  # noqa: B018
