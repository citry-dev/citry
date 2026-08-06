# ruff: noqa: S101, T201
"""Measure readable graph-first adoption against ordinary Alpine roots."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from statistics import median
from typing import Any

from playwright.sync_api import BrowserType, Page, sync_playwright

REPO = Path(__file__).resolve().parents[3]
RESEARCH = Path(__file__).resolve().parent
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"
ROOT_GROUP = RESEARCH / "root_group_adapter.js"
ADAPTER = RESEARCH / "component_first_adapter.js"
COUNTS = (100, 300, 500)
RUNS_PER_MODE = 3


def _manifest(count: int) -> dict[str, Any]:
    return {
        "version": 1,
        "runtimeId": "scaling",
        "instances": [
            {"id": f"i{index}", "regionIds": [f"r{index}"], "initialScope": {"value": index}} for index in range(count)
        ],
        "locations": [],
        "regions": [{"id": f"r{index}", "selector": f"#root-{index}"} for index in range(count)],
        "fills": [],
        "bindings": [],
        "rootless": [],
        "mirrors": [],
    }


def _html(mode: str, count: int) -> str:
    if mode == "baseline":
        roots = "".join(f'<div id="root-{index}" x-data="{{ value: {index} }}"></div>' for index in range(count))
        manifest = ""
    else:
        roots = "".join(f'<div id="root-{index}"></div>' for index in range(count))
        payload = json.dumps(_manifest(count), separators=(",", ":"))
        manifest = f'<script type="application/json" data-component-first="alpine">{payload}</script>'
    return f"<!doctype html><html><body>{roots}{manifest}</body></html>"


def _run_page(page: Page, mode: str, count: int) -> dict[str, Any]:
    console: list[dict[str, str]] = []
    errors: list[str] = []
    page.on("console", lambda message: console.append({"type": message.type, "text": message.text}))
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.set_content(_html(mode, count))
    if mode == "graph":
        page.add_script_tag(path=ROOT_GROUP)
        page.add_script_tag(path=ADAPTER)
    page.evaluate(
        """
        window.__componentFirstScalingStarted = performance.now()
        """
    )
    page.add_script_tag(path=ALPINE)
    if mode == "graph":
        result = page.evaluate(
            """
            async () => {
              const [runtime] = await window.ComponentFirstSpikeReady
              const last = document.querySelector(`#root-${runtime.instanceState.size - 1}`)
              return {
                elapsed: performance.now() - window.__componentFirstScalingStarted,
                instances: runtime.instanceState.size,
                roots: Array.from(runtime.instanceState.values()).reduce(
                  (total, state) => total + state.els.length,
                  0,
                ),
                value: window.Alpine.evaluate(last, 'value'),
              }
            }
            """
        )
    else:
        page.wait_for_function(
            "count => document.querySelector(`#root-${count - 1}`)?._x_dataStack?.length > 0",
            arg=count,
        )
        result = page.evaluate(
            """
            (count) => {
              const last = document.querySelector(`#root-${count - 1}`)
              return {
                elapsed: performance.now() - window.__componentFirstScalingStarted,
                instances: count,
                roots: document.querySelectorAll('[x-data]').length,
                value: window.Alpine.evaluate(last, 'value'),
              }
            }
            """,
            count,
        )
    assert console == []
    assert errors == []
    assert result["instances"] == count
    assert result["roots"] == count
    assert result["value"] == count - 1
    assert result["elapsed"] >= 0
    return result


def _run_engine(engine: BrowserType) -> dict[str, Any]:
    browser = engine.launch(headless=True)
    result: dict[str, Any] = {"browserVersion": browser.version, "counts": {}}
    for count in COUNTS:
        modes = {}
        for mode in ("baseline", "graph"):
            passes = []
            for _ in range(RUNS_PER_MODE):
                page = browser.new_page()
                passes.append(_run_page(page, mode, count))
                page.close()
            modes[mode] = {
                "medianMilliseconds": median(item["elapsed"] for item in passes),
                "passes": passes,
            }
        payload = json.dumps(_manifest(count), separators=(",", ":")).encode()
        result["counts"][str(count)] = {
            "manifestBytes": len(payload),
            "manifestGzipBytes": len(gzip.compress(payload, mtime=0)),
            "modes": modes,
        }
    browser.close()
    return result


def main() -> None:
    with sync_playwright() as playwright:
        evidence = {
            "runsPerMode": RUNS_PER_MODE,
            "engines": {
                "chromium": _run_engine(playwright.chromium),
            },
        }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
