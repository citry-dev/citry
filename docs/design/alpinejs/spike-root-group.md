# RootGroup spike: faithful multi-root event aggregation

An empirical preimplementation spike for WP23, run on 2026-07-19 against the
repo's pinned Alpine 3.15.12 in headless Chromium, Firefox, and WebKit. It asks
whether a Citry-owned `RootGroup` can relocate one authored Alpine or Citry
handler to several rendered roots without inserting a wrapper element and
without turning one logical binding into independent per-root bindings.

This report calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

**Verdict: the adapter is feasible and the general multi-root wrapper error is
not needed.** One group can preserve Alpine's single-root modifier ordering,
native DOM values, union containment, shared timing and lifetime state,
dynamic membership, open-shadow composed paths, and one logical poll cadence.
All harness assertions passed in all three engines, with no page errors or
console output. Three full reruns produced byte-identical JSON.

This is a research prototype, not product runtime code. The result clears the
mechanism gate for WP23 stage two. Product integration still has to connect the
group to component-tag client binding records, parent lexical evaluation,
source Events anchors,
morph adoption, and the instance registry.

## Artifacts and rerun

- [`root_group_adapter.js`](root_group_adapter.js) is the isolated prototype.
  It imports no Alpine private module and is never bundled into Citry.
- [`root_group_scenarios.js`](root_group_scenarios.js) contains the browser
  scenarios.
- [`root_group_harness.py`](root_group_harness.py) loads the repo's real Alpine
  CDN build, drives all three Playwright engines, asserts the contract, and
  prints deterministic JSON. Generated evidence is not checked in.

Run with the repository's documented additive e2e environment:

```console
uv sync --locked --all-packages --group e2e
.venv/bin/python docs/design/alpinejs/root_group_harness.py
uv sync --locked --all-packages
```

Pins used by the recorded run:

| Piece | Pin |
|---|---|
| Alpine | 3.15.12, loaded from `packages/js/citry-client/node_modules/alpinejs/dist/cdn.js` |
| Playwright | 1.61.0 |
| Chromium | 149.0.7827.55 |
| Firefox | 151.0 |
| WebKit | 26.5 |

The three-run evidence hash was
`1d0f269b703a2029c6ee129cc4cd233a2caecdb1`. Timing assertions use eventual
states rather than recording clock values, so the JSON itself stayed stable.

## Baselines kept separate

### Alpine handlers

Alpine 3.15.12 constructs a listener in a fixed order, independent of the
author's modifier order. It normalizes the event name and options, wraps the
callback in debounce and then throttle, then wraps prevent, stop, once,
outside or away, self, submit flushing, and finally key filtering. See the
pinned [`utils/on.js`](../../../packages/js/citry-client/node_modules/alpinejs/src/utils/on.js).
Consequently:

- key, self, and outside rejection happens before `.once` is consumed;
- prevent and stop happen synchronously even when the callback is deferred;
- throttle wraps debounce when both are present;
- `.once.debounce` removes the listener immediately but leaves its accepted
  callback pending;
- synchronous `event.currentTarget` is the root, `window`, or `document`, and
  a deferred callback observes native `currentTarget === null`;
- Alpine's ordinary cleanup removes the listener but does not cancel a pending
  debounce timer.

The prototype reproduces that construction order instead of copying handlers
to roots with separate calls to `Alpine.bind`. Its single-root differential
oracle does use the public `Alpine.bind` API, so every compared case reaches
Alpine's real `on.js` path.

### Citry `@c-*` handlers

Citry's compiled modifier set is smaller: key, self, once, prevent, stop,
debounce, and throttle. Its current runtime keeps timing and once state per
element and binding slot, then executes through one delegated document
listener. See `runElementEventBindings` and `scheduleEventBinding` in
[`citry-events.ts`](../../../packages/js/citry-client/src/citry-events.ts).

The prototype therefore has a separate Citry profile. It shares state across
the group while retaining Citry's key, self, once, prevent, stop, and timing
order. It does not claim that Alpine and Citry currently have identical
`currentTarget` behavior: a direct grouped client binding reports the real child root,
whereas today's delegated plain-element `@c-*` listener reports `document`.
The recommended stage-two contract is direct-root semantics for a
client binding, because its child roots are the designed physical
event carriers. Existing plain-element delegation can remain an internal
optimization and is not changed by this spike.

## Evidence matrix

The following rows passed in Chromium, Firefox, and WebKit.

| Area | Probe | Observed result |
|---|---|---|
| Single-root Alpine differential | `.self.prevent.stop.once.debounce`, descendant rejection, and a second post-once dispatch | Alpine and RootGroup JSON matched exactly. The accepted event was prevented and stopped synchronously; one deferred callback ran with native `currentTarget: null`. |
| Keys and timing | `keyup.ctrl.enter`, leading throttle, and combined throttle plus debounce | Wrong keys were rejected before state changed. The first root won a throttle window, the last admitted root won debounce, and throttle wrapped debounce. |
| Global targets | `.window` and `.document` | One callback per logical group, not one per root. Native `currentTarget` remained `window` or `document`. |
| Outside aliases | `.outside` and `.away` | Both matched Alpine for one root. For several roots, events inside either root were rejected and a real gap was outside. |
| Outside visibility | A hidden, B visible; then both hidden | Any visible member made the group eligible. With both hidden, the outside callback did not run. Evaluation stayed on the first live root, even when another root supplied visibility. |
| Options and ordering | `.capture`, `.passive`, `.passive.false`, dot, camel, and submit model flushing | Listener options and capture-path position matched Alpine. Dot/camel event names and submit flush order matched. The pinned Alpine `passive.false` click-filter oddity is canaried and matched. |
| Direct DOM values | Root B and a descendant of B | `event.currentTarget` and the evaluation carrier were B during dispatch. After an `await`, native `currentTarget` was null while the separately captured carrier remained B. |
| Group state | `.once`, debounce, throttle, and two logical client bindings sharing one physical root | Once and timing state were shared per logical binding. Two distinct logical bindings on the same DOM root remained independent. |
| Propagation | Two same-target listeners plus `.stop.prevent` | Both listeners on the root ran; the ancestor did not. The event was prevented. |
| Redispatch | Dispatch the same `Event` object twice | Two callbacks ran. There is no Event-object deduplication. |
| Dynamic roots | Remove A, add C while throttle is open | Membership changed without resetting timing state. C was suppressed until the shared window reopened. |
| Detached adoption | Bind direct and window handlers before insertion, then connect, disconnect, and reconnect without changing membership | Detached delivery was suppressed; both handlers became active on connection, inactive on disconnection, and active again on reconnection without a sync call. |
| Global anchor election | Document event, remove elected A, event again | The evaluation carrier changed from A to the next live root B without reinstalling per-root global listeners. |
| Pending debounce | Remove its carrier; keep its carrier while adding another root; destroy the group | A removed carrier's callback was dropped, a surviving carrier's callback ran, and full teardown canceled pending work. |
| Enter and leave | Synthetic and real mouse/pointer movement across A, B, and a gap | A-to-B transitions were suppressed when `relatedTarget` stayed inside the union. Outside-to-A, A-to-gap, gap-to-B, and B-to-outside remained native boundaries. |
| Focus | Focus A, then B | Native `focus:a`, `blur:a`, `focus:b` ran. No synthetic group focus boundary was invented. |
| Shadow DOM | Composed click inside an open shadow root, then outside | The composed path identified the member as inside; the external click fired once. |
| Pointer capture | Capture on A, move to B, release | Capture and release completed in all engines. The native post-release leave carrier differed by engine and was preserved rather than normalized. |
| Poll | Tick on A, remove A, tick on B, restore A | One interval kept its cadence and elected `A, B, A`; partial membership changes did not create or reset per-root timers. |
| Live root list | Hold `group.els`, update membership, destroy | The array identity stayed stable and its contents changed in place, then cleared on teardown. |

The full single-root result object was identical between Alpine and RootGroup
in every engine. The only intentional differential probe was cleanup with a
pending debounce: Alpine produced one late callback, while RootGroup produced
zero.

## Contract pinned by the spike

### Membership and evaluation carriers

`RootGroup` owns one ordered, stable `els` array and updates it in place. This
is the recommended `ctx.els` representation: user code can retain the array
identity while membership stays current. Product code still needs to prove
that morph membership updates reach it at the correct time.

Ordinary event evaluation uses the root whose native listener received the
event. That carrier is captured separately from the Event so deferred or
async evaluation can retain `$el` while leaving `event.currentTarget`
untouched. Window, document, outside, away, and poll use the first connected
root at trigger time. If it disappears before deferred delivery, the first
live root is re-elected for a global event; a pending direct-root callback is
dropped when its actual carrier disappears.

### One logical binding lifetime

One binding owns all per-root listeners, its one global listener where
applicable, one once bit, debounce timer, throttle window, and cleanup.
Adding, removing, or reordering roots does not reset that state. `.once`
removes every listener for the logical binding after its first eligible
trigger, including when the accepted callback is still debounced.

Listeners attach as soon as a root joins the group, even when the root is
detached, because client binding adoption may precede fragment insertion. Delivery
still requires a connected carrier. Connection, disconnection, and
reconnection therefore need no separate membership notification.

Full logical teardown cancels pending timers. This deliberately strengthens
raw Alpine cleanup, which can invoke a debounced callback after cleanup. It is
the safer Citry lifecycle contract: a replaced client binding or dead logical instance
must not evaluate user code later. Partial membership changes do not cancel
group work indiscriminately; only a delayed direct callback whose physical
carrier died is dropped.

### Union rules

Outside and away use union containment through `Event.composedPath()` plus
ordinary DOM containment. A gap between roots remains outside. Visibility is
also a union rule: at least one connected member must pass Alpine's geometry
and `_x_isShown` checks.

Mouse and pointer enter/leave remain listeners on the real roots. The adapter
only drops a boundary event whose `relatedTarget` is contained by any current
member. It does not calculate a wrapper rectangle, deduplicate an Event, or
manufacture normalized pointer-capture behavior.

Focus and blur are aggregated native events. Moving focus between roots is
still a blur and a focus, as it would be for two elements inside a wrapper.

## Known boundaries and stage-two work

The positive verdict is for the RootGroup mechanism, not the whole client binding
feature. Stage two still has to prove these integrations in the real runtime:

1. Client binding adoption must create and update groups before incoming roots
   initialize, then clean replacement and removal exactly once.
2. Alpine handler expressions and optional Citry argument expressions authored
   on a child component tag evaluate against the exact parent source location.
   The physical carrier supplies only `$el`, `$dispatch`, and `$event`; native
   `currentTarget` remains untouched. RootGroup
   proves listener/modifier/carrier behavior; the focused
   [`boundary-handler scope spike`](spike-citry-handler-refs.md) proves the
   isolated evaluator. Real Citry server-handler parsing and dispatch remain
   product integration work.
3. Parent-owned Citry `@c-*` additionally dispatches through the exact source
   Events anchor. It cannot reuse nearest-child `sendFromElement` resolution.
4. Closed shadow roots cannot be classified faithfully by a document-level
   outside listener from a composed path that hides their internals. Citry's
   server-rendered roots normally live in light DOM. If closed-shadow roots
   become supported input, outside/away needs a shadow-local listener design
   or a pointed unsupported-case error.
5. The poll prototype proves one cadence and carrier transfer. Product poll
   integration must still preserve the source parent anchor, recurring queue
   key, visibility pause, and live argument evaluation.
6. The single-root differential should become a permanent canary when the
   adapter enters product code, because Alpine's `on.js` remains private and
   can change on an upgrade.

Pointer capture deserves an explicit non-normalization clause. Chromium and
Firefox reported the final leave on B after capture release, while WebKit
reported it on A. All three were native, internally consistent event streams.
The RootGroup guarantee is therefore filtering by union membership when a
native boundary event exists, not making all engines emit an identical
boundary carrier.

## Recommendation for WP23

Proceed with a Citry-owned `RootGroup` in stage two. Keep ordinary listeners
on each live root, global and outside listeners once per binding, and all
timing and lifecycle state on the logical binding. Use the stable in-place
`els` array for the group and `$component` context. Preserve native DOM event
objects and use a separate evaluation-carrier value rather than forging
`currentTarget`.

Do not use the generic multi-root wrapper error for the supported light-DOM
and open-shadow cases proven here. Retain a pointed error only for a concrete
unsupported combination, such as closed-shadow outside/away, until that case
has its own listener design.
