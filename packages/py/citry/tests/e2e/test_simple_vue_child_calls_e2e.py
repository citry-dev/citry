"""
A browser check that children called from a ``simple="vue"`` template hydrate and keep working.

Each row is ``simple="vue"`` and owns a Vue toggle. It calls an ordinary
``Counter`` whose button sends a Citry event; the server answers with a new
render of that one counter. The page must hydrate without mismatches, each
row's toggle must still work, and a counter update must leave the row's own
browser state alone.
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.e2e


def test_children_of_simple_vue_rows_hydrate_and_handle_events(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="simple-vue-child-calls-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class CounterState:
        label: str = ""
        count: int = 0

    class Counter(Component):
        citry = engine
        State = CounterState

        class Kwargs:
            label: str
            count: int = 0

        class Events:
            def bump(self, state: CounterState) -> Component:
                return Counter(label=state.label, count=state.count + 1)

        template = """
            <button class="counter" @c-click="bump">{{ label }}: {{ count }}</button>
        """

    class Row(Component):
        citry = engine
        simple = "vue"

        class Kwargs:
            name: str

        template = """
            <li class="row">
              <button class="toggle" @click="open = !open" :aria-expanded="open">{{ name }}</button>
              <c-Counter c-label="name" />
            </li>
        """
        js = "$component({data(){return {open:false}}})"

    class Page(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"names": ["one", "two"]}

        template = """
            <ul><c-Row c-for="name in names" #c-key="name" c-name="name" /></ul>
        """

    dispatcher_for(engine)
    html = Page().render().serialize()
    assert '"hydrate":true' in html
    faults: list[str] = []
    warnings: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None)
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(serve_live(engine, html, "") + "/")
    page.wait_for_function("window.__citryHydrationReport !== undefined")

    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    assert report["replacedElementCount"] == 0, report

    # The row's own Vue state works in each row independently.
    toggles = page.locator(".row .toggle")
    toggles.nth(1).click()
    page.wait_for_function("document.querySelectorAll('.row .toggle')[1].getAttribute('aria-expanded') === 'true'")
    assert toggles.nth(0).get_attribute("aria-expanded") == "false"

    # The ordinary child sends its event and the server re-renders only it.
    counters = page.locator(".row .counter")
    assert counters.nth(1).text_content() == "two: 0"
    counters.nth(1).click()
    page.wait_for_function("document.querySelectorAll('.row .counter')[1].textContent === 'two: 1'")
    counters.nth(1).click()
    page.wait_for_function("document.querySelectorAll('.row .counter')[1].textContent === 'two: 2'")
    assert counters.nth(0).text_content() == "one: 0"
    # The counter's update left the row's browser state in place.
    assert toggles.nth(1).get_attribute("aria-expanded") == "true"
    assert faults == [], faults
    assert warnings == [], warnings
