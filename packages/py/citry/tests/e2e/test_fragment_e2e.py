"""
Cross-browser e2e for the ``fragment`` strategy (HTMX-style on-demand loading).

Proves the full live path: an initial page loads the runtime, then fetches a
fragment and inserts it; the runtime sees the fragment's manifest, fetches the
component's JS and CSS from citry's ``/citry/cache/...`` routes, runs the JS,
and applies the styles. This is what makes citry's fragments "just work" in
the browser, and it exercises the live-server half of the harness.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.dependencies.routes import script_url

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
        js = "$component(({ els, data }) => { els[0].setAttribute('data-n', String(data.n)); });"

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, int]:
            return {"n": 42}

    # Rendered on the same instance the server uses, so the per-instance vars
    # script is in that instance's cache when the /citry/cache route serves it.
    fragment_html = Frag().render().serialize(deps_strategy="fragment")

    base = serve_live(c, _PAGE, fragment_html)
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('.frag')?.dataset.n === '42'")
    assert page.locator(".frag").get_attribute("data-n") == "42"


def test_fragment_callback_waits_for_component_css(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class StyledProbe(Component):
        citry = c
        template = '<div class="css-readiness-probe">probe</div>'
        css = ".css-readiness-probe { color: rgb(31, 41, 55); }"
        js = """
          $component(({ els }) => {
            const root = els[0];
            root.dataset.callbackColor = getComputedStyle(root).color;
          });
        """

    fragment_html = StyledProbe().render().serialize(deps_strategy="fragment")
    held_routes: list[Any] = []
    page.route("**/cache/*.css", lambda route: held_routes.append(route))

    base = serve_live(c, _PAGE, fragment_html)
    page.goto(base + "/")
    for _ in range(100):
        if held_routes:
            break
        page.wait_for_timeout(10)
    assert len(held_routes) == 1
    assert page.locator(".css-readiness-probe").get_attribute("data-callback-color") is None

    held_routes[0].continue_()
    page.wait_for_function(
        "document.querySelector('.css-readiness-probe')?.dataset.callbackColor === 'rgb(31, 41, 55)'"
    )


def test_fragment_static_and_scoped_css_load_on_demand(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Static(Component):
        citry = c
        template = '<div id="static-fragment">static</div>'
        css = "#static-fragment { background-color: rgb(231, 241, 255); border: 2px solid rgb(0, 123, 255); }"

    class Themed(Component):
        citry = c
        template = '<div id="themed-fragment">themed</div>'
        css = "#themed-fragment { background-color: var(--bg-color); border: 2px solid var(--border-color); }"

        def css_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"bg-color": "rgb(212, 237, 218)", "border-color": "rgb(40, 167, 69)"}

    class Fragment(Component):
        citry = c
        template = "<section><c-static /><c-themed /></section>"

    rendered = Fragment().render()
    themed_record = next(
        record for record in rendered.context.extra["dependencies"] if record.class_id == Themed.class_id
    )
    assert themed_record.css_vars_hash is not None
    fragment_html = rendered.serialize(deps_strategy="fragment")

    base = serve_live(c, _PAGE, fragment_html)
    page.goto(base + "/")
    page.wait_for_function("""() => {
        const plain = document.querySelector('#static-fragment');
        const themed = document.querySelector('#themed-fragment');
        if (!plain || !themed) return false;
        const plainStyle = getComputedStyle(plain);
        const themedStyle = getComputedStyle(themed);
        return plainStyle.backgroundColor === 'rgb(231, 241, 255)'
            && plainStyle.borderColor === 'rgb(0, 123, 255)'
            && themedStyle.backgroundColor === 'rgb(212, 237, 218)'
            && themedStyle.borderColor === 'rgb(40, 167, 69)';
    }""")

    assert page.locator("#static-fragment").get_attribute(f"data-ccss-{themed_record.css_vars_hash}") is None
    assert page.locator("#themed-fragment").get_attribute(f"data-ccss-{themed_record.css_vars_hash}") == ""
    assert page.locator(f'link[href="{script_url(Static, "css")}"]').count() == 1
    assert page.locator(f'link[href="{script_url(Themed, "css")}"]').count() == 1
    assert page.locator(f'link[href="/citry/cache/{Themed.class_id}.{themed_record.css_vars_hash}.css"]').count() == 1


def test_fragment_local_dependency_assets_load_on_demand(page: Any, serve_live: Any, tmp_path: Any) -> None:
    (tmp_path / "fragment-dependency.js").write_text(
        "document.querySelector('#dependency-fragment').dataset.loaded = 'true';"
    )
    (tmp_path / "fragment-dependency.css").write_text(
        "#dependency-fragment { color: rgb(76, 29, 149); background-color: rgb(237, 233, 254); }"
    )
    c = Citry(dirs=[tmp_path])
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        template = '<div id="dependency-fragment">fragment dependency</div>'

        class Dependencies:
            js = "fragment-dependency.js"
            css = "fragment-dependency.css"

    fragment_html = Frag().render().serialize(deps_strategy="fragment")
    base = serve_live(c, _PAGE, fragment_html)
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#dependency-fragment')?.dataset.loaded === 'true'")

    styles = page.eval_on_selector(
        "#dependency-fragment",
        "el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor})",
    )
    assert styles == {"color": "rgb(76, 29, 149)", "background": "rgb(237, 233, 254)"}
    emitted = page.evaluate(
        """() => ({
          scripts: [...document.querySelectorAll('script:not([src])')].map((el) => el.textContent),
          styles: [...document.querySelectorAll('style')].map((el) => el.textContent),
        })"""
    )
    assert any("dependency-fragment" in content for content in emitted["scripts"])
    assert any("#dependency-fragment" in content for content in emitted["styles"])


def test_content_page_dedupes_a_reused_components_css(page: Any, serve_live: Any) -> None:
    # A content-only mounted page (component CSS, no $component) still ships
    # the runtime and a markLoaded manifest, so a fragment that reuses the same
    # component dedups its CSS instead of re-fetching it and duplicating the
    # <link>. Live regression for the fragment-dedup fix
    # (docs/design/migration_djc_tests.md, 2026-07-02).
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<div class="card">card</div>'
        css = ".card { color: rgb(0, 128, 128); }"

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-card /><div id='target'></div></body></html>"

    css_url = script_url(Card, "css")
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
    # component that has plain JS (no $component) ships the runtime and a
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

    js_url = script_url(Widget, "js")
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
