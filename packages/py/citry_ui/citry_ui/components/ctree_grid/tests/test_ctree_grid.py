from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTreeGrid, CTreeGridColumn, CTreeGridRow


def _render(columns, rows, attrs: str = "") -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {"columns": columns, "rows": rows}

        template = f'<c-CTreeGrid c-columns="columns" c-rows="rows" label="Hierarchy" {attrs} />'

    return str(Page())


def _data():
    columns = [CTreeGridColumn("name", "Name", 240), CTreeGridColumn("owner", "Owner")]
    rows = [
        CTreeGridRow(
            "root",
            "Root",
            {"name": "Root", "owner": "Ada"},
            children=[CTreeGridRow("child", "Child", {"name": "Child", "owner": "Mira"})],
        )
    ]
    return columns, rows


def test_schema_registration_hierarchy_and_native_selection() -> None:
    columns, rows = _data()
    assert [item.name for item in fields(CTreeGrid.Kwargs)][:9] == [
        "columns",
        "rows",
        "label",
        "id",
        "expanded",
        "selection",
        "selected",
        "name",
        "form",
    ]
    assert CTreeGrid in citry_ui.COMPONENTS
    html = _render(
        columns, rows, 'c-expanded="[\'root\']" selection="multiple" c-selected="[\'child\']" name="chosen"'
    )
    assert 'role="treegrid"' in html
    assert 'aria-rowcount="3"' in html
    assert 'aria-level="1"' in html
    assert 'aria-level="2"' in html
    assert 'aria-expanded="true"' in html
    assert 'aria-selected="true"' in html
    assert re.search(r'<input[^>]+name="chosen"[^>]+value="child"', html)


@pytest.mark.parametrize(
    ("columns", "rows", "attrs", "match"),
    [
        ([], [CTreeGridRow("x", "X", {})], "", "at least one"),
        ([CTreeGridColumn("a", "A")], [CTreeGridRow("x", "X", {"wrong": 1})], "", "exactly match"),
        (
            [CTreeGridColumn("a", "A")],
            [CTreeGridRow("x", "X", {"a": 1}, children=[CTreeGridRow("x", "Again", {"a": 2})])],
            "",
            "duplicated",
        ),
        ([CTreeGridColumn("a", "A")], [CTreeGridRow("x", "X", {"a": 1})], "c-expanded=\"['x']\"", "unknown or leaf"),
        (
            [CTreeGridColumn("a", "A")],
            [CTreeGridRow("x", "X", {"a": 1}, disabled=True)],
            'selection="multiple" c-selected="[\'x\']"',
            "disabled",
        ),
    ],
)
def test_invalid_data_fails(columns, rows, attrs: str, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _render(columns, rows, attrs)


def test_assets_docs_and_translations_cover_contract() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text()
    css = (root / "runtime.source.css").read_text()
    guide = (root / "api.md").read_text()
    reference = (root / "api.yml").read_text()
    for fragment in (
        "shiftKey",
        "ArrowLeft",
        "ArrowRight",
        "onExpandedChange",
        "onSelectionChange",
        "i18n.bind",
        "removeEventListener",
    ):
        assert fragment in js
    for fragment in ("prefers-reduced-motion", "forced-colors", "@media print"):
        assert fragment in css
    assert guide.count("<c-ui-demo ") == 6
    for suffix in ("expand", "collapse", "expanded", "collapsed", "selected", "unselected"):
        assert f"citry-ui-tree-grid-{suffix}" in reference
