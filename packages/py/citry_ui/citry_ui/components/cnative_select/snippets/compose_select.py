from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CNativeSelect, CNativeSelectOption

citry.register_library(citry_ui)


class ComposeNativeSelect(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        options = [
            CNativeSelectOption("north", "North transect"),
            CNativeSelectOption("central", "Central transect"),
            CNativeSelectOption("south", "South transect"),
        ]
        return {
            "options": options,
            "python_select": CNativeSelect(
                options=options,
                id="python-transect",
                name="python_transect",
                value="central",
            ),
        }

    template = """
      <section class="ocean-compose">
        <c-CField>
          <c-fill name="label">Template-composed transect</c-fill>
          <c-fill name="default">
            <c-CNativeSelect
              name="template_transect"
              c-options="options"
              value="north"
            />
          </c-fill>
        </c-CField>

        <div>
          <label class="ocean-compose__label" for="python-transect">
            Python-composed transect
          </label>
          {{ python_select }}
        </div>
      </section>
    """

    css = """
      :where(.ocean-compose) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.ocean-compose__label) {
        display: block;
        margin-block-end: 0.5rem;
        font-weight: 650;
      }
    """


preview = ComposeNativeSelect()

preview  # noqa: B018
