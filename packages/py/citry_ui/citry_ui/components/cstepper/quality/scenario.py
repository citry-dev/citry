"""Shared Stepper scenario used by repository quality tools."""

from __future__ import annotations

from citry import Citry, Component


def stepper_states_component(app: Citry) -> type[Component]:
    class CitryUiStepperStates(Component):
        citry = app
        template = """
          <section class="citry-ui-quality-stack" data-quality-stepper-ready>
            <h1>Stepper states</h1>
            <c-CStepper label="Static progress" c-active="1" variant="soft">
              <c-CStep>Profile</c-CStep><c-CStep>Security</c-CStep><c-CStep>Review</c-CStep>
            </c-CStepper>
            <c-CStepper label="Interactive non-linear" interactive c-linear="False" variant="outline">
              <c-CStep>Draft</c-CStep><c-CStep>Review</c-CStep><c-CStep error>Publish</c-CStep>
            </c-CStepper>
            <c-CStepper label="Vertical optional" orientation="vertical" size="lg" c-active="1">
              <c-CStep>Contact</c-CStep>
              <c-CStep optional>
                <c-fill name="default">Preferences</c-fill>
                <c-fill name="description">Optional step with a long explanatory description</c-fill>
              </c-CStep>
              <c-CStep>Finish</c-CStep>
            </c-CStepper>
            <fieldset disabled>
              <legend>Disabled workflow</legend>
              <c-CStepper label="Disabled workflow" interactive c-linear="False">
                <c-CStep>One</c-CStep><c-CStep>Two</c-CStep>
              </c-CStepper>
            </fieldset>
            <div dir="rtl">
              <c-CStepper label="مسار العمل" c-active="1" variant="outline">
                <c-CStep>البداية</c-CStep><c-CStep>المراجعة</c-CStep><c-CStep>النهاية</c-CStep>
              </c-CStepper>
            </div>
            <div style="color-scheme:dark; background:Canvas; color:CanvasText; padding:1rem">
              <c-CStepper label="Night workflow" c-active="1" variant="soft">
                <c-CStep>Collect</c-CStep><c-CStep>Compare</c-CStep><c-CStep>Decide</c-CStep>
              </c-CStepper>
            </div>
          </section>
        """

    return CitryUiStepperStates
