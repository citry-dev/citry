"""Report reproducible Citry UI asset bytes by component family."""

from __future__ import annotations

import gzip
import json
import sys
from dataclasses import asdict, dataclass

import brotli

import citry_ui
from citry import Citry

_FAMILY_COMPONENTS = {
    "button": frozenset({"CButton"}),
    "field-input": frozenset({"CField", "CInput"}),
    "form": frozenset({"CForm"}),
    "tabs": frozenset(
        {
            "CTabs",
            "CTab",
            "CTabPanel",
            "CInternalTabsDeclarations",
            "CInternalTabs",
            "CInternalTab",
            "CInternalTabPanel",
        },
    ),
    "dialog": frozenset({"CDialog"}),
    "combobox": frozenset({"CCombobox"}),
    "table": frozenset({"CTable"}),
}


@dataclass(frozen=True, slots=True)
class AssetBytes:
    """Raw and compressed bytes for one asset kind."""

    raw: int
    gzip: int
    brotli: int


def _measure(payload: bytes) -> AssetBytes:
    if not payload:
        return AssetBytes(raw=0, gzip=0, brotli=0)
    return AssetBytes(
        raw=len(payload),
        gzip=len(gzip.compress(payload, mtime=0)),
        brotli=len(brotli.compress(payload)),
    )


def _family_assets(names: frozenset[str]) -> tuple[bytes, bytes]:
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    values: dict[str, list[bytes]] = {"js": [], "css": []}
    seen: dict[str, set[bytes]] = {"js": set(), "css": set()}
    for definition in citry_ui.COMPONENTS:
        if definition.__name__ not in names:
            continue
        concrete = installation[definition]
        for kind, value in (("js", concrete.get_js()), ("css", concrete.get_css())):
            if value is None:
                continue
            payload = value.encode()
            if payload not in seen[kind]:
                seen[kind].add(payload)
                values[kind].append(payload)
    return b"\n".join(values["js"]), b"\n".join(values["css"])


def asset_report() -> dict[str, object]:
    """Return deterministic per-family and full-catalog byte counts."""
    families: dict[str, object] = {}
    for family, names in _FAMILY_COMPONENTS.items():
        javascript, css = _family_assets(names)
        families[family] = {
            "components": sorted(names),
            "javascript": asdict(_measure(javascript)),
            "css": asdict(_measure(css)),
        }
    javascript, css = _family_assets(frozenset(definition.__name__ for definition in citry_ui.COMPONENTS))
    return {
        "schema": "citry-ui-asset-report/v1",
        "families": families,
        "catalog": {
            "javascript": asdict(_measure(javascript)),
            "css": asdict(_measure(css)),
        },
    }


if __name__ == "__main__":
    sys.stdout.write(json.dumps(asset_report(), indent=2, sort_keys=True) + "\n")
