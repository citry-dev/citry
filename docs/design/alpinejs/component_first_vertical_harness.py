# ruff: noqa: ANN001, ANN202, ARG002, S101, T201
"""Real Citry render plus manually assembled graph browser composition slice."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from component_first_server_ownership_harness import OwnershipTrace
from playwright.sync_api import BrowserType, Page, sync_playwright

from citry import Citry, Component
from citry.constness import const_value

REPO = Path(__file__).resolve().parents[3]
RESEARCH = Path(__file__).resolve().parent
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"
MORPH = REPO / "packages/js/citry-client/node_modules/@alpinejs/morph/dist/cdn.js"
ROOT_GROUP = RESEARCH / "root_group_adapter.js"
ROOTLESS = RESEARCH / "rootless_lifecycle_adapter.js"
REFS_CLIENT_BINDING = RESEARCH / "refs_client_binding_adapter.js"
SLOTS_SCOPE = RESEARCH / "slots_scope_adapter.js"
ADAPTER = RESEARCH / "component_first_adapter.js"
SCENARIOS = RESEARCH / "component_first_vertical_scenarios.js"


def _render_and_manifest() -> dict[str, Any]:
    trace = OwnershipTrace()
    registry = Citry(extensions=[trace.extension_class()])
    captured_kwargs: list[dict[str, Any]] = []
    captured_client_bindings: list[dict[str, str]] = []

    class Card(Component):
        citry = registry
        template = """
          <section id="vertical-card-a"><c-slot name="body" /></section>
          <button id="vertical-card-b" data-vertical-child x-text="'child:' + owner"></button>
        """

        def template_data(self, kwargs, slots):
            captured_kwargs.append({key: const_value(value) for key, value in kwargs.items()})
            bindings: dict[str, str] = {}
            for binding in self._component_tag_client_bindings:
                expression = getattr(binding.payload, "expression", None)
                if not isinstance(expression, str):
                    raise TypeError("The vertical fixture expects only Alpine-expression client bindings.")
                bindings[binding.key] = expression
            captured_client_bindings.append(bindings)
            return {}

    class Page(Component):
        citry = registry
        template = """
          <main
            id="vertical-source"
            x-data="{ owner: 'parent', count: 0, theme: 'blue' }"
          >
            <span id="vertical-source-ref" x-ref="same"></span>
            <!--citry-fill-source:vertical-parent-->
            <c-card
              $c-props="{ theme, count }"
              @click.once="count += 1"
              @dblclick="count += 10"
            >
              <c-fill name="body">
                <strong
                  id="vertical-owned"
                  x-text="`${owner}:${$refs.same.id}`"
                ></strong>
              </c-fill>
            </c-card>
          </main>
        """

    page = Page()
    trace.root_element_object_id = id(page)
    with trace.patches():
        render = page.render()
    html = render.serialize(deps_strategy="ignore")
    server = trace.finish(html)

    assert captured_kwargs == [{}]
    assert captured_client_bindings == [
        {
            "$c-props": "{ theme, count }",
            "@click.once": "count += 1",
            "@dblclick": "count += 10",
        }
    ]
    page_record = next(item for item in server["componentInstances"] if item["class"] == "Page")
    card_record = next(item for item in server["componentInstances"] if item["class"] == "Card")
    call = next(item for item in server["callEdges"] if item["targetRenderId"] == card_record["renderId"])
    fill = next(
        item for item in server["logicalFills"] if item["kind"] == "named-fill" and item["invocationRegionIds"]
    )
    assert call["sourceRenderId"] == page_record["renderId"]
    assert fill["writerRenderId"] == page_record["renderId"]
    assert len(fill["invocationRegionIds"]) == 1

    page_id = page_record["renderId"]
    card_id = card_record["renderId"]
    call_location_id = call["sourceLocationId"]
    fill_location_id = fill["sourceLocationId"]
    assert call_location_id is not None
    assert fill_location_id is not None
    assert call_location_id != fill_location_id
    manifest = {
        "version": 1,
        "runtimeId": "vertical",
        "instances": [
            {
                "id": page_id,
                "regionIds": ["vertical-source-root"],
                "initialScope": {"componentBase": "page"},
            },
            {
                "id": card_id,
                "renderParentId": page_id,
                "provideParentRenderId": page_id,
                "regionIds": ["vertical-card-roots"],
                "initialScope": {"owner": "child"},
            },
        ],
        "locations": [
            {
                "id": call_location_id,
                "ownerRenderId": page_id,
                "lexicalParentLocationId": None,
                "sourceToken": "vertical-parent",
            },
            {
                "id": fill_location_id,
                "ownerRenderId": page_id,
                "lexicalParentLocationId": call_location_id,
                "sourceToken": "vertical-parent",
            },
        ],
        "regions": [
            {"id": "vertical-source-root", "selector": "#vertical-source"},
            {
                "id": "vertical-card-roots",
                "selector": f"[data-cid-{card_id}]",
            },
            {"id": "vertical-fill-region", "selector": "#vertical-owned"},
        ],
        "fills": [
            {
                "id": fill["logicalFillId"],
                "sourceLocationId": fill_location_id,
                "regionIds": ["vertical-fill-region"],
            }
        ],
        "bindings": [
            {
                "id": "vertical-props",
                "kind": "props",
                "sourceLocationId": call_location_id,
                "targetRenderId": card_id,
                "targetRegionId": "vertical-card-roots",
                "expression": captured_client_bindings[0]["$c-props"],
            },
            {
                "id": "vertical-click",
                "kind": "alpine-event",
                "sourceLocationId": call_location_id,
                "targetRenderId": card_id,
                "targetRegionId": "vertical-card-roots",
                "event": "click",
                "modifiers": ["once"],
                "expression": captured_client_bindings[0]["@click.once"],
            },
            {
                "id": "vertical-live-click",
                "kind": "alpine-event",
                "sourceLocationId": call_location_id,
                "targetRenderId": card_id,
                "targetRegionId": "vertical-card-roots",
                "event": "dblclick",
                "modifiers": [],
                "expression": captured_client_bindings[0]["@dblclick"],
            },
        ],
        "rootless": [],
        "mirrors": [],
    }
    return {
        "cardId": card_id,
        "html": html,
        "manifest": manifest,
        "pageId": page_id,
        "server": server,
    }


def _document(rendered: dict[str, Any]) -> str:
    manifest = json.dumps(rendered["manifest"], separators=(",", ":")).replace("</", "<\\/")
    return f"""<!doctype html><html><body>
{rendered["html"]}
<script type="application/json" data-component-first="alpine">{manifest}</script>
</body></html>"""


def _run_page(page: Page, rendered: dict[str, Any]) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(_document(rendered))
    for script in (ROOT_GROUP, ROOTLESS, REFS_CLIENT_BINDING, SLOTS_SCOPE, ADAPTER, MORPH, ALPINE, SCENARIOS):
        page.add_script_tag(path=script)
    result = page.evaluate(
        "window.runComponentFirstVertical",
        {"pageId": rendered["pageId"], "cardId": rendered["cardId"]},
    )
    return {"console": console, "pageErrors": page_errors, "result": result}


def _assert_browser(evidence: dict[str, Any]) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    assert result["initial"] == {
        "child": "child:child",
        "owned": "parent:vertical-source-ref",
        "pageRoots": ["vertical-source"],
        "props": {"count": 0, "theme": "blue"},
        "roots": ["vertical-card-a", "vertical-card-b"],
    }
    assert result["afterEvent"]["events"] == [
        {
            "binding": "vertical-click",
            "carrier": "vertical-card-b",
            "target": "vertical-card-b",
        }
    ]
    assert result["afterEvent"]["owned"] == "parent:vertical-source-ref"
    assert result["afterEvent"]["props"] == {"count": 1, "theme": "blue"}
    assert result["afterSourceMorph"] == {
        "child": "child:child",
        "owned": "parent-new:vertical-source-ref-new",
        "pageRoots": ["vertical-source"],
        "props": {"count": 7, "theme": "orange"},
        "roots": ["vertical-card-a", "vertical-card-b"],
    }
    assert result["afterTargetMorph"] == {
        "child": "child:child",
        "elsIdentity": True,
        "eventTail": {
            "binding": "vertical-live-click",
            "carrier": "vertical-card-b-new",
            "target": "vertical-card-b-new",
        },
        "owned": "parent-new:vertical-source-ref-new",
        "pageRoots": ["vertical-source"],
        "props": {"count": 17, "theme": "orange"},
        "roots": ["vertical-card-a", "vertical-card-b-new"],
        "secondTag": "ARTICLE",
    }
    assert result["afterDestroy"] == {
        "eventCount": 2,
        "props": {"count": 17, "theme": "orange"},
    }


def _run_engine(engine: BrowserType, rendered: dict[str, Any]) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    passes = []
    for _ in range(3):
        page = browser.new_page()
        evidence = _run_page(page, rendered)
        page.close()
        _assert_browser(evidence)
        passes.append(evidence["result"])
    result = {"browserVersion": browser.version, "passes": passes}
    browser.close()
    return result


def main() -> None:
    rendered = _render_and_manifest()
    manifest_json = json.dumps(rendered["manifest"], separators=(",", ":")).encode()
    with sync_playwright() as playwright:
        browsers = {
            "chromium": _run_engine(playwright.chromium, rendered),
            "firefox": _run_engine(playwright.firefox, rendered),
            "webkit": _run_engine(playwright.webkit, rendered),
        }
    evidence = {
        "browsers": browsers,
        "manifestBytes": len(manifest_json),
        "manifestGzipBytes": len(gzip.compress(manifest_json, mtime=0)),
        "server": {
            "callEdges": len(rendered["server"]["callEdges"]),
            "componentInstances": len(rendered["server"]["componentInstances"]),
            "logicalFills": len(rendered["server"]["logicalFills"]),
            "physicalRegions": len(rendered["server"]["physicalRegionsAndTransitions"]),
        },
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
