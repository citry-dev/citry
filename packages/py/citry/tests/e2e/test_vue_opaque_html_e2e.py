from __future__ import annotations

import json
from typing import Any

import pytest

from citry import Citry, Component
from citry._vue.serialization import hydration_admission
from citry.ext.events import actions
from citry.ext.events.renderers import dispatcher_for
from citry.util.html import Markup

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


def _zone_html(page: Any) -> str:
    """Return the zone's HTML without the Fragment comments a hydrated block keeps around it."""
    return page.locator("#zone").inner_html().replace("<!--[-->", "").replace("<!--]-->", "")


def test_opaque_html_updates_as_keyed_inert_static_ranges(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="opaque-html-e2e-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")

    body_a = (
        '<button id="opaque-a" @click="globalThis.__opaqueRan=true">'
        '{{ unsafe }}</button><!-- middle --><span id="opaque-b">B</span>'
    )
    body_b = '<article id="opaque-changed">changed payload</article>'
    body_reordered = (
        '<span id="opaque-b">B</span><button id="opaque-a" @click="globalThis.__opaqueRan=true">{{ unsafe }}</button>'
    )
    bodies = (
        body_a,
        body_a,
        body_a,
        body_a,
        body_b,
        "",
        body_a,
        body_reordered,
    )

    class Opaque(Component):
        citry = engine
        template = (
            '<main><button id="advance" @c-click="advance">advance</button><section id="zone">{{ bo'
            "dy }}</section></main>"
        )

        class State:
            stage: int = 0

        class Events:
            def advance(self, state: Opaque.State):
                state.stage += 1
                return Opaque(stage=state.stage)

        def template_data(self, kwargs, slots):
            return {
                # This test passes fixed trusted markup to exercise opaque HTML updates.
                "body": Markup(bodies[kwargs.get("stage", 0)])  # noqa: S704 -- trusted test fixture
            }

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, Opaque(stage=0).render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 0")
    assert _zone_html(page) == body_a
    assert page.locator("#opaque-a").text_content() == "{{ unsafe }}"
    page.locator("#opaque-a").click()
    assert page.evaluate("globalThis.__opaqueRan") is None
    page.evaluate("""() => {
      globalThis.__firstOpaque = document.querySelector('#opaque-a');
      globalThis.__firstOpaqueNodes = [...document.querySelector('#zone').childNodes];
    }""")

    for revision in (1, 2, 3):
        page.locator("#advance").click()
        page.wait_for_function(
            "revision => __citryRuntime._apps.values().next().value.revision === revision",
            arg=revision,
        )
        assert _zone_html(page) == body_a
        assert page.evaluate("""() => globalThis.__firstOpaqueNodes.every(
          (node, index) => document.querySelector('#zone').childNodes[index] === node
        )""")
        assert page.evaluate("globalThis.__firstOpaque === document.querySelector('#opaque-a')")

    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 4")
    page.wait_for_selector("#opaque-changed")
    assert _zone_html(page) == body_b
    assert page.evaluate("""() => globalThis.__firstOpaqueNodes.every(
      node => !document.querySelector('#zone').contains(node)
    )""")

    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 5")
    assert _zone_html(page) == ""

    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 6")
    assert _zone_html(page) == body_a
    assert page.evaluate("""() => globalThis.__firstOpaqueNodes.every(
      node => !document.querySelector('#zone').contains(node)
    )""")
    assert page.evaluate("""() => {
      globalThis.__recreatedOpaqueNodes = [...document.querySelector('#zone').childNodes];
      return globalThis.__recreatedOpaqueNodes[0] !== globalThis.__firstOpaqueNodes[0];
    }""")

    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 7")
    assert _zone_html(page) == body_reordered
    assert page.locator("#zone > *").all_inner_texts() == ["B", "{{ unsafe }}"]

    unmounted = page.evaluate("""() => {
      const app = __citryRuntime._apps.values().next().value;
      const host = app.hostElement;
      app.vueApp.unmount();
      return {hostChildCount: host.childNodes.length, registeredApps: __citryRuntime._apps.size};
    }""")
    assert unmounted == {"hostChildCount": 0, "registeredApps": 0}
    assert faults == []


def test_static_html_replacement_loses_mounted_listener_while_vue_patch_preserves_it(
    page: Any, serve_live: Any
) -> None:
    engine = Citry(secret="opaque-static-listener-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    static_a = '<span id="opaque-span" title="inert">same</span>'
    static_b = '<span title="inert" id="opaque-span">same</span>'

    class Opaque(Component):
        citry = engine
        template = (
            '<main><button id="advance" @c-click="advance">advance</button>'
            '<section id="zone">{{ body }}</section>'
            '<span id="ordinary-span" ref="ordinary">same</span></main>'
        )
        js = """$component({
          mounted(){
            const opaque=this.$el.querySelector('#opaque-span');
            const ordinary=this.$refs.ordinary;
            const state=globalThis.__nativeState={opaqueClicks:0,ordinaryClicks:0,cleanupCount:0};
            this.__opaqueNativeClick=()=>state.opaqueClicks++;
            this.__ordinaryNativeClick=()=>state.ordinaryClicks++;
            opaque.addEventListener('click',this.__opaqueNativeClick);
            ordinary.addEventListener('click',this.__ordinaryNativeClick);
            globalThis.__opaqueMountedRef=opaque;
            globalThis.__ordinaryMountedRef=ordinary;
          },
          beforeUnmount(){
            globalThis.__opaqueMountedRef.removeEventListener('click',this.__opaqueNativeClick);
            globalThis.__ordinaryMountedRef.removeEventListener('click',this.__ordinaryNativeClick);
            globalThis.__nativeState.cleanupCount++;
          }
        });"""

        class State:
            stage: int = 0

        class Events:
            def advance(self, state: Opaque.State):
                state.stage += 1
                return Opaque(stage=state.stage)

        def template_data(self, kwargs, slots):
            html = static_a if kwargs.get("stage", 0) == 0 else static_b
            return {"body": Markup(html)}  # noqa: S704 -- fixed trusted test fixture

    dispatcher_for(engine)
    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    base = serve_live(engine, Opaque(stage=0).render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 0")
    page.wait_for_function("window.__nativeState?.cleanupCount === 0")

    initial = page.evaluate("""() => {
      const opaque=document.querySelector('#opaque-span');
      const ordinary=document.querySelector('#ordinary-span');
      return {opaqueHtml:opaque.outerHTML,ordinaryHtml:ordinary.outerHTML,
        refsMatch:window.__opaqueMountedRef===opaque && window.__ordinaryMountedRef===ordinary,
        counts:{...window.__nativeState}};
    }""")
    assert initial == {
        "opaqueHtml": static_a,
        "ordinaryHtml": '<span id="ordinary-span">same</span>',
        "refsMatch": True,
        "counts": {"opaqueClicks": 0, "ordinaryClicks": 0, "cleanupCount": 0},
    }
    page.locator("#opaque-span").click()
    page.locator("#ordinary-span").click()
    assert page.evaluate("({ ...window.__nativeState })") == {
        "opaqueClicks": 1,
        "ordinaryClicks": 1,
        "cleanupCount": 0,
    }

    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 1")
    after = page.evaluate("""() => {
      const opaque=document.querySelector('#opaque-span');
      const ordinary=document.querySelector('#ordinary-span');
      const names=node=>Object.fromEntries([...node.attributes].map(attr=>[attr.name,attr.value])
        .sort(([left],[right])=>left.localeCompare(right)));
      return {opaqueHtml:opaque.outerHTML,opaqueSameNode:opaque===window.__opaqueMountedRef,
        opaqueRefConnected:window.__opaqueMountedRef.isConnected,
        opaqueDomEquivalent:opaque.textContent===window.__opaqueMountedRef.textContent
          && JSON.stringify(names(opaque))===JSON.stringify(names(window.__opaqueMountedRef)),
        ordinarySameNode:ordinary===window.__ordinaryMountedRef,
        counts:{...window.__nativeState}};
    }""")
    assert after["opaqueHtml"] == static_b
    assert after["opaqueSameNode"] is False
    assert after["opaqueRefConnected"] is False
    assert after["opaqueDomEquivalent"] is True
    assert after["ordinarySameNode"] is True
    assert after["counts"] == {"opaqueClicks": 1, "ordinaryClicks": 1, "cleanupCount": 0}

    page.locator("#opaque-span").click()
    page.locator("#ordinary-span").click()
    assert page.evaluate("({ ...window.__nativeState })") == {
        "opaqueClicks": 1,
        "ordinaryClicks": 2,
        "cleanupCount": 0,
    }

    cleanup = page.evaluate("""() => {
      const app=__citryRuntime._apps.values().next().value;
      const host=app.hostElement;
      app.vueApp.unmount();
      const afterUnmount={hostChildCount:host.childNodes.length,registeredApps:__citryRuntime._apps.size,
        counts:{...window.__nativeState}};
      window.__opaqueMountedRef.dispatchEvent(new MouseEvent('click',{bubbles:true}));
      window.__ordinaryMountedRef.dispatchEvent(new MouseEvent('click',{bubbles:true}));
      return {afterUnmount,afterDetachedClicks:{...window.__nativeState}};
    }""")
    assert cleanup == {
        "afterUnmount": {
            "hostChildCount": 0,
            "registeredApps": 0,
            "counts": {"opaqueClicks": 1, "ordinaryClicks": 2, "cleanupCount": 1},
        },
        "afterDetachedClicks": {"opaqueClicks": 1, "ordinaryClicks": 2, "cleanupCount": 1},
    }
    assert faults == []


def test_hydrated_static_vnode_keeps_node_and_native_listener_on_unchanged_render(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="opaque-static-hydration-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    body = '<span id="opaque-span" title="inert">same</span>'

    class Opaque(Component):
        citry = engine
        template = (
            '<main><button id="advance" @c-click="advance">advance</button>'
            '<section id="zone">{{ body }}</section></main>'
        )
        js = """$component({
          mounted(){
            const node=this.$el.querySelector('#opaque-span');
            const state=globalThis.__staticVNodeState={clicks:0,cleanupCount:0};
            this.__staticVNodeClick=()=>state.clicks++;
            node.addEventListener('click',this.__staticVNodeClick);
            globalThis.__staticVNodeRef=node;
          },
          beforeUnmount(){
            globalThis.__staticVNodeRef.removeEventListener('click',this.__staticVNodeClick);
            globalThis.__staticVNodeState.cleanupCount++;
          }
        });"""

        class State:
            stage: int = 0

        class Events:
            def advance(self, state: Opaque.State):
                state.stage += 1
                return Opaque(stage=state.stage)

        def template_data(self, kwargs, slots):
            return {"body": Markup(body)}  # noqa: S704 -- fixed trusted test fixture

    dispatcher_for(engine)
    faults: list[str] = []
    warnings: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on("console", lambda message: warnings.append(message.text) if message.type == "warning" else None)
    rendered = Opaque(stage=0).render()
    html = rendered.serialize()
    # The block is written between the Fragment comments of its static vnode.
    assert '"hydrate":true' in html
    assert f'<section id="zone"><!--[-->{body}<!--]--></section>' in html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.declines == ()

    base = serve_live(engine, _capture_served_nodes(html, "#opaque-span"), "")
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(base + "/")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 0")
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    initial = page.evaluate("""() => ({
      sameServerNode:window.__servedNodes[0]===document.querySelector('#opaque-span'),
      sameMountedRef:window.__servedNodes[0]===window.__staticVNodeRef,
      probe:window.__citryHydrationReport,
      state:{...window.__staticVNodeState}
    })""")
    assert initial["sameServerNode"] is True
    assert initial["sameMountedRef"] is True
    assert initial["state"] == {"clicks": 0, "cleanupCount": 0}
    assert initial["probe"]["mountError"] is None
    assert initial["probe"]["mismatchCount"] == 0
    assert initial["probe"]["reusedElementCount"] >= 2
    assert initial["probe"]["replacedElementCount"] == 0

    page.locator("#opaque-span").click()
    assert page.evaluate("window.__staticVNodeState.clicks") == 1
    page.locator("#advance").click()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 1")
    after_revision = page.evaluate("""() => ({
      sameServerNode:window.__servedNodes[0]===document.querySelector('#opaque-span'),
      sameMountedRef:window.__staticVNodeRef===document.querySelector('#opaque-span'),
      markup:document.querySelector('#zone').innerHTML,
      state:{...window.__staticVNodeState}
    })""")
    assert after_revision["sameServerNode"] is True
    assert after_revision["sameMountedRef"] is True
    assert after_revision["markup"] == f"<!--[-->{body}<!--]-->"
    assert after_revision["state"] == {"clicks": 1, "cleanupCount": 0}
    page.locator("#opaque-span").click()
    assert page.evaluate("window.__staticVNodeState.clicks") == 2

    cleanup = page.evaluate("""() => {
      const app=__citryRuntime._apps.values().next().value;
      const host=app.hostElement;
      app.vueApp.unmount();
      const counts={...window.__staticVNodeState};
      window.__servedNodes[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));
      return {hostChildCount:host.childNodes.length,registeredApps:__citryRuntime._apps.size,
        counts,afterDetachedClick:{...window.__staticVNodeState}};
    }""")
    assert cleanup == {
        "hostChildCount": 0,
        "registeredApps": 0,
        "counts": {"clicks": 2, "cleanupCount": 1},
        "afterDetachedClick": {"clicks": 2, "cleanupCount": 1},
    }
    assert warnings == []
    assert faults == []


# Each block is trusted HTML the page carries between two plain texts. The
# browser's parse must give Vue exactly the nodes the server counted.
_TRICKY_BLOCKS = {
    "text-around": "lead <b>bold</b> tail",
    "comments": "<b>x</b><!-- middle --><i>y</i><!-- end -->",
    "entities": "a &amp; b &lt;c&gt; <em>&quot;e&quot;</em>",
    "nested": "<span><em>a<b>b</b></em></span>",
    "adjacent-first": "one <i>1</i>",
    "adjacent-second": "<i>2</i> two",
}


def test_raw_html_blocks_hydrate_in_place_with_no_mismatch(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class Blocks(Component):
        citry = engine
        template = """
<main>
  <p id="text-around">before {{ blocks['text-around'] }} after</p>
  <div id="comments">{{ blocks['comments'] }}</div>
  <p id="entities">{{ blocks['entities'] }}</p>
  <p id="nested">x{{ blocks['nested'] }}y</p>
  <p id="adjacent">{{ blocks['adjacent-first'] }}{{ blocks['adjacent-second'] }}</p>
  <p id="spaces">[<c-raw>   </c-raw>]</p>
  <p id="empty">[<c-raw></c-raw>]</p>
  <p id="leading-comment">{{ leading_comment }}</p>
  <button
    id="bump"
    type="button"
    @click="count++"
  >bump</button>
  <output id="count" v-text="count"></output>
</main>
"""
        js = """
$component({data(){return {count: 0};}});
"""

        def template_data(self, kwargs: Any, slots: Any) -> dict[str, Any]:
            return {
                # Fixed trusted fixtures.
                "blocks": {name: Markup(html) for name, html in _TRICKY_BLOCKS.items()},  # noqa: S704
                "leading_comment": Markup("<!-- first --><b>after a comment</b>"),
            }

    rendered = Blocks().render()
    html = rendered.serialize()
    assert '"hydrate":true' in html
    host = html[html.index('<div id="citry-vue-') : html.index("<script", html.index('<div id="citry-vue-'))]
    for block in _TRICKY_BLOCKS.values():
        assert f"<!--[-->{block}<!--]-->" in host
    assert "<!--[-->   <!--]-->" in host
    assert "[<!--[--><!--]-->]" in host
    # Vue's static hydration cannot start at a comment, so that block's
    # paragraph is built in the browser; it still shows the block until then.
    admission = hydration_admission(rendered)
    assert admission is not None
    assert [(item.code, item.shell_tag, item.shell_content) for item in admission.declines] == [
        ("opaque-html", "p", True)
    ]
    assert '<p id="leading-comment" data-allow-mismatch="children"><!-- first --><b>after a comment</b></p>' in host

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    page.goto(serve_document(_capture_served_nodes(html, "main *")))
    page.wait_for_function("window.__citryHydrationReport !== undefined")
    report = page.evaluate("window.__citryHydrationReport")
    assert report["mountError"] is None, report
    assert report["mismatchCount"] == 0, report
    assert report["replacedElementCount"] == 0, report
    assert report["warnings"] == [], report

    expected = {
        "text-around": "before lead bold tail after",
        "comments": "xy",
        "entities": 'a & b <c> "e"',
        "nested": "xaby",
        "adjacent": "one 12 two",
        "spaces": "[   ]",
        "empty": "[]",
        "leading-comment": "after a comment",
    }

    def texts() -> dict[str, str]:
        return {name: page.text_content(f"#{name}") for name in expected}

    assert texts() == expected
    # Every element the server wrote outside the rebuilt paragraph is still
    # the one the browser parsed, including the blocks' own elements.
    kept = "() => window.__servedNodes.every((node, i) => window.__servedInShell[i] || node.isConnected)"
    assert page.evaluate(kept) is True

    # A local update renders the component again and leaves every block alone.
    page.click("#bump")
    page.wait_for_function("document.querySelector('#count').textContent === '1'")
    assert texts() == expected
    assert page.evaluate(kept) is True
    assert faults == [], faults


def test_root_opaque_html_mounts_multiple_roots_without_a_wrapper(page: Any, serve_document: Any) -> None:
    engine = Citry(autodiscover=False)

    class OpaqueRoot(Component):
        citry = engine
        template = "{{ body }}"
        js = "$component({data(){return {mounted: true};}});"
        css = ".opaque-root { color: var(--opaque-color); }"

        def template_data(self, kwargs, slots):
            return {
                "body": Markup(
                    '<span id="first-root" class="opaque-root">A</span>'
                    '<span id="second-root" class="opaque-root">B</span>'
                )
            }

        def css_data(self, kwargs, slots):
            return {"opaque-color": "rgb(0, 128, 0)"}

    faults: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.goto(serve_document(OpaqueRoot().render().serialize()))
    page.wait_for_selector("#first-root")
    assert page.locator('[id^="citry-vue-"] > span').count() == 2
    assert page.locator("#first-root").text_content() == "A"
    assert page.locator("#second-root").text_content() == "B"
    for selector in ("#first-root", "#second-root"):
        names = page.locator(selector).evaluate("node => node.getAttributeNames()")
        assert len([name for name in names if name.startswith("data-ccss-")]) == 1
        assert page.locator(selector).evaluate("node => getComputedStyle(node).color") == "rgb(0, 128, 0)"
    assert faults == []


def test_changed_python_summary_updates_during_render_action(page: Any, serve_live: Any) -> None:
    engine = Citry(secret="changed-python-summary-secret", autodiscover=False)  # noqa: S106
    engine.set_mounted_prefix("/citry")
    calls = {"page": 0, "summary": 0, "sibling": 0}
    events: list[int] = []
    summary_render_id = ""

    class Summary(Component):
        citry = engine
        template = """\
<section id="summary"><h4>Total</h4>\
<span id="python-value">{{ value }}</span></section>\
"""

        def template_data(self, kwargs, slots):
            nonlocal summary_render_id
            calls["summary"] += 1
            summary_render_id = self.id
            return kwargs

    class LocalSibling(Component):
        citry = engine
        template = """\
<button id="local-sibling" @click="local += 1" v-text="local"></button>\
"""
        js = """$component({
          data(){return {local:0};},
          mounted(){
            globalThis.__siblingLifecycle ||= {mounted:0,cleanup:0};
            globalThis.__siblingLifecycle.mounted++;
          },
          beforeUnmount(){globalThis.__siblingLifecycle.cleanup++;}
        });"""

        def template_data(self, kwargs, slots):
            calls["sibling"] += 1
            return {}

    class Page(Component):
        citry = engine
        template = """\
<main><button id="advance" @c-click="advance">advance</button>\
{{ summary }}{{ sibling }}</main>\
"""

        class State:
            value: int = 10

        class Events:
            def advance(self, state: Page.State):
                events.append(state.value)
                state.value += 1
                return actions.Render(
                    Summary(value=str(state.value)),
                    target=f"render:{summary_render_id}",
                )

        def template_data(self, kwargs, slots):
            calls["page"] += 1
            value = str(kwargs.get("value", 10))
            return {"summary": Summary(value=value), "sibling": LocalSibling()}

    dispatcher_for(engine)
    faults: list[str] = []
    console_errors: list[str] = []
    page.on("pageerror", lambda error: faults.append(str(error)))
    page.on(
        "console",
        lambda message: console_errors.append(message.text) if message.type in {"warning", "error"} else None,
    )
    page.add_init_script(
        """window.__changedSummaryReady=[];
        document.addEventListener('citry:ready', event => window.__changedSummaryReady.push(event.detail.appId));"""
    )

    page.add_init_script("globalThis.__citryHydrationDiagnostics = true")
    rendered = Page(value=10).render()
    assert calls == {"page": 1, "summary": 1, "sibling": 1}
    html = rendered.serialize(ssr=True)
    assert calls == {"page": 1, "summary": 1, "sibling": 1}
    # The summary is ordinary Vue output, so the page hydrates and the later
    # Render patches its Python value in place.
    assert '"hydrate":true' in html
    assert '<section id="summary"><h4>Total</h4><span id="python-value">10</span></section>' in html
    admission = hydration_admission(rendered)
    assert admission is not None
    assert admission.shell_count == 0, admission
    # The configuration JSON starts right after the data block's opening tag.
    payload_start = html.index(">", html.index('<script type="application/json" data-citry-vue-document="')) + 1
    configuration, _ = json.JSONDecoder().raw_decode(html[payload_start:])
    manifest = configuration["manifest"]
    # The Python value travels as prepared text, not as a block of HTML.
    assert all(not definition["opaqueHtmlSites"] for definition in manifest["definitions"])
    assert [
        occurrence["preparedData"]
        for occurrence in manifest["occurrences"]
        if "opaqueHtml" in occurrence["preparedData"] or "10" in occurrence["preparedData"].values()
    ] == [{"calls": {}, "citryText0": "10"}]

    page.goto(serve_live(engine, html, "") + "/")
    page.wait_for_function("window.__changedSummaryReady?.length === 1")
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 0")
    initial = page.evaluate("""() => {
      const summary=document.querySelector('#summary');
      const sibling=document.querySelector('#local-sibling');
      window.__initialSibling=sibling;
      window.__initialSiblingInstance=sibling.__vueParentComponent;
      return {summaryHtml:summary.outerHTML, summaryValue:summary.querySelector('#python-value')?.textContent,
        siblingText:sibling.textContent, siblingLifecycle:{...window.__siblingLifecycle},
        probe:window.__citryHydrationReport ?? null};
    }""")
    assert initial["summaryValue"] == "10"
    assert initial["siblingText"] == "0"
    assert initial["siblingLifecycle"] == {"mounted": 1, "cleanup": 0}
    assert initial["probe"]["mountError"] is None
    assert initial["probe"]["mismatchCount"] == 0
    assert initial["probe"]["replacedElementCount"] == 0

    page.locator("#local-sibling").click()
    page.wait_for_function("document.querySelector('#local-sibling')?.textContent === '1'")
    with page.expect_response("**/ext/events/call") as render_response:
        page.locator("#advance").click()
    assert render_response.value.ok, render_response.value.text()
    page.wait_for_function("__citryRuntime._apps.values().next().value.revision === 1")
    page.wait_for_function("document.querySelector('#python-value')?.textContent === '11'")

    updated = page.evaluate("""() => {
      const summary=document.querySelector('#summary');
      const sibling=document.querySelector('#local-sibling');
      const probe=window.__citryHydrationReport;
      return {summaryHtml:summary.outerHTML,
        siblingStable:sibling===window.__initialSibling
          && sibling.__vueParentComponent===window.__initialSiblingInstance,
        siblingText:sibling.textContent, siblingLifecycle:{...window.__siblingLifecycle},
        probe:probe ?? null};
    }""")
    assert updated["summaryHtml"] != initial["summaryHtml"]
    assert updated["summaryHtml"] == (
        '<section id="summary"><h4>Total</h4><span id="python-value">11</span></section>'
    )
    assert updated["siblingStable"] is True
    assert updated["siblingText"] == "1"
    assert updated["siblingLifecycle"] == {"mounted": 1, "cleanup": 0}
    # The probe records only the first mount, so the Render leaves it as it was.
    assert updated["probe"] == initial["probe"]
    assert calls == {"page": 1, "summary": 2, "sibling": 1}
    assert events == [10]

    cleanup = page.evaluate("""() => {
      const app=__citryRuntime._apps.values().next().value;
      const host=app.hostElement;
      app.vueApp.unmount();
      return {hostChildCount:host.childNodes.length,registeredApps:__citryRuntime._apps.size,
        siblingLifecycle:{...window.__siblingLifecycle}};
    }""")
    assert cleanup == {
        "hostChildCount": 0,
        "registeredApps": 0,
        "siblingLifecycle": {"mounted": 1, "cleanup": 1},
    }
    assert console_errors == []
    assert faults == []
