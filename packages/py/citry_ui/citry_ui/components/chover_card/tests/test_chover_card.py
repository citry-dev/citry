"""Server contract tests for HoverCard."""

from __future__ import annotations

import re
from dataclasses import fields
from typing import get_args, get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CButton, CHoverCard


def _render(value: object) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = "<main>{{ value }}</main>"

        def template_data(self, _kwargs: object, _slots: object) -> dict[str, object]:
            return {"value": value}

    return str(Page())


def _card(**kwargs: object) -> CHoverCard:
    return CHoverCard(
        **kwargs,
        slots={
            "activator": lambda ctx: CButton(
                attrs=ctx.data.activator_attrs,
                slots={"default": "Inspect Ada"},
            ),
            "default": "Ada maps resilient distributed systems.",
        },
    )


def test_hover_card_renders_hidden_supplementary_top_layer_anatomy() -> None:
    seen: dict[str, object] = {}

    def activator(ctx: object) -> CButton:
        seen["data"] = ctx.data
        return CButton(attrs=ctx.data.activator_attrs, slots={"default": "Ada"})

    html = _render(
        CHoverCard(
            id="ada-preview",
            open=True,
            delay=400,
            close_delay=250,
            placement="top-end",
            size="lg",
            arrow=False,
            class_="profile-preview",
            attrs={"data-profile": "ada"},
            slots={"activator": activator, "default": "Supplementary biography"},
        )
    )
    surface = re.search(r'<div class="cui-hover-card(?:\s|\")[^>]*>', html)

    assert surface is not None
    assert 'id="ada-preview"' in surface.group(0)
    assert 'popover="manual"' in surface.group(0)
    assert 'aria-hidden="true"' in surface.group(0)
    assert 'role="' not in surface.group(0)
    assert 'data-placement="top-end"' in surface.group(0)
    assert 'data-size="lg"' in surface.group(0)
    assert " data-arrow" not in surface.group(0)
    assert 'data-profile="ada"' in surface.group(0)
    assert "aria-describedby" not in html
    assert seen["data"].hover_card_id == "ada-preview"
    assert seen["data"].activator_attrs["data-citry-hover-card-trigger"] == ""


def test_hover_card_public_schema_is_runtime_introspectable() -> None:
    assert [item.name for item in fields(CHoverCard.Kwargs)] == [
        "id",
        "open",
        "disabled",
        "delay",
        "close_delay",
        "placement",
        "arrow",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CHoverCard.Slots)] == ["activator", "default"]
    hints = get_type_hints(CHoverCard.Kwargs)
    assert get_args(hints["size"]) == ("sm", "md", "lg")
    assert "bottom-start" in get_args(hints["placement"])


@pytest.mark.parametrize(
    ("kwargs", "exception", "message"),
    [
        ({"open": 1}, TypeError, "CHoverCard open"),
        ({"disabled": 1}, TypeError, "CHoverCard disabled"),
        ({"arrow": 1}, TypeError, "CHoverCard arrow"),
        ({"delay": True}, TypeError, "CHoverCard delay"),
        ({"delay": -1}, ValueError, "CHoverCard delay"),
        ({"close_delay": 60_001}, ValueError, "CHoverCard close_delay"),
        ({"placement": "left"}, ValueError, "CHoverCard placement"),
        ({"size": "xl"}, ValueError, "CHoverCard size"),
        ({"id": "two words"}, ValueError, "CHoverCard id"),
        ({"attrs": []}, TypeError, "CHoverCard attrs must be a mapping"),
        ({"attrs": {"aria-hidden": "false"}}, ValueError, "owned attribute"),
        ({"attrs": {":role": "dialog"}}, ValueError, "dynamically bind"),
        ({"attrs": {"x-show": "open"}}, ValueError, "ownership directive"),
        ({"attrs": {"data-citry-root": ""}}, ValueError, "runtime attribute"),
    ],
)
def test_hover_card_rejects_invalid_or_owned_inputs(
    kwargs: dict[str, object], exception: type[Exception], message: str
) -> None:
    with pytest.raises(exception, match=message):
        _render(_card(**kwargs))


def test_hover_card_requires_both_owned_slots() -> None:
    with pytest.raises(Exception, match="activator"):
        _render(CHoverCard(slots={"default": "Preview"}))
    with pytest.raises(TypeError, match="default"):
        _render(
            CHoverCard(
                slots={
                    "activator": lambda ctx: CButton(
                        attrs=ctx.data.activator_attrs,
                        slots={"default": "Preview"},
                    )
                }
            )
        )


def test_hover_card_css_exposes_card_tokens_and_environment_rules() -> None:
    css = CHoverCard.css

    assert "--cui-hover-card-inline-size" in css
    assert "--cui-hover-card-padding" in css
    assert '[data-citry-ui-part="arrow"]' in css
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
    assert "@media print" in css
