# Discover deferred child work in one native traversal

## Prior art

`component_render.py:590` recursively scans parts into `_RenderTask` and
`_ContextMergeTask` objects. `_settle_render` reverses that list onto its work
stack. Positions retain the original parts list, index and lexical context;
context-merge tasks follow all deferred descendants of a foreign-context
interior render. `_replace_in_parts` separately tolerates later list edits.
The retained orchestration profile reports 1,020 parts-list visits across 343
scans, about 1.508 ms instrumented cumulative time. This is diagnostic cost,
not an expected wall-time saving. Read the actual code alongside section 4 of
`docs/design/component_rendering_defer.md`; its older pseudocode does not fully
describe current cross-context traversal.

## Experimental design and alternatives

Use an isolated PyO3 extension to walk current exact lists and known render
objects with an explicit stack. Retain Python objects and call the existing
Python task constructors. Preserve duplicate occurrences, parts-list/context
identities and index values, source order, wrapper transparency and post-descendant context merges.
No tree or task result is reused across scans. Unknown objects, subclasses,
non-list parts or excessive nesting return an unsupported result and use the
original Python scanner. Exact placeholders, strings and Markup values contribute no task.
Nested depth and wrapper chains are each bounded to 256 before falling back.
Render/list cycles then reach Python recursion failure; wrapper-only cycles
retain the original unwrap loop, which does not terminate. This experiment
does not repair malformed cyclic trees.

Guard the original constructors, scanner helper, unwrap helper and relevant
slot/getattribute descriptors, wrapper base and type MRO identities before
entering the native helper. Preinstalled
replacements, tracing callbacks, concurrent mutation, allocation finalizers and
changed class implementations remain production qualification work. This is a
bounded fixture experiment, not a proposed production-compatible binding.
Unsupported fallback may repeat ordinary slot reads; custom getters must not
be admitted by the entry guards. No production files or regular native binary
change. Python-specific object scanning has no parser/compiler/LangImpl impact;
any later adoption needs its private registration, stub, wrapper and fallback.

Collecting tasks during body construction could avoid scanning, but public
parts-list mutation means those tasks would need invalidation or revalidation.
Moving only task constructors would leave traversal in Python. This experiment
measures the existing whole scan before either larger representation change.

## Evidence and decision

Check task types/order and every retained object identity on synthetic nested,
wrapped, repeated and foreign-context parts. Check current list edits and
unsupported objects/subclasses. Compare full fixture HTML and all reached
ownership snapshots. Count native admission in an untimed render. Run focused
existing deferred-render checks under the adapter if fixture equivalence holds.

After correctness and independent review, retain eight fresh-process pairs,
six initial renders and 80 warmed samples per process with normal GC and
balanced randomized order. Require seven joint wall/CPU wins and at least
0.25 ms median paired reduction in process mean wall time to justify production
qualification. Keep actual second renders separate. Do not rerun a failed
screen to seek acceptance. Record all source/artifact hashes and samples.
