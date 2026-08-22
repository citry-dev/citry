import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class WindowedDataGrid(Component):
    template = """
      <section x-data="{notice:'This static preview supplies one complete window'}">
        <output x-text="notice">This static preview supplies one complete window</output>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Audit records"
          c-total_count="16"
          c-row_height="44"
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
                for index in range(16)
            ),
        }


preview = WindowedDataGrid()
preview  # noqa: B018
