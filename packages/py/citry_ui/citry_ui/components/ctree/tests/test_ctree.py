from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTree, CTreeItem


def _render(template: str, *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("<c-css />" if include_css else "")

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def _tag(html: str, part: str, index: int = 0) -> str:
    tags = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(tags) > index
    return tags[index]


def _tree(root: str = "") -> str:
    return (
        f'<c-CTree label="Files" {root}>'
        '<c-CTreeItem value="docs" label="Documents">'
        '<c-CTreeItem value="readme" label="Readme" />'
        '<c-CTreeItem value="guide" label="Guide" />'
        "</c-CTreeItem>"
        '<c-CTreeItem value="photos" label="Photos" />'
        "</c-CTree>"
    )


def test_public_schemas_and_aliases_are_exact() -> None:
    assert [item.name for item in fields(CTree.Kwargs)] == [
        "label",
        "expanded",
        "selected",
        "selection_mode",
        "disabled",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CTreeItem.Kwargs)] == [
        "value",
        "label",
        "disabled",
        "class_",
        "style",
        "attrs",
    ]
    hints = get_type_hints(CTree.Kwargs)
    assert hints["selection_mode"] == citry_ui.CTreeSelectionMode
    assert hints["variant"] == citry_ui.CTreeVariant
    assert hints["size"] == citry_ui.CTreeSize
    assert CTree in citry_ui.COMPONENTS
    assert CTreeItem in citry_ui.COMPONENTS


def test_server_tree_anatomy_expansion_selection_and_roving_focus() -> None:
    html = _render(_tree('c-expanded="[\'docs\']" c-selected="[\'readme\']" variant="outline"'))
    root = _tag(html, "tree")
    branch = _tag(html, "item", 0)
    selected = _tag(html, "item", 1)
    leaf = _tag(html, "item", 2)
    group = _tag(html, "group")
    assert 'role="tree"' in root
    assert 'aria-label="Files"' in root
    assert 'data-selection-mode="single"' in root
    assert 'role="treeitem"' in branch
    assert 'aria-expanded="true"' in branch
    assert 'data-level="1"' in branch
    assert 'aria-selected="true"' in selected
    assert 'tabindex="0"' in selected
    assert 'data-level="2"' in selected
    assert "aria-expanded" not in leaf
    assert 'role="group"' in group
    assert "hidden" not in group


def test_collapsed_branch_hides_and_inerts_group() -> None:
    html = _render(_tree())
    assert 'aria-expanded="false"' in _tag(html, "item", 0)
    group = _tag(html, "group")
    assert "hidden" in group
    assert "inert" in group


def test_selection_modes_have_exact_aria_surface() -> None:
    none_html = _render(_tree('selection_mode="none"'))
    assert "aria-selected" not in _tag(none_html, "item", 0)
    multiple = _render(_tree("selection_mode=\"multiple\" c-selected=\"['docs', 'photos']\""))
    assert 'aria-selected="true"' in _tag(multiple, "item", 0)
    assert 'aria-selected="true"' in _tag(multiple, "item", 3)


def test_disabled_root_and_item_are_reflected_without_native_controls() -> None:
    html = _render(
        '<form><c-CTree label="Files" disabled>'
        '<c-CTreeItem value="a" label="A" /><c-CTreeItem value="b" label="B" disabled />'
        "</c-CTree><button type=submit>Submit</button></form>"
    )
    assert "data-disabled" in _tag(html, "tree")
    assert 'aria-disabled="true"' in _tag(html, "item", 0)
    assert 'tabindex="-1"' in _tag(html, "item", 0)
    assert "<button" in html


def test_root_and_item_attrs_reach_concrete_elements() -> None:
    html = _render(
        '<c-CTree label="Files" class_="brand" style="inline-size:20rem" c-attrs="{\'data-test\': \'root\'}">'
        '<c-CTreeItem value="a" label="A" class_="special" style="color:red" '
        "c-attrs=\"{'data-test': 'item'}\" />"
        "</c-CTree>"
    )
    root = _tag(html, "tree")
    item = _tag(html, "item")
    assert 'class="cui-tree brand"' in root
    assert 'style="inline-size: 20rem;"' in root
    assert 'data-test="root"' in root
    assert 'class="cui-tree__item special"' in item
    assert 'style="color: red;"' in item
    assert 'data-test="item"' in item


@pytest.mark.parametrize(
    ("template", "message"),
    [
        ('<c-CTree c-label="\'\'"><c-CTreeItem value="a" label="A" /></c-CTree>', "label must be nonempty"),
        ('<c-CTree label="Files"></c-CTree>', "requires 1 slot"),
        (
            '<c-CTree label="Files"><c-CTreeItem value="a" label="A" /><c-CTreeItem value="a" label="B" /></c-CTree>',
            "unique",
        ),
        (_tree("c-expanded=\"['photos']\""), "unknown or leaf"),
        (_tree("c-selected=\"['missing']\""), "unknown Items"),
        (_tree('selection_mode="none" c-selected="[\'docs\']"'), "must be empty"),
        (_tree("selection_mode=\"single\" c-selected=\"['docs', 'photos']\""), "at most one"),
        (
            '<c-CTree label="Files"><c-CTreeItem value="bad id" label="Bad" /></c-CTree>',
            "ASCII whitespace",
        ),
        (_tree('variant="raised"'), "variant must be one of"),
    ],
)
def test_invalid_family_inputs_fail(template: str, message: str) -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError), match=message):
        _render(template)


def test_item_outside_tree_and_unknown_collection_content_fail() -> None:
    with pytest.raises(ValueError, match="must be rendered directly inside"):
        _render('<c-CTreeItem value="a" label="A" />')
    with pytest.raises(ValueError, match="documented Tree declaration anatomy"):
        _render('<c-CTree label="Files"><p>Wrong</p><c-CTreeItem value="a" label="A" /></c-CTree>')
    with pytest.raises(ValueError, match="documented Tree declaration anatomy"):
        _render(
            '<c-CTree label="Files"><c-CTreeItem value="a" label="A">'
            '<span>Wrong</span><c-CTreeItem value="b" label="B" /></c-CTreeItem></c-CTree>'
        )


@pytest.mark.parametrize(
    "template",
    [
        _tree("c-attrs=\"{'role': 'listbox'}\""),
        _tree("c-attrs=\"{':data-selection-mode': 'mode'}\""),
        _tree("c-attrs=\"{'x-html': 'content'}\""),
        '<c-CTree label="Files"><c-CTreeItem value="a" label="A" c-attrs="{\'aria-expanded\': \'true\'}" /></c-CTree>',
    ],
)
def test_owned_attrs_and_directives_are_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(template)


def test_css_exposes_public_variables_environment_rules_and_parts() -> None:
    html = _render(_tree(), include_css=True)
    for token in (
        "--cui-tree-indent",
        "--cui-tree-selected-background",
        "--cui-tree-focus-color",
        "prefers-reduced-motion",
        "forced-colors",
        "@media print",
        'data-citry-ui-part="group"',
    ):
        assert token in html
