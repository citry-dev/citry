from __future__ import annotations

import re

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CList, CListItem


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def test_semantic_unordered_and_ordered_lists():
    unordered = _render('<c-CList marker="disc"><c-CListItem>Moon</c-CListItem></c-CList>')
    ordered = _render(
        '<c-CList c-ordered="True" marker="decimal" c-start="3" c-reversed="True">'
        "<c-CListItem>Align</c-CListItem></c-CList>"
    )
    assert "<ul" in unordered
    assert "<li" in unordered
    assert "<ol" in ordered
    assert 'start="3"' in ordered
    assert "reversed" in ordered


def test_link_action_static_and_current_surfaces():
    html = _render(
        '<c-CList><c-CListItem href="/sky" c-current="True">Sky</c-CListItem>'
        '<c-CListItem c-action="True">Open</c-CListItem><c-CListItem>Static</c-CListItem></c-CList>'
    )
    assert re.search(r'<a[^>]+href="/sky"[^>]+aria-current="page"', html)
    assert re.search(r'<button[^>]+type="button"', html)
    assert '<div data-citry-ui-part="surface">' in html


def test_disabled_links_become_static_and_disabled_actions_remain_native_buttons():
    html = _render(
        '<c-CList><c-CListItem href="/sky" c-disabled="True">Sky</c-CListItem>'
        '<c-CListItem c-action="True" c-disabled="True">Open</c-CListItem></c-CList>'
    )
    assert 'href="/sky"' not in html
    assert re.search(r'<button[^>]+data-citry-ui-part="surface"[^>]+disabled', html)


def test_all_item_slots_render_owned_wrappers():
    html = _render(
        '<c-CList><c-CListItem><c-fill name="start">S</c-fill><c-fill name="default">Body</c-fill>'
        '<c-fill name="description">Description</c-fill><c-fill name="end">E</c-fill>'
        "</c-CListItem></c-CList>"
    )
    for part in ("start", "body", "description", "end"):
        assert f'data-citry-ui-part="{part}"' in html
    assert re.search(r'<div[^>]+data-citry-ui-part="body"', html)


@pytest.mark.parametrize(
    "source",
    [
        "<c-CList c-attrs=\"{'aria-label': 'Shadow name'}\"><c-CListItem>X</c-CListItem></c-CList>",
        "<c-CList><c-CListItem c-surface_attrs=\"{'aria-hidden': True}\">X</c-CListItem></c-CList>",
        "<c-CList><c-CListItem c-surface_attrs=\"{'aria-label': 'Shadow name'}\">X</c-CListItem></c-CList>",
    ],
)
def test_owned_accessibility_attributes_fail(source):
    with pytest.raises(ValueError, match="cannot"):
        _render(source)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        (
            "<c-CList c-attrs=\"{'v-bind:aria-label': 'name'}\"><c-CListItem>X</c-CListItem></c-CList>",
            "CList attrs cannot contain the Vue directive 'v-bind:aria-label'",
        ),
        (
            "<c-CList c-attrs=\"{'V-IF': 'shown'}\"><c-CListItem>X</c-CListItem></c-CList>",
            "CList attrs cannot contain the Vue directive 'V-IF'",
        ),
        (
            "<c-CList c-attrs=\"{'#default': ''}\"><c-CListItem>X</c-CListItem></c-CList>",
            "CList attrs cannot contain the Vue directive '#default'",
        ),
        (
            "<c-CList><c-CListItem c-attrs=\"{'v-for': 'row in rows'}\">X</c-CListItem></c-CList>",
            "CListItem attrs cannot contain the Vue directive 'v-for'",
        ),
        (
            "<c-CList><c-CListItem c-attrs=\"{':role': 'kind'}\">X</c-CListItem></c-CList>",
            "CListItem attrs cannot contain the Vue directive ':role'",
        ),
        (
            "<c-CList><c-CListItem c-surface_attrs=\"{'v-html': 'markup'}\">X</c-CListItem></c-CList>",
            "CListItem surface attrs cannot contain the Vue directive 'v-html'",
        ),
        (
            "<c-CList><c-CListItem c-surface_attrs=\"{'@click': 'open()'}\">X</c-CListItem></c-CList>",
            "CListItem surface attrs cannot contain the Vue directive '@click'",
        ),
        (
            "<c-CList><c-CListItem c-surface_attrs=\"{'.aria-hidden': 'hidden'}\">X</c-CListItem></c-CList>",
            "CListItem surface attrs cannot contain the Vue directive '.aria-hidden'",
        ),
    ],
)
def test_python_attrs_reject_vue_directives(source, message):
    # Python attrs are data; Vue bindings and listeners belong on the
    # component tag in a template, such as `<c-CListItem @click="open">`.
    with pytest.raises(ValueError, match=re.escape(message)):
        _render(source)


def test_attrs_without_vue_syntax_stay_ordinary_attributes():
    html = _render("<c-CList c-attrs=\"{'x-data': '{}'}\"><c-CListItem>X</c-CListItem></c-CList>")
    assert 'x-data="{}"' in html


@pytest.mark.parametrize(
    "source",
    [
        '<c-CList><c-CListItem href="/x" c-action="True">X</c-CListItem></c-CList>',
        '<c-CList><c-CListItem c-current="True">X</c-CListItem></c-CList>',
        '<c-CList c-start="2"><c-CListItem>X</c-CListItem></c-CList>',
        '<c-CList c-ordered="True" marker="disc"><c-CListItem>X</c-CListItem></c-CList>',
    ],
)
def test_invalid_contracts_fail(source):
    with pytest.raises(ValueError, match="CList"):
        _render(source)


def test_item_outside_list_fails():
    with pytest.raises(ValueError, match="inside CList"):
        _render("<c-CListItem>Loose</c-CListItem>")


def test_public_classes_have_zero_javascript():
    assert getattr(CList, "js", None) is None
    assert getattr(CListItem, "js", None) is None
