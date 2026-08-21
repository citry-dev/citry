import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow

citry.register_library(citry_ui)


class ControlledDataGrid(Component):
    template = """
      <section x-data="{sort:[],selected:['ada']}">
        <button type="button" @click="selected=[]">Clear selection</button>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Controlled members"
          selection="multiple"
          $c-props="{
            sort,
            selected,
            onSortChange:(next)=>sort=next,
            onSelectionChange:(next)=>selected=next,
          }"
        />
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("name", "Name", sortable=True, width=190),
                CDataGridColumn("role", "Role", sortable=True, width=170),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada Lovelace", "role": "Engineer"}),
                CDataGridRow("grace", {"name": "Grace Hopper", "role": "Admiral"}),
            ),
        }


preview = ControlledDataGrid()
preview  # noqa: B018
