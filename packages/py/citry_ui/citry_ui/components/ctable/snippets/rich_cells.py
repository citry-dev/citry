from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTableCell, CTableColumn, CTableRow

citry.register_library(citry_ui)


class ObservationCatalog(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="observation-catalog">
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          variant="outline"
          hover
        >
          <c-fill name="caption">
            Tonight's observation catalog
          </c-fill>
          <c-fill name="cell" data="{ row, column, cell }">
            <c-if cond="column.key == 'visibility'">
              <span c-class="['visibility', 'visibility--' + cell.value]">
                {{ cell.value }}
              </span>
            </c-if>
            <c-elif cond="column.key == 'action'">
              <c-CButton size="sm" variant="outline">
                View {{ row.key }}
              </c-CButton>
            </c-elif>
            <c-else>
              {{ cell.value }}
            </c-else>
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.observation-catalog) {
        max-width: 58rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.visibility) {
        display: inline-flex;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: capitalize;
      }

      :where(.visibility--excellent) {
        color: light-dark(#166534, #bbf7d0);
        background: light-dark(#dcfce7, #14532d);
      }

      :where(.visibility--limited) {
        color: light-dark(#9a3412, #fed7aa);
        background: light-dark(#ffedd5, #7c2d12);
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        return {
            "columns": (
                CTableColumn("target", "Target", row_header=True),
                CTableColumn("type", "Type"),
                CTableColumn("visibility", "Visibility"),
                CTableColumn("action", "Actions"),
            ),
            "rows": (
                CTableRow(
                    "orion-nebula",
                    {"target": "Orion Nebula", "type": "Nebula", "visibility": "excellent", "action": None},
                ),
                CTableRow(
                    "andromeda",
                    {
                        "target": CTableCell("Andromeda Galaxy", attrs={"class": "featured-target"}),
                        "type": "Galaxy",
                        "visibility": "limited",
                        "action": None,
                    },
                ),
            ),
        }


preview = ObservationCatalog()

preview  # noqa: B018
