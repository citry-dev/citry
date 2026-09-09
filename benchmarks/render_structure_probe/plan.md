# Measure which render structures are rebuilt and revisited

Cython and ABI work is parked. Before selecting the next larger rendering change,
count construction and traversal over the same complete page, then vary a loop's
input size. This distinguishes reusable authored structure from request-specific
occurrences and checks whether repeated tree discovery is substantial enough to
justify changing how rendering communicates pending work.

Prior art: `component_render._render_body` constructs nested parts, then
`_scan_deferred_parts` searches those parts for tasks. `_contains_deferred`
separately checks foreign-context content before merging dependencies. Public
`CitryRender.parts` remains mutable, and hooks may replace a tree, so a cached
work list cannot be reused without a mutation boundary. Iteration 42 moved the
search to Rust but retained discovery and conversion; its regression does not
answer whether construction can supply the pending work directly.

Run six warmups, then two unchanged inputs and one shortened `outputs` input.
Count body and scan input lengths and render/frame construction through a Python
profile callback. Observe ownership snapshots at their existing call sites and
compare their complete canonical values with deterministic IDs. This is an
untimed structural diagnostic; profiling adds overhead and its counts cannot
be converted into predicted milliseconds. Do not modify production or remove
ownership capture. Record whether changed loop input changes the topology and
retain source hashes. Use the results to choose a bounded algorithm experiment,
not to claim a speedup or general stability across requests.
