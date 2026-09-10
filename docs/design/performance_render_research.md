# Repeat-render optimization research

## Objective and working state

Improve repeat rendering toward the Django benchmark while preserving Citry's
ownership, hooks, cache, validation and browser behavior. Work takes place in
`/Users/mac/repos/citry-perf-repeat`, branch `perf/repeat-render-20260908`.
The original checkout is left untouched. Commit `1294c51d` captures the existing
uncommitted working state, including prior ownership work; it is a baseline,
not an optimization. Each completed area receives a separate commit.

The user waived the fable workflow and authorized continued optimization beyond
ownership. Measurements guide the next areas; final validation covers the
combined change. Targeted checks during development catch representation errors.

## Measurement setup

Python 3.14.3 on the same Apple M4 machine as the ownership investigation.
The worktree has a copied isolated environment with editable imports redirected
and verified to resolve inside this worktree. The native extension is the same
release artifact used by the baseline, SHA256
`57c7320a79c9ba202dfe3512b7e5a53c59a935fab8b26fcaabf4946fdf8fe9bc`.
No Rust changes have been made. Django 6.0.6, django-components 0.151.1 and
Jinja2 3.1.6 provide the documented baseline dependencies.

The bounded worker uses the repository's scenario source slicer, times first
and second renders separately, then takes 20 samples after six renders.
Fresh-process comparisons alternate original and candidate checkouts seven
times. Raw results are in `benchmarks/results/performance-render/`. Absolute times
only describe this workload and machine. Per-process HTML hashes vary because
scenario/runtime state differs; equivalence is checked separately within one
process with shared scenario data and reset render IDs.

## Area 1: ownership record construction

Six frequently reconstructed ownership record types use immutable NamedTuple
storage. Their named fields, defaults and update methods remain; replay uses
`_replace` to remap those rows. Source records and snapshots remain dataclasses.
This tests cheaper immutable allocation before introducing a mutable builder's
snapshot/rollback bookkeeping. Records still cannot change beneath an existing
snapshot or shallow replay backup.

Seven alternating process pairs measured median process warm times of
38.403 ms baseline and 37.151 ms candidate, a 3.3% reduction. Second-render
medians were 41.348 and 40.796 ms. These are modest improvements, far from Django
parity. A separate alternating in-process probe checks identical HTML.

Focused ownership, manifest and replay tests: 128 passed. Further validation
of cache, security and all combined changes remains for the final gate.

## Next areas

Reduce retirement's temporary collections and repeated scans; prepare extension
configuration constructors once per component class; inspect attribute merging
and normalization. Keep only changes supported by complete-render measurements
and preserve invalidation and dynamic-input behavior. Revisit mutable capture
storage if the additional implementation complexity has a measured payoff.

Area 1 equivalence follow-up: alternating in-process medians were 38.908 ms
baseline and 36.938 ms candidate; the complete 1,013,746-byte HTML matched
exactly. Ruff passed for ownership.py. The same-run Django warm median was
11.155 ms, leaving the candidate about 3.33 times slower on this workload.

## Area 2: retirement temporary collections

Retirement builds one active-instance class lookup and uses it for membership,
then inspects each fill's region IDs once. It avoids a separate active-ID set
and two intermediate per-fill region lists while preserving newer selected
regions, original order and receiver rebinding. Alternating in-process medians
were 36.720 and 36.594 ms, a small 0.13 ms difference, not a material independent
speedup claim. HTML matched exactly; the same 128 focused tests and Ruff passed.
The change reduces work without introducing persistent indexes or cache state.

## Area 3: extension configuration setup

Component-class setup now retains its exact ordered configuration constructors.
Instance setup creates fresh configs from that plan, avoiding repeated extension
filtering, class lookup and subclass checks. The plan is stored on the exact
component class, rebuilt with config materialization, and never inherited from
a parent's class. No config instances are shared. The fallback builds missing
plans for classes created before setup.

The in-process comparison was 36.827 versus 36.747 ms, too small to claim a
material whole-page improvement by itself. HTML matched. Extension tests:
82 passed, 1 expected failure. Ruff passed. Combined measurements follow.

## Area 4: attribute normalization and formatting

Nested class/style values now update one accumulator rather than allocating a
mapping for every nested item. Bounded caches reuse whitespace tokenization of
exact class strings (512 entries, at most 2,048 characters each) and identity
normalization of exact attribute names (512 entries, at most 256 characters).
String subclasses bypass shared caches, preserving their custom behavior.
Dynamic mappings and enabled/disabled values are still processed each render.

The internal renderer inserts already-escaped attribute strings directly;
public formatting still returns Markup. This avoids Markup allocation and its concatenation dispatch for an
already-escaped attribute chunk. Attributes introduced
by extension hooks still take the validated path.

Alternating full-page medians were 37.552 ms with the previous attribute path
and 35.670 ms with the candidate, a 5.0% reduction within that comparison.
The complete HTML matched. Attribute/template/security tests: 240 passed.
Ruff passed. These gains are not added arithmetically to earlier independent
measurements; a final fresh-process comparison will measure the combined work.

## Mutable builder experiment (not retained)

A temporary prototype used mutable slotted records, changed only updated
fields, cached immutable snapshot rows, and copied mutable rows for replay
rollback. Full-page alternating medians were 34.628 ms for the immutable rows
and 34.767 ms for the mutable prototype, with identical HTML. This does not
prove every mutable design loses, but it does not justify the extra state and
rollback machinery here. No mutable-builder implementation is included.

## Area 5: immutable source occurrence storage

Source sites and occurrences now also use named immutable tuples, preserving
their separate identities, metadata properties and cache relocation fields.
The occurrence's shared site reference is named `site`. Source replay remapping
uses `_replace`; no source information or capture is omitted. The existing
shared-site identity assertion follows that internal field name.

Alternating full-page medians were 36.273 versus 35.700 ms, with identical HTML.
Ownership/manifest/replay/security checks: 247 passed. Ruff passed. Before this
area, the broader Python suite passed 4,659 tests with 5 skips and 1 expected
failure; it will run again against the complete final change.

## Area 6: plain-text traversal

Deferred-component discovery and render-ID walks skip exact plain strings
before checking wrapper/render types. Body rendering also inserts exact string
results directly. Ownership containment avoids dictionary and cycle-set work
for exact strings, which cannot identify a physical region. Subclasses and
all structured parts retain the existing path.

Alternating full-page medians were 34.768 and 34.542 ms, a small difference;
HTML matched exactly. The complete Citry Python suite then passed 4,659 tests,
with 5 skips and 1 expected failure. Ruff passed. Final formatting also removed
one extra blank line from extension configuration setup.

## Final combined measurement

The durable runner is `benchmarks/performance_render.py`. It executes the existing
scenarios in fresh subprocesses, alternating baseline/candidate/Django order,
with five rounds per engine and size. Each process records the first and second
renders separately, then measures 20 renders after six warmup renders. Unlike
the exploratory equivalence probes, this runner does not reset render IDs or
replace the scenario's clock. Full observations and native/scenario hashes are
in `benchmarks/results/performance-render/final-comparison.json`.

The baseline checkout is pinned to `1294c51d`, rather than depending on later
edits to the user's original checkout. Both Citry checkouts used the same native
artifact hash recorded above. Code under measurement is the six optimization
commits through `4ed9ad8`; subsequent changes add tests, reporting and comments.

| Scenario and observation | Baseline Citry, ms | Optimized Citry, ms | Django, ms |
|---|---:|---:|---:|
| Small: second render | 0.2309 | 0.2151 | 0.0417 |
| Small: steady-state median | 0.1225 | 0.1134 | 0.0197 |
| Large: second render | 39.6308 | 37.9760 | 11.2241 |
| Large: steady-state median | 38.7302 | 34.9273 | 11.0256 |

The combined large-page steady-state reduction is 9.8%; the second-render
reduction is 4.2%. Small-page reductions are 7.4% steady-state and 6.8% on the
second render. The large-page first-render medians were 83.150 ms baseline,
76.926 ms candidate and 18.492 ms Django. No first-render regression was
observed in this comparison.

Django parity was not reached: optimized Citry remains 3.17 times Django's
large-page steady-state time and 3.38 times its second-render time. Both Citry
variants produced 1,013,746 bytes for the large page and 338 bytes for the small
page. Django produced 456,422 and 381 bytes respectively. These are existing
framework scenarios, not identical feature sets; Citry's browser ownership,
security and extension behavior remains enabled. Same-process per-area probes
checked byte-identical Citry HTML; byte counts across fresh processes alone
would not prove equivalence.

## Final validation and review

- Complete Citry non-browser Python suite: 4,659 passed, 5 skipped, 1 expected
  failure, after all six runtime areas.
- Complete Citry browser suite on Chromium: 553 passed. A separate earlier
  ownership/cache/slot/CSP subset passed 45 tests.
- Two additional public class-normalization regressions cover a string subclass
  that cannot be hashed and a mutable class mapping changing between calls.
  The final attribute suite passes with these included.
- Mypy: all 158 Citry runtime/typing-contract files passed with Linux platform
  analysis; the five changed runtime paths also passed the local-platform pass.
- Ruff check and formatting passed for the changed runtime and benchmark files.
- Independent technical review found no blocking runtime issue. Its separate
  prose review corrected the description of Markup concatenation and the
  formatter comment. NamedTuple equality does differ from dataclass equality:
  an equivalent plain tuple can compare equal. No production consumer requiring
  class-sensitive equality was found; snapshots and rollback remain immutable.

The full repository coverage and qualification profile passed every non-Rust
phase. Its three Rust phases initially failed on worktree dependency setup;
formatting, Clippy and Rust tests all passed on targeted reruns after the
correction described below. All final phase verdicts and their evidence sources
are in `benchmarks/results/performance-render/final-validation.json`; the initial
full-profile report is preserved in `full-profile-initial.json` with its FAILED
status. Detailed passing rerun records are preserved in
`benchmarks/results/performance-render/dependency-rechecks.json`. The complete
supported-Python/browser version matrix was not run. Rust source, protocol
formats and browser source were unchanged.

## Remaining performance gap

The mutable-builder prototype did not show an improvement after including
snapshot work. The retained changes reduce allocation and repeated static
work without dropping runtime behavior. Reaching Django parity would need a
larger reduction than these representation changes provide, most likely in
component construction and coordinated native ownership operations. Moving
individual field reads across the Python/Rust boundary or enabling unsafe
capture omission is not established as a solution by this investigation.

## Worktree build-dependency correction

The original checkout's Ruff submodule is at `5b48a040974781ba90b47c8df628f8fd9b6c95dd`
(0.16.2), while its recorded superproject pointer was still
`45bbb4cbffe73cf925d4579c2e3eb413e0539390` (0.14.10). The initial snapshot copied
ordinary working files but retained that older Git pointer. Rust integration
checks exposed the mismatch. The optimization branch now records the revision
actually used by the original checkout; this is preservation of existing working
state, not a new dependency upgrade. Python performance comparisons used the
same already-built release extension throughout and are unaffected.

Build dependencies are installed locally in the worktree. Temporary dependency
symlinks were removed because they changed generated JavaScript bundle paths.
The first integration reports include those setup failures; final evidence uses
the repaired dependencies and retains the original reports' failure status.

Final integration evidence covers all 19 full-profile phases, including coverage
and qualification. No coverage threshold or test expectation was weakened.

## Continued iteration: select surviving objects before searching regions

The next pass starts from `26a2392b`. A fresh 20-render cProfile recording
(`/tmp/citry-repeat-round2.prof`) still points to component construction,
attribute/input resolution and ownership capture. Its instrumentation expands
wall time substantially, so it identifies work to investigate rather than
providing production timings.

A generator that replaces its output with serialized text constructs a new
render container. Previously the region search received that new container's
identity and its text identities, even though none could identify a retained
physical occurrence. It consequently searched the complete captured region
tree and found nothing. The selection walk now retains only render/wrapper
identities, and the caller removes its newly created container before searching.
An empty selection returns immediately. A hook retaining a nested render or
region wrapper still follows the existing ancestry search. All ownership rows
are still captured and retired normally.

Across 40 alternating same-process pairs, the large-page median moved from
34.434 ms to 33.983 ms (1.3%). Resetting render IDs between observations produced
byte-identical 1,013,746-byte HTML. These are per-area observations against the
previous optimized renderer, not a refreshed comparison with Django. Raw
observations are in `benchmarks/results/performance-render/selection-shortcut.json`.
The ownership, ownership-manifest and cache-replay test suites passed.

### Selection follow-up and independent review

The independent reviewer checked retained nested renders, both region wrapper
forms, plain/subclass text and cyclic trees. No blocking behavior difference was
found. The reviewer also noticed that the first timing probe compared only its
last baseline/candidate HTML outputs. The strengthened probe compares every
pair; all 40 pairs match. That rerun measured 33.582 ms baseline and 32.982 ms
candidate. The updated raw selection artifact contains this run; the first run
remains available in commit `f56df3d`. Variation between runs is why cumulative
claims require a new alternating comparison.

## Continued iteration: lazy extension configuration experiment

An instrumented large render creates 342 each of Cache, Dependencies, Events
and I18n configs. It reads fields on every Cache and I18n config but no fields
on Dependencies or Events configs. Counts are recorded in
`benchmarks/results/performance-render/config-access-counts.json`. These observations
cover this scenario, not other applications or all access through arbitrary
custom descriptors.

A temporary descriptor prototype deferred Dependencies and Events construction
until attribute access. Forty alternating pairs measured 35.166 ms eager and
34.936 ms lazy, with identical HTML in every pair. The prototype deliberately
omits compatibility guards for user constructors, existing component attributes
and custom attribute access. The saving is too small to justify adopting that
version or claiming the guarded design would win. Production initialization
remains eager. Raw observations and the prototype's unproven production-safety
status are in `benchmarks/results/performance-render/lazy-config-probe.json`.

## Continued iteration: reuse successful attribute work

Spread attributes repeatedly present the same names with changing values. Each
ElementAttrsNode now retains up to 64 successfully checked exact-string keys,
each at most 256 characters. Their validation covers attribute syntax, reserved
translation names and compiler-owned Events names. Cache misses still run the
same validators and raise at the current render site. Keys that fail these three
name checks are never stored.
Keys that are subclasses or longer strings keep their original validation path.
Values still resolve and merge each time, and the later framework/client-props
checks and extension hooks still run.

Class accumulation also repeats identical plain-string contributions. A bounded
512-entry cache shares the final whitespace splitting and deduplication result
for at most eight exact-string contributions of at most 256 characters each.
Keys contain the values, never mutable container identity. Mappings, nested
lists, proxies and string subclasses continue through the existing merge, so
later false mappings can remove previously added names.

Forty alternating pairs for each individual change measured:

| Change | Baseline, ms | Candidate, ms |
|---|---:|---:|
| Successful spread-key validation | 33.307 | 33.067 |
| Final plain-string class merge | 33.424 | 33.120 |

Every pair produced identical HTML. Raw observations are in
`spread-key-validation.json` and `class-merge-cache.json` in the repeat-render
results directory. These are small per-area measurements, not additive claims.
Regression tests cover changing values and invalid/reserved keys after warmup,
stateful string-subclass validation, and mutable class removals after warming a
plain-string merge.

## Second iteration: cumulative comparison

The same five-round fresh-process runner compared `1294c51d` with the retained
runtime changes through `3533fba`, alternating Citry baseline, candidate and
Django. This refresh includes both new optimization areas and the preceding six.
No scenario, opt-in purity setting, output feature or native artifact changed.
The detailed observations and hashes are in
`benchmarks/results/performance-render/round2-comparison.json`.

| Scenario and observation | Baseline Citry, ms | Optimized Citry, ms | Django, ms |
|---|---:|---:|---:|
| Small: second render | 0.2331 | 0.2204 | 0.0417 |
| Small: steady-state median | 0.1238 | 0.1075 | 0.0199 |
| Large: second render | 39.4141 | 34.3256 | 11.3868 |
| Large: steady-state median | 39.9009 | 34.0725 | 11.1680 |

The cumulative large-page reduction in this comparison is 14.6% steady-state
and 12.9% on the second render. Citry remains 3.05 times Django's steady-state
time. First-render medians were 85.565 ms baseline and 77.364 ms candidate.
Output sizes remain 1,013,746 bytes for both Citry variants and 456,422 bytes
for Django. The framework-feature and output-size caveats in the first
comparison still apply. The difference between rounds is not a direct measure
of the two new commits; the interleaved per-area probes isolate those changes.

The profile motivating this iteration is now preserved in
`benchmarks/results/performance-render/round2-profile.json`: the 80 functions with
most instrumented self time, from 20 renders of `26a2392b`. It is a profile of
the starting point, not the final optimized tree.

### Next larger experiment

The next target is a compact ownership journal that combines capture and update
operations. The existing `OwnershipGraph.record_component_invocation()` creates
both invocation and queue rows; `bind_instance()` rewrites those and creates an
initialization edge and logical instance; `settle_component()` rewrites the
queue again. Python consumers outside ownership read immutable snapshots rather
than the mutable row lists. Those consumers include manifest preparation,
JavaScript/CSP validation, cache replay, i18n and Events emission. A prototype
must include their snapshot/export cost, not only append speed.

The falsifiers are concrete: snapshots taken before a later update must remain
unchanged; replay rollback must restore all rows and IDs; saved fills and nested
render replacements must keep exact occurrence identity; validation must inspect
all reached bindings. A compact representation must preserve capture order and
the full retired history exposed by snapshots. The earlier mutable-row probe's
neutral result and the previous native-formatter/body-walk experiments make
another isolated field-allocation rewrite a weak candidate. The next useful
boundary combines related updates and closure work behind numeric handles while
keeping Python callbacks and retained render objects in Python. No native
journal implementation or performance win is claimed yet.

### Second-iteration validation

The fast repository profile passed all 18 phases, including 8,071 Python tests,
5 skips and 1 expected failure. The full profile then passed all 19 phases in
one invocation, including coverage and qualification, in 144.942 seconds.
The complete Chromium suite passed 553 tests. Linux-platform mypy passed all
156 Citry runtime source files. The complete supported-version matrix was not
run. No test expectation or coverage threshold was weakened.

Durable evidence is in the repeat-render results directory:
`round2-fast-validation.txt`, `round2-full-validation.json`,
`round2-browser-validation.txt`, and `round2-mypy-linux.txt`. Independent review
found no blocking runtime issue in either optimization area. Its corrections
to validation-cache wording and test component member order were applied before
the full profile. The branch contains separate commits `f56df3d` (selection)
and `3533fba` (attributes); the final evidence commit also records the review
corrections. Django parity remains an active objective.

## Third iteration: combined native invocation and queue prototype

Starting from `f7d7117b`, a standalone release PyO3 experiment combined
invocation and queue storage. The executable source, pinned Cargo workspace,
interface stub and commands are in `benchmarks/ownership_journal_probe/`.
Production rendering and the production native extension remain unchanged.

The prototype reduces repeated target storage and combines binding with queue
updates. A second version batches retirement state changes after the existing
Python relation closure. Immutable NamedTuple exports are built only when a
Python reader requests them, cached until mutation, and included in complete
render timings. Replay converts the tables to ordinary lists and delegates to
the existing implementation, so native replay speed is unmeasured.

| Experiment | Python median, ms | Candidate median, ms |
|---|---:|---:|
| Combined capture, binding and settlement | 33.410 | 33.475 |
| Add batched retirement | 33.088 | 32.915 |
| Explicit capture signature and snapshot checks | 33.491 | 32.497 |
| Confirmation of the final version | 32.765 | 32.513 |

Each run contains 40 alternating pairs, with matching HTML in every pair.
The apparent 0.994 ms gain in the third row is larger than its median paired
saving of 0.393 ms; the confirmation does not reproduce that large difference.
Four ownership snapshots reached by the full render match exactly between
reference and candidate in the final two runs. Direct lifecycle checks preserve
old snapshots and failed-queue ordering; all 128 ownership, manifest and
cache-replay tests pass. The public production rendering result remains the
second-iteration result above, not one of these experimental timings.

The backend is not adopted. It still exports records for Python relation walks,
keeps invocation metadata as Python references, and uses Python replay. Its
small observed saving does not justify shipping a second storage authority with
those limitations. A broader native design remains unproven; the experiment
does not establish a useful gain from this implementation of paired record
updates. Raw results are
`combined-journal-capture-probe.json`, `combined-journal-bulk-initial.json`,
`combined-journal-explicit-signature.json` and `combined-journal-probe.json` in
the repeat-render results directory.

Independent review checked the prototype, all four reports and the prose. It
corrected one rounding error and narrowed the conclusion to this implementation.
It also found that native retirement order overflow could wrap; the retained
prototype now raises `OverflowError`, with a direct boundary check. That guard
was added after timing. The final focused run still passes 128 tests, recorded
in `combined-journal-validation.txt`; Cargo formatting, Clippy and Python lint
also pass. These checks qualify the experiment, not a production native backend.

## Fourth iteration: keep unchanged empty root frames

Component finalization refreshes an immutable `RenderFrame` after component and
extension hooks have finished. The frame holds the component's identity and
extra attributes to attach to its root HTML elements. Most benchmark components
have no extra root attributes, but finalization still copied the frame.

The finalizer now keeps the existing frame when both marker collections are
empty, the frame is exactly `RenderFrame`, and its old markers are an ordinary
tuple. It still collects current markers after hooks and removes duplicates.
Added or removed markers create a new frame, preserving earlier snapshots.
Custom frame constructors and custom marker containers retain replacement.
Nothing is cached across renders, so identity and hook contributions stay live.

`benchmarks/frame_finalize_probe.py` compares the production function against
the same function with unconditional replacement. It warms both versions and
alternates their order across 60 pairs. The final guarded version measured
33.753 ms reference and 33.362 ms candidate, with a median paired saving of
0.401 ms and 46 favorable pairs. Every pair produced identical HTML. Raw
observations and the function hash are in `frame-finalization-probe.json`.
This small local gain does not establish the cumulative Django comparison.

Independent review found that the first guard could invoke a custom marker
tuple's truthiness. The final guard checks exact types before truthiness.
Seven added cases cover hook marker additions, removals and deduplication,
retained snapshots, custom frame construction, and empty custom tuple/list
containers. The render, hook and serialization-security suites pass 200 tests.

### Fourth-iteration cumulative comparison

The same release native extension and five alternating fresh-process rounds
compare the original `1294c51d` snapshot with the production source committed as
`1db0e1d`. The standalone native journal is inactive. Each process records the
second render separately, then 20 warm samples after six renders.

| Scenario and metric | Original Citry, ms | Current Citry, ms | Django, ms |
|---|---:|---:|---:|
| Large, second render | 39.285 | 34.863 | 11.304 |
| Large, warm median | 39.010 | 33.221 | 11.000 |
| Small, second render | 0.230 | 0.208 | 0.042 |
| Small, warm median | 0.119 | 0.109 | 0.020 |

The cumulative large warm improvement is 14.84%; the second-render improvement
is 11.26%. Citry remains 3.02 times Django's warm time. The scenarios keep their
existing different feature sets and output sizes: 1,013,746 bytes for large
Citry and 456,422 bytes for large Django. These are scenario comparisons, not
equal-output engine throughput measurements. Raw observations, native/scenario
hashes and environment information are in `round4-comparison.json`. Absolute
timings vary between runs; the paired frame probe is the evidence for that
individual change.

### Fourth-iteration validation and next investigation

The full repository profile passed all 19 phases in 117.101 seconds, including
coverage and qualification. The complete Chromium suite passed 553 tests in
43.97 seconds; Linux-platform mypy passed all 156 Citry runtime source files.
The supported-version matrix was not run. Reports are
`round4-full-validation.json`, `round4-browser-validation.txt`, and
`round4-mypy-linux.txt`. Independent review approved the final frame guard,
its seven regression cases, the paired harness and that section's prose.

The next candidate is source-span preparation across renders. The current
`OwnershipGraph._source_site_cache` lasts for one graph, so byte-span conversion
and line/column calculation recur on the next root render. A bounded cache of
source text, position and origin could preserve those immutable facts while
every ownership occurrence still receives fresh IDs and order. Its speed and
memory cost are unmeasured. It must account for changed template text/origin,
invalid UTF-8 boundaries, custom source values, and retention of large source
strings before adoption. Django parity remains the active objective.

## Fifth iteration: repeated preparation experiments

Two exploratory comparisons ran against `8afbea56`, with 60 alternating pairs
each. These were complete large renders, and every pair produced matching HTML.

| Experiment | Reference median, ms | Candidate median, ms | Median paired saving, ms |
|---|---:|---:|---:|
| Share source sites across root renders | 34.449 | 34.055 | 0.185 |
| Reuse hook order and filtered hook lists | 32.808 | 32.697 | 0.220 |

The source experiment reused one unbounded process dictionary. It retained 115
sites referring to 26,085 bytes of distinct source text, and improved 35 of 60
pairs. This confirms repeated preparation exists, but the measured gain is
small and noisy. The prototype does not qualify memory limits, custom values
or cache lifetimes for production. Graph-local source caching remains in use.

The hook experiment prepared three lists once per manager: data hooks with i18n
last, rendered hooks without dormant i18n, and attribute hooks for ordinary
elements. It improved 42 of 60 pairs. This version does not track changes to
hook metadata or derived lists; its small gain does not justify adopting that
additional cache state without a stronger design. Production hook dispatch is
unchanged.

Raw initial observations are `source-site-cache-initial.json` and
`hook-subsets-initial.json`. `benchmarks/repeated_work_probe.py` makes these
comparisons repeatable against the current imported runtime and additionally
checks all ownership snapshots reached by one untimed render per variant.
That snapshot check was not present in the two initial measurements. Both
cache modes are experiments; importing the harness does not enable them or
load the native ownership journal.

A fresh 20-render cProfile capture, `round5-profile.json`, records the production
starting point. It identifies 2,112 generator-context-manager constructions per
render across the framework. Of these, 342 are calls to
`resume_ownership_graph()`, normally requesting the graph that is already active.
Profile times are instrumented and are not whole-render benchmark times.

## Sixth iteration: skip an already-active ownership scope

`_render_one_traced()` now calls the rendering/error helper directly when an
element has no saved graph or its saved graph is already current. These are the
same no-op cases that `resume_ownership_graph()` already implements, so the
common path avoids creating and driving its generator context manager. A
different saved graph still enters that context manager. The helper records
failure while the saved graph remains active, before restoration to the outer
graph. Hooks, component creation and ownership capture still run on every call.

The helper lets the wrapper select the rendering path with one read of the
element's saved graph. The error path keeps its existing live field reads.
Six regression cases cover inherited, current and different saved graphs, each
with success and failure. The ownership, on-render and cache-replay suites pass
136 tests. Independent review found no production blocker.

The `graph-scope` mode in `benchmarks/repeated_work_probe.py` extracts the exact
old wrapper from `8afbea56` and compares it with the current wrapper against the
same remaining runtime. Sixty alternating pairs measured 32.728 ms reference
and 32.534 ms candidate. Median paired saving was 0.169 ms, with 44 favorable
pairs. Every pair's HTML matched, and all four ownership snapshots reached by
the untimed comparison matched. `graph-scope-probe.json` contains the evidence.
These measurements do not include either exploratory cache.

### Sixth-iteration cumulative comparison

Five alternating fresh-process rounds compare the original `1294c51d` snapshot
with the production source committed as `3910d94`. Each process records the
second render and takes 20 warm samples after six renders. Citry uses identical
release native artifacts in both checkouts; the standalone journal is inactive.

| Scenario and metric | Original Citry, ms | Current Citry, ms | Django, ms |
|---|---:|---:|---:|
| Large, second render | 38.959 | 34.047 | 11.163 |
| Large, warm median | 38.646 | 32.642 | 10.948 |
| Small, second render | 0.225 | 0.200 | 0.042 |
| Small, warm median | 0.121 | 0.104 | 0.020 |

The cumulative large warm improvement is 15.53%; the second-render improvement
is 12.61%. Citry takes 2.98 times Django's warm time. Output sizes and scenario
features remain different between the frameworks, as documented above. The
small change since the previous cumulative run includes measurement variation;
the isolated paired saving for the scope change is 0.169 ms. All observations
are in `round6-comparison.json`.

The full repository profile passed all 19 phases, including coverage and
qualification, in 116.391 seconds. Chromium passed 553 tests in 43.72 seconds;
Linux-platform mypy passed all 156 runtime files. The supported-version matrix
was not run. Evidence is in `round6-full-validation.json`,
`round6-browser-validation.txt` and `round6-mypy-linux.txt`.

The next larger ownership experiment should move relation indexes and
retirement selection together with record updates. The combined native journal
left those Python readers materializing immutable records during updates;
keeping them inside a native graph could defer more exports until snapshots
are requested. That benefit remains unproven. It requires a complete audit of
saved fills, selected nested renders, replay rollback, failure ordering and
retained snapshots, including the cost of materializing those snapshots.

## Seventh iteration: native retirement relationships

The standalone ownership journal now has an optional native calculation for
`retire_component_output()`. `src/graph.rs` under the experiment contains a
portable numeric relationship model. Its PyO3 adapter reads invocation fields
without exporting their NamedTuple records, then converts the current instance,
initialization-edge, fill and region tables when retirement is requested.
Python applies the returned changes to those remaining immutable records.
Nothing in this iteration changes the production renderer or native extension.

The implementation preserves historical relationships, the reference's three
LIFO worklist phases, and Python integer-set iteration for queue settlement.
It chooses receivers after instance retirement and reactivates older fills
selected by later captured regions. Native preparation and result application
stay inside the complete-render timer. Replay still materializes the journal
and uses Python; this is not a complete native ownership graph.

### Measurements and decision

All observations use the large scenario against production revision `e712d911`
and the same production native artifact. The native candidate also loads the
standalone release journal. Each run alternates reference/candidate order for
60 pairs. The initial and first confirmation runs preceded the numeric-subclass
guard correction; only the final runs qualify the corrected implementation.

| Run | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Initial, production reference | 32.027 | 31.613 | 0.311 | 49/60 |
| First confirmation, production reference | 32.550 | 32.381 | 0.339 | 47/60 |
| Initial, bulk-journal reference | 31.917 | 31.840 | 0.046 | 36/60 |
| Final, production reference | 32.398 | 31.975 | 0.348 | 48/60 |
| Final, bulk-journal reference | 32.085 | 32.179 | 0.053 | 38/60 |

A difference between separate medians is not the median of paired differences.
The final bulk-reference run illustrates that distinction: its candidate median
is higher, while its median paired saving is slightly positive. The incremental
benefit of moving retirement relationships is small and noisy. The total
candidate gain includes the earlier combined journal and cannot be attributed
to native relationship calculation alone.

Both final runs match all four ownership snapshots reached by the untimed
comparison and every timed HTML pair. Each recorded 61 successful native
retirement calls and no unsupported-input fallbacks. This default scenario has
no artifact replay. Evidence is in `native-retirement-*.json`; the final reports
include source and standalone artifact hashes. Earlier files remain exploratory
evidence, not qualification of the corrected guard.

Do not adopt this partial native migration. The extra layer adds conversion,
index construction and Python record updates while delivering only about
0.05 ms incremental paired saving over the earlier journal. A full native graph
could avoid more of those costs, but these results do not establish its benefit.
The next investigation should revisit component setup, template execution and
child/attribute preparation, where the existing profile shows more total work.
Production remains at the sixth-iteration cumulative measurement: 32.642 ms
large warm median versus Django's 10.948 ms, or 2.98 times its time.

### Correctness and limitations

Independent review found that converting a custom integer region ID to `u64`
could change set membership. The native path now rejects non-exact `int` IDs and
orders, alongside non-exact `str` relationship IDs, before mutation. Sixteen
regression cases cover the numeric row fields, supplied region IDs, current and
cutoff orders, and custom strings. Each verifies rejection before mutation and
snapshot equality through the Python fallback.

The corrected implementation passes 134 existing ownership, manifest and
cache-replay tests. Differential checks compare 10,000 synthetic relationship
graphs, three sequential retirements each, under hash seeds 0, 1 and 42: 90,000
comparisons. They compare every snapshot field, retained earlier snapshots,
queue order, receiver lookup and rebuilt receiver indexes. These fixtures
exercise relationships and historical states; they are not complete validated
renderer lifecycles. Raw results are in `native-retirement-validation.txt` and
`native-retirement-random-hash{0,1,42}.txt`.

Cargo formatting, Clippy and the experiment's Ruff checks pass. Independent
review approved the numeric guard correction and ordinary-record semantics.
The prior full production gate, browser and Linux mypy results remain applicable
because production code is unchanged. The supported-version matrix and native
replay implementation are still unqualified.

The standalone prototype also retains its documented 64-bit order bound and
non-atomic mutation errors. It assumes consistent table/index relationships;
custom immutable-record mutation callbacks and arbitrary malformed graphs are
outside its tested contract. These restrictions prevent treating successful
benchmark comparisons as approval for production deployment.

## Eighth iteration: compile component transaction functions

The component construction audit found that render-task records already use
NamedTuple. The earlier body-walker and generated-body prototypes did not deliver large
gains. The unmeasured
option in performance section 10.9 was compiling the transaction functions
while retaining Python objects and callbacks.

`benchmarks/transaction_compile_probe/probe.py` extracts four current functions:
`_render_one`, `Component.__init__`, `ComponentMeta._create_instance`, and
`ComponentNode._resolve_inputs`. Cython 3.3.0 and setuptools 84.0.0 are installed
only in a temporary build-tools directory. The generated native modules live
in a separate temporary directory. Existing annotations do not impose Cython
type restrictions (`annotation_typing=False`, `infer_types=False`); method
binding stays enabled. The plan records the
[compiler directives](https://docs.cython.org/en/latest/src/userguide/source_files_and_compilation.html),
reproduction commands and qualified behavior.

| Candidate | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| All four, initial | 31.947 | 31.376 | 0.487 | 49/60 |
| Construction | 32.140 | 31.998 | 0.091 | 45/60 |
| Render one component | 32.246 | 32.176 | 0.170 | 44/60 |
| Input resolution | 32.776 | 32.537 | 0.049 | 35/60 |
| All four, confirmation | 33.003 | 32.476 | 0.521 | 46/60 |

Each run uses 60 alternating pairs on production revision `c8da9e03`. All four
ownership snapshots and every pair's HTML match. The confirmation explicitly
counts 342 native calls each for rendering, initialization and construction,
and 339 for input resolution. It checks the loaded extension's directory and
original-source, generated-source and built-artifact hashes. Build/import work
and namespace refresh occur outside timing; compiled dispatch and the original
Python object/callback work remain inside. Reports are
`transaction-compiled-*.json`, including compiler output and build/runtime
Python versions. The earlier runs predate the stronger loading checks.

The combined 0.49-0.52 ms paired saving is repeatable in these two runs, but
insufficient to justify another shipped native build system. Keep this candidate
experimental. The result does not disprove full-module compilation or a more
compact native transaction design; it shows that compiling these existing
functions preserves most of their object and callback cost.

Each case must run in a fresh Python process: reusing an already imported native
module after rebuilding its file is outside the loader contract. The experiment
refreshes imported globals between renders, not during one.
Renamed compiled functions also have different introspection and traceback
metadata. Snapshot and HTML equality do not qualify those differences or the
complete callback/error surface. The supported-version matrix, PyPy, `abi3` and
browser-wheel paths were not tested. Production source and dependencies remain
unchanged, so the sixth-iteration cumulative benchmark and full validation are
still the latest production evidence.

## Ninth iteration: direct component-input constness checks

`_kwarg_is_const()` now uses a direct loop for expression attributes instead
of constructing a generator and calling `all()` for every input. The rule is
unchanged: static attributes are constant, expressions with no variable reads
are constant, and an expression with variables is constant only if each live
value has the marker. Variable lookups retain their order and stop at the first
nonconstant value. No constantness result or application value is cached.

The comparison mode in `benchmarks/repeated_work_probe.py` loads the exact helper
from `c8da9e03` and compares it against the current function with the same other
runtime code. Its restoration now puts back the exact imported functions for
all modes. Runs of 60 alternating pairs measured:

| Run | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Initial probe | 32.406 | 32.355 | 0.132 | 40/60 |
| First production comparison | 32.486 | 32.387 | 0.132 | 42/60 |
| Before error compatibility correction | 32.964 | 32.765 | 0.206 | 44/60 |
| With error compatibility correction | 33.223 | 33.098 | 0.175 | 47/60 |
| Final source and prose | 34.279 | 34.121 | 0.180 | 46/60 |

Independent review found one compatibility detail: a generator translates
`StopIteration` raised by variable lookup or marker classification into
`RuntimeError`. The direct loop now preserves that message and exception cause.
The catch covers only the loop body, so a failure while obtaining the variable
iterator still propagates unchanged. Three regression cases exercise lookup,
classification and iterator-construction failures.

Every run matched all four captured ownership snapshots and every timed HTML
pair. `input-constness-qualified.json` records the final node-module and harness
hashes. The constness, component-node and general-node suites pass 138 tests.
Other paired observations are in `input-constness-{initial,final,confirmation,corrected}.json`;
focused validation is in `input-constness-validation.txt`. The earlier full gate
in `input-constness-before-error-correction-validation.json` predates the error
correction and does not qualify the final implementation.

Keep this small Python refactor. Its observed saving is modest, but it removes
an allocation without adding cached state, another representation or a native
build requirement. The standalone compilation and ownership-journal experiments
remain disabled in production.

The final full repository profile passed all 19 phases in 110.739 seconds,
including coverage and qualification. Chromium passed 553 tests in 43.39 seconds;
Linux-platform mypy passed all 156 runtime files. Final evidence is in
`round9-full-validation.json`, `round9-browser-validation.txt` and
`round9-mypy-linux.txt`. The supported-version matrix was not run.

### Ninth-iteration cumulative comparison

Five alternating fresh-process rounds compare baseline `1294c51d` with
production commit `4f529c6`. Each process records the second render, then takes
20 warm samples after six renders. Both Citry checkouts use the same release
native artifact; neither standalone native experiment is active.

| Scenario and metric | Original Citry, ms | Current Citry, ms | Django, ms |
|---|---:|---:|---:|
| Large, second render | 40.372 | 34.385 | 11.595 |
| Large, warm median | 40.251 | 33.918 | 11.121 |
| Small, second render | 0.233 | 0.205 | 0.042 |
| Small, warm median | 0.128 | 0.108 | 0.021 |

The cumulative large warm reduction is 15.73%. Citry takes 3.05 times Django's
warm time in this run. Both Citry medians are higher than in round six, so the
new change's contribution is assessed through its isolated 0.180 ms paired
saving. Output sizes and scenario features still differ between frameworks.
All samples and scenario/native hashes are preserved in `round9-comparison.json`.

The measured dispatch changes produced small gains while retaining the current
objects.
The next larger investigation should measure opportunities to combine the
built-in operations across node boundaries, reducing intermediate state and
helper calls while retaining fresh component instances and user hooks. The
earlier body-walker and native-journal experiments remain the prior art for
that work; repeating those boundaries alone is unlikely to close the gap.

## Tenth iteration: combine simple-name expression evaluation

The ordinary evaluator compiles an expression once, but each call still passes
through an error wrapper, a generated lambda and decorated operation helpers.
An untimed diagnostic on `26312d08` counted 1,904 complete bare-name expressions
among 2,541 evaluations per large render. The narrower candidate subset, exact
ASCII identifier strings without surrounding syntax, ran 1,840 times per render
across 339 cached node evaluators.

The proposed helper combines the normal single-positional-argument call, live
`is_safe_variable()` check and mapping lookup. It retains the ordinary generated
evaluator for keyword calls and invalid arguments. Extra variable validators,
substituted interceptors and other expression shapes stay on the general path.
Both operation and expression error formatting remain. Values and policy
results are never cached.

Independent review found that the original source string is not necessarily
the same object as the generated lambda's name constant. A mapping or policy
callback can distinguish them by identity. The corrected helper reads the
actual key and token objects from the compiled function and reuses them.
An unfamiliar compiler constant layout falls back to the ordinary evaluator.
Regression cases compare positional calls with the same evaluator's keyword
fallback, including source offsets beyond the small-integer cache.

The plan required two runs saving at least 0.15 ms by the median paired
difference, with at least 40 of 60 pairs improving in each run. Measurements:

| Candidate stage | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Initial prototype using module attribute lookups | 32.076 | 31.960 | 0.163 | 39/60 |
| Prototype using runtime globals | 32.290 | 31.898 | 0.195 | 43/60 |
| Runtime-globals confirmation | 32.591 | 32.293 | 0.222 | 44/60 |
| Production-shaped helper before identity correction | 32.142 | 31.787 | 0.235 | 48/60 |
| Identity guard left helper inactive | 32.593 | 32.067 | 0.128 | 43/60 |
| Inactive helper, confirmation | 32.609 | 32.881 | -0.050 | 26/60 |
| Active corrected helper | 31.869 | 31.716 | 0.198 | 43/60 |
| Active corrected helper, confirmation | 32.444 | 32.229 | 0.274 | 42/60 |

Every run matched all four captured ownership snapshots and every timed HTML
pair, with 1,013,746 output bytes. The first identity-preserving version assumed
a constant layout that did not match Python 3.14.3, so its guard left the helper
inactive. The two inactive rows compare ordinary evaluators and cannot support
an adoption or rejection decision. The reproduction guard caught this, as did
independent review. The corrected implementation locates the unique key and
token constants by type and value, without assuming their order. The tests and
benchmark now assert that the intended shortcut is active.

The final two active runs meet the stated adoption rule. Keep the small
optimization, while recognizing that it saves only about 0.2 ms on this
workload. The helper retains one fallback callable and its closure per eligible
compiled expression. Those objects follow the existing node lifetime. The
constant scan and allocation run at compilation, outside the repeated-render
measurements. These results establish neither a first-render speedup nor a
memory reduction. No native code, compiler output contract or shipped
dependency changed.

The 300 focused evaluator tests pass with the active-helper checks. They cover
live mappings and policies, one lookup per call, missing and private names,
`StopIteration`, unprocessed and already processed errors, formatter failures,
keyword and invalid calls, extra validators, substituted interceptors and
spellings outside the shortcut. Other interpreter versions and arbitrary
code-object/closure mutations remain unqualified. The plan and reproduction
instructions are in `benchmarks/name_eval_probe/plan.md`.

Raw exploratory reports are `name-eval-{initial,globals,confirmation,production}.json`.
The misleadingly named first qualification files were renamed to
`name-eval-inactive.json` and `name-eval-inactive-confirmation.json`; their contents
are preserved. The valid active-helper comparisons are `name-eval-active.json`
and `name-eval-active-confirmation.json`. Each report records source and harness
hashes. `name-eval-focused-validation.txt` records the final focused test result.

The full repository profile passed all 19 phases in 114.188 seconds, including
coverage, qualification, native checks, JavaScript and typing. Its report is
`round10-full-validation.json`.
Chromium passed 553 tests in 43.63 seconds. Linux-platform mypy passed all
168 files across the Citry and Citry Core runtimes. Reports are
`round10-browser-validation.txt` and `round10-mypy-linux.txt`.
The supported-version matrix was not run.

### Tenth-iteration cumulative comparison

Five alternating fresh-process rounds compare baseline `1294c51d` with
production commit `1a57a09`. Each process records the second render and takes
20 warm samples after six renders. Both Citry checkouts use the same release
native artifact. No standalone native experiment is active.

| Scenario and metric | Original Citry, ms | Current Citry, ms | Django, ms |
|---|---:|---:|---:|
| Large, second render | 41.460 | 34.475 | 11.448 |
| Large, warm median | 40.549 | 34.296 | 11.310 |
| Small, second render | 0.236 | 0.210 | 0.043 |
| Small, warm median | 0.124 | 0.111 | 0.021 |

The current large warm time remains about three times Django's. Its cumulative
reduction from the original Citry baseline is about 15.4%. The new expression
change's small contribution is established by the isolated active-helper pairs;
differences between cumulative runs also reflect measurement variation. Citry
emits 1,013,746 bytes and Django 456,422 bytes in their respective large
scenarios, so these are framework benchmark comparisons with different output
and features. All samples and scenario/native hashes are retained in
`round10-comparison.json`.

## Eleventh iteration: current composition and representation experiments

The refreshed diagnostic at production revision `7c0a2cb5` uses the original
operation boundaries and nested-time subtraction. It measures 30 ordinary
renders and ten instrumented tree builds after six warmups. All final HTML
matches with deterministic IDs. The reproducible script is
`benchmarks/render_breakdown.py`; samples, operation counts and artifact hashes
are in `round11-breakdown.json`.

| Work | Instrumented ms/render | Share of instrumented tree |
|---|---:|---:|
| Component setup and orchestration | 8.59 | 25.3% |
| Ownership tracking | 7.95 | 23.4% |
| Child inputs and slots | 4.89 | 14.4% |
| Element attributes | 3.95 | 11.6% |
| Body traversal, expressions and control flow | 2.95 | 8.7% |
| Extension hooks and configuration allocation | 2.49 | 7.3% |
| Template and reusable-body cache work | 1.19 | 3.5% |
| Nested serialization | 1.06 | 3.1% |
| Application data callbacks | 0.90 | 2.7% |

The denominator is 33.9732 ms of instrumented tree work. Ordinary medians in
this run are 29.0928 ms for the tree, 3.3598 ms for final root serialization,
and 32.4539 ms overall, including root construction. Final root serialization
is outside the percentage table; serialization performed inside component
hooks is inside it. Timers change execution cost. These are diagnostic
operation buckets, not exact uninstrumented times or removable overhead.
Unwrapped work stays in its enclosing bucket, and residual outer tree time
is assigned to orchestration, matching the original diagnostic.

Ownership's assigned time fell from the historical 10.30 ms to 7.95 ms;
attributes fell from 5.95 ms to 3.95 ms. Historical and current diagnostic
runs were not paired, so use the controlled comparisons above for adoption
and cumulative claims. This run's 32.45 ms overall also does not supersede
the fresh-process cumulative comparison's 34.30 ms or imply a new gain.
No production code changed between those two measurements.

### Assessing the proposed directions

The shared [ChatGPT discussion](https://chatgpt.com/share/6aa06f46-2524-83eb-84a8-08d280d94087)
was read, including its proposal to keep symbolic child references until the
final HTML join. The current serializer confirms its concrete premise:
`serialize_render_result()` stores `finished[key] = "".join(parts)` for each
frame. An ancestor can copy text already joined in its descendants. The
conversation supplies hypotheses, not measured Citry speedups.

**Retirement represented by structural edits.** This could help if one render
attempt owned a region of records and retirement changed an attempt's state
once. The current relations are more complicated than one physical subtree:
logical parents, lexical sources, invocation targets, slot receivers and
physical placements can differ. Preserved descendants can escape the replaced
subtree, and later regions can keep fills alive. A promising representation
would combine attempt identifiers, adjacency indexes and explicit exceptions,
then materialize public record states when read. It must cover resurrection,
failed queues and snapshots taken between updates. That is a candidate design,
not a proof that all current retirement searches can disappear.

A preliminary untimed check counted calls to the immutable-row update helpers
in one warm render. None returned a row equal to its prior value. A trivial
"skip unchanged state" check therefore adds work on this fixture. Another
candidate, `resolve_slot_region()`, scans captured regions, but is called zero
times in the default fixture: its caller needs an `on_slot_rendered` hook.
Optimizing that scan would not improve this comparison. These were ephemeral
diagnostics, not retained timing evidence.

**Alternative tree representations.** A contiguous traversal tape, compact
integer columns or an arena with adjacency offsets fit the actual sparse
relationships better than a dense 2D or 3D lattice. Geometry alone adds no
useful invariant here. Depth-first entry/exit intervals make ancestry queries
cheap while a tree stays fixed; reparenting, cross-links and subsequent
updates require maintenance or another relation. A settled-tree tape is more
plausible than forcing every intermediate ownership relation into one order.
Python packing into bytes also introduces packing, decoding and offset work.
A native arena becomes attractive when its consumers use it directly and
public Python rows are produced only when required.

**Known kwargs and slots.** Exact counts alone do not prove that names are
valid. Known names can allow a node or exact component class to prepare the
binding layout, normalized keys and some schema checks once. Known empty
inputs can skip scans. Values, validators, default factories and hooks must
still run; exposed mutable dictionaries must retain their ownership rules.
The current common component-input path already applies to 324 of 339 calls
in the measured large fixture. `_finalize_inputs()` also rechecks slots after
extensions may mutate them and constructs typed `Kwargs` and `Slots` objects.
Any specialization must distinguish facts established before those hooks
from facts that remain valid afterward. This makes fixed names more useful
than counts alone, but leaves less unclaimed work than a generic-path profile
might suggest.

**Generated node/component methods.** Preparing a specialized function for
an immutable node plan or an exact class could remove repeated dispatch and
checks. Overwriting a shared method based on the first instance would make
subclasses, custom constructors and later input shapes unsafe. Use explicit
eligibility and a fallback. Vue's compiler similarly retains static facts and
marks dynamic work; that is a useful design precedent, not a Citry performance
prediction. See [Vue's rendering mechanism](https://vuejs.org/guide/extras/rendering-mechanism).
Earlier Citry body unrolling and compiled Python transaction probes retained
many Python object operations, so specialization should remove an entire
repeated operation rather than just move its call site.

**Reuse the preceding render.** Reuse template plans and guarded topology,
while refreshing occurrence IDs, values and effects. The same source node can
have different owners when branches, loop lengths, component targets, fills
or hook-selected output change. Reusing its previous ownership record without
those guards is unsafe. The validation and replay cost belongs in the timed
candidate; previous body replay experiments show that reuse is not free.
A static plan may also be simpler to manage than keeping the entire preceding
request's mutable graph alive.

**Omit ownership for plain HTML or components without JavaScript.** Neither
property alone proves that ownership is unused. A text-only slot still has a
lexical supplier and physical placement; empty output can still affect
selection and lifecycle, and surrounding components can depend on provenance.
A safe omission would need a transitive effect summary covering descendants,
slots, extensions, selection, replay and security consumers. Establishing a
restricted no-effect subtree may be worthwhile; disabling ownership whenever
`js` is empty is not a qualified optimization.

**Browser-triggered lazy rendering.** This can reduce initial work when the
product permits incomplete initial HTML. Livewire provides viewport-triggered
lazy rendering and post-load deferred rendering, serializes inputs for the
later request, and can bundle requests. See [Livewire lazy loading](https://livewire.laravel.com/docs/4.x/lazy).
Citry's existing server deferred-render queue does not implement that browser
contract. A `<c-lazy>` proposal needs explicit inputs or a way to reconstruct
the captured context; arbitrary Python closures cannot simply be sent as JSON.
Named groups would need one in-flight load, defined group membership, retries,
and clear behavior when a member appears after the group has loaded. Each
later request needs authorization, ownership and dependency handling. This is
a separate feature and latency strategy; it does not establish parity for
rendering the same complete page. No syntax or browser behavior is added here.

**What rejected native experiments have in common.** Several accelerated an
isolated calculation while retaining Python iteration, conversions, temporary
objects or a parallel representation. The native attribute formatter was
faster in isolation but did not improve complete rendering. The retirement
probe added only about 0.053 ms over its invocation/queue journal: other rows
were converted at retirement and updates were applied back in Python. A
larger native owner would need to retain capture, binding, relationships and
retirement together, then export rows only when a consumer needs them.
Python callbacks still require their existing order and effects. The earlier
Rust body engine also failed to beat Python decisively, so a larger Rust
implementation is not automatically a win. [PyO3's performance guidance](https://pyo3.rs/v0.27.1/performance.html)
also identifies avoidable conversion and attachment work; those savings must
be measured at Citry's full-render boundary.

The next bounded experiment tests symbolic serializer assembly. It changes
one internal representation without changing ownership rules or the native
boundary. Its plan and harness live in
`benchmarks/serialization_assembly_probe/`.

### Symbolic assembly result

The candidate keeps references to previously built child chunks, then flattens
once before hooks. It preserves the original bottom-up lookup rule, including
unresolved, forward and self-referencing authored placeholders.

| Measurement | Reference | Candidate |
|---|---:|---:|
| Complete large render median, ms | 31.414 | 31.441 |
| Synthetic 400-level chain with 100,000-character leaf: assembly only, ms | 1.195 | 0.154 |

The full-render median paired saving was only 0.023 ms, with 36 of 60 pairs
improving. This fails the predeclared threshold of at least 0.15 ms and 40
favorable pairs in each of two runs. Stop after this first inconclusive run;
the synthetic win alone does not justify adopting it. All four ownership
snapshots, all timed HTML pairs and five synthetic assembly cases matched.
No runtime source changed.

Across six serialization calls, the real fixture contains 325 frames. Their
root outputs total 327,312 characters before hooks; frames with
placeholders produce 2,090,273 joined-output characters. Those are character
lengths, not measured allocation traffic. The final root is 179,631 characters
before whole-page hooks, which helps explain why copying during this assembly
stage is less costly than the final 1,013,746-byte output might suggest.
The prototype adds Python list traversal to avoid C string joins. Its net
benefit is unproven on the default scenario, despite the repeated text assembly.
Raw samples and hashes are in `assembly-symbolic.json`; the bounded plan and
reproduction command are in `benchmarks/serialization_assembly_probe/plan.md`.

Both new diagnostic scripts pass Ruff checks and formatting. Independent
review checked timer boundaries, arithmetic, candidate activation, placeholder
semantics and the research prose. This iteration changes only opt-in diagnostics
and research artifacts. The production files retain the tenth iteration's
full-profile, browser and typing validation; no new production validation is
claimed for the rejected serializer prototype.

## Twelfth iteration: native storage beside retirement

The standalone ownership experiment now stores instances, initialization edges,
fills and physical regions beside the invocation/queue journal. Capture writes
field tuples, selected binding operations patch fields, and component-output
retirement updates those native tables directly. It exports immutable public
rows only when a Python consumer asks for them. Source records, receiver maps
and capture orchestration remain Python-owned. Numeric retirement relationships
are still derived on demand; this is not a persistent numeric graph.

The plan, adapter and implementation are in
`benchmarks/ownership_journal_probe/storage_plan.md`, `storage_probe.py` and
`src/storage.rs`. Production source and shipped native bindings are unchanged.

### Measurements and decision

Each comparison uses 60 alternating pairs of complete large renders, with the same
rebuilt standalone module for both sides of the incremental comparison. All
four ownership snapshots and all timed HTML pairs match. Each candidate run
records 67 native retirements, including six warmups, one snapshot-check render
and 60 timed renders; no unsupported-value fallback occurs in this scenario.

| Comparison | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Initial, versus production | 31.959 | 31.591 | 0.306 | 43/60 |
| Initial, versus previous native algorithm with Python tables | 33.953 | 33.749 | 0.264 | 33/60 |
| Final artifact, versus production | 31.739 | 31.357 | 0.250 | 47/60 |
| Final artifact, versus previous native algorithm with Python tables | 31.682 | 31.670 | -0.040 | 25/60 |

The final pair of runs followed a module-comment correction and retain hashes
for the final native source/artifact. The executable algorithm did not change
between these initial and final runs. Their variation does not establish an
incremental storage benefit. Both production comparisons miss the 0.5 ms
threshold; neither incremental comparison meets the complete acceptance rule.
Keep the backend experimental. This does not justify a production migration.
Raw observations are `ownership-storage-{production,incremental}.json` and
`ownership-storage-{production,incremental}-final.json`.

### Why row storage alone still saves little

An untimed factory diagnostic counted 1,423 captured rows across the four new
tables, but 2,916 immutable public-row exports. Of these, 907 are requested by
`_rebuild_relation_indexes`: 340 instances, 338 initialization edges and 229
physical regions. Another 1,275 exports are requested by `snapshot()`.
Fill binding and slot capture account for most of the remaining requests.
Counts identify when a public row is constructed, not when a cached row is
read, and the caller is the nearest Python frame. They do not measure time or
memory. `storage_readers.py` and `ownership-storage-readers.json` retain the
reproduction and counts.

A separate untimed call trace found that `retire_unselected_after()` requests
ancestry for one selected render ID while indexes are dirty. That triggers
Python index construction before native component-output retirement. The new
storage therefore recreates many intermediate rows to serve a remaining
Python consumer. The next experiment should move this ancestry consumer beside
the stored fields as well. Removing its demand for Python indexes is a more
specific hypothesis than adding another cache or merely packing the same rows.
The trace itself was ephemeral; the retained reader diagnostic establishes the
export counts that motivated it.

### Correctness and limits

Review found that both new tables and the earlier Journal could retain cycles
through user field values. Both now participate in Python GC, including cached
public rows. A second finding was replay inside a running slot callback:
replay materializes tables, so a subsequent native patch must check the current
table type again. Success and error cases now preserve output, snapshots and
the original exception object. Custom slot-name subclasses fall back before
retirement mutation because their hash callbacks could observe intermediate
receiver-map updates. These changes affect the standalone experiment only.

The storage candidate passes 134 ownership/manifest/replay tests, 3,000
sequential randomized retirement comparisons and 17 custom-value fallback
cases. The modified earlier mode also passes 3,000 sequential comparisons and
17 fallback cases. Focused checks cover immutable cached records, ordered
lookup, patch validation, four reference cycles and two mid-callback replay
cases. Reports are `ownership-storage-{focused-validation,differential,prior-mode-differential,contracts}.txt`.
Cargo formatting and Clippy, plus the changed experiment's Ruff checks, pass.

Native iteration exports a snapshot list. Arbitrary mutation during private
container iteration, custom factories/helpers, reentrant destructors and
malformed graphs remain unqualified. The earlier unsigned-64-bit limits and
non-atomic native failures remain. Supported-interpreter and platform matrices
were not run. These results do not establish a complete replacement for Python
lists or production readiness. The production files retain their previously
recorded integration validation.

## Thirteenth iteration: native ancestry lookup

The standalone backend now has an optional ancestry query beside its stored
rows. It builds only the parent relations needed by the query, keeping the
original string objects and Python set insertion order. Historical rows,
selectors, initialization edges and the last non-None logical parent remain
part of the result. The production renderer is unchanged.

`ancestry_plan.md`, `src/ancestry.rs`, and `check_ancestry.py` under
`benchmarks/ownership_journal_probe/` document the design and qualification.
`storage_probe.py --native-ancestors` enables it; `--compare-storage` selects
the preceding stored-row backend as the reference.

| Comparison, 60 alternating pairs each | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Versus stored rows with Python ancestry | 33.009 | 32.241 | 0.699 | 52/60 |
| Same comparison, confirmation | 32.584 | 31.773 | 0.469 | 55/60 |
| Versus production | 32.860 | 32.612 | 0.401 | 38/60 |
| Versus production, confirmation | 32.450 | 32.187 | 0.282 | 39/60 |

The ancestry query meets its incremental threshold in both runs. The complete
backend's production comparisons remain modest and inconsistent in pairwise
wins. Keep it experimental. Different processes and reference implementations
mean the incremental and production savings cannot be added. Every run matches
all four ownership snapshots and all timed HTML pairs, with 1,013,746 output
bytes. Counters confirm 67 native ancestry queries and 67 native retirements,
including warmups and the untimed snapshot render, with no fallback.
Reports are `ownership-ancestry-{incremental,production}.json` and their
`-confirmation.json` counterparts.

The new reader diagnostic counts 2,143 public record exports instead of the
previous 2,916, a reduction of 773. Index-building exports disappear, while
some records are first requested by later snapshots or ordered searches.
The captured-row count remains 1,423. These are untimed construction counts,
not allocation-byte or time measurements. `ownership-ancestry-readers.json`
retains the current diagnostic.

### Qualification and a remaining dependency

The query passes 3,000 randomized ancestry comparisons, checking membership,
iteration order and string identity, plus 17 unsupported-input cases. It also
passes 3,000 sequential retirement comparisons, 17 retirement fallback cases,
and 134 ownership/manifest/replay tests. Reports are
`ownership-ancestry-{contracts,retirement,focused-validation}.txt`.
Cargo formatting, Clippy and the changed experiment's Ruff checks pass.

The guards include exact selector tuples and exact seed sets, plus the string
and integer keys used by Python's unrelated region indexes. Unsupported values
use the original helper. Unique invocation IDs and a consistent invocation
index are required. The previous storage limitations still apply.

The sequential checker caught a dependency in the Python fallback:
`retire_component_output()` assumes ancestry lookup has built Python relation
indexes. Native ancestry deliberately does not build them. When native
retirement rejects an input and enters Python retirement, the adapter now
builds those indexes explicitly. The fallback cases pass after this correction.

### Is the measured lookup needed?

A subsequent untimed trace of the default large production render found one
`retire_unselected_after()` call with checkpoint 3,849 and through-order 3,849.
It preserves one component ID and no physical regions. The selected interval
contains zero invocation, instance, initialization-edge, fill or region rows.
Thus this call requests ancestry for an empty retirement interval. The trace
was ephemeral; the next experiment should retain a reproduction and compare
an early empty-interval return against both production and the native backend.

This changes the next action. A faster ancestry query is useful within the
prototype, but avoiding this particular empty-window query may be simpler.
Production component-output retirement subsequently needs its Python indexes,
so skipping the earlier query need not save the full index-build cost there.
The native backend could avoid that work entirely. Neither saving is yet
established by a complete-render comparison with the empty-window guard.


## Fourteenth iteration: omit empty hook retirement

The production settlement loop now skips `retire_unselected_after()` when
its caller-owned before/after hook capture orders are equal. Selection
discovery and retirement of the old component output remain unchanged. This
adds one branch and no cache. The ownership helper's direct-call behavior is
unchanged. `benchmarks/empty_retirement_plan.md` records the decision criteria.

An untimed default large render reaches one hook-retirement call at orders
3,849 through 3,849. All five record intervals are empty. The candidate omits
that call and preserves all four ownership snapshots and every timed HTML
pair. The harness rejects missing snapshots or an inactive guard. Independent
review confirmed that the generated candidate and production function have
identical ASTs, excluding comments, and that subsequent retirement builds its
own required indexes.

| Comparison, 60 alternating pairs each | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Production, initial | 33.270 | 33.487 | 0.121 | 33/60 |
| Production, initial confirmation | 32.883 | 32.958 | 0.011 | 30/60 |
| Production, final harness | 31.864 | 31.838 | 0.015 | 33/60 |
| Production, final confirmation | 34.049 | 34.195 | -0.048 | 28/60 |
| Native stored rows, initial | 32.335 | 31.610 | 0.670 | 55/60 |
| Native stored rows, final harness | 32.607 | 31.741 | 0.631 | 55/60 |

There is no reliable production speedup. The small guard meets the plan's
no-regression criterion and avoids a provably empty operation. Production
still builds Python relation indexes during subsequent old-output retirement.
The native backend can avoid those Python consumers entirely, explaining its
larger incremental saving. These are separate comparisons; their savings must
not be added. Native storage remains experimental.

Raw reports are `empty-retirement-production{,-confirmation,-final,-final-confirmation}.json`
and `empty-retirement-native{,-final}.json` under the repeat-render results
directory. Initial reports precede the harness's explicit snapshot/activation
assertions and adapter hash; final reports contain them. Native counters cover
both variants: 134 retirements across warmups, snapshot capture and timed
renders, with zero fallback. Native ancestry is disabled in both variants.

The actual production path passes 215 tests across `test_on_render.py`,
`test_render.py`, ownership, manifest and cache replay. Existing cases exercise
nonempty post-yield side effects, discarded replacement output, and a generator
returning the settled result. Ruff check and formatting pass. Independent
technical and separate prose review found no blocker.

The full repository gate passes all 19 phases in 133.844 seconds, including
Rust tests, both Python type checkers, JavaScript checks, ordinary Python tests
and qualification tests. The separate browser suite passes 553 tests in
50.27 seconds. Linux-targeted mypy passes for all 156 Citry package source
files. Reports are `round14-full-validation.json`,
`round14-browser-validation.txt` and `round14-mypy-linux.txt`. The supported
interpreter and platform matrix was not run.


## Fifteenth iteration: reuse final attribute strings

A bounded cache at the final attribute formatter found substantial value
repetition, but did not meet the complete-render adoption threshold.
An untimed default large render reached 535 final maps. Of these, 525 used
exact string keys and simple builtin values, with 130 distinct ordered maps.
The warmed formatter cache reports 525 hits and no misses in one diagnostic
render, retaining 130 of its allowed 256 entries.

The first candidate uses a Python LRU after the original resolution and hook
pipeline. A second candidate moves the cache to `ElementAttrsNode._format`,
so a hit also skips nested-render detection, repeated key validation and
leading-space assembly. The broader candidate uses a FIFO dictionary whose
miss calls the original node method, preserving tag-specific diagnostics and
the result's str/Markup type. Neither candidate is enabled in production.
The design and executable probes are in `benchmarks/attrs_cache_probe/`.

Both admit only bounded exact builtin keys and values. They retain at most
256 entries, with at most 16 attributes and 2,048 total string characters per
key; integer values are limited to 256 bits. Floats, proxies, string subclasses,
protocol objects and structured class/style values use the original path.
Resolution and hooks run for every render. The node cache retains neither
nodes nor contexts and includes the validation mode in its key.

| Comparison, 60 alternating pairs each | Reference median, ms | Candidate median, ms | Median paired saving, ms | Favorable pairs |
|---|---:|---:|---:|---:|
| Formatter LRU, initial | 33.706 | 33.782 | 0.209 | 39/60 |
| Formatter LRU, confirmation | 32.986 | 32.825 | 0.230 | 40/60 |
| Whole node formatting, initial | 35.430 | 34.991 | 0.595 | 41/60 |
| Whole node formatting, confirmation | 32.966 | 32.403 | 0.521 | 44/60 |
| Whole node formatting, final guards | 32.413 | 32.242 | 0.482 | 43/60 |
| Whole node formatting, final confirmation | 43.516 | 41.909 | 0.523 | 37/60 |

The predeclared production proposal threshold is at least 0.25 ms median
paired saving and at least 45 favorable pairs in each of two fresh processes.
The formatter-only cache misses both requirements; the broader cache has a
larger median saving but misses the pairwise requirement in both final runs.
Keep both experimental. The final confirmation has substantially slower
absolute timings than the earlier process. A post-run process inspection
showed four active Python test workers in the original checkout; their elapsed
times overlapped the comparison. That confirmation is confounded by external
load and does not establish a new production render time. A renewed adoption
proposal would need controlled timing as well as the remaining qualification.
The two implementations cover overlapping work and
their savings must not be added. These figures are experimental comparisons,
not an additional cumulative production improvement.

The broader cache reaches 495 warm hits, no misses and 126 retained entries in
its diagnostic render. It leaves public formatting calls outside nodes alone.
Every timing run preserves all four ownership snapshots and every HTML pair.
Initial formatter-only timings reset IDs to the same start on each render.
Node comparisons use a distinct deterministic start per pair, shared within
that pair, to prevent artificial cross-render reuse of generated IDs.

Review found an unguarded direct formatter alias. The final node candidate
checks both the attrs and node aliases, accepts only exact ElementAttrsNode
objects, and requires an already-resolved exact-string tag name when validating
keys. The previous node reports precede these guards; all reports retain their
harness hashes. Helpers that were replaced before candidate construction, and
changes inside otherwise unchanged helper functions, remain unqualified. The
identity guards detect the covered later replacements; they do not establish
that an arbitrary initial helper is deterministic.

The revised node candidate passes 197 attribute, template-attribute and
ownership tests. A standalone differential checker compares 3,000 randomized
inputs twice, exercises warm hits and diagnostics, preserves repeated custom
HTML and tag callbacks, checks a post-warm formatter replacement, rejects
three oversized inputs from caching and retains exactly 256 entries after
1,000 distinct inserts. These are representative checks, not a full supported
interpreter or mutation matrix. Ruff check and formatting pass. Reports are
`attrs-cache-node-validation.txt` and `attrs-cache-node-contracts.json`;
timing reports are `attrs-cache-{initial,confirmation}.json` and
`attrs-cache-node-{initial,confirmation,final,final-confirmation}.json` in the repeat-render
results directory. The production files retain round14 integration validation.


## Sixteenth iteration: interpret the cache timing distribution

The 45-of-60 threshold in the previous iteration was a conservative screening
rule chosen before that experiment, not a statistical significance test. The
user's question prompted a closer look at what a per-render win measures when
both variants share one Python heap. All four earlier node comparisons had
positive median differences in both execution orders, despite missing the
win-count threshold. The slower last run was additionally confounded by other
test workers. The earlier rule and results remain recorded; they do not prove
that the cache has no benefit.

### GC and execution-order diagnostics

The harness now offers `--diagnostic --order balanced-random`, retaining
wall time, process CPU time and GC events per render. A fixed seed shuffles
30 reference-first and 30 candidate-first pairs. GC remains enabled and its
cost, including observer overhead, remains inside the render timer. Matched
IDs advance across pairs. Neither the candidate nor production changed.

| Diagnostic, 60 pairs each | Median paired wall saving, ms | Mean paired wall saving, ms | Favorable pairs |
|---|---:|---:|---:|
| Seed 20260909 | 0.488 | 0.418 | 45/60 |
| Seed 20260910 | 0.566 | 0.671 | 51/60 |

In the first run, 12 of 15 losing pairs charged the candidate at least 0.25 ms
more GC time; in the second, 8 of 9 did. Correlations between paired wall-time
and paired GC-time differences are 0.985 and 0.983. These associations explain
why collection scheduling deserves attention. They do not identify which
variant originally allocated the reclaimed objects. A collection in one
render can reclaim earlier renders from either implementation. The observer
and retained diagnostic records also affect collection timing.

Both diagnostics preserve all four ownership snapshots and every HTML pair.
Their reports are `attrs-cache-node-timing-diagnostic.json` and
`attrs-cache-node-timing-diagnostic-confirmation.json`. No GC-excluded subset
is used as an adoption result.

### Separate process lifetimes

`benchmarks/attrs_cache_probe/process_probe.py` gives each variant its own
fresh process, six warmups and 80 complete measured renders. Normal GC stays
enabled, with no observer. The worker records wall and CPU time, but uses the
mean of all 80 renders as its throughput measure, including collected renders.
Eight process pairs run in balanced randomized order. Within each pair, both
workers use the same Python hash seed and ID base; IDs advance across samples.
Every sample's HTML digest matches across the paired workers, and their native
artifact hashes match. Candidate counters confirm cache use.

The predeclared follow-up rule requires positive mean wall and CPU savings in
at least seven of the same eight process pairs, plus at least 0.25 ms median
process-pair mean wall saving. The candidate meets it: seven pairs are jointly
positive, with median wall and CPU savings of 0.688 and 0.689 ms/render.
The remaining pair favors the reference by 0.003 ms on both measures. All
pairs are retained. The evidence is in `attrs-cache-node-processes.json`.

This is stronger support for proceeding with production qualification. It
also shows why a per-render win count from a shared heap should not alone
settle a small optimization. The cache is still experimental: preinstalled or
internally modified helpers, cache lifetime and invalidation, and supported
runtime behavior need a production design and qualification. The result is
not an additional cumulative production speedup and cannot be added to the
previous overlapping cache comparisons.

`timing_plan.md` records both stages before their measurements. Independent
technical and separate prose review found no blocking measurement defect.
Review clarified that the process rule counts joint wall-and-CPU wins; the
seven joint wins above are derived from the raw pair records. The runner now
also emits that aggregate directly. That reporting-only addition follows the
retained run, whose original runner hash is preserved. Candidate code and
worker timing behavior did not change. Ruff checks and formatting pass;
production still has the round14 integrated validation.


## Seventeenth iteration: reuse qualified attribute output in production

Across eight process pairs, the median reduction in average render time was
0.551 ms. All eight process pairs favor the production cache on both wall
and CPU time; the median CPU saving is 0.551 ms. Every pair's HTML digests
and loaded native hashes match. This passes the rule written before the
production change: at least seven joint wins and at least 0.25 ms median
process-pair mean wall saving. It remains a workload-specific screening rule,
not a statistical significance claim or a cumulative Django comparison.

The implementation caches the final string returned by
`ElementAttrsNode._format` only when its caller has already validated keys.
An untimed large render reached 505 such calls and no validation-required
calls. Each production timing worker reaches 495 hits, no misses and 126
retained entries in its separate activation render. These counters run after
the 80 timed samples, with ordinary GC enabled throughout the measurement.

The production guards are narrower than the earlier prototype. Original helper
identities are captured in their defining modules, and reuse requires the
known MarkupSafe C escaper. Replacing covered helpers before the first use or
after a hit leaves their calls live. Exact builtin keys and values exclude
user protocols; ordered, typed keys distinguish `True` from `1`. The existing
size limits bound retention. Cacheable misses format a copy made from the
key's immutable values so concurrent input changes cannot poison an entry.
Insertion and eviction share a lock; hits do not take it. The cache stores
no node, context or engine-specific facts. The runtime contract and precise
limits are documented in `template_html_attrs.md` section 5.2.

The process comparison uses the exact pre-change `_format` method from
`5bad7af8` against the actual production method, with shared live dependencies.
Mean wall savings across the eight pairs are 0.286, 0.498, 0.595, 0.508,
0.119, 0.850, 1.088 and 1.487 ms. Absolute times drift upward across the run;
all observations are retained, and both execution-order groups improve.
The report is `attrs-cache-production-processes.json`. A separate two-pair
equivalence check preserves all four ownership snapshots and both HTML pairs;
its sample count is for correctness, not a speed claim.

`production_check.py` compares 3,000 randomized maps twice against the same
pinned method, including output types and exception types/messages. The
focused suites pass 297 tests. New cases cover helper replacements before use
and after hits, an escaper replaced before importing Citry, validation, live
protocols/proxies, input changes, retention, independent engines and engine
clearing, oversized values, and concurrent misses. Eight threads perform 64
distinct misses while the cache starts one entry below its bound. Input
callbacks remain live after an engine clear. Ruff checks and formatting pass;
macOS and Linux-targeted mypy pass for 156 files.

The retained evidence is `attrs-cache-production-{equivalence,contracts}.json`
and `attrs-cache-production-validation.txt` in the repeat-render results
directory. Helper identity checks do not qualify concurrent replacement and
restoration, rewritten code objects or arbitrary changes inside unchanged
helpers. Non-C escaping backends keep the original uncached path. The full
supported interpreter/platform matrix has not been run.

The full repository gate passes all 19 phases in 147.394 seconds, including
coverage and qualification. The browser suite passes 553 tests in 44.23 seconds.
Reports are `round17-full-validation.json`, `round17-browser-validation.txt`
and `round17-linux-mypy.txt`. After the full gate, review prompted a test-only
template formatting/member-order correction; its 19 focused tests, Ruff check
and formatting pass again (`attrs-cache-production-final-tests.txt`). Runtime
source remained unchanged throughout these checks and the production timing.

### Current composition and cumulative comparison

At production revision `59e84ac`, the original diagnostic boundaries give:

| Work | Instrumented ms/render | Share of instrumented tree |
|---|---:|---:|
| Component setup and orchestration | 8.85 | 25.7% |
| Ownership tracking | 8.13 | 23.6% |
| Child inputs and slots | 5.01 | 14.6% |
| Element attributes | 3.64 | 10.6% |
| Body traversal, expressions and control flow | 3.01 | 8.8% |
| Extension hooks and configuration allocation | 2.54 | 7.4% |
| Template and reusable-body cache work | 1.25 | 3.6% |
| Nested serialization | 1.07 | 3.1% |
| Application data callbacks | 0.91 | 2.6% |

The denominator is 34.4153 ms of instrumented tree construction. Thirty
ordinary samples give medians of 29.5002 ms for the tree, 3.3956 ms for final
root serialization and 32.8856 ms overall. These are separate medians, so they
need not add. The percentage table excludes final root serialization but
includes serialization inside component hooks. Ten instrumented renders
preserve the same HTML. Instrumentation changes costs; historical diagnostic
differences are not controlled speedup measurements. The evidence, operation
counts and hashes are in `round17-breakdown.json`.

Five alternating fresh-process rounds then compare the original `1294c51d`
baseline, production `59e84ac` and Django. Each process takes 20 warm samples
after six renders. Both Citry checkouts load the same release native artifact;
none of the experimental native implementations is active.

| Scenario and metric | Original Citry, ms | Current Citry, ms | Django, ms |
|---|---:|---:|---:|
| Large, second render | 42.693 | 38.250 | 11.777 |
| Large, warm median | 41.226 | 33.353 | 11.373 |
| Small, second render | 0.241 | 0.217 | 0.046 |
| Small, warm median | 0.128 | 0.109 | 0.021 |

The large warm benchmark is 19.1% faster than the original Citry baseline
and takes 2.93 times Django's time. Parity remains distant. The second-render
statistic has only one observation per worker, five per variant, and is more
sensitive to collection timing than the warm-sample comparison. These
fresh cumulative figures do not attribute the change from the previous run
to the attribute cache alone; its contribution is measured by the direct
process comparison above. Citry emits 1,013,746 bytes and Django 456,422 bytes
in their respective large scenarios. All observations and scenario/native
hashes are retained in `round17-comparison.json`.


## Eighteenth iteration: separate slot result conversion from capture

`OwnershipGraph.capture_slot_call()` invokes a callback before it wraps the
result. That callback renders the slot body and calls `_render_value()`, which
unwraps Const values, resolves component-like objects, renders elements and
escapes text. The earlier timers subtract instrumented nested body work but
leave uninstrumented result conversion inside the ownership bucket. This
means the bucket is not exclusively time spent creating and updating records.

An optional `--detail-value-conversion` mode in `render_breakdown.py` times
the `_render_value()` aliases used by expressions and Slot calls in this
scenario and subtracts their nested work
using the existing timer stack. It assigns 1.095 ms, or 3.2% of the 33.9203 ms
instrumented tree, to value conversion across expressions and slot callbacks.
All HTML matches. The report is `round18-value-conversion-breakdown.json`.
Ownership is 7.407 ms (21.8%) with the finer boundaries, but the difference
from round17 is not a paired measurement of conversion inside ownership.
The runs have different instrumentation and normal timing variation.

The next candidate is the repeated runtime `ComponentLike` protocol check
inside `_render_value()`. Python 3.14's loaded `_ProtocolMeta.__instancecheck__`
checks class membership and then uses `inspect.getattr_static` to search each
required member on a failed class check. Even ordinary text and already-built
renders take that path before the existing renderer recognizes them. A
specialization for exact builtin values or exact slotted render types could
avoid some repeated inspection. It must preserve component-like subclasses,
instance-assigned protocol members, explicit protocol registration, dynamic
class changes, Const unwrapping and escaping. This diagnostic does not measure
a production specialization; the 1.095 ms bucket is not a predicted saving.

### Guarded value-conversion experiment

The experiment in `benchmarks/render_value_probe/` skips instance-level
protocol inspection for exact strings and ordinary exact CitryRender objects.
Const unwrapping and Slot dispatch stay live. Each call still checks protocol
class membership so explicit registration takes effect. The render branch
also checks its object base and rejects class-defined protocol members,
custom attribute access and class overrides. Subclasses and Markup retain the
original conversion path. No arbitrary class-negative cache is introduced.

The initial eight-process-pair comparison has eight joint wall/CPU wins and
a median reduction in mean wall time of 1.048 ms. Review found missing guards
for rebound structural type aliases, a render-class `__getattr__` on older
Python versions, and aliases replaced before candidate creation. The revised
candidate captures its trusted types once, checks all four live dispatch
aliases, rejects `__getattr__`, and refuses a vacuous empty snapshot check.
These changes require new measurements; the initial result cannot qualify
the revised candidate.

The revised eight process pairs all improve on both wall and CPU time. The
median reduction in process mean wall time is 0.800 ms; CPU time is also
0.800 ms. All four reached ownership snapshots and every paired HTML digest
match. Both variants use ordinary GC, 80 timed renders after six warmups,
the same per-pair hash seed and advancing IDs, and the same native artifact.
An untimed activation render in each candidate worker reaches 274 render
shortcuts and 88 string shortcuts. The earlier exploratory count covered only
the expression/Slot aliases; this experiment also installs the candidate at
i18n's imported alias. The predeclared screen requires seven
joint wins and at least 0.25 ms median reduction in process mean wall time;
the revised experiment passes it.

Twenty-three focused contract cases pass, covering output types and escaping,
render identity, Const and Slot callbacks, protocol members on classes and
instances, live helpers, preinstalled and later alias replacements, and
explicit protocol registration in isolated subprocesses. The existing
component-like, slot, rendering, deferred rendering, ownership and i18n suites
pass 249 tests with the candidate installed at all three runtime aliases.

A separate Python-only checker executes the real conversion function source
and the candidate snippet with stand-in Citry types. Its 13 dispatch cases
pass on CPython 3.10.20, 3.11.15, 3.12.13, 3.13.12, 3.14.3, free-threaded
3.14.6 and PyPy 3.11.15. This establishes interpreter-specific protocol
behavior at that boundary, not full native runtime support across the matrix.
Private edits to the protocol implementation or metadata remain unqualified.

Evidence is retained in `render-value-processes.json`,
`render-value-processes-guarded.json`, `render-value-contracts.txt`,
`render-value-validation.txt` and `render-value-protocol-matrix.json`.
Ruff checks and formatting pass. Independent technical and separate prose
review found no remaining blocker in the revised experiment's stated scope.
Production remains unchanged at this point; adoption needs a production
implementation, its direct comparison and integrated validation.

### Production result

The production implementation has eight joint wall/CPU wins against the
pinned pre-change `_render_value` from `49852e7`. Across those process pairs,
the median reduction in average render time is 0.755 ms wall and 0.755 ms CPU.
Every HTML digest matches, all four ownership snapshots match, and candidate
workers reach 274 render shortcuts and 88 string shortcuts in their untimed
activation renders. All 80 timed samples from each worker remain included
with ordinary garbage collection enabled. This is the direct contribution
of this area, not a new cumulative Django comparison.

The branch logic follows the revised prototype. Original ComponentLike and
CitryElement identities are saved where those types are defined; the renderer
combines them with its own original render and physical-region classes. The
guard therefore rejects imported aliases replaced before the render module
loads as well as later replacements. Existing Const, Slot, protocol, element
and escaping paths remain live whenever the shortcut does not apply. The
runtime contract is documented in `component_rendering.md` section 3.1.

Twenty-five package regressions pass. They include replacing an imported
alias before reloading the render module, plus explicit protocol registration
after a successful shortcut has warmed the negative class check. The existing
249 component-like, slot, rendering, deferred, ownership and i18n tests also
pass against production. The seven-interpreter dispatch matrix passes all
13 cases using the actual production function and the pinned old function
with Python-only stand-ins; this does not establish full native-runtime
qualification on each interpreter.

The evidence is `render-value-production-processes.json`,
`render-value-production-contracts.txt`,
`render-value-production-validation.txt` and
`render-value-production-protocol-matrix.json`. Review found that the old
default benchmark mode would insert the prototype into already optimized
production. It now requires a pre-production checkout; current code requires
`--production`. The historical prototype tests skip on an optimized checkout,
where the package regressions exercise the production code instead. Both
mode-rejection checks pass (`render-value-mode-checks.json`).

The mode checks were added after the production timing run. Its exact runner
source is retained in `render-value-production-runner.py.txt`, matching the
hash recorded in the timing report. Those later changes affect only rejected
prototype mode; production worker timing and runtime source are unchanged.

The integrated repository gate passes all 19 phases in 115.663 seconds,
including coverage and qualification. The browser suite passes 553 tests in
42.96 seconds. Repository mypy and the Linux-targeted check pass; the latter
covers 156 files. Reports are
`round18-full-validation.json`, `round18-browser-validation.txt` and
`round18-linux-mypy.txt`. Independent technical and separate prose review
found no remaining production or measurement blocker. The production
function matches the pinned old function's AST after removing the added
type assignment and guarded branches.

### Cumulative timing after production value conversion

Production commit `d1c25cb` was measured against the original `1294c51d`
checkout and Django with five alternating fresh-process rounds per case.
Each process retains 20 warm samples after six warmups, with ordinary garbage
collection. The runner uses the existing scenarios unchanged; the large Citry
scenario explicitly marks HeroIcon and ProjectOutputBadge as pure. All Citry
workers use the same native extension hash, and the baseline and candidate
scenario hashes match for each size.

| Case | Original Citry | Current Citry | Django |
|---|---:|---:|---:|
| Large warm median | 39.2279 ms | 31.6041 ms | 11.1011 ms |
| Large second render | 40.1333 ms | 35.0228 ms | 11.1892 ms |
| Small warm median | 0.1189 ms | 0.1035 ms | 0.0198 ms |
| Small second render | 0.2255 ms | 0.2025 ms | 0.0427 ms |

The large warm result is 19.43% below the original branch and 2.847 times
Django. The small warm result is 12.94% below the original branch. The second
render figures have only five observations per case and are more sensitive
to garbage collection. Timing shifts from round 17 include changes in the
measurement environment; the eight process pairs above isolate this area's
contribution more directly. Citry emits 1,013,746 bytes for the large case,
while Django emits 456,422 bytes. These scenarios exercise different framework
features and output, so the ratio does not compare identical rendering work.
The observations are in `round18-comparison.json`.

Using the original diagnostic boundaries, the instrumented tree takes
33.6242 ms, with this composition:

| Work | Instrumented ms/render | Share of tree |
|---|---:|---:|
| Component setup and orchestration | 8.784 | 26.1% |
| Ownership tracking | 7.684 | 22.9% |
| Child inputs and slots | 4.982 | 14.8% |
| Element attributes | 3.567 | 10.6% |
| Body traversal, expressions and control flow | 2.854 | 8.5% |
| Extension hooks and configuration allocation | 2.548 | 7.6% |
| Template and reusable-body cache work | 1.205 | 3.6% |
| Nested serialization | 1.078 | 3.2% |
| Application data callbacks | 0.924 | 2.7% |

The separate ordinary diagnostic medians are 27.9981 ms for the tree,
3.3282 ms for final root serialization, and 31.4004 ms total. These are
separate medians, so the phase medians need not sum to the total. Instrumented
percentages include timer overhead and cover the tree only; nested
serialization is already within that tree, while final root serialization
is outside it. All diagnostic HTML outputs match. Revision, source hashes,
individual observations and phase counts are in `round18-breakdown.json`.

## Nineteenth iteration: measure a cheaper render-frame representation

`RenderFrame.from_context` is called 1,015 times in one warm large-page
render: 326 calls have a true component-root flag and 689 have a false flag.
The latter includes interior renders and transparent component roots. These
calls reach 416 distinct contexts, 714 distinct context/value
combinations and 644 distinct frame values. The count retains the contexts
until the render finishes so recycled object IDs cannot merge observations.
It covers this factory boundary, not direct constructors or dataclass
replacement. Within those observed calls, a cache per context could avoid at
most 301 duplicate frame constructions at this boundary; it would also need
lookups, checks for changed identity values, and storage.

The frame stores render ID, class ID, class name, the component-root flag and
root markers. These values must describe the context when the render is
created. Ownership readers, serialization and cache replay consume that
snapshot. Deferring the snapshot until someone reads it would change behavior
when a hook later mutates the context or component. The exported dataclass
also supports subclassing, frozen-assignment errors and dataclass operations.

The isolated experiment in `benchmarks/frame_creation_probe` substitutes a
named tuple holding the same five fields while retaining the exact existing
`from_context` body. It switches the four production import aliases together
and provides dataclass field metadata for replacement calls. This deliberately
changes public object behavior, including tuple membership, iteration and
equality. It is a performance probe, not a compatible production replacement.
Any adoption would require a different implementation preserving the public
interface, and that implementation would need its own timings.

Eight balanced randomized process pairs retain 80 complete render samples per
worker after six warmups. Ordinary GC remains enabled. The median reduction
in process mean time is 0.266 ms wall and 0.266 ms CPU, with six of eight pairs
jointly positive. Every paired HTML digest matches, native artifacts match,
and four separately captured ownership snapshots match. An untimed root
render in each worker confirms the selected frame type. The raw wall savings
per pair are 0.786, 0.421, 0.268, 0.159, 0.264, -0.764, -0.013 and 0.897 ms.
Every pair remains in the result.

The result misses the predeclared requirement of seven joint wins, despite
meeting the 0.25 ms median saving requirement. Production remains unchanged.
A compatible representation would require further work, so frame storage is
not the next production project. This does not prove that all frame caching
or representation changes are ineffective, or bound their possible gains.
Component setup and orchestration, plus child inputs and slots, remain the
next areas to inspect.

Evidence is `frame-creation-processes.json`. Its `counts.creations` field
counts only `from_context` calls; review identified that the label could imply
a broader constructor count. The current harness calls that field
`from_context_calls` and states the boundary explicitly. The measured runner
is retained as `frame-creation-runner.py.txt`, matching the report's source
hash. Only that report label and its counting docstring changed afterward;
worker timing and candidate code are unchanged.

Ruff checks and formatting pass. Independent technical and separate prose
review confirmed the retained measurements and the stated experiment limits.
Production source is unchanged, so the previous integration validation still
applies to it; this step does not claim new integration qualification.

## Twentieth iteration: delay fallback-slot initialization

Every executed slot outlet constructs its fallback Slot before invoking the
selected content. The fallback's source occurrence and logical fill row are
recorded even if the fill never reads the fallback. Those records participate
in snapshots and retirement, so skipping them would change ownership history.
The experiment keeps that recording and delays only the Python wrapper's
initialization.

`benchmarks/lazy_fallback_probe/probe.py` creates a Slot subclass with the
same layout, initially storing seven constructor arguments in its `contents`
field. Its first attribute read changes the object's class to ordinary Slot,
then builds the template content callable, scratch dictionary and callable's
weak reference. Subsequent access follows the ordinary Slot implementation.
Named and implicit fills still use the original factory. In each untimed
candidate render, 274 fallback wrappers are created and 80 initialize on an
attribute read. The counter measures initialization, not invocation; metadata
inspection can initialize a fallback without rendering its body.

The eight balanced randomized process pairs retain 80 complete samples per
worker after six warmups, with ordinary GC enabled. Median process-pair mean
wall saving is -0.345 ms, and CPU saving is -0.345 ms: the candidate is slower.
Only two of eight pairs improve both measures. All paired HTML digests match,
all native artifact hashes match, and four separately reached ownership
snapshots match. All candidate workers reach 274 creations and 80
initializations in their untimed activation renders. The raw wall savings
are -0.778, -0.321, 0.032, 0.593, -0.111, -0.369, -0.768 and -0.687 ms.
No pair was removed from the result.

Independent review also identified concrete public incompatibilities before
initialization. Writing `extra` loses the assigned mapping when initialization
later runs. Writing `contents` overwrites the pending arguments and can make
attribute access fail. Deleting an unset field raises before the ordinary
Slot would. Direct descriptor access exposes the pending tuple, and `type()`
sees the private subclass. `contracts.py` records all five counterexamples
against the original factory in `lazy-fallback-counterexamples.json`; those
are observed compatibility failures, not passing production contract tests.
A changed constructor could also fail after the class assignment and leave
a partially initialized ordinary Slot. That failure and wider interpreter,
reentrancy and replay behavior remain unqualified.

Reject this candidate: it regresses complete-render timing and changes public
behavior. Production is unchanged. The experiment shows that avoiding 194
fallback initializations alone does not make this wrapper worthwhile. It does
not establish the cause of the regression or rule out other ways to defer
slot work. The timing report is `lazy-fallback-processes.json`. Its exact
runner is retained in `lazy-fallback-runner.py.txt`; after timing, only a
copied error message was corrected from frame representation to fallback
initialization. The candidate and worker timing code are unchanged.

Ruff checks and formatting pass. Production remains covered by the previous
integration validation; this experiment does not claim new integration
qualification. Independent review checked the implementation, timing and
compatibility limits, with a separate prose pass.

## Twenty-first iteration: bounded reuse of source-site metadata

The earlier unbounded source-site experiment preceded separate-process timing.
A new candidate places a 256-entry `functools.lru_cache` behind the existing
graph-local cache. Only local misses consult it. Eligible keys contain exact
primitive types: source and optional origin strings, plus a two-int byte-span
tuple. Source text is limited to 8,192 characters, origin to 1,024 characters
and offsets to 32 bits. Other inputs use the uncached calculation. This limits
shared retention while leaving the existing graph-local cache unchanged.

Every occurrence still converts its source to text, reads the live template
origin and records its current owner, ID and order. Shared hits avoid only
repeated UTF-8 span validation, line/column calculation and immutable site
construction. The candidate does not share ownership graphs or occurrence
records. In each untimed activation render it reaches 115 shared hits, zero
misses and 115 retained entries.

Eight balanced randomized process pairs retain 80 complete samples per worker
after six warmups, with ordinary GC enabled. The median process-pair mean
saving is -0.076 ms wall and -0.076 ms CPU, with only three joint wins. The raw
wall savings are -0.007, -0.217, 0.546, -0.450, 1.970, -0.213, -0.145 and
0.093 ms. Every pair remains included. Paired HTML digests and native hashes
match, as do all four separately captured ownership snapshots. This result
fails both parts of the predeclared adoption screen; production retains its
graph-local cache.

Independent review confirmed that the calculation matches the original AST
after accounting for its return and constructor reference. The experiment
captures constructor identities at probe import, so a replacement already
installed then would be trusted. It also runs the copied calculation under
probe globals, rather than ownership-module globals. Production adoption
would need defining-module originals and qualification of overrides; cache
locking does not make concurrent constructor replacement atomic. These
limits do not change the measurements against the unmodified fixture. No
broader compatibility or interpreter qualification is claimed for this
rejected candidate.

The plan and harness are in `benchmarks/source_site_probe`; observations and
source hashes are in `source-site-bounded-processes.json`. Ruff checks and
formatting pass. Independent technical and separate prose review found the
measurement valid within its stated scope. Production source is unchanged.

### Check whether pure-body preparation repeats already completed work

A separate untimed probe checked whether constant precomputation had reduced
pure component bodies entirely to strings, leaving pure-body lookup with
nothing to save. The existing large scenario reaches 55 pure-body lookups:

| Component | Body items | Live nodes | Cache hits | Cache misses |
|---|---:|---:|---:|---:|
| HeroIcon | 5 | 2 | 30 | 11 |
| ProjectOutputBadge | 3 | 1 | 10 | 4 |

Every observed body still contains live nodes, so an all-text-body shortcut
would not activate in this workload. HeroIcon's 11 capture calls each retain
two reusable node outputs. ProjectOutputBadge captures one reusable node
output once and none on its other three misses. That last count alone does
not justify a negative-result cache: repeated key construction, context
changes and whether those misses recur still need investigation.

`benchmarks/pure_body_shape_probe.py` records these counts after six warmups
and an ordinary comparison render. Instrumentation leaves the HTML unchanged.
`pure-body-shapes.json` retains the counts, revision and source hashes. This
is an activation diagnostic, not a timing comparison or a claim about the
net benefit of `pure = True`. No runtime behavior changes from this check.

## Twenty-second iteration: direct positions for ownership IDs

Ordinary capture assigns consecutive IDs to invocation, fill and physical
region rows. Queue rows follow invocation creation. The four dictionaries
mapping these IDs to list positions therefore repeat information already
available as `id - 1` on this path. Retirement updates rows in place without
removing them, so retired history does not itself create position gaps.

The isolated candidate in `benchmarks/dense_index_probe` transforms 31 index
read sites into subtraction, removes four index-write sites and replaces
five membership sites with bounds checks. These are source-site counts, not
calls per render. The four empty dictionary allocations remain. Snapshot
import and mutation backup/restore explicitly raise; the candidate does not
claim replay support. The separate instance-only import method remains
callable and does not populate the four indexed tables.

Replay needs separate treatment because fresh IDs are assigned in sorted
local-ID order while rows append in snapshot order. The runtime artifact
producer uses sequential source, invocation, fill and region IDs, but queue
IDs resolve through references. This experiment does not establish a position
invariant for every supported replay input or failed construction path.

Eight balanced randomized fresh-process pairs retain 80 complete renders per
worker after six warmups, with ordinary GC enabled. Median process-pair mean
saving is 0.256 ms wall and 0.257 ms CPU. Five of eight pairs improve both
measures, missing the required seven joint wins. Raw wall savings are -0.197,
0.276, 0.237, 0.303, 1.123, -0.030, 0.539 and -0.090 ms; every pair remains
included. All paired HTML digests and native hashes match. All four ownership
snapshots reached in the untimed comparison match and have consecutive IDs at their observed
positions. Each candidate worker's untimed activation has 339 invocation
rows, 468 fills, 274 regions and 339 queue rows, with all four index maps empty.

The counterexamples in `contracts.py` demonstrate why subtraction alone is
not a production replacement. Retiring ID zero rejects with `KeyError` in
the original graph but silently retires the final invocation in the candidate.
A past-end ID changes `KeyError` to `IndexError`. A float equal to an existing
integer key succeeds in the original dictionary lookup but raises `TypeError`
when used as a list index. These observations are retained in
`dense-index-counterexamples.json`. Missing/custom IDs, constructor failures,
reentrancy, concurrent mutation and replay remain unqualified.

Do not adopt this candidate. It misses the consistency screen and has concrete
behavior differences; a compatible design would require checks or a fallback
representation with its own measured cost. The result does not rule out all
ways to simplify ownership storage. `dense-index-processes.json` retains all
samples, activation counts, transformation counts and source hashes. Ruff
checks and formatting pass. Production source and its previous integrated
validation remain unchanged.

Independent technical review checked the transformations, timing evidence and
executed counterexamples. A separate prose pass checked the plan, this section,
checker comments and delivery wording.

## Twenty-third iteration: repeated generation of provided payload classes

The earlier cycle cleanup already prevents this fixture from leaving render,
component or ownership objects for cyclic collection. A new diagnostic warms
the fixture six times, performs a full collection, disables automatic GC for
one discarded render and then collects with `DEBUG_SAVEALL`. Its 265 retained
unreachable objects include seven `Provided` classes: one with `render_context`
and six with `tabs, enabled`. Walking references from those classes, restricted
to the collected objects, reaches all 265. These counts describe this diagnostic
on Python 3.14.3, not the cost of ordinary automatic collections.

`make_provided` creates a new typed named-tuple class for every keyword-field
provide call. Each class needs generated methods, field descriptors and
annotations, even when its field layout matches the previous call. The first
candidate caches up to 128 classes by ordered field names. Eligibility requires
an exact dict with at most 16 exact string keys of at most 128 characters each.
Each payload still receives its current values. The cache stores classes rather
than payload instances; because classes are mutable, a caller can attach
arbitrary application objects to a cached class. The entry bound therefore
does not bound retained bytes under class mutation.

Eight balanced randomized fresh-process pairs, with six warmups and 80 complete
samples per worker, show a median process-pair mean saving of 0.380 ms wall and
0.381 ms CPU. All eight pairs improve both measures. Wall savings are 0.332,
0.254, 0.495, 0.070, 0.014, 0.429, 0.588 and 0.683 ms. All samples retain
ordinary GC costs. Every candidate activation records seven hits, zero misses
and two cached classes. All four ownership snapshots reached in the untimed
comparison match, as do all paired HTML digests and native hashes.

The separate diagnostic finds zero unreachable objects for this warmed
candidate. It also proves a behavior change: two calls with the same fields
receive instances of the same class. Assigning `type(first).value = 999` makes
a later payload's `.value` read 999 while its tuple item remains the supplied
3. The original returns 3 through both accesses. Passing the timing screen
therefore justifies a compatible follow-up, not adoption of shared classes.

### Reuse constructor compilation while preserving fresh classes

The follow-up copies the local standard-library factory functions with private
globals and changes only their constructor `eval`: a 128-entry cache retains
compiled code for source strings up to 4,096 characters. It still creates fresh
functions, namespaces, descriptors, annotations and classes. Standard-library
modules are not patched. This is an experiment tied to the current Python
factory implementation, not a proposed production dependency on its private
functions.

The same eight-pair screen finds 0.101 ms median wall and CPU savings, with only
four joint wins. Wall savings are 0.270, 0.833, -0.241, -0.280, -0.068, 0.340,
-0.069 and 0.752 ms. Every activation has seven hits and two code entries;
snapshots, HTML and native hashes match. Fresh class identity and the observed
class-edit isolation match the original. The separate census still finds 265
unreachable objects, all reachable from the seven generated classes. Other
interpreters, factory replacements, custom mapping callbacks, code-object
identity, tracing and audit-hook behavior remain unqualified.

Reject both implementations for production: sharing classes changes behavior,
and reusing constructor compilation alone misses both parts of the timing
screen. This does not rule out preparing more of class generation while
preserving fresh public objects. It establishes neither the removable GC cost
nor a speed ceiling for a different design.

The plan and four scripts are in `benchmarks/provided_type_probe`. Reports are
`provided-{type,constructor}-{processes,contracts}.json` in the repeat-render
results directory. Exact measured runners are retained as
`provided-{type,constructor}-runner.py.txt`; subsequent runner edits only
qualify two docstrings and add a lint suppression. The timing code is
unchanged. Ruff checks and formatting pass. Production source and its previous
integrated validation remain unchanged.

Independent technical review recomputed both reports from their raw samples
and checked the archives and diagnostic evidence. A separate prose pass
checked this section, the plan, all four scripts, archives, reports and
delivery wording.

## Twenty-fourth iteration: declare context-record merge operations

The three default context-merge subscribers all copy a nonempty child record
dictionary into the corresponding parent dictionary. Each manager call also
constructs a frozen hook context and dispatches Dependencies, Events and I18n
callbacks. The fixture reaches 546 calls, with 227 empty child `extra` mappings
and nine calls sharing the outer `extra` mapping. Untimed post-merge inspection
finds 319 nonempty dependency entries containing 2,490 items in total, and no
Events or I18n entries. Those last counts inspect child records after the
complete merge; they are not general counts of actual update operations when
entries alias across keys.

The first candidate in `benchmarks/context_merge_probe` prepares the ordered
keys of the three exact built-in subscriber types on its first call. Later
calls apply their dictionary operations directly, without hook-context creation
or callback dispatch. Child entries are read in the original subscriber order,
after earlier updates. Dictionary updates remain live, including shared maps.
Preparation rejects unknown subscriber types and class hooks changed after the
probe captured their identities at import. Preinstalled replacements are
trusted, and later hook or metadata changes are untracked.

Eight balanced randomized fresh-process pairs retain 80 complete renders after
six warmups, with normal GC. Median process-pair mean saving is 0.548 ms wall
and 0.531 ms CPU; seven pairs improve both. Raw wall savings are 0.359, 0.664,
0.476, 0.730, 0.583, 0.514, -0.015 and 0.732 ms. All pairs remain included.
Every candidate worker activates the same three-key plan and reaches the counts above.
All four ownership snapshots reached in the untimed comparison match, as do
all paired HTML digests and native hashes.

Five synthetic cases preserve ordered results for empty entries, all three
extensions, overwrites, shared outer mappings and shared inner mappings.
An instance-hook counterexample proves the compatibility limit: the original
calls an overridden hook and records its application value; the candidate
silently omits both. Passing the performance screen therefore supports a
follow-up design, not adopting this inferred fixed plan.

### Resolve each hook before selecting its merge operation

`live_probe.py` resolves each current hook in dispatch order. Recognized exact
bound methods use the dictionary operation. Other callbacks run normally,
sharing a hook context created only when first needed. The focused checks
preserve instance overrides, a class override installed after an earlier merge,
and a callback that replaces the next subscriber's method. The last check also
confirms that both ordinary callbacks receive the same context object.

The same process screen finds 0.147 ms median wall and CPU savings, with seven
joint wins. Wall savings are 0.154, 0.140, 0.122, 1.372, 0.153, 0.189, 0.054
and -0.430 ms; none is excluded. Activation, all reached snapshots, paired HTML
and native hashes match. This candidate misses the 0.25 ms magnitude threshold.
The two separate experiments do not establish an exact cost for live hook
selection. They show that this particular follow-up does not retain enough
measured benefit to justify production adoption.

Both candidates remain experimental. A production mechanism must let every
extension declare its own merge policy, with an explicit relationship to custom
hooks. Core special cases for three named extensions would violate the
repository's composition rule. Helper/global changes inside recognized methods,
function-body edits, hook-context constructor changes, custom manager dispatch,
preinstalled replacements and concurrency remain unqualified. No extension API
or production source changes in this iteration.

The plan and four scripts are in `benchmarks/context_merge_probe`; raw reports
are `context-merge-{processes,contracts}.json` and
`context-merge-live-{processes,contracts}.json`. Exact measured runners are
retained as `context-merge-runner.py.txt` and
`context-merge-live-runner.py.txt`. Later runner edits only clarify diagnostic
docstrings and add a lint suppression. Ruff checks and formatting pass;
production retains its previous integrated validation.

Independent technical review recomputed the reported savings and checked the
archives, snapshots and synthetic observations. A separate prose pass checked
the plan, scripts, this section, reports, archived runners and delivery draft.

## Twenty-fifth iteration: reuse attribute merges or name positions

The final attribute-output cache runs after element nodes merge their resolved
contributions. The first candidate in `benchmarks/attr_merge_probe` caches that
merge result for an exact list of at most 16 exact two-item tuples. Keys must
be exact strings, and values exact strings, bools or None. The total input text
is limited to 2,048 characters and the cache to 256 entries. Each hit constructs
a fresh dict from cached immutable items. Expression resolution, spread
iteration and validation, directives, extension hooks and formatting remain
outside this cache.

Eight balanced randomized fresh-process pairs retain 80 complete renders after
six warmups with normal GC. Median process-pair mean saving is 0.296 ms wall
and CPU, with six joint wins. Wall savings are 1.455, -0.396, 0.200, 0.388,
2.501, 0.203, 0.638 and -0.029 ms. Every pair remains included. Each candidate
activation reaches 430 hits, zero misses and 96 retained contribution sequences.
All four ownership snapshots reached in the untimed comparison match; every
paired HTML digest and native hash also matches.

The checker compares 300 randomized ordered results and verifies that changing
one returned dict does not affect the next. It also checks two mutations of
structured fallback input, a 256-entry limit after 400 distinct inputs and an
oversized fallback. Two counterexamples prevent a compatibility claim: equal
hits reuse earlier string key/value objects, and a changed class normalizer
leaves the cached output stale. Returning a fresh dict does not preserve current
ordinary-attribute string identities. The candidate misses the seven-win
screen, so it is not adopted.

### Prepare attribute-name positions while keeping values live

A different candidate caches only the ordered name relationships: first key
positions, last ordinary-value positions and the indices contributing to class
and style. Each application reads the current keys and values and calls the
current normalizers in the original class-then-style order. The cache retains
names and integer positions rather than application values. Exact list, tuple
and key checks still apply; the text bound now covers names only. Replacing any
of the three HTML identity helper functions after probe import takes the original
path. Preinstalled replacements, changes inside functions, translation-table
mutation and concurrency remain unqualified.

The same eight-pair screen yields -0.118 ms median wall and CPU saving, with
two joint wins. Wall savings are -0.282, -0.052, -0.269, 0.218, -0.327, -0.169,
0.090 and -0.068 ms. Every candidate activation reaches 505 hits, zero misses
and 51 retained name layouts. All reached snapshots, paired HTML digests and
native hashes match. This candidate is active but slower in the measured
workload; it is not adopted.

The same 300 ordered-result and output-isolation checks pass, as do structured
mutations and the cache bound. Additional observations preserve the current
string objects, use a replaced class normalizer and fall back to a replaced
HTML identity helper. These focused checks are not full production qualification.
The timing does not show that all preparation of name relationships is
ineffective; a design avoiding the candidate's per-call work would need its
own evidence.

The plan and four scripts are in `benchmarks/attr_merge_probe`. Reports are
`attr-merge-{processes,contracts}.json` and
`attr-merge-positions-{processes,contracts}.json`. The exact measured runners
are retained in `attr-merge-runner.py.txt` and
`attr-merge-positions-runner.py.txt`. Subsequent runner edits organize imports
and clarify one docstring; candidate algorithms and timing loops are unchanged.
Ruff checks and formatting pass. Production source and its previous integrated
validation remain unchanged.

Independent technical review recomputed the timing aggregates and checked
activation, equality, contract observations and archived-runner provenance.
A separate prose pass covered the plan, four scripts, this section, reports,
archives and delivery draft.

## Twenty-sixth iteration: recheck combined native ownership storage

The existing native ownership prototype passes the current process screen when
combined with the current renderer: 0.911 ms median process-pair mean wall and
CPU saving, with seven of eight pairs faster on both clocks. This supports
further work on native ownership operations. It does not qualify the prototype
for production or attribute the gain to a particular earlier change.

The standalone locked release build uses the existing Rust sources and the
current interpreter. Both variants load that artifact outside timing. Eight
balanced randomized fresh-process pairs retain 80 complete renders after six
warmups with normal GC. Wall savings are 2.249, 1.188, 0.857, 0.730, 0.867,
1.682, 0.955 and -0.478 ms; every pair remains included. All paired HTML
hashes and both native artifact hashes match. Four snapshots reached in the
untimed reference/candidate comparison are equal. Every candidate activation
keeps all four native table families through its observed snapshots and runs
one native retirement with zero unsupported-input fallbacks. Native ancestry
queries remain disabled. The current empty-hook-retirement guard runs in both
variants; this experiment does not isolate its contribution.

An additional untimed render wraps the four native table factories to count
immutable Python record exports and record their nearest Python caller. Its
HTML matches an ordinary render with the same IDs. Across 1,423 captured rows
(342 instances, 339 ancestry edges, 468 fills and 274 physical regions), it
observes 2,115 exports. Snapshot readers account for 1,385. Other readers account
for 730: source invocation binding exports 194 fills; checking whether a fill
needs revival exports another 194; slot capture exports 274 fills and 68 parent
regions. These are construction counts, not timings or allocation bytes. The
counter excludes invocation, queue and source-location record families.

A native table caches an exported immutable record until a patch invalidates
it. Python capture code can therefore export a row, read a few fields, patch
it, then export it again at the next reader. Moving related field checks and
updates together could eliminate some of these intermediate records. That is
the next bounded investigation. Snapshot exports still supply the current
Python-facing ownership contract and remain inside render timing.

The plan and two scripts are in `benchmarks/native_storage_process_probe`.
Reports are `native-storage-current-processes.json` and
`native-storage-current-readers.json`. Both include the exact harness and native
artifact hashes; the timing report also records the adapter and Rust sources.
Ruff checks and formatting passed before execution. No production or Rust
source changes in this iteration. Replay fallback, private container/factory
compatibility, native numeric limits, mutation atomicity and reentrancy remain
qualification work; the existing production validation does not cover this
experimental backend.

Independent technical review recomputed the raw-sample aggregates and checked
source/artifact hashes, equality and diagnostic totals. A separate prose pass
covered both scripts, the plan, reports, this section and delivery wording.

## Twenty-seventh iteration: combine native fill checks and binding

Two experimental RecordTable operations work directly on fill fields. Source
binding checks policy, kind, lexical owner and an existing source invocation
before updating that invocation. Receiver binding handles an active fill whose
receiver is empty or equal, then updates receiver ID/class together. Retired
fills and another receiver use the existing Python revival/forwarding path.
The adapter preserves per-slot iteration and updates. Review caught a table
conversion during slot iteration; the source-binding adapter now checks the
current table per slot and continues with Python on materialized lists.

The untimed reader diagnostic confirms the intended reduction: 1,727 exports
for the same 1,423 captured rows, removing all 388 source-binding and revival
exports observed in iteration twenty-six. Snapshot exports remain 1,385; slot
capture accounts for the remaining 342. Matching HTML and explicit count checks
establish that the new branches activate. These counts cover only the four
native table families and do not measure time or bytes.

The median increase in process mean render time is 0.138 ms wall and
0.137 ms CPU, with four of eight pairs improving both clocks. Wall savings
are 0.021, 0.222, -0.568, 0.641, -0.424, -0.297, -0.867 and 0.084 ms.
Each fresh process retains 80 renders after six warmups with normal GC; all
samples remain included. Both variants use the same newly built standalone
artifact. The reference enables the existing native backend; the candidate adds
the two grouped binding operations. Every paired HTML digest and native hash
matches. Four snapshots in the untimed comparison match, and both timed variants'
separate activation renders retain native tables and native retirement without
fallback. This comparison is incremental against native storage, not production.

The candidate fails both the seven-win and 0.25 ms magnitude screens and is
not adopted. Fewer immutable exports alone did not yield a complete-render
benefit in this design. The experiment does not isolate the costs of native
calls, rich comparisons or Python fallback checks, so it cannot assign the
regression to one of those mechanisms. It also does not invalidate the broader
combined-native result from iteration twenty-six.

Nine differential binding cases compare production with the grouped backend:
normal/repeated attachment, fallback/Python supplies, wrong lexical owner,
rebinding, forwarding, retirement and materialization during slot iteration.
They compare errors, retained immutable records, final fills and receiver maps.
Six native validation observations reject wrong-width or empty-table indexes
without changing table length. The existing ownership, manifest and cache-replay
suites pass all 134 tests with the candidate installed. These checks do not
qualify custom factories/helpers, private container mutation, reentrant rich
comparisons/destructors, concurrency or the prototype's broader numeric and
atomicity limits.

The prior-art plan and four scripts live in
`benchmarks/native_fill_binding_probe`. The two methods and their signatures
are confined to the standalone journal crate and its local stub. Reports are
`native-fill-binding-{processes,readers,contracts}.json` and
`native-fill-binding-tests.txt`. Timing and reader reports retain exact harness,
adapter and artifact hashes; timing also records the Rust sources. Ruff checks,
Python formatting and Rust formatting pass. No production source or shipping
binding changes in this iteration; its previous integrated validation remains
the production evidence.

Independent technical review checked the native operations, adapter fallback,
focused observations and hashes, then recomputed the timing aggregates. A
separate prose pass covered the plan, scripts, Rust comments, local stub, reports,
this section and delivery wording.

## Twenty-eighth iteration: prepare a slot region in one native operation

The next standalone operation reads an active fill and its containing region,
resolves the receiver and ownership transition, assembles region fields and
appends the region. Python retains supply selection, context variables, callback
execution, result-owner lookup and wrapping. Retired fills use the existing
revival path. Counters and the region index become visible before the callback;
post-callback patches check the current storage in case replay materialized it.
The rejected grouped binding operations from iteration twenty-seven stay disabled.

The untimed reader render exports 1,811 records across the four native table
families, compared with 2,115 in iteration twenty-six. All 342 capture-reader
exports disappear, but snapshots export 1,423 rather than 1,385 records: 38 rows
previously exported during capture were reusable at the snapshot. The net
reduction is therefore 304 records. Source binding and revival still export
194 fills each. HTML matches and explicit count checks establish activation;
these counts do not measure allocation bytes or timing.

Eight balanced randomized fresh-process pairs compare this candidate against
the existing native backend using the same rebuilt artifact. Each process
retains 80 complete renders after six warmups with normal GC. Median paired
mean savings are 0.351 ms wall and CPU, with six joint wins. Wall savings are
0.436, 0.267, -0.126, 0.436, 0.469, 1.047, -0.018 and 0.078 ms; all samples
remain included. Four untimed snapshots, every paired HTML digest and both
native artifact hashes match. The separate activation render in each worker
retains native tables and native retirement with no fallback.

This candidate passes the magnitude screen but misses the required seven joint
wins. It remains experimental. The evidence supports examining a larger combined
operation or conversion path; it does not establish an adoptable incremental
gain or justify adding this saving to earlier measurements.

Seven differential cases compare callback-visible counters/indexes/snapshots and
final state with production: standalone fills, outlets, nesting, retired fills,
untracked slots, callback errors and wrapper-class alias replacement during the
callback. Review found that wrapper imports must stay after the callback; the
adapter now follows that order. Two reused storage checks exercise successful
and raising replay inside the callback with the candidate installed. Six native
validation cases reject wrong layouts, malformed argument tuples or invalid
indexes before appending. An inactive fill declines before parent-row lookup.
All 134 ownership, manifest and cache-replay tests pass with the candidate.

The prior-art plan and four scripts are in `benchmarks/native_slot_region_probe`.
Reports are `native-slot-region-{processes,readers,contracts}.json` and
`native-slot-region-tests.txt`. Exact adapter/artifact/harness hashes are retained;
the timing report also records Rust sources. Python lint/format and Rust format
checks pass. The new method and stub remain confined to the standalone benchmark
crate. Custom factories/helpers, selection/hash callback effects on fallback,
malformed private indexes, reentrancy, concurrent mutation and allocation-failure
atomicity remain outside qualification. No production or shipping binding source
changes in this iteration.

Independent technical review checked the native field mapping, callback/fallback
behavior, focused observations and source hashes, then recomputed the timing
aggregates. A separate prose pass covered the plan, scripts, native comments,
stub, reports, this section and delivery wording.

## Twenty-ninth iteration: construct exported records from the field tuple

The native tables and invocation journal already assemble a complete tuple of
fields before exporting an immutable Python record. The local NamedTuple
constructor then repacks positional arguments in its generated Python `__new__`
function and calls `tuple.__new__`. An experimental optional constructor lets
native export call that builtin directly with the known record class and its
existing field tuple. Cached immutable views remain unchanged. Native GC visits
and clears the optional callable. The grouped binding and slot-preparation
operations remain disabled in this comparison.

The untimed diagnostic reaches all six classes: 678 invocation records, 339
queue records, 1,098 fills, 336 regions, 342 instances and 339 ancestry edges.
That is 3,132 direct constructions, including the same 2,115 four-table exports
observed in iteration twenty-six. The wrapper counting these calls preserves
the HTML. This changes construction work, not the number of retained ownership
records or the snapshot contract.

Eight balanced randomized fresh-process pairs compare direct construction with
the existing native backend using the same rebuilt artifact. Each retains 80
complete renders after six warmups with normal GC and all samples included.
Median paired mean savings are 0.418 ms wall and CPU, with six joint wins.
Wall savings are 0.623, 0.453, 1.363, -1.092, 0.384, 2.804, -0.380 and
0.047 ms. Four untimed snapshots, all paired HTML digests and both native
artifact hashes match. Every worker's separate activation render retains native
tables and uses native retirement with no fallback.

The candidate misses the seven-win consistency screen and is not adopted.
Its positive median and the preceding slot-preparation result justify a
combined measurement, since changing which records are exported can change the
construction costs too. The separate savings cannot establish their combined
benefit. Normal GC remains inside timing; no samples or unfavorable pairs are
removed.

The focused checker verifies all field identities and exact record types for
four table families, cache reuse, and retained views across patches. Journal
checks cover both exact record types, cache preservation when configuring the
constructor, invalidation after binding, and the retained source-field identity.
Two non-callable constructor cases recover through the normal factory after an
export error. Four cycles through the optional constructor are collected, for
table/journal storage both before and after export. All 134 ownership, manifest
and cache-replay tests pass with direct construction installed.

The plan and four scripts are in `benchmarks/native_record_export_probe`.
Reports are `native-record-export-{processes,readers,contracts}.json` and
`native-record-export-tests.txt`. Timing retains exact harness, adapter, Rust
source and artifact hashes; focused reports also retain their relevant hashes.
Python lint/format and Rust format checks pass. The experimental setter and
helper live only in the standalone crate and its local stub. Custom record
constructors, mutations to their definitions or helper globals, arbitrary
constructor callbacks and reentrancy remain unqualified. No production or
shipping binding source changes in this iteration.

Independent technical review checked constructor/caching/GC behavior and the
focused reports, then recomputed all timing aggregates and checked source hashes.
A separate prose pass covered the plan, scripts, native additions, local stub,
reports, this section and delivery wording.

## Thirtieth iteration: combine native slot preparation and direct exports

The combined adapter installs the existing slot-preparation method and the graph
initializer that configures direct tuple construction. Grouped fill binding
remains disabled. It adds no Rust or production source changes. Both parent
experiments had positive median savings but missed the seven-win screen; this
comparison measures their interaction directly.

The combined candidate passes against the existing native backend: 0.569 ms
median paired mean wall saving and 0.569 ms CPU saving, with eight joint wins.
Wall savings are 0.476, 1.000, 0.582, 0.814, 0.422, 0.557, 0.646 and
0.485 ms. Eight balanced randomized fresh-process pairs retain 80 complete
renders after six warmups with normal GC. Both variants load the same native
artifact, and all samples remain included. Four snapshots, all paired HTML
digests and both artifact hashes match. Both variants' separate activation
renders retain native tables and native retirement with no fallback.

A new production-reference comparison then measures the whole combination.
Median paired mean savings are 1.284 ms wall and 1.280 ms CPU, with eight
joint wins. Wall savings are 1.275, 0.759, 0.751, 1.288, 2.444, 1.314,
1.280 and 1.957 ms. It uses the same process method with a new balanced order
seed and the same artifact in both variants. Four snapshots now compare directly
with production and match, as do every paired HTML digest and native hash.
Candidate-only activation confirms native tables and retirement. This establishes
a current full-render candidate gain; it is not a sum of historical results.

The untimed constructor diagnostic reaches 2,828 direct exports: 678 invocation
records, 339 queue records, 856 fills, 274 regions, 342 instances and 339
ancestry edges. It confirms both operations activate and preserves the HTML.
That is 304 fewer constructions than direct export alone. The slot contract
checker passes all seven differential cases, both mid-callback replay cases,
six invalid-input observations and inactive-fill rejection before parent lookup.
All 134 ownership, manifest and cache-replay tests pass with the composition.
These checks support the next compatibility/integration audit; they do not yet
qualify the whole native backend for production.

The plan and five scripts are in `benchmarks/native_combined_capture_probe`.
Reports are `native-combined-capture-{processes,production,readers,contracts}.json`
and `native-combined-capture-tests.txt`. The exact measured production runner is
retained as `native-combined-production-runner.py.txt`; the subsequent runner
edit only clarifies the reference backend in a docstring. Timing reports retain
the combined and both parent adapters, harness, Rust sources and artifact hashes.
Python lint/format checks pass; Rust source is unchanged from iteration twenty-nine.
The next task is to audit native runtime behavior, exposed/private contracts and
packaging before integrating it, retaining the limitations recorded in the parent
plans until evidence or implementation resolves them. Production source and its
previous integrated validation remain unchanged.

Independent technical review checked composition/restoration, focused evidence
and both timing comparisons, including raw aggregates and the archived runner.
A separate prose pass covered the plan, five scripts, archive, reports, this
section and delivery wording.

## Thirty-first iteration: widen native ownership qualification

The full non-browser Citry test selection passes with the combined native
candidate installed in the pytest process: 4,728 passed, five skipped, 553
browser tests deselected and one expected failure in 28.04 seconds. Existing
fresh-interpreter subprocess checks retain their normal bootstrap and do not
qualify the native backend. This is broader main-process runtime evidence than
the 134-test ownership/manifest/replay selection. It is not the full repository gate
or browser validation, and production remains unchanged.

The source audit finds the six mutable ownership table fields used only inside
`ownership.py` in production Python code. `OwnershipGraph` exposes an immutable
snapshot result; changing its private list representation need not change those
record types or fields. Replay transaction snapshots materialize rows into lists,
and rollback restores those lists. The prototype's snapshot import materializes
tables before continuing through the existing replay implementation. Detached
instance import appends records supported by RecordTable. These observations
scope the integration audit; they do not make arbitrary private mutation a
supported extension API.

A retained native boundary probe establishes a representation gap. Capture,
binding and settlement reject a queue order of `2**64` with OverflowError before
changing journal rows. Retiring one invocation starting at `2**64 - 1` raises
after marking that invocation retired, leaving its queue enqueued. These inputs
are constructed native-boundary cases, not failures observed in the normal
render fixture. Python graph counters and queue records use arbitrary-precision
integers, so preserving their existing object references is a plausible fix that
also avoids conversion into and back out of u64 on ordinary exports.

The next implementation will separate stored Python queue orders from the
portable numeric relationship calculation. Out-of-range retirement inputs need
the Python fallback before mutation; ordinary native capture/bind/settle need
not impose a numeric range on stored field references. Recheck errors, retained
records, collection and complete-render performance after this change.

The plan and two executable probes are in
`benchmarks/native_ownership_qualification`. Reports are
`native-qualification-suite.txt` and `native-qualification-boundaries-before.json`,
including exact runner/installer/artifact hashes. Ruff checks and formatting pass.
The broader packaging audit also confirms that the existing retirement
calculation is independent of Python, while the prototype still builds in its
own workspace. A reviewed structural plan must place portable relationships in
the Rust workspace and Python object handling in the binding before integration.

Independent technical review checked the suite scope, boundary outcomes,
replay/storage source inventory, packaging requirements and hashes. A separate
prose pass covered the plan, both scripts/reports and this section; the text
now distinguishes the patched pytest process from normal child interpreters.

## Thirty-second iteration: retain Python queue-order objects

The native journal now stores enqueued, rendered and settled orders as Python
references. Capture, binding, settlement and queue assignment retain the supplied
objects, and exports clone those references. Native GC visits all three fields.
Retirement increments the Python integer and stores the same resulting object
in the queue. This removes the demonstrated u64 overflow failure from stored
queue orders and avoids reconstructing those integers during export.

The portable numeric retirement calculation still uses u64. Its adapter now
classifies out-of-range exact integers as UnsupportedRetirement before mutation,
so the existing Python path handles those relationships. This does not add a
Rust arbitrary-precision type or expand the portable calculation's numeric domain.
The Python stub's int contract includes arbitrary-precision values already.

All four retained boundary operations now succeed. Focused checks preserve
specific input objects beyond `2**64`, including assigned enqueued/rendered
fields after cache invalidation and a fresh export. Retirement across the
boundary returns the same integer object stored in its settled queue. Failed
queues retain state, order and cached view; earlier exported records remain
unchanged. Six synthetic cycles through the three order fields are collected,
both before and after export. Five constructed graphs with large/negative IDs,
large current order or large/negative cutoffs match production snapshots and
request exactly one Python retirement fallback each. These are boundary and
relationship fixtures, not complete validated render lifecycles.

The full non-browser Citry selection passes again with the candidate installed
in the pytest process: 4,728 passed, five skipped, 553 deselected and one expected
failure in 27.86 seconds. Existing fresh-interpreter child checks use their
normal bootstrap. Rust formatting, Clippy with warnings denied and Python
lint/format checks pass. The fresh-export setter assertion was added after the
suite/timing runs; it changes only the focused checker, which was rerun.

A fresh production-reference comparison retains the complete candidate's gain:
1.329 ms median paired mean wall saving and 1.313 ms CPU saving, with eight
joint wins. Wall savings are 1.992, 1.353, 1.234, 1.359, 1.105, 0.294,
1.306 and 1.445 ms. Eight balanced randomized fresh-process pairs retain 80
renders after six warmups with normal GC and every sample included. Four
snapshots, all paired HTML digests and both native artifact hashes match.
Candidate activations retain native tables and use native retirement with zero
fallbacks on this ordinary fixture. This compares the full corrected candidate
against production; it does not isolate an incremental timing gain from retaining
queue-order objects.

The written design and focused checker are
`native_ownership_qualification/queue_orders.md` and `queue_order_checks.py`.
Reports are `native-qualification-boundaries-after.json`,
`native-queue-order-{checks,production}.json` and `native-queue-order-suite.txt`.
They retain their runner/adapter/artifact hashes; timing also records native
sources. The current README describes Python order retention and numeric
fallback, and the earlier design plans link to the current qualification.
Changes remain in the standalone native prototype. Private inconsistent writes,
custom arithmetic/reentrancy and allocation-failure atomicity remain unqualified.
Production packaging and activation still require the structural integration
plan, binding/stub work and broader repository/browser validation.

Independent technical review checked the storage/conversion/GC changes, focused
boundary and fallback evidence, suite scope and raw timing aggregates. A separate
prose pass covered the current README, historical-plan pointers, queue-order
plan/checker, native changes, reports, this section and delivery wording.

## Thirty-third iteration: share the portable ownership calculation

The relationship calculation now lives in the internal `citry_ownership` Rust
workspace crate. The standalone native probe consumes that crate by path.
Its calculation source is byte-identical to the preceding committed prototype;
this stage changes build ownership, not the retirement algorithm. Python
references, conversion, storage and mutation still live in the probe binding.
The ordinary Python package does not activate this backend yet.

Five focused Rust tests cover preserved descendants and ancestry, order
cutoffs, nested physical-region preservation, later fill promotion, cyclic
ancestry with selectors/initialization, and duplicate identifiers. The rebuilt
probe passes 1,000 seeded graphs with 3,000 sequential retirement comparisons
against Python and 17 custom-value rejection/fallback cases. The combined
slot/callback/replay checks and arbitrary-precision queue-order checks pass
against the rebuilt artifact as well. Rust formatting and Clippy with warnings
denied pass for both crates; all changed Python runners pass Ruff.

Workspace membership, dependency declarations and both lockfiles include the
new crate. Existing repository and CI Rust checks discover it automatically.
The codebase guide includes it in crate listings and scoped test commands.
Every executable timing runner that recorded the probe's graph source now
records the shared crate source/manifest and root manifests. Historical reports
retain their original source hashes. New reports are
`native-core-extraction.json`, `native-core-extraction-contracts.json` and
`native-core-extraction-queue-orders.json` under `benchmarks/results/performance-render`.

Moving code across a crate boundary can change compiler inlining, so the
extraction also received one fresh complete-render comparison. It retains
eight joint wins and a median paired mean wall saving of 1.444 ms (1.444 ms
CPU) against production. The eight wall savings are 1.757, 1.041, 2.238,
1.251, 0.945, 1.638, 2.412 and 0.846 ms. Four snapshots and HTML match;
candidate activation uses native tables and one native retirement with zero
fallbacks. `native-core-extraction-production.json` retains all samples and
source/artifact hashes. This rechecks the complete candidate, not an incremental
speedup from extraction. No builds or CPU-heavy checks overlapped timing.

The user also asked what the consistency threshold means. The existing screening
rule requires at least seven of eight process pairs to improve both wall and
CPU time, plus at least 0.25 ms median paired mean wall saving. Each worker
performs six warmups and 80 measured renders, retaining all samples with normal
GC. This is a practical experiment threshold, not a statistical confidence
guarantee or a substitute for correctness and workload qualification. The last
pre-extraction result passed with eight wins and 1.329 ms median wall saving.

The staged integration design is
`benchmarks/native_ownership_qualification/integration.md`. Next, add host
reference storage and conversion to the ordinary PyO3 binding, with matching
stub/wrapper declarations, before activating it in the ownership runtime.

Independent technical review verified source identity, the graph lifecycle,
workspace/lockfile changes, all four reports' hashes and the raw timing means.
A separate prose pass covered the new crate, integration plan, changed runners
and benchmark docs, codebase guide, this section, reports and delivery wording.
The plan now identifies the pre-extraction timing and historical source citation
explicitly. Timing descriptions distinguish each process mean from the median
of paired savings.

## Thirty-fourth iteration: build ownership storage in the regular extension

The regular `citry_core_py` extension now includes ownership storage through
`_rust.ownership` and the private `citry_core._ownership` wrapper. The shared
`citry_ownership` crate still owns the portable relationship calculation.
The binding retains Python fields, queue orders and cached immutable exports;
it exposes the accepted capture, binding, settlement, slot preparation and
retirement operations. The stub and wrapper move with registration. Optional
ancestry and grouped fill-binding experiments stay in the standalone probe.
Packaged retirement accepts the four native tables and five state values used
by the accepted candidate. Replay and unsupported-value fallback still run
through Python in the experimental runtime adapters.

Fourteen new core-package tests check exception identity, sequence/bisect
behavior, field identity, retained views, export errors, queue settlement,
arbitrary-precision orders, conversion errors and reference cycles. The core
package selection passes 459 tests. With the packaged candidate installed in
pytest, the non-browser Citry selection passes 4,728 tests, with five skipped,
553 deselected and one expected failure. The qualification runner also reuses
1,000 seeded graphs with 3,000 sequential retirement comparisons, 17 custom
fallback cases and the existing slot/callback/replay and queue-order checks.
Child interpreters use ordinary runtime activation at this stage.

The older journal checker still expected queue-order overflow, despite the
earlier implementation fix. A search found this one stale executable assertion.
It now checks successful retirement across `2**64` and identity of the returned
order in the queue. This corrects the checker to the established Python order
contract; it does not change the native implementation.

The local CPython 3.14 release build passes the complete-render comparison with
eight joint wins and median paired mean savings of 1.546 ms wall and 1.545 ms
CPU against production. The wall savings are 1.337, 1.579, 1.599, 1.664,
1.300, 1.452, 1.512 and 1.834 ms. Four snapshots, HTML, worker inputs and
artifact hashes match; candidate retirement uses native storage with zero
fallbacks. Both variants load the same normal extension. The capture adapters
remain experimental, so this is not yet ordinary runtime activation.

The ABI3 build also succeeds with the publishing workflow's `release-wheel`
profile and `abi3-py310` feature. After checking the actual imported path and moving the generated
version-specific binary aside, the ABI3 artifact passes all 459 core tests and
the 4,728-test Citry selection, including the repeated focused qualification.
The build guide now explains how to check artifact selection when switching
build configurations. These runs exercise ABI3 on CPython 3.14 on macOS; they
do not establish the full interpreter/platform release matrix.
Both local builds use the recorded nightly Rust toolchain; the publishing
workflow's pinned toolchain remains part of final release qualification.

The verified ABI3 artifact also retains eight joint wins, with median paired
mean savings of 1.572 ms wall and 1.572 ms CPU against production. Wall savings
are 1.363, 2.472, 1.894, 1.340, 1.425, 1.556, 1.588 and 1.641 ms.
Four snapshots and all paired HTML/native hashes match; candidate activation
again records one native retirement and zero fallbacks. Both build comparisons
use eight balanced fresh-process pairs, six warmups and 80 measured renders
per worker, normal GC and no excluded samples. No builds or CPU-heavy checks
overlap either comparison. These are complete-candidate comparisons against
production, not incremental savings to add to the earlier prototype results.

Rust formatting and repository-form Clippy (`--no-deps`, warnings denied) pass.
Linux-target mypy passes for the 13 core Python source files, and changed Python
files pass Ruff. The initial Clippy invocation included vendored dependencies
and failed on an existing Ruff `collapsible_if` warning; the repository's
configured command scopes those dependency lints out. An initial root-directory
maturin invocation rejected the tooling-only root pyproject; both successful
builds used the owning package directory.

The stage-two plan is `benchmarks/native_ownership_qualification/binding.md`; runnable
qualification and timing are in `benchmarks/packaged_ownership_probe`.
`packaged-ownership-builds.json` records build commands, imported paths, native
hashes, tool versions and binding/shared-crate source hashes. The other
`packaged-ownership-*` reports retain the contract, test and raw timing evidence.
The preceding local-build contract report is retained separately as
`packaged-ownership-cp314-contracts.json`.

Next, activate the binding through ordinary ownership runtime code, preserving
the Python fallback and callback/replay behavior. That stage must check second
renders and smaller workloads, then run the repository and browser gates on
the integrated result. No user-facing performance release note is warranted
for adding an inactive internal binding alone.

Independent technical review compared the retained binding operations with the
prototype and verified raw means, sample counts, snapshots, activation and
artifact/source hashes for both builds. A separate prose pass covered the
binding plan, Rust modules, Python declarations/tests, crate pointers, build
guide, runners, reports, this section and delivery wording. The text now makes
index conversion errors, imported artifact selection and pytest-process scope
explicit.

## Thirty-fifth iteration: activate native ownership in ordinary renders

The runtime now creates the packaged invocation/queue journal and four native
record tables when the installed core exposes them. Hot capture methods append
record fields directly and export the existing immutable Python record types
when a reader asks for them. Source-location records remain Python values.
Native retirement applies the shared relationship calculation. Unsupported
values fall through to the existing Python retirement algorithm.

An older core can lack both the native ownership namespace and its Python
wrapper. Runtime capability detection imports only `_rust`, so that pairing
continues with Python lists. Replay materializes the six stored families into
lists before importing records. Slot callbacks can perform replay and then
return or raise; subsequent writes inspect the current storage.

Independent source review found three observable differences during integration.
A custom string ID can run Python while hashing or comparing with a later ID.
Combining invocation and queue binding moved a queue update ahead of that code.
The first such bound ID now materializes invocation and queue storage, preserving
Python mutation order for the rest of the graph. Separately, comparisons and
result properties can replace a saved fill or region. Three native update sites
now check that the current cached record is still the saved record; otherwise
they perform the original immutable replacement. Custom component attribute access can also replay the graph during binding;
those components use separate Python binding operations before any getter runs.
Twelve regression cases cover these transitions in both storage modes. Six additional tests cover ordinary
activation, an older core in a fresh interpreter, and replay inside successful
and failing slot callbacks.

`benchmarks/runtime_ownership_probe/reference_ownership.py.txt` archives the
ownership module at `1d8e8217`. The benchmark compiles only its collector class
against current record classes and context variables, then switches methods on
the existing class. This updates methods seen through aliases already imported by render
entry points. Candidate workers use ordinary runtime methods. Untimed renders
check that reference containers are lists and candidate containers are native.
The large fixture's four snapshots and the small fixture's three snapshots,
plus complete HTML, match. Seeded differential qualification passes 1,000 graphs,
3,000 sequential retirements and 17 unsupported-value fallback cases.

The timing runner retains six initial renders as well as 80 warm observations
per process. The second initial render measures the actual second render in a
fresh process. Both wall and CPU time and all HTML digests are retained. The
large-workload acceptance screen remains seven joint wins out of eight process
pairs and at least 0.25 ms median paired mean wall saving; smaller and initial
render observations provide additional workload qualification.

The final integrated large-workload comparison retains eight joint wins. Median
paired mean savings are 1.534 ms wall and 1.526 ms CPU. The eight wall savings
are 1.754, 1.717, 0.417, 1.242, 3.107, 1.600, 1.449 and 1.469 ms.
Actual second renders improve in seven pairs, with a median paired wall saving
of 1.827 ms. This second-render observation has only eight samples per variant;
it is supporting evidence, not the 80-sample warm throughput comparison.
The median worker means are 33.092 ms for Python and 31.747 ms for native.
A difference of these two medians need not equal the median paired saving.

The tiny fixture regresses: median paired warm wall saving is -0.006525 ms,
with only one joint win. Median worker means are 0.109235 ms Python and
0.116634 ms native. Its actual second render has a median paired regression of
0.019459 ms. Accept this iteration for the repeat-render target's large fixture,
with the small-workload tradeoff explicit. Native storage setup is a plausible
next lead, but this comparison does not isolate that cost. Lazy allocation or
conversion after a small Python prefix needs its own transition and timing
checks before adoption. Do not claim a benefit for every workload.

Reports are `runtime-ownership-large.json` and `runtime-ownership-small.json`.
Both use the ABI3 artifact SHA recorded in the preceding iteration, normal GC,
all eight process pairs and all samples. No tests or builds overlapped timing.
Ordinary desktop processes remained running; their presence and differences
between process means are reasons to prefer the paired comparison over an
absolute comparison with a previous day's result.

A fresh phase breakdown uses the original diagnostic boundaries:

| Work | Instrumented ms/render | Share of tree build |
|---|---:|---:|
| Component setup and orchestration | 9.08 | 27.4% |
| Ownership tracking | 6.39 | 19.3% |
| Child inputs and slots | 5.17 | 15.6% |
| Element attributes | 3.69 | 11.1% |
| Body traversal, expressions and control flow | 2.81 | 8.5% |
| Extension hooks and configuration allocation | 2.62 | 7.9% |
| Template and reusable-body cache work | 1.32 | 4.0% |
| Nested serialization | 1.07 | 3.2% |
| Application data callbacks | 0.95 | 2.9% |

These timers add overhead: the instrumented tree averages 33.095 ms. Separate
ordinary observations have median tree build 26.557 ms, root serialization
3.633 ms and total render 30.241 ms. Tree shares exclude root serialization.
Ownership's largest timed operations are slot capture/wrapping (1.729 ms),
source occurrences (1.462 ms), template fills (0.799 ms) and instance binding
(0.532 ms). Retirement is 0.384 ms. Compared with the preceding diagnostic,
ownership falls from 22.9% to 19.3%; independently timed runs are descriptive,
while the paired comparison above measures the adopted change.

The first full gate passed all 8,192 tests but failed coverage at 88.13% against
the 88.5% requirement. Default native activation bypasses Python fallback
branches that remain shipped. The existing ownership contract module now runs
in both installed and forced-Python modes. This exercises the fallback directly;
it does not claim installation of an older published wheel. The gate also found
formatting drift in the standalone experiment stub, now formatted without a
semantic change. Preserve the first report alongside the final gate report.

The final full gate passes all 19 phases in 113.744 seconds, with 88.74%
coverage. Linux-target mypy passes all 169 checked source files. The complete
553-test browser suite passed before the final custom-attribute binding guard;
after that guard, all 28 ownership-manifest and cache-replay browser tests pass.
The Unreleased performance entry records the larger-render improvement and
tiny-render overhead.
No package versions or release pins change in this iteration.

The tiny fixture has no component invocations, one logical instance, two fills
and one physical region. Its three snapshots report the same counts. That makes
allocation on the first actual nested component invocation a concrete next
experiment: retain Python storage for this fixture and convert existing rows
only when nested capture begins. The conversion boundary must preserve retained
snapshots, replay, custom IDs and callback-visible ordering. This is a lead for
the next independently measured area, not part of the accepted implementation.

## Thirty-sixth iteration: allocate native storage at the first nested call

The preceding iteration's tiny fixture has no nested invocations. This candidate
starts each graph with Python lists and creates native storage at its first
nested component call. It copies the existing instance, ancestry, fill and
region rows through native `append`, retaining immutable record identity.
The counter/index state and existing physical wrappers stay in the same graph.
Graphs with no nested calls continue recording all ownership in Python.

The conversion check runs after source preparation and before advancing the
invocation counter. Existing invocation or queue rows prevent conversion.
Imported invocation rows already advance the counter, so subsequent capture
stays on Python storage. Empty replay can still be followed by first-call
conversion; rollback restores the prefix and allows conversion from that state.
Construct replacement tables before assigning them. The native interface and
shared retirement calculation do not change.

The plan is `benchmarks/native_ownership_qualification/deferred.md`. Before
measurement, it requires at least seven joint tiny-fixture wins and positive
median paired wall/CPU savings. The large-fixture margin is at most 0.10 ms
median paired regression on either clock, about 0.3% of current total time.
Report signed results even inside that margin. This corrects small-render cost;
it is not another claim of a 0.25 ms large-render improvement.

`benchmarks/deferred_ownership_probe/eager_ownership.py.txt` archives the module
at `9cc3264`. The existing-class method switch compares that eager constructor
with the ordinary deferred runtime. Both fixture HTML outputs and all four
large/three small snapshots match. Activation checks require native tables for
the eager tiny reference and Python lists for its deferred counterpart. The
large fixture uses native tables in both variants.

Eight new tests cover retained rows through conversion inside successful and
failing slot callbacks, root-only storage, replay before conversion and rollback
after either replay or conversion. Existing native callback/replay fixtures now
explicitly initialize native storage so their backend labels remain meaningful.
The seeded native checker likewise initializes its synthetic native graphs;
3,000 sequential retirement comparisons and 17 fallback cases still pass.
The full non-browser Citry suite passed 4,813 tests before adding the eight new
transition tests. Independent technical and separate prose review found no
remaining blocker before timing.

The tiny comparison passes its screen: all eight pairs improve both clocks.
Median paired mean savings are 4.560 microseconds wall and
4.625 microseconds CPU. Median worker means are 0.113340 ms eager and
0.109261 ms deferred. Its actual second render is effectively unchanged in
this eight-pair sample: median wall saving -0.0004375 ms, four wall wins.
These are incremental measurements against eager native allocation, not a
new direct comparison with the original Python collector.

The large comparison also passes the predeclared margin. Median paired mean
savings are 0.134785 ms wall and 0.134675 ms CPU, with only five joint
wins. The eight wall savings are 0.336, -0.042, 1.686, -0.437, -0.286, 0.208, 0.062, 0.250 ms.
This supports retaining large-render performance within the chosen margin;
it does not pass the seven-win/0.25 ms screen for claiming a new large-render
throughput improvement. Actual second renders improve in all eight pairs,
with median paired wall saving 1.201833 ms. That is eight observations per
variant, not the 80-sample warmed throughput comparison. The median paired
saving in the mean of the first six renders is 0.935611 ms; the improvement is
not solely one render moving cost to another of those six. Its cause has not
been isolated.

Reports `deferred-ownership-small.json` and `deferred-ownership-large.json`
retain all samples, GC statistics, paired HTML digests and source/artifact
hashes. The ABI3 extension is unchanged. No tests or builds overlapped timing.
An unrelated background process was active at about 75% of one CPU when the
tiny run started and about 28% before the large run. It was left running and
no samples or pairs were excluded. Treat these as desktop comparisons under
normal background load, not measurements on an isolated machine.

The final repository gate passes all 19 phases in 126.689 seconds, with 88.75%
coverage. All 553 browser tests pass on the final source in 88.61 seconds.
Linux-target mypy passes 169 source files. The performance release note now
states that renders without nested component calls avoid native storage setup;
the preceding iteration retains the measured eager-allocation tradeoff in this
research history. This does not claim a new speedup for small nested trees,
which were not the tiny fixture measured here.

## Thirty-seventh iteration: capture body-builder values without closure cells

A fresh cProfile diagnostic records 342 calls to `_render_one` per large render,
with 3.023 ms instrumented self time. `ConstBodyCache.get_or_build` runs 340 times;
`RenderFrame.from_context` runs 1,015 times. These instrumented call costs locate
work to inspect. They are not ordinary render times, and cumulative rows overlap.
The complete diagnostic is `orchestration-profile.json` in the repeat-render
results directory, generated by `benchmarks/orchestration_probe/call_profile.py`.

The nested template-body builder captures seven outer bindings. Python allocates
those seven closure cells on every outer call, including cache hits and early
returns: 2,394 cells across the 342 calls. The experimental adapter gives the
builder seven default parameters, removing all outer closure cells while keeping
the referenced values, live module globals and existing zero-argument cache calls.
It still constructs a builder function and defaults tuple when execution reaches
the definition. It preserves both existing locks and cache lookup behavior.
The builder's internal introspection signature changes. This is an experiment,
not a qualified change to the ordinary runtime.

The plan and adapter live in `benchmarks/orchestration_probe/`. Independent source
review found no binding reassignment after the definition or timing fairness
blocker. Full fixture HTML and all four reached ownership snapshots match, and
activation checks confirm the candidate has no closure cells. Ordinary native
ownership storage is active for both variants.

The predeclared screen requires at least seven of eight fresh-process pairs to
improve both wall and CPU time, plus at least 0.25 ms median paired mean wall
saving. Each process performs six initial renders and 80 measured warm renders.
This is a practical acceptance rule, not a formal statistical confidence claim.
All observations and GC costs remain in the comparison; paired execution order
is balanced and randomized with seed 20261002.

The candidate fails both requirements. Six pairs improve both clocks. Median
paired mean savings are 0.046488 ms wall and 0.046550 ms CPU. The eight wall
savings are 0.265451, -0.756267, 0.050290, 0.943188, 0.040695, -0.099323,
0.305796 and 0.042686 ms. Median worker means are 31.091041 ms for closure
capture and 31.038678 ms for default capture. Actual second renders have four
wall wins and a median paired saving of 0.109209 ms, based on only eight
observations per variant. Neither result establishes a repeatable improvement
large enough for adoption under this plan.

`orchestration-defaults-large.json` retains all observations, initial renders,
GC statistics, HTML digests and source/artifact hashes. No builds or tests
overlapped timing. An unrelated background process used about 22.5% of one CPU
before timing and remained running. These are desktop measurements under
background load, with no pairs or samples removed. Python formatting and lint
checks pass for the probe. Production stays at `b11a895`; the full production
and browser checks recorded in iteration thirty-six still describe that code.
The candidate does not proceed to production qualification or smaller-fixture
timing. Removing these cells alone has not justified further work on this
particular representation; larger changes to repeated setup remain open.

Independent final technical review recomputed both clock aggregates and the
second-render result, checked all 23 manifest hashes and the common ABI3 artifact
in all 16 workers, and confirmed all paired initial/warm HTML digests match.
Every worker retained six initial and 80 measured observations with GC enabled.
The separate prose review found no required file corrections.

## Thirty-eighth iteration: run the attribute merge loop in Rust

The component setup inspection found that extension constructors are already
prepared once per exact component class. The fresh diagnostic attributes only
0.502 ms cumulative instrumented time to typed-input finalization across 342
calls. A broader next experiment therefore targets `_merge_resolved_attrs`:
505 calls, 0.916 ms self and 2.825 ms cumulative instrumented time. Earlier
merge-result caching changed current-input object identity, and caching name
positions did not establish a whole-render gain.

`benchmarks/native_attr_merge_probe/` implements an unpublished ABI3 extension
that performs the whole contribution loop in one call. It accepts exact lists
of exact two-item tuples with exact UTF-8-representable string keys. Unsupported
shapes, custom keys and lone surrogates return a sentinel before callbacks, so
the adapter can run the original Python merger. Native name grouping preserves
ASCII case folding and case-sensitive Citry directive prefixes. It builds a
fresh dict, retaining the current first key and last ordinary value objects.
Class and style contributions keep their original values and run the existing
Python normalizers in class-then-style order. Looking up the style helper after
the class callback preserves a callback's replacement of that helper.

The adapter uses explicit identity checks for the three name-identity helpers.
Independent review found that the initial tuple equality guard could accept a
replacement callable's custom equality; the final guard and retained
counterexample fix that before timing. Preinstalled replacements, mutation
inside helper functions or their translation table, concurrency and finalizer
timing remain unqualified. No cross-render values are retained. This experiment
leaves expression resolution, spread validation, extension hooks, filtering and
final formatting in their existing paths. It adds no production API or binding.

The bounded check passes 2,000 seeded ordered outcome comparisons, including
error types/messages, structured class/style values and case variants. It also
checks current key/value identity, seven unsupported shapes/iterators/surrogate
cases, live style-helper replacement and an identity-helper callable that
claims equality with everything. Full fixture HTML and all four ownership
snapshots match. A separate untimed activation render reaches 505 native
successes and zero native unsupported-input returns. That counter does not
include adapter fallbacks caused by changed helpers; fixture helpers are
unchanged. Python lint/format and Rust format/Clippy checks pass.

The eight fresh-process pairs fail the predeclared seven-joint-win/0.25 ms
median paired mean wall screen. Five pairs improve both clocks. Median paired
mean savings are 0.163087 ms wall and 0.142506 ms CPU. The wall savings are
0.221018, -0.279688, 0.211457, 0.228689, 0.114717, 0.593045, -0.832875 and
-0.122297 ms. Median worker means are 30.383031 ms reference and 30.211328 ms
candidate. Actual second renders have five wall wins and a median paired
saving of 0.3318125 ms, from only eight observations per variant. The warmed
comparison retains all 80 observations after six initial renders in every
process, normal GC and balanced randomized order with seed 20261003.

Reports `native-attr-merge-large.json` and `native-attr-merge-contracts.json`
retain the results. The timing report records Python/Rust source and lockfile
hashes, both loaded artifacts and paired HTML digests. The standalone release
artifact hash is `a5d5f45053bf50f4460ed709b4e68a0db9c6e96adb8090138aa6ea9aa532245f`.
No builds or tests overlapped timing. Ordinary desktop activity remained;
WindowServer used about 21.6% of one CPU and sysmond about 16.5% before timing.
No observations were removed.

Keep this implementation experimental and do not proceed to production or
small-fixture qualification. Moving the merge loop alone has not established
a large enough repeat-render gain. This result leaves combined resolution,
merging and formatting open; it does not establish a limit on a different,
larger native operation. Production remains the independently qualified code
at `b11a895`; this iteration introduces only research code and evidence.

Independent final review recomputed the reported results, verified all 30
manifest hashes and both artifacts across workers, and checked native activation
counts and paired HTML digests. Its separate prose pass found no file changes
required. The remaining semantic qualifications in the plan are still open;
this review approves archiving the experiment, not production adoption.

## Thirty-ninth iteration: compact native attribute-output cache keys

The output cache still builds one `(name, type, value)` tuple per attribute and
then an outer tuple on every lookup. The experiment in
`benchmarks/native_attrs_output_probe/` replaces that Python loop with one native
call returning a flat tuple of successive name/type/value triples. It retains
the current references, type distinctions, map order and existing admission
bounds. Misses reconstruct their input snapshot from those offsets and run the
original formatting, helper recheck, insertion lock and eviction. The previous
native contribution merger remains inactive; this targets a different stage.

The fixture reaches 495 admitted native keys and ten unsupported maps per
render. Those are admission counts, not cache hits. HTML and all four ownership
snapshots match. The checker compares 2,000 seeded keys, with reference identity
checked on all 950 admitted cases, plus 17 explicit boundary/unsupported cases.
All 19 output-cache tests pass under the adapter. Their copied source changes
only the concurrency test's private key offset and installs the adapter in
both the parent and the backend test's fresh interpreter. The report retains
original and adapted test-source hashes. Python lint/format and Rust
format/Clippy checks pass. Independent review found no blocker before timing;
mutation/lifetime and older-core behavior remain production qualification work.

All eight fresh-process pairs improve both clocks. Median paired mean savings
are 0.391992 ms wall and 0.391569 ms CPU, passing the predeclared seven-win and
0.25 ms screen. Wall savings are 1.055575, 0.816431, 0.443624, 0.446563,
0.160858, 0.189359, 0.340359 and 0.175361 ms. Median worker means are
31.079286 ms reference and
30.667383 ms candidate. Actual second renders have
4 wall wins and a median paired saving of -0.139000 ms, only eight
observations per variant. This establishes the planned warm-throughput screen,
not a demonstrated second-render improvement.

`native-attrs-output-large.json` retains all observations, initial renders, GC
statistics, paired HTML digests and source/artifact hashes;
`native-attrs-output-contracts.json` records bounded validation. Every process
keeps six initial and 80 measured warm renders with normal GC; order is balanced
and randomized with seed 20261004. No builds or tests overlap timing. Desktop
activity remains: WindowServer used about 20% of one CPU before the run. No
observations were removed. Production qualification will replace the AST
experiment with ordinary source and the packaged binding, then measure that
actual implementation against the archived original formatter.

## Fortieth iteration: packaged compact keys fail the final performance screen

The candidate was moved into ordinary typed source and the regular ABI3
extension. `_rust.attrs.output_cache_key` and its private wrapper returned the
flat key, with a Python builder selected when the capability was absent.
The formatter kept one private key shape and reconstructed its miss snapshot
from successive triples. The archived patch includes the binding, registration,
stub, wrapper, runtime, tests and package pointers. Parser/compiler contracts
were unchanged because these keys contain Python types and values.

Nineteen core tests cover admission, bounds, Unicode/surrogates, signed integers,
retained references, ordering and unsupported protocols. The runtime cache
suite runs with both native and Python builders; together the focused checks
pass 59 tests. A fresh subprocess explicitly selects and executes the Python
builder with the native capability removed. Another fresh process loads the
actual preceding ABI3 binary, verifies that capability is absent, executes the
fallback and renders changed values correctly. The full repository gate passes
all 19 phases in 116.264 seconds with 88.74% coverage. Browser tests pass all
553 cases in 83.17 seconds. Linux-target mypy passes 536 source files.

Despite those behavioral checks, the packaged large-fixture comparison fails
the predeclared seven-joint-win/0.25 ms screen: three pairs improve both clocks,
with median paired mean savings -0.035789 ms wall and -0.016650 ms CPU.
Wall savings are -0.691445, -0.545359, 0.244940, -0.138906, -0.062783,
0.590208, -0.008794 and 0.096235 ms. Median worker means are 31.347133 ms
reference and 31.454288 ms candidate. Actual second renders have two wall
wins and a median saving of -0.227041 ms from eight observations per variant.
The positive standalone result therefore does not support adopting this
ordinary packaged implementation.

The tiny native comparison stays within its 0.005 ms regression margin.
Median paired mean savings are 0.004923 ms wall and 0.004806 ms CPU, with six
joint wins. Actual second renders have three wall wins and a median saving
of -0.007896 ms. The Python fallback exceeds its separately declared 0.10 ms
large-fixture regression limit: median paired mean savings -0.170350 ms wall
and -0.170631 ms CPU, with two joint wins. Its actual second-render median
saving is -0.049209 ms, with four wall wins. Keep these signed results separate
from the earlier prototype; do not pool different implementations to obtain
a passing adoption result.

The final three comparisons retain all eight process pairs, six initial and
80 measured warm renders per process, normal GC, paired HTML and source/artifact
hashes. Their seeds are 20261005, 20261006 and 20261007. No builds or tests overlap
timing. Ordinary desktop activity remains; WindowServer used about 18.9% of
one CPU before the first run. No observations were excluded. All fixture HTML
and reached ownership snapshots match. The native large fixture admits 495
keys and rejects ten maps at the key-building boundary, as in the prototype.

A post-comparison diagnostic counted 495 cache hits, zero misses and zero
miss-path string casts in one warmed fixture render. On the same 495 admitted
maps, standalone and packaged native builders returned equal keys and ran at
nearly the same isolated speed: median packaged-minus-standalone difference
-0.000234 ms wall and -0.000250 ms CPU per set of maps. This does not measure
complete rendering or explain the whole-render discrepancy. It rules out
miss-path casts for that diagnostic render and gives no evidence of a large
native-function slowdown from packaging. Process heap behavior and other
sources of variation remain unisolated. No whole-render retry was used to
seek a passing result.

The candidate is rejected. `benchmarks/attrs_output_qualification/candidate.patch`
retains its exact production changes, while `result.md` explains how to apply
and measure it in a separate checkout. Reports named `packaged-attrs-output-*`
retain behavior, performance and diagnostic evidence. The ordinary runtime
and its preceding ABI3 artifact are restored; production qualification is not
complete merely because tests pass. The next investigation should remove more
repeated work or evaluate a different representation, with its own evidence.

Independent final review verified the candidate patch against the staged diff,
all timing/diagnostic hashes before restoration, paired outputs and reported
arithmetic. Its separate prose pass found no required corrections in the
candidate code and reports. After restoration, production paths have no diff,
the original ABI3 hash matches, and 21 cache/benchmark tests pass in 0.90 seconds.
`git apply --check` confirms the archived patch applies to the restored source.


## Forty-first iteration: earlier attribute-output reuse misses the saving threshold

The experiment caches final attribute strings immediately after collecting
current contributions. This moves the lookup ahead of merge allocation,
class/style normalization, framework-key checks, filtering and the existing
output-cache key. Copies of the original method ASTs split collection from
finishing while retaining live module globals. Direct `_resolve` calls stay
unchanged, and every input expression still runs. Only bounded primitive
contributions qualify; ordered pairs retain duplicate names and output order.
The cache retains at most 256 keys and strings, with no component, context,
node or merged dict references. `benchmarks/attrs_pipeline_probe/plan.md`
records the scope and acceptance rule before timing.

The fixture matches full HTML and all four reached ownership snapshots. In
one separate untimed warm render, collection runs 505 times, the earlier cache
hits 430 times and finishing runs 75 times. There are 96 cache entries and no
misses among admitted lookups. These are fixture counts, not a general hit-rate
claim. Live checks guard node methods, merge/format/class/style helpers,
client-props helpers and applicable extension hooks. Storing requires
eligibility both before and after finishing. Independent review prompted
additional class/style helper guards before timing.

The checker exercises changing values and order, normalization and escaping,
once-per-render input callbacks, post-warm parser/class-collector replacement,
custom HTML values, repeated errors, node overrides, added hooks and cache
bounds. It also proves a production incompatibility: a component with custom
attribute access observes one `citry` read on an original cache miss and three
under the prototype. Eligibility reads state before the original merge and
again before insertion. The report explicitly marks production compatibility
false. Preinstalled overrides, helper-body/table mutation, callback mutation,
concurrency and compiler/node mutation remain unqualified. Successful fixture
checks do not resolve these gaps.

Seven of eight process pairs improve both wall and CPU time. Median paired
mean savings are 0.208557 ms wall and 0.207913 ms CPU. Wall savings by pair are
0.320458, -0.464628, 0.088840, 0.247856, 0.169258, 0.769538, 0.936008 and
0.119038 ms. This passes the seven-win condition but misses the separately
required 0.25 ms minimum saving. The candidate is rejected without a retry.
The rule is a practical screening decision, not a statistical confidence bound
or proof that the candidate has no effect.

Median worker means are 30.193689 ms reference and 30.276790 ms candidate.
Those separate medians do not preserve pairing and should not be subtracted
to obtain the paired statistic above. Actual second renders have six wall wins
and a median paired saving of 0.606042 ms, from only eight observations per
variant. This sparse second-render result does not override the declared
warm-throughput screen or the known correctness failure.

`attrs-pipeline-large.json` retains all eight fresh-process pairs, six initial
and 80 measured warm renders per process, normal GC, HTML digests and source/
artifact hashes. Process order is balanced and randomized with seed 20261008.
No agent builds or tests overlap timing, and no observations are excluded.
`attrs-pipeline-contracts.json` retains the bounded checks and the getter
counterexample. Python lint and formatting pass. Production source and the
original ABI3 artifact remain unchanged throughout this experiment.

Skipping hundreds of merge/format paths yields only a small net benefit with
these guards included. This does not isolate guard cost, nor establish that
all earlier caching designs fail. A materially different design would need
its own measurement and must preserve observable state reads before adoption.

Independent final review verified all 27 source/artifact hashes, paired
outputs, sample counts and reported arithmetic. Its separate prose pass found
no required corrections in the experiment files or this research entry.


## Forty-second iteration: native deferred discovery adds more checking than it saves

The retained orchestration profile attributes about 1.508 ms instrumented
cumulative time to `_scan_deferred`, with 1,020 parts-list visits across 343
scans. The scanner finds children after component body construction, produces
current list/index/context positions and appends dependency-merge tasks after
foreign-context descendants. Collecting that work during body construction
could avoid this scan, but public edits to `CitryRender.parts` would require
invalidation or revalidation. This experiment first measures moving the
existing discovery traversal into one native call per scan.

`benchmarks/native_deferred_scan_probe/plan.md` records the design and decision
before timing. Its standalone PyO3 extension uses an explicit stack over exact
lists, strings, Markup, placeholders, renders and physical wrappers. It creates
the existing Python task types and retains current Python references. It
preserves duplicate occurrences, task order and lexical context identity,
including the existing behavior that a wrapped deferred component is ignored
by this scanner. Nested physical render wrappers use the innermost render's
current parts and context. Unsupported objects/subclasses, non-list parts and
nesting or wrapper chains exceeding 256 steps use the original scanner.
This does not repair malformed cycles; wrapper-only cycles retain the original
nonterminating unwrap behavior on fallback.

The adapter guards class MRO identities, getters, slot descriptors, task
constructors, scanner/unwrap helpers and the wrapper base. These checks keep
supported post-import replacements on the original path. Preinstalled changes,
tracing callbacks, concurrent mutation and allocation-finalizer behavior remain
unqualified. The extension is an experiment, not a production-compatible
replacement. No parser, compiler, language implementation, public binding,
production Python source or regular native artifact changes.

The checker compares 1,000 generated trees before and after reversing their
root parts, checking the types, order and retained identities of 10,222 tasks
across 2,000 comparisons. Explicit checks cover wrapped deferreds, nested
wrappers with different mirrored outer slots, subclass/non-list/depth fallback,
changed getters, `__class__` spoofing through a getter, wrapper-base rebinding
and a replaced task constructor on an unsupported tree. The constructor must
run once through fallback, without speculative native calls. Nine existing
`test_deferred_render.py` tests pass with the adapter installed in 0.18 seconds.
Full fixture HTML and all four reached ownership snapshots match. A separate
untimed render confirms 343 native scans and zero fallbacks. Rust formatting
and Clippy pass, as do Python lint and formatting.

The performance screen fails: only one of eight process pairs improves both
clocks. Median paired reductions in process mean render time are -0.929536 ms
wall and -0.929562 ms CPU. Wall savings by pair are -0.806545, -0.732791,
-2.229512, -0.679255, 0.291388, -1.145750, -1.448409 and -1.052528 ms.
Median worker means are 30.441001 ms reference and 31.544366 ms candidate.
Actual second renders have two wall wins and a median paired saving of
-1.063938 ms from eight observations per variant. The candidate is rejected.

`native-deferred-scan-large.json` retains all eight fresh-process pairs, six
initial and 80 measured warm renders per process, normal GC, paired outputs,
and 30 source/artifact hashes. Process order is balanced and randomized with
seed 20261009. No agent builds or tests overlap timing; no observations are
excluded. `native-deferred-scan-contracts.json` records the bounded checks.

A separate short diagnostic times admission checks and native traversal during
ten alternating pairs of renders in one process, after six initial renders.
All calls use current trees, with 343 scans per render. Median instrumented
costs per page are 0.475771 ms for the original scanner, 0.743961 ms for the
candidate's guard checks and 0.379105 ms for its native scanner. Timers and an
extra function containing the extracted guard expression add overhead. These
figures must not be treated as whole-render savings or added to explain the
entire measured regression. They suggest that guard overhead is substantial,
while native traversal itself has modest headroom over the current Python
scanner. Moving only the guards into Rust would still need new evidence.

`native-deferred-scan-diagnostic.json` retains every diagnostic observation.
Its `source_archives` mapping points to the exact measured script; the runnable
script subsequently binds its loop counters explicitly and follows formatting
rules. No diagnostic observation was discarded or replaced, and the measured
adapter and native source remain unchanged. This investigation does not justify
changing the tree representation solely to remove deferred discovery. A different
representation would need its own measurement, including the cost of preserving
public parts-list mutation.

Independent final review verified the 30 main and four diagnostic hashes,
paired statistics and diagnostic call counts. The measured diagnostic source
matches its archive. Its prose correction limits the representation conclusion
to what this experiment establishes.


## Forty-third iteration: smaller ownership scope objects do not improve throughput enough

Four ownership factories currently create generator context managers:
`active_region`, `active_invocation_region`, `select_supply` and `slot_site`.
The generator holds entry arguments and cleanup state; contextlib adds a
wrapper that drives it. This experiment replaces each pair with one small
scope object using slots. It preserves the `_SlotSite` and `_SelectedSupply`
payload dataclasses and accesses the ownership module's live globals. It does
not add a per-call compatibility scan or change native code.

`benchmarks/ownership_scope_probe/plan.md` records the design and acceptance
rule before timing. The prototype looks up invocation parents on entry,
continues to call the graph's live `active_region` override, restores context
variable tokens on ordinary exit and supports recreation for decorators.
Factory counts in a separate untimed fixture render are 675 active-region,
eight invocation-region, 194 selected-supply and 274 slot-site scopes: 1,151
scope constructions in total. This is a count of replaced factory calls, not a
measurement of every allocation made while entering and exiting those scopes.

The fixture matches full HTML and all four reached ownership snapshots.
193 existing ownership and slot tests pass with the adapter installed in
0.81 seconds. The focused checker covers nested graph restoration, body
exception identity including StopIteration and BaseException, decorator reuse,
copied-context payload identity, changed invocation parents before entry,
delegated exception suppression, slot-site owner lookup and completed-manager
reference release. Python lint and formatting pass.

Three counterexamples explicitly prevent production adoption. First, dropping
a manually entered original manager restores its context variable through
generator finalization; the prototype leaves it active. Second, a new
StopIteration raised by a slot entry callback becomes RuntimeError under the
original generator but propagates as StopIteration under the class scope.
Third, a slot source retained only by the manager stays alive through the
original with-block but can be collected before the prototype's body runs.
The latter difference occurs even during normal context-manager use. Review
identified the callback and lifetime gaps; the checker reproduces all three
and marks production compatibility false. Malformed protocol calls, unusual
delegated descriptors and exact traceback behavior remain unqualified as well.

The whole-render screen fails. Five of eight process pairs improve both
clocks, with median paired reductions in process mean render time of
0.017660 ms wall and 0.018019 ms CPU. Wall savings by pair are -0.884018,
0.345001, -0.040261, 0.015390, 0.208396, -0.119492, 0.019930 and 0.372327 ms.
Median worker means are 30.453345 ms reference and 30.448095 ms candidate.
Actual second renders have three wall wins and a median paired saving of
-0.381771 ms from eight observations per variant. These results miss both the
seven-joint-win condition and the 0.25 ms minimum saving. Reject this candidate;
its known compatibility differences do not warrant production qualification
on the strength of these measurements.

`ownership-scope-large.json` retains all eight balanced randomized fresh-process
pairs, six initial and 80 measured warm renders per process, normal GC, paired
HTML and 28 source/artifact hashes. The order seed is 20261010. No agent builds
or tests overlap timing, and no observations are excluded.
`ownership-scope-contracts.json` records focused checks and counterexamples.
Production source and the regular native artifact remain unchanged.

Reducing the number of temporary scope objects is not sufficient evidence of
a whole-render improvement. This experiment also preserves the payload objects
and token operations, so it does not test eliminating ownership scope work
altogether. A future change must be evaluated on its own behavior and measured
cost, including any cleanup and lifetime guarantees it preserves.

Independent final review verified all 28 hashes, paired outputs, scope
counts and warm/second-render statistics. It checked the three executable
compatibility counterexamples. Its separate prose pass found no remaining
substantive correction.


## Forty-fourth iteration: compiling the ownership module gives a small consistent gain

Compiling the complete ownership module improves every measured process pair,
but the gain does not justify adding a compiler and another native distribution
path. The median paired reduction in mean warm-render time is 0.445213 ms wall
and 0.444869 ms CPU. The experiment meets its consistency condition of seven
joint wall/CPU wins, with eight wins, but misses its separately declared 1.0 ms
minimum saving. Keep the experiment as research; production remains unchanged.

`benchmarks/ownership_module_probe/plan.md` records the decision rule before
timing. Unlike iteration eight's four isolated compiled functions, this probe
compiles the exact complete `citry.ownership` source, covering capture, record
construction, scopes, bindings and updates. It retains Python objects and
dynamic operations without introducing native field types. The generated module
loads under its real package name before Citry imports, so callers import its
classes and functions through the ordinary package path. A fresh worker loads
either that extension or the original Python module; neither variant reloads an
already-imported module.

Cython 3.3.0 and setuptools 84.0.0 run from a separate temporary tools directory.
The probe disables annotation typing and type inference and enables binding.
These options limit intentional changes to existing annotations and method
binding; they do not prove Python semantic equivalence. Build and import time
are outside repeated-render timing. The production Python source and ordinary
Rust ABI3 binary are unchanged. The compiler's generated-C and artifact hashes,
source hash, directives, interpreter and build output are retained in
`ownership-module-build.json`. The compiled extension SHA-256 is
`1cf06fbe20973f9564e8a1fdd34a350942ac4a84c952508d0c5ec57f5125c91c`.

The existing ownership suite passes all 134 tests under the compiled module in
0.71 seconds. A fresh-process smoke comparison matches HTML and all four
reached ownership snapshots. Snapshot comparison includes record types, field
names, values and sequence order. It does not prove object identity or arbitrary
callback behavior. Workers check the actual extension loader, module path and
compiled method type. A separate untimed render replaces the live source-record
method and observes 1,081 calls, establishing replacement lookup for that method
on this fixture. It does not establish compatibility for every callback or
module-global replacement. Python lint and formatting pass.

`ownership-module-large.json` retains eight balanced randomized fresh-process
pairs, six initial and 80 measured warm renders per process, normal GC, paired
HTML, all four snapshot digests, activation counts and eight source hashes.
The report also embeds the build evidence. The order seed is 20261011. No agent
builds or tests overlap timing, and no samples are excluded. Wall savings by
pair are 0.371621, 0.443889, 0.403976, 0.511116, 0.303078, 0.665594, 0.446538 and
0.633902 ms. Median worker means are 30.232270 ms reference and 29.679566 ms
candidate; those separate medians are not the paired improvement statistic.
Actual second renders have seven wall wins and a median paired saving of
0.680771 ms, from eight observations per variant. The one-sample smoke report
is qualification evidence, not a performance estimate.

This result supports a limited conclusion: compiling this larger ownership unit
can reduce interpreter overhead, but the measured saving is small compared with
the remaining gap to Django. It does not test a redesigned ownership data model,
elimination of repeated recording or a Rust implementation with native field
types. Since the experiment misses its declared benefit requirement, further
qualification of callbacks, errors, object lifetime, introspection and supported
interpreters is deferred. No new runtime dependency or release change follows
from this experiment.


### Production breakdown after this experiment

A fresh run of the unchanged `benchmarks/render_breakdown.py` measures ordinary
production, with the Python ownership module and regular Rust artifact.
`round44-breakdown.json` retains 30 ordinary and ten instrumented renders after
six warmups, with equal HTML and source/artifact hashes. The ordinary medians
are 29.554980 ms total, 25.996667 ms tree building and 3.542480 ms final
serialization. Separate medians need not sum to the total median.

| Work inside tree building | Instrumented ms | Share |
|---|---:|---:|
| Component setup and orchestration | 8.590 | 27.3% |
| Ownership tracking | 5.787 | 18.4% |
| Child inputs and slots | 4.900 | 15.6% |
| Element attributes | 3.514 | 11.2% |
| Body traversal, expressions and control flow | 2.648 | 8.4% |
| Extension hooks and configuration allocation | 2.487 | 7.9% |
| Nested serialization | 1.370 | 4.4% |
| Template and reusable-body cache work | 1.282 | 4.1% |
| Application data callbacks | 0.891 | 2.8% |

The instrumented tree mean is 31.468646 ms. These shares use nested timers
with timed descendants subtracted and remaining outer time assigned to
orchestration. Timer overhead changes costs, so they describe an instrumented
run and cannot be scaled directly into ordinary wall-time savings. The final
root serialization is outside this table; nested serialization occurs while
building the tree and is included. This measurement refreshes the breakdown
without claiming a new production improvement or a fresh comparison to Django.

Independent final review verified the compiled-module experiment's eight source
hashes, build provenance, paired outputs and warm/second-render statistics.
Its separate prose pass required the delivery to distinguish a median paired
reduction in process means from a saving on every individual render.


`round44-call-profile.json` retains a separate 20-render cProfile diagnostic
after six warmups, with the interpreter, revision, regular native hash and all
Python runtime source hashes. It records 57,736 isinstance calls per render.
The largest Python self-time rows are `_render_one`, `_render_body` and
`record_source_location`. These instrumented call counts identify places to
inspect; cumulative times overlap, and the profiler changes costs. They do not
establish that deleting a particular check is compatible or profitable.


## Forty-fifth iteration: deferred source-record creation misses the consistency screen

The source-occurrence table still creates a Python record on every capture,
while other ownership tables can retain fields in the existing native storage
and create a record when read. This experiment applies that same storage to
source occurrences. It uses the current release ABI3 extension without changing
Rust code or adding a dependency. Earlier source-site caching experiments
changed shared metadata; this experiment changes when occurrence objects are
created. The prior body-unrolling experiment in `performance.md` reported a small
apparent saving within noise, so this iteration did not repeat that experiment.

`benchmarks/source_record_storage_probe/plan.md` declares the design and screen.
The AST adapter adds an eight-field source table to the first nested-invocation
conversion, keeps already-created prefix records by identity and appends later
field tuples. Source preparation, UTF-8 validation, IDs, order and mapping
values stay live. Root-only graphs retain Python lists. Reads export and cache
ordinary `SourceLocationRecord` objects; replay rollback can restore a list,
which subsequent captures handle. The candidate checks the live record class
and its `__new__` method before choosing field append.

The full-render comparison has six joint wall/CPU wins from eight process
pairs. Median paired reductions in process mean warm-render time are
0.416398 ms wall and 0.416394 ms CPU. Wall savings by pair are 0.580206,
0.560162, 0.355363, -0.522677, 0.155133, 0.477433, -0.887683 and 0.609813 ms.
The median improvement exceeds the 0.25 ms condition, but the six wins miss
the separately declared seven-joint-win requirement. Reject this candidate
rather than retrying to seek acceptance. Median worker means are 30.510667 ms
reference and 30.582282 ms candidate; separate medians do not measure the
paired improvement. Actual second renders have four wall wins and a median
paired saving of -0.072104 ms, from eight observations per variant.

`source-record-storage-large.json` retains all eight balanced randomized
fresh-process pairs, six initial and 80 measured warm renders per process,
normal GC and 28 source/artifact hashes. The seed is 20261012. All timed and
initial HTML matches across each pair. Each pair also matches four
canonical ownership snapshots and HTML in separate untimed renders. Candidate
workers verify native RecordTable storage and record 1,081 source rows; reference
workers verify list storage. No agent builds or tests overlap timing, and no
observations are excluded.
The one-sample smoke report is qualification evidence only. Its `source_archives`
mapping retains the exact measured plan before a prose correction clarified
that the guard checks `__new__`, not the whole construction protocol. Runtime
code is identical between smoke and main timing.

All 134 existing ownership tests pass under the adapter in 0.63 seconds,
covering both installed native storage and the older-core Python fallback.
The focused checker verifies prefix identity, repeated export and snapshot
identity, shared sites, UTF-8 errors without counter advancement, a constructor
changed before entry, replay rollback identity, append after rollback and GC
of a cycle through a stored field. It also reproduces a compatibility failure:
a graph's `_next_order` override can change the record's `__new__` while
constructor arguments are evaluated. The current eager path invokes that
changed constructor; this candidate misses it because its guard ran earlier.
The report explicitly marks production compatibility false. Changes to other
constructor behavior, private-container mutation, arbitrary class changes and
reentrant callbacks/destructors remain unqualified. Python lint and formatting
pass. Production source and the regular native artifact remain unchanged.

### Where deferred source records become necessary again

The separate untimed reader diagnostic counts 1,081 capture calls. Four rows
already exist when the first nested invocation activates native storage, and
all remaining 1,077 rows are exported by `snapshot()`. No source-record
construction is ultimately eliminated on this fixture. The representation
moves creation later and changes the construction path; the counts alone do
not identify the cause of the measured timing difference. Each native row also
retains field references after exporting its cached Python record; lower memory
use was not established. The four snapshots in each measured worker's activation render have equal complete digests.
`source-record-storage-readers.json` retains counts, reader names and its three
source hashes; `source-record-storage-contracts.json` retains focused results.

This points to the reader contracts as part of any larger storage redesign.
The manifest builder omits source provenance from the production wire format,
but still checks that referenced source IDs exist. Its unchanged-graph guard
also compares complete snapshots after delayed work. Those checks cannot be
silently removed just because the browser does not receive source text.
A narrower internal read or a native check could avoid some record exports,
but would need to preserve dangling-reference errors, graph mutation detection,
public snapshot behavior and callback semantics. Merely making the existing
source table lazy does not establish that larger optimization.


## Forty-sixth iteration: internal source-field snapshots remove exports but not enough work

Changing the source collector and its snapshot readers together removes the
1,077 deferred public-record exports on the large fixture's production path.
The whole-render saving remains small: the median paired reduction in process
mean warm-render time is 0.116668 ms wall and 0.120556 ms CPU, with six joint
wins from eight comparisons. It misses both the declared seven-win condition
and the 0.25 ms minimum saving. Reject this candidate without retrying the
screen. The known compatibility differences described below also prevent
adoption as implemented.

`benchmarks/source_snapshot_probe/plan.md` records the broader design. An
isolated native `SourceTable` retains each eight-field tuple, an optional
public record and a cached immutable tuple of all source rows. Append and
replacement invalidate the current raw snapshot while existing captures keep
their old values. A private `SourceView` provides an ordered source sequence
for internal manifest captures. Two such views compare complete field values;
comparison with a public source tuple materializes records. Public graph
snapshots continue to return ordinary immutable records. The first nested
invocation still activates storage and preserves the already-created prefix.

The manifest adapter validates referenced source IDs directly from the field
view, preserving the ordinary dangling-reference error on normal records.
Production wire output omits source provenance while retaining every source
value in the internal capture for later unchanged-graph checks. Development
provenance selection walks the source view and materializes the rows it visits.
The Events reader also uses an internal snapshot because it needs logical
instances rather than source records. Other ownership tables, retirement,
rendering and the shipped native artifact remain unchanged.

The new standalone crate uses pinned PyO3 0.27.1 with abi3-py310. It neither
changes the shared parser/compiler contract nor adds a shipping dependency.
The source append adapter retains the live append method and record class,
evaluates arguments in the original order, then checks the captured class's
`__new__` and `__init__`. This handles the previous experiment's demonstrated
constructor change inside `_next_order`. Source values remain Python objects;
there is no new integer narrowing or packed byte format.

### Measurements and retained evidence

Wall savings by process pair are 0.056999, 0.299828, -0.051923, 0.225829,
-0.548808, 0.176336, 0.023225 and 1.032605 ms. Median worker means are
30.125668 ms reference and 30.376227 ms candidate; these separate medians are
not the paired improvement statistic. Actual second renders have three wall
wins and a median paired saving of -0.904605 ms from eight observations per
variant. No observations are excluded.

`source-snapshot-large.json` retains all eight balanced randomized fresh-process
pairs, six initial and 80 measured warm renders per process, ordinary GC and
40 source/artifact hashes. The order seed is 20261013. All initial and measured
HTML matches within each pair. Separate untimed renders compare complete
canonical ownership snapshots, including the source records represented by
internal views. Both production and development modes match HTML and all four
reached snapshots. Candidate activation asserts SourceTable and SourceView;
reference activation asserts list and tuple storage. Both report 1,081 rows.
No agent builds or tests overlap timing.

The same untimed diagnostic observes four cached prefix records and zero
SourceView exports during the candidate's production render. Development
materializes 1,077 records through SourceView. Canonical comparison deliberately
materializes complete values after the observed render, with its export counter
restored, so that verification work is excluded from the reported render counts.
The candidate still allocates one plain field tuple for each deferred occurrence.
Removing public records therefore does not remove all per-occurrence row
allocations, and lower retained memory was not established. These counts show
what work remains; they do not isolate the cause of the timing result.

The smoke report retains all observations and its 37 original hashes. Its
`source_archives` mapping points to the exact pre-correction plan, adapter,
checker and probe text. Before main timing, the harness gained explicit
activation assertions, probe dependencies were added to provenance, and prose
and checker-template formatting were corrected. Runtime activation and output
equivalence were checked again before the main run. The standalone artifact's
SHA-256 is `239f21f2f664dd9c0497c2fa358bf3d1a3031697c783d47f31f67b4530d856e7`;
the regular extension retains `321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.

### Correctness checks and concrete limits

All 168 existing ownership and manifest tests pass under the adapter in
0.93 seconds, including the installed-core and Python fallback paths. Focused
checks retain prefix/public export identity, shared sites, invalid UTF-8 errors,
GC cycles, replay rollback, append after rollback and changed constructors.
Additional checks cover equality and hashing against public snapshots, immutable
captures across append and replacement, a simple public snapshot override,
dangling-ID rejection and post-capture source mutation detection. Rust build,
formatting and Clippy pass; Python lint and formatting pass. The retained
contracts report marks production qualification incomplete.

`source-snapshot-counterexamples.json` preserves two differences that the
passing tests do not cover. First, an internal view and a public graph snapshot
can return equal but distinct record objects. Public graph reads retain their
own cached identity, but internal/public identity is not preserved. Second,
changing `SourceLocationRecord.id` after rendering to report a different value
causes the reference serializer to reject a dangling source reference; this
candidate reads the original field directly and succeeds. This bypass of the
changed descriptor prevents shipping the candidate as-is. Source-ID hash and
equality callback order, arbitrary record-class changes and private mutations
also remain unqualified. Inspecting a public snapshot override can read
`graph.snapshot` twice, so the simple lambda override check does not prove
arbitrary descriptor or `__getattribute__` callback equivalence.

This result narrows the next search. Eliminating public exports while retaining
per-occurrence field tuples, Python capture checks and internal snapshot wrappers
does not provide enough benefit in this implementation. It does not establish
a ceiling for native capture with a different representation or larger groups
of operations. Production source and release behavior remain unchanged.


## Forty-seventh iteration: consolidate experiments and refresh the comparison

The user's requested one-sentence experiment ledger and cumulative timeline are
in [performance_render_experiment_summary.md](performance_render_experiment_summary.md).
The ledger distinguishes adopted changes, rejected prototypes, and successive
qualification of the same native combination. Its local savings are not summed.
`benchmarks/performance_render_timeline.py` derives the timeline from nine retained
five-round comparisons, using the contemporaneous original-branch measurement
as each checkpoint's denominator. Its x-axis is research iteration, not hours.

A fresh comparison at research HEAD `e0c77ad1`, with unchanged production runtime
from `b11a895`, measures 39.609292 ms original Citry and 30.146563 ms current Citry
large warm medians: 23.8902% less time. Django measures 11.206021 ms, so Citry
takes 2.6902 times its time. Actual second-render medians are 42.157958,
34.521959 and 11.512542 ms respectively; the Citry reduction is 18.1128%.
Those second-render figures have only five observations per variant. Tiny warm
medians are 0.1192085 ms original, 0.1050420 ms current and 0.0197705 ms Django.
The raw observations remain authoritative for all rounded figures.

Both Citry checkouts load the current ABI3 artifact with SHA
`321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.
The original checkout's version-specific native filename temporarily holds that
binary; its previous bytes are restored and their hash verified in a finally
block. An earlier invocation rejected mismatched binaries and wrote no report.
The successful comparison retains all five fresh rounds and 20 warm samples
per worker after six renders, with ordinary GC and no concurrent agent builds
or tests. Citry and Django retain their different scenario output and features,
including 1,013,746 versus 456,422 output bytes for the large page.

`round47-comparison.json` retains observations and scenario/native hashes;
`round47-comparison-provenance.json` records the source revision, runner hash and
artifact handling. This refresh measures cumulative production progress; it
establishes no new optimization since iteration 36. The next experiment gives
the ownership collector's Python-object fields native offsets throughout the
class, following the grouped-capture question; its plan and build are isolated
in `benchmarks/ownership_layout_probe/`.


## Forty-eighth iteration: native field offsets throughout ownership capture

The compiled candidate gives OwnershipGraph's 30 fields fixed native offsets
while retaining Python objects as their values. Its 43 method bodies match the
original ASTs. The rest of ownership.py is also compiled, as in iteration 44;
this measures the whole compilation/layout combination against production,
not an incremental comparison with that earlier compiled module. Generated C
confirms direct accesses to the collector fields. Counters remain Python
integers and the ordinary native ownership tables stay active.

The plan, builder, import adapter, timing runner and focused checker are in
`benchmarks/ownership_layout_probe/`. Cython 3.3.0 and setuptools 84.0.0 build
only the temporary source under `/tmp/citry-ownership-layout`. The extension
loads under the real `citry.ownership` name before any Citry imports; its SHA is
`633eb0ccb8d86e6b433a3318999ba9f8e41e1d0241629d1c2c71979368cb2e67`.
The regular ABI3 artifact and production source remain unchanged. The build
report retains original/transformed source, generated C and setup hashes,
compiler output, directives, declared fields and interpreter details.

Eight balanced randomized fresh-process pairs retain six initial renders and
80 warm renders per process with ordinary GC. Seven pairs improve both wall
and CPU time. The median paired reduction in process mean time is 0.743333 ms
wall and 0.742994 ms CPU. Wall savings are 0.814510, 0.368201, -0.830730,
0.443944, 0.894959, 0.672155, 0.954944 and 1.032742 ms; all remain included.
Median worker means are 30.412140 ms reference and 29.877367 ms candidate;
the difference between these medians is not the median paired reduction.
Actual second renders improve in all eight pairs, with median savings of
0.791230 ms wall and 0.787000 ms CPU. Those are only eight observations per
variant, separate from warm throughput. No agent tests or builds overlap timing.

Every initial and warm HTML digest matches across its pair. After timing,
observers attached to the actual graph instances capture four complete canonical
snapshots and count 1,081 source-record calls per worker; those snapshots and
HTML match too. The extension class is immutable, so untimed instrumentation
wraps the existing render scope and assigns instance methods. Timed workers
retain the original scope and methods. Layout checks confirm all 30 native
field descriptors, a dynamic dictionary and weak-reference support.

The existing ownership/manifest selection passes 168 tests in 1.03 seconds.
A further storage selection passes 24 and fails two tests. Both failures are
`test_stable_component_id_getter_replay_keeps_binding_visible`, under Python and
native storage: its ID getter detects bind_instance through the caller's Python
frame, which compiled execution does not provide. The replay trigger therefore
never runs. These failures are retained; they do not qualify replay during that
callback, and the production tests are unchanged.

Focused checks preserve arbitrary-precision orders, instance method overrides,
UTF-8 source fields, retained record identity, replay rollback and collection
of a cycle through a stored field. They also reproduce several differences:
class method assignment raises, vars(graph) omits the 30 declared fields,
writing `_order` through the dictionary leaves the native field unchanged,
compiled methods bypass a subclass's `_order` property, and the compiled scope
constructor bypasses module-level replacement of OwnershipGraph. Uninitialized
field behavior, wider introspection, concurrency and supported distributions
remain unqualified. These are limitations of the measured representation,
not proposed changes to the public runtime contract.

Reject this implementation. It passes the seven-pair consistency screen but
misses the predeclared 1 ms requirement for adding a Cython distribution path,
and it has concrete compatibility differences. The 0.743 ms saving cannot be
added to or subtracted from iteration 44's unrelated run to attribute field
layout alone. It also does not establish a memory reduction or a limit on a
larger design that removes capture operations themselves.

Reports are `ownership-layout-{build,contracts,smoke,large}.json` and
`ownership-layout-{tests,storage-tests}.txt`. Eight main source hashes match;
the earlier smoke's eight hashes resolve through two exact source archives for
its pre-format runner and pre-clarification plan. The smoke is activation
evidence only. Python lint and formatting pass. Production continues to use
the runtime qualified in iteration 36, with the fresh cumulative measurement
in iteration 47; no full production gate is rerun for this rejected prototype. A fresh ordinary-runtime
run passes all 194 ownership, manifest and storage tests in 1.21 seconds, including
the two cases that failed under Cython; its report is
`round48-production-ownership-tests.txt`.


## Research mode change: larger scope and architectural experiments

**Starts at iteration 49, after commit `1805e15` (2026-09-09).** The user
explicitly directed: "move towards experimenting with larger scope / even
architectural changes", having run enough small-scale optimizations. Future
experiments should prioritize changes spanning rendering stages, execution
models, data representations, relationships, or deferred work. Small local
changes remain useful when needed to make a larger experiment correct; they
are no longer the default search strategy.

The performance anchor at this transition is iteration 47's fresh cumulative
large comparison: 30.146563 ms current warm median versus 39.609292 ms original
Citry (23.8902% less time), with Django at 11.206021 ms. Production runtime is
still `b11a895`; iteration 48's rejected compiled collector adds no adopted gain.
This marker separates research approaches for later time-series analysis and
does not itself claim a performance improvement. Iteration 49 begins by
compiling the complete component-render, node and slot modules together.


## Forty-ninth iteration: compile three rendering modules together

This is the first experiment in the broader research mode marked above.
The exact component_render.py, nodes/__init__.py and slots.py sources are compiled
as three complete modules using the isolated Cython tools. All classes remain
Python classes, with annotation typing and inference disabled. The finder loads
the three extension modules under their real package names before Citry imports;
ordinary node submodule discovery remains available. Ownership and the regular
Rust ABI3 artifact remain unchanged. This expands substantially beyond iteration
8's four transaction functions and iterations 44/48's ownership-only compilation.

The eight fresh-process pairs all improve both clocks. Median paired reductions
in process mean warm render time are 2.149446 ms wall and 2.149594 ms CPU. The
wall savings are 2.110248, 1.452012, 2.661504, 2.188644, 2.409903, 2.084832,
3.057278 and 1.717538 ms. Each worker retains six initial and 80 warm renders,
ordinary GC, all samples, and balanced randomized variant order. No agent tests
or builds overlap timing. Median worker means are 30.331087 ms reference and
28.118015 ms candidate. Actual second renders improve in all eight pairs, with
median savings of 3.1167715 ms wall and 3.117000 ms CPU; those eight observations
per variant are separate from warmed throughput. Every initial/warm HTML digest and four separately
captured canonical snapshots match across pairs. Each worker verifies all three
module paths and entry-point types. This passes the predeclared seven-joint-win,
1 ms screen for further qualification; it is not an adopted production gain.

The expanded node, component-node, slot, fill, render, deferred, hook, ownership,
manifest, callback, Const, component-like and value-dispatch selection passes 623
tests and fails two in 3.63 seconds. Both failures are the ownership test that
requires the root component and graph to be released immediately after the last
render reference is deleted, under installed and Python storage. The earlier
selection attempt used an incorrect test filename and collected no tests; its
error report is retained separately. Production tests and source are unchanged.

A focused warmed two-component render reproduces the lifetime difference:
reference component/graph weakrefs clear immediately and a subsequent full
collection finds zero unreachable objects; candidate weakrefs remain live until
collection, which finds 89 objects. Its unreachable settlement scope contains
four compiled callbacks, each of which refers back to the scope, and the scope
also holds a CitryRender. The generated C's `_settle_render` closure struct
confirms it groups commit, requeue, settle, settle_in_invocation_region, root_result
and stack together. These callback/scope cycles retain the render tree until GC.
The counts describe this diagnostic, not allocation bytes or the general page.

The performance comparison includes ordinary GC, but does not force outstanding
collection work at the end of each worker into its measured samples. The proven
lifetime difference therefore matters even with all samples retained. Further
qualification must remove this cycle and measure the corrected implementation;
this result alone cannot justify shipping the compiled pipeline. Other callback,
replay, introspection, mutation, interpreter and distribution limits also remain.

The next architectural experiment replaces the settlement function's nested
callbacks with methods on an explicit render-local state object. That object can
own the pending task stack and current root without retaining its own bound
methods. This changes the settlement representation and aims to preserve its
error, hook and replacement order while avoiding the compiled closure cycle.
Its performance and complete compatibility remain unproven at this point.

The executable plan/build/adapter/timing/lifetime scripts are in
`benchmarks/render_modules_probe/`. Reports are
`render-modules-{build,smoke,large,lifetime}.json`, `render-modules-tests.txt` and
`render-modules-selection-error.txt`. Nine main source hashes match; the smoke's
nine hashes resolve through an exact runner archive preceding a docstring-only
correction. Build metadata retains all three source, generated-C and artifact
hashes, compiler output and directives. The lifetime report has its own two
script hashes and build provenance. Python lint and formatting pass. No adopted
runtime change or new cumulative Django comparison results from this iteration.


## Fiftieth iteration: explicit settlement state in the compiled pipeline

The corrected pipeline replaces five nested settlement callbacks with methods
on one ordinary slotted `_SettlementState` object. The state owns the existing
pending-task stack and current root result, without retaining bound methods.
A bounded AST transform changes 12 shared references inside those methods and
five references in the outer settlement function. Independent review inverted
the substitutions and recovered all five original callback ASTs and the outer
flow; every other module AST remains unchanged. Task ordering, replacement,
ownership retirement, error propagation and cache publication keep their
original operations. This is the next architectural experiment in the mode
introduced at iteration 49.

The temporary corrected component-render source is compiled alongside the same
complete node and slot sources in `/tmp/citry-settlement-state`. Build metadata
records original/copied source, transformation, generated C and artifact hashes.
The classes remain Python classes. The ordinary Python source and Rust ABI3
extension remain unchanged, and fresh candidate workers select all three modules
before Citry imports. This measures the complete corrected execution pipeline
against production, not the settlement state's incremental contribution alone.

The preceding 625-test selection now passes in 3.69 seconds, including both
immediate-lifetime tests that failed in iteration 49. The full non-browser Citry
selection passes 4,821 tests, with five skips, 553 browser tests deselected and
one expected failure, in 28.90 seconds. Loaded module paths and compiled entry
points are checked before/after that run. Existing tests that launch fresh
interpreters use their normal bootstrap; those children do not qualify the
compiled candidate. This is not a full repository or browser gate.

The warmed two-component lifetime diagnostic now finds immediate component and
graph release and zero cyclic garbage for both variants. A separate full large
benchmark diagnostic also finds no live graph among four snapshot observations
after the rendered string returns, before explicit GC. Each variant leaves the
same 265 unreachable objects with matching type counts; none are ownership
collectors or settlement scopes. Those collection counts describe these fixtures,
not allocated bytes or a general memory guarantee. The small smoke run is only
activation/equality evidence and briefly overlapped the small lifetime diagnostic.
No agent tests or builds overlap the main timing comparison.

All eight main process pairs improve both wall and CPU time. Median paired
reductions in process mean warm render time are 3.131560 ms wall and
3.131762 ms CPU. Wall savings are 3.300409, 3.035184, 3.181321, 3.240275,
2.436897, 3.121130, 3.141990 and 2.915533 ms. Median worker means are
30.531441 ms reference and 27.606539 ms candidate. The difference of these
medians is not the median paired reduction. Actual second renders improve in
all eight pairs, with median savings of 2.728417 ms wall and 2.727000 ms CPU;
these eight observations per variant remain separate from warmed throughput.

Each worker retains six initial and 80 warm renders with ordinary GC, balanced
randomized process order and all samples included. Every initial/warm HTML
digest and all four canonical ownership snapshots match across pairs. The
fixture emits 1,013,746 bytes. Activation requires the explicit settlement class
only in the candidate and all three intended compiled entry points. All ten
main source hashes and ten smoke source hashes match the retained files.
The ordinary ABI3 artifact remains common to both variants.

The corrected pipeline passes the predeclared seven-joint-win, 1 ms screen and
resolves the demonstrated closure-cycle defect. Advance it to broader execution
and distribution qualification; do not activate it in production yet. Supported
interpreters/platforms, browser behavior, packaging, introspection and compiler
semantics beyond these tests remain unqualified. In particular, compiled stack
frames and function inspection still differ from ordinary Python. The larger
saving justifies work on those questions but does not establish Django parity,
new cumulative adopted performance, or a sum with iteration 49's earlier result.

The plan, transform, build, adapter, timing and two lifetime scripts are in
`benchmarks/settlement_state_probe/`. Reports are
`settlement-state-{build,smoke,large,lifetime,large-lifetime}.json`,
`settlement-state-tests.txt` and `settlement-state-suite.txt`. Python lint and
formatting pass. This experiment and the mode-change marker are retained on the
isolated optimization branch; the production timeline remains at iteration 47.


## Fifty-first iteration: target the Python 3.10 stable ABI

The corrected three-module pipeline from iteration 50 now has a separate
Limited API build with `Py_LIMITED_API=0x030A0000` and `py_limited_api=True`.
All three artifacts use `.abi3.so` names. Original/transformed source and the
settlement representation are unchanged. The experiment runs on CPython 3.14.3;
a Python 3.10 ABI target does not itself qualify execution on Python 3.10 or
other platforms. The original version-specific binaries remain preserved.

This is distribution qualification of the broader execution architecture, not
a local rendering algorithm change. The [Cython stable ABI guide](https://docs.cython.org/en/latest/src/userguide/limited_api.html)
warns that interacting with Python objects can cost more under the Limited API,
and that its vectorcall support begins with the Python 3.12 API target. It also
requires testing supported interpreter versions. Those facts motivate measuring
the candidate; they do not establish a Citry-specific overhead in advance.

The same 625 selected tests pass in 3.68 seconds. Both lifetime diagnostics
match production: the small fixture releases component/graph references
immediately with zero cyclic garbage, and the full fixture has no live graph
among four snapshot observations before collection. Both full-fixture variants
leave 265 unreachable objects with matching type counts. All initial/warm HTML
digests and four canonical ownership snapshots match in each timing pair.
The workers verify the actual ABI3 paths and compiled entry points; compiler
commands and artifact/source hashes qualify the local build selection.

The complete-render comparison fails both predeclared requirements. Five of
eight pairs improve both wall and CPU time. Median paired reductions in process
mean warm time are 0.533149 ms wall and 0.533188 ms CPU. Wall savings are
0.403117, -0.250740, -0.094625, 0.677920, 1.300360, -0.255263, 0.769783
and 0.663182 ms. Every worker retains six initial and 80 warm renders with
ordinary GC, balanced randomized order and all samples. No agent tests or builds
overlap main timing. Median worker means are 30.610625 ms reference and
30.261922 ms candidate; their difference is not the median paired saving.
Actual second renders have five wins and median savings of 0.2466875 ms wall
and 0.238000 ms CPU, with only eight observations per variant.

Reject this Python 3.10 stable-ABI implementation for the performance target.
It retains too little complete-render benefit under the seven-joint-win/1 ms
screen. This does not invalidate iteration 50's interpreter-specific candidate,
nor isolate ABI overhead by subtracting measurements from different runs.
No older-interpreter, browser or packaging qualification is pursued for this
failed target. The next bounded distribution comparison should use the Python
3.12 stable ABI, retaining an explicit Python fallback for older interpreters
as a requirement of any eventual packaging design.

The plan and scripts are in `benchmarks/settlement_abi_probe/`; the reviewed
settlement transform is reused directly from the preceding experiment. Reports
are `settlement-abi310-{build,smoke,large,lifetime,large-lifetime}.json` and
`settlement-abi310-tests.txt`. All ten main and ten smoke source hashes match.
The two lifetime reports retain their own hashes and build provenance. Python
lint and formatting pass. Production source, dependencies and the regular Rust
extension remain unchanged; this is not a new adopted performance checkpoint.


## Fifty-second iteration: target the Python 3.12 stable ABI

The corrected three-module pipeline now has a separate build with
`Py_LIMITED_API=0x030C0000` and `py_limited_api=True`. The source and explicit
settlement-state transform remain the same as iteration 50. Cython's documented
vectorcall support at this target motivates the comparison, but this experiment
measures the complete pipeline against production and does not isolate that
call mechanism or subtract results from independent earlier runs.

All 625 selected tests pass in 3.59 seconds on CPython 3.14.3. The small lifetime
fixture releases both component and graph immediately with zero cyclic garbage.
The full fixture releases all four observed graph references before collection;
both variants leave 265 unreachable objects with matching type counts. These
are fixture-specific lifetime checks, not a general memory guarantee. Actual
compiled entry points and ABI3 paths are checked, and every initial/warm HTML
digest and all four canonical ownership snapshots match in every timing pair.

All eight process pairs improve both wall and CPU time. Median paired reductions
in process mean warm time are 1.294648 ms wall and 1.295063 ms CPU. Wall savings
are 1.526053, 1.192666, 1.109615, 1.298019, 1.291276, 1.184741, 1.826739
and 2.567538 ms. Median worker means are 30.602588 ms reference and
29.128424 ms candidate; their difference is not the median paired reduction.
Actual second renders have five wins, with median savings of 0.571813 ms wall
and 0.570500 ms CPU across eight observations per variant. The consistent warm
throughput result does not establish equally consistent second-render gains.

Each fresh worker retains six initial and 80 warm renders, with ordinary GC,
balanced randomized process order and all samples included. No tests or builds
overlap main timing. All ten main and ten smoke source hashes match the retained
files. The separate build log records the compiler flags, generated source and
artifact hashes; both lifetime reports retain their own provenance. Python lint
and formatting pass, and independent technical and separate prose review found
no pre-timing blockers.

This target passes the declared seven-joint-win/1 ms warm-render screen and
advances to bounded execution qualification. It remains experimental: only
CPython 3.14 on macOS ARM64 has run these artifacts so far. The Python 3.12 ABI
label does not prove execution on Python 3.12 or 3.13. Any eventual distribution
must preserve supported Python implementations through qualified acceleration
or the existing Python implementation. No fallback packaging, minimum-version
change or production activation is implemented. The version-specific candidate
also remains available; this result does not add to its earlier saving or change
the adopted performance timeline.

The plan and scripts are in `benchmarks/settlement_abi312_probe/`, reusing the
reviewed settlement transform directly. Reports are
`settlement-abi312-{build,smoke,large,lifetime,large-lifetime}.json` and
`settlement-abi312-tests.txt`. The next check should exercise these same binaries
on the oldest supported ABI target and the intervening CPython version, then
check browser integration before making a packaging decision.


## Research direction change: park Cython and ABI exploration

After iteration 52 (`2130a6e`), the user asked to park Cython and ABI work and
focus on other avenues. Preserve iterations 49 through 52 as experimental
evidence; none activates a compiled Python module in production. The subsequent
runtime qualification plan was prepared, and isolated CPython 3.12 and 3.13
environments had their dependencies installed, but its tests had not begun.
The deferred plan and dependency pins are in
`benchmarks/settlement_runtime_qualification/`; installation logs are
`settlement-runtime{312,313}-environment.txt`. They establish no additional
compatibility or performance result and do not count as iteration 53.

Continue the larger-scope research mode established at iteration 49 through
changes to rendering work and representation. Revisit ownership structure reuse
and construction/discovery of the render tree, using earlier rejected attempts
to avoid repeating isolated record caches and helper translations. Keep live
values, occurrence identities, hooks, input validation and replacement behavior
in each complete-render comparison. The adopted timeline remains iteration 47.


## Fifty-third iteration: map repeated tree construction and discovery

With compilation research parked, an untimed census measures which structures
ordinary production rebuilds and revisits. The complete page executes 927 body
walks over 3,796 input entries. It enters 1,015 ordinary `CitryRender`
constructors, 1,015 `RenderFrame` constructors and 274 physical-region render
constructors. These are constructor-entry counts, not allocator or retained-memory
measurements; the census excludes the physical-region constructor's call into
its base constructor so that one wrapper is not counted twice.

Deferred discovery then makes 1,020 recursive scan calls whose input lengths
sum to 4,167 part entries,
plus 195 separate calls asking whether a nested render contains deferred work.
Neither measure counts loop iterations directly; the latter count also does
not measure its input sizes. Construction and
scan entries are different populations, so their ratio is not a duplication
percentage. They do show that the scheduler rediscovers work from the output
structure after body rendering has already produced it.

The 342 component-render constructor calls account for only part of the tree:
274 ordinary renders come from template slot content, and 356 from node render
methods, with another 40 from pure-body replay. The default benchmark already
includes some internally pure components; this diagnostic does not set
`pure = True` on the user fixture. The 274 physical-region wrappers preserve
ownership placement and are distinct from those slot-content renders.

Two identical inputs yield identical complete HTML and all four complete
ownership snapshot digests when occurrence ID generation is deliberately reset.
Each snapshot contains 1,081 source occurrences but only 115 distinct source-site
objects, plus 339 invocations, 342 instances, 339 ancestry rows, 468 fills,
274 regions and 339 queue rows. Resetting IDs is a comparison aid; this is not
proof that occurrence identities or live values can be reused across requests.

Shortening the fixture's `outputs` list from fourteen items to one reduces
ordinary render/frame constructor calls to 362 each, physical wrappers to 81,
source occurrences to 331, invocations to 107 and instances to 110. Deferred
scans fall to 367 calls whose input lengths sum to 1,499 entries. The source-site count remains close
at 109. Thus authored source structure stays largely shared while executed
ownership structure changes substantially with a normal input-shape change.
The output and snapshot digests change, as expected. A previous-render plan
must refresh or rebuild those occurrences when execution changes.

The next candidate direction is to carry pending child work alongside tree
construction, avoiding later discovery where the renderer can prove the
structure is still current. This differs from iteration 42's native scanner,
which retained discovery and added conversion. The design must first establish
where such a plan is valid: public `parts` lists are mutable, a later expression
or custom node can mutate an earlier result, hooks can replace output, and
cross-context dependency merges must occur after the correct descendants.
A saved work list without those boundaries is not a safe optimization. Custom
and changed trees need the existing discovery path. No scheduler or public tree
representation changes are adopted by this census.

`benchmarks/render_structure_probe/` retains the plan and diagnostic;
`render-structure-census.json` records all three cases, interpreter/revision,
normal Rust artifact hash and Python source hashes. It uses six ordinary warmups
before observation and adds profile callbacks only for counting. An initial
reporting attempt used `vars()` on the slotted snapshot and failed after its
render; the retained script enumerates dataclass fields. An initial wrapper
counter also counted base-constructor entries, which the retained script filters.
Neither draft supplies timing or performance evidence. Lint and formatting pass.
This investigation records no speedup and leaves the adopted timeline unchanged.

A separate mutation probe exercises `_render_body` with a node that emits a
mutable fragment, followed by a node that appends, removes or replaces a deferred
child in that fragment. In all three cases the existing post-body scan sees
the updated work, while a list captured at initial emission is stale. These
checks establish a concrete failure of unconditional early discovery; they do
not exercise task execution or prove any proposed invalidation mechanism.
`mutation_boundary.py` and `render-structure-mutation-boundary.json` retain the
three cases and source hashes. The next design needs an explicit mutation
boundary or guarded fallback before performance timing is meaningful.


## Fifty-fourth iteration: carry scheduling plans through body construction

The renderer can avoid most ordinary deferred discovery by recording non-text
positions as it constructs private body lists, but this prototype increases
complete-render time. Reject the current representation: all eight process
pairs regress, with a median paired increase in process mean warm time of
0.912239 ms wall and 0.912381 ms CPU. A separate constructor counterexample
also blocks adoption. Production remains unchanged.

`benchmarks/producer_schedule_probe/adapter.py` changes both the producer and
consumer in an isolated Python adapter. Each body returns its usual list and
hands a temporary scheduling plan through a ContextVar. Exact known IfNode,
ForNode and TemplateNode methods may contribute nested plans; ForNode transfers
iteration positions into its outer list. Other returned renders stay borrowed,
so the consumer scans their current contents at settlement. A completed initial
component result receives a plan only when its parts list matches the handoff.
The consumer removes that root plan on use. Replacement and unrecognized results
use ordinary discovery. Returned list, render, context and frame types stay the
same on the ordinary benchmark path. Cython and ABI work remain parked.

The untimed activation render consumes 569 plans covering input lengths totaling
3,056 parts but only 875 recorded positions. Ordinary recursive scan calls fall
from 1,020 to 451, and their input lengths fall from 4,167 to 1,111 entries.
These counts measure different paths through this prototype, not distinct tree
nodes or direct loop-iteration counts. Plan construction, list/tuple allocation,
method eligibility checks, handoff and consumption add work alongside the scans
that remain. The complete-render regression shows that the combined costs exceed
the benefit on this fixture; it does not assign a separate cost to each addition.

All 625 selected rendering, slot, ownership, manifest, const and dispatch tests
pass in 3.53 seconds. Full-render append/remove/replace cases preserve the earlier
borrowed-fragment mutation behavior. In the tested success and error paths,
`SCOPE.get()` returns None after rendering. This does not prove release from
copied execution contexts or establish retained-memory bounds.

The constructor counterexample replaces the renderer's CitryRender constructor
with a subclass that appends a deferred child to its received parts list. The
ordinary scanner finds and renders that child. The candidate recognizes the same
list identity, accepts its earlier position plan and leaves the child unresolved.
This demonstrates a missing exposure boundary; matching list identity does not
prove unchanged contents. Independent review identified the same mechanism.
The contracts report explicitly marks production compatibility false. Custom
constructor, tracing, copied-context, descriptor and arbitrary callback behavior
remain unqualified beyond the recorded checks.

The failure was found before main timing. The plan then explicitly limited the
comparison's decision to whether the unchanged fixture's benefit justified fixing
and qualifying the representation. No timing result could authorize adoption.
The single-sample draft smoke already matched HTML and all four snapshots, and
was retained as activation evidence, not the performance decision. The later
formatting-only probe revision and plan clarification each have exact source
archives for the draft report's original hashes.

Eight balanced randomized fresh-process pairs retain six initial and 80 warm
renders per worker, ordinary GC and every sample. No tests or builds overlap
main timing. Paired initial/warm HTML and all four canonical ownership snapshot
digests match. The fixture emits 1,013,746 bytes and both variants load the same
ordinary Rust artifact. Wall savings (negative means slower) are -1.447545,
-0.896092, -0.661110, -0.928387, -0.030357, -0.954698, -0.678209 and
-0.952755 ms. The candidate misses both the seven-joint-win and 1 ms saving
requirements. Median worker means are 30.507553 ms reference and 31.336022 ms
candidate; their difference is not the median paired result. Actual second
renders also regress in all eight pairs, with median increases of 1.348000 ms
wall and 1.346500 ms CPU across eight observations per variant.

The plan, adapter, timing harness, contracts and source archives are in
`benchmarks/producer_schedule_probe/`. Reports are
`producer-schedule-{smoke-draft,large,contracts}.json` and
`producer-schedule-tests.txt`. All eleven main hashes, eleven draft hashes and three contract hashes match
the retained files using their explicit archive mappings. A final Scope
docstring correction has its measured adapter source preserved in an archive;
it changes no executable logic. Python lint and formatting
pass. Keep the reduced-scan counts as architectural evidence, but do not continue
adding guards to this slower representation. Further experiments should remove
construction and processing together rather than add a parallel description of
an already-materialized tree. The adopted timeline remains iteration 47.


## Fifty-fifth iteration: invoke template fills without unused fallback objects

The direct template-fill prototype saves 0.370244 ms wall and 0.370113 ms CPU
by the median paired reduction in process mean warm render time, with seven of
eight joint wins. It was initially rejected against a 1 ms requirement. After
the user's threshold question, that decision is revised: the result supports
further qualification under the earlier 0.25 ms screen, while two retained
counterexamples still block adoption. The correction below preserves the
original decision and its timing evidence. Production remains unchanged.
Cython and ABI exploration remains parked.

Iteration 20 delayed fallback initialization but retained a lazy wrapper. This
experiment omits the unused fallback Slot and its content callable, scratch
dictionary and weak-reference binding entirely. It also omits SlotData and
SlotContext construction and calls the supplied template body directly. Initial
eligibility requires an exact ordinary template fill with no fallback variable
or data binding, ordinary data input and selected unchanged helpers. The adapter
still records the fallback source and fill rows in order and keeps ownership
capture, result conversion, physical wrapping, error boundaries and outlet hooks
in the benchmark path. Template execution and fresh result construction remain.

The activation render reports 194 omitted fallbacks and 194 direct calls. Complete
initial/warm HTML and all four canonical ownership snapshots match between each
pair on the standard fixture. A small ordinary template example also matches,
and a Python callback that renders its fallback takes the ordinary path and
matches. All 625 selected rendering, slot, ownership, manifest, const and dispatch
tests pass in 3.60 seconds. These checks do not establish general compatibility.

Independent review identified two failures reproduced before main timing. A
replacement supply-selection constructor changes the selected slot's content
after eligibility. Reference rendering invokes that new callable with a real
fallback; the candidate reads template-content fields from the new function and
raises AttributeError. Separately, a replacement template-render helper that
compares equal to the original defeats the tuple-equality checks. Reference
rendering outputs the replacement's text; the candidate ignores it and renders
the original body. Both failures are retained in the contracts report, which
marks production compatibility false. Other skipped constructors, normalization
helper replacements and rendering a retained SlotNode context outside active
capture remain unqualified review findings, not additional reproduced failures.

The plan was updated before main timing to permit only a diagnostic decision:
does the unchanged fixture save enough to justify repairing this path? No timing
result could permit adoption with the known failures. The main run retains eight
balanced randomized fresh-process pairs, six initial and 80 warm renders per
worker, ordinary GC and every sample. No tests or builds overlap main timing.
Both variants load the same production Rust binary. Wall savings are 0.004429,
0.564752, 0.273894, 0.622462, 0.232528, 0.466595, 0.471507 and -0.228577 ms.
The seven-joint-win requirement passes, but the 1 ms requirement fails. Median
worker means are 30.661039 ms reference and 30.352936 ms candidate; their difference
is not the median paired saving. Actual second renders save 1.240147 ms wall and
1.240000 ms CPU, with seven joint wins across only eight observations per variant.
That separate early-render result does not override the warm-render screen.

The plan, adapter, timing harness, contracts and measured-source archives are in
`benchmarks/template_fill_probe/`. Reports are
`template-fill-{smoke,large,contracts}.json` and `template-fill-tests.txt`. The
single-pair, single-sample smoke establishes activation, not a performance
decision. Its original import ordering failed lint; the exact measured probe
bytes are archived before sorting. The later plan clarification and adapter
docstring correction also have archives for the earlier smoke/contracts hashes.
All twelve main hashes, twelve smoke hashes and three contract hashes resolve
to retained files through their archive mappings. Python lint and formatting pass.

Removing construction and generic dispatch together produces a small improvement
here. The measurements do not isolate guard cost from the work omitted. The
initial decision was to stop extending the adapter because it missed 1 ms; the
following correction reopens qualification. The adopted timeline remains iteration 47.

### Threshold correction after iteration 55

The user asked why this Python-only experiment needed a 1 ms saving when the
higher requirement had accompanied added build complexity. It adds no compiler,
binary, ABI target or packaging step. I carried the stricter threshold from the
compiled pipeline into subsequent architectural probes, rather than tying it to
this candidate's concrete cost. The mode change at iteration 49 directs where
to search; it does not require discarding smaller valid gains.

The earlier eight-pair screen was at least seven joint wall/CPU wins and a
0.25 ms median paired reduction in process mean warm time. Iteration 55 meets
that screen. Its status is now performance evidence supporting further
qualification, with compatibility unresolved. This is a reassessment after
measurement, not a claim that it passed the original predeclared 1 ms rule.
The original plan is retained with a source-archive mapping in the main report.
No timing samples or measured code changed, and no new performance gain is claimed.

For subsequent eight-pair Python experiments, use 0.25 ms and seven joint wins
as the default screen for further qualification. Additional compiler or binary
distribution work can justify the stricter 1 ms screen used for compilation
experiments. Any other higher requirement needs a specific implementation or
maintenance cost documented before timing; being architectural is insufficient.
These are practical research criteria chosen by the agent, not statistical
significance boundaries or requirements imposed by the user. Correctness,
lifetime and supported-runtime checks remain separate adoption requirements.

Next, repair the concrete failures and examine the remaining review findings,
then measure that exact candidate against the 0.25 ms default. The uncorrected
0.370244 ms result cannot establish the speed of a repaired implementation.
Iteration 54 still fails the default screen because all eight pairs regress;
this threshold correction does not reopen its slower scheduling representation.


## Fifty-sixth iteration: qualify the direct template-fill path

The guarded Python candidate saves 0.158217 ms wall and 0.158569 ms CPU by the
median paired reduction in process mean warm time, with six of eight joint wins.
Reject this implementation: it misses both the corrected 0.25 ms saving and
seven-win requirements. A further callback case also prevents adoption. This
result measures the whole candidate against production; subtracting iteration
55's separately measured saving would not isolate the cost of the added guards.

The candidate retains iteration 55's fallback source/fill rows and direct body
execution, but replaces equality checks with live identity checks. It checks
the selected-supply record, skipped constructors, slot-data normalization,
fill-data binding and Python region-capture method. Retained outlet contexts
without their active graph use the ordinary call path. An explicit dependency
list generates a fixed chain of identity comparisons once at adapter import;
each eligible call still reads the live helpers. Graph-bound methods are checked
separately. No application values or eligibility results are cached across calls,
and this Python experiment adds no compilation or binary-distribution dependency.

The two original failures now match reference behavior. Independent review found
two more: an error-context manager can change the selected callable after
preparation, and SlotContext attribute access can observe a read that the direct
path skips. Fresh-process cases reproduce both before their guards are added.
The final checks include that error context, SlotContext attribute access and
field descriptors, and the Slot/content attribute setters. Fourteen focused cases
then match, covering ordinary fills, Python fallback access, helper equality,
selection and capture replacement, constructor calls, normalization, data binding
and an outlet called after its original graph scope ends. Constructor/helper
cases check observed calls as well as output. All 625 selected rendering,
ownership, slot, manifest, const and dispatch tests pass in 3.70 seconds.

The contracts harness needed one correction. Assigning and then removing an
inherited __new__ replacement left later constructions failing on this CPython
3.14 runtime, despite the visible method resolving to object.__new__ again.
The original shared-process report therefore contains matching unrelated errors
and is explicitly excluded from qualification. The final harness uses fresh
workers for every case and variant. It requires reference success, except for
the intended SlotContext error, and checks helper activation before comparison.
The draft script and report remain archived alongside the corrected results.

During main timing, review identified another callback window through accepted
provided-value keys. A string subclass deliberately hashes to the same value as
another provided key. Its equality callback changes the selected template fill's
fallback binding during the provides merge. Both maps are exact dictionaries, so
the candidate's shape guard accepts them. Reference rendering rereads that
binding after the merge and outputs fallback text; the direct path ignores the
new binding and outputs the supplied variable. The focused fifteenth case,
executed after timing, reproduces both the output and callback-count difference.
It uses public provide inputs without replacing helpers, although the callback
deliberately changes private template state. This remains an adoption blocker.
Checking exact key types could reject this case, but that proposed repair is
unmeasured; this run does not justify continuing to expand the guard chain.

Main timing retains eight balanced randomized fresh-process pairs, six initial
and 80 warm renders per worker, ordinary GC and all samples. No tests or builds
overlap it. Complete initial/warm HTML and all four canonical ownership snapshots
match on the standard fixture. The separate activation render reports 194 omitted
fallbacks and 194 direct calls. Both variants load the unchanged production Rust
artifact. Wall savings per pair are 0.200007, 0.039495, 0.339250, 0.210317,
-0.011129, 0.369179, 0.116427 and -0.026580 ms. Median worker means are
30.756806 ms reference and 30.514003 ms candidate; their difference is not the
median paired saving. Actual second renders save 0.552479 ms wall and 0.552000 ms
CPU, with seven joint wins across eight observations per variant. That separate
early-render result does not override the predeclared warm-render screen.

The plan, adapter, timing harness, contracts and source archives are in
`benchmarks/template_fill_qualified_probe/`. Evidence is
`template-fill-qualified-{smoke,large}.json`, `template-fill-qualified-tests.txt`
and the five `template-fill-qualified-contracts*.json` reports. All twelve main
hashes, twelve smoke hashes and three hashes in each contract report match their
retained files or archive mappings. The smoke is a single-sample activation check,
not a performance decision. Python lint and formatting pass. The adopted
timeline remains iteration 47, and Cython/ABI work remains parked.


## Fifty-seventh iteration: retain serializer frames in a Rust session

The combined native serializer path saves 0.279838 ms wall and 0.258444 ms CPU
by the median paired reduction in process mean warm time, with six of eight
joint wins. It meets the 0.25 ms magnitude requirement but misses the seven-win
consistency screen. Do not advance this implementation to production
qualification. Two Python-string compatibility failures also remain. The result
does not prove that native frame storage has no benefit; it does not meet the
predeclared screen on the default fixture.

Iteration 11 retained symbolic child chunks in Python and did not establish a
complete-render improvement. This experiment combines more of the path: it keeps
marker inheritance, scanned frames, placeholder lookup and final assembly in
one Rust session. Python still builds each frame and runs component/context
reads in the existing depth-first order. It calls native code once per frame,
but keeps scanned text and placeholder arrays in Rust. This reduces intermediate
Python exports; it does not eliminate per-frame native calls. A final explicit
stack writes resolved text into one output buffer, preserving the reverse-order
lookup rule for authored unknown, self and earlier-frame placeholders.

The prototype reuses the existing portable mark_html scanner. It handles only
serialization without an ownership-manifest artifact; the current Python path
handles artifact boundary comments. Whole-page security checks, component-class
collection, extension placeholder updates and serialization hooks remain around
the resulting HTML. The standard page activates five sessions covering 282 frames
per render. An earlier untimed count found 325 frames total across six serialize
calls, with the other 43 using an artifact. These are path counts, not a time
share or an allocation measurement.

This uses an isolated benchmark crate with the existing PyO3 version and ordinary
build configuration. It does not compare ABIs or use Cython. A production version
would fit the existing Rust extension rather than add a toolchain or distribution
target, so the plan uses the normal 0.25 ms / seven-win screen. Production Rust,
Python registration, wrappers and stubs remain unchanged. The experimental native
interface has its own stub and build metadata.

The initial native code had two corrected defects found by independent review
and reproduced in retained probes. Invalid valued-marker errors used Rust debug
formatting instead of Python repr, changing their quotes and escaping. They now
use Python repr. A compact 64-frame program with two references to the next frame
and a one-byte leaf computes a 2^63-byte result. Its capacity reservation panicked
despite passing the usize arithmetic checks. Fallible reservation now raises
MemoryError for that case. The initial source, artifact and reports are preserved
before the rebuild; no initial timing is used as the main performance decision.

Fourteen of sixteen focused comparisons match after those corrections, including
marker inheritance, valued-marker order, duplicate IDs, repeated/unknown/self/
earlier references, extension placeholder updates, malformed/raw-text HTML and
the valued-marker trailing-newline behavior. Two cases remain incompatible:
the original serializer preserves a lone surrogate in an unmarked component-less
string or a valued marker, while native UTF-8 extraction raises UnicodeEncodeError.
Custom string methods and helpers changed during callbacks remain unqualified.
The plan records these failures before main timing and permits only a diagnostic
decision about whether a correct fallback is worth pursuing. The native capacity
case is separate from the sixteen output/error comparisons.

All 360 selected marker, serialization-security, ownership-manifest, render,
deferred-render, on-render, slot and slot-node tests pass in 1.82 seconds against
the initial artifact and 1.97 seconds against the rebuilt artifact. The tests
do not cover the two surrogate failures.
Release compilation, Clippy and Python lint/format checks pass. The direct native
interface rejects missing root/unknown parent IDs and malformed argument types;
those behaviors follow the implementation and are not additional counted test
cases. Broad integration or supported-platform qualification was not run for
this rejected prototype.

Eight balanced randomized fresh-process pairs retain six initial and 80 warm
renders per worker, normal GC and all observations. No tests or builds overlap
main timing. Complete initial/warm HTML and four canonical ownership snapshots
match on the standard fixture. Both variants load the same production native
binary and the same experimental artifact; only candidate serialization uses
the session. Wall savings per pair are -0.008539, 0.191629, 0.561903, 0.354270,
0.205406, -0.589870, 1.431861 and 0.580065 ms. Median worker means are 30.405432 ms
reference and 30.236611 ms candidate; their difference is not the median paired
saving. Actual second renders regress by 0.099167 ms wall and 0.097500 ms CPU at
the median, with three joint wins across eight observations per variant.

The plan, adapter, native source, stub, timing harness, focused cases and source
archives are in benchmarks/serializer_session_probe/. Reports are
serializer-session-{build,smoke,large,contracts,contracts-initial}.json, with
build, Clippy, test and contract-console logs for both artifact versions. The
nineteen main hashes, nineteen smoke hashes, four hashes in each contract report
and ten build-source hashes match current files or explicit archive mappings.
Build metadata also records compiler versions and both artifact hashes; the
initial binary is retained at /tmp/citry-serializer-session-initial.dylib. Final
plan citation corrections have the measured plan bytes archived. No production
speedup is adopted and the cumulative timeline remains iteration 47.


## Fifty-eighth iteration: explicit settlement state in ordinary Python

The Python-only settlement state shows no useful full-render improvement. Its
median paired saving is -0.012631 ms wall and -0.012631 ms CPU, with four of eight
pairs improving both clocks. It misses the predeclared 0.25 ms and seven-joint-win
screen, so reject this change as a standalone performance optimization. Cython
and ABI work remain parked, and the adopted runtime and performance timeline
remain unchanged.

Iteration 50 moved five nested settlement callbacks onto a slotted state object
while compiling three whole modules. This experiment reuses that exact bounded
AST transform, but executes only the generated state class and scheduler in the
original Python module globals. All other runtime functions and classes retain
their identities. The object holds the existing pending-task stack and current
root result; the transformed methods use twelve explicit shared references, and
the outer scheduler uses five. Scanning, task construction, child rendering,
hook replacement, ownership retirement and finalization retain their original
operations. No native compilation or production source mutation is involved.

The activation render constructs only two settlement states on this large
fixture. Each replaces construction of five local functions, so the opportunity
is ten local-function allocations per full render. This representation still
executes the per-component settlement work. The measured result does not isolate
allocation savings from method dispatch and field access, and it does not explain
which compiled operations produced iteration 50's gain.

All 625 selected rendering, hooks, slot, ownership, manifest, const and dispatch
tests pass in 3.51 seconds. A small two-component lifetime diagnostic finds
immediate component and graph release, with zero cyclic garbage, in both variants.
A separate complete-page diagnostic observes four ownership snapshots and finds
all their graph references dead before explicit collection. Each variant leaves
265 unreachable objects with identical type counts. Automatic GC is disabled only
in those lifetime diagnostics; these fixture results are not a general lifetime
or memory guarantee. Generated traceback locations and private function inspection
still differ and have not been qualified for production.

The main comparison keeps eight balanced randomized fresh-process pairs, six
initial and 80 warm renders per worker, ordinary GC and all samples. No tests or
builds overlap main timing. Every initial and warm HTML digest and all four
canonical ownership snapshots match in each pair, as do the production Rust
binary and generated-source hashes. Candidate activation reports two state
constructions in every worker. Wall savings are 0.032875, 0.261970, -0.058137,
-0.088172, -0.246683, 0.507963, 0.294863 and -0.518324 ms. Median worker means
are 30.472072 ms reference and 30.619851 ms candidate; their difference is not
the median paired saving. Actual second renders save 0.423084 ms wall and
0.419500 ms CPU, with five joint wins across eight observations per variant.
That separate small sample does not change the warm-render decision.

The plan, adapter, timing harness and two lifetime diagnostics are in
`benchmarks/python_settlement_probe/`. Reports are
`python-settlement-{smoke,large,lifetime,large-lifetime}.json` and
`python-settlement-tests.txt`. The single-sample smoke checks activation and
output equality only. All 37 source hashes across the four reports resolve to
retained files; the measured plan is archived before its prose clarification.
Independent review reversed the five methods to their original ASTs and reviewed
the adapter, harness, lifetime checks and prose. Python lint and formatting pass.
The existing broader
compiled-pipeline result remains separate evidence; this experiment provides
no new adopted gain and does not resume its distribution qualification.


## Fifty-ninth iteration: identify component cases and question the contract

### Research mode change

The user redirected the investigation toward distinct component cases and the
work they can avoid. The first example is a component without slots, Alpine or
JS/CSS variables that could approach a plain template call. The user then asked
which API conveniences would be worth restricting or removing to unlock further
savings. This is a second research mode change after iteration 49: start from
required behavior, identify work that becomes unnecessary, and only then choose
an implementation. Record both compatible opportunities and explicit contract
tradeoffs. Architectural scope alone is not evidence of an opportunity.

The intervening reads of extension dispatch and source-location capture produced
no new implementation or timing result. The extension manager already records
which config constructors to call and which extensions implement each hook,
and related source-site reuse was measured in
iterations 5 and 21. Close that investigation and use the component census below
to choose the next experiments. Cython and ABI qualification remain parked.

### What the current benchmark actually contains

The retained census observes all 342 component renders in the default large case
and 110 in a version containing one project output. Instrumented and ordinary
renders produce identical complete HTML and all four canonical ownership snapshot
digests in each case. It deliberately retains component/render references until
classification finishes and makes no timing, allocation-cost or lifetime claim.

The groups are mutually exclusive observations of the executed inputs, not class
capabilities or safe optimization eligibility:

| Observed case | Large occurrences | One-output occurrences |
|---|---:|---:|
| Asset or client work in the observed output | 225 | 35 |
| Slots, with no observed asset or client work | 45 | 38 |
| Nested component work, with no observed slots/assets/client work | 16 | 9 |
| Ordinary leaves without observed slots/assets/client work | 54 | 26 |
| Dependency insertion placeholders, superficially in the leaf group | 2 | 2 |

The raw report puts the last two rows together as `observed_plain_leaf`; inspection
separates the `Css` and `Js` built-ins because their custom `on_render` methods
produce dependency placeholders. Manager input/data/finish counts record entry
into dispatch methods, not how many extension callbacks execute. Input dispatch
can immediately return and dormant i18n can eliminate finish callbacks already.

The 54 ordinary leaves are 41 `HeroIcon`, 11 `ProjectOutputBadge`, one `TabsStatic`
and one `ListComponent`. All 54 have typed kwargs, custom `template_data()` and
inherited provided values. None has a custom initializer or `on_render` method;
52 declare `pure = True`. Their contexts have no extension scratch keys immediately
after body construction. They still execute 216 base config initializations, 72
context constructions, 116 frame snapshots, and 54 entries into each of the input,
data and finish dispatch methods. These are counts, not estimates of recoverable
time. Their incoming ownership invocation is captured in the caller and therefore
is not charged to their own source-location counter.

All 342 occurrences use the default JS/CSS data methods and produce empty JS/CSS
data on this fixture. This includes components with client behavior: 71 occurrences
have a JS asset, and 224 have Alpine in their direct settled output. No occurrence
has a CSS asset, external dependencies or component-tag client bindings. The second
Alpine inspection stops at captured slot regions and still finds 223 occurrences;
only `Base` loses Alpine under that inspection. Thus slot content alone does not
explain most client-positive observations here. These dimensions should remain
separate: static assets, variable data, component-owned client state and ordinary
Alpine attributes need not require the same machinery.

### Insights that change the next design

1. **A leaf is an execution case, not necessarily a class property.**
   `ProjectOutputBadge` renders as a leaf 11 times and calls `Icon` three times,
   depending on `completed` and `missing_deps`. The template contains both paths.
   A prepared leaf branch could be useful; marking the whole class as incapable
   of children would be wrong.
2. **No supplied slots is weaker than no slot behavior.** `ListComponent` has an
   empty-list fallback containing a slot, even though this input never executes
   it. Slot outlets, supplied fills and callback-produced content need separate
   treatment.
3. **Expression values can change the rendering model.** The first node-only
   census incorrectly treated `Breadcrumbs` as a leaf. Inspecting settled child
   frames finds a rendered child inserted through an expression, moving it into
   the nested group. `TabsStatic.selected_content` and `ListComponent.item.value`
   are also general template values. A scalar-only value contract could remove
   recursive component dispatch in places where today's API permits it.
4. **No client behavior in one result does not establish inert inputs.**
   `HeroIcon` accepts an arbitrary attribute mapping. Other values can introduce
   Alpine even though these 41 icon results do not. A useful specialization must
   constrain or classify attribute names and values, not just inspect class JS.
5. **Template-only work and instance-free execution are different opportunities.**
   The ordinary leaves already have no observed client/slot work, but all invoke
   a typed data callback through a live component instance. Eliminating unrelated
   stages can preserve that callback; eliminating the instance requires proving
   it unobserved or offering a data function that does not receive one.
6. **The empty-data case extends beyond leaves.** Every component here uses the
   default JS/CSS data methods. A component execution plan could establish which
   data channels exist and avoid absent-channel work even in a component that
   renders slots or Alpine. Default method identity alone is insufficient:
   JsData/CssData schemas can introduce defaults, coercion or validation during
   normalization. Whether omitting a proven-absent channel saves useful time
   needs measurement;
   copying the existing empty checks elsewhere is not the hypothesis.

The census combines executed node calls, child render calls with an explicit
parent, and settled child frames. It does not certify that arbitrary callbacks
cannot render another independent root and return its HTML as a string. The
Alpine observations describe physical output; they do not infer who authored
an attribute or what every possible expression result could contain.

### Compatible paths and explicit API tradeoffs

The next proposals must state the exact case, which work disappears, when the
necessary facts become known, and how much of the real benchmark reaches it.
Changes to API guarantees are research options, not adopted behavior:

| Contract to examine | Opportunity under the current contract | Explicit restriction to measure | Capability affected |
|---|---|---|---|
| Every component call has a live instance | Preserve the instance/data callback while omitting proven-unused stages | A template-function component receives inputs without a component instance | `self`, instance attributes, parent/root inspection and instance lifecycle methods |
| Any template value may compose renderable objects | Specialize values after checking their kind | Scalar/text-only values at declared expression sites | Inserting components, slots, ComponentLike values or structured renders at those sites |
| Input mappings can be copied and mutated by hooks | Prepare schema/name facts while keeping runtime validation | Inputs are immutable and accepted once at a declared boundary | Input-mutating hooks and callbacks that edit their input mapping |
| Extensions can observe component lifecycle stages | Use the installed extensions' declared participation to skip unused stages | Template-function components opt out of instance hooks | Instrumentation, transforms or side effects expecting every component instance |
| Every call has a render identity; non-transparent output creates a component frame | Preserve compact fresh identity/provenance while simplifying execution | Inline template fragments belong to their caller's boundary | Per-fragment IDs, component-directed browser behavior and independently retained component renders |
| Runtime methods/configuration can change | Validate the relevant current definition before taking a shortcut | Freeze an execution definition until an explicit rebuild/revision boundary | Hot replacement without invalidating the prepared definition |

Some restrictions already exist: a component's Citry owner, pure declaration and
nested declaration bindings cannot be changed through ordinary class assignment
(`component.py:233-276`). Do not introduce a new restriction where current
immutability already supplies the needed fact. `transparent = True` already
omits a component-root marker, but `_render_one` still creates the component,
context and ownership records; an instance-free template call would change more
than that existing setting. Also separate documented extension
and component behavior from arbitrary mutation of private helpers when revisiting
rejected experiments; an adversarial private-field mutation is evidence of a
behavior difference, not automatically a public API promise worth preserving.

The first concrete comparison should use a template-only case with explicit value
and lifecycle restrictions, measure it against the ordinary component renderer
and equivalent Django/Jinja templates, then add typed inputs, a data callback,
slots, nested children and client behavior separately. Keep escaping and output
work comparable and report any omitted identity/ownership behavior. Apply a useful
result to a case that occurs in the real benchmark, starting with icons or a
proven leaf badge branch,
so a synthetic win cannot substitute for progress on the large benchmark. A plain
component is not proven template-speed merely because it lacks JS or slots.

### Evidence and review

The census and plan live in `benchmarks/component_cases_probe/`; current reports
are `component-cases-census.{json,txt}`. The initial JSON/source/plan are retained
with a qualification note: the first owner-attribution rule silently omitted
slot-capture calls because that function has no component/context argument. The
corrected report records 274 large-case and 81 reduced-case slot captures separately,
alongside two anonymous context constructions and frame snapshots in each case.
Independent review also prompted the settled-child-frame check, which corrected
the initial 55 ordinary-leaf count to 54. The initial artifact remains diagnostic
history, not the current classification. No production code or adopted performance
checkpoint changes in this iteration. All 324 Python-source/plan hashes across
the current and initial reports resolve to retained files. The current report
also records the unchanged production Rust binary hash. Lint and formatting pass.


## Sixtieth iteration: a restricted template function approaches template-engine throughput

The case-driven experiment gives a strong result for a deliberately smaller
contract. A prepared function using Citry's existing body nodes beats ordinary
transparent Citry components in all eight joint wall/CPU comparisons for every
fixture. It also beats Django and Jinja in all eight comparisons for static HTML,
scalar text and typed data preparation. This justifies trying the contract on a
real component; it does not establish a large-page saving or a production API.

### Contract and work omitted

The function accepts exact built-in scalar values nested in acyclic plain dict,
list and tuple containers, with an exact dictionary at the root. It optionally
runs the shared data adapter, validates the returned dictionary, creates a
component-free CitryContext, executes the existing body walker and flattens text
and interior renders. Escaped Markup returned by the existing nodes is accepted;
caller-supplied Markup and arbitrary conversion objects are rejected. The typed
fixture uses the same Citry kwargs schema and data-preparation function in all
four engines, including defaults and unknown-key rejection.

There is no live Component instance, instance callback, parent/root access,
provided-value scope, supplied slot, component-valued expression result, asset
collection, runtime extension hook, component identity/ownership record, retained
component render or document serialization. The prototype uses component classes
for the existing compiler and typed schema definitions; it removes per-call
instances, not those preparation-time definitions. This is the explicit contract
tradeoff requested after iteration 59, not a compatible shortcut selected from an
empty slot or JS-data dictionary.

The fixed templates contain static text, scalar expressions, dynamic title
attributes, a condition, a loop, and typed data preparation. Body validation rejects
component/slot/foreign/template nodes, nested template attributes and spreads.
It is still only a constructor for these trusted fixtures: it does not prove that
arbitrary source or Python expressions cannot introduce client behavior or effects.
A general source/definition classifier and application-facing API remain undesigned.
The prototype adds no whole-output cache; both Citry paths retain existing node
caches, including the attribute-output cache. No Cython, ABI or native build changes
are involved.

The ordinary Citry reference uses `transparent = True` so all four paths produce
the same complete HTML. That existing setting removes root markers but keeps
normal instances, IDs, hooks and ownership. In a separate activation call each
ordinary fixture constructs one ownership graph, one component and four base
extension configs, enters data and finish dispatch once, runs one settlement
session and serializes the document once. All seven counters are zero for the
function path. The existing body/evaluation/escaping work remains in both paths;
branches inside those routines may also skip work when there is no component.

### Warm results

Values are microseconds per call, using the median of eight process means. The
loop rotates between zero, one and eight items; it is not an eight-item-only row.
The savings column is the separate median paired difference of process means.

| Fixture | Ordinary transparent Citry | Template function | Django | Jinja | Paired saving vs Citry |
|---|---:|---:|---:|---:|---:|
| Static HTML | 38.963 | 1.077 | 1.760 | 2.385 | 37.877 |
| Scalar text | 42.455 | 2.139 | 2.836 | 2.784 | 40.312 |
| Dynamic title attribute | 48.294 | 3.867 | 3.759 | 3.030 | 44.398 |
| Condition | 44.911 | 2.527 | 2.253 | 2.554 | 42.404 |
| Loop, mixed lengths | 55.007 | 7.948 | 6.656 | 3.198 | 46.990 |
| Typed inputs and data function | 43.704 | 2.431 | 3.092 | 3.037 | 41.239 |

All six cases have eight joint wins over ordinary Citry. Against Django the
function has eight joint wins for static/scalar/typed, one for attributes and
none for the condition or loop. Against Jinja it has eight for static/scalar/typed,
five for the condition and none for attributes/loop. The paired median loop ratio
is 1.187 times Django and 2.495 times Jinja. Therefore the remaining loop execution,
validation and context work deserves a separate explanation; parity is not a
universal property even of these restricted examples.

Eight fresh-process blocks balance all four engine positions, with matching hash
seeds within each block and the case order rotated between blocks. Each process
retains six individual initial calls and 80 measured batches of 50 calls per case.
Inputs rotate throughout the timed loop. Ordinary GC remains enabled and every
sample is included; no tests or builds overlap main timing. Complete output strings
for every retained input are compared across all four engines outside timing.
The installed versions are CPython 3.14.3, Django 6.0.6 and Jinja 3.1.6. All workers
use the same production Rust binary.

### Second calls and limits of the result

The individual second calls remain distinct from warmed batches. These are median
microseconds after engine-specific adapter preparation; earlier calls may still
perform lazy compilation. They are not a comparison of total application startup.

| Fixture | Ordinary transparent Citry | Template function | Django | Jinja |
|---|---:|---:|---:|---:|
| Static HTML | 64.708 | 2.604 | 3.875 | 4.646 |
| Scalar text | 69.688 | 8.312 | 8.521 | 6.229 |
| Dynamic title attribute | 81.666 | 17.729 | 6.729 | 5.812 |
| Condition | 68.124 | 7.979 | 5.667 | 5.000 |
| Loop | 104.855 | 36.104 | 15.876 | 5.792 |
| Typed inputs and data function | 67.854 | 6.979 | 7.749 | 6.417 |

The function's warmed scalar advantage over Jinja does not extend to the median
second call here. The user’s repeat-render goal therefore still needs both early
and sustained measurements. Six initial calls and adapter preparation are retained
in the raw report rather than hidden in an aggregate.

The result supports a concrete insight: these examples can execute at roughly
template-engine cost with Citry's current node implementation once they stop
paying the full component protocol. It does not attribute the saving to any one
omitted stage or show that all those stages must be removed together. In particular,
do not multiply a standalone saving by the 54 observed large-page leaves: nested
components already share the outer graph, settlement session and document serializer.
The large-page result must be measured directly with any identity/ownership differences
stated and checked. The full framework is not at Django parity, and the adopted
performance timeline remains at iteration 47.

### Contract checks, review and next experiment

Before main timing, six fixtures and fourteen input sets match across all four
engines. Six additional scalar cases and four attribute cases match ordinary Citry,
including quote escaping, None and booleans. Thirteen input/body rejection cases
pass, as does typed unknown-key rejection in all four engines. A mutation check
confirms current inputs are read and the caller's mapping is unchanged. These are
bounded prototype checks; they are not a repository gate or a claim of general
source safety or API compatibility.

Independent review identified two gaps before main timing: non-dictionary root
inputs were accepted, and a TemplateHtmlAttr could hide nested rendering inside an
allowed attribute node. Root/data dictionary checks and explicit attribute-type
checks now reject them. Adapter output is revalidated even when it is the original
input object. The first ordinary scalar render also demonstrated that escaped
Markup is a normal node result; the flattener accepts that result type while
continuing to reject caller-provided trusted-HTML objects. No measured runtime
source changes after main timing.

Artifacts live in `benchmarks/template_function_probe/`, with reports
`template-function-{smoke,main,contracts,contracts-initial}.json`. The smoke contains
one call per case and predates the conditional fixture and final restrictions;
it is not used for the performance decision. Exact source archives retain its
inputs, the first contract checks and the main plan before prose clarification.
All 331 source/plan hashes across the four reports resolve to retained files;
independent review also recomputed the raw timing summaries and second-call values.
Lint and formatting pass. The production renderer and native artifact remain
unchanged.

Next, try an explicitly selected real leaf, starting with HeroIcon, while measuring
its caller and the complete page. Its arbitrary attribute spreads need an explicit
admissible-input rule; its existing data method must be represented as a function
without instance access. Compare the contracts separately: first how much can be
removed while keeping a compact fresh identity/ownership boundary, and then what
inlining into the caller's boundary saves. State which behavior each version loses.
This uses the discovered case and tests a whole omitted stage, rather than returning
to isolated cache or language-boundary tuning.


## Sixty-first iteration: a leaf keeps ownership identity without a live component

The restricted HeroIcon prototype produces the same complete HTML and ownership
snapshots for the checked nested cases, while avoiding initialization of all 41
HeroIcon components. It nevertheless makes the large page **0.154 ms slower by
median paired warm wall time, with 0/8 joint wall/CPU wins**. Do not adopt this
implementation. This result separates a feasible identity representation from
an implementation that improves performance; it establishes only the former for
the bounded cases checked here.

### The contract removes instance capabilities and keeps graph records

Iteration 60 removed whole standalone render sessions. This experiment selects
only the benchmark's exact HeroIcon inside an ordinary component tree. Its inspected
data method does not read self or slots. The adapter constructs its existing typed
kwargs and calls that method as a function, then uses the existing compiler, body
walker, attribute handling and outer document serializer. It retains the ordinary
scheduler and full ownership graph.

A temporary metadata object supplies a fresh ID and class metadata to
`OwnershipGraph.bind_instance`. The graph does not retain that object. A RenderFrame
stores the identity and root markers in the returned render, whose context has no
live Component. The normal finalization stage settles that ID, while skipping
component hooks. This avoids the live instance, its four base extension configs,
input/data/render hooks, template and attribute extension rewrites,
cache-extension lookup and instance state. It does not
remove incoming invocation capture, ownership binding, caller-side construction of component descriptors, scheduler work or final HTML marking. Parent context-merge hooks
still run and see a child context with no Component.

The explicit experimental contract gives up self/parent/provides access, supplied
slots, instance lifecycle hooks, per-instance extension participation, assets,
JS/CSS data, client directives, template overrides and globals. It requires an
ordinary enclosing component and rejects direct root rendering. Dynamic attribute
spreads accept only an explicit set of ordinary SVG names and exact built-in
scalar/container values. Citry Const wrappers are read through to their values;
custom objects, trusted-HTML inputs and renderables are rejected. These restrictions
are proposed capability tradeoffs, not an inferred guarantee for existing users.
The adapter trusts the retained HeroIcon template and data method; it is not a
general source classifier or application-facing API.

### Full-page timing rejects this implementation

Eight balanced fresh-process pairs each perform six initial and 80 warm renders,
with ordinary GC, unchanged native code and every sample retained. No tests or
builds overlap main timing. Complete HTML digests match on all initial/warm calls;
an untimed observation in every worker also matches all four canonical ownership
snapshot digests. The activation check confirms 41 selected calls in each variant,
41 ordinary initializations in the reference and zero in the candidate.

| Measure | Ordinary Citry | Restricted icon |
|---|---:|---:|
| Median of process mean warm wall times | 30.248 ms | 30.382 ms |
| Median observed second-render wall time | 33.718 ms | 31.725 ms |

The median paired warm change is **0.154348 ms slower in wall time** and
**0.153875 ms slower in CPU time**. Every pair is slower in both. The median
paired second-render saving is 2.357667 ms, based on only one second render per
worker; it does not establish a repeat-render improvement. The table's separate
medians are not the median of paired differences. This candidate fails the
predeclared 0.25 ms / seven-win full-page screen and adds no production checkpoint.

### Why the standalone result did not transfer

After main timing, a separate cProfile run enables profiling only inside selected
HeroIcon `_render_one` calls, over eight pages after six warmups. This excludes
later settlement, parent work and document serialization. Its times include profiler
overhead and are not additive estimates of uninstrumented savings.

| Work inside selected icon calls | Ordinary calls/page | Candidate calls/page |
|---|---:|---:|
| Pure-body capture for a distinct body/input result | 11 | 0 |
| Top-level pure-body replay | 30 | 0 |
| Attribute regions resolved with spreads | 22 | 82 |
| Recursive value-validation calls | 0 | 1,804 |
| Recursive input-copy/unwrapping calls | 0 | 328 |

The ordinary path already renders only 11 icon bodies and reuses their results
for the other 30 occurrences. The candidate walks all 41 bodies. Its repeated
contract checks also traverse both inputs and application-produced data, including
rechecking attribute values. Value validation accounts for 0.729 ms of profiler
self time; spread resolution grows from 0.088 to 0.313 ms of self time. Selected
initial-render work totals 5.599 ms instrumented for the reference and 6.591 ms
for the candidate, including the profiler's own disable calls.

These counts identify work introduced by this implementation. They do not prove
that removing validation or restoring body reuse will yield a particular saving.
The next experiment should keep the existing pure-body behavior while separating
which restrictions can be established at registration, which typed inputs require
validation on each call, and which trusted application outputs need no second
recursive validation. That tests the cost of enforcing the selected contract,
without assuming a leaf body should lose an existing optimization. Broader leaf
classification and inlining into the caller remain unqualified follow-ups.

### Checks, review and retained evidence

Contract checks compare complete HTML and full canonical snapshots in memory for
the large and one-output page, twice each, plus five icon input sets. Sequential
icon changes reuse one prepared candidate body. Cases include nested Const wrappers,
solid/outline values, custom sizes, structured class/style data and escaped quotes,
angle brackets and ampersands. Mutating an attribute between calls changes output
and leaves caller input intact. Two ordinary errors, an invalid variant and unknown
kwarg, match error classes, failed ownership snapshots and subsequent ID consumption.
Thirteen restricted inputs/modes are rejected: ten attribute-value/name cases,
supplied slots, direct-root rendering and per-render globals.

Independent technical review caught three gaps before main timing: schema/data
validation initially preceded ID binding, direct-root serialization could not
find the Citry owner, and the first mutation check rebuilt the prepared body.
The adapter now binds before schema/data errors, rejects direct roots, and the
changing-input checks reuse one installation. The first development smoke also
found nested Const wrappers; input unwrapping now reads every wrapper layer.
Development smoke runs did not determine the timing decision.

Artifacts are in `benchmarks/identity_leaf_probe/`; reports are
`identity-leaf-{smoke,main,contracts,diagnosis}.json` under the existing results
directory. All 36 recorded source/plan hashes resolve to the retained current files.
Independent review recomputed the raw timing summaries, checked profiler counts
and reviewed the prose separately. Lint and formatting pass. These are bounded
experimental checks, not a full
repository gate or a qualification of arbitrary extension behavior. No production
source or native build changes; the adopted timeline remains at iteration 47.


## Sixty-second iteration: body reuse helps, but the restricted icon misses the consistency criterion

Restoring render-local body reuse saves **0.454 ms with 8/8 joint wins** against
iteration 61's guarded icon prototype. The final restricted variant, which also
omits redundant validation, saves **0.273 ms against ordinary Citry with 6/8 joint
wins**. It passes the size criterion but misses the seven-win consistency criterion.
Do not adopt it or add it to the production timeline. The measurements support
retaining body reuse in future architectural experiments; they do not establish
a reliable whole-page gain from this restricted leaf alone.

### Separate the implementation cost from the API promise

Four variants run in each block:

- **Reference:** ordinary Citry with its existing component lifecycle and pure-body
  reuse.
- **Guarded:** the unchanged iteration 61 prototype, with input/output checks and
  no pure-body reuse.
- **Reuse:** the guarded prototype plus existing pure lookup, output-capture and
  replay helpers. A miss renders the inspected SVG body and captures strings and
  transparent interior structure. A hit rebuilds that structure with the current
  context and fresh root identity. Capture checks for new ownership records,
  extension data and unsupported parts; it does not construct i18n configuration.
- **Contract:** reuse plus one recursive input-copy/validation walk and a separate
  attribute-name check. It omits the second input walk and recursive checks of the
  trusted application-produced output. Typed kwargs and the data function still
  execute for every occurrence.

The last variant requires an additional explicit promise: the registered data
function and its module data must keep producing the declared ordinary SVG values.
The prototype trusts the inspected HeroIcon callback and fixed template; it does
not infer that property for arbitrary Python. Replacing the callback or mutating
module data to violate the promise is unsupported, and output violations are not
guaranteed to be detected or safely rejected. Caller input values remain checked,
including custom objects, renderables, cycles and attribute names. This experiment
is not a public API or a sandbox.

Both new variants retain iteration 61's restrictions, including no live instance,
slots, per-instance hooks/assets/client state, template or attribute extension
rewrites, globals or direct-root rendering. They retain full ownership capture,
fresh IDs, root markers, caller descriptors, scheduling and document serialization.
This measures the cost of enforcing the stated capability restrictions.

The candidates reuse **32** icon calls rather than the reference's **30**. An
untimed source/value diagnostic found five ordinary calls carrying a doubly wrapped
Const stroke-width value. Ordinary pure keying unwraps one layer; the retained
prototype input normalizer unwraps every layer. Ordinary lookup therefore sees
11 keys, while the new variants see nine. This difference was documented before
main timing and checked in each worker's untimed activation render. Checked HTML
and ownership remain identical. The reuse comparison to the guarded variant uses
the same input normalization on both sides.

### Four-way full-page measurement

Eight blocks run all four variants in fresh processes, with balanced cyclic orders
randomized at the block level. Each variant occupies each process position twice.
Every worker keeps six initial and 80 warm renders, ordinary GC and all observations.
No tests or builds overlap main timing. The primary comparison was declared as
reference to contract before measurement; other contrasts explain specific costs.

| Variant | Median process mean warm wall time | Median observed second-render time |
|---|---:|---:|
| Reference | 30.900 ms | 34.990 ms |
| Guarded | 31.081 ms | 32.383 ms |
| Reuse | 30.692 ms | 34.825 ms |
| Contract | 30.484 ms | 34.153 ms |

| Paired comparison | Median warm wall saving | Median warm CPU saving | Joint wins |
|---|---:|---:|---:|
| Reference to contract | 0.272830 ms | 0.272819 ms | 6/8 |
| Guarded to reuse | 0.454451 ms | 0.454338 ms | 8/8 |
| Reuse to contract | 0.138659 ms | 0.138519 ms | 6/8 |

Separate medians in the first table are not paired differences. The primary
second-render paired saving is 0.481854 ms, with only one such observation per
worker. Do not combine medians from different experiments into a cumulative
speedup. The decision still uses at least 0.25 ms and seven joint wins against
ordinary Citry; no build complexity or 1 ms threshold is introduced here.

### Profiling confirms which work changed

A separate diagnostic after main timing profiles only the selected icon initial
render calls, over eight full pages after six warmups. It excludes later settlement,
parent work and document serialization. These counts and instrumented self times
explain work performed, not recoverable uninstrumented milliseconds.

| Work inside selected icon calls, per page | Reference | Guarded | Reuse | Contract |
|---|---:|---:|---:|---:|
| Attribute regions resolved with spreads | 22 | 82 | 18 | 18 |
| Recursive value-validation calls | 0 | 1,804 | 1,804 | 246 |
| Recursive input-copy/unwrapping calls | 0 | 328 | 328 | 328 |
| Pure-body lookup calls | 41 | 0 | 41 | 41 |

Guarded value validation takes 0.712 ms of profiler self time; contract validation
checks only scalar leaves during the input walk and takes 0.022 ms. Spread
resolution self time falls from 0.312 ms guarded to 0.069 ms contract. The selected
initial-render totals, including profiler disable calls, are 5.597 ms reference,
6.452 ms guarded, 4.900 ms reuse and 3.613 ms contract. Profiler overhead amplifies
many small calls, so those totals cannot replace the complete-page comparison.

### Checks, review and next scope

Both variants pass the retained full-HTML/full-ownership comparisons for large
and one-output pages, changed icon inputs, escaping and mutable caller input.
Invalid variants and unknown kwargs match ordinary error types, failed ownership
snapshots and subsequent ID consumption. Thirteen restricted input/mode cases
are rejected. A new three-icon fixture checks miss/hit/miss reuse within one root,
including a changed attribute on the third icon, and compares complete HTML and
ownership. The earlier sequential-input check reuses the same prepared body across
root renders. Main workers match every initial/warm/activation HTML digest and
all four canonical ownership snapshot digests, retain 41 selected calls and omit
all 41 initializations in every candidate. New-variant workers confirm 41 lookups
and 32 hits outside timers.

Artifacts are in `benchmarks/leaf_contract_probe/`, with reports
`leaf-contract-{main,smoke,reuse-checks,contract-checks,diagnosis}.json`. All 49
recorded source/plan hashes resolve to current retained files. Lint and formatting
pass. Independent technical review checked the fixed-body effect assumptions,
input rejection, error order, identity and cache behavior before main timing;
prose received a separate review. Final review recomputed the timing summaries,
checked the profiler counts and verified all 49 hashes. No production source or
native artifact changed.
These bounded checks are not the final repository/browser gate.

The next comparison should ask what retaining every leaf's independent identity
costs. An explicitly inline icon would also give up its own ownership entry and
HTML marker, while remaining ordinary SVG owned by its caller. That is a different
API contract and requires comparisons that account for those deliberate changes;
it cannot be called byte-identical to the reference. After measuring that boundary,
expand the case analysis beyond these 41 icons. The current result gives no reason
to expect repeatedly tuning this one leaf to close the whole gap to Django.


## Sixty-third iteration: caller-owned icon output passes the performance screen

The inline HeroIcon prototype saves **0.950 ms versus ordinary Citry, with 8/8
joint wall/CPU wins**. Removing identity also saves **0.729 ms versus iteration
62's identity-preserving contract, with 8/8 wins**. This passes the declared screen
and advances the caller-owned HTML contract to broader qualification. It is not a
production optimization yet: the component API and browser isolation behavior
change, and browser behavior has not been qualified.

### Independent identity has a cost beyond the live instance

The selected direct HeroIcon tag still resolves its inputs and creates deferred
work. Its data function therefore runs in the same scheduler position as before.
It uses iteration 62's checked caller inputs, trusted callback output and existing
pure-body reuse. The difference is that the tag creates no ownership invocation,
source occurrence or queue record, and the function creates no ID or component
root frame. Its interior render joins its caller's frame during serialization.
Keeping the descriptor and scheduler work separates this experiment from immediate
function evaluation, which could also change callback/error order.

This explicitly gives up the icon's independent component identity, marker,
initialization dependency, morph range and Alpine isolation. The template tag
rejects component range directives, slots and client bindings. Direct-root,
forwarded/dynamic, hook-produced descriptors and template-global cases are excluded.
The remaining restrictions and the promise that the registered callback and its
module data produce supported values are those of iteration 62. No existing component is automatically classified into this mode.

The initial inspection revealed why "no own JavaScript" is insufficient to describe
this contract. `ownership_manifest.py:522` propagates client-active state from an
active parent to descendants so each component can cut Alpine inheritance. In the
large fixture, **13 HeroIcon instances appear in the browser graph, and 12 receive
Alpine isolation markers**. The first ID-occurrence count conflated those facts;
direct marker and manifest checks established the distinction before main timing.
The thirteenth has graph membership without isolation. The other 28 icons appear
only through their ordinary component markers in this serialized document.

| Large-page work/records | Ordinary / identity-preserving | Inline |
|---|---:|---:|
| Selected icon callbacks | 41 | 41 |
| Generated render IDs / logical instances | 342 | 301 |
| Source occurrences | 1,081 | 1,040 |
| Component invocations / ancestry / graph queue rows | 339 each | 298 each |
| Logical fills | 468 | 468 |
| Physical regions | 274 | 274 |
| Selected instances in browser graph | 13 | 0 |
| Selected Alpine isolation markers | 12 | 0 |
| Complete serialized bytes | 1,013,746 | 1,005,379 |

The output reduction is 8,367 bytes. The table counts graph queue rows, not deferred
scheduler tasks: the latter still execute for all 41 icons.

### Compare the remaining behavior without hiding the deliberate changes

Raw HTML and ownership graphs are different by design. The comparison first
validates each raw browser manifest with the existing protocol validator, including
its revision and relationships. It then removes only selected icon markers and
browser instance/invocation/ancestry entries, renumbers the remaining wire IDs and
range comments consistently, and normalizes the manifest revision and dependency
payload's reference to it. All other HTML and browser payload fields remain in the
comparison. Component IDs receive stable comparison names by class and occurrence.

For the server graph, remove only the selected logical instances, invocations,
source occurrences, ancestry and graph queue rows. Rename each independent ID
namespace and renumber retained event values while preserving their relative order.
Retain every other field, relationship and table sequence. References from retained
records to a removed icon are rejected rather than silently discarded. The comparison
is limited to production-mode fixtures without component-tag client bindings;
development provenance and arbitrary nested binding records need more work.

Separate activation assertions ensure the inline implementation actually removed
the identities: projected equality alone could also pass an implementation that
kept them. Every main inline worker records 41 callbacks, zero selected identities,
invocations or ID-bearing frames, no selected initializations, and 301 generated
IDs. The identity-preserving worker records 41 selected IDs and 342 generated IDs.

These checks establish the stated projection, not browser compatibility. In
particular, losing Alpine isolation is a deliberate capability change whose
application consequences require browser tests and a documented public contract.

### Main timing and decision

Eight blocks run ordinary Citry, the identity-preserving contract and inline output
in fresh processes. Shuffle all six process-order permutations plus two cyclic
orders; ordinary and inline run in each relative order four times. Each worker
performs six initial and 80 warm renders with ordinary GC and changing render IDs.
No tests or builds overlap main timing. Every output gets both a raw digest and
a digest of the complete projected output, and each worker captures all four
projected server ownership snapshots outside timers.

The harness retains all 86 output strings until timing finishes, then validates and
normalizes them. This keeps substantial comparison work out of the timing loop,
but holds about 87 MB of output per worker. These allocation conditions differ from
the previous probes; use the within-experiment comparisons rather than subtracting
its absolute times from earlier checkpoints.

| Variant | Median process mean warm wall time | Median observed second-render time |
|---|---:|---:|
| Ordinary Citry | 30.657 ms | 34.873 ms |
| Identity-preserving contract | 30.489 ms | 34.538 ms |
| Inline contract | 29.775 ms | 32.822 ms |

| Paired comparison | Median warm wall saving | Median warm CPU saving | Joint wins |
|---|---:|---:|---:|
| Ordinary to inline | 0.950212 ms | 0.950331 ms | 8/8 |
| Identity-preserving to inline | 0.729036 ms | 0.729056 ms | 8/8 |

The median paired inline/ordinary warm ratio is 0.968916, about **3.1% less time per warm render** in this run. Separate medians in the first table are not paired differences. The
ordinary-to-inline second-render paired saving is 1.301229 ms, based on one second
render per worker. The primary comparison clears both the 0.25 ms saving criterion
and seven-win consistency criterion. There is no extra build requirement or 1 ms
threshold. Passing justifies broader qualification, not automatic adoption.

### Qualification evidence and remaining work

The retained contract runner compares complete projected HTML/browser data and
server graphs for large and one-output pages, four changing icon input sets, and
ancestor recovery from an invalid icon. Cases include nested Const wrappers,
escaping, structured class/style inputs, repeated icons and a changed attribute.
Prepared bodies persist across changing root calls. Invalid variants and unknown
kwargs retain their application error classes; inline errors deliberately create
no icon instance or queue record and consume no icon ID. Ten unsupported input
or invocation cases are rejected, including a hook-produced descriptor. Four
negative comparison checks detect changed SVG text, an unrelated caller marker,
a corrupted revision and a changed retained browser field.

Independent review caught raw revision normalization that could hide corruption,
an unmarked hook-produced descriptor that bypassed the direct-tag restriction,
and an overbroad provenance claim. Raw protocol validation, an InlineElement
subclass identifying the selected direct tag, and explicit production/no-binding
scope resolve those gaps before main timing. Lint and formatting pass.

Artifacts are in `benchmarks/inline_leaf_probe/`, with reports
`inline-leaf-{contracts,smoke,main}.json`. All 51 recorded source/plan hashes resolve
to retained current files; final independent review recomputed the timing summaries and checked all 51
hashes, activation counts and output comparisons. Prose received a separate
review. The production runtime and native artifact are unchanged. The adopted
timeline remains at iteration 47.

Next, qualify the proposed caller-owned HTML behavior in the browser, including
ancestor Alpine state/events and slot placement, then broaden the case analysis
beyond HeroIcon. This result supports an explicit distinction between reusable HTML
and components that require an independently observable runtime boundary. A general
registration API, enforcement rules, more component families and the final
repository/browser gate remain unfinished. Full-page Django parity remains open.

## Sixty-fourth iteration: caller-owned SVG works in bounded browser cases

The unchanged iteration 63 adapter passes its declared browser checks in Chromium,
Firefox and WebKit. This iteration measures no rendering speedup. It qualifies part
of the behavior behind the earlier 0.950 ms warm-render saving, while keeping that
result separate from production adoption and the adopted performance timeline.

### Giving up identity removes a browser restriction too

Under an active Alpine ancestor, ordinary Citry gives a descendant component its
own Alpine isolation even when the component has no JavaScript of its own. That makes its HTML more than a reusable
piece of markup: a browser clone would also need a fresh component identity and
ownership relationships. Section 8 of `alpinejs.md`, the existing structural browser
tests, and `citry.js::rejectStructuralComponentClones` establish the resulting
restriction. Citry rejects client-active component roots inside native `x-if`,
`x-for` and `x-teleport` templates before graph activation.

The first fixture combined an ordinary icon, supplied and fallback slot content,
a teleport and an x-if. It timed out waiting for Alpine in the ordinary reference.
A targeted browser diagnostic found the explicit x-teleport clone error, rather
than a missing runtime asset. The failure and exact original
fixture, probe and plan are retained. The revised cases separate ordinary slot
checks from each structural directive, with the existing rejection expected for
variants retaining identity. This
changes the qualification plan, not the measured adapter or production runtime.

The candidate's SVG has no independent identity to clone. For this restricted
fixture, it behaves as HTML belonging to the caller, including when Alpine creates
or moves its physical nodes. This is an additional reason to distinguish reusable
HTML from independently addressable components. It is not evidence that existing
components can silently lose identity or isolation.

### Browser checks and observations

Use the benchmark's exact HeroIcon and the unchanged adapters from iterations 62
and 63. The page and receiver each define an `owner` value, set to `caller` and
`receiver` respectively. Its supplied fill originates in the page, and its fallback
originates in the receiver. The icon accepts ordinary SVG attributes and has no
Alpine directives or handlers of its own.

| Case, repeated in each browser | Ordinary component | Identity-preserving function | Caller-owned function |
|---|---|---|---|
| Direct icon, supplied fill and receiver fallback | Isolated; clicks update the enclosing button's state | Same | Caller scope for direct/fill; receiver scope for fallback; clicks update those states |
| Icon inside caller's x-if | Expected clone rejection before graph activation | Same | Correct caller scope and clicks after 20 removal/recreation cycles |
| Icon inside a teleported supplied fill | Expected clone rejection before graph activation | Same | Correct caller scope and clicks after placement outside receiver and caller |

The final run records Chromium **151.0.7922.34**, Firefox **153.0** and WebKit
**26.5**. Across three variants, three cases and three browsers, **15 cases activate
and pass their interaction assertions; 12 retain the expected rejection**. Every
accepted case has exactly one graph revision and no page or console errors.
Rejected cases report the matching directive's clone error, no unexpected additional
error, zero graph revisions and zero anchors, with Alpine startup incomplete.

Accepted cases click SVG paths, verify the enclosing buttons update the intended
state, and check exact final icon counts. The teleport must appear at its target;
the x-if icon must disappear and reappear on each cycle and retain caller scope
and click behavior afterwards. These assertions do not qualify native teleport
bubbling paths or `currentTarget`, detached-node cleanup, memory growth, keyed
morphing, server Events, arbitrary directives or all slot arrangements. The x-if
case is directly under the caller; only the teleport case originates in a supplied
fill. No independent icon lifecycle is promised by the proposed contract.

### Retained evidence and decision

The standalone harness and plan are in `benchmarks/inline_browser_probe/`. Reports
under `benchmarks/results/performance-render/` are:

- `inline-browser-initial-failure.json`: the first fixture's diagnosed rejection;
  `*.initial.txt` preserve its original sources and plan.
- `inline-browser-smoke.json`: Chromium with two x-if cycles.
- `inline-browser-initial-checks.json`: the first three-browser qualification.
- `inline-browser-main.json`: the final qualification with explicit local imports.

An intermediate smoke completed browser work but failed while writing its report
because the harness used the wrong path for the shipped Events JavaScript. No
result is claimed for that attempt. The corrected harness hashes sources before
launching browsers, so a missing artifact fails before doing browser work.
Independent review also identified that importing fixtures before setting local
package paths could select another installed Citry. The environment resolved both
packages to this worktree, but the final harness explicitly prepends their paths,
asserts their resolved files and records them. The earlier successful probe is
retained as `probe.py.smoke.txt` for its report hashes.

No production source or iteration 63 adapter changes. This qualification supports
continued work on an explicit caller-owned HTML contract; it does not add a
production optimization or a new timing point. The broader API and enforcement
rules, other component families, general slot topologies and the final repository
gate remain open. Next, broaden the semantic cases beyond icons: distinguish
presentation templates that can call other presentation templates from wrappers
that accept caller-owned content, and identify which need an independent boundary.

Independent technical and separate prose review checked the final harness, reports
and write-up. All 39 recorded hashes across the four reports resolve to current
or explicitly retained historical files; the final report also records both local
package import paths. Ruff formatting, lint and diff whitespace checks pass.

## Sixty-fifth iteration: render a button wrapper as a caller-owned function

The next architectural experiment targets the benchmark's **114 Button calls**.
Its fixed template chooses an anchor or a button and inserts its default body once.
It has no assets or instance-dependent data method of its own, but callers often
pass Alpine attributes. The useful distinction is therefore whether this wrapper
needs independent identity, rather than whether the resulting HTML contains Alpine.

### Treat the default body as caller content within the same owner

The prototype intercepts direct tags for the exact benchmark Button. It resolves
the existing tag inputs, validates and copies the resolved built-in values,
constructs the existing typed kwargs, and calls the existing data function without
an instance. It walks the unchanged compiled template with fresh template variables
but the caller's component, provides and ownership graph. The default outlet walks
its captured body with the original caller context, so caller expressions retain
their variables and ordinary nested components retain their source owner.

Both the wrapper and the inserted body now belong to that caller. There is no
wrapper instance, invocation, deferred descriptor or new slot placement to record.
Existing surrounding slots remain ordinary: their source can still differ from
the component that physically places the content. A ContextVar selects the special
outlet only while the fixed wrapper template runs, and is cleared while caller
content executes. Nested ordinary slots therefore use their normal implementation;
nested wrapper calls temporarily install their own outlet and restore it afterwards.

This removes more than identity. The function runs immediately during its caller's
body walk, so its data callback, body expressions and errors can occur before
previously deferred siblings. A focused test observes `sibling, button` with ordinary
Citry and `button, sibling` with the prototype. This is a demonstrated API change.
Registered wrapper data callbacks must be side-effect-free; component initialization,
data and completion hooks and slot hooks do not run for this template function.
Ordinary context-merge hooks still run as interior renders join. Custom merge hooks
remain unqualified.

The prototype accepts implicit default content and rejects named fills, component
client bindings, range metadata, globals and unsupported values in resolved kwargs.
Caller-side expressions and tag-level spreads still use ordinary input resolution;
a custom mapping can execute its methods there before validation. Independent review
caught wording that had incorrectly promised to reject such caller code. The fixed
callback, template and module data are trusted. This is neither a sandbox nor an
automatic classifier for arbitrary component classes. Root and descriptor-based
Button calls still use ordinary Citry because this experiment selects direct tags.

### Whole-page work and bounded correctness checks

| Large-page operation or record | Ordinary Citry | Button function | Removed |
|---|---:|---:|---:|
| Button data callbacks / default outlets | 114 / 114 | 114 / 114 | 0 |
| Component instances and generated IDs | 342 | 228 | 114 |
| Component invocations / ancestry / graph queue rows | 339 each | 225 each | 114 each |
| Source occurrences | 1,081 | 641 | 440 |
| Logical fills | 468 | 256 | 212 |
| Physical slot regions | 274 | 160 | 114 |
| Browser graph instances | 44 | 43 | 1 |
| Complete serialized bytes | 1,013,746 | 1,010,065 | 3,681 |

The 440 source occurrences comprise 114 wrapper calls, 98 nonempty supplied bodies,
114 slot outlets and 114 fallback bodies. The 212 logical fills comprise those 98
supplied bodies and 114 fallbacks. An empty fallback is recorded by ordinary Citry
even when the supplied body wins. Only one Button appears in this page's serialized
browser graph; observed Alpine attributes alone are not a count of browser graph
instances. The main reduction here is server work.

The complete large page and reduced-input page retain identical application HTML
and dependency payloads under the declared comparison. The comparison validates
raw browser manifests, then removes ownership manifests, range comments and component
markers and normalizes remaining render IDs/revision references. It does **not**
compare ownership graphs for equality or guarantee retained markers and relationships
are unchanged. All raw server snapshots and browser manifests are retained in a
compressed archive. Nonselected component execution counts match, and the main
harness independently asserts every recorded graph-table count at all four snapshot
points. These are useful checks with a weaker relationship oracle than iteration 63.

Focused server checks cover four changing input sets, escaping, attributes, link
versus disabled-button branches, nested Const values, nested wrappers, an ordinary
child and an ordinary caller slot inside wrapper content. One prepared body is
reused across changing roots. Ancestor error recovery matches; a supplied-body
exception leaves no stale outlet in the next root render. Seven unsupported cases
are rejected. Callback-order differences are retained explicitly.

Browser checks use Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5. The ordinary
reference retains isolated wrapper scopes; the candidate sees caller state for a
direct button and a supplied fill, and receiver state for a receiver's fallback.
Candidate-only clicks through passed Alpine attributes update the intended counters.
An ordinary child inside wrapper content retains its root marker and local state,
and cannot read either caller counter. Each accepted page has one graph revision
and no page or console errors. The reference is not clicked with those attributes,
so this is verification of the proposed caller-owned behavior, not a claim of equal
interaction behavior with ordinary Button components.

These cases leave general lifecycle, Events, keyed morphing, custom hooks, dynamic
registration, development provenance and arbitrary slot topologies unqualified.
A new public registration API and the final repository gate remain unfinished.

### Main timing: 5.73 ms saved with eight of eight joint wins

Eight fresh-process pairs compare ordinary Citry with the Button function alone.
Each variant runs first in four pairs; pair order uses seed 20261101, and each pair
shares a Python hash seed. Each worker performs six initial and 80 warm renders
with ordinary GC. IDs change every render. All 86 output strings remain live until
timing stops, about 87 MB per process, then every raw browser manifest is validated
and every application HTML projection is compared with an independently observed
render. No tests, browsers or builds overlap the main run. Use within-experiment
comparisons because retaining outputs changes allocation conditions.

| Variant | Median process mean warm wall time | Median observed second-render time |
|---|---:|---:|
| Ordinary Citry | 30.707545 ms | 34.518875 ms |
| Button function | 24.993963 ms | 25.402875 ms |

The **median paired warm wall saving is 5.731342 ms**, with **5.742481 ms saved in
CPU time and 8/8 joint wins**. The median paired warm ratio is 0.812738, or
**18.7% less warm-render time**. The median paired second-render saving is
9.103208 ms, based on one second render per worker. Separate medians in the table
are not paired differences. The main run passes the predeclared 0.25 ms and seven-win
screen. No additional build or distribution requirement is introduced.

This result combines removal of wrapper construction, deferred execution, independent
identity and default-slot recording. It does not attribute the saving to any single
one of them. The icon optimization from iteration 63 is not installed, and its
0.950 ms saving must not simply be added to this result. A combined implementation
needs its own measurement. Django is not rerun here, so this is not a new parity
measurement.

### Artifacts, review and next step

The implementation and plan are in `benchmarks/wrapper_function_probe/`. Retained
reports are `wrapper-function-{counts,contracts,browser,timing-smoke,timing-main}.json`
under `benchmarks/results/performance-render/`. Raw server snapshots and browser manifests
are in `wrapper-function-snapshots.json.gz`; its hash is recorded in the counts
report. The smoke pair with two warm samples is harness evidence, not the performance
decision. Sources referenced by that smoke but changed during qualification are
retained as `*.smoke.txt`.

The first activation check caught a case mismatch between the declared `Button`
name and the compiler's lowercase tag name, before any performance claim. The
first content comparison also exposed a harness mistake: its marker-removal pattern
left the `=""` suffix of ordinary root markers. Reading the raw HTML established
the cause; the corrected projection removes the complete marker attribute. These
were prototype/harness corrections, not changes to production behavior.

All 351 recorded source hashes across the five reports resolve to current or retained
historical files, and the compressed snapshot archive hash verifies. The native
artifact remains `321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.
Production and the adopted timeline remain unchanged. This passes an experimental
API screen and bounded browser checks, with the ownership comparison limitations
stated above. The next architectural step is to make caller-owned templates compose
with one another, then test the combined button, icon-label and SVG cases rather
than adding their separate savings. A general API, broader qualification, final
repository checks and full-page Django parity remain open.

Caller ownership and immediate execution are separate choices. A caller-owned
function could retain deferred scheduling, and a future API could define hooks
for template functions. This combined prototype does not measure those alternatives
or establish that every listed restriction is necessary for all of the saving.

Independent technical review recomputed the raw timing summaries, pairing, output
checks, operation counts, archive relationships and all retained hashes. A separate
prose pass covered the plan, code, reports, research summary and user-facing
explanation. Ruff lint, formatting and diff whitespace checks pass. No additional
renders or timing runs were needed during final review.

Follow-up qualification in iteration 66 found a limitation of this retained
Button-only prototype: it renders formatting-only whitespace as supplied content,
where ordinary Citry treats that body as an absent slot. The original checked
benchmark inputs did not expose this difference. Iteration 66 corrects the composed
adapter and keeps the unchanged Button adapter as the historical timing control.
This adds a concrete reason that iteration 65 is not a generally compatible or
adopted implementation; its recorded benchmark measurements remain historical evidence.

## Sixty-sixth iteration: compose caller-owned templates and separate scheduling

The user asked what losing identity and executing callbacks earlier means. These
are separate choices, so this experiment compares immediate and deferred execution
under the same caller-owned contract. It also tests composition across the large
page's 114 direct Button, 40 direct Icon and 41 HeroIcon calls. One Icon produced
outside a selected direct tag remains an ordinary component.

### One function registry, two execution schedules

The fixed registry selects the existing Button, Icon and HeroIcon classes by direct
tag and exact registry identity. The prototype checks and copies supported resolved
built-in input values, constructs each existing Kwargs schema and runs its trusted
data method without an instance. Each function has fresh template variables but
uses its caller's component and ownership context. Supplied content evaluates in
its original caller context. Component hooks and function-outlet hooks are omitted;
ordinary context-merge hooks remain active. None of these templates gains a new
per-call identity. This is an explicit experimental function contract, not an
automatic classification of arbitrary Component classes.

Immediate execution walks the function body as soon as the caller reaches its tag.
Deferred execution puts a private function-call descriptor through the existing
DeferredComponent queue. It records the surrounding physical slot region, restores
it for execution, and marks the returned interior render so finalization propagates
errors without finalizing its caller again. The function still has no invocation
or identity record. Ordinary child components retain their normal execution path.

Icon calls HeroIcon through the same registry. HeroIcon retains render-local pure
body reuse: nine distinct large-case bodies are built and 32 calls replay prepared
parts. Button and Icon do not cache complete output. Ordinary input expressions and
spreads run before resolved-value validation and can execute caller code. The fixed
templates, callbacks and module data are trusted. Named fills, component client
bindings, range metadata and globals are rejected; HeroIcon additionally accepts
no body and only declared ordinary SVG attribute names.

### Qualification found a whitespace difference and checks the two schedules

Reading ComponentNode._collect_slots exposed the static-whitespace rule. A focused
reproduction showed that iteration 65 and the first composed draft rendered a body
containing only formatting whitespace. Ordinary Citry omits that implicit slot.
The composed adapter now applies the same source-body check. Tests cover empty
bodies, static whitespace and whitespace produced by an expression, which remains
content. The unchanged Button-only control still demonstrates the mismatch. The
before-fix report is retained as `composed-function-whitespace-before.json`.

Four changing input sets check empty loops, escaping, attribute combinations, link
and solid-icon branches, and nested Const values. Reusing prepared templates across
four roots preserves the checked output. Nested errors leave no stale outlet state,
and an ordinary ancestor can recover an error from the function. Ten cases reject
unsupported inputs across the two composed schedules.

A nested ordinary child inside Button/Icon content is supplied by SourceCaller to
Receiver through a normal named slot. In both composed modes the child's logical
parent and invocation source remain SourceCaller; its physical region records
Receiver and the lexical owner SourceCaller. This checks a relationship that an
HTML-only comparison would miss.

The focused callback test records the following order:

| Mode | Data callbacks and supplied-content expression, in execution order |
|---|---|
| Ordinary | Sibling, Button, Icon, content expression, HeroIcon, child |
| Button-only control | Button, Sibling, Icon, content expression, HeroIcon, child |
| Composed immediate | Button, Icon, HeroIcon, content expression, Sibling, child |
| Composed deferred | Sibling, Button, Icon, content expression, HeroIcon, child |

The caller's on_render generator enters and finishes once in every mode. A separate
observer at the extension manager confirms that the caller's on_component_rendered
dispatch also runs exactly once. Deferred functions preserve the checked order;
this bounded result does not establish arbitrary lifecycle equivalence.

Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5 each pass reference, immediate
and deferred pages, nine pages total. Direct and supplied-fill function output can
read caller Alpine state; fallback output reads receiver state. Actual SVG-path
clicks in both function modes update the intended counters through the containing
buttons. An ordinary child retains its isolated local state and cannot read the
caller or receiver counters. Each page has one graph revision and no page or console errors.
The ordinary reference is checked for isolation and is not clicked with the
caller-oriented handlers, so this is qualification of the proposed behavior,
not equality of all browser interactions.

### Counts and ownership evidence

| Large-page work or output | Ordinary | Button only | Composed, either schedule |
|---|---:|---:|---:|
| Component instances and generated IDs | 342 | 228 | 147 |
| Invocation / ancestry / graph queue rows, each | 339 | 225 | 144 |
| Source occurrences | 1,081 | 641 | 470 |
| Logical fills | 468 | 256 | 206 |
| Physical slot regions | 274 | 160 | 120 |
| Serialized bytes | 1,013,746 | 1,010,065 | 987,414 |

Each of the 195 selected function calls still runs its data method, and the wrappers insert
154 default outlets. The deferred mode schedules exactly those 195 functions;
the immediate mode schedules none of them. Nonselected component execution counts
match the reference after subtracting the fixed selected class counts. Standalone
large and reduced probes and main timing each assert activation explicitly.

Both composed schedules produce matching complete application HTML and dependency
payloads under the declared metadata-removal comparison. The raw browser manifests
are validated before removing graph scripts, range comments and component markers;
remaining render IDs and revision references are normalized. This comparison is
weaker than an ordinary-to-candidate ownership equivalence check, because ownership
and isolation intentionally change.

In addition, every field of every captured server ownership snapshot matches
between the immediate and deferred modes after normalizing generated render IDs.
This holds for both the large and reduced cases. Raw snapshots and browser
manifests are retained for all eight case/variant combinations. Snapshot equality
is claimed only between the two composed modes for these observed renders, not
against ordinary Citry or for arbitrary applications.

### Timing method and remaining qualification

Eight blocks execute each of four variants in a fresh process. Four cyclic orders
and their four reversals place each variant in each position twice and each pair
in each relative order four times. Each worker runs six initial and 80 warm renders
with ordinary GC, changing generated IDs on every render and retaining all 86 output
strings until timing ends. All timed application projections and raw browser
manifests are checked after timing. The main timing harness also verifies fixed function counts,
ordinary component counts, all four snapshot-count vectors and immediate/deferred
normalized snapshot equality. No tests, browsers or builds overlap main timing.

The primary comparisons are ordinary versus each composed mode. Button-only versus
composed-immediate measures the combined architectural extension beyond iteration
65; deferred versus immediate measures scheduling under the same selected function
set. The ordinary 0.25 ms / seven-of-eight joint wall-and-CPU win screen applies.
There is no new native build or distribution requirement and no 1 ms threshold.
Retaining outputs changes allocation conditions, so compare within this experiment
and do not add savings from separate runs. Django is not rerun in this comparison.

General Events, keyed morphing, custom hooks, dynamic registration, development
provenance and arbitrary slot topologies remain unqualified. A public function API
and the final repository gate are still open. Production and the adopted timeline
remain unchanged.

### Main result: most of the gain survives deferred execution

| Variant | Median process mean warm wall time | Median observed second-render time |
|---|---:|---:|
| Ordinary Citry | 30.957734 ms | 34.624375 ms |
| Button-only function control | 25.274153 ms | 26.051105 ms |
| Composed immediate | 21.444535 ms | 21.955021 ms |
| Composed deferred | 22.419127 ms | 22.509021 ms |

| Paired comparison | Median warm wall saving | Median warm CPU saving | Joint wins | Median paired warm ratio |
|---|---:|---:|---:|---:|
| Ordinary to composed immediate | 9.473116 ms | 9.473375 ms | 8/8 | 0.692621 |
| Ordinary to composed deferred | 8.428723 ms | 8.430363 ms | 8/8 | 0.726005 |
| Button-only to composed immediate | 3.741162 ms | 3.741356 ms | 8/8 | 0.850614 |
| Composed deferred to immediate | 0.964700 ms | 0.963369 ms | 8/8 | 0.957176 |

The immediate composition uses **30.7% less warm time** than ordinary Citry by the
median paired ratio; deferred composition uses **27.4% less**. Both pass the
predeclared screen. The direct scheduling comparison saves **0.965 ms with 8/8
joint wins**, so the identity/slot contract can retain most of the measured gain
while preserving deferred order in the checked cases. Removing identity, wrapper
slot machinery and component hooks remains a combined change; this experiment
does not assign separate shares to those omissions.

The median paired second-render savings are 12.610396 ms for immediate composition
and 12.163124 ms for deferred composition versus ordinary Citry, based on one
actual second render per worker. Separate medians in the first table are not paired
differences. No full-page Django comparison or adopted production checkpoint is
added. The Button-only control here is measured again in the same four-way run;
its comparison does not add iteration 63 or 65's separately measured savings.

### Retained evidence and next architectural question

Sources and the predeclared plan are in `benchmarks/composed_function_probe/`.
Reports under `benchmarks/results/performance-render/` are
`composed-function-{counts,contracts,browser,timing-smoke,timing-main,audit}.json`,
the before-fix whitespace report, and `composed-function-snapshots.json.gz`.
The one-block, two-warm-sample smoke is harness evidence only; historical source
versions referenced by it are retained as `*.smoke.txt`.

The first deferred activation observer wrapped the inner ordinary render function
and therefore missed the prototype's intercepted function calls. Moving that
observer to the existing outer tracing entry point exposed all 195 scheduled calls
before main timing. Fixed expected counts now prevent the selected paths from
silently turning off in either benchmark case.

The final local audit recomputed all paired summaries and balanced orders from
raw samples, verified 2,752 timed render records, resolved all 354 recorded source
hash references against current or retained historical files, and verified the
archive hash and all 32 archived snapshot digests. Nine browser pages pass. The
native artifact is unchanged at
`321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.

This strengthens the semantic case: a presentation wrapper can compose other
presentation templates and ordinary child components without becoming a separately
owned component itself. The next architectural question is what representation
those function-only subtrees need. They currently still create nested interior
render objects and pass through ordinary settlement and serialization. A subtree
with no ordinary components, ownership effects or collected metadata may be able
to produce HTML directly. That requires a specific supported-case contract and
new measurement, especially when caller content has expressions, errors or effects;
it is not a claim that arbitrary function output can be cached or flattened safely.

Independent technical review separately recomputed the timing summaries, ordering,
source hashes and archived snapshot relationships. The separate prose pass covered
the sources, plan, reports, research log, experiment summary and user-facing result.
Ruff lint, formatting and staged diff whitespace checks pass. No additional renders
or timing runs were needed for final review.

## Sixty-seventh iteration: profile the remaining function render tree

Iteration 66 removed 195 component identities but still used the ordinary body
walker, render objects and serializer. This diagnostic asks which of that work
remains and whether the selected function subtrees contain anything besides text.
It makes no production change and claims no new wall-time improvement.

### Component removal leaves most render-object construction and traversal

Three separate processes profile ordinary Citry, composed immediate and composed
deferred rendering after six warmups. Each profiles twenty renders and retains the
combined call statistics, then observes constructors in a separate untimed render. All twenty profiled outputs
and the constructor-observed output equal the uninstrumented output within their
mode, using deterministic IDs. The application HTML projection also matches the
ordinary reference. Fixed counts require observing exactly 114 Button, 40 Icon and
41 HeroIcon function results in each composed mode.

| Work per large render | Ordinary | Composed immediate | Composed deferred |
|---|---:|---:|---:|
| Render objects constructed, including physical wrappers | 1,289 | 1,151 | 1,151 |
| Interior render objects constructed | 963 | 1,020 | 1,020 |
| Identity frames created from contexts | 1,015 | 1,031 | 1,031 |
| Body walks | 927 | 904 | 904 |
| Part-list visits while scanning deferred work | 1,020 | 1,036 | 1,036 |
| Calls checking whether a render contains deferred work | 195 | 436 | 241 |
| Serializer part-list visits | 1,284 | 1,146 | 1,146 |
| Context dependency merges | 546 | 583 | 592 |
| Element attribute resolutions | 505 | 501 | 501 |

Both composed modes construct 836 ordinary CitryRender objects, 120 physical-region
render wrappers and 195 FunctionRender objects. Of the total, 1,020 are interior
renders and 131 carry a component-root frame. The frame flag counts render objects,
not logical component instances: transparent output and physical wrappers prevent
using it as an instance count.

This changes the next design question. Removing full components saves lifecycle
and ownership work, but does not remove the nested representation used for template
control flow and content insertion. In fact, the composed paths create more interior
renders and identity-frame snapshots. The attribute path remains almost unchanged.
A further improvement needs to avoid constructing and revisiting those structures,
or reduce actual attribute work; counting fewer components is not enough.

Selected self times in the immediate-mode profile show where that work is charged:

| Operation | Calls per render | Instrumented self ms per render |
|---|---:|---:|
| Body walking and result assembly | 904 | 1.953 |
| Ordinary component lifecycle body | 147 | 1.382 |
| Attribute spread resolution | 368 | 1.263 |
| Attribute region resolution | 501 | 1.120 |
| Attribute formatting | 501 | 1.014 |
| Serializer part-list traversal | 1,146 | 0.846 |
| Deferred part-list traversal | 1,036 | 0.826 |
| Checking for deferred descendants | 436 | 0.771 |
| Identity-frame construction from contexts | 1,031 | 0.488 |

These are selected cProfile self times, not a complete phase breakdown. The full
instrumented totals are 79.997 ms ordinary, 60.182 ms immediate and 61.669 ms deferred;
they are not the roughly 31/21/22 ms warm wall times from iteration 66. Profiler
overhead changes relative costs, cumulative rows overlap, and even self-time savings
here do not predict the saving from a representation change. Every raw profile row
is retained rather than presenting selected rows as the whole render cost.

### A text-only body can still carry collected metadata

At each FunctionRender constructor, the observer examines the result before deferred
descendants settle. It records text, component-root renders, physical regions,
deferred ordinary components, deferred function calls, placeholders, context data,
error-tainted contexts, and differing frame owners or ownership graphs. Physical
wrappers are recognized before the CitryRender superclass. It does not mutate parts.

| Function | Calls | Immediate: text only and no context data | Deferred: text only and no context data |
|---|---:|---:|---:|
| Button | 114 | 40 | 38 |
| Icon | 40 | 16 | 0 |
| HeroIcon | 41 | 41 | 41 |

In the immediate mode all selected results contain finished text, with no ordinary
component roots, physical regions, placeholders or deferred descendants. However,
74 Button results and 24 Icon results contain nonempty dependency data in their
contexts. Those wrappers do not declare their own assets. Their supplied content
uses the caller's context, whose dependency records are copied into the function's
fresh context and subsequently merged back toward that caller. The dependency
extension's ordered dictionary makes that merge idempotent, but the repeated
wrapping, dispatch and copying still happens.

In the deferred mode every Icon result contains a queued HeroIcon function call
when constructed. None contains a deferred ordinary child in this large case.
Separating those cases matters: a pending presentation function could be handled
by a function-specific execution plan, whereas an ordinary child still needs its
component lifecycle and ownership. Seventy-six deferred Button results and 32 Icon
results contain dependency data. The overlapping obstacle counts are not a
partition, and ancestor/nested subtree observations must not be summed as page-wide
allocations. All observed function subtrees retain one frame owner and one ownership
graph, and none has an error-tainted context in this successful fixture.

This is descriptive evidence, not a safe-to-flatten predicate. Even empty extra
data does not suppress on_render_context_merge hooks, and merging propagates an
error-tainted flag. The serializer can also emit transparent-instance caps around
same-owner interior renders. A new text representation must preserve needed
metadata, error propagation, ownership caps and ordinary descendants, or define
and enforce an explicit restriction. The existing whole-page fixture cannot prove
those rules for arbitrary input or caller components.

### Next experiment and retained evidence

The next candidate is to emit text into a shared output buffer while executing a
selected presentation function and its control-flow bodies. Keep actual component
children and physical regions as structured parts, and keep collected metadata
separate from variable scopes. This would avoid building a tree only to discover
later that its leaves were all text. The immediate function mode is the first
comparison because its selected subtrees already finish synchronously. Queued
function execution remains a separate case; do not silently change its order.

The candidate must test ordinary nested components, supplied-slot ownership,
transparent callers, context merges, metadata and errors. A dynamic value that
produces a component or retained render cannot be evaluated twice to select a
fallback. Use the existing branch-selection and loop-iteration helpers where they
preserve the needed checks. Keep HeroIcon's existing pure-body benefit, compare
against the unchanged composed implementation, and measure the complete page.

Sources are `benchmarks/function_tree_probe/call_profile.py` and `plan.md`; reports
are `function-tree-profile-{reference,immediate,deferred}.json` under
`benchmarks/results/performance-render/`. Each report records 182 source hashes, including
the executed earlier adapters, scenario/observation helpers, Python runtime and core
wrappers, plus the unchanged native artifact hash. No adopted checkpoint or Django
parity claim is added.

Independent technical review verified all 546 recorded source-hash references,
constructor and obstacle summaries, call counts, selected self times and aggregate
profile totals. A separate prose pass covered the source, plan, reports, research
log, experiment summary and proposed result. Ruff lint, formatting and staged diff
whitespace checks pass. No additional rendering or profiling was needed for review.

## Sixty-eighth iteration: emit function text into a shared parts buffer

Iteration 67 found that function composition kept most interior-render construction
and traversal. This candidate changes how the selected immediate functions produce
their output. It compares against iteration 66's immediate implementation, not
ordinary Citry, and preserves the same selected Button/Icon/HeroIcon contract.

### Build text directly and retain structured child boundaries

The candidate walks a selected function's body into one ordered parts list. An if
node uses its existing branch-selection helper; a loop uses its existing iteration
helper, retaining variable checks, bindings and empty branches. A loop with
precomputed text retains its ordinary render path and validation. Nested selected
functions append to the same list. The function's default outlet executes supplied
content with the original caller variables and ordinary handling of caller slots.
Values are evaluated once; no speculative rendering is repeated to choose a path.

Wrappers keep fresh variable scopes but share their caller's collected-data
dictionary. Ordinary completed foreign renders, deferred child components, physical
regions and placeholders remain structured parts. A function whose complete output
is text returns one string; mixed output retains a FunctionRender so the scheduler
can locate ordinary child work. HeroIcon retains the existing render-local pure-body
key and replay mechanism, storing a single text part when its fixed body completes
without graph effects, collected metadata or an error-tainted context.

Transparent callers use iteration 66's implementation because the serializer can
surround their interior output with identity markers. The optimization does not
infer from empty metadata alone that those frames can be discarded. Whole-result
replacement and recovery hooks are tested separately. Hooks that inspect or modify
function interior parts, and arbitrary custom merge hooks, remain unqualified:
the intermediate structure and internal merge observations deliberately change.
This is an additional explicit restriction on the experimental function contract.

### Activation caught an unintended interaction with pure-body reuse

The first large-page render matched complete serialized HTML and every server
ownership snapshot. But it ran only 39 Icon and 40 HeroIcon callbacks, rather than
40 and 41. Returning text allowed an enclosing pure component to capture that
function output as a reusable body part. Its next matching occurrence then skipped
the nested function callbacks and one SVG replay.

This was not accepted as a direct-emission speedup. When a function's caller is
pure, the candidate now retains a small FunctionRender containing the joined text.
The existing pure capture rejects that subclass as a detached text part, preserving
the live function call. Both the large and reduced page then matched full HTML,
all ownership snapshots and every function/outlet/replay count. The first and
corrected observations are retained as `function-text-first.json` and
`function-text-second.json`. Complete function-output reuse could be a separate
purity-contract experiment; it is excluded from this comparison.

### Qualification and construction counts

| Constructed render object | Immediate control | Direct emission |
|---|---:|---:|
| Ordinary CitryRender | 836 | 487 |
| PhysicalRegionRender | 120 | 120 |
| FunctionRender | 195 | 3 |
| Total | 1,151 | 610 |

This removes 541 render-object constructions in the large case while keeping all
114 Button, 40 Icon and 41 HeroIcon data callbacks, 154 default outlets and 32 SVG
replays. The three retained function results protect live calls under pure callers.
Operation counts are evidence of the representation change, not a timing result.

The large and reduced page comparisons require exact serialized HTML, including
framework comments, markers and dependency payloads, plus complete server snapshots,
ordinary component calls, generated IDs and function counts. Eight additional cases
check empty/changing loops, loops containing ordinary children with dependencies,
transparent callers, completed foreign output mixed with deferred children, whole
caller-output replacement containing an ordinary child and supplied slot, failure
after composing a child, and a recovered child error. Both implementations propagate
the recovered child's error-tainted state to the caller. Unsupported resolved values
produce matching error text; independent review caught and corrected an accidental
difference in the input validator's error translation.

The retained iteration 66 contracts also run with direct emission in their immediate
mode. They cover changing inputs, escaping, static versus expression-produced
whitespace, supplied-slot ownership, hot roots, outlet cleanup, invalid arguments,
callback/content order and exactly-once caller completion. Their other modes retain
the earlier implementations, and the report identifies that substitution.

The retained browser fixture runs in Chromium 151.0.7922.34, Firefox 153.0 and
WebKit 26.5. All nine pages pass: three direct-emission candidate pages and six
ordinary/deferred reference pages. SVG-path clicks update the correct caller or
receiver counters, and an ordinary child retains its isolated state. The report
labels which mode uses the new implementation. These are bounded checks, not
general Events, morphing, custom-hook or arbitrary-depth qualification.

### Timing method

Eight pairs run each implementation in a fresh process, with four pairs in each
order shuffled using seed 20261104. Pair members share a Python hash seed. Each
worker reuses iteration 66's measured loop: six initial renders and 80 warm renders,
ordinary GC, changing generated IDs, and all 86 outputs retained until timing ends.
Every paired raw output digest must match, as must application projections, fixed
activation records, normalized full-snapshot digests and the native artifact hash.
The worker validates raw browser manifests and graph-count vectors after timing.
Measured source files and the native artifact are frozen and hashed by the parent.
No tests, browser checks or profilers overlap the main run.

The predeclared screen is at least 0.25 ms median paired warm wall saving and at
least seven of eight pairs improving both wall and CPU time. There is no new build
requirement and no 1 ms threshold. The short one-pair/two-warm-sample smoke checks
the harness only; source versions changed after it are retained as `*.smoke.txt`.
Do not add savings from separate experiments or treat this comparison as a new
ordinary-Citry-versus-Django measurement. Production and the adopted timeline
remain unchanged.

### Main result: 1.367 ms saved beyond immediate composition

| Variant | Median process mean warm wall time | Median observed second-render time |
|---|---:|---:|
| Iteration 66 immediate control | 21.252246 ms | 21.602000 ms |
| Direct text emission | 20.128368 ms | 20.124709 ms |

The median paired warm saving is **1.367472 ms wall and 1.367537 ms CPU**, with
**8/8 joint wins**. The median paired warm ratio is **0.936176**, or **6.4% less
warm time**. Actual second renders save **1.392187 ms by median paired difference**.
Separate medians in the table are not paired differences. The candidate passes the
predeclared screen and advances experimental qualification under the additional
interior-structure restrictions; it is not adopted production behavior.

All 1,376 timed render records were checked. Every control/candidate pair has
identical complete raw output digests, application projection digests, activation
records and observed normalized snapshot digests. The local audit recomputed the
summary and balanced order, verified 392 recorded source/native hash references
against current or retained smoke sources, and confirmed the unchanged native
artifact. Its hash remains
`321af83391e96c3770513de105b53f51e0cb2af60ea254857faa85b8fc9f71c7`.

Sources and the predeclared plan are in `benchmarks/function_text_probe/`. Reports
under `benchmarks/results/performance-render/` are
`function-text-{checks,browser,timing-smoke,timing-main,audit}.json`, plus the first
and corrected activation observations. The reused iteration 66 contract result is
embedded in the checks report with its mode substitution explicitly identified.
The next public-API discussion must distinguish this representation change from
iteration 66's independent choice between immediate and deferred execution.

### User direction: an explicit Component.simple flag with strict validation

The user proposed `Component.simple = True`, with errors when a class or its
template/assets/methods fail the requirements. This is the next implementation
direction. Iteration 66 has only an exact-class allowlist, not a general classifier
or public flag: fixed callbacks and templates were manually audited, while the
adapter checks a limited set of input and call-site restrictions.

A public flag needs a documented, enforceable contract covering inherited
declarations, templates loaded through providers, instance-dependent methods,
component/slot hooks, assets, kwargs, content and identity. It also needs consistent
handling of direct tags, Python-composed component values and root renders, rather
than making optimization depend silently on how a class was called. Scheduling is
a separate choice and must not be changed implicitly while exposing the flag.
Unsupported declarations or invocations should raise explicit errors, not silently
fall back to the ordinary component pipeline. Arbitrary Python callback purity
cannot be inferred from the absence of assets or from a method's name; the method
contract must state what the implementation can actually enforce.

### Independent review

A separate reviewer checked the implementation and final artifacts, recomputed the
paired statistics, verified all 1,376 timed records and 392 source/native hash
references, and confirmed the construction and browser counts. It found no
blockers for committing the experiment. Its separate prose pass covered all five
probe sources, retained smoke sources, report text and both research-log updates,
with no remaining findings. Production adoption and public API qualification remain
separate work.

## Public simple-component API design checkpoint after iteration 68

The user requested a dedicated design document for `Component.simple = True`.
[`component_simple.md`](component_simple.md) now records the proposed public
contract, prior art, strict class/template/call validation, caller ownership,
deferred scheduling, Python composition and root handling, and the implementation
and qualification stages. It is explicitly a design in progress; the public flag
and its runtime are not implemented at this checkpoint.

The design separates loss of instance identity from both immediate callback
execution and the `pure` body-reuse promise. It proposes the inherited default
data method or an explicit synchronous static method, rather than trying to prove
that arbitrary instance methods do not use `self`. Default-content representation
and the exact freezing/invalidation mechanisms remain prerequisites for the
implementation stage.

Independent technical review identified several concrete gaps, now recorded in
the document: replacement values and dynamic-selector forwarding must be checked
alongside ordinary expression values; globals retain ordinary precedence;
template validation must follow lexical ownership before Const pruning; previously
rendered values retain their existing owner; and deferred scheduling alone does
not prevent recursive serialization of same-owner interior renders. The depth
qualification must complete `serialize()` or `str()`. The review also corrected
the distinction between experiments 61-62 (no instance, retained identity) and
the unmeasured alternative of retaining an instance while skipping hooks.

The reviewer separately checked the draft against the house style; its suggested
wording changes were applied. This checkpoint adds no production code or new
timing result, and leaves the adopted performance timeline unchanged.

## Simple API implementation: declaration validation

Added the private `citry._simple_declarations` validator and 36 focused tests.
This is preparation for the public flag: it is not called by class creation or
the renderer yet, and it changes no production render behavior or benchmark time.
It returns the checked data callback and schema references for subsequent runtime
integration.

The checks cover effective inherited assets, paired asset resets, authored
extension configuration versus generated defaults, core/object method overrides,
instance descriptors, synchronous static callback signatures, and the permitted
slot schema. The callback signature is checked using its actual code/defaults;
forged `__signature__` or `__wrapped__` metadata cannot make an invalid call shape
pass. Static descriptor inspection also avoids triggering a helper object's
`__class__` property or its metaclass during classification.

Independent review exposed four classes of defect in the first implementation:
asset fields checked independently from their paired inheritance semantics;
method masking through object methods or private-name exemptions; hidden slot
constructor behavior; and descriptor detection executing author-defined lookup.
The fixes use existing asset-pair resolution, protect the effective base methods,
inspect descriptor types statically, and constrain Slots to plain authored field
declarations. Follow-up checks cover custom `__post_init__` descriptors,
class-valued descriptors, InitVar/ClassVar fields and `init=False` as well. A
library test checks distinct materializations of the same definition into two
engines with their effective input schemas.

The stricter Slots rule is recorded in `component_simple.md`. Arbitrary custom
constructors cannot be proven harmless from their field metadata. The chosen
initial schema permits absent content or one optional default field, while kwargs
and template-data schemas retain ordinary adapter choices. Public flag wiring,
mutation rules, template checks and the shared rendering path remain the next
implementation work. No performance gain is claimed for this preparatory area.

The final independent technical review found no remaining blocker for this
private validator. Its separate prose pass covered both code files and both
documentation updates; the wording was corrected to distinguish the enforced
slot field/default/constructor rules from the illustrative Slot annotation.
Focused pytest passed all 36 cases and Ruff passed. Broader rendering checks
belong to the next integration stage because no render path calls this helper yet.

## Simple API implementation: deep interior traversal

Public runtime integration exposed a recursion limit outside the component
scheduler. A chain of 1,100 simple calls built deferred work successfully, but
rescanning its completed interior renders recursed in `_scan_deferred_parts`.
Serialization's `_append_frame_parts` had the same recursive shape. Both walkers
now keep explicit stacks. Child tasks remain in source order, cross-context
merges follow the affected children, and serialization preserves physical caps,
component placeholders and individual placeholder occurrences.

This is committed as a separate runtime area before the public flag integration.
Two regression tests exercise deep interior renders without depending on the
simple API: one checks the deferred task and all 1,100 context merges; the other
checks complete serialization and exact text order. The in-progress public test
also completes render and serialize for a 1,100-level simple component chain.
Independent technical review compared each walker against the previous committed
implementation on 300 randomized shallow cases, including shared contexts,
physical wrappers and capped serialization, and found identical results.

The broader in-progress runtime passed 325 selected tests covering simple
integration, declarations, deferred rendering, ownership, manifests, provides and
value dispatch. Adding the two traversal tests brought that batch to 327 passing
tests. A separate temporary package snapshot containing only the staged walker
changes over the committed runtime passed all 258 relevant ordinary-runtime and
traversal tests. Ruff passed, and the independent prose review's two wording
corrections were applied. These are targeted checks, not the final repository
gate. No performance saving is claimed for this traversal change; balanced benchmarks
remain pending until the public contract is qualified.

The remaining integration work includes dynamic selector forwarding, transparent
owner placement, declaration mutation coverage, error recovery and dependencies,
public documentation and type/tooling consumers, browser qualification and the
final gate. Review has already identified a concrete transparent-owner problem:
serializing several interiors belonging to one transparent caller can emit that
caller's instance caps repeatedly. The public path must preserve one valid
placement for that caller without restoring an independent simple instance.
Python slot evaluation, explicit provided-value overrides and separate nested
render roots also required context propagation fixes; these remain in the
uncommitted integration and have focused regression coverage. The design remains
in progress, and the adopted performance timeline is unchanged.

## Simple API implementation: one placement for a transparent caller

The transparent-caller failure came from confusing an output fragment's owner
with a new physical instance boundary. A transparent caller's outer result,
control-flow results and supplied-content results can all carry the same owner
ID. The serializer emitted that ID's cap pair at each interior it encountered.
Simple composition exposed another such interior, but an ordinary transparent
component with a conditional and a slot fill reproduced the defect too.

Manifest preparation now chooses one enclosing render object for each included
transparent instance. Nested fragments with that identity share its placement;
serialization emits the instance pair only at the chosen object. Disconnected
uses of an included transparent identity raise an error. The check runs only
when a manifest is prepared and includes that identity. Plain text rendered
without an ownership manifest keeps its existing behavior.

This separates physical placement from lexical ownership without adding a field
to every render frame or changing the detached cache artifact format. The
alternative of explicitly marking each whole transparent output would require
carrying another root flag through construction, replacement, artifact export and
replay. The calculation reads the final render tree and skips its extra traversal
when no transparent instance is included. Its performance
cost has not been measured yet; this is a correctness prerequisite for public
simple support, not a claimed speedup.

Three new server tests check one pair across ordinary control flow and fills,
disconnected output rejection, and missing placement rejection. A public-simple
regression covers the originally reported nested receiver. The selected ordinary
ownership, deferred, replacement and cache suites passed 383 tests. The new
ordinary and simple browser cases passed in Chromium, Firefox and WebKit (six
cases); existing ownership-manifest and cache-replay browser suites passed all
84 cases across those browsers.

Independent technical review also checked six direct, conditional and nested
fragment-cache outputs, verifying every cap count, balanced nesting and nearest
physical parent-region relationships. A separate public component-cache miss/hit
case executed the transparent child's callback only once across two renders and
preserved all eight caps on both outputs. No placement or replay defect was found
in those bounded checks. The broader public API remains in progress, with
forwarding, mutation/error coverage, tooling and final qualification still
outstanding. No benchmark or adopted-timeline change is claimed here.

The staged placement change was also tested without any in-progress simple code:
a temporary package snapshot containing only this area over the prior committed
runtime passed the same 383 ordinary tests. Ruff passed. Independent prose review
covered both runtime files, both new ordinary test files, the design subsection,
this research entry and the release note; its two clarity edits were applied.

## Simple API implementation: initial public runtime integration

The experimental branch now wires `Component.simple = True` into class creation
and rendering. Each effective simple class is checked before registration, gets
an inherited exact-boolean flag, and freezes its checked class declarations.
Library definitions expose the flag, inherit it through the merged C3 order, and
keep it fixed before publication as well. Materialized classes receive the
ordinary declaration checks. Slot schemas are checked again for rebinding or MRO
changes before their constructors run; Python-managed annotation caches do not
invalidate a plain declaration.

Direct tags decide before collecting ownership for a new component boundary.
They retain caller variables for lazy default content and queue the simple body
at the normal deferred stage. The body gets fresh template data and globals but
uses the caller's instance and ownership graph. Python-composed values render at
the ordinary immediate expression stage, with the actual insertion context.
Standalone simple roots use the existing transparent template-root owner.
Settling a simple result does not finalize its caller again; the caller still
runs its own hooks at the normal stage. Ordinary children keep their own
construction, hooks, dependencies and identity.

The initial integration preserves structured render parts and context merges.
It does not yet apply iteration 68's text-buffer implementation. Default content
is exposed to static data callbacks as a real Slot. Pure bodies with outlets stay
live because empty content must not be cached over a later supplied value; pure
bodies without outlets can use the existing body cache. The simple callback itself
still runs for every invocation. Template preparation validates every generated
branch and nested template, including branches not reached by the first inputs,
and rechecks after a loaded template record changes.

Dynamic selectors retain their ordinary input/render hooks and choose their
target at the existing stage. When they choose a simple class, their existing
instance owns the result and completes the pending invocation; the selected
simple class gets no instance. Explicit fill/range presence travels separately
from kwargs through selector subclasses and forwarding chains, so selecting the
target later does not bypass restrictions. Python roots and already-bound aliases
do not bind slot supplies twice. Ordinary targets keep their forwarding path.
This retains dynamic-selector overhead rather than claiming the direct-tag cost.

Review and broader tests found concrete integration defects: an empty pure outlet
could hide later content; base-order inspection differed from the merged C3 order;
source provenance followed the caller rather than the simple template; explicit
Python Slot calls lost their insertion context; slot overrides were discarded;
an explicit nested root inherited the previous engine's ambient context; ordinary
runtime annotation metadata was rejected; changing a Slots base bypassed the
mutation guard; and custom selectors lost restrictions or bound fills twice.
Focused tests now cover these cases. The broad Python suite also found twelve
existing lightweight-context tests that do not carry a template record; source
capture now preserves that adapter behavior while preferring real lexical records.

This is an implementation checkpoint, not adoption or a new performance result.
Public user documentation, catalog/tooling decisions, additional error/mutation/
concurrency qualification, balanced ordinary/simple/Django measurements and the
full repository gate remain subsequent work. The research timeline retains the
previous adopted measurements until that work provides comparable evidence.

Validation at this checkpoint: 4,908 Python tests passed, with five skips, one
expected failure and 556 browser cases deselected. The six focused simple browser
cases passed across Chromium, Firefox and WebKit. Package mypy passed, including
the Linux branch and library authoring type surface, and Ruff passed. These checks
do not replace the final repository gate or performance measurements.

Independent review also exercised simple replacements after success and after a
child error. Only the selected ordinary descendants remained active, the caller
hook ran once, and recovered-error taint survived. One additional mutation window
was found: a kwargs adapter could replace Slots after the initial check. The
single check now runs after template preparation, kwargs adaptation and raw-slot
creation, immediately before invoking the Slots constructor. A focused regression
rejects that mutation without executing the changed constructor.

After closing that mutation window, the simple and dynamic-selector suites passed
113 tests. Independent technical review found no remaining blocker for this
checkpoint. A separate prose review covered the runtime, tests, design, research
entry, release note and delivery text; its four clarity corrections were applied.

## Simple API qualification: ordinary attribute spreads

The first public-API benchmark smoke render exposed an integration gap before
timing could be accepted. The default i18n template hook wraps every ordinary
`c-bind` region, even with no translation catalog, while the simple validator
rejects unrecognized wrappers. That prevented the benchmark's Icon from rendering.

The hook now keeps ordinary attribute nodes for simple classes. Simple template
validation rejects literal `$c-tr` declarations across all branches, and ordinary
spread resolution raises a simple-specific error if such a key arrives later.
This preserves plain attribute merging without borrowing the caller's translation
collector. Focused coverage includes merged classes, escaping, adjacent text
expressions, inactive bindings, later dynamic bindings, and a caller with active
translation bindings on both sides of the simple child.

The benchmark adapter now uses only public class declarations, preserving all
callback bodies and templates. It also reaches one Python-composed Icon missed
by the earlier tag-only prototype: 41 Icon callbacks, 41 HeroIcon callbacks and
114 Button callbacks remain live, with 146 identities versus 342 ordinary ones.
The first comparison smoke check preserved all projected application HTML. Its
two warmed samples are not a performance result; balanced measurements follow
the reviewed fix.

The related i18n, HTML-attribute, selector and simple suites passed 258 tests
before the last added regressions. The final simple and i18n suites passed 78
tests. Linux package mypy and Ruff passed. Independent technical review found
that skipping i18n wrapping also skipped structural-attribute validation; the
common simple attribute check now covers literal, expression and backtick-valued
keys, with inactive component-call regressions. A separate prose review covered
the fix, tests, design, this entry and the benchmark harness and plan.

## Simple API measurement: public declarations on the large page

The first balanced measurement of the public implementation at `1c70f91` saves
**8.424893 ms (26.63%) in median paired warmed render time** versus ordinary
Citry. Wall and CPU time improve in all six blocks; the paired CPU saving is
8.425225 ms. This measures the actual public flag and static callback contract,
including validation and deferred execution for direct tags. It does not use the
earlier prototype adapters or iteration 68's shared text buffer.

| Engine and declarations | First render, ms | Actual second render, ms | Warmed render, ms | Output bytes |
| --- | ---: | ---: | ---: | ---: |
| Ordinary Citry | 73.623 | 36.365 | 31.589 | 1,013,746 |
| Citry, Button/Icon/HeroIcon simple | 60.192 | 23.425 | 23.215 | 986,602 |
| Existing Django scenario | 18.570 | 10.996 | 11.032 | 456,422 |

Each table cell is a median across six fresh processes; the warmed cell is the
median of each process's mean of 80 retained-output renders. The actual second
render is sample two, before the remaining four initial renders. Median paired
second-render saving is 12.563354 ms (34.52% by paired ratio). The difference of
the table's medians is not the median paired saving. Simple remains 2.1044 times
Django's warmed render time on this page, so this does not reach parity.

All six permutations of ordinary/simple/Django run once, balancing position.
The report retains 1,548 wall/CPU observations, first and second samples, GC
counters, raw output digests and byte counts. Normal GC remains enabled and all
86 output strings stay alive through each worker's timed loop. Python is 3.14.3;
Django is 6.0.6 and django-components is 0.151.1. The native release artifact is
unchanged from the accepted baseline. All 375 recorded source/artifact hashes
matched after timing, and the gzip capture archive's checksum was verified.

Every timed Citry output passes the existing application-content projection and
its emitted browser manifests validate. The two Citry variants have matching
projected content and retain the same observed component calls and 114 Button,
41 Icon and 41 HeroIcon data callbacks. The public flag also covers one Python
Icon insertion, so it removes 196 identities, compared with the earlier
prototype's 195. The observed graph changes from 342 to 146 logical instances,
1,081 to 468 source locations, 339 to 144 invocations, 468 to 205 fills and 274 to
119 physical regions. Complete snapshots and manifests are archived from one
instrumented render after timing in each Citry process; callback and server graph
counts are not independently instrumented during the timed loop.

The output contract deliberately differs when these classes opt into simple.
The projection removes ownership markers and replaces generated IDs with stable
names; it does not prove equivalence of independent component identity or hooks.
Django also emits different output and uses the vendored HTML-attribute helper.
This is the first public-API performance result, not completed feature adoption,
and the historical adopted timeline remains unchanged. Public documentation and
tooling, broader qualification and the final repository gate remain pending.

Evidence: [timing report](../../benchmarks/results/performance-render/simple-api-timing-main.json),
[complete observed captures](../../benchmarks/results/performance-render/simple-api-timing-main.captures.json.gz),
and [measurement method](../../benchmarks/simple_api_probe/plan.md).

Independent audit recomputed the reported savings and ratios, checked every
source hash and the archive checksum, confirmed all six process orders and 1,548
observations, validated the 12 archived manifests, and matched all 48 snapshot
field counts to the report. It found no technical blocker. These checks read the
saved evidence; they did not rerun the benchmark.

## Public simple follow-up: remaining representation and component cases

After integrating the public API, fixing plain attribute spreads and measuring
the public flag against ordinary Citry and Django, this follow-up profiles the
committed implementation to record directions for future work. Optimization
experiments are now paused at the user's request. This diagnostic makes no runtime
change and claims no additional speedup.

Separate ordinary and simple processes profile twenty renders after six initial
renders, then observe constructors in one render and component preparation and
finalization intervals in ten more. All observed complete outputs match their
own uninstrumented reference with identical IDs. Unlike the balanced benchmark,
this diagnostic resets IDs to the same values each time. The cProfile totals are
83.483 ms ordinary and 63.718 ms simple; they must not be confused with the
31.589/23.215 ms warmed measurements.

| Work per large render | Ordinary | Public simple |
| --- | ---: | ---: |
| Ordinary render objects | 1,015 | 788 |
| Physical-region render objects | 274 | 119 |
| Simple render objects | 0 | 196 |
| All render objects, excluding identity frames | 1,289 | 1,103 |
| Identity frames | 1,015 | 984 |
| Body walks | 927 | 896 |
| Attribute-region resolutions | 505 | 505 |
| Attribute-spread resolutions | 372 | 372 |
| Deferred-part traversal calls | 343 | 343 |
| Serializer-part traversal calls | 325 | 129 |

Removing 196 component identities only removes 186 render-object constructions
and 31 identity-frame constructions. Nearly all attribute work remains. The
iterative walkers handle many interiors within one call, so their call counts
are not counts of visited parts. In the simple profile, body walking takes 2.090
instrumented self ms, deferred-part traversal 1.867, serializer-part traversal
1.360, attribute-spread resolution 1.259, attribute-region resolution 1.110 and
attribute formatting 0.999. These selected self times are not a full page
breakdown and do not predict the saving from removing an operation.

The separate component timers identify three cases worth distinguishing:

1. **Presentation classes already simple.** Button enters component preparation 114 times;
   Icon and HeroIcon enter it 41 times each. They avoid instances but continue to walk
   attributes and construct interiors. This supports qualifying a representation
   that writes plain output directly while retaining real child boundaries, as
   iteration 68 explored. The public API's deferred order, ordinary descendants,
   merge hooks, error propagation and transparent owners must remain explicit.
2. **Remaining classes with no assets or instance-dependent data method.**
   Thirteen rendered declarations pass this initial screen, accounting for 32
   calls: MenuList, Table, Breadcrumbs, ListComponent, TabsStatic,
   ProjectStatusUpdates, ProjectOutputBadge, ProjectOutputs,
   ProjectOutputsSummary, ProjectInfo, ProjectNotes, Navbar and ProjectPage.
   Their observed ordinary calls supply no slots. Some produce ordinary children
   and named fills for those children; those differ from accepting named content
   themselves. A group opt-in experiment should run the real declaration/template
   validators and preserve every callback before claiming eligibility or savings.
   ProjectPage is a root, so its simple form still needs a transparent root owner.
3. **Components whose current behavior needs a separate decision.**
   ExpansionPanel has JS and named header/content slots; Form has JS and default
   content; Tags reads `self.raw_slots` and has a named fallback outlet; TabItem
   has an instance-dependent data method and a render hook. They do not satisfy
   the current simple contract. The built-in DynamicElement also renders 15 times
   through a transparent component plus default slot, despite producing a dynamic
   HTML tag. It is a distinct architectural candidate, but its ownership, morph
   metadata and hooks cannot be discarded just because its final output is HTML.

In the separate preparation timers that subtract nested measured calls, Button takes 2.388 ms,
DynamicElement 2.110, ExpansionPanel 2.000, Icon 1.199, Tags 1.147 and
ProjectOutputAttachments 1.131. These intervals include supplied content and other
work they execute; they are not estimates of removable component overhead.
Nested instrumentation setup and cleanup can be charged to enclosing intervals.
Scheduler and final serialization outside those intervals are absent, so the
numbers must not be presented as a complete percentage split.

Parked research directions are qualifying the remaining presentation declarations
as a group using the public flag, then investigating a representation that avoids
repeated attribute and interior-render work. Another small declaration group alone
is unlikely to close the roughly twofold gap to Django. No further optimization
experiment is scheduled during the documentation and handoff work.

Evidence: [diagnostic method](../../benchmarks/simple_api_probe/diagnosis.md),
[ordinary profile](../../benchmarks/results/performance-render/simple-api-diagnosis-ordinary.json)
and [simple profile](../../benchmarks/results/performance-render/simple-api-diagnosis-simple.json).
Independent technical review verified both sets of 374 hashes, constructor and
caller counts, profile self-time totals, unchanged attribute counts and the
thirteen-class/32-call screen. It found no blocker and performed no rerenders.

Separate prose review covered the diagnostic harness, method, reports and this
entry. Its attribution and terminology corrections were applied, and the research
directions are explicitly parked in response to the user's pause.


## Final handoff: documentation, publication and integration checks

Optimization experiments are paused at the user's request. This stage documents
the public simple API, refreshes benchmark images and checks the retained work.
It is not another optimization iteration.

The public guide explains declaration and call restrictions, callback timing,
caller ownership, default content and the difference from `pure` and `Const`.
The performance page, component guide, navigation and API docstrings link it.
The Citry changelog records the opt-in API and the retained runtime improvements.

The publication report compares five configurations in ten balanced fresh-process
blocks, retaining 80 warmed outputs per worker with normal garbage collection.
It records 4,300 timed outputs plus 20 separate Citry ownership captures.
Ordinary Citry measured 32.710 ms warmed, selected simple classes 23.849 ms,
Django 11.277 ms, django-components 52.867 ms and Jinja2 6.967 ms. Median paired
simple savings were 8.777 ms / 26.71%. The report records its source hashes and
measurement revision (`7c292e8c`); subsequent final-integration corrections are
separate from this timing evidence. The images are generated from the retained
report and both published copies are byte-identical.

The first full gate found three Citry UI tabs tests failing after the earlier
transparent-boundary correction. Tabs retain a transparent declaration wrapper
and insert its caller-owned lazy content elsewhere. Manifest preparation had
mistaken the shared lexical identity for another whole component output.
The correction explicitly marks transparent whole outputs and preserves that
marker through replacement and cache replay. Remote caller-owned interiors do
not select boundaries; repeated actual outputs and missing boundaries still
fail. The pre-1.0 cache format remains version 1; entries lacking the required
boolean become ordinary cache misses. This is a correctness fix, with no speed
claim. Focused cache, simple, pure and placement checks passed before the final
repository and browser reruns.


Final validation: all 19 full-gate phases passed, with 88.64% Python coverage
against the 88.5% requirement; Linux-platform mypy passed across 537 source files.
Four additional hook-replacement cases passed after the gate's collection, with
nine total focused placement cases passing. The 1,269-case Citry/UI Chromium
suite passed 1,263 cases initially; six needed the generated Tailwind fixture.
After building it, all 12 selected CSS-coexistence cases passed. The public
simple and transparent-placement cases passed in Firefox and WebKit (six cases).

The 108-case docs browser suite initially passed 106 cases. Refreshing the
editable Citry UI package metadata from 0.2.0 to the workspace's 0.2.1 resolved
one playground label mismatch. The toast-focus assertion passed on its isolated
retry without a code change; its original failure remains recorded as transient,
not as a fixed runtime bug. Both failed cases passed on their focused reruns.
Independent technical and separate prose reviews found no remaining runtime or
publication blocker after the recorded corrections.

The final `python -m docs_site build-check --strict` passed with no guard findings.


## Devlog story and release preparation, 9 September 2026

At the user's request, posted the optimization journey to
[citry-ops issue 79](https://github.com/citry-dev/citry-ops/issues/79#issuecomment-5607335812).
The local [story](performance_render_devlog_story.md) includes the user's account of
the 14-hour Astra run and the measured results from the two distinct benchmark
comparisons. The diminishing-returns graph counts retained large-page gains
across logged research entries, including qualification; it does not measure
equal-duration or independent attempts. Independent review verified the counts
and separately reviewed the prose. JSON data and PNG/SVG copies are under
`docs/design/assets/repeat_render_retained_gains.*`. The posted body was read
back and matched the local draft.

Added the remaining public render API and compatibility changes to Citry's
Unreleased changelog. The release preparation now records the user's selected
Citry 0.5.0 target and the Preview extension being developed by another agent.
Package metadata changes and combined release qualification remain part of the
prepared release work. Optimization remains paused; no Git promotion, commit,
branch change or push was performed.

## Bounded follow-up after the 0.5.0 release (2026-09-10)

The maintainer authorized exactly four parked avenues, with no further search
after them. This resumes the distinct-case and architectural approach; Cython
and ABI explorations remain parked. Package publication and docs deployment are
complete. The release-automation replay is being monitored separately while
these experiments run. Benchmark probes and results remain on this research
branch and must not be merged into main.

The four attempts are:

1. Qualify the remaining thirteen presentation declarations as one group using
   the public simple flag, then measure the eligible group.
2. Investigate DynamicElement's transparent component and default-slot path as
   a distinct built-in rendering case.
3. Evaluate one explicit slot/JS contract for a broader component fast path.
4. Evaluate one output representation that avoids repeated attribute and
   interior-render work.

Each avenue gets one candidate, correctness qualification and a measurement
where meaningful. Record rejected proposals as well as accepted changes; do not
expand into an open-ended search. Keep the normal API unless an explicit new
contract is proposed and documented. Commit the result of each area separately.
Fresh control measurements determine gains; historical timings are context only.
The archived Python runtime and benchmark fixture match main at ea4d20d58. The
current local native build is reused in both control and candidate processes;
its digest is recorded with the new results.
