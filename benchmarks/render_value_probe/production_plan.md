# Put the guarded conversion branches into production

The revised prototype improves all eight process pairs on both wall and CPU
time, with a median reduction in process mean wall time of 0.800 ms. It
preserves four ownership snapshots and every HTML digest, passes 23 dispatch
regressions and 249 existing tests, and checks protocol behavior on seven
installed interpreters using Python-only stand-ins. Independent review closed
alias, preinstalled-type and older-protocol lookup gaps.

Insert the same branches into `citry_render._render_value`, after Const
unwrapping and Slot dispatch. Preserve all existing downstream paths. Capture
the original ComponentLike and CitryElement identities in their defining
modules; use those identities with locally defined CitryRender and
PhysicalRegionPart in the guard. This prevents a preinstalled imported alias
from becoming trusted. Keep class membership, class shape and escaping live.
No new cache, public API, grammar, AST or native surface is needed.

Reject or revise if production changes protocol resolution, scalar output
types, escaping, callbacks, dynamic class changes, explicit registration or
runtime alias replacements. Preserve the experiment's scope: private edits to
typing's protocol implementation or metadata and concurrent class mutation
are not newly qualified by these identity checks. Put representative
regressions in the normal package test suite and retain the interpreter
dispatch checker as separate evidence, not a full native support claim.

Compare the actual production function against the pinned pre-change source
in the same eight-pair, 80-sample runner with ordinary GC. Require seven joint
wall/CPU wins and at least 0.25 ms median reduction in process mean wall time,
matching output digests and nonempty equal ownership snapshot traces. Count
actual production branch execution only in a separate untimed render. Run
focused checks during implementation, then the repository integration gate
and browser suite once the runtime change settles. Obtain independent
technical and separate prose review before the production commit and record
all results in the research log. A failed comparison leaves the prototype as
evidence rather than adopting a slower guarded implementation.
