import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridRow, CDataGridSort

citry.register_library(citry_ui)


class DataGridSortingSelection(Component):
    template = """
      <section x-data="{sort:[{key:'name',direction:'asc'}],notice:'Activate a sortable header or select a row'}">
        <output x-text="notice">Activate a sortable header or select a row</output>
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          c-sort="sort"
          label="Sortable people"
          selection="multiple"
          c-selected="['grace']"
          $c-props="{
            sort,
            onSortChange:(next,detail)=>{
              sort=next;
              notice=`Accepted sort: ${detail.columnKey} ${detail.direction ?? 'none'}`;
            },
            onSelectionChange:(selected)=>notice=`Selected: ${selected.join(', ') || 'none'}`,
          }"
        />
      </section>
    """

    def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
        return {
            "columns": (
                CDataGridColumn("name", "Name", sortable=True, width=190),
                CDataGridColumn("team", "Team", sortable=True, width=150),
                CDataGridColumn("score", "Score", sortable=True, width=100, align="end"),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada Lovelace", "team": "Platform", "score": 98}),
                CDataGridRow("grace", {"name": "Grace Hopper", "team": "Compiler", "score": 95}),
                CDataGridRow("lin", {"name": "Lin Clark", "team": "Runtime", "score": 91}),
            ),
            "sort": (CDataGridSort("name", "asc"),),
        }


preview = DataGridSortingSelection()
preview  # noqa: B018
