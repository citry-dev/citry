"""Test whether caller-owned lowering preserves a static-JS receiver's named fill scope."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.inline_browser_probe.probe import READY, serve  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

import citry_core._rust as native  # noqa: E402
from citry import Citry, Component  # noqa: E402

REGISTRATION = """
document.addEventListener('alpine:init', () => {
    Alpine.data('slot_js_receiver', () => ({owner: 'receiver', count: 0}));
});
"""
SUPPLY = """
<button id="supplied" x-text="owner" @click="count += 1"></button>
"""
RECEIVER = """
<section id="receiver" x-data="slot_js_receiver">
    <button id="own" @click="count += 1">Receiver button</button>
    <output id="receiver-count" x-text="count"></output>
    OUTLET
</section>
"""


def document(candidate: bool) -> str:
    """Use ordinary named content or its one-outlet caller-owned lowering."""
    app = Citry()
    receiver_namespace: dict[str, Any] = {
        "citry": app,
        "name": "Receiver",
        "template": RECEIVER.replace("OUTLET", "<c-slot />" if candidate else '<c-slot name="body" />'),
    }
    if candidate:
        receiver_namespace["simple"] = True
    else:
        receiver_namespace["js"] = REGISTRATION
    type("Receiver", (Component,), receiver_namespace)
    supply = SUPPLY if candidate else '<c-fill name="body">' + SUPPLY + "</c-fill>"
    page_namespace: dict[str, Any] = {
        "citry": app,
        "template": """
<html><body>
    <main id="caller" x-data="{owner: 'caller', count: 0}">
        <output id="caller-count" x-text="count"></output>
        <c-Receiver>SUPPLY</c-Receiver>
    </main>
</body></html>
""".replace("SUPPLY", supply),
    }
    if candidate:
        page_namespace["js"] = REGISTRATION
    page_class = type("Page", (Component,), page_namespace)
    return page_class().render().serialize(deps_strategy="document")


def observe(browser: Any, url: str) -> dict[str, Any]:
    """Read both scopes and actual click results after Alpine activation."""
    page = browser.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    try:
        page.goto(url)
        page.wait_for_function(READY)
        initial = page.locator("#supplied").inner_text()
        receiver_owner = page.evaluate("Alpine.evaluate(document.querySelector('#receiver'), 'owner')")
        page.locator("#supplied").click()
        after_supply = {
            "caller": page.locator("#caller-count").inner_text(),
            "receiver": page.locator("#receiver-count").inner_text(),
        }
        page.locator("#own").click()
        after_own = {
            "caller": page.locator("#caller-count").inner_text(),
            "receiver": page.locator("#receiver-count").inner_text(),
        }
        return {
            "supplied_owner": initial,
            "receiver_owner": receiver_owner,
            "after_supplied_click": after_supply,
            "after_receiver_click": after_own,
            "errors": errors,
        }
    finally:
        page.close()


def main() -> None:
    """Retain the counterexample without claiming a complete fast-path implementation."""
    documents = {f"/{name}": document(name == "candidate") for name in ("control", "candidate")}
    server = serve(documents)
    results: dict[str, Any] = {}
    versions: dict[str, str] = {}
    try:
        with sync_playwright() as playwright:
            for name in ("chromium", "firefox", "webkit"):
                browser = getattr(playwright, name).launch()
                try:
                    versions[name] = browser.version
                    results[name] = {
                        variant: observe(browser, f"http://127.0.0.1:{server.server_address[1]}/{variant}")
                        for variant in ("control", "candidate")
                    }
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
    expected = {
        "supplied_owner": "caller",
        "receiver_owner": "receiver",
        "after_supplied_click": {"caller": "1", "receiver": "0"},
        "after_receiver_click": {"caller": "1", "receiver": "1"},
        "errors": [],
    }
    report = {
        "candidate": "caller-owned named-content lowering with hoisted static Alpine registration",
        "scope": "one named outlet manually lowered to current simple default content; not a general implementation",
        "expected": expected,
        "browsers": results,
        "browser_versions": versions,
        "control_passed": all(value["control"] == expected for value in results.values()),
        "candidate_preserves_contract": all(value["candidate"] == expected for value in results.values()),
        "document_sha256": {name: hashlib.sha256(html.encode()).hexdigest() for name, html in documents.items()},
        "source_sha256": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).with_name("slot_js_plan.md"),
                ROOT / "packages/py/citry/citry/_simple_runtime.py",
                ROOT / "packages/py/citry/citry/_simple_declarations.py",
                ROOT / "packages/py/citry/citry/component_render.py",
                ROOT / "packages/py/citry/citry/nodes/__init__.py",
                ROOT / "packages/py/citry/citry/ext/dependencies/extension.py",
                ROOT / "packages/py/citry/tests/e2e/test_alpine_slot_scope_e2e.py",
            )
        },
        "native_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
    }
    print(json.dumps(report, indent=2))
    if not report["control_passed"]:
        raise SystemExit("The control did not establish the expected contract.")


if __name__ == "__main__":
    main()
