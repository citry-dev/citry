from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectPlaceholder(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "destinations": [
                CNativeSelectOption("lagoon", "Lagoon station"),
                CNativeSelectOption("shelf", "Shelf station"),
                CNativeSelectOption("slope", "Continental slope"),
            ],
        }

    template = """
      <c-CForm class_="ocean-placeholders">
        <c-CField required>
          <c-fill name="label">Required destination</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="required_destination"
              c-options="destinations"
              placeholder="Choose a destination"
            />
          </c-fill>
          <c-fill name="error">Choose a destination before departure.</c-fill>
        </c-CField>

        <c-CField>
          <c-fill name="label">Optional backup</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="backup_destination"
              c-options="destinations"
              placeholder="No backup destination"
            />
          </c-fill>
        </c-CField>

        <div class="ocean-placeholders__actions">
          <c-CButton type="submit">Validate route</c-CButton>
          <c-CButton type="reset" variant="outline">Reset</c-CButton>
        </div>
      </c-CForm>
    """

    css = """
      :where(.ocean-placeholders) {
        display: grid;
        gap: 1rem;
        max-width: 36rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-placeholders__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
      }
    """


preview = NativeSelectPlaceholder()

preview  # noqa: B018
