"""
Browser proof of the development check of server-rendered HTML.

Vue builds the children of a shell (an element the server marks
``data-allow-mismatch="children"``) in the browser, so it never reports when
its first render there differs from what the server sent. With
``Citry(mode="development")`` the runtime compares the two and logs a console
warning. These tests load pages in Chromium and check that a real difference
warns, that correct pages and production pages stay silent, and that the
documented ways to accept a difference work.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e

_WIDE = {"width": 1280, "height": 800}
_NARROW = {"width": 600, "height": 800}


def _open(page: Any, url: str, viewport: dict[str, int]) -> tuple[list[str], list[str]]:
    """Load one page at a window size, wait for its app, and return its warnings and other problems."""
    warnings: list[str] = []
    problems: list[str] = []
    page.on("pageerror", lambda error: problems.append(str(error)))

    def record(message: Any) -> None:
        if message.type == "warning":
            warnings.append(message.text)
        elif message.type == "error":
            problems.append(message.text)

    page.on("console", record)
    # The listener must exist before the runtime dispatches citry:ready.
    page.add_init_script(
        "window.__citryReadyApps = [];"
        "document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));"
    )
    page.set_viewport_size(viewport)
    page.goto(url)
    page.wait_for_function("window.__citryReadyApps?.length === 1")
    return warnings, problems


def _details_page(engine: Citry, *, hook: str, button_attrs: str = "") -> type[Component]:
    """The error benchmark's m14 page: a panel that opens on wide windows, beside a status line."""

    class Status(Component):
        citry = engine
        template = """
<p class="status">
  Status: <span v-text="open ? 'open' : 'closed'"></span>
  <button
    type="button"
    @click="$emit('close')"
  >Close</button>
</p>
"""
        js = """
$component({
  props: {open: {type: Boolean, required: true}},
  emits: ['close'],
});
"""

    class Details(Component):
        citry = engine

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, bool]:
            return {"open": False}

        template = f"""
<section class="details">
  <button
    id="toggle"
    type="button"
    :aria-expanded="open"
    {button_attrs}
    @click="open = !open"
  >Details</button>
  <p v-if="open">Details are visible</p>
  <c-Status
    :open="open"
    @close="open = false"
  />
</section>
"""
        js = f"""
$component({{
  {hook}() {{
    this.open = window.matchMedia('(min-width: 60rem)').matches;
  }},
}});
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


def test_state_changed_before_the_first_render_warns_on_a_wide_window(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False, mode="development")
    html = _details_page(engine, hook="created")().render().serialize()

    warnings, problems = _open(page, serve_document(html), _WIDE)

    assert problems == [], problems
    [warning] = warnings
    assert warning.startswith("[Citry] Details_"), warning
    assert 'On <button id="toggle">, the server sent aria-expanded="false"' in warning
    assert 'the browser shows aria-expanded="true"' in warning
    # The page still works after the check.
    page.click("#toggle")
    page.wait_for_function("document.querySelector('#toggle').getAttribute('aria-expanded') === 'false'")


def test_the_same_page_is_silent_when_the_first_render_matches(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False, mode="development")
    html = _details_page(engine, hook="created")().render().serialize()

    warnings, problems = _open(page, serve_document(html), _NARROW)

    assert (warnings, problems) == ([], [])


def test_production_pages_do_not_load_or_run_the_check(page: Any, serve_document: Any) -> None:
    html = _details_page(Citry(autodiscover=False), hook="created")().render().serialize()

    warnings, problems = _open(page, serve_document(html), _WIDE)

    assert (warnings, problems) == ([], [])
    assert page.evaluate("typeof window.CitryVueDevChecks") == "undefined"


def test_state_changed_in_mounted_does_not_warn(page: Any, serve_document: Any) -> None:
    # mounted() runs after the first render, which is where Vue's own docs
    # put code that reads the browser.
    engine = Citry(autodiscover=False, mode="development")
    html = _details_page(engine, hook="mounted")().render().serialize()

    warnings, problems = _open(page, serve_document(html), _WIDE)

    assert (warnings, problems) == ([], [])
    page.wait_for_function("document.querySelector('#toggle').getAttribute('aria-expanded') === 'true'")


def test_data_allow_mismatch_accepts_an_intended_difference(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False, mode="development")
    html = _details_page(engine, hook="created", button_attrs='data-allow-mismatch="attribute"')().render().serialize()

    warnings, problems = _open(page, serve_document(html), _WIDE)

    assert (warnings, problems) == ([], [])


def test_a_correct_page_with_props_slots_lists_and_conditions_is_silent(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False, mode="development")

    class Card(Component):
        citry = engine
        template = """
<article
  class="card"
  :class="{'card--wide': wide}"
  :title="heading"
>
  <h2 v-text="heading"></h2>
  <slot></slot>
</article>
"""
        js = """
$component({props: ['heading', 'wide']});
"""

    class Board(Component):
        citry = engine

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"items": ["a", "b"], "flag": True, "label": "Hello", "count": 2}

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, str]:
            return {"owner": "Ada"}

        template = """
<section class="board">
  <ul>
    <li
      v-for="item in items"
      :key="item"
      :data-item="item"
      v-text="item"
    ></li>
  </ul>
  <ol>
    <li
      v-for="item in doubled"
      :key="item"
      v-text="item"
    ></li>
  </ol>
  <p v-if="flag">Flag on</p>
  <p v-else>Flag off</p>
  <p v-if="many">Many</p>
  <p v-else>Few</p>
  <span v-text="label"></span>
  <b v-text="shout"></b>
  <input
    type="checkbox"
    :checked="flag"
  />
  <button
    type="button"
    :disabled="!flag"
    :style="{color: flag ? 'green' : 'red'}"
  >Go</button>
  <c-Card
    :heading="label"
    :wide="many"
  >
    <em v-text="label"></em> by {{ owner }}
  </c-Card>
</section>
"""
        js = """
$component({
  computed: {
    doubled() { return this.items.map(item => item + item); },
    many() { return this.count > 1; },
    shout() { return this.label.toUpperCase(); },
  },
});
"""

    class Page(Component):
        citry = engine
        template = """
<!doctype html>
<html>
  <head><title>Board</title></head>
  <body><main><c-Board /></main></body>
</html>
"""

    html = Page().render().serialize()
    assert "CitryVueDevChecks" in html, "the page must have a shell with served contents to compare"

    warnings, problems = _open(page, serve_document(html), _WIDE)

    assert (warnings, problems) == ([], [])
