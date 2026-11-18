"""The attribute map of a table row, cell, column, select option or breadcrumb item refuses `is` and `key`."""

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
from citry_ui.components._attrs import reject_data_item_vue_name

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

# `is` names a custom element for Vue to create, and the server leaves the
# row out of its HTML; `key` would clash with the row or option key the
# component sets. One spelling of each case is enough per map; the test
# below covers every letter case and value against one map.
REFUSED = [("is", "svg"), ("IS", "math"), ("key", "x"), ("Key", "x")]


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
@pytest.mark.parametrize(("name", "value"), REFUSED)
@pytest.mark.parametrize("case", list(CASES))
def test_data_item_attrs_refuse_names_vue_reads(
    app: Citry, case: str, name: str, value: str, *, interactive: bool
) -> None:
    """A data item's `attrs` cannot set `is` or `key`, whatever the letter case and the value."""
    # Every map, the editor map included, runs the shared reserved-name check
    # first, so every case gets the shared message.
    message = "'is' and 'key' are reserved"
    with pytest.raises(ValueError, match=f"{name!r}. {message}"):
        _render(app, case, {name: value}, interactive=interactive)


@pytest.mark.parametrize(
    "name",
    ["is", "IS", "Is", "iS", "key", "KEY", "Key", "kEy"],
)
@pytest.mark.parametrize("value", ["svg", "math", "mglyph", "malignmark", "vue:svg", "div", "", None, False])
def test_every_spelling_and_value_is_refused(app: Citry, name: str, value: object) -> None:
    """The check reads only the name, so no letter case and no value gets through, also `None` or `False`."""
    with pytest.raises(ValueError, match="'is' and 'key' are reserved"):
        _render(app, "CDataGridRow.attrs", {name: value})


def test_str_subclass_name_cannot_hide_is() -> None:
    """A `str` subclass that answers `translate` with another spelling is still read as its real text."""

    class Disguised(str):
        __slots__ = ()

        def translate(self, table: object) -> str:
            return "title"

    with pytest.raises(ValueError, match="'is' and 'key' are reserved"):
        reject_data_item_vue_name(Disguised("is"), where="CTable row 'r' attrs")


# The editor map takes only a short list of input attributes, applied in the
# browser when editing starts, so it has no place in the rendered-HTML control.
_RENDERED_CASES = [case for case in CASES if case != "CDataGridColumn.editor_attrs"]


@pytest.mark.parametrize("interactive", [False, True], ids=["page", "inside-js-component"])
@pytest.mark.parametrize("case", _RENDERED_CASES)
def test_data_item_attrs_keep_names_that_only_contain_is_or_key(app: Citry, case: str, *, interactive: bool) -> None:
    """Control: `title`, `data-is` and `data-key` still render in the same maps."""
    html = _render(app, case, {"title": "t1", "data-is": "svg", "data-key": "k1"}, interactive=interactive)

    assert 'title="t1"' in html or '"title":"t1"' in html
    assert "data-is" in html
