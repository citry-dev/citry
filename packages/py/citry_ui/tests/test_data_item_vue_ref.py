"""The attribute map of a table row, cell, column, select option or breadcrumb item refuses Vue `ref` names."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import (
    CBreadcrumbItem,
    CDataGridCell,
    CDataGridColumn,
    CDataGridRow,
    CNativeSelectGroup,
    CNativeSelectOption,
    CTableCell,
    CTableColumn,
    CTableRow,
    CTreeGridCell,
    CTreeGridColumn,
    CTreeGridRow,
)

# Each case is a template plus a function that puts the `attrs` mapping into
# one data item's map. CDataGrid, CTreeGrid and CNativeSelect render these
# rows and options through Vue in the browser; CTable and CBreadcrumbs write
# them as static HTML and follow the same rule.
ItemCase = tuple[str, Callable[[Mapping[str, object]], dict[str, Any]]]

_TABLE = """
<c-CTable c-columns="columns" c-rows="rows" />
"""
_DATA_GRID = """
<c-CDataGrid label="Grid" c-columns="columns" c-rows="rows" />
"""
_TREE_GRID = """
<c-CTreeGrid label="Tree" c-columns="columns" c-rows="rows" />
"""
_NATIVE_SELECT = """
<c-CNativeSelect c-options="options" />
"""
_BREADCRUMBS = """
<c-CBreadcrumbs c-items="items" />
"""

CASES: dict[str, ItemCase] = {
    "CTableRow.attrs": (
        _TABLE,
        lambda a: {"columns": [CTableColumn("n", "N")], "rows": [CTableRow("r", {"n": "x"}, attrs=a)]},
    ),
    "CTableCell.attrs": (
        _TABLE,
        lambda a: {"columns": [CTableColumn("n", "N")], "rows": [CTableRow("r", {"n": CTableCell("x", attrs=a)})]},
    ),
    "CTableColumn.header_attrs": (
        _TABLE,
        lambda a: {"columns": [CTableColumn("n", "N", header_attrs=a)], "rows": [CTableRow("r", {"n": "x"})]},
    ),
    "CTableColumn.cell_attrs": (
        _TABLE,
        lambda a: {"columns": [CTableColumn("n", "N", cell_attrs=a)], "rows": [CTableRow("r", {"n": "x"})]},
    ),
    "CTableColumn.footer_attrs": (
        _TABLE,
        lambda a: {
            "columns": [CTableColumn("n", "N", footer="f", footer_attrs=a)],
            "rows": [CTableRow("r", {"n": "x"})],
        },
    ),
    "CDataGridRow.attrs": (
        _DATA_GRID,
        lambda a: {"columns": [CDataGridColumn("n", "N")], "rows": [CDataGridRow("r", {"n": "x"}, attrs=a)]},
    ),
    "CDataGridCell.attrs": (
        _DATA_GRID,
        lambda a: {
            "columns": [CDataGridColumn("n", "N")],
            "rows": [CDataGridRow("r", {"n": CDataGridCell("x", attrs=a)})],
        },
    ),
    "CDataGridColumn.header_attrs": (
        _DATA_GRID,
        lambda a: {"columns": [CDataGridColumn("n", "N", header_attrs=a)], "rows": [CDataGridRow("r", {"n": "x"})]},
    ),
    "CDataGridColumn.cell_attrs": (
        _DATA_GRID,
        lambda a: {"columns": [CDataGridColumn("n", "N", cell_attrs=a)], "rows": [CDataGridRow("r", {"n": "x"})]},
    ),
    "CDataGridColumn.editor_attrs": (
        _DATA_GRID,
        lambda a: {
            "columns": [CDataGridColumn("n", "N", editable=True, editor_attrs=a)],
            "rows": [CDataGridRow("r", {"n": "x"})],
        },
    ),
    "CTreeGridRow.attrs": (
        _TREE_GRID,
        lambda a: {"columns": [CTreeGridColumn("n", "N")], "rows": [CTreeGridRow("r", "R", {"n": "x"}, attrs=a)]},
    ),
    "CTreeGridCell.attrs": (
        _TREE_GRID,
        lambda a: {
            "columns": [CTreeGridColumn("n", "N")],
            "rows": [CTreeGridRow("r", "R", {"n": CTreeGridCell("x", attrs=a)})],
        },
    ),
    "CTreeGridColumn.header_attrs": (
        _TREE_GRID,
        lambda a: {
            "columns": [CTreeGridColumn("n", "N", header_attrs=a)],
            "rows": [CTreeGridRow("r", "R", {"n": "x"})],
        },
    ),
    "CTreeGridColumn.cell_attrs": (
        _TREE_GRID,
        lambda a: {
            "columns": [CTreeGridColumn("n", "N", cell_attrs=a)],
            "rows": [CTreeGridRow("r", "R", {"n": "x"})],
        },
    ),
    "CNativeSelectOption.attrs": (
        _NATIVE_SELECT,
        lambda a: {"options": [CNativeSelectOption("a", "A", attrs=a)]},
    ),
    "CNativeSelectGroup.attrs": (
        _NATIVE_SELECT,
        lambda a: {"options": [CNativeSelectGroup("g", [CNativeSelectOption("a", "A")], attrs=a)]},
    ),
    "CBreadcrumbItem.attrs": (
        _BREADCRUMBS,
        lambda a: {"items": [CBreadcrumbItem("Home", "/", attrs=a), CBreadcrumbItem("Now")]},
    ),
}

# Vue reads `ref`, `ref_for` and `ref_key` itself and stores the element in
# the component's own value of that name, so data must not choose them. Core
# `c-bind` refuses them while the page renders, before the Vue writer turns
# the rows and options into the data the browser renders from.
REFUSED = ["ref", "REF", "ref_for", "Ref_Key"]


# A fresh app per test, because each test defines its own `Page` class and an
# app refuses a second class with the same name.
@pytest.fixture
def app() -> Citry:
    registry = Citry(autodiscover=False)
    registry.register_library(citry_ui)
    return registry


def _render(app: Citry, case: str, attrs: Mapping[str, object], *, interactive: bool = False) -> str:
    """Render one component with `attrs` in one data item's map and return the HTML."""
    source, build_data = CASES[case]
    data = build_data(attrs)
    # Inside a component with `js`, a static component's HTML becomes part of
    # the parent's Vue render too, so both placements are checked.
    members: dict[str, Any] = {
        "citry": app,
        "template": f"<div>{source}</div>",
        "template_data": lambda self, kwargs, slots: data,  # noqa: ARG005
    }
    if interactive:
        members["js"] = "\n$component({});\n"
    page = type("Page", (Component,), members)
    return page().render().serialize(security_javascript="omit")


@pytest.mark.parametrize("interactive", [False, True], ids=["page", "inside-js-component"])
@pytest.mark.parametrize("name", REFUSED)
@pytest.mark.parametrize("case", list(CASES))
def test_data_item_attrs_refuse_vue_ref_names(app: Citry, case: str, name: str, *, interactive: bool) -> None:
    """A data item's `attrs` cannot set `ref`, `ref_for` or `ref_key`, whatever the letter case."""
    # The editor map takes a short list of input attributes and refuses the
    # names with its own message; every other map reaches core `c-bind`.
    message = "cannot contain" if case == "CDataGridColumn.editor_attrs" else f"c-bind sets {name!r}"
    with pytest.raises(ValueError, match=message):
        _render(app, case, {name: "items"}, interactive=interactive)


# The editor map takes only a short list of input attributes, applied in the
# browser when editing starts, so it has no place in the rendered-HTML control.
_RENDERED_CASES = [case for case in CASES if case != "CDataGridColumn.editor_attrs"]


@pytest.mark.parametrize("interactive", [False, True], ids=["page", "inside-js-component"])
@pytest.mark.parametrize("case", _RENDERED_CASES)
def test_data_item_attrs_keep_names_that_only_look_like_ref(app: Citry, case: str, *, interactive: bool) -> None:
    """Control: `reference` and `data-ref` still render in the same maps."""
    html = _render(app, case, {"reference": "r1", "data-ref": "r2"}, interactive=interactive)

    assert 'reference="r1"' in html or '"reference":"r1"' in html
    assert "data-ref" in html
