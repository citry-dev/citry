"""Citry UI components hand your `attrs` mapping to HTML elements, and Citry checks each name."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CBreadcrumbItem, CTableCell, CTableColumn, CTableRow

# Each case is a template plus a function that puts the `attrs` mapping into
# the data the template reads, at the place that component hands it to an
# element. These components do not check the names themselves; the
# check is the one Citry applies to every attribute mapping bound to an element.
AttrsCase = tuple[str, Callable[[Mapping[str, object]], dict[str, Any]]]

CASES: dict[str, AttrsCase] = {
    "badge": (
        """
        <c-CBadge c-attrs="attrs">x</c-CBadge>
        """,
        lambda attrs: {"attrs": attrs},
    ),
    "card": (
        """
        <c-CCard c-attrs="attrs">x</c-CCard>
        """,
        lambda attrs: {"attrs": attrs},
    ),
    "breadcrumb-current-item": (
        """
        <c-CBreadcrumbs c-items="items" />
        """,
        lambda attrs: {"items": (CBreadcrumbItem("Home", "/"), CBreadcrumbItem("Now", attrs=attrs))},
    ),
    "breadcrumb-link-item": (
        """
        <c-CBreadcrumbs c-items="items" />
        """,
        lambda attrs: {"items": (CBreadcrumbItem("Home", "/", attrs=attrs), CBreadcrumbItem("Now"))},
    ),
    "table-cell-in-row": (
        """
        <c-CTable c-columns="columns" c-rows="rows" />
        """,
        lambda attrs: {
            "columns": (CTableColumn("n", "Name"),),
            "rows": (CTableRow("r1", {"n": CTableCell("x", attrs=attrs)}),),
        },
    ),
    "table-column-header": (
        """
        <c-CTable c-columns="columns" c-rows="rows" />
        """,
        lambda attrs: {
            "columns": (CTableColumn("n", "Name", header_attrs=attrs),),
            "rows": (CTableRow("r1", {"n": "x"}),),
        },
    ),
    "table-column-cells": (
        """
        <c-CTable c-columns="columns" c-rows="rows" />
        """,
        lambda attrs: {
            "columns": (CTableColumn("n", "Name", cell_attrs=attrs),),
            "rows": (CTableRow("r1", {"n": "x"}),),
        },
    ),
    "table-column-footer": (
        """
        <c-CTable c-columns="columns" c-rows="rows" />
        """,
        lambda attrs: {
            "columns": (CTableColumn("n", "Name", footer="total", footer_attrs=attrs),),
            "rows": (CTableRow("r1", {"n": "x"}),),
        },
    ),
}


# A fresh app per test, because each test defines its own `Page` class and an
# app refuses a second class with the same name.
@pytest.fixture
def app() -> Citry:
    registry = Citry(autodiscover=False)
    registry.register_library(citry_ui)
    return registry


def _render_case(app: Citry, case: str, attrs: Mapping[str, object]) -> str:
    """Render one component with `attrs` and return its HTML."""
    source, build_data = CASES[case]
    data = build_data(attrs)

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data

        template = source

    return Page().render().serialize(security_javascript="omit")


@pytest.mark.parametrize("case", list(CASES))
@pytest.mark.parametrize("name", ["onclick", "OnClick"])
def test_citry_ui_attrs_may_not_name_code_reading_attributes(app: Citry, case: str, name: str) -> None:
    """
    An `attrs` key such as `onclick` is refused, because the browser reads that value as code.

    Citry UI components take `attrs` from your code, which may build it from
    data. An event handler is written in the template, as `@click` or `@c-click`.
    """
    with pytest.raises(ValueError, match="start with 'on'"):
        _render_case(app, case, {name: "x"})


@pytest.mark.parametrize("case", list(CASES))
def test_citry_ui_attrs_keep_ordinary_attributes(app: Citry, case: str) -> None:
    """Control: an ordinary attribute name in the same place renders on the element."""
    html = _render_case(app, case, {"title": "x"})

    assert 'title="x"' in html
