"""Report reproducible Citry UI asset bytes by component family."""

from __future__ import annotations

import gzip
import hashlib
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path

import brotli

import citry_ui
from citry import Citry, Component, LibraryInstallation
from citry.ext.dependencies import Dependency
from citry_ui.components.ccommand_palette import CCommandPalette

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
}

_INCREMENTAL_BASELINES = {
    "image": frozenset(),
    "scroll-area": frozenset(),
    "context-menu": frozenset({"CMenu", "CSplitButton"}),
    "split-button": frozenset({"CButton", "CMenu"}),
    "tags-input": frozenset({"CField", "CMultiSelect", "CTag"}),
    "command-palette": frozenset({"CDialog", "CCombobox"}),
}

_CONTEXT_MENU_ASSET_PROVENANCE = {
    "context_javascript_source": {
        "sha256": "d74fd1adf4be44ed687c4753633a1e46c900b8d0710b58a5c4802a18a4bc4315",
        "raw": 28_081,
        "gzip": 9_088,
        "brotli": 8_262,
    },
    "context_css_source": {
        "sha256": "22979cafffdd6a575000af38ba46f75bab8eed45c72bd7f2351b02d53eaf603a",
        "raw": 575,
        "gzip": 257,
        "brotli": 193,
    },
    "menu_runtime_before_context": {
        "sha256": "1c44a9bbc35186fdcabb1a0e7f9f23e62f4743c462614a4fb33c8f65bafb4116",
        "raw": 82_023,
        "gzip": 15_494,
        "brotli": 12_999,
    },
    "menu_runtime_after_context": {
        "sha256": "cf6d144c5b4fe322010e8c02d35ac4581cecbcb0bb4721de527abde47f473178",
        "raw": 85_640,
        "gzip": 16_142,
        "brotli": 13_538,
    },
    "anchored_layer_before_context": {
        "sha256": "ca5ab04ec15f4abaa17a6878ea209e0165175cae0188b0c058d64f1273682624",
        "raw": 29_168,
        "gzip": 5_521,
        "brotli": 4_803,
    },
    "anchored_layer_after_context": {
        "sha256": "a695ff7cd36c37848769a072084679de0c815928a1eddd234a55fcd4fef9a3e2",
        "raw": 29_514,
        "gzip": 5_598,
        "brotli": 4_871,
    },
}


@dataclass(frozen=True, slots=True)
class AssetBytes:
    """Raw and compressed bytes for one asset kind."""

    raw: int
    gzip: int
    brotli: int


_CATALOG_ASSET_LIMITS = {
    "javascript": AssetBytes(raw=1024 * 1024, gzip=192 * 1024, brotli=144 * 1024),
    "css": AssetBytes(raw=360 * 1024, gzip=44 * 1024, brotli=36 * 1024),
}


_CONTEXT_MENU_SHARED_JAVASCRIPT_DELTA = AssetBytes(raw=3_963, gzip=725, brotli=607)

_IMAGE_ASSET_PROVENANCE = {
    "javascript_source": {
        "sha256": "75b74be92b6761ef0c2194474eefc0e99e69ef409b79037b4c61caf47ef36f53",
        "raw": 31_583,
        "gzip": 6_534,
        "brotli": 5_734,
    },
    "css_source": {
        "sha256": "113c53abe2c901f3858e9bb6faad27d003da53c857adc2f984e38b9fbd0359e6",
        "raw": 3_063,
        "gzip": 680,
        "brotli": 553,
    },
    "terser_lower_bound": {
        "sha256": "7d7e133da45731d825bf47c13ea83157b5dc5ecfaeb47a4928ffecab2b859b35",
        "raw": 13_361,
        "gzip": 4_705,
        "brotli": 4_209,
    },
}

_COMMAND_PALETTE_MARKERS = (
    "initializer",
    "dialog-layer-preparation",
    "dialog-document-lock-state",
    "dialog-handoff-keys",
    "dialog-root-scope-state",
    "dialog-document-lock",
    "dialog-root-scope-manager",
    "dialog-handoff-close-state",
    "dialog-focus-target",
    "dialog-handoff-consume",
    "dialog-focus-hooks",
    "dialog-focus-restore",
    "dialog-handoff-close-intent",
    "dialog-handoff-close-expected",
    "dialog-handoff-close-reclaim",
    "dialog-handoff-close-retire",
    "dialog-root-scope-refresh",
    "dialog-handoff-close-listener",
    "dialog-handoff-close-cleanup",
    "dialog-handoff-close-unlisten",
    "dialog-handoff-produce",
    "dialog-handoff-abort",
    "active-owner-key",
    "active-owner-transfer",
    "active-neighbor-handoff",
    "active-group-registration",
    "active-owner-cleanup",
)

_COMMAND_PALETTE_SHARED_BASELINES: dict[str, dict[str, str | int]] = {
    "dialog": {
        "sha256": "17b49a6cc706860b32316c42c6d4822e1d85f245e508e9af07995933d2ca50db",
        "raw": 17_870,
        "gzip": 4_327,
        "brotli": 3_723,
    },
    "anchored-layer": {
        "sha256": "dcdb81484caa8915fda8df0496f69ee32bfb60f73a991620626bdf9b0b190951",
        "raw": 29_534,
        "gzip": 5_607,
        "brotli": 4_882,
    },
    "combobox": {
        "sha256": "f1d24c5827e40c9990542b61375ab8aaa880b0703818bca1506df8cf760f078e",
        "raw": 38_243,
        "gzip": 7_596,
        "brotli": 6_648,
    },
}

_COMMAND_PALETTE_SOURCE_FREEZE = {
    "citry_ui.components.cdialog.cdialog": "21560ee8b89e73feba2f6800f149523a61de0a3f332d1aad60c40136fd7d84e4",
    "citry_ui.components.ccombobox.ccombobox": "447c48f29ca4626d238e966ad1aaef85e5565abfa2aabed1c1143304c81c5257",
    "citry_ui.components._dialog_controller": "5439f917d4918c8926ee82f0a33056ae58d4f2a0b2c7bd903308df37b9c157c3",
    "citry_ui.components._active_descendant": "041544b5de5f5d59bc8ca8d5910516347f27c2e2591a48aca7c7f27d409766c6",
    "citry_ui.components._anchored_layer": "7a27e4491359af9a4f916726e1423d1fd846fe55e9be24063748c2d8798f9694",
}


def _measure(payload: bytes) -> AssetBytes:
    if not payload:
        return AssetBytes(raw=0, gzip=0, brotli=0)
    return AssetBytes(
        raw=len(payload),
        gzip=len(gzip.compress(payload, mtime=0)),
        brotli=len(brotli.compress(payload)),
    )


def _frame(payload: bytes) -> dict[str, str | int]:
    """Describe one independently emitted asset frame."""
    return {"sha256": hashlib.sha256(payload).hexdigest(), **asdict(_measure(payload))}


def _marked_slice(payloads: tuple[bytes, ...], marker: str) -> bytes:
    """Extract one complete, uniquely owned CommandPalette marker block."""
    prefix = f"/* citry-ui:command-palette-attribution:{marker}:".encode()
    begin = prefix + b"begin */"
    end = prefix + b"end */"
    matches: list[bytes] = []
    for payload in payloads:
        if begin not in payload and end not in payload:
            continue
        if payload.count(begin) != 1 or payload.count(end) != 1:
            raise ValueError(f"CommandPalette asset marker {marker!r} is not unique.")
        start = payload.index(begin)
        stop = payload.index(end, start) + len(end)
        matches.append(payload[start:stop])
    if len(matches) != 1:
        raise ValueError(f"CommandPalette asset marker {marker!r} must occur in one frame.")
    return matches[0]


def _validate_marker_ownership(payloads: tuple[bytes, ...], markers: tuple[str, ...]) -> None:
    prefix = b"citry-ui:command-palette-attribution:"
    if sum(payload.count(prefix) for payload in payloads) != len(markers) * 2:
        raise ValueError("CommandPalette asset markers do not match the frozen ownership set.")
    for payload in payloads:
        spans: list[tuple[int, int]] = []
        for marker in markers:
            begin = f"/* citry-ui:command-palette-attribution:{marker}:begin */".encode()
            end = f"/* citry-ui:command-palette-attribution:{marker}:end */".encode()
            if begin not in payload and end not in payload:
                continue
            if payload.count(begin) != 1 or payload.count(end) != 1:
                raise ValueError(f"CommandPalette asset marker {marker!r} is not unique.")
            start = payload.index(begin)
            stop = payload.index(end, start) + len(end)
            spans.append((start, stop))
        spans.sort()
        if any(previous[1] > current[0] for previous, current in pairwise(spans)):
            raise ValueError("CommandPalette asset markers overlap.")


def _strip_marked_slices(payload: bytes, markers: tuple[str, ...]) -> bytes:
    for marker in markers:
        begin = f"/* citry-ui:command-palette-attribution:{marker}:begin */".encode()
        end = f"/* citry-ui:command-palette-attribution:{marker}:end */".encode()
        if begin not in payload and end not in payload:
            continue
        if payload.count(begin) != 1 or payload.count(end) != 1:
            raise ValueError(f"CommandPalette asset marker {marker!r} is not unique.")
        start = payload.index(begin)
        stop = payload.index(end, start) + len(end)
        payload = payload[:start] + payload[stop:]
    return payload


def _positive_delta(current: AssetBytes, baseline: dict[str, str | int]) -> AssetBytes:
    return AssetBytes(
        raw=max(0, current.raw - int(baseline["raw"])),
        gzip=max(0, current.gzip - int(baseline["gzip"])),
        brotli=max(0, current.brotli - int(baseline["brotli"])),
    )


def _command_palette_source_freeze() -> dict[str, str]:
    actual: dict[str, str] = {}
    for module_name, expected in _COMMAND_PALETTE_SOURCE_FREEZE.items():
        module_path = Path(importlib.import_module(module_name).__file__ or "")
        digest = hashlib.sha256(module_path.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError(f"CommandPalette correctness-freeze source changed: {module_name}.")
        actual[module_name] = digest
    return actual


def _command_palette_shared_foundations(
    payloads: dict[str, tuple[bytes, ...]],
    dialog_payloads: dict[str, tuple[bytes, ...]],
    combobox_payloads: dict[str, tuple[bytes, ...]],
) -> tuple[dict[str, dict[str, object]], AssetBytes]:
    dialog_markers = tuple(marker for marker in _COMMAND_PALETTE_MARKERS if marker.startswith("dialog-"))
    active_markers = tuple(marker for marker in _COMMAND_PALETTE_MARKERS if marker.startswith("active-"))

    def dependency_frame(marker: str) -> bytes:
        begin = f"/* citry-ui:command-palette-attribution:{marker}:begin */".encode()
        matches = tuple(payload for payload in payloads["js"] if begin in payload)
        if len(matches) != 1:
            raise ValueError(f"CommandPalette shared frame for {marker!r} must be unique.")
        return matches[0]

    def primary_frame(name: str, frames: tuple[bytes, ...]) -> bytes:
        # _family_asset_payloads always places concrete.get_js() before its
        # secondary dependencies. The exact emitted hash remains a separate
        # frozen assertion, while this position lets the report recompute a
        # changed live logical frame and its positive delta.
        if not frames or not frames[0]:
            raise ValueError(f"CommandPalette live {name} primary frame is missing.")
        return frames[0]

    dialog_helper = dependency_frame("dialog-document-lock-state")
    anchored = dependency_frame("dialog-layer-preparation")
    active_helper = dependency_frame("active-owner-key")
    logical_payloads = {
        "dialog": primary_frame("dialog", dialog_payloads["js"]) + _strip_marked_slices(dialog_helper, dialog_markers),
        "anchored-layer": _strip_marked_slices(anchored, ("dialog-layer-preparation",)),
        "combobox": primary_frame("combobox", combobox_payloads["js"])
        + _strip_marked_slices(active_helper, active_markers),
    }
    foundations: dict[str, dict[str, object]] = {}
    deltas: list[AssetBytes] = []
    for name, payload in logical_payloads.items():
        current = _measure(payload)
        baseline = _COMMAND_PALETTE_SHARED_BASELINES[name]
        delta = _positive_delta(current, baseline)
        deltas.append(delta)
        foundations[name] = {
            "baseline": dict(baseline),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "current": asdict(current),
            "positive_delta": asdict(delta),
        }
    return foundations, _sum_asset_bytes(*deltas)


def _command_palette_attribution(
    payloads: dict[str, tuple[bytes, ...]],
    dialog_payloads: dict[str, tuple[bytes, ...]],
    combobox_payloads: dict[str, tuple[bytes, ...]],
) -> dict[str, object]:
    _validate_marker_ownership(payloads["js"], _COMMAND_PALETTE_MARKERS)
    _validate_marker_ownership(payloads["css"], ("css",))
    javascript_slices = tuple(_marked_slice(payloads["js"], marker) for marker in _COMMAND_PALETTE_MARKERS)
    css_slice = _marked_slice(payloads["css"], "css")
    attributed_javascript = b"".join(javascript_slices)
    attributed_css = css_slice
    standalone_javascript = b"".join(payloads["js"])
    standalone_css = b"".join(payloads["css"])
    attributed_javascript_bytes = _measure(attributed_javascript)
    shared_foundations, shared_javascript_delta = _command_palette_shared_foundations(
        payloads,
        dialog_payloads,
        combobox_payloads,
    )
    return {
        "provenance": {
            "javascript_source": _frame(CCommandPalette.js.encode()),
            "css_source": _frame(CCommandPalette.css.encode()),
            "shared_source_freeze": _command_palette_source_freeze(),
        },
        "emitted": {
            "js": tuple(_frame(payload) for payload in payloads["js"]),
            "css": tuple(_frame(payload) for payload in payloads["css"]),
        },
        "marker_slices": {
            "javascript": tuple(
                {"marker": marker, **_frame(payload)}
                for marker, payload in zip(_COMMAND_PALETTE_MARKERS, javascript_slices, strict=True)
            ),
            "css": ({"marker": "css", **_frame(css_slice)},),
        },
        "attributed": {
            "javascript": _frame(attributed_javascript),
            "css": _frame(attributed_css),
        },
        "shared_foundations": shared_foundations,
        "shared_positive_delta": {
            "javascript": asdict(shared_javascript_delta),
            "css": asdict(AssetBytes(raw=0, gzip=0, brotli=0)),
        },
        "charged": {
            "javascript": asdict(_sum_asset_bytes(attributed_javascript_bytes, shared_javascript_delta)),
            "css": asdict(_measure(attributed_css)),
        },
        "standalone": {
            "javascript": _frame(standalone_javascript),
            "css": _frame(standalone_css),
        },
    }


def _sum_asset_bytes(*values: AssetBytes) -> AssetBytes:
    return AssetBytes(
        raw=sum(value.raw for value in values),
        gzip=sum(value.gzip for value in values),
        brotli=sum(value.brotli for value in values),
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


def _family_asset_frames(
    names: frozenset[str],
    *,
    installation: LibraryInstallation | None = None,
) -> dict[str, tuple[dict[str, str | int], ...]]:
    """Return ordered hashes and sizes for every unique emitted frame."""
    payloads = _family_asset_payloads(names, installation=installation)
    return {kind: tuple(_frame(payload) for payload in values) for kind, values in payloads.items()}


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
        if family == "context-menu":
            adapter_javascript, adapter_css = _incremental_family_assets(
                _INCREMENTAL_BASELINES[family],
                names,
                installation=installation,
            )
            adapter_javascript_bytes = _measure(adapter_javascript)
            record["attribution"] = {
                "provenance": {name: dict(frame) for name, frame in _CONTEXT_MENU_ASSET_PROVENANCE.items()},
                "adapter": {
                    "javascript": _frame(adapter_javascript),
                    "css": _frame(adapter_css),
                },
                "shared_positive_delta": {
                    "javascript": asdict(_CONTEXT_MENU_SHARED_JAVASCRIPT_DELTA),
                    "css": asdict(AssetBytes(raw=0, gzip=0, brotli=0)),
                },
                "charged": {
                    "javascript": asdict(
                        _sum_asset_bytes(
                            adapter_javascript_bytes,
                            _CONTEXT_MENU_SHARED_JAVASCRIPT_DELTA,
                        )
                    ),
                    "css": asdict(_measure(adapter_css)),
                },
                "frame_slices": {
                    "menu-only": _family_asset_frames(
                        frozenset({"CMenu"}),
                        installation=installation,
                    ),
                    "split-button-only": _family_asset_frames(
                        frozenset({"CSplitButton"}),
                        installation=installation,
                    ),
                    "context-menu-only": _family_asset_frames(
                        names,
                        installation=installation,
                    ),
                    "combined": _family_asset_frames(
                        frozenset({"CMenu", "CSplitButton", "CContextMenu"}),
                        installation=installation,
                    ),
                },
            }
        if family == "image":
            record["attribution"] = {
                "provenance": {name: dict(frame) for name, frame in _IMAGE_ASSET_PROVENANCE.items()},
                "emitted": _family_asset_frames(names, installation=installation),
                "shared_positive_delta": {
                    "javascript": asdict(AssetBytes(raw=0, gzip=0, brotli=0)),
                    "css": asdict(AssetBytes(raw=0, gzip=0, brotli=0)),
                },
                "charged": {
                    "javascript": asdict(_measure(javascript)),
                    "css": asdict(_measure(css)),
                },
            }
        if family == "command-palette":
            record["attribution"] = _command_palette_attribution(
                _family_asset_payloads(names, installation=installation),
                _family_asset_payloads(frozenset({"CDialog"}), installation=installation),
                _family_asset_payloads(frozenset({"CCombobox"}), installation=installation),
            )
        families[family] = record
    javascript, css = _family_assets(
        frozenset(definition.__name__ for definition in citry_ui.COMPONENTS),
        installation=installation,
    )
    catalog_javascript = _frame(javascript)
    catalog_css = _frame(css)
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
