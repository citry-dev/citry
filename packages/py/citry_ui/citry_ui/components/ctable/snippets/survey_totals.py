from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class SurveyTotals(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="survey-totals">
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          variant="outline"
        >
          <c-fill name="caption">
            Telescope survey time
          </c-fill>
          <c-fill name="footer" data="{ column, value }">
            <c-if cond="column.key == 'hours'">
              <strong>{{ value }}</strong>
            </c-if>
            <c-else>
              {{ value }}
            </c-else>
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.survey-totals) {
        max-width: 44rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.survey-totals [data-citry-ui-part="footer-cell"]) {
        color: light-dark(#1e3a8a, #bfdbfe);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("program", "Program", row_header=True, footer="Total"),
                CTableColumn("instrument", "Instrument", footer="3 programs"),
                CTableColumn(
                    "hours",
                    "Hours",
                    align="end",
                    cell_attrs={"style": {"font-variant-numeric": "tabular-nums"}},
                    footer="84.5",
                ),
            ),
            "rows": (
                CTableRow("aurora", {"program": "Aurora survey", "instrument": "Spectrograph", "hours": "36.0"}),
                CTableRow("rings", {"program": "Ring survey", "instrument": "Wide-field camera", "hours": "28.5"}),
                CTableRow("comets", {"program": "Comet survey", "instrument": "Infrared camera", "hours": "20.0"}),
            ),
        }


preview = SurveyTotals()

preview  # noqa: B018
