"""
Browser test for `#c-ignore` on an element in an interactive component.

The server writes the element's contents once, and the browser keeps those
nodes for the life of the component instance. A library can then change them,
and a later server render that produces different contents leaves them alone,
while the element itself and the rest of the component still update.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


def _capture_served_nodes(html: str, selector: str) -> str:
    """Record the elements `selector` matches while the browser parses the page, before the runtime runs."""
    host = html.index('<div id="citry-vue-')
    first_script = html.index("<script", host)
    # A node inside a shell is removed before Vue hydrates, so remember which ones are.
    capture = (
        f"<script>window.__servedNodes=[...document.querySelectorAll({json.dumps(selector)})];"
        "window.__servedInShell=window.__servedNodes.map("
        "node => node.parentElement.closest('[data-allow-mismatch]') !== null);</script>"
    )
    return html[:first_script] + capture + html[first_script:]


def test_a_server_render_leaves_the_ignored_contents_untouched(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="ignore-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Chart(Component):
        citry = engine
        template = """
            <main>
              <button id="advance" @c-click="advance">advance</button>
              <p id="stage">{{ stage }}</p>
              <div id="chart" #c-ignore c-data-stage="stage">
                <canvas id="canvas"></canvas>
                <span id="label">stage {{ stage }}</span>
              </div>
            </main>
        """

        class State:
            stage: int = 0

        class Events:
            def advance(self, state: Chart.State):
                state.stage += 1
                return Chart(stage=state.stage)

        def template_data(self, kwargs, slots):
            return {"stage": kwargs.get("stage", 0)}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    # Remember the canvas the browser parsed from the served page, before Vue starts.
    served = _capture_served_nodes(Chart(stage=0).render().serialize(), "#canvas")
    base = serve_live(engine, served, "")
    page.goto(base + "/")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 0")
    # Vue adopted the served nodes instead of building new ones.
    assert page.evaluate("window.__servedNodes.length === 1 && window.__servedInShell[0] === false")
    assert page.evaluate("window.__servedNodes[0] === document.querySelector('#canvas')")
    # Page code takes over the kept nodes, as a chart library would.
    page.evaluate("""() => {
      globalThis.__canvas = document.querySelector('#canvas');
      globalThis.__canvas.dataset.owner = 'library';
      document.querySelector('#chart').append(Object.assign(document.createElement('i'), {id: 'added'}));
    }""")

    for revision in (1, 2):
        page.locator("#advance").click()
        page.wait_for_function(
            "revision => __citryRuntime._apps.values().next().value.revision === revision",
            arg=revision,
        )
        # The rest of the component and the element's own attributes update.
        assert page.locator("#stage").text_content() == str(revision)
        assert page.locator("#chart").get_attribute("data-stage") == str(revision)
        # The contents stay as the first render wrote them, with the library's changes.
        assert page.locator("#label").text_content() == "stage 0"
        assert page.evaluate("globalThis.__canvas === document.querySelector('#canvas')")
        assert page.locator("#canvas").get_attribute("data-owner") == "library"
        assert page.locator("#added").count() == 1

    assert faults == []
