import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class DataGridStates(Component):
    template = """
      <div class="grid-states">
        <c-CDataGrid c-columns="columns" c-rows="[]" label="Empty records" />
        <c-CDataGrid c-columns="columns" c-rows="rows" label="Loading records" state="loading" />
        <c-CDataGrid c-columns="columns" c-rows="rows" label="Failed records" state="error">
          <c-fill name="error"><strong>Records are unavailable.</strong> Try again from the toolbar.</c-fill>
        </c-CDataGrid>
      </div>
    """
    css = ":where(.grid-states){display:grid;gap:1rem}"

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (CDataGridColumn("name", "Name"), CDataGridColumn("status", "Status")),
            "rows": (CDataGridRow("placeholder", {"name": "Placeholder", "status": "Pending"}),),
        }


preview = DataGridStates()
preview  # noqa: B018
