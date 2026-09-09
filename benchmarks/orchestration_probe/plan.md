# Reduce closure allocation in component orchestration

The fresh call profile identifies `_render_one` as a substantial Python-side
cost, with 342 executions per large render. Its code has seven cell variables:
`citry_instance`, `comp_cls`, `compiled`, `const_vars`, `extensions`, `generate`
and `visible_names`. The nested body-builder captures all seven, creating cells
and a function even when the reusable-body cache hits.

## Prior art and experiment

`component_render.py::_render_one` constructs `build` before selecting standalone
or class-based caching. `ConstBodyCache.get_or_build` owns locking, pruning,
lookup, miss execution and eviction. Earlier Cython transaction compilation
saved about half a millisecond for four functions together, insufficient to add
another build system. No closure-default experiment is recorded in the research
journal.

Try binding the builder's seven values through default parameters. The existing
zero-argument cache call remains valid, and the surrounding function no longer
needs closure cells. The referenced objects remain the same objects: mutations
through extensions remain visible. The builder still runs only on a cache miss,
under the existing lock. No cache interface, lookup count or eviction behavior
changes. The local builder has a different introspection signature; it is an
internal callback supplied by this function, not a component hook.

A new cache hit-only API could avoid constructing the function too, but adds a
lookup on misses and another cache method. A general builder-plus-arguments
interface changes the cache callable contract. Measure default capture first.
The prototype changes only the nested function's AST and uses live module
globals; it keeps the outer function's filename, name and line positions.

## Acceptance

Verify zero remaining cell variables, identical full HTML and ownership
snapshots, and the intended capture path. Use eight fresh process pairs,
six warmups and 80 measured renders, retaining all samples with normal GC.
Require seven joint wall/CPU wins and at least 0.25 ms median paired mean
wall saving before production qualification. A small or inconsistent saving
leaves the change experimental. If it passes, use ordinary source code and
proper annotations, check first/second and smaller renders, and exercise cache
misses, reentrant builds, concurrent builds, errors and extension callbacks.
Existing cache semantics and supported public mutation behavior must remain.
