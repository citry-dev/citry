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
