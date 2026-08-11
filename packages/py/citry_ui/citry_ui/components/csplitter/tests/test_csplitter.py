from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CSplitter, CSplitterPanel


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


def _two_panels(root: str = "") -> str:
    return (
        f"<c-CSplitter {root}>"
        '<c-CSplitterPanel id="nav" label="Navigation">Navigation</c-CSplitterPanel>'
        '<c-CSplitterPanel id="main" label="Main">Main</c-CSplitterPanel>'
        "</c-CSplitter>"
    )


def test_public_schemas_and_aliases_are_exact() -> None:
    assert [item.name for item in fields(CSplitter.Kwargs)] == [
        "sizes",
        "orientation",
        "disabled",
        "keyboard_step",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CSplitterPanel.Kwargs)] == [
        "id",
        "label",
        "min_size",
        "max_size",
        "class_",
        "style",
        "attrs",
    ]
    hints = get_type_hints(CSplitter.Kwargs)
    assert hints["orientation"] == citry_ui.CSplitterOrientation
    assert hints["variant"] == citry_ui.CSplitterVariant
    assert hints["size"] == citry_ui.CSplitterSize
    assert CSplitter in citry_ui.COMPONENTS
    assert CSplitterPanel in citry_ui.COMPONENTS


def test_two_panel_server_anatomy_and_accessible_separator() -> None:
    html = _render(_two_panels('c-sizes="[30, 70]" variant="outline"'))
    root = _tag(html, "splitter")
    panels = [_tag(html, "panel", index) for index in range(2)]
    handle = _tag(html, "handle")
    assert root.startswith("<div")
    assert 'data-orientation="horizontal"' in root
    assert 'data-variant="outline"' in root
    assert 'role="group"' in panels[0]
    assert 'aria-label="Navigation"' in panels[0]
    assert 'style="flex: 30 1 0px;"' in panels[0]
    assert 'data-size-percent="70.0"' in panels[1]
    assert 'role="separator"' in handle
    assert 'tabindex="0"' in handle
    assert 'aria-label="Navigation / Main"' in handle
    assert 'aria-orientation="vertical"' in handle
    assert 'aria-valuenow="30.0"' in handle
    panel_ids = [re.search(r'id="([^"]+)"', panel).group(1) for panel in panels]  # type: ignore[union-attr]
    assert f'aria-controls="{panel_ids[0]} {panel_ids[1]}"' in handle


def test_three_panels_create_two_adjacent_handles() -> None:
    html = _render(
        '<c-CSplitter c-sizes="[20, 45, 35]">'
        '<c-CSplitterPanel id="a" label="A">A</c-CSplitterPanel>'
        '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel>'
        '<c-CSplitterPanel id="c" label="C">C</c-CSplitterPanel>'
        "</c-CSplitter>"
    )
    assert len(re.findall('data-citry-ui-part="panel"', html.split("<script", 1)[0])) == 3
    assert len(re.findall('data-citry-ui-part="handle"', html.split("<script", 1)[0])) == 2
    assert 'aria-label="A / B"' in _tag(html, "handle", 0)
    assert 'aria-label="B / C"' in _tag(html, "handle", 1)


def test_vertical_layout_uses_horizontal_separator() -> None:
    html = _render(_two_panels('orientation="vertical"'))
    assert 'data-orientation="vertical"' in _tag(html, "splitter")
    assert 'aria-orientation="horizontal"' in _tag(html, "handle")


def test_equal_sizes_are_stable_without_explicit_vector() -> None:
    html = _render(_two_panels())
    assert 'style="flex: 50 1 0px;"' in _tag(html, "panel", 0)
    assert 'style="flex: 50 1 0px;"' in _tag(html, "panel", 1)


def test_panel_content_can_nest_a_fresh_splitter() -> None:
    html = _render(
        "<c-CSplitter>"
        '<c-CSplitterPanel id="outer-a" label="Outer A">A</c-CSplitterPanel>'
        '<c-CSplitterPanel id="outer-b" label="Outer B"><c-CSplitter orientation="vertical">'
        '<c-CSplitterPanel id="inner-a" label="Inner A">IA</c-CSplitterPanel>'
        '<c-CSplitterPanel id="inner-b" label="Inner B">IB</c-CSplitterPanel>'
        "</c-CSplitter></c-CSplitterPanel></c-CSplitter>"
    )
    assert len(re.findall('data-citry-ui-part="splitter"', html.split("<script", 1)[0])) == 2
    assert 'data-panel-id="inner-a"' in html


def test_root_and_panel_attrs_reach_concrete_elements() -> None:
    html = _render(
        '<c-CSplitter class_="brand" style="block-size:20rem" c-attrs="{\'data-test\': \'root\'}">'
        '<c-CSplitterPanel id="a" label="A" class_="primary" style="color:red" '
        "c-attrs=\"{'data-test': 'panel'}\">A</c-CSplitterPanel>"
        '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel></c-CSplitter>'
    )
    root = _tag(html, "splitter")
    panel = _tag(html, "panel")
    assert 'class="cui-splitter brand"' in root
    assert 'style="block-size: 20rem;"' in root
    assert 'data-test="root"' in root
    assert 'class="cui-splitter__panel primary"' in panel
    assert "color: red" in panel
    assert "flex: 50 1 0px" in panel
    assert 'data-test="panel"' in panel


@pytest.mark.parametrize(
    ("template", "message"),
    [
        ('<c-CSplitter><c-CSplitterPanel id="a" label="A">A</c-CSplitterPanel></c-CSplitter>', "at least two"),
        (
            '<c-CSplitter><c-CSplitterPanel id="a" label="A">A</c-CSplitterPanel>'
            '<c-CSplitterPanel id="a" label="B">B</c-CSplitterPanel></c-CSplitter>',
            "unique",
        ),
        (_two_panels('c-sizes="[100]"'), "entries for 2 panels"),
        (_two_panels('c-sizes="[30, 60]"'), "total 100"),
        (
            '<c-CSplitter c-sizes="[15, 85]"><c-CSplitterPanel id="a" label="A" c-min_size="20">A</c-CSplitterPanel>'
            '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel></c-CSplitter>',
            "outside",
        ),
        (
            '<c-CSplitter><c-CSplitterPanel id="a" label="A" c-min_size="60" c-max_size="50">A</c-CSplitterPanel>'
            '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel></c-CSplitter>',
            "cannot exceed",
        ),
        (_two_panels('orientation="diagonal"'), "orientation must be one of"),
        (_two_panels('c-keyboard_step="0"'), "between 0.1"),
        (
            '<c-CSplitter><c-CSplitterPanel id="bad id" label="A">A</c-CSplitterPanel>'
            '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel></c-CSplitter>',
            "ASCII whitespace",
        ),
    ],
)
def test_invalid_family_inputs_fail(template: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(template)


def test_panel_outside_splitter_and_unknown_direct_content_fail() -> None:
    with pytest.raises(ValueError, match="must be rendered directly inside CSplitter"):
        _render('<c-CSplitterPanel id="a" label="A">A</c-CSplitterPanel>')
    with pytest.raises(ValueError, match="only CSplitterPanel declarations"):
        _render(
            '<c-CSplitter><p>Wrong</p><c-CSplitterPanel id="a" label="A">A</c-CSplitterPanel>'
            '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel></c-CSplitter>'
        )


@pytest.mark.parametrize(
    "template",
    [
        _two_panels("c-attrs=\"{'role': 'group'}\""),
        _two_panels("c-attrs=\"{':data-orientation': 'orientation'}\""),
        _two_panels("c-attrs=\"{'x-html': 'content'}\""),
        '<c-CSplitter><c-CSplitterPanel id="a" label="A" c-attrs="{\'role\': \'region\'}">A</c-CSplitterPanel>'
        '<c-CSplitterPanel id="b" label="B">B</c-CSplitterPanel></c-CSplitter>',
    ],
)
def test_owned_attrs_and_directives_are_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(template)


def test_css_exposes_public_variables_environment_rules_and_parts() -> None:
    html = _render(_two_panels(), include_css=True)
    for token in (
        "--cui-splitter-min-block-size",
        "--cui-splitter-handle-size",
        "--cui-splitter-handle-active-color",
        "prefers-reduced-motion",
        "forced-colors",
        "@media print",
        'data-citry-ui-part="handle-grip"',
    ):
        assert token in html
