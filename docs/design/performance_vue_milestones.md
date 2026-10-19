# Vue performance milestones

This round begins after the intermediate Vue report and static-template grouping
experiment. It has a hard limit of 30 optimization experiments in total.
Correctness fixes within an experiment do not create extra numbered attempts;
a materially different optimization hypothesis does. Baseline measurements,
qualification and final reporting do not consume attempts. Stop earlier when
remaining candidates lack a plausible material benefit or fail their contracts.
Reserve attempts for the later action/first-load stages; do not consume the
entire allowance chasing the first milestone.

## Priorities and comparison

1. Meet or beat Django + HTMX + Alpine on second-load time to interactive at
   both 140 and 1,400 outputs.
2. Once the first target is met or useful candidates are exhausted, improve
   server-action latency and first-load time to interactive.
3. Produce a standalone HTML graph report including both scales and the
   Python API + Vue/React references. Preserve previous reports.

Use the existing readiness and semantic oracle without weakening it. Second
load means a warmed application with a fresh browser context, not a cached
HTTP page. Compare current stacks in the same run. A single favorable sample
is insufficient to declare a milestone met: repeat the comparison and inspect
spread and phase attribution. This is local engineering evidence, not a
publication-grade ranking. Keep historical Citry + Alpine explicitly labeled.

Each accepted change needs meaningful behavior qualification and evidence of
benefit. Record scale tradeoffs; an improvement at 1,400 can justify a small
140-output regression when the overall milestone still improves. Never keep
incorrect output, weaker readiness or a broken public contract for a faster
number. No Node production dependency, page-state snapshots, benchmark-only
application shortcuts, or arbitrary limits tuned to these two fixture sizes.

## Starting evidence

The saved installed-wheel intermediate report is
`.benchmarks/research/vue-fusion-intermediate/report.html`. At 140 outputs its
second-load Citry + Vue result was 71.6 ms versus Django + HTMX + Alpine's
56.2 ms. It did not measure 1,400 outputs. The static-grouping change since
that report saved median paired server render-plus-preparation time of
3.094 ms at 140 and 50.518 ms at 1,400 in source Python 3.14t diagnostics;
those are not end-to-end installed-wheel gains. Static grouping is part of
this round's baseline.

The document-body serialization shortcut was deferred because it did not
preserve security inspection, hooks, dependency placeholders and nested
shell selection. Its replacement design is in [vue.md](vue.md#avoiding-discarded-body-html-shared-document-selection).

## Experiment ledger

The baseline wheel is frozen, qualified and measured. M01–M09 and M11–M13 are retained;
M06 chiefly reduces delivered code and first-load time, and M07 removes a
small browser cost. M08 reduces redundant run data and action latency. Experiment selection followed measured costs and
separates authored-static structure, Python-selected structure, per-occurrence
data, browser-local state and server revisions.

| Attempt | Hypothesis and eligible cases | Result | Savings and evidence | Decision |
| --- | --- | --- | --- | --- |
| M01 | Validate and detach user data once; reuse builder-owned JSON containers at the occurrence boundary | 82 focused checks pass; strict-constructor occurrence-payload oracle agrees | Source paired total: -1.246 ms at 140, -13.016 ms at 1,400; installed cumulative result under M02 | Keep |
| M02 | Reuse a leaf component browser program and evaluate per-render data/control operations | Independent review and installed qualification pass | Cumulative M01/M02 second load: 61.9 ms at 140, 481.1 ms at 1,400 | Keep; target still unmet |
| M03 | Compile constant and fixed-name element attributes into the leaf program, avoiding per-render typed attribute construction | Independent review accepted; 192 focused checks, final 5-test edge batch and installed 80/80 qualification pass | Installed second load vs M02: -6.1 ms at 140, -65.9 ms at 1,400 | Keep; gaps to Django 1.6/88.4 ms in this short run |
| M04 | Share the complete compiler structure for repeated instances of one whole-leaf program within an assembly | Independent review accepted; 113 focused checks, exact general-path parity and installed 80/80 checks pass | Second load vs M03: -2.4 ms at 140, -20.8 ms at 1,400 | Keep; small-case target reached in one short run |
| M05 | Convert exact ordinary scalar expression values directly to Vue text data | Independent review accepted; 72 focused checks, installed qualification and timing pass | Installed second load vs M04: -1.1/-20.0 ms at 140/1,400 | Keep; large-case gap 49.6 ms |
| M06 | Keep keyed, slot-free repeated component calls as one trusted browser loop plus Python-prepared instance data | Source review, installed zero-to-two/reorder proof and canonical qualification pass | At 1,400: first load -19.9 ms; second load -1.5 ms (too small to establish a gain); source bundle -543 KB | Keep for payload/first load; later milestones recover the action cost |
| M07 | Put the trusted component loop directly on its keyed component, removing the per-member template Fragment | Source review, native/Python checks, installed lifecycle proof and canonical qualification pass | Second load -1.0/-3.5 ms at 140/1,400; large browser-after -2.1 ms | Keep; modest gain |
| M08 | Represent eligible run members directly by occurrence ID, omitting redundant local-call records | Final source review passes, including slot placement, callback order and a nonempty reorder oracle | Second load -1.6/-8.0 ms at 140/1,400; large select/insert -20.85/-16.85 ms | Keep; large second-load gap 34.1 ms |
| M09 | Resolve built-in class metadata once per type during a preparation, preserving custom behavior | Independent source review and exact paired payload/code parity pass | Source full Page -0.938/-6.480 ms; installed second load -0.5/-12.6 ms at 140/1,400 | Keep; large same-run gap 18.7 ms |
| M10 | Skip callback scheduling for components without server-render callbacks while retaining host registration and Vue flushes | Correctness passes; installed browser phases unchanged | No measurable gain | Rejected; pre-M10 scheduling restored |
| M11 | Remove DOM occurrence annotations after occurrence lookup moved to Vue instance maps | Source review, existing Node 22/22 and retained lifecycle browser proof pass | Not individually timed; measured cumulatively with M12 | Keep for removal of unused work |
| M12 | Retain resolved spread attribute dictionaries in leaf programs, materializing typed records only on fallback | Correctness and payload parity pass; source timing is mixed | Cumulative M11/M12 second load -1.7/-24.5 ms vs M09; large server phase -20.44 ms | Keep; large case effectively tied in one run |
| M13 | Reuse strict-JSON validation within one synchronous protocol validation call | Final source review, protocol package 16/16 and installed qualification pass | Large select/insert -26.45/-29.45 ms vs M12, chiefly browser time | Keep for action latency |

## Initial candidate queue

- Select the body once for both serialization and assembly, preserving the
  documented security, shell and hook contracts; avoid producing discarded HTML.
- Reuse authored browser structure while Python supplies selected branches,
  iterations and occurrence data, instead of reconstructing per-row source.
- Detach and validate mutable data once at the trust boundary, avoiding repeated
  JSON round trips while preserving mutation isolation and strict JSON rules.
- If leaf-program profiling still shows attribute resolution dominant, distinguish
  fixed known attribute names from spreads and class/style merging. Validate
  immutable names once, preserve value normalization and hooks, and avoid
  rebuilding generic contribution lists for the fixed-name case.
- For ordinary text values, avoid HTML escaping followed by unescaping before
  Vue receives text data; preserve special-value protocols and defer escaping
  to actual static HTML serialization. Profile protocol inspection separately.
- Use browser profiles to identify bridge, native Vue, asset loading and
  initialization costs before choosing any browser-side specialization.

These were screening candidates at the start of the round, not commitments or claims of benefit. The later experiment sections and stopping decision record their outcomes.

## Baseline qualification correction

Review found that reverting the complete typed-shell shortcut had left an
earlier unconditional root-child skip in `serialize.py`. The starting wheel
therefore does not fully materialize descendant HTML before Vue preparation.
The first baseline run must be identified as that partial-shortcut checkpoint,
not evidence that removing a full body pass would produce further savings.
Static head components and active security policies need regression checks.
Restore or guard the skip before accepting a new implementation checkpoint;
keep existing raw observations unchanged and record this qualification limit.

## Larger candidate: reusable programs for leaf components

Prior art: `PreparedExprNode` and `PreparedElementOpenNode` in `_vue/capture.py`
create per-render typed leaves; `ForNode.iter_bodies` preserves Python loop
semantics; `_vue/direct_capture.py` then reconstructs browser source from those
leaves. The rejected generated-function experiments in `performance.md`
sections 6.9 and 6.10 sped up the walk without removing this work. This candidate
must remove leaf construction and source reconstruction to justify itself.

A leaf component here means its final post-extension template has no Citry
component calls, slot calls, foreign nodes or unknown nodes. It may have local
Vue behavior and Python-selected conditionals and loops. Eligibility is about
the final template and active hooks, not component names or benchmark counts.
`ProjectOutput` is an example of this general case; components that render
other components continue through the general renderer.

Compile immutable authored structure once into a browser template plus Python
data operations. The operations evaluate text and attributes in source order,
choose Python branches and enumerate Python loops. They record values and
nested iteration records. Vue receives the shared browser template and those
records, so it builds the DOM without the server rebuilding identical source
for every occurrence. Python still executes every selected expression and
component data callback exactly once. JavaScript never executes Python or
creates an unrendered Python component.

A typed result retains the program and evaluated records. Interactive assembly
uses its prepared compiler input directly. Static serialization interprets the
same records to produce HTML, without evaluating Python again. Author-provided
Vue expressions remain source; Python values remain data. Authored `{{ ... }}`
text cannot accidentally become executable Vue source.

Initial eligibility should exclude custom or unknown runtime attribute hooks
and unknown structural replacements. Exact built-in attribute hooks needed by
eligible spreads must execute once through their existing contract. A dynamically
evaluated expression can still produce trusted HTML, a slot, or a component.
Preserve its existing static or interactive result by reconstructing the general
typed result from already evaluated, output-normalized records. Never retry the
template or repeat side effects. Generated loop data does not authorize user
`v-for` to create Python components.

Preserve lazy loop interleaving: request one item, evaluate its body, then request
the next. Keep source spans for errors and use the existing special-value
conversion rules, including dynamic protocol registration. Recorded values must
not call `__str__` or `__html__` again during fallback or static serialization.
Nested iteration records require an explicit Vue identity rule; compare reorder
and insertion with edited inputs and local state against current behavior.
Component hooks and dependency merging still run once after dynamic children
settle. Cache programs by the final transformed template and applicable hook
configuration; unknown hooks and tracing use the general renderer.

Required checks include source-order side effects, empty and filtered loops,
multi-target unpacking, nested loops, changing branches, dynamic attribute
names/order, static HTML equivalence, escaping, special value protocols,
unchanged JS callbacks, and the canonical browser oracle at both scales.
Measure server rendering, assembly, compilation, payload and end-to-end time;
a first-load compile penalty must be reported separately. This approach is now
supported by the installed profile and implementation review
recorded below.

The initial implementation also excludes document shells and keyed Python
loops. Document boundaries must stay visible to body selection. A generated
Vue loop introduces a fragment per iteration; putting an existing element key
inside an unkeyed fragment can change which DOM nodes survive reordering.
Keep those loops on the general path until fragment identity is qualified.
Likewise, dependency placeholders and unknown extension nodes retain their
existing path. These exclusions follow structural properties, not fixture names.

## Installed baseline, 2026-09-13

Qualification `20260913T000914Z-8efa95c8` passed 88 semantic checks and all
160 observations. Timed run `20260913T001727Z-3f9773ad` also passed 160/160.
Both use installed Python 3.12.13 and frozen wheels. Their documented partial
root-child skip remains a correctness limitation outside the canonical case.

| Outputs | Citry second load | Django + HTMX + Alpine second load | Citry server preparation | Django server preparation |
| --- | ---: | ---: | ---: | ---: |
| 140 | 66.1 ms | 55.7 ms | 32.792 ms | 4.921 ms |
| 1,400 | 535.6 ms | 323.6 ms | 320.684 ms | 45.815 ms |

A separate installed cProfile probe is retained under
`.benchmarks/research/vue-optimization-baseline/`. Instrumented times are much
higher than normal request times and must not replace them. At 1,400 outputs,
its median render is 560 ms and serialization 373 ms; assembly accounts for
about 296 ms of serialization. About 8,430 `inspect.getattr_static` checks for the `__html__` value protocol
cost 22 ms cumulatively, while text escaping costs about 8 ms. This supports
removing repeated leaf construction and browser-source assembly before focusing
on those smaller text costs. The legacy frame builder runs only once on this
canonical Page, confirming that a large discarded-body pass is already absent.

The profile also finds two application snapshot conversions, because the
fixture's separate template and JS-data callbacks each read a snapshot. This
round does not count changing that fixture as a framework optimization.

## M01: builder-owned prepared data

The private assembly constructor adopts containers built from normalized user
inputs; the public occurrence constructor retains its strict deep-copy contract.
Server data still detaches once. Review verified every user-derived prepared
assignment passes through the normalization boundary. Tests cover mutation
isolation, shared inputs, finite values, cycles, tuple normalization, and equality
of strict and adopted occurrence payloads containing component calls, selected
slots and event bindings.
Existing string-subclass key normalization is preserved.

`m01-single-detach-paired.json` under the direct-relationships research directory
records six alternating fresh-process pairs at each count, one excluded warmup,
and five consecutive measured observations per process. Native compilation is
absent during measured batches. Median paired preparation savings are 1.348 ms
at 140 and 13.801 ms at 1,400; total render-plus-preparation savings are 1.246
and 13.016 ms. These are Python 3.14t source diagnostics. The toggle isolates
adoption versus the strict constructor while keeping the strengthened ingress
checks in both arms; an installed cumulative run must establish net public-path
performance. No browser speedup is attributed to these stage measurements.

## Browser attribution before M02

The installed baseline's browser-after phase is about 30.8 ms at 140 outputs
on both loads, and 211.1/210.6 ms on first/second loads at 1,400. Python API +
Vue measures 27.8/28.5 ms and 207.7/210.7 ms respectively. These are separate
sample medians, so their differences are descriptive rather than paired
estimates of bridge overhead. They do show that the large second-load gap is
currently in server preparation. Browser work alone cannot plausibly close it.

The retained analysis is
`.benchmarks/research/vue-optimization-baseline/browser_phase_candidates.json`.
After the server experiment, profile Vue mounting and layout, payload parsing
and definition registration, then the callback coordinator. Use the existing
CDP startup profiler with current Vue entry points. Keep profiler observations
separate from ordinary browser timings and preserve the full readiness oracle.

## M02: corrected source diagnostic

The controlled source comparison uses the canonical **Board component**,
not the complete Page request. Four alternating fresh-process pairs per count
average three observations after an excluded warmup. Native compiler calls are
zero during measured observations. The artifact is
`.benchmarks/research/vue-poc/direct-relationships/m02-leaf-program-paired.json`.
The artifact reports medians of paired on-minus-off differences; the table
presents their magnitudes as savings. The corrected run
replaced the first provisional JSON; those earlier numbers are superseded.
Subsequent observations must use unique artifact names to retain each checkpoint.

| Outputs | Render + prepare saving | Board render + serialize saving | Prepared payload increase |
| --- | ---: | ---: | ---: |
| 140 | 2.205 ms | 5.660 ms | 4,142 bytes |
| 1,400 | 23.281 ms | 61.624 ms | 64,403 bytes |

Rendering alone becomes slightly slower; preparation becomes faster. The program
currently retains exact resolved attribute objects for static serialization and
fallback. It removes repeated browser-source assembly, text leaf creation and
control-flow render wrappers, rather than all per-element construction.
The number of prepared definitions falls from 16 to 12 in this Board probe.

The larger serialization saving must not be presented as a Page-request saving.
Board is a fragment, so serialization materializes the complete fragment HTML
even when Vue later replaces it with a host. The canonical Page can defer its
body serialization. Installed
Page measurements must determine its actual server and browser benefit.

The stable Python 3.12 source browser oracle passes at both sizes, including nine
signed actions, retained component identity/local state, callback DOM revisions,
cleanup and effect traces, and zero browser faults. Artifacts are
`.benchmarks/research/vue-optimization-m02/qualification-source-{140,1400}.json`.
These source-browser observations precede the final review corrections and do
not pin the central leaf-program module in their recorded hashes. They establish
the observed checkpoint, not qualification of the corrected implementation.
Independent review requested fixes for loop evaluation context, tracing,
error locations, structured-output dependencies and exact extension eligibility.
Those fixes now pass the focused checks. Final acceptance requires independent
review and the corrected installed-wheel qualification and timings, recorded below.

## M02: installed Page result

Qualification `20260913T011801Z-ed5f77f6` and timed run
`20260913T012222Z-65f14876` each pass 80/80 observations. The report is retained
in that timed run's `report.html`; exact wheel and run hashes are in
`.benchmarks/research/vue-optimization-m02/status.json`.

| Outputs | Citry second load | Django + HTMX + Alpine | Remaining gap | Citry select / insert |
| --- | ---: | ---: | ---: | ---: |
| 140 | 61.9 ms | 55.8 ms | 6.1 ms | 43.3 / 42.1 ms |
| 1,400 | 481.1 ms | 325.3 ms | 155.8 ms | 370.9 / 373.75 ms |

Relative to the starting installed run, Citry's second load improves by 4.2 ms
and 54.5 ms. These are cumulative M01/M02 checkpoint differences, not an isolated
M02 causal estimate. The controls remain close to their starting load times.
Each `initial` action row, including the quoted second-load rows, has only one
observation in this short comparison; repeat
the eventual milestone comparison before claiming parity. Server actions remain
ahead of the Django control at both sizes. First loads measure 89.3/526.0 ms.

The installed Page cProfile is in the same research directory. At 1,400 outputs,
instrumented rendering measures about 538 ms and serialization 214 ms, compared
with 560/373 ms at baseline. Assembly falls from about 296 to 176 ms cumulatively.
Attribute handling remains a large rendering cost: resolving attributes takes
about 115 ms, constructing typed opening-element/attribute records about 82 ms,
and leaf attribute checks about 35 ms. These are instrumented cumulative costs;
they cannot be added indiscriminately or presented as uninstrumented savings.

## M03: compiled element-attribute plans

Prior art: `ElementAttrsNode._resolve_for_output` and `_resolve` own evaluation,
merging and hooks; `PreparedElementOpenNode._prepared_from_resolved` partitions
authored syntax from Python data and creates typed attribute objects. The leaf
program subsequently examines those objects, builds data dictionaries, and saves
the objects for possible static serialization. `_merge_resolved_attrs` owns
case-insensitive identity, first spelling/order and class/style accumulation.
Preserve those contracts rather than implementing a competing general normalizer.

Handle two cases within the existing program:

1. A completely authored opening element needs no Python evaluation. Compile its
   HTML once, retain its authored browser requirements, and avoid resolving or
   validating it during each occurrence. This includes constant openings inside
   Python branches and loops. Dynamic keys, server Events bindings and other
   live metadata remain outside this case.
2. For exact built-in attributes with known names and ordinary dynamic values,
   compile their source/data partition and evaluation order. Fill owned data
   records directly, without constructing `PreparedAttribute` and
   `PreparedElementOpen` objects for later disassembly. Initially retain the
   general resolver for spreads, custom hooks, dynamic class/style merging and
   uncertain extension wrappers. Extend eligibility only when the same shared
   contracts can be proved cheaply.

Static serialization and structured-value fallback must reconstruct output from
these recorded values without evaluating expressions or value protocols again.
Authored Vue expressions remain source; Python values remain data. Keep the
existing JSON normalization boundary and reject unsafe dynamic DOM properties.
Preserve case-insensitive attribute identities, authored ordering, boolean/None
omission, class/style behavior, SVG closing rules, source diagnostics, TRACE,
context scopes and dependency settlement. Unknown cases use the existing path.

Compare canonical Page output and browser behavior, server render/preparation,
payload and both scales. A microbenchmark of attribute construction alone is
insufficient. The decision should be based on reduced complete-request work,
with additional complexity justified by its measured benefit.

The first implementation restricts direct dynamic plans to exact built-in
attribute nodes with unique case-insensitive identities. Spreads, dynamic
class/style merging, Events metadata, conflicting authored Vue targets and
extension wrappers retain the general resolver. Values remain raw until the
existing JSON or static-HTML boundary; exact attribute syntax does not imply
that its runtime value is an ordinary scalar. Fallback must consume recorded
values, never evaluate an expression again.

Review caught an error-timing regression: rejecting reserved Events attribute
names while compiling a whole program also rejected inactive branches. Those
names now make the direct attribute plan ineligible; the general selected-time
path rejects them before expression evaluation, as before. The final direct
edge batch covers inactive/selected branches, one-evaluation behavior and
protocol/Const values, identity collisions, extension fallback and assembly
parity. No remaining code blocker was found.

The four-pair source Page diagnostic is
`.benchmarks/research/vue-poc/direct-relationships/m03-compiled-attrs-page-run1.json`
(final metadata SHA prefix `f7e3adb5`). Its toggle disables only the fixed
dynamic-attribute plan; both arms retain the constant-opening shortcut, so it
does not isolate all of M03 against M02. At 140/1,400, paired render-plus-prepare
improves by about 5.25/37.62 ms; a separate complete Page render-and-serialize
workload improves by about 8.26/70.63 ms. These workloads are timed separately
on source Python 3.14t and cannot be added or substituted for installed TTI.
Warm native compile calls remain zero and definition count remains 14. Payload
differs by four bytes because the diagnostic's on/off session names differ.
Source hashes include `serialize.py` but omit `_vue/serialization.py`; the
installed wheel checkpoint is authoritative for the complete source closure.

Installed M03 qualification `20260913T015005Z-4e06c18e` and timing
`20260913T015431Z-3f83758e` both pass 80/80 observations. The clean pure wheel
has SHA prefix `e49323a0`, build prefix `a872f3aa`, with the unchanged ABI3 core.
Second-load TTI is 55.8/415.2 ms at 140/1,400 versus the same-run Django + HTMX
+ Alpine control's 54.2/326.8 ms. Citry select/insert measures 36.35/35.85 ms at
140 and 297.35/297.75 ms at 1,400. This short checkpoint still has only one
observation per initial-load row; repeat the final milestone comparison before
claiming parity. The source diagnostic isolated only part of the change; this
installed comparison covers the complete accepted M03 implementation.

M03 first-load TTI is 82.9/447.5 ms at 140/1,400. The second-load server segment
is 23.52/209.83 ms and browser-after segment 30.8/202.8 ms. Django's corresponding
second-load server segment is 7.07/57.82 ms and browser-after 45.7/266.3 ms.
Citry's browser advantage is not yet large enough to cover its server cost.
The separate Page cProfile records rendering/serialization of about 39.85/24.26
instrumented ms at 140 and 364.04/198.73 ms at 1,400. Assembly is about 161 ms
cumulative at 1,400; ordinary text resolution remains about 77 ms cumulative.
These instrumented values are not additional latency phases.

### M04 design: whole-leaf definition artifacts

`assemble_typed_render` currently copies the shared leaf fragment's metadata,
constructs a new compiler input, serializes its structural identity and hashes
it for every occurrence. The structure belongs to the compiled program, while
occurrence data, parent identity and event credentials belong to the render.
If the next profile supports it, share a complete immutable definition artifact
for an exact whole-leaf body. Retain the general assembly path when extensions
change the final parts, a structured value causes fallback, or the body includes
component/slot relationships. Do not cache mutable occurrence data or silently
change the contract of a supplied component-tag callback.

Independent design review supports a cache scoped to one assembly, keyed by
`(type_key, id(fragment))`, only after logical-body selection returns exactly
one `PreparedLeafProgram`. Copy binding metadata once into that assembly's
compiler input. Keep the existing structural definition identity and collision
check. Every occurrence still validates its own data and errors; no credentials,
parent relationships or occurrence data enter this cache. This avoids
cross-request mutation/lifetime complexity while addressing repeated instances
within a render. Implementation starts only after the M03 wheel captures its
source checkpoint.

Falsifiers include one type with two different programs, one program used by
different types, final hooks that reshape parts, structured-value fallback,
and invalid JSON or a Vue error in a later occurrence of a reused program.
Compare definition IDs, compiler inputs and payloads against general assembly,
then complete Page timings at both scales. A smaller construction microbenchmark
alone is not acceptance evidence.

The first M04 source Page comparison is
`.benchmarks/research/vue-poc/direct-relationships/m04-leaf-artifact-page-run1.json`
(artifact SHA prefix `cf162ab5`). Preparation improves by about 2.03/15.25 ms
at 140/1,400. Rendering, which this change does not modify, drifts by
0.18/12.84 ms in the same diagnostic, leaving paired render-plus-prepare gains
of only 1.85/2.38 ms. A separately timed complete Page workload improves by
4.89/36.80 ms. Treat this as noisy source evidence; the installed checkpoint
decides whether the complete-request improvement persists. The assembly parity
oracle confirms unchanged definition IDs and compiler inputs, while a bad
value in a later occurrence still fails validation. The frozen wheel SHA is
`5d953920ac4685211cfa8146542d76316d5cf2ff32bd4cdb8d5f9c304a26aca4`.

Installed qualification `20260913T020159Z-d45a5143` and timing
`20260913T020619Z-a4780b81` pass 80/80. Citry first/second/select/insert is
80.5/53.4/34.85/33.7 ms at 140 and 429.4/394.4/279.0/279.3 ms at 1,400.
Django second load is 56.3/333.9 ms in that run. The small case is ahead by
2.9 ms in this single observation; the large case remains behind by 60.5 ms.
The separate instrumented Page profile shows assembly falling from about
161 ms at M03 to 108 ms at M04 at 1,400; rendering stays about 363 ms while
serialization falls to about 145 ms. This supports the intended mechanism.

### M05 design: text-data specialization

`PreparedExprNode.resolve_value` currently checks `__html__`, invokes the HTML
value dispatcher, escapes ordinary text and then unescapes it into Vue data.
For exact built-in scalar values the output destination is already known:
Vue receives text, and static serialization performs the eventual escaping.
The M02 profile puts about 84 instrumented ms in expression resolution at
1,400 outputs, including 33 ms in `_render_value`; these overlap.

A bounded candidate is to normalize exact strings, int/float values and booleans
directly to text and keep `None` as empty text. Preserve runtime
`ComponentLike` registration and replacement of the dispatch types, just as
the existing `_render_value` fast path does. String subclasses, trusted HTML,
Slots, rendered components and unknown objects keep the existing protocol
path. Do not weaken sandbox evaluation or move callback execution. Tests must
cover escaping round trips, empty/boolean/numeric values, dynamic protocol
registration in a subprocess, and static versus prepared output. Implementation
began after the M04 wheel captured its source checkpoint. Nonfinite float values
retain their existing text spellings; this path does not place raw NaN or
Infinity into JSON data.

The final implementation shares the existing live dispatch guard and restricts
its use in the ordinary HTML renderer to the existing exact-type fast paths;
unknown custom values do not pay an extra protocol check. Focused capture and
dispatch tests pass 72/72. The corrected Page source artifact
`.benchmarks/research/vue-poc/direct-relationships/m05-exact-scalar-page-run1.json`
(SHA prefix `77ce5f0f`) records paired render-plus-prepare improvements of
2.13/18.67 ms at 140/1,400, and separately timed full Page improvements of
5.24/17.02 ms. Payload and HTML bytes match exactly. An earlier run with unequal
session IDs is preserved as `m05-exact-scalar-page-run1-invalid-session-id.json`
and is not used. M05 installed qualification
`20260913T021251Z-d9751f89` passes 80/80.

Installed timing `20260913T021707Z-e9ce1b44` also passes 80/80. Citry
first/second/select/insert is 77.8/52.3/32.9/31.8 ms at 140 and
407.3/374.4/261.25/258.75 ms at 1,400. Django second load is 56.9/324.8 ms.
The small-case lead is 4.6 ms and large-case deficit 49.6 ms in this short run.
These remain single initial-load observations; final repeated measurements
will determine whether the first milestone is met consistently.

## M06 design: Python-prepared component call runs

> Template text in the M06 and M07 sections records what the compiler
> emitted at the time. The current compiler reads the same occurrence data
> through the `$citryPrepared` instance property (for example
> `$citryPrepared.callRuns.citryRun0`) and names the loop variable
> `citryOccurrenceId`. The manifest the server sends still names this field
> `preparedData`.

### Prior art and scope

`direct_capture.py:225` transforms each physical child occurrence into a
separate source call and local-call metadata record. Canonical `PhaseGroup`
repeats one self-closing `ProjectOutput` call beneath a stable `v-show`.
`citry_vue_compiler/src/lib.rs:490` rejects local calls under any Vue `v-for`;
`validate_local_call` requires literal `preparedData.calls.LOCAL.id/key`.
`client.js:67` validates the flat call/parent graph, and `validateActions`
checks additions/removals and observed mounts. Its `localDescendants` metadata
is stored but does not derive remount expectations: those are caller supplied.
The M04 instrumented profile still spends about 108 ms in assembly at 1,400.

The selected design represents repetitions as data while Python still creates
and renders every component. This is a native compiler/protocol change, not a
permission for authored Vue loops to create Python components. Alternatives
are retaining unrolled source (correct but count-dependent) or letting an
arbitrary browser loop create components (breaks Python execution/identity).
An assembler-only rewrite without trusted metadata is rejected.

Besides source construction and hashing, compact call runs may reduce first-load
compilation, definition transfer and browser execution of large unrolled render
functions. A stable parent definition may also avoid a new definition fetch
when the number of rows changes. These are hypotheses to attribute separately;
no browser/JIT improvement is assumed in the acceptance criterion.

### Contract

Keep the existing flat `preparedData.calls` map and all per-child stable IDs,
parent/reference checks, rendering, data validation and callbacks. Add
`preparedData.callRuns`, mapping a generated run ID to an ordered list of
existing local-call keys. Emit one template per run:

```html
<template v-for="citryLocalId in preparedData.callRuns.citryRun0"
          :key="preparedData.calls[citryLocalId].key">
  <component :is="'citry-row'"
             :citry-id="preparedData.calls[citryLocalId].id"
             :key="preparedData.calls[citryLocalId].key"></component>
</template>
```

The generator emits this without additional whitespace/children. A separate
`LocalCallRun` compiler input has `runId`, `typeKey`, `componentTag`,
`sourceStart/sourceEnd` for the child and `loopSourceStart/loopSourceEnd` for
the wrapper, using the same UTF-8 span convention as existing local calls.
The alias is fixed to `citryLocalId`. Rust must claim and validate the exact
wrapper and immediate empty child, the wrapper's matching stable key,
the constant `:is` tag, exact bindings, safe identifiers, and
absence of extra directives, fills, nested loops or destructuring. Reject
unmatched/duplicate metadata and unclaimed generated bracket-form calls.
The blanket ban on ordinary local calls inside authored `v-for` remains.

Emit validated run declarations as `localCallRuns` in the native artifact and
registered browser definition; `preparedData.callRuns` is the occurrence-data
map. Bind declaration metadata into compiler/cache/content identities and
the synchronized helper contract. Replacement sites gain
`localDescendantRuns` alongside their ordinary local descendants. Stable
`v-show` ancestors remain eligible. Actual lifecycle-definition changes still
require caller-supplied remount expectations, exactly as before; test them
explicitly rather than assuming the metadata computes them automatically.

Assembler eligibility must remain stable as a run shrinks from two members to
one: group eligible runs of one or more, not only two or more. Prove the
authored invocation has no slot body using private call metadata captured
from the exact compiled `ComponentNode`; default this proof to false for
other producers. Require an explicit key, identical authored callsite/type,
same data owner/placement route and no actual supplied fills. Preserve physical
order and significant text; only flatten transparent containers whose existing
assembly semantics permit it. Do not merge across elements or slot boundaries.
Initially group only in the component's own body: no containing slot, empty
placement route, and data owner equal to the current occurrence. Calls inside
selected fills or forwarding paths stay general; a component that itself was
placed through a slot can still optimize its own ordinary body.
Keep unknown cases on ordinary calls. Test count transitions 0/1/2 and more,
since a count-dependent switch between a direct call and a loop wrapper could
otherwise remount retained state.

Before mounting the normal prepared app, validate run declarations against
each occurrence's run data and flat calls: exact run set, ordered unique own
call keys, no member reused across runs, existing child and matching type.
Repeat this validation before any server-update mutation. Public low-level
entry points must not acquire a validation bypass. Definition loading precedes
type-bound checks; run shape checks can happen during initial configuration.

Integration review established that a definition may contain both ordinary
calls and runs. Its browser metadata therefore also declares `localCalls`,
with `localId`, `typeKey` and `componentTag` for each ordinary call. Ordinary
IDs and run members must form an exact, disjoint partition of the occurrence's
flat calls. Allowing undeclared remainder entries would hide missing run
members. Validate tag/type consistency both within each incoming definition
and against already registered definitions, then commit the registration only
after validation succeeds. A failed registration must permit a clean retry.
Replacement expectations expand both ordinary descendants and run descendants.

Review also found that discovering runs only from rendered children loses
the declaration when a Python loop is empty. The source test now demonstrates
identical definitions and compiler input for zero, one and two members.
Browser lifecycle and installed measurements remain pending.
The selected refinement retains a private transparent render wrapper from an
exact `ForNode` with one branch and one keyed, empty-body, named component
invocation. This carries the authored site and safe type proof even at zero;
the assembler verifies every actual child against it. Loops with an empty
branch, dynamic component selection, unknown producers or incompatible
placement keep the general path. This structural proof replaces the proposed
discovery by contiguous rendered siblings. Empty loops must not evaluate
component inputs or expose errors from an invocation that never executes.

Initial zero-to-one also requires registering a component type first introduced
by a server update on the existing Vue app. Loading its render definition alone
is insufficient: its exact emitted component JavaScript and styles are
published as content-addressed assets, loaded once before registration and the
update. Initial assets already emitted by Dependencies prime those identities.
Only types with actual occurrences load their component assets; an empty loop
must not execute an absent child's surrounding JavaScript. Concatenating whole
component scripts into each render-definition bundle was rejected because it
could replay arbitrary side effects and duplicate initial scripts and styles.

The generated dynamic component has a compiler-owned constant tag. Vize places
`resolveDynamicComponent` inside the list callback, so an empty list does not
resolve the absent child type. The ordinary named-tag form resolves the type
before entering the loop and would require premature registration. This uses
Vue's standard dynamic-component behavior; it does not patch generated
JavaScript or expose a user-controlled type expression. Validate the incoming
graph and tag/type consistency before registering new types and applying the
update; cover initial zero-to-one as well as one-to-zero-to-one.

The initial supported lazy-asset path uses built-in dependency handling and
the ordinary JavaScript delivery policy. Custom dependency hooks must not be
bypassed when a new type appears: an unapproved new asset/type fails before
execution instead of loading the raw class script. Initial assets still use
the normal dependency pipeline. Every selected type carries a policy record,
including types with no class JS/CSS. Newly introduced types with custom
component dependency hooks or nested Dependencies fail closed, as does a global
custom dependency policy. Nonce propagation reaches the dynamic asset loaders.
Broader custom-policy delivery is not implied by the default-policy benchmark.

### Blast radius and verification

The native `CompileRequest`/artifact and PyO3 `_compile_vue` gain run metadata;
the hand-written `_rust.pyi`, Python `DefinitionCompileInput`, native adapter,
cache/content identity, emitted definition metadata, assembly metadata/rebasing,
browser validation, and built runtime copies must move together. The Citry
template grammar, AST structs, five host-language `LangImpl` implementations
and public component Python API do not change: this is the private prepared
browser compiler boundary. No Node runtime dependency is introduced.

Required checks: native valid/malformed UTF-8 metadata and old authored-loop
rejections; Python IDs/data/callback-order parity and unknown-case fallback;
browser insert/remove/reorder and 0/1/2 transitions with retained local state;
stable `v-show` toggles; changed lifecycle definitions with correct, omitted
and wrong remount IDs; malformed or wrong-type run membership rejected before
mutation. First establish a small real-tree/compiler/browser proof, then run
the unchanged canonical qualification at 140/1,400 and complete-request timing.
Reject the approach if its extra metadata/validation erases the savings or if
it cannot preserve these identity and lifecycle contracts. This is the sixth
hypothesis. Source work began after the M05 wheel checkpoint; acceptance still
requires the listed browser and installed checks.

The first canonical M06 qualification, `20260913T031727Z-92efb831`, failed
at reorder (action 7) at both scales after revisions 1–6 passed. The generated
template loop had no fragment key: a key on its child was insufficient to
preserve identity when Vue reconciled the surrounding fragments by position.
The corrected contract puts the same stable key on the template wrapper.
A minimal browser test using actual compiler output must prove retained local
state and callback generations on reorder before repeating qualification.
The failed run is correctness evidence, not an accepted performance result.

Review also caught an accidental quadratic cost in the new browser checks:
each occurrence rebuilt the complete incoming-occurrence map. The corrected
validator constructs that map once per update and reuses it. Subtree duplicate
checks, collisions with retained outside instances and per-action validation
still run before mutation. This corrects M06's implementation before timing;
it is not a separately measured optimization of the M05 checkpoint.

The corrected installed build passed the zero/one/two/reorder proof, retaining
DOM-node identity and occurrence IDs, running scripts once and processing a
post-reorder callback. Canonical qualification `20260913T034217Z-2a81a39b`
then passed 44/44 checks (eleven checks for each stack and scale). The candidate
pure wheel SHA-256 begins `0400a7b8`, its ABI3 core wheel begins `b133286b`, and
its prepared build ID begins `39df005b`.

The isolated source comparison is
`.benchmarks/research/vue-poc/direct-relationships/m06-call-runs-page-run1.json`
(SHA-256 prefix `44c74c21`). Four alternating fresh-process pairs at each scale
use one excluded warmup and three averaged observations. Both arms retain the
same asset/policy delivery; only the structural run wrapper is disabled in OFF.
The comparison excludes definition IDs, run representation and volatile event
transport tokens from its semantic projection, retaining occurrence IDs,
ordinary call data, server data and other prepared/event data. That projection
matches. Source/native hashes remain stable and warm native compilation is zero.

At 140/1,400 outputs, paired render-plus-preparation savings are 0.574/8.246 ms;
separately measured complete Page render/serialize savings are 0.566/7.684 ms.
Page payload and HTML each shrink by 17,387/155,267 bytes, while the generated
render-definition bundle shrinks by 59,980/543,190 bytes. Definitions fall from
14 to 11. At 1,400 outputs the bundle is 63,701 bytes, down from 606,891. These
Python 3.14t diagnostics isolate the mechanism; the installed end-to-end
measurement below quantifies its browser and request-level benefit.
The source launcher explicitly selected CPython 3.14.6 free-threaded and the
artifact records its `cpython-314t` native extension. During packaging, a
workspace `uv run --python 3.12` command had recreated the worktree's `.venv`
as 3.12; the explicit A/B launcher did not use that environment. Subsequent
builds must select an explicit interpreter without recreating the shared
environment, and diagnostic artifacts should record `sys.version` and
`sys.executable` directly. The original repository environment was only read
for dependencies, not modified.

Installed run `20260913T034819Z-7099fa9b` passed. First/second load are
77.0/52.2 ms at 140 and 387.4/372.9 ms at 1,400. Against M05, the large first
load improves by 19.9 ms, while second load changes by only 0.1/1.5 ms at the
two scales. Treat the latter as effectively unchanged in this short run.
Large select/insert are 265.75/270.55 ms, versus M05's 261.25/258.75 ms;
this action regression remains a follow-up concern. Django second load is
55.8/349.1 ms in the same run. Its large result is slower than its earlier
324.8 ms, so the smaller apparent gap does not establish equivalent progress
by Citry. Repeated final comparisons remain necessary.

At 1,400, Citry's second-load phase is about 169.8 ms server and 200.8 ms
browser-after. Its instrumented Page profile records median rendering
320.874 ms, serialization 123.841 ms and total 445.619 ms. The standalone
profile is `vue-optimization-m06/profile_initial_page.json` (SHA prefix
`4910486e`); `vue-optimization-m06/status.json` records exact wheel/build and
qualification/timing paths. These diagnostics support keeping the smaller
programs while testing their per-member browser wrapper cost next.

### Browser attribution cross-check

The M02 installed browser diagnostic now brackets the page clock with CDP
monotonic timestamps and crops CPU samples to the recorded readiness interval.
The original observer-inclusive results are retained but superseded for this
purpose. See
`.benchmarks/research/vue-optimization-m02/browser_profile_ready_window_v2.json`
(SHA-256 prefix `e8efc4ac`). Raw and cropped profiles are both saved. Clock
alignment uncertainty is approximately 0.5–1 ms for initial loads and up to
1.6 ms for the measured insert; sampling also adds overhead.

At 1,400 outputs, cold/warm initial readiness contains about 197/193 ms of
sampled browser work. Native DOM insertion contributes about 66/60 ms, Vue's
mount path about 33/32 ms, and element creation about 11/11 ms. These are
sampled self-time categories, not predictions of recoverable savings. The
insert profile contains about 297 ms idle/server wait; active costs include
strict JSON validation (about 15 ms), cloning (13 ms) and pointer validation
(10 ms). Server preparation remains the main first-milestone opportunity;
trusted internal browser data versus incoming protocol data deserves a later
action-stage experiment. Never remove remote-input validation just because
the canonical fixture supplies valid data.

The concrete later action-stage candidate is repeated validation within one
synchronous call: `preflightResultEnvelope` validates a reply, then
`validateExchange` validates the same reply again; nested result/action
validators also repeat strict-JSON traversal already completed at the root.
Keep every public entry point strict, but consider private schema-only helpers
after its root has passed strict-JSON validation. Preserve error precedence,
paths and messages, and never persist a validation result across mutations.
This needs no claim that network input is trusted and no public bypass flag.

Another later browser candidate distinguishes components that actually define
`onServerRender` from those that only use ordinary Vue data. `typeOptions` in
`_vue/client.js` currently creates a promise chain per initial mount even when
the built-in host returns synchronously and the callback is absent. The update
coordinator also awaits the empty callback wrapper for every updated occurrence.
Profile this cost before acting. A specialization would still publish every
mount to the Events host, wait for asynchronous hosts and real callbacks, and
preserve error handling and callback order. It would skip only scheduling that
has no callback or asynchronous host work to execute.

### Candidates screened for the next decision

These are source/profile observations, not additional attempted experiments.
Recheck their importance after M06's installed profile before choosing one.

- Eligible repeated calls have one known type and their physical parent is the
  owning component. Their Vue key is already their occurrence ID. Yet every
  member carries a separate local-call ID, a record repeating its occurrence ID
  as both `id` and `key`, and another copy of the parent ID. An ordered list of
  occurrence IDs could express this case directly. Ordinary calls and slot
  placements would keep their existing representation. Validation would still
  prove unique references, parent/type agreement and exact declared run sets;
  replacement-site expansion would read the IDs directly. Measure saved
  construction, payload, JSON copying and validation against the extra branch.
- The actual M06 compiler output creates one keyed Fragment around every child
  component because the generated loop uses a `<template>` wrapper. A separate
  experiment could put `v-for` directly on the dynamic component, retaining
  its stable key and lazy type resolution. Inspect actual compiler output and
  qualify zero-to-many, reorder and enclosing replacement behavior before
  attributing any saved VNode or DOM work to this change. Removing the wrapper
  is distinct from compacting the run data above.
- The M05 1,400-output profile calls the built-in component tag resolver 4,247
  times for roughly fourteen types. Its 35 instrumented ms includes about
  24 ms in registry lookup and lifecycle read protection. A default-only
  per-preparation metadata cache could reduce repeated type work; custom tag
  callbacks must retain their existing invocation and consistency checks.
  Registry mutation and lifecycle behavior need an explicit review first.
  Holding the lifecycle read lock across assembly is unsuitable because it is
  a plain lock and nested registry calls or user callbacks could deadlock.
  Independent review permits a request-local built-in cache of the exact class
  object and formatted tag. Each lifecycle read is atomic, but repeated reads
  do not promise a transaction spanning preparation. When assets are prepared,
  verify that a fresh unique-type lookup still resolves to that exact class;
  reject replacement rather than combining an old body with a new class's
  assets. No cache belongs in the long-lived producer closure.
- General spread openings resolve and merge attributes, construct typed
  attribute records, then turn those records back into Vue data dictionaries.
  The profile spends about 20 instrumented ms constructing those openings.
  Eligible leaf programs could retain the normalized dictionary, materializing
  typed records only for static output or structured fallback. Keep the
  existing spread validation, merge rules, extension behavior and single
  evaluation of user expressions. This does not justify bypassing i18n or
  Events checks merely because the benchmark supplies ordinary attributes.
- Simple scalar lookup expressions remain common, but the sandbox already has
  exact-type guards and a simple-name evaluator. Further specialization would
  need to preserve live security policy, custom mappings and sourced errors.
  This is lower priority than eliminating demonstrated intermediate objects;
  disabling the sandbox is not an optimization of equivalent behavior.

## M07: put the loop directly on its component

Prior art: M06's `_vue/direct_capture.py` emitted the same keyed template wrapper
for zero and nonzero runs. `citry_vue_compiler/src/lib.rs` validated that wrapper
in `validate_local_call_run`, recorded the child path in `walk`, and derived
ancestor replacement-site coverage from that path. Vize's component-loop
code generator can return a keyed dynamic component directly from `renderList`.
The template-loop output added a keyed Fragment around that component.

Generate this exact empty component element, with the same data and keys as
M06, keeping type resolution inside the list callback (written in the
M07-era form; see the note at the top of M06 for the current names):

```html
<component
  v-for="citryLocalId in preparedData.callRuns.citryRun0"
  :is="'citry-row'"
  :citry-id="preparedData.calls[citryLocalId].id"
  :key="preparedData.calls[citryLocalId].key"
></component>
```

The native validator must claim the exact four-attribute element, with equal
component and loop opening spans, no children and no containing authored loop.
Keep all existing unclaimed/dynamic-component and ordinary-call-in-`v-for`
rejections. Record this element's path for ancestor descendant coverage. The
removed template wrapper has no runtime directive or replacement site. Bind
the exact generated form into the helper/cache identity and update native,
Python and browser fixtures together. The PyO3 signature, grammar, public
component API and wire membership representation remain unchanged.

Keeping the wrapper preserves M06's implementation but adds one VNode and
two DOM boundary anchors per run member. Rewriting generated JavaScript is
unnecessary when Vue already supports the direct loop. Falsifiers are eager
resolution for an empty run, changed identity on insert/remove/reorder,
incorrect enclosing lifecycle replacement coverage, or relaxed authored-loop
validation. Verify actual compiler output, the small installed lifecycle proof
and canonical behavior before timing. Measure both scales and retain only if
the saved browser work survives the complete request measurement.

M07 source review found no contract blocker. Native 12/12 and Python 126/126
checks passed, followed by the installed zero-to-two/reorder proof and
qualification `20260913T040405Z-f3ed49ea`. Timed run
`20260913T040808Z-a68abdea` passed. Second load is 51.2/369.4 ms at
140/1,400, improving by 1.0/3.5 ms against M06. At 1,400, browser-after is
198.7 ms, down 2.1 ms. Large insert improves from 270.55 to 265.0 ms, though
only 0.65 ms of that difference is in browser-after; server variation accounts
for most of it. Large select changes from 265.75 to 266.9 ms. These are modest,
short-checkpoint results, not evidence of a large gain from removing anchors.
Exact build/wheel/run evidence is in `vue-optimization-m07/status.json`
(SHA-256 prefix `46259d1a`).

## M08: direct occurrence IDs in repeated calls

Prior art: M07's `_vue/direct_capture.py` constructed each run member's local-call
record and repeated this for its siblings. `_vue/client.js` checked membership
through those records; `validateGraph` checked parent coverage and
`validateActions` expanded replacement descendants. `_vue/protocol.py` and
`citry_vue_compiler/src/lib.rs` validated the exact generated expressions.
These are the boundaries that change together.
This follows the measured M07 direct-component loop. Its design has passed
independent review; implementation, independent review and installed qualification pass.

For the same eligible, keyed, slot-free runs, store ordered occurrence ID
strings in `preparedData.callRuns`. The generated alias then supplies both
`citry-id` and Vue's key directly. Ordinary calls retain their existing map.
Keep each stable occurrence ID, explicit-key duplicate check, source counter,
Python callback and custom tag-resolution call and consistency check. Keep
M07's direct-component template form and its existing eligibility.

The browser must validate that every run member exists, has the declared type,
has its owning occurrence as parent, and appears exactly once among all
ordinary and run references. Run names must still exactly match declarations.
Ordinary declarations must separately cover exactly every key in the ordinary
call map; a graph-valid but undeclared extra ordinary binding must fail.
The union of ordinary child references and direct run IDs must cover every
non-root occurrence exactly once. The Python assembler's `reference_parents`
ledger must receive the same single physical-parent reference for each run
member even though the separate call record is absent.
Replacement-site expansion reads the occurrence IDs directly. Changes to run
order or membership must count as changed call bindings, even if the ordinary
call map remains identical. Zero members still carry the declared empty list;
malformed, missing, duplicate or wrong-parent/type members fail before mutation.

Keeping the redundant records would minimize implementation change but retain
per-row allocation, hashing, wire bytes and JSON work. Encoding IDs as offsets
or binary data is deferred: direct strings remove known redundancy without
introducing a second decoder or a less inspectable protocol.

Update the Python assembler and protocol validator, exact native expression
validation, helper/cache identity, browser graph and update checks, definition
fixtures, built runtime and wheel evidence together. The PyO3 argument shape,
Citry template grammar, language implementations and public Python component
API need no new surface. Extend the compiler's unclaimed generated-binding
checks to the direct alias expression so the shorter binding cannot bypass
run provenance validation. Test mixed ordinary/run calls, zero-to-many, reorder,
stable IDs, wrong parent/type and repeated references. Retain the zero/one/two
identical-definition check and verify custom tag callback count/order and
source-counter behavior. Measure against M07 at
both scales; reject if the extra handling erases the savings or breaks retained
instance or callback behavior.

Final review caught and corrected three issues before performance acceptance.
Ordinary slot calls can belong to a lexical data owner different from their
physical parent; only direct runs impose parent-equals-owner. Global reference
coverage is checked once, avoiding a full occurrence scan for every owner.
The tag mapper retains its two calls per child in the original order, including
the consistency check after transforming the child. Finally, the reorder test
now reads actual run members and asserts nonempty membership, reversed order
and stable IDs by value. Reading the ordinary call map had made that test
vacuous after the representation change.

The final source review passes, with native 12/12, Python 128/128, a final
three-test callback/reorder batch, and client 22/22 checks. An earlier pure
wheel beginning `6213799e` and build `c766d8d0`
were rejected after the remaining callback issue was identified; qualification
was stopped and no timing from that candidate is used. The corrected pure
wheel begins `f824f669`, reuses ABI3 core `7f3f7e25`, and produces build
`b95eb8c5`. Its installed lifecycle/lazy-type proof passes; canonical
qualification passes 44/44 (`20260913T042554Z-ea1dd3c2`). Official run
`20260913T042956Z-2536af93` passes with these medians:

| Outputs | Citry first load | Citry second load | Django second load | Citry select | Citry insert |
| --- | ---: | ---: | ---: | ---: | ---: |
| 140 | 75.2 ms | 49.6 ms | 55.4 ms | 32.25 ms | 29.6 ms |
| 1,400 | 372.0 ms | 361.4 ms | 327.3 ms | 246.05 ms | 248.15 ms |

Against M07, second load improves by 1.6/8.0 ms. Large select/insert improve
by 20.85/16.85 ms. This remains a short checkpoint with one observation per
load type, so the final repeated comparison must verify the small differences.
The 1,400-output milestone remains unmet by 34.1 ms in this same-run comparison.

The fresh installed profile has median render/serialize/total of
34.684/16.359/51.046 ms at 140 and 322.807/118.141/440.947 ms at 1,400.
Initial HTML is 148,736/1,262,780 bytes. These instrumented times are attribution
evidence, not the uninstrumented server phases above. Full wheel, build,
summary and profile hashes are in
`.benchmarks/research/vue-optimization-m08/status.json`.


## M09: built-in class metadata during preparation

Before M09, `default_events_producer` in `_vue/events.py` created the built-in
tag callback, which resolved a registered class, split its name and hashed
its type key on each call. Assembly checked the mapping on every occurrence
and invocation. Initial serialization then called the same mapper for every
occurrence again to construct a dictionary with only one entry per type.
M08 records 4,247 tag calls for roughly fourteen types in
`initial-page-1400-1.pstats`: 34.5 instrumented cumulative ms, including
registry lookup. These overlapping times must not be added together. Custom callbacks
must retain their invocation and consistency behavior; this proposal concerns
the known built-in mapper and ordinary component metaclasses.

Mark the built-in callback by exact function identity and its weak engine
reference when creating the default producer. During one preparation, if that
callback and engine still match, resolve and format each ordinary class once
and reuse the result. Keep the cache local to the preparation. Custom callbacks,
custom metaclasses or mismatched producer/engine cases use the current path.
Do not hold the lifecycle lock across assembly or user callbacks.

The selected-type asset pass uses the same cached class as preparation. After
all preparation callbacks, compare a fresh registry lookup and freshly formatted
tag with that cached pair. Revalidate after any remaining custom tag callbacks
in initial serialization, rejecting a class replacement or name change before
emitting a configuration that mixes captured output and different metadata. Initial serialization can iterate distinct selected type keys for the
unchanged built-in mapper and `component_tag` method; custom methods/callbacks
retain their per-occurrence calls. This needs no new wire fields, public flag,
persistent class cache or native build.

Tests must cover ordinary metadata reuse, custom callback count/order and
nondeterminism, a second preparation observing changed registry state, class
replacement/name mutation during preparation, engine lifetime, and the custom
metaclass fallback. Measure only after M08's checkpoint and profile confirm
the remaining cost. Reject if normal-path overhead erases the benefit or the
cache can combine one class's rendered output with another class's assets.

M09 is now the ninth optimization hypothesis. Its cache is anchored to the
exact class of each rendered component during the existing assembly traversal;
a render made before a registry replacement must not silently use the new
class. All occurrences with one type key must agree on that class. Zero-member
runs still resolve their declarations without running child data callbacks.
Specialization also requires the base registry lookup and producer method,
without instance overrides. A custom metaclass uses the general path.

Revalidate every cached registry class and formatted name after all preparation
callbacks, including compilation, dependencies and asset publication. Pass the
validated tags privately into initial serialization, preserving the public
manifest dictionary. Tests cover stale renders, two class generations sharing
a type key, callback-time registry/name changes, overrides, engine collection
and separate preparations. No request may reuse another request's cache.

## M10: components without server-render callbacks

M08's large second load spends 198.4 ms after the response in the browser.
Large select/insert spend 83.5/81.55 ms there. Before M10, the mounted hook created
a Promise chain and tracks an initial task even when a component has no
`onServerRender` callback. The revision coordinator also awaits the empty
callback function once for every changed component. Those are distinct from
Vue's own mount and update work.

The proposed specialization preserves mounted identity registration for every
component. On initial mount, omit the callback task only when there is no
callback and either no host or the exact built-in synchronous host hook is
recognized privately. Custom hosts keep the current Promise and thenable
semantics, including exceptions; actual callbacks retain their microtask start.
The built-in hook only updates Events source/context maps. Do not add a public
capability flag that can silently discard an asynchronous host result.

For revisions, notify the host about all changed or remounted components, then
skip the empty callback awaits. Keep callback order, cleanup, the awaited host
hook and the final Vue tick. That last tick also covers reactive work done by
a custom host. Readiness retains its first Vue tick and waits for every real
initial task. Invalid truthy callbacks must still fail, not be silently ignored.

Falsifiers are mixed callback/no-callback trees, callback-created reactive work,
new and remounted descendants, source/context refresh, cleanup, host-triggered
reactive changes, custom thenables and sync/async failures. The measurement
must distinguish saved scheduling from skipped lifecycle work. Implementation began after M09's wheel was frozen and audited, so the
installed M09 comparison cannot include this change. Source edits may overlap
that frozen-wheel run; tests and builds wait for its timing lock to end.

## M12: spread attributes as leaf data

Before M12, the general opening path resolves a spread dictionary, constructs a
`PreparedAttribute` for every entry, then the leaf evaluator turns those entries
back into a dictionary. M08 records 1,621 `_prepared_from_resolved` calls taking
20.23 instrumented cumulative ms. A leaf-specific representation could retain
the normalized dictionaries and create typed attributes only for a later
structured fallback.

Eligibility would require an exact prepared opening node with a spread and no
authored Vue attributes, event binding metadata or element metadata. An exact
i18n wrapper is eligible only while its live passthrough condition holds:
a component exists, no static binding, and no active compiled catalog. Otherwise
the wrapper runs normally. Keep `_resolve_for_output` once, including merge,
hooks, runtime Events processing and validation. Copy extension output; preserve
the executable and unsafe DOM-property checks in their existing order.

A spread needs its own retained representation because every resolved attribute
has data origin. The existing fixed-attribute fallback prepends authored source
attributes and would duplicate or misclassify spread values. Structured fallback
must derive the same per-name spans from the already resolved values, without
calling Python expressions or hooks again. Static fallback uses no authored
attributes. Preserve the separate shallow snapshots currently used by fallback
output and prepared data so mutating one does not change the other.

Independent design review found these boundaries viable. M12 implementation began for this
case while the installed M10 wheel was being timed. M11 DOM annotation removal is
common to both arms of the planned server-only paired test, so it cannot
explain that server result. M11 and M12 will share one later installed
checkpoint against accepted M09; M10 is rejected and removed. The report will
identify the cumulative measurement explicitly.


M09 final independent source review passes on `events.py` `7006412a`,
`direct_capture.py` `3917ab01`, and `serialization.py` `f0e7bfd0`.
Review corrected per-occurrence custom callback handling, instance overrides,
mapper identity drift and validation after serialization-side callbacks. Public
payloads remain ordinary dictionaries. The private result carries partial cached
tags and a validator; it validates through the prepared plan handoff. Later
arbitrary serialization hooks are outside that preparation boundary.
The paired diagnostic uses source Python 3.12.13, three alternating fresh-process
pairs, one excluded warmup and three observations averaged per arm. At 140,
prepare/render-plus-prepare/full-Page improve by 0.552/0.576/0.938 ms; at 1,400,
by 4.785/5.692/6.480 ms. Full normalized payload and generated bundle SHA
sequences match for every pair; payload, HTML, bundle, definition and run-member
counts are unchanged. Warm native compilation is zero. This is a source
comparison, not installed browser timing.

Artifact: `.benchmarks/research/vue-poc/direct-relationships/m09-builtin-metadata-page-run1.json`,
SHA `02d7cb4b1b37f702162866293cc3a156d1f495f34e6f9e98a8ec941be666f1ea`.
The diagnostic records actual interpreter/import/native paths and source hashes.
The installed checkpoint follows before final acceptance.

## M11: remove unused DOM occurrence annotations

Before M11, production mount/unmount hooks added and removed `data-citry-occurrence` on
component element roots. The current Events bridge identifies the source from
the Vue instance record and a source map. Parent checks, readiness, remount
tracking and server targets also use instance/occurrence maps. Independent
repo search found no production reader of the attribute and no documented
public contract. Components with non-element roots already have no annotation;
components sharing one root can write several IDs into the same attribute.

Removing these writes would finish that part of the migration to Vue-owned
instances. It removes attribute reads/writes, string splitting and joining on
mount/unmount, and stops overwriting an authored data attribute. This should
help initial insertion and actual new/remounted/removed components; retained
selection or reorder should not gain from it.

The installed run-retention test currently reads this private attribute.
Replace that observation with actual retained DOM references and stable IDs
from the mounted-instance map, then assert both survive reorder and the next
server action. Regenerate the runtime. An unreferenced historical benchmark
asset contains an old reader; the current benchmark loads the installed Events
runtime and does not load that asset. No historical result needs changing.
Independent design review passes. Source implementation began after M10's
wheel is frozen. This small removal will receive focused lifecycle checks and
the next cumulative installed comparison; no individual millisecond saving is
claimed without a separate measurement.


### M09 installed checkpoint

Pure wheel `bb91e16756de4c2b1b535eebf7ccfc72cb0a2a831649ca96de45dc71d9c5efb7`
reuses M08's ABI3 core. Build `06e534fef3a980df8eb10bb8f38847847195f92c7cf96354627c994108be90dd`
passes qualification `20260913T045821Z-f782fbb3` and official run
`20260913T050244Z-bbdace8e`.

| Outputs | Citry first load | Citry second load | Django second load | Citry select | Citry insert |
| --- | ---: | ---: | ---: | ---: | ---: |
| 140 | 75.2 ms | 49.1 ms | 56.4 ms | 31.4 ms | 29.3 ms |
| 1,400 | 368.1 ms | 348.8 ms | 330.1 ms | 240.4 ms | 240.2 ms |

The large second load improves by 12.6 ms against M08, including 9.52 ms in
the server phase and 3.0 ms in browser time. Treat the latter as run variation:
this change acts on the server, and the controlled source gain is 6.48 ms.
Large select/insert improve by 5.65/7.95 ms, mainly in server time. M09 is
retained. The remaining large-case gap is 18.7 ms in this short same-run
comparison; repeated final measurements still determine milestone attainment.
No extra profile was run because phase attribution agrees with the source
hypothesis. M10 source edits happened only after this wheel/build was frozen.


M10's source review and focused checks pass: Node scheduler/call-run tests
17/17 and three real-browser cases, including the built-in empty-task counter,
host-triggered reactive changes, public Events, and empty-to-many/reorder
lifecycle behavior. Source client SHA begins `993d6f30`, generated runtime
`7fae964b`; no compiler or native change is required. Biome, Ruff and diff
checks pass. The source browser checks use the existing benchmark runner's
CPython 3.12 environment with source imports and installed application
dependencies, avoiding incompatible borrowed browser binaries. Installed timing
was still pending at this point.

## M13: validate strict JSON once per public call

Before M13, `packages/protocol/events/v1/js/src/results.ts` validated strict JSON
at the envelope, result and action levels. `preflightResultEnvelope` then called
`validateExchange`, which repeats envelope validation. For one render action,
that repeatedly traverses the same prepared component payload. The schema and
correlation checks are useful; repeating the complete strict-JSON walk inside
one synchronous validation call is the candidate cost.

Introduce private shape-only helpers behind the public validators. Each standalone value validator remains strict-first, and `validateExchange`
still strictly validates its result envelope. Its typed call-envelope argument
is assumed valid, as before. Nested helpers reuse that fact.
Preflight can call a private correlation helper after its full envelope check.
Retain error precedence, paths, categories, messages and edge-error behavior.
Keep data-copy isolation and standalone validators; add no cache, public skip
flag or asynchronous gap between validation and reuse.

Review must check accessor, symbol, sparse-array, cycle and nonfinite-number
rejection, as well as errors in a later nested value taking precedence over an
earlier schema error. Existing cross-language fixture results must remain the
same. This is preferable to beginning with an opaque staged-update plan, which
would also need to account for asset scripts, changing definitions and mounted
state between preflight and commit. The synchronous validator case has a smaller contract to prove and is selected
for M13. Source implementation began after the M11/M12 wheel is frozen; the
opaque prepared-plan candidate remains deferred.


### M10 rejection after installed measurement

M10 passes qualification `20260913T051013Z-7118f964` and official run
`20260913T051426Z-520f0159`, but does not establish a performance gain.
At 1,400 outputs, first/second/select/insert are
368.3/350.4/248.4/240.2 ms. Browser-after is respectively
195.2/194.5/84.4/81.4 ms, compared with M09's
196.3/195.4/83.45/81.15 ms. These changes are within checkpoint variation.
The select regression is mainly server variation; this browser-only candidate
cannot explain that server cost.

At 140 outputs, first/second/select/insert are
74.6/49.5/32.65/29.15 ms. Same-run Django second load is 55.7 ms at 140 and 326.7 ms at 1,400.
The empty Promise work is not a material part of canonical browser time.
Reject M10 and restore the preceding scheduling code, including its host
handling. Keep its frozen wheel and results as experiment evidence. Remove
M10-only tests of the specialized behavior; M11's independent DOM annotation
removal and retention oracle remain. No savings are attributed to M10.
Full provenance is `.benchmarks/research/vue-optimization-m10/status.json`.


M11's final client is exactly accepted M09 minus the two occurrence-attribute
lifecycle blocks. M10 scheduling changes are absent. Client/runtime SHA prefixes
are `ccc61ff6`/`6b63822c`; existing Node tests pass 22/22 and the retained
lifecycle browser proof passes 1/1. The test asserts the final action's initial
text is 0, waits for the retained node to become 1, and rechecks its stable ID.

M12 source review passes on `capture.py` `4eec97c1`, `leaf_program.py`
`42f68344` and focused tests `e9c3c6a2`. Eight focused checks cover merging,
omission, snapshot separation and fallback values/origins/spans. The spread
plan itself distinguishes retained spread dictionaries from fixed-attribute
dictionaries, so no extra wrapper object is necessary. The resolver reads an
extension-owned mapping once, then copies that normalized dictionary for the
second snapshot. The paired Page diagnostic follows from this frozen source.


### M12 mixed source result and installed decision

The three-pair source diagnostic preserves all normalized payload and bundle
SHA sequences, output lengths, definitions, run members and warm native-call
counts. At 140, render-plus-prepare/full-Page improve by 1.048/1.207 ms.
At 1,400, render improves by 3.399 ms and preparation regresses by 4.825 ms;
the paired median combined change is +2.803 ms. Full Page improves by a paired
median 10.854 ms, with individual pairs -10.854/+4.992/-13.787 ms. These are
separate measurements and paired medians, so component medians need not sum.

This is mixed evidence, not performance acceptance. The full Page measurement
is closer to second-load TTI than standalone preparation, so the installed
comparison would decide whether to keep M12. No extra source matrix is needed.
Artifact: `.benchmarks/research/vue-poc/direct-relationships/m12-spread-attrs-page-run1.json`,
SHA `0e40a2c6d3181b0a303379027449eb1e1559e6cb12df04c0b88fdab4a32f3455`.
M11 is identical in both arms; M10 is absent.

Cumulative M11/M12 pure wheel `665e90f9768e6dc1534337c22e1f6af868586de76c4b84c9e2f72afbf51689d8`
reuses the M08 ABI3 core. Build
`4ea24f62ec3bc571be18bd32ab44fba08959ca5366fdb6ca8ba80f7c72623ef0`
was frozen for qualification and the installed comparison. M13 source edits
began only after this freeze and cannot alter those installed bytes.


### M11/M12 installed acceptance

Qualification `20260913T052706Z-608612e5` and official run
`20260913T053125Z-7d59fc5e` pass. Against accepted M09, cumulative M11/M12
improves second load by 1.7/24.5 ms at 140/1,400. At 1,400 the server phase
falls from 151.358 to 130.923 ms and browser-after from 195.4 to 191.0 ms.
These are cumulative observations: M11's individual contribution is not timed.

| Outputs | Citry first load | Citry second load | Django second load | Citry select | Citry insert |
| --- | ---: | ---: | ---: | ---: | ---: |
| 140 | 73.1 ms | 47.4 ms | 56.0 ms | 30.55 ms | 36.4 ms |
| 1,400 | 352.7 ms | 324.3 ms | 324.2 ms | 232.5 ms | 236.2 ms |

The installed full-Page flow resolves the mixed source result in favor of
keeping M12. Large first/select/insert improve by 15.4/7.9/4.0 ms. Small insert
has a server-phase outlier in this short checkpoint and needs the final repeated
comparison. Citry is 0.1 ms slower at 1,400 in this run, effectively tied within
measurement variation; this is not evidence of a clear win. At this checkpoint, the planned final repeated
comparison would determine whether both scales meet the milestone.
Full provenance: `.benchmarks/research/vue-optimization-m12/status.json`.

M13's final source review passes at `results.ts` `f4ff474a`, after execution
caught a data-action fallthrough in the first draft. The final explicit data
branch retains shared timing validation and relies on the outer strict-JSON
check. Protocol package checks pass 16/16. The diagnostic reference predates
Vue-renderer support, so its 114 comparisons establish parity only on shared
legacy cases; it is not an exact pre-M13 Vue worktree snapshot. Current prepared
renderer tests and browser qualification cover the actual Vue target.

A possible generated Python leaf evaluator was checked against the earlier
research before starting another attempt. `performance.md` records a similar
unrolled body function saving about 0.21 ms, below useful benefit. Do not repeat
that experiment unless a fresh profile identifies a materially different cost
in the current leaf evaluator. It has not consumed an optimization attempt.


### M13 installed acceptance and fresh profile

Qualification `20260913T053910Z-c0431734` and official run
`20260913T054320Z-a4f7bfd2` pass. The strict-JSON change cuts large-page select
and insert browser time by 26.50/27.05 ms. Total action latency improves by
26.45/29.45 ms. This supports retaining M13 for actions; it does not establish
a startup improvement.

| Outputs | Citry first load | Citry second load | Django second load | Citry select | Citry insert |
| --- | ---: | ---: | ---: | ---: | ---: |
| 140 | 73.3 ms | 47.5 ms | 54.0 ms | 26.75 ms | 25.1 ms |
| 1,400 | 352.0 ms | 332.8 ms | 324.9 ms | 206.05 ms | 206.75 ms |

Large second load is 8.5 ms slower than M12 in this short checkpoint, including
4.66 ms in the server phase, which this browser-only change cannot explain.
First load is effectively unchanged. A repeated final comparison was still
necessary at this point before judging the startup milestone. Full wheel and source hashes
are in `.benchmarks/research/vue-optimization-m13/status.json`.

The separate installed CPython 3.12.13 profile records the actual interpreter,
installed Citry and native package imports, application source and build. At
1,400 outputs its three profiled iterations have median render/serialize/total
times of 298.728/96.328/396.631 ms. These instrumented times are not comparable
to uninstrumented browser totals. Representative self costs are leaf operation
evaluation 24.58 ms, `isinstance` 22.84 ms, prepared JSON normalization
16.55 ms, expression variable-safety checks 15.62 ms, and dataclass conversion
15.23 ms. Cumulative times overlap and must not be summed.

The profile is `.benchmarks/research/vue-optimization-m13/profile_initial_page.json`,
SHA `5933c7452f31280ac3a6200f13323f947762de255242866aa929bbfe8381e5b3`.
Before opening another attempt, distinguish application data conversion from
Citry-owned structures and check whether any redundant browser copies can be
removed while preserving input, snapshot and reactive-state isolation.


### Candidate screening after M13

A JSON-copy function generated from compiler-known payload shapes was considered without implementation. Of
36,488 `_json_plain` calls, roughly 6,000 traverse compiler-created loop lists
and records; most remaining work validates actual user values. A second walker
could save an estimated 3–5 instrumented milliseconds at 1,400 outputs, before
its own traversal and fallback costs. This estimate is not a measured saving.
The extra shape checks, mutation fallbacks and duplicate traversal machinery
do not justify another attempt on this evidence.

The dataclass conversion cost comes from two application `model.snapshot()`
calls, through `Board.template_data()` and `Board.js_data()`. Reusing that
application snapshot could change the benchmark, but would not establish a
framework improvement. It is deliberately excluded from this round.

The final report will use three independent blocks, one session per block, no
extra warmup cycles and two page loads per session. Each block therefore
contributes one process-cold first load and one warm-server second load in a
fresh browser context. It compares Citry + Vue, Django + HTMX + Alpine,
Python API + Vue and Python API + React at both output counts. Optimization
progress is separate from these current-stack charts, with cumulative
M01/M02 and M11/M12 labels and M10 explicitly rejected.


### Stopping decision

Stop after 13 optimization hypotheses: 12 retained and M10 rejected. The
30-attempt limit is a ceiling, not a quota. Independent review agrees that
remaining candidates do not have a sufficiently large evidenced benefit.

Browser publication still has a discarded duplicate `serverData` clone: a
whole-occurrence clone is immediately given a separately cloned `serverData`.
The initial boundary copy and the separate mutable reactive copy have different
isolation duties and remain necessary. Removing the discarded intermediate
copy is a possible small cleanup, but existing browser attribution does not
support treating it as the next large milestone optimization. Broader staged
transaction reuse would need to handle asset callbacks, definition changes and
mount generations between validation and application. That complexity is not
justified by the current evidence. Neither candidate was implemented or counted
as M14.

The retained set improves server preparation, delivered code and action handling.
The final repeated comparison below determines the second-load result; stopping does
not imply that every requested performance target was reached. These are
experimental Vue worktree results, not proof that the broader Vue migration
is release-ready.


## Final repeated comparison

Four-stack qualification `20260913T055152Z-4c92bace` passes. Official run
`20260913T060101Z-30f25eb7` records 480 successful samples and zero failures
across three blocks. Each stack/scale contributes three first loads, three
second loads and six observations per server action. No source changes or
heavy concurrent work occurred during timing.

| Outputs | Stack | First-load TTI | Second-load TTI | Select | Insert |
| --- | --- | ---: | ---: | ---: | ---: |
| 140 | Citry + Vue | 73.6 ms | 47.5 ms | 26.95 ms | 25.1 ms |
| 140 | Django + HTMX + Alpine | 58.4 ms | 56.3 ms | 64.15 ms | 65.5 ms |
| 140 | Python API + Vue | 30.3 ms | 29.4 ms | 22.3 ms | 21.0 ms |
| 140 | Python API + React | 42.7 ms | 41.9 ms | 20.4 ms | 20.45 ms |
| 1,400 | Citry + Vue | 354.0 ms | 325.5 ms | 206.8 ms | 208.05 ms |
| 1,400 | Django + HTMX + Alpine | 333.8 ms | 326.8 ms | 614.95 ms | 879.6 ms |
| 1,400 | Python API + Vue | 212.0 ms | 208.7 ms | 90.75 ms | 87.2 ms |
| 1,400 | Python API + React | 269.0 ms | 266.9 ms | 145.3 ms | 155.15 ms |

These are local medians, not precise population or tail estimates. Django's
large actions vary substantially: select ranges from 476.1 to 1,021.9 ms and
insert from 789.1 to 1,089.3 ms. The report retains ranges and phase details.

### Second-load target assessment

Citry is faster at 140 in every block. At 1,400 it has a narrow median lead
and effectively reaches parity; this is not a robust claim of being faster
in every run. The one 0.1 ms loss is within the observed variation.

| Outputs | Block | Citry | Django + HTMX + Alpine | Citry minus Django |
| --- | ---: | ---: | ---: | ---: |
| 140 | 0 | 47.4 ms | 56.2 ms | -8.8 ms |
| 140 | 1 | 48.3 ms | 56.5 ms | -8.2 ms |
| 140 | 2 | 47.5 ms | 56.3 ms | -8.8 ms |
| 1,400 | 0 | 325.5 ms | 330.5 ms | -5.0 ms |
| 1,400 | 1 | 326.2 ms | 326.1 ms | +0.1 ms |
| 1,400 | 2 | 324.7 ms | 326.8 ms | -2.1 ms |

### Improvement from this round's baseline

The starting installed run was a single block, so these baseline-to-final
changes show the engineering trajectory rather than a paired experiment.
Static grouping was already present in that baseline and receives no additional
savings attribution here.

| Outputs | Metric | Baseline | Final | Reduction |
| --- | --- | ---: | ---: | ---: |
| 140 | First-load TTI | 98.8 ms | 73.6 ms | 25.5% |
| 140 | Second-load TTI | 66.1 ms | 47.5 ms | 28.1% |
| 140 | Select | 45.55 ms | 26.95 ms | 40.8% |
| 140 | Insert | 44.95 ms | 25.1 ms | 44.2% |
| 1,400 | First-load TTI | 606.0 ms | 354.0 ms | 41.6% |
| 1,400 | Second-load TTI | 535.6 ms | 325.5 ms | 39.2% |
| 1,400 | Select | 407.25 ms | 206.8 ms | 49.2% |
| 1,400 | Insert | 413.3 ms | 208.05 ms | 49.7% |

Large second-load phase attribution is about 130.91 ms on the server and
192.3 ms after receipt in the browser, plus 2.29 ms in the remaining phases.
Large select is about 147.886 ms server and 56.3 ms browser-after; insert is
151.662/54.25 ms. First load remains slower than Django, and both Python API
references retain lower startup and action times at 1,400. The completed round
does not establish that Citry is faster than all comparison stacks.

Raw summary and samples are in
`.benchmarks/results/vue-optimization-final-m13-official/20260913T060101Z-30f25eb7/`.
The standalone report adds graphs and accepted-experiment progress to those
measurements while preserving previous reports.


### Report artifact

[Open the standalone graph report](../../.benchmarks/research/vue-optimization-final-m13/report-v3.html).
It includes the full interactive phase, preparation and size charts at both
scales, followed by the accepted trajectory and paired-block comparisons.
All chart data and scripts are embedded; raw-data links resolve within this
worktree. Earlier report files are preserved. SHA-256:
`9f99c6548b5d888c9b34855dc8d55d93271874588a874f1a7c2f138a5ea8d8ec`.

Independent review recomputed the final medians, paired differences, phase
figures and baseline reductions from the raw artifacts. All agree.


### Integration check outcome

The fast repository profile is not green. Its first invocation stopped on a
stale one-item phase tuple for the removed client graph protocol. The runner
entry was removed and a test now checks the shape of every phase in the fast,
full and default profiles; all three focused checks pass, and independent
review accepts the fix. This changes check machinery only, not the frozen
benchmark implementation, and is not another optimization hypothesis.

Passing phases from the interrupted invocation were retained. Failed phases
were run again to capture their details, followed by phases that had not run.
This composed evidence has 12 passing and five failing phases. Rust format,
clippy and tests pass, as do the client and Events JavaScript checks, pyright,
CodeMirror, copied protocol Python, docs playground, VS Code extension,
lockfile and repository validators.

The failing groups are Ruff lint (eight findings), formatting (29 files),
Python typing, legacy protocol constraint inventories, and portable Python
tests. Pytest reports 6,761 passed, 873 failed, 14 collection errors, 111 skipped
and one expected failure. Failures span removed Alpine/ownership expectations,
Vue mount/dependency requirements, i18n/CSS/root-marker/UI integration, and
missing optional packages in the existing environment. These categories are
not proof that every failure predates this round; no clean pre-round full-suite
comparison was made. The performance qualification and 480 successful timed
samples cover the benchmark scenarios, not all public framework behavior.

The broad migration failures were recorded, not repaired as additional
performance experiments. The worktree is not ready for release. Full status,
phase output and hashes are recorded in
[status.json](../../.benchmarks/research/vue-optimization-final-m13/status.json).
