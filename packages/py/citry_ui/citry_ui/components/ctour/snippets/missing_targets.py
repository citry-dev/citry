import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TourMissingTargets(Component):
    template = """
      <c-CTour missing_target="skip">
        <c-fill name="activator" data="{ activator_attrs }">
          <c-CButton c-attrs="activator_attrs">Show conditional tour</c-CButton>
        </c-fill>
        <c-fill name="default">
          <c-CTourStep value="intro">
            <c-fill name="title">Conditional features</c-fill>
            <c-fill name="default">Unavailable targeted steps are skipped.</c-fill>
          </c-CTourStep>
          <c-CTourStep value="optional" target_id="feature-not-rendered">
            <c-fill name="title">Optional feature</c-fill>
            <c-fill name="default">This step is skipped because its target is absent.</c-fill>
          </c-CTourStep>
          <c-CTourStep value="summary">
            <c-fill name="title">Summary</c-fill>
            <c-fill name="default">The next available centered step remains usable.</c-fill>
          </c-CTourStep>
        </c-fill>
      </c-CTour>
    """


preview = TourMissingTargets()
preview  # noqa: B018
