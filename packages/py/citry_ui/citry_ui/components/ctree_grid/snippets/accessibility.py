# ruff: noqa: ANN001, ANN201 - public snippets keep focus on component use

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridAccessibility(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("name", "Record", 260), CTreeGridColumn("status", "Status")],
            "rows": [
                CTreeGridRow("available", "Available record", {"name": "Available record", "status": "Ready"}),
                CTreeGridRow(
                    "locked", "Locked record", {"name": "Locked record", "status": "Archived"}, disabled=True
                ),
            ],
        }

    template = (
        '<c-CTreeGrid c-columns="columns" c-rows="rows" label="Records" selection="multiple" density="spacious" />'
    )


preview = TreeGridAccessibility()
preview  # noqa: B018
