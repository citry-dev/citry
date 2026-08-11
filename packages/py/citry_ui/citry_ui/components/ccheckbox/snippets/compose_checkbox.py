from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CCheckbox

citry.register_library(citry_ui)


class ComposeCheckbox(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "python_checkbox": CCheckbox(
                name="archive",
                value="photographs",
                variant="outline",
                slots={"default": "Archive specimen photographs"},
            )
        }

    template = """
      <section class="checkbox-compose" aria-label="Checkbox authoring forms">
        <div>
          <p class="checkbox-compose__eyebrow">Template</p>
          <c-CCheckbox name="archive" value="notes" checked>
            Archive handwritten field notes
          </c-CCheckbox>
        </div>
        <div>
          <p class="checkbox-compose__eyebrow">Python composition</p>
          {{ python_checkbox }}
        </div>
      </section>
    """

    css = """
      :where(.checkbox-compose) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1rem;
        max-width: 46rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.checkbox-compose > div) {
        display: grid;
        gap: 0.75rem;
        padding: 1rem;
        border: 1px solid light-dark(#c8d8c3, #3d5540);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.checkbox-compose__eyebrow) {
        margin: 0;
        color: light-dark(#38714a, #86c999);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
      }
    """


preview = ComposeCheckbox()

preview  # noqa: B018
