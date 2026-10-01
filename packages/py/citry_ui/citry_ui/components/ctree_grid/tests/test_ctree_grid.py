from __future__ import annotations

import json
import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTreeGrid, CTreeGridCell, CTreeGridColumn, CTreeGridRow


def _render(columns, rows, attrs: str = "", *, static_fallback: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {"columns": columns, "rows": rows}

        template = f'<c-CTreeGrid c-columns="columns" c-rows="rows" label="Hierarchy" {attrs} />'

    page = Page()
    return page.render().serialize(security_javascript="omit") if static_fallback else str(page)


def _manifest(html: str) -> dict[str, object]:
    match = re.search(
        r'<script type="application/json" data-citry-vue-document="[^"]*"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    return json.loads(match.group(1))["manifest"]


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
        columns,
        rows,
        'c-expanded="[\'root\']" selection="multiple" c-selected="[\'child\']" name="chosen"',
        static_fallback=True,
    )
    assert 'role="treegrid"' in html
    assert 'aria-rowcount="3"' in html
    assert 'aria-level="1"' in html
    assert 'aria-level="2"' in html
    assert 'aria-expanded="true"' in html
    assert 'aria-selected="true"' in html
    for role in ("rowgroup", "row", "columnheader", "gridcell"):
        assert f'role="{role}"' not in html
    assert re.search(r'<input[^>]+name="chosen"[^>]+value="child"', html)


def test_server_defaults_are_namespaced_away_from_vue_props() -> None:
    columns, rows = _data()
    html = _render(columns, rows, 'disabled selection="multiple"')
    occurrence = next(item for item in _manifest(html)["occurrences"] if item["typeKey"].startswith("CTreeGrid_"))
    server_data = occurrence["serverData"]
    assert set(server_data) == {"serverDefaults"}
    assert set(server_data["serverDefaults"]) == {
        "expanded",
        "selection",
        "selected",
        "name",
        "form",
        "disabled",
        "catalog",
        "labels",
    }


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


@pytest.mark.parametrize(
    ("place", "attribute", "owner"),
    [
        ("root", ":role", "CTreeGrid attrs"),
        ("root", "v-if", "CTreeGrid attrs"),
        ("root", "V-IF", "CTreeGrid attrs"),
        ("root", "@keydown", "CTreeGrid attrs"),
        ("row", "v-bind:aria-level", "CTreeGrid Row 'x' attrs"),
        ("row", "#default", "CTreeGrid Row 'x' attrs"),
        ("column", "v-html", "CTreeGrid Column 'a' cell_attrs"),
        ("cell", ".aria-colindex", "CTreeGrid Row 'x' Cell 'a' attrs"),
    ],
)
def test_python_attrs_reject_vue_directives(place: str, attribute: str, owner: str) -> None:
    # Directive syntax in Python data could rebind owned state or change the
    # structure, so the message names the exact mapping that held it.
    attrs = {attribute: "x"}
    column = CTreeGridColumn("a", "A", cell_attrs=attrs if place == "column" else None)
    cell = CTreeGridCell(1, attrs=attrs) if place == "cell" else 1
    row = CTreeGridRow("x", "X", {"a": cell}, attrs=attrs if place == "row" else None)
    root_attrs = f"c-attrs=\"{{'{attribute}': 'x'}}\"" if place == "root" else ""
    with pytest.raises(ValueError, match=re.escape(f"{owner} cannot contain the Vue directive {attribute!r}")):
        _render([column], [row], root_attrs)


def test_attrs_without_vue_syntax_stay_ordinary_attributes() -> None:
    # Names outside Vue's directive syntax are plain HTML attributes, even
    # when they resemble another framework's directives.
    columns, rows = _data()
    html = _render(columns, rows, "c-attrs=\"{'x-data': '{}', 'hx-get': '/rows'}\"", static_fallback=True)

    root = re.search(r'<[^>]+data-citry-ui-part="tree-grid"[^>]*>', html)
    assert root is not None
    assert 'x-data="{}"' in root.group(0)
    assert 'hx-get="/rows"' in root.group(0)


def test_assets_docs_and_translations_cover_contract() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text()
    css = (root / "runtime.source.css").read_text()
    guide = (root / "api.md").read_text()
    reference = (root / "api.yml").read_text()
    for fragment in (
        "onServerRender",
        "Citry.vue.watchEffect",
        "shiftKey",
        "ArrowLeft",
        "ArrowRight",
        "onExpandedChange",
        "onSelectionChange",
        "i18n.bind",
        "removeEventListener",
    ):
        assert fragment in js
    assert "init:" not in js
    for fragment in ("prefers-reduced-motion", "forced-colors", "@media print"):
        assert fragment in css
    assert guide.count("<c-ui-demo ") == 6
    for suffix in ("expand", "collapse", "expanded", "collapsed", "selected", "unselected"):
        assert f"citry-ui-tree-grid-{suffix}" in reference
