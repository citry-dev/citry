# Vue rendering strategy comparisons

This local research log compares the rendering strategies proposed in
[`vue.md`](vue.md). It follows the private ordinary-VNode HTTP integration,
which passed 10 Python tests and 23 browser checks. V1 through V6 isolate browser
and compiler behavior. V7 adds the first end-to-end canonical comparison.
V9 begins replacing the public runtime in this local worktree; the earlier
experiments did not make that change.

## V14: initial server and browser attribution, 2026-09-22

This pass explains the two largest initial-load questions in the fourteen-stack
report. It uses the retained composite report
`vue-migration-cohort-composite-14/20260922T153000Z-14-contestants`, an exact
warm server profile of the cohort Citry wheels, wire-manifest inspection, and a
separate sampling profile. Sampling changes elapsed time and therefore supports
function attribution only; the report remains the latency source.

At 1,400 outputs, Citry's second-load main-document server interval is 206.89
ms and its reported output-preparation span is 204.86 ms. A separate warm direct
profile measures 196.87 ms for `Page.render().serialize()` (117.89 ms rendering
plus 79.19 ms serialization). The roughly 2 ms difference between the report's
server and preparation intervals shows that Django, CSRF, and response setup are
not the main problem.

The request path is linear in rendered component occurrences. The 1,400-output
page creates 1,416 occurrences and 1,404 leaf programs, runs 21,681 safe
expression evaluations, and then transforms the typed result into 1,416 Vue
occurrences. Under cProfile, the overlapping major paths are 326.64 ms across
1,416 component `_render_one` calls, 186.75 ms across 5,907 leaf-program inner
evaluations, and 188.16 ms assembling the typed render. Assembly recursively
normalizes JSON 37,908 times, with 17,587 primitive calls. cProfile inflates the
whole operation from about 197 ms to 582 ms, so those milliseconds are not an
additive production-time split; the counts and rank identify repeated work.
Native Vue compilation is cached and absent from the important request
hotspots.

The benchmark adapter adds avoidable application work. `Board.template_data()`
builds a complete snapshot and `Board.js_data()` calls `snapshot()` again merely
to read the revision. At 1,400 outputs the duplicated snapshot path accounts for
about 39 cumulative cProfile milliseconds, again under inflated instrumentation.
This should be fixed in the adapter, then the server profile repeated. It cannot
explain the remaining Citry traversal and assembly work.

The duplicate was subsequently removed by carrying the already-computed scalar
revision from `template_data()` to `js_data()` on the same render instance. A
balanced in-process A/B measured about 0.8 ms at 140 outputs and 8.5 ms at 1,400
outputs. This exact component-lifecycle mistake was specific to Citry + Vue,
but an adapter audit found separate duplicate-snapshot bugs in Django + HTMX +
Alpine's initial request and Jinja + HTMX + Alpine's initial and action paths.
Those adapters now pass the already-captured state into their view-data helper.
Focused adapter tests pass. A local diagnostic reduced Django's initial request
from 6.137 to 5.371 ms at 140 outputs and from 56.119 to 49.817 ms at 1,400;
Jinja fell from 3.288 to 2.629 ms and from 24.636 to 18.649 ms respectively.
The other audited adapters already captured one application snapshot per
request.

The first fused-emission fast path removes another measured repetition. The
assembler previously called `typed_leaf_parts()` for every generated leaf only
to scan the reconstructed element openings for extension browser bindings.
Ordinary generated leaves cannot contain those bindings; they exist only when
an extension has explicitly supplied `cached_typed_parts`. Restricting the scan
and typed fallback to that cached case preserves the extension path while
allowing normal leaves to contribute their evaluated `prepared_data` directly.
Focused Vue tests passed (121 tests). With the duplicate-snapshot fix present,
2 warmups plus 7 samples measured 22.949 to 20.318 ms at 140 outputs (11.5%)
and 209.882 to 184.274 ms at 1,400 outputs (12.2%).

The current interactive document is client-rendered, not Vue-hydrated SSR.
Serialization replaces everything inside `<body>` with an empty Citry host, and
the browser calls `Vue.createApp(...).mount(host)`. The prepared server pass
therefore produces definitions, per-occurrence data, identities, event context,
and a document shell; it does not deliver a Vue-owned DOM tree for hydration.
The browser still creates and inserts the complete DOM.

That also explains why server compilation does not beat the Python API + Vue
control in browser time. The control already ships esbuild-produced handwritten
render functions, and Nuxt ships build-time compiled render functions. None of
the three pays Vue runtime-template compilation in the measured interval. At
1,400 outputs Citry and Python API + Vue have essentially equal `browser_after`
medians, 205.05 and 203.25 ms. A focused sampling profile of the same shape puts
roughly 60 ms of Citry samples in native `insertBefore`, about 11 ms in native
`createElement`, and about 28 ms in Vue's minified mount path. Nuxt's hydrated
profile does not show DOM creation or insertion as corresponding top samples.

The reported Nuxt comparison needs one measurement caveat. Its 162.70 ms
`browser_after` is 19.95% below Python API + Vue's 203.25 ms, but Nuxt has
already sent and parsed SSR HTML during the document exchange. Its 6.90 ms
response-receive segment is much larger than Python API + Vue's 0.10 ms, and its
main-document server costs 22.23 ms rather than 1.18 ms. End to end, Nuxt is
195.40 versus 205.50 ms, a 4.9% advantage. The SSR-plus-hydration path is faster
in this comparison, but the control does not isolate hydration from SSR HTML
delivery, server work, transfer, or the phase boundary. The `browser_after`
subphase also places incremental HTML parsing before that boundary.

Other measured differences explain fixed and protocol overhead without
explaining the whole large-page result:

- Citry makes 12 initial requests and transfers 1,710,737 identity-encoded body
  bytes at 1,400 outputs. Python API + Vue makes four requests and transfers
  478,034 bytes; Nuxt makes six and transfers 2,354,827 bytes.
- Citry's document contains an approximately 1.28 MB prepared manifest. Its
  1,416 occurrence records occupy about 1.27 MB: prepared data is about 803 KB,
  while repeated IDs, parent IDs, placement keys, render IDs, definition IDs,
  and type keys account for hundreds of kilobytes. The 1,400 `ProjectOutput`
  records alone are about 1.06 MB, including about 604 KB of prepared data and
  413 KB of repeated identity fields.
- Citry's runtime response is about 361 KB in the retained report, versus a
  72.8 KB Python API + Vue client bundle and about 171.6 KB of Nuxt chunks. This
  matters more at 140 outputs, where Citry's browser interval is 42.05 ms versus
  26.85 ms. At 1,400 outputs, DOM work dominates and Citry reaches parity with
  the client Vue control despite that fixed overhead.
- The isolated ordinary-VNode comparison measured only a 2.1 ms mount penalty
  at 1,400 outputs against the hoisted optimized control. Ordinary VNodes are
  therefore not the primary explanation for current client mounting. Their
  hydration cost remains unmeasured, and Vue's compiler metadata can accelerate
  hydration as well as later updates.

The current architecture is client-rendered with a server-prepared protocol: it
pays Python component execution and a second prepared-assembly pass, then sends
an empty app host and performs full client DOM creation. The experiments below
tested the two coherent endpoints before more local tuning:

The full initial path is:

1. The application snapshots its server model and adds view-derived values.
2. Citry runs component data callbacks, slots, `c-if`, and `c-for`, evaluates
   Python expressions, and creates the typed render tree.
3. Vue preparation walks that completed tree and separates reusable component
   definitions from per-render component occurrences.
4. The native compiler turns each unique definition into a browser render
   function. Citry serializes those definition descriptors and every occurrence
   into the prepared manifest.
5. The response carries the physical document shell, an empty Vue host, the
   manifest, and runtime/definition assets.
6. The browser reconstructs the occurrence relationships and mounts the Vue
   tree, creating all DOM below the host.
7. Event responses send later occurrence revisions through the same protocol.

The manifest is the serialized intermediate representation joining stages 3
and 6. Its root fields identify the protocol, app, revision, root occurrence,
markers, definitions, and occurrences. Definition descriptors identify compiled
render-function assets plus directive, dynamic-element, local-call, replacement,
opaque-HTML, and runtime-event sites. Each occurrence contains its stable ID,
type and definition IDs, physical parent and placement key, `js_data()` as
`serverData`, and evaluated template values as `preparedData`. The latter holds
resolved text, attributes and keys; branch and `c-for` results; child calls and
selected slots; controls; and runtime event bindings.

“Double rendering” refers to three different repetitions here. First, the
benchmark adapter accidentally calls `snapshot()` once through
`render_snapshot()` and again from `js_data()` merely to read the revision.
Second, Citry evaluates the typed render and then traverses it again during
prepared assembly; this does not rerun `template_data()`, but it does repeat
structural walking, validation, materialization, and JSON normalization. Third,
the server resolves the complete logical page while the browser later constructs
the complete physical DOM because no hydratable body was delivered. The first
is adapter waste, the second is the fused-emission target, and the third is the
hydration target.

1. **Vue-compatible hydration.** Emit the actual body DOM with Vue's required
   fragment, conditional, and special-node markers, switch to `createSSRApp`,
   and compare identical VNodes under mount and hydration. This tests whether
   avoiding native creation/insertion closes the approximately 42 ms Citry/Nuxt
   `browser_after` gap at 1,400 outputs. The first proof should keep current
   per-occurrence data and callbacks so only bootstrap changes.
2. **Compact already-resolved server output, without changing directive
   ownership.** `c-for` must remain a Citry/Python operation and `v-for` must
   remain a reactive browser operation; converting one into the other would
   change when and where user code runs. The discarded broad proposal was to
   preserve a server loop for Vue and send its source collection as bulk JSON.
   A valid narrower experiment may compact the results only *after* Citry has
   executed the `c-for`, including every Python component, slot, callback, and
   Event that it implies. This could reduce the 1.28 MB wire manifest, but does
   not by itself remove the measured Python occurrence-expansion cost and is
   therefore no longer one of the leading server-time experiments.
3. **Controlled Nuxt SSR/CSR comparison.** Run the same compiled Nuxt page with
   SSR on and off, retaining the same readiness and semantic checks. This
   separates hydration from Nuxt's single-component template structure and
   from the report's phase-boundary placement.
4. **Fuse typed rendering and assembly after the architectural controls.** If
   the general prepared path remains necessary, emit occurrence data and
   compiler fragments during component execution rather than creating typed
   parts and walking them again. Reuse JSON-safe values within one occurrence
   and compact repeated identity fields on the wire. This follows the measured
   repeated work rather than treating native compilation as the target.

The leading recommendation is to prototype hydration first, establish the Nuxt
SSR/CSR control, and then fuse Citry's typed rendering with prepared occurrence
emission. These retain the existing division between server-side `c-for` and
browser-side `v-for`.

### Completed architectural controls

The focused Nuxt SSR/CSR control uses the same Nuxt 4.5.2 application, data,
readiness signal, and actions, changing only `ssr: true` to `ssr: false`.
Qualification passed 44/44 cases and the latency run passed 240/240 observations
across three blocks. Warm second-load medians were:

| Outputs | Mode | Main server | Response receipt | Browser after | Total |
|---:|---|---:|---:|---:|---:|
| 140 | Nuxt SSR/hydration | 4.844 ms | 0.100 ms | 38.800 ms | 45.200 ms |
| 140 | Nuxt CSR | 0.734 ms | 0.100 ms | 27.600 ms | 29.400 ms |
| 1,400 | Nuxt SSR/hydration | 22.866 ms | 7.100 ms | 161.900 ms | 195.500 ms |
| 1,400 | Nuxt CSR | 0.726 ms | 0.100 ms | 199.700 ms | 201.500 ms |

SSR plus hydration is a scale-dependent trade. At 140 outputs, matching the larger SSR
document costs more than fresh client creation. At 1,400 outputs, it removes
37.8 ms (18.9%) from `browser_after`; the added server and response work reduces
that to a 6.0 ms (3.0%) end-to-end win. Actions are effectively identical,
in this measurement.

An opt-in Citry proof then retained Python-rendered body HTML, emitted Vue
fragment bounds for the canonical component and `c-for` structure, removed
source-only directive/ownership attributes, and selected `createSSRApp`.
Chromium reported zero hydration mismatches and reached readiness while reusing
all original elements: 477 elements at 14 outputs, 3,708 at 140, and 36,018 at
1,400. Direct mount/hydration intervals were 4.9, 9.9, and 41.9 ms respectively.
This establishes structural feasibility for the canonical page; it is not yet
a production hydration contract. General correctness still needs the design's
empty output, table normalization, slot/fragment, opaque HTML, directive, and
extension counterexamples, plus an end-to-end comparison including larger HTML
serialization and transfer.

The focused end-to-end control then used identical current Citry/Core wheels
for ordinary client mount and the hydration probe. Qualification passed all 44
cases; latency and size capture passed 160/160 observations. Warm second-load
medians were:

| Outputs | Mode | Prepare | Main server | Response receipt | Browser after | Total |
|---:|---|---:|---:|---:|---:|---:|
| 140 | Client mount | 21.691 ms | 22.663 ms | 0.150 ms | 42.250 ms | 66.550 ms |
| 140 | Hydration | 53.802 ms | 55.058 ms | 0.150 ms | 52.500 ms | 109.050 ms |
| 1,400 | Client mount | 187.204 ms | 189.221 ms | 0.550 ms | 202.750 ms | 393.950 ms |
| 1,400 | Hydration | 501.070 ms | 503.832 ms | 6.950 ms | 180.750 ms | 692.950 ms |

`Prepare` is a server-local subspan of `Main server`; it must not be added to
`Main server` or `Total`. Totals also contain the omitted `browser_before` and
exchange-residual intervals.

At 1,400 outputs, reusing all counted elements saves about 22 ms in `browser_after`,
but the proof's additional 314 ms of server preparation dominates. The main
document grows from 1,282,171 to 2,685,480 bytes and all initial bodies from
1,741,854 to 3,145,222 bytes. At 140 outputs hydration loses in the browser as
well as on the server. Actions remained essentially unchanged in the measured
run; the intended difference is confined to the initial hydration document.

A serialization profile identifies why the proof's server cost is not the
irreducible cost of hydration. At 1,400 outputs it spends two dominant passes in
Python's `HTMLParser`: `_hydration_host()` parses the populated body to infer
root count, and `VueSerializationPlan.finalize()` parses the entire hooked
document again to validate the host. It also calls `static_leaf_parts()` 1,404
times, recursively materializing 6,107 leaf operations into HTML after the
prepared-data pass. A production candidate should derive root shape and fragment
bounds from the typed/compiler plan, validate the host structurally without
reparsing the multi-megabyte document, and emit hydratable HTML alongside
prepared values during the original leaf evaluation. A fused emitter is the
next way to measure whether the approximately 22 ms large-page browser saving
justifies the extra response bytes after removing these probe-specific passes.

The next bounded assembly experiment did not justify another local change. The
current warm 1,400-output path measured about 168–171 ms. Under cProfile, leaf
evaluation accounted for about 207 instrumented ms, prepared assembly for about
108 ms, and `_json_plain()` for about 50 ms within assembly; these instrumented
times overlap and are not production-time additions. Identity tracing found
12,724 aggregate normalization calls, all on distinct objects, so memoization
has no repeated object to reuse. A temporary primitive-specialized normalizer
was slightly slower across 20 samples. Directly adopting leaf data is also not
safe under the current mutable contract: an existing test mutates a nested
prepared value to `NaN` and requires final assembly to reject it. The next
meaningful step is therefore a designed capture-time normalization and
occurrence-emission contract, or an immutable/mutation-tracked prepared payload;
a cache or mechanical rewrite of `_json_plain()` is rejected.

### Current server operation profile

The operation-level profile uses low-overhead counters and nested timers, with
an ordinary warm run as the wall-clock reference. At 140 outputs, rendering
takes 12.17 ms and serialization 6.52 ms, for 18.69 ms total. At 1,400 outputs,
rendering takes 119.08 ms and serialization 48.27 ms, for 167.35 ms total.
Instrumentation changes the timings below, so nested rows explain composition
and must not be added to their parents.

| Operation | 140 calls / instrumented ms | 1,400 calls / instrumented ms |
|---|---:|---:|
| Component renders | 156 / 11.40 | 1,416 / 105.20 |
| Body walks | 335 / 9.80 | 2,945 / 82.90 |
| Typed leaf renders | 144 / 5.30 | 1,404 / 54.10 |
| Expression evaluations | 869 / 0.42 | 8,429 / 4.06 |
| Component node calls | 155 / 0.53 | 1,415 / 4.24 |
| Slot renders | 7 / 1.34 | 7 / 4.92 |
| Slot capture | 7 / 1.28 | 7 / 4.84 |
| `c-for` calls / iterations | 10 / 337 | 10 / 3,217 |
| `c-for` including loop bodies | 10 / 1.09 | 10 / 8.26 |
| Derived `c-for` bookkeeping | 10 / 0.28 | 10 / 1.83 |
| Extension component-data hooks | 156 / not isolated | 1,416 / 6.33 |
| Data normalization | 468 / 0.25 | 4,248 / 2.04 |
| Finalization hooks | 156 / 0.18 | 1,416 / 2.03 |
| Occurrence construction | 156 / 0.50 | 1,416 / 4.54 |
| Prepared-data detachment | 156 / 0.34 | 1,416 / 3.03 |

At 1,400 outputs the result contains 1,416 component occurrences, 1,415 parent
links, 1,404 leaf programs, seven slot projections, and seven direct call-run
relationships. Those occurrences share 11 component definitions and 11 compiler
inputs. The native Vue compiler runs 11 times; definition compilation is not a
per-occurrence cost on this path.

Final strict-JSON validation visits 37,908 values: 16,263 strings, 10,504
dictionaries, 8,813 integers, 1,416 constant mappings, 804 lists, 104 booleans,
and four nulls. Of 17,587 top-level validation calls, `attach_leaf_data()` makes
15,717, `transform_component()` makes 1,416, `_json_attribute_map()` makes 331,
and `transform_parts()` makes 123. cProfile attributes about 25 ms of self time
and 42 ms of cumulative instrumented time to `_json_plain()` at 1,400 outputs.
These are slowed profiler times, not removable wall-clock milliseconds.

The final configuration JSON is 148,658 bytes at 140 outputs and 1,281,603 bytes
at 1,400 outputs. The corresponding UTF-8 response bodies are about 149,177 and
1,282,121 bytes. These measure serialized data sent to the browser, not the
memory occupied by the larger Python object graph. The diagnostic scripts and
raw results are under `.benchmarks/research/vue-server-operation-profile-20260922.py`,
`.benchmarks/research/vue-server-cprofile-20260922.py`, `profile-140-light2.json`,
`profile-1400-light3.json`, `cprofile-140.json`, and `cprofile-1400.json`.

A follow-up counted 2,845 identity-digest calls per 1,400-output render. Every
input within one render was distinct. The apparent 80% repetition across five
samples was the same 2,845 identities recurring on later renders. A diagnostic
cross-render cache was slower after constructing general nested cache keys, and
such a cache would retain dynamic component keys between requests. No cache was
adopted. These digests define browser-visible component, slot, placement, and
event identities; changing their bytes needs an identity-protocol design. The
evidence is in `.benchmarks/research/digest-profile-20260922.py` and the matching
`digest-profile-140.json` and `digest-profile-1400.json` results.

The leaf evaluator was then split by operation type. At 1,400 outputs it walks
68,551 operations and produces 15,717 prepared-data keys plus 8,803 resolved
opening records. The timings include observer overhead; they compare operations
within this run and are not additive wall-clock costs.

| Leaf operation | Calls | Inclusive ms | Exclusive ms |
|---|---:|---:|---:|
| Spread-attribute opening | 1,400 | 38.50 | 38.50 |
| Server loop | 804 | 36.73 | 14.21 |
| Dynamic text | 8,307 | 17.92 | 17.92 |
| Conditional | 2,803 | 19.74 | 11.23 |
| Fixed-attribute opening | 7,303 | 7.28 | 7.28 |
| Static content | 31,427 | 5.61 | 5.61 |
| General dynamic opening | 100 | 1.54 | 1.54 |
| Static opening | 8,704 | 1.96 | 1.96 |
| Closing element | 7,703 | 1.73 | 1.73 |

Raw expression interpretation is 4.15 instrumented ms across 8,429 calls.
`PreparedExprNode.resolve_value()` is 13.28 ms because it additionally handles
constant values, nested-template values, text conversion, escaping, trusted
HTML, and fallback rendering. For dynamic openings, `_resolve_for_output()` is
9.38 ms and `_prepared_from_resolved()` is 12.81 ms across 1,621 calls. The
canonical page has no event, poll, or control bindings on these leaf openings.
The leading bounded experiment is therefore to let a proven ordinary spread
opening produce its final attribute dictionary directly, while retaining the
full `PreparedElementOpen` path for Vue syntax, events, controls, keys,
extensions, unsafe attributes, and materialization requirements.

Evidence is in `.benchmarks/research/leaf-operation-profile-20260922.py`,
`leaf-operation-profile-140.json`, `leaf-operation-profile-1400.json`,
`leaf-method-profile-140.json`, and `leaf-method-profile-1400.json`.

The first direct plain-spread candidate measured a promising diagnostic result,
but independent review rejected it pending stricter parity. `_resolve_for_output()` has already
validated names, merged contributions, normalized `class` and `style`, and
removed `None` and `False`. When the compiled opening also proves that it has no
Vue syntax, runtime Events candidates, metadata, active i18n catalog, attribute
hook, class/style accumulator, or authored/data collision, the leaf retains the
resolved dictionary instead of creating a general `PreparedElementOpen` and
then converting it back into a dictionary. General and extension cases keep the
old path. However, the first guard still allowed authored ordinary attributes
whose original spelling and quoting the full `PreparedElementOpen` preserves,
and it allowed an i18n wrapper while resolving the underlying node directly.
The first A/B also used different session identities and did not establish exact
output equality. The candidate must exclude authored source attributes and i18n
wrappers, then prove equal manifest and HTML bytes under one identity before its
timing can be accepted.

| Outputs | Measure | General path | Direct plain spread | Saving |
|---:|---|---:|---:|---:|
| 140 | Render | 11.883 ms | 11.145 ms | 0.738 ms (6.2%) |
| 140 | Render plus preparation | 17.046 ms | 16.407 ms | 0.640 ms (3.8%) |
| 1,400 | Render | 115.452 ms | 101.942 ms | 13.510 ms (11.7%) |
| 1,400 | Render plus preparation | 153.772 ms | 146.859 ms | 6.913 ms (4.5%) |

In this provisional run, at 1,400 outputs about 6.2 ms moved from render into
preparation because the static fallback still materialized the retained plain
mapping there. The 6.913 ms comparison includes both phases but excludes final
JSON encoding and transport; it is not yet an accepted end-to-end saving.
Diagnostic source and raw results are
under `.benchmarks/research/direct-spread-ab-20260922.py` and the matching
`direct-spread-ab-{140,1400}-{off,on}.json` outputs.

The corrected experiment rejected the candidate. It requires no authored
ordinary attributes and requires the renderer to be the original opening node,
so source spelling and i18n wrapper behavior cannot be skipped. The canonical
page's only `c-bind` opening is wrapped by the i18n attribute node; the strict
shortcut consequently ran zero times. With equal deterministic IDs, session and
app identity, render sequence, manifest hash, HTML hash and byte counts, the
candidate was slower: render plus preparation changed from 17.862 to 18.371 ms
at 140 outputs (+2.8%) and from 152.078 to 155.204 ms at 1,400 (+2.1%). The
shortcut was removed. Focused fallback coverage now includes authored boolean,
quoted, entity-encoded and unquoted attributes plus the i18n wrapper; 225 Vue
tests and Ruff pass. The original 38.5 instrumented ms spread bucket therefore
includes required wrapper/formatting behavior on this page; the first apparent
saving came partly from skipping that behavior.

A same-context recursion experiment removed redundant context-variable wrappers
for selected `c-if` branches and empty `c-for` branches. Evaluation wrappers
fell from 597 to 314 at 140 outputs and from 5,907 to 3,104 at 1,400, with exact
response and payload parity. Timing did not establish a retained gain. In a
15-sample run, the 1,400-output render changed from 116.009 to 113.136 ms, but
render plus preparation changed from 156.685 to 157.487 ms; an earlier
seven-sample run reversed the render direction. The candidate is rejected and
removed because the complete server result overlaps measurement noise.

## V9: Vue-only migration and combined assembly

**Mode change, 2026-09-12:** the user requested removal of the ownership and
Alpine implementations from this worktree. Historical results provide the
comparison. Keeping a graph-backed mode in current source is no longer an
experiment requirement.

The implementation plan is in the
[Vue-only cutover design](vue.md#vue-only-cutover-2026-09-12). Work includes
deleting dormant Python graph branches and native storage, replacing shipped
browser dependencies and Events emission, handing the selected render directly
to serialization, and combining typed capture with prepared-output assembly.
Final post-hook `js_data` now belongs to its component render context, avoiding
the prototype's external capture store. A new profile will follow the completed
cutover; V8 timings are not measurements of these changes.

This migration also requires Vue-aware diagnostics, editor metadata, and owned
templates/scripts. Such consumers must be migrated or explicitly recorded as
unfinished; a successful private benchmark alone does not establish a complete
runtime replacement.

The output-cache replay format serializes ownership locations, calls, fills,
regions, and queue records. That format is being removed with the graph. During
the cutover, configured output caching follows normal rendering rather than
reading or writing the obsolete artifact. This preserves rendered output and
normal hooks but temporarily gives up cache-hit behavior and its performance.
A typed selected-output cache needs its own implementation and qualification;
the migration must not report the cache as fully ported before that work.

The removal pass has deleted the Python ownership graph, manifest, graph adapter,
and replay modules, plus the Rust ownership crate, its PyO3 storage surface, and
the client-graph binding. Normal rendering uses direct relationships, and static
serialization does not emit graph manifests or range caps. The render/slot/
provide/extension semantic sweep passed 240 tests with one expected failure.
The remaining work is the default Vue document/Events integration, combined
assembly, dependent source/tooling migration, and new performance measurements.

The Events producer now sends complete root or target-subtree snapshots without retaining previous
prepared pages on the server. The browser derives topology changes from its
committed snapshot and checks the base revision before mutation. Compiler and
asset caches remain; page-history storage is not required for this protocol.

Independent review found a responsibility that must survive graph deletion:
dependency records from discarded hook output must not reach the browser.
At discovery time Dependencies and i18n consumed accumulated render records,
whereas Events already used the selected occurrence map. The correction now
filters both through the final selected occurrence set, without restoring graph
retirement. Review also
identified obsolete Alpine CSP-expression restrictions and the need to report
the temporary output-cache bypass explicitly.

The app-root benchmark does not cover nested Events owners. Same-class
component-subtree refresh, different-class replacement, and explicit-marker
insertion are separate integration cases in the design. No successful root
benchmark should conceal missing support for those operations.

V9 experiment ledger, before new timing qualification:

| Change or candidate | State | Evidence and next check |
| --- | --- | --- |
| Delete graph, retirement, physical ranges, Alpine runtime and native ownership storage | Implemented in the core removal pass | Core semantic tests and native compile check pass; public runtime migration is still in progress. V8's small graph/direct difference is not a V9 timing. |
| Capture final `js_data` on the render context and share exact selected occurrence mapping | Implemented | Removes external data capture and order-based Events matching. Qualify discarded hook output across all extensions. |
| Precompute authored attribute source slices | Implemented | Template-node construction now owns source encoding and slicing. Per-render attribute objects and sorting still remain. |
| Freeze occurrences only after their logical definition is known | Implemented | Removes the initial placeholder occurrence; wire encoding maps compiled IDs without rebuilding each occurrence. |
| Emit compiler input, bindings, identities and validation during one selected traversal | Implemented on the production Events path | Compiler fragments replace the ordinary prepared-node mirror; independent review found no benchmark-path blocker. Legacy private helper/test interfaces still need migration. |
| Use the same typed output for normal static and interactive serialization | In progress | Static output must skip Vue compilation; interactive output must avoid generating a discarded flat body. |
| Compile server-event listeners into Vue's lexical component closures | In progress | Replaces the temporary DOM scan and closest-component lookup, which is incorrect inside caller-owned fills. No latency saving measured yet. |
| Explicit production flags for the newly packaged Vue runtime | Build correction in progress | Whitespace-only esbuild minification selected development mode; the new Vue-only bundle needs explicit production definitions and browser requalification. Historical V8 used a different production runtime artifact. |
| Record deferred child work while building output instead of searching ordinary leaves afterward | Candidate, profile first | The V8 profile includes a deferred-child scan. Hooks can replace output, so any fast path must preserve post-hook selection and lexical context merge order. |

No new percentage saving is assigned to these rows until a coherent version
passes behavior checks and is measured. Instrumented call counts help choose
work; they are not substitutes for ordinary request latency.

### Universal typed checkpoint: source diagnostic before final fusion

The 140-output page has 154 component occurrences. A source-tree Python 3.14t
diagnostic used two warmups and seven measured samples. Stage medians:

| Stage | Milliseconds |
| --- | ---: |
| Python rendering | 26.885 |
| Selected-tree assembly | 27.864 |
| Native compiler/cache wrapper | 0.991 |
| Remaining producer work | 0.362 |

The producer's preparation interval, which includes assembly and compilation
but excludes Python rendering, had a median of 29.180 ms. Stage medians should
not be summed as though they came from one sample. Assembly is now the largest
individual stage and remains the next optimization target.

This uses a different interpreter/environment from the V8 installed-wheel
Python 3.12 results, so it does not establish a percentage improvement over V8.
It also excludes final HTTP encoding and transport. The original small harness
and raw samples are retained at
`.benchmarks/research/vue-poc/direct-relationships/profile-universal-before-fusion.{py,json}`.
That capture hashes three central source files, not the whole implementation;
later captures need broader source/native provenance and a start/end stability
check. The public browser smoke at this point passes an initial mount and one
normal Events update, but the shared serializer and lexical event-handler
integration remain unfinished.

The subsequent shared-runtime checkpoint passes four real Chromium tests:
normal signed Events across two updates with refreshed State tokens, standalone
local Vue without Events routes, two independently serialized apps sharing one
runtime, and a receiver-only refresh selecting fallback while preserving its
sibling. The latter initially kept the old supplied slot and is now corrected.
Native Events dispatch uses the lexical component record; authored argument
closures, full-document shell/compiler partitioning, and broader extension
migration remain under implementation. These are behavior checks, not new
end-to-end benchmark results.

Review of the new JavaScript build found approximately 277 KiB of Vue runtime
before the coordinator and Events code, versus approximately 106 KiB for the
installed upstream production global runtime. These are different bundlings,
not a measured saving. The new file retained development branches because
[esbuild defaults `NODE_ENV` to development unless all minification options are
enabled](https://esbuild.github.io/api/#platform). The correction explicitly
selects production, retains Options API, and disables production devtools and
detailed hydration warnings using [Vue's documented compile-time
flags](https://vuejs.org/api/compile-time-flags.html). Replaying the original
build options in memory against the same current Vue source establishes:

| Vue asset build | Bytes |
| --- | ---: |
| Original whitespace-only options | 283,409 |
| Explicit production flags and syntax minification | 215,835 |
| Also minify internal identifiers, Vue target only | 117,559 |

The final Vue asset is 58.5% smaller than the original-options rebuild, SHA-256
`fc8b9e95faff9dcf4c605366653aa82da3d689208fcca5842820789d63c2ad75`.
The combined runtime is 198,101 bytes, SHA-256
`ae295d53c0b2c0b6b888c65932ce2e7c8a416bb79255bb5def467c4097e775e9`.
Coordinator changes happened concurrently, so the combined-file difference is
not attributed solely to these build flags. Build exactness, type checks and
the 11 JavaScript tests pass; broader browser qualification remains. These are
byte savings, not latency measurements, and do not revise V8's timings.

### Incremental assembly experiments

The following consecutive captures use the same development diagnostic at
140 outputs. They are not alternating controlled pairs; small differences
may reflect host noise. Values are stage medians in milliseconds.

| Checkpoint | Render | Assembly | Compile/cache | Producer preparation |
| --- | ---: | ---: | ---: | ---: |
| Universal typed baseline | 26.885 | 27.864 | 0.991 | 29.180 |
| Reuse static source/open/close descriptors | 19.400 | 27.998 | 0.989 | 29.330 |
| Cache immutable binding-site digests | 18.707 | 21.156 | 0.982 | 22.456 |
| Produce compiler input during definition finalization | 19.472 | 20.679 | 0.992 | 21.995 |
| Replace binding digests with per-owner ordinals | 19.076 | 20.044 | 0.911 | 21.256 |
| Enforce builder invariants without repeating whole-view validation | 18.819 | 18.906 | 0.919 | 20.139 |
| Derive authored/data attribute groups once per element descriptor | 19.619 | 16.858 | 0.915 | 18.112 |
| Build compiler fragments directly, without the intermediate node tree | 19.820 | 11.659 | 0.915 | 12.883 |

Static descriptor reuse removes work that never depends on the component
instance. Binding-digest caching demonstrated substantial repeated hash work,
but was superseded by ordinal binding names, which need neither hashing nor
a lookup cache. Component and slot identities retain authored-site/key
semantics. Definition finalization now shares its compiler input with the
producer. Builder validation is undergoing independent review against the
strict constructor; removing a duplicate check must not weaken the
construction invariants.

Independent review found missing revision/root-anchor validation and incorrect
key scoping for repeated slot-hook placements. Those checks must be corrected
before accepting the validation change. Separate authored component sites also
need distinct Vue keys even when the author supplies the same local key.
Test-only reconstruction and binding/parent audits exercise these invariants
without adding a validation traversal to every production render.

Assembly fell by about 16.20 ms, or 58.2%, between the first and last captures.
This is a diagnostic-stage comparison, not an end-to-end performance claim.
The fragment change alone saved about 5.20 ms against the preceding checkpoint
(30.8% of assembly). It appends authored/generated compiler text, rebases
UTF-8 metadata when inserting a slot fill, and keeps lexical data ownership
separate from physical component placement. The production Events path consumes
that input directly. Independent review found no additional benchmark-path
semantic blocker; 37 focused checks passed. Existing private helpers that
promise full `PreparedView` definitions still need migration, so this is not
a claim that the entire repository test suite passes.

Raw results are the `profile-*.json` files beside the baseline harness. The
final row uses `profile-fragment-fusion.{py,json}`, whose script asserts equal
source hashes before and after measurement and records the native module hash.
The next checkpoint was the requested installed-Python-3.12 HTML graph report;
further assembler experiments paused until that report was delivered.

### Intermediate public-path benchmark, 2026-09-13

At the user's request, optimization paused to measure and graph the current
implementation. The canonical adapter now uses ordinary
`Page(...).render().serialize()`, the default Events dispatcher, signed routes
and the packaged runtime. Its custom prepared bootstrap and Events DOM scan
are not part of this run.

Qualification `20260912T233122Z-453f6b64` passed. Timed run
`20260912T233258Z-037e7e2c` has 160 successful measurements across four stacks,
14/140 outputs, two loads and two cycles of nine actions. The standalone
comparison at `.benchmarks/research/vue-fusion-intermediate/report.html` adds
exactly 40 optimized Alpine Citry observations from
`20260911T120026Z-81b161c7`. The visible banner and `provenance.json` identify
that historical row; it was not rerun concurrently. Raw current results remain
unchanged. The report contains ten interactive SVG charts, with no browser
errors in its inspection.

140-output medians in milliseconds:

| Stack | First load | Second load | Select action | Insert action |
| --- | ---: | ---: | ---: | ---: |
| Citry + Vue | 102.00 | 71.60 | 51.00 | 50.55 |
| Optimized Citry + Alpine, historical | 119.50 | 100.30 | 160.90 | 152.65 |
| Django + HTMX + Alpine | 58.30 | 56.20 | 68.40 | 69.95 |
| Python API + Vue | 29.90 | 29.50 | 21.95 | 21.00 |
| Python API + React | 42.20 | 41.90 | 20.35 | 19.95 |

This is a small local diagnostic run: one measurement per page-load stage and
two per action/count/stack. Second loads warm server state while starting a new
browser context. The result supports choosing the next experiments, not a
publication-grade ranking or an isolated attribution to one optimization.

Citry + Vue server output preparation measures 38.142 ms on second load and
36.038 ms on select, compared with Django's 4.844/4.886 ms. Browser improvements
now give Citry the lower select/insert totals in this run, but server work
remains substantially higher. The initial serializer still materializes a
body before producing its Vue shell; eliminating that pass is the next
measured serializer experiment. Core profiling and authored-run coalescing
resume after the report.

Clean wheels installed under Python 3.12.13:

- Citry `8d67a14c0bb8dc240d7b263f719b4670245c879b11b6fc02c86dace0875180a9`.
- Citry-core ABI3 `f494e43a39ba0a5bf9caf9b07cf0212b043898ce6793381fcfd29f1c728a5d31`.

Both are under `.benchmarks/wheels/vue-fusion/`. Packaging first exposed stale
setuptools build output that included deleted modules. That wheel and its
prepared environment were excluded from measurement. Generated build metadata
was moved intact to `.benchmarks/build-quarantine/`, then the clean wheel was
rebuilt and checked for absent ownership/client-graph modules. No quarantined
files were deleted.

### Work resumed after the intermediate report

The report and its installed wheels remain the fixed comparison checkpoint.
Source work then grouped adjacent immutable authored template pieces, keeping
Vue attributes and physical document boundaries available for inspection.
The consecutive Python 3.14t diagnostic at 140 outputs measured render 17.958,
assembly 9.004, compile/cache 0.915, and producer preparation 10.238 ms.
Preparation excludes rendering. These are stage medians from two warmups and
seven observations in `profile-static-runs.{py,json}`. They do not measure
the initial document serializer or update the installed-wheel HTML report.
An initial one-observation comparison regressed at 140 outputs and improved
at 1,400, prompting inspection of garbage collection and compiler calls. The
final controlled run uses six alternating fresh-process pairs per count,
one excluded warmup and five consecutive measured renders per process.
It records actual native compiler calls: zero in every measured batch.
Median paired render-plus-preparation savings are 3.094 ms at 140 outputs
and 50.518 ms at 1,400 outputs. Garbage collection remains enabled and is
included in those times. Its different placement helps explain why a single
post-warmup observation gave a different result; it is not established as
the sole cause of the earlier regression.

The final timestamp is `2026-09-13T00:02:38Z`; results and harness are
`profile-static-runs-paired.{py,json}` and `static-runs-pair-worker.py`.
Tracked source hashes match before and after measurement, and the native
module hash is recorded. A prior amortized result had an invalid compiler
cache counter and is explicitly named
`profile-static-runs-paired-gc-amortized-invalid-cache-counter.json`.
Its cache counts must not be used. An unrelated process consumed one CPU
core during the final run, limiting absolute timing claims. Alternating
pairs support retaining grouping for further end-to-end qualification;
these source timings do not revise the installed-wheel graph report.

The supplied-slot Events regression also passes a stable Python 3.12.13
browser check with the installed ABI3 core and source Citry. The saved result
records one Events call, final DOM text 2, and zero faults; the exercised
fixture targeted caller lexical scope. Evidence is
`qualification-lexical-stable-312.json` in the same research directory. The
artifact does not independently retain the request trace or initial DOM text.
This is a focused check, not qualification of the full migration or every
server action.

The initial serializer separately began selecting the typed document shell
before constructing body HTML. Focused checks caught and fixed a JavaScript
omission regression: omission must retain ordinary body HTML. Further review
covers nested shell boundaries, head behavior, hook edits and asset ordering.
Independent review found body-security inspection, explicit dependency
placeholders, hook asset visibility, and nested shell selection incomplete.
The complete shortcut was deferred. Subsequent milestone review found an
earlier unconditional root-child skip still active in the public path, so
this did not restore full descendant materialization. Its removal or guarded
qualification is tracked in [the milestone log](performance_vue_milestones.md).
No latency saving is attributed to the complete shortcut.
This rejects the incomplete shortcut, not the goal of avoiding discarded HTML.

## V8: Direct relationships during Python rendering

This experiment targets the server work exposed by V7. The private direct mode
renders without constructing or snapshotting an ownership graph. Template fills
retain their lexical source; actual slot calls return structured relationships;
deferred component calls retain their key and placement context. Final selected
output supplies the component occurrences, native Vue slots, browser data, and
Events credentials. The graph-backed mode remains available as a control.

The initial correctness checks include the canonical Django page and all nine
signed Events actions with ownership-graph construction and snapshots forbidden.
Review also found a slot-hook case in which selecting an earlier sibling's
result could leave an unbound forwarded slot. The correction uses the selected
fill's lexical source with the current outlet's physical receiver. Final
assembly must reject unconsumed fill relationships. Repeated calls, fallback
invocation, and forwarding remain separate cases because their lexical and
physical owners can differ.

The paired diagnostic uses the same installed Python 3.12 wheel for graph and
direct modes, alternating their order across seven pairs per case. Warm
producer medians in milliseconds:

| Outputs | Operation | Graph | Direct | Difference of medians |
| ---: | --- | ---: | ---: | ---: |
| 14 | Initial preparation | 11.324 | 11.017 | 0.307 |
| 14 | Select revision | 11.516 | 11.074 | 0.442 |
| 140 | Initial preparation | 72.555 | 71.610 | 0.945 |
| 140 | Select revision | 72.941 | 71.848 | 1.093 |

At 140 outputs, rendering medians fell from 34.123 to 33.116 ms for initial
preparation and from 34.465 to 33.128 ms for the revision. Assembly stayed near
32 ms in both modes. Compilation and its cache lookup stayed near 1.6 ms.
The direct path removes the graph dependency, but this experiment does not
demonstrate a large preparation speedup.

These are instrumented producer intervals, excluding final HTTP response JSON
encoding. Stage medians cannot be summed to reconstruct the total median.
The median within-pair saving at 140 outputs was 0.544 ms for initial preparation
and 1.463 ms for the revision. Initial paired differences ranged from -14.082
to +18.723 ms, so the small initial saving is noisy. The profiler compares
topology, data multisets, and definition sharing; browser semantic checks are
required separately to establish equivalent output.

Raw samples and the profiler are under
`.benchmarks/research/vue-poc/direct-relationships/`. The wheel is
`.benchmarks/wheels/vue-direct/citry-0.5.0-py3-none-any.whl`
(`bdebbebebcf2840d7a861726c9d5597f435119899dc829ed3c957a9992326339`),
installed in build
`0b3ae6fa664cb5097179dd6494c2317ea57a6901c0d838bbab90cebcd23ddf06`.
The native compiler wheel is unchanged. V7's artifacts remain intact.

The same installed wheel passed graph and direct browser checks at both sizes:
8/8 lifecycle checks per case, no faults, and identical canonical board HTML
hashes after each of the nine actions. Focused Python tests passed 55 checks;
the ordinary-render regression sweep passed 467 with one expected failure.

The shared five-stack run passed 200/200 observations with none missing.
Qualification is `20260912T212442Z-cd465ea5`; the updated comparison report is
[report.html](../../.benchmarks/runs/20260912T212631Z-1dfd8b45/report.html).
The schedule remains one block/session, no warmups, two actions per kind, and
one observation per initial-load number. Both loads use fresh browser contexts;
the second warms the server rather than the browser asset cache. Results are
local diagnostics, and 1,400 outputs remain unmeasured for this path.

| Stack, 140 outputs | First interactive | Second interactive | Select | Insert |
| --- | ---: | ---: | ---: | ---: |
| Citry + optimized Alpine | 122.2 ms | 101.1 ms | 162.05 ms | 156.8 ms |
| Citry + direct Vue | 137.2 ms | 117.7 ms | 98.6 ms | 100.4 ms |
| Django + HTMX + Alpine | 59.3 ms | 57.2 ms | 67.3 ms | 66.3 ms |
| Python API + Vue | 30.4 ms | 30.3 ms | 23.8 ms | 21.05 ms |
| Python API + React | 44.4 ms | 42.5 ms | 20.45 ms | 20.6 ms |

The direct Vue select response had 84.086 ms of server preparation and 9.9 ms
after the primary response in the browser. Insert fetches additional definition
code, so its overall time is valid but its phase breakdown remains unclassified.
The separate V7 run measured select at 118.55 ms and insert at 118.45 ms.
The controlled same-wheel test supports only a modest preparation saving;
it does not establish that graph removal caused this larger end-to-end change.

The follow-up `cprofile-direct140.json` identifies work still performed on the
direct path: attribute resolution and typed-part creation during rendering,
then another traversal creating prepared nodes, validating spans and values,
hashing binding identities, and detaching data for the wire format. The profile
records 3,703 attribute-node renders, 6,985 span validations, and 1,967 digest
calls. Its producer time rises to 225 ms under instrumentation, so these call
counts guide investigation; its function times are not the normal render-time
composition. The next structural opportunity is to combine typed capture and
prepared assembly so that values and source metadata are processed fewer times.
That work is queued, not implemented or credited as a saving here.

The second-load browser interval in V7 was 32.7 ms for Citry + Vue and 28.0 ms
for Python API + Vue at 140 outputs. Investigating that gap is queued separately:
the interval includes subsequent requests and does not isolate the bridge or
ordinary-VNode reconciliation cost.

## Comparison plan, 2026-09-12

| ID | Question | Comparison and acceptance evidence | Status |
| --- | --- | --- | --- |
| V1 | Can a retained element safely lose a directive? | Compare rejection, warning-only application, a directive-specific reset followed by removal, and replacement of the affected element. Verify DOM, local component state, focus, selection, input behavior, and intermediate effects. Time successful strategies separately from rejection and incorrect output. | Completed; narrow reset works, general signature changes remain guarded. |
| V2 | What does ordinary reconciliation cost when the compiled definition stays fixed? | Compare native optimized and ordinary VNodes on equivalent nested pages derived from the canonical project at 140 and 1,400 outputs. Separate initial mount, a local component update, and a server data update. Validate full output and state after timing. | Completed; small measured cost at the larger size, ordinary remains the planned default. |
| V3 | Does using internal bailout flags only during a server structural update preserve useful local-update performance? | Compare ordinary VNodes with an optimized initial/local path that uses bailout throughout the structural-update flush. Require correct changed static content and slots, retained instances, and correct later local updates before comparing timing. | Completed; correct for this fixture but slower structural updates and no demonstrated local benefit. Do not adopt. |

The directive comparison uses deliberately small, known templates, including
`v-show` removal and a change to `v-model` input behavior. It does not implement
general directive extraction or a universal neutral value. The rendering
comparison retains nested component and slot boundaries so it can expose work
that a single large render function would miss.

Performance runs use the existing production Vue 3.5.42 runtime and native Vize
compiler. No Node process participates in template compilation. Runs use
balanced mode order and save raw observations, spread, prepared JSON and
definition-source byte sizes, and source hashes. Browser timing runs execute sequentially across experiments to
avoid competing for CPU. Full DOM verification runs after the timed endpoint.
Vue's committed DOM and a later animation-frame checkpoint are reported
separately; neither is presented as measured physical screen presentation.
Generated JavaScript is delivered as scripts with locally bound helper
namespaces. Browser `eval` or `Function` construction is not part of this path.
Cross-mode output hashes must be compared, not just recorded, and semantic
checks must cover the expected canonical data as well as element counts.
The mount interval starts after generated definition factories execute, so
optimized hoisted VNodes can already have been created before its timer starts.
It measures `app.mount()` through `nextTick`, not complete page startup.

Generated probes, exact compiled functions, raw results, and HTML graphs live
under `.benchmarks/research/vue-poc/directive-comparison/` and
`.benchmarks/research/vue-poc/performance-comparison/`. Only compact evidence is
retained; these experiments do not copy environments or build trees.

The V2/V3 fixture is a canonical-derived nested subset, not a replacement for
the complete framework benchmark. It uses the canonical project data and
repeated output, note/comment, attachment/tag, and dependency content, with
explicit server-prepared component calls. It isolates Vue rendering strategy
costs. Definition loading, the private HTTP coordinator's validation, server
event transport, and production source-provenance capture are outside its
browser update interval. The final report must enumerate omitted page behavior
and distinguish server-side preparation measurements from those browser times.

## Decision constraints

Ordinary VNodes remain the selected default for the planned integration while
these comparisons run. Native optimized output is a valid control for a fixed
compiled definition. An incorrect optimized structural replacement cannot win
by doing less work. A conditional bailout candidate must remain enabled for
the whole Vue update flush, including unchanged descendants executing changed
caller slots, and restore its mode before later local updates.

An element replacement may be fast and correct while losing browser-local
state. A two-stage reset may preserve the element while exposing an intermediate
state to hooks or effects. Both are API tradeoffs to report, not defects to hide
behind the timing result. A rejected update is not equivalent to a completed
update and has no place in the successful-update ranking.

No fixed one-millisecond acceptance threshold applies to these comparisons.
First establish correctness and an equivalent measured operation. Then compare
the absolute time, spread across paired observations, scaling, and the benefit
relative to the implementation and API cost. A timing improvement alone does
not qualify reliance on Vue's private flags across unsupported features.

The targeted `v-show` reset can use an intermediate compiled definition with
`v-show="true"`; it need not change the user's reactive `shown` field. Vue still
runs an intermediate update. The experiment must distinguish that behavior
from a reset implemented by mutating application state. Vue's
[`v-show` hooks](https://github.com/vuejs/core/blob/v3.5.42/packages/runtime-dom/src/directives/vShow.ts)
restore a recorded display value, while
[`v-model` setup](https://github.com/vuejs/core/blob/v3.5.42/packages/runtime-dom/src/directives/vModel.ts)
installs listeners whose event choice is captured at creation. These are
different cleanup problems. Later style changes and directive reintroduction
are diagnostic checks; successful removal alone does not qualify every later
revision.

## V1: Directive-removal result

Nine correctness checks passed without unexpected browser faults. Rejection
leaves the current view intact. Warning-only application leaves a hidden
`v-show` element hidden after its new text renders, and leaves the old
`v-model.lazy` change listener active on a reused input.

The intermediate compiled `v-show="true"` definition restores the authored
`inline-flex` display, without changing application `shown` data. It produces
two Vue component updates. The retained input keeps focus and selection, but
its removed `v-model.lazy` listener still runs. A later style update works;
reintroducing `v-show="false"` without replacing the element leaves it visible.
The narrow visibility reset therefore does not establish arbitrary repeated
directive changes.

Replacing just the affected elements restores the correct visibility and
input-listener behavior while retaining the surrounding component and its
local data. The new input loses focus and selection. That is an explicit
element-state tradeoff, even though the surrounding component is retained.

The separate timing fixture contains only repeated `v-show` spans. Both
successful strategies produce the same final visible B content, by updating
retained spans or replacing them. Times cover definition
publication through the final Vue flush, excluding mount, unmount, asset loading,
and paint. Each of six balanced measured samples is the mean of ten fresh
operations; two warm-up rounds are excluded.

| Directive-bearing elements | Two-flush reset | Element replacement |
| ---: | ---: | ---: |
| 140 | 0.075 ms | 0.080 ms |
| 1,400 | 0.640 ms | 0.885 ms |

The 140-element difference is too small to guide the design given timer
resolution and spread. At 1,400 elements the reset saves about 0.245 ms in this
small fixture. This does not justify a generic directive-cleanup framework.
Keep signature rejection in the private integration. A targeted visibility
reset and explicit element replacement remain separate possible policies,
with their tested limitations recorded above.

Exact templates, generated code, traces, samples, and graphs are in the ignored
`directive-comparison/` directory. The graph separates the incorrect warning-only
diagnostic, and does not rank rejection as a successful update. The measured
native compiler hash starts `a9d255a0`; the Vue runtime hash starts `6ebafd50`.

## V2/V3 measurement correction: repeated mounts in one page

The first timing harness repeatedly mounted and unmounted all variants inside
one browser page. Its 1,400-output mount times showed a sawtooth pattern:
successive observations rose from about 1,139 to 1,293 to 1,458 ms, later reached
2,139 ms, then fell to 793 ms before rising again. Balanced variant order did
not make those accumulating costs a useful initial-mount comparison.

The raw run is preserved as `results-main-before-post-local.json` in the ignored
performance directory. It is diagnostic evidence, not the initial-mount
ranking. Accumulating browser state and garbage collection are plausible
causes; the timing pattern alone does not identify the mechanism. The corrected
comparison gives each observation a fresh browser context so earlier mounts
cannot accumulate in that page's JavaScript state.

## V2: Fixed-definition rendering result

The final cohort contains 156 measured phase observations, plus 52 excluded
warm-up observations, without browser faults. Each mode and size has six
measured fresh contexts after two warm-up contexts. The data-update contexts
measure mounting, a nested local input update, and broad prepared-data
publication. Separate structural contexts measure the definition change and
a later local update. Initial samples come only from the data-update contexts,
so the ordinary mode is not counted twice.

All modes use the same native-compiled source templates. The hoisted control
enables static hoisting; handler caching is disabled in every mode. The second
native control also disables hoisting, which isolates the cost of ordinary
VNode creation more closely. Hoisting changes the emitted source for 26 of the
28 template/count combinations, so the hoisting comparison is not comparing
identical compiler output under different labels.

Median milliseconds:

| Outputs | Operation | Native, hoisted | Native, no hoisting | Ordinary VNodes |
| ---: | --- | ---: | ---: | ---: |
| 140 | Mount through Vue flush | 10.80 | 11.05 | 10.70 |
| 140 | Local input update | 0.60 | 0.50 | 0.55 |
| 140 | Broad data update | 4.00 | 4.00 | 4.10 |
| 1,400 | Mount through Vue flush | 104.90 | 106.80 | 107.00 |
| 1,400 | Local input update | 0.65 | 0.60 | 0.60 |
| 1,400 | Broad data update | 26.00 | 26.45 | 27.60 |

At 1,400 outputs, the ordinary mount median is 2.10 ms above the hoisted control
and only 0.20 ms above the native no-hoist control. The mount distributions
overlap. The broad data update costs 1.60 ms more than the hoisted control
(about 6.2%): its six observations span 27.1 to 28.0 ms, compared with 25.8 to
26.1 ms for that control. This is an observed cost for this update and workload,
not a universal Vue penalty. The smaller workload and local input action do
not show a useful architecture-level difference.

Keep ordinary VNodes as the planned default. These results do not justify
adding a public fixed-definition setting now. Such a setting could still help
different workloads, but the measured benefit must be weighed against the
restriction on later server-driven structure. The mount interval excludes
factory execution, including creation of hoisted VNodes, as well as asset
loading and parsing. Its difference is not a whole-page startup advantage.

## V3: Conditional bailout result

The conditional mode mounts with native no-hoist output, enables the internal
`BAIL` flag throughout the structural flush, then restores native behavior
before the next local action. The structural change replaces five retained
Phase render definitions, changing static content and caller-supplied slot
closures while retaining Phase, Output, and ActionForm instances. Output
definitions stay fixed, which exercises unchanged descendants receiving
changed slots. The slot action and later local input both work.

| Outputs | Operation | Ordinary VNodes | Conditional bailout |
| ---: | --- | ---: | ---: |
| 140 | Structural update | 3.85 ms | 4.45 ms |
| 1,400 | Structural update | 27.60 ms | 29.80 ms |
| 1,400 | Local input after structural update | 0.10 ms | 0.10 ms |

The conditional mode is about 2.20 ms slower for the larger structural update
(about 8%). Ordinary observations span 26.9 to 28.4 ms; bailout observations
span 29.0 to 30.5 ms. The later local action is near timer resolution and shows
no measurable benefit. The initial local action and post-structural local action
have different warmup histories; they are not a before/after optimization pair.

Do not add this conditional mode to the private integration. It is correct for
the tested transition, but adds reliance on private flags and flush coordination
without a measured advantage here. Broader local updates and unsupported Vue
features remain unqualified; this experiment does not prove that the mechanism
could never help another workload.

The standalone `performance-comparison/report.html` graphs use only the fresh
cohort. `summary.json` records medians, ranges, nearest-rank p90 values, and
source hashes; `fresh-context-results.json` retains all final phases.
Failed and stopped prequalification attempts are retained separately in
`fresh-context-failed-runs.json`. The parse failure while adding the
fresh-context harness produced no samples.

## V4: Enclosing-element replacement

The user accepted focus loss for correct directive cleanup. The next question
was whether replacing an enclosing element also resets nested component state.
The isolated native-compiled proof passes **7/7 checks with zero faults**.

| Change | Nested child outcome |
| --- | --- |
| Data-only update with stable structure | Same instance, input, and edited local state; new server seed observed |
| New definition with the same wrapper key | Same instance and state; supplied slot updates |
| Replace only a sibling | Same child instance and state |
| Replace enclosing wrapper, A-to-B-to-A | Fresh child each time, new seed, discarded local/input state |

The remounted child has the same Vue type, key, and semantic server ID, and a
multi-root template with a native supplied slot. Its parent and sibling outside
the replaced wrapper retain identity and local state. Both repetitions verify
the exact slot body and wrapper class, directive teardown hooks, removal of the
directive's global listener, child unmount hooks, and an explicitly stopped
detached effect scope. Custom resources still require author-provided cleanup.

Decision: proceed with affected-element replacement and document descendant
state reset. The private HTTP coordinator still rejects incompatible directive
signatures and needs generation-aware remount handling before admitting this
case. The [implementation requirements](vue.md#accepted-element-replacement-and-descendant-state)
explain the stale callback and per-instance data problems found by review.
This result establishes behavior, not a measured speedup or production readiness.

Artifacts are under the ignored
`.benchmarks/research/vue-poc/enclosing-replacement/` directory: `README.md`,
`compiler-output.json`, `compiled.js`, `probe.js`, `run.py`, and `results.json`.
The reviewed result hash begins `14f66cd5`, and the probe hash begins `cb9d8001`.
No new compiler build, dependency environment, or worktree snapshot was created.

## V5: Integrated callback coordinator

The private HTTP coordinator now passes 26 browser checks and 10 Python checks,
with independent review. It preserves retiring instances' data through cleanup,
seeds remounts from authoritative incoming data, verifies the exact next mount
generation, and runs `onServerRender` once on the current instance. Simultaneously
updated descendants and client-edited server fields are covered. Native Vue
`mounted` hooks retain their normal timing. No performance saving is claimed.

The fixture still supplies absolute replacement IDs; reusable compiler metadata
must identify local call locations and bind them per occurrence. The
[implementation log](vue.md#implementation-sequence) records the decisions and
remaining integration work. Reviewed client hash: `c04f1fa3`; browser result:
`a645c8ad`, under the existing ignored stable-instance harness.

## V6: Native directive discovery

Vize's pre-transform AST supplies the required element/directive structure.
The isolated metadata proof passes 18 assertions, including keyed reorder,
multiple directives per element, directive removal, caller-slot attribution,
UTF-8 spans, and rejected dynamic keys or Citry calls under `v-for`.
The result is a generated-key plan; executable key insertion and reusable
definition integration follow. This establishes compiler capability, not speed.
Artifacts: `.benchmarks/research/vue-poc/compiler-metadata/`. Reviewed binary
hash: `67fee9f3`; source: `86712c9d`; runner: `976bb201`.

## V7: Real Citry rendering and Events integration

The integrated adapter uses the actual canonical Citry component templates,
typed Python-prepared values, the in-process Vize compiler, and Vue's production
runtime-only build. It sends updates through the normal signed Events route.
No handwritten browser UI render functions or browser template compiler stand
in for Citry's rendering work.

The development-environment semantic checks passed at 14 and 140 outputs, with
all nine server actions and the shared full-page assertions. A separate lifecycle
check verified retained component identities and local state, ten Board callbacks
for revisions zero through nine, nine cleanups, and no stale reactive effect.
Its compact evidence is in the ignored
`.benchmarks/research/vue-poc/direct-integration/qualification.json`; the matching
runner is `qualification.py` in that directory. This behavior check does not
substitute for the isolated Python 3.12.13 performance run.

Integration required separating a fill's lexical scope from its physical Vue
parent, distinguishing keyed additions from forced remounts, and comparing each
request with the last view the browser actually applied. Review also caught
unsorted replacement metadata, unsafe property meanings for Python-generated
attributes, competing key sources, and a readiness mark that preceded completion
of the full Events action chain. These were corrected before the timed build.

This first adapter has one Board-root Events owner and serialized sends. It
still uses the server ownership graph to prepare native component and slot
relationships, so it does not demonstrate removal of server ownership costs.
The [design](vue.md#general-implementation-checks) records the restricted Vue
helper list and the remaining general-API requirements.

### First isolated comparison

Run `20260912T201950Z-199d4a27` passed all 200 observations after qualification
`20260912T201757Z-9d2262a8`. The offline graph report, raw samples, sizes, and
server timings are under `.benchmarks/runs/20260912T201950Z-199d4a27/`.
The prepared build is
`b8e7296b79df41b23d7d3b27c15b09efeb323cd5fdce7b67352e2e13ac219bda`.
All five adapters use Python 3.12.13. Citry/Alpine uses the optimized workspace
browser assets with its pinned published Python package. Citry + Vue uses the
local experimental Python wheel and optimized native compiler wheel.

The 140-output observations are in milliseconds:

| Stack | First load | Second load | Select item | Insert output |
| --- | ---: | ---: | ---: | ---: |
| Citry/Alpine | 121.9 | 101.0 | 162.1 | 154.4 |
| Citry + Vue | 137.1 | 117.1 | 118.6 | 118.5 |
| Django + HTMX + Alpine | 59.8 | 55.9 | 64.6 | 67.8 |
| Python API + Vue | 30.2 | 29.5 | 22.7 | 20.1 |
| Python API + React | 44.5 | 41.7 | 20.3 | 19.1 |

This is one local block and session, with one observation per initial load and
two observations per action. Action entries are medians of those two samples;
they are not publication estimates or medians across different actions. Both
page loads use fresh browser contexts. The second observes a warmed server,
not an HTTP-cache hit. The 1,400-output case has not been measured in this run.

At 14 outputs, Citry + Vue also improved the second load (36.4 versus 42.1 ms),
selection (23.3 versus 36.5 ms), and insertion (22.8 versus 33.1 ms) compared
with Citry/Alpine. At 140 outputs, selection improved by 26.8% and insertion by
23.3%, but the second load took 16.1 ms longer. The API-driven controls and
Django + HTMX + Alpine remain faster overall at the larger size.

The measured selection breakdown explains the mixed result. The browser
interval after the primary response fell from 136.4 to 12.4 ms; this includes
response processing, the coordinator, Vue's update, and readiness work, rather
than isolating virtual-DOM work. Server output preparation rose from 21.6 to
101.7 ms. On the second initial load, the combined browser/subsequent-request
interval fell from 77.0 to 32.7 ms, but output preparation rose from 21.2 to
82.4 ms. The extra server preparation is now the main bottleneck in this
prototype. The integrated measurements alone do not attribute it to native
compilation, capture conversion, validation, or serialization.

Initial response bodies at 140 outputs fell from 876,779 to 519,180 bytes
(40.8%). Selection response bodies fell from a median 289,847.5 to 174,714 bytes
(39.7%). These sums include all responses in the measured operation and use
identity encoding; they are not TCP/TLS wire sizes.

New definition bundles make some updates use multiple HTTP requests. The report
keeps their end-to-end time and total bytes but displays an unclassified latency
stack when it cannot identify a single exchange. In particular, the insertion
figure above has no measured browser/server phase decomposition. The report was
opened offline and checked at 140 outputs with no JavaScript errors; all ten
charts rendered.

### Attribution of the extra server work

A separate instrumented probe used the frozen build's installed Python 3.12.13
wheels and canonical 140-output prepared workload. Five warm initial preparations had a
median total of 70.3 ms. The independently calculated stage medians were about
34.0 ms for Python prepared rendering, 31.0 ms for converting the typed render
tree into the prepared view, 1.6 ms for constructing compiler inputs and calling
the compiler wrapper, and 3.5 ms for the remaining manifest and bundle work.
The compiler wrapper's nested 1.1 ms includes its Python cache lookup; this
probe does not count actual Rust compiler invocations separately.

The representative update probe showed the same dominant rendering and
conversion work, with more variation between samples. Stage medians are not a
decomposition of the median total from one common observation. These diagnostic
figures are also not substitutes for the official HTTP timings above: they time
the producer in a separate process and exclude final response-envelope encoding.
They establish the next investigation target as prepared rendering and tree
conversion, rather than suggesting that native template compilation explains
the steady server overhead. Probe source and results are retained as
`.benchmarks/research/vue-poc/direct-integration/probe.py` and `results.json`.

## Separate server preparation diagnostic

The subsequent implementation reached typed Citry capture and Events transport
groundwork, then paused because the native build lacked disk space. The exact
tested and unqualified boundaries are recorded in the
[implementation checkpoint](vue.md#implementation-paused-for-disk-space-2026-09-12).
No end-to-end observation or performance saving is added for that work.

The Python fixture's repeated reset, snapshot, and JSON serialization takes
median 0.622 ms at 140 outputs and 5.747 ms at 1,400 outputs. The delivered
experimental state objects contain 73,290 and 739,196 uncompressed JSON bytes.
These are measurements of the fixture model, not Citry's component rendering
or a database-backed request.

Native compilation is measured separately with the existing Vize development
binary, with no release optimization. Summing each required definition's median
uncached compilation time gives about 12.72 ms for the 140-output initial set
and 110.91 ms for the 1,400-output initial set. The five changed Phase definitions
sum to 11.86 and 111.06 ms respectively. These sums describe the initial or changed
definitions for one ordinary target; they do not count every variant and unused
definition in the research bundle. They are sums of per-definition medians,
not observed whole-request medians.

Repeated requests to the persistent compiler still compile the template. Those
observations are not cache hits. Definition reuse could avoid compilation, but
this comparison does not time the private compiler service's cache-hit path.
A release-built compiler and the actual Citry serialization path are required
before these preparation diagnostics can predict end-to-end latency. Browser
mount or update savings must not be treated as eliminating that server work.
