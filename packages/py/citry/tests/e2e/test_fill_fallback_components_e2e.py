"""
A receiver's slot fallback that a caller shows through ``<c-fill fallback=...>``, holding a component.

The caller's template compiles the fallback, so the component calls in it
are recorded in the caller's data. The browser must agree: Vue hydrates the
server's HTML without a mismatch, the child stays interactive, an Events
render of the caller shows the child in the fill again, and an Events render
of the receiver alone, which drops the caller's fill, shows the child from
the receiver's own fallback (#351).
"""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")


def _page() -> type[Component]:
    engine = Citry(secret="fill-fallback-components-e2e-secret", autodiscover=False)  # noqa: S106 - test signing key
    engine.set_mounted_prefix("/citry")

    class Child(Component):
        citry = engine
        template = """
          <button
            id="child"
            @click="count += 1"
            v-text="'child ' + count"
          ></button>
        """

        def js_data(self, kwargs, slots):
            return {"count": 0}

    class Receiver(Component):
        citry = engine

        class State:
            renders: int = 0

        class Events:
            def bump(self, state: Receiver.State):
                state.renders += 1
                return Receiver(renders=state.renders)

        def template_data(self, kwargs, slots):
            return {"renders": int(kwargs.get("renders", 0))}

        template = """
          <article>
            <button id="bump" @c-click="bump">renders {{ renders }}</button>
            <c-slot name="body"><c-Child /></c-slot>
          </article>
        """

    class Caller(Component):
        citry = engine

        class State:
            renders: int = 0

        class Events:
            def refresh(self, state: Caller.State):
                state.renders += 1
                return Caller(renders=state.renders)

        def template_data(self, kwargs, slots):
            return {"renders": int(kwargs.get("renders", 0))}

        template = """
          <section>
            <button id="refresh" @c-click="refresh">caller {{ renders }}</button>
            <c-Receiver>
              <c-fill
                name="body"
                fallback="fallback"
              >
                <p id="framed">{{ fallback }}</p>
              </c-fill>
            </c-Receiver>
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
            <head></head>
            <body>
              <main><c-Caller /></main>
            </body>
          </html>
        """

    dispatcher_for(engine)
    return Page


@pytest.mark.e2e
def test_a_fallback_component_shown_by_a_fill_hydrates_and_follows_caller_and_receiver_renders(
    page: Any,
    serve_live: Any,
    send_event: Any,
) -> None:
    root = _page()
    # Vue reports a hydration mismatch through the console, so any warning
    # or error there means the server and browser renders disagreed.
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: faults.append(message.text) if message.type in {"error", "warning"} else None,
    )
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(serve_live(root.citry, root().render().serialize(), "") + "/")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report

    # The child sits in the caller's fill and is a live component.
    assert page.locator("#framed #child").text_content().strip() == "child 0"
    page.locator("#child").click()
    page.wait_for_function("document.querySelector('#child')?.textContent.trim() === 'child 1'")

    # A new render of the caller rebuilds the calls in its own data, so the
    # fill shows a new Child in the caller's frame.
    send_event(lambda: page.locator("#refresh").click(), handler="refresh")
    page.wait_for_function("document.querySelector('#refresh')?.textContent.trim() === 'caller 1'")
    assert page.locator("#framed #child").text_content().strip() == "child 0"
    page.locator("#child").click()
    page.wait_for_function("document.querySelector('#child')?.textContent.trim() === 'child 1'")

    # The event renders a new Receiver that has no fill from the caller, so
    # it shows its own fallback: a new Child, outside the caller's frame.
    send_event(lambda: page.locator("#bump").click(), handler="bump")
    page.wait_for_function("document.querySelector('#bump')?.textContent.trim() === 'renders 1'")
    assert page.locator("#child").count() == 1
    assert page.locator("#framed").count() == 0
    assert faults == []
