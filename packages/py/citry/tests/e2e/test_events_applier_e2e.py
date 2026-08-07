"""
Browser e2e for the events actions applier, the `applyActions` half of the
client runtime shipped as ``citry/ext/events/client/citry-events.js`` (design
contract: docs/design/events.md 4.2/4.3/5.2/5.3/5.5; the component-identity
and keyed-morph spikes pin the mechanics). Every test feeds result envelopes
straight into the applier, no wire involved
(``Citry.events._internal.applyResult`` / ``applyEnvelope``, or the public
``Citry.events.applyActions``), with fragments rendered by the real server
pipeline (``.render().serialize(deps_strategy="fragment")``, the exact shape
the server's Render action encodes); the transport suite next door owns the
wire's own behavior.

What this suite locks, mapped to the design:

- Every protocol example's result envelope applies cleanly (ok results
  update the DOM / resolve ``data`` / refresh tokens; error results are the
  transport's job and the applier leaves them alone without throwing).
- The uncorrelated-id lifecycle: a correlated self-render lands the server's
  fresh ``data-cid-<id>`` while the anchor's ``$state`` identity and epoch
  bookkeeping persist; the manifest tags are delivered by the applier after
  the morph, so assets load and ``$component`` re-fires with teardown
  first; a plain-HTML render retires the anchor and the dependency
  reconciler's teardown runs exactly once; a different-class render adopts
  the fresh contract wholesale.
- Positional-unkeyed and keyed linking under a parent render: a same-class
  unkeyed child at the same direct-child position links, while a keyed child
  can also link across reorder (draft, ``$loading``, subscription, and the
  epoch pair survive). The horizon cut drops the child's in-flight render
  while its ``data`` still resolves; two keyed inputs that swap positions
  carry their typed values (the composite-key morph callback).
- Targeted renders as remove-and-replace, with keyed matches inside the
  fragment linking; per-action liveness within one result and across results
  in one batch envelope (the caller-inside-target drop, reason ``retired``);
  a multi-target render mirroring one shared instance with duplicate
  manifest tags stripped.
- The epoch guard at apply time (an older response's instance-mutating
  actions drop with reason ``epoch`` while its ``data`` resolves).
- The preservation rules: the two poles (fast typing over a patch loses
  nothing, in both draft stages; submit-then-clear clears a still-focused
  flushed field), the ``#c-ignore`` subtree opt-out with the instance-root
  warning, and the busy re-stamp for linked anchors (new roots plus the
  surviving triggering element).
- Faithful action ordering with the ``delay``/``wait`` timing fields, a
  scheduled action re-resolving its target at fire time, the zero-match
  warning, and the ``citry:events:swapped`` / ``citry:events:stale``
  lifecycle events with their ``detail`` contract.
- History actions preserve application-owned state and do not emit
  ``popstate`` themselves; native Back/Forward still emits it without Citry
  restoring or changing component DOM and State.
- The recurring-timer structure (anchor timers stop at retirement; an
  element-keyed timer dedupes instead of double-polling).

Uses the live-server harness (conftest ``serve_live``) like the WP15 suite,
so pages fetch ``/citry/citry.js`` and ``/citry/ext/events/runtime.js`` from
the real routes. Locked strings (warnings, drop reasons) were observed from
the real runtime first, then locked.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component
from citry.ext.events import actions

pytestmark = pytest.mark.e2e

SIGNING_KEY = "e2e-secret"

READY = "window.Citry && Citry.events && Citry.events._internal && Citry.events._internal.alpineStarted === true"

TESTS_DIR = Path(__file__).resolve().parents[4] / "protocol" / "events" / "v1" / "tests"

# Registered on every page before anything applies: collects the runtime's
# lifecycle events (detail elements mapped to counts so the log serializes
# back to Python) and the values `data` actions resolve.
_SETUP_LOGS = """
() => {
  window.__log = { stale: [], swapped: [], data: [], events: [] };
  document.addEventListener("citry:events:stale", (e) => {
    window.__log.stale.push({
      instance: e.detail.instance,
      cls: e.detail.class,
      event: e.detail.event,
      reason: e.detail.reason,
    });
  });
  document.addEventListener("citry:events:swapped", (e) => {
    window.__log.swapped.push({
      instance: e.detail.instance,
      cls: e.detail.class,
      event: e.detail.event,
      els: (e.detail.els || []).length,
    });
  });
}
"""


def _collect_console(page: Any) -> list[str]:
    """Start collecting console messages as ``type:text`` strings."""
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}:{msg.text}"))
    return messages


def _citry_errors(messages: list[str]) -> list[str]:
    return [m for m in messages if m.startswith("error:")]


def _fragment(component: Component) -> str:
    """Render a component the way the server's Render action encodes html."""
    return component.render().serialize(deps_strategy="fragment")


def _goto(page: Any, serve_live: Any, citry: Citry, html: str) -> list[str]:
    """Serve the page, open it, wait for the runtime, register the log listeners."""
    messages = _collect_console(page)
    base = serve_live(citry, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.evaluate(_SETUP_LOGS)
    return messages


# ----- the WP5 protocol-test replay -----


def _substituted_result(result: dict, dynamic_fields: list[str], live_id: str, fresh_html: str) -> dict:
    """Fill a protocol result's declared dynamic fields with live harness values."""
    out = copy.deepcopy(result)
    for path in dynamic_fields:
        if not path.startswith("result."):
            continue
        tokens = re.findall(r"\.([A-Za-z_]+)|\[(\d+)\]", path[len("result") :])
        keys: list[Any] = [key if key else int(index) for key, index in tokens]
        parent: Any = out
        for key in keys[:-1]:
            parent = parent[key]
        leaf = keys[-1]
        if leaf == "html":
            parent[leaf] = fresh_html
        elif leaf == "target":
            parent[leaf] = f"render:{live_id}"
        elif leaf == "instance":
            parent[leaf] = live_id
        elif leaf == "token":
            parent[leaf] = "tok-replayed"
    return out


def test_wp5_fixtures_replay_through_the_applier(page: Any, serve_live: Any) -> None:
    # The conformance idea applied client-side: every protocol example's
    # result envelope feeds the applier against a live page. Volatile result
    # paths are substituted with live values (the spec's counter component
    # rendered fresh per example), and each example replays against reset
    # epoch bookkeeping, mirroring the tests README's fresh-render rule. Ok
    # results must apply (render lands, data resolves, token refreshes);
    # error results carry no actions and must be a clean no-op.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class CounterState:
        count: int = 0
        name: str = "Counter"
        _public = ("count", "name")

    class Counter(Component):
        citry = c
        State = CounterState

        class Events:
            def increment(self, state):
                return None

            def rename(self, state):
                return None

        template = """
          <div class="counter">
            <h2 x-text="$state.name">Counter</h2>
            <button class="n" x-text="'Clicked ' + $state.count + ' times'">Clicked 0 times</button>
          </div>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>protocol examples</title></head>
            <body>
              <c-counter />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    page.evaluate("() => { document.addEventListener('counter:renamed', (e) => window.__log.events.push(e.detail)); }")

    index = json.loads((TESTS_DIR / "index.json").read_text(encoding="utf-8"))
    assert len(index) == 19  # every protocol example replays; add new examples here too
    render_fixtures = 0
    data_values: list[Any] = []
    for entry in index:
        result_doc = json.loads((TESTS_DIR / entry["result"]).read_text(encoding="utf-8"))
        live_id = page.evaluate("() => document.querySelector('.counter').getAttribute('data-cid')")
        fresh_html = _fragment(Counter(count=1, name="Counter"))
        substituted = _substituted_result(result_doc, entry["dynamic_fields"], live_id, fresh_html)
        has_render = any(
            action.get("action") == "render"
            for result in substituted["results"]
            for action in result.get("actions", [])
        )

        outcome = page.evaluate(
            """
            async ([results, liveId]) => {
              const internal = Citry.events._internal;
              const anchor = internal.getAnchor(liveId);
              // Each example replays independently (the README's fresh-render
              // rule): reset the epoch bookkeeping the previous replay moved.
              if (anchor) {
                anchor.highestApplied = 0;
                anchor.epochOwner = null;
              }
              const ctxs = results.map(() => ({
                anchor,
                instance: liveId,
                event: "replay",
                onData: (v) => window.__log.data.push(v),
              }));
              await internal.applyEnvelope(results, ctxs);
              return { newId: document.querySelector(".counter")?.getAttribute("data-cid") ?? null };
            }
            """,
            [substituted["results"], live_id],
        )

        if has_render:
            render_fixtures += 1
            assert outcome["newId"] is not None
            assert outcome["newId"] != live_id, entry["result"]  # the fresh fragment landed
        else:
            assert outcome["newId"] == live_id, entry["result"]  # error and data results leave the DOM alone
        for result in substituted["results"]:
            for action in result.get("actions", []):
                if action.get("action") == "data":
                    data_values.append(action["value"])

    # Every data action resolved through the caller hook, in envelope order.
    assert page.evaluate("() => window.__log.data") == data_values
    assert render_fixtures == 3  # happy_render, baseline_swap, batch_two
    # rename_coerce's event action (delay 1.5, wait false) re-resolves the
    # caller's anchor at fire time and reaches the instance's current root.
    page.wait_for_function("window.__log.events.length === 1", timeout=8000)
    assert page.evaluate("() => window.__log.events[0]") == {"name": "Tally"}
    assert _citry_errors(messages) == []


# ----- the correlated self-render lifecycle -----


def _make_todo_app() -> tuple[Citry, type[Component], type[Component]]:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class TodoState:
        query: str = ""
        note: str = ""
        count: int = 0
        _public = ("query", "note", "count")

    class Todo(Component):
        citry = c
        State = TodoState

        class Events:
            def save(self, state):
                return None

        js = """
          $component(({ id }) => {
            window.__fires = (window.__fires || 0) + 1;
            window.__lastId = id;
            return () => { window.__cleanups = (window.__cleanups || 0) + 1; };
          });
        """
        template = """
          <div class="todo">
            <span class="q" x-text="$state.query"></span>
            <span class="k" x-text="$state.count"></span>
          </div>
        """

    class Page(Component):
        citry = c

        template = """
          <html>
            <head><title>applier</title></head>
            <body>
              <c-todo query="shoes" />
            </body>
          </html>
        """

    return c, Todo, Page


def test_self_render_lands_fresh_id_while_anchor_and_state_identity_persist(page: Any, serve_live: Any) -> None:
    # The core of the lifecycle: a correlated self-render routes to the
    # caller's anchor (by the context the transport will hand over, never by
    # a component id), morphs through the real pinned morph, lands the
    # server's fresh data-cid, keeps the anchor and $state identity, applies
    # the reconcile rule (server wins per field except pending unsent
    # writes), marks the epoch applied, and delivers the fragment's manifest
    # tags after the patch, so the dependency manager re-fires $component
    # with teardown first (machinery items 1 and 2).
    c, Todo, Page = _make_todo_app()
    messages = _goto(page, serve_live, c, str(Page()))
    page.wait_for_function("window.__fires === 1")

    fresh = _fragment(Todo(query="fresh-q", note="server-note", count=5))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const oldId = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          const before = {
            anchorId: anchor.anchorId,
            proxy: anchor.stateProxy,
            values: anchor.values,
            tags: document.querySelectorAll("script[data-citry-events]").length,
          };
          anchor.stateProxy.note = "local-draft"; // a pending, not-yet-sent write
          anchor.epoch = 1; // the transport's send-side increment, simulated
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor, instance: oldId, event: "save" },
          );
          const newId = document.querySelector(".todo").getAttribute("data-cid");
          const after = internal.getAnchor(newId);
          return {
            oldId,
            newId,
            idChanged: newId !== oldId,
            oldUnlinked: internal.getAnchor(oldId) === null,
            sameAnchor: after === anchor,
            anchorIdKept: anchor.anchorId === before.anchorId,
            proxyKept: anchor.stateProxy === before.proxy,
            valuesKept: anchor.values === before.values,
            query: anchor.values.query,
            note: anchor.values.note,
            count: anchor.values.count,
            pendingKept: anchor.pending.note === "local-draft",
            highestApplied: anchor.highestApplied,
            tokenSet: anchor.token.length > 0,
            tagsAdded: document.querySelectorAll("script[data-citry-events]").length - before.tags,
            swapped: window.__log.swapped,
          };
        }
        """,
        [fresh],
    )

    assert result["idChanged"] is True
    assert result["oldUnlinked"] is True
    assert result["sameAnchor"] is True
    assert result["anchorIdKept"] is True
    assert result["proxyKept"] is True
    assert result["valuesKept"] is True
    assert result["query"] == "fresh-q"  # server wins a clean field
    assert result["note"] == "local-draft"  # the pending unsent write wins its field
    assert result["count"] == 5
    assert result["pendingKept"] is True
    assert result["highestApplied"] == 1
    assert result["tokenSet"] is True
    assert result["tagsAdded"] == 1  # the applier inserted the fragment's manifest tags after the morph
    # The swapped lifecycle event carries the {instance, class, event} detail
    # plus the swapped-in roots; the instance is the fresh id at fire time.
    assert result["swapped"] == [
        {"instance": result["newId"], "cls": Todo.class_id, "event": "save", "els": 1},
    ]
    # Reactivity carried the reconciled values into the bound text.
    page.wait_for_function("document.querySelector('.q').innerText === 'fresh-q'")
    # The re-inserted manifest re-fired $component, teardown first, exactly once.
    page.wait_for_function("window.__cleanups === 1 && window.__fires === 2")
    assert page.evaluate("() => window.__lastId") == result["newId"]
    assert _citry_errors(messages) == []


def test_adopt_and_plain_html_branches_through_a_real_morph(page: Any, serve_live: Any) -> None:
    # The other two branches of the three-way split, this time through the
    # real applier and morph. A different-class render adopts the server's
    # contract wholesale on the same anchor; a plain-HTML render then makes
    # the position non-interactive: the anchor retires and the dependency
    # reconciler runs the instance's teardown exactly once.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class CardState:
        title: str = "t1"
        _public = ("title",)

    class Card(Component):
        citry = c
        State = CardState

        class Events:
            def save(self, state):
                return None

        js = """
          $component(() => {
            window.__cardFires = (window.__cardFires || 0) + 1;
            return () => { window.__cardCleanups = (window.__cardCleanups || 0) + 1; };
          });
        """
        template = """
          <div class="card">
            <span x-text="$state.title"></span>
          </div>
        """

    class PanelState:
        mode: str = "m1"
        _public = ("mode",)

    class Panel(Component):
        citry = c
        State = PanelState

        class Events:
            def flip(self, state):
                return None

        template = """
          <section
            class="panel"
            x-data
            @private-event="window.__panelAlpine = (window.__panelAlpine || 0) + 1"
            @c-private-event="flip"
          >
            <span class="m" x-text="$state.mode"></span>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>split</title></head>
            <body>
              <c-card />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    page.wait_for_function("window.__cardFires === 1")

    panel_html = _fragment(Panel(mode="m-adopted"))
    adopt = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const oldId = document.querySelector(".card").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          window.__panelCalls = [];
          window.__panelAlpine = 0;
          internal.setTransport((call) => { window.__panelCalls.push(call); return null; });
          document.addEventListener('citry:events:swapped', () => {
            document.querySelector('.panel')?.dispatchEvent(new CustomEvent('private-event'));
            window.__duringSwapped = {
              calls: window.__panelCalls.length,
              alpine: window.__panelAlpine,
            };
          }, { once: true });
          anchor.stateProxy.title = "will-be-dropped"; // pending writes do not survive a class change
          const beforeProxy = anchor.stateProxy;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor, instance: oldId, event: "save" },
          );
          const newId = document.querySelector(".panel")?.getAttribute("data-cid") ?? null;
          let writeError = null;
          try {
            anchor.stateProxy.title = "x";
          } catch (err) {
            writeError = String(err.message || err);
          }
          return {
            newId,
            sameAnchor: newId !== null && internal.getAnchor(newId) === anchor,
            classId: anchor.classId,
            mode: anchor.values.mode,
            proxyRebuilt: anchor.stateProxy !== beforeProxy,
            pendingCleared: Object.keys(anchor.pending).length === 0,
            writeError,
            rootIsSection: document.querySelector(".panel")?.tagName ?? null,
            cardGone: document.querySelector(".card") === null,
            duringSwapped: window.__duringSwapped,
          };
        }
        """,
        [panel_html],
    )
    assert adopt["sameAnchor"] is True
    assert adopt["classId"] == Panel.class_id
    assert adopt["mode"] == "m-adopted"
    assert adopt["proxyRebuilt"] is True  # the contract is rebuilt for the new class
    assert adopt["pendingCleared"] is True
    assert "not client-writable" in (adopt["writeError"] or "")  # the writable set switched with the class
    assert adopt["rootIsSection"] == "SECTION"  # a different root tag swaps wholesale
    assert adopt["cardGone"] is True
    assert adopt["duringSwapped"] == {"calls": 0, "alpine": 0}
    # The card instance's teardown ran once when its id left the DOM.
    page.wait_for_function("window.__cardCleanups === 1")
    page.wait_for_function("Citry.events._internal.debug().bindingListenerTargets === 1")
    page.evaluate("document.querySelector('.panel').dispatchEvent(new CustomEvent('private-event'))")
    page.wait_for_function("window.__panelCalls.length === 1")
    assert page.evaluate("window.__panelCalls[0].handlerName") == "flip"
    assert page.evaluate("window.__panelAlpine") == 1

    plain = page.evaluate(
        """
        async () => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".panel").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html: "<p class='gone'>done</p>" }],
            },
            { anchor, instance: id, event: "flip" },
          );
          return {
            text: document.querySelector(".gone")?.innerText ?? null,
            retired: anchor.componentId === null && anchor.classId === null,
            unlinked: internal.getAnchor(id) === null,
            panelGone: document.querySelector(".panel") === null,
          };
        }
        """
    )
    assert plain == {"text": "done", "retired": True, "unlinked": True, "panelGone": True}
    page.wait_for_function("Citry.events._internal.debug().bindingListenerTargets === 0")
    assert _citry_errors(messages) == []


# ----- reset and keyed linking under a parent render -----


def _make_list_app() -> tuple[Citry, type[Component], type[Component], type[Component]]:
    """A parent whose self-render carries a keyed child, an unkeyed child, and two keyed plain inputs."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ItemState:
        note: str = "srv"
        _public = ("note",)

    class Item(Component):
        citry = c
        State = ItemState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="item">
            <input class="note" :c-note="save" />
            <button class="go">go</button>
          </div>
        """

    class LooseState:
        note: str = "srv"
        _public = ("note",)

    class Loose(Component):
        citry = c
        State = LooseState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="loose">
            <span x-text="$state.note"></span>
          </div>
        """

    class ParentState:
        tick: int = 0
        _public = ("tick",)

    class Parent(Component):
        citry = c
        State = ParentState

        class Events:
            def refresh(self, state):
                return None

        template = """
          <div class="parent">
            <c-item #c-key="'k1'" />
            <c-loose />
            <c-for each="ident in idents">
              <input class="f" #c-key="ident" />
            </c-for>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"idents": kwargs["idents"]}

    return c, Parent, Item, Loose


def test_unkeyed_and_keyed_children_link_under_a_parent_render(page: Any, serve_live: Any) -> None:
    # One parent render exercises both correspondence paths. The unkeyed child
    # keeps positional same-class identity, including pending writes. The keyed
    # child links by its component-range key: the anchor with its draft, $loading
    # count, subscription, and epoch pair carries across, the horizon cut
    # arms, and the post-patch re-apply restores the draft into the bound
    # control. The component key lives on the invocation's virtual range,
    # never on the child's root element. The two keyed plain inputs swap
    # positions and their typed values travel through ordinary element keys.
    c, Parent, _Item, _Loose = _make_list_app()

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>linking</title></head>
            <body>
              <c-parent c-idents="[1, 2]" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    # Type into the two keyed plain inputs (real keyboard input, so the value
    # lives on the node the way a user's draft does).
    page.locator(".f").nth(0).fill("one")
    page.locator(".f").nth(1).fill("two")
    page.locator(".f").nth(0).focus()

    fresh = _fragment(Parent(idents=[2, 1]))  # the parent's re-render reorders the keyed inputs
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const parentId = document.querySelector(".parent").getAttribute("data-cid");
          const itemId = document.querySelector(".item").getAttribute("data-cid");
          const looseId = document.querySelector(".loose").getAttribute("data-cid");
          const parentAnchor = internal.getAnchor(parentId);
          const itemAnchor = internal.getAnchor(itemId);
          const looseAnchor = internal.getAnchor(looseId);

          itemAnchor.stateProxy.note = "draft-x"; // the keyed child's unsent draft
          itemAnchor.loading.any = 1; // an in-flight call's counter
          itemAnchor.epoch = 2; // two sends so far
          looseAnchor.stateProxy.note = "positional-draft"; // same-class unkeyed position links
          const unsub = Citry.events._onFor(itemId, "item:ping", (d) => window.__log.events.push(d));

          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );

          const freshItemId = document.querySelector(".item").getAttribute("data-cid");
          const freshLooseId = document.querySelector(".loose").getAttribute("data-cid");
          // The linked child still hears events addressed to its current id.
          await Citry.events.applyActions([
            { action: "event", eventName: "item:ping", detail: { n: 1 }, target: "render:" + freshItemId },
          ]);
          unsub();
          return {
            itemLinked: internal.getAnchor(freshItemId) === itemAnchor,
            itemAnchorId: itemAnchor.anchorId,
            draftKept: itemAnchor.pending.note === "draft-x",
            valueKept: itemAnchor.values.note === "draft-x",
            loadingKept: itemAnchor.loading.any === 1,
            horizonCut: itemAnchor.highestApplied === 2 && itemAnchor.epochOwner === null,
            inputRestored: document.querySelector(".item .note").value,
            componentKeyAbsent: !document.querySelector(".item").hasAttribute("data-citry-key"),
            looseLinked: internal.getAnchor(freshLooseId) === looseAnchor,
            looseRetired: looseAnchor.componentId === null,
            loosePending: looseAnchor.pending.note,
            flip: Array.from(document.querySelectorAll(".f")).map((el) => el.value),
            focusedValue: document.activeElement?.value,
            events: window.__log.events,
          };
        }
        """,
        [fresh],
    )

    assert result["itemLinked"] is True
    assert result["draftKept"] is True
    assert result["valueKept"] is True  # reconcile kept the pending field
    assert result["loadingKept"] is True
    assert result["horizonCut"] is True  # highest-applied jumped to the send counter at link time
    assert result["inputRestored"] == "draft-x"  # the post-patch re-apply restored the draft
    assert result["componentKeyAbsent"] is True
    assert result["looseLinked"] is True
    assert result["looseRetired"] is False
    assert result["loosePending"] == "positional-draft"
    assert result["flip"] == ["two", "one"]  # the typed values followed their keys through the reorder
    assert result["focusedValue"] == "one"  # moving the keyed node does not drop browser focus
    assert result["events"] == [{"n": 1}]  # the subscription reads the anchor's current id at fire time
    warning = [m for m in messages if "was reset or removed while holding" in m]
    assert warning == []
    assert _citry_errors(messages) == []


def test_keyed_childs_own_self_render_keeps_the_key_and_links_again(page: Any, serve_live: Any) -> None:
    # A parent's #c-key belongs to the child's logical invocation range. A
    # child's own same-class render therefore keeps the parent-authored key on
    # the logical state without copying it onto the root DOM element. The root
    # patches in place and the next parent render links the same anchor again.
    c, Parent, Item, _Loose = _make_list_app()

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>key carriage</title></head>
            <body>
              <c-parent c-idents="[1]" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    parent_html_1 = _fragment(Parent(idents=[1]))
    child_html = _fragment(Item(note="self-rendered"))
    parent_html_2 = _fragment(Parent(idents=[1]))
    result = page.evaluate(
        """
        async ([parentHtml1, childHtml, parentHtml2]) => {
          const internal = Citry.events._internal;
          const parentId = document.querySelector(".parent").getAttribute("data-cid");
          const parentAnchor = internal.getAnchor(parentId);
          const itemAnchor = internal.getAnchor(document.querySelector(".item").getAttribute("data-cid"));

          // Parent render 1 links the keyed child (the horizon cut arms).
          itemAnchor.epoch = 1;
          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html: parentHtml1 }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );

          // The child's own next call applies (epoch 2 clears the cut at 1).
          const linkedId = itemAnchor.componentId;
          const rootBefore = document.querySelector(".item");
          itemAnchor.epoch = 2;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{ action: "render", target: "render:" + linkedId, swap: "morph", html: childHtml }],
            },
            { anchor: itemAnchor, instance: linkedId, event: "save" },
          );
          const rootAfterSelf = document.querySelector(".item");
          const afterSelf = {
            applied: itemAnchor.values.note === "self-rendered",
            componentKeyAbsent: !rootAfterSelf.hasAttribute("data-citry-key"),
            patchedInPlace: rootAfterSelf === rootBefore,
          };

          // Parent render 2 still finds the key and links the same anchor.
          const parentId2 = parentAnchor.componentId;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{ action: "render", target: "render:" + parentId2, swap: "morph", html: parentHtml2 }],
            },
            { anchor: parentAnchor, instance: parentId2, event: "refresh" },
          );
          const finalItemId = document.querySelector(".item").getAttribute("data-cid");
          return {
            afterSelf,
            linkedAgain: internal.getAnchor(finalItemId) === itemAnchor,
          };
        }
        """,
        [parent_html_1, child_html, parent_html_2],
    )

    assert result["afterSelf"]["applied"] is True
    assert result["afterSelf"]["componentKeyAbsent"] is True
    assert result["afterSelf"]["patchedInPlace"] is True
    assert result["linkedAgain"] is True
    assert _citry_errors(messages) == []


def test_horizon_cut_drops_a_linked_childs_in_flight_render_while_data_resolves(page: Any, serve_live: Any) -> None:
    # The one sub-rule riding every link: after the parent's render linked
    # the child, the child's own in-flight response arrives. Its epoch is not
    # newer than the horizon (and the owner token was reset), so its
    # instance-mutating render drops with reason `epoch`, while its `data`
    # still resolves the caller's promise.
    c, Parent, Item, _Loose = _make_list_app()

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>horizon</title></head>
            <body>
              <c-parent c-idents="[1]" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    parent_html = _fragment(Parent(idents=[1]))
    late_child_html = _fragment(Item(note="late-response"))
    result = page.evaluate(
        """
        async ([parentHtml, childHtml]) => {
          const internal = Citry.events._internal;
          const parentId = document.querySelector(".parent").getAttribute("data-cid");
          const childId = document.querySelector(".item").getAttribute("data-cid");
          const parentAnchor = internal.getAnchor(parentId);
          const childAnchor = internal.getAnchor(childId);
          childAnchor.epoch = 1; // the in-flight call's send already counted

          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html: parentHtml }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const linkedId = document.querySelector(".item").getAttribute("data-cid");

          // The child's own response lands late: epoch 1 against the cut.
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [
                { action: "render", target: "render:" + childId, swap: "morph", html: childHtml },
                { action: "data", value: { saved: true } },
              ],
            },
            { anchor: childAnchor, instance: childId, event: "save", onData: (v) => window.__log.data.push(v) },
          );
          return {
            domIdUnchanged: document.querySelector(".item").getAttribute("data-cid") === linkedId,
            note: childAnchor.values.note,
            stale: window.__log.stale,
            data: window.__log.data,
          };
        }
        """,
        [parent_html, late_child_html],
    )

    assert result["domIdUnchanged"] is True  # the late render never landed
    assert result["note"] == "srv"  # the parent-render state stands, not the late response's
    assert result["data"] == [{"saved": True}]  # the caller's own promise value still resolved
    assert len(result["stale"]) == 1
    assert result["stale"][0]["reason"] == "epoch"
    assert result["stale"][0]["event"] == "save"
    assert _citry_errors(messages) == []


# ----- targeted renders -----


def test_selector_target_resets_through_an_unmatched_component_boundary(page: Any, serve_live: Any) -> None:
    # A selector target has no explicit component-root correlation. Its
    # enclosing PanelBody invocation is therefore unmatched and opaque, so a
    # keyed Item inside that virtual boundary does not leak out and match by a
    # region-wide scan. Driven through the public applyActions entry point.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ItemState:
        note: str = "srv"
        _public = ("note",)

    class Item(Component):
        citry = c
        State = ItemState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="item">
            <input class="note" :c-note="save" />
          </div>
        """

    class WidgetState:
        n: int = 0
        _public = ("n",)

    class Widget(Component):
        citry = c
        State = WidgetState

        class Events:
            def bump(self, state):
                return None

        template = """
          <div class="widget">
            <span x-text="$state.n"></span>
          </div>
        """

    class PanelBody(Component):
        citry = c
        template = """
          <div id="panel">
            <c-item #c-key="'keep'" />
            <c-widget />
            <p class="stamp">{{ stamp }}</p>
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"stamp": kwargs["stamp"]}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>targeted</title></head>
            <body>
              <c-panel-body c-stamp="'v1'" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    fresh = _fragment(PanelBody(stamp="v2"))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const itemId = document.querySelector(".item").getAttribute("data-cid");
          const widgetId = document.querySelector(".widget").getAttribute("data-cid");
          const itemAnchor = internal.getAnchor(itemId);
          const widgetAnchor = internal.getAnchor(widgetId);
          itemAnchor.stateProxy.note = "draft-kept";

          await Citry.events.applyActions([{ action: "render", target: "#panel", swap: "morph", html }]);

          const freshItemId = document.querySelector(".item").getAttribute("data-cid");
          const freshWidgetId = document.querySelector(".widget").getAttribute("data-cid");
          const freshItemAnchor = internal.getAnchor(freshItemId);
          return {
            stamp: document.querySelector(".stamp").innerText,
            itemLinked: internal.getAnchor(freshItemId) === itemAnchor,
            itemRetired: itemAnchor.componentId === null,
            freshItemPending: Object.keys(freshItemAnchor.pending).length,
            inputRestored: document.querySelector(".item .note").value,
            widgetReset: internal.getAnchor(freshWidgetId) !== widgetAnchor,
            widgetRetired: widgetAnchor.componentId === null,
          };
        }
        """,
        [fresh],
    )

    assert result["stamp"] == "v2"  # the region shows exactly what the handler returned
    assert result["itemLinked"] is False
    assert result["itemRetired"] is True
    assert result["freshItemPending"] == 0
    assert result["inputRestored"] == "srv"
    assert result["widgetReset"] is True
    assert result["widgetRetired"] is True
    assert _citry_errors(messages) == []


def test_per_action_liveness_drops_the_self_render_after_the_caller_retired(page: Any, serve_live: Any) -> None:
    # Machinery item 4, both spans. Within one result: an earlier targeted
    # render replaces the region containing the caller, so the caller's
    # following self-render drops with reason `retired` while its `data`
    # still resolves. Across results in one batch envelope: an earlier
    # result's render retires a later result's caller the same way.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ActorState:
        n: int = 0
        _public = ("n",)

    class Actor(Component):
        citry = c
        State = ActorState

        class Events:
            def rebuild(self, state):
                return None

        template = """
          <div class="actor">
            <span x-text="$state.n"></span>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>liveness</title></head>
            <body>
              <div id="zone-a"><c-actor /></div>
              <div id="zone-b"><c-actor /></div>
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    actor_a_html = _fragment(Actor(n=1))
    actor_b_html = _fragment(Actor(n=2))
    result = page.evaluate(
        """
        async ([actorAHtml, actorBHtml]) => {
          const internal = Citry.events._internal;
          const aId = document.querySelector("#zone-a .actor").getAttribute("data-cid");
          const bId = document.querySelector("#zone-b .actor").getAttribute("data-cid");
          const aAnchor = internal.getAnchor(aId);
          const bAnchor = internal.getAnchor(bId);

          // Within one result: the targeted render retires the caller, then
          // the caller's own self-render must drop and its data still lands.
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [
                { action: "render", target: "#zone-a", swap: "replace", html: "<div id='zone-a'>rebuilt</div>" },
                { action: "render", target: "render:" + aId, swap: "morph", html: actorAHtml },
                { action: "data", value: "a-done" },
              ],
            },
            { anchor: aAnchor, instance: aId, event: "rebuild", onData: (v) => window.__log.data.push(v) },
          );
          const withinResult = {
            zone: document.querySelector("#zone-a").innerText,
            retired: aAnchor.componentId === null,
            selfRenderDropped: document.querySelector("#zone-a .actor") === null,
          };

          // Across results in one batch envelope: result 0 retires B's zone,
          // result 1 is B's own response.
          await internal.applyEnvelope(
            [
              {
                ok: true,
                actions: [
                  { action: "render", target: "#zone-b", swap: "replace", html: "<div id='zone-b'>rebuilt-b</div>" },
                ],
              },
              {
                ok: true,
                sendSequence: 1,
                actions: [
                  { action: "render", target: "render:" + bId, swap: "morph", html: actorBHtml },
                  { action: "data", value: "b-done" },
                ],
              },
            ],
            [
              null,
              { anchor: bAnchor, instance: bId, event: "rebuild", onData: (v) => window.__log.data.push(v) },
            ],
          );
          return {
            aId,
            bId,
            withinResult,
            bRetired: bAnchor.componentId === null,
            bZone: document.querySelector("#zone-b").innerText,
            stale: window.__log.stale.map((s) => s.reason),
            data: window.__log.data,
          };
        }
        """,
        [actor_a_html, actor_b_html],
    )

    assert result["withinResult"] == {"zone": "rebuilt", "retired": True, "selfRenderDropped": True}
    assert result["bRetired"] is True
    assert result["bZone"] == "rebuilt-b"
    assert result["stale"] == ["retired", "retired"]  # one drop per dead self-render, no other drops
    assert result["data"] == ["a-done", "b-done"]  # data resolves whatever else dropped
    retired_debug = [message for message in messages if message.startswith("debug:") and "instance retired" in message]
    assert retired_debug == [
        f"debug:[Citry] events: dropped a render for instance '{result['aId']}'"
        " (the instance retired, design 5.5 machinery item 4).",
        f"debug:[Citry] events: dropped a render for instance '{result['bId']}'"
        " (the instance retired, design 5.5 machinery item 4).",
    ]
    assert _citry_errors(messages) == []


def test_multi_target_render_mirrors_one_instance_and_strips_duplicate_tags(page: Any, serve_live: Any) -> None:
    # A selector matching several elements inserts one shared instance,
    # mirrored per match: one instance id, one anchor, one State, and the
    # trailing manifest tags ride only the first insertion (machinery item
    # 2's multi-target rule). A later correlated self-render applies to each
    # copy independently and still inserts the tags once.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Sub(Component):
        citry = c
        template = '<aside class="badge-sub"><input class="sub-draft" /><span>sub</span></aside>'

    class Frame(Component):
        citry = c

        class Kwargs:
            count: int

        template = '<div class="region-shell" c-data-count="count"><c-slot /></div>'

        def template_data(self, kwargs, slots):
            return {"count": kwargs.count}

    class BadgeState:
        count: int = 0
        _public = ("count",)

    class Badge(Component):
        citry = c
        State = BadgeState

        class Events:
            def bump(self, state):
                return None

        template = """
          <div class="badge" x-data="{ local: 0 }">
            <span class="c" x-text="$state.count"></span>
            <button class="local" @click="local += 1" x-text="local"></button>
            <c-sub #c-key="'stable-sub'" />
            <c-frame c-count="count" #c-key="'stable-provider'">
              <input class="badge-region-draft" #c-key="'region-input'" c-value="count" />
            </c-frame>
          </div>
        """

    class PingState:
        n: int = 0
        _public = ("n",)

    class Ping(Component):
        citry = c
        State = PingState

        class Events:
            def ping(self, state):
                return None

        template = """
          <div class="ping"></div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>mirror</title></head>
            <body>
              <div class="slot" id="s1"></div>
              <div class="slot" id="s2"></div>
              <c-ping />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    badge_html = _fragment(Badge(count=1))
    inserted = page.evaluate(
        """
        async ([html]) => {
          await Citry.events.applyActions([{ action: "render", target: ".slot", swap: "inner", html }]);
          const ids = Array.from(document.querySelectorAll(".badge")).map((el) => el.getAttribute("data-cid"));
          const ownership = Citry.manager.ownership;
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, ids[0]));
          const route = ownership.forRender(revision, ids[0]);
          const placements = ownership.get(revision).registry.physicalPlacements.get(route.instance.key);
          return {
            ids,
            sharedId: ids.length === 2 && ids[0] === ids[1],
            tagsInS1: document.querySelectorAll("#s1 script[data-citry-events]").length,
            tagsInS2: document.querySelectorAll("#s2 script[data-citry-events]").length,
            depsTagsInS2: document.querySelectorAll("#s2 script[data-citry]").length,
            placements: placements.map((placement) => ({
              id: placement.placementId,
              marker: placement.start.data,
              connected: placement.start.isConnected && placement.end.isConnected,
            })),
          };
        }
        """,
        [badge_html],
    )
    assert inserted["sharedId"] is True
    assert inserted["tagsInS1"] == 1  # the first insertion carries the manifest tags
    assert inserted["tagsInS2"] == 0  # the mirror copy is stripped of them
    assert inserted["depsTagsInS2"] == 0
    assert inserted["placements"][0]["id"] is None
    assert inserted["placements"][0]["marker"].startswith("citry:g1:")
    assert isinstance(inserted["placements"][1]["id"], str)
    assert inserted["placements"][1]["marker"].startswith("citry:p1:")
    assert all(placement["connected"] for placement in inserted["placements"])

    # One shared anchor: a $state write in one copy reflects in both.
    page.evaluate(
        """
        () => {
          const id = document.querySelector(".badge").getAttribute("data-cid");
          Citry.events._internal.getAnchor(id).stateProxy.count = 7;
        }
        """
    )
    page.wait_for_function(
        "Array.from(document.querySelectorAll('.badge .c')).map((el) => el.innerText).join(',') === '7,7'"
    )

    # Each physical placement keeps its own ordinary Alpine state.
    page.locator(".badge .local").nth(0).click()
    page.locator(".badge .local").nth(1).click(click_count=2)
    assert page.locator(".badge .local").all_inner_texts() == ["1", "2"]

    # A correlated self-render of the mirrored instance patches each copy
    # independently, keeps the one anchor, and adds the tags exactly once.
    fresh_badge = _fragment(Badge(count=9))
    mirrored = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const oldId = document.querySelector(".badge").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          const oldSubRoots = Array.from(document.querySelectorAll(".badge-sub"));
          const oldSubId = oldSubRoots[0].getAttribute("data-cid");
          const oldSubRevision = ownership.revisions().find((candidate) => ownership.forRender(candidate, oldSubId));
          const oldSubRoute = ownership.forRender(oldSubRevision, oldSubId);
          const oldSubPlacements = ownership
            .get(oldSubRevision)
            .registry.physicalPlacements.get(oldSubRoute.instance.key);
          oldSubRoots.forEach((root, index) => { root.querySelector(".sub-draft").value = `sub-${index}`; });
          const oldRegionInputs = Array.from(document.querySelectorAll(".badge-region-draft"));
          oldRegionInputs.forEach((input, index) => { input.value = `region-${index}`; });
          document.querySelectorAll(".region-shell")[0].setAttribute("data-citry-morph", "ignore");
          const oldBadgeState = ownership.get(oldSubRevision);
          const oldRegion = Array.from(oldBadgeState.registry.slotRegions.values()).find(
            (candidate) => oldBadgeState.registry.physicalPlacements.get(candidate.key).length === 2,
          );
          const oldRegionPlacements = oldBadgeState.registry.physicalPlacements.get(oldRegion.key);
          const tagsBefore = document.querySelectorAll("script[data-citry-events]").length;
          delete anchor.pending.count; // the write above rode a send; the server may win the field again
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor, instance: oldId, event: "bump" },
          );
          const ids = Array.from(document.querySelectorAll(".badge")).map((el) => el.getAttribute("data-cid"));
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, ids[0]));
          const route = ownership.forRender(revision, ids[0]);
          const placements = ownership.get(revision).registry.physicalPlacements.get(route.instance.key);
          const subRoots = Array.from(document.querySelectorAll(".badge-sub"));
          const subId = subRoots[0].getAttribute("data-cid");
          const subRevision = ownership.revisions().find((candidate) => ownership.forRender(candidate, subId));
          const subRoute = ownership.forRender(subRevision, subId);
          const subPlacements = ownership.get(subRevision).registry.physicalPlacements.get(subRoute.instance.key);
          const regionInputs = Array.from(document.querySelectorAll(".badge-region-draft"));
          const regionPlacements = oldBadgeState.registry.physicalPlacements.get(oldRegion.key);
          return {
            ids,
            bothFresh: ids.length === 2 && ids[0] === ids[1] && ids[0] !== oldId,
            sameAnchor: internal.getAnchor(ids[0]) === anchor,
            count: anchor.values.count,
            tagsAdded: document.querySelectorAll("script[data-citry-events]").length - tagsBefore,
            placements: placements.map((placement) => placement.placementId),
            nested: {
              rootsKept: subRoots.every((root, index) => root === oldSubRoots[index]),
              drafts: subRoots.map((root) => root.querySelector(".sub-draft").value),
              anchorKept: subRoute.anchor === oldSubRoute.anchor,
              logicalKept: subRoute.logicalInstance === oldSubRoute.logicalInstance,
              capsKept: subPlacements.every(
                (placement, index) =>
                  placement.start === oldSubPlacements[index].start && placement.end === oldSubPlacements[index].end,
              ),
            },
            region: {
              shellCounts: Array.from(document.querySelectorAll(".region-shell")).map(
                (shell) => shell.getAttribute("data-count"),
              ),
              rootsKept: regionInputs.every((input, index) => input === oldRegionInputs[index]),
              drafts: regionInputs.map((input) => input.value),
              freshValues: regionInputs.map((input) => input.getAttribute("value")),
              capsKept: regionPlacements.every(
                (placement, index) =>
                  placement.start === oldRegionPlacements[index].start &&
                  placement.end === oldRegionPlacements[index].end,
              ),
              placements: regionPlacements.map((placement) => placement.placementId),
              markers: regionPlacements.map((placement) => placement.start.data),
              oldRevisionKept: ownership.revisions().includes(oldSubRevision),
            },
          };
        }
        """,
        [fresh_badge],
    )
    assert mirrored["bothFresh"] is True
    assert mirrored["sameAnchor"] is True
    assert mirrored["count"] == 9
    assert mirrored["tagsAdded"] == 1
    assert mirrored["placements"][0] is None
    assert isinstance(mirrored["placements"][1], str)
    assert mirrored["nested"] == {
        "rootsKept": True,
        "drafts": ["sub-0", "sub-1"],
        "anchorKept": True,
        "logicalKept": True,
        "capsKept": True,
    }
    assert mirrored["region"]["rootsKept"] is True
    assert mirrored["region"]["shellCounts"] == ["1", "9"]
    assert mirrored["region"]["drafts"] == ["region-0", "region-1"]
    assert mirrored["region"]["freshValues"] == ["1", "1"]
    assert mirrored["region"]["capsKept"] is True
    assert mirrored["region"]["oldRevisionKept"] is True
    assert mirrored["region"]["placements"][0] is None
    assert isinstance(mirrored["region"]["placements"][1], str)
    assert mirrored["region"]["markers"][0].startswith("citry:g1:")
    assert mirrored["region"]["markers"][1].startswith("citry:p1:")
    page.wait_for_function(
        "Array.from(document.querySelectorAll('.badge .c')).map((el) => el.innerText).join(',') === '9,9'"
    )
    assert page.locator(".badge .local").all_inner_texts() == ["1", "2"]
    assert _citry_errors(messages) == []


def test_adjacent_mirror_placements_self_render_independently_and_event_dispatches_once(
    page: Any, serve_live: Any
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class TileState:
        n: int = 0
        _public = ("n",)

    class Tile(Component):
        citry = c
        State = TileState

        class Events:
            def refresh(self, state):
                return None

        template = """
          <div class="tile" x-text="$state.n"></div>
        """

    class Boot(Component):
        citry = c

        class Events:
            def ready(self):
                return None

        template = """
          <i class="boot"></i>
        """

    class Page(Component):
        citry = c
        template = """
          <html><body>
            <main id="copies"><div class="slot"></div><div class="slot"></div></main><c-boot />
          </body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    first = _fragment(Tile(n=1))
    fresh = _fragment(Tile(n=2))
    result = page.evaluate(
        """async ([first, fresh]) => {
          await Citry.events.applyActions([{ action: 'render', target: '.slot', swap: 'replace', html: first }]);
          // Processed manifest tags are not part of either visual placement.
          // Removing them makes the two single-root copies element-adjacent,
          // the shape that sibling-run inference used to collapse.
          document.querySelectorAll('#copies script').forEach((tag) => tag.remove());
          const oldId = document.querySelector('.tile').getAttribute('data-cid');
          const anchor = Citry.events._internal.getAnchor(oldId);
          const initiallyAdjacent = document.querySelectorAll('.tile')[0].nextElementSibling ===
            document.querySelectorAll('.tile')[1];
          let documentEvents = 0;
          let firstRootEvents = 0;
          let secondRootEvents = 0;
          document.addEventListener('tile:done', () => { documentEvents += 1; });
          document.querySelectorAll('.tile')[0].addEventListener('tile:done', () => { firstRootEvents += 1; });
          document.querySelectorAll('.tile')[1].addEventListener('tile:done', () => { secondRootEvents += 1; });
          await Citry.events.applyActions([{
            action: 'event', eventName: 'tile:done', target: 'render:' + oldId,
          }]);
          anchor.epoch = 1;
          await Citry.events._internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: 'render', target: 'render:' + oldId, swap: 'morph', html: fresh }],
            },
            { anchor, instance: oldId, event: 'refresh' },
          );
          const tiles = Array.from(document.querySelectorAll('.tile'));
          return {
            initiallyAdjacent,
            count: tiles.length,
            values: tiles.map((tile) => tile.textContent),
            sharedFreshId:
              tiles.length === 2 &&
              tiles[0].getAttribute('data-cid') === tiles[1].getAttribute('data-cid'),
            documentEvents,
            firstRootEvents,
            secondRootEvents,
          };
        }""",
        [first, fresh],
    )
    assert result.pop("initiallyAdjacent") is True
    assert result == {
        "count": 2,
        "values": ["2", "2"],
        "sharedFreshId": True,
        "documentEvents": 1,
        "firstRootEvents": 1,
        "secondRootEvents": 0,
    }
    assert _citry_errors(messages) == []


def test_corrupt_mirror_rejects_without_partial_incoming_adoption(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Tile(Component):
        citry = c

        class State:
            n: int = 0
            _public = ("n",)

        class Events:
            def refresh(self, state):
                return None

        template = '<div class="corrupt-tile">{{ label }}</div>'

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Boot(Component):
        citry = c

        class Events:
            def ready(self):
                return None

        template = "<i>boot</i>"

    class Page(Component):
        citry = c
        template = """
          <html><body><div class="corrupt-slot"></div><div class="corrupt-slot"></div><c-boot /></body></html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    first = _fragment(Tile(label="old"))
    fresh = _fragment(Tile(label="new"))
    result = page.evaluate(
        """
        async ([first, fresh]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          await Citry.events.applyActions([{ action: "render", target: ".corrupt-slot", swap: "inner", html: first }]);
          const oldId = document.querySelector(".corrupt-tile").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          const revision = ownership.revisions().find((candidate) => ownership.forRender(candidate, oldId));
          const route = ownership.forRender(revision, oldId);
          const placements = ownership.get(revision).registry.physicalPlacements.get(route.instance.key);
          placements[1].start.data += ":corrupt";
          const incoming = document.createElement("template");
          incoming.innerHTML = fresh;
          const graph = JSON.parse(incoming.content.querySelector("script[data-citry-graph]").textContent);
          const incomingIds = graph.graphs.flatMap((entry) =>
            entry.componentInstances.map((instance) => instance.renderId),
          );
          let error = null;
          anchor.epoch = 1;
          try {
            await internal.applyResult(
              {
                ok: true,
                sendSequence: 1,
                actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html: fresh }],
              },
              { anchor, instance: oldId, event: "refresh" },
            );
          } catch (caught) {
            error = String(caught && caught.message ? caught.message : caught);
          }
          return {
            error,
            texts: Array.from(document.querySelectorAll(".corrupt-tile")).map((element) => element.textContent),
            anchorKept: internal.getAnchor(oldId) === anchor,
            incomingAnchors: incomingIds.filter((renderId) => internal.getAnchor(renderId)).length,
          };
        }
        """,
        [first, fresh],
    )
    assert result["error"] is not None
    assert "one physical placement" in result["error"]
    assert result["texts"] == []  # landed corruption fails closed for the whole shared range
    assert result["anchorKept"] is False
    assert result["incomingAnchors"] == 0
    expected_errors = [message for message in _citry_errors(messages) if "ownership range" in message]
    assert len(expected_errors) <= 1


# ----- the epoch guard at apply time -----


def test_stale_epoch_response_drops_instance_mutations_but_resolves_data(page: Any, serve_live: Any) -> None:
    # The out-of-order guard (design 4.2) at apply time: the newer response
    # applies first, then the older one arrives. Its self-render and token
    # refresh drop (one `epoch` drop event per result, with the detail
    # contract), while its `data` still resolves the caller's promise.
    c, Todo, Page = _make_todo_app()
    messages = _goto(page, serve_live, c, str(Page()))

    html_b = _fragment(Todo(query="newer", count=2))
    result = page.evaluate(
        """
        async ([htmlB]) => {
          const internal = Citry.events._internal;
          const oldId = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          anchor.epoch = 2; // two sends in flight

          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [
                { action: "render", target: "render:" + oldId, swap: "morph", html: htmlB },
                { action: "data", value: "B" },
              ],
            },
            { anchor, instance: oldId, event: "save", onData: (v) => window.__log.data.push(v) },
          );
          const idAfterB = document.querySelector(".todo").getAttribute("data-cid");
          const tokenAfterB = anchor.token;

          // The slower first send answers second: epoch 1 against highest 2.
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [
                { action: "state", targetRenderId: oldId, stateToken: "tok-stale" },
                { action: "render", target: "render:" + oldId, swap: "morph", html: "<div class='todo'>stale</div>" },
                { action: "data", value: "A" },
              ],
            },
            { anchor, instance: oldId, event: "save", onData: (v) => window.__log.data.push(v) },
          );
          return {
            idUnchanged: document.querySelector(".todo").getAttribute("data-cid") === idAfterB,
            query: anchor.values.query,
            tokenUnchanged: anchor.token === tokenAfterB && anchor.token !== "tok-stale",
            data: window.__log.data,
            stale: window.__log.stale,
            highestApplied: anchor.highestApplied,
          };
        }
        """,
        [html_b],
    )

    assert result["idUnchanged"] is True  # the stale render never rolled the DOM back
    assert result["query"] == "newer"
    assert result["tokenUnchanged"] is True  # the stale token refresh dropped too
    assert result["data"] == ["B", "A"]  # both promises resolved with their own values
    assert result["highestApplied"] == 2
    # One drop event per stale result, carrying the {instance, class, event,
    # reason} detail contract.
    assert len(result["stale"]) == 1
    stale = result["stale"][0]
    assert stale["reason"] == "epoch"
    assert stale["event"] == "save"
    assert stale["cls"] == Todo.class_id
    assert stale["instance"] is not None
    stale_debug = [message for message in messages if message.startswith("debug:") and "stale response" in message]
    assert stale_debug == [
        "debug:[Citry] events: dropped a state token refresh of a stale response (epoch 1, highest applied 2).",
        "debug:[Citry] events: dropped a self-render of a stale response (epoch 1, highest applied 2).",
    ]
    assert _citry_errors(messages) == []


# ----- preservation -----


def test_preservation_poles_fast_typing_keeps_drafts_and_submit_then_clear_clears(page: Any, serve_live: Any) -> None:
    # The two acceptance poles of design 5.5's preservation block, plus the
    # mid-debounce stage. A focused two-way control with a pending unsent
    # write keeps its typed value and caret through a patch (the guard), and
    # the post-patch re-apply skips it (never undoing the guard). A control
    # holding only an unflushed DOM draft (marked through the drafts record
    # this package defines for the forms runtime) is kept the same way. A
    # flushed control (nothing unsent) takes the server's value even while
    # focused: submit-then-clear lands.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class FormState:
        query: str = ""
        _public = ("query",)

    class Form(Component):
        citry = c
        State = FormState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="form">
            <input class="q" :c-query="save" />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>poles</title></head>
            <body>
              <c-form query="start" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    # Pole 1a: a pending unsent $state write, control focused mid-edit.
    server_html = _fragment(Form(query="server-q"))
    pole_1a = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".form").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const input = document.querySelector(".q");
          input.value = "draft";
          input.focus();
          input.setSelectionRange(3, 3);
          anchor.stateProxy.query = "draft"; // the flushed-but-unsent stage
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "save" },
          );
          const after = document.querySelector(".q");
          return {
            value: after.value,
            caret: after.selectionStart,
            focused: document.activeElement === after,
            sameElement: after === input,
            stateValue: anchor.values.query,
          };
        }
        """,
        [server_html],
    )
    assert pole_1a == {
        "value": "draft",
        "caret": 3,
        "focused": True,
        "sameElement": True,
        "stateValue": "draft",  # the pending write kept its field through the reconcile
    }

    # Pole 1b: the mid-debounce stage: the DOM holds a draft the flush has
    # not yet written into $state; the drafts record marks the control.
    server_html_2 = _fragment(Form(query="server-2"))
    pole_1b = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".form").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          delete anchor.pending.query; // the previous pole's write is "sent" now
          const input = document.querySelector(".q");
          input.value = "ab";
          input.focus();
          input.setSelectionRange(2, 2);
          internal.drafts.mark(input); // what the forms runtime does while a flush timer pends
          anchor.epoch = 2;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "save" },
          );
          const after = document.querySelector(".q");
          internal.drafts.clear(input);
          return { value: after.value, caret: after.selectionStart, stateValue: anchor.values.query };
        }
        """,
        [server_html_2],
    )
    assert pole_1b == {"value": "ab", "caret": 2, "stateValue": "server-2"}

    # Pole 2: submit-then-clear: nothing unsent, so the still-focused control
    # takes the server's cleared value.
    cleared_html = _fragment(Form(query=""))
    pole_2 = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".form").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const input = document.querySelector(".q");
          input.value = "sent already";
          input.focus();
          anchor.epoch = 3;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 3,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "save" },
          );
          const after = document.querySelector(".q");
          return { value: after.value, focused: document.activeElement === after, stateValue: anchor.values.query };
        }
        """,
        [cleared_html],
    )
    assert pole_2 == {"value": "", "focused": True, "stateValue": ""}
    assert _citry_errors(messages) == []


def test_ignore_marker_preserves_nested_ranges_and_excludes_incoming_dependencies(
    page: Any,
    serve_live: Any,
) -> None:
    # `#c-ignore` compiles to the runtime marker the morph hook reads: the
    # subtree another library owns stays untouched while everything else
    # patches. A nested ComponentRange is retained with that ignored branch,
    # and an incoming-only component inside the branch never inserts or runs
    # its component dependency.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class RootIgnored(Component):
        citry = c

        class State:
            n: int = 0
            _public = ("n",)

        class Events:
            def bump(self, state):
                return None

        template = """
          <div #c-ignore class="child-root">{{ label }}</div>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class HostState:
        tick: int = 0
        _public = ("tick",)

    class Nested(Component):
        citry = c

        class State:
            n: int = 0
            _public = ("n",)

        class Events:
            def bump(self, state):
                return None

        template = """
          <strong class="inside-range">{{ label }}</strong>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class IncomingOnly(Component):
        citry = c
        js = """
          $component(() => {
            window.__excludedDependencyFired = (window.__excludedDependencyFired || 0) + 1;
          });
        """
        css = """
          .incoming-only { --excluded-style: 1; }
        """
        template = """
          <aside class="incoming-only">incoming</aside>
        """

    class Host(Component):
        citry = c
        State = HostState

        class Events:
            def refresh(self, state):
                return None

        template = """
          <div class="host">
            <div class="keep" #c-ignore>
              <span class="lib">{{ owned }}</span>
              <c-nested c-label="owned" />
              <c-if cond="show">
                <c-root-ignored c-label="'excluded-x'" />
                <c-incoming-only />
              </c-if>
            </div>
            <p class="server">{{ owned }}</p>
            <div class="keyed-wrap"><c-nested c-label="owned" #c-key="'k'" /></div>
            <c-root-ignored c-label="owned" />
          </div>
        """

        def template_data(self, kwargs, slots):
            return {"owned": kwargs["owned"], "show": kwargs["show"]}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>ignore</title></head>
            <body>
              <c-host c-owned="'v1'" c-show="False" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    fresh = _fragment(Host(owned="v2", show=True))
    replacement = _fragment(Host(owned="v3", show=False))
    result = page.evaluate(
        """
        async ([html, incomingClass, replacementHtml]) => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".host").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const initialRevision = anchor.descriptorRevision;
          const nestedId = document.querySelector(".inside-range").getAttribute("data-cid");
          const nestedAnchor = internal.getAnchor(nestedId);
          const activeChildId = document.querySelector(".child-root").getAttribute("data-cid");
          const activeChildAnchor = internal.getAnchor(activeChildId);
          const incoming = document.createElement("template");
          incoming.innerHTML = html;
          const graphManifest = JSON.parse(incoming.content.querySelector("script[data-citry-graph]").textContent);
          const incomingRevision = graphManifest.revision;
          const incomingIds = new Set(
            graphManifest.graphs.flatMap((graph) =>
              graph.componentInstances
                .filter((instance) => instance.classId === incomingClass)
                .map((instance) => instance.renderId),
            ),
          );
          const dependencyManifest = JSON.parse(
            incoming.content.querySelector("script[data-citry]:not([data-citry-events])").textContent,
          );
          const decode = (value) => decodeURIComponent(escape(atob(value)));
          const excludedDescriptors = [
            ...dependencyManifest.fetch.js,
            ...dependencyManifest.fetch.css,
          ]
            .filter((entry) => entry[1]?.some((owner) => incomingIds.has(decode(owner))))
            .map((entry) => JSON.parse(decode(entry[0])));
          const eventsTag = incoming.content.querySelector("script[data-citry-events]");
          const eventsManifest = JSON.parse(eventsTag.textContent);
          const nestedDescriptor = eventsManifest.componentClasses.find(
            (descriptor) => descriptor.componentClassId === nestedAnchor.classId,
          );
          nestedDescriptor.eventHandlers = {};
          eventsTag.textContent = JSON.stringify(eventsManifest);
          html = incoming.innerHTML;
          // A third-party library mutated its owned subtree client-side.
          const lib = document.querySelector(".keep .lib");
          lib.setAttribute("data-lib", "y");
          lib.textContent = "client-owned";
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "refresh" },
          );
          await new Promise((resolve) => setTimeout(resolve, 0));
          let retainedCall = null;
          internal.setTransport((call) => {
            retainedCall = call;
            return { ok: true };
          });
          await Citry.events.send(document.querySelector(".inside-range"), "bump");
          const retained = {
            libText: document.querySelector(".keep .lib").textContent,
            libAttr: document.querySelector(".keep .lib").getAttribute("data-lib"),
            serverText: document.querySelector(".server").innerText,
            childText: document.querySelector(".child-root").innerText,
            activeChildLinked:
              internal.getAnchor(document.querySelector(".child-root").getAttribute("data-cid")) === activeChildAnchor,
            nestedText: document.querySelector(".inside-range").innerText,
            nestedLinked:
              internal.getAnchor(document.querySelector(".inside-range").getAttribute("data-cid")) === nestedAnchor,
            incomingPresent: Boolean(document.querySelector(".incoming-only")),
            excludedDependencyFired: window.__excludedDependencyFired || 0,
            retainedHandler: retainedCall && retainedCall.handlerName,
            excludedAnchorCount: Array.from(incomingIds).filter((incomingId) => internal.getAnchor(incomingId)).length,
            excludedAssetsInserted: excludedDescriptors.filter((descriptor) => {
              const url = descriptor.attrs && (descriptor.attrs.src || descriptor.attrs.href);
              if (url) {
                return Array.from(document.querySelectorAll(descriptor.tag)).some(
                  (element) => element.getAttribute("src") === url || element.getAttribute("href") === url,
                );
              }
              return Array.from(document.querySelectorAll(descriptor.tag)).some(
                (element) => element.textContent === (descriptor.content || ""),
              );
            }).length,
            excludedResourcesFetched: excludedDescriptors.filter((descriptor) => {
              const url = descriptor.attrs && (descriptor.attrs.src || descriptor.attrs.href);
              return url && performance.getEntriesByType("resource").some((entry) => entry.name.includes(url));
            }).length,
          };
          const revisionsWhileRetained = Array.from(internal.descriptorRevisions.keys());
          const replacement = document.createElement("template");
          replacement.innerHTML = replacementHtml;
          const replacementRevision = JSON.parse(
            replacement.content.querySelector("script[data-citry-graph]").textContent,
          ).revision;
          const activeId = anchor.componentId;
          anchor.epoch = 2;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 2,
              actions: [{ action: "render", target: "render:" + activeId, swap: "replace", html: replacementHtml }],
            },
            { anchor, instance: activeId, event: "refresh" },
          );
          await new Promise((resolve) => setTimeout(resolve, 0));
          await new Promise((resolve) => setTimeout(resolve, 0));
          const revisionsAfterReplace = Array.from(internal.descriptorRevisions.keys());
          return {
            ...retained,
            retainedRevisionTables: {
              initial: revisionsWhileRetained.includes(initialRevision),
              incoming: revisionsWhileRetained.includes(incomingRevision),
            },
            replacedRevisionTables: {
              initial: revisionsAfterReplace.includes(initialRevision),
              incoming: revisionsAfterReplace.includes(incomingRevision),
              replacement: revisionsAfterReplace.includes(replacementRevision),
            },
          };
        }
        """,
        [fresh, IncomingOnly.class_id, replacement],
    )

    assert result["libText"] == "client-owned"  # the ignored subtree kept the client's DOM
    assert result["libAttr"] == "y"
    assert result["serverText"] == "v2"  # everything else patched
    assert result["childText"] == "v1"
    assert result["activeChildLinked"] is True  # final positional matching runs after excluded X leaves the pool
    assert result["nestedText"] == "v1"
    assert result["nestedLinked"] is True
    assert result["incomingPresent"] is False
    assert result["excludedDependencyFired"] == 0
    assert result["retainedHandler"] == "bump"
    assert result["excludedAnchorCount"] == 0
    assert result["excludedAssetsInserted"] == 0
    assert result["excludedResourcesFetched"] == 0
    assert result["retainedRevisionTables"] == {"initial": True, "incoming": True}
    # The document Page is still a live non-Events ownership root in the
    # initial revision, so descriptor pruning must wait for it too.
    assert result["replacedRevisionTables"] == {"initial": True, "incoming": False, "replacement": True}
    root_warnings = [m for m in messages if "component instance root" in m and "unsupported" in m]
    assert root_warnings == []
    assert _citry_errors(messages) == []


def test_duplicate_component_key_warning_waits_for_ignore_closure(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Item(Component):
        citry = c
        template = '<span class="closure-key-item">{{ label }}</span>'

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Host(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="closure-key-host">
            <div class="closure-key-barrier" #c-ignore>
              <c-item #c-key="'duplicate'" c-label="'first'" />
              <c-item #c-key="'duplicate'" c-label="'second'" />
            </div>
            <c-item #c-key="'active'" c-label="'active'" />
          </main>
        """

    class Page(Component):
        citry = c
        template = "<html><body><c-host /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Host())
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const host = document.querySelector(".closure-key-host");
          const id = host.getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const retained = Array.from(document.querySelectorAll(".closure-key-barrier .closure-key-item"));
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html }],
            },
            { anchor, instance: id, event: "refresh" },
          );
          const after = Array.from(document.querySelectorAll(".closure-key-barrier .closure-key-item"));
          return {
            retained: after.length === 2 && after.every((node, index) => node === retained[index]),
            labels: after.map((node) => node.textContent),
          };
        }
        """,
        [fresh],
    )
    assert result == {"retained": True, "labels": ["first", "second"]}
    assert not [message for message in messages if "duplicate component key" in message]
    assert _citry_errors(messages) == []


def test_physical_planner_drops_stale_candidate_after_ignore_closure(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Leaf(Component):
        citry = c
        template = """<b class="stale-pool-leaf">leaf</b>"""

    class Box(Component):
        citry = c
        template = """
          <section class="stale-pool-box">
            <c-if cond="has_leaf"><c-leaf #c-ignore /></c-if>
            <span>{{ label }}</span>
          </section>
        """

        def template_data(self, kwargs, slots):
            return {"has_leaf": kwargs["has_leaf"], "label": kwargs["label"]}

    class Host(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="stale-pool-host">
            <div class="stale-pool-ignore" #c-ignore>
              <c-if cond="incoming_x"><c-box c-has_leaf="True" c-label="'excluded-x'" /></c-if>
            </div>
            <c-box c-has_leaf="outside_leaf" c-label="'active'" />
          </main>
        """

        def template_data(self, kwargs, slots):
            return {
                "incoming_x": kwargs["incoming_x"],
                "outside_leaf": kwargs["outside_leaf"],
            }

    class Page(Component):
        citry = c
        template = """<html><body><c-host c-incoming_x="False" c-outside_leaf="True" /></body></html>"""

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Host(incoming_x=True, outside_leaf=False))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const host = document.querySelector(".stale-pool-host");
          const hostId = host.getAttribute("data-cid");
          const anchor = internal.getAnchor(hostId);
          const leaf = document.querySelector(".stale-pool-leaf");
          const leafId = leaf.getAttribute("data-cid");
          const oldRevision = ownership.revisions().find((revision) => ownership.forRender(revision, leafId));
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + hostId, swap: "morph", html }],
            },
            { anchor, instance: hostId, event: "refresh" },
          );
          await new Promise((resolve) => setTimeout(resolve, 0));
          return {
            ignoredIncomingStayedExcluded: document.querySelector(".stale-pool-ignore").children.length === 0,
            activeBoxLabel: document.querySelector(".stale-pool-box span").textContent,
            leafRemoved: !document.querySelector(".stale-pool-leaf"),
            leafAnchorRetired: internal.getAnchor(leafId) === null,
            leafRouteRetired: ownership.forRender(oldRevision, leafId) === null,
          };
        }
        """,
        [fresh],
    )
    assert result == {
        "ignoredIncomingStayedExcluded": True,
        "activeBoxLabel": "active",
        "leafRemoved": True,
        "leafAnchorRetired": True,
        "leafRouteRetired": True,
    }
    assert _citry_errors(messages) == []


def test_unmatched_ignored_range_history_cannot_retain_nested_barrier_child(
    page: Any,
    serve_live: Any,
) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Child(Component):
        citry = c
        js = """
          $component(({ id }) => {
            window.__historyChildInit = (window.__historyChildInit || []).concat(id);
            return () => {
              window.__historyChildCleanup = (window.__historyChildCleanup || []).concat(id);
            };
          });
        """
        template = """<b class="history-child">child</b>"""

    class Ignored(Component):
        citry = c
        template = """
          <div class="history-ignored-range">
            <div class="history-ordinary-ignore" #c-ignore><c-child /></div>
          </div>
        """

    class Host(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = """
          <main class="history-host">
            <c-if cond="old_wrapper">
              <section class="history-old-wrapper"><c-ignored #c-ignore /></section>
            </c-if>
            <c-else>
              <article class="history-new-wrapper"><c-ignored #c-ignore /></article>
            </c-else>
          </main>
        """

        def template_data(self, kwargs, slots):
            return {"old_wrapper": kwargs["old_wrapper"]}

    class Page(Component):
        citry = c
        template = """<html><body><c-host c-old_wrapper="True" /></body></html>"""

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Host(old_wrapper=False))
    result = page.evaluate(
        """
        async ([html]) => {
          const ownership = Citry.manager.ownership;
          const internal = Citry.events._internal;
          const host = document.querySelector(".history-host");
          const hostId = host.getAttribute("data-cid");
          const anchor = internal.getAnchor(hostId);
          const oldIgnored = document.querySelector(".history-ignored-range");
          const oldChild = document.querySelector(".history-child");
          const oldIgnoredId = oldIgnored.getAttribute("data-cid");
          const oldChildId = oldChild.getAttribute("data-cid");
          const oldRevision = ownership.revisions().find(
            (revision) => ownership.forRender(revision, oldIgnoredId),
          );
          anchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + hostId, swap: "morph", html }],
            },
            { anchor, instance: hostId, event: "refresh" },
          );
          await new Promise((resolve) => setTimeout(resolve, 0));
          const newIgnored = document.querySelector(".history-ignored-range");
          const newChild = document.querySelector(".history-child");
          return {
            wrapperReplaced:
              !document.querySelector(".history-old-wrapper") &&
              Boolean(document.querySelector(".history-new-wrapper")),
            ignoredDomReplaced: !oldIgnored.isConnected && newIgnored !== oldIgnored,
            childDomReplaced: !oldChild.isConnected && newChild !== oldChild,
            oldIgnoredRouteRetired: ownership.forRender(oldRevision, oldIgnoredId) === null,
            oldChildRouteRetired: ownership.forRender(oldRevision, oldChildId) === null,
            oldChildCleaned: (window.__historyChildCleanup || []).includes(oldChildId),
            newChildInitialized: (window.__historyChildInit || []).includes(newChild.getAttribute("data-cid")),
          };
        }
        """,
        [fresh],
    )
    assert result == {
        "wrapperReplaced": True,
        "ignoredDomReplaced": True,
        "childDomReplaced": True,
        "oldIgnoredRouteRetired": True,
        "oldChildRouteRetired": True,
        "oldChildCleaned": True,
        "newChildInitialized": True,
    }
    assert _citry_errors(messages) == []


def test_pure_morph_planner_matches_the_pinned_working_sequence(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c

        class State:
            ready: bool = True
            _public = ("ready",)

        class Events:
            def refresh(self, state):
                return None

        template = """
          <html>
            <head><title>planner parity</title></head>
            <body><main>ready</main></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    traces = page.evaluate(
        """
        () => {
          const cases = [
            [
              '<i data-probe="old-b" data-citry-key="b" data-citry-morph="ignore"></i>' +
                '<i data-probe="old-c" data-citry-key="c"></i>',
              '<i data-probe="new-a" data-citry-key="a"></i>' +
                '<i data-probe="new-b" data-citry-key="b"></i>' +
                '<i data-probe="new-c" data-citry-key="c"></i>',
            ],
            [
              '<b data-probe="old-a" data-citry-key="a"></b>' +
                '<b data-probe="old-b" data-citry-key="b"></b>',
              '<b data-probe="new-b" data-citry-key="b"></b>' +
                '<b data-probe="new-a" data-citry-key="a"></b>',
            ],
            [
              '<u data-probe="old-u"></u><u data-probe="old-k" data-citry-key="k"></u>',
              '<u data-probe="new-k" data-citry-key="k"></u><u data-probe="new-u"></u>',
            ],
            [
              '<section data-probe="old-x"><em data-probe="old-child"></em></section>',
              '<article data-probe="new-x"><em data-probe="new-child"></em></article>',
            ],
          ];
          const key = (element) => element.getAttribute && element.getAttribute("data-citry-key");
          const run = (oldHtml, newHtml, planning) => {
            const oldContainer = document.createElement("div");
            const newContainer = document.createElement("div");
            oldContainer.innerHTML = oldHtml;
            newContainer.innerHTML = newHtml;
            const trace = [];
            const options = {
              key,
              updating(from, to, _childrenOnly, skip) {
                const oldProbe = from.getAttribute && from.getAttribute("data-probe");
                const newProbe = to.getAttribute && to.getAttribute("data-probe");
                if (oldProbe || newProbe) trace.push(`pair:${oldProbe || '-'}:${newProbe || '-'}`);
                if (from.getAttribute?.("data-citry-morph") === "ignore") skip();
              },
              adding(node) {
                const probe = node.getAttribute && node.getAttribute("data-probe");
                if (probe) trace.push(`add:${probe}`);
              },
              removing(node) {
                const probe = node.getAttribute && node.getAttribute("data-probe");
                if (probe) trace.push(`remove:${probe}`);
              },
            };
            if (planning) Alpine._citryPlanBetween(oldContainer, newContainer, options);
            else Alpine.morph(oldContainer, newContainer, options);
            return trace;
          };
          return cases.map(([oldHtml, newHtml]) => ({
            planned: run(oldHtml, newHtml, true),
            applied: run(oldHtml, newHtml, false),
          }));
        }
        """,
    )
    assert all(case["planned"] == case["applied"] for case in traces), traces
    assert _citry_errors(messages) == []


def test_range_ignore_discards_every_incoming_resource(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class IncomingOnly(Component):
        citry = c
        js = """
          $component(() => {
            window.__discardedComponentFired = (window.__discardedComponentFired || 0) + 1;
          });
        """
        css = """
          .discarded-incoming { --discarded-style: 1; }
        """
        template = """
          <aside class="discarded-incoming">incoming</aside>
        """

    class Frozen(Component):
        citry = c

        class State:
            ready: bool = True
            _public = ("ready",)

        class Events:
            def refresh(self, state):
                return None

        template = """
          <section class="frozen">
            <span class="frozen-label">{{ label }}</span>
            <c-if cond="show"><c-incoming-only /></c-if>
          </section>
        """

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"], "show": kwargs["show"]}

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>range discard</title></head>
            <body><c-frozen c-label="'old'" c-show="False" #c-ignore /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    fresh = _fragment(Frozen(label="new", show=True))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const oldId = document.querySelector(".frozen").getAttribute("data-cid");
          const oldAnchor = internal.getAnchor(oldId);
          const incoming = document.createElement("template");
          incoming.innerHTML = html;
          const graphManifest = JSON.parse(incoming.content.querySelector("script[data-citry-graph]").textContent);
          const incomingRevision = graphManifest.revision;
          const incomingIds = graphManifest.graphs.flatMap((graph) =>
            graph.componentInstances.map((instance) => instance.renderId),
          );
          const dependencyTag = incoming.content.querySelector("script[data-citry]:not([data-citry-events])");
          const dependencyManifest = JSON.parse(dependencyTag.textContent);
          const decode = (value) => decodeURIComponent(escape(atob(value)));
          const descriptors = [...dependencyManifest.fetch.js, ...dependencyManifest.fetch.css]
            .filter((entry) => entry[1] !== null)
            .map((entry) => JSON.parse(decode(entry[0])));
          const encode = (value) => btoa(unescape(encodeURIComponent(value)));
          window.__discardedCustomConstructed = 0;
          if (!customElements.get("citry-discarded-probe")) {
            customElements.define("citry-discarded-probe", class extends HTMLElement {
              constructor() {
                super();
                window.__discardedCustomConstructed += 1;
              }
            });
          }
          dependencyManifest.beforeManifest.push(
            encode(
              JSON.stringify({
                tag: "script",
                attrs: {},
                content: "window.__discardedBeforeManifest = (window.__discardedBeforeManifest || 0) + 1;",
              }),
            ),
            encode(
              JSON.stringify({
                tag: "citry-discarded-probe",
                attrs: { "data-probe": "discarded" },
                content: "",
              }),
            ),
          );
          dependencyTag.textContent = JSON.stringify(dependencyManifest);
          html = incoming.innerHTML;
          oldAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
            },
            { anchor: oldAnchor, instance: oldId, event: "refresh" },
          );
          await new Promise((resolve) => setTimeout(resolve, 0));
          return {
            text: document.querySelector(".frozen-label").textContent,
            incomingPresent: Boolean(document.querySelector(".discarded-incoming")),
            componentFired: window.__discardedComponentFired || 0,
            beforeManifestFired: window.__discardedBeforeManifest || 0,
            customConstructed: window.__discardedCustomConstructed,
            customPresent: Boolean(document.querySelector("citry-discarded-probe")),
            anchorKept: internal.getAnchor(oldId) === oldAnchor,
            incomingAnchors: incomingIds.filter((renderId) => internal.getAnchor(renderId)).length,
            assetsInserted: descriptors.filter((descriptor) => {
              const url = descriptor.attrs && (descriptor.attrs.src || descriptor.attrs.href);
              return Array.from(document.querySelectorAll(descriptor.tag)).some((element) =>
                url
                  ? element.getAttribute("src") === url || element.getAttribute("href") === url
                  : element.textContent === (descriptor.content || ""),
              );
            }).length,
            resourcesFetched: descriptors.filter((descriptor) => {
              const url = descriptor.attrs && (descriptor.attrs.src || descriptor.attrs.href);
              return url && performance.getEntriesByType("resource").some((entry) => entry.name.includes(url));
            }).length,
            incomingDescriptorRevision: internal.descriptorRevisions.has(incomingRevision),
          };
        }
        """,
        [fresh],
    )
    assert result == {
        "text": "old",
        "incomingPresent": False,
        "componentFired": 0,
        "beforeManifestFired": 0,
        "customConstructed": 0,
        "customPresent": False,
        "anchorKept": True,
        "incomingAnchors": 0,
        "assetsInserted": 0,
        "resourcesFetched": 0,
        "incomingDescriptorRevision": False,
    }
    assert _citry_errors(messages) == []


def test_failed_graph_descriptor_install_rolls_back_the_revision_table(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = c

        class State:
            value: str = ""
            _public = ("value",)

        class Events:
            def save(self, state):
                return None

        template = "<section class='descriptor-widget'>{{ label }}</section>"

        def template_data(self, kwargs, slots):
            return {"label": kwargs["label"]}

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-widget c-label=\"'old'\" /><div id='target'></div></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    fresh = _fragment(Widget(label="fresh"))
    observer_fragment = _fragment(Widget(label="observer"))
    result = page.evaluate(
        """
        async ([html, observerHtml, classId]) => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const observerParsed = document.createElement("template");
          observerParsed.innerHTML = observerHtml;
          const observerRevision = JSON.parse(
            observerParsed.content.querySelector("script[data-citry-graph]").textContent,
          ).revision;
          const observerIds = JSON.parse(
            observerParsed.content.querySelector("script[data-citry-graph]").textContent,
          ).graphs.flatMap((graph) => graph.componentInstances.map((instance) => instance.renderId));
          const oldId = document.querySelector(".descriptor-widget").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          const oldDescriptorRevision = anchor.descriptorRevision;
          const observerEventsTag = observerParsed.content.querySelector("script[data-citry-events]");
          const observerEvents = JSON.parse(observerEventsTag.textContent);
          observerEvents.componentInstances[0].renderId = oldId;
          observerEventsTag.textContent = JSON.stringify(observerEvents);
          const originalObserverAttach = ownership._attachEvents;
          const originalObserverPreflight = ownership._preflightEvents;
          ownership._preflightEvents = () => {};
          ownership._attachEvents = () => { throw new Error("forced observer descriptor-install failure"); };
          document.getElementById("target").innerHTML = observerParsed.innerHTML;
          await new Promise((resolve) => setTimeout(resolve, 0));
          await new Promise((resolve) => setTimeout(resolve, 0));
          ownership._attachEvents = originalObserverAttach;
          ownership._preflightEvents = originalObserverPreflight;
          const observerRollback = {
            revision: internal.descriptorRevisions.has(observerRevision),
            anchors: observerIds.filter((renderId) => internal.getAnchor(renderId)).length,
            anchorRevision: anchor.descriptorRevision === oldDescriptorRevision,
            descriptor: internal.descriptorRevisions.has(oldDescriptorRevision),
          };
          const parsed = document.createElement("template");
          parsed.innerHTML = html;
          const revision = JSON.parse(parsed.content.querySelector("script[data-citry-graph]").textContent).revision;
          const originalAttach = ownership._attachEvents;
          ownership._attachEvents = () => { throw new Error("forced descriptor-install failure"); };
          let error = null;
          try {
            anchor.epoch = 1;
            await internal.applyResult(
              {
                ok: true,
                sendSequence: 1,
                actions: [{ action: "render", target: "render:" + oldId, swap: "morph", html }],
              },
              { anchor, instance: oldId, event: "save" },
            );
          } catch (err) {
            error = String(err && err.message ? err.message : err);
          } finally {
            ownership._attachEvents = originalAttach;
          }
          await new Promise((resolve) => setTimeout(resolve, 0));
          await new Promise((resolve) => setTimeout(resolve, 0));
          return {
            observerRollback,
            error,
            failedRevisionPresent: internal.descriptorRevisions.has(revision),
            failedRevisionPending: internal.pendingDescriptorRevisionRefs.has(revision),
            failedOwnershipPresent: ownership.revisions().includes(revision),
            graphDescriptorLeakedGlobal: internal.classes.has(classId),
          };
        }
        """,
        [fresh, observer_fragment, Widget.class_id],
    )
    assert result == {
        "observerRollback": {
            "revision": False,
            "anchors": 0,
            "anchorRevision": True,
            "descriptor": True,
        },
        "error": "forced descriptor-install failure",
        "failedRevisionPresent": False,
        "failedRevisionPending": False,
        "failedOwnershipPresent": False,
        "graphDescriptorLeakedGlobal": False,
    }
    expected_errors = _citry_errors(messages)
    assert expected_errors


def test_pending_call_holds_descriptor_revision_until_full_settlement(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Widget(Component):
        citry = c

        class State:
            value: str = ""
            _public = ("value",)

        class Events:
            def save(self, state):
                return None

        template = "<section class='pending-descriptor'>pending</section>"

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-widget /></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    result = page.evaluate(
        """
        async () => {
          const internal = Citry.events._internal;
          const ownership = Citry.manager.ownership;
          const root = document.querySelector(".pending-descriptor");
          const id = root.getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          const revision = anchor.descriptorRevision;
          let resolveTransport;
          internal.setTransport(() => new Promise((resolve) => { resolveTransport = resolve; }));
          const pending = Citry.events.send(id, "save");
          for (let i = 0; i < 20 && internal.pendingDescriptorRevisionRefs.get(revision) !== 1; i += 1) {
            await new Promise((resolve) => setTimeout(resolve, 0));
          }
          root.remove();
          internal.retireAnchor(anchor);
          await new Promise((resolve) => setTimeout(resolve, 0));
          await new Promise((resolve) => setTimeout(resolve, 0));
          const held = {
            refs: internal.pendingDescriptorRevisionRefs.get(revision) || 0,
            descriptor: internal.descriptorRevisions.has(revision),
            ownership: ownership.revisions().includes(revision),
            pruneVetoed: Citry.events._pruneDescriptorRevision(revision) === false,
          };
          resolveTransport({ ok: true });
          await pending;
          await new Promise((resolve) => setTimeout(resolve, 0));
          await new Promise((resolve) => setTimeout(resolve, 0));
          return {
            held,
            released: {
              refs: internal.pendingDescriptorRevisionRefs.get(revision) || 0,
              descriptor: internal.descriptorRevisions.has(revision),
              ownership: ownership.revisions().includes(revision),
            },
          };
        }
        """,
    )
    assert result == {
        "held": {"refs": 1, "descriptor": True, "ownership": True, "pruneVetoed": True},
        "released": {"refs": 0, "descriptor": True, "ownership": True},
    }
    assert _citry_errors(messages) == []


def test_pinned_morph_key_map_filter_prevents_rejected_key_pull(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c

        class Events:
            def refresh(self):
                return None

        template = "<html><body><main>ready</main></body></html>"

    messages = _goto(page, serve_live, c, str(Page()))
    result = page.evaluate(
        """
        () => {
          const host = document.createElement("div");
          document.body.append(host);
          const start = document.createComment("filter-start");
          const oldKeyed = document.createElement("button");
          oldKeyed.dataset.key = "shared";
          oldKeyed.textContent = "old-keyed";
          const oldUnkeyed = document.createElement("i");
          oldUnkeyed.textContent = "old-unkeyed";
          const end = document.createComment("filter-end");
          host.append(start, oldKeyed, oldUnkeyed, end);
          const fresh = document.createElement("div");
          fresh.innerHTML = '<i>new-unkeyed</i><button data-key="shared">new-keyed</button>';
          Alpine.morphBetween(start, end, fresh, {
            key: (element) => element.dataset.key || null,
            keyMapFilter: (element) => element !== oldKeyed,
          });
          const landed = host.querySelector("button");
          return {
            oldPulledFromMap: landed === oldKeyed,
            oldConnected: oldKeyed.isConnected,
            landedText: landed && landed.textContent,
            order: Array.from(host.children).map((element) => element.localName),
          };
        }
        """
    )
    assert result == {
        "oldPulledFromMap": False,
        "oldConnected": False,
        "landedText": "new-keyed",
        "order": ["i", "button"],
    }
    assert _citry_errors(messages) == []


def test_pure_morph_planner_does_not_construct_custom_elements(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class Page(Component):
        citry = c

        class State:
            ready: bool = True
            _public = ("ready",)

        class Events:
            def refresh(self, state):
                return None

        template = """
          <html>
            <head><title>planner custom elements</title></head>
            <body><main>ready</main></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))
    counts = page.evaluate(
        """
        () => {
          let constructed = 0;
          customElements.define(
            "x-citry-plan-probe",
            class extends HTMLElement {
              constructor() {
                super();
                constructed += 1;
              }
            },
          );
          const inert = document.implementation.createHTMLDocument("");
          const oldContainer = inert.createElement("div");
          const newContainer = inert.createElement("div");
          oldContainer.append(inert.createElementNS("http://www.w3.org/1999/xhtml", "x-citry-plan-probe"));
          newContainer.append(inert.createElementNS("http://www.w3.org/1999/xhtml", "x-citry-plan-probe"));
          const afterStructure = constructed;
          Alpine._citryPlanBetween(oldContainer, newContainer, {});
          return { afterStructure, afterPlan: constructed };
        }
        """,
    )
    assert counts == {"afterStructure": 0, "afterPlan": 0}
    assert _citry_errors(messages) == []


def test_busy_restamp_covers_new_roots_and_the_surviving_trigger(page: Any, serve_live: Any) -> None:
    # Busy display carries with the loading counters (design 5.5): morph
    # strips the client-stamped data-citry-busy from surviving elements, so
    # after a keyed link the applier re-stamps the linked anchor's new roots
    # and the triggering element where it survived the patch.
    c, Parent, _Item, _Loose = _make_list_app()

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>busy</title></head>
            <body>
              <c-parent c-idents="[1]" />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    fresh = _fragment(Parent(idents=[1]))
    result = page.evaluate(
        """
        async ([html]) => {
          const internal = Citry.events._internal;
          const parentId = document.querySelector(".parent").getAttribute("data-cid");
          const itemId = document.querySelector(".item").getAttribute("data-cid");
          const parentAnchor = internal.getAnchor(parentId);
          const itemAnchor = internal.getAnchor(itemId);
          const trigger = document.querySelector(".item .go");

          // What the queue does from the gesture: counter up, busy stamped
          // on the roots and the trigger, the trigger remembered.
          itemAnchor.loading.any = 1;
          document.querySelector(".item").setAttribute("data-citry-busy", "");
          trigger.setAttribute("data-citry-busy", "");
          itemAnchor.busyTriggers.add(trigger);

          parentAnchor.epoch = 1;
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + parentId, swap: "morph", html }],
            },
            { anchor: parentAnchor, instance: parentId, event: "refresh" },
          );
          const root = document.querySelector(".item");
          const survivingTrigger = document.querySelector(".item .go");
          return {
            rootBusy: root.hasAttribute("data-citry-busy"),
            triggerSurvived: survivingTrigger === trigger,
            triggerBusy: survivingTrigger.hasAttribute("data-citry-busy"),
            linked: internal.getAnchor(root.getAttribute("data-cid")) === itemAnchor,
          };
        }
        """,
        [fresh],
    )

    assert result == {"rootBusy": True, "triggerSurvived": True, "triggerBusy": True, "linked": True}
    assert _citry_errors(messages) == []


# ----- ordering, timing fields, and warnings -----


def test_actions_apply_in_faithful_order_with_delay_and_wait(page: Any, serve_live: Any) -> None:
    # Design 4.3's ordering rules: list order is faithful, a blocking delay
    # holds later actions, `wait: false` schedules without holding, and a
    # scheduled action re-resolves its target at fire time (the target
    # element replaced in the meantime is a zero-match warning, never a
    # stale-reference patch).
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class PingState:
        n: int = 0
        _public = ("n",)

    class Ping(Component):
        citry = c
        State = PingState

        class Events:
            def ping(self, state):
                return None

        template = """
          <div class="ping"></div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>order</title></head>
            <body>
              <div id="box">before</div>
              <c-ping />
            </body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    order = page.evaluate(
        """
        async () => {
          const seen = [];
          ["a", "b", "c", "x", "y"].forEach((name) => {
            document.addEventListener("t:" + name, () => seen.push({ name, at: performance.now() }));
          });
          // Blocking delay: c waits for b's 150 ms.
          await Citry.events.applyActions([
            { action: "event", eventName: "t:a" },
            { action: "event", eventName: "t:b", delay: 0.15 },
            { action: "event", eventName: "t:c" },
          ]);
          // Non-blocking: y applies immediately, x fires later.
          await Citry.events.applyActions([
            { action: "event", eventName: "t:x", delay: 0.1, wait: false },
            { action: "event", eventName: "t:y" },
          ]);
          await new Promise((resolve) => setTimeout(resolve, 250));
          return seen.map((s) => s.name).join(",") + "|" + String(seen[1].at - seen[0].at >= 100);
        }
        """
    )
    assert order == "a,b,c,y,x|true"

    fire_time = page.evaluate(
        """
        async () => {
          // The scheduled render targets #box, but an immediate render
          // replaces it first: at fire time the selector matches nothing.
          await Citry.events.applyActions([
            {
              action: "render",
              target: "#box",
              swap: "replace",
              html: "<div id='late'>late</div>",
              delay: 0.12,
              wait: false,
            },
            { action: "render", target: "#box", swap: "replace", html: "<div id='other'>now</div>" },
          ]);
          await new Promise((resolve) => setTimeout(resolve, 250));
          return {
            other: document.querySelector("#other")?.innerText ?? null,
            late: document.querySelector("#late") === null,
          };
        }
        """
    )
    assert fire_time == {"other": "now", "late": True}
    zero_match = [m for m in messages if "matched nothing" in m]
    assert len(zero_match) == 1  # the scheduled action's fire-time miss, and nothing else
    assert _citry_errors(messages) == []


def test_url_action_and_strict_action_validation(page: Any, serve_live: Any) -> None:
    # The `url` action applies history push or replace without navigation
    # while preserving application-owned history state. A malformed public
    # action array rejects before any member applies.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class PingState:
        n: int = 0
        _public = ("n",)

    class Ping(Component):
        citry = c
        State = PingState

        class Events:
            def ping(self, state):
                return actions.ReplaceUrl("/from-handler")

        template = """
          <div class="ping"></div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>url</title></head>
            <body><div id="app">app</div><c-ping /></body>
          </html>
        """

    messages = _goto(page, serve_live, c, str(Page()))

    result = page.evaluate(
        """
        async () => {
          history.replaceState({ router: "kept" }, "", location.href);
          let popstates = 0;
          addEventListener("popstate", () => { popstates += 1; });
          const before = history.length;
          const id = document.querySelector(".ping").getAttribute("data-cid");
          await Citry.events.send(id, "ping", {});
          const serverPath = location.pathname;
          await Citry.events.applyActions([
            { action: "url", url: "/pushed", mode: "push" },
            { action: "url", url: "/replaced", mode: "replace" },
            { action: "url", url: "https://example.com/cross-origin", mode: "push" },
            { action: "url", url: "/after-errors", mode: "replace" },
          ]);
          let invalid = null;
          try {
            await Citry.events.applyActions([
              { action: "url", url: "/invalid-mode", mode: "mystery" },
              { action: "url", url: "/must-not-apply", mode: "replace" },
              { action: "mystery", value: 1 },
            ]);
          } catch (error) {
            invalid = error.message;
          }
          const invalidData = [];
          for (const wait of [false, true]) {
            try {
              await Citry.events.applyActions([
                { action: "data", value: { answer: 42 }, wait },
              ]);
            } catch (error) {
              invalidData.push(error.message);
            }
          }
          return {
            path: location.pathname,
            serverPath,
            growth: history.length - before,
            state: history.state,
            popstates,
            invalid,
            invalidData,
          };
        }
        """
    )
    assert result == {
        "path": "/after-errors",
        "serverPath": "/from-handler",
        "growth": 1,
        "state": {"router": "kept"},
        "popstates": 0,
        "invalid": "[Citry] applyActions received an invalid citry-events/1 action array.",
        "invalidData": [
            "[Citry] applyActions received an invalid citry-events/1 action array.",
            "[Citry] applyActions received an invalid citry-events/1 action array.",
        ],
    }
    assert any("could not apply a url action" in m for m in messages)
    assert _citry_errors(messages) == []


def test_back_and_forward_leave_component_dom_and_state_untouched(page: Any, serve_live: Any) -> None:
    c, _Todo, Page = _make_todo_app()
    messages = _goto(page, serve_live, c, str(Page()))

    result = page.evaluate(
        """
        async () => {
          const root = document.querySelector(".todo");
          const id = root.getAttribute("data-cid");
          const internal = Citry.events._internal;
          const anchor = internal.getAnchor(id);
          const stateIdentity = anchor.stateProxy;
          history.replaceState({ router: "kept" }, "", "/history-start");
          await Citry.events.applyActions([
            { action: "url", url: "/history-pushed", mode: "push" },
          ]);
          anchor.stateProxy.query = "client-state";
          await Alpine.nextTick();
          root.querySelector(".q").textContent = "client-dom";
          root.setAttribute("data-local", "kept");

          const navigate = (direction) => new Promise((resolve, reject) => {
            const timer = setTimeout(() => reject(new Error("popstate did not fire")), 2000);
            addEventListener("popstate", (event) => {
              clearTimeout(timer);
              resolve({ path: location.pathname, state: event.state });
            }, { once: true });
            history[direction]();
          });
          const back = await navigate("back");
          const afterBack = internal.getAnchor(id);
          const forward = await navigate("forward");
          const afterForward = internal.getAnchor(id);
          return {
            back,
            forward,
            currentPath: location.pathname,
            anchorPersisted: afterBack === anchor && afterForward === anchor,
            statePersisted: afterBack.stateProxy === stateIdentity && afterForward.stateProxy === stateIdentity,
            query: afterForward.stateProxy.query,
            text: document.querySelector(".todo .q").textContent,
            local: document.querySelector(".todo").getAttribute("data-local"),
          };
        }
        """
    )
    assert result == {
        "back": {"path": "/history-start", "state": {"router": "kept"}},
        "forward": {"path": "/history-pushed", "state": {"router": "kept"}},
        "currentPath": "/history-pushed",
        "anchorPersisted": True,
        "statePersisted": True,
        "query": "client-state",
        "text": "client-dom",
        "local": "kept",
    }
    assert _citry_errors(messages) == []


# ----- recurring timers (machinery item 5's structure) -----


def test_recurring_timers_retire_with_the_anchor_and_dedupe_per_element(page: Any, serve_live: Any) -> None:
    # The structure the bindings runtime wires @c-poll onto: an interval
    # registered to an anchor stops when the anchor retires (a replaced
    # region never leaves a dead interval firing), and an element-keyed
    # interval holds one timer per (element, key), so a morph survivor
    # dedupes against the fresh instance's own interval instead of
    # double-polling.
    c, _Todo, Page = _make_todo_app()
    messages = _goto(page, serve_live, c, str(Page()))

    stopped = page.evaluate(
        """
        async () => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          window.__polls = 0;
          internal.timers.registerAnchorInterval(anchor, setInterval(() => { window.__polls += 1; }, 30));
          await new Promise((resolve) => setTimeout(resolve, 100));
          const ranBefore = window.__polls > 0;
          // A plain-HTML self-render retires the anchor, and its timers with it.
          await internal.applyResult(
            {
              ok: true,
              sendSequence: 1,
              actions: [{ action: "render", target: "render:" + id, swap: "morph", html: "<p>gone</p>" }],
            },
            { anchor, instance: id, event: "save" },
          );
          const atRetire = window.__polls;
          await new Promise((resolve) => setTimeout(resolve, 120));
          return { ranBefore, stoppedAfter: window.__polls === atRetire };
        }
        """
    )
    assert stopped == {"ranBefore": True, "stoppedAfter": True}

    dedupe = page.evaluate(
        """
        async () => {
          const internal = Citry.events._internal;
          const el = document.body;
          window.__a = 0;
          window.__b = 0;
          internal.timers.registerElementInterval(el, "poll", setInterval(() => { window.__a += 1; }, 30));
          internal.timers.registerElementInterval(el, "poll", setInterval(() => { window.__b += 1; }, 30));
          await new Promise((resolve) => setTimeout(resolve, 120));
          return { first: window.__a, secondRan: window.__b > 0 };
        }
        """
    )
    assert dedupe["first"] == 0  # the earlier timer was cleared, never double-polling
    assert dedupe["secondRan"] is True
    assert _citry_errors(messages) == []
