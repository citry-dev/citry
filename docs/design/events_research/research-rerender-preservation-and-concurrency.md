# Research: re-render preservation and in-flight concurrency across the field

Field research feeding two client-runtime decisions ahead of the WP16/WP17
client work ([`../events_plan.md`](../events_plan.md)): what should survive
when a parent component re-renders (preservation), and what should happen
when a child's event call is in flight while a parent re-render lands
(concurrency, the dead-target race). It surveys ten systems: Laravel
Livewire, Phoenix LiveView, HTMX, Turbo 8, Unpoly, Datastar, the three morph
libraries (morphdom, idiomorph, Alpine morph), and the client data layers
(Apollo Client, TanStack Query, React 18/19). This document is the input to a
maintainer decision, not a decision; it reports what the field does, with
pros and cons as the field experienced them, then ends with recommendations
and their falsifiers. The companion decision analysis for the nested-anchor
half of the problem is
[`analysis-nested-anchor-continuity.md`](analysis-nested-anchor-continuity.md).

Written 2026-07-14. Produced from four source-verified research passes (one
per framework cluster) followed by an adversarial fact-check pass; the
fact-check's corrections are incorporated, and every claim it could not
verify is marked unverified inline. Sources are cited inline with the
framework version each claim is about.

## The two questions, in citry vocabulary

Citry terms used throughout, one line each (all from
[`../events.md`](../events.md)):

- **Anchor**: the stable, client-internal identity of one interactive DOM
  position; the reactive State, the Alpine scope, and the epoch guard hang
  off it, while the server mints a fresh component id on every render
  (events.md 5.5).
- **Epoch guard**: a per-anchor monotonic counter; a response echoing an
  epoch older than the highest applied gets its instance-mutating actions
  dropped, while its `data` still resolves the caller's promise
  (events.md 4.2).
- **`citry:events:stale`**: the DOM event that fires when the epoch guard
  drops a late response's DOM changes (events.md 5.2; also reused for
  version-skew stale state, 4.5).
- **Morph by default**: responses patch the DOM via `@alpinejs/morph`;
  `c-key` gives list items identity, `data-citry-morph="ignore"` opts a
  subtree out, and a focused two-way-bound control's live value is kept via
  the `keepLiveValue` branch of the `updating` hook (events.md 5.3).
- **Three-way split and reconcile rule**: on a re-render, same class means
  reconcile `$state` in place (server wins per field except pending unsent
  local writes), different class means discard and adopt, plain HTML means
  the anchor goes non-interactive (events.md 5.5).

The two questions:

1. **Preservation.** When a parent re-renders (for example on a poll),
   nested children and mid-edit inputs get reset by the update. The
   maintainer leans "reset by default, developer opts into preservation via
   keying". What mechanisms does the field use: keying for morph matching,
   preserve/ignore markers, focused-element special cases, and the
   recommended patterns (disable inputs while loading, lift input state to
   server state, avoid re-render-on-poll)?

2. **Concurrency.** A child's event call is in flight when a parent
   re-render lands, killing the child's client identity; the response
   arrives addressed to a dead target. Options on the table: drop plus log
   plus a developer-facing callback; a policy setting (parent cannot send
   while child in flight, or the reverse); a queue where events touching the
   same component subtree serialize (siblings parallel, nested serialized).
   Do other frameworks do something like this, and what are the pros and
   cons?

## Executive summary

**Question 1: does the field do reset-by-default with opt-in keying?** The
field splits by family, and the split is architectural, not stylistic. The
swap-by-default hypermedia frameworks (HTMX 2.x, Unpoly 3.x) reset
everything in the updated region and offer opt-in keep markers tied to an
element id (`hx-preserve`, https://htmx.org/attributes/hx-preserve/;
`[up-keep]`, https://unpoly.com/up-keep). That is the maintainer's lean,
verbatim. The server-driven frameworks (Livewire v3/v4, LiveView v1.2.7)
lean preserve-by-default instead, but they buy it structurally rather than
through client cleverness: Livewire's parent re-render does not touch child
roots at all (the server emits only a placeholder stub per child,
https://livewire.laravel.com/docs/3.x/understanding-nesting), and LiveView
sends minimal diffs of only the changed dynamic parts while component state
lives server-side (https://hexdocs.pm/phoenix_live_view/Phoenix.LiveComponent.html,
v1.2.7). The morph-by-default systems (Turbo 8 page-refresh morphs, Datastar
v1, and the morph libraries themselves) sit between: unchanged DOM survives
in place, and anything that must survive an actual content change needs an
id, a key, or a marker. The invariant the evidence supports: **preservation
always rides a stable identity or an explicit marker.** Some frameworks own
that identity themselves (Livewire's framework-minted `wire:id` lets its
morph skip child roots with zero author action; LiveView holds component
state server-side), and where the framework does not own one, the identity
must be author-supplied. The citry consequence is what supports the lean:
citry mints fresh component ids on every render, so the only stable
identity available to it is an author-supplied one. The mechanism inventory the field converged on is
five-fold: user-authored keys for matching, a whole-subtree ignore marker
plus (eventually, in every morph framework) a finer per-attribute tier, a
focused-element rule (a genuine three-way split in defaults, detailed
below, not the consensus one input claimed), lifted input state riding the
next request, and disable-while-loading affordances. Citry's designed stack
(events.md 5.3, 5.5) already contains all five; the focused-element rule is
the one that is net-new client work, because citry's chosen morpher ships
none.

**Question 2: do frameworks ship concurrency policies like the subtree
queue, and which model won?** Serialization exists nearly everywhere, but
nobody scopes it by the component tree. Livewire serializes per component
and merges queued actions into one follow-up request (source-verified in
v2 and v3, stated as contract in v4:
https://livewire.laravel.com/docs/4.x/actions). LiveView serializes the
whole view: one Elixir process handles every event in arrival order, the
coarsest possible subtree queue and the opposite pole from per-element
policy (https://hexdocs.pm/phoenix_live_view/Phoenix.LiveComponent.html,
v1.2.7). The data layers serialize by a developer-chosen key (TanStack
Query `scope.id`, Apollo's community `serializationKey` link, React 19's
`useActionState` per-hook queue), always with siblings parallel. The
hypermedia cluster resolves conflicts by aborting instead of queueing:
Unpoly's default `{ abort: 'target' }` kills earlier requests targeting
fragments inside the updated subtree (https://unpoly.com/aborting-requests,
3.x), Turbo and Datastar are newest-wins (globally and per endpoint
respectively). HTMX's `hx-sync` is the field's one per-element,
ancestor-imposes-on-descendants **policy setting**
(https://htmx.org/attributes/hx-sync/), the closest prior art for citry's
policy-setting option, and its documented weaknesses (a fully silent
default drop, per-pair reasoning burden) are the argument against copying
it. The dead-target race itself has three field answers: dissolve it
structurally (Livewire's stable ids plus skipped children), serialize it
away server-side and no-op-ack the residue (LiveView), or abort the child's
in-flight work when the parent wins (Unpoly). And one datum the maintainers
of the queue-based systems supplied themselves: Livewire v4's escape hatch
from its queue (`#[Async]`) ships with the warning "Never use async actions
if they modify component state that's reflected in your UI"
(https://livewire.laravel.com/docs/4.x/actions), which is the maintainers'
own verdict that unserialized same-component concurrency is unsafe.

**What this means for citry, shortest form** (full recommendations with
falsifiers in the last section): keep the designed preservation stack and
add nothing speculative (R1); serialize sends per anchor with merge, keep
siblings parallel, and answer the parent/child overlap with drop plus
surface rather than a policy setting or a full subtree queue in v1 (R2);
make every drop observable through one event with a reason and never leave
a promise unsettled, which is already citry's design and is strictly ahead
of the field norm (R3).

## The field at a glance

| System (version) | Default when new HTML lands | Preservation mechanisms | Concurrency model | What surfaces when work is dropped or superseded |
|---|---|---|---|---|
| Livewire v3.x (v4 Jan 2026) | Morph in place; child component roots skipped entirely | `wire:key` (mandatory in loops), `wire:ignore` / `.self`, `wire:replace`, injected block markers around conditionals, deferred `wire:model` diffs, auto-disable during submit | One in-flight request per component; later actions merge and wait (5ms buffer); independent components bundle into one request; `#[Isolate]`; v4 `#[Async]` escape | Nothing for queued-then-merged work (never dropped); fail hooks plus error modal; failed call promises never settle (source-verified gap) |
| Phoenix LiveView v1.2.7 | Minimal server diffs; patch touches only changed nodes | Always-on focused-input value rule, `phx-update="ignore"`, `JS.ignore_attributes`, DOM ids, streams, `:key` (v1.1), DOM-patch-aware JS commands, hooks, form recovery | Whole view is one server process (every event serializes); client locks per element and defers display until acks; debounce/throttle | Dead-CID events acked with a no-op and silently dropped; hook `pushEvent` promises reject; declarative bindings get loading classes only |
| HTMX 2.x | Swap (innerHTML) replaces the region | `hx-preserve` by id (loses focus/caret), idiomorph extension (id sets, `restoreFocus`), `hx-disabled-elt`, `hx-indicator` | Per-element queue (default `last`); `hx-sync` per-element-pair policy (drop, abort, replace, queue) | `hx-sync` default drop is fully silent; abort/replace surface only via the generic `htmx:sendAbort`; per-class error events exist |
| Turbo 8 (main, July 2026) | Replace by default; opt-in page-refresh morph (idiomorph) | `data-turbo-permanent` by id, cancelable per-element and per-attribute morph events, frames reload from their own src | Global newest wins: a new visit or submission stops the current one; submitter auto-disabled | No cancelled-visit event in the documented list (unverified, docs absence); `turbo:submit-end`, fetch-error events |
| Unpoly 3.x | Swap the targeted fragment | `[up-keep]` by derivable id (`true`, `same-html`, `same-data`, `false` server veto), `[up-watch-disable]` | Per-subtree conflict: a render aborts older requests targeting fragments inside it (newest wins); watch callbacks serialize (queue-last); network concurrency cap 6 | `up:fragment:aborted` plus `up:request:aborted` plus a rejected promise (`up.AbortError`): the richest surface surveyed |
| Datastar v1 | Morph by id (idiomorph) | `data-ignore-morph`, `data-preserve-attr`, durable state in signals (data-down) | Per-endpoint newest wins: auto-cancels in-flight requests to the same URL and method | One typed lifecycle event (`datastar-fetch`: started, finished, error, retrying) |
| Morph libraries (morphdom 2.x, idiomorph 0.7.4, Alpine morph 3.x) | n/a (libraries) | Keys (`node.id` / id sets / `key` attribute); before-hooks to skip subtrees; focused-element handling: none / focus-restore by default / none | n/a | Nothing: synchronous patchers with veto hooks, no events |
| Client data layers (Apollo 3.x, TanStack Query v5, React 19) | n/a | Optimistic layers rebased over a server-canonical store | Parallel by default; opt-in serialization by key (`serializationKey`, `scope.id`, `useActionState`); transitions interruptible | Failure callbacks per call plus one global hook; supersession is silent everywhere |

## Dimension 1: what survives a re-render

### Morph versus replace: the two default camps

Livewire v3 made morphing the default precisely to answer this question:
"event listeners, focus state, and form input values are all preserved
between Livewire updates" because unchanged elements are patched in place,
never recreated (https://livewire.laravel.com/docs/3.x/morphing, v3). The
v2-era client used morphdom and had chronic lost-focus and lost-input
issues (for example issue
https://github.com/livewire/livewire/issues/687 and discussion
https://github.com/livewire/livewire/discussions/4709); the v3 rewrite
around Alpine state binding is what fixed the class. LiveView goes further
upstream: the server sends minimal diffs of only the changed dynamic parts,
so the patch never touches nodes whose rendered output did not change
(https://www.phoenixframework.org/blog/phoenix-liveview-1-1-released and
the v1.2.7 guides). Turbo 8 keeps full-page replace as the default and
offers morphing as an opt-in per page (`meta turbo-refresh-method=morph`,
https://turbo.hotwired.dev/handbook/page_refreshes). HTMX and Unpoly keep
swap as the default and treat morphing as an extension or a keep-marker
special case.

Citry is already in the morph camp (events.md 5.3), so the relevant field
lessons are the morph camp's: everything below about keys, markers, and
focused elements is what every morph-by-default system eventually built.

### Keying: universal, user-authored, and load-bearing

Every surveyed system keys morph matching on author-supplied identity, and
none invents keys:

- morphdom 2.x matches positionally by default; the `getNodeKey(node)`
  option (defaulting to `node.id`) upgrades matching so keyed elements move
  instead of being destroyed and recreated
  (https://github.com/patrick-steele-idem/morphdom).
- idiomorph v0.7.4 exists because hand-keying everything is painful: its
  "id sets" algorithm gives every element the set of its own plus
  descendant ids, and two elements match when the sets intersect, so one id
  deep in a subtree keeps the whole ancestor chain matched
  (https://github.com/bigskysoftware/idiomorph).
- Alpine morph 3.x matches children by the plain `key` attribute
  (customizable via the `key(el)` hook, https://alpinejs.dev/plugins/morph).
  This is the mechanism citry's `c-key` writes into (events.md 5.3).
- Livewire resolves its morph key as `wire:key`, else `wire:id`, else the
  plain `id` attribute (source: the key function in
  https://raw.githubusercontent.com/livewire/livewire/3.x/js/morph.js), and
  explicitly pins `lookahead: false` (also the plugin default) in the same
  file, relying on keys plus injected markers instead. The
  docs make keys mandatory for child components inside loops, a stronger
  requirement than Vue or React: "Livewire relies more heavily on keys and
  will behave incorrectly without them"
  (https://livewire.laravel.com/docs/nesting, v4; the v3 morphing docs say
  the same about loops). The single most repeated community lesson in the
  Livewire ecosystem is that a missing `wire:key` on looped or dynamic
  elements causes lost focus and stale input values, and "add wire:key" is
  the reflexive first fix
  (https://github.com/livewire/livewire/discussions/7937,
  https://github.com/alpinejs/alpine/issues/3097,
  https://github.com/alpinejs/alpine/discussions/2826).
- LiveView keys everything on unique DOM ids (duplicate ids silently
  corrupt patching; LiveViewTest raises on them in v1.2), pairs
  `phx-update="stream"` children by id, and added keyed comprehensions in
  v1.1 (`:key={item.id}`) because unkeyed `:for` diffs by index and a
  prepend resends every following row
  (https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.1.14/CHANGELOG.md).

Because unkeyed lists pair positionally, per-element state (focus, caret,
an ignored subtree) sticks to the position rather than the item once a list
reorders. Citry's one-line docs guidance ("add `c-key` to `<c-for>` items
whose list can reorder", events.md 5.3) is exactly the universal guidance,
with Livewire's experience arguing it should be framed strongly for child
components in loops, not as an optimization.

One honest nuance on the maintainer's lean: in the field, keys fix
**matching**, and preservation of a child's state then follows from
architecture (Livewire skips child roots; LiveView holds component state
server-side keyed by module plus id, "Two live components with the same
module and ID are treated as the same component, regardless of where they
are in the page",
https://hexdocs.pm/phoenix_live_view/Phoenix.LiveComponent.html, v1.2.7).
The hypermedia frameworks are the ones where preservation of the element
itself is opt-in via marker plus id (HTMX `hx-preserve`, Unpoly
`[up-keep]`). Citry's lean (continuity of the child's **anchor** is opt-in
via keying, reset otherwise) applies the hypermedia stance at the anchor
layer; no surveyed framework does exactly that, because none has citry's
fresh-id-per-render plus whole-subtree re-render combination
(events.md 5.3 "a parent's morph does not skip nested instance roots").
That is design space citry occupies alone, which is why the companion
analysis exists.

### Preserve and ignore markers: every morph framework grew both tiers

The whole-subtree marker exists everywhere under different names, always
motivated by third-party-owned DOM:

- Livewire v3: `wire:ignore` (skip element and subtree), `wire:ignore.self`
  (patch children, keep the element's own attributes), and the inverse
  `wire:replace` / `wire:replace.self` which bypass morphing for a subtree
  (https://livewire.laravel.com/docs/3.x/wire-ignore and
  https://livewire.laravel.com/docs/3.x/morphing; implemented as flags the
  morph hooks honor, https://raw.githubusercontent.com/livewire/livewire/3.x/js/morph.js).
- LiveView v1.2.7: `phx-update="ignore"`, which freezes content and
  attributes "except for data attributes", which are merged so the server
  can still pass data to client JS; requires a unique DOM id
  (https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/guides/client/bindings.md).
- Turbo 8: `data-turbo-permanent`; verified in source, `beforeNodeMorphed`
  returns false for any element carrying it, and `beforeNodeAdded` refuses
  to insert an incoming node when a permanent element with the same id
  already exists, so the id requirement is structural
  (https://raw.githubusercontent.com/hotwired/turbo/main/src/core/morphing.js,
  main as of July 2026).
- Datastar v1: `data-ignore-morph` (https://data-star.dev/reference/attributes).
- The libraries: morphdom's `onBeforeElUpdated` returning false, idiomorph's
  `beforeNodeMorphed` returning false, Alpine morph's `skip()` inside
  `updating`. Citry's `data-citry-morph="ignore"` maps onto the last of
  these (events.md 5.3), the same way Livewire implements `wire:ignore`.

And framework after framework that lived with the whole-subtree marker
grew a **finer per-attribute tier** (four of the surveyed systems:
LiveView, Turbo, Datastar, and idiomorph; Livewire and Alpine morph have
not), because the subtree marker
is all-or-nothing and browser-owned attributes (like `open` on `<details>`
or `<dialog>`) kept getting stripped by patches: LiveView added
`JS.ignore_attributes` in v1.1 for exactly that reason
(https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.1.14/CHANGELOG.md),
Turbo has the cancelable `turbo:before-morph-attribute` event
(https://turbo.hotwired.dev/reference/events), Datastar has
`data-preserve-attr` (https://data-star.dev/reference/attributes), and
idiomorph has `beforeAttributeUpdated`
(https://github.com/bigskysoftware/idiomorph). Citry reserves an
`"ignore-self"` marker value mapping to `childrenOnly()` (events.md 5.3);
the field's trajectory says a per-attribute request will follow once real
apps hit browser-owned attributes, so it is worth expecting, not building.

Two marker gotchas the field documented: markers hold only on the code
paths that honor them (Turbo's `data-turbo-permanent` is honored by
page-refresh morphs but users report it not holding under turbo-stream
updates, per the Hotwire discussion titled "data-turbo-permanent is
recreated on updating form with turbo-stream",
https://discuss.hotwired.dev/t/data-turbo-permanent-is-recreated-on-updating-form-with-turbo-stream/6202;
title located via search, thread not read in full, so treat the details as
unverified). And keep-by-id without morphing is not enough for mid-edit
inputs: HTMX's own `hx-preserve` docs concede text inputs still lose focus
and caret position and point to the morph extension for anything richer
(https://htmx.org/attributes/hx-preserve/, 2.x).

### Focused-element rules: a three-way split, not a consensus

One research input claimed every serious morph library special-cases the
focused element out of the box. The fact-check disproved that, and the
corrected picture matters for citry because it changes what is free and
what is net-new work. The field is a three-way split:

1. **Always-on rule (LiveView v1.2.7).** "The JavaScript client is always
   the source of truth for current input values. For any given input with
   focus, LiveView will never overwrite the input's current value, even if
   it deviates from the server's rendered updates"
   (https://hexdocs.pm/phoenix_live_view/form-bindings.html, v1.2.7). In
   source, the morphdom `onBeforeElUpdated` hook skips patching the focused
   editable input entirely, with two carve-outs: a focused `<select>` whose
   options changed is blurred and patched, and number inputs in a
   `badInput` validity state are skipped
   (https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/assets/js/phoenix_live_view/dom_patch.ts).
   Note the protection covers only the focused input by rule; unfocused
   dirty inputs are protected by the locking machinery described under
   concurrency.

2. **Focus-restore by default, value protection opt-in (idiomorph
   v0.7.4).** `restoreFocus: true` by default (re-focus and restore
   selection after the morph), while `ignoreActive` and `ignoreActiveValue`
   both default to **false**, so the focused element's value is morphed
   unless the integrator opts out
   (https://github.com/bigskysoftware/idiomorph).

3. **Nothing built in (morphdom 2.x, Alpine morph 3.x, and Livewire's own
   morph layer).** morphdom has no focused-element handling; issue
   https://github.com/patrick-steele-idem/morphdom/issues/135 documents the
   focus and caret loss users hit, and the community idiom is an
   `el === document.activeElement` check in `onBeforeElUpdated` (packaged,
   for example, as the `inputPersistence` plugin in
   https://www.npmjs.com/package/@retailmenot/morphdom-plugins). Alpine
   morph has no `document.activeElement` handling anywhere; its attribute
   patching uses `setAttribute` only
   (https://raw.githubusercontent.com/alpinejs/alpine/main/packages/morph/src/morph.js,
   verified by the fact-check pass). Livewire's morph wrapper adds no
   focused-element case either (grep-verified in
   https://raw.githubusercontent.com/livewire/livewire/3.x/js/morph.js);
   Livewire's inputs survive as a side effect of the morph never writing a
   dirtied input's live `value` property plus the state binding described
   next. (Contrast morphdom, which **does** sync the `value` property in
   `src/specialElHandlers.js`,
   https://raw.githubusercontent.com/patrick-steele-idem/morphdom/master/src/specialElHandlers.js,
   which is exactly why raw morphdom clobbers typed text and Alpine morph
   tends not to.)

The two failure directions are both on record. **No protection** is the
morphdom #135 class: every keystroke-driven morph can eat focus and caret.
**Blanket protection** is Turbo's lesson: Turbo 8.0 passed idiomorph's
`ignoreActiveValue: true` (added in PR
https://github.com/hotwired/turbo/pull/1141), and the protection itself
became the bug, "Morphing: impossible to clear a form due to
ignoreActiveValue: true" (https://github.com/hotwired/turbo/issues/1194,
verified: after a successful submit, the server-rendered empty field could
not overwrite the still-focused input). The fix, PR
https://github.com/hotwired/turbo/pull/1195, removed the blanket option;
current main passes no `ignoreActiveValue` and relies on idiomorph's
`restoreFocus` default (verified in
https://raw.githubusercontent.com/hotwired/turbo/main/src/core/morphing.js).

For citry the consequence is direct: `@alpinejs/morph`, the chosen morpher,
ships **no** focused-element handling, so the focused-control rule in
events.md 5.3 (`keepLiveValue` inside the `updating` hook, scoped to a
focused **and** two-way-bound control) is net-new runtime work, not
something the library gives for free. The narrow scoping is the right side
of both recorded failure directions, and the Turbo #1194 scenario
(handler legitimately clears a bound field that still has focus, the
submit-then-clear chat box) is the test case that narrow scoping must pass;
it belongs in the WP16/WP17 test plan.

### Lifting input state, and disabling while loading

The maintainer asked about three recommended patterns. All three are
confirmed as first-class, documented features across the field:

**Lift input state to server state.** Livewire's plain `wire:model` is
deferred: it writes into client-side state and sends no request; the typed
value rides along as a diff with the next request from the component,
**including a `wire:poll` tick**, so a poll uploads the draft instead of
resetting it, and the server echoes it back as canonical
(https://livewire.laravel.com/docs/3.x/wire-model, v3; source: the
canonical-vs-ephemeral diff in
https://raw.githubusercontent.com/livewire/livewire/3.x/js/request/commit.js).
On response, the merge computes which keys the server actually changed
beyond what the client sent and only overwrites those, so keystrokes typed
while a request was in flight survive
(https://raw.githubusercontent.com/livewire/livewire/3.x/js/component.js,
`mergeNewSnapshot`). LiveView's idiom is the same shape: `phx-change` on
the form sends all fields to the server, and form recovery re-triggers the
last `phx-change` after a reconnect so server state is rebuilt
(https://hexdocs.pm/phoenix_live_view/form-bindings.html, v1.2.7). Citry
already has this pattern designed as the updates piggyback: a pending
`$state` write rides the next call from the instance, whatever sends it
(events.md 4.2, 5.5), which is Livewire's deferred-diff trick in citry
vocabulary and makes polls draft-safe with no developer action.

**Disable inputs while loading.** Livewire automatically marks inputs
readonly and disables submit buttons during `wire:submit`
(https://raw.githubusercontent.com/livewire/livewire/3.x/js/features/supportDisablingFormsDuringRequest.js),
with `wire:loading.attr="disabled"` plus `wire:target` as the manual
pattern (https://livewire.laravel.com/docs/3.x/wire-loading). LiveView's
`phx-submit` sets the form's inputs readonly and disables submit buttons
until the ack, with `phx-disable-with` for button text
(https://hexdocs.pm/phoenix_live_view/form-bindings.html, v1.2.7; gotcha:
`phx-disable-with` works on `innerText`, so nested svg icons are not
preserved, and the docs steer to CSS loading classes). Unpoly bakes it into
the watch layer as `[up-watch-disable]` (https://unpoly.com/watch-options),
HTMX as `hx-disabled-elt` and `hx-indicator`
(https://htmx.org/attributes/hx-disabled-elt/ and
https://htmx.org/attributes/hx-indicator/, 2.x). Citry's
counterpart is `data-citry-busy` on the triggering element and instance
roots plus `$loading` (events.md 5.3, 5.5), which supports the same CSS
attribute-selector pattern with zero new vocabulary.

**Avoid re-render-on-poll resets, structurally.** Livewire's answer is
architecture: children are skipped on a parent poll, and drafts ride the
poll (above). Datastar's answer is data-down by construction: durable
client state lives in signals, and the server patches signals rather than
re-rendering DOM around mid-edit state, so preservation pressure on the
morph is deliberately low (https://data-star.dev/guide/backend_requests,
v1). LiveView's answer is minimal diffs. Citry re-renders the whole subtree
by design (props flow naturally, events.md 5.3), so its equivalents are the
reconcile rule (pending unsent writes win per field, 5.5), the piggyback,
and the local-first `$state` pattern (5.5); the docs guidance worth writing
is "a poll is safe over drafts because updates ride it; keep client-only UI
state in your own `x-data`".

### Where the field disagrees on dimension 1

Two of the research inputs frame the same facts oppositely, and both are
right at their own layer. The Livewire pass concluded Livewire is "the
opposite pole" of citry's reset lean, because its re-render default
preserves child roots and inputs without any author action. The
morph-libraries pass concluded citry's lean "is exactly the
idiomorph/Livewire consensus", because at the mechanism layer (keys are
user-authored, unkeyed lists pair positionally, ignore markers are opt-in)
Livewire's client behaves precisely like citry's design. The resolution:
Livewire's **defaults** are preserve-leaning because of architecture
(skipped children, stable ids, state binding), while its **mechanisms** are
the same opt-in-identity toolkit citry plans. A reader deciding "is
reset-by-default defensible?" should weigh the hypermedia cluster (yes,
with keep markers) and the fact that the two closest competitor frameworks
avoided the question architecturally rather than answering it with a
default.

## Dimension 2: overlapping work and the dead-target race

### The six concurrency models in the field

**(a) Livewire: per-component serialization with merge (v2, v3
source-verified; v4 documents it as contract).** Each component has at most
one loose commit; every action fired merges into it; a 5ms buffer coalesces
near-simultaneous triggers (the docs' example: a click that also blurs a
field); if the component already has a commit inside an in-flight pool, the
new commit waits, and when the pool returns, queued commits go out as a
single follow-up request. Nothing is dropped
(https://raw.githubusercontent.com/livewire/livewire/3.x/js/request/bus.js).
v4 states it plainly: "By default, Livewire serializes actions within the
same component to ensure predictable state updates. If one action is
in-flight, subsequent actions are queued and wait for it to finish"
(https://livewire.laravel.com/docs/4.x/actions). Across components there is
no serialization; commits from different components in the same 5ms window
are bundled into one network request for transport efficiency
(https://livewire.laravel.com/docs/3.x/bundling), with `#[Isolate]` to opt
a slow component out of the shared pool. The community-reported costs:
head-of-line blocking within a component (a slow action delays everything
else on it; https://github.com/livewire/livewire/discussions/7081 asked for
non-blocking actions, answered only by v4's `#[Async]`), and the queue does
not cover direct client state pokes (`$wire.set()` twice in quick
succession still corrupts state,
https://github.com/livewire/livewire/discussions/8776, v3.5.4, no
documented fix).

**(b) LiveView: whole-view server serialization plus per-element client
locks (v1.2.7).** One LiveView is one Elixir process, and LiveComponents
run inside it, so every event targeting the view or any component in it is
processed one at a time in mailbox order
(https://hexdocs.pm/phoenix_live_view/Phoenix.LiveComponent.html). This is
the maintainer's "subtree queue" at the coarsest granularity: the
serialization unit is the whole view, and only separate LiveViews run in
parallel. The documented cost is the same head-of-line blocking, and the
documented cure is not finer concurrency but moving slow work off-process
(`assign_async` / `start_async`,
https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/lib/phoenix_live_view.ex).
On the client, every push carries a monotonically increasing ref the
maintainers describe as a clock ("LiveView tracks each event sent to the
server with clocks to prevent outdated server updates from rendering on the
client", https://www.phoenixframework.org/blog/phoenix-liveview-1-1-released),
and a locked element's incoming patches are redirected onto a private
cloned tree, then replayed on ack: "The changes to the form are applied
behind the scenes as they arrive, but LiveView only shows them once all
in-flight events have been resolved"
(https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/guides/client/syncing-changes.md).
Nothing is dropped or blocked; display is deferred per element. The
maintenance bill for that cloned-tree machinery is on record and is the
budget warning for anyone copying it: locked containers failing to apply
pending stream updates (1.0.x changelog), LiveComponent updates discarded
when locked trees are restored
(https://github.com/phoenixframework/phoenix_live_view/issues/3941, fixed
in v1.1.x), locks on skipped nodes
(https://github.com/phoenixframework/phoenix_live_view/issues/4209, fixed
in v1.2.0), and stale events crossing a live redirect
(https://github.com/phoenixframework/phoenix_live_view/issues/4291, fixed
in v1.2.1; all in
https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/CHANGELOG.md).

**(c) Unpoly: per-subtree conflict detection, resolved newest-wins
(3.x).** Every render pass defaults to `{ abort: 'target' }`: it aborts
earlier requests targeting fragments **within** the fragment being updated;
requests targeting non-conflicting fragments continue in parallel
(https://unpoly.com/aborting-requests). This is the field's only
subtree-scoped conflict model and the strongest precedent for citry's
"events touching the same component subtree conflict" framing, but the
resolution is the opposite of a queue: the older request is killed. A
request opts out with `{ abortable: false }`; destroying a fragment aborts
requests targeted at it regardless of settings. The 3.0 changelog frames
the design as a deliberate retreat from Unpoly 2's global "abort
everything" option: Unpoly 3 "by default only aborts requests conflicting
with your update" (https://unpoly.com/changes/3.0.0). Separately, the
form-watch layer serializes its callbacks queue-last: "Unpoly will
guarantee that only one async callback is running concurrently... Unpoly
will wait until the callback concludes and then re-run it with the latest
field values" (https://unpoly.com/watch-options).

**(d) HTMX: per-element queue plus the hx-sync policy surface (2.x).**
When an element triggers while its own request is in flight, the event is
queued; the default strategy is `last` (only the most recent trigger
replays when the current request completes; verified in source,
https://raw.githubusercontent.com/bigskysoftware/htmx/master/src/htmx.js),
with `first`, `all`, and `none` available
(https://htmx.org/attributes/hx-trigger/). Requests from different elements
run fully parallel with no coordination, which is exactly how a child call
and a parent poll collide. `hx-sync="<selector>:<strategy>"` is the
declarative per-element-pair policy on top: `drop` (default), `abort`,
`replace`, `queue first|last|all`; it is inherited, so an ancestor imposes
policy on descendants, canonically `hx-sync="closest form:abort"` so an
input's validation request dies when its form submits
(https://htmx.org/attributes/hx-sync/). This is the closest prior art in
the field for citry's "policy setting" option. Its weaknesses are discussed
under dimension 3 and R2.

**(e) Turbo and Datastar: newest wins, globally or per endpoint.** Turbo
Drive keeps at most one navigation or form submission: starting a new one
calls `stop()` on the current visit and in-flight submission first
(verified in
https://raw.githubusercontent.com/hotwired/turbo/main/src/core/drive/navigator.js,
main as of July 2026), and the submitter button is disabled for the
duration (https://turbo.hotwired.dev/handbook/drive). Frames navigate
independently; no cross-frame queue is documented (unverified beyond
absence in the docs). Datastar's backend actions default to
`requestCancellation: 'auto'`, which "cancels in-flight requests to the
same URL using the same HTTP method"
(https://data-star.dev/reference/actions, v1); note the key is URL plus
method, not component identity, so two components sharing an endpoint can
cancel each other's requests (an implication of the documented semantics,
not stated in the docs; unverified). No cross-request ordering guarantee is
documented for its SSE patch streams (unverified, docs absence).

**(f) The data layers: parallel by default, serialization by opt-in key.**
Apollo Client 3.x mutations fire in parallel with no built-in ordering
(long-standing issue
https://github.com/apollographql/apollo-client/issues/3715); ordering is
added by composing links, and
https://github.com/helfer/apollo-link-serialize queues all operations
sharing a `serializationKey` (request B is not even forwarded until A has
completed or errored) while different keys stay parallel. TanStack Query v5
documents "all mutations run in parallel - even if you invoke `.mutate()`
of the same mutation multiple times", and mutations given a
`scope: { id }` "will run in serial", starting in `isPaused: true` when one
is already in flight
(https://tanstack.com/query/v5/docs/framework/react/guides/mutations,
verified); the scope feature shipped in v5.31.0 ("feat: scoped mutations
(#7312)", https://github.com/TanStack/query/releases/tag/v5.31.0). The RFC
behind it (https://github.com/TanStack/query/discussions/7126) motivates it
with exactly citry's problem class: concurrent PATCHes to one resource,
out-of-order execution after offline resume, redundant intermediate
operations. React draws the same line: raw async transitions guarantee
nothing ("Actions within a Transition do not guarantee execution order",
called a known limitation, https://react.dev/reference/react/useTransition),
and the blessed path is the per-hook serial queue of `useActionState`:
"React queues and executes multiple calls to dispatchAction sequentially.
Each call to reducerAction receives the result of the previous call."
(https://react.dev/reference/react/useActionState, React 19).

The pattern across (a), (b), and (f): where serialization exists, it is
"serialize within one identity unit, parallel across other units, nothing
dropped". What happens to the queued work differs, three distinct drain
variants: run each queued item in turn (LiveView, `useActionState`,
TanStack scope, apollo-link-serialize), merge queued work into one
follow-up request (Livewire alone, source-verified), or keep only the
newest trigger (HTMX's default `queue "last"`).
The unit differs too (component, view, key, hook), and
**no surveyed system derives the unit from the component tree**, because
none of the data layers knows a tree and the server-driven frameworks never
needed one (Livewire's architecture dissolves the parent/child case, next
section). A tree-derived scope would be citry-novel, with the TanStack RFC
as the closest design discussion.

### The dead-target race: the field's three answers

The maintainer's exact scenario is a child's call in flight when a parent
re-render lands, so the response arrives addressed to a client identity
that the re-render retired. The field has three answers:

1. **Dissolve it structurally (Livewire).** `wire:id` is stable across
   re-renders and a parent's morph skips child roots entirely, so a parent
   re-render landing mid-flight cannot kill the child's client identity;
   responses are addressed by component id and always find their component
   (https://livewire.laravel.com/docs/3.x/understanding-nesting, v3;
   https://raw.githubusercontent.com/livewire/livewire/3.x/js/morph.js).
   The residual case, a child conditionally removed from the DOM while its
   request is in flight, appears to be handled without cancellation: the
   response merges into the in-memory component object and morphs its
   detached root invisibly, and the next parent commit prunes dead children
   from the snapshot before sending
   (`getEncodedSnapshotWithLatestChildrenMergedIn`,
   https://raw.githubusercontent.com/livewire/livewire/3.x/js/request/commit.js).
   This silent-discard-by-detachment behavior is inferred from source, not
   documented prose (unverified as a stated contract). The structural
   choice is worth naming because citry made the opposite one on purpose:
   fresh component ids per render and whole-subtree re-renders (so props
   flow and ids are never stale, events.md 5.3, 5.5) are what make the
   dead-target case real for citry while Livewire never needed an answer.

2. **Serialize it away, then no-op-ack the residue (LiveView v1.2.7).**
   Because the whole view is one process, a child event and a parent update
   cannot interleave; they queue. Component removal is additionally a
   two-phase handshake: the client sends `cids_will_destroy`, the server
   only marks components for deletion, the client re-checks after pending
   transitions whether a marked component came back, and only then sends
   `cids_destroyed` (source:
   https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/lib/phoenix_live_view/channel.ex
   and
   https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/assets/js/phoenix_live_view/view.ts).
   Server state outlives the DOM removal until the client confirms, so a
   racing event usually still finds a live target. If an event nevertheless
   arrives for a component id that no longer exists, the server
   acknowledges with an empty no-op reply so the client's loading and lock
   state resolves cleanly, and the event is dropped; the source comment
   marks it as an accepted race: "Due to race conditions, the browser can
   send a request for a component ID that no longer exists. So we need to
   check for the :error case accordingly." (channel.ex, v1.2.7). The
   historical record shows why the hardening exists: dead-CID races used to
   crash the client and freeze the UI
   (https://github.com/phoenixframework/phoenix_live_view/issues/1848,
   https://github.com/phoenixframework/phoenix_live_view/issues/759).

3. **Abort the loser (Unpoly 3.x).** A parent render aborts in-flight
   requests targeting fragments inside it by default, and destroying a
   fragment aborts requests targeted at it regardless of settings
   (https://unpoly.com/aborting-requests). The child's in-flight work is
   discarded rather than serialized, the sharp edge being that a child's
   slow save can be killed by a parent poll unless marked
   `{ abortable: false }`; the compensation is the richest surfacing in the
   field (dimension 3).

Citry's epoch guard (events.md 4.2) already implements a fourth variant for
the same-anchor half: never abort the server work, let every response
arrive, drop only the stale response's instance-mutating actions, and still
resolve the caller's promise with its `data`. That is closer to LiveView's
let-everything-run philosophy than to Unpoly's abort, but without locks:
newest wins on display, work is never killed. What the epoch guard does not
cover is the cross-anchor case (parent morph retires the child anchor),
which is precisely the open question in events.md 16.1 and the companion
analysis.

### Pros and cons ledger

**Per-unit serialization with merge (Livewire, LiveView, TanStack scope,
useActionState).** Pros: prevents the state-fork race by construction
(Livewire's v4 `#[Async]` warning, quoted in the executive summary, is the
maintainers' own statement that the queue is the only safe default for
UI-affecting state); merging means a burst of triggers costs one follow-up
request; ordering is trivially explainable. Cons: head-of-line blocking
within the unit, reported in every system that has the queue
(https://github.com/livewire/livewire/discussions/7081; LiveView's docs
steer slow work to `assign_async`); queue-bypassing writes stay dangerous
(Livewire's `$wire.set()` corruption, discussion 8776); and where the
display of queued work is deferred (LiveView's locks), the machinery has a
real bug tail (the four changelog entries cited above).

**Newest-wins abort (Unpoly, Turbo, Datastar).** Pros: dead simple, no
stale responses by construction, no queue to explain. Cons: in-flight work
is discarded, which is wrong for writes (a killed save is data loss from
the user's viewpoint); scoping matters enormously (Unpoly's per-subtree
scoping is livable, Turbo's global scoping is only livable because Drive is
page-level; Datastar's URL-plus-method key can couple unrelated
components, an unverified implication of the documented "auto" semantics);
and every abort needs surfacing or it becomes silent data
loss.

**Per-pair policy setting (HTMX hx-sync).** Pros: policy is local,
declarative, composable per pair, and inheritance lets a form impose policy
on its inputs. Cons: the default `drop` is fully silent (dimension 3); the
developer must reason per element pair rather than getting one framework
rule; and nothing names the sync policy in any event when it fires, so
debugging a dropped request means reading attributes.

**Cross-component bundling (Livewire v3).** Orthogonal to ordering but
worth recording: commits from independent components in the same 5ms window
share one HTTP request, cutting connection overhead, and bundling is what
lets parent and child commits ride together for `#[Reactive]` props
(https://livewire.laravel.com/docs/3.x/bundling). The con is latency
coupling (one slow component delays the bundle), which is exactly what
`#[Isolate]` exists to fix. Citry's envelope already reserves the shape
(`calls[]` is an array from day one, same-tick coalescing is a v2 client
feature, events.md 4.2), so this is a paved path, not a new decision.

## Dimension 3: what developers see when work fails or is dropped

### Supersession is silent almost everywhere

Across the whole survey, superseded (not failed) work is dropped silently:
an interrupted React transition render, a replaced Apollo optimistic layer,
a TanStack refetch cancelled by `cancelQueries` inside `onMutate`
(https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates),
a Livewire action merged into a queued commit (never dropped, so never
surfaced), a LiveView patch applied invisibly to a locked element's clone.
No surveyed framework fires a developer callback for supersession; only
failures get callbacks. The two partial exceptions are Unpoly, which fires
`up:fragment:aborted` on the aborted fragment plus `up:request:aborted` at
the network layer and rejects the programmatic caller's promise with
`up.AbortError` (https://unpoly.com/aborting-requests), and Datastar, which
routes everything through one typed lifecycle event (`datastar-fetch` with
`detail.type` of started, finished, error, retrying, retries-failed,
https://data-star.dev/reference/actions). Citry's designed
`citry:events:stale` event (events.md 5.2, surfacing the epoch drop rule of
4.2) is therefore already **more** observable than the field norm, sitting
between Unpoly's per-fragment event and Datastar's single typed event.

The cautionary tale on the other end is HTMX, scoped precisely: a request
suppressed by `hx-sync`'s default `drop` strategy is fully silent (the
source returns early and fires nothing; verified in
https://raw.githubusercontent.com/bigskysoftware/htmx/master/src/htmx.js),
while a request killed by the `abort` or `replace` strategies does surface,
but only through the generic `htmx:sendAbort` event
(https://htmx.org/reference/); no event names the sync policy as the cause
in either case. So the failure mode to design against is specifically the
silent default drop, and secondarily the anonymous abort.

### Failure surfacing

- **Livewire v3**: a non-2xx response runs all commit-level and
  request-level `fail` callbacks, then (unless a hook called
  `preventDefault()`) status 419 shows the built-in "page expired" dialog
  and other errors open a full-screen modal rendering the server's error
  HTML; a network failure runs the fail callbacks with
  `{ status: 503, content: null }` and shows no modal
  (https://raw.githubusercontent.com/livewire/livewire/3.x/js/request/index.js).
  The developer hook for a custom toast is `Livewire.hook('commit', ...)`
  (per component, per round trip) and `Livewire.hook('request', ...)` whose
  `fail` receives `preventDefault`
  (https://livewire.laravel.com/docs/3.x/javascript). The gap the source
  shows and the docs do not state: an action's `$wire.call()` promise
  resolvers are invoked only on the success path, so `await $wire.call(...)`
  never settles on a failed request (source-verified in
  https://raw.githubusercontent.com/livewire/livewire/3.x/js/request/commit.js).
  Error surfacing is hook-based, not per-await. A citry promise that
  rejects with the structured error envelope (events.md 5.2, 3.7) is
  strictly better ergonomics than this default.
- **LiveView v1.2.7**: declarative bindings get no per-event error channel
  at all; surfacing is coarse and stateful (loading classes persist until
  all in-flight events resolve,
  https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/guides/client/syncing-changes.md).
  Hooks get the only per-event channel: `pushEvent` returns a promise that
  rejects on error or timeout, while "the callback version silently ignores
  errors" (https://hexdocs.pm/phoenix_live_view/js-interop.html). A push
  timeout is treated as unrecoverable: the client logs "received timeout
  while communicating with server. Falling back to hard refresh for
  recovery" and reloads
  (https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/assets/js/phoenix_live_view/view.ts).
  A handler exception crashes the process and the client remounts: "Once
  the client notices the error, it will remount the LiveView"
  (https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/guides/server/error-handling.md).
  The philosophy is drop-silently-and-converge, with hooks as the opt-in
  path for anyone needing a toast.
- **The data layers**: TanStack pairs per-mutation `onError` with one
  global `MutationCache` `onError` for app-wide toasts, and splits
  `mutate()` (errors only into callbacks) from `mutateAsync()` (rejects)
  (https://tanstack.com/query/latest/docs/framework/react/guides/mutations).
  Documented sharp edge: callbacks passed to a `mutate()` call fire only
  for the latest call and only if the component is still mounted, while
  hook-level callbacks fire for every call. React 19's `useActionState`
  splits expected errors (returned as action state) from unexpected ones
  (thrown to the nearest error boundary), and on a thrown error "React
  cancels all queued actions" in that hook's queue
  (https://react.dev/reference/react/useActionState): the blessed behavior
  for work queued behind a failure is drop the queue and surface one error.

### Dead targets, specifically

When a response or message addresses a component that left the DOM:

- LiveView acks the event with an empty no-op reply so the client's
  loading and lock state resolves cleanly, then drops it, with no log on
  either side (the `push_noop` path in channel.ex, v1.2.7). A server-side
  `send_update` to a removed component logs at **debug** level:
  `Logger.debug("send_update failed because component with CID ... does not
  exist or it has been removed")`; the adjacent code comment explains the
  choice informally as "Only a warning, because there can be race
  conditions"
  (https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/lib/phoenix_live_view/channel.ex).
  A `phx-target` selector matching nothing is a client console error and
  the event is not sent (view.ts, v1.2.7).
- Livewire's lookup of a destroyed component throws a bare string
  `'Component not found: ' + id`, surfacing as an uncaught console error
  outside any hook
  (https://raw.githubusercontent.com/livewire/livewire/3.x/js/store.js).
- TanStack's per-call callbacks silently stop firing after unmount while
  hook-level and global-cache callbacks still fire (mutations guide,
  above): the field pattern is component-level callbacks drop, global-level
  hooks survive.

The LiveView no-op ack is the load-bearing precedent for citry: whatever
else happens to a response addressed to a retired anchor, the caller's
promise must settle and the busy state (`data-citry-busy`, `$loading`) must
clear, or the UI wedges the way pre-hardening LiveView did (issue 1848).

## Recommendations

### R1: preservation, keep the designed stack and treat the focused rule as real work

Adopt all of: user-authored `c-key` for matching (5.3 as written),
`data-citry-morph="ignore"` as the whole-subtree marker (5.3 as written),
the narrow focused-control rule (focused **and** two-way-bound, keep the
live value), the updates piggyback as the lifted-input-state story (4.2,
5.5 as written), and `data-citry-busy` plus `$loading` as the
disable-while-loading story. This is not a menu; the field grew all five
everywhere it morphs by default, and each mechanism covers a failure class
the others do not (keys: reordering lists; marker: third-party DOM; focused
rule: the one input mid-keystroke; piggyback: polls over drafts; busy
state: double-submit).

Three specifics the field evidence sharpens:

- **The focused-element rule is net-new runtime work, and its narrowness is
  the design.** `@alpinejs/morph` ships no focused-element handling (source
  check, https://raw.githubusercontent.com/alpinejs/alpine/main/packages/morph/src/morph.js),
  so `keepLiveValue` in the `updating` hook is citry code. Ground it on
  LiveView's always-on rule (the strongest player,
  https://hexdocs.pm/phoenix_live_view/form-bindings.html v1.2.7), and test
  it against both recorded failure directions: absence (morphdom #135,
  focus and caret loss per keystroke) and blanket protection (Turbo #1194,
  a form that cannot be cleared after submit). The submit-then-clear case
  is the acceptance test: a handler that legitimately empties a bound field
  which still has focus must win. Citry's scoping to two-way-bound controls
  plus the reconcile rule's "server wins except pending unsent writes"
  (5.5) is designed to pass it; verify, do not assume.
- **Frame `c-key` strongly for child components in loops.** Livewire's
  docs escalated from "recommended" to "will behave incorrectly without
  them" for exactly this case (https://livewire.laravel.com/docs/nesting,
  v4), and "add wire:key" is that ecosystem's most repeated fix. Citry's
  one-line guidance (5.3) is right for plain elements; child instances in
  a `<c-for>` deserve the stronger wording.
- **Expect the per-attribute preservation request; do not build it yet.**
  Every long-lived morph framework added one (LiveView
  `JS.ignore_attributes` v1.1, Turbo `turbo:before-morph-attribute`,
  Datastar `data-preserve-attr`) after users hit browser-owned attributes
  like `open` on `<details>`. The reserved `"ignore-self"` marker value
  (5.3) plus this note is enough for now.

**Falsifiers.** If the dogfood port (events.md section 13) hits a case
where the focused rule fights a legitimate server clear even with the
narrow scoping, the rule needs an opt-out or a further condition, and Turbo
#1194 says find it before shipping, not after. If unkeyed `<c-for>` child
instances misbehave in the dogfood port even without reordering, the
Livewire-strength wording ("will behave incorrectly") becomes the citry
wording too.

### R2: concurrency, serialize per anchor with merge, answer parent/child with drop plus surface

For **same-anchor** overlap (two sends from one instance), serialize with
merge: at most one in-flight call per anchor, later sends coalesce and
follow as one request. The serialize-per-unit half is the field's
convergent shape (Livewire per component, LiveView per view, React
`useActionState` per hook, each with nothing dropped). The merge half is
Livewire's specific drain variant, alone among the surveyed systems
(source-verified; LiveView and `useActionState` instead run each queued
item in turn). Merge is chosen here on Livewire's precedent plus citry's
own envelope, which already reserves the carrier (`calls[]` plus the
updates piggyback, 4.2); the maintainers of the largest queue-owning
system also state serialization as the only safe default for UI state
(the v4 `#[Async]` warning). The epoch guard stays as the safety net for whatever still
races (transport reordering). Head-of-line blocking, the queue's documented
cost, is acceptable at anchor granularity because an anchor is one
interactive position, not a page; the field's pressure valve (an explicit
fire-and-forget escape like `#[Async]`) can wait for demand, and if built
must carry the same never-for-UI-state warning Livewire wrote.

For **parent/child** overlap (the dead-target race), take the drop plus
surface option in v1, not the policy setting and not the full subtree
queue:

- **Against the policy setting**: one field precedent exists, HTMX's
  `hx-sync`, an inherited per-element-pair policy where an ancestor imposes
  conflict behavior on descendants (canonical form:
  `hx-sync="closest form:abort"`, https://htmx.org/attributes/hx-sync/).
  Its documented weaknesses argue against copying it rather than for it:
  the default strategy drops requests fully silently, nothing names the
  policy as the cause when it fires, and correctness depends on developers
  reasoning per pair. The silent-drop weakness, to be fair, is an HTMX
  implementation flaw that R3's every-drop-fires-an-event rule would cure,
  not an intrinsic property of policy settings; the rejection rests on the
  remaining two legs: the per-pair reasoning burden, and the preference
  for one framework-level rule with a single observable outcome for
  citry's audience.
- **Against the subtree queue (for v1)**: no surveyed system implements
  "nested serialize, siblings parallel" derived from a component tree; the
  pieces exist separately (Livewire's per-component queue, Unpoly's
  per-subtree conflict detection, TanStack's `scope.id`), so it is
  buildable but citry-novel. Two field warnings apply: head-of-line
  blocking grows with the subtree (LiveView's whole-view queue is the
  worked example of the coarse end, tolerable only because its escape is
  off-process async work), and deferred-application machinery has a real
  bug tail (LiveView's four lock-related changelog fixes). Most
  importantly, if the companion nested-anchor analysis lands continuity
  (the child's anchor survives the parent morph), the response is no longer
  addressed to a dead target and the queue's main justification evaporates;
  decide continuity first.
- **For drop plus surface**: it is the citry-consistent answer. The epoch
  guard already embodies the philosophy (never abort server work, drop
  stale DOM effects, resolve the caller's promise, fire an event, 4.2 and
  5.2); LiveView's no-op ack shows the hygiene a drop needs (settle the
  promise, clear busy state, accept the race explicitly in a comment);
  Unpoly shows the surfacing ceiling (a per-fragment event plus a rejected
  promise). Server-side handler effects still commit (citry never cancels
  the request), which distinguishes this from Unpoly's abort: the drop is
  of client application, not of work.

**Falsifiers.** If the dogfood port shows users actually losing visible
work to parent-poll-versus-child-save collisions at a rate a toast cannot
excuse, the subtree queue gets designed for v2, with TanStack's RFC
(https://github.com/TanStack/query/discussions/7126) and
apollo-link-serialize as the key-scoped references and the anchor tree
supplying the key. If same-anchor serialization's head-of-line blocking
turns out to bite real components (a slow save blocking a fast toggle on
one anchor), the escape hatch moves up the priority list, warning included.

### R3: surfacing, one observable event per drop, and every promise settles

- **Every drop fires one DOM event with a reason.** Citry already commits
  to `citry:events:stale` for epoch drops (5.2) and reuses it for
  version-skew staleness (4.5). Extend the same event (a `reason` field on
  the detail, or a sibling event if the maintainer prefers) to the
  dead-target drop from R2, so all three drop causes are observable through
  one listener. The field norm is silence for supersession; the two
  frameworks that do surface it (Unpoly's `up:fragment:aborted`, Datastar's
  typed `datastar-fetch`) are the models, and HTMX's silent `hx-sync` drop
  default is the anti-model. This gives the maintainer's "developer-facing
  callback for surfacing a toast" for free: it is an ordinary
  `document.addEventListener`, the same pattern as the existing
  `citry:events:error` toast example (5.2).
- **Every promise settles.** The field's worst ergonomic gap is
  source-verified in Livewire v3: failed calls leave `await` hanging
  forever. Citry's design already settles everything (stale still resolves
  with `data`, errors reject with the structured envelope); the WP16
  addition is making the dead-target branch explicit: when a response's
  target anchor is gone, resolve the caller's promise with its `data`,
  clear `data-citry-busy` and `$loading`, fire the drop event, and log at
  debug level, mirroring LiveView's no-op ack and its debug-level
  `send_update` log (v1.2.7 channel.ex). Never a console throw for a
  routine race (Livewire's `'Component not found'` string is the
  anti-model).
- **Keep the toast pattern two-tier.** Per-call promise rejection for
  local handling plus the global `citry:events:error` listener for
  app-wide toasts is exactly TanStack's per-mutation-callback plus
  `MutationCache.onError` pairing, the most-liked surfacing design in the
  survey; 5.2's examples already show it. Document that per-call handlers
  die with their caller and the global listener is the reliable tier (the
  TanStack unmount lesson).

**Falsifier.** If the drop event fires so often under normal fast typing
that developers tune it out (5.2 already notes staleness is normal under
fast typing), split the noisy epoch-drop reason from the rare dead-target
reason so the latter stays actionable; the default handling stays a debug
breadcrumb either way, per 5.2's example.

## Where the inputs disagreed, and what stays unverified

### Disagreements between the research passes, resolved here

- **"Every serious library special-cases the focused element" (morph
  libraries pass) versus grep-verified absence in Alpine morph and
  Livewire (Livewire pass).** The consensus claim was wrong; the corrected
  three-way split (LiveView always-on rule / idiomorph focus-restore by
  default with value protection opt-in / morphdom, Alpine morph, and
  Livewire's morph layer: nothing) is what this document states, with the
  consequence for citry called out in R1.
- **"Livewire is the opposite pole of citry's lean" (Livewire pass) versus
  "citry's lean is exactly the idiomorph/Livewire consensus" (morph
  libraries pass).** Both are right at their layer: Livewire's defaults
  preserve because of architecture; its mechanisms are the same
  opt-in-identity toolkit citry plans. Detailed at the end of dimension 1.

### Unverified claims register

Each of these is also marked inline where used:

- Turbo 8: absence of a cross-frame request queue, and absence of a
  dedicated cancelled-visit event, are inferred from documentation absence
  only (https://turbo.hotwired.dev/handbook/drive,
  https://turbo.hotwired.dev/reference/events).
- Turbo issue 1210 (Stimulus values reset by morph) and the Hotwire
  discussion on `data-turbo-permanent` under turbo-stream updates: titles
  verified via search, threads not read in full.
- Datastar v1: that URL-plus-method cancellation lets two components
  sharing an endpoint cancel each other is an implication of the documented
  `'auto'` semantics, not a documented statement; SSE cross-request
  ordering has no documented guarantee either way
  (https://data-star.dev/reference/actions).
- Livewire v3: the detached-child silent-merge behavior (response morphs a
  detached root invisibly, next commit prunes it) is inferred from source
  (commit.js), not documented prose.
- TanStack Query: the claim that resumed offline mutations ran serially
  across scopes before v5.31.0 and in parallel after surfaced in docs
  search results naming v5.29.2 and v5.31.0, but could not be pinned to a
  currently readable docs page; treat the direction as plausible and the
  version boundary as soft. The scope feature's v5.31.0 release itself is
  verified (https://github.com/TanStack/query/releases/tag/v5.31.0).

Confirmed since the research passes ran: Turbo issue
https://github.com/hotwired/turbo/issues/1194 is verified in full (exact
title "Morphing: impossible to clear a form due to ignoreActiveValue:
true"; the option was added in PR 1141, the issue was closed via PR 1195,
and current main passes no `ignoreActiveValue`, verified in
src/core/morphing.js).

## How this document was produced

Four research passes, one per cluster (Livewire v2/v3/v4; Phoenix LiveView
v1.2.7; the hypermedia cluster HTMX 2.x, Turbo 8, Unpoly 3.x, Datastar v1;
the morph libraries plus client data layers), each working from official
docs, framework source on GitHub, and issue trackers, with claims
source-verified where the framework's code is public. An adversarial
fact-check pass then re-verified claims against sources; its corrections
(the focused-element split, the `hx-sync` event scoping, LiveView's
`send_update` log level, the Turbo 1194 confirmation, the TanStack version
pinning, and the events.md section references) are incorporated above.
Citry mappings were checked against [`../events.md`](../events.md) sections
4.2, 4.5, 5.2, 5.3, 5.5, and 16.1 as of 2026-07-14.

## Primary sources by framework

Livewire (v3 unless noted):
https://livewire.laravel.com/docs/3.x/morphing,
https://livewire.laravel.com/docs/3.x/understanding-nesting,
https://livewire.laravel.com/docs/3.x/wire-model,
https://livewire.laravel.com/docs/3.x/wire-ignore,
https://livewire.laravel.com/docs/3.x/wire-loading,
https://livewire.laravel.com/docs/3.x/bundling,
https://livewire.laravel.com/docs/3.x/javascript,
https://livewire.laravel.com/docs/4.x/actions (v4),
https://livewire.laravel.com/docs/nesting (v4);
source (3.x branch): js/request/bus.js, js/request/pool.js,
js/request/commit.js, js/request/index.js, js/morph.js, js/component.js,
js/features/supportDisablingFormsDuringRequest.js,
js/features/supportIsolating.js, js/store.js (all under
https://raw.githubusercontent.com/livewire/livewire/3.x/), and
js/component/index.js on the 2.x branch;
discussions/issues: 8776, 7081, 8992, 4709, 7160, 6456, 7937, 687 (all
under https://github.com/livewire/livewire/).

Phoenix LiveView (v1.2.7 unless noted):
https://hexdocs.pm/phoenix_live_view/form-bindings.html,
https://hexdocs.pm/phoenix_live_view/js-interop.html,
https://hexdocs.pm/phoenix_live_view/Phoenix.LiveComponent.html;
guides and source at
https://raw.githubusercontent.com/phoenixframework/phoenix_live_view/v1.2.7/:
guides/client/syncing-changes.md, guides/client/bindings.md,
guides/server/error-handling.md, lib/phoenix_live_view/channel.ex,
assets/js/phoenix_live_view/dom_patch.ts, element_ref.ts, view.ts,
constants.ts, CHANGELOG.md (and v1.1.14/CHANGELOG.md);
https://www.phoenixframework.org/blog/phoenix-liveview-1-1-released;
issues 1848, 759, 866, 3941, 4209, 4291 (under
https://github.com/phoenixframework/phoenix_live_view/).

Hypermedia cluster:
https://htmx.org/attributes/hx-sync/, https://htmx.org/attributes/hx-preserve/,
https://htmx.org/attributes/hx-trigger/, https://htmx.org/reference/,
https://raw.githubusercontent.com/bigskysoftware/htmx/master/src/htmx.js;
https://turbo.hotwired.dev/handbook/page_refreshes,
https://turbo.hotwired.dev/handbook/drive,
https://turbo.hotwired.dev/reference/events,
https://raw.githubusercontent.com/hotwired/turbo/main/src/core/morphing.js,
https://raw.githubusercontent.com/hotwired/turbo/main/src/core/drive/navigator.js,
Turbo issues 1194, 1083, 1210 and PRs 1141, 1195 (under
https://github.com/hotwired/turbo/),
https://discuss.hotwired.dev/t/data-turbo-permanent-is-recreated-on-updating-form-with-turbo-stream/6202,
https://thoughtbot.com/blog/turbo-morphing-woes,
https://fly.io/ruby-dispatch/8-turbo-8-gotchas/;
https://unpoly.com/aborting-requests, https://unpoly.com/up-keep,
https://unpoly.com/watch-options, https://unpoly.com/up.network.config,
https://unpoly.com/changes/3.0.0;
https://data-star.dev/reference/attributes,
https://data-star.dev/reference/actions,
https://data-star.dev/guide/backend_requests.

Morph libraries and data layers:
https://github.com/patrick-steele-idem/morphdom (and
src/specialElHandlers.js, issue 135),
https://www.npmjs.com/package/@retailmenot/morphdom-plugins,
https://github.com/bigskysoftware/idiomorph,
https://alpinejs.dev/plugins/morph,
https://raw.githubusercontent.com/alpinejs/alpine/main/packages/morph/src/morph.js,
Alpine issues/discussions 3120, 3097, 2826 (under
https://github.com/alpinejs/alpine/);
https://www.apollographql.com/docs/react/performance/optimistic-ui,
Apollo issues 3715, 5706, https://github.com/helfer/apollo-link-serialize,
https://github.com/adobe/apollo-link-mutation-queue;
https://tanstack.com/query/v5/docs/framework/react/guides/mutations,
https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates,
https://github.com/TanStack/query/discussions/7126,
https://github.com/TanStack/query/releases/tag/v5.31.0;
https://react.dev/reference/react/useTransition,
https://react.dev/reference/react/useOptimistic,
https://react.dev/reference/react/useActionState.
