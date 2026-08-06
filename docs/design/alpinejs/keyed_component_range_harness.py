# ruff: noqa: S101, T201
"""
Cross-browser evidence for the disposable keyed-component-range spike.

Reproduce from the repository environment (Playwright 1.61.0 is pinned):

    python docs/design/alpinejs/keyed_component_range_harness.py

The harness loads the repository's pinned Alpine and morph bytes. It does not
load or modify the Citry product runtime.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserType, Page, sync_playwright

REPO = Path(__file__).resolve().parents[3]
RESEARCH = Path(__file__).resolve().parent
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"
MORPH = REPO / "packages/js/citry-client/node_modules/@alpinejs/morph/dist/cdn.js"
ADAPTER = RESEARCH / "keyed_component_range_adapter.js"
SCENARIOS = RESEARCH / "keyed_component_range_scenarios.js"

HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Keyed component range spike</title></head>
  <body></body>
</html>
"""

DIRECTIVE_INSTALLER = """
window.__keyedRangeDirectiveLog = [];
document.addEventListener("alpine:init", () => {
  Alpine.directive("range-probe", (el, { expression }, { cleanup }) => {
    window.__keyedRangeDirectiveLog.push(`init:${expression}`);
    cleanup(() => window.__keyedRangeDirectiveLog.push(`cleanup:${expression}`));
  });
});
"""


def _run_page(page: Page) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(HTML)
    page.add_script_tag(content=DIRECTIVE_INSTALLER)
    page.add_script_tag(path=MORPH)
    page.add_script_tag(path=ALPINE)
    page.wait_for_function("Boolean(window.Alpine && Alpine.version === '3.15.12' && Alpine.morphBetween)")
    page.add_script_tag(path=ADAPTER)
    page.add_script_tag(path=SCENARIOS)
    result = page.evaluate("window.runKeyedComponentRangeScenarios()")
    return {"console": console, "pageErrors": page_errors, "result": result}


def _run_engine(engine: BrowserType, *, passes: int = 3) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    runs = []
    for _ in range(passes):
        page = browser.new_page()
        runs.append(_run_page(page))
        page.close()
    evidence = {"browserVersion": browser.version, "passes": runs}
    browser.close()
    return evidence


def _assert_residue(result: dict[str, Any]) -> None:
    for scenario, value in result.items():
        if isinstance(value, dict) and "residue" in value:
            assert value["residue"] == {"holders": 0, "sentinels": 0}, scenario


def _assert_result(result: dict[str, Any]) -> None:
    assert result["directiveLog"] == [
        "init:axes-a",
        "cleanup:axes-a",
        "init:axes-b",
        "cleanup:axes-b",
        "init:axes-new-component",
        "cleanup:axes-new-component",
        "init:stationary",
        "init:stationary",
        "cleanup:stationary",
        "init:portable",
        "init:portable",
        "cleanup:portable",
    ]
    assert result["adjacentEmptyRangeReorder"] == {
        "anchors": True,
        "capIdentities": True,
        "empty": [0, 0],
        "residue": {"holders": 0, "sentinels": 0},
        "startOrder": [
            "citry-vrange:empty-b-new:s",
            "citry-vrange:empty-a-new:s",
        ],
    }
    assert result["inertIslandNegativeControl"] == {
        "freshDiscarded": True,
        "result": "old child bytes",
    }

    stationary = result["stationaryFreshContentAndBrowserState"]
    assert stationary == {
        "anchorIdentity": True,
        "capIdentity": True,
        "clientDraft": "client draft",
        "focus": True,
        "frameIdentity": True,
        "frameStamp": "kept",
        "freshAttribute": "fresh",
        "freshLabel": "fresh label",
        "logicalState": "state-kept",
        "residue": {"holders": 0, "sentinels": 0},
        "rootIdentity": True,
        "scopeDraft": "client draft",
        "scopeIdentity": True,
        "scroll": 91,
        "selection": [2, 7],
        "usedConnectedPath": True,
    }
    assert result["stationaryRangeBeforeElementKeyReorder"] == {
        "childText": "fresh child",
        "identities": True,
        "order": ["B", "A"],
        "residue": {"holders": 0, "sentinels": 0},
        "text": ["B fresh", "A fresh"],
        "usedConnectedPath": True,
    }
    range_moves = result["rangeMovesRelativeToOrdinaryElement"]
    expected_move = {
        "anchor": True,
        "capIdentities": True,
        "childIdentity": True,
        "childText": "child fresh",
        "ordinaryIdentity": True,
        "ordinaryText": "ordinary fresh",
        "residue": {"holders": 0, "sentinels": 0},
        "usedConnectedPath": False,
    }
    assert range_moves["leftToRight"] == {**expected_move, "order": ["div", "article"]}
    assert range_moves["rightToLeft"] == {**expected_move, "order": ["article", "div"]}

    axes = result["independentComponentAndElementKeys"]
    assert axes == {
        "componentKept": {
            "anchorIdentity": True,
            "cleanupCount": 0,
            "rootIdentity": False,
            "text": "element reset",
        },
        "componentReset": {
            "anchorIdentity": False,
            "newElementDespiteSameInnerKey": True,
            "oldAnchorCleanup": 1,
            "text": "component reset",
        },
        "residue": {"holders": 0, "sentinels": 0},
    }

    reordered = result["reorderedSiblingRanges"]
    assert reordered["anchorsFollowKeys"] is True
    assert reordered["capIdentities"] is True
    assert reordered["innerRootsFollowComponentKeys"] is True
    assert reordered["freshText"] == ["B fresh", "A fresh"]
    assert reordered["componentOrder"] == ["anchor-3", "anchor-2"]

    shapes = result["multiRootAndShapeTransitions"]
    assert shapes == {
        "asText": {"anchor": True, "text": "plain text"},
        "backToElement": {"anchor": True, "name": "em", "text": "element"},
        "empty": {"anchor": True, "nodes": 0},
        "reordered": {
            "anchor": True,
            "identities": True,
            "names": ["b", "i", "u"],
            "text": "two freshone freshthree",
        },
        "residue": {"holders": 0, "sentinels": 0},
    }

    nested = result["nestedBoundaryIsolation"]
    assert nested == {
        "reset": {
            "grandAnchorLeaked": False,
            "grandRootLeaked": False,
            "oldGrandCleanup": 1,
            "oldParentCleanup": 1,
            "parentAnchorLeaked": False,
        },
        "residue": {"holders": 0, "sentinels": 0},
        "stable": {
            "freshText": "parent freshgrand fresh",
            "grandAnchor": True,
            "grandRoot": True,
            "parentAnchor": True,
        },
    }

    assert result["selfRenderThenParentRender"] == {
        "afterParentAnchor": True,
        "afterSelfAnchor": True,
        "inheritedKey": "parent-key",
        "residue": {"holders": 0, "sentinels": 0},
        "text": "parent fresh",
    }

    values = result["nullEmptyFalseZeroAndClass"]
    assert values == {
        "classChangePreserved": False,
        "oldEmptyCleanup": 1,
        "residue": {"holders": 0, "sentinels": 0},
        "valueSemantics": {"empty": True, "false": True, "null": False, "zero": True},
    }

    assert result["contextualSelectRange"] == {
        "anchor": True,
        "identity": True,
        "options": 1,
        "residue": {"holders": 0, "sentinels": 0},
        "text": "fresh",
    }
    assert result["idOnlyWrapperReorder"] == {
        "anchor": True,
        "capIdentities": True,
        "residue": {"holders": 0, "sentinels": 0},
        "rootIdentity": True,
        "text": "fresh child",
        "usedConnectedPath": False,
        "wrapperOrder": ["right", "left"],
    }
    assert result["wrapperDepthMove"] == {
        "anchor": True,
        "capIdentities": True,
        "cleanupAfterRemoval": 1,
        "cleanupDuringMove": 0,
        "newAncestors": ["aside", "section"],
        "residue": {"holders": 0, "sentinels": 0},
        "rootIdentity": True,
        "text": "fresh location",
    }
    _assert_residue(result)


def main() -> None:
    evidence: dict[str, Any] = {
        "pins": {"alpine": "3.15.12", "morph": "3.15.12", "playwright": "1.61.0"},
        "engines": {},
    }
    cross_engine_baseline: dict[str, Any] | None = None
    with sync_playwright() as playwright:
        for name, engine in (
            ("chromium", playwright.chromium),
            ("firefox", playwright.firefox),
            ("webkit", playwright.webkit),
        ):
            engine_evidence = _run_engine(engine)
            for run in engine_evidence["passes"]:
                assert run["console"] == []
                assert run["pageErrors"] == []
                _assert_result(run["result"])
            baseline = engine_evidence["passes"][0]["result"]
            assert all(run["result"] == baseline for run in engine_evidence["passes"][1:])
            if cross_engine_baseline is None:
                cross_engine_baseline = baseline
            else:
                assert baseline == cross_engine_baseline
            evidence["engines"][name] = engine_evidence
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
