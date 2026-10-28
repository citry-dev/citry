"""Prepared Vue support for selected transparent roots and Python Slot calls."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.slots import Slot

pytestmark = pytest.mark.e2e


def _logged_error_text(message: Any) -> str:
    """Return the text of the error a page logged with `console.error`."""
    # Chromium's `message.text` includes a logged Error's message, but Firefox
    # prints `JSHandle@object`. The last argument is the Error itself, so ask
    # the browser for its message. This must run outside the console event
    # handler, where Playwright cannot wait for a browser round trip.
    if not message.args:
        return message.text
    return message.args[-1].evaluate("error => String(error?.message ?? error)")


def test_python_slot_keeps_nested_authored_fill_in_its_lexical_vue_scope(
    page, serve_document, open_citry_page
) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)

    class Receiver(Component):
        citry = app
        template = "<article><c-slot /></article>"

        def js_data(self, kwargs, slots):
            return {"label": "receiver"}

    class Content(Component):
        citry = app
        template = (
            "<c-Receiver #c-key=\"'receiver'\">"
            '<button class="lexical" v-text="label" @click="label += \'!\'"></button>'
            "</c-Receiver>"
        )

        def js_data(self, kwargs, slots):
            return {"label": "caller"}

    class Host(Component):
        citry = app
        template = "<main><c-slot /></main><aside><c-slot /></aside>"

    # The buttons are server HTML; clicking before the app mounts reaches no handler.
    open_citry_page(serve_document(Host(slots={"default": Content()}).render().serialize()))
    buttons = page.locator("button.lexical")
    assert buttons.all_text_contents() == ["caller", "caller"]
    buttons.first.click()
    assert buttons.all_text_contents() == ["caller!", "caller"]
    assert errors == []


def test_transparent_root_mounts_python_composed_multiroot_component(page, serve_document, open_citry_page) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)

    class Shell(Component):
        citry = app
        template = "<section><c-slot /></section>"

    class Widget(Component):
        citry = app
        template = '<button class="value" v-text="label"></button><span class="tail">tail</span>'
        js = "$component(({ component }) => { globalThis.__multiMounts = (globalThis.__multiMounts || 0) + 1; });"

        def js_data(self, kwargs, slots):
            return {"label": "ready"}

    rendered = app.render_template(
        '<c-shell><c-fill name="default"><c-slot name="content" /></c-fill></c-shell>',
        slots={"content": Slot(lambda ctx: Widget().render(provides=ctx.provides))},
    )
    # The button is server HTML, but the mount counter is set by the component's
    # JS, so wait for the app rather than for the button.
    open_citry_page(serve_document(rendered.serialize()))

    assert page.locator("button.value").text_content() == "ready"
    assert page.locator("span.tail").text_content() == "tail"
    assert page.evaluate("() => globalThis.__multiMounts") == 1
    assert errors == []


def test_transparent_root_mounts_empty_python_composed_component(page, serve_document, open_citry_page) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)

    class VoidWidget(Component):
        citry = app
        template = ""
        js = "$component(({ component }) => { globalThis.__emptyMounts = (globalThis.__emptyMounts || 0) + 1; });"

    rendered = app.render_template(
        '<c-slot name="content" />',
        slots={"content": Slot(lambda ctx: VoidWidget().render(provides=ctx.provides))},
    )
    # The host element is server HTML; the mount counter needs the mounted app.
    open_citry_page(serve_document(rendered.serialize()))

    assert page.locator("body").inner_text() == ""
    assert page.evaluate("() => globalThis.__emptyMounts") == 1
    assert errors == []


def test_prepared_component_without_events_unmounts_cleanly(page, serve_document, open_citry_page) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)

    class Widget(Component):
        citry = app
        template = '<button class="no-events" v-text="label"></button>'

        def js_data(self, kwargs, slots):
            return {"label": "Ready"}

    rendered = app.render_template('<main id="owner"><c-widget /></main>')
    # The registry holds the app before it mounts, when `vueApp` is still unset,
    # so wait for the mount before unmounting it.
    open_citry_page(serve_document(rendered.serialize()))
    page.wait_for_selector("button.no-events")
    page.evaluate("""() => {
      const [appId, record] = [...__citryRuntime._apps.entries()][0];
      globalThis.__noEventsAppId = appId;
      record.vueApp.unmount();
    }""")
    page.wait_for_function("() => __citryRuntime._apps.size === 0")
    assert errors == []


def test_fragment_manager_loads_and_mounts_python_composed_component(
    page, serve_live, wait_for_citry_ready, wait_for_count
) -> None:
    errors: list[str] = []
    # Keep the message objects too: when the product logs an Error object,
    # only the message's arguments give the same error text in every browser.
    console_messages: list[Any] = []

    def collect_console_error(message: Any) -> None:
        if message.type == "error":
            errors.append(message.text)
            console_messages.append(message)

    page.on("console", collect_console_error)
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = app
        template = '<button class="fragment-value" v-text="label"></button>'
        css = ".fragment-value { color: rgb(1, 2, 3); }"
        js = (
            "$component(({ component }) => { globalThis.__fragmentMounts = (globalThis.__fragmentMounts || 0) + 1; });"
        )

        def js_data(self, kwargs, slots):
            return {"label": "fragment ready"}

    rendered = app.render_template(
        '<main><c-slot name="content" /></main>',
        slots={"content": Slot(lambda ctx: Widget().render(provides=ctx.provides))},
    )
    fragment = rendered.serialize(deps_strategy="fragment", csp_nonce="response-token")
    document = """
        <html><head><script nonce="base-token" src="/citry/citry.js"></script></head><body>
        <div id="target"></div><script nonce="base-token">
        fetch('/fragment').then(response => response.text()).then(html => {
          document.getElementById('target').innerHTML = html;
        });
        </script></body></html>
    """
    url = serve_live(app, document, fragment)
    page.route(
        url,
        lambda route: route.fulfill(
            body=document,
            content_type="text/html",
            headers={
                "Content-Security-Policy": (
                    "default-src 'self'; script-src 'nonce-base-token'; "
                    "style-src 'nonce-base-token'; connect-src 'self'"
                )
            },
        ),
    )
    page.goto(url)

    # The page fetches the fragment after load and the manager mounts it after
    # that, so a fixed sleep can check before the mount on a slow runner. The
    # app's `citry:ready` comes once it has mounted with its stylesheet.
    wait_for_citry_ready()
    assert errors == [], page.content()
    assert page.locator('[id^="citry-vue-"]').count() == 1, page.content()
    assert page.locator("script[data-citry-vue-fragment]").count() == 1, page.content()
    assert page.evaluate("() => ({stable: !!window.__citryRuntime, manager: !!window.Citry?.fragments})") == {
        "stable": True,
        "manager": True,
    }
    page.wait_for_selector("button.fragment-value", timeout=5_000)
    assert page.locator("button.fragment-value").text_content() == "fragment ready"
    assert page.locator("button.fragment-value").evaluate("node => getComputedStyle(node).color") == "rgb(1, 2, 3)"
    assert page.evaluate("() => globalThis.__fragmentMounts") == 1
    assert page.locator("link[data-citry-vue-style-app]").evaluate("node => node.nonce") == "base-token"
    assert page.evaluate("""async () => {
      const tag = document.querySelector('script[data-citry-vue-fragment]');
      const first = Citry.fragments.load(JSON.parse(tag.textContent), tag);
      const second = Citry.fragments.load(JSON.parse(tag.textContent), tag);
      await first;
      return {same: first === second, mounts: globalThis.__fragmentMounts};
    }""") == {"same": True, "mounts": 1}
    assert (
        page.evaluate("""async () => {
      const tag = document.querySelector('script[data-citry-vue-fragment]');
      const manifest = JSON.parse(tag.textContent);
      manifest.calls = [];
      try { await Citry.fragments.load(manifest); }
      catch (error) { return String(error).includes('legacy dependency state'); }
      return false;
    }""")
        is True
    )
    assert page.evaluate("""async () => {
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const manifest = structuredClone(source);
      const host = document.createElement('div');
      host.id = 'duplicate-app-host';
      document.body.append(host);
      manifest.vue.host = '#duplicate-app-host';
      manifest.vue.prepared.host = '#duplicate-app-host';
      try { await Citry.fragments.load(manifest); }
      catch (error) {
        return {
          rejected: String(error),
          alive: __citryRuntime._apps.has(source.vue.appId),
          mounts: globalThis.__fragmentMounts,
          text: document.querySelector('button.fragment-value')?.textContent,
        };
      }
      return {rejected: false};
    }""") == {
        "rejected": "Error: duplicate Citry Vue app",
        "alive": True,
        "mounts": 1,
        "text": "fragment ready",
    }
    assert page.evaluate("""async () => {
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const valid = structuredClone(source.vue.prepared);
      const appId = 'fragment-concurrent-' + source.vue.appId;
      const host = document.createElement('div');
      host.id = appId;
      document.body.append(host);
      valid.host = '#' + appId;
      valid.manifest.appId = appId;
      valid.manifest.styles = [];
      valid.manifest.scripts = [];
      const invalid = structuredClone(valid);
      invalid.host = '#missing-concurrent-host';
      const rejected = __citryRuntime.startPrepared(invalid).then(() => false, () => true);
      const mounted = await __citryRuntime.startPrepared(valid);
      return {rejected: await rejected, alive: __citryRuntime._apps.has(appId), mounted: mounted.appId === appId};
    }""") == {"rejected": True, "alive": True, "mounted": True}
    page.evaluate("""() => {
      const appId = [...__citryRuntime._apps.keys()].find(id => id.startsWith('fragment-concurrent-'));
      __citryRuntime._apps.get(appId).vueApp.unmount();
      document.getElementById(appId).remove();
    }""")
    assert page.evaluate("""async () => {
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const manifest = structuredClone(source);
      const appId = 'fragment-invalid-' + source.vue.appId;
      const host = document.createElement('div');
      host.id = appId;
      document.body.append(host);
      manifest.vue.appId = appId;
      manifest.vue.host = '#' + appId;
      manifest.vue.prepared.host = '#' + appId;
      manifest.vue.prepared.manifest.appId = appId;
      const valid = structuredClone(manifest.vue.prepared.manifest.scripts[0]);
      valid.registersOptions = false;
      valid.source.url = '/must-not-load.js';
      const invalid = structuredClone(valid);
      invalid.source.url = '/invalid-second.js';
      invalid.source.attrs = {nonce: 'response-token'};
      manifest.vue.prepared.manifest.scripts = [valid, invalid];
      const before = performance.getEntriesByName(location.origin + '/must-not-load.js').length;
      try { await Citry.fragments.load(manifest); }
      catch (error) {
        const after = performance.getEntriesByName(location.origin + '/must-not-load.js').length;
        return {error: String(error), untouched: before === after};
      }
      return {error: 'mounted', untouched: false};
    }""") == {"error": "Error: invalid prepared asset source attributes", "untouched": True}
    assert page.evaluate("""async () => {
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const manifest = structuredClone(source);
      const appId = 'fragment-collision-' + source.vue.appId;
      const host = document.createElement('div');
      host.id = appId;
      document.body.append(host);
      manifest.vue.appId = appId;
      manifest.vue.host = '#' + appId;
      manifest.vue.prepared.host = '#' + appId;
      manifest.vue.prepared.manifest.appId = appId;
      const first = structuredClone(manifest.vue.prepared.manifest.scripts[0]);
      first.registersOptions = false;
      first.source.url = '/duplicate-script.js';
      first.source.attrs = {crossorigin: 'anonymous'};
      const second = structuredClone(first);
      second.source.attrs = {crossorigin: 'use-credentials'};
      manifest.vue.prepared.manifest.scripts = [first, second];
      const before = performance.getEntriesByName(location.origin + '/duplicate-script.js').length;
      try { await Citry.fragments.load(manifest); }
      catch (error) {
        const after = performance.getEntriesByName(location.origin + '/duplicate-script.js').length;
        return {error: String(error), untouched: before === after};
      }
      return {error: 'mounted', untouched: false};
    }""") == {"error": "Error: prepared script URL identity collision", "untouched": True}

    stalled_routes = []
    fragment_mount_baseline = page.evaluate("() => globalThis.__fragmentMounts")
    page.route("**/stalled-fragment.css", lambda route: stalled_routes.append(route))
    page.route(
        "**/must-not-run-after-cancel.js",
        lambda route: route.fulfill(
            body="globalThis.__cancelledScriptRuns=(globalThis.__cancelledScriptRuns||0)+1",
            content_type="text/javascript",
        ),
    )
    page.evaluate("""() => {
      globalThis.__cancelledScriptRuns = 0;
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const manifest = structuredClone(source);
      const appId = 'fragment-cancelled-' + source.vue.appId;
      const host = document.createElement('div');
      host.id = appId;
      document.body.append(host);
      manifest.vue.appId = appId;
      manifest.vue.host = '#' + appId;
      manifest.vue.prepared.host = '#' + appId;
      manifest.vue.prepared.manifest.appId = appId;
      manifest.vue.prepared.manifest.styles[0].source = {
        kind: 'external', url: '/stalled-fragment.css', attrs: {rel: 'stylesheet'},
      };
      const script = structuredClone(manifest.vue.prepared.manifest.scripts[0]);
      script.registersOptions = false;
      script.source = {kind: 'external', url: '/must-not-run-after-cancel.js', attrs: {}};
      manifest.vue.prepared.manifest.scripts = [script];
      globalThis.__cancelledManifest = manifest;
      globalThis.__cancelledHost = host;
      globalThis.__cancelledAppId = appId;
      globalThis.__cancelledResult = Citry.fragments.load(manifest).then(
        () => 'mounted',
        error => String(error),
      );
    }""")
    page.wait_for_function("() => document.querySelector('link[href$=\"/stalled-fragment.css\"]') !== null")
    page.evaluate("""() => {
      globalThis.__stalledLink = document.querySelector('link[href$="/stalled-fragment.css"]');
      __cancelledHost.id = __cancelledHost.id + '-changed';
    }""")
    # The link is in the DOM before its request reaches the route handler.
    wait_for_count(stalled_routes, 1)
    assert "host changed while mounting" in page.evaluate("() => __cancelledResult")
    cancelled = page.evaluate("""() => ({
      app: __citryRuntime._apps.has(__cancelledAppId),
      style: document.querySelector('link[href$="/stalled-fragment.css"]') !== null,
      scriptFetches: performance.getEntriesByName(location.origin + '/must-not-run-after-cancel.js').length,
      scriptRuns: globalThis.__cancelledScriptRuns,
      mounts: globalThis.__fragmentMounts,
    })""")
    assert cancelled == {
        "app": False,
        "style": False,
        "scriptFetches": 1,
        "scriptRuns": 0,
        "mounts": fragment_mount_baseline,
    }
    reused = page.evaluate("""async () => {
      const manifest = structuredClone(__cancelledManifest);
      const host = document.createElement('div');
      host.id = __cancelledAppId;
      document.body.append(host);
      manifest.vue.prepared.manifest.styles = [];
      manifest.vue.prepared.manifest.scripts = [];
      await Citry.fragments.load(manifest);
      __stalledLink.onerror?.();
      await Promise.resolve();
      return {alive: __citryRuntime._apps.has(__cancelledAppId), mounts: globalThis.__fragmentMounts};
    }""")
    assert reused == {"alive": True, "mounts": fragment_mount_baseline + 1}
    stalled_routes[0].fulfill(body=".fragment-value { color: rgb(7, 8, 9); }", content_type="text/css")
    page.evaluate("() => document.getElementById(__cancelledAppId).remove()")
    page.wait_for_function("() => !__citryRuntime._apps.has(__cancelledAppId)")

    late_script_routes = []
    page.route("**/late-extension-script.js", lambda route: late_script_routes.append(route))
    page.evaluate("""() => {
      __citryRuntime.registerBrowserPlugin('fragment_test', 1, () => ({
        install() {}, prepareRevision() { return {}; }, activateRevision() {}, commitRevision() {},
        abortRevision() {}, rollbackRevision() {}, dispose() {},
      }));
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const manifest = structuredClone(source);
      const appId = 'fragment-late-script-' + source.vue.appId;
      const host = document.createElement('div');
      host.id = appId;
      document.body.append(host);
      manifest.vue.appId = appId;
      manifest.vue.host = '#' + appId;
      manifest.vue.prepared.host = '#' + appId;
      manifest.vue.prepared.manifest.appId = appId;
      manifest.vue.prepared.manifest.styles = [];
      manifest.vue.prepared.manifest.extensions = {
        fragment_test: {payload: {}, schemaVersion: 1, templateContextNames: []},
      };
      manifest.vue.prepared.manifest.scripts = [{
        lazyAllowed: true, registersOptions: false,
        owner: {kind: 'extension', extensionName: 'fragment_test'},
        source: {kind: 'external', url: '/late-extension-script.js', attrs: {}},
      }];
      manifest.vue.prepared.manifest.scripts.push(
        structuredClone(manifest.vue.prepared.manifest.scripts[0]),
      );
      globalThis.__lateScriptManifest = manifest;
      globalThis.__lateScriptHost = host;
      globalThis.__lateScriptAppId = appId;
      globalThis.__lateScriptFirst = Citry.fragments.load(manifest).then(() => 'mounted', error => String(error));
    }""")
    page.wait_for_function(
        "() => document.querySelectorAll('script[src$=\"/late-extension-script.js\"]').length === 1"
    )
    page.evaluate("""() => {
      globalThis.__lateScriptElement = document.querySelector('script[src$="/late-extension-script.js"]');
      globalThis.__lateScriptOnerror = __lateScriptElement.onerror;
      __lateScriptHost.remove();
    }""")
    assert "host changed while mounting" in page.evaluate("() => __lateScriptFirst")
    # The script element exists before its request reaches the route handler,
    # so the list can still be empty here.
    wait_for_count(late_script_routes, 1)
    late_script_routes[0].abort()
    # Route abort delivery and the script element's error cleanup are separate
    # browser tasks. Wait for the cancelled request's actual script cleanup
    # before mounting the replacement, otherwise both script elements can
    # remain visible while the retry is waiting for its one deduplicated asset.
    page.wait_for_function("() => !__lateScriptElement.isConnected")
    page.evaluate("""() => {
      const host = document.createElement('div');
      host.id = __lateScriptAppId;
      document.body.append(host);
      globalThis.__lateScriptSecond = Citry.fragments.load(structuredClone(__lateScriptManifest));
    }""")
    page.wait_for_function(
        "() => document.querySelectorAll('script[src$=\"/late-extension-script.js\"]').length === 1"
    )
    wait_for_count(late_script_routes, 2)
    # Chromium reports the aborted request in the console, Firefox does not,
    # so the browser message is allowed to be absent.
    expected_abort_errors = [error for error in errors if "net::ERR_FAILED" in error]
    assert len(expected_abort_errors) <= 1
    for error in expected_abort_errors:
        errors.remove(error)
    page.evaluate("() => __lateScriptOnerror(new Event('error'))")
    late_script_routes[1].fulfill(body="", content_type="application/javascript")
    page.evaluate("() => __lateScriptSecond")
    assert len(late_script_routes) == 2
    assert page.evaluate("() => __citryRuntime._apps.has(__lateScriptAppId)") is True
    page.evaluate("() => document.getElementById(__lateScriptAppId).remove()")
    page.wait_for_function("() => !__citryRuntime._apps.has(__lateScriptAppId)")

    page.evaluate("""async () => {
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      for (const suffix of ['throwing', 'following']) {
        const manifest = structuredClone(source);
        const appId = 'fragment-dispose-' + suffix + '-' + source.vue.appId;
        const host = document.createElement('div');
        host.id = appId;
        document.body.append(host);
        manifest.vue.appId = appId;
        manifest.vue.host = '#' + appId;
        manifest.vue.prepared.host = '#' + appId;
        manifest.vue.prepared.manifest.appId = appId;
        manifest.vue.prepared.manifest.styles = [];
        manifest.vue.prepared.manifest.scripts = [];
        await Citry.fragments.load(manifest);
      }
      const throwingId = [...__citryRuntime._apps.keys()].find(id => id.startsWith('fragment-dispose-throwing-'));
      const followingId = [...__citryRuntime._apps.keys()].find(id => id.startsWith('fragment-dispose-following-'));
      const throwingApp = __citryRuntime._apps.get(throwingId).vueApp;
      globalThis.__restoreThrowingUnmount = throwingApp.unmount.bind(throwingApp);
      throwingApp.unmount = () => { throw new Error('expected fragment dispose failure'); };
      document.getElementById(throwingId).remove();
      document.getElementById(followingId).remove();
      globalThis.__throwingId = throwingId;
      globalThis.__followingId = followingId;
    }""")
    page.wait_for_function("() => !__citryRuntime._apps.has(__followingId)")
    assert page.evaluate("() => __citryRuntime._apps.has(__throwingId)") is True
    # Read the logged error's message outside the console handler. Chromium's
    # `message.text` includes it, but Firefox prints `JSHandle@object`.
    expected_dispose_errors = [
        message for message in console_messages if "expected fragment dispose failure" in _logged_error_text(message)
    ]
    assert len(expected_dispose_errors) == 1
    errors.remove(expected_dispose_errors[0].text)
    page.evaluate("""() => {
      __restoreThrowingUnmount();
      __citryRuntime._apps.delete(__throwingId);
    }""")

    delayed_routes = []
    delayed_mount_baseline = page.evaluate("() => globalThis.__fragmentMounts")
    page.route("**/delayed-fragment.css", lambda route: delayed_routes.append(route))
    page.route(
        "**/must-not-run-after-css.js",
        lambda route: route.fulfill(
            body="globalThis.__relocatedScriptRuns=(globalThis.__relocatedScriptRuns||0)+1",
            content_type="text/javascript",
        ),
    )
    page.evaluate("""() => {
      globalThis.__relocatedScriptRuns = 0;
      const source = JSON.parse(document.querySelector('script[data-citry-vue-fragment]').textContent);
      const manifest = structuredClone(source);
      const appId = 'fragment-relocated-' + source.vue.appId;
      const origin = document.createElement('div');
      const destination = document.createElement('div');
      const host = document.createElement('div');
      origin.id = appId + '-origin';
      destination.id = appId + '-destination';
      host.id = appId;
      origin.append(host);
      document.body.append(origin, destination);
      manifest.vue.appId = appId;
      manifest.vue.host = '#' + appId;
      manifest.vue.prepared.host = '#' + appId;
      manifest.vue.prepared.manifest.appId = appId;
      manifest.vue.prepared.manifest.styles[0].source = {
        kind: 'external', url: '/delayed-fragment.css', attrs: {rel: 'stylesheet'},
      };
      const script = structuredClone(manifest.vue.prepared.manifest.scripts[0]);
      script.registersOptions = false;
      script.source = {kind: 'external', url: '/must-not-run-after-css.js', attrs: {}};
      manifest.vue.prepared.manifest.scripts = [script];
      globalThis.__relocatedAppId = appId;
      globalThis.__relocatedHost = host;
      globalThis.__relocatedDestination = destination;
      globalThis.__relocatedResult = Citry.fragments.load(manifest).then(
        () => 'mounted',
        error => String(error),
      );
    }""")
    page.wait_for_function("() => document.querySelector('link[href$=\"/delayed-fragment.css\"]') !== null")
    page.evaluate("() => __relocatedDestination.append(__relocatedHost)")
    # As above, the link exists before its request reaches the route handler.
    wait_for_count(delayed_routes, 1)
    delayed_routes[0].fulfill(body=".fragment-value { color: rgb(4, 5, 6); }", content_type="text/css")
    assert "host changed while mounting" in page.evaluate("() => __relocatedResult")
    page.wait_for_function("() => !__citryRuntime._apps.has(__relocatedAppId)")
    assert page.locator('link[href$="/delayed-fragment.css"]').count() == 0
    assert page.evaluate("""() => ({
      scriptFetches: performance.getEntriesByName(location.origin + '/must-not-run-after-css.js').length,
      scriptRuns: globalThis.__relocatedScriptRuns,
      scriptElements: document.querySelectorAll('script[src$="/must-not-run-after-css.js"]').length,
    })""") == {"scriptFetches": 1, "scriptRuns": 0, "scriptElements": 0}
    assert page.evaluate("() => globalThis.__fragmentMounts") == delayed_mount_baseline
    assert (
        page.evaluate("""async () => {
      const tag = document.querySelector('script[data-citry-vue-fragment]');
      const manifest = JSON.parse(tag.textContent);
      manifest.vue.host = '#target';
      try { await Citry.fragments.load(manifest); }
      catch (error) { return String(error).includes('valid bound Vue mount descriptor'); }
      return false;
    }""")
        is True
    )
    page.locator("#target").evaluate("node => { node.textContent = ''; }")
    page.wait_for_function("() => __citryRuntime._apps.size === 0")
    assert errors == []


def test_fragment_startup_styles_survive_other_unmount_and_release_on_own_cancel(
    page, serve_live, wait_for_count, settle_timers
) -> None:
    """A pending fragment stylesheet is owned until startup accepts or cancels it."""
    import base64
    import json
    import time

    # Keep the message objects: the product logs an Error object, and only
    # its arguments give the same error text in every browser (see
    # `_logged_error_text`).
    console_errors: list[Any] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message) if message.type == "error" else None)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    app = Citry(autodiscover=False)
    app.set_mounted_prefix("/citry")

    class Existing(Component):
        citry = app
        template = '<p class="existing">existing</p>'
        css = ".existing { color: rgb(1, 2, 3); }"
        js = "$component({mounted(){window.__existingMounted=true},beforeUnmount(){window.__existingUnmounted=true}});"

    class SlowReplacement(Component):
        citry = app
        template = '<p class="slow-replacement">replacement</p>'
        css = ".slow-replacement { color: rgb(4, 5, 6); }"
        js = "$component({mounted(){window.__replacementMounted=true}});"

    class Cancelled(Component):
        citry = app
        template = '<p class="cancelled-startup">cancelled</p>'
        css = ".cancelled-startup { color: rgb(7, 8, 9); }"
        js = "$component({mounted(){window.__cancelledMounted=true}});"

    def encoded(component: Component) -> tuple[str, list[str]]:
        fragment = component.render().serialize(deps_strategy="fragment")
        # Stylesheets are addressed by content digest, so read each URL from
        # the fragment manifest to delay exactly this fragment's styles.
        manifest_json = fragment.split('<script type="application/json" data-citry-vue-fragment>', 1)[1]
        manifest = json.loads(manifest_json.split("</script>", 1)[0])
        style_urls = [style["source"]["url"] for style in manifest["vue"]["prepared"]["manifest"]["styles"]]
        return base64.b64encode(fragment.encode()).decode(), style_urls

    existing, _ = encoded(Existing())
    replacement, replacement_style_urls = encoded(SlowReplacement())
    cancelled, cancelled_style_urls = encoded(Cancelled())
    assert len(replacement_style_urls) == 1
    assert len(cancelled_style_urls) == 1
    document = f"""
      <html><head><script src="/citry/citry.js"></script></head><body>
      <div id="replacement-host"></div><div id="cancel-host"></div>
      <script>
      const fragment = value => atob(value);
      replacementHost = document.getElementById('replacement-host');
      cancelHost = document.getElementById('cancel-host');
      replacementHost.innerHTML = fragment({json.dumps(existing)});
      cancelHost.innerHTML = fragment({json.dumps(cancelled)});
      setTimeout(() => cancelHost.replaceChildren(), 50);
      const replace = setInterval(() => {{
        if (!window.__existingMounted) return;
        clearInterval(replace);
        replacementHost.innerHTML = fragment({json.dumps(replacement)});
      }}, 10);
      </script></body></html>
    """
    url = serve_live(app, document, "")

    answered_styles: list[str] = []

    def slow_style(route) -> None:
        time.sleep(0.35)
        route.continue_()
        answered_styles.append(route.request.url)

    page.route(f"**{replacement_style_urls[0]}", slow_style)
    page.route(f"**{cancelled_style_urls[0]}", slow_style)
    page.goto(url)
    # The replacement's markup is inserted before it mounts, so wait for its
    # mount and its delayed stylesheet rather than for the element.
    page.wait_for_function("() => window.__replacementMounted === true", timeout=5_000)
    page.wait_for_function(
        "() => getComputedStyle(document.querySelector('.slow-replacement')).color === 'rgb(4, 5, 6)'"
    )
    # Cancelling the cleared host's startup logs one console error.
    wait_for_count(console_errors, 1)
    # Once both delayed stylesheets have been answered, a cancelled startup
    # that still held its stylesheet would mount or keep its link right away.
    wait_for_count(answered_styles, 2)
    page.wait_for_function(
        'url => document.querySelectorAll(`link[href="${url}"]`).length === 0', arg=cancelled_style_urls[0]
    )
    # Checking that the cancelled startup did not mount needs a short wait for
    # something that should not happen; one timer and two frames cover it.
    settle_timers()

    assert page.evaluate("() => window.__existingUnmounted") is True
    assert page.evaluate("() => window.__replacementMounted") is True
    assert page.evaluate("() => window.__cancelledMounted") is not True
    assert page.locator(".cancelled-startup").count() == 0
    assert page.locator(f'link[href="{replacement_style_urls[0]}"]').count() == 1
    assert page.locator(f'link[href="{cancelled_style_urls[0]}"]').count() == 0
    assert page.locator(".slow-replacement").evaluate("node => getComputedStyle(node).color") == "rgb(4, 5, 6)"
    assert page_errors == []
    assert len(console_errors) == 1
    assert "Vue fragment host changed while mounting" in _logged_error_text(console_errors[0])
