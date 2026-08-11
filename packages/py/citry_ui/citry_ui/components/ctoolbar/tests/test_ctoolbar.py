from __future__ import annotations

import re
from dataclasses import fields
from typing import get_type_hints

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CToolbar


def _render(template: str, *, include_css: bool = False, data: dict[str, object] | None = None) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)
    source = template + ("{{ css }}" if include_css else "")

    class Page(Component):
        citry = app
        template = source

        def template_data(self, kwargs, slots):
            return {"css": app.get("css")(), **(data or {})}

    return str(Page())


def _root(html: str) -> str:
    match = re.search(r'<div[^>]+data-citry-ui-part="toolbar"[^>]*>', html)
    assert match is not None
    return match.group(0)


def _toolbar(children: str = "<button>A</button><button>B</button><a href='/c'>C</a>") -> str:
    return f'<c-CToolbar label="Editor tools">{children}</c-CToolbar>'


def test_schema_defaults_and_public_types_are_exact() -> None:
    assert [field.name for field in fields(CToolbar.Kwargs)] == [
        "label",
        "orientation",
        "loop",
        "variant",
        "size",
        "class_",
        "style",
        "attrs",
    ]
    assert [field.name for field in fields(CToolbar.Slots)] == ["default"]
    hints = get_type_hints(CToolbar.Kwargs)
    assert hints["orientation"] == citry_ui.CToolbarOrientation
    assert hints["variant"] == citry_ui.CToolbarVariant
    assert hints["size"] == citry_ui.CToolbarSize
    assert CToolbar in citry_ui.__citry_library__.components


def test_default_toolbar_renders_named_horizontal_composite() -> None:
    root = _root(_render(_toolbar()))
    assert 'role="toolbar"' in root
    assert 'aria-label="Editor tools"' in root
    assert 'aria-orientation="horizontal"' in root
    assert 'data-orientation="horizontal"' in root
    assert "data-loop" in root
    assert 'data-variant="plain"' in root
    assert 'data-size="md"' in root


def test_configuration_and_root_customization_are_exact() -> None:
    root = _root(
        _render(
            '<c-CToolbar label="Map tools" orientation="vertical" c-loop="False" '
            'variant="outline" size="lg" class_="custom" '
            "style=\"inline-size:20rem\" c-attrs=\"{'data-test': 'toolbar'}\">"
            "<button>A</button><button>B</button><button>C</button></c-CToolbar>"
        )
    )
    assert 'class="cui-toolbar custom"' in root
    assert 'style="inline-size: 20rem;"' in root
    assert 'data-test="toolbar"' in root
    assert 'aria-orientation="vertical"' in root
    assert "data-loop" not in root
    assert 'data-variant="outline"' in root
    assert 'data-size="lg"' in root


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (_toolbar().replace('label="Editor tools"', "c-label=\"''\""), ValueError),
        (_toolbar().replace('label="Editor tools"', 'label="Editor" orientation="diagonal"'), ValueError),
        (_toolbar().replace('label="Editor tools"', 'label="Editor" variant="solid"'), ValueError),
        (_toolbar().replace('label="Editor tools"', 'label="Editor" size="xl"'), ValueError),
        (_toolbar().replace('label="Editor tools"', 'label="Editor" c-loop="1"'), TypeError),
        ('<c-CToolbar label="Editor"></c-CToolbar>', SyntaxError),
        (_toolbar().replace('label="Editor tools"', 'label="Editor" c-attrs="[]"'), TypeError),
    ],
)
def test_invalid_server_inputs_fail(template: str, error: type[Exception]) -> None:
    with pytest.raises(error):
        _render(template)


@pytest.mark.parametrize(
    "attribute",
    [
        "role",
        "aria-label",
        "aria-orientation",
        "tabindex",
        "hidden",
        "inert",
        ":data-size",
        "x-show",
        "x-ignore.self",
        "data-citry-toolbar-initialized",
    ],
)
def test_owned_runtime_and_visibility_attributes_are_rejected(attribute: str) -> None:
    with pytest.raises(ValueError, match="cannot"):
        _render(
            '<c-CToolbar label="Editor" c-attrs="attrs">'
            "<button>A</button><button>B</button><button>C</button></c-CToolbar>",
            data={"attrs": {attribute: "consumer"}},
        )


def test_css_contract_uses_public_inputs_through_private_fallbacks() -> None:
    html = _render(_toolbar(), include_css=True)
    for name in (
        "gap",
        "padding",
        "min-height",
        "radius",
        "background",
        "foreground",
        "border-color",
        "focus-color",
    ):
        assert re.search(rf"--_cui-toolbar-{name}: var\(\s*--cui-toolbar-{name},", html)
    assert "@media (forced-colors: active)" in html
    assert "@media (prefers-reduced-motion: reduce)" in html
