"""
Browser e2e for the events client runtime, the bundle shipped as
``citry/ext/events/client/citry-events.js`` and served at
``ext/events/runtime.js`` (design contract: docs/design/events.md section 5,
in particular 5.5; the WP6 and component-identity spikes pin the mechanics).
This suite covers the v1 Alpine layer:

- Boot: the runtime loads on a real serialized page (the events manifest, the
  inline bootstrap stub, and the runtime tag all come from the real emission),
  seeds ``$state`` from the manifest values, and produces no console errors.
- Scopes: isolation between nested instances (a nested citry instance does
  not inherit its parent's ``x-data`` while Alpine-native anonymous nesting
  still does), including when a head-placed ``<c-js />`` makes the runtime
  consume the manifest before any instance root is parsed; a user ``x-data``
  on the instance root coexisting with the boundary entry (checked on the
  scope stack itself: Alpine's merged ``$data`` proxy hides every key from
  ``Object.keys``, spike F6), and the magics resolving inside nested user
  ``x-data``.
- The two identities: the reactive State and its ``$state`` facade key off
  the stable anchor while the faithful component id re-links through a
  re-render (link before morph: both ids resolve to the anchor between
  ``linkRenderedInstance`` and ``finishRender``).
- The three-way split, driven by stubbed incoming render metadata (no real
  morph; the actions applier work package owns that): same class reconciles
  (server wins per field except pending unsent writes; ``$state`` identity
  persists), a different class adopts the server state wholesale (identity
  rebuilt, writable set switched), plain HTML retires the anchor.
- Magics: ``$loading``/``$error`` transitions over a stubbed transport (set
  through the runtime's ``_internal.setTransport`` hook; the real fetch
  transport is the transport work package), a failed send putting its
  unsent ``$state`` writes back in the pending queue so a retry still
  carries them, write gating with pointed errors, unknown-name pointed
  errors, innermost resolution on a shared root, the ``$state`` inert
  fallback for a marker whose id is unregistered mid-morph, and the hard
  error outside any instance.
- The ``$component`` payload members (``state``/``sendEvent``/``onEvent``)
  for interactive and non-interactive instances, instance-scoped ``onEvent``
  filtering, and the bootstrap stub's queue draining into the runtime.

Uses the live-server harness (conftest ``serve_live``) so the page fetches
``/citry/citry.js`` and ``/citry/ext/events/runtime.js`` from the real
routes. State values asserted here were observed from real render output
first (the manifest carries template kwargs as rendered), then locked.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("pytest_playwright")

from citry import Citry, Component

pytestmark = pytest.mark.e2e

SIGNING_KEY = "e2e-secret"

READY = "window.Citry && Citry.events && Citry.events._internal && Citry.events._internal.alpineStarted === true"
_MANIFESTS_DIR = (
    Path(__file__).resolve().parents[5] / "packages" / "protocol" / "events" / "v1" / "tests" / "manifests"
)
_MANIFEST_CASES = json.loads((_MANIFESTS_DIR / "index.json").read_text(encoding="utf-8"))


def _collect_console(page: Any) -> list[str]:
    """Start collecting console messages as ``type:text`` strings."""
    messages: list[str] = []
    page.on("console", lambda msg: messages.append(f"{msg.type}:{msg.text}"))
    return messages


def _citry_errors(messages: list[str]) -> list[str]:
    return [m for m in messages if m.startswith("error:")]


def _make_todo_page() -> tuple[Citry, str, type[Component]]:
    """One interactive Todo instance on a document page; returns (citry, html, Todo)."""
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class TodoState:
        query: str = ""
        note: str = ""
        count: int = 0
        hidden: str = "server-only"
        _public = ("query", "note", "count")

    class Todo(Component):
        citry = c
        State = TodoState

        class Events:
            def save(self, state):
                return None

            def find(self, state):
                return None

        template = """
          <div class="todo">
            <span class="q" x-text="$state.query"></span>
            <span class="n" x-text="$state.count"></span>
            <span class="busy" x-text="$loading() ? 'busy' : 'idle'"></span>
            <span class="busy-save" x-text="$loading('save') ? 'busy' : 'idle'"></span>
            <span class="err" x-text="$error ? $error.message : 'none'"></span>
            <button
              class="inc"
              x-on:click="$state.count = $state.count + 1"
            >inc</button>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head><title>e2e</title></head>
            <body>
              <c-todo query="shoes" />
            </body>
          </html>
        """

    return c, str(Page()), Todo


def _goto_todo(page: Any, serve_live: Any) -> list[str]:
    """Serve the Todo page, open it, wait for the runtime; returns console log."""
    c, html, _ = _make_todo_page()
    messages = _collect_console(page)
    base = serve_live(c, html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    return messages


# ----- boot and $state basics -----


def test_page_boots_seeds_state_and_stays_error_free(page: Any, serve_live: Any) -> None:
    # The full real pipeline: serialization emitted the events manifest, the
    # bootstrap stub, and the runtime tag; the runtime consumed the manifest,
    # attached the scope, booted Alpine, and the bound text shows the seeded
    # public values. Zero console errors is part of the contract.
    messages = _goto_todo(page, serve_live)

    assert page.locator(".q").inner_text() == "shoes"
    assert page.locator(".n").inner_text() == "0"
    assert page.locator(".busy").inner_text() == "idle"
    assert page.locator(".err").inner_text() == "none"
    # The anchor exists, keyed separately from the component id, and carries
    # the epoch structure (the counter and highest-applied are this work
    # package's contract; the send-and-compare is the transport's).
    result = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          return {
            hasAnchor: !!anchor,
            anchorIdShape: anchor.anchorId.startsWith("a"),
            componentId: anchor.componentId === id,
            sendSequence: anchor.epoch,
            highestApplied: anchor.highestApplied,
            token: anchor.token.length > 0,
          };
        }
        """
    )
    assert result == {
        "hasAnchor": True,
        "anchorIdShape": True,
        "componentId": True,
        "sendSequence": 0,
        "highestApplied": 0,
        "token": True,
    }
    assert _citry_errors(messages) == []


@pytest.mark.parametrize(
    "case",
    _MANIFEST_CASES,
    ids=[case["file"] for case in _MANIFEST_CASES],
)
def test_browser_validator_replays_the_protocol_manifest_corpus_without_mutation(
    page: Any,
    serve_live: Any,
    case: dict[str, Any],
) -> None:
    _goto_todo(page, serve_live)
    manifest = json.loads((_MANIFESTS_DIR / case["file"]).read_text(encoding="utf-8"))
    result = page.evaluate(
        """
        ([manifest]) => {
          const internal = Citry.events._internal;
          const before = internal.debug();
          let error = null;
          try {
            internal.stageEventsManifest(manifest);
          } catch (caught) {
            error = String(caught && (caught.message || caught));
          }
          return { before, after: internal.debug(), error };
        }
        """,
        [manifest],
    )

    assert (result["error"] is None) is case["valid"]
    assert result["after"] == result["before"]


def test_browser_rejects_non_json_application_values_without_mutation(page: Any, serve_live: Any) -> None:
    _goto_todo(page, serve_live)
    result = page.evaluate(
        """
        async () => {
          const internal = Citry.events._internal;
          const before = internal.debug();
          const manifest = JSON.parse(`{
            "protocol": "citry-events/1",
            "clientGraphRevision": null,
            "componentClasses": [{
              "componentClassId": "Probe",
              "eventHandlers": {"save": {"httpMethod": "POST"}}
            }],
            "componentInstances": [{
              "renderId": "probe1",
              "componentClassId": "Probe",
              "stateToken": "token",
              "publicState": {"overflow": 1e400}
            }]
          }`);
          const cyclic = {};
          cyclic.self = cyclic;
          const errors = [];
          try {
            internal.stageEventsManifest(manifest);
          } catch (error) {
            errors.push(String(error && (error.message || error)));
          }
          for (const actions of [
            [{ action: "data", value: Infinity }],
            [{ action: "event", eventName: "probe", detail: () => {} }],
            [{ action: "data", value: cyclic }],
          ]) {
            try {
              await Citry.events.applyActions(actions);
            } catch (error) {
              errors.push(String(error && (error.message || error)));
            }
          }
          return { before, after: internal.debug(), errors };
        }
        """
    )

    assert len(result["errors"]) == 4
    assert result["after"] == result["before"]


def test_outgoing_batch_rejects_non_json_args_and_state_before_side_effects(page: Any, serve_live: Any) -> None:
    _goto_todo(page, serve_live)
    result = page.evaluate(
        """
        () => {
          const internal = Citry.events._internal;
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = internal.getAnchor(id);
          let sends = 0;
          let beforeEvents = 0;
          const errors = [];
          internal.setTransport(() => { sends += 1; return { ok: true }; });
          document.addEventListener("citry:events:before", () => { beforeEvents += 1; });
          const startingSequence = anchor.epoch;
          try {
            internal.sendCalls([
              { target: id, name: "save", args: {} },
              { target: id, name: "find", args: { invalid: () => {} } },
            ]);
          } catch (error) {
            errors.push(String(error && (error.message || error)));
          }
          anchor.stateProxy.query = Infinity;
          try {
            internal.sendCalls([{ target: id, name: "save", args: {} }]);
          } catch (error) {
            errors.push(String(error && (error.message || error)));
          }
          return {
            sends,
            beforeEvents,
            sequenceUnchanged: anchor.epoch === startingSequence,
            pendingStillNonFinite: anchor.pending.query === Infinity,
            errors,
          };
        }
        """
    )

    assert result["sends"] == 0
    assert result["beforeEvents"] == 0
    assert result["sequenceUnchanged"] is True
    assert result["pendingStillNonFinite"] is True
    assert len(result["errors"]) == 2


def test_state_reads_are_reactive_and_writes_queue_pending_updates(page: Any, serve_live: Any) -> None:
    # A $state write from an Alpine expression lands in the DOM through
    # reactivity (on the next tick, spike F11) and queues as a pending update
    # on the anchor, which the next send will carry.
    _goto_todo(page, serve_live)

    page.locator(".inc").click()
    page.wait_for_function("document.querySelector('.n').innerText === '1'")

    pending = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          return Citry.events._internal.getAnchor(id).pending;
        }
        """
    )
    assert pending == {"count": 1}


def test_state_write_gating_throws_the_pointed_error(page: Any, serve_live: Any) -> None:
    # Writable fields default to the public fields (the descriptor omits
    # `model` when _model equals _public, design 7.2). A write to anything else names the
    # writable fields; a non-public field reads as plain undefined.
    _goto_todo(page, serve_live)

    result = page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const state = Citry.events._internal.getAnchor(id).stateProxy;
          let thrown = null;
          try {
            state.hidden = "hacked";
          } catch (err) {
            thrown = String(err.message);
          }
          return { thrown, hiddenRead: state.hidden === undefined, query: state.query };
        }
        """
    )
    assert result["hiddenRead"] is True
    assert result["query"] == "shoes"
    assert "'hidden'" in result["thrown"]
    assert "not client-writable" in result["thrown"]
    assert "count, note, query" in result["thrown"]  # the pointed error names the writable fields


def test_narrow_model_gates_writes_and_refreshes_on_a_live_descriptor(page: Any, serve_live: Any) -> None:
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class LimitedState:
        query: str = "shoes"
        count: int = 0
        _public = ("query", "count")
        _model = ("query",)

    class Limited(Component):
        citry = c
        State = LimitedState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="limited">
            <span class="limited-query" x-text="$state.query"></span>
            <span class="limited-count" x-text="$state.count"></span>
          </div>
        """

    class Page(Component):
        citry = c
        template = "<html><head></head><body><c-limited /><c-limited /></body></html>"

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    result = page.evaluate(
        """
        () => {
          const root = document.querySelector(".limited");
          const id = root.getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          let rejected = null;
          try {
            anchor.stateProxy.count = 7;
          } catch (error) {
            rejected = error.message;
          }
          const pendingAfterRejected = Object.assign({}, anchor.pending);
          anchor.stateProxy.query = "hats";
          return {
            rejected,
            pendingAfterRejected,
            pending: Object.assign({}, anchor.pending),
            query: anchor.stateProxy.query,
            count: anchor.stateProxy.count,
          };
        }
        """
    )

    assert "'count'" in result["rejected"]
    assert "writable fields: query" in result["rejected"]
    assert result["pendingAfterRejected"] == {}
    assert result["pending"] == {"query": "hats"}
    assert result["query"] == "hats"
    assert result["count"] == 0

    # Re-processing metadata for one live id must update the Sets closed over
    # by every live proxy of that class. Descriptors are class-global even
    # when a fragment carries only one of several sibling instances.
    refreshed = page.evaluate(
        """
        async () => {
          const roots = document.querySelectorAll(".limited");
          const id = roots[0].getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          const siblingId = roots[1].getAttribute("data-cid");
          const sibling = Citry.events._internal.getAnchor(siblingId);
          sibling.stateProxy.query = "boots";
          let rejectTransport = null;
          Citry.events._internal.setTransport(
            () => new Promise((_resolve, reject) => { rejectTransport = reject; }),
          );
          const inFlight = Citry.events.send(roots[0], "save").then(
            () => "resolved",
            () => "rejected",
          );
          if (!rejectTransport) throw new Error("the test transport did not receive the call");
          const manifest = {
            protocol: "citry-events/1",
            clientGraphRevision: null,
            componentClasses: [{
              componentClassId: anchor.classId,
              eventHandlers: { save: { httpMethod: "POST" } },
              writableStateFields: [],
            }],
            componentInstances: [{
              renderId: id,
              componentClassId: anchor.classId,
              stateToken: anchor.token,
              publicState: { query: "hats", count: 0 },
            }],
          };
          const tag = document.createElement("script");
          tag.type = "application/json";
          tag.setAttribute("data-citry-events", "");
          tag.textContent = JSON.stringify(manifest);
          document.body.appendChild(tag);
          Citry.events._internal.processEventsManifests();
          rejectTransport(new Error("offline after the descriptor refresh"));
          const settlement = await inFlight;
          let staleCall = null;
          anchor.pending.count = 17;
          Citry.events._internal.setTransport(async (call) => {
            staleCall = call;
            return null;
          });
          await Citry.events.send(roots[0], "save");
          Citry.events._internal.setTransport(null);
          let rejected = null;
          try {
            anchor.stateProxy.query = "blocked";
          } catch (error) {
            rejected = error.message;
          }
          let siblingRejected = null;
          try {
            sibling.stateProxy.query = "also blocked";
          } catch (error) {
            siblingRejected = error.message;
          }
          return {
            rejected,
            siblingRejected,
            settlement,
            staleWireUpdates: staleCall && staleCall.stateUpdates,
            pending: Object.assign({}, anchor.pending),
            siblingPending: Object.assign({}, sibling.pending),
            query: anchor.stateProxy.query,
            siblingQuery: sibling.stateProxy.query,
          };
        }
        """
    )

    assert "writable fields: (none)" in refreshed["rejected"]
    assert "writable fields: (none)" in refreshed["siblingRejected"]
    assert refreshed["settlement"] == "rejected"
    assert refreshed["staleWireUpdates"] is None
    assert refreshed["pending"] == {}
    assert refreshed["siblingPending"] == {}
    assert refreshed["query"] == "hats"
    assert refreshed["siblingQuery"] == "boots"


# ----- scopes -----


def test_scope_isolation_between_nested_instances(page: Any, serve_live: Any) -> None:
    # The boundary entry's truncation cuts scope inheritance at the nested
    # instance root: the outer root's own x-data is visible inside the outer
    # component and inside an anonymous nested x-data (Alpine-native nesting
    # kept), but not inside the nested citry instance. $state resolves per
    # instance on both sides.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class InnerState:
        owner: str = "inner"

    class Inner(Component):
        citry = c
        State = InnerState

        class Events:
            def ping(self, state):
                return None

        template = """
          <section class="inner">
            <span class="inner-secret" x-text="typeof outerSecret"></span>
            <span class="inner-owner" x-text="$state.owner"></span>
          </section>
        """

    class OuterState:
        owner: str = "outer"

    class Outer(Component):
        citry = c
        State = OuterState

        class Events:
            def pong(self, state):
                return None

        template = """
          <div class="outer" x-data='{"outerSecret": "s3cret"}'>
            <span class="outer-secret" x-text="typeof outerSecret"></span>
            <span class="outer-owner" x-text="$state.owner"></span>
            <div x-data='{"anon": 1}'>
              <span class="anon-secret" x-text="typeof outerSecret"></span>
            </div>
            <c-inner />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body><c-outer /></body>
          </html>
        """

    messages = _collect_console(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    assert page.locator(".outer-secret").inner_text() == "string"
    assert page.locator(".anon-secret").inner_text() == "string"
    assert page.locator(".inner-secret").inner_text() == "undefined"
    assert page.locator(".outer-owner").inner_text() == "outer"
    assert page.locator(".inner-owner").inner_text() == "inner"
    assert _citry_errors(messages) == []


def test_head_placed_c_js_still_isolates_nested_instances(page: Any, serve_live: Any) -> None:
    # The nested-isolation contract again, with the one template change that
    # used to break it: `<c-js />` in `<head>`. The placeholder pulls the
    # events manifest and the runtime script into the head, so the runtime
    # consumes the manifest while only the head is parsed and the attach-by-
    # query finds no instance roots. The boundary must then attach from
    # Alpine's init walk instead, and the isolation still holds.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class InnerState:
        owner: str = "inner"

    class Inner(Component):
        citry = c
        State = InnerState

        class Events:
            def ping(self, state):
                return None

        template = """
          <section class="inner">
            <span class="inner-secret" x-text="typeof outerSecret"></span>
            <span class="inner-owner" x-text="$state.owner"></span>
          </section>
        """

    class OuterState:
        owner: str = "outer"

    class Outer(Component):
        citry = c
        State = OuterState

        class Events:
            def pong(self, state):
                return None

        template = """
          <div class="outer" x-data='{"outerSecret": "s3cret"}'>
            <span class="outer-secret" x-text="typeof outerSecret"></span>
            <span class="outer-owner" x-text="$state.owner"></span>
            <c-inner />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head>
              <c-js />
            </head>
            <body><c-outer /></body>
          </html>
        """

    messages = _collect_console(page)
    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    # The scenario precondition: the runtime script really sits in <head>.
    assert page.evaluate("""() => !!document.head.querySelector('script[src$="ext/events/runtime.js"]')""") is True

    assert page.locator(".outer-secret").inner_text() == "string"
    assert page.locator(".inner-secret").inner_text() == "undefined"
    assert page.locator(".outer-owner").inner_text() == "outer"
    assert page.locator(".inner-owner").inner_text() == "inner"
    # Both roots carry the boundary entry: the outer under its own x-data
    # layer, the inner as its whole stack (ancestors cut).
    stacks = page.evaluate(
        """
        () => ({
          outer: document.querySelector(".outer")._x_dataStack.map((layer) => Object.keys(layer)),
          inner: document.querySelector(".inner")._x_dataStack.map((layer) => Object.keys(layer)),
        })
        """
    )
    assert stacks == {"outer": [["outerSecret"], []], "inner": [[]]}
    assert _citry_errors(messages) == []


def test_fragment_inserted_into_live_x_data_region_stays_isolated(page: Any, serve_live: Any) -> None:
    # The case that makes the isolation truncation load-bearing: on the
    # initial page, boundary entries attach during parse when no ancestor
    # scope exists yet, but a fragment lands AFTER Alpine.start() inside an
    # already-initialized x-data region, where addScopeToNode alone would
    # bake the ancestor scopes into the instance root's stack. The truncation
    # cuts them, so the late instance sees neither the page scope nor
    # anything else above it.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class SeedState:
        label: str = "seed"

    class Seed(Component):
        citry = c
        State = SeedState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="seed">seed</div>
        """

    class LateState:
        label: str = "late"

    class Late(Component):
        citry = c
        State = LateState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="late">
            <span class="late-secret" x-text="typeof pageSecret"></span>
            <span class="late-label" x-text="$state.label"></span>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body>
              <c-seed />
              <div x-data='{"pageSecret": "leak"}'>
                <div id="target"></div>
              </div>
              <script>
                window.__insertFragment = () =>
                  fetch("/fragment")
                    .then((r) => r.text())
                    .then((html) => { document.getElementById("target").innerHTML = html; });
              </script>
            </body>
          </html>
        """

    fragment_html = Late().render().serialize(deps_strategy="fragment")
    base = serve_live(c, str(Page()), fragment_html)
    page.goto(base + "/")
    page.wait_for_function(READY)

    page.evaluate("() => window.__insertFragment()")
    page.wait_for_function("document.querySelector('.late-label')?.innerText === 'late'")

    assert page.locator(".late-secret").inner_text() == "undefined"
    # The late root's stack is exactly the empty boundary: ancestors cut.
    stack_keys = page.evaluate(
        """() => document.querySelector(".late")._x_dataStack.map((layer) => Object.keys(layer))"""
    )
    assert stack_keys == [[]]
    # The page's own x-data region still works for the page itself.
    assert page.evaluate("() => window.Alpine.evaluate(document.getElementById('target'), 'pageSecret')") == "leak"


def test_user_x_data_on_instance_root_coexists_on_the_scope_stack(page: Any, serve_live: Any) -> None:
    # The purity check runs against the scope stack itself, not Object.keys
    # on the merged $data proxy (which hides every key, spike F6): the
    # instance root's stack is exactly [the user's x-data layer, the empty
    # boundary entry], so citry added no enumerable key to any user scope.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class CardState:
        label: str = "card"

    class Card(Component):
        citry = c
        State = CardState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="card" x-data='{"open": true}'>
            <span class="both" x-text="open + ':' + $state.label"></span>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body><c-card /></body>
          </html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    assert page.locator(".both").inner_text() == "true:card"
    stack_keys = page.evaluate(
        """() => document.querySelector(".card")._x_dataStack.map((layer) => Object.keys(layer))"""
    )
    assert stack_keys == [["open"], []]


def test_magics_resolve_inside_nested_user_x_data(page: Any, serve_live: Any) -> None:
    # A user's own x-data inside the component template nests normally and
    # still sees the citry magics (design 5.5: it is the home for client-only
    # UI state).
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class BoxState:
        label: str = "boxed"

    class Box(Component):
        citry = c
        State = BoxState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="box">
            <div x-data='{"open": true}'>
              <span class="probe" x-text="open ? $state.label : 'closed'"></span>
            </div>
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body><c-box /></body>
          </html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    assert page.locator(".probe").inner_text() == "boxed"


def test_shared_root_resolves_magics_to_the_innermost_instance(page: Any, serve_live: Any) -> None:
    # One element roots both a wrapper and its only child (data-cid carries
    # both ids, innermost last): expression-level magics resolve to the
    # child, while the wrapper keeps full access through its $component
    # payload (the same registry state object, no DOM walk).
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class ChildState:
        owner: str = "child"

    class Child(Component):
        citry = c
        State = ChildState

        class Events:
            def ping(self, state):
                return None

        template = """
          <p class="shared" x-text="$state.owner"></p>
        """

    class WrapState:
        owner: str = "wrap"

    class Wrap(Component):
        citry = c
        State = WrapState

        class Events:
            def pong(self, state):
                return None

        js = """
          $component((ctx) => {
            window.__wrap = {
              stateOwner: ctx.state ? ctx.state.owner : null,
              sendEvent: typeof ctx.sendEvent,
              onEvent: typeof ctx.onEvent,
            };
          });
        """
        template = """
          <c-child />
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body><c-wrap /></body>
          </html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("!!window.__wrap")

    marker = page.evaluate("""() => document.querySelector(".shared").getAttribute("data-cid")""")
    assert len(marker.split()) == 2  # both ids on the one element, innermost last
    assert page.locator(".shared").inner_text() == "child"
    assert page.evaluate("window.__wrap") == {"stateOwner": "wrap", "sendEvent": "function", "onEvent": "function"}


# ----- the two identities and the three-way split (stubbed render metadata) -----


def test_same_class_render_reconciles_and_relinks_the_faithful_id(page: Any, serve_live: Any) -> None:
    # The anchor-side of a same-class re-render, exactly what the actions
    # applier will call around its morph: linkRenderedInstance BEFORE the
    # patch (both the old and the fresh component id resolve to the anchor
    # through the patch window), finishRender after. Server wins per field
    # except the pending unsent local write; the $state facade and the
    # reactive object keep their identity; the registry entry now shows the
    # server's fresh id while the anchor is unchanged.
    _goto_todo(page, serve_live)

    result = page.evaluate(
        """
        () => {
          const internal = Citry.events._internal;
          const oldId = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = internal.getAnchor(oldId);
          anchor.stateProxy.query = "local-q"; // a pending, not-yet-sent write
          const before = { proxy: anchor.stateProxy, values: anchor.values, anchorId: anchor.anchorId };

          const outcome = internal.linkRenderedInstance(anchor, {
            componentId: "srv-fresh-1",
            classId: anchor.classId,
            token: "tok-2",
            values: { query: "server-q", note: "server-note", count: 9 },
          });
          const during = {
            oldStillMapped: internal.getAnchor(oldId) === anchor,
            freshMapped: internal.getAnchor("srv-fresh-1") === anchor,
          };
          internal.finishRender(anchor, outcome.oldComponentId);

          return {
            branch: outcome.branch,
            during,
            proxyKept: anchor.stateProxy === before.proxy,
            valuesKept: anchor.values === before.values,
            anchorIdKept: anchor.anchorId === before.anchorId,
            query: anchor.values.query,
            note: anchor.values.note,
            count: anchor.values.count,
            pendingKept: anchor.pending.query === "local-q",
            oldGone: internal.getAnchor(oldId) === null,
            freshIs: internal.getAnchor("srv-fresh-1") === anchor,
            componentId: anchor.componentId,
            token: anchor.token,
          };
        }
        """
    )
    assert result == {
        "branch": "reconcile",
        "during": {"oldStillMapped": True, "freshMapped": True},
        "proxyKept": True,
        "valuesKept": True,
        "anchorIdKept": True,
        "query": "local-q",  # pending unsent local write wins
        "note": "server-note",  # server wins a clean field
        "count": 9,
        "pendingKept": True,
        "oldGone": True,
        "freshIs": True,
        "componentId": "srv-fresh-1",
        "token": "tok-2",
    }


def test_different_class_adopts_wholesale_and_plain_html_discards(page: Any, serve_live: Any) -> None:
    # The other two branches of the three-way split. A different class
    # discards the old state and adopts the server values wholesale: the
    # $state identity is rebuilt, the writable set switches to the new
    # class's fields, pending writes are dropped. A plain-HTML render then
    # retires the anchor entirely, and $state on the still-marked element
    # goes inert instead of throwing.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class CardState:
        title: str = "t1"

    class Card(Component):
        citry = c
        State = CardState

        class Events:
            def save(self, state):
                return None

        template = """
          <div class="card">
            <span class="t" x-text="$state.title"></span>
          </div>
        """

    class PanelState:
        mode: str = "m1"

    class Panel(Component):
        citry = c
        State = PanelState

        class Events:
            def flip(self, state):
                return None

        template = """
          <section class="panel">
            <span x-text="$state.mode"></span>
          </section>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body>
              <c-card />
              <c-panel />
            </body>
          </html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    result = page.evaluate(
        """
        () => {
          const internal = Citry.events._internal;
          const cardId = document.querySelector(".card").getAttribute("data-cid");
          const panelClass = internal.getAnchor(
            document.querySelector(".panel").getAttribute("data-cid")
          ).classId;
          const anchor = internal.getAnchor(cardId);
          anchor.stateProxy.title = "local-title"; // pending write, dropped by the class switch
          const before = { proxy: anchor.stateProxy, values: anchor.values };

          const adopt = internal.linkRenderedInstance(anchor, {
            componentId: "srv-panel-1",
            classId: panelClass,
            token: "tok-p",
            values: { mode: "adopted" },
          });
          internal.finishRender(anchor, adopt.oldComponentId);
          let oldFieldWrite = null;
          try {
            anchor.stateProxy.title = "x";
          } catch (err) {
            oldFieldWrite = String(err.message);
          }
          const adopted = {
            branch: adopt.branch,
            proxyRebuilt: anchor.stateProxy !== before.proxy,
            valuesRebuilt: anchor.values !== before.values,
            mode: anchor.values.mode,
            titleGone: anchor.values.title === undefined,
            pendingCleared: Object.keys(anchor.pending).length === 0,
            classId: anchor.classId,
            token: anchor.token,
            oldFieldWriteThrew: oldFieldWrite !== null && oldFieldWrite.includes("not client-writable"),
          };

          const anchorsBefore = internal.anchors.size;
          const plain = internal.linkRenderedInstance(anchor, null);
          const inert = window.Alpine.evaluate(document.querySelector(".card"), "$state.title");
          return {
            adopted,
            plain: {
              branch: plain.branch,
              freshGone: internal.getAnchor("srv-panel-1") === null,
              anchorRetired: internal.anchors.size === anchorsBefore - 1,
              inertRead: inert === undefined,
            },
          };
        }
        """
    )
    assert result == {
        "adopted": {
            "branch": "adopt",
            "proxyRebuilt": True,
            "valuesRebuilt": True,
            "mode": "adopted",
            "titleGone": True,
            "pendingCleared": True,
            "classId": result["adopted"]["classId"],  # asserted non-trivially below
            "token": "tok-p",
            "oldFieldWriteThrew": True,
        },
        "plain": {
            "branch": "plain-html",
            "freshGone": True,
            "anchorRetired": True,
            "inertRead": True,
        },
    }
    assert result["adopted"]["classId"].startswith("Panel_")


def test_state_is_inert_for_unregistered_marker_and_pointed_outside(page: Any, serve_live: Any) -> None:
    # The two edges of magic resolution (design 5.3/5.5). A marker-bearing
    # element whose id is not registered (the mid-morph window; here a
    # hand-inserted ghost) reads as inert: bound text renders the fallback
    # and nothing throws. An element with no citry marker anywhere above it
    # gets the hard pointed error instead (surfaced through Alpine's
    # expression error handling on the console).
    messages = _goto_todo(page, serve_live)

    page.evaluate(
        """
        () => {
          document.body.insertAdjacentHTML(
            "beforeend",
            '<div data-cid-ghost1 data-cid="ghost1">' +
              '<span class="ghost" x-text="$state.anything === undefined ? \\'inert\\' : \\'leak\\'"></span></div>'
          );
        }
        """
    )
    page.wait_for_function("document.querySelector('.ghost')?.innerText === 'inert'")
    assert _citry_errors(messages) == []

    # Alpine reports expression errors on the console (it does not rethrow
    # synchronously), so the pointed error is asserted there.
    with page.expect_console_message(lambda msg: "outside any interactive component instance" in msg.text):
        page.evaluate("""() => { window.Alpine.evaluate(document.body, "$state.anything"); }""")


# ----- $loading / $error over a stubbed transport -----


def test_loading_and_error_transitions_with_a_stubbed_transport(page: Any, serve_live: Any) -> None:
    # The anchor-side send pipeline drives $loading (callable, per-handler)
    # and $error (last envelope, cleared on the next success) around a
    # transport stub set through the internal hook. The call record the
    # transport receives carries the instance's class, event, faithful id,
    # token, and the queued pending updates.
    _goto_todo(page, serve_live)

    # In-flight: the stub holds the promise open so the loading flags show.
    page.evaluate(
        """
        () => {
          window.__calls = [];
          Citry.events._internal.setTransport((call) => {
            window.__calls.push(call);
            return new Promise((resolve, reject) => {
              window.__settle = { resolve, reject };
            });
          });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          anchor.stateProxy.query = "typed"; // queue a pending update to ride the call
          window.__sent = Citry.events.send(id, "save", { extra: 1 });
          window.__sent.then(
            (v) => { window.__outcome = ["ok", v]; },
            (e) => { window.__outcome = ["err", String(e.message || e)]; },
          );
        }
        """
    )
    page.wait_for_function("document.querySelector('.busy').innerText === 'busy'")
    assert page.locator(".busy-save").inner_text() == "busy"
    call = page.evaluate("window.__calls[0]")
    assert call["componentClassId"].startswith("Todo_")
    assert call["handlerName"] == "save"
    assert call["callerRenderId"] == page.evaluate("document.querySelector('.todo').getAttribute('data-cid')")
    assert call["stateToken"].startswith("cev1.")
    assert call["stateUpdates"] == {"query": "typed"}
    assert call["args"] == {"extra": 1}
    # The queued write was snapshotted into the call: no longer pending.
    assert (
        page.evaluate(
            "Citry.events._internal.getAnchor(document.querySelector('.todo').getAttribute('data-cid')).pending"
        )
        == {}
    )

    # Success settles loading and resolves the caller with the transport's value.
    page.evaluate("window.__settle.resolve({ ok: true })")
    page.wait_for_function("document.querySelector('.busy').innerText === 'idle'")
    assert page.evaluate("window.__outcome") == ["ok", {"ok": True}]
    assert page.locator(".err").inner_text() == "none"

    # A failed call sets $error to the structured envelope...
    page.evaluate(
        """
        () => {
          window.__sent2 = Citry.events.send(
            document.querySelector(".todo").getAttribute("data-cid"), "find", {},
          );
          window.__sent2.catch(() => {});
          window.__settle.reject({ status: 422, code: "invalid_args", message: "boom", fieldErrors: {} });
        }
        """
    )
    page.wait_for_function("document.querySelector('.err').innerText === 'boom'")
    error = page.evaluate(
        "Citry.events._internal.getAnchor(document.querySelector('.todo').getAttribute('data-cid')).errorBox.current"
    )
    assert error == {"status": 422, "code": "invalid_args", "message": "boom", "fieldErrors": {}}

    # ...and the next successful call clears it.
    page.evaluate(
        """
        () => {
          window.__sent3 = Citry.events.send(
            document.querySelector(".todo").getAttribute("data-cid"), "save", {},
          );
          window.__settle.resolve({ ok: true });
        }
        """
    )
    page.wait_for_function("document.querySelector('.err').innerText === 'none'")


def test_failed_send_restores_pending_updates_for_the_retry(page: Any, serve_live: Any) -> None:
    # The local-first failure path: a send snapshots the queued $state writes
    # into the call and drains the pending queue, so a REJECTED call must put
    # them back, or the retry would carry no updates and the next incoming
    # render would silently revert the field (server wins a field only when
    # no pending unsent write holds it). A field the user wrote again while
    # the call was in flight keeps the newer value.
    _goto_todo(page, serve_live)

    page.evaluate(
        """
        () => {
          window.__calls = [];
          window.__outcomes = [];
          Citry.events._internal.setTransport((call) => {
            window.__calls.push(call);
            return new Promise((resolve, reject) => {
              window.__settle = { resolve, reject };
            });
          });
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          window.__pending = () => Citry.events._internal.getAnchor(
            document.querySelector(".todo").getAttribute("data-cid")
          ).pending;
          anchor.stateProxy.query = "draft"; // queue a write, then fail the send
          Citry.events.send(id, "save", {}).catch(() => { window.__outcomes.push("fail1"); });
        }
        """
    )
    # Mid-flight the write rides the call and the queue is drained.
    assert page.evaluate("window.__calls[0].stateUpdates") == {"query": "draft"}
    assert page.evaluate("window.__pending()") == {}

    # The failure puts the unsent write back in the queue.
    page.evaluate("window.__settle.reject(new Error('net down'))")
    page.wait_for_function("window.__outcomes.length === 1")
    assert page.evaluate("window.__pending()") == {"query": "draft"}

    # The retry carries it again, and success drains it for good.
    page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          Citry.events.send(id, "save", {}).then(
            () => { window.__outcomes.push("ok2"); },
            () => { window.__outcomes.push("fail2"); },
          );
        }
        """
    )
    assert page.evaluate("window.__calls[1].stateUpdates") == {"query": "draft"}
    page.evaluate("window.__settle.resolve({ ok: true })")
    page.wait_for_function("window.__outcomes.length === 2")
    assert page.evaluate("window.__outcomes") == ["fail1", "ok2"]
    assert page.evaluate("window.__pending()") == {}

    # A write made while a failing call is in flight wins over the restore:
    # the newer value stays queued, the stale snapshot does not clobber it.
    page.evaluate(
        """
        () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          const anchor = Citry.events._internal.getAnchor(id);
          anchor.stateProxy.count = 7;
          Citry.events.send(id, "find", {}).catch(() => { window.__outcomes.push("fail3"); });
          anchor.stateProxy.count = 8; // in-flight rewrite
        }
        """
    )
    assert page.evaluate("window.__calls[2].stateUpdates") == {"count": 7}
    page.evaluate("window.__settle.reject(new Error('net down again'))")
    page.wait_for_function("window.__outcomes.length === 3")
    assert page.evaluate("window.__pending()") == {"count": 8}


def test_unknown_names_throw_pointed_errors_naming_declared_events(page: Any, serve_live: Any) -> None:
    # $loading and sendEvent validate names against the class descriptor
    # before anything could hit a wire; the errors name the declared events.
    _goto_todo(page, serve_live)

    # The expression path: Alpine reports expression errors on the console
    # (never a synchronous rethrow), so the $loading pointed error lands there.
    with page.expect_console_message(
        lambda msg: "has no event 'nope'" in msg.text and "declared events: find, save" in msg.text
    ):
        page.evaluate("""() => { window.Alpine.evaluate(document.querySelector(".todo"), "$loading('nope')"); }""")

    # The promise path keeps the same pointed message.
    send_err = page.evaluate(
        """
        async () => {
          const id = document.querySelector(".todo").getAttribute("data-cid");
          return await Citry.events.send(id, "nope", {}).then(
            () => null,
            (err) => String(err.message),
          );
        }
        """
    )
    assert send_err is not None
    assert "has no event 'nope'" in send_err
    assert "declared events: find, save" in send_err


# ----- $component payload and server-dispatched events -----


def test_payload_members_for_a_non_interactive_instance(page: Any, serve_live: Any) -> None:
    # The decorator runs for every $component payload. A component with no
    # Events class gets state: null and members whose errors say plainly why
    # they cannot do more.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class PlainState:
        label: str = "irrelevant"

    class Interactive(Component):
        citry = c
        State = PlainState

        class Events:
            def poke(self, state):
                return None

        template = """
          <div class="interactive">on</div>
        """

    class Plain(Component):
        citry = c
        js = """
          $component((ctx) => {
            window.__plain = { state: ctx.state };
            ctx.sendEvent("anything").catch((err) => {
              window.__plainSendErr = String(err.message);
            });
          });
        """
        template = """
          <div class="plain">off</div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body>
              <c-interactive />
              <c-plain />
            </body>
          </html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("!!window.__plainSendErr")

    assert page.evaluate("window.__plain.state") is None
    err = page.evaluate("window.__plainSendErr")
    assert "declares no events" in err
    assert "class Events" in err


def test_onevent_scopes_to_the_instance_and_global_on_unwraps_detail(page: Any, serve_live: Any) -> None:
    # Server-dispatched events arrive as bubbling CustomEvents on the target
    # instance's elements (that is what the actions applier will do). An
    # instance's onEvent fires only for events whose nearest instance root is
    # its own: an event aimed at the nested child does not fire the parent's
    # subscription even though it bubbles through the parent's DOM. The
    # global Citry.events.on hears everything, unwrapped to the detail.
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")

    class InState:
        owner: str = "in"

    class In(Component):
        citry = c
        State = InState

        class Events:
            def ping(self, state):
                return None

        js = """
          $component((ctx) => {
            window.__inLog = [];
            ctx.onEvent("todo:done", (detail) => { window.__inLog.push(detail); });
          });
        """
        template = """
          <section class="in">in</section>
        """

    class OutState:
        owner: str = "out"

    class Out(Component):
        citry = c
        State = OutState

        class Events:
            def pong(self, state):
                return None

        js = """
          $component((ctx) => {
            window.__outLog = [];
            ctx.onEvent("todo:done", (detail) => { window.__outLog.push(detail); });
          });
        """
        template = """
          <div class="out">
            <c-in />
          </div>
        """

    class Page(Component):
        citry = c
        template = """
          <html>
            <head></head>
            <body><c-out /></body>
          </html>
        """

    base = serve_live(c, str(Page()), "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("!!window.__inLog && !!window.__outLog")

    result = page.evaluate(
        """
        () => {
          window.__globalLog = [];
          Citry.events.on("todo:done", (detail) => { window.__globalLog.push(detail); });
          const fire = (el, n) =>
            el.dispatchEvent(new CustomEvent("todo:done", { bubbles: true, detail: { n } }));
          fire(document.querySelector(".in"), 1);   // aimed at the child
          fire(document.querySelector(".out"), 2);  // aimed at the parent
          return { inLog: window.__inLog, outLog: window.__outLog, globalLog: window.__globalLog };
        }
        """
    )
    assert result == {
        "inLog": [{"n": 1}],
        "outLog": [{"n": 2}],
        "globalLog": [{"n": 1}, {"n": 2}],
    }


# ----- the bootstrap stub and boot-order edges -----


def test_bootstrap_stub_queues_and_the_runtime_drains(page: Any, serve_live: Any) -> None:
    # A hand-ordered page proving the load-ordering contract (design 5.2):
    # the inline stub (the real emitted constant) runs first, calls made
    # before the runtime arrives queue on it, and the runtime replaces the
    # stub and drains the queue. Configure deliberately precedes transport
    # registration in the stub queue; the runtime installs declarations in a
    # first pass, so the configured transport serves the queued valid send.
    # A queued applyActions call proves that public Promise surface too.
    from citry.ext.events.emission import _EVENTS_BOOTSTRAP_STUB

    manifest = json.dumps(
        {
            "protocol": "citry-events/1",
            "clientGraphRevision": None,
            "componentClasses": [
                {
                    "componentClassId": "StubCls",
                    "eventHandlers": {"save": {"httpMethod": "POST"}},
                }
            ],
            "componentInstances": [
                {
                    "renderId": "x1",
                    "componentClassId": "StubCls",
                    "stateToken": "stub-token",
                    "publicState": {"n": 1},
                }
            ],
        }
    )
    page_html = f"""
    <html>
      <head></head>
      <body>
            <div data-cid-x1 data-cid="x1"></div>
        <script src="/citry/citry.js"></script>
        <script>{_EVENTS_BOOTSTRAP_STUB}</script>
        <script>
          window.__wasStub = !!Citry.events._stubQueue;
          Citry.events.configure({{ timeout: 5, transport: "early" }});
          window.__offPing = Citry.events.on("stub:ping", (detail) => {{ window.__pinged = detail; }});
          Citry.events.registerTransport("early", {{
            send: (envelope) => Promise.resolve({{
              protocol: envelope.protocol,
              requestId: envelope.requestId,
              results: envelope.calls.map((call) => ({{
                ok: true,
                sendSequence: call.sendSequence,
                actions: [{{ action: "data", value: {{ via: "early" }} }}],
              }})),
            }}),
          }});
          window.__queuedApply = false;
          Citry.events.applyActions([
            {{ action: "event", eventName: "stub:ping", detail: {{ hi: true }} }},
          ]).then(() => {{ window.__queuedApply = true; }});
          Citry.events.send("x1", "save", {{}}).then(
            (v) => {{ window.__queuedOutcome = ["ok", v]; }},
            (e) => {{ window.__queuedOutcome = ["err", String(e.message || e)]; }},
          );
        </script>
        <script type="application/json" data-citry-events>{manifest}</script>
        <script src="/citry/ext/events/runtime.js"></script>
      </body>
    </html>
    """
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")
    base = serve_live(c, page_html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)
    page.wait_for_function("!!window.__queuedOutcome")
    page.wait_for_function("window.__queuedApply === true")

    result = page.evaluate(
        """
        () => {
          return {
            wasStub: window.__wasStub,
            stubGone: Citry.events._stubQueue === undefined,
            queuedOutcome: window.__queuedOutcome,
            configApplied: Citry.events._internal.config.timeout,
            transportApplied: Citry.events._internal.config.transport,
            pinged: window.__pinged,
                anchorSeeded: Citry.events._internal.getAnchor("x1").values.n,
          };
        }
        """
    )
    assert result["wasStub"] is True
    assert result["stubGone"] is True
    assert result["queuedOutcome"] == ["ok", {"via": "early"}]
    assert result["configApplied"] == 5
    assert result["transportApplied"] == "early"
    assert result["pinged"] == {"hi": True}
    assert result["anchorSeeded"] == 1


def test_foreign_alpine_warns_and_the_owned_global_wins(page: Any, serve_live: Any) -> None:
    # Morph's bridge reads window.Alpine.cloneNode, so leaving a foreign
    # object there after warning was internally inconsistent. A3 preserves
    # one Citry-owned global and names the fix.
    page_html = """
    <html>
      <head><script>window.Alpine = { probe: 1 };</script></head>
      <body>
        <script src="/citry/citry.js"></script>
        <script src="/citry/ext/events/runtime.js"></script>
      </body>
    </html>
    """
    c = Citry(secret=SIGNING_KEY)
    c.set_mounted_prefix("/citry")
    messages = _collect_console(page)
    base = serve_live(c, page_html, "")
    page.goto(base + "/")
    page.wait_for_function(READY)

    warnings = [m for m in messages if "another Alpine instance is already on this page" in m]
    assert warnings, f"expected the second-Alpine warning, got: {messages}"
    assert page.evaluate("window.Alpine.probe") is None
    assert (
        page.evaluate("window.Alpine === globalThis.Alpine && typeof window.Alpine.cloneNode === 'function'") is True
    )
