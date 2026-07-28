"""A9 structural Alpine and dynamic client identity acceptance."""

from __future__ import annotations

import re
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "a9-structural-e2e"
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def _fragment(component: Component) -> str:
    return component.render().serialize(deps_strategy="fragment")


def _goto(page: Any, serve_live: Any, citry: Citry, html: str) -> list[str]:
    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    return messages


def test_nested_structural_fill_churn_keeps_source_identity_and_cleans_native_resources(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        template = '<section class="stress-card"><c-slot /></section>'

    class Page(Component):
        citry = c
        js = """
          window.__a9Structural = {
            active: 0, cleanups: 0, effectRuns: 0, hits: 0, inits: 0,
          };
          Citry.alpine.beforeStart((Alpine) => {
            Alpine.directive('a9-probe', (el, { expression }, { cleanup, effect, evaluateLater }) => {
              const state = window.__a9Structural;
              const evaluate = evaluateLater(expression);
              const hit = () => { state.hits += 1; };
              state.active += 1;
              state.inits += 1;
              el.addEventListener('a9-probe', hit);
              effect(() => evaluate((value) => {
                state.effectRuns += 1;
                el.dataset.probe = String(value);
              }));
              cleanup(() => {
                state.active -= 1;
                state.cleanups += 1;
                el.removeEventListener('a9-probe', hit);
              });
            });
          });
          $component(() => {});
        """
        template = """
          <html><body>
            <div id="stress-moved"></div>
            <div id="stress-destination"></div>
            <main
              id="stress-source"
              x-data="{
                owner: 'source',
                groups: [
                  { id: 'a', label: 'A', show: true,
                    items: [{ id: 'a1', label: 'A1' }, { id: 'a2', label: 'A2' }] },
                  { id: 'b', label: 'B', show: true,
                    items: [{ id: 'b1', label: 'B1' }, { id: 'b2', label: 'B2' }] }
                ]
              }"
            >
              <c-card>
                <template x-for="group in groups" :key="group.id">
                  <article
                    class="stress-group"
                    :data-key="group.id"
                    x-id="['row']"
                    x-a9-probe="group.label"
                  >
                    <input
                      class="stress-model"
                      :data-key="group.id"
                      :aria-describedby="$id('row')"
                      x-model="group.label"
                      x-ref="rowRef"
                    >
                    <output class="stress-id" :id="$id('row')" x-text="group.label"></output>
                    <span class="stress-local" x-data="{ local: 'local' }" x-text="local + ':' + owner"></span>
                    <template x-if="group.show">
                      <span class="stress-if" :data-key="group.id" x-a9-probe="group.label"></span>
                    </template>
                    <template x-for="item in group.items" :key="item.id">
                      <button
                        class="stress-item"
                        :data-key="item.id"
                        x-a9-probe="item.label"
                        x-text="group.label + ':' + item.label"
                      ></button>
                    </template>
                    <template x-teleport="#stress-destination">
                      <button
                        class="stress-teleport"
                        :data-key="group.id"
                        x-a9-probe="group.label"
                        x-text="owner + ':' + group.label"
                      ></button>
                    </template>
                  </article>
                </template>
              </c-card>
            </main>
          </body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    page.wait_for_function("document.querySelectorAll('.stress-item').length === 4")
    page.wait_for_function("document.querySelectorAll('.stress-teleport').length === 2")

    result = page.evaluate(
        """
        async () => {
          const pause = () => new Promise((resolve) => setTimeout(resolve, 30));
          const source = document.getElementById('stress-source');
          const ownership = Citry.manager.ownership;
          const initialAnchors = ownership.anchors().length;
          const group = (key) => document.querySelector(`.stress-group[data-key="${key}"]`);
          const item = (key) => document.querySelector(`.stress-item[data-key="${key}"]`);
          const rowId = (key) => group(key).querySelector('.stress-id').id;
          const before = {
            a: group('a'), b: group('b'), a1: item('a1'), a2: item('a2'),
            aId: rowId('a'), bId: rowId('b'),
          };
          const refBefore = Alpine.evaluate(source, '$refs.rowRef?.dataset.key ?? null');
          const initialActive = window.__a9Structural.active;

          Alpine.evaluate(source, 'groups.reverse()');
          Alpine.evaluate(source, 'groups.find((group) => group.id === "a").items.reverse()');
          await pause();
          const keyedReuse =
            group('a') === before.a && group('b') === before.b &&
            item('a1') === before.a1 && item('a2') === before.a2;
          const idsStable = rowId('a') === before.aId && rowId('b') === before.bId;

          const input = group('a').querySelector('.stress-model');
          input.value = 'A*';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          await pause();
          const modelUpdated =
            group('a').querySelector('.stress-id').textContent === 'A*' &&
            document.querySelector('.stress-teleport[data-key="a"]').textContent === 'source:A*';

          Alpine.evaluate(source, `
            const target = groups.find((group) => group.id === 'a');
            target.show = false;
          `);
          await pause();
          Alpine.evaluate(source, `groups.find((group) => group.id === 'a').show = true`);
          await pause();
          Alpine.evaluate(source, `groups.find((group) => group.id === 'a').show = false`);
          await pause();
          Alpine.evaluate(source, `groups.find((group) => group.id === 'a').show = true`);
          await pause();

          const removedGroup = group('b');
          const removedNodes = [
            removedGroup,
            ...removedGroup.querySelectorAll('[x-a9-probe]'),
            document.querySelector('.stress-teleport[data-key="b"]'),
          ];
          window.__a9RemovedGroup = Alpine.evaluate(
            source,
            `groups.find((group) => group.id === 'b')`,
          );
          Alpine.evaluate(source, `groups.splice(groups.findIndex((group) => group.id === 'b'), 1)`);
          await pause();
          const refAfterRemoval = Alpine.evaluate(source, '$refs.rowRef?.dataset.key ?? null');
          const effectsAfterRemoval = window.__a9Structural.effectRuns;
          const hitsAfterRemoval = window.__a9Structural.hits;
          window.__a9RemovedGroup.label = 'retired';
          removedNodes.forEach((node) => node?.dispatchEvent(new CustomEvent('a9-probe')));
          await pause();
          const retiredStayedQuiet =
            window.__a9Structural.effectRuns === effectsAfterRemoval &&
            window.__a9Structural.hits === hitsAfterRemoval;
          const removedRouteGone = ownership._ownerForElement(removedGroup) === null;

          Alpine.evaluate(source, `groups.push({
            id: 'b', label: 'B2', show: true,
            items: [{ id: 'b1', label: 'B1' }, { id: 'b2', label: 'B2' }]
          })`);
          await pause();
          const recreatedFresh = group('b') !== before.b && rowId('b') !== before.bId;
          const refAfterRecreate = Alpine.evaluate(source, '$refs.rowRef?.dataset.key ?? null');

          document.getElementById('stress-moved').append(document.getElementById('stress-destination'));
          await pause();
          const teleported = document.querySelector('.stress-teleport[data-key="a"]');
          const teleportKeptSource =
            teleported.parentElement.id === 'stress-destination' &&
            Alpine.evaluate(teleported, 'owner') === 'source' &&
            Alpine.evaluate(teleported, '$root.id') === 'stress-source';

          return {
            activeBalanced: window.__a9Structural.active === initialActive,
            anchorsStable: ownership.anchors().length === initialAnchors,
            cleanupBalanced:
              window.__a9Structural.cleanups === window.__a9Structural.inits - window.__a9Structural.active,
            idsDistinct: before.aId !== before.bId,
            idsStable,
            keyedReuse,
            localData: group('a').querySelector('.stress-local').textContent,
            modelUpdated,
            recreatedFresh,
            refAfterRecreate,
            refAfterRemoval,
            refBefore,
            removedRouteGone,
            retiredStayedQuiet,
            revisionCount: ownership.revisions().length,
            teleportKeptSource,
          };
        }
        """
    )

    assert result == {
        "activeBalanced": True,
        "anchorsStable": True,
        "cleanupBalanced": True,
        "idsDistinct": True,
        "idsStable": True,
        "keyedReuse": True,
        "localData": "local:source",
        "modelUpdated": True,
        "recreatedFresh": True,
        "refAfterRecreate": "b",
        "refAfterRemoval": None,
        "refBefore": "b",
        "removedRouteGone": True,
        "retiredStayedQuiet": True,
        "revisionCount": 1,
        "teleportKeptSource": True,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_native_structural_clone_of_server_component_fails_before_graph_activation(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = "$component(() => { window.__a9ClonedChildRuns = (window.__a9ClonedChildRuns || 0) + 1; });"
        template = '<button class="cloned-server-child">child</button>'

    class Page(Component):
        citry = c
        template = """
          <html><body><main x-data="{ items: [1, 2] }">
            <template x-for="item in items"><c-child /></template>
          </main></body></html>
        """

    errors: list[str] = []
    messages: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_timeout(150)

    combined = errors + messages
    assert any(
        "native x-for cannot clone a server-rendered client-active Citry component" in message
        and "server <c-for>" in message
        and "browser blueprint" in message
        for message in combined
    ), combined
    assert page.evaluate("window.__a9ClonedChildRuns || 0") == 0
    assert page.evaluate("Citry.manager.ownership.revisions().length") == 0
    assert page.evaluate("Citry.manager.ownership.anchors().length") == 0


def test_compatible_morph_retires_old_component_tag_client_bindings_and_prunes_revisions(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, required: true } },
            init: ({ props, effect }) => {
              effect(() => { window.__a9LatestProp = props.value; });
            },
          });
        """
        template = '<button class="client-binding-child">child</button>'

    class Parent(Component):
        citry = c

        class Events:
            def record(self):
                return None

            def refresh(self):
                return None

        template = """
          <section class="client-binding-parent" x-data="{ supplied: 1 }">
            <c-child
              #c-key="'stable'"
              $c-props="{
                value: (window.__a9SupplierReads = (window.__a9SupplierReads || 0) + 1, supplied)
              }"
              @click="window.__a9AlpineHits = (window.__a9AlpineHits || 0) + 1"
              @c-click="record()"
            />
          </section>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    fragments = [_fragment(Parent()) for _ in range(3)]
    result = page.evaluate(
        """
        async ([fragments]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const anchor = internal.getAnchor(document.querySelector('.client-binding-parent').getAttribute('data-cid'));
          window.__a9BoundaryCalls = [];
          internal.setTransport((call) => {
            window.__a9BoundaryCalls.push(call);
            return Promise.resolve({ ok: true, actions: [] });
          });
          for (const html of fragments) {
            const epoch = anchor.epoch + 1;
            anchor.epoch = epoch;
            await internal.applyResult(
              {
                ok: true,
                epoch,
                actions: [{
                  action: 'render',
                  target: 'render:' + anchor.componentId,
                  swap: 'morph',
                  html,
                }],
              },
              { anchor, instance: anchor.componentId, event: 'refresh' },
            );
          }
          await new Promise((resolve) => setTimeout(resolve, 30));
          const beforeReads = window.__a9SupplierReads;
          Alpine.evaluate(document.querySelector('.client-binding-parent'), 'supplied = 7');
          await new Promise((resolve) => setTimeout(resolve, 30));
          document.querySelector('.client-binding-child').click();
          await new Promise((resolve) => setTimeout(resolve, 30));
          return {
            alpineHits: window.__a9AlpineHits || 0,
            latestProp: window.__a9LatestProp,
            revisionCount: ownership.revisions().length,
            sends: window.__a9BoundaryCalls.length,
            supplierDelta: window.__a9SupplierReads - beforeReads,
          };
        }
        """,
        [fragments],
    )

    assert result == {
        "alpineHits": 1,
        "latestProp": 7,
        "revisionCount": 2,
        "sends": 1,
        "supplierDelta": 1,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_child_only_self_render_preserves_caller_boundary_without_a_successor_invocation(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, required: true } },
            init: ({ props, effect }) => {
              effect(() => { window.__a9ChildOnlyProp = props.value; });
            },
          });
        """

        class Events:
            def refresh(self):
                return None

        template = '<button class="child-only-target">child</button>'

    class Parent(Component):
        citry = c
        template = """
          <section class="child-only-source" x-data="{ supplied: 1 }">
            <c-child
              $c-props="{ value: supplied }"
              @click="window.__a9ChildOnlyHits = (window.__a9ChildOnlyHits || 0) + 1"
            />
          </section>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Child())
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const target = document.querySelector('.child-only-target');
          const oldId = target.getAttribute('data-cid');
          const anchor = internal.getAnchor(oldId);
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: 'render', target: 'render:' + oldId, swap: 'morph', html }],
            },
            { anchor, instance: oldId, event: 'refresh' },
          );
          Alpine.evaluate(document.querySelector('.child-only-source'), 'supplied = 5');
          await new Promise((resolve) => setTimeout(resolve, 30));
          document.querySelector('.child-only-target').click();
          await new Promise((resolve) => setTimeout(resolve, 30));
          return {
            hits: window.__a9ChildOnlyHits || 0,
            prop: window.__a9ChildOnlyProp,
            revisions: ownership.revisions().length,
          };
        }
        """,
        [fresh],
    )

    assert result == {"hits": 1, "prop": 5, "revisions": 2}
    assert not [message for message in messages if message.startswith("error:")]


@pytest.mark.parametrize("next_mode", ["none", "handler"])
def test_compatible_caller_render_can_remove_props_and_its_last_component_tag_client_binding(
    page: Any,
    serve_live: Any,
    next_mode: str,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, default: 0 } },
            init: ({ props, effect }) => {
              effect(() => { window.__a9RemovedClientBindingProp = props.value; });
            },
          });
        """
        template = '<button class="removed-client-binding-child">child</button>'

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <section class="removed-client-binding-parent" x-data="{ supplied: 1 }">
            <c-child
              #c-key="'stable'"
              $c-props="{
                value: (window.__a9RemovedBindingReads = (window.__a9RemovedBindingReads || 0) + 1, supplied)
              }"
              @click="window.__a9RemovedOldHits = (window.__a9RemovedOldHits || 0) + 1"
            />
          </section>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    Parent.template = (
        """
          <section class="removed-client-binding-parent" x-data="{ supplied: 1 }">
            <c-child
              #c-key="'stable'"
              @click="window.__a9RemovedNewHits = (window.__a9RemovedNewHits || 0) + 1"
            />
          </section>
        """
        if next_mode == "handler"
        else """
          <section class="removed-client-binding-parent" x-data="{ supplied: 1 }">
            <c-child #c-key="'stable'" />
          </section>
        """
    )
    Parent.reset_template()
    fresh = _fragment(Parent())
    result = page.evaluate(
        """
        async ([html, nextMode]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const parent = document.querySelector('.removed-client-binding-parent');
          const oldId = parent.getAttribute('data-cid');
          const anchor = internal.getAnchor(oldId);
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: 'render', target: 'render:' + oldId, swap: 'morph', html }],
            },
            { anchor, instance: oldId, event: 'refresh' },
          );
          await new Promise((resolve) => setTimeout(resolve, 30));
          const reads = window.__a9RemovedBindingReads;
          Alpine.evaluate(document.querySelector('.removed-client-binding-parent'), 'supplied = 9');
          await new Promise((resolve) => setTimeout(resolve, 30));
          document.querySelector('.removed-client-binding-child').click();
          await new Promise((resolve) => setTimeout(resolve, 30));
          return {
            newHits: window.__a9RemovedNewHits || 0,
            oldHits: window.__a9RemovedOldHits || 0,
            prop: window.__a9RemovedClientBindingProp,
            readsAfterRemoval: window.__a9RemovedBindingReads - reads,
            revisionCount: ownership.revisions().length,
            wantedNewHits: nextMode === 'handler' ? 1 : 0,
          };
        }
        """,
        [fresh, next_mode],
    )
    assert result == {
        "newHits": result["wantedNewHits"],
        "oldHits": 0,
        "prop": 0,
        "readsAfterRemoval": 0,
        "revisionCount": 2,
        "wantedNewHits": result["wantedNewHits"],
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_compatible_caller_render_can_add_props_during_physical_root_replacement(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component({
            props: { value: { type: Number, default: 0 } },
            init: ({ props, effect }) => {
              effect(() => { window.__a9AddedClientBindingProp = props.value; });
            },
          });
        """
        template = '<button class="added-client-binding-child">child</button>'

    class Parent(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <section class="added-client-binding-parent" x-data="{ supplied: 4 }">
            <c-child
              #c-key="'stable'"
              @click="window.__a9AddedOldHits = (window.__a9AddedOldHits || 0) + 1"
            />
          </section>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))

    Child.template = (
        '<div class="added-client-binding-child" '
        'x-init="window.__a9AddedRootInits = (window.__a9AddedRootInits || 0) + 1">child</div>'
    )
    Child.reset_template()
    Parent.template = """
      <section class="added-client-binding-parent" x-data="{ supplied: 4 }">
        <c-child
          #c-key="'stable'"
          $c-props="{
            value: (window.__a9AddedClientBindingReads = (window.__a9AddedClientBindingReads || 0) + 1, supplied)
          }"
        />
      </section>
    """
    Parent.reset_template()
    with_props = _fragment(Parent())

    Child.template = '<button class="added-client-binding-child">child</button>'
    Child.reset_template()
    Parent.template = """
      <section class="added-client-binding-parent" x-data="{ supplied: 4 }">
        <c-child
          #c-key="'stable'"
          @click="window.__a9AddedNewHits = (window.__a9AddedNewHits || 0) + 1"
        />
      </section>
    """
    Parent.reset_template()
    without_props = _fragment(Parent())

    result = page.evaluate(
        """
        async ([withProps, withoutProps]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const parent = document.querySelector('.added-client-binding-parent');
          const anchor = internal.getAnchor(parent.getAttribute('data-cid'));
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{
                action: 'render', target: 'render:' + anchor.componentId,
                swap: 'morph', html: withProps,
              }],
            },
            { anchor, instance: anchor.componentId, event: 'refresh' },
          );
          await new Promise((resolve) => setTimeout(resolve, 30));
          const first = {
            inits: window.__a9AddedRootInits || 0,
            prop: window.__a9AddedClientBindingProp,
            root: document.querySelector('.added-client-binding-child').tagName,
          };
          Alpine.evaluate(document.querySelector('.added-client-binding-parent'), 'supplied = 7');
          await new Promise((resolve) => setTimeout(resolve, 30));
          const reactive = window.__a9AddedClientBindingProp;

          anchor.epoch = 2;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{
                action: 'render', target: 'render:' + anchor.componentId,
                swap: 'morph', html: withoutProps,
              }],
            },
            { anchor, instance: anchor.componentId, event: 'refresh' },
          );
          await new Promise((resolve) => setTimeout(resolve, 30));
          const reads = window.__a9AddedClientBindingReads;
          Alpine.evaluate(document.querySelector('.added-client-binding-parent'), 'supplied = 9');
          await new Promise((resolve) => setTimeout(resolve, 30));
          document.querySelector('.added-client-binding-child').click();
          await new Promise((resolve) => setTimeout(resolve, 30));
          return {
            first,
            newHits: window.__a9AddedNewHits || 0,
            oldHits: window.__a9AddedOldHits || 0,
            propAfterRemoval: window.__a9AddedClientBindingProp,
            reactive,
            readsAfterRemoval: window.__a9AddedClientBindingReads - reads,
            revisionCount: ownership.revisions().length,
          };
        }
        """,
        [with_props, without_props],
    )

    assert result == {
        "first": {"inits": 1, "prop": 4, "root": "DIV"},
        "newHits": 1,
        "oldHits": 0,
        "propAfterRemoval": 0,
        "reactive": 7,
        "readsAfterRemoval": 0,
        "revisionCount": 2,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_citry_enter_leave_handlers_treat_multi_root_component_as_one_union(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <button class="union-root-a">a</button>
          <button class="union-root-b">b</button>
        """

    class Parent(Component):
        citry = c

        class Events:
            def record(self):
                return None

        template = """
          <main><button class="union-gap">gap</button>
            <c-child
              @c-mouseenter.once="record({ kind: 'mouseenter', related: $event.relatedTarget.className })"
              @c-mouseleave.once="record({ kind: 'mouseleave', related: $event.relatedTarget.className })"
              @c-pointerenter.once="record({ kind: 'pointerenter', related: $event.relatedTarget.className })"
              @c-pointerleave.once="record({ kind: 'pointerleave', related: $event.relatedTarget.className })"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    result = page.evaluate(
        """
        async () => {
          const calls = [];
          Citry.events._internal.setTransport((call) => {
            calls.push(call.args);
            return Promise.resolve({ ok: true, actions: [] });
          });
          const a = document.querySelector('.union-root-a');
          const b = document.querySelector('.union-root-b');
          const gap = document.querySelector('.union-gap');
          a.dispatchEvent(new MouseEvent('mouseenter', { relatedTarget: b }));
          a.dispatchEvent(new MouseEvent('mouseenter', { relatedTarget: gap }));
          a.dispatchEvent(new MouseEvent('mouseleave', { relatedTarget: b }));
          a.dispatchEvent(new MouseEvent('mouseleave', { relatedTarget: gap }));
          a.dispatchEvent(new PointerEvent('pointerenter', { relatedTarget: b }));
          a.dispatchEvent(new PointerEvent('pointerenter', { relatedTarget: gap }));
          a.dispatchEvent(new PointerEvent('pointerleave', { relatedTarget: b }));
          a.dispatchEvent(new PointerEvent('pointerleave', { relatedTarget: gap }));
          await new Promise((resolve) => setTimeout(resolve, 30));
          return calls;
        }
        """
    )

    assert result == [
        {"kind": "mouseenter", "related": "union-gap"},
        {"kind": "mouseleave", "related": "union-gap"},
        {"kind": "pointerenter", "related": "union-gap"},
        {"kind": "pointerleave", "related": "union-gap"},
    ]
    assert not [message for message in messages if message.startswith("error:")]


def test_citry_once_detaches_native_listeners_and_does_not_attach_to_later_roots(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        template = """
          <button class="once-citry-root once-root-a">a</button>
          <button class="once-citry-root once-root-b">b</button>
        """

    class Parent(Component):
        citry = c
        js = """
          window.__a9OnceListeners = { adds: 0, removes: 0 };
          if (!window.__a9OncePatched) {
            window.__a9OncePatched = true;
            const add = EventTarget.prototype.addEventListener;
            const remove = EventTarget.prototype.removeEventListener;
            EventTarget.prototype.addEventListener = function (type, listener, options) {
              if (type === 'click' && this instanceof Element && this.classList.contains('once-citry-root')) {
                window.__a9OnceListeners.adds += 1;
              }
              return add.call(this, type, listener, options);
            };
            EventTarget.prototype.removeEventListener = function (type, listener, options) {
              if (type === 'click' && this instanceof Element && this.classList.contains('once-citry-root')) {
                window.__a9OnceListeners.removes += 1;
              }
              return remove.call(this, type, listener, options);
            };
          }
          $component(() => {});
        """

        class Events:
            def record(self):
                return None

        template = '<main><c-child @c-click.once="record()" /></main>'

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    result = page.evaluate(
        """
        async () => {
          const calls = [];
          Citry.events._internal.setTransport((call) => {
            calls.push(call);
            return Promise.resolve({ ok: true, actions: [] });
          });
          const a = document.querySelector('.once-root-a');
          const b = document.querySelector('.once-root-b');
          const initialAdds = window.__a9OnceListeners.adds;
          a.click();
          await new Promise((resolve) => setTimeout(resolve, 30));
          const afterOnce = { ...window.__a9OnceListeners };
          const later = b.cloneNode(true);
          later.classList.remove('once-root-b');
          later.classList.add('once-root-c');
          a.remove();
          b.after(later);
          await new Promise((resolve) => setTimeout(resolve, 30));
          later.click();
          await new Promise((resolve) => setTimeout(resolve, 30));
          return {
            afterOnce,
            calls: calls.length,
            final: window.__a9OnceListeners,
            initialAdds,
          };
        }
        """
    )

    assert result == {
        "afterOnce": {"adds": 2, "removes": 2},
        "calls": 1,
        "final": {"adds": 2, "removes": 2},
        "initialAdds": 2,
    }
    assert not [message for message in messages if message.startswith("error:")]


def test_render_adoption_rejects_structural_server_component_clone_before_provisional_activation(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = "$component(() => { window.__a9AdoptChildRuns = (window.__a9AdoptChildRuns || 0) + 1; });"
        template = '<button class="adopt-clone-child">child</button>'

    class Shell(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <section class="adopt-clone-shell" x-data="{ items: [1, 2] }"><c-child /></section>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-shell /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Shell())
    fresh, replacements = re.subn(
        r'(<button class="adopt-clone-child"[^>]*>child</button>)',
        r'<template x-for="item in items">\1</template>',
        fresh,
        count=1,
    )
    assert replacements == 1
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const shell = document.querySelector('.adopt-clone-shell');
          const oldId = shell.getAttribute('data-cid');
          const anchor = internal.getAnchor(oldId);
          const before = {
            anchors: ownership.anchors().length,
            childRuns: window.__a9AdoptChildRuns,
            revisions: ownership.revisions().length,
          };
          anchor.epoch = 1;
          let error = '';
          try {
            await internal.applyResult(
              {
                ok: true,
                sendSequence: 1,
                actions: [{ action: 'render', target: 'render:' + oldId, swap: 'morph', html }],
              },
              { anchor, instance: oldId, event: 'refresh' },
            );
          } catch (caught) {
            error = String(caught?.message || caught);
          }
          await new Promise((resolve) => setTimeout(resolve, 30));
          return {
            anchorStayed: internal.getAnchor(oldId) === anchor,
            anchorsStable: ownership.anchors().length === before.anchors,
            callbackStable: window.__a9AdoptChildRuns === before.childRuns,
            error,
            revisionsStable: ownership.revisions().length === before.revisions,
            rootStayed: document.querySelector('.adopt-clone-shell') === shell,
          };
        }
        """,
        [fresh],
    )

    assert result["anchorStayed"] is True
    assert result["anchorsStable"] is True
    assert result["callbackStable"] is True
    assert result["revisionsStable"] is True
    assert result["rootStayed"] is True
    assert "native x-for cannot clone a server-rendered client-active Citry component" in result["error"]
    assert "browser blueprint" in result["error"]
    assert not [message for message in messages if message.startswith("error:")]


def test_transitioning_root_morph_forces_fresh_ownership_markers_without_resetting_alpine(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Card(Component):
        citry = c
        js = """
          $component(({ els, scope }) => {
            window.__a9TransitionCalls = window.__a9TransitionCalls || [];
            window.__a9TransitionCalls.push({ els, scope });
          });
        """

        class Events:
            def refresh(self):
                return None

        template = """
          <section
            class="transition-card"
            x-data="{ shown: true, draft: 'initial' }"
            x-show="shown"
            x-transition.duration.200ms
            x-ref="transitionRoot"
          >
            <input class="transition-draft" x-model="draft">
            <span class="transition-label">{{ label }}</span>
          </section>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Page(Component):
        citry = c
        template = "<html><body><c-card c-label=\"'one'\" /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Card(label="two"))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const root = document.querySelector('.transition-card');
          const input = root.querySelector('.transition-draft');
          const oldId = root.getAttribute('data-cid');
          const oldRevision = ownership.revisions().find((revision) => ownership.forRender(revision, oldId));
          const oldRoute = ownership.forRender(oldRevision, oldId);
          const anchor = internal.getAnchor(oldId);
          input.value = 'kept';
          input.dispatchEvent(new Event('input', { bubbles: true }));
          Alpine.evaluate(root, 'shown = false');
          for (let count = 0; count < 20 && !root._x_transitioning; count += 1) {
            await new Promise((resolve) => setTimeout(resolve, 5));
          }
          const transitionWasActive = Boolean(root._x_transitioning);
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: 'render', target: 'render:' + oldId, swap: 'morph', html }],
            },
            { anchor, instance: oldId, event: 'refresh' },
          );
          await new Promise((resolve) => setTimeout(resolve, 260));
          const landed = document.querySelector('.transition-card');
          const newId = anchor.componentId;
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, newId));
          const route = ownership.forRender(revision, newId);
          return {
            callbackStable:
              window.__a9TransitionCalls.length === 2 &&
              window.__a9TransitionCalls[0].els === window.__a9TransitionCalls[1].els &&
              window.__a9TransitionCalls[0].scope === window.__a9TransitionCalls[1].scope,
            dataIdFresh: landed.getAttribute('data-cid').split(' ').includes(newId),
            draft: Alpine.evaluate(landed, 'draft'),
            elsLive: route.logicalInstance === oldRoute.logicalInstance &&
              window.__a9TransitionCalls[1].els.length === 1 &&
              window.__a9TransitionCalls[1].els[0] === landed,
            label: landed.querySelector('.transition-label').textContent,
            markerFresh: landed.hasAttribute('data-cid-' + newId),
            markerRetired: landed.hasAttribute('data-cid-' + oldId),
            refsStable: Alpine.evaluate(landed, '$refs.transitionRoot === $el'),
            rootKept: landed === root,
            routeLive: Boolean(route),
            transitionFinished: !landed._x_transitioning,
            transitionWasActive,
          };
        }
        """,
        [fresh],
    )

    assert result == {
        "callbackStable": True,
        "dataIdFresh": True,
        "draft": "kept",
        "elsLive": True,
        "label": "two",
        "markerFresh": True,
        "markerRetired": False,
        "refsStable": True,
        "rootKept": True,
        "routeLive": True,
        "transitionFinished": True,
        "transitionWasActive": True,
    }
    assert not [message for message in messages if message.startswith("error:")]
