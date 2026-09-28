"""Browser proof that a fill reads its author's Vue data wherever it is rendered."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, Slot
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytestmark = pytest.mark.e2e


class PingIn:
    value: str


def _declaration_components(engine: Citry) -> None:
    """
    Register the pattern citry_ui groups use, without citry_ui.

    ``Declare`` stores the fill it receives instead of rendering it, and the
    transparent ``Receiver`` renders the stored fill later, inside
    ``Physical``, a component with its own Vue definition. The fill's author
    calls ``Declare`` and ``Physical`` but never ``Receiver`` directly.
    """
    declarations: list[Slot] = []

    class Declare(Component):
        citry = engine
        name = "declare"
        template = """
          <c-slot />
        """

        def template_data(self, kwargs, slots):
            declarations.append(slots["default"])
            return {}

        def on_render(self):
            return ""

    class Receiver(Component):
        citry = engine
        name = "receiver"
        transparent = True
        template = """
          <div class="receiver">{{ content }}</div>
        """

        def template_data(self, kwargs, slots):
            declaration = declarations[-1]
            return {"content": Slot(lambda _: declaration())}

    class Physical(Component):
        citry = engine
        name = "physical"
        template = """
          <section class="physical"><c-receiver /></section>
        """

        def js_data(self, kwargs, slots):
            return {"label": "Physical", "count": 100, "text": "physical"}


def test_fill_bindings_read_and_write_the_authors_data(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="fill-author-scope-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    received: list[str] = []
    _declaration_components(engine)

    class Author(Component):
        citry = engine
        name = "author"
        # Physical defines the same names with other values, so reading
        # them from the wrong component shows up as a wrong value, not as
        # an empty one.
        template = """
          <main>
            <c-declare>
              <span id="text" v-text="label"></span>
              <button id="inc" @click="count++">inc</button>
              <input id="model" v-model="text" />
              <button id="event" @c-click="ping({value: label})">event</button>
              <button id="event-static" @c-click="ping({value: 'static'})">static</button>
            </c-declare>
            <c-physical />
            <p id="author-count" v-text="count"></p>
            <p id="author-text" v-text="text"></p>
          </main>
        """

        class Events:
            def ping(self, data: PingIn):
                received.append(data.value)

        def js_data(self, kwargs, slots):
            return {"label": "Lexical", "count": 0, "text": ""}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_live(engine, Author().render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#text')?.textContent === 'Lexical'")

    page.locator("#inc").click()
    page.locator("#model").fill("typed")
    page.wait_for_function("document.querySelector('#author-count').textContent === '1'")
    page.wait_for_function("document.querySelector('#author-text').textContent === 'typed'")

    # Both Events bindings reach the author's handler, including the one
    # whose argument reads the author's data.
    page.locator("#event").click()
    page.locator("#event-static").click()
    page.wait_for_function("() => document.querySelectorAll('.physical .receiver #text').length === 1")
    page.wait_for_timeout(300)
    assert received == ["Lexical", "static"]
    assert faults == []


def test_events_update_of_a_component_between_author_and_receiver_keeps_the_page_working(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="fill-author-scope-update-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    _declaration_components(engine)
    panel_render_id = ""

    class Panel(Component):
        citry = engine
        name = "panel"
        # Panel sits between the page, which writes the fill, and the
        # receiver inside Physical. It passes the page's fill on as a slot.
        template = """
          <article class="panel" c-data-title="title">
            <c-declare><c-slot /></c-declare>
            <c-physical />
          </article>
        """

        def template_data(self, kwargs, slots):
            nonlocal panel_render_id
            panel_render_id = self.id
            return {"title": kwargs["title"]}

    class Replacement(Component):
        citry = engine
        name = "replacement"
        template = """
          <b id="replacement" v-text="note"></b>
        """

        def js_data(self, kwargs, slots):
            return {"note": "from the update"}

    class Author(Component):
        citry = engine
        name = "author"
        template = """
          <main>
            <c-panel title="first">
              <span id="text" v-text="label"></span>
              <button id="inc" @click="count++">inc</button>
            </c-panel>
            <p id="author-count" v-text="count"></p>
            <button id="refresh" @c-click="refresh">refresh</button>
          </main>
        """

        class Events:
            def refresh(self):
                # The update renders Panel on its own, under the id the
                # browser already holds. Its new fill comes from this
                # handler, not from the page's template.
                return actions.Render(
                    Panel(title="second", slots={"default": Replacement()}),
                    target=f"render:{panel_render_id}",
                )

        def js_data(self, kwargs, slots):
            return {"label": "Lexical", "count": 0}

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    page.goto(serve_live(engine, Author().render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#text')?.textContent === 'Lexical'")
    page.locator("#inc").click()
    page.wait_for_function("document.querySelector('#author-count').textContent === '1'")

    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('.panel')?.dataset.title === 'second'")
    page.wait_for_function("document.querySelector('#replacement')?.textContent === 'from the update'")
    # The update's own fill replaced the page's fill, and the page's slot
    # content did not come back alongside it.
    assert page.locator(".panel #text").count() == 0
    assert page.locator(".physical .receiver #replacement").count() == 1
    # The page itself was not re-rendered and keeps its state.
    assert page.locator("#author-count").text_content() == "1"
    assert faults == []
