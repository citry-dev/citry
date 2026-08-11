"""Server contract tests for CTooltip."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import fields
from typing import get_args, get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CButton, CTooltip


def _page_html(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ value }}</main>"

        def template_data(self, kwargs, slots):
            return {"value": value}

    return str(Page())


def _tooltip(**kwargs: object) -> CTooltip:
    return CTooltip(
        **kwargs,
        slots={
            "activator": lambda ctx: CButton(
                attrs=ctx.data.activator_attrs,
                slots={"default": "Inspect Europa"},
            ),
        },
    )


def test_tooltip_renders_semantic_top_layer_anatomy_and_typed_slot_data():
    seen = {}

    def activator(ctx):
        seen["activator"] = ctx.data
        return CButton(attrs=ctx.data.activator_attrs, slots={"default": "Inspect"})

    html = _page_html(
        CTooltip(
            id="europa-tooltip",
            text="Jupiter's icy moon",
            open=True,
            delay=450,
            close_delay=80,
            placement="top-end",
            class_="mission-tooltip",
            style={"--cui-tooltip-max-inline-size": "24rem"},
            attrs={"data-mission": "europa"},
            slots={"activator": activator},
        )
    )
    surface = re.search(r'<div class="cui-tooltip(?:\s|\")[^>]*>', html)

    assert surface is not None
    assert 'id="europa-tooltip"' in surface.group(0)
    assert 'popover="manual"' in surface.group(0)
    assert 'role="tooltip"' in surface.group(0)
    assert " data-open" in surface.group(0)
    assert 'data-placement="top-end"' in surface.group(0)
    assert 'data-mission="europa"' in surface.group(0)
    assert 'class="cui-tooltip mission-tooltip"' in surface.group(0)
    assert "--cui-tooltip-max-inline-size: 24rem" in surface.group(0)
    assert "--_cui-tooltip-anchor: --_cui-tooltip-anchor-ref-" in surface.group(0)
    assert 'aria-describedby="europa-tooltip"' in html
    assert "anchor-name: --_cui-tooltip-anchor-ref-" in html
    assert "Jupiter" in html
    assert "icy moon" in html
    assert seen["activator"].tooltip_id == "europa-tooltip"
    assert seen["activator"].activator_attrs["data-citry-tooltip-trigger"] == ""


def test_tooltip_accepts_exclusive_static_default_fill():
    html = _page_html(
        CTooltip(
            placement="bottom",
            slots={
                "activator": lambda ctx: CButton(
                    attrs=ctx.data.activator_attrs,
                    slots={"default": "Inspect"},
                ),
                "default": "A sulfur-stained surface",
            },
        )
    )

    assert "A sulfur-stained surface" in html
    assert "<span data-citry-tooltip-text>" not in html


def test_tooltip_public_schema_is_nested_slotted_and_runtime_introspectable():
    assert [item.name for item in fields(CTooltip.Kwargs)] == [
        "id",
        "text",
        "open",
        "disabled",
        "delay",
        "close_delay",
        "placement",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CTooltip.Slots)] == ["activator", "default"]
    hints = get_type_hints(CTooltip.Kwargs)
    assert get_args(hints["placement"]) == (
        "top-start",
        "top",
        "top-end",
        "bottom-start",
        "bottom",
        "bottom-end",
    )


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        ({"open": 1}, TypeError, "CTooltip open"),
        ({"disabled": 1}, TypeError, "CTooltip disabled"),
        ({"delay": True}, TypeError, "CTooltip delay"),
        ({"delay": -1}, ValueError, "CTooltip delay"),
        ({"delay": 60_001}, ValueError, "CTooltip delay"),
        ({"close_delay": 1.5}, TypeError, "CTooltip close_delay"),
        ({"placement": "left"}, ValueError, "CTooltip placement"),
        ({"id": ""}, ValueError, "CTooltip id"),
        ({"id": "two words"}, ValueError, "CTooltip id"),
        ({"id": "nul\0id"}, ValueError, "U\\+0000"),
        ({"text": "  "}, ValueError, "CTooltip text"),
        ({"text": "nul\0text"}, ValueError, "CTooltip text"),
        ({"attrs": []}, TypeError, "CTooltip attrs must be a mapping"),
        ({"attrs": {"popover": "auto"}}, ValueError, "owned attribute"),
        ({"attrs": {"ROLE": "alert"}}, ValueError, "owned attribute"),
        ({"attrs": {":aria-label": "other"}}, ValueError, "dynamically bind"),
        ({"attrs": {"x-bind": "surfaceAttrs"}}, ValueError, "ownership directive"),
        ({"attrs": {"x-show": "visible"}}, ValueError, "ownership directive"),
        ({"attrs": {"data-citry-root": ""}}, ValueError, "runtime attribute"),
    ],
)
def test_tooltip_rejects_invalid_or_ambiguous_inputs(kwargs, exception, message):
    inputs = {"text": "Europa", **kwargs}
    with pytest.raises(exception, match=message):
        _page_html(_tooltip(**inputs))


def test_tooltip_requires_activator_and_exactly_one_content_source():
    with pytest.raises(Exception, match="activator"):
        _page_html(CTooltip(text="Europa"))
    with pytest.raises(ValueError, match="exactly one"):
        _page_html(_tooltip())
    with pytest.raises(ValueError, match="exactly one"):
        _page_html(
            CTooltip(
                text="Europa",
                slots={
                    "activator": lambda ctx: CButton(
                        attrs=ctx.data.activator_attrs,
                        slots={"default": "Inspect"},
                    ),
                    "default": "Duplicate description",
                },
            )
        )


def test_tooltip_detrusts_safe_strings_before_rendering():
    html = _page_html(
        _tooltip(
            id=Markup('moon"data-unsafe="yes'),
            text=Markup("</span><script>window.__pwned=true</script>"),
        )
    )

    assert 'id="moon&#34;data-unsafe=&#34;yes"' in html
    assert 'data-unsafe="yes"' not in html
    assert "&lt;/span&gt;&lt;script&gt;" in html
    assert "<script>window.__pwned" not in html


class _SideEffectMapping(Mapping[str, object]):
    def __init__(self) -> None:
        self.iterations = 0

    def __getitem__(self, key: str) -> object:
        if key == "data-snapshot":
            return "first"
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("attrs mapping was consumed more than once")
        yield "data-snapshot"

    def __len__(self) -> int:
        return 1


def test_tooltip_snapshots_caller_owned_attrs_once_per_render():
    attrs = _SideEffectMapping()
    html = _page_html(_tooltip(text="Europa", attrs=attrs))

    assert 'data-snapshot="first"' in html
    assert attrs.iterations == 1
