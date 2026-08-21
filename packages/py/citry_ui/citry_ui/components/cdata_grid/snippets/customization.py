import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class CustomizedDataGrid(Component):
    template = """
      <div class="custom-grid">
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Compact metrics"
          density="compact"
          striped
          column_borders
          c-style="{
            '--cui-data-grid-radius':'1rem',
            '--cui-data-grid-selected-background':'color-mix(in srgb, #7c3aed 20%, Canvas)',
          }"
        />
      </div>
    """
    css = """
      :where(.custom-grid [data-citry-ui-part="header-cell"]) { text-transform:uppercase;letter-spacing:.04em; }
      :where(.custom-grid [data-column-key="value"]) { font-variant-numeric:tabular-nums; }
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("metric", "Metric", width=220),
                CDataGridColumn("value", "Value", width=120, align="end"),
            ),
            "rows": (
                CDataGridRow("latency", {"metric": "P95 latency", "value": "128 ms"}),
                CDataGridRow("errors", {"metric": "Error rate", "value": "0.04%"}),
                CDataGridRow("uptime", {"metric": "Uptime", "value": "99.99%"}),
            ),
        }


preview = CustomizedDataGrid()
preview  # noqa: B018
