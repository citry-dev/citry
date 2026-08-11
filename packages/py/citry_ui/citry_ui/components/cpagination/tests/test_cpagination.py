from __future__ import annotations

import re

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui.components.cpagination.cpagination import _range


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def test_compact_range_expands_single_gaps():
    assert _range(5, 3, 0, 1) == (1, 2, 3, 4, 5)
    assert _range(20, 10, 1, 1) == (1, "ellipsis", 9, 10, 11, "ellipsis", 20)


def test_native_links_and_current_page_are_exact():
    html = _render('<c-CPagination c-pages="20" c-page="10" href="?page={page}" />')
    assert "<nav" in html
    assert 'aria-label="Pagination"' in html
    assert 'href="?page=10"' in html
    assert 'aria-current="page"' in html
    assert len(re.findall(r'<span[^>]+data-citry-ui-part="ellipsis"', html)) == 2


def test_button_mode_edges_and_unavailable_controls():
    html = _render('<c-CPagination c-pages="4" c-page="1" c-show_edges="True" />')
    assert html.count('data-kind="first"') == 1
    assert html.count('data-kind="last"') == 1
    first = re.search(r'<button[^>]+data-kind="first"[^>]*>', html)
    assert first is not None
    assert "disabled" in first.group(0)


@pytest.mark.parametrize(
    "source",
    [
        '<c-CPagination c-pages="0" />',
        '<c-CPagination c-pages="4" c-page="5" />',
        '<c-CPagination c-pages="4" href="?p=x" />',
        '<c-CPagination c-pages="4" page_label="Page" />',
        '<c-CPagination c-pages="4" c-siblings="11" />',
    ],
)
def test_invalid_inputs_fail(source):
    with pytest.raises(ValueError, match="CPagination"):
        _render(source)


def test_owned_attrs_fail():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = '<c-CPagination c-pages="4" c-attrs="attrs" />'

        def template_data(self, kwargs, slots):
            return {"attrs": {"aria-label": "bad"}}

    with pytest.raises(ValueError, match="cannot"):
        str(Page())
