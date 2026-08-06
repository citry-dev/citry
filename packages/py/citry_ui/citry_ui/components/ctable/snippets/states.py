from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn

citry.register_library(citry_ui)


class TableStates(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-states">
        <article>
          <h2>Loading</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            state="loading"
            loading_label="Receiving deep-space survey..."
          >
            <c-fill name="loading">
              Receiving deep-space survey...
            </c-fill>
          </c-CTable>
        </article>
        <article>
          <h2>Empty</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            empty_label="No signals match this wavelength."
          />
        </article>
        <article>
          <h2>Error</h2>
          <c-CTable
            c-columns="columns"
            c-rows="()"
            state="error"
            error_label="The telescope feed is unavailable."
          />
        </article>
      </section>
    """

    css = """
      :where(.table-states) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        max-width: 68rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-states article) {
        min-width: 0;
        padding: 1rem;
        border: 1px solid light-dark(#c7d2fe, #3730a3);
        border-radius: 0.875rem;
        background: Canvas;
      }

      :where(.table-states h2) {
        margin: 0 0 0.75rem;
        font-size: 0.875rem;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("signal", "Signal", row_header=True),
                CTableColumn("strength", "Strength", align="end"),
            ),
        }


preview = TableStates()

preview  # noqa: B018
