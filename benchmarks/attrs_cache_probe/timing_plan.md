# Check what the paired win count is measuring

The original 45-of-60 rule was a conservative screening choice, not a
statistical significance test. The four node comparisons have positive median
paired differences in both execution orders. In the three less-loaded runs,
individual differences range roughly from -8 to +8 ms while median differences
are around 0.5 ms. The last comparison overlapped other test workers and has
much wider variation. These observations justify investigating measurement
noise; they do not justify silently changing the adoption rule.

Add a diagnostic mode that records wall time, process CPU time and garbage
collection events per render, without disabling collection or excluding its
cost from the reported total. Keep the callbacks inside the diagnostic only.
Randomize a balanced list of reference-first/candidate-first pairs with a fixed
seed. Preserve exact HTML equality within every pair, changing deterministic
IDs across pairs. Record the seed and order policy. Run two independent
processes after checking for concurrent test activity.

Inspect paired differences by order and by reached collections. Comparisons
excluding collected renders are descriptive subsets, not adoption results:
the real renderer must pay collection costs too. Likewise process CPU time
helps distinguish scheduling delays but does not eliminate all external-load
effects. Report the complete-render distributions and every raw observation.
If GC/order explains the low win count, design a further process-level
comparison before making a production proposal. Do not select a favorable
subset or change the cache implementation during this timing investigation.

The callbacks and retained diagnostic records also affect allocation and
collection timing. A collection during one render may reclaim objects
allocated by either variant's earlier renders.

## Follow-up: separate process lifetimes

The two diagnostics have median paired savings of 0.488 and 0.566 ms with
45 and 51 wins. GC-time differences correlate strongly with wall-time
differences, while the mean total savings remain positive with GC included.
Use fresh, single-variant processes to separate their heaps and GC schedules.
Each worker performs six warmups followed by 80 complete renders with ordinary
GC enabled and no GC observer. Retain wall and process CPU time per render and
compare means as the throughput measure; retain medians as descriptive data.

Run eight process pairs in balanced randomized order. Both workers in a pair
use the same Python hash seed and generated-ID base; advance render IDs across
samples and verify every HTML digest across the paired processes. Require
positive mean wall and CPU savings in at least seven of eight process pairs,
and at least 0.25 ms median process-pair mean wall saving, before proposing
production qualification. This new process-level rule replaces neither the
old recorded outcome nor the remaining semantic checks. It measures a more
appropriate independent unit after diagnosing the shared-heap limitation.
Keep all process pairs, including slow ones; inspect external load before the
run and do not launch other CPU-heavy work while it runs. A failed output
comparison invalidates the measurement rather than allowing a selected subset.
