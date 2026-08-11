"""Frozen Citry UI component-catalog asset budgets."""

from __future__ import annotations

import gzip

import brotli

import citry_ui
from citry import Citry
from citry_ui.quality.asset_report import _family_assets


def _assets(*, kind: str, names: set[str] | None = None) -> bytes:
    selected = names or {definition.__name__ for definition in citry_ui.COMPONENTS}
    javascript, css = _family_assets(frozenset(selected))
    return javascript if kind == "js" else css


def test_complete_component_catalog_stays_inside_compressed_asset_budgets() -> None:
    javascript = _assets(kind="js")
    css = _assets(kind="css")

    assert len(brotli.compress(javascript)) <= 80 * 1024
    assert len(brotli.compress(css)) <= 30 * 1024
    assert len(gzip.compress(javascript)) > 0
    assert len(gzip.compress(css)) > 0


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
