from __future__ import annotations

import re
from dataclasses import fields

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CTimeline, CTimelineItem
from citry_ui.quality.asset_sources import read_component_source_css


def _render(source: str, *, css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>{'<c-css />' if css else ''}"

    return str(Page())


def test_public_schema_is_small_and_server_only():
    assert [item.name for item in fields(CTimeline.Kwargs)] == [
        "orientation",
        "side",
        "line_style",
        "density",
        "size",
        "label",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CTimelineItem.Kwargs)] == ["state", "side", "class_", "style", "attrs"]
    assert getattr(CTimeline, "js", None) is None
    assert getattr(CTimelineItem, "js", None) is None


def test_default_anatomy_is_one_ordered_list_with_list_items():
    html = _render("<c-CTimeline><c-CTimelineItem>First</c-CTimelineItem></c-CTimeline>")

    assert len(re.findall(r'<ol[^>]+data-citry-ui-part="timeline"', html)) == 1
    assert len(re.findall(r'<li[^>]+data-citry-ui-part="item"', html)) == 1
    assert 'data-orientation="vertical"' in html
    assert 'data-side="end"' in html
    assert 'data-line-style="solid"' in html
    assert 'data-density="comfortable"' in html
    assert 'data-size="md"' in html
    assert 'data-state="neutral"' in html
    assert "aria-current" not in html
    for part in ("track", "before", "indicator", "after", "content"):
        assert f'data-citry-ui-part="{part}"' in html
    assert re.search(r'<div[^>]+aria-hidden="true"[^>]+data-citry-ui-part="track"', html)


def test_states_side_resolution_and_current_semantics_are_exact():
    html = _render(
        '<c-CTimeline side="alternate"><c-CTimelineItem state="complete">A</c-CTimelineItem>'
        '<c-CTimelineItem state="current">B</c-CTimelineItem>'
        '<c-CTimelineItem state="pending" side="start">C</c-CTimelineItem>'
        '<c-CTimelineItem state="error" side="end">D</c-CTimelineItem></c-CTimeline>'
    )
    roots = re.findall(r'<li[^>]+data-citry-ui-part="item"[^>]*>', html)
    assert len(roots) == 4
    assert 'data-side="end"' in roots[0]
    assert 'data-side="start"' in roots[1]
    assert 'aria-current="true"' in roots[1]
    assert 'data-side="start"' in roots[2]
    assert 'data-side="end"' in roots[3]


def test_slots_render_with_settled_slot_data_and_decorative_indicator():
    html = _render(
        '<c-CTimeline><c-CTimelineItem state="current">'
        '<c-fill name="opposite" data="{ index, side, is_first, is_last }">'
        "{{ index }}:{{ side }}:{{ is_first }}:{{ is_last }}</c-fill>"
        '<c-fill name="indicator" data="{ index }">I{{ index }}</c-fill>'
        '<c-fill name="default" data="{ state }">{{ state }}</c-fill>'
        "</c-CTimelineItem></c-CTimeline>"
    )
    assert re.search(r'data-citry-ui-part="opposite">0:end:True:True</div>', html)
    assert re.search(r'data-citry-ui-part="indicator">\s*I0', html)
    assert re.search(r'data-citry-ui-part="content">current</div>', html)


def test_root_and_item_styling_and_allowed_attrs_merge():
    html = _render(
        '<c-CTimeline label="History" c-class_="[\'extra\']" '
        "c-style=\"{'--cui-timeline-gap':'2rem'}\" "
        "c-attrs=\"{'id':'history','class':'root','style':'color:red'}\">"
        "<c-CTimelineItem c-class_=\"{'chosen':True}\" "
        "c-attrs=\"{'id':'event','class':'item'}\">A</c-CTimelineItem>"
        "</c-CTimeline>"
    )
    root = re.search(r'<ol[^>]+id="history"[^>]*>', html)
    item = re.search(r'<li[^>]+id="event"[^>]*>', html)
    assert root is not None
    assert item is not None
    assert all(name in root.group(0) for name in ("cui-timeline", "root", "extra"))
    assert "color: red" in root.group(0)
    assert "--cui-timeline-gap: 2rem" in root.group(0)
    assert all(name in item.group(0) for name in ("cui-timeline__item", "item", "chosen"))
    assert 'aria-label="History"' in root.group(0)


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("orientation", "diagonal"),
        ("side", "center"),
        ("line_style", "double"),
        ("density", "dense"),
        ("size", "xl"),
    ],
)
def test_invalid_root_choices_fail(attribute: str, value: str):
    with pytest.raises(ValueError, match=f"CTimeline {attribute}"):
        _render(f'<c-CTimeline {attribute}="{value}"><c-CTimelineItem>A</c-CTimelineItem></c-CTimeline>')


@pytest.mark.parametrize(
    "source",
    [
        '<c-CTimeline><c-CTimelineItem state="unknown">A</c-CTimelineItem></c-CTimeline>',
        '<c-CTimeline><c-CTimelineItem side="alternate">A</c-CTimelineItem></c-CTimeline>',
    ],
)
def test_invalid_item_choices_fail(source: str):
    with pytest.raises(ValueError, match="CTimelineItem"):
        _render(source)


def test_declaration_grammar_and_current_uniqueness_fail_closed():
    with pytest.raises(SyntaxError, match="requires 1 slot"):
        _render("<c-CTimeline />")
    with pytest.raises(ValueError, match="only CTimelineItem declarations"):
        _render("<c-CTimeline><p>Loose</p><c-CTimelineItem>A</c-CTimelineItem></c-CTimeline>")
    with pytest.raises(ValueError, match="at most one"):
        _render(
            '<c-CTimeline><c-CTimelineItem state="current">A</c-CTimelineItem>'
            '<c-CTimelineItem state="current">B</c-CTimelineItem></c-CTimeline>'
        )


def test_item_outside_timeline_and_direct_nested_timeline_fail():
    with pytest.raises(ValueError, match="directly inside CTimeline"):
        _render("<c-CTimelineItem>Loose</c-CTimelineItem>")
    with pytest.raises(ValueError, match="Nested CTimeline"):
        _render(
            "<c-CTimeline><c-CTimeline><c-CTimelineItem>Nested</c-CTimelineItem></c-CTimeline>"
            "<c-CTimelineItem>Outer</c-CTimelineItem></c-CTimeline>"
        )


@pytest.mark.parametrize(
    "source",
    [
        "<c-CTimeline c-attrs=\"{'role':'presentation'}\"><c-CTimelineItem>A</c-CTimelineItem></c-CTimeline>",
        "<c-CTimeline c-attrs=\"{'aria-label':'Shadow'}\"><c-CTimelineItem>A</c-CTimelineItem></c-CTimeline>",
        "<c-CTimeline><c-CTimelineItem c-attrs=\"{'aria-current':'page'}\">A</c-CTimelineItem></c-CTimeline>",
        "<c-CTimeline><c-CTimelineItem c-attrs=\"{'x-html':'unsafe'}\">A</c-CTimelineItem></c-CTimeline>",
    ],
)
def test_owned_or_replacing_attrs_fail(source: str):
    with pytest.raises(ValueError, match="cannot"):
        _render(source)


def test_css_uses_public_variable_private_fallbacks_and_environment_rules():
    css = read_component_source_css("ctimeline")
    for public in (
        "--cui-timeline-gap",
        "--cui-timeline-indicator-size",
        "--cui-timeline-line-color",
        "--cui-timeline-current-color",
        "--cui-timeline-error-color",
    ):
        assert public in css
        assert public.replace("--cui-", "--_cui-", 1) in css
    assert "@media (forced-colors: active)" in css
    assert "@media print" in css
    assert "overflow-x: auto" in css
