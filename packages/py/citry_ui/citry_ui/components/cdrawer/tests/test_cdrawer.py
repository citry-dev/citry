"""Server contract tests for CDrawer."""

from __future__ import annotations

import pytest

import citry_ui
from citry import Citry


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")
    app.register_library(citry_ui)
    return app


def _render(**kwargs) -> str:
    app = _app()
    slots = kwargs.pop("slots", {"title": "Field note", "default": "Body"})
    return citry_ui.CDrawer(**kwargs, slots=slots).render(citry=app).serialize(deps_strategy="fragment")


def test_drawer_renders_native_modal_anatomy_and_logical_configuration() -> None:
    html = _render(
        id="field-note",
        open=True,
        placement="block-end",
        size="lg",
        scroll="drawer",
        slots={
            "title": "Field note",
            "description": "Observation details",
            "default": "Body",
            "actions": "Done",
        },
    )

    assert '<dialog class="cui-drawer" id="field-note" open' in html
    assert 'aria-labelledby="field-note-title"' in html
    assert 'aria-describedby="field-note-description"' in html
    assert 'data-placement="block-end"' in html
    assert 'data-size="lg"' in html
    assert 'data-scroll="drawer"' in html
    assert 'data-citry-ui-part="surface"' in html
    assert 'data-citry-ui-part="actions"' in html


def test_drawer_slot_data_supplies_owned_relationships() -> None:
    app = _app()
    drawer = citry_ui.CDrawer(
        id="notes",
        slots={
            "activator": lambda activator_attrs: str(activator_attrs),
            "title": "Notes",
            "default": "Body",
            "actions": lambda close_attrs: str(close_attrs),
        },
    )

    html = drawer.render(citry=app).serialize(deps_strategy="fragment")

    assert "data-citry-drawer-trigger" in html
    assert "aria-controls" in html
    assert "data-citry-drawer-close" in html


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("open", "yes"),
        ("dismissible", 1),
        ("placement", "right"),
        ("size", "xl"),
        ("scroll", "surface"),
        ("initial_focus", "first"),
        ("close_label", ""),
        ("id", "bad id"),
    ],
)
def test_drawer_rejects_invalid_server_inputs(name: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _render(**{name: value})


@pytest.mark.parametrize(
    "attr",
    [
        "id",
        "open",
        "role",
        "aria-hidden",
        "data-placement",
        "x-html",
        "x-ignore",
        ":open",
        "x-bind:aria-labelledby",
    ],
)
def test_drawer_rejects_owned_static_and_dynamic_attrs(attr: str) -> None:
    with pytest.raises(ValueError, match="CDrawer attrs"):
        _render(attrs={attr: "consumer"})


def test_drawer_merges_class_style_and_unrelated_attrs() -> None:
    html = _render(
        class_=["field-drawer", {"is-current": True}],
        style={"--cui-drawer-extent": "31rem"},
        attrs={"data-workflow": "field-note", "@close": "closed = true"},
    )

    assert 'class="cui-drawer field-drawer is-current"' in html
    assert "--cui-drawer-extent: 31rem" in html
    assert 'data-workflow="field-note"' in html
    assert '@close="closed = true"' in html


def test_drawer_public_types_are_runtime_introspectable() -> None:
    from typing import get_type_hints

    hints = get_type_hints(citry_ui.CDrawer.Kwargs)
    assert hints["placement"] == citry_ui.CDrawerPlacement
    assert hints["size"] == citry_ui.CDrawerSize
    assert hints["scroll"] == citry_ui.CDrawerScroll
