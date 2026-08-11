from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CBreadcrumbItem, CBreadcrumbs


def _render(template: str, data: dict[str, object], *, include_css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    template_source = template
    values = data

    class Page(Component):
        citry = app
        template = template_source

        def template_data(self, kwargs, slots):
            return values

    html = str(Page())
    return html + (str(app.get("css")()) if include_css else "")


def _items():
    return (
        CBreadcrumbItem("Home", "/"),
        CBreadcrumbItem("Rooms", "/rooms", {"data-level": "rooms"}),
        CBreadcrumbItem("Reading nook"),
    )


def test_breadcrumb_schema_and_item_record_are_explicit():
    assert [field.name for field in fields(CBreadcrumbs.Kwargs)] == [
        "items",
        "label",
        "separator",
        "size",
        "wrap",
        "class_",
        "style",
        "attrs",
        "list_attrs",
    ]
    assert [field.name for field in fields(CBreadcrumbs.Slots)] == ["item", "separator"]
    assert [field.name for field in fields(CBreadcrumbItem)] == ["label", "href", "attrs"]


def test_breadcrumbs_render_nav_ordered_list_links_current_page_and_hidden_separators():
    html = _render('<c-CBreadcrumbs c-items="items" label="Page location" />', {"items": _items()})

    assert '<nav class="cui-breadcrumbs" aria-label="Page location"' in html
    assert '<ol data-citry-ui-part="list">' in html
    assert html.count('<li data-citry-ui-part="item">') == 3
    assert '<a href="/" data-citry-ui-part="link">' in html
    assert 'href="/rooms"' in html
    assert 'data-level="rooms"' in html
    assert '<span aria-current="page" data-citry-ui-part="current">' in html
    assert html.count('aria-hidden="true" data-citry-ui-part="separator"') == 2


def test_linked_last_item_is_still_marked_current_page():
    items = (CBreadcrumbItem("Home", "/"), CBreadcrumbItem("Current", "/current"))
    html = _render('<c-CBreadcrumbs c-items="items" />', {"items": items})

    current = re.search(r'<a[^>]+href="/current"[^>]*>', html)
    assert current is not None
    assert 'aria-current="page"' in current.group(0)


def test_scoped_item_and_separator_slots_receive_exact_data():
    html = _render(
        """
          <c-CBreadcrumbs c-items="items">
            <c-fill name="item" data="{ item, index, is_current, attrs }">
              <span c-bind="attrs" c-data-index="index">{{ item.label }}:{{ is_current }}</span>
            </c-fill>
            <c-fill name="separator" data="{ index }">→{{ index }}</c-fill>
          </c-CBreadcrumbs>
        """,
        {"items": _items()},
    )

    assert 'data-index="0">Home:False' in html
    assert 'aria-current="page" data-index="2">Reading nook:True' in html
    assert "→0" in html
    assert "→1" in html


def test_breadcrumbs_validate_records_and_exact_strings():
    with pytest.raises(ValueError, match="at least one"):
        _render('<c-CBreadcrumbs c-items="items" />', {"items": ()})
    with pytest.raises(TypeError, match=r"items\[0\]"):
        _render('<c-CBreadcrumbs c-items="items" />', {"items": ("Home",)})
    with pytest.raises(ValueError, match="label must be non-empty"):
        _render('<c-CBreadcrumbs c-items="items" />', {"items": (CBreadcrumbItem(""),)})
    with pytest.raises(ValueError, match=r"U\+0000"):
        _render('<c-CBreadcrumbs c-items="items" />', {"items": (CBreadcrumbItem("Bad\0label"),)})
    with pytest.raises(ValueError, match="href must be non-empty"):
        _render('<c-CBreadcrumbs c-items="items" />', {"items": (CBreadcrumbItem("Home", ""),)})


@pytest.mark.parametrize(
    ("input_name", "attribute"),
    [
        ("attrs", "role"),
        ("attrs", "aria-label"),
        ("attrs", "x-if"),
        ("attrs", "data-citry-morph"),
        ("list_attrs", "role"),
        ("list_attrs", "aria-hidden"),
    ],
)
def test_breadcrumbs_reject_competing_root_and_list_ownership(input_name, attribute):
    with pytest.raises(ValueError, match=r"owned|ownership|reserved"):
        _render(
            f"<c-CBreadcrumbs c-items=\"items\" c-{input_name}=\"{{'{attribute}': 'x'}}\" />",
            {"items": _items()},
        )


def test_item_attrs_are_snapshotted_and_cannot_replace_navigation_semantics():
    attrs = {"class": "ancestor"}
    item = CBreadcrumbItem("Home", "/", attrs)
    html = _render('<c-CBreadcrumbs c-items="items" />', {"items": (item,)})
    attrs["href"] = "/evil"
    assert 'class="ancestor"' in html
    assert "/evil" not in html
    with pytest.raises(ValueError, match="owned"):
        _render(
            '<c-CBreadcrumbs c-items="items" />',
            {"items": (CBreadcrumbItem("Home", "/", {"aria-current": "step"}),)},
        )


def test_breadcrumbs_root_styling_wrap_and_css_contract():
    html = _render(
        """
          <c-CBreadcrumbs
            c-items="items"
            size="lg"
            c-wrap="False"
            class_="house-trail"
            c-style="{'--cui-breadcrumbs-gap': '20px'}"
            c-attrs="{'data-owner': 'house'}"
            c-list_attrs="{'data-list': 'trail'}"
          />
        """,
        {"items": _items()},
        include_css=True,
    )

    assert 'class="cui-breadcrumbs house-trail"' in html
    assert 'style="--cui-breadcrumbs-gap: 20px;"' in html
    assert 'data-size="lg"' in html
    assert "data-wrap" not in re.search(r"<nav[^>]+>", html).group(0)
    assert 'data-owner="house"' in html
    assert 'data-list="trail"' in html
    assert "--cui-breadcrumbs-current-color" in html
    assert "forced-colors" in html
    assert "@media print" in html
