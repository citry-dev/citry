from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelectOption

citry.register_library(citry_ui)


class NativeSelectVariants(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "variants": ("outline", "filled", "plain"),
            "depths": [
                CNativeSelectOption("surface", "Surface"),
                CNativeSelectOption("twilight", "Twilight zone"),
                CNativeSelectOption("midnight", "Midnight zone"),
            ],
        }

    template = """
      <section class="ocean-variants">
        <c-for each="variant in variants">
          <c-CField>
            <c-fill name="label">{{ variant.title() }}</c-fill>
            <c-fill name="default">
              <c-CNativeSelect
                c-options="depths"
                c-variant="variant"
                value="twilight"
              />
            </c-fill>
          </c-CField>
        </c-for>
      </section>
    """

    css = """
      :where(.ocean-variants) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }
    """


preview = NativeSelectVariants()

preview  # noqa: B018
