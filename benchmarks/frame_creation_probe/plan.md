# Measure the cost of immutable render-frame construction

Every `CitryRender` captures component identity in an immutable `RenderFrame`
unless its caller supplies a frame. The large scenario calls
`RenderFrame.from_context` 1,015 times in one warm render: 326 true
component-root flags and 689 false flags (interior renders or transparent
component roots). An initial count at that boundary found 714 distinct
context/value combinations and 644 distinct values. Direct constructors and
dataclass replacement calls are outside that count.
Keeping earlier frames per context could therefore avoid only part of this
work, and would add lookups and retention.

The prior-art search covered `RenderFrame.from_context`, `CitryRender.__init__`,
the frame-finalization optimization, and frame readers in `component_render`,
`nodes`, `serialize`, `ownership_manifest` and cache replay. `RenderFrame` is
exported from `citry`, and tests use dataclass replacement, frozen-assignment
errors, subclass construction and snapshot equality. Delaying the identity
snapshot would change what readers observe after a context changes.

First measure a cheaper representation with the same five eagerly captured
fields. The experiment substitutes a named tuple and keeps the existing
`from_context` body. It supplies dataclass field metadata so the existing
replacement path can execute. All runtime import aliases found by the search
are switched together. This is a performance experiment, not a compatible
public replacement: tuple iteration, equality and assignment errors differ.
Any useful result would require a separate design preserving the public
dataclass interface, with its additional costs measured again. This is not
a mathematical upper bound on all possible frame optimizations.

Compare eight balanced randomized fresh-process pairs, each with six warmups
and 80 complete renders under ordinary garbage collection. Keep every sample
and match HTML digests and native artifacts within each pair. Separately
compare all reached ownership snapshots and count `from_context` calls and
duplicate snapshots captured at that boundary.
Do not count operations inside timed renders. Require at least seven joint
wall/CPU wins and 0.25 ms median process-pair mean wall saving to justify a
production-compatible follow-up. A failure of that screen rejects this
representation as the next production project, not every possible frame
optimization. No production source or native interface changes in this step.
