from __future__ import annotations

import re
from dataclasses import fields
from pathlib import Path
from typing import get_args, get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CNavigationMenu, CNavigationMenuItem, CNavigationMenuLink


def _render(source: str) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = source

    return str(Page())


def _source(root: str = "", item: str = "") -> str:
    return (
        f'<c-CNavigationMenu label="Main" {root}>'
        '<c-CNavigationMenuLink href="/home" c-current="True">Home</c-CNavigationMenuLink>'
        f'<c-CNavigationMenuItem value="products" {item}>'
        '<c-fill name="label">Products</c-fill>'
        '<c-fill name="default"><a href="/products/a">Product A</a></c-fill>'
        "</c-CNavigationMenuItem></c-CNavigationMenu>"
    )


def test_navigation_menu_renders_native_navigation_anatomy() -> None:
    html = _render(_source('value="products" variant="surface" size="lg"'))
    assert re.search(r'<nav[^>]+aria-label="Main"', html)
    assert re.search(r'<nav[^>]+data-value="products"', html)
    assert '<ul data-citry-ui-part="list">' in html
    assert re.search(r'<a[^>]+href="/home"[^>]+aria-current="page"', html)
    assert re.search(r'<button[^>]+type="button"[^>]+aria-expanded="true"', html)
    assert re.search(r'<div[^>]+data-citry-ui-part="panel"[^>]*>', html)
    assert 'role="menu"' not in html
    assert 'role="menubar"' not in html


def test_closed_and_disabled_panels_are_inert_and_form_safe() -> None:
    html = _render(_source(item='c-disabled="True"'))
    trigger = re.search(r"<button[^>]+data-citry-navigation-menu-trigger[^>]*>", html)
    panel = re.search(r"<div[^>]+data-citry-navigation-menu-panel[^>]*>", html)
    assert trigger is not None
    assert " disabled" in trigger.group(0)
    assert 'type="button"' in trigger.group(0)
    assert panel is not None
    assert " hidden" in panel.group(0)
    assert " inert" in panel.group(0)


def test_public_schema_and_registration_are_exact() -> None:
    assert [item.name for item in fields(CNavigationMenu.Kwargs)] == [
        "label",
        "id",
        "value",
        "orientation",
        "disabled",
        "delay",
        "close_delay",
        "loop",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    hints = get_type_hints(CNavigationMenu.Kwargs)
    assert get_args(hints["orientation"]) == ("horizontal", "vertical")
    assert CNavigationMenu in citry_ui.COMPONENTS
    assert CNavigationMenuLink in citry_ui.COMPONENTS
    assert CNavigationMenuItem in citry_ui.COMPONENTS


@pytest.mark.parametrize(
    ("root", "message"),
    [
        ('orientation="diagonal"', "orientation"),
        ('variant="filled"', "variant"),
        ('size="xl"', "size"),
        ('c-delay="-1"', "delay"),
        ('c-loop="1"', "loop"),
        ('id="two words"', "ASCII whitespace"),
        ("c-attrs=\"{'role': 'navigation'}\"", "owned"),
        ("c-attrs=\"{'x-show': 'open'}\"", "ownership"),
    ],
)
def test_invalid_root_inputs_fail(root: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(_source(root))


def test_empty_unknown_duplicate_and_orphan_collections_fail() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _render(
            '<c-CNavigationMenu label="Main"><c-fill name="default"><c-if cond="False">'
            '<c-CNavigationMenuLink href="/">Hidden</c-CNavigationMenuLink>'
            "</c-if></c-fill></c-CNavigationMenu>"
        )
    with pytest.raises(ValueError, match="does not identify"):
        _render(_source('value="missing"'))
    with pytest.raises(ValueError, match="duplicated"):
        _render(
            '<c-CNavigationMenu label="Main">'
            '<c-CNavigationMenuItem value="same"><c-fill name="label">A</c-fill><c-fill name="default">A</c-fill>'
            '</c-CNavigationMenuItem><c-CNavigationMenuItem value="same"><c-fill name="label">B</c-fill>'
            '<c-fill name="default">B</c-fill></c-CNavigationMenuItem></c-CNavigationMenu>'
        )
    with pytest.raises(ValueError, match="inside CNavigationMenu"):
        _render('<c-CNavigationMenuLink href="/">Loose</c-CNavigationMenuLink>')
    with pytest.raises(ValueError, match="Nested CNavigationMenu"):
        _render(
            '<c-CNavigationMenu label="Outer"><c-CNavigationMenuItem value="more">'
            '<c-fill name="label">More</c-fill><c-fill name="default">'
            '<c-CNavigationMenu label="Inner"><c-CNavigationMenuLink href="/inner">Inner</c-CNavigationMenuLink>'
            "</c-CNavigationMenu></c-fill></c-CNavigationMenuItem></c-CNavigationMenu>"
        )
    with pytest.raises(ValueError, match="inside CNavigationMenu"):
        _render(
            '<c-CNavigationMenu label="Outer"><c-CNavigationMenuItem value="more">'
            '<c-fill name="label">More</c-fill><c-fill name="default">'
            '<c-CNavigationMenuItem value="nested"><c-fill name="label">Nested</c-fill>'
            '<c-fill name="default">Nested</c-fill></c-CNavigationMenuItem>'
            "</c-fill></c-CNavigationMenuItem></c-CNavigationMenu>"
        )


def test_owned_destination_attributes_fail() -> None:
    with pytest.raises(ValueError, match="owned"):
        _render(_source(item="c-trigger_attrs=\"{'aria-expanded': 'false'}\""))
    with pytest.raises(ValueError, match="owned"):
        _render(_source(item="c-panel_attrs=\"{'hidden': False}\""))


def test_css_contract_covers_public_states_and_environments() -> None:
    css = (Path(__file__).parents[1] / "runtime.source.css").read_text(encoding="utf8")
    assert "--cui-navigation-menu-panel-background" in css
    assert '[data-citry-ui-part="indicator"]' in css
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
    assert "@media print" in css
