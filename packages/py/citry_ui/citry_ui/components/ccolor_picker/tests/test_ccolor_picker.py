from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pytest

import citry_ui
from citry import Citry, Component
from citry_ui import CColorPicker, CColorSwatch


def _render(attrs: str = "", *, swatches: object = ()) -> str:
    app = Citry(autodiscover=False)
    app.register_library(citry_ui)

    class Page(Component):
        citry = app

        def template_data(self, _kwargs, _slots):
            return {"swatches": swatches}

        template = f'<c-CColorPicker label="Brand color" {attrs} c-swatches="swatches" />'

    return str(Page())


def test_schema_registration_normalization_native_fallback_and_swatches() -> None:
    assert [item.name for item in fields(CColorPicker.Kwargs)][:7] == [
        "label",
        "value",
        "id",
        "name",
        "form",
        "format",
        "swatches",
    ]
    assert CColorPicker in citry_ui.COMPONENTS
    html = _render('value="#AbC" name="brand" form="profile" c-open="True"', swatches=[CColorSwatch("#fff", "White")])
    assert 'type="color"' in html
    assert 'value="#aabbcc"' in html
    assert 'name="brand"' in html
    assert 'form="profile"' in html
    assert 'role="dialog"' in html
    assert 'role="slider"' in html
    assert 'data-value="#ffffff"' in html
    assert 'aria-label="White"' in html


@pytest.mark.parametrize(
    ("attrs", "swatches", "match"),
    [
        ('value="red"', (), "#rgb or #rrggbb"),
        ('format="lab"', (), "format must be one of"),
        ('c-open="1"', (), "open must be a bool"),
        ('selected_label="Selected"', (), "must contain"),
        ("", [CColorSwatch("#fff", "White"), CColorSwatch("#ffffff", "Again")], "duplicated"),
        ("", [CColorSwatch("nope", "Bad")], "#rgb or #rrggbb"),
    ],
)
def test_invalid_values_fail(attrs: str, swatches: object, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _render(attrs, swatches=swatches)


def test_assets_docs_and_translations_cover_contract() -> None:
    root = Path(__file__).parents[1]
    js = (root / "runtime.source.js").read_text(encoding="utf8")
    css = (root / "runtime.source.css").read_text(encoding="utf8")
    guide = (root / "api.md").read_text(encoding="utf8")
    reference = (root / "api.yml").read_text(encoding="utf8")
    for fragment in ("ArrowLeft", "PageUp", "parseText", "onValueChange", "removeEventListener"):
        assert fragment in js
    for fragment in ("prefers-reduced-motion", "forced-colors", "@media print"):
        assert fragment in css
    assert guide.count("<c-ui-demo ") == 6
    for suffix in ("open", "area", "hue", "format", "value", "invalid", "selected"):
        assert f"citry-ui-color-picker-{suffix}" in reference
