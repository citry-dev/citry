# Iteration 67: inspect the remaining render-tree work in composed functions

Iteration 66 makes 195 calls use caller-owned templates, reducing warm time while
retaining ordinary body nodes, interior render objects, settlement and serialization.
Before choosing another representation, measure which of those stages remains
expensive and which function outputs contain only finished text.

Read the composed adapter, `_render_body`, `_contains_deferred`,
`_scan_deferred_parts`, `CitryRender`, `RenderFrame`, the physical-region wrappers,
and the prior render-breakdown and call-profile harnesses. Interior renders can
carry deferred components, physical slot occurrences and extension data. A wrapper
without its own assets may still receive collected data from caller content.
Do not infer that every interior render can become a string.

Use separate processes for ordinary, composed-immediate and composed-deferred
diagnostics. Retain all cProfile rows after six warmups and twenty profiled renders.
Report self time and calls; cumulative times overlap and must not be added.
Observe object construction in a separate untimed render, including function
results at their creation point before the scheduler settles descendants. Count
component-root renders, deferred function calls, deferred ordinary children,
physical regions, placeholders and nonempty
context data as explicit obstacles to representing a result as text alone.

These counts describe the reached output shape; text conversion also needs to
preserve context-merge effects and serialization markers. Empty context data does
not suppress merge hooks, and the serializer can emit transparent-instance markers
around interior renders. Record differing ownership graphs and error-tainted
contexts, and distinguish queued template functions from ordinary child components.
Ancestor and nested function records overlap, so their subtree counts cannot be
summed as page-wide allocations.

Check fixed function activation and compare complete normalized application output
with the ordinary reference. The diagnostic observer must preserve exact output
within each mode. Preserve measured iteration 66 sources. This is a mechanism
study; profiler time is not a fresh-process performance decision. A subsequent
representation experiment needs its own contract, checks and paired timing.
