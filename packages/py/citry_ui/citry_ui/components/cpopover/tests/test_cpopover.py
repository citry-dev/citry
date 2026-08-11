"""Server contract tests for CPopover."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import fields
from typing import get_args, get_type_hints

import pytest
from markupsafe import Markup

import citry_ui
from citry import Citry, Component
from citry_ui import CButton, CPopover, CTooltip


def _page_html(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ value }}</main>"

        def template_data(self, kwargs, slots):
            return {"value": value}

    return str(Page())


def _popover(**kwargs: object) -> CPopover:
    return CPopover(
        **kwargs,
        slots={
            "activator": lambda ctx: CButton(
                attrs=ctx.data.activator_attrs,
                slots={"default": "Inspect moon"},
            ),
            "title": "Europa",
            "default": "Subsurface ocean",
        },
    )


def test_popover_and_tooltip_emit_one_shared_anchored_runtime_dependency():
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    popover = _popover()
    tooltip = CTooltip(
        text="Icy moon",
        slots={
            "activator": lambda ctx: CButton(
                attrs=ctx.data.activator_attrs,
                slots={"default": "Describe moon"},
            )
        },
    )

    class Page(Component):
        citry = app
        template = "<main>{{ popover }}{{ tooltip }}</main><c-js />"

        def template_data(self, kwargs, slots):
            return {"popover": popover, "tooltip": tooltip}

    html = str(Page())

    assert html.count("cannot replace an incompatible anchored-layer runtime") == 1
    assert html.count("anchored-layer runtime dependency did not load") == 2


def test_popover_renders_semantic_top_layer_anatomy_and_typed_slot_data():
    seen = {}

    def activator(ctx):
        seen["activator"] = ctx.data
        return CButton(attrs=ctx.data.activator_attrs, slots={"default": "Inspect"})

    def actions(ctx):
        seen["actions"] = ctx.data
        return CButton(attrs=ctx.data.close_attrs, slots={"default": "Close"})

    html = _page_html(
        CPopover(
            id="europa-popover",
            open=True,
            placement="top-end",
            match_width=True,
            class_="mission-popover",
            style={"--cui-popover-inline-size": "24rem"},
            attrs={"data-mission": "europa"},
            slots={
                "activator": activator,
                "title": "Europa",
                "description": "Jupiter's icy moon",
                "default": "Subsurface ocean",
                "actions": actions,
            },
        )
    )
    surface = re.search(r'<div class="cui-popover(?:\s|\")[^>]*>', html)

    assert surface is not None
    assert 'id="europa-popover"' in surface.group(0)
    assert 'popover="manual"' in surface.group(0)
    assert 'role="dialog"' in surface.group(0)
    assert 'tabindex="-1"' in surface.group(0)
    assert 'aria-labelledby="europa-popover-title"' in surface.group(0)
    assert 'aria-describedby="europa-popover-description"' in surface.group(0)
    assert " data-open" in surface.group(0)
    assert 'data-placement="top-end"' in surface.group(0)
    assert " data-match-width" in surface.group(0)
    assert 'data-mission="europa"' in surface.group(0)
    assert 'class="cui-popover mission-popover"' in surface.group(0)
    assert "--cui-popover-inline-size: 24rem" in surface.group(0)
    assert "--_cui-popover-anchor: --_cui-popover-anchor-ref-" in surface.group(0)
    assert 'aria-controls="europa-popover"' in html
    assert 'aria-expanded="true"' in html
    assert 'aria-haspopup="dialog"' in html
    assert "anchor-name: --_cui-popover-anchor-ref-" in html
    assert seen["activator"].activator_attrs["data-citry-popover-trigger"] == ""
    assert seen["actions"].close_attrs == {"data-citry-popover-close": ""}


def test_popover_public_schema_is_nested_slotted_and_runtime_introspectable():
    assert [item.name for item in fields(CPopover.Kwargs)] == [
        "id",
        "open",
        "dismissible",
        "placement",
        "match_width",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CPopover.Slots)] == [
        "activator",
        "title",
        "default",
        "description",
        "actions",
    ]
    hints = get_type_hints(CPopover.Kwargs)
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
        ({"open": 1}, TypeError, "CPopover open"),
        ({"dismissible": 1}, TypeError, "CPopover dismissible"),
        ({"match_width": 1}, TypeError, "CPopover match_width"),
        ({"placement": "left"}, ValueError, "CPopover placement"),
        ({"id": ""}, ValueError, "CPopover id"),
        ({"id": "two words"}, ValueError, "CPopover id"),
        ({"id": "nul\0id"}, ValueError, "U\\+0000"),
        ({"attrs": []}, TypeError, "CPopover attrs must be a mapping"),
        ({"attrs": {"popover": "auto"}}, ValueError, "owned attribute"),
        ({"attrs": {"ROLE": "alert"}}, ValueError, "owned attribute"),
        ({"attrs": {":aria-labelledby": "other"}}, ValueError, "dynamically bind"),
        ({"attrs": {"x-bind": "surfaceAttrs"}}, ValueError, "ownership directive"),
        ({"attrs": {"x-show": "visible"}}, ValueError, "ownership directive"),
        ({"attrs": {"data-citry-root": ""}}, ValueError, "runtime attribute"),
    ],
)
def test_popover_rejects_invalid_or_ambiguous_inputs(kwargs, exception, message):
    with pytest.raises(exception, match=message):
        _page_html(_popover(**kwargs))


def test_popover_detrusts_safe_id_strings_before_rendering():
    html = _page_html(_popover(id=Markup('moon"data-unsafe="yes')))

    assert 'id="moon&#34;data-unsafe=&#34;yes"' in html
    assert 'data-unsafe="yes"' not in html


def test_popover_requires_every_structural_fill():
    with pytest.raises(Exception, match="activator"):
        _page_html(CPopover(slots={"title": "Title", "default": "Body"}))
    with pytest.raises(Exception, match="title"):
        _page_html(
            CPopover(
                slots={
                    "activator": lambda ctx: CButton(
                        attrs=ctx.data.activator_attrs,
                        slots={"default": "Open"},
                    ),
                    "default": "Body",
                }
            )
        )
    with pytest.raises(Exception, match="default"):
        _page_html(
            CPopover(
                slots={
                    "activator": lambda ctx: CButton(
                        attrs=ctx.data.activator_attrs,
                        slots={"default": "Open"},
                    ),
                    "title": "Title",
                }
            )
        )


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


def test_popover_snapshots_caller_owned_attrs_once_per_render():
    attrs = _SideEffectMapping()
    html = _page_html(_popover(attrs=attrs))

    assert 'data-snapshot="first"' in html
    assert attrs.iterations == 1
