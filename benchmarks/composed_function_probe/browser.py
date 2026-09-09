"""Check composed caller-owned button and icon templates across a browser slot boundary."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "packages/py/citry"), str(ROOT / "packages/py/citry_core")]

from benchmarks.composed_function_probe.adapter import installed  # noqa: E402
from benchmarks.inline_browser_probe.probe import READY, serve  # noqa: E402
from benchmarks.ownership_journal_probe.probe import scenario  # noqa: E402
from playwright.sync_api import Error as PlaywrightError  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from citry import Component  # noqa: E402


def fixtures(module: Any) -> type[Component]:
    class Receiver(Component):
        citry = module.app
        template = """
<section x-data="{owner: 'receiver', receiverCount: 0}">
    <c-slot name="body" />
    <c-slot name="empty">
        <c-Button
            c-attrs="{'id': 'fallback', '@click': 'receiverCount += 1'}"
        >
            <c-Icon
                name="home"
                c-attrs="{'id': 'icon-fallback'}"
                c-svg_attrs="{'class': 'svg-fallback'}"
            >
                fallback
            </c-Icon>
        </c-Button>
    </c-slot>
    <output id="receiver-count" x-text="receiverCount"></output>
</section>
"""

    class Child(Component):
        citry = module.app
        template = """
<span
    id="child"
    x-data="{owner: 'child'}"
    x-text="owner"
>
</span>
"""

    class Page(Component):
        citry = module.app
        template = """
<html><body><main x-data="{owner: 'caller', count: 0}">
    <c-Button
        c-attrs="{'id': 'direct', '@click': 'count += 1'}"
    >
        <c-Icon
            name="home"
            c-attrs="{'id': 'icon-direct'}"
            c-svg_attrs="{'class': 'svg-direct'}"
        >
            direct
        </c-Icon>
    </c-Button>
    <c-receiver><c-fill name="body">
        <c-Button
            c-attrs="{'id': 'fill', '@click': 'count += 1'}"
        >
            <c-Icon
                name="home"
                c-attrs="{'id': 'icon-fill'}"
                c-svg_attrs="{'class': 'svg-fill'}"
            >
                fill
            </c-Icon>
        </c-Button>
    </c-fill></c-receiver>
    <c-Button c-attrs="{'id': 'child-wrapper'}"><c-Icon name="home"><c-child /></c-Icon></c-Button>
    <output id="caller-count" x-text="count"></output>
</main></body></html>
"""

    return Page


def check(browser: Any, url: str, variant: str) -> dict[str, Any]:
    enabled = variant in ("immediate", "deferred")
    page = browser.new_page()
    errors = []
    console_errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    result = {}
    try:
        page.goto(url)
        page.wait_for_function(READY)
        page.wait_for_function("document.querySelector('#child').textContent === 'child'")
        scopes = page.evaluate("""() => Object.fromEntries(
            ['direct','fill','fallback','icon-direct','icon-fill','icon-fallback','child'].map(id => {
            const element = document.getElementById(id);
            return [id, {owner: Alpine.evaluate(element, 'typeof owner === "undefined" ? null : owner'),
                         isolated: element.hasAttribute('data-citry-root')}];
        }))""")
        expected = {
            name: {
                "owner": ("receiver" if name in ("fallback", "icon-fallback") else "caller") if enabled else None,
                "isolated": not enabled,
            }
            for name in ("direct", "fill", "fallback", "icon-direct", "icon-fill", "icon-fallback")
        }
        expected["child"] = {"owner": "child", "isolated": True}
        if scopes != expected:
            raise AssertionError(f"Scope mismatch: {scopes!r}; expected {expected!r}")
        child_scope = page.evaluate("""() => ({
            count: Alpine.evaluate(document.getElementById('child'), 'typeof count'),
            receiverCount: Alpine.evaluate(document.getElementById('child'), 'typeof receiverCount')
        })""")
        if child_scope != {"count": "undefined", "receiverCount": "undefined"}:
            raise AssertionError(f"Ordinary child inherited caller variables: {child_scope!r}")
        if enabled:
            page.locator(".svg-direct path").click()
            page.locator(".svg-fill path").click()
            page.locator(".svg-fallback path").click()
            page.wait_for_function("document.querySelector('#caller-count').textContent === '2'")
            page.wait_for_function("document.querySelector('#receiver-count').textContent === '1'")
        final = page.evaluate("""() => ({caller: document.querySelector('#caller-count').textContent,
            receiver: document.querySelector('#receiver-count').textContent,
            revisions: Citry.manager.ownership.revisions().length})""")
        if final != {"caller": "2" if enabled else "0", "receiver": "1" if enabled else "0", "revisions": 1}:
            raise AssertionError(f"Wrong final browser state: {final!r}")
        if errors or console_errors:
            raise AssertionError("Unexpected browser error")
        result.update(status="passed", scopes=scopes, final=final, clicked=enabled, child_scope=child_scope)
    except (AssertionError, PlaywrightError) as error:
        result.update(status="failed", failure=str(error))
    finally:
        result.update(page_errors=errors, console_errors=console_errors)
        page.close()
    return result


def main() -> None:
    module = scenario()
    page_cls = fixtures(module)
    documents = {}
    for variant in ("reference", "immediate", "deferred"):
        with installed(module, variant):
            documents["/" + variant] = str(page_cls())
    results = {}
    server = serve(documents)
    try:
        with sync_playwright() as playwright:
            for name in ("chromium", "firefox", "webkit"):
                browser = getattr(playwright, name).launch()
                try:
                    results[name] = {
                        "version": browser.version,
                        "variants": {
                            variant: check(browser, f"http://127.0.0.1:{server.server_address[1]}/{variant}", variant)
                            for variant in ("reference", "immediate", "deferred")
                        },
                    }
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()
    paths = [
        Path(__file__),
        Path(__file__).with_name("adapter.py"),
        ROOT / "packages/py/citry/citry/ext/dependencies/client/citry.js",
        ROOT / "packages/py/citry/citry/ext/events/client/citry-events.js",
    ]
    failed = any(v["status"] == "failed" for r in results.values() for v in r["variants"].values())
    print(
        json.dumps(
            {
                "browser_qualification_only": True,
                "passed": not failed,
                "results": results,
                "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            },
            indent=2,
        )
    )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
