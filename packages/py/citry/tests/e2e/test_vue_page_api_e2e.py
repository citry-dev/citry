"""
Browser tests for the page-wide Vue APIs: `Citry.vue.use()` and the options of an Events call.

`Citry.vue.use()` installs a Vue plugin on every Vue app Citry creates, so a
page can add a store, a global property, or a global directive. The call must
run before Citry starts its first app. The other tests check that
`$sendEvent` and `Citry.events.send` accept only the options Citry
implements and name the problem in the rejection.
"""

from __future__ import annotations

import base64
from typing import Any

import pytest

from citry import Citry, Component, Extension
from citry.ext.dependencies import Script
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for

pytest.importorskip("playwright.sync_api")

_START_SCRIPT = '<script type="module">'


def _collect_page_errors(page: Any) -> list[str]:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return errors


def _with_head_defer_script(html: str, script: str) -> str:
    # The documented recipe: a `defer` script placed before Citry's scripts runs
    # after the runtime has loaded and before the module script that starts the
    # app. A data URL stands in for the page's own script file.
    source = base64.b64encode(script.encode()).decode()
    return f'<script defer src="data:text/javascript;base64,{source}"></script>{html}'


@pytest.mark.e2e
def test_a_page_plugin_reaches_every_component_of_the_app(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Badge(Component):
        citry = engine
        template = """
            <b
                class="badge"
                v-mark="'child'"
                v-text="$greeting"
            ></b>
        """
        js = """
            $component({});
        """

    engine.register(Badge)

    class Greeting(Component):
        citry = engine
        # `$greeting` and `v-mark` exist only because the page plugin adds them.
        template = """
            <section id="greeting">
                <p
                    id="greet"
                    v-mark="'parent'"
                    v-text="$greeting"
                ></p>
                <c-badge />
            </section>
        """
        js = """
            $component({});
        """

    plugin_script = """
        window.__useErrors = [];
        window.__installs = 0;
        const plugin = {
          install(app, options) {
            window.__installs += 1;
            app.config.globalProperties.$greeting = options.text;
            app.directive('mark', {mounted(el, binding) { el.dataset.mark = binding.value; }});
          },
        };
        Citry.vue.use(plugin, {text: 'hello'});
        // A second registration of the same plugin does nothing, as with app.use.
        Citry.vue.use(plugin, {text: 'ignored'});
        for (const value of [42, null, {install: 'no'}]) {
          try { Citry.vue.use(value); } catch (error) { __useErrors.push(`${error.name}: ${error.message}`); }
        }
        document.addEventListener('citry:ready', () => {
          try { Citry.vue.use({install() {}}); } catch (error) { __useErrors.push(`${error.name}: ${error.message}`); }
          window.__afterReady = true;
        });
    """
    errors = _collect_page_errors(page)
    page.goto(serve_document(_with_head_defer_script(Greeting().render().serialize(), plugin_script)))
    page.wait_for_function("window.__afterReady === true")

    assert page.locator("#greet").text_content() == "hello"
    assert page.locator("#greet").get_attribute("data-mark") == "parent"
    assert page.locator(".badge").text_content() == "hello"
    assert page.locator(".badge").get_attribute("data-mark") == "child"
    assert page.evaluate("window.__installs") == 1
    use_errors = page.evaluate("window.__useErrors")
    assert len(use_errors) == 4
    for message in use_errors[:3]:
        assert message.startswith("TypeError: Citry.vue.use() needs a Vue plugin")
    # Too late: the app already started without the plugin, and the message says where to call it.
    assert use_errors[3].startswith("Error: Citry.vue.use() was called after Citry created a Vue app")
    assert "`defer`" in use_errors[3]
    # `use` is Citry's addition, so it stays out of an enumeration of the Vue runtime.
    assert page.evaluate("Object.keys(Citry.vue).includes('use')") is False
    assert errors == []


def _events_page(engine: Citry) -> type[Component]:
    class Counter(Component):
        citry = engine
        template = """
            <output id="counter">ready</output>
        """
        js = """
            $component({
              mounted() {
                window.__counter = this;
              },
            });
        """

        class Events:
            def ping(self):
                return actions.Data("pong")

    return Counter


@pytest.mark.e2e
def test_send_options_reject_wait_false_and_unknown_keys(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="vue-send-options-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    counter = _events_page(engine)
    dispatcher_for(engine)
    errors = _collect_page_errors(page)
    requests: list[str] = []

    def record_call(request: Any) -> None:
        if request.url.endswith("/ext/events/call"):
            requests.append(request.url)

    page.on("request", record_call)
    # `Citry.events.send` finds its target only once the app is ready, so every
    # attempt starts from `citry:ready`.
    page.add_init_script(
        """
        document.addEventListener('citry:ready', () => {
          const counter = window.__counter;
          const attempts = [
            () => counter.$sendEvent('ping', {}, {wait: false}),
            () => counter.$sendEvent('ping', {}, {timout: 100}),
            () => Citry.events.send(counter.$el, 'ping', {}, {wait: false}),
            () => counter.$sendEvent('ping', {}, {wait: true, timeout: 5000}),
          ];
          Promise.allSettled(attempts.map(attempt => attempt())).then(results => {
            window.__sendResults = results.map(result =>
              result.status === 'fulfilled' ? result.value : String(result.reason));
          });
        });
        """
    )
    page.goto(serve_live(engine, counter().render().serialize(), "") + "/")
    page.wait_for_function("window.__sendResults !== undefined")

    wait_false, unknown, public_wait_false, accepted = page.evaluate("window.__sendResults")
    assert wait_false.startswith("TypeError: Citry Events option 'wait' accepts only true.")
    assert "one at a time" in wait_false
    assert "@event(latest_wins=True)" in wait_false
    assert unknown == (
        "TypeError: Citry Events send got an unknown option 'timout'; the options are 'timeout' and 'wait'."
    )
    assert public_wait_false == wait_false
    assert accepted == "pong"
    # Only the accepted call reached the server.
    assert len(requests) == 1
    assert errors == []


@pytest.mark.e2e
def test_scripts_the_app_loads_before_it_starts_may_register_plugins(page: Any, serve_live: Any) -> None:
    # A script an extension adds to early_scripts and a component's own JavaScript run
    # while Citry prepares the app, before it creates the Vue app, so a plugin
    # they register still reaches that app.
    class PagePlugins(Extension):
        name = "page_plugins"

        def on_dependencies(self, ctx):
            ctx.early_scripts.append(
                Script(
                    content=(
                        "Citry.vue.use({install(app) { app.config.globalProperties.$fromExtension = 'extension'; }});"
                    ),
                    wrap=False,
                )
            )

    engine = Citry(extensions=[PagePlugins], autodiscover=False)

    class Plugged(Component):
        citry = engine
        template = """
            <p
                id="plugged"
                v-text="$fromExtension + ' ' + $fromComponent"
            ></p>
        """
        js = """
            Citry.vue.use({install(app) { app.config.globalProperties.$fromComponent = 'component'; }});
            $component({});
        """

    errors = _collect_page_errors(page)
    page.goto(serve_live(engine, Plugged().render().serialize(), "") + "/")
    page.wait_for_function("document.querySelector('#plugged')?.textContent === 'extension component'")
    assert errors == []
