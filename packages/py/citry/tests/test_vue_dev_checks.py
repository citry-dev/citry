"""
What the server sends for the development check of server-rendered HTML.

With ``Citry(mode="development")``, the browser compares each shell's served
contents (an element marked ``data-allow-mismatch="children"``, whose children
Vue builds in the browser) with Vue's first render. The comparison itself is
covered by ``packages/js/citry-client/test/dev-checks.test.mjs`` and, in a
real browser, by ``tests/e2e/test_vue_dev_checks_e2e.py``. These tests check
that only a development page carries the flag and the check's script, and that
a production page carries neither.
"""

import json
import re
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import DEV_CHECKS_SRC

# A global the check's script defines; only the script contains it.
_SCRIPT_MARKER = "CitryVueDevChecks = Object.freeze"
# The page's start configuration, a JSON block the runtime reads.
_CONFIGURATION = re.compile(
    r'<script type="application/json" data-citry-vue-document="[^"]+">(.*?)</script>', re.DOTALL
)


def _configuration(html: str) -> dict[str, Any]:
    match = _CONFIGURATION.search(html)
    assert match is not None, html[:500]
    return json.loads(match.group(1))


def _shell_page(engine: Citry) -> type[Component]:
    """A page whose Details component becomes a shell with served contents."""

    class Status(Component):
        citry = engine
        template = """
<p class="status">Status</p>
"""
        js = """
$component({props: ['open'], emits: ['close']});
"""

    class Details(Component):
        citry = engine

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, bool]:
            return {"open": False}

        template = """
<section class="details">
  <button
    type="button"
    :aria-expanded="open"
  >Details</button>
  <c-Status
    :open="open"
    @close="open = false"
  />
</section>
"""
        js = """
$component({});
"""

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Details</title></head>
  <body><main><c-Details /></main></body>
</html>
"""

    return Page


def _plain_page(engine: Citry) -> type[Component]:
    """A page Vue adopts completely, with no shell."""

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Counter</title></head>
  <body>
    <main>
      <button
        type="button"
        @click="count++"
      >Add</button>
    </main>
  </body>
</html>
"""
        js = """
$component({data() { return {count: 0}; }});
"""

    return Page


def test_development_page_with_served_shells_carries_the_flag_and_the_check() -> None:
    html = _shell_page(Citry(autodiscover=False, mode="development"))().render().serialize()

    configuration = _configuration(html)
    assert configuration["development"] is True
    assert configuration["emptyShells"] is True
    assert html.count(_SCRIPT_MARKER) == 1
    # The script is a classic script, placed before the module script that
    # starts the app, so its global exists when the runtime looks for it.
    assert html.index(_SCRIPT_MARKER) < html.index("__citryRuntime.startDocument(")


@pytest.mark.parametrize("page", [_shell_page, _plain_page])
def test_production_page_carries_neither_the_flag_nor_the_check(page: Any) -> None:
    html = page(Citry(autodiscover=False))().render().serialize()

    assert "development" not in _configuration(html)
    assert _SCRIPT_MARKER not in html


def test_development_page_without_served_shells_carries_only_the_flag() -> None:
    # With nothing to compare, the page goes without the script.
    html = _plain_page(Citry(autodiscover=False, mode="development"))().render().serialize()

    configuration = _configuration(html)
    assert configuration["development"] is True
    assert "emptyShells" not in configuration
    assert _SCRIPT_MARKER not in html


def test_the_check_script_ships_as_a_readable_file() -> None:
    # Development pages inline this file, so the package must include it.
    assert _SCRIPT_MARKER in DEV_CHECKS_SRC.read_text(encoding="utf8")
