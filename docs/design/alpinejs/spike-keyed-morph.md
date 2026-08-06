# Keyed-morph spike: key scoping, the preservation matrix, and the per-call key callback

An empirical spike answering three questions about how `@alpinejs/morph`
matches elements by key, run on 2026-07-16 against the real pinned Alpine
3.15.12 plus `@alpinejs/morph` 3.15.12 build in headless Chromium. It picks
between two designed forms for the key attribute that keyed anchor linking
(the option C design in
[`analysis-nested-anchor-continuity.md`](../events_research/analysis-nested-anchor-continuity.md))
would emit on child instance roots:

- the **class-id-scoped form**: the emitted key is the component class id
  plus the author's key value (for example `TodoItem:5`), a value that is
  stable across renders and needs no runtime help to compare;
- the **id-to-anchor normalized form**: the emitted key embeds the
  per-render component id, and every `Alpine.morph` call gets a `key`
  callback that maps old and new component ids to one stable anchor token
  before comparison (the anchor is the client-internal stable identity of
  one interactive DOM position, from
  [`spike-component-identity.md`](spike-component-identity.md)).

**Result: morph's key matching is sibling-window scoped, so the design
should pin the class-id-scoped form.** A sibling window is the set of
direct children of one already-matched parent pair; that set is the only
place morph ever compares keys, so a key can never pair across depths or
across parents, and the self-nesting collision that motivated the
normalized form cannot arise. The per-call callback of the normalized form
is proven to work (Q3), so it stays available as a recorded fallback, but
it is not needed for v1. All eleven scenarios produced zero page errors and
zero console messages, and three consecutive runs were identical on every
non-timing field (`deterministic_across_runs: true`).

Every claim below marked (empirical) is read from the harness evidence;
(source) points into the shipped plugin file
`node_modules/@alpinejs/morph/dist/module.esm.js`, a single 394-line file.

## Version pins

| Piece | Pin |
|---|---|
| `alpinejs` | 3.15.12 (exact, `Alpine.version` read at runtime) |
| `@alpinejs/morph` | 3.15.12 (exact) |
| esbuild | 0.28.1 |
| node | v25.8.1 |
| Playwright / Chromium | 1.61.0 (repo venv) / 149.0.7827.55 (headless) |

The bytes under test are the repo's own installed packages: the harness
bundle imports `packages/js/citry-client/node_modules/alpinejs/dist/module.esm.js`
and `.../@alpinejs/morph/dist/module.esm.js` by absolute path, the same
files the shipped `citry-events.js` bundle is built from
(`citry-events.ts:77-78`, plugin registered at `citry-events.ts:352`; the
transport work package makes the actual morph calls). Every morph in the
harness passes `lookahead: false`, which is both the plugin default
(`module.esm.js:40`) and the pinned runtime setting, matching Livewire;
the lookahead flag only affects unkeyed pairing (an `isEqualNode` scan,
`module.esm.js:200`), so the keyed conclusions do not depend on it.

## What the harness is

Location (session-temporary, throwaway, left runnable):
`/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/keyed-morph-spike/`

Re-run: build the bundle with the repo's own esbuild
(`packages/js/citry-client/node_modules/.bin/esbuild src/entry.js --bundle
--format=iife --platform=browser --target=es2020 --outfile=public/alpine-bundle.js`),
then `/Users/mac/repos/citry/.venv/bin/python run_keyed.py` (serves
`public/`, drives headless Chromium three times, prints the evidence and
writes `evidence-keyed-morph.json`).

Three pieces:

- `src/entry.js`, bundled to `public/alpine-bundle.js`: the pinned Alpine
  and morph, booted the way the runtime boots (plugin registered at
  evaluation time, `Alpine.start()` deferred to DOMContentLoaded, WP6
  finding F2), so morph's Alpine bridge runs during every patch exactly as
  it will in production.
- `public/scenarios.js`: the eleven scenarios. Each mounts its own DOM,
  mutates live node state (typed values, checkedness, focus, selection,
  scroll, an opened `details`, a loaded and stamped iframe, a playing
  src-backed video generated in-page by MediaRecorder), morphs, and
  returns a JSON evidence object. Old nodes are tagged with JS expandos
  and saved references so node identity and node travel are measured
  directly, not inferred. Fragment HTML is whitespace-compact (no text
  nodes between siblings) so text-node pairing never confounds the keyed
  observations.
- `run_keyed.py`: the Playwright driver (repo venv), which also collects
  console output and page errors and checks the three runs agree on every
  field except raw timing floats.

What the harness deliberately does not cover: no citry runtime, manifests,
or anchors are loaded, because the questions are purely about the morph
library's matching behavior. How the runtime composes with morph (link
before morph, scope survival, teardown) is already proven by the two
sibling spikes.

## Scenario table

| # | Scenario | Question it answers |
|---|---|---|
| a1 | Same key (`TodoItem:5`) at two depths, both sides, markers swapped | Q1a: do same-key nodes at different depths ever cross-pair? (the self-nesting collision shape) |
| a2 | Key exists only shallow in old, only three levels deep in new | Q1a: does the shallow old node travel to the deep new position? |
| a3 | Reverse of a2 (deep old, shallow new) | Q1a mirror |
| b | Keyed nodes swapped between two distant sibling groups (different parents), plus an in-window control | Q1b: does the value follow the key across parents? |
| c0 | Same-parent swap with no keys | Q1c baseline: what unkeyed pairing does |
| c | Same-parent keyed swap `[C,A,B] -> [C,B,A]` with the full state matrix | Q1c and the whole of Q2 |
| c2 | Keyed swap ahead of a logically-stationary trailing keyed row, with an iframe on the trailing row | Q2 rider: who pays the move cost |
| q1-data | a1/b/c core probes rerun through a `key` callback reading `data-ckey` | Q1: scoping is a property of the walk, not of the default callback |
| q3 | Two consecutive morphs, keys embed changing component ids, per-call normalizing closures | Q3: the id-to-anchor normalized form works |
| q3-ctl-root | Same renders, default key callback, keyed root | Q3 control: what raw id-bearing keys do at the root |
| q3-ctl-child | Same renders, default key callback, unkeyed root, keyed child | Q3 control: what raw id-bearing keys do among siblings |

## Q1: key matching is sibling-window scoped

### a1, the self-nesting collision shape (empirical): no cross-pairing

The same key at two depths, on both sides, with marker attributes swapped
between the depths so a cross-depth move would be rewarded if the
algorithm did one:

```json
{"shallow_same_node": true, "deep_same_node": true,
 "shallow_tag": "old-shallow", "deep_tag": "old-deep",
 "shallow_value": "SHALLOW-VALUE", "deep_value": "DEEP-VALUE",
 "shallow_marker_synced": "Y", "deep_marker_synced": "X"}
```

Each depth kept its own node (expando tags intact), each input kept its
own typed value, and the markers were updated in place as plain attribute
syncs. Nothing crossed depths.

### a2 and a3, the key moving between depths (empirical): no teleport, values die

Key only on the shallow node in the old DOM, only on a node three levels
deeper in the new fragment:

```json
{"shallow_window_child_count": 0, "shallow_old_node_still_connected": false,
 "deep_node_key": "dup", "deep_value_after": "",
 "deep_got_shallow_node": false, "deep_is_fresh_node": true}
```

The shallow keyed node was simply removed with its window, and the deep
keyed position is a brand-new node with an empty input. The mirror run
(a3) is symmetric: `"shallow_got_deep_node": false`, both old nodes
disconnected, both values gone. A key appearing at, or disappearing from,
a node also kills that node in place: the old/new pair differs in key, so
`patch` replaces it wholesale rather than patching it
(`differentElementNamesTypesOrKeys`, `module.esm.js:76-78`).

### b, the cross-parent swap (empirical): the value never follows

`k1` moves from group A to group B, `k3` the other way, `k2` stays inside
group A as the in-window control:

```json
{"k1_in_groupB": true, "k1_value_followed": "", "k1_is_old_node": false,
 "k1_old_node_connected": false,
 "k3_in_groupA": true, "k3_value_followed": "", "k3_is_old_node": false,
 "k3_old_node_connected": false,
 "k2_control_same_node": true, "k2_control_value": "V2"}
```

Both travelers are fresh clones with empty inputs; both old nodes are
gone; the control that stayed within its window kept its node and its
typed value. This also empirically confirms the divergence the option C
analysis predicted between morph's DOM pairing (per sibling window) and
the anchor matcher (region-wide): a keyed child moving between sibling
groups can have its anchor payload carried by the matcher while the DOM
state dies with the node.

### c0 and c, the same-parent swap (empirical): the value follows the key

Unkeyed baseline first: after swapping two unkeyed rows, position 1 shows
item B's content with item A's typed value
(`{"pos1_item": "B", "pos1_value": "VA", ...}`), the classic
state-sticks-to-position bug that keys exist to fix. With keys, the swap
moves the real old nodes and everything property-held travels (full
matrix in Q2 below):

```json
{"order_after": ["C", "B", "A"],
 "node_identity": {"C_same": true, "A_same": true, "B_same": true},
 "input_value": {"A": "typed-A", "B": "typed-B", "C_control": "typed-C"}}
```

### The rerun through a data-attribute callback (empirical): same scoping

All three core probes rerun with `key: (el) => el.getAttribute("data-ckey")`
and no plain `key` attribute anywhere: depths stay independent
(`"shallow_value": "SHALLOW-VALUE", "deep_value": "DEEP-VALUE"`), the
cross-parent value still dies (`"k1_value_followed": ""`), the same-parent
swap still travels (`"A_value_followed": "VA", "B_same_node": true`). The
window scoping is a property of the walk, not of the default callback.

### Why, from the source

`patchChildren(from, to)` builds its key index from the direct children of
the current from-parent only (`let fromKeys = context.keyToMap(from.children)`,
`module.esm.js:125`) and keeps its stash of displaced keyed nodes in a
local variable of the same walk (`fromKeyHoldovers`, `:126`). Recursion
into a matched pair starts a brand-new walk with a brand-new index
(`:72-74`). There is no subtree-wide or document-wide key registry
anywhere in the plugin, so keys at different depths or under different
parents are never in one comparison set.

## Q2: the preservation matrix for the same-parent keyed swap

Layout `[C, A, B] -> [C, B, A]`. C sits before the reorder point and is
the untouched control. The two movers take the algorithm's two distinct
paths: B is pulled into place by `replaceWith` (`module.esm.js:232`), A is
displaced into the holdover stash and re-appended at the end
(`:231`, `:146-151`). The mutation records show exactly that choreography
(empirical): `[{"removed": ["B"], "added": []}, {"removed": ["A"], "added":
["B"]}, {"removed": [], "added": ["A"]}]`. Both paths are a real DOM detach
plus reinsert, and the matrix came out identical for both:

| State | Moved node (A or B) | Unmoved control (C) | Verdict |
|---|---|---|---|
| Input value (property) | `typed-A` / `typed-B` kept | `typed-C` kept | travels |
| Checkbox checkedness (property) | `true` kept | `true` kept | travels |
| Selection range (on the blurred input) | `{start: 2, end: 5}` kept | n/a | travels |
| Focus | lost, `activeElement` fell to `BODY` | n/a (focus was on A) | lost on move |
| Scroll position of an inner scrollable div | `0` (was 120 / 77) | `55` kept | lost on move |
| `details` open (attribute-reflected) | closed | closed | lost either way, see below |
| iframe document | reloaded: post-morph `load` fired once, window stamp gone | not reloaded: zero loads, stamp intact | reloads on move |
| Video (src-backed blob webm) | reloaded: `{"loadstart": 1, "emptied": 1, "pause": 0}`, `currentTime` 0.285 -> 0, playback stopped, element identity and `src` kept | n/a | reloads on move |

```json
{"scroll": {"A": 0, "B": 0, "C_control": 55},
 "focus": {"before_was_inA": true, "after_active_element": "BODY",
           "moved_node_lost_focus": true},
 "iframe": {"A_load_count_after_morph": 1, "A_stamp": null,
            "A_same_element": true,
            "C_control_load_count": 0, "C_control_stamp": "stamp-1"},
 "video": {"same_element": true, "src_preserved": true,
           "raw_ct_before": 0.285201, "raw_ct_immediately_after": 0,
           "paused_after_wait": true,
           "events_after_morph": {"loadstart": 1, "emptied": 1, "pause": 0}}}
```

Three readings, all empirical:

- **What travels is what lives on the node object.** Value, checkedness,
  and the selection range are element properties; the moved element is the
  same object, so they ride along. What resets is what the browser ties to
  document presence: focus, layout scroll state, an iframe's document, a
  media element's loaded resource (the `emptied` plus `loadstart` pair
  shows the video re-ran its resource load on reinsertion, the media
  analogue of the iframe reload, not a mere pause). One caveat on the
  video cell: the in-page MediaRecorder blob carries no duration metadata,
  so the exact post-reload position behavior of a normal served file may
  differ; the reload events are the mechanism either way.
- **`details` open state is not a move cost.** The unmoved control lost it
  too, because the incoming HTML carried no `open` attribute and
  `patchAttributes` faithfully removes attributes absent from the new
  fragment (`module.esm.js:104-115`). Client-toggled attribute-reflected
  state survives a morph only if the server echoes it.
- **The move cost cascades past the reordered pair** (scenario c2). In
  `[A, B, C] -> [B, A, C]` the logically-stationary trailing row C was
  also detached and reinserted (mutation records
  `[{"removed": ["B"], "added": []}, {"removed": ["A"], "added": ["B"]},
  {"removed": ["C"], "added": ["A"]}, {"removed": [], "added": ["C"]}]`),
  and its iframe
  reloaded (`"C_iframe_reloads": 1`, stamp gone) even though its value and
  node identity were kept. Only rows sitting before the first out-of-order
  position stay physically untouched (scenario c's C row, zero reloads).

## Q3: the key callback is contextual per call, and normalization works

Each `Alpine.morph` invocation builds a fresh context from its own options
object (`createMorphContext(options)`, `module.esm.js:2-4`, `:34-47`), so
the `key` option is a per-call closure with whatever state the caller
gives it. The harness simulates the runtime's component-id-to-anchor
index: keys are emitted as `<componentId>` on the region root and
`<componentId>::<userKey>` on keyed children, and each morph passes a
closure that maps the ids alive across that render to one anchor token
(`cid-a1` and `cid-b2` both to `anchor-7` on the first morph; `cid-b2` and
`cid-c3` on the second; the second closure never knew `cid-a1` and the
first never knew `cid-c3`).

Morph 1 (ids `cid-a1 -> cid-b2`, items reordered) and morph 2
(`cid-b2 -> cid-c3`, order restored), evidence verbatim:

```json
{"after_morph_1": {
   "region_same_node": true, "region_cid_synced": "cid-b2",
   "region_key_attr_synced": "cid-b2",
   "draft_value": "draft-typed", "draft_same_node": true,
   "item_values_in_dom_order": ["L2-typed", "L1-typed"],
   "it1_same_node": true, "it2_same_node": true,
   "child_keys_synced": [null, "cid-b2::draft", "cid-b2::item-2", "cid-b2::item-1"],
   "keyfn_calls": 38,
   "raw_keys_seen": ["cid-a1", "cid-a1::draft", "cid-a1::item-1", "cid-a1::item-2",
                     "cid-b2", "cid-b2::draft", "cid-b2::item-1", "cid-b2::item-2"]},
 "after_morph_2": {
   "region_same_node": true, "region_cid_synced": "cid-c3",
   "draft_value": "draft-typed", "draft_same_node": true,
   "item_values_in_dom_order": ["L1-typed", "L2-typed"],
   "it1_same_node": true, "it2_same_node": true}}
```

Everything the normalized form promises holds (empirical): the region and
every keyed child keep node identity and typed values through two renders
and three id generations; a reorder composed with an id change still
travels the values; and because the callback only affects comparison while
`patchAttributes` still syncs the real attributes, the DOM's `key` and
`data-cid` always show the fresh server id afterward, so the faithful-id
surface costs nothing. The callback is consulted for both sides of every
comparison (`raw_keys_seen` contains both id generations) and participates
in the root-level same-node decision as well (`:48-51`, `:76-78`).

The controls show what raw id-bearing keys do without normalization
(empirical): with the region root keyed, the whole region is
wholesale-swapped and every value dies
(`{"region_is_old_node": false, "old_root_connected": false,
"draft_value_after": ""}`); with only children keyed, each keyed child is
replaced by a fresh clone (`{"draft_same_node": false,
"draft_value_after": ""}`). Raw per-render ids in keys are strictly worse
than no keys at all.

One cost note (empirical): the callback ran 38 times for a region of four
children (morph consults it repeatedly per node: the window index, the
walk, and every `patch` entry), so a production closure must be a cheap
pure lookup, never a DOM walk.

## Findings

- **F-KM-1 (empirical, source).** Morph key matching is sibling-window
  scoped: keys are compared only among the direct children of one
  already-matched parent pair (`fromKeys = keyToMap(from.children)`,
  `module.esm.js:125`; per-walk holdovers, `:126`; fresh walk per matched
  pair, `:72-74`). A key at two depths never cross-pairs (a1); a key
  moving between depths (a2/a3) or between parents (b) yields a fresh
  clone at the new place and the old node is discarded; the value never
  follows. There is no subtree-global key registry.
- **F-KM-2 (empirical).** Within one sibling window, a keyed reorder moves
  the real old nodes (the `replaceWith` pull, `module.esm.js:232`, and the
  holdover re-append, `:146-151`): node identity, input value,
  checkedness, and selection range travel with the key. Unkeyed siblings
  pair positionally and state sticks to the position (c0).
- **F-KM-3 (empirical).** The keyed move costs, on the moved node: scroll
  positions reset, a focused control blurs (`activeElement` falls to
  `BODY`; its selection range values are still retained), an iframe in the
  moved subtree reloads its document, and a src-backed video re-runs its
  media load (`emptied` + `loadstart`, `currentTime` collapses to 0,
  playback stops). An unmoved sibling in the same morph keeps scroll and
  its iframe document.
- **F-KM-4 (empirical).** The move cost cascades: a keyed swap detaches
  and reinserts every keyed sibling from the first out-of-order position
  to the end of the window, including rows whose logical position did not
  change (c2: the trailing row's iframe reloaded). Rows before the reorder
  point are untouched.
- **F-KM-5 (empirical).** Attribute-reflected client state (`details`
  open) does not survive any morph whose incoming HTML lacks the
  attribute, moved or not; `patchAttributes` is faithful to the fragment.
  Recorded so the matrix is honest: it is a morph property, not a keying
  cost, and the fix is server-side echoing.
- **F-KM-6 (empirical, source).** The `key` option is contextual per call
  (`createMorphContext(options)` per invocation, `module.esm.js:34-47`),
  is consulted for both the live and the incoming element of every
  comparison, and participates in the root-level swap decision
  (`:76-78`). A per-call closure normalizing component ids to anchor
  tokens keeps node identity and typed values across consecutive renders
  with fresh ids, while attribute sync leaves the fresh server id visible
  in the DOM.
- **F-KM-7 (empirical).** Un-normalized per-render ids inside key
  attributes are actively destructive: a keyed root wholesale-swaps the
  whole region on every render, keyed children clone fresh. If component
  ids ever ride key attributes, normalization is mandatory.
- **F-KM-8 (empirical).** The key callback is hot: 38 invocations for a
  four-child region in one morph. Keep it a pure map lookup.

## Verdict: pin the class-id-scoped key form

The design should pin the **class-id-scoped form** for keyed anchor
linking: the emitted morph key on a child instance root is the component
class id plus the author's `c-key` value, a value that is stable across
renders and compared raw by morph's default callback, with no `key` option
passed at all. The decision rests on F-KM-1: matching is sibling-window
scoped, so the self-nesting collision that would force normalization (the
same class-scoped key on an outer instance and on a same-class instance
nested deeper) cannot arise, because keys at different depths are never in
one comparison set. The class prefix also makes morph's DOM pairing agree
with the region-wide anchor matcher in the one divergence the option C
analysis flagged (same tag and key on two different classes): with the
class inside the key string, morph refuses exactly the pairs the matcher
refuses. Two rules ride the pin: emitted keys must never embed per-render
component ids (F-KM-7 makes that worse than no keys), and duplicate keys
within one sibling window remain the author's responsibility, documented
the same way as Vue's `:key` guidance. The id-to-anchor normalized form is
empirically proven feasible (F-KM-6: a per-call closure over the
component-id-to-anchor index, both sides normalized, values survive id
churn) and is the recorded fallback if a future mechanism ever requires
ids inside keys; it is not needed for v1. Q2's matrix sets the user-facing
expectation for docs: a keyed move preserves form state (value,
checkedness, selection) but resets focus, scroll, iframes, and media
inside every physically-moved row, and the move set extends from the first
out-of-order sibling to the end of the window (F-KM-4), so reorder-prone
keyed lists should not wrap heavy embedded content lightly.

## Sources

- Harness and evidence (throwaway, session-temporary):
  `/private/tmp/claude-501/-Users-mac-repos-citry/73f703cb-6307-4ae1-9c01-a5061174cbc5/scratchpad/keyed-morph-spike/`
  (`evidence-keyed-morph.json`; quotes above are verbatim from run 1 of 3;
  the three runs agree on every non-timing field). Run on 2026-07-16,
  macOS, headless Chromium 149.0.7827.55 via Playwright 1.61.0 from the
  repo venv.
- The plugin under test:
  `packages/js/citry-client/node_modules/@alpinejs/morph/dist/module.esm.js`
  3.15.12 (line references throughout), imported by absolute path into the
  harness bundle; Alpine 3.15.12 alongside it.
- How the runtime holds morph today:
  `packages/js/citry-client/src/citry-events.ts:72-78` (plugin import),
  `:352` (registration); the transport work package makes the calls.
- Design under test: [`../events.md`](../events.md) 5.3 (the morph call,
  the "Keys are user-authored" rule, `c-key`) and 5.5 (the anchor, the
  component-id-to-anchor index);
  [`analysis-nested-anchor-continuity.md`](../events_research/analysis-nested-anchor-continuity.md)
  option C (keyed linking, the key-emission open mechanic, the
  matcher-versus-morph divergence note).
- Prior spikes this extends:
  [`spike-morph-alpine.md`](spike-morph-alpine.md) (pins, boot order F2,
  key matching on the plain `key` attribute F10),
  [`spike-component-identity.md`](spike-component-identity.md) (the
  two-identity model, link-before-morph F-CI-2).
