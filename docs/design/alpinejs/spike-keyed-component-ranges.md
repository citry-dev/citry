# Keyed component ranges: virtual-node identity without root-key collisions

An empirical spike for separating component-invocation keys from independently
keyed root elements, run on 2026-08-04 against Citry's pinned Alpine 3.15.12 and
`@alpinejs/morph` 3.15.12.

**Implementation status (2026-08-04): landed.** Production now carries
required nullable `morphKey` on nested client-graph invocations, plans
correspondence top-down, keeps stationary ranges connected, transplants real
moves, recursively applies fresh HTML, correlates structurally equivalent slot
regions without crossing opaque components, supports split document/body and
mirrored placements, and gives `replace` logical-only continuity. This file
remains the empirical rationale and acceptance matrix. The approved normative
model that extends this foundation to positional unkeyed ranges and
range-level morph policy is
[`component_ranges.md`](../component_ranges.md).

For the parser's split Document/body topology, the live opening caps that
precede `<html>` are temporarily projected behind the body morph cursor. This
gives the planner one ordered sibling window for nested keyed components and
slot regions. Caps that still delimit document-root content are restored
before graph adoption; caps moved into authored wrappers remain there and are
reclassified from the committed DOM. When the HTML parser places authored
boundary text on only one side of that projection, the planner seeds the
incoming text into the old operational window before morphing; it does not
discard whitespace, including visible non-breaking spaces.

## Verdict

**A keyed component can be represented as a comment-bounded virtual node, and
its key should not be stamped onto any child root element.** The browser can
preserve component State and recursively apply fresh server HTML while keeping
an independently keyed child root. The mechanism passed three deterministic
runs in Chromium, Firefox, and WebKit with no console messages or page errors.

The important qualification is that stock Alpine has no keyed range primitive.
Citry must plan component-range correspondence before morphing and make each
matched range opaque to the enclosing element walk. There are three physical
paths:

1. A stationary range with the same structural parent path and unchanged
   physical Alpine-walk prefix stays connected. A temporary keyed sentinel
   tells the outer walk where to skip, while Citry recursively morphs the live
   range against the fresh range.
2. A reordered range in the same Alpine sibling window is temporarily held in
   a keyed `<template>`, recursively morphed, moved by Alpine, and synchronously
   expanded.
3. A range that crosses DOM wrappers or depths cannot be linked by Alpine's
   parent-local key lookup. Citry holds the old range, lets the fresh parent
   structure land, explicitly transplants the old range into the fresh
   placeholder, recursively morphs it, and expands it synchronously.

The first path matters. Using inert holders for every matched child would
detach even stationary inputs, scroll containers, iframes, and media. The
connected path preserves those browser-owned resources.

The adapter below remains disposable research code rather than the production
runtime. Its verdict has since been implemented across the graph protocol,
Events applier, cache format, tests, and public documentation.

## Saved reproduction

- [`keyed_component_range_adapter.js`](keyed_component_range_adapter.js):
  disposable range registry, correspondence planner, and the three physical
  morph paths.
- [`keyed_component_range_scenarios.js`](keyed_component_range_scenarios.js):
  negative control and browser scenario matrix.
- [`keyed_component_range_harness.py`](keyed_component_range_harness.py):
  pinned local Alpine/morph loader, assertions, three engines, and three runs
  per engine.

Run from the repository environment:

```console
python docs/design/alpinejs/keyed_component_range_harness.py
```

The harness prints the complete JSON evidence. The recorded run used
Playwright 1.61.0 with these browser versions:

| Engine | Browser version | Passes | Console/page errors |
|---|---:|---:|---:|
| Chromium | 149.0.7827.55 | 3 | 0 / 0 |
| Firefox | 151.0 | 3 | 0 / 0 |
| WebKit | 26.5 | 3 | 0 / 0 |

Every result object was identical across all nine executions.

## Why the current inert-island correspondence is insufficient

The existing range protector in `citry.js` collapses both the live child range
and the incoming child range into keyed templates. Alpine retains the old
template wholesale, and Citry expands the retained old contents. That is the
right behavior for a deliberately frozen island but the wrong behavior for a
matched Citry component: fresh child attributes, text, props, and descendants
never land.

The spike contains a negative control using that exact shape:

```json
{
  "freshDiscarded": true,
  "result": "old child bytes"
}
```

The recursive paths produce the opposite result: stable logical identity plus
fresh server content.

## Identity model under test

The virtual component key is the pair `(targetClassId, morphKey)`. It belongs
to the authored component invocation and the stable browser anchor. It is not
an element key and is never serialized into a range comment.

The fixed cap syntax continues to identify a physical component placement:

```html
<!--citry:g1:<revision-alias>:<graph>:i:<instance>:s-->
...
<!--citry:g1:<revision-alias>:<graph>:i:<instance>:e-->
```

The marker uses the first eight characters of the complete manifest revision;
the manifest and ownership registry retain the complete revision as identity.

The ownership graph supplies the invocation key. Ordinary elements continue
to use `data-citry-key` inside one matched component range.

The spike locks these value semantics:

| Evaluated component key | Meaning | Preserved in the scenario |
|---|---|---:|
| `None` / graph `null` | unkeyed invocation | no |
| `""` | real empty-string key | yes |
| `False` stringification | real key | yes |
| `0` stringification | real key | yes |

The class is part of identity. The same key with a different component class
creates a new anchor and cleans the old anchor once.

## Scenario findings

### Stationary component: all identity layers compose

With a stable component key and stable child-root element key, the following
all survived while fresh server label text and attributes landed:

- stable component anchor and its logical state;
- exact start/end comment objects;
- child root and input node objects;
- Alpine `x-data` scope object and draft value;
- focus and selection;
- scroll position; and
- iframe element, document, and a property stamped on its `contentWindow`.

No holder or sentinel remained after the synchronous operation.

This state-identity result keeps the authored `x-data` expression unchanged.
Changing the `x-data` attribute itself invokes Alpine's ordinary directive-
attribute replacement semantics and can recreate that scope; a component key
does not override explicit directive changes from the server.

The harness also locks Alpine's normal clone-mode directive behavior. A custom
directive is invoked once on the live node and once while Alpine seeds the
detached incoming counterpart; only the live node owns a lasting cleanup, which
runs once when its fixture is removed. The complete directive log is asserted,
not merely printed.

The sentinel also composed with a keyed ordinary-element reorder immediately
after the component range: both following elements kept their node identities
and followed their own `data-citry-key` values. The skip ends on the component's
end caps so Alpine recomputes sibling keys on its next walker iteration.

Moving the component range itself across an ordinary keyed sibling takes the
holder path, even when it is the only logical child component. Both left-to-
right and right-to-left cases preserved the range caps, component root,
ordinary element, and their independent identities while updating fresh text.

### Component key and element key are independent axes

- Stable component key plus changed child-root element key preserved the
  component anchor but replaced the root element.
- Changed component key plus stable child-root element key created a new
  component anchor and a new root. The equal inner element key could not leak
  through the unmatched component boundary.

This is the behavior the current duplicate `data-citry-key` attributes cannot
express.

### Reorder, multi-root, and rootless shapes

Two same-class component ranges were reordered while their roots deliberately
used the same element key. Component anchors, caps, and root objects followed
the component keys; fresh labels landed in both ranges.

A stable component range also passed:

- keyed multi-root reorder plus insertion;
- multi-root to text-only;
- text-only to empty; and
- empty to an element.

Two adjacent empty keyed ranges reordered without ambiguity. Their anchors and
exact cap objects followed their keys.

### Recursive boundaries and wrapper changes

A keyed parent and keyed grandchild both preserved their anchors and roots
while both received fresh content. Changing only the parent's component key
reset both parent and grandchild even though the grandchild component key and
root element key were unchanged. Matching is top-down; an unmatched ancestor
is an opacity boundary.

A keyed component also moved from a direct `<div>` child to
`<section><aside>...`. The old caps, root object, and anchor were explicitly
transplanted into the new wrapper and then received fresh content. This case is
the clearest proof that the virtual-node layer must act above Alpine's
parent-local element-key matcher. An Alpine directive on the transplanted root
did not clean up during the same-task move and cleaned up exactly once when the
fixture was later removed.

The physical-path classifier uses exactly the same identity source as the
spike's Alpine key callback. In particular, plain HTML `id` is positional here,
not a hidden range-parent key: reordered id-only wrappers take the explicit
transplant path and preserve the child caps/root without silently linking a
replacement DOM range. A production classifier must likewise share its exact
key function with the production Alpine morph call.

### Self-render continuity

A child self-render has no parent invocation in its incoming graph. The spike
therefore retained both the parent-authored component key and the stable
parent-anchor relation on the logical browser record. A subsequent parent
render rediscovered the child and reused the same anchor. Keeping only the key
is insufficient; losing the parent relation makes the next parent planner
treat the child as absent.

### Contextual parsing

A keyed component range directly inside `<select>` retained its anchor and
`<option>` node while fresh option text landed. This exercises contextual
fragment parsing plus temporary templates in a constrained HTML parent. The
existing A6 contextual parsing coverage remains relevant for `tbody`, `tr`,
and SVG.

## Production representation and flow

The clean graph addition is a required nullable field on every nested
component invocation:

```ts
interface NestedComponent {
  // existing fields
  morphKey: string | null;
}
```

The server-side `ComponentInvocationRecord` should carry the corresponding
`morph_key: str | None`. The parent evaluates the authored key and records it
on that invocation. The client matches direct logical children by
`(targetClassId, morphKey)` in document order, top-down, and only when
`morphKey` is non-null.

A production transaction should:

1. validate the incoming graph and every old/new cap;
2. compute the complete top-down correspondence plan before DOM mutation;
3. link planned logical anchors before Alpine evaluates incoming expressions;
4. make every direct component child opaque to its parent's element walk;
5. take the connected, sibling-holder, or explicit-transplant physical path;
6. recursively morph every matched child against fresh contents;
7. expand/remove all temporary nodes synchronously;
8. atomically transfer fresh render IDs, caps, placements, and parent links;
9. retire every unmatched old logical instance exactly once; and
10. publish the new ownership state only if the whole operation succeeds.

The current `options.correspondence` hook and ownership adoption transaction
are useful starting points, but the existing frozen-island expansion is not
the recursive operation above.

## Blast radius discovered by the spike and audit

Moving the component key off roots is broader than a serializer edit:

- server invocation capture and ownership records;
- client-graph schema, spec, validator, fixtures, canonical hashes, and
  conformance corpus;
- stable client logical anchors and top-down range correspondence;
- Events self-render and parent-render adoption;
- cache artifact export/replay for descendant invocation keys;
- transparent and dynamic component inclusion in the ownership closure;
- mirrors and every physical placement of one logical anchor;
- generated `citry-events.js` copies and payload budgets; and
- tests, public key documentation, design docs, and changelog.

Cached descendant invocations have an exact encoded shape. They must archive
`morph_key`; silently reading an older artifact as unkeyed would change State
semantics. The cache artifact format should therefore be versioned rather than
defaulting the missing field.

Arbitrary user key text also makes two dormant wire issues reachable:

- graph JSON embedded in an inert script must escape `<` (for example as
  `\u003c`) so a key containing `</script>` is safe; and
- server canonical hashing must use the same Unicode representation as browser
  `JSON.stringify` (the direct Python fix is `ensure_ascii=False`).

A useful conformance key is `'</script><x>&"π'` because it exercises exact
value preservation, script safety, Unicode hashing, and the guarantee that no
user text enters a comment marker.

## Costs and boundaries

The spike supports the direction, with costs that should remain explicit:

- A genuinely moved range is detached. Focus, layout scroll state, iframe
  documents, and media resources may pay the same browser costs already
  measured for moved keyed elements. Stationary ranges avoid that cost.
- Temporary `<template>` elements are an implementation device, not a public
  DOM contract. The transaction must remove every one before observers and
  lifecycle reconciliation resume.
- Duplicate direct sibling component keys are matched in supplied invocation
  order and the research adapter records a warning. Production must either map
  that order to its validated document-order policy or reject duplicates;
  whether it warns or errors remains a policy decision.
- `swap="replace"` needs an explicit rule: keyed logical continuity can remain
  while physical DOM is replaced, or replace can deliberately disable range
  preservation. It must not be accidental.
- This adapter models one physical placement per logical range. Production
  mirrors must plan one logical match and morph every live placement without
  allowing one placement to steal another's caps or Alpine state.
- The `Document`/`body` split-cap topology is not modeled. The existing narrow
  document-body holder may remain necessary.
- Failure rollback and transition-interrupted commits are not proven by this
  disposable adapter. Production must retain the existing graph transaction's
  all-or-nothing publication rule.

## Recommendation

Proceed with the virtual-range design rather than choosing “drop the parent
key,” “drop the child key,” allowing duplicate root keys, or accepting the
current browser behavior. The component key and child-root key express
different identities, and the spike demonstrates that both can work when the
component is represented at its real boundary.

Before production implementation, lock the remaining policy choices for
duplicate component keys and `swap="replace"`, and include mirrors plus the
document-body topology in the implementation acceptance matrix.
