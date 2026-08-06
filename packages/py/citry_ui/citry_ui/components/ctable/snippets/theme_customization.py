from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class ObservatoryTables(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="observatory-tables">
        <article class="observatory-tables__night">
          <h2>Night observation</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            variant="outline"
            striped
          >
            <c-fill name="caption">
              Winter sky
            </c-fill>
          </c-CTable>
        </article>
        <article class="observatory-tables__day">
          <h2>Solar observation</h2>
          <c-CTable
            c-columns="columns"
            c-rows="rows"
            variant="outline"
            style="--cui-table-header-background: light-dark(#fef3c7, #78350f)"
          >
            <c-fill name="caption">
              Daylight calibration
            </c-fill>
          </c-CTable>
        </article>
      </section>
    """

    css = """
      :where(.observatory-tables) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
        gap: 1rem;
        max-width: 70rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.observatory-tables article) {
        min-width: 0;
        padding: 1rem;
        border-radius: 0.875rem;
      }

      :where(.observatory-tables h2) {
        margin: 0 0 0.75rem;
        font-size: 1rem;
      }

      :where(.observatory-tables__night) {
        color-scheme: dark;
        color: #e0f2fe;
        background: #0c1b33;
        --cui-table-background: #102a43;
        --cui-table-foreground: #e0f2fe;
        --cui-table-border-color: #486581;
        --cui-table-header-background: #243b53;
        --cui-table-striped-background: #173a5e;
      }

      :where(.observatory-tables__day) {
        color-scheme: light;
        color: #422006;
        background: #fffbeb;
        --cui-table-border-color: #f59e0b;
      }

      :where(.observatory-tables [data-citry-ui-part="footer-cell"]) {
        letter-spacing: 0.02em;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("star", "Star", row_header=True, footer="Brightest"),
                CTableColumn("magnitude", "Magnitude", align="end", footer="-1.46"),
            ),
            "rows": (
                CTableRow("sirius", {"star": "Sirius", "magnitude": "-1.46"}),
                CTableRow("canopus", {"star": "Canopus", "magnitude": "-0.74"}),
                CTableRow("arcturus", {"star": "Arcturus", "magnitude": "-0.05"}),
            ),
        }


preview = ObservatoryTables()

preview  # noqa: B018
