# A10 client performance and payload budgets

**Status (2026-08-20): implemented and remeasured.** Deterministic byte limits
are enforced in CI. Browser timing and heap measurements are recorded for orientation and
regression investigation because shared runners cannot provide stable timing
or memory ceilings.

## Workload

[`../../../benchmarks/client_scenario.py`](../../../benchmarks/client_scenario.py)
builds 10-, 100-, and 325-child pages through ordinary server template
ancestry. Each child has:

- a keyed server identity;
- reactive `$c-props` supplied from its parent;
- one relocated Alpine handler and one relocated Citry handler;
- one declared prop, managed effect, initializer, and cleanup;
- two root-binding resources;
- supplied default-slot content for document and fragment measurements.

The 325-instance size matches the repository's realistic large page. A
450-instance payload-only case provides a larger-workload regression budget.
These are CI architecture budgets, not protocol validity limits.

The morph timing page deliberately replaces supplied slot regions with an
equivalent nested child list. It measures the base coordinated graph, Events,
dependency, and DOM transaction without making repeated fill projection the
dominant variable. Slot and fill morph behavior remains required by the
cross-browser conformance matrix.

## Enforced deterministic budgets

[`../../../packages/py/citry/tests/test_client_performance_payload.py`](../../../packages/py/citry/tests/test_client_performance_payload.py)
enforces:

| Payload | Budget |
|---|---:|
| Combined owned Alpine and Events runtime, raw | 755,500 bytes |
| Combined owned Alpine and Events runtime, gzip | 158,500 bytes |
| 325-instance ownership graph, raw | 660,000 bytes |
| 325-instance ownership graph, gzip | 38,000 bytes |
| 325-instance document, raw | 1,442,500 bytes |
| 325-instance document, gzip | 188,000 bytes |
| 450-instance ownership graph, raw | 900,000 bytes |

The current deterministic measurement on 2026-08-20 is:

| Payload | Raw | Gzip |
|---|---:|---:|
| Combined runtime | 754,238 | 157,151 |
| 10-instance graph | 15,783 | 1,263 |
| 100-instance graph | 153,747 | 6,077 |
| 325-instance graph | 500,697 | 18,205 |
| 325-instance document | 1,441,181 | 187,232 |
| 450-instance graph | 693,447 | 24,880 |

Gzip uses Python's `gzip.compress(..., mtime=0)` so CI results are
deterministic. Runtime files are measured exactly as shipped by the Python
package. The workload uses a fresh fixed-width lowercase render-ID sequence
for every scenario, and an executable repeatability check compares two fresh
scenarios byte for byte. The page includes the declared prop, initializer,
managed effect, and cleanup listed above; payload enforcement does not remove
those lifecycle records.

The 2026-07-24 client context implementation added 37,915 raw bytes and 7,706
gzip bytes to the combined runtime. The raw runtime ceiling and the raw and
gzip document ceilings were raised by the measured feature cost while
retaining similar regression headroom; the ownership graph budgets did not
change.

Later protocol validation, ComponentRange planning and ignore transactions,
direct element event listeners, strict input-type validation, and typed custom
elements account for the current runtime baseline. These are deliberate
validation and identity costs; the limits retain narrow headroom so unrelated
bundle growth remains visible.

## Browser runner

Run the standalone benchmark after installing the e2e dependency group and
Playwright browsers:

```bash
uv run --no-sync python benchmarks/client.py \
  --browser chromium --counts 10 100 325 --rounds 9 --memory
```

Use `--json` for machine-readable output. Multiple counts run in isolated
Python subprocesses so process-wide component and asset caches cannot leak
between sizes. Each size discards one cold round and reports the median and
p95 of measured rounds.

The runner measures:

- inline document startup from response end through DOMContentLoaded;
- warm fragment adoption from parsing through graph readiness and callback
  settlement;
- a real Events render-action morph transaction and its double-animation-frame
  paint settlement;
- payload sizes and aggregate runtime resources;
- optional Chromium forced-GC heap, DOM-node, document, and all-JavaScript
  listener counts through the Chrome DevTools Protocol.

A console error, page error, missing callback, wrong component count, or wrong
resource, initializer, or cleanup count invalidates the sample instead of
producing a deceptively fast number. JSON output records
`git describe --always --dirty`, so a measurement from an uncommitted worktree
cannot be mistaken for clean `HEAD`.

## Timing policy

The reference Apple M4 target is a 325-instance startup median below 500 ms,
warm fragment adoption below 750 ms, and base morph transaction below 1,000
ms. A two-second median in any of those paths is a catastrophic regression
that requires investigation. These are developer-machine orientation targets,
not CI assertions. Browser version, operating system, power state, build
profile, and runner contention must accompany published measurements.

Compare timing numbers only within one captured run. Payload budgets are the
portable release gate.

The 2026-08-20 refresh on an Apple M4, Chromium 151.0.7922.34, Python
3.14.3, macOS 26.6.2, and nine measured rounds after one discarded cold round
gave:

| Instances | Startup median/p95 | Adoption median/p95 | Morph median/p95 | Forced-GC used heap |
|---:|---:|---:|---:|---:|
| 10 | 19.3 / 19.6 ms | 27.1 / 27.6 ms | 0.8 / 0.9 ms | 2,418,164 bytes |
| 100 | 58.1 / 59.8 ms | 87.8 / 93.7 ms | 0.8 / 0.9 ms | 3,488,400 bytes |
| 325 | 358.5 / 361.3 ms | 568.2 / 574.3 ms | 0.9 / 0.9 ms | 6,175,524 bytes |

The refresh first found an obsolete runner oracle: it expected a keyed morph
to destroy and recreate every child, so it waited for doubled initializer and
cleanup counts even though the current runtime correctly retained every keyed
physical node and lifecycle resource. The runner now requires the initializer
and cleanup counts to remain unchanged and still rejects browser errors,
resource drift, or wrong component counts. The much smaller morph transaction
time therefore reflects retained keyed identity, not a disabled correctness
check. Paint settlement remains measured separately in the JSON result.

The earlier closeout run also found and closed a correctness failure:
mixed-case base-62 render IDs could differ only by case while their
`data-cid-*` attribute names collapsed under HTML case folding. Production IDs
now use a `c` prefix plus eight lowercase base-36 characters, custom generators
reject unsafe values, and graph plus Events consumers validate the wire value
before using it in a selector.

## Interpreting resource counts

`nativeListenerTargets` counts Citry RootGroup target/type registrations. It
is not the browser's total JavaScript listener count. The optional Chromium
CDP sample supplies the latter. Events reports ordinary HTML bindings
separately as `bindingListenerElements` and `bindingListenerTargets`; the
second count is the sum of element/event-type registrations. Likewise,
`propsEffects`, `managedEffects`, and Events `formEffects` are separate
categories; adding them together does not produce an Alpine internal effect
total.

The cross-browser churn test, rather than a heap threshold, is the enforced
leak detector: 25 compatible morphs must leave all stable aggregate resource
classes unchanged and must run exactly one cleanup per replaced render. Every
morph except the last carries a distinct `js_data()` payload. Live class-data
ownership must stay fixed, while the page-lifetime content-addressed cache adds
one entry per new hash. The final fresh graph repeats an earlier hash and must
settle without adding a cache entry or fetching its already-loaded variables
script again.
