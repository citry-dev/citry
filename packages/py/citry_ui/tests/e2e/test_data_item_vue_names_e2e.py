"""
Browser tests: data cannot give a grid row or a select option an `is` or `key` attribute.

`CDataGrid`, `CTreeGrid` and `CNativeSelect` render their rows and options
through Vue in the browser. Vue reads `is` to name a custom element to create
and `key` to tell rows apart, so these names in a row's, cell's, column's,
option's or group's `attrs` are refused when the page renders. Each test
also loads the same page with an ordinary name and checks that the rows the
browser shows carry it.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

import citry_ui
from citry import Citry, Component
from citry_ui import (
    CDataGridCell,
    CDataGridColumn,
    CDataGridRow,
    CNativeSelectGroup,
    CNativeSelectOption,
    CTreeGridCell,
    CTreeGridColumn,
    CTreeGridRow,
)

pytestmark = pytest.mark.e2e


def _data_grid(attrs: dict[str, object]) -> tuple[str, dict[str, Any]]:
    template = """
      <c-CDataGrid label="Grid" c-columns="columns" c-rows="rows" />
    """
    columns = [
        CDataGridColumn("n", "Name", header_attrs=attrs, cell_attrs=attrs),
    ]
    rows = [
        CDataGridRow("b", {"n": CDataGridCell("Beta", attrs=attrs)}, attrs=attrs),
        CDataGridRow("a", {"n": CDataGridCell("Alpha", attrs=attrs)}, attrs=attrs),
    ]
    return template, {"columns": columns, "rows": rows}


def _tree_grid(attrs: dict[str, object]) -> tuple[str, dict[str, Any]]:
    template = """
      <c-CTreeGrid label="Tree" c-columns="columns" c-rows="rows" />
    """
    columns = [CTreeGridColumn("n", "Name", header_attrs=attrs, cell_attrs=attrs)]
    rows = [CTreeGridRow("r", "Root", {"n": CTreeGridCell("Root", attrs=attrs)}, attrs=attrs)]
    return template, {"columns": columns, "rows": rows}


def _native_select(attrs: dict[str, object]) -> tuple[str, dict[str, Any]]:
    template = """
      <c-CNativeSelect c-options="options" />
    """
    options = [
        CNativeSelectOption("a", "Alpha", attrs=attrs),
        CNativeSelectGroup("g", [CNativeSelectOption("b", "Beta", attrs=attrs)], attrs=attrs),
    ]
    return template, {"options": options}


BUILDERS = {"CDataGrid": _data_grid, "CTreeGrid": _tree_grid, "CNativeSelect": _native_select}


def _page(component: str, attrs: dict[str, object]) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    template, data = BUILDERS[component](attrs)
    members = {
        "citry": app,
        "template": f"<main>{template}</main>",
        "template_data": lambda self, kwargs, slots: data,  # noqa: ARG005
    }
    return type("Page", (Component,), members)().render().serialize()


@pytest.mark.parametrize("name", ["is", "IS", "key", "Key"])
@pytest.mark.parametrize("component", list(BUILDERS))
def test_rows_and_options_refuse_is_and_key_from_data(page: Any, component: str, name: str) -> None:
    """The page does not render with `is` or `key` in an item map, and the rows Vue builds keep other names."""
    with pytest.raises(ValueError, match="'is' and 'key' are reserved"):
        _page(component, {name: "svg"})

    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    html = _page(component, {"title": "kept"})
    # The server writes the rows itself, so a page without JavaScript shows them.
    assert 'title="kept"' in html
    page.set_content(html, wait_until="load")
    page.wait_for_function("() => document.querySelector('[data-citry-ui-part]') !== null")
    page.wait_for_timeout(200)
    shown = page.evaluate(
        """() => ({
          titled: document.querySelectorAll('main [title="kept"]').length,
        })"""
    )

    assert errors == []
    assert shown["titled"] > 0
