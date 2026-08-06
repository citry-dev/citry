# ruff: noqa: S101, T201
"""
Cross-browser evidence for the redone Alpine slot-scope exploration.

Reproduce with the cached, lock-matching browser package:

    uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
        python docs/design/alpinejs/slots_scope_harness.py

The pure mode loads the pinned Alpine and morph distributions with a
research-only source-link adapter. The runtime mode loads Citry's actual core
and Events client bundles and proves what its current physical marker
resolution does.
No product runtime file is modified by this harness.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserType, Page, sync_playwright

REPO = Path(__file__).resolve().parents[3]
RESEARCH = Path(__file__).resolve().parent
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"
MORPH = REPO / "packages/js/citry-client/node_modules/@alpinejs/morph/dist/cdn.js"
CITRY_CORE = REPO / "packages/py/citry/citry/ext/dependencies/client/citry.js"
CITRY_RUNTIME = REPO / "packages/py/citry/citry/ext/events/client/citry-events.js"
ADAPTER = RESEARCH / "slots_scope_adapter.js"
SCENARIOS = RESEARCH / "slots_scope_scenarios.js"

PURE_HTML = r"""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Citry slot scope spike</title></head>
  <body>
    <div id="teleport-destination"></div>
    <div id="nested-teleport-destination"></div>
    <div id="persistent-destination"></div>

    <section
      id="ordering-source"
      data-cid="ordering-source"
      x-data="{ owner: 'parent', parentOnly: 'P', count: 0 }"
      x-id="['scope-id']"
      @scope-event.capture="window.__nativeOrder.push('source-capture')"
      @scope-event="window.__nativeOrder.push('source-bubble')"
    >
      <span id="ordering-source-ref" x-ref="same"></span>
      <!--citry-fill-source:ordering-->
      <div
        id="ordering-child"
        data-cid="ordering-child"
        x-data="{ owner: 'child', childOnly: 'C' }"
        x-id="['scope-id']"
        @scope-event.capture="window.__nativeOrder.push('child-capture')"
        @scope-event.stop="window.__nativeOrder.push('child-bubble')"
      >
        <span id="ordering-child-ref" x-ref="same"></span>
        <span id="ordering-child-only-ref" x-ref="childOnlyRef"></span>
        <span
          id="old-interceptor-fill"
          data-old-cfill="ordering"
          x-text="typeof parentOnly === 'undefined' ? 'missing' : parentOnly"
        ></span>
        <button
          id="ordering-fill"
          x-cfill="ordering"
          x-ref="fillOwned"
          x-text="owner"
          @scope-event="window.__nativeOrder.push('fill-target'); window.__fillEvent = $event; count += 1"
        ></button>
        <div id="local-fill" x-cfill="ordering" x-data="{ owner: 'local', localOnly: 'L' }"></div>
        <div id="restamp-fill" x-cfill="ordering" x-data="{ owner: 'restamp-local', localOnly: 'keep' }"></div>
        <div id="morph-fill" x-cfill="ordering" x-data="{ owner: 'morph-local', localOnly: 'kept' }">
          <span id="morph-child" x-text="owner + ':' + parentOnly"></span>
        </div>
      </div>
    </section>

    <section
      id="clone-source"
      data-cid="clone-source"
      x-data="{ owner: 'clone-parent', sourceOnly: 'source-value', show: true, items: ['a', 'b'] }"
    >
      <span id="clone-source-ref" x-ref="sourceRef"></span>
      <!--citry-fill-source:clone-->
      <div id="clone-child" data-cid="clone-child" x-data="{ owner: 'clone-child' }">
        <template id="if-template" x-cfill="clone" x-if="show">
          <article
            id="if-generated"
            x-data="{ owner: 'if-local' }"
            x-id="['if-local-id']"
            x-ref="ifOwned"
          >
            <span
              id="if-generated-child"
              x-ref="ifChild"
              x-text="owner + ':' + sourceOnly"
            ></span>
            <template x-if="show">
              <em id="if-nested-clone" x-ref="nestedIf" x-text="owner + ':' + sourceOnly"></em>
            </template>
          </article>
        </template>
        <template id="for-template" x-cfill="clone" x-for="item in items" :key="item">
          <article
            class="for-generated"
            :id="'for-' + item"
            x-data="{ owner: 'for-local' }"
            x-id="['for-local-id']"
            x-ref="forOwned"
          >
            <span
              class="for-generated-child"
              :id="'for-child-' + item"
              x-ref="forChild"
              x-text="owner + ':' + sourceOnly + ':' + item"
            ></span>
            <template x-if="item === 'a'">
              <em
                class="for-nested-clone"
                :id="'for-nested-' + item"
                x-ref="nestedFor"
                x-text="owner + ':' + item"
              ></em>
            </template>
          </article>
        </template>
      </div>
    </section>

    <section
      id="loop-call-source"
      data-cid="loop-call-source"
      x-data="{ owner: 'loop-call-source', items: ['A', 'B'] }"
    >
      <template x-for="item in items" :key="item">
        <article class="loop-call-iteration">
          <!--citry-fill-source:loop-call-->
          <div class="loop-call-child" data-cid="loop-call-child" x-data="{ owner: 'loop-child' }">
            <span class="loop-call-fill" x-cfill="loop-call" x-text="item"></span>
          </div>
        </article>
      </template>
    </section>

    <section id="fallback-source" data-cid="fallback-source" x-data="{ owner: 'fallback-parent' }">
      <!--citry-fill-source:fallback-parent-->
      <div id="fallback-child" data-cid="fallback-child" x-data="{ owner: 'fallback-child' }">
        <!--citry-fill-source:fallback-child-->
        <article id="fallback-outer" x-cfill="fallback-parent">
          <b x-text="owner"></b>
          <i id="fallback-child-owned" x-cfill="fallback-child" x-text="owner"></i>
          <i id="fallback-unmarked-control" x-text="owner"></i>
        </article>
      </div>
    </section>

    <section
      id="nested-source"
      data-cid="nested-source"
      x-data="{ owner: 'nested-parent', parentOnly: 'parent-secret' }"
    >
      <!--citry-fill-source:nested-->
      <div id="nested-receiver" data-cid="nested-receiver" x-data="{ owner: 'receiver' }">
        <article id="nested-fill" x-cfill="nested">
          <span id="nested-ordinary" x-text="owner"></span>
          <section id="nested-component" data-cid="nested-component" x-data="{ owner: 'inner', innerOnly: 'I' }">
            <span id="nested-component-template" x-text="owner"></span>
          </section>
        </article>
        <section
          id="collision-component"
          data-cid="collision-component"
          x-cfill="nested"
          x-data="{ owner: 'collision-inner' }"
        >
          <span id="collision-component-template" x-text="owner"></span>
        </section>
      </div>
    </section>

    <section id="synthetic-source">
      <!--citry-fill-source:synthetic-->
    </section>
    <section id="synthetic-child">
      <button id="synthetic-fill">synthetic</button>
    </section>

    <section
      id="teleport-source"
      data-cid="teleport-source"
      x-data="{ owner: 'teleport-parent', sourceOnly: 'tele-source', teleCount: 0 }"
      x-id="['teleport-shared-id']"
      @teleport-probe="window.__teleportOrder.push('source-bubble')"
    >
      <span id="teleport-source-ref" x-ref="sourceRef"></span>
      <span id="teleport-source-same-ref" x-ref="same"></span>
      <!--citry-fill-source:teleport-->
      <div
        id="teleport-child"
        data-cid="teleport-child"
        x-data="{ owner: 'teleport-child', childOnly: 'TC' }"
        @teleport-probe="window.__teleportOrder.push('child-bubble')"
      >
        <template x-teleport="#teleport-destination">
          <button
            id="teleport-fill"
            x-cfill="teleport"
            x-ref="teleportedOwned"
            @teleport-probe="
              window.__teleportOrder.push('fill-target');
              window.__teleportEvent = $event;
              teleCount += 1
            "
          ></button>
        </template>
        <template
          id="teleport-direct-template"
          x-cfill="teleport"
          x-teleport="#teleport-destination"
        >
          <article
            id="teleport-local"
            x-data="{ owner: 'teleport-local' }"
            x-id="['teleport-shared-id']"
            x-ref="teleportLocalRoot"
          >
            <span id="teleport-local-child" x-ref="teleportLocalChild"></span>
            <span id="teleport-local-same-ref" x-ref="same"></span>
          </article>
        </template>
        <template id="teleport-outer-template" x-teleport="#teleport-destination">
          <template id="teleport-inner-template" x-teleport="#nested-teleport-destination">
            <article
              id="teleport-nested-local"
              x-cfill="teleport"
              x-data="{ owner: 'teleport-nested-local' }"
              x-id="['teleport-shared-id']"
              x-ref="teleportNestedRoot"
            >
              <span id="teleport-nested-child" x-ref="teleportNestedChild"></span>
              <span id="teleport-nested-same-ref" x-ref="same"></span>
            </article>
          </template>
        </template>
      </div>
    </section>

    <section id="multi-source" data-cid="multi-source" x-data="{ owner: 'multi-parent', count: 0 }">
      <!--citry-fill-source:multi-->
      <div id="multi-child" data-cid="multi-child" x-data="{ owner: 'multi-child' }">
        text-before
        <button id="multi-a" x-cfill="multi"></button>
        text-between
        <button id="multi-b" x-cfill="multi"></button>
        text-after
      </div>
    </section>

    <section
      id="dynamic-source-old"
      data-cid="dynamic-source-old"
      x-data="{ owner: 'old-source' }"
      x-id="['dynamic-id']"
    >
      <span id="dynamic-old-ref" x-ref="same"></span>
      <!--citry-fill-source:dynamic-->
    </section>
    <section id="dynamic-host" data-cid="dynamic-host" x-data="{ owner: 'dynamic-child' }">
      <span id="dynamic-fill" x-cfill="dynamic" x-text="owner"></span>
    </section>
  </body>
</html>
"""

PURE_INSTALLER = r"""
window.__nativeOrder = [];
window.__teleportOrder = [];
document.addEventListener("alpine:init", () => {
  Alpine.addRootSelector(() => "[data-cid]");
  const attached = new WeakSet();
  Alpine.interceptInit((el) => {
    if (!el.hasAttribute?.("data-cid") || attached.has(el)) return;
    Alpine.addScopeToNode(el, {});
    el._x_dataStack = el._x_dataStack.slice(0, 1);
    attached.add(el);
  });
  Alpine.interceptInit((el) => {
    const token = el.getAttribute?.("data-old-cfill");
    if (!token) return;
    const source = SlotsScopeSpike.sourceComments(token)[0];
    Alpine.addScopeToNode(el, {}, source);
  });
});
"""


def _b64(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _runtime_manifest() -> str:
    parent_class = "ParentClass"
    child_class = "ChildClass"
    descriptor = json.dumps({"events": {}})
    return json.dumps(
        {
            "instances": [
                [_b64("runtime-parent"), _b64(parent_class), _b64(""), _b64(json.dumps({"owner": "parent-state"}))],
                [_b64("runtime-child"), _b64(child_class), _b64(""), _b64(json.dumps({"owner": "child-state"}))],
            ],
            "classes": {
                _b64(parent_class): _b64(descriptor),
                _b64(child_class): _b64(descriptor),
            },
        }
    )


def _runtime_html() -> str:
    return f"""
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Citry runtime slot scope control</title></head>
  <body>
    <section
      id="runtime-parent"
      data-cid="runtime-parent"
      data-cid-runtime-parent=""
      x-data="{{ owner: 'parent-alpine', parentOnly: 'runtime-parent-only' }}"
    >
      <span id="runtime-parent-ref" x-ref="same"></span>
      <!--citry-fill-source:runtime-->
      <div
        id="runtime-child"
        data-cid="runtime-child"
        data-cid-runtime-child=""
        x-data="{{ owner: 'child-alpine', childOnly: 'runtime-child-only' }}"
      >
        <span id="runtime-child-ref" x-ref="same"></span>
        <button id="runtime-fill" x-cfill="runtime" x-ref="fillOwned" x-text="owner"></button>
      </div>
    </section>
    <script type="application/json" data-citry-events>{_runtime_manifest()}</script>
  </body>
</html>
"""


def _console_and_errors(page: Page) -> tuple[list[dict[str, str]], list[str]]:
    console: list[dict[str, str]] = []
    errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: errors.append(str(error)))
    return console, errors


def _run_pure(page: Page) -> dict[str, Any]:
    console, errors = _console_and_errors(page)
    page.set_content(PURE_HTML)
    page.add_script_tag(content=PURE_INSTALLER)
    page.add_script_tag(path=ADAPTER)
    page.add_script_tag(path=MORPH)
    page.add_script_tag(path=ALPINE)
    page.wait_for_function("Boolean(window.Alpine && Alpine.version === '3.15.12' && Alpine.morph)")
    page.add_script_tag(path=SCENARIOS)
    result = page.evaluate("window.runSlotsScopeScenarios()")
    return {"console": console, "pageErrors": errors, "result": result}


def _run_runtime(page: Page) -> dict[str, Any]:
    console, errors = _console_and_errors(page)
    page.set_content(_runtime_html())
    page.add_script_tag(path=CITRY_CORE)
    page.add_script_tag(path=ADAPTER)
    page.add_script_tag(path=CITRY_RUNTIME)
    page.wait_for_function(
        "Boolean(window.Alpine && window.Citry?.events?._internal?.alpineStarted)",
    )
    result = page.evaluate(
        """
        () => {
          const fill = document.getElementById('runtime-fill');
          const source = document.getElementById('runtime-parent');
          return {
            alpineVersion: Alpine.version,
            fill: {
              alpineOwner: Alpine.evaluate(fill, 'owner'),
              childOnlyType: Alpine.evaluate(fill, 'typeof childOnly'),
              parentOnly: Alpine.evaluate(fill, 'parentOnly'),
              root: Alpine.evaluate(fill, '$root.id'),
              sameRef: Alpine.evaluate(fill, '$refs.same?.id ?? null'),
              stateOwner: Alpine.evaluate(fill, '$state.owner'),
              text: fill.textContent,
            },
            source: {
              fillRef: Alpine.evaluate(source, '$refs.fillOwned?.id ?? null'),
              stateOwner: Alpine.evaluate(source, '$state.owner'),
            },
          };
        }
        """
    )
    return {"console": console, "pageErrors": errors, "result": result}


def _run_engine(engine: BrowserType) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    passes = []
    for _ in range(3):
        pure_page = browser.new_page()
        runtime_page = browser.new_page()
        passes.append({"pure": _run_pure(pure_page), "runtime": _run_runtime(runtime_page)})
        pure_page.close()
        runtime_page.close()
    evidence = {"browserVersion": browser.version, "passes": passes}
    browser.close()
    return evidence


def _assert_pure(evidence: dict[str, Any]) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    assert result["alpineVersion"] == "3.15.12"

    ordinary = result["ordinaryScope"]
    assert ordinary["failedInterceptorControl"] == {"stackKeys": [], "text": "missing"}
    assert ordinary["fill"] == {
        "childOnlyType": "undefined",
        "dataOwner": "parent",
        "el": "ordering-fill",
        "fillRef": "ordering-fill",
        "id": ordinary["source"]["id"],
        "owner": "parent",
        "parentOnly": "P",
        "root": "ordering-source",
        "sameRef": "ordering-source-ref",
        "childRef": None,
        "text": "parent",
    }
    assert ordinary["local"] == {
        "childOnlyType": "undefined",
        "localOnly": "L",
        "owner": "local",
        "parentOnly": "P",
        "root": "local-fill",
    }
    assert ordinary["source"]["countAfter"] == ordinary["source"]["countBefore"] + 2
    assert ordinary["source"]["fillRef"] == "ordering-fill"

    templates = result["directTemplateRoots"]
    assert templates["xIf"]["absent"] is True
    assert templates["sourceLocalRefs"] == {
        "forChild": None,
        "forOwned": None,
        "ifChild": None,
        "ifOwned": None,
        "lateChild": None,
    }
    for index, snapshot in enumerate([templates["xIf"]["first"], templates["xIf"]["second"]]):
        assert snapshot["child"] == {
            "directSource": None,
            "id": snapshot["localId"],
            "localRef": "if-generated-child",
            "owner": "if-local",
            "root": "if-generated",
            "sourceOnly": "source-value",
            "sourceRef": "clone-source-ref",
        }
        assert snapshot["directSource"] == "clone"
        assert snapshot["hasMarker"] is True
        assert snapshot["localRootRef"] == "if-generated"
        assert snapshot["nested"] == {
            "directSource": None,
            "localRef": "if-nested-clone",
            "owner": "if-local",
            "root": "if-generated",
            "sourceOnly": "source-value",
        }
        assert snapshot["owner"] == "if-local"
        assert snapshot["root"] == "if-generated"
        assert snapshot["sourceOnly"] == "source-value"
        assert snapshot["sourceRef"] == "clone-source-ref"
        assert snapshot["sourceToken"] == "clone"
        if index == 1:
            assert snapshot["freshNode"] is True

    late = templates["xIf"]["late"]
    assert late == {
        "childDirectSource": None,
        "childId": late["id"],
        "directSource": None,
        "id": late["id"],
        "localRef": "if-late-child",
        "owner": "late-local",
        "root": "if-late-root",
        "sourceOnly": "source-value",
        "sourceRef": "clone-source-ref",
    }

    for item, snapshot in zip(["a", "b"], templates["xFor"], strict=True):
        assert snapshot["childDirectSource"] is None
        assert snapshot["childId"] == snapshot["localId"]
        assert snapshot["childRef"] == f"for-child-{item}"
        assert snapshot["childRoot"] == f"for-{item}"
        assert snapshot["childText"] == f"for-local:source-value:{item}"
        assert snapshot["directSource"] == "clone"
        assert snapshot["hasMarker"] is True
        assert snapshot["item"] == item
        assert snapshot["localRootRef"] == f"for-{item}"
        assert snapshot["owner"] == "for-local"
        assert snapshot["root"] == f"for-{item}"
        assert snapshot["sourceOnly"] == "source-value"
        assert snapshot["sourceRef"] == "clone-source-ref"
        assert snapshot["sourceToken"] == "clone"
        if item == "a":
            assert snapshot["nestedDirectSource"] is None
            assert snapshot["nestedOwner"] == "for-local"
            assert snapshot["nestedRef"] == "for-nested-a"
            assert snapshot["nestedRoot"] == "for-a"
        else:
            assert snapshot["nestedDirectSource"] is None
            assert snapshot["nestedOwner"] is None
            assert snapshot["nestedRef"] is None
            assert snapshot["nestedRoot"] is None

    assert result["clientLoopCallSites"] == [
        {"item": "A", "owner": "loop-call-source", "strategy": "nearest-preceding", "text": "A"},
        {"item": "B", "owner": "loop-call-source", "strategy": "nearest-preceding", "text": "B"},
    ]
    assert result["fallbackOwnership"] == {
        "outer": "fallback-parent",
        "childFallback": "fallback-child",
        "unmarkedControl": "fallback-parent",
    }

    nested = result["nestedOwnership"]
    assert nested["ordinary"] == {"owner": "nested-parent", "parentOnly": "parent-secret"}
    assert nested["nestedComponent"] == {
        "closestOuterFill": True,
        "owner": "inner",
        "parentOnlyType": "undefined",
        "innerOnly": "I",
    }
    assert nested["markedComponentCollision"] == {
        "owner": "collision-inner",
        "parentOnly": "parent-secret",
        "parentOnlyType": "string",
    }

    native = result["nativeEvents"]
    assert native["exactEvent"] is True
    assert native["order"] == [
        "source-capture",
        "child-capture",
        "fill-target",
        "child-bubble",
        "component-boundary",
    ]
    assert native["target"] == "ordering-fill"

    synthetic = result["syntheticForwardingControl"]
    assert synthetic["dispatchResult"] is True
    assert synthetic["original"]["defaultPrevented"] is False
    assert synthetic["original"]["target"] == "synthetic-fill"
    assert "synthetic-child" in synthetic["original"]["path"]
    assert synthetic["forwarded"]["defaultPrevented"] is True
    assert synthetic["forwarded"]["exactEvent"] is False
    assert synthetic["forwarded"]["target"] == "#comment"
    assert "synthetic-child" not in synthetic["forwarded"]["path"]
    assert "component-boundary-original" not in synthetic["order"]
    assert synthetic["order"].count("document-capture-original") == 1
    assert synthetic["order"].count("document-capture-new") == 1

    teleport = result["teleportedScope"]
    assert teleport["directTemplate"] == {
        "childDirectSource": None,
        "childId": teleport["directTemplate"]["localId"],
        "childRef": "teleport-local-child",
        "childRoot": "teleport-local",
        "destination": "teleport-destination",
        "localId": teleport["directTemplate"]["localId"],
        "localRootRef": "teleport-local",
        "nativeOrigin": "teleport-direct-template",
        "owner": "teleport-local",
        "sameRef": "teleport-local-same-ref",
        "sourceLocalChildRef": None,
        "sourceSameRef": "teleport-source-same-ref",
        "sourceOnly": "tele-source",
        "sourceRef": "teleport-source-ref",
    }
    nested_teleport = teleport["nestedTemplate"]
    assert nested_teleport == {
        "chain": [
            "teleport-inner-template",
            "teleport-outer-template",
            "teleport-source",
        ],
        "childDirectSource": None,
        "childId": nested_teleport["localId"],
        "childRef": "teleport-nested-child",
        "childRoot": "teleport-nested-local",
        "destination": "nested-teleport-destination",
        "directSource": "teleport",
        "localId": nested_teleport["localId"],
        "localRootRef": "teleport-nested-local",
        "nativePairs": [True, True],
        "owner": "teleport-nested-local",
        "sameRef": "teleport-nested-same-ref",
        "sourceId": nested_teleport["sourceId"],
        "sourceLocalChildRef": None,
        "sourceSameRef": "teleport-source-same-ref",
        "sourceOnly": "tele-source",
        "sourceRef": "teleport-source-ref",
    }
    assert nested_teleport["localId"] != nested_teleport["sourceId"]
    assert teleport["destination"] == "teleport-destination"
    assert teleport["event"] == {
        "exact": True,
        "order": ["fill-target"],
        "target": "teleport-fill",
    }
    assert teleport["scope"] == {
        "childOnlyType": "undefined",
        "owner": "teleport-parent",
        "root": "teleport-source",
        "sourceRef": "teleport-source-ref",
        "teleportedRefAtSource": "teleport-fill",
    }

    assert result["multiRootScope"] == {
        "count": 11,
        "roots": [
            {"el": "multi-a", "owner": "multi-parent", "source": "multi"},
            {"el": "multi-b", "owner": "multi-parent", "source": "multi"},
        ],
    }

    lifecycle = result["morphAndRestamp"]
    assert lifecycle["afterMorph"] == {
        "identity": True,
        "localOnly": "kept",
        "owner": "morph-local",
        "parentOnly": "P",
        "text": "morph-local:P",
    }
    assert lifecycle["beforeRestamp"] == {
        "localOnly": "keep",
        "owner": "restamp-local",
        "stackLength": 2,
    }
    assert lifecycle["afterRestamp"] == {
        "localOnlyType": "undefined",
        "owner": "parent",
        "stackLength": 1,
    }

    replacement = result["sourceReplacement"]
    assert replacement["before"] == {
        "id": replacement["before"]["id"],
        "owner": "old-source",
        "ref": "dynamic-old-ref",
        "root": "dynamic-source-old",
        "text": "old-source",
    }
    assert replacement["detached"] == {"ownerType": "undefined", "root": "dynamic-source-old"}
    assert replacement["after"] == {
        "id": replacement["after"]["sourceId"],
        "owner": "new-source",
        "ref": "dynamic-new-ref",
        "root": "dynamic-source-new",
        "sourceId": replacement["after"]["sourceId"],
        "text": "new-source",
    }
    assert replacement["after"]["id"] != replacement["before"]["id"]


def _assert_runtime(evidence: dict[str, Any]) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    assert result["alpineVersion"] == "3.15.12"
    assert result["fill"] == {
        "alpineOwner": "parent-alpine",
        "childOnlyType": "undefined",
        "parentOnly": "runtime-parent-only",
        "root": "runtime-parent",
        "sameRef": "runtime-parent-ref",
        "stateOwner": "child-state",
        "text": "parent-alpine",
    }
    assert result["source"] == {
        "fillRef": "runtime-fill",
        "stateOwner": "parent-state",
    }


def _assert_pass(result: dict[str, Any]) -> None:
    _assert_pure(result["pure"])
    _assert_runtime(result["runtime"])


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
