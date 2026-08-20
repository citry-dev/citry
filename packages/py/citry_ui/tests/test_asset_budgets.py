"""Frozen Citry UI component-catalog asset budgets."""

from __future__ import annotations

import brotli

import citry_ui
from citry import Citry
from citry_ui.quality.asset_report import _family_assets, asset_report


def _assets(*, kind: str, names: set[str] | None = None) -> bytes:
    selected = names or {definition.__name__ for definition in citry_ui.COMPONENTS}
    javascript, css = _family_assets(frozenset(selected))
    return javascript if kind == "js" else css


def test_complete_component_catalog_stays_inside_compressed_asset_budgets() -> None:
    catalog = asset_report()["catalog"]

    assert catalog["javascript"] == {
        "sha256": "f52d5b8e0910b380bfeb15413a008160ddb51893586619e7f42fe2b0d5b5f148",
        "raw": 931_875,
        "gzip": 174_653,
        "brotli": 126_213,
    }
    assert catalog["css"] == {
        "sha256": "88dab541edf4f08b6712d4b531c96004e97b59dbece326485df253ddd12410f5",
        "raw": 323_806,
        "gzip": 39_177,
        "brotli": 30_765,
    }
    assert catalog["limits"] == {
        "javascript": {"raw": 960 * 1024, "gzip": 192 * 1024, "brotli": 128 * 1024},
        "css": {"raw": 336 * 1024, "gzip": 40 * 1024, "brotli": 32 * 1024},
    }
    assert all(value > 0 for values in catalog["headroom"].values() for value in values.values())


def test_basic_action_form_and_table_route_stays_inside_narrow_budget() -> None:
    names = {"CButton", "CCheckbox", "CField", "CInput", "CNativeSelect", "CTable", "CTextarea"}
    javascript = _assets(kind="js", names=names)
    css = _assets(kind="css", names=names)

    assert len(brotli.compress(javascript)) <= 8 * 1024
    assert len(brotli.compress(css)) <= 12 * 1024


def test_semantic_table_has_no_component_javascript() -> None:
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)

    assert installation[citry_ui.CTable].get_js() is None
    assert installation[citry_ui.CCard].get_js() is None


def test_idle_button_runtime_declares_no_retained_global_resource() -> None:
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    javascript = installation[citry_ui.CButton].get_js()

    assert javascript is not None
    assert "MutationObserver" not in javascript
    assert "setInterval" not in javascript
    assert "document.addEventListener" not in javascript
    assert "window.addEventListener" not in javascript
