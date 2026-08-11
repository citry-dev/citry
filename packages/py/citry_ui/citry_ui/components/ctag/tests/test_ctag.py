from __future__ import annotations

import re
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component


def _render(source: str, data: dict[str, object] | None = None) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return data or {}

    return str(Page())


def _markup(html: str) -> str:
    start = html.find('<div class="cui-tag-group"')
    end = html.find("<script", start)
    return html[start:end]


def test_descriptive_group_uses_native_list_semantics() -> None:
    html = _render(
        '<c-CTagGroup label="Topics"><c-CTag value="css">CSS</c-CTag><c-CTag value="html">HTML</c-CTag></c-CTagGroup>'
    )
    markup = _markup(html)
    assert 'role="list"' in markup
    assert markup.count('role="listitem"') == 2
    assert 'data-selection-mode="none"' in markup
    assert 'data-citry-ui-part="group-label"' in markup
    assert "aria-selected" not in markup


def test_interactive_group_has_grid_relationships_and_form_safe_remove_buttons() -> None:
    html = _render(
        '<c-CTagGroup label="Topics" selection_mode="multiple" '
        "c-value=\"['css']\" removable actionable>"
        '<c-CTag value="css">CSS</c-CTag>'
        '<c-CTag value="html">HTML</c-CTag>'
        "</c-CTagGroup>"
    )
    markup = _markup(html)
    assert 'role="grid"' in markup
    assert markup.count('role="row"') == 2
    assert markup.count('role="gridcell"') == 2
    assert markup.count('type="button"') == 2
    assert markup.count('aria-selected="true"') == 1
    assert markup.count('aria-selected="false"') == 1
    assert markup.count('tabindex="0"') == 1
    assert markup.count('tabindex="-1"') >= 3
    assert re.search(r'aria-labelledby="[^\"]+-remove [^\"]+-label"', markup)


def test_named_label_description_start_and_root_destinations_render() -> None:
    html = _render(
        '<c-CTagGroup label="Fallback" class_="group-extra" c-attrs="{\'data-test\': \'group\'}">'
        '<c-fill name="label"><strong>Visible topics</strong></c-fill>'
        '<c-fill name="description">Choose a topic.</c-fill>'
        '<c-fill name="default">'
        '<c-CTag value="css" class_="tag-extra" c-attrs="{\'data-test\': \'tag\'}">'
        '<c-fill name="start"><span>★</span></c-fill>'
        '<c-fill name="default">CSS</c-fill>'
        "</c-CTag>"
        "</c-fill>"
        "</c-CTagGroup>"
    )
    assert "Visible topics" in html
    assert "Fallback" not in html
    assert "Choose a topic." in html
    assert 'aria-describedby="' in html
    assert 'data-citry-ui-part="start"' in html
    assert 'data-test="group"' in html
    assert "group-extra" in html
    assert 'data-test="tag"' in html
    assert "tag-extra" in html


def test_labelled_collection_may_settle_empty() -> None:
    html = _render(
        '<c-CTagGroup label="Empty"><c-CTag c-for="value in []" c-value="value">{{ value }}</c-CTag></c-CTagGroup>'
    )
    markup = _markup(html)
    assert 'role="list"' in markup
    assert 'data-citry-ui-part="tag"' not in markup


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('<c-CTag value="x">X</c-CTag>', "inside CTagGroup"),
        (
            '<c-CTagGroup label="Duplicate"><c-CTag value="x">One</c-CTag>'
            '<c-CTag value="x">Two</c-CTag></c-CTagGroup>',
            "unique",
        ),
        (
            '<c-CTagGroup label="Unknown" selection_mode="single" value="missing">'
            '<c-CTag value="x">X</c-CTag></c-CTagGroup>',
            "unknown",
        ),
        (
            '<c-CTagGroup label="Invalid" c-mandatory="True"><c-CTag value="x">X</c-CTag></c-CTagGroup>',
            "selectable",
        ),
        (
            '<c-CTagGroup label="Invalid" selection_mode="multiple" c-mandatory="True">'
            '<c-CTag value="x">X</c-CTag></c-CTagGroup>',
            "initial value",
        ),
        (
            '<c-CTagGroup label="Nested"><c-CTag value="x"><c-CTag value="y">Y</c-CTag></c-CTag></c-CTagGroup>',
            "inside CTagGroup",
        ),
    ],
)
def test_invalid_composition_and_values_fail(source: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _render(source)


@pytest.mark.parametrize(
    "attrs",
    [
        {"role": "button"},
        {"tabindex": 0},
        {"aria-hidden": "true"},
        {":data-disabled": "bad"},
        {"x-html": "bad"},
        {"data-citry-private": "bad"},
    ],
)
def test_owned_group_and_tag_attrs_are_rejected(attrs: dict[str, object]) -> None:
    group_source = '<c-CTagGroup label="Topics" c-attrs="attrs"><c-CTag value="x">X</c-CTag></c-CTagGroup>'
    tag_source = '<c-CTagGroup label="Topics"><c-CTag value="x" c-attrs="attrs">X</c-CTag></c-CTagGroup>'
    with pytest.raises(ValueError, match="cannot"):
        _render(group_source, {"attrs": attrs})
    with pytest.raises(ValueError, match="cannot"):
        _render(tag_source, {"attrs": attrs})


def test_public_types_and_runtime_type_hints_resolve() -> None:
    assert get_type_hints(citry_ui.CTagGroup.Kwargs)["selection_mode"] == citry_ui.CTagSelectionMode
    assert get_type_hints(citry_ui.CTag.Kwargs)["value"] is str
    assert citry_ui.CTagGroup in citry_ui.__citry_library__.components
    assert citry_ui.CTag in citry_ui.__citry_library__.components
