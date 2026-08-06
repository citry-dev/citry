# Rootless lifecycle spike: comment-owned logical instances

An empirical preimplementation spike for WP23, run on 2026-07-19 against the
repo's pinned Alpine 3.15.12 and morph 3.15.12 in headless Chromium, Firefox,
and WebKit. It asks whether a client-active Citry component whose current
output is text or empty can initialize, receive props, morph, poll, and clean
up without adding a wrapper element.

**Verdict: the mechanism is feasible, with load-bearing Citry-owned identity,
morph, and lifetime adapters plus a preserved-comments deployment
requirement.** A logical instance
can be represented by an ordered start/end comment pair, expose one stable
`ctx.els` array whose current value is `[]`, and own Alpine effects, reactive
scope, timers, and cleanup independently of an Element. Context-sensitive
morphing requires `Range.createContextualFragment()` plus a parent-shaped
container. Nested instances require stable-anchor normalization followed by a
synchronous keyed inert-template guard around Alpine's block morph. Mirrored
physical ranges require one grouped logical lifetime. Stock
`morphBetween(start, end, htmlString)` fails
the `tbody` control, and unguarded stock morph destroys nested comment identity
when a keyed sibling is inserted before it.

All semantic assertions passed in Chromium, Firefox, and WebKit, three full
passes per engine, with no page errors or console output. The spike therefore
clears F21's mechanism gate. It does not make the current Citry runtimes
rootless-aware, and it does not clear the separate named-client-target or
browser-blueprint work.

This report calls `$c-props`, an Alpine handler such as `@click`, or a Citry
handler such as `@c-save` or `@c-poll.5s` on a nested `<c-*>` tag a
**component-tag client binding**. The parent owns the expression or server
handler, while the child supplies the component boundary where the browser
applies it. Later references shorten this to “client binding.”

## Artifacts and rerun

- [`rootless_lifecycle_adapter.js`](rootless_lifecycle_adapter.js) is the
  isolated registry, lifecycle, contextual morph, and nested-range prototype.
  It is research code and is not bundled into Citry.
- [`rootless_lifecycle_scenarios.js`](rootless_lifecycle_scenarios.js) contains
  the browser scenarios.
- [`rootless_lifecycle_harness.py`](rootless_lifecycle_harness.py) loads the
  repo's local pinned Alpine and morph bytes, runs three deterministic semantic
  passes in all three Playwright engines, and prints the evidence JSON.

The ordinary repo environment intentionally omits Playwright. The recorded run
used the already-cached lock-matching package without changing that environment:

```console
uv run --isolated --no-project --offline --with 'playwright==1.61.0' \
  python docs/design/alpinejs/rootless_lifecycle_harness.py
```

| Piece | Pin |
|---|---|
| Alpine | 3.15.12 |
| `@alpinejs/morph` | 3.15.12 |
| Playwright | 1.61.0 |
| Chromium | 149.0.7827.55 |
| Firefox | 151.0 |
| WebKit | 26.5 |

Timer evidence records eventual lower bounds rather than clock-exact counts.
Every contract assertion was stable across all nine passes.

## Why the current runtime is not the mechanism

The existing dependency manager invokes a markerless `$component` callback
with `els=[]`, but its next sweep queries `[data-cid-<id>]`, finds no Element,
and cleans the instance immediately. See
[`citry.js`](../../../packages/py/citry/citry/ext/dependencies/client/citry.js).
The Events registry has the opposite failure: an anchor becomes positively
live only after an Element root is seen, while an anchor never seen in the DOM
is deliberately skipped by retirement. Rootless instances can therefore be
prematurely cleaned by one runtime and retained indefinitely by the other.

Server serialization has no rootless identity either. `mark_html()` can add
`data-cid-*` only to element roots, and the locked text-only behavior emits the
text unchanged. See
[`serialize.py`](../../../packages/py/citry/citry/serialize.py) and
[`test_markers.py`](../../../packages/py/citry/tests/test_markers.py).
Events fragment parsing is context-free `<template>.innerHTML`, correlation
reads only the first Element root, target selection queries element markers,
and replacement groups Element runs. See
[`citry-events.ts`](../../../packages/js/citry-client/src/citry-events.ts).

The spike consequently uses a separate registry. A positive result implies a
future shared instance-liveness primitive and range-aware serialization,
adoption, targeting, morphing, and cleanup. It is not a selector tweak.

## Mechanism proved

### Comment identity and logical lifetime

The prototype adopts exact opaque-region-shaped comments:

```html
<!--citry-start:c7-->Done<!--citry-end:c7-->
```

Each physical range has a unique token even when several ranges mirror one
logical anchor. The adapter retains the two actual `Comment` objects as
physical identity and creates temporary native `Range` objects only for
parsing. A valid live region requires both comments to be connected, unchanged,
under the same Element parent, and in start-before-end order. Pending adoption
stays quiet while start and end arrive in separate mutation batches, then an
explicit settlement boundary rejects duplicate or crossed topology pointedly.
An unrelated sibling whose end is still pending does not poison a complete
pair in the same parent.
One document `MutationObserver` reconciles final state
at the microtask checkpoint. This mirrors Alpine's move handling: a whole
range moved through a `DocumentFragment` and reconnected in the same task
stays alive, while a detach across a task tears down exactly once and never
resurrects.

Initialization is logical-instance-owned. The range parent is a sufficient
Alpine evaluation location, so real `Alpine.evaluateRaw()` supplied reactive
props before init with `ctx.els=[]`. Init ran once, a managed effect reacted to
the parent `x-data`, one poll timer fired against the current range parent,
and marker removal canceled both exactly once. Moving the range to a different
`x-data` parent restarted only its supplier effect; init and logical state
survived. A separate Element-bearing move kept the root node, its own
initialized `x-data`, the Citry scope layer, and their reactive expressions
intact while supply reelected the new parent. The adapter does not remove and
re-add Citry scope on a moved initialized root, because Alpine's
`addScopeToNode()` replaces the whole stack and would erase root-owned layers.
Other inherited Alpine lexical values follow Alpine's native move semantics.

Alpine's own observer ignores added and removed non-Elements, and `initTree()`
cannot initialize a Comment. The range registry must therefore own comment
liveness and logical helpers. Element content between the caps stays under
Alpine's normal observer: inserted directives initialized once and removed
directives cleaned once.

### Stable live `els` and scope

The lifecycle owns one array object for its entire lifetime and mutates its
contents in place. The tested sequence was text, empty, text, two Elements,
one Element, and text again. The same retained array reported `[]`, `[]`, `[]`,
`[span, b]`, `[i]`, and `[]`.

Before Alpine's mutation observer initializes newly inserted top-level roots,
the adapter attaches the lifecycle's stable reactive `scope` with
`Alpine.addScopeToNode()`. Both roots in the multi-root phase rendered a field
written during rootless init. This proves the intended meaning of an
instance-scoped shared bag: an instance may initialize while rootless and its
later element roots can all consume the same scope without rerunning init.

### Contextual parsing

The HTML Standard defines `Range.createContextualFragment()` in terms of the
range start node's context; when that node is a Comment, its parent Element is
used. See the [contextual-fragment algorithm](https://html.spec.whatwg.org/multipage/dynamic-markup-insertion.html#dom-range-createcontextualfragment)
and the [HTML fragment parsing algorithm](https://html.spec.whatwg.org/multipage/parsing.html#parsing-html-fragments).

For each replacement, the adapter:

1. creates a collapsed native Range immediately after the start comment;
2. parses the incoming string with `createContextualFragment()`;
3. moves the parsed nodes into a shallow clone of the real parent, preserving
   its local name and namespace;
4. passes that Element container to `Alpine.morphBetween()`.

This produced `tr` under `tbody`, two `td` nodes under `tr`, `optgroup` and
`option` under `select`, and an SVG-namespace `circle` under `svg` in all three
engines. The separate stock-string control produced a text node rather than a
`tr`, because pinned morph parses strings through a synthetic `div`. Passing a
`DocumentFragment` directly is not a replacement: morph may call
`Alpine.cloneNode()` on its container, and Alpine's Element interceptors assume
Element methods.

The contextual path does not legalize invalid HTML. Browser parsing can foster
parent invalid table content, and initial server markup is normalized before
Citry boots. Components placed in table/select grammars still have to produce
content valid for that context. The spike proves a correctly placed empty
range can become `tr`, `td`, or `option` without a synthetic-div parse bug.

### Nested ranges need an island guard

Alpine morph keys only Elements. Arbitrary Citry comments are positional and
have no special block semantics. The falsifier inserts a keyed Element before
a live nested range. With ordinary contextual `morphBetween`, the nested start
comment is replaced and its lifecycle is destroyed.

The positive path adds a narrow Citry-owned pre/post step:

1. Ask the already-required identity reconciler to map each incoming fresh
   render id to a retained stable anchor, or explicitly refuse the link for an
   unkeyed or new-class replacement.
2. Collapse each top-level nested live range, including both comments, into an
   inert `<template key="citry-rootless:<stable-anchor>">` immediately before
   morph.
3. Collapse incoming nested ranges to the reconciler-selected keyed form in
   the detached contextual container.
4. Let Alpine's ordinary Element-key matcher move, retain, add, or remove those
   inert islands.
5. Expand every surviving template synchronously before MutationObserver
   delivery.

This is not a rendered component wrapper. The temporary template is inert,
exists only during one synchronous morph call, and is gone before paint and
observer delivery. In the passing case, the live and incoming render IDs
differed, the identity resolver mapped both to one stable anchor, and the inner
start comment, end comment, Element, Alpine directive lifetime, and
client-owned state all retained exact identity while keyed siblings were added
before and after it. Refusing that identity mapping instead removed the old
lifecycle once and adopted the incoming fresh range once, modeling the reset
path for unkeyed or new-class replacement. Removing the nested range cleaned
the inner lifecycle and directive once while the outer and adjacent instances
stayed live. A newly inserted nested range expanded to real comments and
adopted once. Two directly adjacent empty ranges also stayed distinct when one
became text.

The guard does not decide keyed, unkeyed, or class-replacement identity. It
consumes the stable key or refusal produced by Citry's existing identity
reconciler. This separation is load-bearing: keying the placeholder directly
by the fresh render id fails continuity.

This guard deliberately gives an already-live nested child island semantics
during its parent's morph. Incoming inner bytes do not overwrite the retained
child through the outer diff; the child's own correlated render path remains
responsible for reconciling it. That matches the existing two-identity and
nested-anchor direction. The harness keeps an explicit different-render-ID
resolver canary so integration cannot regress to transient-id keying.

### Mirrored physical ranges share one lifetime

Events normatively permits one shared instance to be inserted at several
selector matches. Reusing one comment token for every copy would be ambiguous,
so the positive representation is one logical anchor owning several uniquely
tokened physical cap pairs. The research `RootlessMirrorGroup` composes those
ranges under one stable `els`, props, scope, effect, poll, init, and cleanup
lifetime.

The two-copy probe initialized once with both regions empty, morphed both to
Elements that consumed one shared scope, and ran one poll timer. The first
physical parent owned supply. Removing it did not clean or rerun init; `els`
contracted in place, polling continued, and supply reelected the second
parent. Removing the final copy stopped the timer and cleaned the logical
instance once. Product caps therefore need a physical region token in addition
to the shared stable anchor. Group construction is failure-atomic: if one
physical pair is missing, already-adopted regions roll back, group init does
not run, and neither group nor region registry entries remain.

### Keys, cleanup, and errors

Element keys remain local to each comment block. Reordering keyed inputs in
range A preserved their node identity and client values; an adjacent range B
with the same key was untouched. This proves the existing block-level key map
does not cross an adjacent rootless boundary.

Removing either cap, removing the ancestor, replacing the parent with
`innerHTML`, or disconnecting the full range across a task produced one
teardown. Reconciliation and registry destruction after that did not clean a
second time. Managed effects were released before user cleanup, a queued
reactive rerun was suppressed by the lifecycle's active guard, polling stopped,
and one throwing cleanup did not prevent later cleanup callbacks. A throwing
init produced a pointed captured error and a terminal instance without an
uncaught page error.

DOM boundary handlers remain unsupported while `els=[]`, because there is no
honest `EventTarget`, `$el`, or `event.currentTarget`. The prototype throws a
pointed no-EventTarget error. Logical polling works and is not multiplied by
the two comments. Programmatic Events sends and targeted server-event delivery
were not simulated; the current element-based queue and bubbling paths still
need a logical rootless branch in product work.

## Evidence matrix

| Area | Passing probe |
|---|---|
| Initial lifetime | Static text and empty-cap adoption; props before init; `els=[]`; init once; no immediate cleanup. |
| Manifest ordering | Pending manifest before dynamically inserted caps; separately arriving caps stayed quiet; init occurred once after both connected; settlement rejected duplicate and crossed caps without poisoning a complete sibling. |
| Shape transitions | Text, empty, one and several Elements, back to text; stable array identity and current membership throughout. |
| Alpine integration | Shared scope visible from every arriving root; directive init and cleanup exactly once per arriving/departing Element. |
| Context | `tbody/tr`, `tr/td`, `select/optgroup/option`, and SVG namespace; stock string control failed separately. |
| Nested topology | Fresh incoming render ID normalized to the live stable anchor; guarded prepend/append retained exact inner comments, Element state, and directive lifetime; refused normalization reset once; removal cleaned inner only; insertion adopted once. |
| Adjacent topology | Element and directly adjacent empty ranges stayed isolated; morphing one did not change the other's comments or roots. |
| Keys | Keyed reorder retained nodes and input values inside the range; identical adjacent-range key could not cross-match. |
| Movement | Same-task text and Element fragment moves retained lifecycle; new parent resupplied props; Element `x-data` and Citry scope survived; across-task detach cleaned once and did not resurrect. |
| Mirrors | Two physical empty ranges shared init, props, scope, effects, one poll, and stable `els`; first removal reelected supply without cleanup; last removal cleaned once; partial construction rolled back atomically. |
| Corruption | Single-cap removal, ancestor removal, active comment stripping, and parent `innerHTML` replacement cleaned once. |
| Managed work | Effects, queued-work guard, manual stop, poll cancellation, cleanup ordering, throwing init, and throwing-cleanup isolation. |
| Rootless handler | DOM handler failed pointedly; one logical poll cadence remained available. |
| Inert template | Comments inside `template.content` were not discovered or initialized by the document registry. |

## Deployment and product boundaries

Preserving Citry anchor comments is a deployment requirement. If a minifier,
CDN, sanitizer, or client rewrite strips comments after activation, the
registry can detect corruption and clean exactly once. If comments are stripped
before adoption, identity is gone and cannot be reconstructed. The tested
contract is a pointed missing-comments error with no initialized lifecycle,
not silent fallback. Product marker text must include an unambiguous opaque
registry token so user comments cannot collide with it.

`template.content` is disconnected and invisible to a document observer.
Cloning a template creates fresh comment objects and can duplicate serialized
identity. The spike intentionally leaves template-blueprint activation to the
separate browser-instantiation design. A pending manifest can wait for one
future connected pair, but that alone is not a safe clone protocol.

The prototype covers ordinary light DOM. Shadow-root observation, ranges whose
caps cross a shadow boundary, parser-created foster-parent movement, and a
comment-altering third-party morph during Citry's synchronous guard are not
claimed. Caps in different parents or reversed order are invalid by contract
and must clean terminally.

## Required stage-two integration

The mechanism result changes the root-shape recommendation from "spike" to
"supported after integration", but the implementation remains substantial:

1. Serialization must emit paired caps, an opaque physical region token, and a
   stable logical anchor for every client-active text/empty instance, including empty inserted fragments whose
   manifests need an insertion location. The exact cap-all-versus-cap-only-
   client-active policy still needs a server-output decision.
2. Dependency and Events manifests must enter one shared registry. Range
   discovery must precede init calls in a mutation batch, and parent-before-
   descendant init must use the accepted ancestry DAG.
3. Every element-only liveness query in dependency cleanup, Events dequeue,
   lifecycle delivery, self-targeting, server event actions, and render target
   selection must route through one `isLive(instance)` abstraction.
4. Fragment parsing and application need the contextual container path,
   comment-block targets, empty-result manifest insertion, stable live `els`
   updates, grouped mirrored regions, and the nested inert-island guard.
5. Existing stable-anchor reconciliation must run before morph and key
   temporary nested placeholders by the logical anchor, not the fresh render
   id. It must refuse that link for new-class, plain-HTML, and unkeyed reset
   cases according to the already accepted identity rules.
6. Rootless `x-props`, init, managed helpers, `scope`, and `@c-poll` can use the
   proved logical path. DOM Alpine and Citry event client bindings must fail pointedly
   until at least one real root exists. Programmatic send and targeted
   `$onEvent` need an internal logical dispatch path or an explicit unsupported
   error rather than today's silent element lookup.
7. Production tests must retain the contextual, nested/adjacent, comment-
   stripping, liveness, exact-cleanup, and three-browser controls from this
   harness. The raw string and unguarded nested failures should remain canaries
   so future simplification cannot remove either adapter accidentally.

## Recommendation for WP23

Proceed with comment-owned rootless instances in WP23 stage two. Keep actual
start/end Comment references as physical-region identity, group mirrored
regions under one stable logical anchor, update one stable `els` array in
place, and keep one logical lifetime for supply, init, effects, polling, and
cleanup. Use contextual fragment parsing and a parent-shaped Element container
for morph. Normalize fresh nested IDs through the existing identity reconciler,
treat linked live ranges as keyed inert islands during the synchronous outer
morph, then restore their real nodes before observers run.

Do not insert a visible wrapper merely to host lifecycle state. Retain pointed
errors for missing/stripped caps, invalid cap topology, DOM event client bindings with no
Element root, and template-clone activation until its separate identity
protocol exists.
