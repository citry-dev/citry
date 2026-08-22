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
    "image": frozenset({"CImage"}),
    "skeleton": frozenset({"CSkeleton"}),
    "button": frozenset({"CButton"}),
    "split-button": frozenset({"CSplitButton"}),
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
            "CInternalMenuSurface",
        }
    ),
    "context-menu": frozenset({"CContextMenu"}),
    "toast": frozenset({"CToastRegion"}),
    "combobox": frozenset({"CCombobox"}),
    "command-palette": frozenset({"CCommandPalette"}),
    "table": frozenset({"CTable"}),
    "data-grid": frozenset({"CDataGrid"}),
    "icon": frozenset({"CIcon"}),
    "card": frozenset({"CCard"}),
    "carousel": frozenset({"CCarousel", "CCarouselSlide"}),
    "timeline": frozenset(
        {
            "CTimeline",
            "CTimelineItem",
            "CInternalTimelineDeclarations",
            "CInternalTimeline",
            "CInternalTimelineItem",
        }
    ),
    "scroll-area": frozenset({"CScrollArea"}),
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
    "tags-input": frozenset({"CTagsInput"}),
    "number-input": frozenset({"CNumberInput"}),
    "slider": frozenset({"CSlider", "CRangeSlider"}),
    "rating": frozenset({"CRating"}),
    "pin-input": frozenset({"CPinInput"}),
    "date-input": frozenset({"CDateInput"}),
    "date-picker": frozenset({"CDatePicker"}),
    "date-range": frozenset({"CDateRange"}),
    "calendar": frozenset({"CCalendar"}),
    "time-input": frozenset({"CTimeInput"}),
    "time-picker": frozenset({"CTimePicker"}),
    "navigation-menu": frozenset({"CNavigationMenu", "CNavigationMenuLink", "CNavigationMenuItem"}),
    "sidebar": frozenset({"CSidebar"}),
    "tour": frozenset(
        {
            "CTour",
            "CTourStep",
            "CInternalTourDeclarations",
            "CInternalTour",
            "CInternalTourStep",
        }
    ),
    "editable": frozenset({"CEditable"}),
    "virtual-list": frozenset(
        {
            "CVirtualList",
            "CVirtualListItem",
            "CVirtualWindow",
            "CInternalVirtualListDeclarations",
            "CInternalVirtualList",
            "CInternalVirtualListStatic",
            "CInternalVirtualListWindow",
            "CInternalVirtualListItem",
        }
    ),
    "transfer-list": frozenset(
        {
            "CTransferList",
            "CTransferListItem",
            "CInternalTransferListDeclarations",
            "CInternalTransferList",
            "CInternalTransferListItem",
        }
    ),
    "form-collection": frozenset(
        {
            "CFormCollection",
            "CFormCollectionItem",
            "CInternalFormCollectionDeclarations",
            "CInternalFormCollection",
            "CInternalFormCollectionItem",
        }
    ),
    "sortable": frozenset(
        {
            "CSortable",
            "CSortableItem",
            "CInternalSortableDeclarations",
            "CInternalSortable",
            "CInternalSortableItem",
        }
    ),
    "infinite-scroll": frozenset({"CInfiniteScroll"}),
    "cascader": frozenset(
        {
            "CCascader",
            "CCascaderOption",
            "CInternalCascaderDeclarations",
            "CInternalCascader",
            "CInternalCascaderGroup",
            "CInternalCascaderOption",
        }
    ),
    "tree-grid": frozenset({"CTreeGrid"}),
    "color-picker": frozenset({"CColorPicker"}),
}

_INCREMENTAL_BASELINES = {
    "image": frozenset(),
    "scroll-area": frozenset(),
    "context-menu": frozenset({"CMenu", "CSplitButton"}),
    "split-button": frozenset({"CButton", "CMenu"}),
    "tags-input": frozenset({"CField", "CMultiSelect", "CTag"}),
    "command-palette": frozenset({"CDialog", "CCombobox"}),
}


@dataclass(frozen=True, slots=True)
class AssetBytes:
    """Raw and compressed bytes for one asset kind."""

    raw: int
    gzip: int
    brotli: int


_CATALOG_ASSET_LIMITS = {
    "javascript": AssetBytes(raw=1088 * 1024, gzip=208 * 1024, brotli=152 * 1024),
    "css": AssetBytes(raw=368 * 1024, gzip=48 * 1024, brotli=40 * 1024),
}


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


def _family_asset_payloads(
    names: frozenset[str],
    *,
    installation: LibraryInstallation | None = None,
) -> dict[str, tuple[bytes, ...]]:
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
    return {kind: tuple(payloads) for kind, payloads in values.items()}


def _family_assets(
    names: frozenset[str],
    *,
    installation: LibraryInstallation | None = None,
) -> tuple[bytes, bytes]:
    payloads = _family_asset_payloads(names, installation=installation)
    return b"\n".join(payloads["js"]), b"\n".join(payloads["css"])


def _incremental_family_assets(
    baseline_names: frozenset[str],
    added_names: frozenset[str],
    *,
    installation: LibraryInstallation | None = None,
) -> tuple[bytes, bytes]:
    """Return only payloads introduced beyond a shared component baseline."""
    baseline = _family_asset_payloads(baseline_names, installation=installation)
    combined = _family_asset_payloads(baseline_names | added_names, installation=installation)
    incremental = {
        kind: tuple(payload for payload in combined[kind] if payload not in set(baseline[kind]))
        for kind in ("js", "css")
    }
    return b"\n".join(incremental["js"]), b"\n".join(incremental["css"])


def asset_report() -> dict[str, object]:
    """Return deterministic per-family and full-catalog byte counts."""
    app = Citry(autodiscover=False)
    installation = app.register_library(citry_ui)
    families: dict[str, object] = {}
    for family, names in _FAMILY_COMPONENTS.items():
        javascript, css = _family_assets(names, installation=installation)
        record: dict[str, object] = {
            "components": sorted(names),
            "javascript": asdict(_measure(javascript)),
            "css": asdict(_measure(css)),
        }
        baseline_names = _INCREMENTAL_BASELINES.get(family)
        if baseline_names is not None:
            incremental_javascript, incremental_css = _incremental_family_assets(
                baseline_names,
                names,
                installation=installation,
            )
            record["incremental"] = {
                "baseline_components": sorted(baseline_names),
                "javascript": asdict(_measure(incremental_javascript)),
                "css": asdict(_measure(incremental_css)),
            }
        families[family] = record
    javascript, css = _family_assets(
        frozenset(definition.__name__ for definition in citry_ui.COMPONENTS),
        installation=installation,
    )
    catalog_javascript = asdict(_measure(javascript))
    catalog_css = asdict(_measure(css))
    return {
        "schema": "citry-ui-asset-report/v1",
        "families": families,
        "catalog": {
            "javascript": catalog_javascript,
            "css": catalog_css,
            "limits": {kind: asdict(limit) for kind, limit in _CATALOG_ASSET_LIMITS.items()},
            "headroom": {
                "javascript": {
                    dimension: int(getattr(_CATALOG_ASSET_LIMITS["javascript"], dimension))
                    - int(catalog_javascript[dimension])
                    for dimension in ("raw", "gzip", "brotli")
                },
                "css": {
                    dimension: int(getattr(_CATALOG_ASSET_LIMITS["css"], dimension)) - int(catalog_css[dimension])
                    for dimension in ("raw", "gzip", "brotli")
                },
            },
        },
    }


if __name__ == "__main__":
    sys.stdout.write(json.dumps(asset_report(), indent=2, sort_keys=True) + "\n")
