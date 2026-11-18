"""The root `attrs` of a list item component and of `CNativeSelect` refuse `is` and `key`."""

from __future__ import annotations

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CNativeSelectOption

# Each case puts `attrs` on the root of one component. The list item
# components all render inside their parent list, and `CNativeSelect` is
# rendered by Vue in the browser.
CASES = {
    "CListItem.attrs": """
        <c-CList>
          <c-CListItem c-attrs="attrs">A</c-CListItem>
        </c-CList>
    """,
    "CListItem.surface_attrs": """
        <c-CList>
          <c-CListItem href="/a" c-surface_attrs="attrs">A</c-CListItem>
        </c-CList>
    """,
    "CTimelineItem.attrs": """
        <c-CTimeline>
          <c-CTimelineItem c-attrs="attrs">A</c-CTimelineItem>
        </c-CTimeline>
    """,
    "CTreeItem.attrs": """
        <c-CTree label="Files">
          <c-CTreeItem value="a" label="A" c-attrs="attrs" />
        </c-CTree>
    """,
    "CSortableItem.attrs": """
        <c-CSortable name="order">
          <c-CSortableItem value="a" label="A" c-attrs="attrs" />
        </c-CSortable>
    """,
    "CTransferListItem.attrs": """
        <c-CTransferList name="people">
          <c-CTransferListItem value="a" label="A" c-attrs="attrs" />
        </c-CTransferList>
    """,
    "CVirtualListItem.attrs": """
        <c-CVirtualList aria_label="Rows">
          <c-CVirtualListItem item_key="a" c-attrs="attrs">A</c-CVirtualListItem>
        </c-CVirtualList>
    """,
    "CNativeSelect.attrs": """
        <c-CNativeSelect name="pick" c-options="options" c-attrs="attrs" />
    """,
}


def _render(case: str, attrs: dict[str, object]) -> str:
    # A fresh app per render, because each render defines its own `Page`
    # class and an app refuses a second class with the same name.
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = CASES[case]

        def template_data(self, kwargs, slots):
            return {"attrs": attrs, "options": [CNativeSelectOption("a", "A")]}

    return str(Page())


@pytest.mark.parametrize("name", ["is", "IS", "key", "Key"])
@pytest.mark.parametrize("case", list(CASES))
def test_item_root_attrs_refuse_names_vue_reads(case: str, name: str) -> None:
    """`is` and `key` are refused with the shared message, in any letter case."""
    with pytest.raises(ValueError, match=rf"cannot set {name!r}\. 'is' and 'key' are reserved"):
        _render(case, {name: "x-item"})


@pytest.mark.parametrize("case", list(CASES))
def test_item_root_attrs_keep_other_names(case: str) -> None:
    """A `data-*` name, the suggested replacement, still renders."""
    assert 'data-key="k1"' in _render(case, {"data-key": "k1"})
