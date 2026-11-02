# ruff: noqa: E501 - embedded Citry templates remain readable as authored HTML

from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CCascader, CCascaderOption


def _render(source: str, *, static_fallback: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    page = Page()
    return page.render().serialize(security_javascript="omit") if static_fallback else str(page)


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
    source = f'<p id="place-label">Destination</p><c-CCascader aria_labelledby="place-label" name="place" form="profile" c-value="[\'world\',\'europe\',\'prague\']">{_OPTIONS}</c-CCascader>'
    html = _render(source, static_fallback=True)
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
    empty = _render('<c-CCascader aria_label="Empty taxonomy" />', static_fallback=True)
    assert "No options" in empty
    # `aria_label` becomes a hidden element; the trigger's name is that label
    # followed by the visible value (WCAG 2.5.3).
    assert re.search(r'<span id="([^"]+)-aria-label" hidden>Empty taxonomy</span>', empty)
    assert re.search(r'aria-labelledby="([^"]+)-aria-label \1-value"', empty)
    assert re.search(r'<ul[^>]+hidden[^>]+data-citry-ui-part="tree"', empty)

    options = _render(f"<c-CCascader>{_OPTIONS}</c-CCascader>", static_fallback=True)
    world = re.search(r'<li[^>]+data-value="world"[^>]*>', options)
    assert world is not None
    assert 'tabindex="0"' in world.group(0)


@pytest.mark.parametrize(
    ("label_attrs", "trigger_name", "tree_name", "hidden_label"),
    [
        ('aria_labelledby="ext"', "ext c-value", "ext", False),
        ('aria_label="Place"', "c-aria-label c-value", "c-aria-label", True),
        ("", None, "c-trigger", False),
        # `aria_labelledby` wins, so the hidden label would be unused and is not rendered.
        ('aria_label="Place" aria_labelledby="ext"', "ext c-value", "ext", False),
    ],
    ids=["labelledby", "label", "neither", "both"],
)
def test_trigger_and_tree_names_follow_the_label_given(
    label_attrs: str, trigger_name: str | None, tree_name: str, hidden_label: bool
) -> None:
    html = _render(f'<c-CCascader id="c" {label_attrs}>{_OPTIONS}</c-CCascader>', static_fallback=True)

    trigger = re.search(r'<button[^>]*data-citry-ui-part="trigger"[^>]*>', html)
    tree = re.search(r'<ul role="tree"[^>]*data-citry-ui-part="tree"[^>]*>', html)
    assert trigger is not None
    assert tree is not None
    # Without a label the trigger keeps the name its visible content gives it.
    if trigger_name is None:
        assert "aria-labelledby" not in trigger.group(0)
    else:
        assert f'aria-labelledby="{trigger_name}"' in trigger.group(0)
    assert f'aria-labelledby="{tree_name}"' in tree.group(0)
    # The hidden label exists only when it is the label in use, and its id
    # never appears twice.
    assert html.count('id="c-aria-label"') == (1 if hidden_label else 0)
    assert (re.search(r'<span id="c-aria-label" hidden>Place</span>', html) is not None) is hidden_label
    ids = re.findall(r'\sid="([^"]+)"', html)
    assert len(ids) == len(set(ids))


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
        (
            '<c-CCascader c-disabled="1"><c-CCascaderOption value="x" label="X" /></c-CCascader>',
            r"CCascader\.Kwargs\.disabled expects bool",
        ),
        (
            '<c-CCascader selected_label="Selected"><c-CCascaderOption value="x" label="X" /></c-CCascader>',
            "must contain",
        ),
    ],
)
def test_invalid_composition_and_values_fail(source: str, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _render(source)


@pytest.mark.parametrize(
    ("owner", "attribute", "message"),
    [
        ("CCascader", "role", "cannot override owned attribute"),
        ("CCascader", "data-citry-morph", "Citry runtime attribute"),
        ("CCascader", ":aria-label", "CCascader attrs cannot contain the Vue directive"),
        ("CCascader", "v-if", "Vue directive"),
        ("CCascader", "V-IF", "Vue directive"),
        ("CCascader", "@click", "Vue directive"),
        ("CCascaderOption", "aria-selected", "cannot override owned attribute"),
        ("CCascaderOption", "v-bind:aria-selected", "CCascaderOption attrs cannot contain the Vue directive"),
        ("CCascaderOption", "v-for", "Vue directive"),
        ("CCascaderOption", "#default", "Vue directive"),
    ],
)
def test_attrs_reject_owned_runtime_and_vue_directive_names(owner: str, attribute: str, message: str) -> None:
    attrs = f"c-attrs=\"{{'{attribute}': 'x'}}\""
    root_attrs, option_attrs = (attrs, "") if owner == "CCascader" else ("", attrs)
    source = f'<c-CCascader aria_label="Places" {root_attrs}><c-CCascaderOption value="x" label="X" {option_attrs} /></c-CCascader>'
    with pytest.raises(ValueError, match=message):
        _render(source)


def test_attrs_without_vue_syntax_stay_ordinary_attributes() -> None:
    source = (
        "<c-CCascader aria_label=\"Places\" c-attrs=\"{'x-if': 'root'}\">"
        '<c-CCascaderOption value="x" label="X" c-attrs="{\'x-show\': \'option\'}" />'
        "</c-CCascader>"
    )
    html = _render(source, static_fallback=True)
    assert 'x-if="root"' in html
    assert 'x-show="option"' in html


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
