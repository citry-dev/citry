"""A6 product acceptance for grouped roots and comment-owned lifecycles."""

from __future__ import annotations

import json
import time
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "a6-root-shapes-e2e"
READY = "window.Citry && Citry.events && Citry.events._internal.alpineStarted === true"


def test_instance_membership_is_bounded_by_its_physical_caps(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = "$component(({ els }) => { window.__a6BoundedEls = els; });"
        template = '<button class="bounded-root">inside</button>'

    class Parent(Component):
        citry = c
        template = """
          <main x-data="{ hits: 0 }">
            <output class="bounded-hits" x-text="hits"></output>
            <c-child @click="hits += 1" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6BoundedEls?.length === 1")

    page.evaluate(
        """
        () => {
          const clone = document.querySelector('.bounded-root').cloneNode(true);
          clone.className = 'out-of-range-clone';
          document.body.append(clone);
        }
        """
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a6BoundedEls.length") == 1

    page.locator(".out-of-range-clone").click()
    page.wait_for_timeout(25)
    assert page.locator(".bounded-hits").inner_text() == "0"
    page.locator(".bounded-root").click()
    assert page.locator(".bounded-hits").inner_text() == "1"


def test_root_group_tracks_dynamic_roots_without_resetting_timing_or_els(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = "$component(({ els }) => { window.__a6DynamicEls = els; window.__a6ElsIdentity = els; });"
        template = """
          <button class="dynamic-root-a">a</button>
          <button class="dynamic-root-b">b</button>
        """

    class Parent(Component):
        citry = c
        template = """
          <main>
            <c-child
              @click.throttle.100ms="(window.__a6DynamicHits ||= []).push($el.className)"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6DynamicEls?.length === 2")
    page.locator(".dynamic-root-a").click()

    page.evaluate(
        """
        () => {
          const a = document.querySelector('.dynamic-root-a');
          const b = document.querySelector('.dynamic-root-b');
          const c = b.cloneNode(true);
          c.className = 'dynamic-root-c';
          a.remove();
          b.after(c);
        }
        """
    )
    page.wait_for_function(
        "window.__a6DynamicEls?.length === 2 && window.__a6DynamicEls[1].className === 'dynamic-root-c'"
    )
    page.locator(".dynamic-root-c").click()
    page.wait_for_timeout(120)
    page.locator(".dynamic-root-c").click()

    assert page.evaluate("window.__a6DynamicEls === window.__a6ElsIdentity") is True
    assert page.evaluate("window.__a6DynamicEls.map((el) => el.className)") == [
        "dynamic-root-b",
        "dynamic-root-c",
    ]
    assert page.evaluate("window.__a6DynamicHits") == ["dynamic-root-a", "dynamic-root-c"]


def test_root_group_preserves_union_global_key_focus_shadow_and_deferred_carriers(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        template = """
          <div class="matrix-root-a" tabindex="0"><button class="matrix-desc-a">a</button></div>
          <div class="matrix-root-b" tabindex="0"><button class="matrix-desc-b">b</button></div>
        """

    class Parent(Component):
        citry = c
        template = """
          <main class="matrix-parent" x-data="{}">
            <button class="matrix-gap">gap</button>
            <c-child
              @click.outside="(window.__a6Matrix.outside ||= []).push($event.target.className)"
              @click.away="(window.__a6Matrix.away ||= []).push($event.target.className)"
              @click.debounce.30ms="(window.__a6Matrix.debounce ||= []).push($el.className)"
              @click.self="(window.__a6Matrix.self ||= []).push($el.className)"
              @a6-window.window="(window.__a6Matrix.window ||= []).push($el.className)"
              @a6-document.document="(window.__a6Matrix.document ||= []).push($el.className)"
              @a6-shadow.outside="(window.__a6Matrix.shadowOutside ||= []).push($event.target.className)"
              @mouseenter="(window.__a6Matrix.enter ||= []).push($el.className)"
              @focus="(window.__a6Matrix.focus ||= []).push($el.className)"
              @keyup.ctrl.enter="(window.__a6Matrix.keys ||= []).push($el.className)"
              @a6-stop.stop.prevent="window.__a6Matrix.stopped = $event.defaultPrevented"
              @a6-async="(
                (window.__a6Matrix.async ||= []).push({
                  phase: 'sync', el: $el.className, current: $event.currentTarget.className
                }),
                queueMicrotask(() => window.__a6Matrix.async.push({
                  phase: 'later', el: $el.className, current: $event.currentTarget
                }))
              )"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(
        """
        () => {
          window.__a6Matrix = {};
          window.__a6ParentBubbles = 0;
          document.querySelector('.matrix-parent').addEventListener('a6-stop', () => window.__a6ParentBubbles++);
          const host = document.createElement('span');
          host.className = 'matrix-shadow-host';
          const shadow = host.attachShadow({ mode: 'open' });
          const inside = document.createElement('button');
          inside.className = 'matrix-shadow-inside';
          shadow.append(inside);
          document.querySelector('.matrix-root-a').append(host);
          window.__a6ShadowInside = inside;
        }
        """
    )

    page.evaluate(
        """
        () => {
          document.querySelector('.matrix-desc-a').dispatchEvent(new MouseEvent('click', { bubbles: true }));
          document.querySelector('.matrix-desc-b').dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
        """
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a6Matrix.debounce") == ["matrix-root-b"]
    assert page.evaluate("window.__a6Matrix.outside || []") == []
    assert page.evaluate("window.__a6Matrix.away || []") == []

    page.locator(".matrix-root-a").dispatch_event("click")
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a6Matrix.self") == ["matrix-root-a"]

    page.locator(".matrix-gap").click()
    assert page.evaluate("window.__a6Matrix.outside") == ["matrix-gap"]
    assert page.evaluate("window.__a6Matrix.away") == ["matrix-gap"]

    page.evaluate("window.dispatchEvent(new CustomEvent('a6-window'))")
    page.evaluate("document.dispatchEvent(new CustomEvent('a6-document'))")
    assert page.evaluate("window.__a6Matrix.window") == ["matrix-root-a"]
    assert page.evaluate("window.__a6Matrix.document") == ["matrix-root-a"]

    page.locator(".matrix-root-a").focus()
    page.locator(".matrix-root-b").focus()
    assert page.evaluate("window.__a6Matrix.focus") == ["matrix-root-a", "matrix-root-b"]

    page.locator(".matrix-desc-b").dispatch_event("keyup", {"key": "Escape", "ctrlKey": True})
    page.locator(".matrix-desc-b").dispatch_event("keyup", {"key": "Enter", "ctrlKey": True})
    assert page.evaluate("window.__a6Matrix.keys") == ["matrix-root-b"]

    page.evaluate(
        """
        () => {
          const a = document.querySelector('.matrix-root-a');
          const b = document.querySelector('.matrix-root-b');
          const gap = document.querySelector('.matrix-gap');
          a.dispatchEvent(new MouseEvent('mouseenter', { relatedTarget: b }));
          a.dispatchEvent(new MouseEvent('mouseenter', { relatedTarget: gap }));
          window.__a6ShadowInside.dispatchEvent(new CustomEvent('a6-shadow', { bubbles: true, composed: true }));
          gap.dispatchEvent(new CustomEvent('a6-shadow', { bubbles: true, composed: true }));
          const stopped = new CustomEvent('a6-stop', { bubbles: true, cancelable: true });
          document.querySelector('.matrix-desc-b').dispatchEvent(stopped);
          window.__a6StoppedDefault = stopped.defaultPrevented;
          document.querySelector('.matrix-desc-b').dispatchEvent(new CustomEvent('a6-async', { bubbles: true }));
        }
        """
    )
    page.wait_for_function("window.__a6Matrix.async?.length === 2")
    assert page.evaluate("window.__a6Matrix.enter") == ["matrix-root-a"]
    assert page.evaluate("window.__a6Matrix.shadowOutside") == ["matrix-gap"]
    assert page.evaluate("window.__a6ParentBubbles") == 0
    assert page.evaluate("window.__a6StoppedDefault") is True
    assert page.evaluate("window.__a6Matrix.async") == [
        {"phase": "sync", "el": "matrix-root-b", "current": "matrix-root-b"},
        {"phase": "later", "el": "matrix-root-b", "current": None},
    ]

    page.locator(".matrix-root-a").evaluate("element => element.remove()")
    page.wait_for_function("!document.querySelector('.matrix-root-a')")
    page.evaluate("window.dispatchEvent(new CustomEvent('a6-window'))")
    assert page.evaluate("window.__a6Matrix.window") == ["matrix-root-a", "matrix-root-b"]


def test_root_group_matches_capture_passive_names_submit_and_event_redispatch(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        template = """
          <div class="options-root-a"><button class="options-target">target</button></div>
          <form class="options-root-b"><button type="submit">submit</button></form>
        """

    class Parent(Component):
        citry = c
        template = """
          <main>
            <c-child
              @a6-capture.capture="window.__a6Options.capture.push('group')"
              @a6-passive.passive.false.prevent="window.__a6Options.passive = $event.defaultPrevented"
              @a6-name.dot="window.__a6Options.dot += 1"
              @a6-camel.camel="window.__a6Options.camel += 1"
              @submit.prevent="window.__a6Options.submit.push(window.__a6PendingModel)"
              @a6-repeat="window.__a6Options.repeat.push($el.className)"
            />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    result = page.evaluate(
        """
        () => {
          window.__a6Options = { capture: [], dot: 0, camel: 0, submit: [], repeat: [] };
          const first = document.querySelector('.options-root-a');
          const target = document.querySelector('.options-target');
          const form = document.querySelector('.options-root-b');
          target.addEventListener('a6-capture', () => window.__a6Options.capture.push('target'));
          target.dispatchEvent(new CustomEvent('a6-capture', { bubbles: true }));

          const passive = new CustomEvent('a6-passive', { bubbles: true, cancelable: true });
          target.dispatchEvent(passive);
          window.__a6Options.passiveAfter = passive.defaultPrevented;

          target.dispatchEvent(new CustomEvent('a6.name', { bubbles: true }));
          target.dispatchEvent(new CustomEvent('a6Camel', { bubbles: true }));

          window.__a6PendingModel = 'stale';
          form._x_pendingModelUpdates = [() => { window.__a6PendingModel = 'flushed'; }];
          form.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true }));

          const repeated = new CustomEvent('a6-repeat', { bubbles: true });
          first.dispatchEvent(repeated);
          form.dispatchEvent(repeated);
          return window.__a6Options;
        }
        """
    )
    assert result == {
        "capture": ["group", "target"],
        "dot": 1,
        "camel": 1,
        "submit": ["flushed"],
        "repeat": ["options-root-a", "options-root-b"],
        "passive": True,
        "passiveAfter": True,
    }


def test_root_group_drops_dead_debounce_carrier_and_cancels_teardown(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = "$component(({ els }) => { window.__a6PendingEls = els; });"
        template = """
          <button class="pending-root-a">a</button>
          <button class="pending-root-b">b</button>
        """

    class Parent(Component):
        citry = c
        template = """
          <main>
            <c-child @click.debounce.50ms="(window.__a6Pending ||= []).push($el.className)" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6PendingEls?.length === 2")
    page.evaluate(
        """
        () => {
          const a = document.querySelector('.pending-root-a');
          a.dispatchEvent(new MouseEvent('click', { bubbles: true }));
          a.remove();
        }
        """
    )
    page.wait_for_timeout(75)
    assert page.evaluate("window.__a6Pending || []") == []

    page.locator(".pending-root-b").click()
    page.wait_for_timeout(75)
    assert page.evaluate("window.__a6Pending") == ["pending-root-b"]

    page.evaluate(
        f"""
        () => {{
          document.querySelector('.pending-root-b').dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const child = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Child.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(child.key);
          for (let node = physical.start; node;) {{
            const next = node.nextSibling;
            node.remove();
            if (node === physical.end) break;
            node = next;
          }}
        }}
        """
    )
    page.wait_for_function("window.__a6PendingEls?.length === 0")
    page.wait_for_timeout(75)
    assert page.evaluate("window.__a6Pending") == ["pending-root-b"]


def test_root_group_poll_has_one_cadence_and_reelects_its_live_carrier(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = "$component(({ els }) => { window.__a6PollEls = els; });"
        template = """
          <button class="poll-root-a">a</button>
          <button class="poll-root-b">b</button>
        """

    class Parent(Component):
        citry = c

        class Events:
            def poll(self):
                return None

        template = '<main><c-child @c-poll.1s="poll" /></main>'

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    held: list[Any] = []
    page.route(f"**/e/{Parent.class_id}/poll", lambda route: held.append(route))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6PollEls?.length === 2")

    def wait_for_calls(count: int) -> None:
        deadline = time.monotonic() + 5
        while len(held) < count:
            if time.monotonic() > deadline:
                raise AssertionError(f"expected {count} grouped poll request(s), got {len(held)}")
            page.wait_for_timeout(25)

    wait_for_calls(1)
    page.wait_for_timeout(100)
    assert len(held) == 1
    assert page.locator(".poll-root-a").get_attribute("data-citry-busy") == ""
    assert page.locator(".poll-root-b").get_attribute("data-citry-busy") is None
    held[0].continue_()
    page.wait_for_function("!document.querySelector('.poll-root-a').hasAttribute('data-citry-busy')")

    page.locator(".poll-root-a").evaluate("element => element.remove()")
    page.wait_for_function("window.__a6PollEls?.length === 1")
    wait_for_calls(2)
    assert page.locator(".poll-root-b").get_attribute("data-citry-busy") == ""

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const child = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Child.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(child.key);
          for (let node = physical.start; node;) {{
            const next = node.nextSibling;
            node.remove();
            if (node === physical.end) break;
            node = next;
          }}
        }}
        """
    )
    held[1].continue_()
    page.wait_for_function("window.__a6PollEls?.length === 0")
    page.wait_for_timeout(1200)
    assert len(held) == 2


def test_rootless_dom_handler_activates_when_an_element_root_arrives(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = """
          $component(({ scope, els }) => {
            scope.label = 'from-child-scope';
            window.__a6ArrivingEls = els;
            window.__a6ArrivingIdentity = els;
          });
        """
        template = "rootless"

    class Parent(Component):
        citry = c
        template = """
          <main x-data="{ hits: 0 }">
            <output class="arriving-hits" x-text="hits"></output>
            <c-child @click="hits += 1" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-parent /></body></html>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6ArrivingEls?.length === 0")
    assert sum("rendered no HTML element root" in message for message in messages) == 1

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Child.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(instance.key);
          const button = document.createElement('button');
          button.className = 'arriving-root';
          button.setAttribute('data-cid', instance.renderId);
          button.setAttribute(`data-cid-${{instance.renderId}}`, '');
          button.setAttribute('data-citry-root', '');
          button.setAttribute('x-text', 'label');
          physical.end.before(button);
        }}
        """
    )
    page.wait_for_function(
        "window.__a6ArrivingEls?.length === 1 "
        "&& document.querySelector('.arriving-root')?.textContent === 'from-child-scope'"
    )
    page.locator(".arriving-root").click()
    assert page.locator(".arriving-hits").inner_text() == "1"

    page.locator(".arriving-root").evaluate("el => el.remove()")
    page.wait_for_function("window.__a6ArrivingEls?.length === 0")
    assert page.evaluate("window.__a6ArrivingEls === window.__a6ArrivingIdentity") is True


@pytest.mark.parametrize(
    ("action", "diagnostic"),
    [
        pytest.param("text", "load-bearing comment caps was changed", id="changed-text"),
        pytest.param("split", "no longer share the validated parent topology", id="split-parent"),
        pytest.param("reverse", "comment caps are reversed", id="reversed"),
    ],
)
def test_runtime_cap_corruption_retires_rootless_lifecycle_once(
    page: Any,
    serve_live: Any,
    action: str,
    diagnostic: str,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6CapInit = (window.__a6CapInit || 0) + 1;
            return () => { window.__a6CapCleanup = (window.__a6CapCleanup || 0) + 1; };
          });
        """
        template = "rootless"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(f"{message.type}:{message.text}"))
    base = serve_live(c, str(Child()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6CapInit === 1")
    page.evaluate(
        """
        action => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values()[0];
          const physical = graph.registry.physicalRegions.get(instance.key);
          if (action === 'text') physical.start.data += ':corrupt';
          if (action === 'split') {
            const sink = document.createElement('div');
            document.body.append(sink);
            sink.append(physical.end);
          }
          if (action === 'reverse') document.documentElement.after(physical.start);
        }
        """,
        action,
    )
    page.wait_for_function("window.__a6CapCleanup === 1")
    page.wait_for_timeout(25)
    assert page.evaluate("window.__a6CapInit") == 1
    assert page.evaluate("window.__a6CapCleanup") == 1
    assert sum(diagnostic in message for message in messages) == 1


def test_range_keeps_its_original_parent_topology_mode(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Page(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6TopologyInit = 1;
            return () => { window.__a6TopologyCleanup = (window.__a6TopologyCleanup || 0) + 1; };
          });
        """
        template = "<html><head></head><body><main>page</main></body></html>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6TopologyInit === 1")
    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values()[0];
          const physical = graph.registry.physicalRegions.get(instance.key);
          if (physical.topology !== 'same-parent') throw new Error(`unexpected topology ${physical.topology}`);
          document.body.append(physical.end);
        }
        """
    )
    page.wait_for_function("window.__a6TopologyCleanup === 1")
    assert sum("validated parent topology" in message for message in messages) == 1


def test_document_body_range_membership_stays_inside_its_exact_caps(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = "$component(({ els }) => { window.__a6DocumentBodyEls = els; });"
        template = "rootless"

    base = serve_live(c, str(Child()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6DocumentBodyEls?.length === 0")
    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values()[0];
          const physical = graph.registry.physicalRegions.get(instance.key);
          if (physical.topology !== 'document-body') throw new Error(`unexpected topology ${physical.topology}`);
          const makeRoot = (name) => {
            const root = document.createElement('button');
            root.className = name;
            root.setAttribute('data-cid', instance.renderId);
            root.setAttribute(`data-cid-${instance.renderId}`, '');
            root.setAttribute('data-citry-root', '');
            return root;
          };
          physical.end.before(makeRoot('document-body-inside'));
          physical.end.after(makeRoot('document-body-outside'));
        }
        """
    )
    page.wait_for_function("window.__a6DocumentBodyEls?.length === 1")
    assert page.evaluate("window.__a6DocumentBodyEls[0].className") == "document-body-inside"


def test_top_level_rootless_document_body_range_can_morph(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = """
          $component(({ els, scope }) => {
            scope.label = 'arrived';
            window.__a6TopMorphEls = els;
            window.__a6TopMorphInits = (window.__a6TopMorphInits || 0) + 1;
          });
        """
        template = "rootless"

    base = serve_live(c, str(Child()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6TopMorphEls?.length === 0")

    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values()[0];
          const physical = graph.registry.physicalRegions.get(instance.key);
          if (physical.topology !== 'document-body') throw new Error(`unexpected topology ${physical.topology}`);
          Citry.manager.ownership._morphRange(
            revision,
            instance.key,
            `<button class="top-rootless-arrival" data-cid="${instance.renderId}"
              data-cid-${instance.renderId} data-citry-root x-text="label"></button>`,
          );
        }
        """
    )
    page.wait_for_function(
        "document.querySelector('.top-rootless-arrival')?.textContent === 'arrived' "
        "&& window.__a6TopMorphEls?.length === 1"
    )
    assert page.evaluate("window.__a6TopMorphInits") == 1

    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values()[0];
          Citry.manager.ownership._morphRange(revision, instance.key, 'rootless again');
        }
        """
    )
    page.wait_for_function("window.__a6TopMorphEls?.length === 0")
    assert page.evaluate("window.__a6TopMorphInits") == 1


def test_same_task_range_move_survives_but_later_detach_is_terminal(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = """
          $component(({ scope }) => {
            window.__a6MoveScope = scope;
            window.__a6MoveInit = (window.__a6MoveInit || 0) + 1;
            return () => { window.__a6MoveCleanup = (window.__a6MoveCleanup || 0) + 1; };
          });
        """
        template = "rootless"

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <div id="move-source"><c-child /></div>
            <div id="move-destination"></div>
          </body></html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6MoveInit === 1")
    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const child = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Child.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(child.key);
          const fragment = document.createDocumentFragment();
          for (let node = physical.start; node;) {{
            const next = node.nextSibling;
            fragment.append(node);
            if (node === physical.end) break;
            node = next;
          }}
          document.getElementById('move-destination').append(fragment);
          window.__a6MovedNodes = [physical.start, physical.end];
        }}
        """
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a6MoveInit") == 1
    assert page.evaluate("window.__a6MoveCleanup || 0") == 0
    assert page.evaluate("window.__a6MovedNodes.every((node) => node.parentElement.id === 'move-destination')") is True

    page.evaluate("window.__a6MovedNodes.forEach((node) => node.remove())")
    page.wait_for_function("window.__a6MoveCleanup === 1")
    page.evaluate(
        """
        () => {
          const destination = document.getElementById('move-destination');
          window.__a6MovedNodes.forEach((node) => destination.append(node));
        }
        """
    )
    page.wait_for_timeout(50)
    assert page.evaluate("window.__a6MoveInit") == 1
    assert page.evaluate("window.__a6MoveCleanup") == 1


def test_adjacent_rootless_ranges_keep_key_locality_during_morph(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class First(Component):
        citry = c
        js = "$component(({ els }) => { window.__a6AdjacentFirstEls = els; });"
        template = "first"

    class Second(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6AdjacentSecondInit = 1;
            return () => { window.__a6AdjacentSecondCleanup = (window.__a6AdjacentSecondCleanup || 0) + 1; };
          });
        """
        template = "second"

    class Page(Component):
        citry = c
        template = "<html><body><c-first /><c-second /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6AdjacentFirstEls?.length === 0 && window.__a6AdjacentSecondInit === 1")
    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const first = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(First.class_id)}
          );
          const second = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Second.class_id)}
          );
          const secondPhysical = graph.registry.physicalRegions.get(second.key);
          window.__a6AdjacentSecondCaps = [secondPhysical.start, secondPhysical.end];
          Citry.manager.ownership._morphRange(
            revision,
            first.key,
            `<button class="adjacent-first-root" data-cid="${{first.renderId}}"
              data-cid-${{first.renderId}} data-citry-root>first</button>`,
          );
        }}
        """
    )
    page.wait_for_function("window.__a6AdjacentFirstEls?.length === 1")
    assert page.evaluate("window.__a6AdjacentSecondCaps.every((cap) => cap.isConnected)") is True
    assert page.evaluate("window.__a6AdjacentSecondCleanup || 0") == 0


def test_throwing_rootless_cleanup_does_not_block_sibling_cleanup(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Throwing(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6ThrowingInit = 1;
            return () => {
              window.__a6ThrowingCleanup = (window.__a6ThrowingCleanup || 0) + 1;
              throw new Error('expected A6 cleanup failure');
            };
          });
        """
        template = "throwing"

    class Healthy(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6HealthyInit = 1;
            return () => {
              window.__a6HealthyCleanup = (window.__a6HealthyCleanup || 0) + 1;
            };
          });
        """
        template = "healthy"

    class Page(Component):
        citry = c
        template = "<html><body><c-throwing /><c-healthy /></body></html>"

    messages: list[str] = []
    page.on("console", lambda message: messages.append(message.text))
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6ThrowingInit === 1 && window.__a6HealthyInit === 1")
    page.evaluate(
        f"""
        () => {{
          const graph = Citry.manager.ownership.get(Citry.manager.ownership.revisions()[0]);
          [{json.dumps(Throwing.class_id)}, {json.dumps(Healthy.class_id)}].forEach((classId) => {{
            const instance = graph.registry.renderIds.values().find((candidate) => candidate.classId === classId);
            const physical = graph.registry.physicalRegions.get(instance.key);
            for (let node = physical.start; node;) {{
              const next = node.nextSibling;
              node.remove();
              if (node === physical.end) break;
              node = next;
            }}
          }});
        }}
        """
    )
    page.wait_for_function("window.__a6ThrowingCleanup === 1 && window.__a6HealthyCleanup === 1")
    assert sum("component cleanup for" in message for message in messages) == 1


def test_shared_root_owner_changes_retarget_existing_alpine_evaluator(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Child(Component):
        citry = c
        js = "$component(({ scope }) => { scope.owner = 'inner'; window.__a6InnerScope = scope; });"
        template = """
          <button
            class="owner-router-root"
            x-data="{ local: 'kept', token: {} }"
            x-init="window.__a6RouterToken = token; window.__a6RouterInits = (window.__a6RouterInits || 0) + 1"
            x-text="`${owner}:${local}`"
            @click="owner = `${owner}!`"
          ></button>
        """

    class Parent(Component):
        citry = c
        js = "$component(({ scope }) => { scope.owner = 'outer'; window.__a6OuterScope = scope; });"
        template = "<c-child />"

    base = serve_live(c, str(Parent()), "")
    page.goto(base + "/")
    page.wait_for_function("document.querySelector('.owner-router-root')?.textContent === 'inner:kept'")
    assert page.evaluate("window.__a6RouterInits") == 1

    page.evaluate(
        rf"""
        () => {{
          const root = document.querySelector('.owner-router-root');
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const inner = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Child.class_id)}
          );
          root.removeAttribute(`data-cid-${{inner.renderId}}`);
          root.setAttribute(
            'data-cid',
            root.getAttribute('data-cid').split(/\s+/).filter((id) => id !== inner.renderId).join(' '),
          );
          window.__a6InnerRenderId = inner.renderId;
        }}
        """
    )
    page.wait_for_function("document.querySelector('.owner-router-root')?.textContent === 'outer:kept'")
    assert page.evaluate("window.__a6RouterInits") == 1
    assert (
        page.evaluate("document.querySelector('.owner-router-root')._x_dataStack[0].token === window.__a6RouterToken")
        is True
    )
    page.locator(".owner-router-root").click()
    page.wait_for_function("document.querySelector('.owner-router-root')?.textContent === 'outer!:kept'")
    assert page.evaluate("window.__a6OuterScope.owner") == "outer!"
    assert page.evaluate("window.__a6InnerScope.owner") == "inner"

    page.evaluate(
        """
        () => {
          const root = document.querySelector('.owner-router-root');
          root.setAttribute(`data-cid-${window.__a6InnerRenderId}`, '');
          root.setAttribute('data-cid', `${root.getAttribute('data-cid')} ${window.__a6InnerRenderId}`);
        }
        """
    )
    page.wait_for_function("document.querySelector('.owner-router-root')?.textContent === 'inner:kept'")
    assert page.evaluate("window.__a6RouterInits") == 1
    assert (
        page.evaluate("document.querySelector('.owner-router-root')._x_dataStack[0].token === window.__a6RouterToken")
        is True
    )


@pytest.mark.parametrize(
    ("page_template", "root_html", "ready_expression"),
    [
        pytest.param(
            "<html><body><table><tbody><c-contextual /></tbody></table></body></html>",
            '<tr class="context-root"><td x-text="label"></td></tr>',
            "document.querySelector('.context-root')?.localName === 'tr' "
            "&& document.querySelector('.context-root td')?.textContent === 'context-ok'",
            id="tbody-tr",
        ),
        pytest.param(
            "<html><body><table><tbody><tr><c-contextual /></tr></tbody></table></body></html>",
            '<td class="context-root" x-text="label"></td>',
            "document.querySelector('.context-root')?.localName === 'td' "
            "&& document.querySelector('.context-root')?.textContent === 'context-ok'",
            id="tr-td",
        ),
        pytest.param(
            "<html><body><select><c-contextual /></select></body></html>",
            '<option class="context-root" x-text="label"></option>',
            "document.querySelector('.context-root')?.localName === 'option' "
            "&& document.querySelector('.context-root')?.textContent === 'context-ok'",
            id="select-option",
        ),
        pytest.param(
            '<html><body><svg xmlns="http://www.w3.org/2000/svg"><c-contextual /></svg></body></html>',
            '<circle class="context-root" x-bind:data-label="label"></circle>',
            "document.querySelector('.context-root')?.namespaceURI === 'http://www.w3.org/2000/svg' "
            "&& document.querySelector('.context-root')?.getAttribute('data-label') === 'context-ok'",
            id="svg-circle",
        ),
    ],
)
def test_range_morph_uses_contextual_parent_and_preserves_stable_scope(
    page: Any,
    serve_live: Any,
    page_template: str,
    root_html: str,
    ready_expression: str,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Contextual(Component):
        citry = c
        js = """
          $component(({ scope, els }) => {
            scope.label = 'context-ok';
            window.__a6ContextEls = els;
            window.__a6ContextElsIdentity = els;
          });
        """
        template = ""

    class Page(Component):
        citry = c

    Page.template = page_template
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6ContextEls?.length === 0")

    page.evaluate(
        f"""
        html => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Contextual.class_id)}
          );
          const marker = instance.renderId;
          const stamped = html.replace(
            'class="context-root"',
            `class="context-root" data-cid="${{marker}}" data-cid-${{marker}} data-citry-root`,
          );
          Citry.manager.ownership._morphRange(revision, instance.key, stamped);
        }}
        """,
        root_html,
    )
    page.wait_for_function(ready_expression)
    assert page.evaluate("window.__a6ContextEls === window.__a6ContextElsIdentity") is True
    assert page.evaluate("window.__a6ContextEls.length") == 1

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const instance = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Contextual.class_id)}
          );
          Citry.manager.ownership._morphRange(revision, instance.key, 'plain text');
        }}
        """
    )
    page.wait_for_function("window.__a6ContextEls?.length === 0")
    assert page.evaluate("window.__a6ContextEls === window.__a6ContextElsIdentity") is True


def test_range_morph_preserves_explicitly_correlated_nested_island(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Inner(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6NestedComponentInits = (window.__a6NestedComponentInits || 0) + 1;
            return () => {
              window.__a6NestedComponentCleanups = (window.__a6NestedComponentCleanups || 0) + 1;
            };
          });
        """
        template = """
          <input
            class="nested-island"
            x-data="{ token: {} }"
            x-init="window.__a6NestedToken = token; window.__a6NestedInits = (window.__a6NestedInits || 0) + 1"
          />
        """

    class Outer(Component):
        citry = c
        js = "$component(() => {});"
        template = '<div class="outer-island"><c-inner /></div>'

    class Page(Component):
        citry = c
        template = "<html><body><c-outer /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6NestedInits === 1 && window.__a6NestedComponentInits === 1")
    page.locator(".nested-island").fill("client-kept")

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const outer = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Outer.class_id)}
          );
          const inner = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Inner.class_id)}
          );
          const physical = graph.registry.physicalRegions.get(inner.key);
          const oldRoot = document.querySelector('.nested-island');
          window.__a6NestedIdentity = {{ start: physical.start, end: physical.end, root: oldRoot }};
          const capKey = physical.start.data.replace(/:s$/, '');
          const correspondence = {{ [capKey]: inner.logicalInstance.id }};
          const incoming = `<div class="outer-island"><p>before</p><!--${{physical.start.data}}-->${{
            oldRoot.outerHTML
          }}<!--${{physical.end.data}}--><p>after</p></div>`;
          Citry.manager.ownership._morphRange(revision, outer.key, incoming, {{ correspondence }});
        }}
        """
    )
    page.wait_for_function("document.querySelector('.outer-island p')?.textContent === 'before'")

    assert page.locator(".nested-island").input_value() == "client-kept"
    assert page.evaluate("window.__a6NestedInits") == 1
    assert page.evaluate("window.__a6NestedComponentInits") == 1
    assert page.evaluate("window.__a6NestedComponentCleanups || 0") == 0
    assert (
        page.evaluate(
            """
        () => {
          const current = document.querySelector('.nested-island');
          return current === window.__a6NestedIdentity.root
            && current._x_dataStack[0].token === window.__a6NestedToken
            && window.__a6NestedIdentity.start.isConnected
            && window.__a6NestedIdentity.end.isConnected;
        }
        """
        )
        is True
    )


def test_range_morph_preserves_nested_island_from_an_independent_graph_revision(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Inner(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6CrossInnerInits = (window.__a6CrossInnerInits || 0) + 1;
            return () => { window.__a6CrossInnerCleanups = (window.__a6CrossInnerCleanups || 0) + 1; };
          });
        """
        template = """
          <input
            class="cross-revision-inner"
            x-data="{ token: {} }"
            x-init="
              window.__a6CrossAlpineToken = token;
              window.__a6CrossAlpineInits = (window.__a6CrossAlpineInits || 0) + 1
            "
          />
        """

    class Outer(Component):
        citry = c
        js = "$component(() => {});"
        template = '<div class="cross-revision-outer"><div id="cross-revision-target"></div></div>'

    class Page(Component):
        citry = c
        template = "<html><body><c-outer /></body></html>"

    fragment = Inner().render().serialize(deps_strategy="fragment")
    base = serve_live(c, str(Page()), fragment)
    page.goto(base + "/")
    page.wait_for_function(READY)
    # Resolve the fetch before insertion. Appending the graph-linked fragment
    # can synchronously start dependency scripts, so keeping that mutation in
    # a non-async evaluation avoids Playwright mistaking the changing script
    # execution context for a navigation while the fetch callback unwinds.
    fetched_html = page.evaluate("async () => await fetch('/fragment').then((response) => response.text())")
    page.evaluate(
        """
        (html) => {
          const template = document.createElement('template');
          template.innerHTML = html;
          document.getElementById('cross-revision-target').append(template.content);
        }
        """,
        fetched_html,
    )
    page.wait_for_function(
        "Citry.manager.ownership.revisions().length === 2 "
        "&& window.__a6CrossInnerInits === 1 && window.__a6CrossAlpineInits === 1"
    )
    page.locator(".cross-revision-inner").fill("cross-client-kept")

    page.evaluate(
        f"""
        () => {{
          const revisions = Citry.manager.ownership.revisions();
          let outer = null;
          let inner = null;
          revisions.forEach((revision) => {{
            const graph = Citry.manager.ownership.get(revision);
            graph.registry.renderIds.values().forEach((instance) => {{
              if (instance.classId === {json.dumps(Outer.class_id)}) outer = {{ revision, graph, instance }};
              if (instance.classId === {json.dumps(Inner.class_id)}) inner = {{ revision, graph, instance }};
            }});
          }});
          const physical = inner.graph.registry.physicalRegions.get(inner.instance.key);
          const root = document.querySelector('.cross-revision-inner');
          window.__a6CrossIdentity = {{
            start: physical.start,
            end: physical.end,
            root,
            anchor: inner.instance.anchor,
          }};
          const capKey = physical.start.data.replace(/:s$/, '');
          const correspondence = {{ [capKey]: inner.instance.logicalInstance.id }};
          const current = document.querySelector('.cross-revision-outer').outerHTML;
          const incoming = current.replace(
            '<div id="cross-revision-target">',
            '<p class="cross-revision-before">before</p><div id="cross-revision-target">',
          );
          Citry.manager.ownership._morphRange(
            outer.revision,
            outer.instance.key,
            incoming,
            {{ correspondence }},
          );
        }}
        """
    )
    page.wait_for_function("document.querySelector('.cross-revision-before')?.textContent === 'before'")

    assert page.locator(".cross-revision-inner").input_value() == "cross-client-kept"
    assert page.evaluate("window.__a6CrossInnerInits") == 1
    assert page.evaluate("window.__a6CrossInnerCleanups || 0") == 0
    assert page.evaluate("window.__a6CrossAlpineInits") == 1
    assert (
        page.evaluate(
            """
            () => {
              const current = document.querySelector('.cross-revision-inner');
              const kept = window.__a6CrossIdentity;
              return current === kept.root
                && current._x_dataStack[0].token === window.__a6CrossAlpineToken
                && kept.start.isConnected
                && kept.end.isConnected
                && Citry.manager.ownership._isLive(kept.anchor);
            }
            """
        )
        is True
    )


def test_fill_mirror_group_keeps_one_physical_lifetime_until_last_copy(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Mirror(Component):
        citry = c
        js = "$component(() => {});"
        template = '<c-slot name="body" /><c-slot name="body" />'

    class Page(Component):
        citry = c
        template = '<html><body><c-mirror><c-fill name="body" /></c-mirror></body></html>'

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function(
        "Citry.manager.ownership.get(Citry.manager.ownership.revisions()[0])"
        ".registry.rangeGroups.values().some((group) => group.slotRegions.length === 2)"
    )

    page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const group = graph.registry.rangeGroups.values().find((candidate) => candidate.slotRegions.length === 2);
          window.__a6MirrorGroup = group;
          window.__a6MirrorEls = group.els;
          group.slotRegions.forEach((region, index) => {
            Citry.manager.ownership._morphRange(
              revision,
              region.key,
              `<span class="mirror-copy" data-copy="${index}">${index}</span>`,
            );
          });
        }
        """
    )
    page.wait_for_function("window.__a6MirrorGroup.els.length === 2")
    assert page.evaluate("window.__a6MirrorGroup.els === window.__a6MirrorEls") is True

    page.evaluate(
        """
        () => {
          const slotRegions = window.__a6MirrorGroup.liveSlotRegions;
          const first = slotRegions[0].physical;
          const second = slotRegions[1].physical;
          const moved = document.createDocumentFragment();
          for (let node = second.start; node;) {
            const next = node.nextSibling;
            moved.append(node);
            if (node === second.end) break;
            node = next;
          }
          first.start.before(moved);
        }
        """
    )
    page.wait_for_function("window.__a6MirrorGroup.els.map((element) => element.dataset.copy).join(',') === '1,0'")
    assert page.evaluate("window.__a6MirrorGroup.els === window.__a6MirrorEls") is True

    page.evaluate(
        """
        () => {
          const region = window.__a6MirrorGroup.liveSlotRegions[0];
          const physical = region.physical;
          for (let node = physical.start; node;) {
            const next = node.nextSibling;
            node.remove();
            if (node === physical.end) break;
            node = next;
          }
        }
        """
    )
    page.wait_for_function("window.__a6MirrorGroup.els.length === 1")
    assert page.evaluate("window.__a6MirrorGroup.active") is True

    page.evaluate(
        """
        () => {
          const region = window.__a6MirrorGroup.liveSlotRegions[0];
          const physical = region.physical;
          for (let node = physical.start; node;) {
            const next = node.nextSibling;
            node.remove();
            if (node === physical.end) break;
            node = next;
          }
        }
        """
    )
    page.wait_for_function("window.__a6MirrorGroup.active === false")
    assert page.evaluate("window.__a6MirrorGroup.els.length") == 0


def test_top_level_fill_mirror_includes_document_body_region_roots(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Mirror(Component):
        citry = c
        js = "$component(() => {});"
        template = '<c-slot name="body" /><c-slot name="body" />'

    class Page(Component):
        citry = c
        template = '<c-mirror><c-fill name="body"><span class="top-level-mirror-copy">x</span></c-fill></c-mirror>'

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("document.querySelectorAll('.top-level-mirror-copy').length === 2")

    result = page.evaluate(
        """
        () => {
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const group = graph.registry.rangeGroups.values().find((candidate) => candidate.slotRegions.length === 2);
          return {
            topologies: group.slotRegions.map((region) => region.physical.topology),
            roots: group.els.map((element) => element.className),
          };
        }
        """
    )
    assert result == {
        "topologies": ["document-body", "same-parent"],
        "roots": ["top-level-mirror-copy", "top-level-mirror-copy"],
    }


def test_top_level_document_body_morph_retires_nested_document_body_range(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Mirror(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6NestedDocumentInit = (window.__a6NestedDocumentInit || 0) + 1;
            return () => {
              window.__a6NestedDocumentCleanup = (window.__a6NestedDocumentCleanup || 0) + 1;
            };
          });
        """
        template = '<c-slot name="body" /><c-slot name="body" />'

    class Page(Component):
        citry = c
        js = "$component(() => { window.__a6OuterDocumentInit = 1; });"
        template = '<c-mirror><c-fill name="body"><span class="nested-document-copy">x</span></c-fill></c-mirror>'

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6OuterDocumentInit === 1 && window.__a6NestedDocumentInit === 1")

    before = page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const outer = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Page.class_id)}
          );
          const inner = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Mirror.class_id)}
          );
          const outerPhysical = graph.registry.physicalRegions.get(outer.key);
          const innerPhysical = graph.registry.physicalRegions.get(inner.key);
          window.__a6OuterDocument = {{ graph, outer, physical: outerPhysical }};
          Citry.manager.ownership._morphRange(revision, outer.key, '<p id="document-body-replaced">new</p>');
          return [outerPhysical.topology, innerPhysical.topology];
        }}
        """
    )
    assert before == ["document-body", "document-body"]
    page.wait_for_function(
        "document.getElementById('document-body-replaced')?.textContent === 'new' "
        "&& window.__a6NestedDocumentCleanup === 1"
    )
    result = page.evaluate(
        """
        () => ({
          html: Boolean(document.documentElement),
          body: Boolean(document.body),
          copies: document.querySelectorAll('.nested-document-copy').length,
          templates: document.querySelectorAll('template[data-citry-range-island]').length,
          outerLive: Citry.manager.ownership._isLive(window.__a6OuterDocument.outer.anchor),
          outerCaps: window.__a6OuterDocument.physical.start.isConnected
            && window.__a6OuterDocument.physical.end.isConnected,
        })
        """
    )
    assert result == {
        "html": True,
        "body": True,
        "copies": 0,
        "templates": 0,
        "outerLive": True,
        "outerCaps": True,
    }
    assert page.evaluate("window.__a6NestedDocumentInit") == 1


def test_top_level_document_body_morph_preserves_correlated_nested_range(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)

    class Mirror(Component):
        citry = c
        js = """
          $component(() => {
            window.__a6KeptDocumentInit = (window.__a6KeptDocumentInit || 0) + 1;
            return () => {
              window.__a6KeptDocumentCleanup = (window.__a6KeptDocumentCleanup || 0) + 1;
            };
          });
        """
        template = '<c-slot name="body" /><c-slot name="body" />'

    class Page(Component):
        citry = c
        js = "$component(() => {});"
        template = (
            '<c-mirror><c-fill name="body">'
            '<input class="kept-document-copy" value="server" '
            'x-init="window.__a6KeptDocumentAlpine = (window.__a6KeptDocumentAlpine || 0) + 1" />'
            "</c-fill></c-mirror>"
        )

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function("window.__a6KeptDocumentInit === 1 && window.__a6KeptDocumentAlpine === 2")
    page.locator(".kept-document-copy").nth(0).fill("client-0")
    page.locator(".kept-document-copy").nth(1).fill("client-1")

    page.evaluate(
        f"""
        () => {{
          const revision = Citry.manager.ownership.revisions()[0];
          const graph = Citry.manager.ownership.get(revision);
          const outer = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Page.class_id)}
          );
          const inner = graph.registry.renderIds.values().find(
            (candidate) => candidate.classId === {json.dumps(Mirror.class_id)}
          );
          const outerPhysical = graph.registry.physicalRegions.get(outer.key);
          const innerPhysical = graph.registry.physicalRegions.get(inner.key);
          if (outerPhysical.topology !== 'document-body' || innerPhysical.topology !== 'document-body') {{
            throw new Error('expected nested document-body ranges');
          }}

          const incoming = document.createElement('div');
          for (let node = outerPhysical.start.nextSibling; node && node !== document.documentElement;
            node = node.nextSibling) incoming.append(node.cloneNode(true));
          for (let node = document.body.firstChild; node && node !== outerPhysical.end;
            node = node.nextSibling) incoming.append(node.cloneNode(true));

          const correspondence = {{}};
          graph.registry.physicalRegions.values().forEach((physical) => {{
            const instance = graph.registry.componentInstances.get(physical.key);
            const region = graph.registry.slotRegions.get(physical.key);
            const capKey = physical.start.data.replace(/:s$/, '');
            if (instance) correspondence[capKey] = instance.logicalInstance.id;
            else if (region) {{
              correspondence[capKey] = `fill:${{region.graphId}}:${{region.fillId}}:${{region.regionId}}`;
            }}
          }});

          window.__a6KeptDocument = {{
            roots: Array.from(document.querySelectorAll('.kept-document-copy')),
            documentCaps: [],
            innerPhysical,
          }};
          for (let node = outerPhysical.start.nextSibling; node && node !== document.documentElement;
            node = node.nextSibling) window.__a6KeptDocument.documentCaps.push(node);

          Citry.manager.ownership._morphRange(
            revision,
            outer.key,
            incoming.innerHTML,
            {{ correspondence }},
          );
        }}
        """
    )
    page.wait_for_function("document.querySelectorAll('.kept-document-copy').length === 2")
    assert page.evaluate("Array.from(document.querySelectorAll('.kept-document-copy'), (input) => input.value)") == [
        "client-0",
        "client-1",
    ]
    result = page.evaluate(
        """
        () => {
          const current = Array.from(document.querySelectorAll('.kept-document-copy'));
          const kept = window.__a6KeptDocument;
          return {
            roots: current.every((root, index) => root === kept.roots[index]),
            documentCaps: kept.documentCaps.every((cap) => cap.parentNode === document),
            innerCaps: kept.innerPhysical.start.isConnected && kept.innerPhysical.end.isConnected,
            templates: document.querySelectorAll('template[data-citry-range-island]').length,
          };
        }
        """
    )
    assert result == {"roots": True, "documentCaps": True, "innerCaps": True, "templates": 0}
    assert page.evaluate("window.__a6KeptDocumentInit") == 1
    assert page.evaluate("window.__a6KeptDocumentCleanup || 0") == 0
    assert page.evaluate("window.__a6KeptDocumentAlpine") == 2
