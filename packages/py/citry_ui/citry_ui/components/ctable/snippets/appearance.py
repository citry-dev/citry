from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class TableAppearance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-appearance">
        <article>
          <h2>Line · comfortable</h2>
          <c-CTable c-columns="columns" c-rows="rows" />
        </article>
        <article>
          <h2>Outline · compact</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            variant="outline"
            density="compact"
            column_borders
          />
        </article>
        <article>
          <h2>Striped · default</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            density="default"
            striped
          />
        </article>
        <article>
          <h2>Hover · bottom caption</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            hover
            caption_side="bottom"
          >
            <c-fill name="caption">
              Hover highlights, but never selects, a row.
            </c-fill>
          </c-CTable>
        </article>
      </section>
    """

    css = """
      :where(.table-appearance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
        gap: 1rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-appearance article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#dbeafe, #1e3a8a);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.table-appearance h2) {
        margin: 0 0 0.75rem;
        font-size: 0.875rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("planet", "Planet", row_header=True),
                CTableColumn("gravity", "Gravity", align="end"),
            ),
            "rows": (
                CTableRow("mars", {"planet": "Mars", "gravity": "3.71 m/s²"}),
                CTableRow("neptune", {"planet": "Neptune", "gravity": "11.15 m/s²"}),
            ),
        }


preview = TableAppearance()

preview  # noqa: B018
