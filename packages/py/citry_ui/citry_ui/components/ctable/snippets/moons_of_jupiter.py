from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableColumn, CTableRow

citry.register_library(citry_ui)


class MoonsOfJupiter(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="moon-table">
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          striped
          hover
        >
          <c-fill name="caption">
            Galilean moons
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.moon-table) {
        max-width: 48rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.moon-table [data-column-key="diameter"]) {
        font-variant-numeric: tabular-nums;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("moon", "Moon", row_header=True),
                CTableColumn("discoverer", "Discoverer"),
                CTableColumn("diameter", "Diameter", align="end"),
            ),
            "rows": (
                CTableRow("io", {"moon": "Io", "discoverer": "Galileo", "diameter": "3,643 km"}),
                CTableRow("europa", {"moon": "Europa", "discoverer": "Galileo", "diameter": "3,122 km"}),
                CTableRow("ganymede", {"moon": "Ganymede", "discoverer": "Galileo", "diameter": "5,268 km"}),
                CTableRow("callisto", {"moon": "Callisto", "discoverer": "Galileo", "diameter": "4,821 km"}),
            ),
        }


preview = MoonsOfJupiter()

preview  # noqa: B018
