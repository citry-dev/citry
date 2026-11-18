"""Citry UI fills an app's label placeholders on the server the way its browser code does."""

from __future__ import annotations

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTreeGridColumn, CTreeGridRow
from citry_ui.components._i18n import fill_label


@pytest.mark.parametrize(
    ("pattern", "values", "expected"),
    [
        ("{count} items added", {"count": 3}, "3 items added"),
        ("{selected} of {total}", {"selected": 1, "total": 9}, "1 of 9"),
        ("Remove {item}, then {item}", {"item": "Ada"}, "Remove Ada, then Ada"),
        # A format spec and a field lookup are not placeholders in the
        # browser's text replacement, so they stay; in a doubled brace only
        # the inner `{count}` is replaced.
        ("{total:>99}", {"total": 9}, "{total:>99}"),
        ("{item.__class__}", {"item": "Ada"}, "{item.__class__}"),
        ("{{count}}", {"count": 3}, "{3}"),
        ("No placeholder", {"count": 3}, "No placeholder"),
    ],
)
def test_fill_label_replaces_only_exact_placeholders(pattern: str, values: dict[str, object], expected: str) -> None:
    assert fill_label(pattern, **values) == expected


def _render(source: str, **data: object) -> str:
    # A fresh app per render, because each render defines its own `Page`
    # class and an app refuses a second class with the same name.
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data

    return str(Page())


def test_tree_grid_template_fills_its_row_label() -> None:
    # CTreeGrid fills the expand label inside its template, per row.
    html = _render(
        """
        <c-CTreeGrid
          label="Files"
          c-columns="columns"
          c-rows="rows"
          expand_label="Open {row} {row:>9}"
        />
        """,
        columns=[CTreeGridColumn("n", "Name")],
        rows=[CTreeGridRow("docs", "Docs", {"n": "Docs"}, children=[CTreeGridRow("a", "A", {"n": "A"})])],
    )
    assert 'aria-label="Open Docs {row:>9}"' in html


def test_sortable_fills_its_handle_label() -> None:
    html = _render(
        """
        <c-CSortable name="order" handle_label="Move {item} {item.__class__}">
          <c-CSortableItem value="a" label="Alpha" />
        </c-CSortable>
        """
    )
    assert 'aria-label="Move Alpha {item.__class__}"' in html
