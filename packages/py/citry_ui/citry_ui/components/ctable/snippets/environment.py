from typing import Any

import citry_ui
from citry import Component, citry
from citry_ui import CTable, CTableColumn, CTableRow

citry.register_library(citry_ui)


class TableEnvironment(Component):
    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <section class="table-environment" dir="rtl">
        <h2>أسماء النجوم</h2>
        <c-CTable
          c-columns="columns"
          c-rows="rows"
          variant="outline"
          striped
          style="--cui-table-min-width: 42rem"
        >
          <c-fill name="caption">
            أسماء عربية وتقليدية للنجوم
          </c-fill>
        </c-CTable>
      </section>
    """

    css = """
      :where(.table-environment) {
        max-width: 34rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.table-environment h2) {
        margin: 0 0 0.75rem;
        color: light-dark(#6d28d9, #c4b5fd);
        font-size: 1rem;
      }

      :where(.table-environment [data-column-key="notes"]) {
        min-width: 18rem;
        white-space: normal;
        overflow-wrap: anywhere;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:  # noqa: ARG002
        nested = CTable(
            columns=(CTableColumn("planet", "الكوكب"),),
            rows=(CTableRow("earth", {"planet": "الأرض"}),),
            density="compact",
            overflow="visible",
            slots={"caption": "نظام نجمي"},
        )
        return {
            "columns": (
                CTableColumn("name", "الاسم", row_header=True),
                CTableColumn("meaning", "المعنى"),
                CTableColumn("notes", "ملاحظات"),
            ),
            "rows": (
                CTableRow(
                    "betelgeuse",
                    {
                        "name": "منكب الجوزاء",
                        "meaning": "كتف الجبار",
                        "notes": "نجم أحمر فائق الضخامة في كوكبة الجبار، واسمه التقليدي طويل عند نقله بين اللغات.",
                    },
                ),
                CTableRow(
                    "nested",
                    {"name": "الشمس", "meaning": "نجمنا", "notes": nested},
                ),
            ),
        }


preview = TableEnvironment()

preview  # noqa: B018
