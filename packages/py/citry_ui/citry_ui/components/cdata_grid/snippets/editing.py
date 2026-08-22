# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CDataGridColumn, CDataGridEditOption, CDataGridRow

citry.register_library(citry_ui)


class EditableDataGrid(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": (
                CDataGridColumn("name", "Name", editable=True, editor_attrs={"maxlength": 80}),
                CDataGridColumn(
                    "role",
                    "Role",
                    editable=True,
                    editor="select",
                    editor_options=(
                        CDataGridEditOption("engineer", "Engineer"),
                        CDataGridEditOption("designer", "Designer"),
                        CDataGridEditOption("lead", "Lead"),
                    ),
                ),
                CDataGridColumn(
                    "allocation",
                    "Allocation",
                    editable=True,
                    editor="number",
                    editor_attrs={"min": 0, "max": 100, "step": 5},
                ),
                CDataGridColumn("active", "Active", editable=True, editor="checkbox"),
            ),
            "rows": (
                CDataGridRow("ada", {"name": "Ada", "role": "engineer", "allocation": 80, "active": True}),
                CDataGridRow("mira", {"name": "Mira", "role": "designer", "allocation": 60, "active": True}),
            ),
        }

    template = """
      <section x-data="{last:'Double-click or press Enter to edit'}">
        <c-CDataGrid
          c-columns="columns"
          c-rows="rows"
          label="Project assignments"
          $c-props="{onCellEditCommit:(value,detail)=>last=`${detail.rowKey}.${detail.columnKey}: ${value}`}"
        />
        <output x-text="last">Double-click or press Enter to edit</output>
      </section>
    """


preview = EditableDataGrid()
preview  # noqa: B018
