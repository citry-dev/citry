# ruff: noqa: S101, T201
"""Run both component-first engines against exactly one fixture and manifest."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

from playwright.sync_api import BrowserType, Page, sync_playwright

REPO = Path(__file__).resolve().parents[3]
RESEARCH = Path(__file__).resolve().parent
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"
MORPH = REPO / "packages/js/citry-client/node_modules/@alpinejs/morph/dist/cdn.js"
ROOT_GROUP = RESEARCH / "root_group_adapter.js"
ROOTLESS = RESEARCH / "rootless_lifecycle_adapter.js"
REFS_CLIENT_BINDING = RESEARCH / "refs_client_binding_adapter.js"
SLOTS_SCOPE = RESEARCH / "slots_scope_adapter.js"
ADAPTER = RESEARCH / "component_first_adapter.js"
SCENARIOS = RESEARCH / "component_first_comparison_scenarios.js"

MANIFEST = {
    "version": 1,
    "runtimeId": "comparison",
    "instances": [
        {
            "id": "cmp-source",
            "regionIds": ["cmp-source-root"],
            "initialScope": {"componentBase": "source"},
        },
        {
            "id": "cmp-child",
            "renderParentId": "cmp-source",
            "provideParentRenderId": "cmp-source",
            "regionIds": ["cmp-child-roots"],
            "initialScope": {"owner": "component-child"},
        },
    ],
    "locations": [
        {
            "id": "cmp-parent-location",
            "ownerRenderId": "cmp-source",
            "lexicalParentLocationId": None,
            "sourceToken": "cmp-parent",
        }
    ],
    "regions": [
        {"id": "cmp-source-root", "selector": "#cmp-source"},
        {"id": "cmp-child-roots", "selector": "[data-cf-region~='cmp-child-roots']"},
        {"id": "cmp-owned-region", "selector": "#cmp-owned"},
    ],
    "fills": [
        {
            "id": "cmp-fill",
            "sourceLocationId": "cmp-parent-location",
            "regionIds": ["cmp-owned-region"],
        }
    ],
    "bindings": [
        {
            "id": "cmp-props",
            "kind": "props",
            "sourceLocationId": "cmp-parent-location",
            "targetRenderId": "cmp-child",
            "targetRegionId": "cmp-child-roots",
            "expression": "{ theme, count }",
        },
        {
            "id": "cmp-text",
            "kind": "owned-text",
            "attribute": "data-cf-binding",
            "sourceLocationId": "cmp-parent-location",
            "targetRenderId": "cmp-child",
            "targetRegionId": "cmp-owned-region",
            "expression": "`${owner}:${$refs.same.id}:${$root.id}`",
        },
        {
            "id": "cmp-click",
            "kind": "boundary-event",
            "sourceLocationId": "cmp-parent-location",
            "targetRenderId": "cmp-child",
            "targetRegionId": "cmp-child-roots",
            "event": "click",
            "modifiers": ["once"],
            "expression": "count += 1",
        },
        {
            "id": "cmp-live-click",
            "kind": "boundary-event",
            "sourceLocationId": "cmp-parent-location",
            "targetRenderId": "cmp-child",
            "targetRegionId": "cmp-child-roots",
            "event": "dblclick",
            "modifiers": [],
            "expression": "count += 10",
        },
    ],
    "rootless": [],
    "mirrors": [],
}


def _html(mode: str) -> str:
    manifest = json.dumps(MANIFEST, separators=(",", ":"))
    return f"""
<!doctype html>
<html>
  <body>
    <section
      id="cmp-source"
      data-cf-region="cmp-source-root"
      x-data="{{ owner: 'parent', count: 0, theme: 'blue' }}"
    >
      <span id="cmp-source-ref" x-ref="same"></span>
      <!--citry-fill-source:cmp-parent-->
    </section>
    <section
      id="cmp-child-a"
      data-cf-region="cmp-child-roots"
      x-data="{{ owner: 'child' }}"
    >
      <span id="cmp-child-ref" x-ref="same"></span>
      <span id="cmp-control" x-text="owner"></span>
      <span id="cmp-owned" data-cf-region="cmp-owned-region" data-cf-binding="cmp-text"></span>
    </section>
    <section id="cmp-child-b" data-cf-region="cmp-child-roots">second root</section>
    <script type="application/json" data-component-first="{mode}">{manifest}</script>
  </body>
</html>
"""


def _run_page(page: Page, mode: str) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(_html(mode))
    for script in (ROOT_GROUP, ROOTLESS, REFS_CLIENT_BINDING, SLOTS_SCOPE, ADAPTER, MORPH, ALPINE, SCENARIOS):
        page.add_script_tag(path=script)
    result = page.evaluate("window.runComponentFirstComparison()")
    return {"console": console, "pageErrors": page_errors, "result": result}


def _assert_result(evidence: dict[str, Any], mode: str) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    expected_mode = "GraphFirstAlpineRuntime" if mode == "alpine" else "CitryDirectiveRuntime"
    assert result["mode"] == expected_mode
    assert result["initial"] == {
        "control": "child",
        "owned": "parent:cmp-source-ref:cmp-source",
        "props": {"count": 0, "theme": "blue"},
    }
    assert result["afterEvent"] == {
        "control": "child",
        "events": [{"binding": "cmp-click", "carrier": "cmp-child-b", "target": "cmp-child-b"}],
        "owned": "parent:cmp-source-ref:cmp-source",
        "props": {"count": 1, "theme": "blue"},
    }
    assert result["afterSourceReplacement"] == {
        "control": "child",
        "owned": "parent-new:cmp-source-ref-new:cmp-source",
        "props": {"count": 9, "theme": "orange"},
    }
    assert result["afterDestroy"] == {
        "events": [{"binding": "cmp-click", "carrier": "cmp-child-b", "target": "cmp-child-b"}],
        "owned": (
            "after-destroy:cmp-source-ref-new:cmp-source"
            if mode == "alpine"
            else "parent-new:cmp-source-ref-new:cmp-source"
        ),
        "props": {"count": 9, "theme": "orange"},
        "futureRoot": "undefined",
        "sourceCount": 20,
    }
    assert result["iterations"] == 1000
    assert result["evaluationMilliseconds"] >= 0


def _run_engine(engine: BrowserType) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    modes: dict[str, Any] = {}
    for mode in ("alpine", "citry"):
        passes = []
        for _ in range(5):
            page = browser.new_page()
            evidence = _run_page(page, mode)
            page.close()
            _assert_result(evidence, mode)
            passes.append(evidence["result"])
        modes[mode] = {
            "evaluationMillisecondsMedian": median(result["evaluationMilliseconds"] for result in passes),
            "passes": passes,
        }
    result = {"browserVersion": browser.version, "modes": modes}
    browser.close()
    return result


def main() -> None:
    with sync_playwright() as playwright:
        evidence = {
            "manifestBytes": len(json.dumps(MANIFEST, separators=(",", ":")).encode()),
            "runsPerMode": 5,
            "engines": {
                "chromium": _run_engine(playwright.chromium),
                "firefox": _run_engine(playwright.firefox),
                "webkit": _run_engine(playwright.webkit),
            },
        }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
