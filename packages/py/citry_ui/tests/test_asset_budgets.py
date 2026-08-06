"""Frozen Phase 7 Citry UI asset budgets."""

from __future__ import annotations

import gzip

import brotli

import citry_ui
from citry import Citry


def _assets(*, kind: str, names: set[str] | None = None) -> bytes:
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    payloads: list[bytes] = []
    seen: set[bytes] = set()
    for definition in citry_ui.COMPONENTS:
        if names is not None and definition.__name__ not in names:
            continue
        concrete = installation[definition]
        value = concrete.get_js() if kind == "js" else concrete.get_css()
        if value is None:
            continue
        payload = value.encode()
        if payload not in seen:
            seen.add(payload)
            payloads.append(payload)
    return b"\n".join(payloads)


def test_complete_phase7_slice_stays_inside_compressed_asset_budgets() -> None:
    javascript = _assets(kind="js")
    css = _assets(kind="css")

    assert len(brotli.compress(javascript)) <= 45 * 1024
    assert len(brotli.compress(css)) <= 30 * 1024
    assert len(gzip.compress(javascript)) > 0
    assert len(gzip.compress(css)) > 0


def test_basic_action_form_and_table_route_stays_inside_narrow_budget() -> None:
    names = {"CButton", "CField", "CInput", "CTable"}
    javascript = _assets(kind="js", names=names)
    css = _assets(kind="css", names=names)

    assert len(brotli.compress(javascript)) <= 8 * 1024
    assert len(brotli.compress(css)) <= 12 * 1024


def test_semantic_table_has_no_component_javascript() -> None:
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)

    assert installation[citry_ui.CTable].get_js() is None


def test_idle_button_runtime_declares_no_retained_global_resource() -> None:
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    javascript = installation[citry_ui.CButton].get_js()

    assert javascript is not None
    assert "MutationObserver" not in javascript
    assert "setInterval" not in javascript
    assert "document.addEventListener" not in javascript
    assert "window.addEventListener" not in javascript
