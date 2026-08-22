# ruff: noqa: ANN001, ANN201, E501 - public template stays readable

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridSelection(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("team", "Team"), CTreeGridColumn("people", "People")],
            "rows": [
                CTreeGridRow("product", "Product", {"team": "Product", "people": 18}),
                CTreeGridRow("ops", "Operations", {"team": "Operations", "people": 12}),
            ],
        }

    template = '<form><c-CTreeGrid c-columns="columns" c-rows="rows" label="Teams" selection="multiple" c-selected="[\'product\']" name="team" /></form>'


preview = TreeGridSelection()
preview  # noqa: B018
