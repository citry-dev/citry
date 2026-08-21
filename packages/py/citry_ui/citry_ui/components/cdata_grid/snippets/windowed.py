import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class WindowedDataGrid(Component):
    template = """
      <section x-data="{notice:'This preview shows the final server range'}">
        <output x-text="notice">This preview shows the final server range</output>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Audit records"
          c-total_count="36"
          c-start_index="20"
          c-row_height="44"
          c-initial_index="20"
          $c-props="{onRangeChange:(detail)=>notice=`Requested ${detail.startIndex}-${detail.endIndex - 1}`}"
        />
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("number", "Record", width=120),
                CDataGridColumn("action", "Action", width=230),
                CDataGridColumn("actor", "Actor", width=160),
            ),
            "rows": tuple(
                CDataGridRow(
                    f"audit-{index}",
                    {"number": f"#{index + 1:05d}", "action": "Signed deployment record", "actor": "Release bot"},
                )
                for index in range(20, 36)
            ),
        }


preview = WindowedDataGrid()
preview  # noqa: B018
