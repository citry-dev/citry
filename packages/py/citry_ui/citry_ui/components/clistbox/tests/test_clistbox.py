from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CListbox, CListboxGroup, CListboxOption
from citry_ui.quality.asset_sources import read_component_source_css


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


def _listbox(root: str = "") -> str:
    return (
        f'<c-CListbox label="Planets" {root}>'
        '<c-CListboxOption value="earth">Earth</c-CListboxOption>'
        '<c-CListboxOption value="mars" disabled>Mars</c-CListboxOption>'
        '<c-CListboxGroup label="Outer planets">'
        '<c-CListboxOption value="jupiter">Jupiter</c-CListboxOption>'
        '<c-CListboxOption value="saturn">Saturn</c-CListboxOption>'
        "</c-CListboxGroup>"
        "</c-CListbox>"
    )


def test_public_schemas_aliases_and_registration_are_exact() -> None:
    assert [item.name for item in fields(CListbox.Kwargs)] == [
        "label",
        "value",
        "multiple",
        "mandatory",
        "disabled",
        "loop",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
        "listbox_attrs",
    ]
    assert [item.name for item in fields(CListboxOption.Kwargs)] == [
        "value",
        "disabled",
        "text_value",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CListboxGroup.Kwargs)] == [
        "label",
        "class_",
        "style",
        "attrs",
    ]
    hints = get_type_hints(CListbox.Kwargs)
    assert hints["variant"] == citry_ui.CListboxVariant
    assert hints["size"] == citry_ui.CListboxSize
    assert CListbox in citry_ui.COMPONENTS
    assert CListboxOption in citry_ui.COMPONENTS
    assert CListboxGroup in citry_ui.COMPONENTS


def test_single_listbox_has_native_aria_selection_grouping_and_roving_focus() -> None:
    html = _render(_listbox('value="earth" variant="outline"'))
    root = _tag(html, "listbox-root")
    surface = _tag(html, "listbox")
    earth = _tag(html, "listbox-option", 0)
    mars = _tag(html, "listbox-option", 1)
    group = _tag(html, "listbox-group")
    assert 'data-variant="outline"' in root
    assert 'role="listbox"' in surface
    assert "aria-multiselectable" not in surface
    assert 'aria-selected="true"' in earth
    assert 'tabindex="0"' in earth
    assert 'aria-disabled="true"' in mars
    assert 'tabindex="-1"' in mars
    assert 'role="group"' in group
    assert "aria-labelledby=" in group


def test_multiple_listbox_reflects_all_selected_values() -> None:
    html = _render(_listbox("multiple c-value=\"['earth', 'saturn']\""))
    assert 'aria-multiselectable="true"' in _tag(html, "listbox")
    assert 'aria-selected="true"' in _tag(html, "listbox-option", 0)
    assert 'aria-selected="true"' in _tag(html, "listbox-option", 3)
    assert "data-multiple" in _tag(html, "listbox-root")


def test_option_regions_have_exact_accessible_relationships() -> None:
    html = _render(
        '<c-CListbox label="People">'
        '<c-CListboxOption value="ada" text_value="Ada Lovelace">'
        '<c-fill name="start"><span aria-hidden="true">AL</span></c-fill>'
        '<c-fill name="default">Ada Lovelace</c-fill>'
        '<c-fill name="description">Analytical engine</c-fill>'
        '<c-fill name="end">Available</c-fill>'
        "</c-CListboxOption>"
        "</c-CListbox>"
    )
    option = _tag(html, "listbox-option")
    assert "aria-labelledby=" in option
    assert "aria-describedby=" in option
    assert 'data-cui-listbox-text-value="Ada Lovelace"' in option
    assert 'aria-hidden="true"' in _tag(html, "listbox-option-start")
    assert 'aria-hidden="true"' in _tag(html, "listbox-option-end")


def test_root_surface_option_and_group_attrs_reach_their_destinations() -> None:
    html = _render(
        '<c-CListbox label="Letters" class_="brand" style="inline-size:20rem" '
        "c-attrs=\"{'data-test': 'root'}\" c-listbox_attrs=\"{'data-test': 'surface'}\">"
        "<c-CListboxGroup label=\"Latin\" c-attrs=\"{'data-test': 'group'}\">"
        '<c-CListboxOption value="a" class_="special" style="color:red" '
        "c-attrs=\"{'data-test': 'option'}\">A</c-CListboxOption>"
        "</c-CListboxGroup></c-CListbox>"
    )
    root = _tag(html, "listbox-root")
    surface = _tag(html, "listbox")
    group = _tag(html, "listbox-group")
    option = _tag(html, "listbox-option")
    assert 'class="cui-listbox brand"' in root
    assert 'style="inline-size: 20rem;"' in root
    assert 'data-test="root"' in root
    assert 'data-test="surface"' in surface
    assert 'data-test="group"' in group
    assert 'class="cui-listbox__option special"' in option
    assert 'style="color: red;"' in option
    assert 'data-test="option"' in option


@pytest.mark.parametrize(
    ("template", "message"),
    [
        (
            '<c-CListbox c-label="\'\'"><c-CListboxOption value="a">A</c-CListboxOption></c-CListbox>',
            "label must be nonempty",
        ),
        ('<c-CListbox label="Empty"></c-CListbox>', "requires 1 slot"),
        (
            '<c-CListbox label="Duplicate"><c-CListboxOption value="a">A</c-CListboxOption>'
            '<c-CListboxOption value="a">Again</c-CListboxOption></c-CListbox>',
            "unique",
        ),
        (_listbox('value="missing"'), "unknown Options"),
        (_listbox('multiple value="earth"'), "sequence of strings"),
        (_listbox("mandatory"), "requires an initial selected value"),
        (_listbox('variant="raised"'), "variant must be one of"),
        (
            '<c-CListbox label="Nested"><c-CListboxGroup label="A">'
            '<c-CListboxGroup label="B"><c-CListboxOption value="a">A</c-CListboxOption>'
            "</c-CListboxGroup></c-CListboxGroup></c-CListbox>",
            "cannot be nested",
        ),
    ],
)
def test_invalid_family_inputs_fail(template: str, message: str) -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError), match=message):
        _render(template)


def test_declarations_outside_listbox_and_unknown_collection_content_fail() -> None:
    with pytest.raises(ValueError, match="must be rendered directly inside"):
        _render('<c-CListboxOption value="a">A</c-CListboxOption>')
    with pytest.raises(ValueError, match="must be rendered directly inside"):
        _render('<c-CListboxGroup label="A"><span>A</span></c-CListboxGroup>')
    with pytest.raises(ValueError, match="documented noninteractive Listbox anatomy"):
        _render('<c-CListbox label="Wrong"><p>Wrong</p><c-CListboxOption value="a">A</c-CListboxOption></c-CListbox>')


def test_interactive_option_content_is_rejected_server_side() -> None:
    with pytest.raises(ValueError, match="interactive"):
        _render(
            '<c-CListbox label="Wrong"><c-CListboxOption value="a">'
            '<input value="nested"></c-CListboxOption></c-CListbox>'
        )


@pytest.mark.parametrize(
    "template",
    [
        _listbox("c-attrs=\"{'role': 'menu'}\""),
        _listbox("c-listbox_attrs=\"{':aria-label': 'name'}\""),
        (
            '<c-CListbox label="Letters"><c-CListboxOption value="a" '
            "c-attrs=\"{'tabindex': 4}\">A</c-CListboxOption></c-CListbox>"
        ),
        (
            '<c-CListbox label="Letters"><c-CListboxGroup label="Latin" '
            "c-attrs=\"{'x-show': 'visible'}\">"
            '<c-CListboxOption value="a">A</c-CListboxOption></c-CListboxGroup></c-CListbox>'
        ),
    ],
)
def test_owned_attrs_and_directives_are_rejected(template: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(template)


def test_css_includes_public_states_environment_rules_and_logical_layout() -> None:
    css = read_component_source_css("clistbox")
    assert "--cui-listbox-selected-background" in css
    assert 'grid-template-areas: "indicator start copy end"' in css
    assert "overflow-wrap: anywhere" in css
    assert "prefers-reduced-motion" in css
    assert "forced-colors" in css
    assert "@media print" in css


def test_output_escapes_hostile_label_and_values() -> None:
    html = _render(
        "<c-CListbox c-label=\"'Planets & <world>'\">"
        "<c-CListboxOption c-value=\"'earth&moon'\">Earth &amp; Moon</c-CListboxOption>"
        "</c-CListbox>"
    )
    assert "Planets &amp; &lt;world&gt;" in html
    assert 'data-value="earth&amp;moon"' in html
