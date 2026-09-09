# Repeat-render optimization handoff

Optimization experiments are paused at the user's request on 2026-09-09.
The work is on `perf/repeat-render-20260908` in the separate
`citry-perf-repeat` worktree. Runtime changes, experiments and measurements are
committed by area. The branch has not been merged or published.

## Changes kept in the runtime

The measurements below belong to their own controlled comparisons. They cannot
be added together. Small early measurements are reported with their original
limits; the cumulative comparison is the stronger measure of the combined work.

| Area | Change kept | Evidence or measured effect | Implementation commits |
| --- | --- | --- | --- |
| Immutable ownership records | Use cheaper tuple-based records and separate reusable source sites from individual occurrences | Initial ownership records saved 1.253 ms; source rows saved 0.573 ms in a separate comparison | `efd4fe1b`, `db0d90e3` |
| Ownership retirement and selection | Avoid temporary retirement collections, skip searches for fresh text containers and skip empty hook retirement intervals | Text-container selection saved 0.599 ms; other guards have no standalone material claim | `9e111ead`, `f56df3db`, `81bb323b` |
| Native ownership storage | Keep related records and calculations together in the shared Rust ownership crate, including queue updates, slot preparation and retirement; preserve Python integer semantics | Integrated backend saved 1.534 ms on the large page | `d9aa7bc1`, `e8f55c7e`, `1d8e8217`, `9cc32644` |
| Small renders | Allocate native ownership storage only when a nested component invocation needs it | Recovered 0.004560 ms on the small case | `b11a8952` |
| HTML attributes | Reduce temporary normalization objects and reuse validated spread keys, plain class merges and bounded final attribute strings | Normalization saved 1.881 ms; final guarded output reuse saved 0.551 ms in a later comparison | `e5406403`, `3533fba7`, `59e84ac1` |
| Render traversal and values | Skip plain text during structural searches, retain unchanged empty frames, avoid re-entering active ownership scopes and bypass redundant protocol inspection for known values | Local savings: 0.227, 0.401, 0.169 and 0.755 ms respectively | `4ed9ad8d`, `1db0e1d7`, `3910d949`, `d1c25cb6` |
| Input and expression work | Check input constness with a direct loop and combine compiler-proven bare-name evaluation steps | 0.180 ms and 0.198/0.274 ms in their local comparisons | `4f529c60`, `1a57a09c` |
| Extension configuration | Prepare configuration constructors once per exact class | Kept simplification; no material standalone speed claim | `58e01234` |
| Explicit simple components | Add `Component.simple = True` and support it on `LibraryComponent` definitions, with strict validation, caller ownership, static data callbacks and optional default content | First public-API comparison saved 8.425 ms, or 26.63%, when Button, Icon and HeroIcon opted in | `fcf6df0c`, `7ff404cc`, `1c70f91d` |
| Deep render interiors | Traverse nested interiors with explicit stacks during scheduling and serialization | Correctness coverage includes a 1,100-level chain; no speed claim | `816136e0` |
| Transparent placements | Mark each whole transparent output explicitly, preserving remote caller-owned fills and one boundary through cache replay | Server, browser and cache-replay qualification; no speed claim | `ec26f3d4`, `5dffcef` |

## What the aggregate measurements establish

The last direct cumulative comparison against the original runtime measured
**39.609 to 30.147 ms warmed rendering, a 23.89% reduction**, with ordinary
component behavior retained. Actual second-render medians were 42.158 to
34.522 ms. Those figures come from iteration 47, before the public simple API.

The first public simple comparison measured **31.589 ms ordinary and 23.215 ms
simple** on the large page. Median paired saving was **8.425 ms, or 26.63%**,
with wall and CPU improvements in all six blocks. Actual second-render medians
were 36.365 and 23.425 ms. All 196 selected data callbacks stayed live while
196 independent component identities were removed. That opt-in changes the
component contract; it is separate from the default-runtime improvement.

Django measured 11.032 ms warmed in that comparison, leaving the selected simple
page at 2.10 times its render time. Django emits different output and does not
perform all Citry's component, dependency and browser-ownership work. Parity was
not reached, and no claim combines the two separate comparisons into one gain.

The refreshed published chart uses a new, internally comparable run across
ordinary Citry, simple Citry, Django, django-components and Jinja2. Its raw
observations are in `benchmarks/results/publication-20260909.json`. The warmed
medians are 32.710 ms ordinary, 23.849 ms simple, 11.277 ms Django, 52.867 ms
django-components and 6.967 ms Jinja2. Median paired simple saving is 26.71%.
That report records measurement revision `7c292e8c`; the final transparent-output
correctness fix `5dffcef` is subsequent work, with no new speed claim.

## Experiments that are not runtime changes

The repository retains prototypes and their evidence under `benchmarks/`,
including Cython/ABI experiments, generated execution functions, alternative
ownership records, native attribute operations, scheduler plans and direct
function text emission. Their presence in commits does not activate them in
ordinary rendering. Iteration 68's shared text buffer remains experimental and
is not part of `Component.simple`.

The remaining presentation-class group, dynamic HTML element redesign, broader
slot/JS contracts and alternative render representations are parked. No further
optimization experiments are scheduled for this handoff.

## Documentation and validation

The public feature is documented in the simple-component guide and linked from
the performance page, component guide, API reference and navigation. The design
document retains the implementation decisions and error boundaries. The runtime
catalog continues to describe registered classes, schemas and assets; it does
not gain a new flag field for this feature, just as it does not expose `pure`.
The public flag remains available on the component class itself.

The full repository gate passed all 19 phases: Rust checks/tests, Python lint,
formatting, typing and tests, JavaScript packages, protocol contracts, and
repository validators. Python coverage was 88.64% against the 88.5% requirement.
The separate Linux-platform mypy run passed across 537 source files. Four hook
replacement tests added after the full gate's collection also passed.

The Citry/UI Chromium suite covered 1,269 cases: 1,263 passed initially and six
needed the generated Tailwind fixture. After building it, all 12 CSS-coexistence
cases in the focused rerun passed. The simple-component and transparent-boundary
checks also passed in Firefox and WebKit (six cases).

The docs browser suite passed 106 of 108 cases initially. The remaining two
passed on focused reruns: one after refreshing stale installed Citry UI version
metadata, and one toast-focus assertion without a code change. The toast failure
is recorded as transient; no claim is made that a runtime defect was fixed.
The final `python -m docs_site build-check --strict` passed with no guard findings.

Independent technical and separate prose reviews checked the runtime correction,
public documentation, benchmark evidence and chart values. These checks qualify
the implementation being handed off; they do not establish performance beyond
the retained benchmark evidence.

## Detailed evidence

- [Research journal](performance_render_research.md)
- [Every experiment and its decision](performance_render_experiment_summary.md)
- [Simple-component design](component_simple.md)
- [Cumulative comparison](../../benchmarks/results/performance-render/round47-comparison.json)
- [First public simple comparison](../../benchmarks/results/performance-render/simple-api-timing-main.json)
- [Public feature guide](../../docs_site/content/advanced/simple-components.md)
