"""
Cross-browser e2e for the ``fragment`` strategy (HTMX-style on-demand loading).

Proves the full live path: an initial page loads the runtime, then fetches a
fragment and inserts it. For an interactive fragment the runtime sees the
fragment's Vue manifest, fetches the component's JS and CSS from citry's
mounted routes, waits for the styles, and mounts the component. A static
fragment carries ordinary style and script tags for the inserting library to
run. This exercises the live-server half of the harness.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.dependencies.routes import script_url

pytestmark = pytest.mark.e2e

# The initial page: load the runtime, then fetch the fragment and drop it in.
# innerHTML-inserted Vue fragment manifests are picked up by the runtime's
# MutationObserver, which then fetches the component's assets and mounts it.
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
        template = '<div ref="root" class="frag">frag</div>'
        js = """
          $component(({ component }) => {
            component.$refs.root.setAttribute('data-n', String(component.n));
          });
        """

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
        template = '<div ref="root" class="css-readiness-probe">probe</div>'
        css = ".css-readiness-probe { color: rgb(31, 41, 55); }"
        js = """
          $component(({ component }) => {
            const root = component.$refs.root;
            root.dataset.callbackColor = getComputedStyle(root).color;
          });
        """

    fragment_html = StyledProbe().render().serialize(deps_strategy="fragment")
    held_routes: list[Any] = []
    # An interactive fragment serves its stylesheet by content digest.
    page.route("**/ext/events/assets/*.css", lambda route: held_routes.append(route))

    base = serve_live(c, _PAGE, fragment_html)
    page.goto(base + "/")
    for _ in range(100):
        if held_routes:
            break
        page.wait_for_timeout(10)
    assert len(held_routes) == 1
    # The Vue fragment mounts only after its stylesheet loads, so neither the
    # component nor its callback exists while the stylesheet is held.
    assert page.locator(".css-readiness-probe").count() == 0

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
    (tmp_path / "fragment-dependency.js").write_text("globalThis.__fragmentDependencyLoaded = true;")
    (tmp_path / "fragment-dependency.css").write_text(
        "#dependency-fragment { color: rgb(76, 29, 149); background-color: rgb(237, 233, 254); }"
    )
    c = Citry(dirs=[tmp_path])
    c.set_mounted_prefix("/citry")

    class Frag(Component):
        citry = c
        template = '<div id="dependency-fragment">fragment dependency</div>'
        js = """
          $component(({ component }) => {
            component.$el.dataset.loaded = String(globalThis.__fragmentDependencyLoaded === true);
          });
        """

        class Dependencies:
            js = "fragment-dependency.js"
            css = "fragment-dependency.css"

    fragment_html = Frag().render().serialize(deps_strategy="fragment")
    # A static fragment carries ordinary style and script tags and relies on
    # the inserting library to run its scripts, as htmx does. innerHTML never
    # runs scripts, so insert through a contextual fragment, which does.
    page_html = _PAGE.replace(
        "document.getElementById('target').innerHTML = html;",
        "const target = document.getElementById('target');"
        " target.append(document.createRange().createContextualFragment(html));",
    )
    assert page_html != _PAGE
    base = serve_live(c, page_html, fragment_html)
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('#dependency-fragment')?.dataset.loaded === 'true'")

    styles = page.eval_on_selector(
        "#dependency-fragment",
        "el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor})",
    )
    assert styles == {"color": "rgb(76, 29, 149)", "background": "rgb(237, 233, 254)"}
    assert page.evaluate("() => window.__fragmentDependencyLoaded") is True
    assert page.locator("link[data-citry-vue-style-app][data-citry-css-url]").count() == 1


def test_content_page_dedupes_a_reused_components_css(page: Any, serve_live: Any) -> None:
    # The initial page and a later fragment share the same content-addressed
    # stylesheet. Each Vue app owns its own style node, while the browser
    # fetches the immutable URL only once.
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<div class="card">card</div>'
        js = "$component({});"
        css = ".card { color: rgb(0, 128, 128); }"

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-card /></body></html>"

    page_html = Page().render().serialize()
    fragment_html = Card().render().serialize(deps_strategy="fragment")
    requests: list[str] = []
    page.on("request", lambda request: requests.append(request.url))
    base = serve_live(c, page_html, fragment_html)
    page.goto(base + "/")

    page.wait_for_selector(".card")
    page.wait_for_function("() => __citryRuntime._apps.size === 1")
    initial_css_requests = [url for url in requests if "/citry/ext/events/assets/" in url and url.endswith(".css")]
    assert len(initial_css_requests) == 1

    # The page's Vue app owns its mount element, and a fragment may not be
    # inserted inside it, so give the fragment its own element beside it.
    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text()).then((html) => {"
        " const target = document.createElement('div'); target.id = 'target';"
        " document.body.append(target); target.innerHTML = html; })"
    )
    page.wait_for_selector("#target .card")
    page.wait_for_function("() => __citryRuntime._apps.size === 2")
    page.wait_for_function(
        "() => getComputedStyle(document.querySelector('#target .card')).color === 'rgb(0, 128, 128)'"
    )

    # The fragment's app gets its own style node for the same URL, and the
    # browser does not request the stylesheet a second time.
    css_requests = [url for url in requests if "/citry/ext/events/assets/" in url and url.endswith(".css")]
    assert css_requests == initial_css_requests
    styles = page.evaluate(
        """() => [...document.querySelectorAll('link[data-citry-vue-style-app][data-citry-css-url]')]
            .map((node) => ({app: node.dataset.citryVueStyleApp, url: node.dataset.citryCssUrl}))"""
    )
    assert len(styles) == 2
    assert len({item["app"] for item in styles}) == 2
    assert len({item["url"] for item in styles}) == 1


def test_fragment_reuses_a_component_script_the_page_already_loaded(page: Any, serve_live: Any) -> None:
    # The page and a later fragment both render Widget. The Vue runtime loads
    # each component script once per page, keyed by its URL (which changes
    # whenever the script's content changes), so the fragment must neither
    # fetch the script again nor run the code a second time.
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = c
        template = """
            <div class="widget">w</div>
        """
        js = """
            window.__widgetRuns = (window.__widgetRuns || 0) + 1;
        """

    class Page(Component):
        citry = c
        template = """
            <html><head></head><body><c-widget /></body></html>
        """

    page_html = Page().render().serialize()
    page_html = page_html.replace("</body>", '<div id="target"></div></body>')
    fragment_html = Widget().render().serialize(deps_strategy="fragment")
    # Read the script URL from the fragment's own manifest, so the check
    # follows whatever URL the server actually asks the browser to load.
    manifest_json = re.search(
        r'<script type="application/json" data-citry-vue-fragment>(.*?)</script>', fragment_html, re.DOTALL
    )
    assert manifest_json is not None
    fragment_scripts = json.loads(manifest_json.group(1))["vue"]["prepared"]["manifest"]["scripts"]
    [js_url] = [
        asset["source"]["url"] for asset in fragment_scripts if asset["owner"].get("typeKey") == Widget.class_id
    ]
    assert js_url in page_html

    # The runtime removes a script element once it has run, so count the
    # browser's requests for the URL rather than elements in the document.
    requested: list[str] = []
    page.on("request", lambda request: requested.append(request.url) if request.url.endswith(js_url) else None)

    base = serve_live(c, page_html, fragment_html)
    page.goto(base + "/")
    page.wait_for_function("() => window.__widgetRuns === 1")
    assert len(requested) == 1

    # The page's Vue app owns its mount element, and a fragment may not be
    # inserted inside it, so give the fragment its own element beside it.
    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text()).then((html) => {"
        " const target = document.createElement('div'); target.id = 'target';"
        " document.body.append(target); target.innerHTML = html; })"
    )
    page.wait_for_selector("#target .widget")

    assert len(requested) == 1
    assert page.evaluate("() => window.__widgetRuns") == 1
