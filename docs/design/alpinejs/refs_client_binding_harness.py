# ruff: noqa: S101, T201
"""
Cross-browser evidence for isolated component-boundary handler scope.

The ordinary repo environment intentionally omits Playwright. Reproduce with
the cached, lock-matching browser package without changing the environment:

    uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
        python docs/design/alpinejs/refs_client_binding_harness.py

The harness loads local pinned Alpine and morph bytes plus adjacent research
artifacts. It does not load or modify the Citry product runtime.
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
ROOT_GROUP = RESEARCH / "root_group_adapter.js"
ADAPTER = RESEARCH / "refs_client_binding_adapter.js"
SCENARIOS = RESEARCH / "refs_client_binding_scenarios.js"

HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Citry boundary handler scope spike</title></head>
  <body></body>
</html>
"""

ROOT_SELECTOR_INSTALLER = """
document.addEventListener("alpine:init", () => {
  Alpine.addRootSelector(() => "[data-cid]");
  Alpine.interceptInit((el) => {
    if (!el.hasAttribute?.("data-cid")) return;
    Alpine.addScopeToNode(el, {});
    // Mirror Citry's boundary attachment: the new instance starts with one
    // isolated boundary layer, then its own x-data may prepend local state.
    el._x_dataStack = el._x_dataStack.slice(0, 1);
  });
});
"""


def _run_page(page: Page) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(HTML)
    page.add_script_tag(content=ROOT_SELECTOR_INSTALLER)
    page.add_script_tag(path=MORPH)
    page.add_script_tag(path=ALPINE)
    page.wait_for_function("Boolean(window.Alpine && Alpine.version === '3.15.12' && Alpine.morph)")
    page.add_script_tag(path=ROOT_GROUP)
    page.add_script_tag(path=ADAPTER)
    page.add_script_tag(path=SCENARIOS)
    result = page.evaluate("window.runBoundaryScopeScenarios()")
    return {"console": console, "pageErrors": page_errors, "result": result}


def _run_engine(engine: BrowserType) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    passes = []
    for _ in range(3):
        page = browser.new_page()
        passes.append(_run_page(page))
        page.close()
    evidence = {"browserVersion": browser.version, "passes": passes}
    browser.close()
    return evidence


def _assert_single_and_grouped(result: dict[str, Any]) -> None:
    single = result["singleRootCollision"]
    assert single["source"] == {
        "alpineId": single["source"]["alpineId"],
        "owner": "parent",
        "same": "parent-same",
        "parentOnlyRef": "parent-only-ref",
        "childOnlyRef": None,
    }
    source_alpine_id = single["source"]["alpineId"]
    common_boundary = {
        "owner": "parent",
        "parentOnly": "parent-only",
        "facadeOwner": "parent-facade",
        "childOnlyType": "undefined",
        "dataOwner": "parent",
        "dataChildOnlyType": "undefined",
        "sameRef": "parent-same",
        "parentOnlyRef": "parent-only-ref",
        "childOnlyRef": None,
        "root": "parent",
        "alpineId": source_alpine_id,
        "el": "child",
        "target": "child",
        "current": "child",
        "exactEvent": True,
    }
    assert single["alpineBoundary"] == [
        {**common_boundary, "profile": "alpine", "facadeHits": 1, "marker": "alpine-event"}
    ]
    assert single["citryBoundary"] == [
        {**common_boundary, "profile": "citry", "facadeHits": 2, "marker": "citry-event"}
    ]
    assert single["dispatchedFrom"] == [
        {"profile": "alpine", "target": "child"},
        {"profile": "citry", "target": "child"},
    ]
    assert single["parentHits"] == 2
    assert single["childHits"] == 101
    assert single["facadeState"] == {"facadeHits": 2, "facadeOwner": "parent-facade"}
    assert single["local"] == {
        "owner": "child",
        "childOnly": "child-only",
        "facadeOwner": "child-facade",
        "facadeHits": 1000,
        "parentOnlyType": "undefined",
        "dataOwner": "child",
        "dataParentOnlyType": "undefined",
        "sameRef": "child-same",
        "childOnlyRef": "child-only-ref",
        "root": "child",
        "alpineId": single["local"]["alpineId"],
        "el": "child",
        "target": "child",
        "current": "child",
        "marker": "local-event",
        "exactEvent": True,
    }
    assert single["local"]["alpineId"] != source_alpine_id

    grouped = result["groupedTargetAndExactSource"]
    assert grouped["controls"] == {
        "aNative": "target-a-same",
        "bNative": "target-b-same",
        "sourceFirstRoot": "a-same",
        "sourceExactLocation": "b-same",
    }
    assert grouped["delivered"] == [
        {
            "same": "b-same",
            "aOnly": None,
            "bOnly": "b-only",
            "el": "target-a",
            "current": "target-a",
        },
        {
            "same": "b-same",
            "aOnly": None,
            "bOnly": "b-only",
            "el": "target-b",
            "current": "target-b",
        },
        {
            "same": "b-same",
            "aOnly": None,
            "bOnly": "b-only",
            "el": "target-c",
            "current": "target-c",
        },
    ]
    assert grouped["liveRoots"] == ["target-b", "target-c"]


def _assert_shared_and_dynamic(result: dict[str, Any]) -> None:
    shared = result["sharedPhysicalRoot"]
    assert shared["native"] == {"same": "shared-same", "childOnly": "shared-only"}
    assert shared["values"] == [
        {
            "clientBinding": 1,
            "same": "one-same",
            "childOnly": None,
            "el": "shared-root",
            "current": "shared-root",
        },
        {
            "clientBinding": 2,
            "same": "two-same",
            "childOnly": None,
            "el": "shared-root",
            "current": "shared-root",
        },
    ]

    dynamic = result["dynamicRefsAndSourceReplacement"]
    assert dynamic["seen"] == [
        "old-ref",
        "morphed-ref",
        None,
        "morphed-ref",
        "new-source-ref",
    ]


def _assert_liveness_and_native_edges(result: dict[str, Any]) -> None:
    delayed = result["delayedLivenessAndFreshness"]
    assert delayed["delivered"] == [{"same": "delay-fresh", "el": "delay-target", "current": None}]
    assert delayed["drops"] == ["source-not-live"]

    teleport = result["teleportOracle"]
    assert teleport == {
        "destination": "destination-same",
        "nativeTarget": "origin-same",
        "origin": "origin-same",
        "seen": [{"same": "origin-same", "el": "teleported-target", "current": "teleported-target"}],
    }

    native = result["nativeConditionalAndLoopCanaries"]
    assert native["initial"] == {"conditional": "conditional-ref", "repeated": "b"}
    assert native["hidden"] == {"conditional": None, "repeated": "b"}
    assert native["restoredAndReordered"] == {
        "conditional": "conditional-ref",
        "repeated": "b",
    }
    assert native["removedOtherClone"] == {"conditional": "conditional-ref", "repeated": None}
    assert native["freshClone"] == {"conditional": "conditional-ref", "repeated": "c"}

    boundaries = result["shadowAndRootlessBoundaries"]
    assert boundaries == {
        "rootlessErrors": {
            "alpine": ("Citry component event handler cannot attach because the target has no HTML element root"),
            "citry": ("Citry component event handler cannot attach because the target has no HTML element root"),
        },
        "shadow": {"light": "light-ref", "shadowOnly": "shadow-ref"},
    }


def _assert_pass(pass_result: dict[str, Any]) -> None:
    assert pass_result["console"] == []
    assert pass_result["pageErrors"] == []
    result = pass_result["result"]
    _assert_single_and_grouped(result)
    _assert_shared_and_dynamic(result)
    _assert_liveness_and_native_edges(result)


def main() -> None:
    with sync_playwright() as playwright:
        evidence = {
            "chromium": _run_engine(playwright.chromium),
            "firefox": _run_engine(playwright.firefox),
            "webkit": _run_engine(playwright.webkit),
        }
    for engine in evidence.values():
        for pass_result in engine["passes"]:
            _assert_pass(pass_result)
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
