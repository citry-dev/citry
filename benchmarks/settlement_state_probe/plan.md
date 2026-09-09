# Make settlement state explicit across the compiled pipeline

## Prior art

Iteration 49 compiles complete component-render, node and slot modules and passes
the performance screen at 2.149 ms saved per render. Two lifetime tests fail:
the compiled `_settle_render` scope stores four callbacks that each reference
the same scope, and the scope retains the root render. Its pending task stack
and current root are the only shared mutable values the callbacks require.
The five local functions are commit, requeue, settle, settle_in_invocation_region
and bubble, in `component_render.py:252-484`. The generated C and retained
`render-modules-lifetime.json` demonstrate the reference cycle.

## Representation change

Give one render-local `_SettlementState` object two slots: the existing task
stack and the current root result. Move the five nested functions to ordinary
methods, passing state as self. Rewrite their references to shared fields and
each other through self; the outer loop uses the same stack and calls the
state's methods. The state does not store bound methods, so normal method calls
do not create a callback/state cycle. Preserve task creation, hook and error
handling order, requeue behavior, ownership retirement and cache publication.

Transform only a temporary copy with a bounded AST rewrite whose exact source
and transformation counts are recorded. Compile the same three complete modules
as iteration 49 under their real names. Retain Python classes and objects; this
does not introduce native extension classes or numeric narrowing. Source-level
introspection and helper metadata change and remain qualification concerns.

Explicitly clearing closure callbacks in a finally block could break the cycle,
but would keep allocating the callbacks and rely on Cython's closure layout.
The state object exposes the actual relationships and gives later execution
work a stable internal structure. Disabling garbage collection or ignoring the
lifetime tests would not solve the demonstrated problem.

## Qualification and decision

First verify the transform is limited to the five callbacks and their shared
references. Compare complete HTML and all four canonical ownership snapshots;
rerun the 625-test selection from iteration 49, especially both failed lifetime
cases, and repeat the focused collection diagnostic. Inspect and retain any
remaining cycle or failure before changing the candidate. Broaden replay/error
qualification if the focused checks pass.

Compare the corrected whole pipeline against ordinary production in eight
balanced randomized fresh-process pairs, six initial and 80 warm renders per
worker, with normal GC and all observations. Require seven joint wall/CPU wins
and 1 ms median paired reduction in process mean wall time, as in iteration 49.
Actual second renders remain separate. No tests or builds overlap timing.
This measures the complete corrected pipeline; it does not isolate the state's
incremental contribution or reuse the previous prototype's speed as proof.
A pass supports broader qualification, not production deployment by itself.
