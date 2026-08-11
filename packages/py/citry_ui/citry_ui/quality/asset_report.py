"""Report reproducible Citry UI asset bytes by component family."""

from __future__ import annotations

import gzip
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import brotli

import citry_ui
from citry import Citry, Component, LibraryInstallation
from citry.ext.dependencies import Dependency

_FAMILY_COMPONENTS = {
    "accordion": frozenset(
        {
            "CAccordion",
            "CAccordionItem",
            "CInternalAccordionItems",
            "CInternalAccordionPanelContent",
        }
    ),
    "disclosure": frozenset({"CDisclosure"}),
    "alert": frozenset({"CAlert"}),
    "alert-dialog": frozenset({"CAlertDialog"}),
    "avatar": frozenset({"CAvatar"}),
    "skeleton": frozenset({"CSkeleton"}),
    "button": frozenset({"CButton"}),
    "divider": frozenset({"CDivider"}),
    "field-input": frozenset({"CField", "CInput"}),
    "file-input": frozenset({"CFileInput", "CDropTarget"}),
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
    "drawer": frozenset({"CDrawer"}),
    "popover": frozenset({"CPopover"}),
    "tooltip": frozenset({"CTooltip"}),
    "hover-card": frozenset({"CHoverCard"}),
    "menu": frozenset(
        {
            "CMenu",
            "CMenuItem",
            "CMenuCheckboxItem",
            "CMenuRadioGroup",
            "CMenuRadioItem",
            "CMenuGroup",
            "CMenuSeparator",
            "CMenuSubmenu",
            "CInternalMenuCollection",
            "CInternalMenuContent",
        }
    ),
    "toast": frozenset({"CToastRegion"}),
    "combobox": frozenset({"CCombobox"}),
    "table": frozenset({"CTable"}),
    "icon": frozenset({"CIcon"}),
    "card": frozenset({"CCard"}),
    "carousel": frozenset({"CCarousel", "CCarouselSlide"}),
    "textarea": frozenset({"CTextarea"}),
    "native-select": frozenset({"CNativeSelect"}),
    "checkbox": frozenset({"CCheckbox"}),
    "button-group": frozenset({"CButtonGroup", "CButton"}),
    "toggle": frozenset({"CToggleGroup", "CToggle"}),
    "tag": frozenset({"CTagGroup", "CTag"}),
    "toolbar": frozenset({"CToolbar"}),
    "stepper": frozenset({"CStepper", "CStep", "CInternalStepperDeclarations", "CInternalStepper", "CInternalStep"}),
    "splitter": frozenset(
        {
            "CSplitter",
            "CSplitterPanel",
            "CInternalSplitterDeclarations",
            "CInternalSplitter",
            "CInternalSplitterPanel",
            "CInternalSplitterHandle",
        }
    ),
    "tree": frozenset({"CTree", "CTreeItem"}),
    "pagination": frozenset({"CPagination"}),
    "list": frozenset({"CList", "CListItem"}),
    "listbox": frozenset({"CListbox", "CListboxOption", "CListboxGroup"}),
    "select": frozenset({"CSelect"}),
    "multi-select": frozenset({"CMultiSelect"}),
    "navigation-menu": frozenset({"CNavigationMenu", "CNavigationMenuLink", "CNavigationMenuItem"}),
    "editable": frozenset({"CEditable"}),
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


def _secondary_asset_payloads(component: type[Component], *, kind: str) -> tuple[bytes, ...]:
    dependencies = component.get_dependencies()
    entries = (
        dependencies.js if kind == "js" else tuple(entry for values in dependencies.css.values() for entry in values)
    )
    payloads: list[bytes] = []
    for entry in entries:
        if isinstance(entry, Dependency):
            content = entry.render_json()["content"]
            if content:
                payloads.append(str(content).encode())
        elif isinstance(entry, Path):
            payloads.append(entry.read_bytes())
        # URL and pre-rendered dependencies have no locally measurable payload.
    return tuple(payloads)


def _family_assets(
    names: frozenset[str],
    *,
    installation: LibraryInstallation | None = None,
) -> tuple[bytes, bytes]:
    # Standalone callers still get an isolated installation, while a report
    # reuses one immutable catalog across every family it measures.
    if installation is None:
        app = Citry(autodiscover=False)
        installation = app.register_library(citry_ui)
    values: dict[str, list[bytes]] = {"js": [], "css": []}
    seen: dict[str, set[bytes]] = {"js": set(), "css": set()}
    for definition in citry_ui.COMPONENTS:
        if definition.__name__ not in names:
            continue
        concrete = installation[definition]
        for kind, value in (("js", concrete.get_js()), ("css", concrete.get_css())):
            payloads = () if value is None else (value.encode(),)
            payloads = (*payloads, *_secondary_asset_payloads(concrete, kind=kind))
            for payload in payloads:
                if payload not in seen[kind]:
                    seen[kind].add(payload)
                    values[kind].append(payload)
    return b"\n".join(values["js"]), b"\n".join(values["css"])


def asset_report() -> dict[str, object]:
    """Return deterministic per-family and full-catalog byte counts."""
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    families: dict[str, object] = {}
    for family, names in _FAMILY_COMPONENTS.items():
        javascript, css = _family_assets(names, installation=installation)
        families[family] = {
            "components": sorted(names),
            "javascript": asdict(_measure(javascript)),
            "css": asdict(_measure(css)),
        }
    javascript, css = _family_assets(
        frozenset(definition.__name__ for definition in citry_ui.COMPONENTS),
        installation=installation,
    )
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
