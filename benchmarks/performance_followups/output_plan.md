# Deferred simple output in one parts buffer

Prior art: iteration 68's `function_text_probe/adapter.py` measured direct emission
under an immediate, exact-class function contract. The public `_simple_runtime.py`
keeps deferred scheduling and SimpleRender boundaries. `component_render._render_body`
still constructs interior conditional/loop renders, then serialization walks them.
`IfNode.active_branch_body` and `ForNode.iter_bodies` expose existing validated
branch/iteration behavior, including current loop contexts. This candidate tests
the representation under the released deferred API, not immediate execution.

One candidate emits simple template control-flow bodies into a shared parts list,
joining adjacent text runs while retaining slot results, deferred components,
foreign renders and physical regions as structured objects. It aims to preserve the top
SimpleRender boundary, current callback schedule, ordinary dependency merges and
value-context selection. Transparent callers and tracing retain their current
walker because their interior frames or trace observations may matter.

The experimental restriction is that hooks must not depend on the number or
shape of same-owner simple interior text/control-flow parts. Plain HTML, client
manifests, source records, callback execution and ordinary child ownership must
remain unchanged. Attributes still evaluate and escape current values; this is
not output caching. Errors retain template positions, and expressions execute
once. A mismatch rejects this one candidate before timing, with no second variant.

Qualification compares exact serialized output, all four ownership snapshots,
manifest validation and authored callback counts on the full benchmark. Exercise
changing simple loop data, ordinary children in loops and error behavior. If it
passes, use the same six balanced process orders, matched hash seeds and 80 warmed
renders as the other follow-ups. Require six wall/CPU wins and paired 95% intervals
above zero; there is no extra build requirement or 1 ms floor. Prototype files and
results remain on the research branch.

## Qualification outcome

The full-page observation matched projected content, manifests and ownership
snapshots; the initial assertion did not include raw HTML. Review caught that
oracle gap, so qualification now separately requires fixed-ID raw HTML equality.
All 74 simple, pure and transparent-placement tests passed under the prototype.

Independent review identified a stronger counterexample: an ordinary child inside
a conditional inside a simple loop merges through the loop context in the
control. Flattening removes that intermediate merge target. The retained public
`on_render_context_merge` witness records different contexts and hook counts.
This violates the proposed preservation of ordinary dependency merges, beyond
the declared change to interior part shapes. Reject this candidate before timing.
A design preserving merge edges separately from text might address it, but no
second representation is attempted in this bounded follow-up.
