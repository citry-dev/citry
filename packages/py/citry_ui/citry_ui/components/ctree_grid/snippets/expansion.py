# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridExpansion(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("work", "Work item", 260), CTreeGridColumn("state", "State")],
            "rows": [
                CTreeGridRow(
                    "launch",
                    "Launch",
                    {"work": "Launch", "state": "Active"},
                    children=[
                        CTreeGridRow("design", "Design", {"work": "Design", "state": "Done"}),
                        CTreeGridRow("build", "Build", {"work": "Build", "state": "Active"}),
                    ],
                )
            ],
        }

    template = '<c-CTreeGrid c-columns="columns" c-rows="rows" label="Project plan" c-expanded="[\'launch\']" />'


preview = TreeGridExpansion()
preview  # noqa: B018
