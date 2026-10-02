"""Prototype coverage for an Events Render that changes the target's component type (#164)."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")


class FinishIn:
    name: str


def _open(page: Any, serve_live: Any, engine: Citry, root: type[Component]) -> list[str]:
    # Every case must run without a browser error, so each collects them.
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: faults.append(message.text) if message.type == "error" else None)
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(serve_live(engine, root().render().serialize(), "") + "/")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    return faults


def _types(page: Any) -> list[str]:
    return page.evaluate(
        "[...[...__citryRuntime._apps.values()][0].occurrences.values()]"
        ".map(item => item.typeKey.split('_')[0]).sort()"
    )


@pytest.mark.e2e
def test_type_change_survives_parent_rerenders_and_swaps_back(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-type-change-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = engine
        template = '<i class="leaf">leaf</i>'

    class Done(Component):
        citry = engine

        class Kwargs:
            label: str

        class Events:
            def back(self):
                return actions.Render(Form())

        template = """
          <section id="done">
            <p id="done-label">{{ label }}</p>
            <button id="back" @c-click="back">back</button>
            <c-Leaf />
          </section>
        """

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                return actions.Render(Done(label="sent"))

        template = """
          <section id="form">
            <button id="local" @click="n++" v-text="'form ' + n"></button>
            <button id="submit" @c-click="submit">submit</button>
          </section>
        """
        js = "$component({data(){return {n: 0}}})"

    class PageState:
        count: int = 0

    class Page(Component):
        citry = engine
        State = PageState

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return actions.Render(Page())

        template = """
          <main>
            <button id="parent-local" @click="n++" v-text="'parent ' + n"></button>
            <button id="parent-refresh" @c-click="refresh">refresh</button>
            <div id="slot"><c-Form /></div>
          </main>
        """
        js = "$component({data(){return {n: 0}}})"

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)

    # Local state in the old component exists before the swap.
    page.locator("#local").click()
    page.wait_for_function("document.querySelector('#local').textContent === 'form 1'")

    page.locator("#submit").click()
    page.wait_for_selector("#done-label")
    assert page.locator("#form").count() == 0
    assert page.locator("#done .leaf").count() == 1
    assert _types(page) == ["Done", "Leaf", "Page"]

    # A browser-only re-render of the caller keeps the new type.
    page.locator("#parent-local").click()
    page.wait_for_function("document.querySelector('#parent-local').textContent === 'parent 1'")
    assert page.locator("#done-label").text_content() == "sent"
    assert page.locator("#form").count() == 0

    # The new component can change the type back; the old local state does not return.
    page.locator("#back").click()
    page.wait_for_selector("#form")
    assert page.locator("#local").text_content() == "form 0"
    assert _types(page) == ["Form", "Page"]
    page.locator("#submit").click()
    page.wait_for_selector("#done-label")

    # A server Render of the caller runs Python again, which writes Form.
    page.locator("#parent-refresh").click()
    page.wait_for_selector("#form")
    assert page.locator("#done").count() == 0
    assert page.locator("#parent-local").text_content() == "parent 1"
    page.locator("#submit").click()
    page.wait_for_selector("#done-label")
    assert faults == [], faults


@pytest.mark.e2e
def test_type_change_inside_a_fill_and_in_a_keyed_loop(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-type-change-fill-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Done(Component):
        citry = engine

        class Kwargs:
            name: str

        template = '<p class="done">done {{ name }}</p>'

    class Row(Component):
        citry = engine

        class Kwargs:
            name: str

        class Events:
            def finish(self, data: FinishIn):
                return actions.Render(Done(name=data.name))

        def js_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"name": kwargs.name}

        template = """
          <div class="row">
            <button class="finish" @c-click="finish({name: name})" v-text="name"></button>
            <c-slot name="default" />
          </div>
        """

    class Card(Component):
        citry = engine
        template = """
          <article class="card">
            <button id="card-local" @click="n++" v-text="'card ' + n"></button>
            <c-slot name="default" />
          </article>
        """
        js = "$component({data(){return {n: 0}}})"

    class Page(Component):
        citry = engine

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {"names": ["one", "two", "three"]}

        template = """
          <main>
            <c-Card>
              <c-Row c-name="'filled'"><b id="row-fill">fill</b></c-Row>
            </c-Card>
            <ul><c-Row c-for="name in names" #c-key="name" c-name="name" /></ul>
          </main>
        """

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)
    assert page.locator("#row-fill").count() == 1

    # The filled Row sits in Card's slot, so Card renders its VNode.
    page.locator(".finish", has_text="filled").click()
    page.wait_for_function("[...document.querySelectorAll('.done')].some(e => e.textContent === 'done filled')")
    assert page.locator("#row-fill").count() == 0
    page.locator("#card-local").click()
    page.wait_for_function("document.querySelector('#card-local').textContent === 'card 1'")
    assert page.locator(".card .done").text_content() == "done filled"

    # One keyed loop row changes type; its siblings keep their place.
    page.locator(".finish", has_text="two").click()
    page.wait_for_function("[...document.querySelectorAll('ul .done')].length === 1")
    assert page.locator("ul > *").evaluate_all("items => items.map(item => item.textContent.trim())") == [
        "one",
        "done two",
        "three",
    ]
    assert faults == [], faults


@pytest.mark.e2e
def test_type_change_stays_inside_its_own_vue_app(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-type-change-apps-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Done(Component):
        citry = engine
        template = '<p class="done">done</p>'

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                return actions.Render(Done())

        template = '<button class="submit" @c-click="submit">submit</button>'

    class Wrapper(Component):
        citry = engine
        template = '<section class="wrapper"><c-Form /></section>'

    class Page(Component):
        citry = engine
        template = "<html><head></head><body><c-Wrapper /></body></html>"

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, Page().render().serialize(), Wrapper().render().serialize(deps_strategy="fragment"))
    page.goto(base + "/")
    page.wait_for_function("() => __citryRuntime._apps.size === 1")
    page.evaluate(
        "() => fetch('/fragment').then((r) => r.text()).then((html) => {"
        " const target = document.createElement('div'); target.id = 'second';"
        " document.body.append(target); target.innerHTML = html; })"
    )
    page.wait_for_function("() => __citryRuntime._apps.size === 2")
    page.wait_for_selector("#second .submit")

    page.locator("#second .submit").click()
    page.wait_for_selector("#second .done")
    assert page.locator(".submit").count() == 1
    page.locator(".submit").click()
    page.wait_for_function("document.querySelectorAll('.done').length === 2")
    assert faults == [], faults


@pytest.mark.e2e
def test_type_change_through_a_passed_on_slot(page: Any, serve_live: Any) -> None:
    # Page fills Outer, and Outer passes that fill on to Inner, so Inner's
    # render creates the VNode of the component that changes type.
    engine = Citry(secret="vue-type-change-passed-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Done(Component):
        citry = engine
        template = '<p id="done">done</p>'

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                return actions.Render(Done())

        template = '<button id="submit" @c-click="submit">submit</button>'

    class Inner(Component):
        citry = engine
        template = """
          <div class="inner">
            <button id="inner-local" @click="n++" v-text="'inner ' + n"></button>
            <c-slot name="default" />
          </div>
        """
        js = "$component({data(){return {n: 0}}})"

    class Outer(Component):
        citry = engine
        template = """
          <section class="outer">
            <c-Inner><c-slot name="default" /></c-Inner>
          </section>
        """

    class Page(Component):
        citry = engine
        template = "<main><c-Outer><c-Form /></c-Outer></main>"

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)
    page.locator("#submit").click()
    page.wait_for_selector(".inner #done")
    page.locator("#inner-local").click()
    page.wait_for_function("document.querySelector('#inner-local').textContent === 'inner 1'")
    assert page.locator("#done").count() == 1
    assert page.locator("#submit").count() == 0
    assert faults == [], faults


@pytest.mark.e2e
def test_caller_bindings_for_the_old_type_do_not_reach_the_new_one(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-type-change-bindings-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Done(Component):
        citry = engine
        template = '<p id="done">done</p>'

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                return actions.Render(Done())

        template = '<button id="submit" @c-click="submit" v-text="title"></button>'
        js = "$component({props: ['title']})"

    class Page(Component):
        citry = engine
        template = "<main><c-Form :title=\"'hello'\" /></main>"

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)
    assert page.locator("#submit").text_content() == "hello"
    page.locator("#submit").click()
    page.wait_for_selector("#done")
    # Form's prop would otherwise become a `title` attribute on Done's root.
    assert page.locator("#done").get_attribute("title") is None
    assert faults == [], faults


@pytest.mark.e2e
def test_a_type_first_seen_as_a_replacement_can_later_be_called_by_tag(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-type-change-tag-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Done(Component):
        citry = engine
        template = '<p class="done">done</p>'

    class Wrapper(Component):
        citry = engine
        template = '<section id="wrapper"><c-Done /></section>'

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                return actions.Render(Done())

        template = '<button id="submit" @c-click="submit">submit</button>'

    class Shell(Component):
        citry = engine

        class Events:
            def wrap(self):
                return actions.Render(Shell(wrapped=True))

        class Kwargs:
            wrapped: bool = False

        template = """
          <div id="shell">
            <button id="wrap" @c-click="wrap">wrap</button>
            <c-Wrapper c-if="wrapped" />
            <c-Form c-else />
          </div>
        """

    class Page(Component):
        citry = engine
        template = "<main><c-Shell /></main>"

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)
    page.locator("#submit").click()
    page.wait_for_selector(".done")
    # Wrapper's template names Done by tag, which the replacement alone never registered.
    page.locator("#wrap").click()
    page.wait_for_selector("#wrapper .done")
    assert faults == [], faults
