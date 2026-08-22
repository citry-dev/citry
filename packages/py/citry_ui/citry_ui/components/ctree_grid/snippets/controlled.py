# ruff: noqa: ANN001, ANN201, E501 - public template stays readable

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridControlled(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("name", "Name")],
            "rows": [
                CTreeGridRow(
                    "root", "Root", {"name": "Root"}, children=[CTreeGridRow("child", "Child", {"name": "Child"})]
                )
            ],
        }

    template = """<div x-data="{open:[],chosen:[]}"><c-CTreeGrid c-columns="columns" c-rows="rows" label="Controlled tree" selection="multiple" $c-props="{expanded:open,selected:chosen,onExpandedChange:value=>open=value,onSelectionChange:value=>chosen=value}" /></div>"""


preview = TreeGridControlled()
preview  # noqa: B018
