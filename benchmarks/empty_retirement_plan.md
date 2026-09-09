# Skip an empty hook-retirement interval at its caller

## Prior art

`component_render.py::_settle_render.requeue` passes the capture order before
and after a component hook to `OwnershipGraph.retire_unselected_after()`.
At `2412f7b0`, the default large scenario calls it once with both orders equal
to 3,849. All five record intervals are empty. The method still closes ancestry
and builds indexes. Production uses those indexes again during subsequent
component-output retirement; the native prototype otherwise does not need them.

Keep selection discovery and retirement of the old component output unchanged.
Only omit the hook-side-effect retirement call when its two caller-owned
capture orders are equal. This leaves the ownership helper's direct-call input
behavior intact. Nonempty hook intervals continue through the same method.
No parser, compiler, public schema or native API changes are needed.

## Measurement and decision

Add an opt-in case to the existing repeated-work harness. Compare the exact
reference function from `2412f7b0` with the one-branch candidate, first using
production ownership and then the existing native stored-row backend without
native ancestry. Record an untimed interval trace and actual retirement calls
for each mode. Compare all reached ownership snapshots and every timed HTML
pair, with deterministic IDs and 60 alternating pairs per run.

The guard makes an empty interval explicit and adds no cache or backend. Keep
it only if existing hook/ownership/replay checks preserve nonempty-interval
behavior, instrumentation confirms the empty call is skipped, and two production
comparisons show no systematic regression (more than 0.15 ms median paired
slowdown with at least 40/60 slower pairs). Claim a production speedup only if
the gain is consistent; a neutral result can justify this small guard but not
a numerical improvement claim. Native comparisons establish whether omitting
the Python consumer helps the larger experimental representation.

Use the existing focused renderer, ownership, manifest and replay tests rather
than a test that merely mirrors the new condition. If the guard is retained in
production, run the final integrated repository checks. The benchmark is opt-in,
adds no CI gate, and takes seconds. Keep builds/tests outside timing runs.
