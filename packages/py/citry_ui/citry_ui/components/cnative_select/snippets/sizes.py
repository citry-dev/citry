from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectSizes(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "sizes": ("sm", "md", "lg"),
            "vessels": [
                CNativeSelectOption("tern", "Tern"),
                CNativeSelectOption("albatross", "Albatross"),
                CNativeSelectOption(
                    "bathyscaphe",
                    "Bathyscaphe for the long continental-slope transect",
                ),
            ],
        }

    template = """
      <section class="ocean-sizes">
        <c-for each="size in sizes">
          <c-CField>
            <c-fill name="label">{{ size.upper() }} vessel control</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="vessels"
                c-size="size"
                value="bathyscaphe"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.ocean-sizes) {
        display: grid;
        gap: 1rem;
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectSizes()

preview  # noqa: B018
