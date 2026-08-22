"""Shared Tree Grid scenario used by repository quality tools."""

# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from citry import Citry, Component
from citry_ui import CTreeGridColumn, CTreeGridRow


def tree_grid_states_component(app: Citry) -> type[Component]:
    class CitryUiTreeGridStates(Component):
        citry = app

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {
                "columns": [
                    CTreeGridColumn("name", "Work item", 300),
                    CTreeGridColumn("owner", "Owner"),
                    CTreeGridColumn("score", "Score", align="end"),
                ],
                "rows": [
                    CTreeGridRow(
                        "program",
                        "A very long program name that wraps safely",
                        {"name": "A very long program name that wraps safely", "owner": "Ada", "score": 92},
                        children=[
                            CTreeGridRow("rtl", "مرحلة البحث", {"name": "مرحلة البحث", "owner": "Mira", "score": 98}),
                            CTreeGridRow(
                                "locked",
                                "Locked task",
                                {"name": "Locked task", "owner": "Noah", "score": 74},
                                disabled=True,
                            ),
                        ],
                    )
                ],
                "quality_attrs": {
                    "data-quality-states": "hierarchy expanded collapsed selection unselection keyboard pointer form disabled rtl narrow localized cleanup"
                },
            }

        template = """<section class="citry-ui-quality-stack" data-quality-tree-grid-ready><h1>Tree Grid states</h1><form><c-CTreeGrid id="quality-tree-grid" c-columns="columns" c-rows="rows" label="Work hierarchy" c-expanded="['program']" selection="multiple" c-selected="['rtl']" name="row" c-attrs="quality_attrs" /></form></section>"""

    return CitryUiTreeGridStates


__all__ = ["tree_grid_states_component"]
