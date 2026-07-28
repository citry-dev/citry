# ruff: noqa: S101, T201
"""
Cross-browser evidence for the isolated rootless-lifecycle prototype.

The ordinary repo environment intentionally omits Playwright. Reproduce with
the cached, lock-matching browser package without changing the environment:

    uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
        python docs/design/alpinejs/rootless_lifecycle_harness.py

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
ADAPTER = RESEARCH / "rootless_lifecycle_adapter.js"
SCENARIOS = RESEARCH / "rootless_lifecycle_scenarios.js"

HTML = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Rootless lifecycle spike</title></head>
  <body></body>
</html>
"""

DIRECTIVE_INSTALLER = """
window.__rootlessDirectiveLog = [];
document.addEventListener("alpine:init", () => {
  Alpine.directive("rootless-probe", (el, { expression }, { cleanup }) => {
    window.__rootlessDirectiveLog.push(`init:${expression}`);
    cleanup(() => window.__rootlessDirectiveLog.push(`cleanup:${expression}`));
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
    result = page.evaluate("window.runRootlessLifecycleScenarios()")
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


def _assert_contextual(result: dict[str, Any]) -> None:
    contextual = result["contextualParsing"]
    assert contextual["tbody"] == {
        "names": ["tr"],
        "namespace": "http://www.w3.org/1999/xhtml",
        "text": "cell",
    }
    assert contextual["tr"] == ["td", "td"]
    assert contextual["select"] == {"names": ["optgroup", "option"], "options": 2}
    assert contextual["svg"] == {
        "name": "circle",
        "namespace": "http://www.w3.org/2000/svg",
    }
    assert contextual["stockStringTbody"] != ["tr"]


def _assert_lifecycle(result: dict[str, Any]) -> None:
    logical = result["initialLogicalLifecycle"]
    assert logical["before"] == {
        "elsEmpty": True,
        "elsStable": True,
        "init": 1,
        "props": 1,
        "scope": "rootless-scope",
    }
    assert logical["active"]["effects"] == [1, 2]
    assert logical["active"]["pollCount"] >= 2
    assert logical["active"]["pollParents"] is True
    assert logical["active"]["cleanup"] == 0
    assert logical["after"] == {"cleanup": 1, "destroyed": True, "pollStopped": True}

    shape = result["shapeTransitionsAndAlpine"]
    assert shape["snapshots"] == [
        {"name": "initial-text", "els": [], "stable": True, "text": "initial"},
        {"name": "empty", "els": [], "stable": True, "text": ""},
        {"name": "text", "els": [], "stable": True, "text": "plain text"},
        {
            "name": "several-elements",
            "els": ["span", "b"],
            "stable": True,
            "text": "from-scopefrom-scope",
        },
        {"name": "one-element", "els": ["i"], "stable": True, "text": "from-scope"},
        {"name": "back-to-text", "els": [], "stable": True, "text": "tail"},
    ]
    assert shape["renderedLabels"] == ["from-scope", "from-scope"]
    assert shape["beforeRemoval"] == {"cleanup": 0, "init": 1}
    assert shape["afterRemoval"] == {"cleanup": 1, "destroyed": True, "init": 1}
    assert shape["directiveLog"] == [
        "init:one",
        "init:two",
        "cleanup:one",
        "cleanup:two",
        "init:three",
        "cleanup:three",
    ]


def _assert_topology(result: dict[str, Any]) -> None:
    topology = result["nestedAndAdjacent"]
    assert topology["protectedMorph"] == {
        "adjacentIdentity": True,
        "cleanups": {"adjacent": 0, "inner": 0, "outer": 0},
        "innerElementIdentity": True,
        "innerEndIdentity": True,
        "innerStartIdentity": True,
        "innerState": "kept",
        "liveRenderId": "inner-old",
        "outerNames": ["p", "##comment", "span", "##comment", "p"],
    }
    assert topology["nestedRemoval"] == {
        "adjacentLive": True,
        "cleanups": {"adjacent": 0, "inner": 1, "outer": 0},
        "directiveLog": ["cleanup:nested"],
        "innerDestroyed": True,
        "outerLive": True,
    }
    assert topology["adjacentMorph"] == {
        "cleanups": {"adjacent": 0, "inner": 1, "outer": 0},
        "firstIdentity": True,
        "names": ["div", "em"],
        "text": "changedextra",
    }
    assert topology["nestedInsertion"] == {"init": 1, "names": ["strong"], "valid": True}
    assert topology["emptyAdjacent"] == {
        "firstText": "A",
        "secondEmpty": True,
        "secondIdentity": True,
        "secondValid": True,
    }
    assert topology["unprotectedControl"] == {
        "destroyed": True,
        "identityPreserved": False,
        "valid": False,
    }
    assert topology["refusedIdentityLink"] == {
        "freshInit": 1,
        "freshText": "fresh child",
        "oldCleanup": 1,
        "oldDestroyed": True,
    }

    assert result["keyedRangeLocality"] == {
        "identitiesPreserved": True,
        "otherIdentity": True,
        "secondValue": "other",
        "values": ["client-b", "client-a"],
    }


def _assert_liveness(result: dict[str, Any]) -> None:
    movement = result["movementAndRemoval"]
    assert movement["sameTaskMove"] == {
        "cleanup": 0,
        "init": 1,
        "parent": "destination",
        "props": 20,
        "valid": True,
    }
    assert movement["acrossTaskDetach"] == {"cleanup": 1, "destroyed": True, "init": 1}
    assert movement["noResurrection"] == {"cleanup": 1, "destroyed": True, "init": 1}
    assert movement["elementMove"] == {
        "identity": True,
        "ownScopePresent": True,
        "props": 40,
        "sharedScopePresent": True,
        "text": "changed:updated",
        "valid": True,
    }
    for key in ["ancestor", "endOnly", "innerHtml", "startOnly"]:
        assert movement[key] == {
            "cleanup": 1,
            "destroyed": True,
            "reason": "invalid-or-removed-range",
        }

    pending = result["pendingAndCommentStripping"]
    assert pending["manifestBeforeCaps"] == {"init": 1, "resolved": True, "valid": True}
    assert pending["missingError"] == (
        "Citry rootless instance stripped is missing its start/end comments; comment stripping is unsupported"
    )
    assert pending["templateContent"] == {"init": 0, "resolved": False}
    assert pending["partialCaps"] == {"errors": [], "init": 0, "resolved": False}
    assert pending["completeCaps"] == {
        "errors": [],
        "init": 1,
        "settled": True,
        "valid": True,
    }
    assert pending["duplicate"] == {
        "destroyed": True,
        "errors": ["Citry rootless instance duplicate needs exactly one start and one end marker"],
        "reason": "invalid-marker-topology",
        "settled": False,
    }
    assert pending["crossed"] == {
        "destroyed": True,
        "errors": [
            "Citry rootless marker topology is invalid for cross-a: Citry rootless markers are crossed near cross-a"
        ],
        "reason": "invalid-marker-topology",
        "settled": False,
    }
    assert pending["unrelatedPartialSibling"] == {
        "aInit": 1,
        "aValid": True,
        "bInit": 1,
        "bSettled": True,
        "bValid": True,
    }


def _assert_mirrors(result: dict[str, Any]) -> None:
    mirrored = result["mirroredLogicalInstance"]
    assert mirrored["initial"] == {
        "cleanup": 0,
        "elsEmpty": True,
        "elsStable": True,
        "init": 1,
        "props": 1,
    }
    assert mirrored["rendered"] == {
        "els": ["shared", "shared"],
        "regions": [1, 1],
    }
    assert mirrored["partialRemoval"] == {
        "cleanup": 0,
        "effects": [1, 2],
        "els": ["shared"],
        "init": 1,
        "pollContinued": True,
        "props": 2,
    }
    assert mirrored["finalRemoval"] == {
        "cleanup": 1,
        "destroyed": True,
        "init": 1,
        "pollStopped": True,
    }
    assert mirrored["failedConstruction"] == {
        "error": (
            "Citry rootless instance mirror-rollback-missing is missing its "
            "start/end comments; comment stripping is unsupported"
        ),
        "groups": 0,
        "init": 0,
        "instances": 0,
    }


def _assert_cleanup_and_boundaries(result: dict[str, Any]) -> None:
    managed = result["managedCleanupAndErrors"]
    assert managed["before"]["effectRuns"] == 2
    assert managed["before"]["pollRuns"] >= 2
    assert managed["after"]["destroyed"] is True
    assert managed["after"]["effectRuns"] == 2
    assert managed["after"]["pollStopped"] is True
    assert managed["after"]["order"] == [
        "cleanup-sees-runs:2",
        "second-cleanup",
        "returned-cleanup",
    ]
    assert managed["after"]["errors"] == ["User cleanup failed for managed: expected cleanup throw"]
    assert managed["throwingInit"] == {
        "destroyed": True,
        "errors": ["Citry rootless init failed for throw-init: expected init throw"],
        "reason": "init-error",
    }
    assert result["handlerBoundary"] == (
        "Rootless Citry instance handler has no DOM EventTarget for a component-boundary handler"
    )


def _assert_pass(evidence: dict[str, Any]) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    assert result["alpineVersion"] == "3.15.12"
    _assert_contextual(result)
    _assert_lifecycle(result)
    _assert_topology(result)
    _assert_liveness(result)
    _assert_mirrors(result)
    _assert_cleanup_and_boundaries(result)


def _run() -> dict[str, Any]:
    with sync_playwright() as playwright:
        engines = {
            "chromium": _run_engine(playwright.chromium),
            "firefox": _run_engine(playwright.firefox),
            "webkit": _run_engine(playwright.webkit),
        }
    for engine in engines.values():
        for evidence in engine["passes"]:
            _assert_pass(evidence)
    return {"playwrightVersion": "1.61.0", "runsPerEngine": 3, "engines": engines}


if __name__ == "__main__":
    observed = _run()
    print(json.dumps(observed, indent=2, sort_keys=True))
