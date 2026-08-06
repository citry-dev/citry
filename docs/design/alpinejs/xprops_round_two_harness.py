# ruff: noqa: S101, T201
"""
Browser evidence for the x-props round-two exploration.

Run after the repo's additive e2e install:

    uv sync --locked --all-packages --group e2e
    .venv/bin/python docs/design/alpinejs/xprops_round_two_harness.py

Restore the ordinary environment afterwards:

    uv sync --locked --all-packages
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

REPO = Path(__file__).resolve().parents[3]
ALPINE = REPO / "packages/js/citry-client/node_modules/alpinejs/dist/cdn.js"

HTML = """
<span id="clear" x-data="{ value: 'ok' }" x-text="value"></span>
<div id="host" x-data="{ offset: 100, items: [
  { id: 'a', value: 10 }, { id: 'b', value: 20 }
] }">
  <template x-for="(item, index) in items" :key="item.id">
    <div class="row" x-props="{
      id: item.id, value: item.value, index, total: item.value + offset
    }"></div>
  </template>
</div>
"""

INSTALL = """
window.__evidence = {
  captures: [],
  supplies: [],
  cleanups: [],
  nextSerial: 1,
};
document.addEventListener("alpine:init", () => {
  const loopScopes = new WeakMap();

  Alpine.interceptInit((el) => {
    if (typeof el._x_refreshXForScope !== "function") return;
    const loopScope = el._x_dataStack[0];
    loopScopes.set(el, loopScope);
    window.__evidence.captures.push({
      markerPresent: true,
      keys: Object.keys(loopScope).sort(),
    });

    // Reproduce Citry's isolation after capturing Alpine's clone scope.
    Alpine.addScopeToNode(el, {});
    el._x_dataStack = el._x_dataStack.slice(0, 1);
  });

  Alpine.directive("props", (el, { expression }, { effect, cleanup }) => {
    const loopScope = loopScopes.get(el);
    const serial = window.__evidence.nextSerial++;
    let lastId = null;

    effect(() => {
      const value = Alpine.evaluateRaw(el.parentNode, expression, {
        scope: loopScope,
      });
      lastId = value.id;
      el.dataset.serial = String(serial);
      el.dataset.supply = JSON.stringify(value);
      window.__evidence.supplies.push({ serial, ...value });
    });

    cleanup(() => {
      window.__evidence.cleanups.push({ serial, id: lastId });
    });
  }).before("data");
});
"""


def _rows(page: Page) -> list[dict[str, Any]]:
    return page.locator(".row").evaluate_all(
        """els => els.map(el => ({
          serial: Number(el.dataset.serial),
          supply: JSON.parse(el.dataset.supply),
        }))"""
    )


def _run() -> dict[str, Any]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(HTML)
        page.evaluate(INSTALL)
        page.add_script_tag(path=ALPINE)
        page.wait_for_function("document.querySelectorAll('.row[data-supply]').length === 2")
        page.wait_for_function("document.querySelector('#clear').textContent === 'ok'")

        initial = _rows(page)
        page.eval_on_selector(
            "#host",
            """el => {
              Alpine.closestDataStack(el)[0].items = [
                { id: 'b', value: 25 }, { id: 'a', value: 11 }
              ];
            }""",
        )
        page.wait_for_function(
            """() => Array.from(document.querySelectorAll('.row'))
              .map(el => JSON.parse(el.dataset.supply).total)
              .join(',') === '125,111'"""
        )
        refreshed = _rows(page)

        page.eval_on_selector(
            "#host",
            """el => {
              Alpine.closestDataStack(el)[0].items = [{ id: 'b', value: 30 }];
            }""",
        )
        page.wait_for_function("document.querySelectorAll('.row').length === 1")
        page.wait_for_function("window.__evidence.cleanups.some(item => item.id === 'a')")

        page.eval_on_selector(
            "#clear",
            "el => { Alpine.closestDataStack(el)[0].value = undefined; }",
        )
        page.wait_for_function("document.querySelector('#clear').textContent === ''")

        evidence = page.evaluate("window.__evidence")
        result = {
            "capture_count": len(evidence["captures"]),
            "capture_keys": evidence["captures"][0]["keys"],
            "initial": initial,
            "refreshed": refreshed,
            "final": _rows(page),
            "cleanups": evidence["cleanups"],
            "cleared_text": page.locator("#clear").text_content(),
        }
        browser.close()
        return result


def _assert_result(result: dict[str, Any]) -> None:
    assert result["capture_count"] == 2
    assert result["capture_keys"] == ["index", "item"]
    assert [row["supply"] for row in result["initial"]] == [
        {"id": "a", "value": 10, "index": 0, "total": 110},
        {"id": "b", "value": 20, "index": 1, "total": 120},
    ]
    assert [row["supply"] for row in result["refreshed"]] == [
        {"id": "b", "value": 25, "index": 0, "total": 125},
        {"id": "a", "value": 11, "index": 1, "total": 111},
    ]
    assert {row["supply"]["id"]: row["serial"] for row in result["initial"]} == {
        row["supply"]["id"]: row["serial"] for row in result["refreshed"]
    }
    assert result["final"][0]["supply"] == {
        "id": "b",
        "value": 30,
        "index": 0,
        "total": 130,
    }
    serial_a = result["initial"][0]["serial"]
    assert {"id": "a", "serial": serial_a} in result["cleanups"]
    assert result["cleared_text"] == ""


if __name__ == "__main__":
    observed = _run()
    _assert_result(observed)
    print(json.dumps(observed, indent=2, sort_keys=True))
