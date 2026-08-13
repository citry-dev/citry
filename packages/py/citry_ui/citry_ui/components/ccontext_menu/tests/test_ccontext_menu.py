"""Server contracts for CContextMenu."""

from __future__ import annotations

from dataclasses import fields
from typing import get_type_hints

import pytest

from citry import Citry, Component, ComponentLibrary
from citry_ui.components.cbutton import CButton
from citry_ui.components.ccontext_menu import (
    CContextMenu,
    CContextMenuMenuSlotData,
    CContextMenuOpenChangeDetail,
    CContextMenuTargetSlotData,
)
from citry_ui.components.cmenu import CMenuItem, CMenuSeparator
from citry_ui.components.cmenu.cmenu import (
    _CMENU_SHARED_ASSETS,
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)

_COMPONENTS = (
    CContextMenu,
    CButton,
    CMenuItem,
    CMenuSeparator,
    CInternalMenuCollection,
    CInternalMenuContent,
    CInternalMenuSurface,
)


def _app() -> Citry:
    app = Citry(autodiscover=False)
    app.register_library(ComponentLibrary("citry-ui-context-menu-tests", _COMPONENTS))
    return app


def _render(template: str, data: dict[str, object] | None = None, *, deps: str = "ignore") -> str:
    app = _app()

    class Page(Component):
        citry = app

        def template_data(self, kwargs, slots):
            return data or {}

    Page.template = template
    return Page().render().serialize(deps_strategy=deps)


def _context_menu(inputs: str = "") -> str:
    return f"""
      <c-CContextMenu aria_label="Document actions" {inputs}>
        <c-fill name="target" data="{{ target_attrs }}">
          <button c-bind="target_attrs" type="button">Quarterly report</button>
        </c-fill>
        <c-fill name="menu">
          <c-CMenuItem value="rename">Rename</c-CMenuItem>
          <c-CMenuSeparator />
          <c-CMenuItem value="delete" intent="danger">Delete</c-CMenuItem>
        </c-fill>
      </c-CContextMenu>
    """


def test_public_exports_and_schema_are_exact() -> None:
    import citry_ui.components.ccontext_menu as family

    assert family.__all__ == [
        "CContextMenu",
        "CContextMenuMenuSlotData",
        "CContextMenuOpenChangeDetail",
        "CContextMenuTargetSlotData",
    ]
    assert [field.name for field in fields(CContextMenu.Kwargs)] == [
        "aria_label",
        "id",
        "open",
        "disabled",
        "loop",
        "close_on_select",
        "size",
        "class_",
        "style",
        "attrs",
        "target_attrs",
    ]
    assert [field.name for field in fields(CContextMenu.Slots)] == ["target", "menu"]
    assert get_type_hints(CContextMenuTargetSlotData) == {"target_attrs": dict[str, object]}
    assert CContextMenuMenuSlotData.__dict__.get("__annotations__", {}) == {}
    assert set(CContextMenuOpenChangeDetail.__required_keys__) == {
        "reason",
        "controlled",
        "forced",
        "source",
        "clientX",
        "clientY",
    }


def test_template_composition_renders_one_correlated_native_anatomy() -> None:
    html = _render(_context_menu('id="document-actions" open size="lg"'))

    assert html.count("data-citry-context-menu-host") == 1
    assert html.count("data-citry-context-menu-target") == 1
    assert html.count("data-citry-context-menu-point") == 1
    assert html.count("data-citry-menu-root") == 1
    assert 'id="document-actions"' in html
    assert 'id="document-actions-target"' in html
    assert 'id="document-actions-point"' in html
    assert 'id="document-actions-menu"' in html
    assert 'aria-label="Document actions"' in html
    assert 'data-citry-ui-part="context-menu"' in html
    assert 'data-citry-ui-part="menu"' in html
    assert 'popover="manual"' in html
    assert "data-open" in html
    assert 'data-size="lg"' in html


def test_direct_python_composition_uses_existing_menu_declarations() -> None:
    component = CContextMenu(
        aria_label="Document actions",
        slots={
            "target": lambda data: CButton(
                attrs=data.target_attrs,
                slots={"default": "Quarterly report"},
            ),
            "menu": (
                CMenuItem(value="rename", slots={"default": "Rename"}),
                CMenuSeparator(),
                CMenuItem(value="delete", slots={"default": "Delete"}),
            ),
        },
    )
    html = component.render(citry=_app()).serialize(deps_strategy="ignore")

    assert html.count("data-citry-context-menu-target") == 1
    assert html.count("data-citry-menu-entry") == 3
    assert "position-anchor: --_cui-menu-anchor-ref-" in html
    assert "Quarterly report" in html
    assert "Rename" in html
    assert "Delete" in html


def test_root_and_target_destinations_are_distinct_and_copied() -> None:
    root_attrs = {"lang": "fr", "data-test-root": "context"}
    target_attrs = {
        "tabindex": "0",
        "aria-describedby": "hint",
        "data-citry-context-menu-native": "",
    }
    html = (
        CContextMenu(
            aria_label="Actions",
            class_="brand-context",
            style={"--cui-menu-offset": "0.5rem"},
            attrs=root_attrs,
            target_attrs=target_attrs,
            slots={
                "target": lambda data: CButton(
                    attrs=data.target_attrs,
                    slots={"default": "Target"},
                ),
                "menu": (CMenuItem(value="go", slots={"default": "Go"}),),
            },
        )
        .render(citry=_app())
        .serialize(deps_strategy="ignore")
    )

    assert root_attrs == {"lang": "fr", "data-test-root": "context"}
    assert target_attrs == {
        "tabindex": "0",
        "aria-describedby": "hint",
        "data-citry-context-menu-native": "",
    }
    assert 'class="cui-context-menu-host brand-context"' in html
    assert 'data-test-root="context"' in html
    assert 'aria-describedby="hint"' in html
    assert 'data-citry-context-menu-native=""' in html
    assert "--cui-menu-offset: 0.5rem" in html


def test_target_accepts_safe_native_semantics_but_root_does_not() -> None:
    target_attrs = {
        "src": "/preview.png",
        "alt": "Preview",
        "form": "asset-form",
        "controls": True,
    }
    html = (
        CContextMenu(
            aria_label="Actions",
            target_attrs=target_attrs,
            slots={
                "target": lambda data: CButton(
                    attrs=data.target_attrs,
                    slots={"default": "Target"},
                ),
                "menu": (CMenuItem(value="go", slots={"default": "Go"}),),
            },
        )
        .render(citry=_app())
        .serialize(deps_strategy="ignore")
    )
    assert 'src="/preview.png"' in html
    assert 'alt="Preview"' in html
    assert 'form="asset-form"' in html
    assert "controls" in html

    for attrs in ({"href": "/wrong-root"}, {"type": "button"}):
        component = CContextMenu(
            aria_label="Actions",
            attrs=attrs,
            slots={
                "target": lambda data: CButton(
                    attrs=data.target_attrs,
                    slots={"default": "Target"},
                ),
                "menu": (CMenuItem(value="go", slots={"default": "Go"}),),
            },
        )
        with pytest.raises(ValueError, match="does not allow attribute"):
            component.render(citry=_app())


@pytest.mark.parametrize(
    ("inputs", "error"),
    [
        ('aria_label=""', "must be a string"),
        ('aria_label="Actions" id="bad id"', "ASCII whitespace"),
        ('aria_label="Actions" size="xl"', "size must be one of"),
        ('aria_label="Actions" c-open="1"', "open must be a bool"),
    ],
)
def test_invalid_structural_inputs_fail_synchronously(inputs: str, error: str) -> None:
    template = _context_menu().replace('aria_label="Document actions"', inputs)
    with pytest.raises((TypeError, ValueError), match=error):
        _render(template)


@pytest.mark.parametrize(
    ("input_name", "attrs", "error"),
    [
        ("attrs", {"id": "hostile"}, "owned attribute"),
        ("attrs", {"data-citry-hostile": "x"}, "owned attribute"),
        ("attrs", {"aria-description": "Hostile"}, "owned attribute"),
        ("attrs", {":aria-description": "description"}, "dynamically bind"),
        ("attrs", {"@contextmenu": "x"}, "owned event"),
        ("target_attrs", {"id": "hostile"}, "owned attribute"),
        ("target_attrs", {"role": "button"}, "owned attribute"),
        ("target_attrs", {"disabled": True}, "owned attribute"),
        ("target_attrs", {"@pointerdown": "x"}, "owned event"),
        ("target_attrs", {"x-data": "{}"}, "ownership directive"),
        ("target_attrs", {"is": "fancy-button"}, "owned attribute"),
    ],
)
def test_owned_and_unsafe_attribute_targets_are_rejected(
    input_name: str,
    attrs: dict[str, object],
    error: str,
) -> None:
    kwargs = {input_name: attrs}
    component = CContextMenu(
        aria_label="Actions",
        slots={
            "target": lambda data: CButton(
                attrs=data.target_attrs,
                slots={"default": "Target"},
            ),
            "menu": (CMenuItem(value="go", slots={"default": "Go"}),),
        },
        **kwargs,
    )
    with pytest.raises(ValueError, match=error):
        component.render(citry=_app())


def test_missing_slots_and_empty_collection_fail_through_shared_menu_validation() -> None:
    with pytest.raises((SyntaxError, TypeError, ValueError)):
        _render('<c-CContextMenu aria_label="Actions"></c-CContextMenu>')
    with pytest.raises(ValueError, match="at least one direct declaration"):
        _render(
            """
              <c-CContextMenu aria_label="Actions">
                <c-fill name="target" data="{ target_attrs }">
                  <button c-bind="target_attrs">Target</button>
                </c-fill>
                <c-fill name="menu"></c-fill>
              </c-CContextMenu>
            """
        )


def test_context_menu_depends_on_one_shared_menu_runtime_and_style() -> None:
    assert CContextMenu.Dependencies.js[-1] is _CMENU_SHARED_ASSETS.runtime
    assert CContextMenu.Dependencies.css == [_CMENU_SHARED_ASSETS.style]
    assert getattr(CInternalMenuSurface, "js", None) is None
    assert getattr(CInternalMenuSurface, "css", None) is None
    html = _render(_context_menu(), deps="simple")
    assert html.count("citry-ui:menu-root-runtime") == 2
    assert html.count("externalActivationVersion") >= 2
    assert html.count(".cui-context-menu-host") == 1


def test_js_and_css_assets_are_direct_multiline_literals() -> None:
    assert CContextMenu.js.startswith("\n")
    assert CContextMenu.css.startswith("\n")
    assert "$component({" in CContextMenu.js
    assert "display: contents" in CContextMenu.css
    assert "pointer-events: none" in CContextMenu.css
    assert "user-select" not in CContextMenu.css
    assert "touch-action" not in CContextMenu.css
