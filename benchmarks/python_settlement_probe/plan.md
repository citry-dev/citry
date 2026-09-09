# Iteration 58: explicit settlement state in ordinary Python

## Prior art and scope

`component_render.py:208-544` settles deferred children and hook replacements
using five nested functions sharing the task stack and root result.
`slots.py:317` and `host_templates.py:78` import that scheduler when needed.
The on-render design specifies replacement, error bubbling and child-first
finalization. Iteration 50's `settlement_state_probe/transform.py` already moves
these five functions to methods on one object with slots for the task stack and
root result; the rewrite changes how those shared values are accessed.
It was measured only with three compiled modules; its 3.132 ms result does not
identify the contribution of the state representation in ordinary Python.
Iteration 54's producer scheduling added plans and changed mutation behavior;
this candidate keeps the existing scan and task queue.

Reuse the bounded transform, then execute only the generated state class and
scheduler function in the original module globals. All other functions and
classes keep their identities. This is a benchmark-only adapter with no Cython,
ABI, native build or production source changes. The hypothesis is that creating
one state object per scheduler invocation costs less than rebuilding five local
functions. Method dispatch and state attribute access could erase that saving.
The ordinary closure scheduler is the comparison and the fallback decision.

## Qualification and measurement

Before timing, run the existing 625 rendering, hooks, slots, ownership, const and
dispatch tests with the candidate installed. Check immediate component and graph
release on a small fixture and all four ownership graph observations of the large
fixture. These diagnostics disable automatic GC only to expose retained cycles;
throughput timing retains ordinary GC. Review the transform and module installation
independently. Incompatible hook, replacement, error, cache or lifetime behavior
blocks adoption. Generated traceback locations and private function inspection
can differ and require assessment before production integration.

Measure eight balanced randomized fresh-process pairs, six initial and 80 warm
renders per worker, retaining every sample. Compare every initial and warm HTML
digest and four full canonical ownership snapshots. Count state constructions
outside timers and confirm the generated scheduler remains active. Run no tests
or builds during main timing. Require at least 0.25 ms median paired reduction in
process mean warm wall time and seven pairs improving both wall and CPU time.
Report actual second renders separately. Passing justifies broader qualification;
failure rejects this change as a standalone performance optimization without
retrying for a favorable run.

These benchmark-only checks protect hook behavior and graph lifetime at the
scheduler boundary. They reuse existing tests and the retained full-render harness,
add no CI or release step, and should take seconds for checks and about a minute
for timing. Independent read-only review can overlap local preparation.
