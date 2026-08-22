# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)
COLUMNS = [CTreeGridColumn("name", "Account", width=240), CTreeGridColumn("owner", "Owner")]
ROWS = [
    CTreeGridRow(
        "north",
        "Northern region",
        {"name": "Northern region", "owner": "Ada"},
        children=[
            CTreeGridRow("prague", "Prague", {"name": "Prague", "owner": "Mira"}),
            CTreeGridRow("berlin", "Berlin", {"name": "Berlin", "owner": "Noah"}),
        ],
    )
]


class TreeGridAtAGlance(Component):
    def template_data(self, _kwargs, _slots):
        return {"columns": COLUMNS, "rows": ROWS}

    template = '<c-CTreeGrid c-columns="columns" c-rows="rows" label="Account hierarchy" c-expanded="[\'north\']" />'


preview = TreeGridAtAGlance()
preview  # noqa: B018
