# Analysis: renders addressed to a different element (`target="#other"`)

Input to a decision, not a decision. Prepared 2026-07-14 for the open item
in [`../events.md`](../events.md) 16.1 ("A render addressed to a different
element", `events.md:3764-3770`) and the matching deferred item in
[`spike-component-identity.md`](../alpinejs/spike-component-identity.md)
(`spike-component-identity.md:504-509`). The item gates WP16/WP17, the
client transport and bindings work packages
([`../events_plan.md`](../events_plan.md) `events_plan.md:8-10`,
`events_plan.md:1527-1678`): the actions applier cannot be written until it
is decided which anchor's epoch guards a targeted render and what happens
to the target region's client-side state.

Terms used throughout, defined once. The **anchor** is the events
runtime's stable, client-internal identity for one interactive DOM
position; the reactive `$state`, the Alpine scope, the pending unsent
writes, the state token, and the epoch all hang off it (`events.md:2254-2268`).
The **epoch** is a per-anchor counter that detects out-of-order responses
(`events.md:1427-1443`). The **correlation id** is the envelope `id` a
response echoes; it routes the response back to the caller's anchor. A
**targeted render** is a `render` action whose `target` names something
other than the calling instance
(`actions.Render(element, target="#sidebar")`, `events.md:990`). The
**events manifest** is the inert JSON script tag riding every fragment,
listing the fragment's interactive instances and their tokens
(`events.md:1583-1586`). **Morph** is the DOM-patching call
(`Alpine.morph`) that applies new HTML as a minimal diff
(`events.md:2094-2126`).

## Prior art (what was searched and read)

- [`/CLAUDE.md`](../../../CLAUDE.md) in full (operating rules, house style).
- [`../events.md`](../events.md): section 2 demo 3 (the cart-badge
  targeted render, `events.md:122-154`); 3.4 (the actions vocabulary,
  `Render`'s `target` parameter and the unit-of-replacement rule,
  `events.md:974-1092`); 4.2 (call envelope, the `instance` field and the
  epoch bullet with its exact drop rule, `events.md:1367-1442`); 4.3
  (result envelope, the action table, target resolution incl. the
  all-matches rule, zero-match warning, `cid:` prefix, swaps, faithful
  ordering, timing fields, `events.md:1453-1581`); 5.2 (`sendEvent`
  promise contract, `Citry.events` surface, lifecycle events,
  `events.md:1880-2050`); 5.3 (morph rules, link-before-morph, `c-key`,
  pairwise multi-root, the parent-morph-does-not-skip-children contrast
  with Livewire, `events.md:2052-2200`); 5.5 (two identities, the anchor
  registry and index, magics resolution, the reconcile rule, the
  three-way split, `events.md:2242-2505`); 7.5 (the golden rule: a
  handler's returned tree is authoritative and shares nothing,
  `events.md:2959-3002`); 8 (server push, push-to-refresh,
  `events.md:3034-3058`); 14.1.12 (the actions round: CSS-default
  targets, `events.md:3517-3542`); 14.1.14 (the fills guard removal,
  `events.md:3559-3572`); 16.1 in full, this item and its neighbors
  (`events.md:3687-3801`).
- [`spike-component-identity.md`](../alpinejs/spike-component-identity.md) in full:
  the anchor lifecycle (created / updated / destroyed,
  `spike-component-identity.md:326-345`), the link-before-morph ordering
  requirement (F-CI-2, `spike-component-identity.md:347-354`), epoch per
  anchor (`spike-component-identity.md:390-401`), the `$state` inert
  fallback (`spike-component-identity.md:431-439`), the removal
  reconciler (F-CI-5, `spike-component-identity.md:457-468`), findings
  F-CI-1 through F-CI-6 (`spike-component-identity.md:519-541`), and the
  deferred item this analysis answers
  (`spike-component-identity.md:504-509`).
- The landed client runtime:
  [`packages/js/citry-client/src/citry-events.ts`](../../../packages/js/citry-client/src/citry-events.ts)
  (the TypeScript file is what exists as of this reading; there is no
  `.js` sibling in `src/`). The file is untracked and a parallel stream
  is actively editing it, so the symbol names are the stable pointer;
  the line numbers are from the 2026-07-15 late-morning read of the
  1197-line file. The same volatility caveat applies to every line-cited
  source in this document: `events.md` and `events_plan.md` are modified
  in the working tree, and the sibling nested-instances analysis is
  untracked and was revised repeatedly while this document was being
  written (its numbers here are from the 2026-07-15 10:37 read of the
  867-line file), so every load-bearing pointer below is paired with a
  section heading, a symbol name, or a quoted sentence; when a number
  has drifted, resolve by that anchor.
  Load-bearing internals cited below by line:
  the `Anchor` shape (`citry-events.ts:142-156`), `createAnchor`
  (`citry-events.ts:532-558`), `linkRenderedInstance` with the three-way
  split (`citry-events.ts:583-621`), `finishRender`
  (`citry-events.ts:625-628`), `applyEventsManifest`'s
  known-id-versus-new-id branches (`citry-events.ts:670-682`),
  `resolveAnchor` and the inert `$state` (`citry-events.ts:726-761`),
  `sendFromAnchor` (`citry-events.ts:804-868`), `subscribeForAnchor`
  (`citry-events.ts:886-897`), `Citry.events.send` target resolution
  (`citry-events.ts:1026-1060`), and the events-manifest observer
  (`citry-events.ts:1124-1133`).
- The dependency manager the anchors ride:
  [`packages/py/citry/citry/ext/dependencies/client/citry.js`](../../../packages/py/citry/citry/ext/dependencies/client/citry.js):
  `liveInstances` (`citry.js:74-80`), the removal sweep
  (`citry.js:254-274`), the deferred Component.css collection
  (`citry.js:241-248`), the attribute-watching observer
  (`citry.js:393-409`), and the open TODO about the same fragment
  inserted into several places (`citry.js:304-305`).
- [`../events_plan.md`](../events_plan.md) WP16 and WP17 in full
  (`events_plan.md:1527-1678`), plus the status header naming this item
  as the gate (`events_plan.md:3-11`).
- [`recon-ecosystem.md`](recon-ecosystem.md) pattern 2c (Turbo Streams,
  htmx out-of-band swaps, Datastar; `recon-ecosystem.md:158-185`) and
  pattern 2b (LiveView diffs, `recon-ecosystem.md:143-156`).
- The sibling analysis of the neighboring 16.1 bullet (nested-instance
  anchor continuity, `events.md:3754-3763`),
  [`analysis-nested-anchor-continuity.md`](analysis-nested-anchor-continuity.md),
  landed from a parallel stream while this document was being written;
  its recommendation is reset as the default for every uncorrelated
  instance id, plus author-keyed linking (its option C) adopted "as the
  only linking mechanism, gated on pricing the key-emission mechanic",
  shipping in the WP16/17 wave if that price is small (its
  "Recommendation" section,
  `analysis-nested-anchor-continuity.md:743-764`). Where this document
  says "the nested-instances lean" it means the shared baseline: a
  parent's re-render resets nested client state (children mint fresh
  anchors). On when keyed continuity ships the two documents diverge;
  the harmonization section states the divergence and decision 10 hands
  it to the maintainer.

## The problem, precisely

A handler can return
`actions.Render(CartBadge(count=3), target="#cart-badge")`. The response
travels back correlated to the **caller's** anchor (the envelope `id`
routes it there, `events.md:2063-2067`), but the DOM change lands on a
**different** region, one the caller does not own. The anchor model is
proven only for self-renders, where the correlation id and the target
agree (`spike-component-identity.md:504-506`). Two questions are open
(`events.md:3764-3770`):

1. **Which anchor's epoch guards the apply?** The caller's epoch says
   "has a newer call from this caller already landed?", which is not the
   same question as "is this region's content newer than what it shows?".
2. **What happens to the target region's anchor(s)?** The region may
   contain interactive instances with live `$state`, pending writes,
   in-flight calls, and subscriptions. Does the incoming render update
   them in place (some reconcile), or replace them outright?

The maintainer's lean, analyzed here as option A: treat the targeted
region as **removed and replaced**. Instances inside the old target
region retire together with their anchors; fresh manifest entries in the
incoming fragment mint fresh anchors; no epoch guard ties the apply to
the target's past.

## What is already normative (facts every option inherits)

These are decided elsewhere and none of the options below reopens them.

- **Target resolution is decided.** A plain-string target is a CSS
  selector applying to **all matches** via `querySelectorAll`; a selector
  matching nothing logs a zero-match warning instead of silently doing
  nothing; `cid:<instance id>` is the reserved instance-targeted form the
  runtime itself uses for self-renders (`events.md:1512-1524`, ratified
  in 14.1.12, `events.md:3527-3529`). So "error versus debug no-op" and
  "first, all, or error" are already answered: warn-and-continue, and
  all matches. What is open is only what those swaps do to anchors.
- **A render's HTML is a complete citry fragment** carrying its own
  `data-citry` and `data-citry-events` manifest tags, so insertion reuses
  the existing observer machinery with zero new mechanics
  (`events.md:1505`).
- **Faithful ordering.** Actions apply strictly in list order; the
  runtime never reorders or drops them, and caveats are documented
  instead (`events.md:1526-1538`). This matters for the
  target-contains-the-caller case: the author controls whether a
  `Dispatch` lands before or after the render that destroys its
  audience.
- **The epoch drop rule as written today, in two places that disagree.**
  4.2 says a stale response (echoed epoch lower than the anchor's
  highest applied) drops its **instance-mutating** actions, defined as
  the self-targeted render and the state token refresh; its `data` still
  resolves the caller's own promise, "and non-instance actions apply
  normally" (`events.md:1432-1436`). 5.2's lifecycle table reads
  broader: the `citry:events:stale` row says the runtime "drops its
  DOM-changing actions" (`events.md:1978`), a set that includes targeted
  renders. So on exactly the case this analysis decides, 4.2 reads as
  pure option A (a stale response's targeted renders apply) and 5.2
  reads as option B (they drop); the broad row is evidence the design
  already leaned toward B's semantics. Whichever rule is ratified, both
  sentences must end up saying it (decision 1 names both edits).
- **The golden rule.** The tree a handler renders shares no inputs and no
  fills with the target's original render; the handler's return is
  authoritative (`events.md:2988-2996`), and the fills guard that once
  made re-rendering a fills-receiving instance an error was deliberately
  removed (`events.md:3559-3572`). Targeted renders into slotted
  components are legitimate by design; leaf-components-into-explicit-
  targets is the documented pattern (`events.md:2968-2970`).
- **The landed runtime already mints anchors for uncorrelated ids.** When
  an events manifest names a component id with no anchor, the runtime
  creates a fresh anchor (initial page load, host-inserted fragment,
  server push); when it names an id that is already linked, it refreshes
  only the token, deliberately not clobbering values
  (`citry-events.ts:670-682`).
- **The landed runtime has no anchor-removal path except the plain-HTML
  branch.** `linkRenderedInstance`'s plain-HTML branch retires the
  caller's own anchor (`citry-events.ts:585-600`); nothing retires an
  anchor whose DOM left for any other reason. Anchors of instances
  removed by a parent's morph, a host script, or (once built) a targeted
  render currently stay in `anchors` / `idToAnchor` forever. Every option
  below needs some retirement mechanism; they differ in which one.
- **The dependency manager already handles the DOM half.** Its removal
  sweep runs an instance's cleanups when the instance's last
  `data-cid-<id>` element leaves the DOM, catching both real removals and
  morph's in-place attribute swap, debounced so remove-then-add churn in
  one batch is seen whole (`citry.js:254-274`, `citry.js:393-409`);
  Component.css collection is deferred and cancellable
  (`citry.js:241-248`). This layer is anchor-free by design
  (`spike-component-identity.md:457-468`) and needs no change under any
  option.
- **Mid-transition reads are already safe.** `$state` on a marker-bearing
  node whose id is momentarily unregistered resolves to an inert empty
  value, never a throw (`citry-events.ts:726-761`,
  `spike-component-identity.md:431-439`).

## The options

Three options are treated in full; a fourth, option D (server-declared
region identity), is dismissed briefly because it changes the wire.

### Option A: the targeted region is removed and replaced (the maintainer's lean)

**The rule.** A targeted render is, to the client state model, a region
teardown plus a fragment insert. Whatever interactive instances lived
inside the old target region retire with their anchors; the incoming
fragment's manifest mints fresh anchors for its instances; the DOM swap
itself uses whatever `swap` strategy the action names (morph included,
purely as a patching mechanism). No epoch comparison guards the apply,
because the target region has no surviving counter to compare against:
its past was retired with its anchors.

Self-continuity (the three-way split, reconcile / adopt / plain-HTML,
`events.md:2403-2421`) remains exclusively the property of the correlated
self-render path. Put as one sentence: **a region's client-side
continuity is owned by its own correlated self-renders alone; a render
arriving from anywhere else replaces the region's client state
wholesale.**

**Mechanics (enough to write the WP16 brief from).**

1. **Resolve targets**: `querySelectorAll` for selectors (all matches,
   zero-match warning), marker lookup for `cid:` targets. Already pinned
   (`events.md:1512-1524`, `events_plan.md:1582-1584`).
2. **Pre-enumerate the departing ids**: collect the `data-cid` ids on and
   under each matched element (the region about to be replaced). These
   are the anchors to retire.
3. **Mint before swap**: parse the action's `html` once (a detached
   template element), read its `data-citry-events` manifest, and mint
   anchors for its unknown ids **before** the DOM swap. This is the
   targeted-render sibling of the spike's link-before-morph requirement
   (F-CI-2, `spike-component-identity.md:347-354`): under `swap="morph"`
   the Alpine bridge evaluates the incoming fragment's bound expressions
   during the patch, and those reads resolve `$state` through the fresh
   component id. Minting first makes them resolve to real state instead
   of the inert fallback (which would leave bound text empty with nothing
   to re-trigger it, since inert reads track no reactive dependency).
   Three mechanics pinned here so the WP16 brief does not have to
   choose. **(a) The manifest is read twice, on purpose**: the applier
   reads the detached tag's JSON directly and does **not**
   push the tag through the processed-marking path
   (`processEventsManifestTag`, `citry-events.ts:689-691`), so the tag
   reaches the DOM unmarked; the observer then processes it post-swap,
   and that second
   pass is idempotent for a known id, refreshing only the token
   (`citry-events.ts:671-677`). (Marking the tag pre-swap would instead
   turn the observer pass into a skip and leave the Alpine scope attach
   riding the `interceptInit` self-heal alone,
   `citry-events.ts:369-388`.) **(b) The applier carries the manifest
   tags across a morph.** How the tags reach the DOM depends on the
   swap: `replace`/`inner`/`append`/`prepend` insert the whole fragment,
   manifest tags included, but the default `swap="morph"` consumes
   **only the fragment's first root** (`events.md:2162-2163`) and would
   silently discard the trailing `data-citry-events` and `data-citry`
   script tags. So under morph the applier itself inserts both tags,
   still unmarked, immediately after the patched root. That one rule
   keeps a single post-swap mechanism across every swap kind: the
   events observer runs its idempotent token pass, and the dependency
   manager sees the `data-citry` tag and loads assets and fires
   `$onComponent` for the new instance exactly as on any insert.
   Without it, the morph path never refreshes the token and the deps
   manager never learns the new instance exists (no assets, no
   `$onComponent`), silently failing the outcome the S1 row asserts.
   (The alternative,
   the applier owning manifest processing exclusively under morph and
   handing the `data-citry` tag to the deps manager by a call that does
   not exist today, forks the mechanism per swap kind; rejected.)
   **(c)** And boundary scopes attach post-swap
   either way: at mint time the fragment is not in the document, so the
   attach pass finds zero elements (`attachBoundaryScopes`,
   `citry-events.ts:646-651`); the
   observer's post-swap pass (with `interceptInit` covering a
   morph-driven init) is what attaches them.
4. **Swap** per the action's strategy. Morph pairs the target element
   against the fragment's first root by tag name and `key` (F-CI-1), so a
   same-tag pair patches in place (the old `data-cid-<old>` attribute
   swaps for the new one on the same node) and a different-tag pair
   replaces wholesale; after the patch the applier inserts the
   fragment's trailing manifest tags (step 3's tag carriage).
   `replace`/`inner`/`append`/`prepend`/`remove` are plain DOM
   operations whose insertions carry the manifest tags for free. The
   state model does not care which: that
   indifference is a simplification this option buys (see S8).
5. **Retire the departed anchors**: for each pre-enumerated id whose
   elements no longer exist in the DOM, run the same field-clearing the
   plain-HTML branch does today (`citry-events.ts:585-600`, factored so
   both paths share it): delete from `anchors` and `idToAnchor`, null the
   component id, class id, values, and proxy, clear pending. Instance JS
   cleanups are **not** the events runtime's job; the dependency
   manager's sweep runs them when the ids leave the DOM, exactly as it
   does for self-renders today (two layers, composing as proven in spike
   scenario 5).
6. **Backstop sweep**: additionally give the events runtime a debounced
   anchor sweep mirroring `citry.js`'s (`citry.js:254-274`): retire any
   anchor whose component id has no live element. This catches removals
   the applier never saw (a parent's morph discarding children, host JS
   clearing a container) and fixes the pre-existing leak noted above. The
   nested-instances lean needs the identical mechanism, which is part of
   the harmonization argument below. Implementation note: the mint (step
   3) and swap (step 4) happen synchronously in one applier step, and the
   sweep is task-debounced, so freshly minted anchors are never swept in
   the gap; this is the same whole-batch property the deps sweep already
   relies on (`citry.js:266-274`). One false positive, named so WP16's
   QA does not discover it cold: host JS that detaches an interactive
   region and re-inserts it later than the sweep's debounce window gets
   its anchors retired, and the re-insertion cannot re-mint them,
   because the fragment's manifest tag stays marked processed
   (`citry-events.ts:689-691`) and the boundary guard short-circuits
   the `interceptInit` drain; the region comes back permanently inert.
   Accepted for v1: the deps layer already leaves the same region torn
   down and never re-fired on the same move (its sweep ran the cleanups
   and dropped the `liveInstances` entry, and the re-inserted
   `data-citry` tag stays marked processed too, `citry.js:382-383`, so
   nothing calls `$onComponent` again), so the events layer's inertness
   adds no new contract breach; detach-and-reinsert across a task
   boundary is already outside the client contract. If real pages hit
   it, the mitigation is an
   unmark-on-retire (or an `interceptInit` re-mint path), not a sweep
   redesign.
7. **Fire `citry:events:swapped`** with the swapped-in roots, as for any
   render (`events.md:1977`).

**What it needs that is not yet built**: the applier itself (WP16 scope
anyway), the shared retire helper, and the anchor sweep. Nothing else in
the landed runtime changes; `createAnchor`-on-unknown-id is the landed
behavior doing the minting.

**New rule it forces about late responses.** Retiring an anchor while its
call is in flight creates a response class the design has not named: a
response whose correlation id resolves to a retired anchor. The
consistent answer (and the one option A recommends ratifying): treat it
like a stale response, drop the instance-mutating actions (there is no
instance left to mutate), still resolve `data`, still apply the
non-instance actions, log at debug. See scenario S4.

**Batch envelopes compose with the same rule.** `calls` carries one to
sixteen entries and `results[i]` answers `calls[i]`
(`events.md:1404-1408`, `events.md:1489`), so one envelope can mix a
self-render with a targeted render that retires a **sibling** call's
caller before that sibling's result is reached. The applier therefore
processes results in envelope order and re-checks anchor liveness per
action as it applies (recommendation 3; the per-result consequence
follows); the retired-anchor response rule applies within an envelope
exactly as across envelopes. v1 scoping: the v1 client sends one call
per envelope (`events.md:1404-1408`), and `Citry.events.applyActions`
applies one result's `actions` array, not a results envelope
(`events.md:1497-1499`, `events.md:1958`), so v2 batching is the only
producer of multi-result envelopes. The public entry point still earns
the rule its place now, for a different reason: actions can reach the
applier with no transport context at all, so the liveness re-check must
be stated as applier policy (checked where actions apply), never as
transport policy, which is why the rule is stated now rather than
rediscovered then.

### Option B: the caller's epoch guards all its targeted applies

**The rule.** Keep option A's anchor lifecycle (remove and replace), but
widen the epoch drop rule: when a response arrives whose echoed epoch is
lower than the **caller's** anchor's highest applied, drop **all** of its
`render` actions, targeted ones included (4.2's clause drops only the
self-targeted render and the state refresh, `events.md:1432-1436`).
`data` still resolves, `event`/`redirect`/`url` still apply.

This is not a target-side epoch. The comparison still happens on the
caller's counter; the target region still carries no past. The lean's
sentence "no epoch guard ties the apply to the target's past" stays true
under B; what changes is that the apply is tied to the **caller's** past.

**Mechanics**: one clause in the applier's stale-response branch (the
branch WP16 builds regardless). No new bookkeeping: the epoch and
highest-applied already live on the caller's anchor
(`citry-events.ts:539-544`), the response already routes there by
correlation id, and the epoch stays an opaque echoed wire field.

**What it fixes.** The same-caller, same-target race: a standalone
search box rendering into `#results`
(`@c-input="search"`, handler returns
`Render(Results(...), target="#results")`) is the shape htmx-trained
users reach for with `target=` (a judgment about likely usage, not an
audit datum: the audited LiveSearch is a self-render), and
rapid keystrokes with out-of-order responses would paint stale results
over newer ones. That is the exact shipped bug class in django-unicorn
and Livewire that the epoch guard exists to kill for self-renders
(`events.md:1436-1439`); pure option A would reintroduce it one
selector away from the guarded path. B is also less a new idea than a
ratification of half the existing text: 4.2's clause reads as pure A
while 5.2's stale row already promises that a stale response's
DOM-changing actions drop (the disagreement named under the normative
facts), so B aligns 4.2 with what 5.2 already tells users.

**What it breaks (the honest cost).** Per-caller staleness is the wrong
question for per-region freshness, in both directions:

- **Under-application**: a caller interleaves targets. Call 1 (epoch 1)
  renders `#sidebar`; call 2 (epoch 2) renders `#main`. Call 2's response
  lands first; call 1's response arrives stale and its `#sidebar` render
  is dropped even though nothing newer touched `#sidebar`. The sidebar
  silently misses one update (observable via `citry:events:stale`,
  `events.md:1978`).
- **No cross-caller protection**: two different product cards racing to
  `#cart-badge` have no shared counter under any per-anchor scheme; that
  race stays last-write-wins in arrival order exactly as in option A.

A "per-target highest applied" that answers the right question needs a
surviving per-region counter, which is exactly the anchor continuity that
remove-and-replace retires (that variant is option C's territory), or a
region-keyed side table (keyed by selector string or by DOM node, both of
which break under multi-match, morph node swaps, and selector aliasing:
two selectors can name one element). Not pursued.

A neighboring variant, considered and not pursued as a default: **abort
the caller's older in-flight call when it issues a newer one** (the
request-level answer htmx ships as `hx-sync`; see the ecosystem
section). It would close S3 by preventing the race instead of guarding
the apply, and it is set aside on three grounds. It breaks the promise
contract: every send resolves with the handler's `data`
(`events.md:1507`), and an aborted call rejects a caller that may be
awaiting a real result, where B's drop rule keeps `data` resolving. It
cancels nothing real: the server still runs the handler (the stance
`configure.timeout` already documents, "the server is not cancelled;
the client just stops waiting", `events.md:1965`), so aborting only
discards an answer already paid for. And it is exactly as blind to
cross-caller races as B. Nothing in B forecloses it: a transport-level
sync option (per send, or configured) composes cleanly later as an
additive client feature for callers that want request serialization
too.

### Option C: the target's anchor updates in place (three-way split against the target)

**The rule.** When the targeted element is (or contains, at its root) an
interactive instance, the incoming render **updates** that instance's
anchor instead of replacing it: resolve the target's innermost
`data-cid`, map it through the index to its anchor, run the same
three-way split a self-render runs (`linkRenderedInstance`,
`citry-events.ts:583-621`): same class reconciles (the anchor's `$state`
identity, pending writes, and epoch survive; server wins per field except
pending unsent local writes), a different class adopts the fresh token
wholesale, plain HTML retires. Then morph.

**Mechanics**: applier resolves target element to anchor; if found, run
`linkRenderedInstance(anchor, meta)` with meta parsed from the fragment,
morph, `finishRender`. If the target is not an instance root (a plain
wrapper div, or an element inside an instance), fall back to option A's
fragment-insert semantics, because there is no anchor to update.

**What it buys.** External refreshes of a live region become
non-destructive: a same-class targeted render onto a form region keeps
the user's pending `$state` writes, the focused control's value and
caret, and the `$loading`/`$error` boxes, exactly as a self-render would.
It also gives the target a surviving `highestApplied`, onto which a real
per-region ordering guard could be built later.

**Why it strains everything else.**

- **Two rules where A has one.** The behavior of a targeted render now
  depends on what the selector happens to hit: instance root (update in
  place), non-root or plain region (replace). The author targeting
  `#cart-badge` (a wrapper div) versus `.cart-badge-root` (the instance
  root) gets different state semantics for the same visual outcome.
- **The per-region epoch it enables is still not the response's epoch.**
  The echoed epoch is the caller's counter; comparing caller A's epoch 3
  against a `highestApplied` last written by caller B's epoch 7 is
  comparing two unrelated counters. A meaningful per-region guard needs a
  region-scoped logical clock that no current wire field carries, so C
  does not actually solve cross-caller ordering either; it only reserves
  a place where a future mechanism could live.
- **Multi-match degrades it to A's outcome, messily.** All-matches is
  normative. One fragment carries one instance id; linking N distinct
  anchors "in place" through one id re-points the index at each link,
  so the last-linked anchor wins (`citry-events.ts:617-620`) and every
  copy thereafter shares it, the same shared-anchor end state option A
  mints deliberately, except which predecessor's state survived into it
  is arbitrary and the losing anchors are left stranded. Making this
  principled forces either a first-match-only restriction for
  interactive fragments (contradicting the ratified all-matches rule)
  or anchor merging machinery.
- **It diverges from the nested-instances lean.** A parent's re-render
  resets a child wholesale, but a targeted render to that same child
  preserves it? Two adjacent "render arrived from elsewhere" cases with
  opposite continuity is exactly the two-rules incoherence the one-rule
  model avoids.
- **The demand is thin.** The production audit found targeted renders
  used for display regions (badges, counters); interactive regions with
  live form state update themselves through their own handlers (the
  LiveSearch pattern is a self-render, `events.md:702`). 7.5's guidance
  is leaf components into explicit targets (`events.md:2968-2970`).
- **It is the v2 question arriving early.** "When may an uncorrelated
  render attach to an existing anchor instead of minting a fresh one" is
  verbatim the open anchor-update question for server push, explicitly
  deferred to v2 (`events.md:3771-3777`). Deciding it now, for the rarest
  consumer, inverts the schedule.

### Option D, dismissed: server-declared region identity (wire change)

A server-stamped stable region key (say a `data-citry-region` attribute
or a per-region epoch minted server-side) would let the client adopt
regions in place and order applies correctly across callers. It is the
only shape that truly answers cross-caller ordering, and it is dismissed
for v1 because it adds wire-visible vocabulary (new manifest or action
fields), server bookkeeping, and a naming contract, for a race the
surveyed field leaves unguarded at apply time by default (htmx's opt-in
`hx-sync` serializes or aborts racing requests before they answer;
Turbo leans on render-current-truth; neither versions the apply; see
the ecosystem section). The
door stays open: it would arrive as additive fields behind `capabilities`
negotiation if a real consumer appears, the same door 4.3 keeps for new
action kinds (`events.md:1552-1558`).

## Edge-case walkthroughs

The scenarios, concrete and reused across all three options:

- **S1, the basic cross-region update**: a `ProductCard`'s `add` handler
  returns `Render(CartBadge(count=n), target="#cart-badge")` plus
  `Dispatch("cart:updated")` (the section 2 demo, `events.md:122-154`).
  `#cart-badge` is a page-level region holding a `CartBadge` instance.
- **S2, two calls race to the same target**: (a) same caller, a rapid
  double-click on one Add button; (b) different callers, two product
  cards clicked in quick succession. The network delivers the second
  response first in both.
- **S3, repeat-fire into a region**: a standalone search box,
  `@c-input="search"` (debounced 250 ms), handler renders results into
  `target="#results"`. The user types fast; response 1 arrives after
  response 2.
- **S4, the target contains the caller**: a toolbar button inside
  `#main` sends `rebuild`; the handler returns
  `[Dispatch("main:rebuilt"), Render(MainPane(...), target="#main"),
  {"ok": true}]`. A second call from the same button is still in flight
  when the render lands. (The dispatch is listed first deliberately; see
  the ordering fact above.)
- **S5, the target is inside another interactive instance**:
  `#badge` lives inside an interactive `ProfileCard` that polls
  (`@c-poll.30s="refresh"`). An unrelated handler renders
  `Badge(...)` into `#badge`; the user is also mid-typing (or
  mid-IME-composition) in a bound
  input inside `#badge` when that render lands; later the parent's poll
  fires.
- **S6, the selector matches nothing**: a typo (`#cart-bagde`), or the
  previous targeted render's fragment did not re-emit `id="cart-badge"`
  on its root, so the hook element no longer exists.
- **S7, the selector matches several elements**: `.cart-badge` matches
  the desktop and the mobile header badge; the fragment is interactive
  (declares Events).
- **S8, swap kinds against the same region**: the same targeted render
  applied with `swap="morph"` versus `"replace"` versus `"inner"`.
- **S9, epoch ordering across regions in one result**: a handler mutates
  state and returns a targeted render, so the result carries a `state`
  action for the caller plus a `render` for `#badge`; two such calls
  race and the older response arrives second.
- **S10, a delayed targeted render races a newer response**: the search
  box again, but the handler returns
  `Render(Results(...), target="#results", delay=2, wait=False)` (the
  timing fields every action accepts, `events.md:997-1000`,
  `events.md:1541-1551`; WP16 builds and tests them,
  `events_plan.md:1533`, `events_plan.md:1591-1592`,
  `events_plan.md:1620`). Response 1's render is still in its
  two-second window when the newer response 2 lands and paints.
- **S11, a send scheduled from inside the targeted region fires after
  the region is replaced**: the user is mid-typing in a bound input
  inside `#panel` (a debounce flush is pending, WP17's 250 ms default,
  `events_plan.md:1650-1651`), or the region polls
  (`@c-poll.30s="refresh"`, `events.md:3038`, WP17 scope,
  `events_plan.md:1662`), or host JS captured `$sendEvent` in a
  closure; an unrelated handler's render replaces `#panel` before the
  timer fires.

### Option A walkthrough matrix

| # | What the runtime does | What the user sees |
|---|---|---|
| S1 | Applier resolves `#cart-badge`; old badge id enumerated; fragment manifest minted (fresh anchor); morph swaps the badge subtree and the applier inserts the fragment's manifest tags after the patched root (step 3's tag carriage, which is what lets the deps manager see the new instance at all under the default morph); old badge anchor retired; deps sweep runs old badge's JS cleanup once, fires the new instance's `$onComponent`; `Dispatch` fires per faithful order. | The badge updates to the new count. Any listener on `cart:updated` reacts. Nothing else on the page moves. |
| S2a (same caller) | Both responses route to the card's anchor. Response 2 (epoch 2) applies: badge shows count 2, caller's state refreshes. Response 1 arrives stale: its **state refresh** is dropped by the caller's epoch guard, and under pure A its **targeted render applies** (4.2's letter, `events.md:1432-1436`; 5.2's stale row promises the opposite, the disagreement named under the normative facts): badge morphs back to count 1. Both `data` promises resolve. | The badge flashes the right count, then regresses to the older one until the next cart action. The page's own card stays consistent (state guarded); the badge lies. |
| S2b (different callers) | Two independent anchors, two epochs, no shared counter. Last-arrived render wins the badge. | Same regression as S2a, now unguardable by any per-anchor scheme. Because handlers render current truth (the count as computed server-side at handler time), the badge shows a value that was briefly true and self-corrects on the next event. |
| S3 | Every keystroke's response repaints `#results` in arrival order; each repaint retires and re-mints the results region's anchors. | Typing "ab" then "abc": results for "abc" render, then the late "ab" response overwrites them. The user sees results that do not match the input box, the exact bug class 4.2's guard kills for self-renders. Mitigations inside pure A: make the results region part of the caller (self-render, guarded; the audited LiveSearch shape) or accept the flicker. |
| S4 | Faithful order: `Dispatch("main:rebuilt")` fires first on the caller's roots (still in the DOM). The render then replaces `#main`: the caller's elements leave, its anchor retires (applier step 5), deps sweep runs its cleanup. The trailing `data` still resolves the promise (a JS closure, DOM-independent). The **second in-flight call** answers later, correlates to the retired anchor: instance-mutating actions dropped with a debug log, its `data` resolves, its own targeted actions (if any) apply. Had the `Dispatch` been listed after the render, its self-addressed dispatch would find zero roots and be dropped with a debug warning (a `document` fallback would half-fire: global `Citry.events.on` listeners would hear it while instance-scoped `$onEvent` filters never match, `eventTargetsInstance` and `subscribeForAnchor`, `citry-events.ts:877-897`). | The pane is rebuilt. The click's `await` still gets `{ok: true}`. Busy styling vanishes with the old DOM. Listeners heard `main:rebuilt` because the author ordered it before the destruction; the second click resolves without visibly doing anything more. No console errors from the response path (a timer or closure firing later from inside the departed region is S11's case). |
| S5 | The external badge render replaces the badge region inside the parent: badge anchors re-mint; the user's mid-typing input inside `#badge` is replaced (its anchor's pending writes die with it; morph's focused-control protection preserves at most the focused element's live value, while its queued `$state` write is gone). A mid-IME-composition input (the CJK-visible case) is harsher still: a replace aborts the composition session outright; morph's focused-element protection (in WP16's pinned morph call block, `events_plan.md:1580`) is the only mitigation, the same stance as the typing variant. The parent's next poll re-renders the whole card from the parent's State; the externally rendered badge content is regenerated from what the parent knows, wiping the targeted update (a parent's morph does not skip nested roots, `events.md:2169-2181`; the handler's tree is authoritative, `events.md:2988-2996`). The badge's anchors re-mint again per the nested lean. | The badge updates when targeted; the user's in-progress text in it is lost (or visibly kept in the focused box but silently untracked, reverting on the next round trip), and an in-progress IME composition is cut short. At the next poll tick the badge snaps back to whatever the parent renders. Acceptable only if the badge's data also lives in the parent's State or the region is page-level; the docs must say exactly that. |
| S6 | `querySelectorAll` finds nothing; zero-match warning logs; the action is a no-op; remaining actions proceed (already normative, `events.md:1515-1516`). The footgun variant is the second listed cause: a previous morph/replace swapped away the element carrying `id="cart-badge"` because the fragment's root did not re-emit it. From then on every targeted render to it warns. | Nothing visibly changes; the badge is frozen at its last content. The console says why on every attempt. Doc rule to ship: **the rendered fragment must carry the target's own hook** (root `id`/class), or use `swap="inner"` against a page-owned wrapper; the same contract htmx documents for `hx-swap-oob`. |
| S7 | Both matches receive the same fragment (all-matches, normative). One manifest, one instance id, minted once; both DOM copies carry `data-cid-<id>`; boundary scopes attach to every copy (`attachBoundaryScopes`, `citry-events.ts:646-651`). The two copies become, in effect, one multi-root instance sharing one anchor for state (multi-root instances share the one state object for free, `events.md:2280-2281`). What a later **self-render** of that instance does is written nowhere for this shape: the pairwise rule covers a fragment component's **adjacent sibling roots** "while the old and new root counts match", falling back to "replacing the whole root range" (`events.md:2162-2169`), and two selector-scattered copies in different page regions are neither adjacent, nor a range, nor count-matched against a one-root fragment. Target resolution itself is already written in the plural: 4.3 says a `cid:` target names "the elements carrying its `data-cid-<id>` marker" (`events.md:1518-1520`), so every copy receiving the fragment is the existing letter, not a new rule. What decision 5 ratifies is only the unwritten swap mechanics for scattered copies (apply the fragment to each marker-carrying element independently) and the shared-anchor state reading; WP16 needs a harness case for it. Wrinkle: the manifest tag is inserted twice, so the deps manager runs one redundant teardown-and-refire cycle for the id (its own open TODO, `citry.js:304-305`); the events side is idempotent (`citry-events.ts:671-677`, `citry-events.ts:689-691`). WP16 should strip manifest tags from all but the first insertion. | Desktop and mobile badges update together, and `$state` written in one reflects in both, which is what a shared badge means. The instance's own next self-render keeps them together only once the per-element swap rule is ratified; today that path is undefined text, not a working guarantee. One avoidable cleanup churn internally. |
| S8 | State model identical across swaps: departed ids retire, fresh manifest mints, no epoch. Differences are purely DOM-mechanical: `morph` patches minimally (unchanged descendants keep focus/scroll; the in-place id swap is caught by the attribute-watching sweep, `citry.js:393-409`); `replace` discards the subtree (focus and scroll in it die); `inner` keeps the wrapper (the safe pattern for plain-region targets, S6); `remove` retires with no successor. | Morph: the region updates with minimal visual disturbance. Replace: the region blinks and focus inside it is lost. Inner: as replace for the content but the wrapper (and its hook id) reliably survives. The choice is cosmetic, not semantic, which makes `swap` teachable. |
| S9 | The server places the `state` action before the handler's actions (`events.md:1508`); the applier refreshes the caller's token, then renders the badge. When the older response arrives second: the caller's `state` is dropped (epoch guard), the badge render applies. | The caller is consistent (its state and self-view never regress), but the badge regresses as in S2. A page where the caller shows "2 items" and the badge shows "1" until the next event. |
| S10 | The scheduled render sits in its `wait: false` window while response 2 paints `#results`. Pure A checks no staleness at arrival or at fire time, so at T+2s the older fragment repaints over the newer one. Independent of any epoch decision, the scheduled action must re-resolve its selector and re-check the caller's anchor liveness when it fires (the target may have left the DOM, the caller may have retired; arrival-time node references would be stale). | The results go right, then regress two seconds later with no interaction to explain it: S3's overwrite through a window the author personally armed. Under pure A the only mitigations are S3's. |
| S11 | The replace retires the region's anchors (steps 5-6). What the pending timer then does is undecided today and depends on when WP17 resolves element-to-anchor. A timer holding the **anchor** fires `sendFromAnchor` on a retired one: the landed runtime throws the pointed no-such-event error (the declared-events check reads an empty list off the null class id, `requireDeclaredEvent`, `citry-events.ts:432-454`, `citry-events.ts:804-813`). A fresh `$sendEvent` read resolves no anchor and returns a rejecting stub (`citry-events.ts:942-959`), an unhandled rejection if nothing catches it. Under `swap="morph"` the in-place id swap means fire-time resolution finds the **new** instance's anchor and fires its handler. Rule to ratify (decision 9), in two halves. Recurring timers retire with the region: retiring an anchor (steps 5-6) also cancels interval timers registered to it, or WP17 keys intervals to the element with one timer per element; either way a replaced `@c-poll` region never keeps an interval firing (and debug-logging a dropped send) every 30 seconds forever, and the element-keyed form makes a morph-surviving timer dedupe against the new instance's own manifest-initialized interval instead of compounding into double polling. One-shot closures resolve at fire time: a pending debounce flush or a captured `$sendEvent` re-resolves element-to-anchor when it fires; a fire-time miss, or a fire-time hit on a class that does not declare the event (a morph swapped in a different component), drops the send with a debug log; a one-shot surviving a morph fires the new instance by design. | Without the rule: a console error or unhandled rejection seconds after a region swap, a ghost call from a region the user watched being replaced, or a replaced polling region that keeps polling (or double-polls after every morph). With it: intervals stop with the region, the flush is silently dropped (debug breadcrumb), and under morph the new instance receives the surviving one-shot, which is what visually continuous DOM implies. |

**Summary of A's stress points**: S2/S3/S9/S10's stale-overwrite of
targeted regions (the guard's blind spot moved one selector away, and
the timing fields widen it), S11's send-from-a-retired-region texture
(an undecided rule the landed runtime answers with a throw), and
S5/S6's footguns, which are documentation problems more than model
problems. Its strengths: one rule, no new wire or bookkeeping, every
mechanism already exists or is needed anyway (the anchor sweep), and
swap-kind indifference.

### Option B walkthrough matrix (delta from A)

Only the cells that change are listed; all others are identical to A.

| # | What changes | What the user sees |
|---|---|---|
| S2a | The stale response's targeted render is dropped along with its state refresh; `citry:events:stale` fires. | The badge shows count 2 and stays there. The same-caller race is fully fixed. |
| S2b | Nothing changes (different callers, no shared counter). | Same last-write-wins regression as A. |
| S3 | The late "ab" response's `#results` render is dropped. | Results always match the newest keystroke that answered, restoring exactly the self-render guarantee. The marquee failure of pure A disappears. |
| S9 | The stale response drops both the state refresh and the badge render. | Caller and badge stay mutually consistent; neither regresses. |
| S10 | B closes this only if the drop rule is evaluated when a scheduled action **fires**, not when its response arrived (recommendation 2's apply-time clause): at T+2s the caller's highest-applied already reflects response 2, so the scheduled render drops and `citry:events:stale` fires. Arrival-time evaluation would wave it through while fresh and let it apply stale. | With apply-time evaluation the results stay right and the armed window closes. Without it, every `delay`/`wait: false` field re-opens the exact S3 hole B exists to close. |
| New cost (interleaved targets) | Call 1 renders `#sidebar` (epoch 1), call 2 renders `#main` (epoch 2), response 2 first: response 1's `#sidebar` render is dropped though nothing newer touched the sidebar. | The sidebar misses one update until the next event; debuggable via the `stale` lifecycle event. This under-application is B's price for S3. |

### Option C walkthrough matrix (delta from A)

| # | What changes | What the user sees |
|---|---|---|
| S1 | If `#cart-badge` is the instance root and the class matches, the badge's anchor reconciles in place (state identity, epoch, `$loading` survive). If `#cart-badge` is a wrapper div, C falls back to A's semantics: two behaviors for one feature. | Identical to A visually in the common case; the difference is invisible until a badge carries client state. |
| S2/S3/S9 | Unchanged: the target's surviving `highestApplied` cannot be compared against the caller's echoed epoch (two unrelated counters), so C brings no ordering fix without a wire change. | Same races as A. |
| S5 (typing variant) | A same-class targeted render onto the region the user is typing in reconciles: pending unsent writes keep their fields, the focused control keeps value and caret (`events.md:2391-2401`). The parent-poll wipe is unchanged (the parent's fragment is authoritative). | The one genuinely better cell: an external same-class refresh does not eat a draft. Weighed against: the audit found no production pattern doing this, and the parent-render case (which C cannot save) remains the bigger hazard in the same scenario. |
| S7 | Degrades to A's end state, reached messily: linking N anchors through one incoming id re-points the index at each link, the last-linked anchor wins (`citry-events.ts:617-620`), and both copies thereafter share it, exactly A's shared-anchor outcome. What C adds is arbitrariness and strays: which predecessor's state continues is whichever match linked last (document order), and the losing anchors are stranded still carrying the live component id, so a liveness sweep cannot retire them and their old subscriptions keep firing on the new copies' events (`subscribeForAnchor`, `citry-events.ts:886-897`). Making this principled means first-match-only for interactive fragments (contradicting the ratified all-matches rule) or anchor merging. | Both copies update and share state as under A; which region's draft or pending writes survived into the shared anchor is arbitrary. The honest cost here is that arbitrariness, not the sharing; C's rejection rests on the other grounds above. |
| S8 | Swap kind becomes semantic: reconcile-in-place makes sense under `morph`, is incoherent under `replace` (a wholesale DOM discard that "keeps" reactive state for controls that no longer exist). | Authors must learn which swap preserves state; the A-model's "swap is cosmetic" teaching is lost. |
| S11 | A same-class targeted render keeps the target's anchor (and its pending writes) alive, so a pending debounce flush or poll timer finds a live anchor at fire time and delivers, carrying the queued writes. | The mid-typing draft survives the external refresh and reaches the server: genuinely better in this cell, weighed exactly as S5's typing variant (no audited production pattern demands it, and the parent-render hazard C cannot save remains). |

## Does remove-and-replace collapse into an existing path?

Yes, and this is the strongest argument for the lean, but the path is not
the one the framing suggests. It does **not** ride the three-way split's
different-class adoption branch: that branch keeps the anchor object
alive (the epoch, `$loading`, and `$error` boxes persist) and rebuilds
its state contract (`citry-events.ts:607-616`), which is precisely what
remove-and-replace refuses to do for a region addressed from elsewhere.

It collapses instead into the **uncorrelated-manifest path**: the landed
runtime already mints a fresh anchor whenever a manifest names an unknown
component id (`citry-events.ts:678-681`), which is how the initial page
load, host-inserted fragments, and (v2) server push all get anchors
(`spike-component-identity.md:331-336`). Under option A a targeted render
is exactly that: an uncorrelated fragment arriving at a DOM position,
plus the retirement of whatever the position held. The whole client model
then has exactly two continuity classes:

1. **Correlated self-render** (the correlation id resolves the caller's
   anchor and the target agrees): the three-way split, reconcile or adopt
   or retire, with the epoch guard.
2. **Everything else** (initial load, host insert, targeted render,
   parent fragment containing children, server push): fragment-insert
   semantics; fresh manifest entries mint fresh anchors, departed ids
   retire.

The three-way split's job narrows to "what may a caller's own response do
to its own anchor", which is exactly where its reconcile subtleties
(pending-writes precedence, focused-control protection) earn their keep.

## Harmonization with the nested-instances lean

The neighboring 16.1 item (child anchor continuity under a parent
re-render, `events.md:3754-3763`) has a maintainer lean of the same
shape: children do not survive a parent's render as continuing client
identities; the parent's fragment carries fresh child ids that mint fresh
anchors, and the old child anchors retire. Adopting both leans yields one
sentence covering both items:

> A render arriving from anywhere other than the region's own correlated
> call replaces the region's client state wholesale.

The mechanism is shared too, not just the sentence: both need (a) the
landed mint-on-unknown-id path, untouched, and (b) the same anchor
removal reconciliation (option A step 6). One sweep retires child anchors
a parent's morph discarded and target anchors a cross-region render
replaced; neither item needs machinery the other does not. The sibling
analysis, written independently, names the same machinery in its own
recommendation, all four items: "pre-registration before the swap, the
retirement sweep, the retired-anchor response policy, the
apply-iff-greater guard"
(`analysis-nested-anchor-continuity.md:749-751`), which is convergent
evidence that the shared-mechanism claim is real rather than wishful.
The convergence must be read precisely, though: the sibling's fourth
item restates the standard narrow guard (instance-mutating actions,
apply-iff-greater, its machinery item 4,
`analysis-nested-anchor-continuity.md:283-288`), and its retired-anchor
drop set is the narrow one, "the self-targeted render and the token
refresh" (its machinery item 3,
`analysis-nested-anchor-continuity.md:276-282`). The sibling is silent
on this document's B widening, so the shared machinery is convergent
evidence for the baseline lifecycle, not independent support for B.

Three points of divergence deserve explicit resolution rather than
papering over. First, **when keyed continuity ships.** This document
defers
every continuity upgrade as one v2 design (recommendation 6): child
keying under a parent morph (the `c-key` kinship the nested bullet
names), targeted adopt-in-place (option C), and anchor update for
server push (`events.md:3771-3777`) are all instances of the same
future question, "when may an uncorrelated render attach to an existing
anchor instead of minting one, and keyed by what", and nothing in
option A forecloses that design: it would slot in as a client-side
attach rule (plus, if server keying is ever wanted, additive manifest
vocabulary behind capabilities). The sibling instead recommends
adopting author-keyed child linking as the only linking mechanism now,
"gated on pricing the key-emission mechanic", shipping in the WP16/17
wave if the `c-key`-to-root-marker forwarding prices small
(its recommendation item 3,
`analysis-nested-anchor-continuity.md:755-760`). Both positions sit on
the same option-A baseline (keyed linking is an attach rule layered on
top, not a different lifecycle), so the either/or is scheduling: design
the three continuity consumers once in v2, or land child keying early
and defer the other two. Neither document can settle that for the
other; decision 10 puts it to the maintainer. Second, **how wide the
stale and retired drop set is.** The sibling's WP16-facing machinery
encodes the narrow set (self-targeted render plus token refresh); this
document's central recommendation widens it to all render actions (the
B extension). Ratifying B therefore edits the sibling's premise, not
just `events.md`; decision 2 carries the sibling's contrary lean.
Third, **liveness re-check granularity**, resolved here by adoption:
the sibling's decision 5 requires the re-check per action within one
result (its concrete shape: `[Render(X, target="#panel"), self-render]`
where `#panel` contains the caller, so action 1 retires the caller and
action 2's self-render must drop,
`analysis-nested-anchor-continuity.md:824-838`), and recommendation 3
adopts exactly that rule, so both documents hand WP16 the same
granularity. One residual WP17-facing texture difference (what a
captured send does against a retired anchor: drop with a debug log
here, keep a pointed error there) is named in decision 9 for the
maintainer to reconcile.

## Ecosystem prior art

Only entries that genuinely map are included.

**htmx out-of-band swaps and `hx-sync`.** `hx-swap-oob` elements in a
response body each update their own target elsewhere in the page,
addressed by id, with the swapped-in element required to carry its own
address (`recon-ecosystem.md:163-165`); swap application itself carries
no versioning, so racing responses are last-write-wins **by default**.
htmx's opt-in answer sits one layer up: `hx-sync` (its attribute
reference; the recon covers only the OOB mechanism) declares a
synchronization strategy on the triggering element (drop, abort,
replace, or queue the request) so racing **requests** are serialized or
cancelled before they answer, with a search input racing itself as the
documented example. The field's precedent for S3 is therefore
request-level sync as an opt-in, never apply-time ordering. OOB is the
direct ancestor of citry's targeted render, and it is pure option A
semantics on a client with no component state: the region is whatever
the last swap put there. Two of its documented contracts carry over
verbatim as doc rules: the fragment must re-emit its own hook to stay
addressable (S6), and ids-as-targets make DOM structure part of the
page's contract (already echoed at `events.md:1520-1522`).

**Turbo Streams.** One response or broadcast carries any number of
`(target, action, fragment)` operations; nine actions; no epochs, no
region versioning; concurrent broadcasts converge because the guidance is
to render current state, not deltas (`recon-ecosystem.md:158-176`). That
convergence property is worth restating in citry's docs as the reason
last-write-wins is tolerable for cross-caller races (S2b): a handler that
renders truth produces regions that are at worst briefly stale and
self-correct on the next event, while a handler that rendered increments
would corrupt. Turbo's `targets` (plural, CSS selector) is the precedent
already cited for the all-matches rule (`events.md:1512-1515`).

**Livewire nested components and `wire:key`.** Livewire's nested
components are islands, answering the identity question in the opposite
direction from citry's subtree re-render: a parent render emits child
placeholder stubs and the morph skips live child roots, so children
update only through their own requests, with `wire:key` naming list
identity (`events.md:2169-2181`). Notably, Livewire has **no**
render-into-another-component's-DOM primitive at all: cross-component
effects go through dispatched events, and the listening component
re-renders itself. The field's component-state framework avoids
cross-addressed renders precisely because of the identity questions this
analysis answers; the fragment-shipping frameworks (htmx, Turbo) embrace
them by having no client component state to reconcile. Citry's lean
threads this exactly: fragment-shipper semantics (wholesale replace) for
renders addressed from elsewhere, island semantics (guarded reconcile)
reserved for a region's own renders, and the Livewire-style
dispatch-and-refresh loop kept as the documented tier for contested
regions (`events.md:1058-1063`).

**Phoenix LiveView components and streams.** LiveView can target a
component by id (`send_update`), but the update flows through server-held
component state and down a single WebSocket, so every client applies a
server-serialized total order; the reorder class this analysis wrestles
with cannot occur there by construction (the server-held diff model,
`recon-ecosystem.md:143-156`). The lesson is not a mechanism to copy
(citry's dispatcher is deliberately stateless over HTTP) but a boundary
to note: citry's v2 WebSocket transport would incidentally serialize
responses per connection and shrink S2/S3 to the multi-tab case. LiveView
streams (collection updates addressed by DOM id, with the server holding
no copy and the collection reset wholesale on remount) are that
framework's own admission that for regions the server does not hold,
last-write-wins plus wholesale reset is the workable contract, which is
option A's contract.

**React keys.** A key change remounts the subtree: state is deliberately
reset when the author declares the identity different. Citry's `c-key`
already borrows this for list morphing (`events.md:2153-2160`); option A
extends the same principle to regions: a targeted render is an identity
change for the region (new instance id, new anchor), so client state
resets by design rather than by accident. That framing is worth using in
the user docs, since the audience knows it from React.

## Wire-protocol impact

The goal is client-internal resolution, and all three options meet it:

- **Option A**: no wire change. Targets, swaps, manifests, and the echoed
  epoch are already in the citry-events/1 schema; minting, retiring, and
  sweeping are client bookkeeping. The retired-anchor response rule is
  client policy over existing fields.
- **Option B**: no wire change. The epoch is already echoed per result
  (`events.md:1427-1443`); widening what the client drops is applier
  policy. It does revise a design-doc sentence (the 4.2 clause that
  non-instance actions of a stale response "apply normally"), which is a
  doc edit, not a protocol edit, and one that aligns 4.2 with 5.2's
  stale row, which already promises the broad drop (`events.md:1978`).
- **Option C**: no wire change for the mechanics analyzed here (target
  resolution to an anchor is a client-side index lookup). Any version of
  C that becomes *useful* for ordering, though, needs a region-scoped
  logical clock or server-declared region identity on the wire, which is
  the dismissed option D. C without D is wire-clean but delivers only
  state continuity, not ordering.

The only shapes that cannot keep the wire unchanged: server-declared
region keys / per-region epochs (option D), and any fix for S7 that mints
N distinct instance ids for N selector matches (the server would have to
render N instances). Both are named so they are not reinvented casually.

## Recommendation

**Adopt option A (remove and replace) as the v1 rule, with the B
extension folded in, and two new lifecycle rules ratified: one for
responses correlating to a retired anchor, one for sends firing from
one.** Concretely:

1. **Anchor lifecycle: option A verbatim.** Targeted renders retire the
   old region's anchors and mint fresh ones from the fragment manifest;
   mint-before-swap mirrors link-before-morph; the events runtime gains
   the anchor removal sweep (which the nested-instances item needs
   anyway and which fixes the existing leak).
2. **Ordering: B's widened drop rule.** A stale result (the caller's
   epoch comparison, unchanged) drops **all** its render actions and its
   state refresh; `data` resolves; `event`/`redirect`/`url` apply;
   `citry:events:stale` fires. This is one clause in a branch WP16
   builds regardless, it keeps the lean's letter (no guard ties the
   apply to the *target's* past), and it closes S3, which otherwise
   reintroduces the unicorn/Livewire stale-overwrite bug one selector
   away from the path the epoch guard protects. The cost (the
   interleaved-targets under-application) is accepted and observable via
   the stale event. One clause more, or the rule leaks through the
   timing fields: **scheduled actions re-evaluate at apply time**. A
   `delay` or `wait: false` action (`events.md:1541-1551`) re-checks
   the caller's staleness and re-resolves its target (and the caller's
   anchor liveness) when it fires, not when its response arrived;
   otherwise a fresh-at-arrival scheduled render applies after a newer
   response has landed and re-opens S3 through a window the author
   armed (S10). If the maintainer prefers pure A, the difference is
   exactly this clause and the S2a/S3/S9/S10 rows above; nothing else
   in this analysis moves.
3. **Retired-anchor responses, with per-action liveness.** A response
   correlating to a retired anchor behaves like a stale response (same
   drop set, debug log). Liveness is re-checked **per action, in
   faithful list order**, not once per response: an earlier action in
   the same result can retire a later action's target or caller. The
   sibling analysis's decision 5 pins the same rule with the concrete
   shape `[Render(X, target="#panel"), self-render]` where `#panel`
   contains the caller (action 1 retires the caller's anchor, so action
   2's self-render drops with the same debug log), and adds the
   mechanism constraint that makes the drop real: the per-action check
   must see retirement the applier performs synchronously (step 5), not
   wait on the microtask-debounced backstop sweep, which settles too
   late (`analysis-nested-anchor-continuity.md:824-838`). Within a
   multi-result envelope the identical rule covers a targeted render
   retiring a sibling call's caller before that sibling's result is
   reached. v1 sends one call per envelope and
   `Citry.events.applyActions` applies one result's actions array
   (`events.md:1958`), so multi-result ordering bites v2 batching
   first, while the per-action re-check is applier policy and bites
   from day one.
4. **Retired-anchor sends: retire recurring timers with the anchor,
   resolve one-shots at fire time.** Two halves, both WP17-facing
   (S11). Recurring timers do not outlive the region: retiring an
   anchor (steps 5-6) also cancels the interval timers registered to
   it, or WP17 keys intervals to the element with one timer per
   element; either form guarantees a replaced `@c-poll` region never
   leaves a dead interval firing (and debug-logging) forever, and the
   element-keyed form makes a morph-surviving timer dedupe against the
   new instance's own manifest-initialized interval instead of double
   polling. One-shot closures (a debounce flush, a captured
   `$sendEvent`) resolve element-to-anchor when they fire; a fire-time
   miss, or a fire-time hit on a class that does not declare the event
   (a morph swapped in a different component), drops the send with a
   debug log instead of the landed runtime's throw or unhandled
   rejection; a one-shot surviving a `swap="morph"` consequently fires
   the new instance's handler, by design. The sibling analysis's
   machinery item 2 names the same two forms, teardown-at-sweep versus
   fire-time-liveness, as the pick the WP17 brief must make
   (`analysis-nested-anchor-continuity.md:265-273`); decision 9
   reconciles the two documents into one rule for that brief.
5. **Cross-caller races stay last-write-wins**, documented with the
   render-truth-not-deltas guidance and the dispatch-and-refresh pattern
   (`Dispatch` plus the listener re-rendering itself) as the tool for
   contested regions, where the region's own anchor serializes its
   updates.
6. **Option C is rejected for v1** and its substance is merged into the
   existing v2 open question on anchor update for server push
   (`events.md:3771-3777`), so continuity upgrades are designed once,
   with child keying, targeted adopt-in-place, and push updates as the
   three consumers (the sibling analysis would land child keying
   earlier if it prices small; that either/or is decision 10).

**Why this and not the alternatives**: it is the only shape that is one
rule instead of two (C fails this), needs zero new wire or server work
(D fails this), does not resurrect a shipped bug class one selector
away from the guarded path (pure A fails this), and composes with the
nested-instances lean
into a single v1 model whose every deferral is genuinely deferable
(whether the child-keying deferral is actually taken is decision 10,
the one scheduling point the sibling analysis answers differently).

**Falsifiers** (evidence that would prove this recommendation wrong):

- The dogfood port (the planned rewrite of the audited production app,
  `events.md` section 13) surfaces a recurring pattern of targeted
  renders into regions holding live client state (drafts, focus,
  pending writes) that dispatch-and-refresh cannot express cleanly. That
  would prove wholesale reset too destructive and pull option C's
  reconcile forward from v2.
- Real usage shows the B extension's under-application (interleaved
  targets from one caller dropping a region's update) at a rate the
  `citry:events:stale` telemetry makes visible and users actually
  notice. That would prove per-caller staleness too blunt and force
  either pure A or per-target bookkeeping (option D's clock).
- The WP16 harness shows the mint-before-swap plus observer-idempotency
  pair failing under `swap="morph"`: bound expressions in the incoming
  fragment rendering blank because a read raced the mint, or the
  fragment's manifest tags never landing in the DOM because the tag
  carriage (step 3) was skipped or mis-ordered, observable as assets
  not loading, `$onComponent` never firing for the new instance, and
  the token refresh going missing. Either symptom would prove the
  two-pass manifest handling insufficient and require the applier to
  own manifest processing exclusively (stripping tags from the fragment
  before insertion and handing the `data-citry` tag to the deps
  manager).
- S7 in practice: if multi-match targeted renders of interactive
  fragments turn out common and the shared-anchor semantics confuse
  users (a send from one copy updating both reads as a bug rather than
  a feature), the all-matches rule needs an interactive-fragment carve
  ("first match wins, warn on the rest"), which contradicts a ratified
  decision and would need its own round.
- The anchor sweep shows measurable cost on dense pages (it is the same
  cost class as the deps sweep: a map iteration plus one selector probe
  per tracked id, debounced). That would argue for folding both sweeps
  into one notification rather than two observers, not for changing the
  model.

## Decisions the maintainer must still make

1. **Ratify the rule** (option A, or A plus the B clause). This edits
   `events.md`: a targeted-render paragraph in 5.5 (or a new 5.6), the
   4.2 epoch bullet's drop-scope sentence, and 5.2's
   `citry:events:stale` row (`events.md:1978`), which today promises
   the broad drop 4.2 does not: under B, 4.2 widens to match the row;
   under pure A, the row narrows to match 4.2. It also edits the
   delegation plan: WP16's build bullet encodes the narrow rule today
   ("stale responses drop instance-mutating actions, promises still
   resolve", `events_plan.md:1562-1563`) and must move with whichever
   rule is ratified (the plan's design-doc-wins rule covers a missed
   spot, but this list is what the brief author edits from). Either way
   all three places end up saying the same thing, and the 16.1 bullet
   resolves into 16.2.
2. **The stale drop set, exactly.** If B is taken: renders and state
   drop; do `event` actions from a stale result still fire? (This
   analysis says yes: a late dispatch is old news whose listeners
   re-fetch fresh truth, so applying it is self-correcting; dropping it
   could starve refresh loops.) Note the sibling analysis leans the
   other way on width: its WP16 machinery pins the narrow set
   (self-targeted render plus token refresh, its machinery item 3), so
   ratifying B also updates that brief's premise.
3. **Retired-anchor responses** (recommendation item 3): ratify the
   drop set, the debug log wording, and per-action liveness re-checking
   in faithful list order, within one result and across results in one
   envelope (the sibling analysis's decision 5 states the same rule;
   the shape to test is a targeted render that retires the caller,
   followed in the same result by the caller's own self-render or
   dispatch).
4. **Self-addressed dispatch after self-destruction** (S4): ratify
   drop-with-debug-warning over a document fallback, and add the
   faithful-order authoring note ("dispatch before the render that
   destroys its audience") to the actions docs.
5. **Multi-match interactive fragments** (S7): ratify the
   shared-anchor / multi-root reading as the documented semantics, and
   ratify the swap mechanics for a later self-render of the duplicated
   instance. Target resolution needs no new rule: 4.3 already writes
   the `cid:` form in the plural ("the elements carrying its
   `data-cid-<id>` marker", `events.md:1518-1520`). What is genuinely
   unwritten is only how the swap applies to selector-scattered copies
   (the pairwise rule assumes adjacent, count-matched roots,
   `events.md:2162-2169`); proposed: apply the fragment to each
   marker-carrying element independently, with a WP16 harness case.
   Plus the WP16 note to strip duplicate manifest
   tags (and whether to also close the deps manager's own
   duplicate-fragment TODO, `citry.js:304-305`, in the same pass).
6. **Selector-hits-the-caller**: a handler that explicitly targets a
   selector resolving to its own region gets replace semantics, not the
   three-way split (self-continuity rides only the server's `cid:`
   self-address). Cheap to state now, confusing to leave implicit.
7. **Sweep architecture** (implementation, WP16): one shared
   DOM-mutation notification driving both the deps sweep and the anchor
   sweep, or two independent observers. Two observers is simpler and
   matches the layer split; fold only if the falsifier above fires.
8. **Docs commitments for WP19**: the fragment-carries-its-own-hook rule
   (S6), `swap="inner"` as the plain-wrapper pattern, render truth not
   deltas, dispatch-and-refresh for contested regions, "a targeted
   render resets the region's client state" stated with the React-key
   framing, and the mid-typing loss (a targeted render into a region
   the user is typing in loses the draft, and an in-progress IME
   composition is cut short on replace; morph's focused-element
   protection is the only mitigation, S5).
9. **The retired-anchor send rule** (S11, recommendation item 4, the
   WP17-facing half): ratify both halves. For recurring timers, pick
   the form: cancel intervals at anchor retirement (steps 5-6), or key
   them to the element with one timer per element so a morph survivor
   dedupes against the new instance's own interval instead of double
   polling; the sibling analysis's machinery item 2 hands the WP17
   brief the same pick as teardown-at-sweep versus fire-time-liveness
   (`analysis-nested-anchor-continuity.md:265-273`). For one-shots,
   ratify fire-time anchor resolution, the drop-with-debug-log on a
   fire-time miss or an undeclared event, and the morph consequence (a
   surviving one-shot fires the new instance). One texture difference
   to reconcile while ratifying: for a captured send hitting a retired
   anchor, this document says drop with a debug log, while the sibling
   says accept the pointed error or make it friendlier, never silence
   (`analysis-nested-anchor-continuity.md:253-260`); WP17 needs one
   answer. The landed runtime's current texture is a pointed throw or
   an unhandled rejection (`requireDeclaredEvent`,
   `citry-events.ts:432-454`, `citry-events.ts:804-813`,
   `citry-events.ts:942-959`), which WP17's debounce and poll work
   would otherwise inherit unratified.
10. **Keyed-linking timing**, the scheduling divergence from the
    sibling analysis (the harmonization section lists the full
    divergence set): defer author-keyed continuity into the single v2
    continuity design (recommendation item 6), or take the sibling's
    gated path, pricing the `c-key`-to-root-marker forwarding now and
    shipping keyed child linking in the WP16/17 wave if small (its
    recommendation item 3,
    `analysis-nested-anchor-continuity.md:755-760`). Both sit on the
    same option-A baseline, so this is scheduling rather than model,
    but the two documents genuinely disagree and the WP16/17 briefs
    need the answer.
