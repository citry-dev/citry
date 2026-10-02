"""An Events Render that replaces the calling component with a different component (#164)."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry.ext.cache.extension import CacheExtension
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
def test_component_change_survives_parent_rerenders_and_swaps_back(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-component-change-secret", autodiscover=False)  # noqa: S106
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

    # A browser-only re-render of the caller keeps the new component.
    page.locator("#parent-local").click()
    page.wait_for_function("document.querySelector('#parent-local').textContent === 'parent 1'")
    assert page.locator("#done-label").text_content() == "sent"
    assert page.locator("#form").count() == 0

    # The new component can bring the old one back; its local state does not return.
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
def test_component_change_inside_a_fill_and_in_a_keyed_loop(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-component-change-fill-secret", autodiscover=False)  # noqa: S106
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

    # One keyed loop row becomes another component; its siblings keep their place.
    page.locator(".finish", has_text="two").click()
    page.wait_for_function("[...document.querySelectorAll('ul .done')].length === 1")
    assert page.locator("ul > *").evaluate_all("items => items.map(item => item.textContent.trim())") == [
        "one",
        "done two",
        "three",
    ]
    assert faults == [], faults


@pytest.mark.e2e
def test_component_change_stays_inside_its_own_vue_app(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-component-change-apps-secret", autodiscover=False)  # noqa: S106
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
def test_component_change_through_a_passed_on_slot(page: Any, serve_live: Any) -> None:
    # Page fills Outer, and Outer passes that fill on to Inner, so Inner's
    # render creates the VNode of the component that is replaced.
    engine = Citry(secret="vue-component-change-passed-secret", autodiscover=False)  # noqa: S106
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
    engine = Citry(secret="vue-component-change-bindings-secret", autodiscover=False)  # noqa: S106
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
    engine = Citry(secret="vue-component-change-tag-secret", autodiscover=False)  # noqa: S106
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


@pytest.mark.e2e
def test_directives_on_the_call_reach_the_new_component_and_a_ref_empties(page: Any, serve_live: Any) -> None:
    # `v-show` and a custom directive belong to the caller's place on the
    # page, so they keep working on whatever component fills it. A template
    # ref points at the old component's API, so it empties instead.
    engine = Citry(secret="vue-component-change-directives-secret", autodiscover=False)  # noqa: S106
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

    class Page(Component):
        citry = engine
        template = """
          <main>
            <button id="toggle" @click="shown = !shown">toggle</button>
            <c-Form v-show="shown" v-mark ref="form" />
          </main>
        """
        js = """
          $component({
            data() { return {shown: true}; },
            directives: {mark: {mounted(el) { el.dataset.mark = "yes"; }}},
            mounted() { globalThis.__formRef = () => this.$refs.form ?? null; },
          });
        """

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)
    assert page.evaluate("__formRef() !== null")
    assert page.locator("#submit").get_attribute("data-mark") == "yes"

    page.locator("#submit").click()
    page.wait_for_selector("#done")
    assert page.locator("#done").get_attribute("data-mark") == "yes"
    assert page.evaluate("__formRef()") is None
    page.locator("#toggle").click()
    page.wait_for_function("getComputedStyle(document.querySelector('#done')).display === 'none'")
    assert faults == [], faults


@pytest.mark.e2e
def test_render_passes_slots_to_the_new_component_and_a_later_dispatch_still_arrives(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="vue-component-change-slots-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Inside(Component):
        citry = engine

        class Events:
            def poke(self):
                return actions.Data({"poked": True})

        template = '<button id="inside" @c-click="poke">inside</button>'

    class Panel(Component):
        citry = engine

        class Kwargs:
            title: str

        template = """
          <section id="panel">
            <h2>{{ title }}</h2>
            <c-slot name="default" />
          </section>
        """

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                # The Dispatch comes after a Render that replaced its sender,
                # so it must start from the component now at the sender's place.
                return [
                    actions.Render(Panel(title="sent", slots={"default": Inside()})),
                    actions.Dispatch("Form:sent", {"ok": True}),
                ]

        template = '<button id="submit" @c-click="submit">submit</button>'

    class Page(Component):
        citry = engine
        template = "<main><c-Form /></main>"

    dispatcher_for(engine)
    page.add_init_script(
        "window.__sent = []; document.addEventListener('Form:sent', event => window.__sent.push(event.detail));"
    )
    faults = _open(page, serve_live, engine, Page)
    page.locator("#submit").click()
    page.wait_for_selector("#panel #inside")
    assert page.locator("#panel h2").text_content() == "sent"
    page.wait_for_function("window.__sent.length === 1")
    assert page.evaluate("window.__sent") == [{"ok": True}]

    # The component that arrived in the Render's slot runs its own handlers.
    with page.expect_response(lambda response: response.url.endswith("/ext/events/call")) as call:
        page.locator("#inside").click()
    assert call.value.status == 200
    assert faults == [], faults


@pytest.mark.e2e
def test_one_response_replaces_the_caller_and_renders_another_target(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-component-change-targets-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    counter_render_id = ""

    class Done(Component):
        citry = engine
        template = '<p id="done">done</p>'

    class Counter(Component):
        citry = engine

        class Kwargs:
            n: int = 0

        template = '<output id="count">{{ n }}</output>'

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            nonlocal counter_render_id
            if kwargs.n == 0:
                counter_render_id = self.id
            return {"n": kwargs.n}

    class Form(Component):
        citry = engine

        class Events:
            def submit(self):
                return [
                    actions.Render(Done()),
                    actions.Render(Counter(n=1), target=f"render:{counter_render_id}"),
                ]

        template = '<button id="submit" @c-click="submit">submit</button>'

    class Page(Component):
        citry = engine
        template = "<main><c-Form /><c-Counter /></main>"

    dispatcher_for(engine)
    faults = _open(page, serve_live, engine, Page)
    page.locator("#submit").click()
    page.wait_for_selector("#done")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    assert page.locator("#submit").count() == 0
    assert faults == [], faults


@pytest.mark.e2e
def test_component_change_in_output_replayed_from_the_cache(page: Any, serve_live: Any, monkeypatch: Any) -> None:
    # Both calls replay one cached render, so they share their prepared
    # output. Replacing one must leave the other working on its own.
    engine = Citry(secret="vue-component-change-cache-secret")  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class Done(Component):
        citry = engine
        template = '<p class="done">done</p>'

    class Cached(Component):
        citry = engine

        class Events:
            def submit(self):
                return actions.Render(Done())

        template = '<button class="cached" @c-click="submit">submit</button>'

    extension = engine.extensions.get_extension("cache")
    assert isinstance(extension, CacheExtension)

    def lookup(component: Any, _context: Any) -> Any:
        if type(component) is Cached:
            return extension._lookup_physical_key("component-change:cached", ttl=None, max_entry_bytes=None)
        return None

    monkeypatch.setattr(extension, "_lookup_component", lookup)
    dispatcher_for(engine)

    class Page(Component):
        citry = engine
        template = """
          <!doctype html>
          <html>
            <head><title>cache replay</title></head>
            <body><c-cached /><c-cached /></body>
          </html>
        """

    faults = _open(page, serve_live, engine, Page)
    page.locator(".cached").nth(0).click()
    page.wait_for_selector(".done")
    assert page.locator(".cached").count() == 1
    page.locator(".cached").click()
    page.wait_for_function("document.querySelectorAll('.done').length === 2")
    assert faults == [], faults
