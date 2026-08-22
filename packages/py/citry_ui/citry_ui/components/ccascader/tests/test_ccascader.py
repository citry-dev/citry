# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CCascader, CCascaderOption


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    return str(Page())


_OPTIONS = """
  <c-CCascaderOption value="world" label="World">
    <c-CCascaderOption value="europe" label="Europe"><c-CCascaderOption value="prague" label="Prague" /></c-CCascaderOption>
    <c-CCascaderOption value="asia" label="Asia"><c-CCascaderOption value="tokyo" label="Tokyo" /></c-CCascaderOption>
  </c-CCascaderOption>
"""


def test_schemas_registration_path_labels_and_native_inputs() -> None:
    assert [item.name for item in fields(CCascader.Kwargs)][:8] == [
        "value",
        "id",
        "aria_label",
        "aria_labelledby",
        "name",
        "form",
        "placeholder",
        "separator",
    ]
    assert [item.name for item in fields(CCascaderOption.Kwargs)] == [
        "value",
        "label",
        "disabled",
        "class_",
        "style",
        "attrs",
    ]
    assert CCascader in citry_ui.COMPONENTS
    assert CCascaderOption in citry_ui.COMPONENTS
    html = _render(
        f'<p id="place-label">Destination</p><c-CCascader aria_labelledby="place-label" name="place" form="profile" c-value="[\'world\',\'europe\',\'prague\']">{_OPTIONS}</c-CCascader>'
    )
    assert "World / Europe / Prague" in html
    assert len(re.findall(r'<input[^>]+name="place"', html)) == 3
    assert 'value="world"' in html
    assert 'value="prague"' in html
    assert 'form="profile"' in html
    assert 'aria-haspopup="tree"' in html
    assert 'aria-labelledby="place-label"' in html
    assert html.count('role="treeitem"') >= 5
    assert 'aria-level="3"' in html
    assert 'aria-posinset="1"' in html
    assert 'aria-setsize="2"' in html
    assert "aria-owns=" in html


def test_empty_hierarchy_and_unselected_server_focus_are_useful_without_client_runtime() -> None:
    empty = _render('<c-CCascader aria_label="Empty taxonomy" />')
    assert "No options" in empty
    assert 'aria-label="Empty taxonomy"' in empty
    assert re.search(r'<ul[^>]+hidden[^>]+data-citry-ui-part="tree"', empty)

    options = _render(f"<c-CCascader>{_OPTIONS}</c-CCascader>")
    world = re.search(r'<li[^>]+data-value="world"[^>]*>', options)
    assert world is not None
    assert 'tabindex="0"' in world.group(0)


def test_parent_selection_policy_and_explicit_messages() -> None:
    with pytest.raises(ValueError, match="must end at a leaf"):
        _render(f"<c-CCascader c-value=\"['world']\">{_OPTIONS}</c-CCascader>")
    html = _render(
        f'<c-CCascader c-change_on_select="True" c-value="[\'world\']" placeholder="Pick" selected_label="Path: {{path}}">{_OPTIONS}</c-CCascader>'
    )
    assert "Path: World" in html


@pytest.mark.parametrize(
    ("source", "match"),
    [
        ("<c-CCascader><p>wrong</p></c-CCascader>", "only nested"),
        (
            '<c-CCascader><c-CCascaderOption value="x" label="X" /><c-CCascaderOption value="x" label="Y" /></c-CCascader>',
            "duplicated",
        ),
        (f"<c-CCascader c-value=\"['missing']\">{_OPTIONS}</c-CCascader>", "not one continuous"),
        ('<c-CCascader c-disabled="1"><c-CCascaderOption value="x" label="X" /></c-CCascader>', "must be a bool"),
        (
            '<c-CCascader selected_label="Selected"><c-CCascaderOption value="x" label="X" /></c-CCascader>',
            "must contain",
        ),
    ],
)
def test_invalid_composition_and_values_fail(source: str, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _render(source)


def test_assets_docs_and_translations_cover_contract() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text(encoding="utf8")
    css = (root / "runtime.source.css").read_text(encoding="utf8")
    guide = (root / "api.md").read_text(encoding="utf8")
    reference = (root / "api.yml").read_text(encoding="utf8")
    for fragment in ("ArrowRight", "ArrowLeft", "typeBuffer", "onValueChange", "removeEventListener"):
        assert fragment in js
    assert "i18n.bind" in js
    for fragment in ("prefers-reduced-motion", "forced-colors", "@media print"):
        assert fragment in css
    assert guide.count("<c-ui-demo ") == 6
    for suffix in ("placeholder", "empty", "selected"):
        assert f"citry-ui-cascader-{suffix}" in reference
