# ruff: noqa: S101, T201
"""
Cross-browser evidence for the isolated RootGroup prototype.

Run after the repo's additive e2e install:

    uv sync --locked --all-packages --group e2e
    .venv/bin/python docs/design/alpinejs/root_group_harness.py

Restore the ordinary environment afterwards:

    uv sync --locked --all-packages

The harness loads the repo's pinned Alpine bytes and the adjacent research-only
adapter and scenarios. It does not load or modify the Citry product runtime.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserType, Page, sync_playwright

REPO = Path(__file__).resolve().parents[3]
RESEARCH = Path(__file__).resolve().parent
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"
ADAPTER = RESEARCH / "root_group_adapter.js"
SCENARIOS = RESEARCH / "root_group_scenarios.js"

HTML = """
<!doctype html>
<html>
  <head>
    <style>
      .fixture { display: block; margin: 4px; }
      .sized { display: inline-block; width: 50px; height: 24px; }
    </style>
  </head>
  <body></body>
</html>
"""


def _run_pointer_probe(page: Page, *, capture: bool) -> list[dict[str, Any]]:
    page.evaluate("capture => window.setupRootGroupPointerProbe(capture)", capture)
    page.mouse.move(20, 20)
    page.mouse.move(120, 120)
    if capture:
        page.mouse.down()
        page.mouse.move(280, 120)
        page.mouse.up()
    else:
        # A direct A-to-B move has B as relatedTarget and must be suppressed as
        # an internal group transition. The second pass crosses a real gap,
        # which remains outside the group and therefore creates boundaries.
        page.mouse.move(280, 120)
        page.mouse.move(420, 220)
        page.mouse.move(120, 120)
        page.mouse.move(220, 120)
        page.mouse.move(280, 120)
    page.mouse.move(420, 220)
    return page.evaluate("window.readRootGroupPointerProbe()")


def _run_engine(engine: BrowserType) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    page = browser.new_page(viewport={"width": 640, "height": 420})
    console: list[dict[str, str]] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.set_content(HTML)
    page.add_script_tag(path=ALPINE)
    page.wait_for_function("window.Alpine && Alpine.version === '3.15.12'")
    page.add_script_tag(path=ADAPTER)
    page.add_script_tag(path=SCENARIOS)
    result = page.evaluate("window.runRootGroupScenarios()")
    pointer = _run_pointer_probe(page, capture=False)
    pointer_capture = _run_pointer_probe(page, capture=True)
    evidence = {
        "browserVersion": browser.version,
        "console": console,
        "pageErrors": page_errors,
        "result": result,
        "pointer": pointer,
        "pointerCapture": pointer_capture,
    }
    browser.close()
    return evidence


def _assert_differential(result: dict[str, Any]) -> None:
    differential = result["differential"]
    assert differential["alpine"] == differential["group"]
    assert differential["group"]["composite"] == {
        "defaultPrevented": [False, True, False],
        "bubbled": 2,
        "callbacks": [{"currentTarget": None, "carrier": True, "target": "root"}],
    }
    assert differential["group"]["keyAndThrottle"] == {
        "keyCallbacks": ["Enter"],
        "throttleCallbacks": ["root", "root"],
    }
    assert differential["group"]["outside"] == ["document"]
    assert differential["group"]["away"] == ["document"]
    assert differential["group"]["globals"] == ["window", "document"]
    assert differential["group"]["namesSubmitAndOptions"] == {
        "names": ["dot", "camel"],
        "options": [{"capture": True, "passive": True}],
        "captureOrder": ["outer-capture", "binding", "target", "outer-bubble"],
        "submitOrder": ["flush", "callback"],
        # This odd result is a pinned Alpine 3.15.12 canary: `false` is read
        # as the passive value but survives as a click key-filter token.
        "passiveFalseClicks": 0,
    }


def _assert_multi_root(result: dict[str, Any]) -> None:
    core = result["multiRootCore"]
    assert core["direct"] == [
        {"target": "a", "current": "a", "carrier": "a"},
        {"target": "b-child", "current": "b", "carrier": "b"},
    ]
    assert core["self"] == ["a", "b"]
    assert core["stopped"] == ["first:b", "second:b"]
    assert core["stopDefaultPrevented"] is True
    assert core["ancestorBubbles"] == 0
    assert core["once"] == ["a"]
    assert core["debounce"] == [{"carrier": "b", "current": None}]
    assert core["throttle"] == ["a", "b"]
    assert core["bothTiming"] == ["a", "b"]
    assert core["outside"] == [
        {"target": "gap", "current": "document", "carrier": "a"},
        {"target": "gap", "current": "document", "carrier": "a"},
    ]
    assert core["globals"] == {"windowCount": 1, "documentCount": 1}
    assert core["redispatchCount"] == 2
    assert core["focus"] == ["focus:a", "blur:a", "focus:b"]
    assert core["asyncCurrentTarget"] == [
        {"phase": "sync", "current": "b", "carrier": "b"},
        {"phase": "async", "current": None, "carrier": "b"},
    ]
    assert core["sharedPhysicalRoot"] == 2

    dynamic = result["dynamicRootsAndCleanup"]
    assert dynamic == {
        "stableArrayIdentity": True,
        "beforeDestroyEls": ["d", "c"],
        "afterDestroyLength": 0,
        "dynamic": ["a", "c"],
        "globalAnchors": ["a", "b"],
        "poll": ["a", "b", "a"],
        "pendingRemovedCarrier": [],
        "survivorPending": ["c"],
        "destroyedPending": [],
    }

    assert result["detachedLifecycle"] == {
        "whileDetached": {"direct": 0, "global": 0},
        "afterConnect": {"direct": 1, "global": 1},
        "afterDisconnect": {"direct": 1, "global": 1},
        "afterReconnect": {"direct": 2, "global": 2},
    }

    boundaries = result["boundariesAndShadow"]
    assert boundaries["transitions"] == [
        "mouseenter:a",
        "mouseleave:b",
        "pointerenter:a",
        "pointerleave:b",
    ]
    assert boundaries["shadowOutside"] == ["gap"]

    citry = result["citrySubset"]
    assert citry == {
        "keySelfOnce": [{"key": "Enter", "carrier": "b"}],
        "debounce": [{"carrier": "b", "current": None}],
        "throttle": ["a", "b"],
        "stopped": 1,
        "bubbled": 0,
        "defaultPrevented": True,
    }


def _assert_pointer(
    engine_name: str,
    pointer: list[dict[str, Any]],
    pointer_capture: list[dict[str, Any]],
) -> None:
    # The direct A-to-B pass is absent because relatedTarget stays in the
    # union. The later gap pass remains observable. Browser event ordering is
    # not normalized; the assertions care only about semantic membership.
    assert not any(
        item["carrier"] == "a" and item["type"] in {"mouseleave", "pointerleave"} and item["related"] == "b"
        for item in pointer
    )
    assert not any(
        item["carrier"] == "b" and item["type"] in {"mouseenter", "pointerenter"} and item["related"] == "a"
        for item in pointer
    )
    assert {item["type"] for item in pointer} == {
        "mouseenter",
        "mouseleave",
        "pointerenter",
        "pointerleave",
    }
    assert any(item["carrier"] == "a" and item["type"] == "mouseenter" for item in pointer)
    assert any(item["carrier"] == "b" and item["type"] == "mouseleave" for item in pointer)

    capture_types = {item["type"] for item in pointer_capture}
    assert "gotpointercapture" in capture_types
    assert "lostpointercapture" in capture_types
    assert [item["type"] for item in pointer_capture] == [
        "pointerenter",
        "mouseenter",
        "gotpointercapture",
        "lostpointercapture",
        "pointerleave",
        "mouseleave",
    ]
    expected_leave_carrier = "a" if engine_name == "webkit" else "b"
    assert [item["carrier"] for item in pointer_capture if item["type"] in {"pointerleave", "mouseleave"}] == [
        expected_leave_carrier,
        expected_leave_carrier,
    ]


def _assert_engine(engine_name: str, evidence: dict[str, Any]) -> None:
    assert evidence["console"] == []
    assert evidence["pageErrors"] == []
    result = evidence["result"]
    assert result["alpineVersion"] == "3.15.12"
    assert result["cleanupDivergence"] == {"alpine": 1, "group": 0}
    _assert_differential(result)
    _assert_multi_root(result)
    _assert_pointer(engine_name, evidence["pointer"], evidence["pointerCapture"])


def _run() -> dict[str, Any]:
    with sync_playwright() as playwright:
        engines = {
            "chromium": _run_engine(playwright.chromium),
            "firefox": _run_engine(playwright.firefox),
            "webkit": _run_engine(playwright.webkit),
        }
    for engine_name, evidence in engines.items():
        _assert_engine(engine_name, evidence)
    return {"playwrightVersion": "1.61.0", "engines": engines}


if __name__ == "__main__":
    observed = _run()
    print(json.dumps(observed, indent=2, sort_keys=True))
