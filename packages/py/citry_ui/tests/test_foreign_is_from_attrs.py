"""
A Citry UI component whose `attrs` mapping picks the tag may not put trusted HTML under `<svg>` or `<math>`.

`CCard`, `CContainer`, `CGrid`, `CRow` and `CCol` render through `<c-element>`,
which takes the tag from an `is` key in `attrs`. Inside `<svg>` or `<math>` the
browser reads `<style>` and `<noscript>` as markup, so the component's default
slot may not hold a `Markup` value that carries a tag. The rule belongs to
`<c-element>` (`packages/py/citry/tests/test_c_element_foreign_body.py` covers
it in full); this file checks that each component reaches it.
"""

from __future__ import annotations

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CCard, CCol, CContainer, CGrid, CRow

# A tag with a handler that would run if the browser read it as markup.
STYLE_HTML = Markup("<style><img src=x onerror=window.__ran=1></style>")


def _render(component: type[Component], slot: object, tag: str) -> str:
    """Render `component` with `attrs={"is": tag}` and `slot` as its default slot, inside a page."""
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    element = component(attrs={"is": tag}, slots={"default": slot})

    class Page(Component):
        citry = app
        template = """
            <main>{{ element }}</main>
        """

        def template_data(self, kwargs, slots):
            return {"element": element}

    return str(Page())


@pytest.mark.parametrize("tag", ["svg", "MATH"])
@pytest.mark.parametrize("component", [CCard, CContainer, CGrid, CRow, CCol])
def test_a_markup_slot_under_a_chosen_foreign_tag_is_refused(component: type[Component], tag: str) -> None:
    with pytest.raises(ValueError, match="tag name chosen at render time"):
        _render(component, STYLE_HTML, tag)


@pytest.mark.parametrize("component", [CCard, CContainer, CGrid, CRow, CCol])
def test_a_plain_text_slot_under_a_chosen_foreign_tag_still_renders(component: type[Component]) -> None:
    # Control: text is escaped, so it stays inert under <svg>.
    html = _render(component, "<x>", "svg")

    assert "<svg" in html
    assert "&lt;x&gt;" in html


@pytest.mark.parametrize("component", [CCard, CContainer, CGrid, CRow, CCol])
def test_a_markup_slot_under_a_div_still_renders(component: type[Component]) -> None:
    # Control: only `svg` and `math` change how the browser reads the body.
    html = _render(component, STYLE_HTML, "div")

    assert str(STYLE_HTML) in html
