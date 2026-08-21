from __future__ import annotations

import inspect
import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CSidebar


def _render(source: str, *, css: bool = False) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app
        template = f"<main>{source}</main>{'<c-css />' if css else ''}"

    return str(Page())


def _tag(html: str, part: str, index: int = 0) -> str:
    matches = re.findall(rf'<[^>]+data-citry-ui-part="{part}"[^>]*>', html)
    assert len(matches) > index
    return matches[index]


def test_public_schema_aliases_and_registration_are_exact() -> None:
    assert [item.name for item in fields(CSidebar.Kwargs)] == [
        "id",
        "label",
        "tag",
        "collapsed",
        "collapsible",
        "side",
        "variant",
        "size",
        "sticky",
        "expand_label",
        "collapse_label",
        "class_",
        "style",
        "attrs",
    ]
    assert [item.name for item in fields(CSidebar.Slots)] == ["default", "header", "footer", "toggle"]
    hints = get_type_hints(CSidebar.Kwargs)
    assert hints["tag"] == citry_ui.CSidebarTag
    assert hints["collapsible"] == citry_ui.CSidebarCollapsible
    assert hints["side"] == citry_ui.CSidebarSide
    assert hints["variant"] == citry_ui.CSidebarVariant
    assert hints["size"] == citry_ui.CSidebarSize
    assert CSidebar in citry_ui.COMPONENTS


def test_default_sidebar_is_a_named_complementary_landmark() -> None:
    html = _render('<c-CSidebar id="workspace" label="Workspace">Navigation</c-CSidebar>')
    root = _tag(html, "sidebar")
    toggle = _tag(html, "toggle")
    panel = _tag(html, "panel")

    assert root.startswith("<aside")
    assert 'id="workspace"' in root
    assert 'aria-label="Workspace"' in root
    assert 'data-collapsible="rail"' in root
    assert 'data-side="inline-start"' in root
    assert 'data-variant="plain"' in root
    assert 'data-size="md"' in root
    assert "data-collapsed" not in root
    assert 'type="button"' in toggle
    assert 'aria-controls="workspace-panel"' in toggle
    assert 'aria-expanded="true"' in toggle
    assert 'id="workspace-panel"' in panel
    assert "hidden" not in panel
    assert "inert" not in panel
    assert "Navigation" in html


def test_nav_offcanvas_and_optional_regions_render_exactly() -> None:
    html = _render(
        '<c-CSidebar id="project" tag="nav" label="Project" c-collapsed="True" '
        'collapsible="offcanvas" side="inline-end" variant="floating" size="lg" c-sticky="True">'
        '<c-fill name="header">Header</c-fill><c-fill name="default">Links</c-fill>'
        '<c-fill name="footer">Footer</c-fill><c-fill name="toggle">T</c-fill></c-CSidebar>'
    )
    root = _tag(html, "sidebar")
    panel = _tag(html, "panel")

    assert root.startswith("<nav")
    for token in (
        "data-collapsed",
        'data-collapsible="offcanvas"',
        'data-side="inline-end"',
        'data-variant="floating"',
        'data-size="lg"',
        "data-sticky",
    ):
        assert token in root
    assert 'aria-expanded="false"' in _tag(html, "toggle")
    assert "hidden" in panel
    assert "inert" in panel
    assert ">T<" in html
    assert _tag(html, "header").startswith("<header")
    assert _tag(html, "footer").startswith("<footer")


def test_custom_labels_do_not_register_catalog_bindings() -> None:
    html = _render(
        '<c-CSidebar label="Tools" expand_label="Show tools" collapse_label="Hide tools">Tools</c-CSidebar>'
    )
    assert "Show tools" in html
    assert "Hide tools" in html
    assert "citry-ui-sidebar-expand" not in html
    assert "citry-ui-sidebar-collapse" not in html


def test_class_style_and_allowed_attrs_merge_on_landmark() -> None:
    html = _render(
        '<c-CSidebar label="Tools" c-class_="[\'brand\']" '
        "c-style=\"{'--cui-sidebar-width':'18rem'}\" "
        "c-attrs=\"{'data-test':'root','class':'extra','style':'color:red'}\">Tools</c-CSidebar>"
    )
    root = _tag(html, "sidebar")
    assert all(name in root for name in ("cui-sidebar", "brand", "extra"))
    assert "--cui-sidebar-width: 18rem" in root
    assert "color: red" in root
    assert 'data-test="root"' in root


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("<c-CSidebar c-label=\"''\">A</c-CSidebar>", "label must be a non-empty string"),
        ('<c-CSidebar label="A" tag="section">A</c-CSidebar>', "tag must be one of"),
        ('<c-CSidebar label="A" collapsible="drawer">A</c-CSidebar>', "collapsible must be one of"),
        ('<c-CSidebar label="A" side="left">A</c-CSidebar>', "side must be one of"),
        ('<c-CSidebar label="A" variant="raised">A</c-CSidebar>', "variant must be one of"),
        ('<c-CSidebar label="A" size="xl">A</c-CSidebar>', "size must be one of"),
        (
            '<c-CSidebar label="A" c-collapsed="True" collapsible="none">A</c-CSidebar>',
            "collapsed=True cannot be used",
        ),
    ],
)
def test_invalid_inputs_fail_closed(source: str, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        _render(source)


@pytest.mark.parametrize(
    "attrs",
    [
        "{'role':'dialog'}",
        "{'aria-label':'Shadow'}",
        "{'data-collapsed':'false'}",
        "{'hidden':True}",
        "{':data-size':'size'}",
        "{'x-html':'unsafe'}",
    ],
)
def test_owned_attrs_and_replacing_directives_are_rejected(attrs: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(f'<c-CSidebar label="A" c-attrs="{attrs}">A</c-CSidebar>')


def test_css_exposes_public_variables_parts_and_environment_rules() -> None:
    html = _render('<c-CSidebar label="Tools">Tools</c-CSidebar>', css=True)
    for token in (
        "--cui-sidebar-width",
        "--cui-sidebar-rail-width",
        "--cui-sidebar-background",
        "--cui-sidebar-sticky-offset",
        "data-citry-sidebar-expanded-only",
        "data-citry-sidebar-rail-only",
        "prefers-reduced-motion",
        "forced-colors",
        "@media print",
    ):
        assert token in html


def test_messages_are_the_final_component_class_member() -> None:
    source = inspect.getsource(CSidebar)
    assert source.rfind("\n    messages =") > source.rfind("\n    css_file =")
    assert "\n    def " not in source[source.rfind("\n    messages =") :]
    assert CSidebar.I18n.messages_locale == "en-US"
    assert "citry-ui-sidebar-expand = Expand sidebar" in CSidebar.messages
    assert "citry-ui-sidebar-collapse = Collapse sidebar" in CSidebar.messages
