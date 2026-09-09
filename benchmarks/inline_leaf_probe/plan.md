# Iteration 63: remove a selected leaf's independent identity

## Prior art and scope

Iterations 61 and 62 removed live HeroIcon instances but retained graph records,
IDs and marked serialization boundaries. The final iteration 62 variant saved
0.273 ms versus ordinary Citry with 6/8 wins, missing the consistency screen.
`nodes/__init__.py:1400` creates the invocation, source occurrence, element and
deferred work. `serialize.py:517` treats a render with no root identity as interior
content, so its SVG can join its caller's frame. Measure the cost of retaining
those independent identity records for a component with no own client expressions that can still receive an Alpine
isolation boundary from an active ancestor.

Intercept only the fixed HeroIcon's direct template tag. Reuse input resolution,
create its ordinary deferred descriptor with no ownership invocation, and keep its
execution position in the scheduler. Render through iteration 62's function, which checks caller inputs, trusts the registered
callback's output, and reuses prepared template output, returning an interior render
with no ID. Keep caller descriptors and scheduler work so this comparison isolates
identity removal; immediate function execution is a separate possible design.

Compare ordinary Citry, iteration 62's identity-preserving contract, and this inline
variant. No production source, parser/compiler format, native build or ABI changes.

## Deliberate behavior changes and failures

The inline icon has no Component, invocation/source occurrence, ancestry or queue
record, root marker, client graph identity or independent morph range. It also
consumes no render ID. Its SVG belongs to its caller. Component range directives,
slots, client bindings, globals, overrides, direct root calls and forwarded dynamic
invocations are rejected. The remaining restrictions and promise that the registered callback and its module data produce supported
values are those of iteration 62; this is a fixed-fixture prototype, not a
general classifier or application-facing API. Ordinary errors still raise their
application/schema types, but contain no failed icon instance/queue record and
consume no icon ID. Ancestor error handling remains scheduled normally.

A diagnostic found 13 of 41 icons in the browser graph, of which 12 receive
Alpine isolation markers from active ancestors. The first ID-occurrence count
conflated those two properties; direct marker and manifest checks separate them. Removing identity also removes their client-root marker and browser
instance/invocation/ancestry entries, changes the manifest revision and linked
range comments, and changes the dependency payload's graph revision. These are
explicit contract changes, not evidence of browser compatibility. No browser
qualification is claimed by the projected comparisons. The other 28 icons have
only their ordinary component marker in the serialized document.


## Validation and measurement

Raw HTML and graph snapshots deliberately differ. An untimed check assigns comparison names by class and occurrence, removes the
selected markers and browser graph entries, renumbers retained wire IDs and range
comments, and compares all remaining HTML and browser data. Validate raw browser
manifests before projection. Restrict this experiment to production mode without
component-tag client bindings; development source provenance is not covered. Compare the remaining ownership graph
by removing the selected icon's records, remapping graph-local record IDs and
renumbering the remaining events while preserving their relative order. Keep all other fields, relationships and sequence
order. Test large/small pages, changed attributes, repeated icons, supported errors
and rejected features. The graph comparison is a projection of the declared
contract, not a claim that raw graphs are identical.

The main harness must compare normalized full output for every warm render while
using the ordinary ID generator and fresh IDs. Keep raw digests too. Establish the
ID mapping outside timers and check a fresh normalized graph observation. Measure
eight fresh-process blocks of all three variants, with six initial and 80 warm
renders, ordinary GC and every sample retained. Shuffle all six permutations plus two additional cyclic orders. Ordinary and
inline run in each relative order four times. Exact equality of positions is
impossible for eight blocks and three variants. No tests/builds during
main timing. Report second-render measurements separately.

The primary comparison is inline versus ordinary Citry. The identity versus inline
contrast explains the additional boundary cost. At least 0.25 ms median paired
saving and seven of eight joint wall/CPU wins justify further qualification, not
production adoption of the changed API. Unexpected projected HTML/ownership drift
falsifies this implementation and must be investigated before main timing.


Retain initial and warm output strings until all timed renders finish, then run
HTML normalization and raw-manifest validation. This keeps validator work outside
the timing loop but retains roughly 87 MB of output per worker; allocator conditions
differ from earlier probes, so compare variants only within this experiment. IDs
still change on every timed call. Untimed activation must independently confirm
41 selected callbacks, zero selected identities/invocations for inline, and 41
fewer generated IDs. A normalization test must detect changes to unrelated text,
markers, graph fields and raw manifest revisions.
