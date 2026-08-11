from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectGroup, CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectOptions(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "regions": [
                CNativeSelectOption("harbor", "Research harbor"),
                CNativeSelectGroup(
                    "Continental shelf",
                    [
                        CNativeSelectOption("bank", "Emerald Bank"),
                        CNativeSelectOption("canyon", "Bluefin Canyon"),
                        CNativeSelectOption("closure", "Seasonal closure", disabled=True),
                    ],
                ),
                CNativeSelectGroup(
                    "Weather hold",
                    [CNativeSelectOption("offshore", "Offshore station")],
                    disabled=True,
                ),
            ],
        }

    template = """
      <section class="ocean-options">
        <c-CField>
          <c-fill name="label">Expedition region</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="region"
              c-options="regions"
              value="bank"
            />
          </c-fill>
          <c-fill name="description">Closed choices remain visible but unavailable.</c-fill>
        </c-CField>
      </section>
    """

    css = """
      :where(.ocean-options) {
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectOptions()

preview  # noqa: B018
