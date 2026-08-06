from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class TableAtAGlance(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-glance">
        <article>
          <h2>Inner planets</h2>
          <c-CTable
            c-columns="columns"
            c-rows="inner_rows"
            density="compact"
            striped
          >
            <c-fill name="caption">
              Distance from the Sun
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Outer planets</h2>
          <c-CTable
            c-columns="columns"
            c-rows="outer_rows"
            variant="outline"
            density="compact"
            hover
          >
            <c-fill name="caption">
              Distance from the Sun
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Survey pending</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            state="loading"
            density="compact"
            loading_label="Loading orbital survey..."
          />
        </article>
        <article>
          <h2>No matching worlds</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            variant="outline"
            density="compact"
            empty_label="No planets match this orbit."
          />
        </article>
      </section>
    """

    css = """
      :where(.table-glance) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 20rem), 1fr));
        gap: 1rem;
        max-width: 72rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-glance article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#bfdbfe, #1e3a8a);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.table-glance h2) {
        margin: 0 0 0.75rem;
        color: light-dark(#1d4ed8, #93c5fd);
        font-size: 1rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("planet", "Planet", row_header=True),
                CTableColumn("distance", "Mean distance", align="end"),
            ),
            "inner_rows": (
                CTableRow("mercury", {"planet": "Mercury", "distance": "57.9 million km"}),
                CTableRow("venus", {"planet": "Venus", "distance": "108.2 million km"}),
                CTableRow("earth", {"planet": "Earth", "distance": "149.6 million km"}),
            ),
            "outer_rows": (
                CTableRow("jupiter", {"planet": "Jupiter", "distance": "778.5 million km"}),
                CTableRow("saturn", {"planet": "Saturn", "distance": "1.43 billion km"}),
                CTableRow("uranus", {"planet": "Uranus", "distance": "2.87 billion km"}),
            ),
        }


preview = TableAtAGlance()

preview  # noqa: B018
