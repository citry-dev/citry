"""Browser acceptance for graph-owned Alpine slot source projection."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component, Markup

pytestmark = pytest.mark.e2e

READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def test_supplied_fill_uses_caller_scope_before_fill_local_data(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = """
          <section class="card" x-data="{ owner: 'child', childOnly: 'C' }" x-ref="childRef">
            <c-slot name="body" />
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <main
              id="fill-source"
              x-data="{ owner: 'parent', parentOnly: 'P', count: 0, show: true, items: ['a', 'b'] }"
              x-id="['shared-id']"
              x-ref="sourceRef"
            >
              <output class="count" x-text="count"></output>
              <c-card>
                <c-fill name="body">
                  <button
                    class="caller-fill"
                    x-ref="fillOwned"
                    x-text="owner"
                    @click="count += 1"
                  ></button>
                  <div class="local-fill" x-data="{ owner: 'local', localOnly: 'L' }"></div>
                  <template x-if="show">
                    <span class="if-fill" x-text="owner + ':' + parentOnly"></span>
                  </template>
                  <template x-for="item in items" :key="item">
                    <span class="for-fill" x-text="owner + ':' + item"></span>
                  </template>
                </c-fill>
              </c-card>
            </main>
          </body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.caller-fill')?.textContent === 'parent'")
    page.wait_for_function("document.querySelectorAll('.for-fill').length === 2")

    result = page.evaluate(
        """
        () => {
          const fill = document.querySelector('.caller-fill');
          const local = document.querySelector('.local-fill');
          const source = document.getElementById('fill-source');
          return {
            fill: {
              owner: Alpine.evaluate(fill, 'owner'),
              parentOnly: Alpine.evaluate(fill, 'parentOnly'),
              childOnlyType: Alpine.evaluate(fill, 'typeof childOnly'),
              root: Alpine.evaluate(fill, '$root.id'),
              sourceRef: Alpine.evaluate(fill, '$refs.sourceRef?.id ?? null'),
              childRef: Alpine.evaluate(fill, '$refs.childRef?.className ?? null'),
              id: Alpine.evaluate(fill, "$id('shared-id')"),
            },
            local: {
              owner: Alpine.evaluate(local, 'owner'),
              parentOnly: Alpine.evaluate(local, 'parentOnly'),
              localOnly: Alpine.evaluate(local, 'localOnly'),
            },
            source: {
              fillRef: Alpine.evaluate(source, '$refs.fillOwned?.className ?? null'),
              id: Alpine.evaluate(source, "$id('shared-id')"),
            },
            structural: {
              ifText: document.querySelector('.if-fill').textContent,
              forText: Array.from(document.querySelectorAll('.for-fill')).map((el) => el.textContent),
            },
          };
        }
        """
    )

    assert result == {
        "fill": {
            "owner": "parent",
            "parentOnly": "P",
            "childOnlyType": "undefined",
            "root": "fill-source",
            "sourceRef": "fill-source",
            "childRef": None,
            "id": result["source"]["id"],
        },
        "local": {"owner": "local", "parentOnly": "P", "localOnly": "L"},
        "source": {"fillRef": "caller-fill", "id": result["source"]["id"]},
        "structural": {"ifText": "parent:P", "forText": ["parent:a", "parent:b"]},
    }

    page.locator(".caller-fill").click()
    page.wait_for_function("document.querySelector('.count')?.textContent === '1'")


def test_nested_fallback_reverses_to_receiver_and_nested_component_stays_isolated(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = c
        template = '<strong class="leaf" x-data="{ owner: \'leaf\', leafOnly: true }" x-text="owner"></strong>'

    class Card(Component):
        citry = c
        template = """
          <section class="nested-card" x-data="{ owner: 'child', childOnly: 'C' }">
            <c-slot name="body"><i class="child-fallback" x-text="owner"></i></c-slot>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html><body><main x-data="{ owner: 'parent', parentOnly: 'P' }">
            <c-card>
              <c-fill name="body" fallback="fallback">
                <article class="outer-fill">
                  <span class="outer-owner" x-text="owner"></span>
                  {{ fallback }}
                  <c-leaf />
                </article>
              </c-fill>
            </c-card>
          </main></body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.child-fallback')?.textContent === 'child'")

    result = page.evaluate(
        """
        () => ({
          outer: document.querySelector('.outer-owner').textContent,
          fallback: {
            text: document.querySelector('.child-fallback').textContent,
            parentOnlyType: Alpine.evaluate(document.querySelector('.child-fallback'), 'typeof parentOnly'),
            childOnly: Alpine.evaluate(document.querySelector('.child-fallback'), 'childOnly'),
          },
          leaf: {
            text: document.querySelector('.leaf').textContent,
            parentOnlyType: Alpine.evaluate(document.querySelector('.leaf'), 'typeof parentOnly'),
            childOnlyType: Alpine.evaluate(document.querySelector('.leaf'), 'typeof childOnly'),
            leafOnly: Alpine.evaluate(document.querySelector('.leaf'), 'leafOnly'),
          },
        })
        """
    )
    assert result == {
        "outer": "parent",
        "fallback": {"text": "child", "parentOnlyType": "undefined", "childOnly": "C"},
        "leaf": {
            "text": "leaf",
            "parentOnlyType": "undefined",
            "childOnlyType": "undefined",
            "leafOnly": True,
        },
    }


def test_slot_only_shared_root_does_not_fall_through_to_receiver_scope(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        js = "$component(({ scope }) => { scope.owner = 'child'; scope.childOnly = 'C'; })"
        template = "<c-slot />"

    class Page(Component):
        citry = c
        template = """
          <html><body><main id="shared-source" x-data="{ owner: 'parent' }">
            <c-card><button class="shared-fill" x-text="owner + ':' + typeof childOnly"></button></c-card>
          </main></body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.shared-fill')?.textContent === 'parent:undefined'")
    assert page.locator(".shared-fill").inner_text() == "parent:undefined"


def test_fill_citry_magics_use_source_owner_but_public_send_element_stays_physical(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = "<c-slot />"

        class Events:
            def save(self):
                return None

    class Page(Component):
        citry = c
        template = """
          <html><body><main class="events-source">
            <c-card>
              <button
                class="events-fill"
                @c-click="save({ kind: 'compiled' })"
                @magic-send="$sendEvent('save', { kind: 'magic' })"
              >send</button>
            </c-card>
          </main></body></html>
        """

        class Events:
            def save(self):
                return None

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(
        """
        () => {
          window.__fillCalls = [];
          Citry.events._internal.setTransport(async (call) => {
            window.__fillCalls.push(call);
            return { ok: true, actions: [] };
          });
        }
        """
    )

    page.locator(".events-fill").click()
    page.wait_for_timeout(100)
    first_probe = page.evaluate(
        """
        () => {
          const el = document.querySelector('.events-fill');
          return {
            calls: window.__fillCalls,
            binding: el.getAttribute('data-cev-on'),
            sourceOwner: Citry.manager.ownership._ownerForElement(el),
            anchors: Array.from(Citry.events._internal.idToAnchor.keys()),
          };
        }
        """
    )
    assert len(first_probe["calls"]) == 1, first_probe
    page.evaluate("document.querySelector('.events-fill').dispatchEvent(new CustomEvent('magic-send'))")
    page.wait_for_function("window.__fillCalls.length === 2")
    page.evaluate("Citry.events.send(document.querySelector('.events-fill'), 'save', { kind: 'imperative' })")
    page.wait_for_function("window.__fillCalls.length === 3")

    result = page.evaluate(
        """
        () => {
          const sourceId = document.querySelector('html').getAttribute('data-cid').trim().split(' ').at(-1);
          const physicalId = document.querySelector('.events-fill').getAttribute('data-cid').trim().split(' ').at(-1);
          return {
            sourceId,
            physicalId,
            calls: window.__fillCalls.map((call) => ({ instance: call.callerRenderId, args: call.args })),
          };
        }
        """
    )
    assert result["sourceId"] != result["physicalId"]
    assert result["calls"] == [
        {"instance": result["sourceId"], "args": {"kind": "compiled"}},
        {"instance": result["sourceId"], "args": {"kind": "magic"}},
        {"instance": result["physicalId"], "args": {"kind": "imperative"}},
    ]


def test_teleported_fill_keeps_source_scope_and_native_physical_event_path(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = """
          <section class="teleport-card" @click="window.__teleportOrder.push('child')">
            <c-slot />
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <div id="teleport-destination" @click="window.__teleportOrder.push('destination')"></div>
            <main
              id="teleport-source"
              x-data="{ owner: 'parent', sourceOnly: 'S' }"
              @click="window.__teleportOrder.push('source')"
            >
              <c-card>
                <template x-teleport="#teleport-destination">
                  <button
                    class="teleported-fill"
                    x-text="owner + ':' + sourceOnly"
                    @click="window.__teleportEvent = {
                      event: $event, el: $el.className, target: $event.target.className,
                      current: $event.currentTarget.className
                    }; window.__teleportOrder.push('target')"
                  ></button>
                </template>
              </c-card>
            </main>
          </body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate("window.__teleportOrder = []; window.__teleportEvent = null")
    page.wait_for_function("document.querySelector('.teleported-fill')?.textContent === 'parent:S'")
    page.locator(".teleported-fill").click()

    result = page.evaluate(
        """
        () => ({
          order: window.__teleportOrder,
          event: {
            exactType: window.__teleportEvent.event.constructor.name,
            el: window.__teleportEvent.el,
            target: window.__teleportEvent.target,
            current: window.__teleportEvent.current,
          },
          destination: document.querySelector('.teleported-fill').parentElement.id,
          owner: Alpine.evaluate(document.querySelector('.teleported-fill'), 'owner'),
          root: Alpine.evaluate(document.querySelector('.teleported-fill'), '$root.id'),
        })
        """
    )
    assert result == {
        "order": ["target", "destination"],
        "event": {
            "exactType": "PointerEvent",
            "el": "teleported-fill",
            "target": "teleported-fill",
            "current": "teleported-fill",
        },
        "destination": "teleport-destination",
        "owner": "parent",
        "root": "teleport-source",
    }


def test_multi_root_mirrors_keep_one_source_when_the_first_copy_is_removed(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Mirror(Component):
        citry = c
        template = '<section class="mirror-host"><c-slot name="body" /><c-slot name="body" /></section>'

    class Page(Component):
        citry = c
        template = """
          <html><body><main x-data="{ owner: 'parent', count: 0 }">
            <output class="mirror-count" x-text="count"></output>
            <c-mirror>
              <c-fill name="body">
                <button class="mirror-a" x-text="owner" @click="count += 1"></button>
                <button class="mirror-b" x-text="owner" @click="count += 10"></button>
              </c-fill>
            </c-mirror>
          </main></body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelectorAll('.mirror-a').length === 2")
    assert page.locator(".mirror-a").all_inner_texts() == ["parent", "parent"]
    assert page.locator(".mirror-b").all_inner_texts() == ["parent", "parent"]

    page.locator(".mirror-a").nth(0).click()
    page.locator(".mirror-b").nth(1).click()
    page.wait_for_function("document.querySelector('.mirror-count')?.textContent === '11'")
    page.evaluate(
        """
        () => {
          const first = document.querySelectorAll('.mirror-a')[0];
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const firstRegion = Array.from(graph.registry.slotRegions.values())[0];
          const physical = graph.registry.physicalRegions.get(firstRegion.key);
          for (let node = physical.start; node;) {
            const next = node.nextSibling;
            node.remove();
            if (node === physical.end) break;
            node = next;
          }
          window.__removedMirrorWasFirst = !first.isConnected;
        }
        """
    )
    page.wait_for_function("document.querySelectorAll('.mirror-a').length === 1")
    assert page.evaluate("window.__removedMirrorWasFirst") is True
    assert page.locator(".mirror-a").inner_text() == "parent"
    page.locator(".mirror-a").click()
    page.wait_for_function("document.querySelector('.mirror-count')?.textContent === '12'")


def test_detached_python_fill_gets_an_empty_base_and_can_define_only_local_data(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = """
          <section class="python-card" x-data="{ receiverOnly: 'secret' }">
            <c-slot />
          </section>
        """

        class Events:
            def noop(self):
                return None

    detached = Markup(
        '<span class="python-fill" '
        "x-data=\"{ localOnly: 'local' }\" "
        "x-text=\"localOnly + ':' + typeof receiverOnly\"></span>"
    )

    class Page(Component):
        citry = c
        template = "<html><body>{{ card }}</body></html>"

        def template_data(self, kwargs, slots):
            return {"card": Card(slots={"default": detached})}

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.python-fill')?.textContent === 'local:undefined'")
    assert page.locator(".python-fill").inner_text() == "local:undefined"


def test_two_same_class_call_sites_keep_distinct_local_source_stacks(page: Any, serve_live: Any) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<section class="call-card"><c-slot /></section>'

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <div x-data="{ callValue: 'first' }">
              <c-card><span class="call-fill" x-text="callValue"></span></c-card>
            </div>
            <div x-data="{ callValue: 'second' }">
              <c-card><span class="call-fill" x-text="callValue"></span></c-card>
            </div>
          </body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelectorAll('.call-fill')[1]?.textContent === 'second'")
    assert page.locator(".call-fill").all_inner_texts() == ["first", "second"]


def test_runtime_dynamic_component_keeps_the_authored_call_site_as_fill_source(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<section class="dynamic-card"><c-slot /></section>'

    class Page(Component):
        citry = c
        template = """
          <html><body><main x-data="{ owner: 'dynamic-parent' }">
            <c-component c-is="target">
              <span class="dynamic-fill" x-text="owner"></span>
            </c-component>
          </main></body></html>
        """

        def template_data(self, kwargs, slots):
            return {"target": Card}

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.dynamic-fill')?.textContent === 'dynamic-parent'")

    result = page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const fill = Array.from(graph.registry.fills.values()).find((candidate) => candidate.kind === 'implicit');
          const invocation = Array.from(graph.registry.nestedComponents.values()).find(
            (candidate) => candidate.graphId === fill.graphId
              && candidate.invocationId === fill.sourceInvocationId
          );
          return {
            text: document.querySelector('.dynamic-fill').textContent,
            sourceInvocation: fill.sourceInvocationId,
            sourceTarget: invocation.targetRenderId,
            targetClass: invocation.targetClassId,
          };
        }
        """
    )
    assert result["text"] == "dynamic-parent"
    assert result["sourceInvocation"] is not None
    assert result["sourceTarget"]
    assert result["targetClass"] == Card.class_id


def test_rootless_supplied_fill_keeps_caps_without_synthesizing_an_element(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class TextOutlet(Component):
        citry = c
        js = "$component(({ scope }) => { scope.receiverOnly = 'secret'; })"
        template = "<c-slot />"

    class Page(Component):
        citry = c
        template = """
          <html><body><main id="rootless-source" x-data="{ owner: 'parent' }">
            <c-text-outlet>plain supplied text</c-text-outlet>
          </main></body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    result = page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const fill = Array.from(graph.registry.fills.values()).find((candidate) => candidate.kind === 'implicit');
          const slotRegions = Array.from(graph.registry.slotRegions.values()).filter(
            (candidate) => candidate.fillId === fill.fillId
          );
          const physical = graph.registry.physicalRegions.get(slotRegions[0].key);
          const nodes = [];
          for (let node = physical.start.nextSibling; node && node !== physical.end; node = node.nextSibling) {
            nodes.push({ type: node.nodeType, text: node.textContent });
          }
          return {
            elements: nodes.filter((node) => node.type === Node.ELEMENT_NODE).length,
            text: nodes.map((node) => node.text).join('').trim(),
            active: graph.registry.rangeGroups.get(fill.key).active,
          };
        }
        """
    )
    assert result == {"elements": 0, "text": "plain supplied text", "active": True}


def test_same_revision_fill_region_morph_reprojects_source_and_final_removal_retires_group(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<section class="morph-card"><c-slot /></section>'

    class Page(Component):
        citry = c
        template = """
          <html><body><main x-data="{ owner: 'parent', count: 0 }">
            <output class="morph-count" x-text="count"></output>
            <c-card><button class="morph-fill" @click="count += 1" x-text="owner"></button></c-card>
          </main></body></html>
        """

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.morph-fill')?.textContent === 'parent'")

    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const fill = Array.from(graph.registry.fills.values()).find((candidate) => candidate.kind === 'implicit');
          const region = Array.from(graph.registry.slotRegions.values()).find(
            (candidate) => candidate.fillId === fill.fillId
          );
          window.__morphFillGraph = { revision, fillKey: fill.key, regionKey: region.key };
          Citry.manager.ownership._morphRange(
            revision,
            region.key,
            `<button class="morph-fill" @click="count += 10" x-text="owner + '-morphed'"></button>`,
          );
        }
        """
    )
    page.wait_for_function("document.querySelector('.morph-fill')?.textContent === 'parent-morphed'")
    page.locator(".morph-fill").click()
    page.wait_for_function("document.querySelector('.morph-count')?.textContent === '10'")

    result = page.evaluate(
        """
        () => {
          const record = window.__morphFillGraph;
          const graph = Citry.manager.ownership.get(record.revision);
          const physical = graph.registry.physicalRegions.get(record.regionKey);
          const removed = document.querySelector('.morph-fill');
          for (let node = physical.start; node;) {
            const next = node.nextSibling;
            node.remove();
            if (node === physical.end) break;
            node = next;
          }
          window.__removedMorphFill = removed;
          return true;
        }
        """
    )
    assert result is True
    page.wait_for_function(
        "Citry.manager.ownership.get(window.__morphFillGraph.revision)"
        ".registry.rangeGroups.get(window.__morphFillGraph.fillKey).active === false"
    )
    assert page.evaluate("Citry.manager.ownership._ownerForElement(window.__removedMorphFill)") is None


def test_independent_fragment_revision_cannot_overwrite_document_fill_routes(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<section class="revision-card"><c-slot /></section>'

    class Document(Component):
        citry = c
        template = """
          <html><body><main x-data="{ owner: 'document' }">
            <c-card><span class="document-fill" x-text="owner"></span></c-card>
            <div id="fragment-target"></div>
          </main></body></html>
        """

    class Fragment(Component):
        citry = c
        template = """
          <aside x-data="{ owner: 'fragment' }">
            <c-card><span class="fragment-fill" x-text="owner"></span></c-card>
          </aside>
        """

    document_html = Document().render().serialize()
    fragment_html = Fragment().render().serialize(deps_strategy="fragment")
    base = serve_live(c, document_html, fragment_html)
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelector('.document-fill')?.textContent === 'document'")

    html = page.evaluate("async () => await fetch('/fragment').then((response) => response.text())")
    page.evaluate(
        """
        (html) => {
          document.getElementById('fragment-target').innerHTML = html;
        }
        """,
        html,
    )
    page.wait_for_function("document.querySelector('.fragment-fill')?.textContent === 'fragment'")

    assert page.locator(".document-fill").inner_text() == "document"
    assert page.locator(".fragment-fill").inner_text() == "fragment"
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 2
    tokens = page.locator("[x-citry-fill-source]").evaluate_all(
        "elements => elements.map((element) => element.getAttribute('x-citry-fill-source'))"
    )
    assert len(tokens) == 2
    assert len(set(tokens)) == 2


def test_teleported_fill_source_death_cancels_declarative_sends_but_keeps_public_send_physical(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry()
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        js = "$component(({ scope }) => { scope.childOnly = 'child'; })"
        template = '<section><div id="retired-teleport-destination"></div><c-slot /></section>'

        class Events:
            def save(self):
                return None

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <main id="retired-fill-source" x-data="{ owner: 'parent' }">
              <button class="queue-blocker" @c-click="save({ kind: 'blocker' })">block</button>
              <c-card>
                <template x-teleport="#retired-teleport-destination">
                  <button
                    id="teleported-retired"
                    @c-click="save({ kind: 'queued' })"
                    @magic-send="$sendEvent('save', { kind: 'magic' })"
                    x-init="window.__retiredFillSend = $sendEvent"
                    x-text="owner"
                  ></button>
                </template>
              </c-card>
            </main>
          </body></html>
        """

        class Events:
            def save(self):
                return None

    base = serve_live(c, Page().render().serialize(), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.getElementById('teleported-retired')?.textContent === 'parent'")
    page.evaluate(
        """
        () => {
          window.__retiredFillCalls = [];
          window.__releaseRetiredBlocker = null;
          Citry.events._internal.setTransport((call) => {
            window.__retiredFillCalls.push(call);
            if (window.__retiredFillCalls.length === 1) {
              return new Promise((resolve) => { window.__releaseRetiredBlocker = resolve; });
            }
            return Promise.resolve({ ok: true, actions: [] });
          });
        }
        """
    )

    page.locator(".queue-blocker").click()
    page.wait_for_function("window.__retiredFillCalls.length === 1 && !!window.__releaseRetiredBlocker")
    page.locator("#teleported-retired").click()
    page.evaluate("document.getElementById('teleported-retired').dispatchEvent(new CustomEvent('magic-send'))")
    physical_id = (
        page.evaluate("document.getElementById('teleported-retired').closest('[data-cid]').getAttribute('data-cid')")
        .strip()
        .split()[-1]
    )
    page.evaluate(
        "() => { Citry.events.send(document.getElementById('teleported-retired'), 'save', "
        "{ kind: 'imperative' }).catch(() => {}); }"
    )
    assert page.evaluate("window.__retiredFillCalls.length") == 1

    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const fill = Array.from(graph.registry.fills.values()).find(
            (candidate) => candidate.kind === 'implicit'
          );
          const region = Array.from(graph.registry.slotRegions.values()).find(
            (candidate) => candidate.fillId === fill.fillId
          );
          const physical = graph.registry.physicalRegions.get(region.key);
          physical.start.remove();
        }
        """
    )
    page.wait_for_timeout(100)
    retirement_probe = page.evaluate(
        """
        () => {
          const el = document.getElementById('teleported-retired');
          return {
            exists: !!el,
            owner: el ? Citry.manager.ownership._ownerForElement(el) : 'missing',
            marker: el?.getAttribute('x-citry-fill-source') ?? null,
          };
        }
        """
    )
    assert retirement_probe == {"exists": True, "owner": None, "marker": None}
    assert page.locator("#teleported-retired").count() == 1

    isolated = page.evaluate(
        """
        () => {
          const el = document.getElementById('teleported-retired');
          return {
            data: Alpine.evaluate(el, "typeof owner + ':' + typeof childOnly"),
            root: Alpine.evaluate(el, '$root.id'),
          };
        }
        """
    )
    assert isolated["data"] == "undefined:undefined"
    assert isolated["root"] != "retired-fill-source"
    page.evaluate("window.__retiredFillSend('save', { kind: 'stale-closure' }).catch(() => {})")
    assert page.evaluate("window.__retiredFillCalls.length") == 1

    page.evaluate("window.__releaseRetiredBlocker({ ok: true, actions: [] })")
    page.wait_for_function("window.__retiredFillCalls.length === 2")
    imperative_call = page.evaluate(
        """
            () => ({
              instance: window.__retiredFillCalls[1].callerRenderId,
              args: window.__retiredFillCalls[1].args,
            })
        """
    )
    assert imperative_call == {"instance": physical_id, "args": {"kind": "imperative"}}
    page.locator("#teleported-retired").click()
    page.wait_for_timeout(100)
    assert page.evaluate("window.__retiredFillCalls.length") == 2
