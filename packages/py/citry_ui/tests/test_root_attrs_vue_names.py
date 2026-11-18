"""
Every Citry UI `attrs=` and `*_attrs=` map refuses `is` and `key`, on the root element and elsewhere.

`CCard`, `CContainer`, `CGrid`, `CGridItem`, `CRow`, `CCol` and `CSidebar`
render their root through `<c-element>`, where an `is` key in the spread
would replace the tag the component chose from its fixed `tag=` list. The
shared check `reject_citry_ui_reserved_attr` refuses both names in every
map, so these cases stand for every component that calls it;
`test_reserved_attr_names.py` checks that every component module does.
"""

from __future__ import annotations

from typing import Any

import pytest

import citry_ui
from citry import Citry, Component

REFUSED = r"cannot set {name!r}\. 'is' and 'key' are reserved in Citry UI attrs"

# Each case puts the map in `attrs` on one component.
CASES = {
    "CCard.attrs": """
        <c-CCard c-attrs="attrs">Body</c-CCard>
    """,
    "CContainer.attrs": """
        <c-CContainer c-attrs="attrs">Body</c-CContainer>
    """,
    "CGrid.attrs": """
        <c-CGrid c-attrs="attrs">Body</c-CGrid>
    """,
    "CGridItem.attrs": """
        <c-CGrid>
          <c-CGridItem c-attrs="attrs">Body</c-CGridItem>
        </c-CGrid>
    """,
    "CRow.attrs": """
        <c-CRow c-attrs="attrs">Body</c-CRow>
    """,
    "CCol.attrs": """
        <c-CCol c-attrs="attrs">Body</c-CCol>
    """,
    "CSidebar.attrs": """
        <c-CSidebar label="Main" c-attrs="attrs">Body</c-CSidebar>
    """,
    "CButton.attrs": """
        <c-CButton c-attrs="attrs">Save</c-CButton>
    """,
    "CCombobox.input_attrs": """
        <c-CCombobox name="plan" c-options="options" c-input_attrs="attrs" />
    """,
}


def _render(case: str, attrs: dict[str, Any]) -> str:
    # A fresh app per render, because each render defines its own `Page`
    # class and an app refuses a second class with the same name.
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = CASES[case]

        def template_data(self, kwargs, slots):
            return {"attrs": attrs, "options": ()}

    return str(Page())


@pytest.mark.parametrize(
    ("name", "value"),
    [("is", "section"), ("IS", "svg"), ("Is", None), ("key", "x"), ("KEY", False)],
)
@pytest.mark.parametrize("case", list(CASES))
def test_attrs_refuse_is_and_key(case: str, name: str, value: object) -> None:
    """Refused in any ASCII letter case and with any value, as the item maps refuse them."""
    with pytest.raises(ValueError, match=REFUSED.format(name=name)):
        _render(case, {name: value})


@pytest.mark.parametrize("case", list(CASES))
def test_a_data_name_still_passes(case: str) -> None:
    # Control: the message points callers at a data-* name, which must work.
    html = _render(case, {"data-key": "row-1"})

    assert 'data-key="row-1"' in html


@pytest.mark.parametrize(
    "component",
    ["CCard", "CContainer", "CGrid", "CRow", "CCol"],
)
def test_the_tag_input_still_picks_the_root_tag(component: str) -> None:
    # Control: the fixed `tag=` list is how these components change their tag.
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"""
            <c-{component} tag="section">Body</c-{component}>
        """

    html = str(Page())

    assert "<section" in html
