# ruff: noqa: S101, T201
"""
Cross-browser evidence for the candidate ``$c-*`` client directives.

The ordinary repository environment intentionally omits Playwright. Run with
the lock-matching package without changing the environment:

    uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
        python docs/design/alpinejs/component_first_syntax_browser.py

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
SCENARIOS = RESEARCH / "component_first_syntax_scenarios.js"

HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Citry client directive syntax</title></head>
  <body>
    <div
      id="alpine-fixture"
      x-data="{ count: 1 }"
      $c-props="{ count: count }"
    >
      <span id="alpine-count" x-text="count"></span>
    </div>
    <div
      id="alpine-bind-object"
      x-data="{ bag: { '$c-props': '{ fromBind: 1 }' } }"
      x-bind="bag"
    ></div>
    <div
      id="alpine-bind-argument"
      x-data="{ value: '{ fromArgument: 2 }' }"
      x-bind:$c-props="value"
    ></div>
    <div
      id="morph-fixture"
      x-data="{ value: 1 }"
      $c-props="v1"
    >
      <span x-text="value"></span>
    </div>
  </body>
</html>
"""

INSTALLER = """
window.__componentFirstSyntax = { directiveRuns: 0, intercepted: [] };
document.addEventListener("alpine:init", () => {
  Alpine.directive("c-props", () => {
    window.__componentFirstSyntax.directiveRuns += 1;
  });
  Alpine.interceptInit((element) => {
    if (!element.hasAttribute("$c-props")) return;
    window.__componentFirstSyntax.intercepted.push({
      id: element.id,
      expression: element.getAttribute("$c-props"),
    });
  });
});
"""


def _run_page(page: Page) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(HTML)
    page.add_script_tag(content=INSTALLER)
    page.add_script_tag(path=MORPH)
    page.add_script_tag(path=ALPINE)
    page.wait_for_function("Boolean(window.Alpine && Alpine.version === '3.15.12' && Alpine.morph)")
    page.wait_for_function("document.getElementById('alpine-count').textContent === '1'")
    page.add_script_tag(path=SCENARIOS)
    result = page.evaluate("window.runComponentFirstSyntaxScenarios()")
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


def _assert_raw_dom(result: dict[str, Any]) -> None:
    raw = result["rawDom"]
    direct = raw["innerHTML"]["direct"]
    assert direct["names"] == ["id", "$c-props", "c-$c-props", "$c-on:click.once"]
    assert direct["props"] == "{ count: 1 }"
    assert "$c-props=" in direct["outerHTML"]

    mixed = raw["innerHTML"]["mixedCase"]
    assert mixed["names"] == ["id", "$c-props"]
    assert mixed["props"] == "mixed"

    assert raw["domParser"]["props"] == "from-parser"
    assert raw["insertAdjacentHTML"]["props"] == "from-adjacent"

    apis = raw["attributeApis"]
    assert apis["names"] == ["id", "$c-props", "c-$c-props", "$c-on:click"]
    assert apis["afterToggleOff"] is False
    for name in ("$c-props", "c-$c-props", "$c-on:click"):
        assert apis["results"][name] == {
            "error": None,
            "value": f"value:{name}",
            "namedItem": f"value:{name}",
        }

    selectors = raw["selectors"]
    assert selectors["raw"] == {"count": None, "error": "SyntaxError"}
    assert selectors["escaped"]["error"] is None
    assert selectors["escaped"]["count"] >= 1
    assert selectors["escapedName"] == "\\$c-props"
    assert selectors["matchesEscaped"] is True

    mutation = raw["mutation"]
    assert [record["name"] for record in mutation["records"]] == [
        "$c-props",
        "$c-props",
        "$c-props",
    ]
    assert [record["oldValue"] for record in mutation["records"]] == ["v1", "v2", None]
    assert mutation["final"]["props"] == "v3"
    assert raw["cloneNode"]["props"] == "v3"
    assert raw["template"]["source"]["props"] == "template"
    assert raw["template"]["clone"]["props"] == "template"
    assert '$c-props="template"' in raw["template"]["serialized"]


def _assert_contextual(result: dict[str, Any]) -> None:
    contextual = result["contextualParsing"]
    assert contextual["table"]["wrapper"] == "tbody"
    assert contextual["table"]["cell"]["props"] == "cell"
    assert contextual["table"]["contextualCell"]["props"] == "range-cell"
    assert contextual["select"]["props"] == "option"

    svg = contextual["svg"]
    assert svg["inner"]["props"] == "group"
    assert svg["innerNamespace"] == "http://www.w3.org/2000/svg"
    assert svg["setAttributeError"] is None
    assert "$c-model" in svg["inner"]["names"]
    assert svg["contextual"]["props"] == "circle"
    assert svg["contextualNamespace"] == "http://www.w3.org/2000/svg"
    assert "$c-props=" in svg["serialized"]

    # The syntax is valid in HTML, including HTML's SVG integration point. It
    # is not an XML attribute name, so an SVG/XML parser rejects the document.
    assert contextual["xmlRoundTrip"]["parserErrors"] >= 1
    assert contextual["xmlRoundTrip"]["rootName"] in {"html", "parsererror"}


def _assert_alpine_and_morph(result: dict[str, Any]) -> None:
    alpine = result["alpine"]
    assert alpine["version"] == "3.15.12"
    assert alpine["direct"]["expression"] == "{ count: count }"
    assert alpine["direct"]["renderedCount"] == "2"
    assert alpine["direct"]["directiveRuns"] == 0
    intercepted = alpine["direct"]["intercepted"]
    assert {"id": "alpine-fixture", "expression": "{ count: count }"} in intercepted
    assert {"id": "morph-fixture", "expression": "v1"} in intercepted
    assert {"id": "api-element", "expression": "value:$c-props"} in intercepted

    # Alpine 3.15.12 cannot parse '$' as an x-bind argument. Its object-bind
    # fallback treats the directive value string as another binding object and
    # emits numeric attributes for the string's character indexes.
    for key in ("xBindObject", "xBindArgument"):
        assert alpine[key]["props"] is None
        assert alpine[key]["numericNames"][0] == "0"
        assert len(alpine[key]["numericNames"]) > 1

    morph = result["morph"]
    assert morph["sameElement"] is True
    assert morph["changed"] == "v2"
    assert morph["removed"] is None
    assert morph["added"] == "v3"
    assert morph["mutationNames"].count("$c-props") >= 3
    assert '$c-props="v3"' in morph["finalOuterHTML"]


def _assert_engine(evidence: dict[str, Any]) -> None:
    assert len(evidence["passes"]) == 3
    first_result = evidence["passes"][0]["result"]
    for run in evidence["passes"]:
        unexpected_console = [
            message for message in run["console"] if "XML Parsing Error: not well-formed" not in message["text"]
        ]
        assert unexpected_console == []
        assert run["pageErrors"] == []
        _assert_raw_dom(run["result"])
        _assert_contextual(run["result"])
        _assert_alpine_and_morph(run["result"])
        assert run["result"] == first_result


def main() -> None:
    with sync_playwright() as playwright:
        evidence = {
            "chromium": _run_engine(playwright.chromium),
            "firefox": _run_engine(playwright.firefox),
            "webkit": _run_engine(playwright.webkit),
        }
    for engine in evidence.values():
        _assert_engine(engine)
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
