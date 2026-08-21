# A2 client ownership graph

**Status:** implementation contract for A2, locked 2026-07-21.

This note records the production result of A2 in
[`../alpinejs_plan.md`](../alpinejs_plan.md). A1 captures ownership before
rendering flattens it. A2 serializes the selected records, marks their exact
physical occurrences, and commits one validated transaction in the browser.
A3 still owns the general live registry and permanent Alpine hook broker.

The versioned wire package is the protocol source of truth:
[`../../../packages/protocol/client_graph/v1/spec.md`](../../../packages/protocol/client_graph/v1/spec.md).

## 1. Compile nested-tag browser bindings before serialization

A **component-tag client binding** is `$c-props`, an Alpine event handler such
as `@click`, or a Citry handler such as `@c-save` or `@c-poll.5s`, resolved
from a nested `<c-*>` tag. The parent owns its expression or server handler,
while the child supplies the component boundary where the browser applies it.
A2 replaces A1's opaque Citry-handler binding value
with a discriminated payload before serialization:

- `props` and `alpine-handler` carry one Alpine expression;
- `citry-dom-event` carries the source parent's class, event, declared server
  handler, optional raw Alpine argument expression, and compiled modifiers;
- `citry-poll` carries the source parent's class, declared server handler,
  optional raw Alpine argument expression, and interval.

Ordinary element bindings and Citry component-tag client bindings use the same
strict server-handler parser. An exact declared handler name is valid. The
call form uses the first `(` and the final non-whitespace `)` as its outer
shell, preserves the non-empty interior verbatim, and rejects trailing text.
Parentheses inside strings, templates, regular expressions, or nested
expressions are opaque to this parser. `handler()` normalizes to the same
no-argument form as `handler`.

Direct, `c-@c-*`, and `c-bind` winners compile against the component where the
tag was authored. A handler declared only by the physical child cannot satisfy
a parent-authored binding.

## 2. Manifest and source coordinates

The server emits one deterministic `citry-client-graph/1` manifest. Its
revision is lowercase SHA-256 of the compact, recursively key-sorted manifest
without the `revision` member. Strings are written inline (a render id, class
id, name, or expression is the JSON string itself); source text is not
serialized. A top-level `mode` (`production` or `development`) selects whether
the manifest carries source provenance: development fills `sourceLocations`
and its references, while production keeps that required collection empty and
nulls every reference (see [`../dev_prod_mode.md`](../dev_prod_mode.md)). The
literal prefix of the physical comment markers is declared by the top-level
`delimiters` member, `{ "format": "citry:g1" }`. Every marker starts with
that value followed by the first eight characters of the manifest revision.
The manifest and every logical graph index retain the complete revision.

In development each location's `sourceOffset` holds half-open UTF-8 byte offsets
into the executed source after `on_template_loaded` hooks (not author-file
coordinates), and its `sourcePos` holds a diagnostic line and column. Each
location also records its origin, mapping key or index when applicable,
logical source owner, class, and physical carrier instance. These offsets are
provenance for tooling; the browser validates their shape but does not act on
them, and production carries no source-location records.

The server aggregates ownership graphs reachable from the final render tree
in physical first-seen order. Pre-rendered subtrees owned by the same `Citry`
instance are accepted as distinct graphs when their relationships remain
graph-local. A delayed result kept after its original render is rejected when
its parent or ownership edge crosses graphs because v1 has no graph-qualified
render reference. A tree
mixing different `Citry` instances is also rejected. Snapshots are taken after
deferred descendants settle, and serialization fails if a graph changes after
preparation. Reusing one concrete component render or one concrete slot
occurrence in two physical positions is rejected instead of cloning its
identity.

Only active records reachable from selected output are serialized. Every
selected nested-component invocation must have settled render-queue work.
Only selected fill occurrences receive physical regions; discarded or inert
fills do not receive speculative caps.

Stringifying a settled same-graph subtree inside a render hook creates a
standalone fragment boundary. A component instance whose parent and creating
invocation remain outside that subtree is rebased as a fragment root. An outer
fill wrapper is omitted only when it contains no direct Alpine directive; an
Alpine directive inside a nested component belongs to that isolated component
and does not make the wrapper projecting. If the wrapper itself needs caller
projection, serialization fails closed because v1 cannot name the absent
source. Delayed content crossing from a foreign ownership graph remains an
error.

## 3. Physical range caps

Every serialized logical instance and selected fill occurrence has one exact
start and end comment pair:

```text
<!--citry:g1:<revision-alias>:<graph>:i:<instance-id>:s-->
<!--citry:g1:<revision-alias>:<graph>:i:<instance-id>:e-->
<!--citry:g1:<revision-alias>:<graph>:r:<region-id>:s-->
<!--citry:g1:<revision-alias>:<graph>:r:<region-id>:e-->
```

The eight-character alias keeps server-rendered HTML readable; it is not the
graph identity. The browser maps it to one complete live or provisional
revision. If another complete revision has the same alias while that mapping
is active, staging rejects the incoming graph before publication. Abort,
discard, and inactive-revision pruning release the mapping.

The wrapper that carries a selected slot occurrence survives until final
serialization, including text-only and empty results. This avoids equality or
string-interning guesses for adjacent and mirrored output. Instance caps wrap
the exact component frame. Region caps wrap the exact selected occurrence.

Caps are balanced, properly nested, non-crossing, unique, and normally share
one parent. A complete rootless HTML document has one narrow parser exception:
an opening cap may remain under `Document` while its closing cap is placed in
the implicit `body`. No other split-parent pair is accepted.

The representation works in single-root, multi-root, rootless, adjacent,
nested, mirrored, table, select, and SVG cases without adding an element.
Deployments using client-active Citry behavior must preserve these comments.

## 4. Emission and activation order

`document` and `fragment` output emit graph data only when the final tree has
client-active ownership behavior, including `$component`, client bindings,
Events, or State. `simple` and `ignore` output contain neither graph comments
nor a graph manifest.

The dependency pipeline emits, in order:

1. the core dependency manager or fragment preloader;
2. `data-citry-graph`;
3. `data-citry-events`, when present;
4. `data-citry` dependency calls.

The Events and dependency manifests name the graph revision they require.
Inserted subtrees are scanned for graph tags before either dependent manifest
is processed.

When an initial parser-created document places `<c-js>` before its outer
component's closing cap, graph adoption waits for `DOMContentLoaded`. A
graph-linked dependency transaction runs in the next task, after Events graph
waiters and mutation observers have applied the Events manifest. Events first
stages every class descriptor and instance entry without touching its live
registries, then explicitly acknowledges success or failure to the graph
registry. Component callbacks wait for that acknowledgment and are discarded
after failure, so they never observe a partially adopted set of Events
anchors.

## 5. Atomic browser staging

The core dependency manager owns the minimal A2 revision registry. Before a
revision is visible it validates:

- exact fields, protocol, mode, and the literal `citry:g1` comment prefix;
- the canonical SHA-256 revision;
- in development, the source locations (their kind, owner, and byte ranges);
  in production, that no source-location records or references are present;
- integer bounds, dense graph IDs, record uniqueness, and known references;
- source-owner, class, carrier, client binding, and component-execution-order
  constraint consistency;
- bidirectional component-instance-to-nested-component endpoint agreement;
- fill owner/source-location and receiver/fallback-location agreement;
- slot-region-to-fill agreement, scope transitions, and acyclic slot-region
  ancestry;
- component execution-order acyclicity;
- every expected physical cap, with no missing, duplicate, crossed, or
  malformed pair, plus agreement between logical slot-region/nested-component
  ancestry and physical nesting.

These correctness checks run in production as well as development. Only the
source-location checks are development-only. The protocol has no fixed
manifest byte ceiling; CI payload budgets catch architectural size regressions
without rejecting a valid large graph at runtime.

The browser indexes nested-component targets, open slot regions, and slot
regions by fill while it stages the graph, so those checks do not repeatedly scan whole
collections. Record-reference and physical-cap validation therefore grow
linearly with the records and comments they inspect.

The decoded record arrays are frozen before commit. No record or callback is
exposed while validation is incomplete. A failed revision rejects registered
waiters and discards dependency manifests blocked on it. Prior committed
revisions remain unchanged.

One concrete graph revision may supply one dependency transaction and one
Events transaction. Non-cloneable `WeakSet` identity makes moving an already
processed tag node a no-op. The preserved `data-*-processed` attributes are
diagnostic only. A cloned or independently created tag is a fresh node even
when it copied that attribute, so it enters normal duplicate-revision
validation. A fresh tag that repeats an already committed revision is
rejected, and its dependent manifests cannot replay component callbacks or
Events adoption. A fresh render must produce a fresh physical graph revision.
After A8, a fully inactive revision may be pruned from the public and internal
registries. A separate used-revision tombstone remains, so pruning does not
make replay valid.

## 6. Acceptance and remaining boundary

Server tests lock deterministic golden output, client binding discrimination, UTF-8
source offsets, same-owner graph aggregation, foreign-owner rejection,
single/multi/rootless/nested/mirrored caps, static output absence, concrete
occurrence reuse failure, and realistic payload size. Protocol fixtures are
checked independently against the published schema and semantic validator.

Chromium, Firefox, and WebKit acceptance covers initial rootless documents,
malformed and partial transactions, waiter rejection, fragment insertion,
resigned endpoint and region-ancestry corruption, cloning an already processed
tag, atomic rejection of a malformed later Events instance, callback blocking,
Events replay rejection, and table/select/SVG contextual fragments. Protocol
tests separately lock fill/source ownership and the production/development mode
invariant (production carries no source provenance).

A2 does not attach Alpine scopes, resolve `$c-props`, attach component-tag
handlers, adopt graph revisions across morphs, or replace the Events anchor.
A3 through A8 implement those client layers. The A8 Events render applier now
preserves the incoming A2 graph tag and comment caps, validates graph-linked Events and
dependency packages before DOM mutation, and commits them through one
graph-aware morph transaction. The canonical `citry-client-graph/1` wire
package remains unchanged; any extra selector-targeted copies use
client-owned runtime placement caps rather than duplicating canonical server
records. Detached package errors leave the old page unchanged. An unexpected
failure after DOM mutation fails closed by retiring incoming ownership,
removing the live target DOM, rejecting waiters, and releasing the adoption
hold; it does not promise arbitrary DOM restoration.

One resilience follow-up remains separate from manifest size: ancestry checks
and deep freezing still use recursive walks in the browser, and the reference
validator's cycle checks are recursive too. A pathologically deep graph can
therefore reach a language call-stack limit even though its byte size is valid.
Before claiming arbitrary nesting depth, replace those walks with iterative
ones and add focused depth stress tests.
