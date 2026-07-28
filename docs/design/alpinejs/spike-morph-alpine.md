# WP6 spike report: morph and Alpine against the real citry.js

The morph and Alpine spike from the Events implementation plan
([`../events_plan.md`](../events_plan.md) WP6, gating WP15 to WP17), run
on 2026-07-07. A throwaway browser harness loaded the real client
runtime (`citry.js`), a pinned Alpine plus `@alpinejs/morph` bundle, and
hand-built manifest tags, then ran the nine scripted assertions from
[`../events.md`](../events.md) section 13 item 2.

**Result: all nine assertions pass.** The client model designed in
events.md 5.3 to 5.5 holds end to end against the shipped manifest
machinery. Section 13.2's failure consequence (redesign before
hardening) is not triggered. The findings below are corrections and
requirements for WP15/WP16, not model failures.

## Version pins (normative for WP15)

| Piece | Pin |
|---|---|
| `alpinejs` | **3.15.12** (exact) |
| `@alpinejs/morph` | **3.15.12** (exact) |
| `esbuild` | 0.28.1 |
| node / npm | v25.8.1 / 11.11.0 |
| Playwright / Chromium | 1.61.0 (repo venv) / 149.0.7827.55 |

The runtime under test was the real file: `public/citry.js` in the
harness is a byte-identical copy of
`packages/py/citry/citry/ext/dependencies/client/citry.js`
(sha256 `11458e9d228c172594ecbb8fe93683416322a6c73c6fcf7c21e74f90a558ee2c`),
re-copied on every run.

## What the harness is

Location (session-temporary, left in place for re-running):
`/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/wp6-spike/`

Re-run: `npm install && npm run build`, then
`/Users/mac/repos/citry/.venv/bin/python run_spike.py` (serves
`public/` on a local port, drives headless Chromium, prints the
evidence JSON that this report quotes, and writes it to
`evidence.json`). Two consecutive runs produced identical pass results.

Contents:

- `package.json` pinning the exact versions above; `npm install` took
  about 1 second and wrote `package-lock.json`.
- `src/harness.js`: a hand-rolled prototype of the events runtime
  pieces under test, bundled by esbuild into a classic (iife) script.
  It implements exactly the pinned design mechanics: the registry-held
  `Alpine.reactive` state keyed by instance id, the fixed-name
  `data-cid` marker with innermost-last resolution, the empty boundary
  scope entry via `addScopeToNode` plus the isolation truncation from
  [`../alpinejs/alpine-vuetify-audit.md`](../alpinejs/alpine-vuetify-audit.md)
  (`component.ts:165-170` of the audited snapshot), the design 5.3
  morph call (ignore marker, focused-value protection, pairwise
  per-root morph with range-replacement fallback), and the 5.5
  reconcile rule with a per-instance pending-writes queue.
- `src/gen.mjs` writes the static page and the pre-serialized
  replacement fragments. Manifest tags are hand-built to the exact
  shipped formats: `data-citry` per `emission.py:_build_manifest`
  (markLoaded/fetch/calls, every string base64, `js_data` variables as
  inline `registerComponentData` script descriptors, `css_data` as
  stylesheets targeting the `data-ccss-<hash>` root attribute), and
  `data-citry-events` per events.md 4.4 (instance 4-tuples plus a
  classes map, every string base64).
- Instance cases on one page: two `TodoCard` siblings (`s1`, `s2`), a
  nested pair (`out1` containing `in1`, with a user `x-data` on the
  outer root and an anonymous nested `x-data` as a control), a
  shared-root pair (`shr-p` and `shr-c` marking the same element,
  `data-cid="shr-p shr-c"`, innermost last), and a multi-root instance
  (`m1`, two sibling roots between anchor elements).
- `run_spike.py`: the Playwright driver (reusing the repo venv's
  Playwright), which scripts the render/state actions and captures all
  evidence.

What the harness deliberately does not cover, so the green here is not
over-read: the compiled `@c-*`/`:c-*` vocabulary (the two-way binding
is a stand-in listener on `data-bind-*` attributes doing exactly what
design 5.5 says the compiled binding does: write `$state.<field>`,
debounce, send), the `$loading`/`$error`/`$sendEvent`/`$onEvent`
magics (only `$state` and the marker-resolution mechanics were built),
and any real transport (render and state actions are applied by
script, with pre-serialized fragments standing in for responses). Those
are WP15 to WP17 scope; this spike proves the substrate they build on.

## Per-assertion results

Runtime health first: the full run produced **zero page errors and zero
console messages** (`"page_errors": [], "console": []`).

### 1. `$onComponent` re-fires exactly once per re-render, after teardown: PASS

The ordered fire/teardown log for `s1` (evidence numbers `n` are the
global sequence): initial fire at n=10, teardown at n=13, exactly one
re-fire at n=16, nothing after. `s2`'s initial fire (n=11) shows the
sibling untouched by `s1`'s re-render.

```json
[{"n": 10, "kind": "fire", "id": "s1", "data": {"apiUrl": "/api/v1"}},
 {"n": 11, "kind": "fire", "id": "s2", "data": {"apiUrl": "/api/v1"}},
 {"n": 13, "kind": "teardown", "id": "s1"},
 {"n": 16, "kind": "fire", "id": "s1", "data": {"apiUrl": "/api/v2"}}]
```

### 2. The re-fire receives the new `js_data` payload: PASS

The re-rendered fragment's manifest carried a fresh variables script
(`registerComponentData("TodoCard", "v2", {"apiUrl": "/api/v2"})`) and
a `calls` entry with the new hash. The re-fire's `ctx.data` is the new
payload, and `ctx.state` is the registry object (`"stateIsRegistry":
true` on every fire):

```json
{"s1_fires": [
  {"n": 10, "data": {"apiUrl": "/api/v1"}, "stateIsRegistry": true},
  {"n": 16, "data": {"apiUrl": "/api/v2"}, "stateIsRegistry": true}]}
```

### 3. New CSS variables take effect on the morphed roots; old ones inert: PASS

`s1`'s label computed color went `rgb(255, 0, 0)` to `rgb(0, 128, 0)`
after the morph swapped the root's hook attribute from
`data-ccss-cssv1` to `data-ccss-cssv2` and the fragment's manifest
loaded the new hashed stylesheet. The old stylesheet stays in the head
and stays inert on the morphed root (it still styles the untouched
sibling `s2`, which keeps `rgb(255, 0, 0)`). The root element itself is
the same DOM node through the morph.

```json
{"before": {"s1Color": "rgb(255, 0, 0)", "s1HasOldHook": true},
 "after":  {"s1Color": "rgb(0, 128, 0)", "s2Color": "rgb(255, 0, 0)",
            "s1HasOldHook": false, "s1HasNewHook": true,
            "oldSheetStillInHead": true, "s1RootIsSameElement": true}}
```

### 4. Assets dedupe: PASS

`comp-shared.js` (the TodoCard component JS, URL-served) is listed in
the initial manifest and again in both re-render fragments' manifests.
It was fetched once, evaluated once, and exists once in the DOM:

```json
{"dom": {"scriptTagCount": 1, "evalCount": 1},
 "network_requests_for_url": ["http://127.0.0.1:61280/comp-shared.js"]}
```

(The port is the run's ephemeral local server port; it differs across
runs, everything else in the evidence is stable.)

### 5. Focused two-way-bound input keeps value and caret through a debounced cycle: PASS

Scripted sequence: focus the input, type `sho`, wait for the debounced
send (300 ms, from the class descriptor's timing hint; the send carried
`{"query": "sho"}` and cleared the pending queue), type `es` (queuing a
new pending write, `query: "shoes"`), set the caret to position 2, then
apply the render response whose fragment input carried
`value="sho"`. After the morph:

```json
{"before": {"value": "shoes", "selStart": 2, "pending": {"query": "shoes"}},
 "after": {"value": "shoes", "selStart": 2, "selEnd": 2,
           "stillFocused": true, "sameElement": true, "valueAttr": "shoes",
           "echo": "sho", "stateQuery": "shoes",
           "keepLiveValueLog": [{"live": "shoes"}]}}
```

Value kept, caret kept at 2, focus kept, element identity kept; the
unfocused `.echo` span took the server text (`"sho"`), and the state
kept the pending local value per the reconcile rule.

### 6. A state action updates the registry with no DOM change: PASS

A state action updating an unbound field (`secret`) changed the
registry and nothing else; the whole stage's `innerHTML` compared equal
before and after, and no morph ran:

```json
{"domUnchanged": true, "morphCallsDelta": 0, "secret": "server-secret"}
```

(A state action on a bound field does change the DOM, through
reactivity alone; that path is assertion 7's second half.)

### 7. The Alpine scope survives the morph; reconcile rule honored: PASS

Before the render, a local write `$state.draft = "local-draft"` was
queued (pending, never sent). The render response's manifest carried
`draft: "server-draft"` and `label: "Card one v2"`. After the morph:
`$state` object identity intact (both the tracking proxy and the
underlying reactive object), the server won `label`, the pending local
write kept `draft`, and both DOM texts agree with the state:

```json
{"after_render": {"stateIdentity": true, "reactiveIdentity": true,
   "label": "Card one v2", "draft": "local-draft",
   "labelDom": "Card one v2", "draftDom": "local-draft",
   "reconcileLog": [{"id": "s1", "field": "draft",
                     "local": "local-draft", "server": "server-draft"}]},
 "reactive_propagation_no_morph": {"noteState": "reactive-note",
   "noteDom": "reactive-note", "morphCallsDelta": 0}}
```

The second half: a later state action on a bound field (`note`) reached
the DOM through Alpine reactivity with zero morph calls.

Note `draftDom: "local-draft"`: the fragment's HTML said
`server-draft`, yet the morphed DOM shows the kept local value. That is
the plugin's Alpine bridge at work, see finding F3.

### 8. Nested-instance isolation, and shared-root innermost resolution: PASS

All probes read from the live DOM after `Alpine.start()`:

```json
{"outerProbe": "string", "nestedProbe": "string", "innerProbe": "undefined",
 "outerState": "outer", "innerState": "inner", "sharedState": "child",
 "outerStackKeys": [["outerSecret"], []], "innerStackKeys": [[]],
 "shrFires": [
   {"cls": "ShrParent", "id": "shr-p", "owner": "parent", "stateIsRegistry": true},
   {"cls": "ShrChild",  "id": "shr-c", "owner": "child",  "stateIsRegistry": true}]}
```

Reading: the outer root's own `x-data` (`outerSecret`) is visible
inside the outer component (`"string"`) and inside an anonymous nested
`x-data` (`"string"`, Alpine-native nesting preserved), but not inside
the nested citry instance (`"undefined"`, the truncation cut
inheritance). `$state` resolves per marker: `outer` in the outer,
`inner` in the inner. On the shared root, the expression-level `$state`
resolves to the child (innermost id last in `data-cid`), while the
parent keeps full access through its `$onComponent` payload (`owner:
"parent"`, same registry object). The scope stacks confirm the design's
no-pollution claim: the outer root's stack is exactly
`[the user's x-data (keys: outerSecret), the empty boundary (no keys)]`.

### 9. Multi-root pairwise morph; changed root count falls back to range replacement: PASS

Same root count (2 to 2): two morph calls, both root elements kept
their DOM identity, content updated in place. Changed count (2 to 3):
zero morph calls, the whole root range replaced in position (old roots
disconnected, three new roots sitting between the same anchor
elements), the registry state object identity survived, and the fresh
manifest re-attached boundary scopes on the new roots (the `x-text`
probe in the replaced list renders `multi` again):

```json
{"pairwise_v2": {"morphCallsDelta": 2, "sameFirstRoot": true,
   "sameSecondRoot": true, "head": "Multi head v2", "item": "alpha v2"},
 "range_replace_v3": {"morphCallsDelta": 0, "count": 3,
   "oldRootsDisconnected": true, "prevAnchor": "m-before",
   "nextAnchor": "m-after", "head": "Multi head v3",
   "foot": "Multi foot new", "owner": "multi",
   "stateIdentityKept": true, "newRootsHaveBoundary": true,
   "rangeLog": [{"id": "m1", "from": 2, "to": 3}]}}
```

## Findings and surprises (normative reading for WP15/WP16)

**F1. The design's pinned import form binds the wrong object.** The
published `@alpinejs/morph` 3.15.12 exports are, verbatim from
`dist/module.esm.js:390-393`:

```js
export {
  module_default as default,
  src_default as morph
};
```

`src_default` is the plugin installer
(`function (Alpine) { Alpine.morph = morph; Alpine.morphBetween = morphBetween; }`),
so `import { morph } from "@alpinejs/morph"` (the form in events.md 5.3's
pinned block) compiles fine and then treats the root element as an
Alpine instance at call time. The raw `morph(from, toHtml, options)`
function is reachable only as `Alpine.morph` after
`Alpine.plugin(...)`. The harness proved the two imports are the same
object at runtime (`"namedExportIsPlugin": true`). WP15 must register
the plugin and call `Alpine.morph`; events.md 5.3's code block needs
that one-line correction when it is next edited.

**F2. Boot order: manifests are processed during parse, so the runtime
must be ready at evaluation time.** Two failures on the way to green
pinned this:

- Loading the harness as a page module (`<script type="module">`) lost
  the race outright: Chromium fired DOMContentLoaded, and with it the
  first component callbacks, before the module's import graph finished
  loading.
- Even a classic script booting everything on DOMContentLoaded is too
  late: citry.js's MutationObserver processes manifest tags **as the
  parser inserts them** (parser insertions are mutations, delivered at
  microtask checkpoints during parse). In the first classic-script run,
  the shared-root instances' callbacks fired mid-parse, before any
  DOMContentLoaded listener, and their payloads were decorated with
  `state: null`.

The working shape, which WP15 should adopt: the runtime is a classic
script loaded right after citry.js; it registers its events-manifest
observer and the `decorateContext` decorator at evaluation time; only
`Alpine.start()` waits for DOMContentLoaded (the Livewire playbook).
Two companion rules make it order-proof:

- **The serializer emits the `data-citry-events` tag before the
  `data-citry` tag** (WP10). Then whenever a call can fire, the events
  tag is already parsed.
- **The decorator drains unprocessed events manifests before
  decorating** (a `querySelectorAll` over the manifest selector with a
  processed-guard), covering the window where the tag is in the DOM but
  its mutation record has not reached the runtime's observer yet.

WP15's build note "ESM so nothing runs early" should be read as "keep
`Alpine.start()` out of module evaluation", not as "ship a page
module": the served artifact must be a classic script (esbuild `iife`
output), or callbacks will fire undecorated.

**F3. The Alpine-state bridge in morph is real and does more than
advertised.** For every element pair, `patch` calls
`window.Alpine.cloneNode(from, to)` (`module.esm.js:57-58`), and
Alpine's `cloneNode` (`alpinejs dist/module.esm.js:1350`) initializes
the incoming tree in cloning mode (directives evaluated once, no
reactive subscriptions). Because the citry magics resolve through
`closest("[data-cid]")` plus the registry, they work even on the
detached incoming tree, so incoming bound text re-renders from live
client state during the patch. Observed effect: assertion 7's `draft`
span shows `local-draft` after a morph whose fragment HTML said
`server-draft`. The pending-local-write display divergence (server HTML
overwriting locally-written bound text until the next reactive trigger)
simply does not happen under `@alpinejs/morph`. This is precisely the
machinery the idiomorph fallback lacks.

**F4. The isolation truncation is two lines here, simpler than the
audited original.** The audit's `isolateInstance` ran inside Alpine's
`x-data` init and needed the `makeInstance` proxy rebuild afterwards.
Attaching at manifest time, before `Alpine.start()`, no proxy exists
yet, so the whole mechanism is:

```js
Alpine.addScopeToNode(root, {});
root._x_dataStack = root._x_dataStack.slice(0, 1);
```

Both touch pinned-version internals (`addScopeToNode` is on the Alpine
object but undocumented; `_x_dataStack` is private). A user `x-data` on
the instance root itself then prepends its own layer and inherits
nothing from above, which is exactly the designed coexistence
(assertion 8's `outerStackKeys`).

**F5. `addScopeToNode` alone does not make a subtree Alpine-active.**
`Alpine.start()` initializes only trees under registered root selectors
(`[x-data]` and `[x-init]` by default). A citry root without `x-data`
would never be walked, boundary entry or not. The harness registers
`Alpine.addRootSelector(() => "[data-cid]")` (a public API, the same
pattern Livewire uses for `[wire\:id]`), and that is what activates
scopeless instance roots. Design 5.5's "the boundary entry guarantees
the subtree is Alpine-active" holds only together with this root
selector registration; WP15 needs both lines.

**F6. `Object.keys($data)` is empty for every Alpine scope, so write
the WP15 purity test against the stack, not the merged proxy.**
Alpine's `mergeProxyTrap` implements `ownKeys` but not
`getOwnPropertyDescriptor`, so `Object.keys` filters every reported key
out (the descriptor lookup falls through to the proxy target). The
harness's citry-scoped probe and a plain-Alpine control both render
`""`. The design claim "citry adds no enumerable keys to any user scope
object" is true and was verified directly on the scope stack objects
instead: `[["outerSecret"], []]`.

**F7. morph permanently monkey-patches
`Element.prototype.setAttribute`.** On the first `morph()` call
(`module.esm.js:3,355-371`), to tolerate `@`-prefixed attribute names.
Page-wide, kept forever. No observed harm; worth knowing when
debugging attribute behavior on a page that has morphed once.

**F8. morph never writes the input `value` property; the designed
protection still earns its keep.** `patchAttributes`
(`module.esm.js:95-123`) syncs attributes only (with special cases for
`dialog[open]`, `_x_transitioning`, `_x_isShown`); a user-modified
(dirty) input keeps its live value property even when the `value`
attribute changes. The focused-value protection in the `updating` hook
matters for what remains: it keeps the value **attribute** (the
form-reset default) equal to the live value, and it guards the
`swapElements` path (tag or `key` mismatch replaces the node wholesale,
`module.esm.js:76-88`, and a fresh node would take its value from the
attribute). Caret survival needed no extra work in the patched-in-place
path (selection 2,2 kept).

**F9. Teardown-on-removal needs a hook citry.js does not expose.**
Design 5.3's `removed(el) { runInstanceTeardowns(el); }` cannot be
implemented against the current runtime surface: the cleanup store
inside citry.js is private, and cleanups only run when a **new call**
arrives for the same instance (`runCleanups` inside `flushCalls`). An
instance that disappears in a morph (or in the range-replacement
fallback) never gets a new call, so its last cleanups never run. The
spike's `removed` hook only logs. WP15/WP16 needs one of: a public
"run this instance's cleanups now" entry point on the manager, or
events-runtime-held teardown tracking. This is the one place the
existing machinery fights the design, and it is an additive change,
not a redesign.

**F10. The `updating` hook's real signature has a sixth argument.**
`shouldSkipChildren` (`module.esm.js:55,295-299`) invokes it as
`updating(from, to, childrenOnly, skip, skipChildren, skipUntil)`. The
design block's five parameters are correct in name and order;
`skipUntil` (a predicate-based section skipper) exists beyond them.
`Alpine.morphBetween` is confirmed present in 3.15.12
(`module.esm.js:13`), so the recorded multi-root upgrade path is real.
Child matching confirmed keyed on the plain `key` attribute
(`defaultGetKey`, `module.esm.js:35`).

**F11. Local `$state` writes reach the DOM asynchronously.** A DOM read
in the same task as the write still sees the old text (Alpine
schedules effects); it settles by the next tick. Only relevant to test
authors; the harness's evidence (`draftDomAfterLocalWrite:
"initial-draft"` in the same task, `"local-draft"` afterwards) shows
both sides.

## Verdict: keep `@alpinejs/morph`; the idiomorph fallback stays on the shelf

Design 5.3 records what falling back to idiomorph would cost: the
ignore marker and focused values are covered natively
(`beforeNodeMorphed`, `ignoreActiveValue`), but there is no Alpine
bridge, so scope survival would be re-implemented by hand. The spike
turns that abstract trade concrete:

- All nine assertions pass on `@alpinejs/morph` 3.15.12 as pinned, with
  zero console errors, against the real citry.js.
- The bridge is not just "scope survival". `cloneNode`'s re-initialization
  of incoming nodes kept bound DOM text consistent with client state
  (pending local writes included) through every morph, for free (F3).
  Under idiomorph, the runtime would need its own post-morph pass to
  re-render every bound node whose state diverges from the server HTML,
  on top of hand-rolling stack survival for replaced nodes.
- The costs found on the Alpine side are small and now pinned: the
  named-export trap (F1), the global `setAttribute` patch (F7), and a
  private-API surface (`addScopeToNode`, `_x_dataStack`, `cloneNode`
  behavior) that is version-coupled and must stay exactly pinned, with
  the audit's canary-test advice carried into WP15's test list.

Nothing in this spike gives idiomorph an advantage on any assertion.
The fallback remains recorded in design 5.3 and would trigger only if a
future Alpine upgrade breaks the pinned private behavior.

## Acquisition verdict for WP15: confirmed, with one adjustment

The pinned acquisition (npm install into a `package.json` with exact
pins, esbuild as the only build tool, output committed) worked without
friction: install resolved 6 packages in about 1 second and produced a
lockfile; esbuild bundled both an ESM artifact (114.2 KB unminified)
and the iife harness bundle (132.4 KB unminified) in single-digit
milliseconds each; no other tooling was needed. Two things for WP15 to
inherit:

- **Adjustment (from F2): the served runtime artifact must be a classic
  script**, i.e. esbuild `--format=iife`, evaluated in the page right
  after (or bundled with) citry.js, registering observers and the
  decorator at evaluation time and deferring only `Alpine.start()` to
  DOMContentLoaded. A `<script type="module">` delivery loses the
  manifest race.
- Import the plugin default and use `Alpine.morph` (F1); do not import
  the named `morph` binding.

## Sources

- Harness and evidence:
  `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/wp6-spike/`
  (`evidence.json` is the full captured log; quotes above are verbatim
  from it). Run on 2026-07-07, macOS, headless Chromium 149.0.7827.55
  via Playwright 1.61.0 from the repo venv.
- `alpinejs@3.15.12` and `@alpinejs/morph@3.15.12` from the npm
  registry; line references are into the installed
  `node_modules/@alpinejs/morph/dist/module.esm.js` and
  `node_modules/alpinejs/dist/module.esm.js`.
- The real runtime under test:
  `packages/py/citry/citry/ext/dependencies/client/citry.js` (sha256
  `11458e9d228c172594ecbb8fe93683416322a6c73c6fcf7c21e74f90a558ee2c`).
- Manifest formats mirrored from
  `packages/py/citry/citry/ext/dependencies/emission.py`
  (`_build_manifest`) and `scripts.py` (`registerComponentData` vars
  scripts, `data-ccss-<hash>` stylesheets, `$onComponent` expansion).
- Design under test: [`../events.md`](../events.md) 4.4, 5.3, 5.4, 5.5,
  13.2; plan entry [`../events_plan.md`](../events_plan.md) WP6, WP15.
- Prior research applied:
  [`../alpinejs/alpine-ecosystem-2026.md`](../alpinejs/alpine-ecosystem-2026.md)
  (pins, Livewire boot playbook),
  [`../alpinejs/alpine-vuetify-audit.md`](../alpinejs/alpine-vuetify-audit.md)
  (the isolation truncation).
