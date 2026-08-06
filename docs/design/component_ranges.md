# Component ranges: component identity above DOM roots

**Status (2026-08-04): implemented.** Component identity, keyed and unkeyed
correspondence, range-level morph policy, ancestor-ordered ignore planning,
and transactional graph/DOM adoption follow this design. Component-tag keys
and ignore markers are range-owned metadata and are never projected onto a
rendered root element.
[`alpinejs.md`](alpinejs.md) describes how the range planner participates in
the wider client transaction.

This document owns Citry's component-range model: what the browser treats as
the component node after a `<c-*>` tag renders away, how that node matches
across updates, where parent-authored morph metadata lives, and how range and
element ignore barriers affect DOM and client-graph adoption. The exact JSON
shape remains owned by the
[`citry-client-graph/1` specification](../../packages/protocol/client_graph/v1/spec.md).
Alpine scopes and root projections remain owned by
[`alpinejs.md`](alpinejs.md), Events and State by
[`events.md`](events.md), and cached render artifacts by
[`caching.md`](caching.md).

---

## 1. Prior art

The design extends mechanisms already in production:

- **The client graph separates an invocation from its placement.** A
  `NestedComponent` connects an authored component-tag occurrence to the
  component it produced. It does not use a root element as the invocation
  record (`packages/protocol/client_graph/v1/spec.md:182`, `:382-407`).
- **Every graph-included component has exact ownership caps.** One start/end
  comment pair brackets single-root, multi-root, text-only, or empty output.
  Slot regions use their own distinct cap kind
  (`packages/protocol/client_graph/v1/spec.md:692-743`).
- **A component key already belongs to the virtual range.** The compiler
  extracts component-tag `#c-key` separately from ordinary attributes
  (`crates/citry_template_parser/src/compiler.rs:931-1035`). The server records
  it on the invocation (`packages/py/citry/citry/ownership.py:196-212`), and
  the graph sends it as `morphKey`. It is never stamped onto a child root.
- **The browser already treats matched keyed ranges as atomic virtual nodes.**
  It plans keyed direct-child correspondence top-down, keeps stationary ranges
  connected, moves complete ranges when necessary, and recursively applies
  fresh HTML inside a match (`packages/py/citry/citry/ext/dependencies/client/citry.js:1867-2160`,
  `:4428-4555`). The empirical basis and browser matrix live in
  [`spike-keyed-component-ranges.md`](alpinejs/spike-keyed-component-ranges.md).
- **Logical component facilities already project onto concrete roots.** One
  `RootGroup` supplies Alpine scopes, component-tag client bindings, handlers,
  busy state, and provide/inject integration to every current element root
  (`docs/design/alpinejs.md:733-923`). Mirrors already separate one logical
  lifetime from several physical placements (`docs/design/alpinejs.md:886-929`).
- **Citry already repairs framework-owned root markers after some Alpine
  skips.** Transition handling refreshes only graph-owned `data-cid` and
  `data-cid-*` projections while preserving Alpine and author-owned attributes
  (`docs/design/alpinejs.md:997-1010`).

Two production orderings are insufficient for a general ignore barrier:

1. The range adapter recursively morphs stationary nested ranges before the
   enclosing Alpine element walk reaches its `updating` hook
   (`citry.js:2087-2099`, then `:2122-2159`). An ordinary ignored element can
   therefore have a nested component updated before Alpine skips the element.
2. The Events applier begins linking the incoming graph before DOM morphing
   starts (`packages/js/citry-client/src/citry-events.ts:4398-4505`, then
   `:4524`). Discovering an ignored branch during the later Alpine hook cannot
   prevent callbacks, dependencies, or ownership records in that branch from
   being adopted.

The component range and its caps are therefore established prior art. This
design changes the order in which Citry plans range and element work, and adds
range-owned morph policy to the same invocation channel as the component key.

## 2. Why the component is a virtual node

An authored component tag does not survive rendering:

```citry-html
<c-Card #c-key="card.id" />
```

The result may be one element, several sibling elements, text, or no DOM nodes
at all. None of those shapes provides one root element that can carry the
component's identity. A child root can also have its own ordinary element key:

```citry-html
{# Parent template: component identity. #}
<c-Card #c-key="card.id" />

{# Card template: element identity. #}
<article #c-key="layout_variant">
  {{ title }}
</article>
```

The component key and element key answer different questions. The first
matches a component invocation and preserves its browser lifecycle. The second
matches an element inside that component's current output. Putting both on the
root element collapses those two identities and cannot represent multi-root or
rootless components.

`#c-ignore` has the same placement distinction:

```citry-html
{# Parent freezes the complete Card component. #}
<c-Card #c-ignore />
```

```citry-html
{# Card freezes one ordinary element. Other roots can still update. #}
<div class="chart" #c-ignore>
  <canvas></canvas>
</div>
<p>{{ updated_caption }}</p>
```

The first marker belongs to the component invocation. The second belongs to
the `div`. Neither marker is copied from one level to the other.

## 3. The model

### 3.1 `ComponentRange`

A **`ComponentRange`** is the logical component node the browser uses after
the authored component tag renders away. It owns:

- the target component class;
- one stable logical browser lifetime and Events anchor;
- the parent-authored component key and morph mode;
- direct logical child ComponentRanges;
- component-level State, props, client bindings, effects, and cleanup; and
- the links from that logical lifetime to its current physical placements.

The server creates a new render ID on every render. That revision ID routes
one server result; it is not the stable ComponentRange identity. A successful
correspondence transfers the fresh route to the existing logical range.

This is not a general virtual DOM. Alpine continues to own ordinary element,
text, and attribute matching. Citry adds component nodes, slot-region nodes,
and their framework metadata to the traversal around Alpine's element walk.

### 3.2 Range placement

A **range placement** is one physical start/end ownership-comment pair and
the DOM interval between it. Most ComponentRanges have one canonical
placement. Mirrored content can give one logical range several placements.

Keys and morph modes live in the client graph, not in comment text. Comments
identify physical placements. This keeps the cap grammar fixed and prevents
author values from becoming DOM parsing input.

### 3.3 `RootGroup`

A **`RootGroup`** is the current ordered set of concrete element roots for one
logical component. Facilities that require elements, including Alpine scope
projection, component-tag handlers, busy markers, and DOM-facing
provide/inject work, use this group.

The RootGroup projects component behavior onto elements. It does not become
the component's identity. A ComponentRange can have zero roots, and its roots
can change without changing its logical lifetime.

### 3.4 Slot region

A **slot region** is one capped place where a fill rendered. It records the
fill source and receiving slot relationship. A slot region can contain
ComponentRanges, but it is not a component and does not own component State or
component-tag metadata.

### 3.5 A mixed tree

The planner sees component ranges and physical DOM containment together:

```text
ComponentRange(Page)
└── <main>
    ├── ComponentRange(Toolbar)
    ├── <section #c-ignore>
    │   └── ComponentRange(Chart)
    └── SlotRegion(default fill)
        └── ComponentRange(Notice)
```

The `section` must be consulted before `Chart`. Once the old `section` says to
ignore its subtree, the planner retains the old section branch and does not
plan incoming work for `Chart`. `Toolbar` and `Notice` remain eligible for
normal correspondence and updates.

## 4. Conceptual and materialized ranges

Every executed component invocation has a conceptual ComponentRange in the
server's render ownership model. The browser needs a materialized range only
when a document or fragment sends the client graph needed for browser-side
behavior.

Graph selection includes a component when any existing graph rule needs it.
A non-null component key or morph mode also forces inclusion, including for a
transparent, text-only, empty, or otherwise browser-inactive component. The
selection walk includes any transparent ancestors required to connect that
range to the graph root. Range ignore alone does not create an Events class or
an Alpine scope.

An ignore marker on an ordinary element remains HTML metadata and does not by
itself create a component graph record. When that element participates in a
Citry fragment morph, the mixed planner reads its live DOM marker.

## 5. Where authored metadata lives

The placement rules are:

| Authored form | Owner | Browser representation |
|---|---|---|
| `<li #c-key="item.id">` | Ordinary element | `data-citry-key` on that element |
| `<li #c-ignore>` | Ordinary element | `data-citry-morph="ignore"` on that element |
| `<c-Row #c-key="item.id">` | Component invocation | `morphKey` on the nested-component graph record |
| `<c-Row #c-ignore>` | Component invocation | `morphMode: "ignore"` on the nested-component graph record |

Component metadata never enters component kwargs, `c-bind`, rendered root
attributes, or cap text. Template authors must write it explicitly. A spread
cannot contribute `#c-key` or `#c-ignore`.

`#c-ignore` is bare. A value is a parse error. `#c-key` requires an expression;
an evaluated `None` means unkeyed, while `False`, `0`, and `""` are real keys.

User component tags and `<c-component>` accept component-range metadata.
Structural tags such as `<c-if>`, `<c-for>`, `<c-slot>`, `<c-fill>`, and
`<c-raw>` are not component identity nodes and reject it.

Placement follows node identity, not rendered shape or client activity. A
transparent, rootless, text-only, or empty component invocation is still a
ComponentRange and may carry range metadata. Conversely, an HTML void element
is still an ordinary element and may carry `#c-key`; the absence of children
does not remove that element's identity.

`<c-element>` always represents the selected ordinary HTML element. Both the
static form `<c-element is="section">` and dynamic form
`<c-element c-is="tag_name">` apply `#c-key` and `#c-ignore` to the produced
element. The runtime-selected path must forward those attributes to the
element rather than create component-range semantics.

## 6. ComponentRange correspondence

The browser computes correspondence before mutating live DOM or activating an
incoming graph.

### 6.1 Addressed root

An Events response first identifies the addressed old range and incoming graph
root. The existing self-render rules apply:

- the same component class keeps the stable browser anchor and logical range;
- a changed class keeps only the action anchor where the Events contract
  requires it and creates a fresh logical component lifetime; and
- plain HTML replacing the target retires the component lifetime.

Child matching only proceeds inside a matched logical parent. An unmatched
component is opaque, so a descendant key cannot reach through it.

### 6.2 Ignore closure before child matching

The planner can discover candidate component identities while it builds the
mixed tree, but it does not finalize direct-child matches until it has found
old ignore barriers at the current level. It computes a retention closure:

1. An old ignored element or ComponentRange marks its old physical subtree as
   retained and the matched incoming physical subtree as excluded.
2. Every component, invocation, fill, and slot-region record referenced by a
   retained physical subtree marks the corresponding old logical record as
   retained.
3. A retained logical record retains every physical placement or slot region
   that shares it. Every corresponding incoming record and placement is
   excluded, even when it appears outside the matched incoming physical
   subtree from step 1.
4. The planner repeats steps 2 and 3 until no shared record adds another
   retained placement or excluded incoming endpoint.
5. It removes retained and excluded endpoints from the active matching pool,
   then finalizes keyed and unkeyed matches among the remaining endpoints.

This closure resolves keyed moves that cross an ignore barrier. A retained old
keyed child keeps its old logical record and all placements; its incoming
counterpart is excluded wherever the new render placed it. An active old child
whose only incoming counterpart lies in an excluded branch becomes a normal
removal. The planner does not retry either endpoint against a different child.
An incoming endpoint excluded because its old counterpart is retained is not
inserted elsewhere.

The same rule handles shared mirror and fill records. An ordinary element's
own DOM skip starts at one placement, but a logical record cannot be old in one
placement and incoming in another. Retention therefore expands to every
physical projection of that record. Section 10.3 specifies the observable
mirror consequence.

### 6.3 Keyed direct children

Among one matched component's active direct logical children, a keyed child
matches by `(targetClassId, morphKey)`. Every string is a key, including the
empty string. Keyed ranges may move across ordinary wrappers or DOM depths
while remaining under the same matched logical component parent.

After ignore closure, the planner reserves keyed matches before positional
unkeyed matches. A duplicate component key within the same matching scope
produces the existing development warning and resolves in invocation order.
Production remains deterministic and uses that same order.

### 6.4 Unkeyed direct children

After keyed matches are reserved, the planner pairs the remaining direct
logical child ranges in invocation order. A pair corresponds only when both
are unkeyed and have the same target component class. A class mismatch makes
that position an unmatched replacement; the planner does not scan later
unkeyed children for a same-class candidate.

This gives unkeyed components logical positional continuity. Ordinary wrappers
do not become component parents, so an unkeyed child can keep identity when a
`div` wrapper becomes a `section`, provided it remains the same active direct
child ordinal and component class under the matched logical parent. The
physical adapter uses its transplant path when the wrapper replacement
requires it. Authors use `#c-key` when a child must retain identity across
insertion, deletion, or reorder. The rule applies to every unkeyed component,
not only an ignored one. That keeps component identity independent of its
current morph mode.

### 6.5 Physical planning and ordinary elements

Logical correspondence and physical traversal constrain each other. For each
matched ComponentRange, the planner walks its old and incoming placements in
ancestor order:

1. consult a matched old ordinary element before planning descendants;
2. stop at an old element ignore barrier;
3. treat a matched child ComponentRange as opaque to the enclosing Alpine
   element walk;
4. recurse into that range unless its old range morph mode is `ignore`; and
5. treat unmatched ranges as atomic insertion, removal, or replacement.

Keyed range moves are considered only after section 6.2's retention closure.
A keyed descendant cannot escape an ignored old element. The ignored branch
stays at its matched outer position, and the incoming copy of every retained
descendant is excluded from activation and insertion.

Equivalent slot regions participate as capped physical nodes. Production
correspondence uses the planned physical parent path and sibling-window
signature together with receiver class, result-owner class, and the fill's
slot, kind, policy, owner class, and receiver class. Development source
locations can improve diagnostics but do not change correspondence. A slot
match never crosses an unmatched ComponentRange.

For a stationary matched range, the live cap interval remains connected.
Temporary paired sentinels bracket it while Citry filters its ordinary roots
out of Alpine's enclosing flat keyed-sibling map and makes that walk jump to
the closing sentinel. Citry recursively morphs the range at its own level; the
parent-level walk never reparents its live nodes. Nested stationary component
and equivalent slot-region ranges are processed inside-out, so each enclosing
walk sees an already-updated connected virtual node. A component can use this
path only when its complete chain of intermediate component and slot ranges is
equivalent; an unmatched intermediate range makes it a real move. Only a range
whose planned position actually changes enters a portable holder for
transplantation.

## 7. The morph transaction

One read-only plan controls DOM work and client-graph adoption:

1. Parse and validate the incoming graph, Events manifest, dependency data,
   and ownership caps while detached.
2. Correlate the addressed root and enough ordinary element and cap structure
   to discover old ignore barriers in ancestor order.
3. Compute section 6.2's retention closure across physical placements and
   shared component, invocation, fill, and slot-region records.
4. Correlate the remaining keyed and unkeyed ComponentRanges and slot regions,
   then classify old and incoming records as matched, replaced, retained old,
   or excluded incoming.
5. Stage routes, RootGroups, props, State, bindings, effects, fills, and
   dependencies only for accepted incoming records. Keep retained old records
   and their supporting revisions live.
6. Apply the planned range moves and the Alpine DOM morph. Do not descend into
   retained branches.
7. Validate the landed caps and physical placements.
8. Commit accepted incoming records together with retained old records,
   refresh permitted root projections, and initialize newly ready instances.
9. Reconcile controls and busy state outside ignored branches. Retire departed
   records and dependencies exactly once.

No incoming callback, effect, dependency, client binding, fill source, or
component instance inside an excluded branch may become observable during
preflight. DOM ignore without graph retention would leave live markup pointing
at retired callbacks. Graph adoption without DOM adoption would attach fresh
callbacks and State to stale markup. The transaction therefore retains or
adopts each planned branch as one unit.

An ordinary ignored element can split one logical component's physical output:
one root branch may remain old while sibling roots receive incoming content.
The committed graph may consequently reference both retained and accepted
records under the same stable component anchor. Revision pruning keeps every
revision that still supplies a live callback, binding, fill, dependency, or
physical branch.

The existing post-mutation failure policy remains fail-closed. Citry promises
detached rejection before mutation for malformed input, but not a general DOM
rollback after Alpine starts. A landed-cap or activation failure removes the
affected live target, aborts provisional routes, rejects the incoming
revision, and runs retirement cleanup once.

## 8. Ignore semantics

### 8.1 Ordinary element ignore

For a matched old ordinary element carrying `#c-ignore`:

- the exact old element object, author-owned attributes, and descendants
  remain untouched by the DOM morph;
- nested ComponentRanges and slot regions remain live from the old graph;
- their incoming counterparts are excluded before activation;
- surrounding siblings and ancestors may still update;
- an ordinary element key may allow the complete ignored element to move as
  one node; and
- removal, key mismatch, tag-name mismatch, or replacement of an unmatched
  ancestor can still remove it because those decisions happen before the
  element's updating hook.

Ignoring morph work does not stop existing Alpine reactivity. Live effects in
the retained element continue to run. If the enclosing ComponentRange itself
is not ignored, accepted component-level props or State can still reach those
already-live effects according to the normal Alpine contract.

Citry may refresh graph-owned `data-cid` and `data-cid-*` root projections
needed to route the retained element through the committed logical anchor. It
does not patch author attributes, Alpine directive attributes, control values,
text, or descendants as part of that repair.

The DOM skip begins at that one physical element. If the retained subtree
references a ComponentRange, fill, or slot-region record shared by other
placements, section 6.2's closure retains every projection of that logical
record. This non-local graph retention is required because one shared record
cannot own old callbacks in one placement and incoming callbacks in another.

### 8.2 ComponentRange ignore

For a matched old ComponentRange whose `morphMode` is `"ignore"`:

- all of its physical placements and their complete DOM contents are retained;
- the logical range, Events anchor, State, props, client bindings, callbacks,
  effects, dependencies, nested components, and slot regions remain the old
  live branch;
- its incoming range and every descendant record are excluded;
- a keyed match may move the complete frozen range to the incoming placement;
- an unkeyed range can retain only its positional match; and
- no root element receives a copied ignore marker.

Changed parent inputs do not enter an ignored ComponentRange. Its old props,
State realization, fills, and client bindings remain authoritative. Existing
actions inside it remain routable because the supporting old graph records and
dependencies stay live.

Retaining an old client binding does not stop that binding's ordinary browser
reactivity. For example, the retained old `$c-props` expression may continue
to respond to later changes in the stable parent State. What ignore excludes
is the incoming render's replacement supplier and values; it does not freeze
the old live expression or route it through a retired parent render ID.

Parent-authored range metadata persists across a same-class child self-render,
just as the component key does. A morph response targeting that child is
therefore skipped. The request lifecycle still completes and busy state
clears, but the incoming DOM, State, callbacks, and dependencies are not
adopted.

### 8.3 The old policy controls

The live old node controls the current morph for both element and range ignore:

- adding ignore in incoming HTML allows that one normal morph and stores the
  policy for the next morph;
- removing ignore through an ordinary morph cannot enter the ignored old node,
  so the policy remains sticky; and
- an explicit replacement, identity mismatch, removal, or unmatched ancestor
  can remove the old policy together with the old node or range.

This matches Alpine's element-hook ordering and avoids letting incoming data
decide whether it should be trusted before the old protection is consulted.

### 8.4 Replacement and mismatch

`swap="replace"` bypasses morph ignore. It replaces physical DOM and caps
wholesale, then applies the normal logical correspondence policy. For a
same-class self replacement, externally authored key and morph metadata remain
attached to the continuing logical range. For a parent render, the incoming
invocation supplies the metadata after replacement, so an explicit replace can
also remove a sticky ignore policy.

Component class and component key compatibility are checked before range
ignore. A changed class or key creates a new ComponentRange. Removing the
invocation removes the old range. An ignored descendant also disappears when
an unmatched enclosing component or ordinary element is replaced.

## 9. Roots remain projections

Moving component identity to ComponentRange does not eliminate special root
handling. Several facilities require concrete elements:

- Alpine scope stacks and directive initialization;
- component-tag `$c-props` and boundary handlers;
- `data-cid` ownership lookup and Events targeting;
- busy markers and focus/control reconciliation;
- provide/inject hooks that attach to physical content; and
- cleanup when a root enters or leaves a logical component.

Those facilities continue to use RootGroup and exact range placements. A
single-root component, multi-root component, text-only component, and empty
component nevertheless share one ComponentRange identity and matching path.

When one ordinary root is ignored and another updates, RootGroup remains one
logical group containing the retained and accepted roots in physical order.
Framework-owned projections may be reconciled across that mixed result. The
ignored root's author content stays untouched.

## 10. Slots, transparent components, mirrors, and document topology

### 10.1 Slots and fills

Slot regions remain distinct from ComponentRanges. The planner first respects
an enclosing ignore barrier, then uses slot-region correspondence only in the
active branch. An ignored branch retains its old supplied or fallback fill,
source projection, nested components, callbacks, and dependencies. The
incoming fill branch is not evaluated or activated in the browser.

An accepted equivalent slot region receives normal Alpine element matching,
including ordinary element keys inside caller-supplied content. An unmatched
slot region is an atomic replacement.

### 10.2 Transparent and dynamic components

Transparent components such as `<c-provide>` still have a conceptual range.
When a key, morph mode, slot relationship, or other graph requirement makes
the range materialized, it receives normal ComponentRange correspondence even
if it produces no element root.

`<c-component>` carries its invocation metadata to the selected component.
The selected target class participates in identity, so changing the selected
class replaces the logical range even when the key text is unchanged.

`<c-element>` remains an ordinary element as specified in section 5. Its
runtime-selected implementation cannot expose its transparent helper
component as a ComponentRange identity.

### 10.3 Mirrors

Range-level ignore applies to every physical placement of one logical range.
The planner validates and classifies all placements before mutating any of
them. A partial mirror update would give one logical component contradictory
DOM realizations, so one missing, crossed, or otherwise corrupt placement
rejects the transaction.

Ordinary element ignore remains placement-local for ordinary DOM that has no
shared graph record below it. The same mirrored logical component can have an
ignored leaf element in one physical placement while an unrelated element in
another placement updates.

When the ignored element contains a mirrored ComponentRange or a slot region
whose component, invocation, fill, or region record is shared, retention
closure applies. Citry retains every physical projection of the shared record,
including projections outside the ignored element, and excludes every
incoming counterpart. The enclosing ordinary DOM in those other placements
can still update around the retained range or region. This deliberately gives
logical consistency priority over placement-local freshness.

### 10.4 Document and body

The existing split document/body projection continues to provide one ordered
planning window for component and slot caps around `<html>` and `<body>`.
Ignore classification occurs while caps are in that operational window. Citry
restores canonical document ownership before graph adoption and never treats
manifest script elements as morph content.

## 11. Compiler, server, protocol, and cache contract

### 11.1 Compiler output

Component invocation metadata is one trailing range-metadata tuple on
`ComponentNode`, separate from kwargs and ordinary HTML attributes. It can
contain the existing expression-backed `#c-key` and the static bare
`#c-ignore`. Calls with no component metadata retain the compact existing
shape.

Runtime-selected `<c-element>` uses a different, private element-metadata
channel. The compiler tags its `#c-key` and `#c-ignore` for the element locus;
`ComponentNode` evaluates the key in the source parent's context and carries
the normalized element metadata beside `raw_kwargs`. It does not record that
metadata on the transparent helper invocation and does not expose it through
user kwargs. `DynamicElement` applies the resulting `data-citry-key` and
`data-citry-morph` attributes when it constructs the selected `CitryElement`.
The static `<c-element is="...">` rewrite continues to compile them directly
as ordinary element attributes.

The compiler implementation plan must pin the tagged tuple and private
runtime-channel shapes, the exact generated Python source, and their golden
tests before code changes begin.

The parser already recognizes both meta-attribute names. Semantic placement
validation changes to accept component-tag `#c-ignore`; the grammar and AST do
not need a new shape. The compiler must update the const-body cloning path as
well as ordinary component construction.

### 11.2 Server ownership

`ComponentNode` evaluates component metadata when it records the invocation.
The invocation stores the normalized key and range morph mode. A shared
`has_range_directive` decision forces graph inclusion when either value is
non-null and carries transparent ancestors required for a connected graph.

Dynamic `<c-component>` forwards the same invocation identity until its
selected target binds. Component metadata therefore follows the selected
target without root-attribute projection.

### 11.3 Client-graph protocol

`NestedComponent` gains one required field:

```ts
morphMode: "ignore" | null;
```

`null` means normal morph behavior. `"ignore"` is the only v1 non-null mode.
The field is required so producers and consumers cannot silently disagree
about range policy. A missing field, boolean, unknown string, or other wrong
type rejects the detached graph before any mutation. Unknown extra fields
continue to follow the protocol's strict validation rules.

`morphKey` remains separate because it selects correspondence, while
`morphMode` controls what happens after correspondence. Neither value is
serialized into ownership comments.

The protocol is pre-beta and permits coordinated in-place v1 changes. The
specification, JSON schema, canonical and shipped Python record helpers,
TypeScript types and validators, fixtures, conformance tests, embedded browser
artifacts, and integrity hashes move together.

### 11.4 Cached render artifacts

Cached descendant invocation records store the range morph mode beside the
component key. Metadata on the current cache-boundary call remains call-owned;
the cache does not overwrite it with the archived boundary invocation.

The pre-1.0 strict cache artifact remains version 1. Its descendant invocation
record requires `morph_key` and `morph_mode`; an artifact with another version
or a missing field is a cache miss or explicit rejection according to the
cache extension's policy. Replay does not default a missing descendant morph
mode, because doing so would change the meaning of cached component output.

## 12. Failure behavior

The implementation must handle these cases explicitly:

| Condition | Required result |
|---|---|
| Missing, crossed, duplicate, or malformed component caps | Reject during detached preflight when detectable; fail closed if physical corruption is discovered only after mutation |
| Missing or invalid `morphMode` | Reject the client graph before DOM, callback, anchor, or dependency mutation |
| Same key with a different component class | Treat as an unmatched replacement |
| Duplicate keyed children in one scope | Emit the established development warning and resolve deterministically in invocation order |
| Unkeyed class mismatch at one position | Replace that position; do not search later unkeyed children |
| Ignored old range with no incoming counterpart | Remove it normally |
| Ignored range below an unmatched ancestor | Remove it with that ancestor |
| Incoming branch below an old ignore barrier | Exclude it before activation |
| Corrupt one-of-many mirror placement | Reject the whole range transaction |
| Failure after Alpine begins mutation | Abort provisional routes, remove the affected target, reject the revision, and clean retired resources once |

An ignore marker is not an error recovery mechanism. Invalid graph data never
becomes acceptable because the affected range would have been ignored.
Validation happens before ignore classification wherever the complete graph is
available.

## 13. Alternatives considered

### 13.1 Copy component metadata to a root element

This cannot represent multi-root, text-only, or empty components and collides
with independent root-element keys and ignore markers. RootGroup remains a
projection target, not the metadata owner.

### 13.2 Reject `#c-ignore` on component tags or roots

Rejection avoids the ordering bug but leaves no consistent way to protect an
entire multi-root or rootless component. It also treats an ordinary root
element differently solely because it happens to be a root. The mixed planner
removes that accidental distinction.

### 13.3 Discover ignore only in Alpine's updating hook

The current nested-range pre-pass and graph adoption both run too early. A
late hook cannot undo nested DOM work or safely un-adopt callbacks and
dependencies. Ignore barriers must be part of detached planning.

### 13.4 Preserve DOM but adopt the incoming graph

Fresh callbacks, State, fills, and dependencies would point into stale HTML.
The reverse, preserving the old graph while adopting fresh DOM, leaves old
records pointing at nodes that no longer exist. Retaining the old branch and
excluding its incoming counterpart is the only coherent branch-level unit.

### 13.5 Require a key for component-range ignore

That would make the natural `<c-Card #c-ignore>` form ineffective and give
unkeyed ComponentRanges no DOM-like positional behavior. Same-class positional
matching gives a predictable default; a key remains necessary for reorder.

### 13.6 Match unkeyed ranges positionally only when ignored

Identity would change when an unrelated morph policy is added or removed.
Applying positional same-class correspondence to all unkeyed ranges keeps
matching independent of update policy.

### 13.7 Use a one-off boolean protocol field

A nullable morph mode describes the policy as one closed protocol choice and
can admit another validated mode later without accumulating unrelated flags.
The key remains its own field because identity and morph policy are separate.

## 14. Acceptance matrix

Implementation is complete only when tests cover the following behavior in
Chromium, Firefox, and WebKit where browser behavior is involved.

### 14.1 Parsing, compilation, protocol, and cache

- bare component-tag `#c-ignore`, alone and with `#c-key`;
- rejection of a valued `#c-ignore`, meta attributes through `c-bind`, and
  placements on structural built-ins;
- component metadata inside loops and control flow;
- static and runtime-selected `<c-element>` using ordinary element semantics;
- compiler golden output and const-body cloning;
- strict Python and TypeScript protocol validation, fixtures, schemas, copied
  helpers, generated bundles, and integrity hashes; and
- version-1 cache miss, hit, replay, missing field, wrong field, and
  cache-boundary call-owned metadata.

### 14.2 Matching and ignore

- keyed same-class match, reorder, wrapper crossing, class mismatch, key
  mismatch, removal, and duplicate warning;
- unkeyed same-class positional continuity, insertion, deletion, reorder
  reset, class mismatch, and wrapper replacement at the same logical ordinal;
- component range ignore for single-root, multi-root, text-only, empty, and
  rootless output;
- keyed ignored range movement with exact DOM nodes and caps preserved;
- adding, sticky removal, explicit replacement, and unmatched-ancestor
  behavior;
- child self-render under parent-authored range ignore; and
- `swap="morph"` compared with `swap="replace"`.

### 14.3 Ordinary ignored elements

- an ignored component template root with and without an Events class;
- one ignored root while sibling roots update;
- an ignored ordinary element containing keyed and unkeyed ComponentRanges;
- an ignored ancestor blocking a nested range before any DOM or graph work;
- keyed old and incoming endpoints crossing into and out of an ignored branch,
  including deterministic removal and exclusion of the other endpoints;
- keyed movement, tag mismatch, element-key mismatch, and removal; and
- internal ownership projection repair without author attribute, directive,
  control, text, or descendant patching.

### 14.4 Cross-cutting lifecycle

- Alpine `x-data`, focus, selection, controls, scroll, iframe, media,
  directives, and cleanup;
- State, props, component-tag client bindings, Events callbacks, pending
  queues, busy state, and later actions from a retained branch;
- supplied and fallback fills, nested slot regions, source ownership, and
  retained dependencies;
- one ordinary-ignored mirror placement whose descendant ComponentRange is
  shared with an otherwise updating placement;
- one retained slot region whose fill record is shared with an otherwise
  updating region, including retention closure over both regions;
- transparent components, dynamic `<c-component>`, RootGroup,
  provide/inject, and relocated handlers;
- every mirror placement and partial-placement corruption;
- document/body topology, table/select/SVG parsing contexts, and fragment
  manifest exclusion;
- old-revision retention and pruning after the ignored branch finally leaves;
  and
- detached rejection, landed-cap failure, activation failure, and cleanup
  exactly once.

## 15. Falsifiers

Any of the following disproves the design or its implementation:

- a component-tag key or ignore marker appears on a rendered root element;
- an ordinary ignored ancestor allows a nested range, slot, callback, or
  dependency to update before the skip;
- an ignored range keeps old DOM while using incoming callbacks, props, State,
  fills, or dependencies;
- a retained action cannot route because its supporting old revision was
  pruned;
- an unkeyed child keeps identity across reorder without a key;
- a descendant key matches through an unmatched component or ignored branch;
- a stationary range is detached, even temporarily, and loses focus,
  selection, scroll, or an iframe browsing context;
- one mirror placement updates while another placement of the same ignored
  range remains old;
- one shared component, invocation, fill, or slot-region record is retained in
  one placement but adopted from incoming data in another;
- ordinary `#c-ignore` on one root freezes unrelated roots of the same
  component;
- a dynamic `<c-element>` gives its helper component range semantics; or
- malformed graph or cap data becomes partially observable before rejection.

Implementation enabled component-tag `#c-ignore` only after focused browser
tests proved the ancestor-ordered planner and retained-old/excluded-incoming
transaction. The syntax and the client contract therefore ship together.
