# Qualify direct template fills with live helper checks

Iteration 55 removed unused fallback objects and generic slot-call contexts,
reducing the process mean warm-render time by 0.370244 ms at the median across measured pairs. Its two
reproduced compatibility failures block adoption. The user's threshold question
reopened qualification under the earlier 0.25 ms and seven-joint-win screen.
This experiment adds guards for the reproduced failures before measuring the path again.

## Prior art and design

Keep iteration 55's normal outlet method, source/fill records, ownership capture
and body execution. Replace equality-based helper tests with identity tests.
Check the supply-selection record and constructors that can expose omitted
objects, slot-data normalization, fill-data binding and the Python region-capture
method. Require the expected graph to be active so retained contexts use the
ordinary resume path. When eligibility detects a change to a listed helper or an
unsupported input shape, it uses the original fallback construction and slot call.

Generate a fixed chain of identity checks from an explicit dependency list once
at adapter import. This avoids per-call tuple construction and loops for those
checks; it does not cache the result of a check or freeze live application values.
Keep graph-bound method checks separate so instance-level replacements remain
visible. Construction and data helpers stay live in the ordinary fallback path.
No compiler dependency, ABI change or production source change is introduced.

Preserve the original failure cases and add checks for skipped constructors,
normalization and binding helpers, Python capture changes and retained contexts.
Helpers can execute callbacks after initial eligibility, so these checks are
qualification evidence, not proof against every possible mutation. Any remaining
failure must be recorded before a diagnostic timing decision.

Independent review found two further omitted operations: the slot-error context
can replace content after preparation, and a SlotContext attribute reader can
observe access to provides. Fresh-process cases reproduce both differences before
their guards are added. The revised helper list includes the error context,
SlotContext attribute access and field descriptors, and object attribute setters.

## Measurement and adoption

Run the rendering/ownership test selection and compare complete HTML and four
canonical snapshots. Keep activation counters outside timing. Use eight balanced
randomized fresh-process pairs, six initial and 80 warm renders per worker,
ordinary GC and every sample. No tests or builds overlap main timing. The
predeclared performance screen is at least seven joint wall/CPU wins and a
0.25 ms median paired reduction in process mean warm wall time. Keep actual second
renders separate. A passing result supports broader qualification, not adoption
with a known failure. Preserve measured sources and all samples on either outcome.

## Outcome

The eight-pair result saves 0.158217 ms wall and 0.158569 ms CPU by the median
paired reduction in process mean warm time, with six joint wins. It misses both
parts of the 0.25 ms / seven-win screen. Reject this guarded implementation.
Actual second renders save 0.552479 ms wall with seven joint wins across only
eight observations per variant; that separate result does not change the
predeclared warm-render decision.

All 625 selected tests and fourteen focused cases pass. During main timing,
independent review identified a further callback through string-subclass provide
keys. A fresh-process case after timing proves it: both mappings are exact dicts,
but key equality changes the selected template's fallback binding during their
merge. Reference renders fallback text; candidate renders the supplied variable.
The fifteen-case report records this failure. No helpers need to be replaced for
this case, although its callback deliberately changes private template state.
The performance result does not justify extending this guard chain further.

The shared-process contracts draft is not qualification evidence: replacing and
restoring inherited __new__ caused later unrelated cases to fail in both variants.
Fresh workers isolate every case and require reference success (or its intended
error) and helper activation before comparing results. Measured sources and all
draft reports remain archived. Production remains unchanged.
