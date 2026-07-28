# ruff: noqa: S101, T201
"""
Cross-browser evidence for the component-first architecture exploration.

Run with the repository's cached Playwright package:

    uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
        python docs/design/alpinejs/component_first_harness.py

The harness loads pinned Alpine 3.15.12, pinned morph 3.15.12, the earlier
RootGroup, rootless, exact-source, and slot-scope research adapters, and two
component-first prototypes. It does not modify the Citry product runtime.
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
ROOTLESS = RESEARCH / "rootless_lifecycle_adapter.js"
REFS_CLIENT_BINDING = RESEARCH / "refs_client_binding_adapter.js"
SLOTS_SCOPE = RESEARCH / "slots_scope_adapter.js"
ADAPTER = RESEARCH / "component_first_adapter.js"
SCENARIOS = RESEARCH / "component_first_scenarios.js"

HTML = r"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Citry component-first exploration</title>
  </head>
  <body>
    <div id="a-teleport-destination"></div>

    <section
      id="a-source"
      data-cf-region="a-source-root"
      x-data="{ owner: 'a-parent', parentOnly: 'P', count: 0, theme: 'violet', show: true }"
      x-id="['shared']"
    >
      <span id="a-source-ref" x-ref="same"></span>
      <!--citry-fill-source:a-parent-->
    </section>

    <section id="a-child-a" data-cf-region="a-child-roots">
      <span id="a-child-ref" x-ref="same"></span>
      <!--citry-fill-source:a-child-->

      <article id="a-outer-fill" data-cf-region="a-outer-region" x-ref="fillOwned">
        <span id="a-outer-text" x-text="owner + ':' + parentOnly"></span>
        <span id="a-child-fallback" data-cf-region="a-fallback-region" x-text="owner"></span>
        <section id="a-nested" data-cf-region="a-nested-root">
          <span id="a-nested-text" x-text="owner"></span>
        </section>
      </article>

      <template id="a-if-template" data-cf-region="a-if-region" x-if="show">
        <span id="a-if-generated" x-text="owner"></span>
      </template>

      <template
        id="a-teleport-template"
        data-cf-region="a-teleport-region"
        x-teleport="#a-teleport-destination"
      >
        <span id="a-teleported" x-text="owner"></span>
      </template>
    </section>

    <section id="a-child-b" data-cf-region="a-child-roots">second child root</section>

    <div
      id="a-shared"
      data-cf-region="a-shared-root"
      data-cf-root="graph-a"
      data-cf-instances-graph-a="a-inner a-wrapper stale"
      x-text="owner"
    ></div>

    <section
      id="a-props-only-source"
      data-cf-region="a-props-only-source-root"
      x-data="{ count: 2, theme: 'cyan' }"
    >
      <!--citry-fill-source:a-props-only-->
    </section>
    <div id="a-props-only-target" data-cf-region="a-props-only-target-root"></div>

    <div id="a-rootless-host">
      <!--citry-start:a-rootless-->rootless text<!--citry-end:a-rootless-->
    </div>

    <div id="a-mirror-host">
      <!--citry-start:a-mirror-one--><span id="a-mirror-one-el">one</span><!--citry-end:a-mirror-one-->
      <!--citry-start:a-mirror-two--><span id="a-mirror-two-el">two</span><!--citry-end:a-mirror-two-->
    </div>

    <section
      id="b-source"
      data-cf-region="b-source-root"
      x-data="{ owner: 'b-parent', count: 0, theme: 'blue' }"
    >
      <!--citry-fill-source:b-parent-->
    </section>

    <section
      id="b-child"
      data-cf-region="b-child-root"
      x-data="{ owner: 'b-child' }"
      $c-props="b-props"
    >
      <span
        id="b-citry-text"
        data-cf-region="b-text-region"
        $c-text="b-text"
      ></span>
      <span id="b-alpine-control" x-text="owner"></span>
      <button
        id="b-citry-button"
        data-cf-region="b-button-region"
        $c-on:click="b-on"
      >increment</button>
    </section>

    <script type="application/json" data-component-first="alpine">
      {
        "version": 1,
        "runtimeId": "graph-a",
        "instances": [
          {
            "id": "a-source",
            "regionIds": ["a-source-root"],
            "initialScope": {"componentBase": "source-base"}
          },
          {
            "id": "a-child",
            "renderParentId": "a-source",
            "provideParentRenderId": "a-source",
            "regionIds": ["a-child-roots"],
            "initialScope": {"owner": "a-child", "childOnly": "C"}
          },
          {
            "id": "a-nested",
            "renderParentId": "a-child",
            "provideParentRenderId": "a-child",
            "regionIds": ["a-nested-root"],
            "initialScope": {"owner": "a-nested", "nestedOnly": "N"}
          },
          {
            "id": "a-inner",
            "renderParentId": "a-wrapper",
            "provideParentRenderId": "a-wrapper",
            "regionIds": ["a-shared-root"],
            "initialScope": {"owner": "a-inner"}
          },
          {
            "id": "a-wrapper",
            "regionIds": ["a-shared-root"],
            "initialScope": {"owner": "a-wrapper"}
          },
          {
            "id": "a-props-only-source",
            "regionIds": ["a-props-only-source-root"]
          },
          {
            "id": "a-props-only-target",
            "renderParentId": "a-props-only-source",
            "provideParentRenderId": "a-props-only-source",
            "regionIds": ["a-props-only-target-root"]
          }
        ],
        "locations": [
          {
            "id": "a-parent-location",
            "ownerRenderId": "a-source",
            "lexicalParentLocationId": null,
            "sourceToken": "a-parent"
          },
          {
            "id": "a-child-location",
            "ownerRenderId": "a-child",
            "lexicalParentLocationId": null,
            "sourceToken": "a-child"
          },
          {
            "id": "a-props-only-location",
            "ownerRenderId": "a-props-only-source",
            "lexicalParentLocationId": null,
            "sourceToken": "a-props-only"
          }
        ],
        "regions": [
          {"id": "a-source-root", "selector": "#a-source"},
          {"id": "a-child-roots", "selector": "[data-cf-region~='a-child-roots']"},
          {"id": "a-nested-root", "selector": "#a-nested"},
          {"id": "a-shared-root", "selector": "#a-shared"},
          {"id": "a-props-only-source-root", "selector": "#a-props-only-source"},
          {"id": "a-props-only-target-root", "selector": "#a-props-only-target"},
          {"id": "a-outer-region", "selector": "#a-outer-fill"},
          {"id": "a-fallback-region", "selector": "#a-child-fallback"},
          {"id": "a-if-region", "selector": "#a-if-template"},
          {"id": "a-teleport-region", "selector": "#a-teleport-template"}
        ],
        "fills": [
          {
            "id": "a-parent-fill",
            "sourceLocationId": "a-parent-location",
            "regionIds": ["a-outer-region", "a-if-region", "a-teleport-region"]
          },
          {
            "id": "a-child-fallback",
            "sourceLocationId": "a-child-location",
            "regionIds": ["a-fallback-region"]
          }
        ],
        "bindings": [
          {
            "id": "a-props",
            "kind": "props",
            "sourceLocationId": "a-parent-location",
            "targetRenderId": "a-child",
            "targetRegionId": "a-child-roots",
            "expression": "{ theme, count }"
          },
          {
            "id": "a-boundary-click",
            "kind": "alpine-event",
            "sourceLocationId": "a-parent-location",
            "targetRenderId": "a-child",
            "targetRegionId": "a-child-roots",
            "event": "click",
            "modifiers": ["once"],
            "expression": "count += 1"
          },
          {
            "id": "a-props-only",
            "kind": "props",
            "sourceLocationId": "a-props-only-location",
            "targetRenderId": "a-props-only-target",
            "targetRegionId": "a-props-only-target-root",
            "expression": "{ theme, count }"
          }
        ],
        "rootless": [
          {
            "id": "a-rootless",
            "anchorKey": "a-rootless",
            "initialScope": {"owner": "a-rootless"}
          },
          {"id": "a-mirror-one"},
          {"id": "a-mirror-two"}
        ],
        "mirrors": [
          {
            "id": "a-mirror",
            "regionIds": ["a-mirror-one", "a-mirror-two"],
            "initialScope": {"owner": "a-mirror"}
          }
        ]
      }
    </script>

    <script type="application/json" data-component-first="citry">
      {
        "version": 1,
        "runtimeId": "directives-b",
        "instances": [
          {"id": "b-source", "regionIds": ["b-source-root"]},
          {
            "id": "b-child",
            "renderParentId": "b-source",
            "provideParentRenderId": "b-source",
            "regionIds": ["b-child-root"]
          }
        ],
        "locations": [
          {
            "id": "b-parent-location",
            "ownerRenderId": "b-source",
            "lexicalParentLocationId": null,
            "sourceToken": "b-parent"
          }
        ],
        "regions": [
          {"id": "b-source-root", "selector": "#b-source"},
          {"id": "b-child-root", "selector": "#b-child"},
          {"id": "b-text-region", "selector": "#b-citry-text"},
          {"id": "b-button-region", "selector": "#b-citry-button"}
        ],
        "fills": [],
        "bindings": [
          {
            "id": "b-props",
            "kind": "props",
            "attribute": "$c-props",
            "sourceLocationId": "b-parent-location",
            "targetRenderId": "b-child",
            "targetRegionId": "b-child-root",
            "expression": "{ theme, count }"
          },
          {
            "id": "b-text",
            "kind": "citry-text",
            "attribute": "$c-text",
            "sourceLocationId": "b-parent-location",
            "targetRenderId": "b-child",
            "targetRegionId": "b-text-region",
            "expression": "`${owner}:${count}`"
          },
          {
            "id": "b-on",
            "kind": "citry-on",
            "attribute": "$c-on:click",
            "sourceLocationId": "b-parent-location",
            "targetRenderId": "b-child",
            "targetRegionId": "b-button-region",
            "event": "click",
            "expression": "count += 1"
          }
        ]
      }
    </script>
  </body>
</html>
"""


def _run_page(page: Page) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(HTML)
    page.add_script_tag(path=ROOT_GROUP)
    page.add_script_tag(path=ROOTLESS)
    page.add_script_tag(path=REFS_CLIENT_BINDING)
    page.add_script_tag(path=SLOTS_SCOPE)
    page.add_script_tag(path=ADAPTER)
    page.add_script_tag(path=MORPH)
    page.add_script_tag(path=ALPINE)
    page.add_script_tag(path=SCENARIOS)
    result = page.evaluate("window.runComponentFirstScenarios()")
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


def _assert_pass(evidence: dict[str, Any]) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    assert result["alpineVersion"] == "3.15.12"
    assert result["descriptorRekey"] == {
        "distinct": True,
        "sourceOne": "descriptor-source-one",
        "sourceTwo": "descriptor-source-two",
    }
    assert result["graph"] == {
        "initial": {
            "childRoots": ["a-child-a", "a-child-b"],
            "fallbackText": "a-child",
            "ifText": "a-parent",
            "nestedText": "a-nested",
            "outerChildOnlyType": "undefined",
            "outerOwner": "a-parent",
            "outerParentOnly": "P",
            "outerRoot": "a-source",
            "outerSameRef": "a-source-ref",
            "outerText": "a-parent:P",
            "props": {"count": 0, "theme": "violet"},
            "sharedInstances": "a-wrapper a-inner",
            "sharedText": "a-inner",
            "sourceFillRef": "a-outer-fill",
            "teleportText": "a-parent",
        },
        "afterGroupedEvent": {
            "count": 1,
            "events": [
                {
                    "binding": "a-boundary-click",
                    "carrier": "a-child-b",
                    "target": "a-child-b",
                }
            ],
            "props": {"count": 1, "theme": "violet"},
        },
        "propsOnly": {
            "initial": {"count": 2, "theme": "cyan"},
            "replaced": {"count": 8, "theme": "amber"},
        },
        "rootlessInitial": {
            "els": [],
            "initialized": True,
            "scopeOwner": "a-rootless",
        },
        "rootlessRooted": {"els": ["a-rootless-element"], "identity": True},
        "rootlessText": {"identity": True, "length": 0},
        "mirrorBefore": {
            "els": ["a-mirror-one-el", "a-mirror-two-el"],
            "regions": 2,
        },
        "mirrorAfter": {
            "destroyed": False,
            "els": ["a-mirror-two-el"],
            "identity": True,
            "regions": 1,
        },
        "afterSourceReplacement": {
            "outerText": "a-parent-new:P2",
            "owner": "a-parent-new",
            "props": {"count": 10, "theme": "green"},
            "ref": "a-source-ref-new",
            "root": "a-source",
        },
        "afterTargetMorph": {
            "count": 10,
            "elsIdentity": True,
            "eventTail": {
                "binding": "a-boundary-click",
                "carrier": "a-child-b",
                "target": "a-child-b",
            },
            "roots": ["a-child-a", "a-child-b-new"],
        },
    }
    assert result["directives"] == {
        "initial": {
            "alpineControl": "b-child",
            "attributes": {"on": "b-on", "props": "b-props", "text": "b-text"},
            "citryText": "b-parent:0",
            "props": {"count": 0, "theme": "blue"},
        },
        "afterEvent": {
            "alpineControl": "b-child",
            "citryText": "b-parent:1",
            "count": 1,
            "events": [
                {
                    "binding": "b-on",
                    "carrier": "b-citry-button",
                    "target": "b-citry-button",
                }
            ],
            "props": {"count": 1, "theme": "blue"},
        },
        "afterSourceReplacement": {
            "alpineControl": "b-child",
            "citryText": "b-parent-new:7",
            "props": {"count": 7, "theme": "orange"},
        },
    }
    assert [item["name"] for item in result["validation"]] == [
        "version",
        "duplicate-instance",
        "dangling-region",
        "lexical-cycle",
        "render-cycle",
        "provide-cycle",
    ]
    assert all(item["error"] for item in result["validation"])


def main() -> None:
    with sync_playwright() as playwright:
        evidence = {
            "playwrightVersion": "1.61.0",
            "runsPerEngine": 3,
            "engines": {
                "chromium": _run_engine(playwright.chromium),
                "firefox": _run_engine(playwright.firefox),
                "webkit": _run_engine(playwright.webkit),
            },
        }
    for engine in evidence["engines"].values():
        for result in engine["passes"]:
            _assert_pass(result)
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
