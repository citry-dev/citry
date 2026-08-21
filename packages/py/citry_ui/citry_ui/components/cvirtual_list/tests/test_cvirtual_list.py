from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CVirtualList, CVirtualListItem, CVirtualWindow
from citry_ui.quality.asset_sources import read_component_source_css


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>"

    return str(Page())


def test_public_schema_separates_css_only_list_from_reactive_window():
    assert [item.name for item in fields(CVirtualList.Kwargs)] == [
        "aria_label",
        "estimated_item_size",
        "viewport_size",
        "focusable",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CVirtualWindow.Kwargs)] == [
        "total_count",
        "start_index",
        "item_size",
        "viewport_size",
        "overscan",
        "initial_index",
        "aria_label",
        "focusable",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CVirtualListItem.Kwargs)] == ["item_key", "class_", "style", "attrs"]
    assert getattr(CVirtualList, "js", None) is None
    assert getattr(CVirtualListItem, "js", None) is None
    assert "onRangeChange" in (Path(__file__).parents[1] / "runtime.source.js").read_text(encoding="utf8")
    assert get_type_hints(CVirtualWindow.Kwargs)["total_count"] is int
    assert CVirtualList in citry_ui.COMPONENTS
    assert CVirtualWindow in citry_ui.COMPONENTS
    assert CVirtualListItem in citry_ui.COMPONENTS


def test_complete_dom_anatomy_keeps_every_server_item_and_loads_no_runtime():
    html = _render(
        '<c-CVirtualList aria_label="Activity"><c-CVirtualListItem item_key="alpha">Alpha</c-CVirtualListItem>'
        '<c-CVirtualListItem item_key="beta">Beta</c-CVirtualListItem></c-CVirtualList>'
    )

    assert len(re.findall(r'<div[^>]+data-citry-ui-part="virtual-list"', html)) == 1
    assert len(re.findall(r'<div[^>]+data-citry-ui-part="item"', html)) == 2
    assert 'data-strategy="content-visibility"' in html
    assert 'role="list"' in html
    assert 'role="listitem"' in html
    assert 'aria-label="Activity"' in html
    assert 'data-index="0"' in html
    assert 'data-index="1"' in html
    assert 'data-item-key="alpha"' in html
    assert 'data-item-key="beta"' in html
    assert "content-visibility: auto" in read_component_source_css("cvirtual_list")
    assert "data-citry-virtual-list-spacer" not in html
    assert "CVirtualList onRangeChange" not in html


def test_complete_dom_slot_data_and_empty_collection_are_server_owned():
    html = _render(
        '<c-CVirtualList><c-CVirtualListItem item_key="alpha">'
        '<c-fill name="default" data="{ index, item_key, set_size, strategy }">'
        "{{ index }}:{{ item_key }}:{{ set_size }}:{{ strategy }}"
        "</c-fill></c-CVirtualListItem></c-CVirtualList>"
    )
    assert "0:alpha:1:content-visibility" in html

    empty = _render("<c-CVirtualList />")
    assert 'role="list"' in empty
    assert not re.search(r'<div[^>]+data-citry-ui-part="item"', empty)


def test_window_renders_exact_spacers_positions_and_fixed_item_metadata():
    html = _render(
        '<c-CVirtualWindow c-total_count="100" c-start_index="10" c-item_size="40" c-initial_index="10" '
        'aria_label="Rows"><c-CVirtualListItem item_key="alpha">Alpha</c-CVirtualListItem>'
        '<c-CVirtualListItem item_key="beta">Beta</c-CVirtualListItem></c-CVirtualWindow>'
    )

    assert 'data-strategy="window"' in html
    assert 'data-start-index="10"' in html
    assert 'data-total-count="100"' in html
    assert 'aria-label="Rows"' in html
    assert 'style="block-size: 400px;"' in html
    assert 'style="block-size: 3520px;"' in html
    assert 'aria-posinset="11"' in html
    assert 'aria-posinset="12"' in html
    assert html.count('aria-setsize="100"') == 2
    assert 'data-index="10"' in html
    assert 'data-index="11"' in html
    assert "CVirtualList onRangeChange" in html


def test_window_slot_data_uses_logical_positions_and_set_size():
    html = _render(
        '<c-CVirtualWindow c-total_count="12" c-start_index="7">'
        '<c-CVirtualListItem item_key="row-7"><c-fill name="default" '
        'data="{ index, item_key, set_size, strategy }">'
        "{{ index }}:{{ item_key }}:{{ set_size }}:{{ strategy }}"
        "</c-fill></c-CVirtualListItem></c-CVirtualWindow>"
    )
    assert "7:row-7:12:window" in html


def test_window_accepts_empty_and_final_partial_ranges():
    empty = _render('<c-CVirtualWindow c-total_count="0" />')
    assert 'data-total-count="0"' in empty
    assert len(re.findall(r'<div[^>]+data-citry-ui-part="spacer"', empty)) == 2
    assert "aria-posinset" not in empty

    final = _render(
        '<c-CVirtualWindow c-total_count="3" c-start_index="2" c-item_size="50">'
        '<c-CVirtualListItem item_key="last">Last</c-CVirtualListItem></c-CVirtualWindow>'
    )
    assert 'style="block-size: 100px;"' in final
    assert 'style="block-size: 0px;"' in final
    assert 'aria-posinset="3"' in final


def test_item_keys_are_required_nonempty_and_unique():
    with pytest.raises(SyntaxError, match="must have one of the following attributes"):
        _render("<c-CVirtualList><c-CVirtualListItem>A</c-CVirtualListItem></c-CVirtualList>")
    with pytest.raises(ValueError, match="item_key must be nonempty"):
        _render('<c-CVirtualList><c-CVirtualListItem item_key=" ">A</c-CVirtualListItem></c-CVirtualList>')
    with pytest.raises(ValueError, match="must be unique"):
        _render(
            '<c-CVirtualList><c-CVirtualListItem item_key="same">A</c-CVirtualListItem>'
            '<c-CVirtualListItem item_key="same">B</c-CVirtualListItem></c-CVirtualList>'
        )


def test_window_rejects_ranges_outside_total_and_unsafe_geometry():
    with pytest.raises(ValueError, match="start_index cannot exceed total_count"):
        _render('<c-CVirtualWindow c-total_count="2" c-start_index="3" />')
    with pytest.raises(ValueError, match="cannot extend beyond total_count"):
        _render(
            '<c-CVirtualWindow c-total_count="2" c-start_index="1">'
            '<c-CVirtualListItem item_key="a">A</c-CVirtualListItem>'
            '<c-CVirtualListItem item_key="b">B</c-CVirtualListItem></c-CVirtualWindow>'
        )
    with pytest.raises(ValueError, match="cannot exceed 16,000,000 CSS pixels"):
        _render('<c-CVirtualWindow c-total_count="400000" c-item_size="48" />')


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('<c-CVirtualList c-estimated_item_size="0" />', "estimated_item_size must be between 1 and 16000000"),
        ('<c-CVirtualList c-viewport_size="0" />', "viewport_size must be between 1 and 16000000"),
        ('<c-CVirtualList c-focusable="1" />', "focusable must be a bool"),
        ('<c-CVirtualWindow c-total_count="-1" />', "total_count must be at least 0"),
        ('<c-CVirtualWindow c-total_count="1" c-item_size="0" />', "item_size must be between 1 and 16000000"),
        ('<c-CVirtualWindow c-total_count="1" c-overscan="101" />', "overscan must be between 0 and 100"),
        ('<c-CVirtualWindow c-total_count="1" c-initial_index="-1" />', "initial_index must be at least 0"),
    ],
)
def test_invalid_server_configuration_is_rejected(source: str, message: str):
    with pytest.raises((TypeError, ValueError), match=message):
        _render(source)


def test_root_and_item_attrs_merge_but_owned_surfaces_are_rejected():
    html = _render(
        "<c-CVirtualList class_=\"brand\" c-style=\"{'color':'red'}\" "
        "c-attrs=\"{'data-test':'root'}\">"
        '<c-CVirtualListItem item_key="a" class_="row" c-attrs="{\'data-test-item\':\'a\'}">A'
        "</c-CVirtualListItem></c-CVirtualList>"
    )
    assert re.search(r'<div class="cui-virtual-list brand"[^>]+data-test="root"', html)
    assert re.search(r'<div class="cui-virtual-list__item row"[^>]+data-test-item="a"', html)
    assert "color: red" in html

    with pytest.raises(ValueError, match="owned attribute 'role'"):
        _render("<c-CVirtualList c-attrs=\"{'role':'feed'}\" />")
    with pytest.raises(ValueError, match="owned attribute 'aria-posinset'"):
        _render(
            '<c-CVirtualList><c-CVirtualListItem item_key="a" '
            "c-attrs=\"{'aria-posinset':2}\">A</c-CVirtualListItem></c-CVirtualList>"
        )


def test_focusable_false_removes_extra_tab_stop():
    html = _render('<c-CVirtualList c-focusable="False" />')
    root = re.search(r'<div class="cui-virtual-list"[^>]*>', html)
    assert root is not None
    assert "tabindex" not in root.group(0)


def test_declarations_reject_misplacement_extra_output_and_direct_nested_owner():
    with pytest.raises(ValueError, match="directly inside CVirtualList or CVirtualWindow"):
        _render('<c-CVirtualListItem item_key="a">A</c-CVirtualListItem>')
    with pytest.raises(ValueError, match="may contain only CVirtualListItem declarations"):
        _render("<c-CVirtualList><p>Unexpected</p></c-CVirtualList>")
    with pytest.raises(ValueError, match="Nested CVirtualList"):
        _render("<c-CVirtualList><c-CVirtualList /></c-CVirtualList>")


def test_nested_list_inside_item_content_is_independent():
    html = _render(
        '<c-CVirtualList><c-CVirtualListItem item_key="outer">Outer'
        '<c-CVirtualList><c-CVirtualListItem item_key="inner">Inner</c-CVirtualListItem></c-CVirtualList>'
        "</c-CVirtualListItem></c-CVirtualList>"
    )
    assert len(re.findall(r'<div[^>]+data-citry-ui-part="virtual-list"', html)) == 2
    assert len(re.findall(r'<div[^>]+data-item-key="outer"', html)) == 1
    assert len(re.findall(r'<div[^>]+data-item-key="inner"', html)) == 1


def test_window_runtime_declares_reactive_inputs_cleanup_and_error_isolation():
    source = (Path(__file__).parents[1] / "runtime.source.js").read_text(encoding="utf8")
    assert "props: {overscan: {}, itemSize: {}, onRangeChange: {}}" in source
    assert "requestAnimationFrame(calculate)" in source
    assert "new ResizeObserver" in source
    assert "root.removeEventListener" in source
    assert "observer.disconnect()" in source
    assert "cancelAnimationFrame" in source
    assert 'root.setAttribute("data-citry-virtual-window-initialized", "")' in source
    assert 'root.removeAttribute("data-citry-virtual-window-initialized")' in source
    assert "onRangeChange callback failed" in source
    assert "data-pending" in source
    assert "aria-busy" in source


def test_family_has_no_catalog_messages_and_messages_would_be_final_member():
    assert "messages" not in CVirtualList.__dict__
    assert "messages" not in CVirtualWindow.__dict__
    assert "messages" not in CVirtualListItem.__dict__
