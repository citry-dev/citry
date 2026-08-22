# ruff: noqa: ANN001, ANN201, E501 - public template stays readable

import citry_ui
from citry import Component, citry
from citry_ui import CTreeGridColumn, CTreeGridRow

citry.register_library(citry_ui)


class TreeGridCustomCells(Component):
    def template_data(self, _kwargs, _slots):
        return {
            "columns": [CTreeGridColumn("name", "Initiative", 240), CTreeGridColumn("score", "Score", align="end")],
            "rows": [
                CTreeGridRow(
                    "quality",
                    "Quality",
                    {"name": "Quality", "score": 92},
                    children=[CTreeGridRow("a11y", "Accessibility", {"name": "Accessibility", "score": 98})],
                )
            ],
        }

    template = """<c-CTreeGrid c-columns="columns" c-rows="rows" label="Initiatives" c-expanded="['quality']"><c-fill name="cell" data="{ column, cell }"><strong c-if="column.key == 'score'">{{ cell.value }}%</strong><span c-else>{{ cell.value }}</span></c-fill></c-CTreeGrid>"""


preview = TreeGridCustomCells()
preview  # noqa: B018
