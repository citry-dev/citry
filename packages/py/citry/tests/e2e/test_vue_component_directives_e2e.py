"""Vue `v-if`, `v-model`, and custom directives on Citry component tags, in a real browser."""

from __future__ import annotations

from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")


def _open(page: Any, serve_live: Any, engine: Citry, html: str, *, hydrated: bool) -> tuple[list[str], list[str]]:
    """Load ``html`` and wait until Citry has mounted or hydrated it."""
    faults: list[str] = []
    warnings: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: warnings.append(message.text) if message.type in {"warning", "error"} else None,
    )
    page.add_init_script(
        """
        globalThis.__citryHydrationDiagnostics = true;
        window.__citryReadyApps = [];
        document.addEventListener('citry:ready', event => window.__citryReadyApps.push(event.detail.appId));
        """
    )
    page.goto(serve_live(engine, html, "") + "/")
    page.wait_for_function("window.__citryReadyApps?.length === 1")
    if hydrated:
        page.wait_for_function("window.__citryHydrationReport !== undefined")
        probe = page.evaluate("window.__citryHydrationReport")
        assert probe["mountError"] is None, probe
        assert probe["mismatchCount"] == 0, probe
        assert probe["replacedElementCount"] == 0, probe
    return faults, warnings


def _declines(rendered: Any) -> list[tuple[str, str, str | None]]:
    admission = hydration_admission(rendered)
    assert admission is not None
    return [(item.code, item.outcome, item.shell_tag) for item in admission.declines]


@pytest.mark.e2e
@pytest.mark.parametrize("use_ssr", [False, True], ids=["mounted", "hydrated"])
def test_v_if_chain_across_calls_and_an_element(page: Any, serve_live: Any, use_ssr: bool) -> None:
    engine = Citry(secret="vue-if-call-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0
        branch: str = "first"

        def render(self):
            return Page(count=self.count, branch=self.branch)

    class First(Component):
        citry = engine
        template = """\
<section id="first">first {{ count }}</section>"""

        def template_data(self, kwargs, slots):
            return kwargs

    class Last(Component):
        citry = engine
        template = """\
<section id="last">last {{ count }}</section>"""
        js = """\
$component(() => { globalThis.__lastCallbacks = (globalThis.__lastCallbacks || 0) + 1; });"""

        def template_data(self, kwargs, slots):
            return kwargs

    class Page(Component):
        citry = engine
        State = PageState
        template = """\
<main>
  <button id="refresh" @c-click="refresh">refresh</button>
  <button id="choose-last" @c-click="choose_last">last</button>
  <c-first v-if="branch === 'first'" c-count="count" />
  <p id="middle" v-else-if="branch === 'middle'">middle</p>
  <c-last v-else c-count="count" />
</main>"""
        js = """\
$component({mounted(){globalThis.__setBranch=value=>{this.branch=value;};}});"""

        def template_data(self, kwargs, slots):
            return kwargs

        # A `js_data` value is known on the server, so a hydrated page is
        # written with the branch Vue will pick, and a server Render can
        # change it.
        def js_data(self, kwargs, slots):
            return {"branch": kwargs["branch"]}

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return state.render()

            def choose_last(self, state: PageState):
                state.count += 1
                state.branch = "last"
                return state.render()

    dispatcher_for(engine)
    rendered = Page(count=0, branch="first").render()
    html = rendered.serialize(ssr=use_ssr)
    assert ('"hydrate":true' in html) is use_ssr
    if use_ssr:
        assert _declines(rendered) == []
        assert '<section id="first">first 0</section>' in html
    faults, warnings = _open(page, serve_live, engine, html, hydrated=use_ssr)

    shown = "() => [...document.querySelectorAll('main > section, main > p')].map(item => item.textContent)"
    assert page.evaluate(shown) == ["first 0"]
    # The browser switches branches on its own.
    page.evaluate("window.__setBranch('middle')")
    page.wait_for_function(f"({shown})()[0] === 'middle'")
    page.evaluate("window.__setBranch('first')")
    page.wait_for_function(f"({shown})()[0] === 'first 0'")

    # A server Render that changes the condition mounts the other child
    # for the first time, with the newest server data.
    page.locator("#choose-last").click()
    page.wait_for_function(f"({shown})()[0] === 'last 1'")
    assert page.evaluate(shown) == ["last 1"]
    # Its server-render callback runs once for that mount, and again for
    # the next revision that updates it.
    page.wait_for_function("globalThis.__lastCallbacks === 1")
    # A server Render that keeps the condition updates the shown child.
    page.locator("#refresh").click()
    page.wait_for_function(f"({shown})()[0] === 'last 2'")
    page.wait_for_function("globalThis.__lastCallbacks === 2")
    # A branch the page has not shown since then mounts with the newest data.
    page.evaluate("window.__setBranch('first')")
    page.wait_for_function(f"({shown})()[0] === 'first 2'")
    assert page.evaluate(shown) == ["first 2"]
    assert faults == [], faults
    assert warnings == [], warnings


@pytest.mark.e2e
@pytest.mark.parametrize("use_ssr", [False, True], ids=["mounted", "hydrated"])
def test_v_model_on_a_call_with_argument_and_modifiers(page: Any, serve_live: Any, use_ssr: bool) -> None:
    engine = Citry(secret="vue-model-call-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Field(Component):
        citry = engine
        template = """\
<label>
  {{ count }}
  <input
    class="plain"
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
  />
  <input
    class="title"
    :value="title"
    @input="titleModifiers.lazy || $emit('update:title', $event.target.value)"
    @change="titleModifiers.lazy && $emit('update:title', $event.target.value)"
  />
</label>"""
        js = """\
$component({
  props: {
    modelValue: {default: ""},
    modelModifiers: {default: () => ({})},
    title: {default: ""},
    titleModifiers: {default: () => ({})},
  },
  emits: ["update:modelValue", "update:title"],
});"""

        def template_data(self, kwargs, slots):
            return kwargs

    class Page(Component):
        citry = engine
        State = PageState
        template = """\
<main>
  <button id="refresh" @c-click="refresh">refresh</button>
  <c-field v-model.trim="query" v-model:title.number.lazy="amount" c-count="count" />
  <output id="state" v-text="JSON.stringify([query, amount, typeof amount])"></output>
</main>"""
        js = """\
$component({
  data(){return {query: "start", amount: 1};},
  mounted(){globalThis.__setQuery=value=>{this.query=value;};},
});"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return state.render()

    dispatcher_for(engine)
    rendered = Page(count=0).render()
    html = rendered.serialize(ssr=use_ssr)
    if use_ssr:
        # The model is a prop and a listener on the call, which the server
        # leaves to the browser like any other call prop.
        assert _declines(rendered) == [("component-attrs", "shell", "main")]
    faults, warnings = _open(page, serve_live, engine, html, hydrated=use_ssr)

    state = "() => document.querySelector('#state').textContent"
    plain = page.locator("input.plain")
    title = page.locator("input.title")
    assert plain.input_value() == "start"
    assert page.evaluate(state) == '["start",1,"number"]'

    # `.trim` on a component: Vue trims what the child emits.
    plain.fill("  hello  ")
    page.wait_for_function(f'({state})() === \'["hello",1,"number"]\'')
    # `.number` converts the emitted text, and `.lazy` is left to the child,
    # which emits only on `change`.
    title.fill("42")
    assert page.evaluate(state) == '["hello",1,"number"]'
    title.dispatch_event("change")
    page.wait_for_function(f'({state})() === \'["hello",42,"number"]\'')

    # The parent's value flows back into the child.
    page.evaluate("window.__setQuery('from parent')")
    page.wait_for_function("document.querySelector('input.plain').value === 'from parent'")

    # A server Render refreshes the child's Python data and keeps both
    # browser values.
    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('label').textContent.trim().startsWith('1')")
    assert page.evaluate(state) == '["from parent",42,"number"]'
    assert plain.input_value() == "from parent"
    assert faults == [], faults
    assert warnings == [], warnings


@pytest.mark.e2e
@pytest.mark.parametrize("use_ssr", [False, True], ids=["mounted", "hydrated"])
def test_custom_directive_on_a_call_reaches_the_child_root(page: Any, serve_live: Any, use_ssr: bool) -> None:
    engine = Citry(secret="vue-directive-call-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        count: int = 0

        def render(self):
            return Page(count=self.count)

    class Child(Component):
        citry = engine
        template = """\
<section>child {{ count }}</section>"""

        def template_data(self, kwargs, slots):
            return kwargs

    class Page(Component):
        citry = engine
        State = PageState
        template = """\
<main>
  <button id="refresh" @c-click="refresh">refresh</button>
  <c-child v-mark:top.big="label" v-focusable c-count="count" />
</main>"""
        js = """\
const describe = (el, binding) => {
  el.dataset.mark = [binding.value, binding.arg, Object.keys(binding.modifiers).join(",")].join("|");
};
$component({
  data(){return {label: "one"};},
  directives: {
    mark: {mounted: describe, updated: describe},
    focusable: {mounted(el){ el.tabIndex = 0; }},
  },
  mounted(){globalThis.__setLabel=value=>{this.label=value;};},
});"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def refresh(self, state: PageState):
                state.count += 1
                return state.render()

    dispatcher_for(engine)
    rendered = Page(count=0).render()
    html = rendered.serialize(ssr=use_ssr)
    if use_ssr:
        assert _declines(rendered) == [("unsupported-directive", "shell", "main")]
    faults, warnings = _open(page, serve_live, engine, html, hydrated=use_ssr)

    root = """() => {
      const section = document.querySelector('main section');
      return {text: section?.textContent, mark: section?.dataset.mark, tab: section?.tabIndex};
    }"""
    assert page.evaluate(root) == {"text": "child 0", "mark": "one|top|big", "tab": 0}
    page.evaluate("window.__setLabel('two')")
    page.wait_for_function("document.querySelector('main section')?.dataset.mark === 'two|top|big'")

    page.locator("#refresh").click()
    page.wait_for_function("document.querySelector('main section')?.textContent === 'child 1'")
    assert page.evaluate(root) == {"text": "child 1", "mark": "two|top|big", "tab": 0}
    assert faults == [], faults
    assert warnings == [], warnings


@pytest.mark.e2e
def test_server_render_switches_calls_and_elements_with_directives(page: Any, serve_live: Any) -> None:
    # Python picks a different authored call or element on each render. A
    # call's directives follow its own Vue key, and an element's custom
    # directive is part of its declared replacement site, so neither switch
    # is reported as an undeclared directive change.
    engine = Citry(secret="vue-directive-switch-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    class PageState:
        decorated: bool = True

        def render(self):
            return Page(decorated=self.decorated)

    class Child(Component):
        citry = engine
        template = """\
<section>child</section>"""
        js = """\
$component({props: {modelValue: {default: ""}}});"""

    class Page(Component):
        citry = engine
        State = PageState
        template = """\
<main>
  <button id="flip" @c-click="flip">flip</button>
  <c-if cond="decorated">
    <c-child v-if="visible" v-model="text" v-mark="'call'" />
    <p v-mark="'element'">element</p>
  </c-if>
  <c-else>
    <c-child />
    <p>element</p>
  </c-else>
</main>"""
        js = """\
$component({
  data(){return {visible: true, text: "x"};},
  directives: {mark: {mounted(el, binding){ el.dataset.mark = binding.value; }}},
});"""

        def template_data(self, kwargs, slots):
            return kwargs

        class Events:
            def flip(self, state: PageState):
                state.decorated = not state.decorated
                return state.render()

    dispatcher_for(engine)
    faults, warnings = _open(
        page, serve_live, engine, Page(decorated=True).render().serialize(ssr=False), hydrated=False
    )
    marks = "() => [...document.querySelectorAll('main section, main p')].map(item => item.dataset.mark ?? null)"
    assert page.evaluate(marks) == ["call", "element"]
    page.locator("#flip").click()
    page.wait_for_function(f"JSON.stringify(({marks})()) === '[null,null]'")
    page.locator("#flip").click()
    page.wait_for_function(f'JSON.stringify(({marks})()) === \'["call","element"]\'')
    assert faults == [], faults
    assert warnings == [], warnings
