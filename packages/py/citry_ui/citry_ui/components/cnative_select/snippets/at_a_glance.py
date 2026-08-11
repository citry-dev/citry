from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectGroup, CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "habitats": [
                CNativeSelectGroup(
                    "Coastal",
                    [
                        CNativeSelectOption("kelp", "Kelp forest"),
                        CNativeSelectOption("reef", "Coral reef"),
                        CNativeSelectOption("mangrove", "Mangrove nursery"),
                    ],
                ),
                CNativeSelectGroup(
                    "Open ocean",
                    [
                        CNativeSelectOption("pelagic", "Pelagic zone"),
                        CNativeSelectOption("abyss", "Abyssal plain"),
                    ],
                ),
            ],
        }

    template = """
      <section class="ocean-glance" aria-label="Ocean habitat survey">
        <c-CField required>
          <c-fill name="label">Primary habitat</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="habitat"
              c-options="habitats"
              placeholder="Choose a habitat"
              value="reef"
            />
          </c-fill>
          <c-fill name="description">Choose the habitat represented by this dive.</c-fill>
        </c-CField>

        <div class="ocean-glance__deep" style="color-scheme: dark">
          <c-CField invalid>
            <c-fill name="label">Unverified station</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="habitats"
                placeholder="Choose a station type"
                variant="filled"
              />
            </c-fill>
            <c-fill name="error">Match this station to a surveyed habitat.</c-fill>
          </c-CField>
        </div>
      </section>
    """

    css = """
      :where(.ocean-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 54rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-glance > *) {
        padding: 1rem;
        border: 1px solid light-dark(#9ccbd3, #315f6a);
        border-radius: 0.875rem;
        background: light-dark(#f1fbfc, #10272d);
      }

      :where(.ocean-glance__deep) {
        --cui-native-select-background: #142f36;
        --cui-native-select-border-color: #57828c;
        --cui-native-select-focus-color: #7ddbea;
      }
    """


preview = NativeSelectAtAGlance()

preview  # noqa: B018
