"""
Cross-browser e2e for the ``fragment`` strategy (HTMX-style on-demand loading).

Proves the full live path: an initial page loads the runtime, then fetches a
fragment and inserts it; the runtime sees the fragment's manifest, fetches the
component's JS from citry's ``/citry/cache/...`` routes, and runs it. This is
what makes citry's fragments "just work" in the browser, and it exercises the
live-server half of the harness.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

# The initial page: load the runtime, then fetch the fragment and drop it in.
# innerHTML-inserted manifests are picked up by the runtime's MutationObserver,
# which then fetches and runs the component's scripts.
_PAGE = """
<html>
  <head><script src="/citry/citry.js"></script></head>
  <body>
    <div id="target"></div>
    <script>
      fetch('/fragment')
        .then((r) => r.text())
        .then((html) => { document.getElementById('target').innerHTML = html; });
    </script>
  </body>
</html>
"""


def test_fragment_scripts_load_on_demand(page: Any, serve_live: Any) -> None:
    c = Citry()
    # The fragment references its scripts by URL, so the prefix must be set
    # before rendering (serve_live also sets it, to the same value).
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        template = '<div class="frag">frag</div>'
        js = "$onComponent(({ els, data }) => { els[0].setAttribute('data-n', String(data.n)); });"

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"n": 42}

    # Rendered on the same instance the server uses, so the per-instance vars
    # script is in that instance's cache when the /citry/cache route serves it.
    fragment_html = Frag().render().serialize(deps_strategy="fragment")

    base = serve_live(c, _PAGE, fragment_html)
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('.frag')?.dataset.n === '42'")
    assert page.locator(".frag").get_attribute("data-n") == "42"


def test_content_page_dedupes_a_reused_components_css(page: Any, serve_live: Any) -> None:
    # A content-only mounted page (component CSS, no $onComponent) still ships
    # the runtime and a markLoaded manifest, so a fragment that reuses the same
    # component dedups its CSS instead of re-fetching it and duplicating the
    # <link>. Live regression for the fragment-dedup fix
    # (docs/design/citry_migration_tests.md, 2026-07-02).
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<div class="card">card</div>'
        css = ".card { color: rgb(0, 128, 128); }"

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-card /><div id='target'></div></body></html>"

    css_url = f"/citry/cache/{Card.class_id}.css"
    # Document strategy on a mounted page with component CSS: ships the runtime
    # and a markLoaded manifest naming the card's CSS cache URL.
    page_html = Page().render().serialize()
    # The fragment reuses the same card; its manifest asks to fetch that URL.
    fragment_html = Card().render().serialize(deps_strategy="fragment")

    base = serve_live(c, page_html, fragment_html)
    page.goto(base + "/")

    # Signal 1: the runtime registered the card's CSS as already-loaded from the
    # page's markLoaded manifest (without the fix, no runtime ships and this
    # never becomes true).
    page.wait_for_function("([url]) => window.Citry?.manager?.isScriptLoaded('css', url)", arg=[css_url])

    # Insert a fragment that reuses the card.
    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text())"
        ".then((html) => { document.getElementById('target').innerHTML = html; })"
    )
    page.wait_for_selector("#target .card")  # fragment content inserted
    # Its manifest was processed (a <script> is never "visible", so match on attach).
    page.wait_for_selector("#target script[data-citry][data-citry-processed]", state="attached")

    # Signal 2: the runtime skipped the fetch, so no duplicate stylesheet <link>
    # was added for the card's CSS.
    assert page.locator(f'link[href="{css_url}"]').count() == 0


def test_content_page_dedupes_a_reused_components_js(page: Any, serve_live: Any) -> None:
    # JS counterpart of the CSS dedup test. A content-only mounted page with a
    # component that has plain JS (no $onComponent) ships the runtime and a
    # markLoaded manifest, so a fragment reusing the component neither re-fetches
    # nor re-runs the component's JS.
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = c
        template = '<div class="widget">w</div>'
        js = "window.__widgetRuns = (window.__widgetRuns || 0) + 1;"

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-widget /><div id='target'></div></body></html>"

    js_url = f"/citry/cache/{Widget.class_id}.js"
    page_html = Page().render().serialize()
    fragment_html = Widget().render().serialize(deps_strategy="fragment")

    base = serve_live(c, page_html, fragment_html)
    page.goto(base + "/")

    # The page's inline component JS ran once, and the runtime registered its
    # cache URL as already-loaded from markLoaded.
    page.wait_for_function("() => window.__widgetRuns === 1")
    page.wait_for_function("([url]) => window.Citry?.manager?.isScriptLoaded('js', url)", arg=[js_url])

    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text())"
        ".then((html) => { document.getElementById('target').innerHTML = html; })"
    )
    page.wait_for_selector("#target .widget")  # fragment content inserted
    page.wait_for_selector("#target script[data-citry][data-citry-processed]", state="attached")

    # Deduped against markLoaded: no <script src> was added, and the component's
    # JS did not run a second time.
    assert page.locator(f'script[src="{js_url}"]').count() == 0
    assert page.evaluate("() => window.__widgetRuns") == 1
