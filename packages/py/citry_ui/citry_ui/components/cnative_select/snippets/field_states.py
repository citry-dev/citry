from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "stations": [
                CNativeSelectOption("alpha", "Station Alpha"),
                CNativeSelectOption("beta", "Station Beta"),
                CNativeSelectOption("gamma", "Station Gamma"),
            ],
        }

    template = """
      <section class="ocean-states">
        <c-CField required>
          <c-fill name="label">Required station</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="station"
              c-options="stations"
              placeholder="Choose a station"
            />
          </c-fill>
        </c-CField>
        <c-CField disabled>
          <c-fill name="label">Closed station</c-fill>
          <c-fill name="default">
            <c-CNativeSelect c-options="stations" value="beta" />
          </c-fill>
        </c-CField>
        <c-CField invalid>
          <c-fill name="label">Unverified station</c-fill>
          <c-fill name="default">
            <c-CNativeSelect c-options="stations" value="gamma" />
          </c-fill>
          <c-fill name="error">Confirm the station with bridge control.</c-fill>
        </c-CField>
        <c-CForm disabled>
          <c-CField>
            <c-fill name="label">Survey locked by Form</c-fill>
            <c-fill name="default">
              <c-CNativeSelect c-options="stations" value="alpha" />
            </c-fill>
          </c-CField>
        </c-CForm>
      </section>
    """

    css = """
      :where(.ocean-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectStates()

preview  # noqa: B018
