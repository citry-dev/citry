# Analysis: anchor continuity for nested instances under a parent morph

A design analysis of the open question in [`../events.md`](../events.md) 16.1
("**Anchor lifecycle for nested instances**", events.md:3754-3763), the item
that becomes blocking before WP16/WP17. This document is the input to a maintainer
decision, not a decision: it enumerates the options, stress-tests each one
against concrete scenarios (including the maintainer's current lean), and ends
with a recommendation, its falsifiers, and the decisions that remain open.

Written 2026-07-14, revised 2026-07-15, against the landed WP15 client
runtime.

## Prior art (what was read)

Design sources, read in full at the cited ranges:

- [`../events.md`](../events.md) 4.2 (the call envelope; the per-anchor epoch
  bullet, events.md:1427-1443; the `instance` field semantics,
  events.md:1409-1418), 4.3 (the result envelope; the action table
  events.md:1504-1511; targets and the zero-match warning,
  events.md:1513-1525; faithful ordering, events.md:1527-1539), 4.4 (the
  events manifest, events.md:1584-1635), 5.3 in full (morph rules,
  events.md:2053-2202; the anchor and correlation routing,
  events.md:2060-2069; link before morph, events.md:2070-2076; the pinned
  morph call, events.md:2095-2127; keys are user-authored,
  events.md:2154-2161; the single-root morph call, "**`morph()` is
  single-root by construction**", events.md:2162-2169; "**a parent's morph
  does not skip nested instance roots**", events.md:2170-2182), 5.5 in full
  (the two identities,
  events.md:2255-2269; the anchor-keyed registry, events.md:2271-2281; magic
  resolution by innermost marker, events.md:2282-2297; the reconcile rule,
  events.md:2392-2402; the three-way state split, events.md:2404-2422), 7.5
  ("**The golden rule to teach**", events.md:2988-2996), and 16.1 (the
  nested-anchor bullet, "**Anchor lifecycle for nested instances**",
  events.md:3754-3763, and its two neighbors: "**A render addressed to a
  different element**", events.md:3764-3770, and "**Anchor creation versus
  update for server push and host-inserted fragments**",
  events.md:3771-3777).
- [`spike-component-identity.md`](../alpinejs/spike-component-identity.md) in full:
  findings F-CI-1 through F-CI-6 (lines 519-541), the anchor lifecycle
  (326-345), the link-before-morph ordering requirement (347-354), the epoch
  bookkeeping (390-401), and the deferred nested-anchor item this analysis
  answers (499-503).
- [`../events_plan.md`](../events_plan.md): WP15's landed-status block
  (events_plan.md:1382-1402), WP16 in full (events_plan.md:1527-1626), WP17
  in full (events_plan.md:1630-1675).

Code, read in full:

- `packages/js/citry-client/src/citry-events.ts` (1197 lines; the TypeScript
  source is what exists, the JS-to-TS conversion has landed; the committed
  bundle at `citry/ext/events/client/citry-events.js` is its build output).
  The file is under active parallel edit, so every cite names the symbol as
  well as the range (ranges re-verified 2026-07-15 against the file's
  10:13 state; on drift, resolve by symbol):
  the anchor and index maps (citry-events.ts:396-404), `createAnchor`
  (532-558), `reconcileValues` (564-569), `linkRenderedInstance` (583-621),
  `finishRender` (625-628), the manifest adoption with its existing-id
  guard (`applyEventsManifest`, 655-685), `interceptInit` (369-388),
  `resolveAnchor` and the inert `$state` (726-761), `sendFromAnchor` with
  the pending-writes snapshot and the rejection restore (804-868),
  `subscribeForAnchor` (886-897), the `$onComponent` decoration
  (`decorateComponentContext`, 976-1022), and the events-manifest
  MutationObserver (1124-1133).
- `packages/py/citry/citry/ext/dependencies/client/citry.js` (435 lines): the
  WP4 removal reconciler (`liveInstances` citry.js:74-80,
  `sweepRemovedInstances` 254-264, the microtask-debounced `scheduleSweep`
  266-274), the deferred Component.css GC (241-248), and the mutation
  observer that watches attributes so in-place `data-cid-<id>` swaps are
  seen (393-409).
- `packages/py/citry/citry/serialize.py` header and marker emission
  (serialize.py:3-10, 113): one element can carry several `data-cid-*`
  markers (a wrapper and its only child sharing a root).

Verification searches:

- `c-key` in the implementation: `grep -rn "c-key"` across
  `crates/citry_template_parser/src/` and `packages/py/citry/citry/` finds
  nothing; `c-key` in the design rides the compiler's generic
  dynamic-attribute handling, which has two channels. On a plain HTML
  element a dynamic attribute is split inline (the compiler emits
  `key="` + `ExprNode` + `"` between static string fragments,
  compiler.rs:39-42 and 365-401), so `c-key="item.id"` there already
  renders a plain `key` attribute. On a **component tag** the same
  attribute instead becomes an `ExprHtmlAttr` in the `ComponentNode`'s
  attrs (compiler.rs:31-37), which `_resolve_kwargs` turns into a component
  input with the `c-` prefix stripped (`_resolve_kwargs`,
  citry/nodes/__init__.py:779-821). What the child then does with that
  `key` input depends on its typing: a child that declares a `Kwargs`
  class (the documented norm) rejects the undeclared field with a
  `TypeError` at `cls.Kwargs(**raw_kwargs)` (component.py:474), so
  `<c-TodoItem c-key="item.id" />` is a render error today; only an
  untyped child (`Kwargs = None`) silently receives it as a kwarg. Either
  way nothing reaches the child's rendered root elements. That forwarding
  is the precise gap option C's key emission must close, and the render
  error means C has no existing-behavior compatibility burden to honor.
- The events runtime never deletes an anchor except in
  `linkRenderedInstance`'s plain-HTML branch (citry-events.ts:585-600) and
  never unlinks an id except there and in `finishRender` (625-628). No code
  path retires an anchor whose id leaves the DOM by any other route. This
  gap is load-bearing for every option (see "What the landed code does
  today").

## The problem, precisely

The two-identity model (events.md 5.5; the component-identity spike) is
proven for a **top-level instance re-rendering itself**: the response is
routed to the caller's anchor by the call-correlation id (the envelope `id`),
the fresh component id is linked to that anchor before the morph, and the
anchor keeps the instance's client-side continuity while the id under it
changes.

When a **parent** instance re-renders, its returned fragment contains fresh
component ids for every nested interactive child (the server re-renders the
whole subtree: "**a parent's morph does not skip nested instance roots**",
events.md:2170-2182, and mints fresh ids per the faithful-id
contract). The correlation id names the parent's anchor only. No correlation
routes to any child, so nothing says which old child (if any) the fresh child
id continues. Matching old child to replacement is kin to list identity and
`c-key` (the nested-anchor bullet, events.md:3760): the client would be
guessing identity the way an unkeyed list diff guesses it.

What hangs on the answer is exactly the anchor's payload, so it is worth
naming once. An anchor (the stable, client-internal identity of one
interactive DOM position) carries:

1. the **epoch pair** (send counter and highest-applied, the out-of-order
   guard, events.md:1426-1442),
2. the **reactive State object** and its `$state` facade, whose identity is
   what keeps Alpine subscribers alive across renders (the same-class
   reconcile branch of `linkRenderedInstance` is what preserves it,
   citry-events.ts:602-606; `adoptStateContract`, citry-events.ts:518-530,
   is where the object gets created),
3. the **pending unsent writes** queued by `$state` writes and two-way
   bindings, which win over incoming server values until sent
   (`reconcileValues`, citry-events.ts:564-569; the send snapshot in
   `sendFromAnchor`, citry-events.ts:815-822),
4. the **state token** the next send will carry,
5. the **`$loading` counters and `$error` box** (`createAnchor`,
   citry-events.ts:551-552),

plus two things held elsewhere that resolve through it: in-flight calls'
correlation records (their responses' instance-mutating actions apply to the
anchor) and `$onEvent` subscriptions (they read `anchor.componentId` at fire
time, `subscribeForAnchor`, citry-events.ts:886-897).

### What the landed code does today (the naive baseline)

If WP16 applied a parent's render with no new policy, the landed WP15 runtime
would do this, mechanically:

1. The morph patches the parent's subtree. Child roots with the same tag are
   patched **in place** (same DOM node, attributes swapped, F-CI-1), so the
   child's input elements, focus, and Alpine scopes survive as DOM.
2. The fragment's trailing `data-citry-events` manifest tag reaches the
   runtime only if WP16 delivers it. The pinned morph call is single-root
   ("**`morph()` is single-root by construction**", events.md:2162-2169):
   it consumes only the first element of the parsed HTML, so under a naive
   morph the trailing `data-citry-events` and `data-citry` tags are not
   part of the patched HTML at all. Assuming WP16 inserts them as new
   elements after the patch, the runtime's MutationObserver processes them
   then (observers deliver after the task). Pairing them in place instead
   (script patched against script) delivers nothing: the events-manifest
   observer watches `childList` only (citry-events.ts:1124-1133), and both
   it and the deps observer (citry.js:393-409) process manifest tags only
   from **added** Element nodes, so an in-place-patched script tag (text
   replaced, processed-stamp stripped) is invisible to both until some
   later full drain (`interceptInit` or `decorateComponentContext`)
   happens to run. During the
   patch, the fresh child ids are not in the index, so every `$state` read
   that morph's Alpine bridge evaluates inside a child resolves to the inert
   empty proxy (citry-events.ts:726-761). The inert proxy is not reactive:
   an effect that read it subscribed to nothing and will not re-run when the
   real anchor appears. Child bound text goes empty or stale indefinitely:
   the effect tracked no live dependency, so no later `$state` write can
   re-run it, and only re-initializing the element (a later swap or morph
   re-evaluating its expressions, or a fresh Alpine init walk) recovers the
   binding. This is finding F-CI-2 generalized from the self case to every
   id in the fragment.
3. When the manifest is processed, each fresh child id is unknown to the
   index, so `applyEventsManifest` **mints a fresh anchor** for it
   (citry-events.ts:678-682): server-rendered token and values, epoch zero,
   empty pending queue.
4. Nothing retires the old child anchors. Their ids left the DOM, but
   `anchors` and `idToAnchor` still hold them (no deletion path fires), so
   they leak; their `$onEvent` subscriptions silently never match again
   (the DOM no longer carries the old id); their in-flight responses will
   route to them and apply state to objects no DOM resolves to.

So the landed structure already behaves **reset-like by accident**, minus
retirement and minus the pre-registration that keeps mid-patch reads live.
Two conclusions before any option is weighed:

- **Every option requires new WP16 machinery.** "Do nothing" is not an
  option: pre-registration before the morph and retirement after it are
  mandatory work under reset and linking alike.
- The maintainer's lean is the smallest step from what exists, which is a
  real (but not decisive) argument for it.

### One rule for every uncorrelated id

A parent self-render is not the only way an instance id appears in a
response without a correlation of its own. The same situation arises for:

- a render action targeting a **CSS selector** whose fragment contains
  instances (`Render(Badge(...), target="#badge")`, events.md 7.5),
- a target region that **contains the caller** (the caller's own id is then
  an old id leaving the DOM, and the fragment's ids are all uncorrelated),
- v2 **server push** and host-inserted fragments ("**Anchor creation
  versus update for server push and host-inserted fragments**",
  events.md:3771-3777).

This analysis therefore frames the policy as: **what happens to every
instance id inside an applied render that is not the correlated caller, and
to every anchor whose id leaves the DOM as a result.** One rule for all of
them keeps the lifecycle explainable. Scope note: the neighbor 16.1 bullet
(which anchor's epoch guards a cross-target render, "**A render addressed
to a different element**", events.md:3764-3770)
stays its own question; this document only settles the fate of instance ids
inside whatever fragment gets applied, wherever it lands.

## Machinery every option needs (WP16 obligations regardless of choice)

These four pieces are option-independent. WP16 briefs can treat them as
settled requirements; the options only change step 2's matching rule.

1. **Generalized link-before-morph, plus WP16-owned manifest delivery.**
   Before calling morph (or any swap),
   parse the fragment's `data-citry-events` manifest tag out of the action's
   HTML and register **every** instance id it names: create-or-link anchors
   so that all ids resolve during the patch (F-CI-2 applied to the whole
   fragment, not just the correlated caller). WP16 also explicitly owns
   getting **both** trailing manifest tags into the DOM as inserted
   elements after the patch, rather than leaning on the observers to find
   them: the single-root morph call does not carry them ("**`morph()` is
   single-root by construction**", events.md:2162-2169), and neither
   observer reacts to a script tag patched in place (both process manifest
   tags only from added Element nodes). That covers `data-citry-events`
   (token refresh) and equally `data-citry`, because assets and the
   `$onComponent` teardown-and-re-fire, which the S7 healing path below
   depends on, ride the deps manifest. Under that insert-style delivery
   the landed manifest observer sees already-linked ids and only refreshes
   tokens, by the existing guard (`applyEventsManifest`,
   citry-events.ts:670-677), so no double handling occurs; the guard only
   helps when the tag arrives as an inserted element.
2. **A retirement sweep.** After the swap settles (and, because host-page JS
   can also remove subtrees containing instances, on DOM mutation like the
   deps manager does, citry.js:393-409), any anchor whose component id no
   longer has a `data-cid-<id>` element in the DOM is retired: unlink the id,
   drop the anchor from the registry, and null its fields the way the
   plain-HTML branch already does (citry-events.ts:585-600). Three spec
   points the nulling alone does not settle. What captured closures then
   do: a captured subscription goes silent (its fire-time handler returns
   early on the null id, `subscribeForAnchor`, citry-events.ts:888), but a
   captured `sendEvent`
   **throws** the declared-event check's pointed error (a retired anchor's
   null class declares no events, `requireDeclaredEvent`,
   citry-events.ts:438-454), whose message
   today names "component null"; the sweep spec should accept that throw or
   swap in a friendlier retired-instance message, never silence. The loss
   must be observable: when the sweep retires an anchor still holding
   non-empty pending writes or a nonzero `loading.any`, it emits a debug
   warning naming the class and the dropped field keys, because that is the
   exact moment reset discards user input or in-flight UI; without it the
   S1/S2 silent revert below is undiagnosable in the field. And timers ride
   the same lifecycle, in one of two forms the WP17 bindings brief must
   pick: **teardown-at-sweep** (interval-bearing bindings, `@c-poll` timers
   and pending debounce closures, tear down with the sweep) or
   **fire-time-liveness** (the timer stays keyed to the element and
   re-checks anchor liveness when it fires). Either form guarantees a
   replaced region never leaves a dead interval polling; the S1/S2
   walkthroughs below assume fire-time-liveness and say what changes under
   teardown-at-sweep. This mirrors the deps manager's
   `sweepRemovedInstances` but stays in the events runtime; the two layers
   keep composing without knowing each other (F-CI-5).
3. **A retired-anchor response policy.** A response whose correlation record
   points at a retired anchor still resolves its `data` action into the
   caller's promise and still applies non-instance actions; its
   instance-mutating actions (the self-targeted render and the token
   refresh) are dropped with a debug log. This extends the epoch guard's
   drop rule (events.md:1431-1438) to "the target position no longer
   exists".
4. **The epoch guard comparison, restated.** The guard applies an
   instance-mutating action iff its epoch is **strictly greater** than the
   anchor's highest-applied. Over at-most-once HTTP delivery this is
   behaviorally identical to 4.2's "drop when lower", and it is the form
   that lets a linking option invalidate all in-flight calls in one move
   (set highest-applied to the send counter; see option C's horizon cut).

Two cross-cutting facts that no option changes, stated once so the matrix
does not repeat them:

- **Cross-region ordering is not fixable client-side.** If a child's save
  response and an unrelated parent render race, the parent's fragment may
  have been computed server-side before the save; whichever applies last
  paints last. Epochs are per anchor and carry no cross-anchor order, and
  the wire carries no global order. Islands avoid the collision by never
  letting the parent touch the child; every other option can only choose
  which side wins ties it can see. The real mitigations are server-side
  design guidance (do not poll a coarse parent over independently edited
  children; poll leaf regions) and, in v2, a transport with server-ordered
  delivery.
- **`data-citry-busy` is client-stamped and morph strips it** from
  surviving elements (client-owned attributes absent from the incoming
  fragment are removed, F-CI-1). Whether and what to re-stamp after a swap
  is a WP16 detail; linking options have the bookkeeping to re-stamp
  meaningfully, reset does not (the new instance genuinely has no call in
  flight *from itself*).
- **A child's `$onComponent` teardown-and-re-fire cycle runs on every
  parent render under A, B, and C alike.** The deps manager keys callbacks
  and cleanups by component id (citry.js:71-80), and the child's id changes
  with every parent render regardless of anchor linking (the identity
  spike's scenario-5 pattern, extended to children), so imperative
  `$onComponent`-managed state (charts, editors, maps, the 5.5 examples)
  tears down and re-initializes each time. Anchor linking preserves State
  identity, pending writes, and subscriptions, never imperative widget
  state; that continuity remains the author's re-init code plus
  `data-citry-morph="ignore"` on non-root subtrees. Only D avoids the
  cycle, by never touching the child at all.
- **Whether an in-place attribute patch disturbs IME composition on a
  focused control is unverified**, and it is option-independent (only D
  avoids touching the child): the focused-value protection
  (events.md:2116-2118) covers the value only, not attribute patching over
  a composing input. If composition does abort, even option C's S1
  "survives" cell is optimistic for IME users. Verify in the WP16 e2e
  pass.

## Option A: reset on parent morph (the maintainer's lean)

**The rule.** Do not link children across a parent re-render. Every
uncorrelated instance id in an applied fragment mints a fresh anchor seeded
from the server-rendered token and values (already the landed behavior,
`applyEventsManifest`, citry-events.ts:678-682, once pre-registration moves
it before the morph).
Every anchor whose id left the DOM retires via the sweep. A child's
client-side continuity (its five payload items above) does not survive a
parent render; its DOM continuity (focus, caret, scroll, user `x-data`,
`data-citry-morph="ignore"` subtrees) survives exactly as far as the morph
preserves it.

**Why it is coherent.** It is the client mirror of the golden rule
("**The golden rule to teach**", events.md:2988-2996): the tree a handler
returns shares nothing with the
original render; the parent's returned tree is authoritative, and the
children in it are new children born of that render, with parent-recomputed
State. The server never promised these are "the same" children, so the
client does not pretend they are. It is also **uniform**: the same rule
covers morph and replace swaps, selector-targeted fragments, the
caller-inside-target case, host inserts, and v2 push, with no matching
heuristics anywhere. And it can never attribute state to the wrong entity,
because it never guesses identity.

**Work implied.** WP16: the shared machinery above; nothing else. WP17: all
binding state must resolve the anchor **at fire time from the element**
(never capture an anchor in a listener, poll timer, or debounce closure),
and one-way binding effects (which are runtime-registered effects, not
Alpine attributes, so the morph bridge does not re-evaluate them) must be
re-registered for every element whose innermost id changed after a swap.
Under reset that re-registration fires for every child under every parent
render, so the cheapest correct form is "after applying a render, re-walk
bound controls under the applied region and rebind". The re-walk must not
stack: rebinding an element tears down (or reuses) its previous effect and
any `@c-poll` interval before installing new ones, so a control that has
lived through three parent renders holds one binding and one timer, not
three. Two more spec points for that rebind. First, **value application
must skip the focused control**: an Alpine `effect()` runs on
registration, so the rebind writes `$state`'s current (reset) value into
the control the moment it re-registers, and without the skip the rebind
itself clobbers the S1 draft under the user's cursor; this mirrors the
post-patch re-apply rule, which touches unfocused controls only
(events.md:2077-2080). Second, this rebind requirement **corrects a WP17
plan assumption**: the plan's one-way bullet says "re-application after a
morph comes from reactivity alone, verify it"
(events_plan.md:1659-1661), which holds for a self-render (the State
object's identity survives the reconcile) but is false for nested
children under reset, where the old effect subscribed to a retired
anchor's State object that no future write will touch. A WP17 brief
written from the plan must carry that correction.

**Outcome, stress-tested.** The maintainer asked what the outcome would be
and where the edges are. The honest summary: the model is sound and simple,
and its failure cases are all of one family, **a child interaction racing a
parent render**. Walked concretely:

- **S1, user mid-keystroke in a child two-way input when a parent poll
  response lands.** The child root is patched in place; the input is the
  same DOM node; the focused-value protection (events.md:2116-2118) keeps
  the typed text and caret. But the fresh anchor's `$state` holds the
  parent-recomputed value and the pending queue is empty. What the user
  sees, step by step: the text stays under their cursor (looks fine);
  keystrokes typed **after** the reset re-queue the whole control value (a
  two-way write carries the full value, so continued typing self-heals);
  but if they pause, the draft is already gone from the model. If the
  pre-reset debounce timer survived the sweep and fires (machinery item
  2's fire-time-liveness option, assumed here; under teardown-at-sweep the
  flush never fires and the rest of this walkthrough is unchanged, minus
  the no-op round trip), the send carries **no update** (the queue was
  reset), the handler runs on the pre-draft State, and the child re-renders
  to the pre-draft value. The field then snaps to `$state`'s value at the
  next patch or reactive re-application after focus leaves (the re-apply
  rule runs after every patch and touches only unfocused controls,
  events.md:2077-2080; nothing fires on blur itself). The `.lazy` variant
  is the one that self-heals: no update event fires until the control
  commits, so the blur-time `change` queues and sends the whole draft
  instead of losing it. Net: **the default-modifier draft silently
  reverts** unless the user happens to keep typing. Nothing errors; the
  user just loses input.
- **S2, the unfocused variant.** User types in child input, tabs away
  (debounce pending), parent poll lands. The control is unfocused, so no
  DOM protection covers it, and **the typed text visibly reverts at the
  parent patch itself**: the post-patch re-application writes the fresh
  anchor's `$state` value, which is the parent-recomputed pre-draft value,
  into every unfocused bound control (the re-apply rule,
  events.md:2077-2080), and the WP17 rebind reaches the same end on its
  own, because a re-registered effect applies on registration. The pending
  debounce changes nothing: if its timer survived the sweep
  (fire-time-liveness), the flush resolves the element to the fresh anchor
  (correct class, fresh token), carries no update (the queue was reset),
  and its response merely re-renders the already-reverted value; under
  teardown-at-sweep there is no flush at all. This is the sharpest cell on
  option A's board because the loss is immediate, visible, and nothing
  errors anywhere.
- **S3, a child's save is in flight when the parent render lands.** The
  child anchor retires; the fresh anchor knows nothing of the call. When
  the save response arrives: its render and token refresh drop (retired
  anchor, policy 3); its `data` action still resolves the `await
  sendEvent(...)` promise, so imperative code continues correctly; a
  self-addressed `event` action targets the dead old id and finds no roots
  (delivery policy is a decision item below). The `$loading` counters lived
  on the dead anchor, so `$loading()` in the fresh fragment reads false
  **while the call is still in flight**, and the busy attribute was
  stripped by the morph. What the user sees: the spinner vanishes at the
  parent update; the save's confirmation render never lands; the child
  shows the parent's view of the world, which may predate the save, until
  the next poll or interaction. The save itself is durable server-side, so
  with polling this is eventual consistency with a stale window; without
  polling the stale child persists until the user acts again.
- **S4, two rapid child sends racing a parent render.** Both responses drop
  their renders (retired anchor); both promises resolve. The user's two
  clicks appear to do nothing visually. No corruption, no error surfaced.
- **S7, `$onEvent` subscriptions.** A subscription made in `$onComponent`
  heals itself: the deps manager tears down the old id and re-fires the new
  id, and the new payload's `onEvent` binds the fresh anchor. But a
  subscription made in an `x-init` expression does not: morph preserved the
  node and scope, so `x-init` never re-runs, and the captured anchor is
  retired (its `componentId` nulled), so the closure returns early forever
  (`subscribeForAnchor`, citry-events.ts:888). The runtime's own comment
  promises "the id
  changes with every render while the subscription lives on"
  (citry-events.ts:883-885); under reset that documented behavior silently
  breaks for nested children. Server `event` actions from later calls are
  fine (new subscriptions target the new id); toasts driven by an in-flight
  call's `event` action are lost with S3.

**The internal tension to weigh.** Morph exists to preserve continuity the
server did not send (focus, caret, scroll); the anchor exists to preserve
continuity the wire does not carry ($state identity, pending writes,
epoch). Option A keeps the first and resets the second, so the DOM can show
state (the protected focused value) that `$state` disagrees with. The
golden rule justifies resetting **server-derived** state; it says nothing
about discarding the **user's unsent input**, which is client property the
server never saw. That is the precise place where the coherence argument
for the lean stops covering, and it is exactly the S1/S2 family.

**When A alone is acceptable.** If v1 content (demos, the dogfood port)
never places two-way-bound or send-heavy children under a re-rendering
parent (no poll-over-form patterns), the S1-S4 family stays theoretical,
and A's simplicity wins outright. The moment a dashboard polls a parent
region containing an editable child, A alone produces silent input loss in
a first-class v1 feature combination (`@c-poll` is WP17 scope).

## Option B: positional matching

**The rule.** During a parent render, match old child anchors to fresh ids
by position: same class at the same structural position under the parent
means the same anchor (link and reconcile per the three-way split's
same-class branch); unmatched old ids retire; unmatched new ids mint fresh
anchors.

**Mechanics.** Two implementable variants:

- **Ride the morph's own pairing.** Morph already decides which old element
  each incoming element continues (tag plus the plain `key` attribute,
  events.md:2107-2110). In the `updating(el, toEl)` hook, when both carry
  instance markers and the ids differ, link the old id's anchor to the new
  id right there, before the child's own subtree is patched (staged
  metadata for the new id comes from the pre-parsed manifest, machinery
  item 1). Anchor pairing then agrees with DOM pairing **by construction**:
  the anchor follows whatever node morph decided is "the same" position.
  Wholesale swaps (different tag) bypass `updating`; the spike's `added`
  hook path covers them.
- **An independent rank matcher** (same class, n-th occurrence in document
  order under the applied region), needed anyway for non-morph swaps
  (`replace`, `inner`, ...), where no pairing hooks exist.

**Wire impact.** None; entirely client-internal.

**Where it breaks.** Positional identity is guessed identity, and the two
failure directions are not symmetric:

- When morph mis-pairs an unkeyed reordered list (the documented `c-key`
  gotcha, "**Keys are user-authored**", events.md:2154-2161), the
  DOM-level damage is cosmetic (focus
  sticks to a position). Under option B the anchor damage is **not**
  cosmetic: the anchor at position 2 carried item B's pending draft and now
  holds item C's token; the next flush sends **B's draft into C's State**.
  Silent cross-entity data corruption, server-side, of exactly the kind the
  design's security posture exists to avoid. Data loss (option A) is
  strictly less bad than data misattribution.
- The morph-pairing variant only exists under `swap: morph`. A client whose
  cached runtime does not advertise `morph` receives `replace`
  (events.md:1391-1402) and silently gets reset semantics, so continuity
  becomes capability-dependent unless the rank matcher is also built, which
  is a second matcher to keep consistent.

React is the honest precedent here: its default reconciliation is exactly
this (same type, same position keeps state), and the well-known unkeyed-list
state-bleed bugs are why keys exist. Adopting B as a default imports that
bug class into a framework whose pending writes get **sent to the server**,
which raises the stakes above React's client-only state.

**Verdict.** Reject as a default. The machinery (in-hook linking, staged
metadata) is worth building only if it is driven by author-asserted
identity, which is option C.

## Option C: explicit keyed linking (`c-key` as opt-in continuity)

**The rule.** Link only where the author asserted identity: an old child
anchor and a fresh id link iff their root elements carry the **same class
and the same `key` value** within the applied region. Keyed matches
reconcile (the same-class branch of the three-way split: `$state` identity,
pending writes, epoch pair, `$loading`, subscriptions all survive; server
wins per field except pending unsent writes). Everything unkeyed or
unmatched behaves exactly as option A. This is one policy, not two: A is
the base lifecycle, and a key is the author's instruction to carry the
anchor across.

**Mechanics.** Swap-agnostic and morph-independent: before the swap, collect
`(classId, key)` for the instance roots currently under the target region;
from the pre-parsed fragment, collect `(classId, key)` for incoming instance
roots; link the intersection; the swap runs with links already in place
(link-before-morph holds); the sweep retires the rest. Because it does not
depend on morph's hooks, the same semantics hold under `replace` (the DOM
state dies with the node, but the anchor payload, crucially the pending
writes and token lineage, carries to the replacement). Duplicate keys within
one region: match in document order and log a debug warning (same spirit as
the zero-match warning). Grandchildren recurse naturally: matching is scoped
per applied region, and a linked child's own subtree is itself a region in
which its keyed grandchildren match.

**The horizon cut (the linking-only sub-rule).** When a parent render links
a child anchor, set the child's highest-applied epoch to its send counter.
Effect: instance-mutating actions of every in-flight child call drop when
their responses arrive (their `data` still resolves; document-level actions
still apply). Rationale: the parent render replaced the child's token with a
parent-derived one; a late child response carries a render and token from
the pre-parent lineage, and applying them would resurrect pre-parent State
for the child's next send, silently discarding the parent's recompute, the
client-side analogue of violating the golden rule. The cut makes linked
children agree with option A about in-flight renders (dropped) while
preserving everything else. The alternative (let the late child render
apply, last-writer-wins) is listed as a decision below but not recommended.

**What C buys, per scenario.** S1/S2: the draft, queue, caret, and reactive
identity survive; the debounce flush carries the draft with the new token;
nothing reverts. S3: the spinner persists (`$loading` counters carried) and
the runtime can re-stamp busy attributes; the in-flight render still drops
(horizon cut), but the self-addressed `event` action can be routed through
the anchor to its current roots, so toasts arrive. S7: `x-init`
subscriptions keep firing (the closure reads the anchor's current id).
S5-reordered lists: keyed children follow their items, drafts included, and
within one same-class sibling list (exactly the S5 shape) DOM pairing
agrees, because morph pairs those siblings by the same `key` attribute the
matcher reads. That agreement is scoped, not universal: morph pairs by tag
plus key among siblings at one level (events.md:2106-2110), the anchor
matcher by class plus key region-wide, and the two can diverge. A keyed
child that moves between sibling groups links its anchor while morph
declines the DOM pair, so the payload carries and the DOM state dies (the
same outcome as a keyed match under `replace`, S10); the same tag and key
on two different component classes can make morph pair roots the matcher
refuses, which falls to reset. The document-order rule for duplicate keys
covers the remaining ambiguity.

**Costs and the one open mechanic.**

- Matching machinery: modest (two `(class, key)` maps per applied render
  plus the link call that already exists, `linkRenderedInstance`,
  citry-events.ts:583-621).
- **Key emission is the genuinely unpriced piece.** The morph key and the
  anchor key must sit **on the child instance's root element** in emitted
  HTML. Today `c-key="expr"` works on plain HTML elements (the inline
  dynamic-attribute split, compiler.rs:365-401); written on a component
  tag (`<c-TodoItem c-key="item.id" />`) it instead compiles to a component
  input (an `ExprHtmlAttr` that `_resolve_kwargs` hands the child as a
  `key` kwarg), which a child declaring `Kwargs` rejects with a render-time
  `TypeError` (`cls.Kwargs(**raw_kwargs)`, component.py:474) and only an
  untyped child silently absorbs. Either way nothing
  reaches the child's rendered roots, and multi-root children need a
  defined stance (first root, or all roots). The workaround that works
  today, keying a wrapper element around the child, gives morph its
  pairing but leaves the instance
  root itself unkeyed, so the anchor matcher would need a
  "nearest-keyed-ancestor" rule with its own ambiguity (two instances under
  one keyed wrapper). Clean version: component-tag `c-key` forwards to the
  root marker elements at serialize time. The forwarding is not purely
  serializer-side: the key must be intercepted in the nodes layer before
  the child's `Kwargs` construction rejects it (in or before
  `_resolve_kwargs`, citry/nodes/__init__.py:779-821) and carried to the
  serializer. Whether that lands as a contained serializer-plus-nodes
  change or touches the compiler contract must be priced before
  C is scheduled; it is server-side rendering work, **not** a wire change.
  The render error also means there is no existing-behavior compatibility
  burden: no working template uses component-tag `c-key` on a typed child
  today.
- Docs cost is one sentence, and it unifies with an existing one: the
  guidance "add `c-key` to `<c-for>` items whose list can reorder"
  (in "**Keys are user-authored**", events.md:2159-2161) extends to "and
  to interactive children that must
  keep unsent input or in-flight UI across a parent update".

**Wire impact.** None on `citry-events/1`: the envelope, actions, and
targets are untouched; the key rides the rendered HTML like any attribute.

## Option D: Livewire-style islands (parent morph skips child subtrees)

**The rule.** The parent's morph never descends into a nested instance's
subtree: the `updating` hook calls `skip()` on child instance roots, so the
child's DOM, anchor, and everything else stay untouched; children change
only through their own calls.

**Why it fails here.** The design already litigated and rejected this,
with the mechanism spelled out: Livewire's skip works because its **server**
does not re-render children at all (it emits a keyed placeholder stub), and
the price is that parent-to-child props go stale unless explicitly marked
reactive; citry deliberately re-renders the whole subtree so props flow
naturally ("**a parent's morph does not skip nested instance roots**",
events.md:2170-2182). Bolting the skip onto citry's client while
the server still renders full children gives the worst of both: the server
does the child render work and the client throws it away; the fragment's
manifest names fresh child ids that never enter the DOM (registry-DOM
divergence: anchors minted for ids with no elements, old ids alive with no
manifest); parent renders can no longer reorder, add, or remove **unkeyed**
children coherently (an unkeyed reordered list under skipped children
simply does not reorder; keyed islands do move as whole units under
morph's tag-plus-key pairing, which is exactly how Livewire manages lists
of islands with `wire:key`, so the rejection's weight rests on the stale
props and the wasted render, not on reordering); and every child's props
freeze at first render, the exact
Livewire disease the design declined. Doing islands honestly requires the
server to emit child stubs, which changes the render-action HTML contract
and the rendering model, a design reversal rather than a client policy.
The JSON envelope would technically be unchanged, but the fragment contract
(what a `render` action's `html` contains) would not be.

**Verdict.** Reject. Included because the maintainer named it; the rejection
is grounded in the already-landed 5.3 decision, not re-argued from scratch.

## The scenario matrix

Rows are the concrete scenarios; cells say **what the user sees**. "C" cells
describe keyed children; unkeyed children under C behave as column A. The
walkthrough details live in the option sections above.

| # | Scenario | A: reset (the lean) | B: positional link | C: keyed link | D: islands |
|---|---|---|---|---|---|
| S1 | Typing in a child two-way input, focused, when a parent poll response lands | Text stays under the cursor (morph protects it), but the draft was silently dropped from the model: a flush before the next keystroke sends nothing, and the field snaps back at the next patch after focus leaves | Survives at a stable position; at a shifted position the draft lands in a different entity's field | Survives; flush carries the draft with the new token | Survives; but the child ignores the parent's new props |
| S2 | Draft typed, user tabbed away, debounce fires after the parent render | Typed text visibly reverts at the parent patch itself (the post-patch re-apply writes the reset `$state` into the unfocused control); a surviving flush merely confirms it; no error anywhere | Survives or misattributes, by position | Survives correctly | Survives |
| S3 | Child save in flight; parent render lands; save response arrives after | Spinner vanishes early; confirmation render never appears; child may show pre-save data until the next update; the awaited promise still resolves | As C when the link is right; misattributed spinner/error boxes when wrong | Spinner persists to settle; render still dropped (horizon cut); toast-style event actions deliverable; promise resolves | Save response applies normally; child correct, parent-provided context stale |
| S4 | Two rapid child sends race a parent render; responses arrive late, out of order | Both renders dropped; clicks look like no-ops; promises resolve | Same as C when linked | Both renders dropped by the cut; loading counts stay truthful | Both apply under the child's own epoch guard, as designed |
| S5 | Parent render reorders an unkeyed same-class child list | All drafts and child UI state reset; focus-follows-position artifacts (the documented DOM `c-key` gotcha) but no misattribution | Drafts follow positions, not items: one item's unsent text can be sent into another item's State (silent corruption) | Unkeyed: as A. Keyed: DOM and anchors both follow the item; drafts included | The reorder never appears on screen (children not moved) |
| S6 | Parent render changes child count, or a different class appears at a position | Correct by construction (fresh and retired) | Rank shifts can mislink same-class siblings; class mismatch falls back to reset | Keyed survivors link even as siblings appear/vanish; the rest resets | Additions render; retained children keep stale props |
| S7 | `$onEvent` made in `x-init`; a later server event targets the child | Subscription silently dead after any parent render (node survived, anchor retired); `$onComponent`-made subscriptions self-heal via re-fire | Alive when linked | Alive | Alive |
| S8 | Handler renders into a selector whose region contains the caller | Caller's anchor retires with its id; the awaited `data` still resolves; region shows exactly what the handler returned | Same, plus possible accidental links inside the region | Same as A unless keyed instances inside the fragment match keyed predecessors | Skip rules ambiguous (the caller is inside the skipped set) |
| S9 | Render target selector matches nothing / several elements | Nothing applied plus the zero-match warning / the same fragment (same instance id) lands N times: one anchor with N root sets sharing `$state`; degenerate under every option, warn | same | same | same |
| S10 | Same parent render arrives with `swap: replace` (capability downgrade) | Identical semantics to morph (uniform); DOM state dies with the node | Morph-pairing variant silently degrades to reset; behavior becomes capability-dependent | Same linking semantics as morph (key match is swap-agnostic); anchor payload survives, DOM state does not | Impossible under replace (no hooks); architecture becomes capability-dependent |
| S11 | Child save response and parent poll response race (both orders) | Whichever paints last wins; a stale parent fragment can visually undo a save until the next update. Option-independent (see "Machinery"); only D avoids the collision by never painting children from the parent | same | same | avoided, at the stale-props price |
| S12 | Grandchildren under a grandparent render | Recursive reset | Recursive, compounding rank fragility | Recursive per region; keys scope naturally | Grandchildren never reached |

## Ecosystem prior art (where it genuinely maps)

**Livewire (islands plus `wire:key`).** Livewire's nested components are
server-side islands: a parent re-render emits only a stub for each child,
the client morph skips the child's DOM, and children update solely through
their own requests; the documented consequences are stale parent-to-child
props (opt-in `#[Reactive]` to fix) and a hard requirement to put `wire:key`
on nested components in loops, whose omission, their docs warn, produces
hard-to-diagnose DOM-diffing misbehavior (exactly the S5 misattribution
family). Citry already chose the opposite server model (re-render the
whole subtree, "**a parent's morph does not skip nested instance
roots**", events.md:2170-2182), which is why option D transplants
badly; but Livewire's `wire:key` requirement is
direct evidence that author-asserted identity is the ecosystem's answer once
nested stateful children and list churn coexist.

**Phoenix LiveView (stateful components and streams).** LiveView's stateful
child components are addressed by a **developer-supplied `:id`**; on a
parent re-render the diff matches children by that id, and a child whose id
persists keeps its server-side state and its DOM, while a new id mounts
fresh. That is option C's philosophy made mandatory: continuity exists only
where the author named an identity, and there is no positional guessing at
all. LiveView can also afford to keep truth server-side (stateful processes,
no signed-token lineage), which is why it never faces citry's
late-response-from-an-old-lineage problem; the horizon cut is citry's
substitute for a server that remembers.

**HTMX (out-of-band swaps).** htmx's OOB swaps target author-owned element
ids, all matches, and its client keeps essentially no per-region state
beyond the DOM, so "continuity" reduces to morphing libraries' element
pairing; the lesson that transfers is narrow but real: id/target-based
addressing with an explicit zero-match behavior (citry already adopted the
all-matches rule and the warning, events.md:1512-1524), and no attempt to
guess identity the markup did not declare.

**React (keys).** React's default reconciliation is positional (same
component type at the same position keeps state), keys override it, and a
**changed key deliberately resets state**. Option B is React's default;
option A is React's changed-key behavior applied unconditionally; option C
is React's keyed path. React's decade of unkeyed-list state-bleed bugs is
the strongest available evidence against B as a default, and React's "key
change means fresh component" is a precedent that reset semantics are
teachable and predictable when they are the documented rule.

## Wire-protocol impact, stated explicitly

The goal (client-internal resolution, nothing new on the wire) is met by
three of the four options:

- **A (reset):** no wire change. The envelope, epoch field, actions, and
  targets are untouched; epochs simply start at zero on fresh anchors, and
  the epoch stays an opaque echoed field.
- **B (positional):** no wire change.
- **C (keyed):** no change to `citry-events/1`. The key rides the rendered
  HTML as a plain attribute (the same one morph already reads). It does
  require server-side **rendering** work (forwarding a component-tag
  `c-key` onto root marker elements, intercepted in the nodes layer before
  the child's `Kwargs` sees it), which is serializer-plus-nodes scope, not
  protocol scope.
- **D (islands):** the JSON envelope is unchanged, but doing islands
  correctly requires the server to emit child stubs inside `render`
  actions' HTML, which changes the fragment contract and the server
  rendering model. It cannot honestly be called client-internal.

## Recommendation

**Adopt option A as the baseline lifecycle for every uncorrelated instance
id, and adopt option C as the only linking mechanism, gated on pricing the
key-emission mechanic.** Concretely:

1. Build the shared machinery (pre-registration before the swap, the
   retirement sweep, the retired-anchor response policy, the
   apply-iff-greater guard) into WP16 now; it is required in every world.
2. Make reset the documented default: uncorrelated means fresh, exactly the
   maintainer's lean, uniform across swap kinds, selector targets, host
   inserts, and v2 push.
3. Price the `c-key`-to-root-marker forwarding (serializer plus the
   nodes-layer interception, decision 3). If it is
   the expected small change, ship keyed linking (with the horizon cut) in
   the WP16/17 wave and add the one-line docs guidance; if it is
   expensive, ship pure A for v1 with the S1/S2 family recorded as a known
   limitation and keyed linking as the designed fast-follow.
4. Do not build positional linking (B) or islands (D). If community demand
   later shows unkeyed continuity is wanted, B's morph-pairing variant
   layers cleanly behind the same linking machinery C introduces, with the
   corruption trade-off re-argued then.

Why this shape: A is the only option that is safe with zero author input
(loss, never misattribution), matches the golden rule and the landed code,
and keeps one lifecycle for every uncorrelated arrival. Its genuine failure
family (a child interaction racing a parent render: S1-S4, S7) is exactly
the set an author-asserted key fixes, the fix is the same concept the
design already teaches for list identity, and the ecosystem (Livewire,
LiveView, React) converged on author-asserted identity for this precise
problem. B is rejected as a default because sending one entity's unsent
input into another entity's State is the only outcome on the board worse
than losing input. D is rejected because it reverses a landed design
decision and reintroduces the stale-props disease citry's server model
exists to avoid.

**Falsifiers** (what would prove this recommendation wrong):

- If the dogfood port and the v1 demos show **no** interactive children
  under re-rendering parents (no poll-over-editable-child patterns), the
  urgency of C is falsified: pure A suffices for v1 and C waits for demand.
- If key forwarding onto child root markers turns out to need compiler or
  core-serialization changes rather than the contained
  serializer-plus-nodes change priced in decision 3,
  C's "modest cost" claim is falsified; re-price against shipping pure A
  plus documentation.
- If a WP16 prototype shows the e2e-visible S2 revert (typed text
  reverting at the parent poll's patch) reproduces in a realistic demo
  page,
  "ship pure A and document it" is falsified as a v1-quality answer, and C
  (or delaying `@c-poll`) becomes the requirement.
- If WP17's rebind-everything-after-every-parent-render cost under A proves
  heavier in practice than maintaining the linking machinery, A's
  simplicity advantage is falsified and C's default-on case strengthens.
- If the horizon cut proves wrong in practice (users report "my save's UI
  never showed" more than they would tolerate "my save's UI showed stale
  parent data"), the drop-vs-apply choice for late linked responses should
  be revisited; both are client-internal and reversible.

## Decisions the maintainer must still make

1. **Confirm reset as the default** for every uncorrelated id (this
   document's framing extends the 16.1 bullet's parent-morph case to
   selector-targeted fragments, caller-inside-target, and v2 push; confirm
   that generalization too, or name exceptions).
2. **C's timing**: in the WP16/17 wave or a fast-follow, after pricing the
   key-emission mechanic.
3. **Key emission mechanics** (only if C proceeds): component-tag `c-key`
   forwarding to root markers, priced across all three layers it can
   touch: the nodes-layer interception (pull `key` out in or before
   `_resolve_kwargs`, citry/nodes/__init__.py:779-821, before
   `cls.Kwargs(**raw_kwargs)`, component.py:474, rejects it with a
   `TypeError` on typed children), the serializer emission onto the root
   markers, and any compiler-contract change; the multi-root stance (key
   all roots or first root); duplicate-key handling (recommend:
   document-order match plus a debug warning). One upside the render
   error grants: forwarding carries no existing-behavior compatibility
   burden, because component-tag `c-key` on a typed child fails today.
4. **The horizon cut** for linked children (recommend: cut, i.e. drop
   in-flight instance-mutating actions at link time), versus
   last-writer-wins.
5. **Retired-anchor response details**: `data` resolves (recommended),
   instance-mutating actions drop with a debug log; and what a
   self-addressed `event` action does when its target id is dead (recommend:
   drop with a debug log; never fall back to a document dispatch, which
   would change delivery semantics silently). The same policy governs
   ordering inside one result: actions apply in list order
   (events.md:1527-1532), so an earlier action can retire a later action's
   target within the same response. A handler returning
   `[Render(X, target="#panel"), self-render]` where `#panel` contains the
   caller is the concrete shape: action 1 resets the caller's anchor, so
   action 2's self-render drops and the handler's intended self-update
   silently vanishes. For that drop to be the path actually taken, the
   applier must check target and anchor liveness per action, or run the
   retirement check synchronously with each swap: machinery item 2's
   sweep runs after the swap settles, and its citry.js precedent
   coalesces on a microtask (`scheduleSweep`, citry.js:266-274), so under
   a deferred sweep action 2 applies before any retirement and instead
   finds zero `cid:`-target elements, the zero-match path rather than
   this policy. Both code paths must end in the same drop plus debug log.
   The inter-result sibling exists from day one too: `calls` arrays carry
   one to sixteen entries (events.md:1404-1408), so within one batch
   envelope an earlier result's render can retire a later result's
   caller; the same drop-plus-debug-log applies across results in one
   envelope. Recommend the same drop-plus-debug-log, plus an
   encode-time dispatcher warning when a self-addressed action follows a
   selector-targeted render (which may contain the caller), the same
   spirit as the after-redirect warning (events.md:1533-1536).
6. **Busy re-stamp policy** after swaps: none under reset; under linking,
   re-stamp roots while `loading.any > 0` and triggering elements that
   survived the patch.
7. **Multi-match selector targets carrying instances** (S9): keep the
   degenerate one-anchor-many-roots behavior with a debug warning, or
   define it away in docs ("do not render instance-bearing fragments into
   multi-match selectors").
8. **`data-citry-morph="ignore"` on instance roots**: the skip leaves the
   old id in the DOM while the manifest introduces a fresh id that never
   lands (registry-DOM divergence). Recommend documenting the marker as
   unsupported on instance roots and logging when detected.
9. **Docs guidance wording**: whether the `c-key` line in 5.3 grows the
   continuity clause now (even under pure A, the sentence sets the right
   author expectation for a later C).
10. **Where the resolution lands**: 16.1's bullet should be moved to 16.2
    (resolved record) once decided, with events.md 5.5 gaining the
    uncorrelated-id lifecycle as normative text WP16 can cite.
