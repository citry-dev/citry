# Component-identity spike: two identities through morph

A design spike validating and detailing the maintainer's decided model for
component identity through a re-render, so it can be implemented in the events
runtime (WP15/WP16) and the serializer (WP10). Run on 2026-07-08 in a browser
harness loading the real `citry.js`, the pinned Alpine 3.15.12 plus
`@alpinejs/morph` 3.15.12 bundle, and hand-built manifests. It extends the WP6
morph and Alpine spike ([`spike-morph-alpine.md`](spike-morph-alpine.md)) and
reuses its pins and manifest builders.

**Result: all seven scenarios pass, with zero page errors and zero console
messages, across six consecutive runs.** The two-identity model holds end to
end against the real morph and the real dependency manager. This report turns it
into an implementable design and marks every claim as either empirical
(harness-proven) or design-recommendation (a server-side or additive choice the
harness models, since the server and the removal reconciler are not built yet).

## The model this spike proves

Two identities, kept separate on purpose:

- **The component id** (`data-cid-<id>`) is the faithful server-truth surface.
  It reflects exactly what the server rendered and it **changes on every
  render**: a re-render shows the server's new component id, never a reused one.
  It is what the DOM carries, what telemetry reads, what `$onComponent` reports,
  and what the dependency manager (`citry.js`) keys its whole lifecycle off. The
  server just renders naturally, minting a fresh id each time; there is no
  server id-reuse policy.
- **The anchor id** is a stable, client-internal identity for one interactive
  DOM position, owned entirely by the events runtime. It never rides the wire
  and is not user-exposed in v1. It keys the epoch out-of-order guard, the
  reactive state, the scope continuity, and the three-way split. It stays stable
  across re-renders even as the component id under it changes.

The client anchors continuity to the DOM position through the call-correlation
id (the envelope `id` field, 4.2), not through the component id. So the epoch
becomes per-anchor, carried in the envelope as an opaque echoed field the server
never interprets, and the wire does not change.

This revises two clauses in the current design, which the maintainer has
decided to reverse:

- events.md 5.3 today reads "the server pins the render id on re-render (`id=`
  argument), so identity is stable across updates." The decided model drops the
  pin: the server mints a fresh id every render, and the client's anchor
  supplies the continuity the pinned id used to.
- events.md 5.5 today holds the reactive State "keyed by instance id." It
  becomes keyed by the anchor, with a component-id-to-anchor index mapping the
  faithful (changing) id onto the stable anchor.

It also reframes events.md 4.2's epoch bullet, which is a consequence of the
two reversals above rather than a third reversal: the epoch's client-side
bookkeeping moves from per-instance to per-anchor to match the state, while
the epoch stays an opaque echoed field the server never interprets, so the
envelope itself is unchanged.

## Version pins (normative for WP15)

| Piece | Pin |
|---|---|
| `alpinejs` | 3.15.12 (exact) |
| `@alpinejs/morph` | 3.15.12 (exact) |
| `esbuild` | 0.28.1 |
| node | v25.8.1 |
| Playwright / Chromium | 1.61.0 (repo venv) / 149.0.7827.55 |

The runtime under test is the real file: `public/citry.js` in the harness is a
byte-identical copy of
`packages/py/citry/citry/ext/dependencies/client/citry.js` (sha256
`11458e9d228c172594ecbb8fe93683416322a6c73c6fcf7c21e74f90a558ee2c`, re-copied
and re-verified on every run). The dependency manager was not modified; the
removal reconciler and CSS GC are modeled as a separate additive layer
(`public/deps-reconciler.js`), which is the design-recommendation under test.

## What the harness is

Location (session-temporary, left runnable):
`/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/anchor-spike/`

Re-run: `npm install && npm run build`, then
`/Users/mac/repos/citry/.venv/bin/python run_anchor.py` (serves `public/`,
drives headless Chromium, prints the per-scenario pass/fail and writes
`evidence-anchor.json`).

Three layers, matching the intended production split:

- `src/anchor-runtime.js` (bundled to the iife `public/anchor-bundle.js`): the
  events runtime prototype. It owns the anchor registry, the
  component-id-to-anchor index, the correlation-to-anchor map, epoch-per-anchor,
  the three-way state split, and the morph call. It carries no knowledge inside
  the dependency manager.
- `public/deps-reconciler.js`: the approved removal reconciler plus Component.css
  GC, built as an additive layer on `citry.js`'s public surface (a
  `registerComponent` wrapper for teardown tracking, plus DOM observation). This
  models finding F9's additive change; it is component-id and class keyed and
  anchor-independent.
- `public/citry.js`: the real, byte-identical dependency manager.

The harness includes a modeled server (`SPIKE.server`) that mints a brand-new
random component id on every render, builds the fragment markup and the manifest
tags, and models the per-call `cls.State(**s)` rebuild (7.1), so the token-class
checks can be exercised. Ten initial instances cover the scenarios: eight
`Card`s, two `Widget`s (for CSS GC), and one multi-root `MultiCard`.

What the harness deliberately does not cover, so the green is not over-read: the
compiled `@c-*`/`:c-*` vocabulary (two-way binding is a stand-in listener plus
the focused-value protection from 5.3), the real transport (responses are
delivered by script with hand-built fragments), and the real removal reconciler
(modeled additively). These are WP10/WP15 to WP17 scope.

## Per-scenario results

Runtime health first: the full run produced zero page errors and zero console
messages (`"page_errors": []`, `"console": []`).

### 1. The faithful component id updates through a re-render (empirical): PASS

An anchor's first render carries `data-cid-init-faithful`. A self-render response
carries a different, fresh server id (`srv-...`). After the morph the DOM root
carries the new id, not the stale one, and the anchor is internally unchanged:

```json
{"c1": "init-faithful", "c2": "srv-m2j2twln", "anchorId": "anchor-1",
 "dom_has_c1": false, "dom_has_c2": true, "same_anchor": true,
 "anchor_current": "srv-m2j2twln", "labelDom": "Faithful v2",
 "domShowsC2Marker": "srv-m2j2twln", "anchorOf_c1": null}
```

The DOM shows the server's new id (`domShowsC2Marker` equals `c2`), the old id
is gone from the DOM and from the index (`anchorOf_c1: null`), and the same
anchor (`anchor-1`) now points at the new id. This is the core goal, and it
holds under a real in-place morph.

### 2. The epoch guard is per-anchor while the component id changes (empirical): PASS

Two rapid sends from one anchor (epoch 1, then epoch 2), each response carrying a
render with its own fresh component id. Epoch 2's response is delivered first,
then epoch 1's. The guard, keyed on the anchor's highest-applied epoch, drops
epoch 1's instance-mutating actions and keeps epoch 2's rendering:

```json
{"epochA": 1, "epochB": 2, "cA": "srv-x6gdrrr7", "cB": "srv-vtjaqop7",
 "anchor_current": "srv-vtjaqop7", "highest": 2,
 "dom_has_cA": false, "dom_has_cB": true,
 "routing": {"corrA_anchor": "anchor-2", "corrB_anchor": "anchor-2"},
 "dropLog": [{"detail": {"anchorId": "anchor-2", "epoch": 1,
   "highestApplied": 2, "action": "render"}}],
 "dataResolved": [{"ok": 1}, "ab", "a"],
 "ids_all_distinct": true}
```

Both responses route to the same anchor by correlation id
(`corrA_anchor` equals `corrB_anchor` equals `anchor-2`), never by component id.
The older response's `render` is dropped
(`"action": "render"`, `"epoch": 1`, `"highestApplied": 2`) even though each
render minted a fresh id (`ids_all_distinct: true`), and the older response's
`data` still resolves its own promise (`"a"` is present in `dataResolved`). This
is the decisive proof that the faithful, changing component id does not break
out-of-order handling.

### 3. The anchor survives every morph kind (empirical): PASS

The server fragment does not carry the anchor id, and morph strips old-element
attributes absent from the new fragment. Both candidate representations were
instrumented and measured before the runtime re-stamps.

Same root tag (`Card` to `Card`), the in-place patch:

```json
{"kind": "in-place", "sameNode": true,
 "attrSurvivedRaw": false, "nodeKeySurvivedRaw": true}
```

The node is kept (`sameNode: true`); a client-owned root attribute is stripped by
morph's `patchAttributes` (`attrSurvivedRaw: false`); a node-keyed WeakMap entry
survives because the node is the same (`nodeKeySurvivedRaw: true`).

Different root tag (`Card` div to `Panel` section), the wholesale swap:

```json
{"kind": "wholesale", "sameNode": false,
 "attrSurvivedRaw": false, "nodeKeySurvivedRaw": false,
 "nodeReplaced": true, "oldNodeDisconnected": true, "rootTag": "SECTION"}
```

The root node is replaced (`from.replaceWith(toCloned)`); neither
representation survives raw. This is confirmed against the plugin source:
`patch()` calls `swapElements` when
`differentElementNamesTypesOrKeys(from, to)` is true (different nodeType,
nodeName, or `key`), and `morph()` still returns the detached old node.

After the runtime re-stamps (in the `updated` hook for the in-place case and the
`added` hook for the wholesale case), both representations are re-established in
both cases (`rep.hasAttr: true`, `rep.nodeLink: true`), and the anchor is stable.
Range replacement (a `MultiCard` going from two roots to three) is runtime-owned,
so the runtime stamps the new roots directly:

```json
{"count": 3, "allRepsStamped": true, "anchorStable": true,
 "rangeLog": [{"detail": {"anchorId": "anchor-11", "from": 2, "to": 3}}]}
```

Reading (design-recommendation): the anchor needs no DOM representation for
correctness. See "The chosen anchor representation" below.

### 4. The three-way state split, keyed by anchor: PASS

**4a. Same class, reconcile with focused-local-first (empirical): PASS.** A
pending, not-yet-sent local write to `draft`, then a self-render whose fragment
says `draft: "server-draft"` and `label: "Recon v2"`:

```json
{"stateIdentity": true, "reactiveIdentity": true,
 "label": "Recon v2", "draft": "local-draft", "keptPending": true,
 "inputAfter": {"value": "ab", "caret": 1, "focused": true, "sameElement": true},
 "anchorStable": true}
```

The `$state` proxy and its reactive object keep identity across the render
(`stateIdentity`, `reactiveIdentity`), the server wins `label`, the pending local
write keeps `draft`, and the focused two-way-bound input keeps its value, caret,
and element identity. This re-confirms WP6 assertion 7, now with the component id
changing under the anchor.

**4b. Different class, wholesale token swap (empirical, with a modeled server
rebuild): PASS.** A `Card` anchor is re-rendered as a `Panel`:

```json
{"mode": "different-class", "currentClassId": "Panel", "tokenClass": "Panel",
 "adoptedFields": ["title", "mode"], "sent2TokenClass": "Panel",
 "bRebuild_ok": true,
 "aWouldCrash": "invalid_state: token class 'Card' does not match route class 'Panel'",
 "newRootIsSection": "SECTION",
 "cardTornDown": 1, "panelFired": 1, "reconRetire": 1,
 "anchorStable_sameId": true}
```

The anchor's old state is replaced wholesale by the Panel's fields (no per-field
reconcile), the anchor adopts the Panel's token, and a subsequent send carries
the Panel's token (`sent2TokenClass: "Panel"`), so the modeled
`Panel.State(**panel_fields)` succeeds (`bRebuild_ok: true`). The old A token on
the B route is exactly the stale-state crash the model avoids
(`aWouldCrash`). The Card's `$onComponent` cleanup runs once and the Panel's
callback fires once (`cardTornDown: 1`, `panelFired: 1`), and the anchor is the
same anchor (`anchorStable_sameId: true`).

**4c. Plain HTML, the anchor goes non-interactive (empirical): PASS.** A render
with no component:

```json
{"mode": "plain-html", "interactive": false, "currentComponentId": null,
 "noNewInstanceForAnchor": 0, "domNoCidMarker": true,
 "domText": "just plain html", "cardTornDown": 1}
```

The anchor becomes non-interactive, its state and scope are discarded, no new
instance is bound to it (`noNewInstanceForAnchor: 0`), the DOM node carries no
citry marker, and the old instance's cleanup runs once, with no console error.

### 5. The two layers compose (empirical against the real citry.js): PASS

A self-render changing the component id under a stable anchor, checked from both
layers:

```json
{"c1": "init-layer", "c2": "srv-i3md68ss",
 "c1_retired_once": 1, "c2_fired_once_recon": 1,
 "c1_teardown_once_comp": 1, "c2_fire_once_comp": 1,
 "anchor_stable": true, "epoch_advanced": true,
 "deps_layer_anchor_free": true}
```

The dependency manager retires the old id's cleanup exactly once and fires the
new id's callback exactly once (old id removed plus new id added), while the
events runtime keeps the anchor and advances its epoch. No cleanup runs twice and
none is missed. `deps_layer_anchor_free` confirms the reconciler's evidence names
only component ids and class ids, never an anchor: the two layers key off
different things and do not need to know about each other.

### 6. Component.css GC on the last instance of a class (empirical): PASS

Two `Widget` instances share one `Component.css` sheet tagged
`data-citry-css-class="Widget"`. Removing one leaves the sheet; removing the
second drops it, while the `Card` sheet (still-live instances) stays:

```json
{"initialPresent": true,
 "afterOne": {"widgetSheet": true, "cardSheet": true},
 "afterBoth": {"widgetSheet": false, "cardSheet": true, "varsSheetStillPresent": true},
 "cssGcLog": [{"classId": "Widget"}],
 "widget1Teardown": 1, "widget2Teardown": 1}
```

The css-vars sheet (`data-ccss-<hash>`) is left inert (`varsSheetStillPresent:
true`), out of scope as specified.

This scenario surfaced a real design point (empirical). A first, inline version
of the GC dropped a class's sheet on every solo-instance re-render, because the
faithful-id model retires the old id before the fresh same-class id fires. The
recorded reconciler evidence showed the thrash directly for the sole `MultiCard`
during the range-replace in scenario 3: `fire -> retire -> css-gc -> fire`. The
fix (design-recommendation, implemented and re-verified) defers the GC and lets a
same-tick same-class arrival cancel it; the same sequence then reads
`fire -> retire -> fire` with no GC, and the only GC in the whole run is the
`Widget` on its genuine last-instance departure. See "The CSS GC contract" below.

### 7. Fresh server ids on every render, no reuse needed (empirical): PASS

Three consecutive self-renders on one anchor, the server minting a brand-new
random id each time:

```json
{"ids": ["srv-m2j2twln", "srv-mr6kcale", "srv-qqax5gwo", "srv-iwmglv5p"],
 "all_distinct": true, "dom_shows_final": true, "state_resolves": "Fresh 2"}
```

Every id is distinct (`all_distinct: true`, four ids across the initial state and
three renders), the DOM always shows the newest id, and `$state` resolves
correctly after each render through the component-id-to-anchor index. The client
never needs the server to reuse an id: correlation-to-anchor routing plus
faithful-id display is sufficient. This proves that no server id-reuse policy is
needed.

## The implementable design

### The anchor lifecycle

An anchor is a plain object in the events runtime's registry, keyed by a
client-minted `anchorId`. Its fields: the current component id, the current class
id, the epoch counter, the highest-applied epoch, the reactive State object, the
pending (not-yet-sent) local writes, and the current token.

- **Created** when an interactive region's component id first appears in a
  manifest that is not a correlated render response: the initial page load, a
  server push, or a plain fragment insert. The runtime mints a fresh anchor id,
  binds the component id to it in the index, seeds the reactive State from the
  manifest's public values, and attaches the boundary scope.
- **Updated** by a correlated render response. The response is routed to the
  anchor by the envelope `id` (the correlation id), never by a component id. The
  runtime, which owns the render application, does the linking and the state
  update **before** the morph, then morphs, then retires the old component id's
  entry in the index (see the ordering requirement below).
- **Destroyed** when the region leaves the DOM: a plain-HTML render on the
  anchor, or the region removed by a parent re-render. The anchor becomes
  non-interactive and its state and scope are discarded.

**Ordering requirement (empirical).** The fresh component id must be bound to the
anchor, and the anchor's State must be updated, before the morph call runs, not
after. Morph's Alpine bridge (finding F3) re-evaluates the incoming fragment's
bound text during the patch, and Alpine re-initializes a wholesale-swapped node
right after; both resolve `$state` through the fresh component id. Linking after
the morph made every incoming `$state` read fail during the patch. The runtime
therefore: captures the current roots by the old id, links the new id and updates
State, morphs, then deletes the old id's index entry.

### The chosen anchor representation

The anchor's tie to the DOM is the **component-id-to-anchor index**, a plain map
the runtime re-links synchronously on every render. It needs no DOM attribute and
no node-keyed WeakMap, because the runtime owns the render application: it parses
the fresh component id from the fragment, knows the anchor from the correlation
id, and re-links around the morph. `$state` resolution walks
`el.closest("[data-cid]")` to the innermost component id and looks that up in the
index, exactly as 5.5 already specifies, with the index (not a reused id)
carrying the continuity.

This is the recommendation because the empirical morph behavior rules out a
DOM-carried anchor as a free ride:

- A same-tag patch is in place (same node), and morph strips a client-owned root
  attribute, so representation (a), the `data-canchor-<id>` attribute, survives
  only if re-stamped.
- A different-tag patch is a wholesale `replaceWith`, so both representation (a)
  and representation (b), the node-keyed WeakMap, are orphaned and must be
  re-linked on the new node.

Because the wholesale case forces an explicit re-link regardless, the WeakMap's
free ride in the in-place case buys nothing the index does not already provide,
while adding a second bookkeeping structure that silently breaks on a class
change. So representation (b) is rejected as the tie.

If a DOM-inspectable anchor marker is wanted later (the devtools root-element
attribute is an open question in events.md 16.1), representation (a), the
re-stamped `data-canchor-<id>` attribute, is preferred: the spike confirms it
stays stable across a same-structure patch (re-stamped in the `updated` hook), a
structurally-different patch (re-stamped in the `added` hook), and a wholesale
node replacement, and it is human-visible in devtools. It is a debugging aid on
top of the index, not the tie itself.

### Epoch per anchor

The epoch counter and the highest-applied epoch live on the anchor. A send
increments the counter and records the correlation id against the anchor. A
response, routed to the anchor by its correlation id, compares its echoed epoch
against the anchor's highest-applied epoch: a strictly lower epoch drops the
instance-mutating actions (the self-targeted `render` and the `state` token
refresh) and keeps the rest (a `data` action still resolves its own promise, and
non-instance actions apply). The faithful, changing component id never enters the
comparison. On the wire the epoch stays an opaque echoed field (4.2); only its
bookkeeping moves from per-instance to per-anchor, which is invisible to the
server.

### The faithful component-id contract

The server mints a fresh component id on every render. `data-cid-<id>` reflects
exactly what the server rendered; the DOM, telemetry, and `$onComponent` always
show the current server id, never a reused or stale one. There is no server
id-reuse policy and no `id=` pin. The client supplies continuity through the
anchor, so the server renders naturally.

### The three-way state split, and where the client detects it

The detection point is one comparison: the anchor's current class id against the
incoming render's token class id (read from the fragment's events manifest
instance tuple, equivalently the fresh token's `c` field).

- **Same class**: reconcile. Server wins per field, except fields with a pending,
  not-yet-sent local write, which keep the local value (5.5). The anchor's Alpine
  scope and `$state` object identity persist; a focused two-way-bound input keeps
  its value and caret.
- **Different class**: discard the anchor's old state and adopt the server's
  fresh token and values wholesale, with no per-field reconcile (the fields do
  not correspond). Rebuild the anchor's boundary scope for the new class. The
  anchor persists, but its state contents are rebuilt, so a subsequent send
  carries the new class's token and the server's `cls.State(**s)` rebuild
  succeeds.
- **Plain HTML** (the render carries no component): the anchor becomes
  non-interactive, its state and scope are discarded, its instance's cleanup runs,
  and no new instance is created.

**A robustness point (empirical in the harness's stand-in, to confirm against
the real magics).** `$state` on an element that carries a marker but whose id
is momentarily unregistered (the brief window mid-morph while the component id
is changing) must resolve to an inert empty value, not throw. Morph's bridge
and Alpine's teardown can evaluate a bound node in that gap. The hard "outside
any instance" error stays reserved for an element with no citry marker at all.
The harness proved this with its stand-in `$state`; confirming it against the
real magics implementation is a tracked deferred item (Deferred design item 4
below, events.md 16.1).

### The layer split, and how the two layers compose

The events runtime owns the anchor, the epoch, the reactive State, the morph
call, and the correlation routing. The dependency manager (`citry.js`) stays
keyed by the component id for `$onComponent`, cleanup, and asset dedupe, and
gains the removal reconciler (below). The dependency manager needs no knowledge
of the anchor.

They compose because a self-render is, to the dependency manager, an old
component id removed and a new one added: it runs the old id's cleanup once (via
the removal reconciler) and fires the new id's callback once (via the existing
call path), each keyed off the component id. The events runtime, meanwhile, keeps
the anchor and its epoch, keyed off the anchor. The spike proves no cleanup runs
twice and none is missed while the id changes under a stable anchor (scenario 5),
against the byte-identical `citry.js`.

**The removal reconciler (design-recommendation, finding F9).** `citry.js` as
shipped runs an instance's cleanup only when a new call for the same id arrives.
Under the faithful-id model a re-render mints a fresh id, so the old id's call
never recurs and its cleanup would leak. The reconciler closes that: it runs an
instance's cleanup when the instance's last `data-cid-<id>` element leaves the
DOM. Detection is a sweep comparing the set of known-fired ids against the live
DOM, triggered on DOM mutation and after each render; it catches both real node
removals and morph's in-place attribute swap (the same node losing its old
`data-cid-<id>` via `removeAttribute`). In the harness the reconciler is an
additive layer on the public surface, which proves F9's claim that this is an
additive change and not a redesign; a real implementation would likely fold it
into `citry.js` reaching the same private cleanup store.

### The CSS GC contract

A class-level `Component.css` sheet carries `data-citry-css-class="<class>"`. The
removal reconciler garbage-collects it when the last live instance of the class
leaves. The per-render css-vars sheets (`data-ccss-<hash>`) are left inert (out
of scope).

**The GC must be deferred, not run inline on retirement (empirical
finding, design-recommendation).** Under the faithful-id model a solo-instance
re-render retires the old id before the fresh same-class id fires, so an inline
"last instance of class left" check fires spuriously on every re-render and drops
the sheet. For a URL-served sheet this would be worse than a redraw: `citry.js`
still marks the sheet's URL loaded, so it would not be re-fetched, and the class
would lose its styling permanently (the harness's inline sheets re-add
themselves, which masks that; a URL sheet would not). Deferring the GC to a
later task and re-checking the live count lets the fresh instance's arrival
cancel it, coalescing re-renders. The spike implements the deferred version and
confirms the re-render no longer GCs while the genuine last-instance departure
still does.

### The plain-HTML contract

A render that carries no component makes the anchor non-interactive: its state
and scope are discarded, its instance's cleanup runs (through the removal
reconciler retiring the old id), no new instance is created, and no console error
is raised.

## Deferred design (not resolved by this spike)

- **Nested anchors.** A citry instance inside another instance's region. The
  innermost-last `$state` resolution already handles reads, but the anchor
  lifecycle under a parent re-render (the parent's fragment carries the child's
  fresh id) needs its own pass: how the parent's render re-links child anchors,
  and whether a child anchor can be created or retired mid-parent-morph.
- **Renders targeting a different element** (`target="#other"` or a CSS
  selector). This spike only exercised self-renders, where the correlation id and
  the target agree. A render addressed to a different anchor, or to a
  non-component region, raises unresolved questions: which anchor's epoch guards
  a cross-anchor render, and whether a selector-targeted render can create or
  retire an anchor.
- **Anchor creation for server push and plain fragment inserts.** The spike
  creates a fresh anchor for any uncorrelated component id, which covers the
  initial page load. Server push (section 8) and host-inserted plain fragments
  arrive with an events manifest but no correlation, and their anchor lifecycle
  (when an uncorrelated manifest should attach to an existing DOM position rather
  than mint a new anchor) needs its own design.
- **The `$state` inert-fallback** for a mid-morph node whose id is momentarily
  unregistered should be confirmed against the real magics implementation.

## Findings, marked

- **F-CI-1 (empirical).** Morph patches the root in place when the root tag and
  `key` match, and replaces it wholesale (`from.replaceWith(toCloned)`) when they
  differ; `morph()` returns the detached old node in the wholesale case. A client
  root attribute is stripped by `patchAttributes` in place; a node-keyed WeakMap
  survives in place but breaks under replacement.
- **F-CI-2 (empirical).** The fresh component id must be linked to the anchor, and
  State updated, before the morph call, because morph's Alpine bridge and
  Alpine's re-init resolve `$state` through the id during the patch.
- **F-CI-3 (empirical).** The two layers compose on the byte-identical `citry.js`:
  old id removed plus new id added, one cleanup and one fire, while the anchor and
  epoch persist.
- **F-CI-4 (empirical, design-recommendation).** Component.css GC on
  last-instance-of-class must be deferred, or the faithful-id model's
  retire-before-fire ordering drops the sheet on every solo-instance re-render.
- **F-CI-5 (design-recommendation).** The removal reconciler (F9) is buildable as
  an additive layer keyed by component id and class, with no anchor knowledge; it
  is the deps-manager half of the two-layer composition.
- **F-CI-6 (design-recommendation).** The anchor needs no DOM representation for
  correctness; the component-id-to-anchor index is the tie. If a devtools marker
  is added (16.1), the re-stamped `data-canchor-<id>` attribute is the choice, not
  a node-keyed WeakMap.

## Sources

- Harness and evidence:
  `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/anchor-spike/`
  (`evidence-anchor.json` is the full captured log; quotes above are verbatim
  from it, with per-run random component ids). Run on 2026-07-08, macOS, headless
  Chromium 149.0.7827.55 via Playwright 1.61.0 from the repo venv. All seven
  scenarios pass across six consecutive runs.
- The real runtime under test:
  `packages/py/citry/citry/ext/dependencies/client/citry.js` (sha256
  `11458e9d228c172594ecbb8fe93683416322a6c73c6fcf7c21e74f90a558ee2c`).
- Morph behavior confirmed against
  `node_modules/@alpinejs/morph/dist/module.esm.js` 3.15.12 (`morph`, `patch`,
  `swapElements`, `patchAttributes`).
- Design under test: [`../events.md`](../events.md) 3.4, 4.2, 4.3, 4.4, 5.3, 5.4,
  5.5, 7.1, 7.2; the dependency manager it composes with,
  [`../dependencies.md`](../dependencies.md) 4, 7.4, 8.
- Prior spike this extends: [`spike-morph-alpine.md`](spike-morph-alpine.md)
  (pins, boot order F2, the Alpine bridge F3, focused-input survival F8, the
  removal-teardown gap F9, the morph hooks F10).
