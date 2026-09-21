"""Prepared Vue support for selected transparent roots and Python Slot calls."""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.slots import Slot

pytestmark = pytest.mark.e2e


def test_python_slot_keeps_nested_authored_fill_in_its_lexical_vue_scope(page, serve_document) -> None:
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

    page.goto(serve_document(Host(slots={"default": Content()}).render().serialize()))
    buttons = page.locator("button.lexical")
    assert buttons.all_text_contents() == ["caller", "caller"]
    buttons.first.click()
    assert buttons.all_text_contents() == ["caller!", "caller"]
    assert errors == []


def test_transparent_root_mounts_python_composed_multiroot_component(page, serve_document) -> None:
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
    page.goto(serve_document(rendered.serialize()))

    page.wait_for_selector("button.value")
    assert page.locator("button.value").text_content() == "ready"
    assert page.locator("span.tail").text_content() == "tail"
    assert page.evaluate("() => globalThis.__multiMounts") == 1
    assert errors == []


def test_transparent_root_mounts_empty_python_composed_component(page, serve_document) -> None:
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
    page.goto(serve_document(rendered.serialize()))

    page.wait_for_function("document.querySelector('[id^=citry-vue-]') !== null")
    assert page.locator("body").inner_text() == ""
    assert page.evaluate("() => globalThis.__emptyMounts") == 1
    assert errors == []


def test_prepared_component_without_events_unmounts_cleanly(page, serve_document) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    app = Citry(autodiscover=False)

    class Widget(Component):
        citry = app
        template = '<button class="no-events" v-text="label"></button>'

        def js_data(self, kwargs, slots):
            return {"label": "Ready"}

    rendered = app.render_template('<main id="owner"><c-widget /></main>')
    page.goto(serve_document(rendered.serialize()))
    page.wait_for_selector("button.no-events")
    page.wait_for_function("() => CitryStable._apps.size === 1")
    page.evaluate("""() => {
      const [appId, record] = [...CitryStable._apps.entries()][0];
      globalThis.__noEventsAppId = appId;
      record.vueApp.unmount();
    }""")
    page.wait_for_function("() => CitryStable._apps.size === 0")
    assert errors == []


def test_fragment_manager_loads_and_mounts_python_composed_component(page, serve_live) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
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

    page.wait_for_timeout(1_000)
    assert errors == [], page.content()
    assert page.locator('[id^="citry-vue-"]').count() == 1, page.content()
    assert page.locator("script[data-citry-vue-fragment]").count() == 1, page.content()
    assert page.evaluate("() => ({stable: !!window.CitryStable, manager: !!window.Citry?.fragments})") == {
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
          alive: CitryStable._apps.has(source.vue.appId),
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
      const rejected = CitryStable.startPrepared(invalid).then(() => false, () => true);
      const mounted = await CitryStable.startPrepared(valid);
      return {rejected: await rejected, alive: CitryStable._apps.has(appId), mounted: mounted.appId === appId};
    }""") == {"rejected": True, "alive": True, "mounted": True}
    page.evaluate("""() => {
      const appId = [...CitryStable._apps.keys()].find(id => id.startsWith('fragment-concurrent-'));
      CitryStable._apps.get(appId).vueApp.unmount();
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
    page.evaluate("""() => {
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
    assert len(stalled_routes) == 1
    assert "host changed while mounting" in page.evaluate("() => __cancelledResult")
    cancelled = page.evaluate("""() => ({
      app: CitryStable._apps.has(__cancelledAppId),
      style: document.querySelector('link[href$="/stalled-fragment.css"]') !== null,
      script: performance.getEntriesByName(location.origin + '/must-not-run-after-cancel.js').length,
      mounts: globalThis.__fragmentMounts,
    })""")
    assert cancelled == {
        "app": False,
        "style": False,
        "script": 0,
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
      return {alive: CitryStable._apps.has(__cancelledAppId), mounts: globalThis.__fragmentMounts};
    }""")
    assert reused == {"alive": True, "mounts": fragment_mount_baseline + 1}
    stalled_routes[0].fulfill(body=".fragment-value { color: rgb(7, 8, 9); }", content_type="text/css")
    page.evaluate("() => document.getElementById(__cancelledAppId).remove()")
    page.wait_for_function("() => !CitryStable._apps.has(__cancelledAppId)")

    late_script_routes = []
    page.route("**/late-extension-script.js", lambda route: late_script_routes.append(route))
    page.evaluate("""() => {
      CitryStable.registerBrowserPlugin('fragment_test', 1, () => ({
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
    late_script_routes[0].abort()
    page.evaluate("""() => {
      const host = document.createElement('div');
      host.id = __lateScriptAppId;
      document.body.append(host);
      globalThis.__lateScriptSecond = Citry.fragments.load(structuredClone(__lateScriptManifest));
    }""")
    page.wait_for_function(
        "() => document.querySelectorAll('script[src$=\"/late-extension-script.js\"]').length === 1"
    )
    for _ in range(50):
        if len(late_script_routes) == 2:
            break
        page.wait_for_timeout(20)
    assert len(late_script_routes) == 2
    expected_abort_errors = [error for error in errors if "net::ERR_FAILED" in error]
    assert len(expected_abort_errors) == 1
    errors.remove(expected_abort_errors[0])
    page.evaluate("() => __lateScriptOnerror(new Event('error'))")
    late_script_routes[1].fulfill(body="", content_type="application/javascript")
    page.evaluate("() => __lateScriptSecond")
    assert len(late_script_routes) == 2
    assert page.evaluate("() => CitryStable._apps.has(__lateScriptAppId)") is True
    page.evaluate("() => document.getElementById(__lateScriptAppId).remove()")
    page.wait_for_function("() => !CitryStable._apps.has(__lateScriptAppId)")

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
      const throwingId = [...CitryStable._apps.keys()].find(id => id.startsWith('fragment-dispose-throwing-'));
      const followingId = [...CitryStable._apps.keys()].find(id => id.startsWith('fragment-dispose-following-'));
      const throwingApp = CitryStable._apps.get(throwingId).vueApp;
      globalThis.__restoreThrowingUnmount = throwingApp.unmount.bind(throwingApp);
      throwingApp.unmount = () => { throw new Error('expected fragment dispose failure'); };
      document.getElementById(throwingId).remove();
      document.getElementById(followingId).remove();
      globalThis.__throwingId = throwingId;
      globalThis.__followingId = followingId;
    }""")
    page.wait_for_function("() => !CitryStable._apps.has(__followingId)")
    assert page.evaluate("() => CitryStable._apps.has(__throwingId)") is True
    expected_dispose_errors = [error for error in errors if "expected fragment dispose failure" in error]
    assert len(expected_dispose_errors) == 1
    errors.remove(expected_dispose_errors[0])
    page.evaluate("""() => {
      __restoreThrowingUnmount();
      CitryStable._apps.delete(__throwingId);
    }""")

    delayed_routes = []
    delayed_mount_baseline = page.evaluate("() => globalThis.__fragmentMounts")
    page.route("**/delayed-fragment.css", lambda route: delayed_routes.append(route))
    page.evaluate("""() => {
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
    assert len(delayed_routes) == 1
    delayed_routes[0].fulfill(body=".fragment-value { color: rgb(4, 5, 6); }", content_type="text/css")
    assert "host changed while mounting" in page.evaluate("() => __relocatedResult")
    page.wait_for_function("() => !CitryStable._apps.has(__relocatedAppId)")
    assert page.locator('link[href$="/delayed-fragment.css"]').count() == 0
    assert (
        page.evaluate("() => performance.getEntriesByName(location.origin + '/must-not-run-after-css.js').length") == 0
    )
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
    page.wait_for_function("() => CitryStable._apps.size === 0")
    assert errors == []


def test_fragment_startup_styles_survive_other_unmount_and_release_on_own_cancel(page, serve_live) -> None:
    """A pending fragment stylesheet is owned until startup accepts or cancels it."""
    import base64
    import json
    import time

    console_errors: list[str] = []
    page_errors: list[str] = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
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

    def encoded(component: Component) -> str:
        fragment = component.render().serialize(deps_strategy="fragment")
        return base64.b64encode(fragment.encode()).decode()

    existing = encoded(Existing())
    replacement = encoded(SlowReplacement())
    cancelled = encoded(Cancelled())
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

    def slow_style(route) -> None:
        time.sleep(0.35)
        route.continue_()

    page.route("**/citry/cache/SlowReplacement_*.css", slow_style)
    page.route("**/citry/cache/Cancelled_*.css", slow_style)
    page.goto(url)
    page.wait_for_selector(".slow-replacement", timeout=5_000)
    page.wait_for_timeout(500)

    assert page.evaluate("() => window.__existingUnmounted") is True
    assert page.evaluate("() => window.__replacementMounted") is True
    assert page.evaluate("() => window.__cancelledMounted") is not True
    assert page.locator(".cancelled-startup").count() == 0
    assert page.locator('link[href*="Cancelled_"]').count() == 0
    assert page.locator(".slow-replacement").evaluate("node => getComputedStyle(node).color") == "rgb(4, 5, 6)"
    assert page_errors == []
    assert len(console_errors) == 1
    assert "Vue fragment host changed while mounting" in console_errors[0]
