import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class DataGridAtAGlance(Component):
    template = """
      <c-CDataGrid c-columns="columns" c-rows="rows" label="Project members" striped>
        <c-fill name="caption">Current project members</c-fill>
      </c-CDataGrid>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("name", "Name", width=190),
                CDataGridColumn("role", "Role", width=180),
                CDataGridColumn("status", "Status", width=130),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada Lovelace", "role": "Engineer", "status": "Active"}),
                CDataGridRow("grace", {"name": "Grace Hopper", "role": "Admiral", "status": "Active"}),
                CDataGridRow("katherine", {"name": "Katherine Johnson", "role": "Mathematician", "status": "Away"}),
            ),
        }


preview = DataGridAtAGlance()
preview  # noqa: B018
