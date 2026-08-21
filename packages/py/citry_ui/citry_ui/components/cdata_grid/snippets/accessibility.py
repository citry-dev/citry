import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class AccessibleDataGrid(Component):
    template = """
      <c-CDataGrid
        c-columns="columns"
        c-rows="rows"
        label="Deployment approvals"
        selection="multiple"
      >
        <c-fill name="caption">Use Arrow keys to move and Shift+Space to select an enabled Row.</c-fill>
      </c-CDataGrid>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("change", "Change", width=240),
                CDataGridColumn("owner", "Owner", width=160),
                CDataGridColumn("status", "Approval status", width=160),
            ),
            "rows": (
                CDataGridRow("api", {"change": "API release", "owner": "Ada", "status": "Approved"}),
                CDataGridRow(
                    "locked",
                    {"change": "Security policy", "owner": "Grace", "status": "Locked"},
                    disabled=True,
                ),
                CDataGridRow("docs", {"change": "Guide update", "owner": "Lin", "status": "Review"}),
            ),
        }


preview = AccessibleDataGrid()
preview  # noqa: B018
