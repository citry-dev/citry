"""Shared Data Grid scenario used by repository quality tools."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from citry import Citry, Component
from citry_ui import CDataGridColumn, CDataGridRow, CDataGridSort


def data_grid_states_component(app: Citry) -> type[Component]:
    class CitryUiDataGridStates(Component):
        citry = app
        template = """
          <section
            class="citry-ui-quality-stack"
            data-quality-data-grid-ready
            data-quality-states="ready sort selection controlled editing window loading empty error rtl narrow cleanup"
          >
            <h1>Data Grid states</h1>
            <div x-data="{sort:[{key:'name',direction:'asc'}],selected:['grace'],notice:'Ready'}">
              <output x-text="notice">Ready</output>
              <c-CDataGrid
                id="quality-data-grid"
                c-columns="columns"
                c-rows="rows"
                c-sort="sort"
                label="Project members"
                selection="multiple"
                c-selected="['grace']"
                striped
                column_borders
                $c-props="{
                  sort,
                  selected,
                  onSortChange:(next)=>{sort=next;notice='Sort accepted'},
                  onSelectionChange:(next)=>{selected=next;notice='Selection accepted'},
                  onCellActivate:(detail)=>notice=`Activated ${detail.rowKey}/${detail.columnKey}`,
                  onCellEditCommit:(value,detail)=>notice=`Edit requested ${detail.rowKey}/${detail.columnKey}: ${value}`,
                }"
              >
                <c-fill name="caption">Keyboard-navigable project members</c-fill>
              </c-CDataGrid>
            </div>
            <div dir="rtl" x-data="{lastRange:null}">
              <c-CDataGrid
                c-columns="columns"
                c-rows="window_rows"
                label="سجل التدقيق"
                c-total_count="200"
                c-start_index="20"
                c-row_height="44"
                c-viewport_size="240"
                c-initial_index="20"
                $c-props="{onRangeChange:(detail)=>lastRange=detail}"
              />
            </div>
            <div class="citry-ui-quality-grid">
              <c-CDataGrid c-columns="columns" c-rows="[]" label="Empty members" />
              <c-CDataGrid c-columns="columns" c-rows="rows" label="Loading members" state="loading" />
              <c-CDataGrid c-columns="columns" c-rows="rows" label="Failed members" state="error" />
            </div>
          </section>
        """

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            columns = (
                CDataGridColumn("name", "Name", sortable=True, width=210, editable=True),
                CDataGridColumn("team", "Team with a long localized heading", sortable=True, width=220),
                CDataGridColumn(
                    "score", "Score", sortable=True, width=110, align="end", editable=True, editor="number"
                ),
            )
            return {
                "columns": columns,
                "sort": (CDataGridSort("name", "asc"),),
                "rows": (
                    CDataGridRow("ada", {"name": "Ada Lovelace", "team": "Platform", "score": 98}),
                    CDataGridRow("grace", {"name": "Grace Hopper", "team": "Compiler", "score": 95}),
                    CDataGridRow(
                        "locked",
                        {"name": "A disabled member with long content", "team": "Security", "score": 90},
                        disabled=True,
                    ),
                ),
                "window_rows": tuple(
                    CDataGridRow(
                        f"audit-{index}",
                        {"name": f"سجل {index + 1}", "team": "فريق المنصة", "score": index},
                    )
                    for index in range(20, 32)
                ),
            }

    return CitryUiDataGridStates


__all__ = ["data_grid_states_component"]
