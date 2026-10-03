# Mixed Vue and HTML architecture experiments

This log records the architecture experiments behind Citry's Vue rendering
path and what became of each one. Several prototypes were built against the
exact benchmark `ProjectOutput` row and page to measure an upper bound; the
supported features in
[`vue_optimization_rollout.md`](vue_optimization_rollout.md) now do the same
jobs for any component that meets each feature's conditions, and the public
board meets the report's request-to-layout targets with them. The results
below stay as the measurements that motivated those features. The research
scripts linked below run only against the source they were written for.
Synthetic browser timings do not predict product speedups.

## Current decision map

These are separate comparisons with different controls; their savings cannot
be added.

| Area | Decision | Representative evidence |
|---|---|---|
| Python row-instance erasure | Replaced by the supported `simple = "vue"` mode | Same buffered SSR mode: 1,400-row request→second-rAF 400.2→358.8 ms in two reversed pairs, for the exact benchmark class. |
| Four-region partial SSR and count-only adoption | Replaced by hydration from Rust server render programs | Earlier ready-only Page timing lost to CSR; one corrected layout-inclusive diagnostic favored count-only SSR by about 12–21 ms at 1,400 rows. |
| Whole-article Static HTML with direct controls | Replaced by ordinary Vue hydration of server-written HTML | Against four-region compiled SSR at 1,400 rows, request→second-rAF 345.7→336.1 ms in two reversed pairs; the row retained its Vue instance. |
| Optimized Vue helper boundary | Measured, not selected | Native block/patch hints ran on all 1,400 rows, but paired Page timings overlapped the ordinary helper path; no material browser gain. |
| Islands and on-demand assets | Design/synthetic only, deferred for this Page | All canonical row controls are live at readiness and type assets are already shared; per-row island startup was slower in the limited fixture. |
| Teleport controls | Not timed, implementation deferred | Native/Python compiler gates and the current SSR emitter lack a matching hydration-anchor contract. No speed verdict. |
| Rust rendering migration | Analysis only | [Native rendering decision](rust_rendering.md) identifies where Rust must call back into Python and which features need parity; no implementation or speed claim. |
| Sending simple component bodies as one block of Python HTML | Measured and removed; every component body renders as ordinary Vue output | Slower at every block size (1,400 rows: render and serialize took 203.5 ms with HTML blocks against 111.6 ms ordinary for 97-character blocks, and 2,065.3 against 420.6 ms for 7,754-character blocks), indented templates showed different text spacing, and large pages fell below the hydration threshold. See [the rollout note](vue_optimization_rollout.md#every-component-body-renders-as-ordinary-vue-output). |
| Whitespace at source/preparation | Speed attempt closed; correctness work remains | The current 1,400-row shell whitespace pass cost about 4.96 ms in one instrumented buffered run; safe removal must distinguish template whitespace from text produced by Python. |

## Results and status

The in-place 14-adapter cohort now has a common ready-to-second-rAF report, but
it is not a qualified parity ranking: all 56 first/second-load initial
observations passed, while a Next 1,400-row action and its dependent actions
remain unavailable. See the [research report](../../.benchmarks/research/vue-architecture-experiments/in-place-cohort-composites/20260924T013000Z-final-verified/report.html)
for per-row run provenance and memory data.

- **Completed:** Analyzer probes expose selected-branch and slot-classifier
  gaps. A mocked nested-island promotion/demotion proof passed; production
  transport and callbacks remain untested.
- **Measured, synthetic browser modes at 1,400 rows:** whole Vue 19.2 ms,
  static VNode 19.2 ms, per-row hydration 26.0 ms, and Teleport 14.5 ms
  (three samples). These do not establish product gains.
- **Rejected prototype:** Handwritten Markup substitution triggers whole-leaf
  fallback.
- **Direct SSR prototype:** The exact-canonical four-region path was a
  research prototype, now replaced by hydration from Rust server render
  programs. Earlier full-HTML and count-only comparisons lost
  actual-Page `citry:ready` time against CSR. A separate, unreplicated
  layout-inclusive diagnostic favored count-only SSR by about 12–21 ms through
  the second animation-frame callback at 1,400 rows; this is not a display-paint
  or general TTI claim. [Streaming research](https://github.com/citry-dev/citry/issues/19#issuecomment-5804122073)
  is a deferred feature and is excluded from framework rankings.
- **Retained source optimization:** wrapper-aware spread projection and the
  evaluation-only plan preserve exact output and reduce full render + serialize
  time in bounded source-mode runs. The second-load browser result is mixed, so
  no repeatable TTI gain is claimed.
- **Retained early return:** repeated eligible leaf occurrences reuse their
  cached definition and avoid the remaining per-occurrence assembly helpers;
  full render + serialize improved in both 20-render windows, with exact output
  parity. Browser measurements remain experimental and mixed.
- **Generated evaluator:** a generated simple-JSON leaf evaluator with
  read-set validation improved the 1,400-row server path in the archived
  source comparison. It now runs automatically for any template whose read
  set holds only plain JSON values.
- **Instance-erasure proof:** an exact-canonical `ProjectOutput` path removed
  per-row Python component/context/frame/render construction while
  preserving HTML and manifest. Three no-precollection server pairs and two
  reversed real-Page browser pairs favored it at 1,400 rows. The supported
  `simple = "vue"` mode does the same for any admitted component.
- **Whole-article controls:** exact-canonical Static HTML with direct local
  bindings passed a real Page action proof and a small paired browser
  comparison; its 1,400-row layout-inclusive median improved by 9.6 ms.
  Ordinary Vue hydration of server-written HTML now gives the board its
  browser-side gain without hand-written bindings.
- **Common-endpoint framework cohort:** the [in-place research report](../../.benchmarks/research/vue-architecture-experiments/in-place-cohort-composites/20260924T013000Z-final-verified/report.html)
  includes all 14 adapters at 140 and 1,400 rows, with one initial observation
  per app, size, and first/second page load. At 1,400 rows on the
  second load, Citry's main-server, browser-after-response, and extra layout
  segments were 190.447 ms, 159.1 ms, and 12.6 ms; Django+HTMX+Alpine measured
  50.445 ms, 261.1 ms, and 11.3 ms; Nuxt measured 19.792 ms, 156.4 ms, and
  14.6 ms. Citry's browser-after-response segment is near Nuxt and below
  Django, while its
  Python server work keeps total parity unmet. Next had an intermittent
  1,400-row Server Action completion error; separate memory observations also
  include that Next error and a Reflex WebSocket-accounting mismatch. That
  Citry arm used the exact-`ProjectOutput` research prototypes (partial SSR
  with static row HTML and direct controls); streaming is off. The current
  public board results are in
  [`vue_optimization_rollout.md`](vue_optimization_rollout.md#current-performance-checkpoint). This n=1 cohort is a diagnostic, not
  a statistically established framework ranking.
- **Cross-framework equivalence repair:** the audit found that Next and Nuxt
  lacked the shared `board.css`, while six row adapters omitted visible section
  headings/empty states or placed attachments inside the select form; those
  earlier timings were not visually/workload equivalent. The [replacement
  report](../../.benchmarks/research/vue-architecture-experiments/equivalence-rerun-20260924/report/20260924T113519Z-all-framework-equivalence-baf9b0b6/report.html)
  joins current cells for the seven repaired apps with the prior seven
  unchanged cells. The unchanged seven were source/resource/geometry audited,
  not rerun under the new post-endpoint guard. Source runs and run IDs are
  mapped per cell; the known Reflex 1,400-row memory WebSocket gap remains
  explicit.
- **Deferred:** the real-Page native Vue-helper trial was flat. Teleport was not
  timed: the present compiler and SSR producer lack a matching anchor contract.
  The current whitespace cleanup costs about 5 ms at 1,400 rows, but safe
  source-level removal needs broader text-provenance work. Fine-grained
  islands still need broader admission before product use. The
  [native renderer design](rust_rendering.md) is analysis only. Incremental
  server updates are deferred to
  [issue #144](https://github.com/citry-dev/citry/issues/144).
- **Vue asset fetch preloads:** eligible initial and revision script requests
  now start together while script execution remains serial; revision CSS is
  fetched early but applied after scripts succeed. Reversed-response, fail-fast,
  cancellation, and CSP/nonce browser checks passed. The n=1 final-Page sample
  showed no material readiness gain at 1,400 rows (330.6→330.4 ms to framework
  ready; 342.6→342.3 ms through the second rAF). The first-to-last request-start
  span across nine definition/Options GETs narrowed from 11.4 to 4.4 ms, with no
  duplicate GETs. See the [bounded result and source
  hashes](../../.benchmarks/research/vue-architecture-experiments/script-preload-experiment/initial-page-preload-timing.json)
  and [invalid runtime-source attempt note](../../.benchmarks/research/vue-architecture-experiments/script-preload-experiment/initial-page-preload-timing-invalid-runtime-source.json).
- **Server-emitted initial HTML hints:** for mounted prepared Vue pages using
  document dependencies, the server validates the prepared definition and
  asset manifest before placing eligible script-only hints after authored head
  metadata. The mounted core runtime and nine unique initial script resources
  each produced exactly one GET, and script execution order and fail-fast
  behavior remained intact. Across three measured samples per arm and size,
  median requestStart→ready was 70.0→63.4 ms at 140 rows and 352.6→332.7 ms at
  1,400; browser-after-document medians were 46.7→39.6 and 158.1→140.6 ms.
  At 140 rows, preparation rose about 0.7 ms and layout-inclusive results were
  noisy; at 1,400 rows, the layout-inclusive median improved 365.0→345.2 ms.
  These are small app-specific samples, not a general performance claim. See
  the [first pair](../../.benchmarks/research/vue-architecture-experiments/script-preload-experiment/preload-hints-ab.json)
  and [reversed pairs](../../.benchmarks/research/vue-architecture-experiments/script-preload-experiment/preload-hints-ab-reverse.json).
  The [Citry-only full-action report refresh](../../.benchmarks/research/vue-architecture-experiments/equivalence-rerun-20260924/report/20260924T145721Z-citry-only-preload-copy-9f6f0edf/report.html)
  updates only Citry's latency, size, server-timing, and memory rows; its 24-chart browser sanity passed with graph names and order matching the base.
- **Avoid a redundant initial server-data copy:** `configure()` now leaves `serverData`
  out of the whole-item clone and detaches it separately, preserving public
  alias and mutation isolation. The two-arm page comparison was flat at both
  sizes (median requestStart→ready delta +0.15 ms at 140 rows and −0.15 ms at
  1,400), so this is a bounded copy reduction with no page-level speed claim.
  See the [copy-only comparison and hashes](../../.benchmarks/research/vue-architecture-experiments/script-preload-experiment/configure-copy-ab.json).

## Prior art

- [`serialization.py`](../../packages/py/citry/citry/_vue/serialization.py) derives selected-root JS data, Events, and browser bindings; [`direct_capture.py`](../../packages/py/citry/citry/_vue/direct_capture.py) assembles occurrences.
- [`leaf_program.py`](../../packages/py/citry/citry/_vue/leaf_program.py) compiles all branches into one fragment, then evaluates only the selected branch; its browser requirements can describe inactive source.
- [`component_render.py`](../../packages/py/citry/citry/component_render.py) computes `js_data()` on each render. Analyzer tests cover materialization, selected bindings, and inactive runtime needs ([security](../../packages/py/citry/tests/test_vue_binding_security.py#L479), [migration](../../packages/py/citry/tests/test_vue_migration_coverage.py#L1019), [poll bindings](../../packages/py/citry/tests/test_vue_runtime_poll_bindings.py#L213)).
- [`vue.md`](vue.md#L490) retains final validation; [`performance_vue_research.md`](performance_vue_research.md#L150) separates Python render, assembly, and DOM work. Earlier [generated-body experiment](performance.md#L576) was slower cold and flat warm.

## Analyzer probe

`render_prepared_direct()` plus `analyze_vue_serialization()` ran without
assembly or native compilation.

| Case | Result |
|---|---|
| Inactive `c-if` branch has `@c-click`; `c-else` selected | Runtime fragment reports Events; active policy is empty. |
| Selected caller fill has `v-show` and `@c-click` | Active policy reports Events but omits selected Vue binding. |
| Selected receiver returns nonempty / empty `js_data()` | Nonempty adds `js_data`; empty adds no requirement. |

Neither runtime requirements nor active policy alone classifies an island.
Use selected output, executed branch/slot data, and reachable lexical
requirements; model Events transport separately from Vue bindings/state.

## Decision ledger

| Proposal | Status / evidence / next check |
|---|---|
| Component-scoped HTML/Vue boundaries | Correctness proof passed; synthetic browser prototype measured. `ProjectTabs` provides child state; class-local state may mean ~1,400 roots. See [`app.py`](../../benchmarks/web/apps/citry_vue/app.py#L94) and [`project_output.html`](../../benchmarks/web/apps/citry_vue/project_output.html#L17). |
| Teleport controls into HTML hosts | Synthetic variant measured. Real-Page trial not timed: the native and Python compiler allowlists reject `Teleport`, and the current exact-source SSR emitter writes literal tags rather than hydration source/target anchors. Supporting it needs a new authenticated compiler/producer contract; no performance verdict. See [feasibility source review](../../.benchmarks/research/vue-architecture-experiments/islands_teleport_next.md#teleport-feasibility-outcome). |
| Static detail subtree in Vue | Synthetic `createStaticVNode` measured, inconclusive: at 1,400 rows both static and dynamic were 19.2 ms; static fixture HTML was 781,250 bytes. |
| G1: direct escaped leaf HTML | Rejected and removed from the leaf producer/evaluator: the prototype was 10.9% slower at 140 and 23.8% slower at 1,400. |
| G3: certified leaf-data adoption | Rejected and removed: exact output parity, but the prototype was 0.7% slower at 140 and 0.9% slower at 1,400. Public occurrence detachment and validated cache replay remain on their established paths. |
| Scalar leaf attribute binding | Rejected: 140-row render + serialize was flat (27.346 → 27.342 ms); 1,400 rows improved 1.4% (165.284 → 162.930 ms), too small and uncertain to justify separate runtime/compiler support. The [source patch](../../.benchmarks/research/vue-architecture-experiments/scalar_leaf_binding_prototype.patch) and [paired timing evidence](../../.benchmarks/research/vue-architecture-experiments/scalar-source-ab.json) are archived. |
| Shared immutable schema + positional values | Rejected after strict-ingress producer + assembly: exact HTML parity, but 140 rows changed 15.318 → 15.436 ms and 1,400 changed 138.477 → 141.346 ms; producer cost outweighed assembly savings. Gzip grew slightly (50,016 → 50,275 bytes). Native compilation and browser behavior were not measured. See [results](../../.benchmarks/research/vue-architecture-experiments/positional-producer-results.md) and [source patch](../../.benchmarks/research/vue-architecture-experiments/positional_leaf_producer_prototype.patch). |
| Wrapper-aware direct spread projection + evaluation plan | Retained behind capability checks: exact output parity and lower final-source render + serialize times; the small source-mode TTI signal is mixed and does not establish a repeatable browser gain. |
| Early cached-leaf return | Retained behind narrow identity/marker/decoration/binding guards: 141/1,401 eligible hits per canonical render and exact response/manifest/compiler parity. In 20-render normal-GC windows, mean full render + serialize changed 20.388 → 19.274 ms (140) and 171.889 → 160.907 ms (1,400); multiple gen2 collections occurred in both arms. See [long windows](../../.benchmarks/research/vue-architecture-experiments/early-cached-leaf-long-window.json), [paired captures](../../.benchmarks/research/vue-architecture-experiments/early-cached-leaf-ab.json), and [source-mode TTI evidence](../../.benchmarks/research/vue-architecture-experiments/early-leaf-source-tti-repeat-reversed.json). |
| Assembly-owned `server_data` adoption | Rejected as a standalone speedup: outputs matched exactly; three-process warm means changed 21.00 → 21.15 ms (140) and 164.62 → 159.27 ms (1,400), but 20-render windows were mixed (20.192 → 19.571 and 165.630 → 165.200 ms). Public constructor detachment was unchanged; [patch](../../.benchmarks/research/vue-architecture-experiments/server-data-adoption.patch), [short A/B](../../.benchmarks/research/vue-architecture-experiments/server-data-adoption-ab.json), and [long-window/GC evidence](../../.benchmarks/research/vue-architecture-experiments/server-data-adoption-window.json) are archived. |
| Closed-engine orchestration cut | Rejected after a research-only exact-class proof: skipped three config allocations, empty input dispatch, disabled-cache lookup, and base JS/CSS/on-render calls while preserving the normal data-hook order. Exact HTML, manifest, compiler, and occurrence parity; three-sample warm medians were 18.448 → 18.420 ms (140, flat) and 161.159 → 162.339 ms (1,400, +0.7%). This bounded class result does not disprove broader orchestration changes; see [capture and qualification](../../.benchmarks/research/vue-architecture-experiments/genuine-instance-orchestration-ab.json) and [source patch](../../.benchmarks/research/vue-architecture-experiments/genuine-instance-orchestration.patch). |
| No-parser SSR upper bound | Research-only canonical-source stub, with original parser validation and exact SSR byte parity. Warm medians (CSR / SSR / no-parser SSR) were 18.73 / 49.45 / 27.57 ms at 140 and 158.91 / 462.74 / 251.74 ms at 1,400; the two SSR parsers accounted for about 21.6 / 211 ms. Instrumented 1,400-row no-parser residual was 88.2 ms over CSR, including about 31 ms across 1,404 `static_leaf_parts` calls, 28–29 ms whitespace stripping, and 8.4 ms source-attribute stripping. This diagnostic does not measure browser behavior. See [paired captures](../../.benchmarks/research/vue-architecture-experiments/ssr-no-parser-suite-140.json), [1,400-row capture](../../.benchmarks/research/vue-architecture-experiments/ssr-no-parser-suite-1400.json), and [phase attribution](../../.benchmarks/research/vue-architecture-experiments/ssr-no-parser-phases-1400.json). |
| Current fused SSR whitespace residual | One instrumented cold-process buffered control per size, normal GC/default IDs and clock, no instance-erasure scope. At 140/1,400 rows, shell whitespace cleanup was 0.594/4.957 ms and source-attribute cleanup 0.218/1.891 ms; whole fusion was 1.261/10.416 ms. Literal preparation was 0.158/0.145 ms, and fallback full-body cleanup had zero hits. The whole-request totals (67.742/264.360 ms) include source read, root-fact scan, and admission assignment, so they are not comparable to earlier warm or erased timings. No whitespace candidate is warranted from this bounded attribution; the older no-parser full-body figures are not current savings forecasts. This does not establish general SSR whitespace correctness. See [method/provenance](../../.benchmarks/research/vue-architecture-experiments/whitespace_current_attribution_provenance.md) and [raw attribution](../../.benchmarks/research/vue-architecture-experiments/whitespace_current_attribution.json). |
| Partial SSR hydration browser proof | Isolated research probe used a private runtime response rewrite. JS-only `v-text`, bound `title`/`id`, and `v-show` initialized while reusing all 13 DOM nodes; class/style and `FULL_PROPS` initialized only with hydration-time prop-key scanning. Mixed `title` with class/style, reserved `key`/`ref`/`onVnode*` filtering, the dynamic-element wrapper, and a production lifecycle gate remained untested in this probe. The supported hydration path is described in [`vue_board_hydration_plan.md`](vue_board_hydration_plan.md); see [probe results](../../.benchmarks/research/vue-architecture-experiments/partial-ssr-hydration-proof-final.json). |
| Four-region inline Static SSR browser opportunity | Fixture-only three-arm proof at 140/1,400 rows. At 1,400, inline Static mount-ready was 69.8 ms versus 70.4 ms for full SSR, but fixture-ready was 94.0 versus 93.7 ms; the pre-mount scan offset the mount difference. Its 83.1 ms fixture-ready gap versus CSR (177.1 ms) is not comparable to the later real-Page post-document phase. Combined fixture gzip was 141,607 bytes versus 160,936 for full SSR and 137,402 for CSR. Initial and one-row local-state/form checks passed. No Citry TTI/server-time or structural `v-if` remount claim; see [summary, phases, and limitations](../../.benchmarks/research/vue-architecture-experiments/opaque-ssr-four-region-browser-summary.md) and the [raw 140](../../.benchmarks/research/vue-architecture-experiments/opaque-ssr-four-region-browser-140.json)/[1,400](../../.benchmarks/research/vue-architecture-experiments/opaque-ssr-four-region-browser-1400.json) captures. |
| Four-region full-HTML sidecars on the real Page path | Not retained as the default transport. After the separate allow/off scan gate, source-mode `Page.render() + serialize()` medians (CSR / full SSR / direct candidate) were 17.86 / 47.32 / 30.31 ms at 140 rows and 150.77 / 440.75 / 245.78 ms at 1,400. In paired/reversed n=2 actual-Page runs with hydration diagnostics off, requestStart→ready was 95.65 / 117.15 then 61.40 / 81.50 ms (CSR / candidate) at 140 rows, and 394.10 / 464.05 then 362.70 / 450.20 ms at 1,400. The candidate loses ~20 ms at 140 and 70–88 ms at 1,400 versus CSR, despite saving ~32 ms after document completion at 1,400. Its 1,400-row response is 3.79 MB raw / 150 KB computed gzip versus CSR 1.28 MB / 109 KB; the response was not HTTP-compressed. A later same-source serializer A/B preserved output bytes and reduced candidate server time 244.18 → 227.52 ms at 1,400, while CSR was 154.87 ms; no new browser timing was taken for that serializer-only refinement. One aligned Chrome trace showed 10.4 → 28.7 ms of HTML-parse spans and 0.3 → 59.9 ms of style/layout spans in the responseEnd→startPrepared interval (CSR → direct); these are overlapping event spans, not additive CPU totals, and the single traced ready-after-document sample is not a TTI result. Full SSR remains a slower server reference; no full-SSR browser TTI was run. Initial real-Page hydration/local state, an unchanged-HTML probe, and Insert passed; Insert mounted a new row and did not test replacing an existing region. Canonical CSS is global; per-component `data-cid-*` CSS/JS consumers remain outside this proof. Count-only initial adoption is a separate follow-on. See [post-gate Page server modes](../../.benchmarks/research/vue-architecture-experiments/four_region_page_server_modes_policy_gate-140-1400.json), [real-Page TTI](../../.benchmarks/research/vue-architecture-experiments/four_region_page_source_tti_csr_vs_direct-140-1400.json), [aligned phase trace](../../.benchmarks/research/vue-architecture-experiments/four_region_page_startup_chrome_trace-1400.json), [hydration proof](../../.benchmarks/research/vue-architecture-experiments/four_region_direct_static_browser_smoke.json), [unchanged probe](../../.benchmarks/research/vue-architecture-experiments/four_region_direct_static_action_browser_smoke.json), and [new-row Insert](../../.benchmarks/research/vue-architecture-experiments/four_region_direct_static_changed_site_action_browser_smoke.json). |
| Count-only initial adoption (same four-region SSR attempt) | Count-only changes four initial `{html}` sidecars to empty records but retains the same server HTML and hydration mechanism. Paired/reversed n=2 at 1,400: CSR / fused-full / count-only requestStart→ready medians were 379.75 / 439.10 / 437.85 ms on first loads and 348.10 / 390.35 / 400.60 ms on second loads. Count-only did not improve readiness over full records and remained slower than CSR. It cut raw response size 3,721,279 → 2,482,174 bytes and computed gzip 150,218 → 127,925 bytes; responses were uncompressed. A separate single warm diagnostic scheduled rAF from the ready callback: on first/second loads, ready→following-rAF callback was 75.1/72.3 ms for CSR and 12.1/12.1 ms for count-only; requestStart→that callback was 451.2/418.4 and 438.8/397.1 ms. The first-rAF forced geometry read took 61.0/58.4 ms for CSR and 2.2/2.0 ms for count-only, while semantic reads afterward took about 7–8 ms in both. The first callback's frame timestamp preceded entry by ~139 ms for CSR and ~34 ms for count-only, so these intervals are diagnostic and do not prove display/compositor paint or provide additive CPU time. The initial-only experiment does not cover Events updates/remounts and is not retained/default. See [three-arm TTI](../../.benchmarks/research/vue-architecture-experiments/four_region_page_source_tti_csr_fused_countonly-1400.json) and [post-frame diagnostic](../../.benchmarks/research/vue-architecture-experiments/four_region_page_postframe_csr_countonly-1400.json). |
| Staged-prefix streaming (attempt 20; region-validation reuse is a refinement) | With the same count-only 1,400-row Page output, the one-warm buffered/streamed pair returned equal-length 2,482,204-byte uncompressed documents. On the recorded second load, requestStart→ready changed 392.2→372.8 ms and requestStart→second-rAF changed 404.3→385.3 ms; ready→second-rAF was 12.1→12.5 ms. Server requestStart→finish changed 222.1→230.0 ms; first-body→finish changed −1.38→52.0 ms, which is elapsed post-prefix preparation rather than CPU time. The server validated each direct region before publishing the prefix, then reused its exact immutable result during the same manifest assembly. One-row instrumentation recorded 4 boundary scans with a matching certificate, 8 with an empty/replaced certificate, and 4 after pre-stage rejection; bytes and callbacks matched. This is a single recorded load per arm, not a CSR comparison or qualified TTI; initial-only behavior, update/remount behavior, and broad extension admission were not built beyond this prototype, and streaming is tracked in [issue #19](https://github.com/citry-dev/citry/issues/19). See [buffered/streamed result](../../.benchmarks/research/vue-architecture-experiments/four_region_stream_buffered_vs_streamed_region_reuse-1400.json), [one-row scan and byte checks](../../.benchmarks/research/vue-architecture-experiments/four_region_stream_asgi_one_row.json), and [CSS/heartbeat diagnostic](../../.benchmarks/research/vue-architecture-experiments/four_region_stream_css_heartbeat_diagnostic-1400.json). |
| `allow`/`off` opaque-record validation gate | Retained separately from the rejected sidecar transport: policy mode controls restrictive JavaScript/CSP validation scans for opaque HTML. Focused policy regression passed: an active handler is accepted silently under allow/off, warn/off warns, forbid/off rejects, and allow/strict rejects; see the post-gate Page comparison above. |
| Marko-inspired whole-article Static/direct bindings | The same-instance fixture passed local-state, replacement, form, and cleanup checks. A later exact-canonical real Page proof passed initial hydration, unrelated parent rerender, and full-HTML Select fallback. In two reversed pairs at 1,400 rows, median request→ready changed 334.3→325.4 ms and request→second-rAF 345.7→336.1 ms; the 140-row frame result was noisier. The prototype admitted only the benchmark row and was not resumability or a general product option; ordinary Vue hydration of server-written HTML replaced it. See [real-Page evidence](../../.benchmarks/research/vue-architecture-experiments/whole-article-static-direct-bindings/whole_article_static_page_postframe_140-1400.json) and [scope](../../.benchmarks/research/vue-architecture-experiments/whole-article-static-direct-bindings/real_page_results.md); the older [fixture comparison](../../.benchmarks/research/vue-architecture-experiments/whole-article-static-direct-bindings/timing-1400.json) is not directly comparable. |
| Hybrid generic outer / keyed optimized subtree | 10/10 correctness checks passed without timing. Changed compiled slot sources participate in definition identity; the key change retains outer state and intentionally resets descendants. Coordinator remount accounting and product integration remain open; see [results](../../.benchmarks/research/vue-architecture-experiments/hybrid-vnode-boundary/results.json). |
| Native Vue compiler helpers for the canonical row | A private runtime switch restored compiled `openBlock`, block VNodes, patch flags, and dynamic-child hints while retaining the four inline Static regions and the same SSR producer. One-row hydration, local state, unrelated parent rerender, and changed-header full-HTML fallback passed. In two reversed real-Page pairs at 1,400 rows, request→second-rAF was [345.5, 349.5] ms ordinary versus [347.6, 346.1] ms native; 140 rows were likewise flat. The switch genuinely hit 1,400 rows (root `dynamicChildren=2`, patch flag 16), but produced no material browser benefit. It is archived, not selected for the final cohort. Equal response lengths are not byte parity because IDs vary. See [one-row proof](../../.benchmarks/research/vue-architecture-experiments/optimized-native-helpers/native_helpers_one_row_result.json) and [paired result](../../.benchmarks/research/vue-architecture-experiments/optimized-native-helpers/native_helpers_page_postframe_140-1400.json). |
| Static element caching in compiled Vue definitions | Rejected and removed; measured after this batch, not counted in it. A research option compiled fully static elements into each instance's render cache, the `_cache[n] \|\| (_cache[n] = ...)` shape with Vue's CACHED patch flag (the `-1` marker that tells Vue to skip the element on re-render), and changed the Rust code that reads compiled render functions for hydration and server rendering, and the browser runtime, to accept it. The pinned Vize 0.420.0 compiler does not write that shape itself: with hoisting on it moves static elements into module-level `_hoisted_N` constants, so a Citry pass had to rewrite them, and Vize has no pass that turns large static subtrees into one HTML string. On the board it was flat to about 1% slower: ready at 1,400 rows on first load was 335.4 ms by default against 339.7 ms with caching, and warm server render at 1,400 rows was 107.4 against 107.6 ms. First paint at 1,400 rows on first load was 296 against 280 ms, within noise (cached samples ranged from 276 to 308 ms), and did not offset the slower ready time. The only gain came on a synthetic page whose static sections sat under `v-show` wrappers (Vize hoists static elements, so the Citry pass could cache them, only below an element with a directive): 50 counter clicks, each re-rendering a component with 300 static sections, took 16.7 ms instead of 26.75 ms. It also had an open correctness bug: a shell (an element whose contents the server leaves for the browser to build) inside a cached element was never filled in; this was found while reviewing the prototype, and no reproduction is saved in the research folder. Compiled definitions keep static hoisting and render caches off. See the [research files](../../.benchmarks/research/static-hoisting/). |
| Opaque Static VNode anchor fix | Retained correctness fix: same-HTML revisions reuse a per-instance VNode, while changed HTML replaces it safely. Focused E2E passes; no performance claim and not counted as an architecture attempt. See [`client.js`](../../packages/py/citry/citry/_vue/client.js), [test](../../packages/py/citry/tests/e2e/test_vue_opaque_html_e2e.py#L15), and [results](../../.benchmarks/research/vue-architecture-experiments/opaque-static-lifecycle/results-postfix.json). |
| Fused prepared-leaf occurrence ticket | Rejected as a standalone optimization. Against the exact pre-edit source, output, manifest, occurrence IDs, call runs, and compiler definitions matched; 1,400-row mean render + serialize improved 162.660 → 156.492 ms (6.17 ms, 3.8%), while 140-row blocks were noisy. The new ticket type crossed render, capture, serialization, typed-document, cache/plain-serialization, hook, and ownership contracts. Seven source files were restored; see the [full disposition](../../.benchmarks/research/vue-architecture-experiments/fused-leaf-ticket-disposition.json), [pre-edit comparison](../../.benchmarks/research/vue-architecture-experiments/fused-leaf-ticket-preedit-vs-direct-registration.json), and [archived prototype patch](../../.benchmarks/research/vue-architecture-experiments/fused-leaf-ticket-prototype.patch). |
| Generated simple-JSON leaf evaluator with read-set validation | Adopted: the read-set evaluator now runs automatically for eligible templates. Exact output, manifest, occurrence IDs, call runs, compiler definitions, and callback traces matched. Against the exact archived source, the main true-source result was 162.095 → 150.471 ms at 1,400 rows (-7.2%) for the earlier whole-tree validator; the later read-set candidate was 155.572 → 150.996 ms (-2.9%). These separate comparisons are not additive. The read-set candidate also showed no gain at 140 rows (18.784 → 19.022 ms); four fallback/effect tests pass. See [whole-tree source evidence](../../.benchmarks/research/vue-architecture-experiments/simple-json-leaf-exact-source.json), [read-set evidence](../../.benchmarks/research/vue-architecture-experiments/simple-json-leaf-readset-exact-source.json), [pre-edit source](../../.benchmarks/research/vue-architecture-experiments/simple-json-readset-pre-edit/leaf_program.py), and [candidate source](../../.benchmarks/research/vue-architecture-experiments/simple-json-readset-candidate/leaf_program.py). |
| Tetra local row and phase controls | Research-only two-template patch replaced native `<details>` with local Alpine state, buttons, `aria-expanded`, and `x-show`. Browser correctness confirmed row/phase toggles and independent `open` scopes with no requests. One source-mode first/second pair per size is mixed at 140 and slower at 1,400; response HTML grew by 12,486 / 120,821 bytes. Templates were restored exactly. See [baseline](../../.benchmarks/research/vue-architecture-experiments/tetra-reactive-controls-baseline-140.json), [candidate 140](../../.benchmarks/research/vue-architecture-experiments/tetra-reactive-controls-candidate-140.json), [baseline 1,400](../../.benchmarks/research/vue-architecture-experiments/tetra-reactive-controls-baseline-1400.json), [candidate 1,400](../../.benchmarks/research/vue-architecture-experiments/tetra-reactive-controls-candidate-1400.json), and the [archived patch](../../.benchmarks/research/vue-architecture-experiments/tetra-reactive-controls.patch). |
| Disable expression sandbox | Diagnostic only, not retained: canonical output and manifest matched exactly. Warm medians were flat at 140 rows (19.369 → 19.381 ms) and 1.9% slower off at 1,400 (167.145 → 170.284 ms); first in-process renders were 49.366 → 47.976 ms and 208.231 → 198.340 ms. Disabling the sandbox changes the security contract. See [captures](../../.benchmarks/research/vue-architecture-experiments/sandbox_config_ab.json). |
| GC pause attribution | With normal GC policy, pauses explained the 140-row outlier (8.8 ms of a 27.0 ms render); three 1,400-row renders spent 11–17% in about 200 collections each. No object cause is inferred. See [captures](../../.benchmarks/research/vue-architecture-experiments/gc-pause-140.json) and [1,400-row captures](../../.benchmarks/research/vue-architecture-experiments/gc-pause-1400.json). |
| Research wire leaf → JSON writer | Rejected as an isolated speedup: payload and trace parity held at both sizes, but 1,400 rows changed 58.45 → 60.39 ms (+3.3%) under a candidate-favorable baseline. This does not measure direct final-occurrence emission; see [proof results](../../.benchmarks/research/vue-architecture-experiments/direct-json-leaf-proof-results.json). |
| Direct final-occurrence emission | Deferred outside this batch. The older render + serialize split was 12.17 + 6.52 ms (140) and 119.08 + 48.27 ms (1,400), but those figures do not predict a direct-emitter gain. The measured four-region producer and instance-erasure proof answer narrower Page questions; a general final-occurrence writer needs a separate contract. |
| Handwritten dependency markup | Rejected on current prepared path; see A/B below. |
| Python component instance erasure | Proof for the exact canonical `ProjectOutput`, since replaced by the supported `simple = "vue"` mode: it creates a terminal owned record without a Python component, child `CitryContext`, `RenderFrame`, `CitryRender`, or `_FinalizeTask`. Static `template_data` ran once per row; deterministic 1,400-row HTML and manifest matched exactly, including render IDs, `callRuns`, four explicit `#c-key` placements, definitions, and class JS assets. In the buffered count-only/fused server A/B with normal IDs/clock and GC enabled, three alternating pairs measured 24.298 → 19.610 ms (140, −19.3%) and 220.586 → 156.976 ms (1,400, −28.8%); each arm produced the expected 0/size erased-record hits and size fused placeholders, with paired HTML lengths equal. The archived initial seven-sample run explicitly called `gc.collect()` before timed executions and is labeled controlled-precollection, not the primary result. Two reversed real-Page browser pairs at each size passed the common ready, first-rAF layout read, second-rAF, semantics, local-control, and fault checks; both arms included the real asset and Events coordinator path. Median requestStart→ready was 78.6 → 72.7 ms at 140 and 388.1 → 346.8 ms at 1,400; requestStart→second-rAF was 90.5 → 75.7 and 400.2 → 358.8 ms. Candidate response bodies were 22 bytes larger at 140 and 21 bytes larger at 1,400; deterministic parity was byte-exact. These are small, app-specific research samples, not a general speed claim. The adopted API is `simple = "vue"`: `simple = False` keeps ordinary component behavior, `simple = True` keeps caller-owned output without Vue identity, and `simple = "vue"` omits the Python instance while retaining Vue identity, state, and assets. See [three-pair server evidence](../../.benchmarks/research/vue-architecture-experiments/instance_erasure_page_ab_verification_3pair.json), [fixed-ID/clock parity](../../.benchmarks/research/vue-architecture-experiments/instance_erasure_fixed_parity_1400.json), [browser evidence](../../.benchmarks/research/vue-architecture-experiments/four_region_instance_erasure_page_postframe_140-1400.json), [controlled-precollection seven-sample run](../../.benchmarks/research/vue-architecture-experiments/instance_erasure_page_ab.json), [precollection provenance](../../.benchmarks/research/vue-architecture-experiments/instance_erasure_page_ab_provenance.md), [corrected verification runner](../../.benchmarks/research/vue-architecture-experiments/instance_erasure_page_ab_verification.py), and [server scope](../../.benchmarks/research/vue-architecture-experiments/four_region_page_tti_server.py). |
| Future native renderer ownership | Analysis only: [native rendering decision](rust_rendering.md) separates a retained arena/scheduler and coarse PyO3 effects from the archived Rust body walk. It maps planned GitHub features to parity obligations, parallel work, or independent APIs. No implementation or speed claim. |
| Stable Vue definitions / structural replacement | Deferred from the final cohort. The bounded keyed-subtree fixture passed correctness, but real-Page native helper hints were flat; general changed-slot/remount admission and coordinator accounting remain future API work. |
| Fine-grained islands / on-demand assets | Deferred for this canonical Page: all row controls are live at readiness, shared type assets are already deduplicated, and a per-row island fixture was slower. The mocked promotion/demotion proof does not qualify production transport or callbacks; a different offscreen-subtree workload could justify it. See [scope review](../../.benchmarks/research/vue-architecture-experiments/islands_teleport_next.md). |
| Server-only regions (Nuxt-style static blocks in one app) | Measured, not built (2026-09-28). A benchmark-only rewrite adopted chosen board parts as `createStaticVNode("", n)` blocks and dropped their insides from the bootstrap JSON. Per row: 2–3 ms (1.5%) faster than the same structure without regions at 1,400 rows, below the 5% bar; regions covered 24% of elements but hydration moved only 53.8 → 53.3 ms, so element checks are cheap and the remaining cost looks per component instance (inferred). Per phase group: 58–64 ms (32–34%) faster, but only by making whole groups static, which disables the row toggles, and it needs a server path that skips preparing region insides. Keeping region HTML in the JSON never beat reading it back from the page. Splitting a row into a child component also forces it off `simple = "vue"` (child calls are rejected), which roughly quadrupled server time. See [design](../../.benchmarks/research/islands-design/REPORT.md) and [measurement](../../.benchmarks/research/islands-stage1/README.md). |
| Data action / incremental updates | Deferred to [issue #144](https://github.com/citry-dev/citry/issues/144) for a separate request/response performance pass. Compare complete Render with the existing Data action before designing a smaller replacement protocol. Excluded from this batch. |

Twenty-two bounded architecture attempts are recorded in this batch: escaped
leaf HTML,
certified leaf-data adoption, evaluation-only plan, strict direct-spread
shortcut, wrapper-aware direct spread, research wire-to-JSON writer, scalar
attribute binding, positional producer construction, early cached-leaf return,
assembly-owned `server_data` adoption, closed-engine orchestration, no-parser
SSR upper bound, partial SSR hydration, fused prepared-leaf tickets, Tetra
local row/phase controls, generated simple-JSON leaf evaluation, and four-region
inline Static SSR browser opportunity, Python component instance erasure, the hybrid keyed optimized-subtree
proof, whole-article Static/direct bindings, native Vue-helper restoration,
and staged-prefix streaming. The opaque Static VNode anchor
fix is a correctness maintenance change, not a performance attempt. Region
validation reuse is a refinement of staged-prefix streaming, not another
attempt. Sandbox
configuration and GC pause attribution were measured separately as diagnostics,
not equivalent optimizations. Four-region SSR and its count-only initial-record
refinement were replaced by hydration from Rust server render programs. Both
lost the earlier actual-Page ready-only comparison against CSR; a separate
single-run layout-inclusive diagnostic favored count-only SSR by about
12–21 ms. Streaming is deferred to
[issue #19](https://github.com/citry-dev/citry/issues/19) and excluded from
framework rankings. A future
cross-framework comparison must report `citry:ready` separately from a
layout-inclusive post-ready endpoint, using the same size and load order for
every framework. The equivalence rerun is a diagnostic, not a qualified
framework ranking; no default-path or full-framework TTI claim is made for
direct SSR.

## Browser comparison

Three rotated samples per size in Chromium 151 / Vue 3.5.42; each synthetic
row had 28 native elements and 25 detail elements. Timer includes HTML
parse/insertion and mount or hydration; excludes generation, asset download,
server rendering, and Citry adapter. All rows and endpoint interactions passed.

| Mode | Fixture HTML bytes (140 / 1,400) | Median parse + mount ms (140 / 1,400) | Topology |
|---|---:|---:|---|
| Whole Vue client mount | 26 / 26 empty host | 1.9 / 19.2 | One app; 140 / 1,400 row components |
| Vue + `createStaticVNode` details | 26 host + 77,430 / 781,250 static | 2.8 / 19.2 | Static details parsed at mount |
| Per-row Vue SSR hydration | 111,406 / 1,130,506 | 2.7 / 26.0 | 140 / 1,400 apps; DOM reused |
| One-app Teleport controls | 103,396 / 1,047,356 | 1.6 / 14.5 | Native details reused |

Inputs are synthetic fixture bytes, not full responses; whole Vue transfers no
representative row JSON. Static HTML is parsed during mount. Hydration used
hand-authored matching HTML; Teleport used a declared effect, not Citry
transport. These three-sample timings do not establish a speedup or predict
canonical island count/startup cost. Browser proof used mocked Events; signed
route, load/cancel/error transport, production callbacks, and Citry Teleport
integration remain untested.

## Mode-switch rules

Proof topology: outer HTML; C1 contains C4 Vue, C2 Vue contains C5 in that app,
and C3 HTML contains C6. A mocked Events click promoted C3 and demoted C2 in
one transaction; a stale prepared transaction was rejected before host writes.

Each Vue island owns its mount target, while Events identity and page routing
outlive Vue app identity so HTML can receive Render/Data/Errors before
promotion. Route updates for absent Vue state to a declared owner or reject;
precommit rejects missing, duplicate, overlapping, or stale targets. Demotion
unmounts listeners and Vue state; mount failure after commit has no rollback.
Arbitrary callbacks, unknown directives, and provide/inject need a managed
boundary or a larger Vue-owned region.

## Handwritten dependency markup A/B

The benchmark-only candidate replaces the Dependencies section with
`{{ dependency_html }}` and returns escaped `Markup`. Separate-process warm
medians were 19.39→49.17 ms (140) and 185.51→383.88 ms (1,400), with matching
class/Event identity and escaped HTML. It triggered whole-leaf typed fallback
(140/1,400 leaves); this rejects only the existing-path substitution. See
[harness](../../.benchmarks/research/vue-architecture-experiments/server_ab.py)
and [samples](../../.benchmarks/research/vue-architecture-experiments/server-ab.json).

## G1 direct escaped emission (rejected prototype)

The removed prototype selected the Dependencies section under `v-show`,
evaluated each value once, escaped text, and used cached typed fallback for
unsupported values. Safe integer `data-*` attrs matched Vue; boolean attrs fell
back. Its unit and browser toggle tests passed with a dedicated opaque-HTML
origin for its regions. No G1-specific TTI run was made. The ordinary leaf
producer has no escaped-region operation or per-render frame/fallback
dispatch; opaque-HTML metadata covers the `raw` and `markup` origins that
other paths produce.

Three processes/mode/size, two warmups, three timed full renders each; visible
DOM, Events identity, and occurrence counts matched. Warm baseline→gated
medians: 21.84→24.24 ms (140), 183.19→226.78 ms (1,400); raw bytes:
150,115→168,610 and 1,290,619→1,474,894; gzip: 15,130→15,672 and
107,423→109,860. Empty sections still create per-row records, so G1 was
removed. See [samples and source hashes](../../.benchmarks/research/vue-architecture-experiments/opaque-ab.json)
and the [source disposition note](../../.benchmarks/research/vue-architecture-experiments/rejected_leaf_paths.md).

## G3 certified leaf-data adoption (rejected prototype)

The removed prototype detached external leaf attributes, keys, and binding
payloads during evaluation, then let final assembly adopt data with a private
certificate tied to that exact prepared-data object. Generated branch and loop
containers avoided another recursive strict-JSON copy. Cache replay created a
certificate only from a validated frozen artifact. Public occurrence
detachment and the ordinary cache-replay path remain unchanged.

Six alternating fresh processes per size (three per mode), each with two
warmups and three timed `Page.render().serialize()` calls, produced exact full
HTML, manifest, compiler-input, response-byte, and occurrence-count parity.
Warm baseline→gated medians were 20.261→20.412 ms at 140 rows and
186.266→187.877 ms at 1,400 rows. Cold medians were 50.602→51.457 ms and
224.676→221.453 ms. The warm path has no repeatable gain, so no browser TTI
run was warranted. See [paired samples and source hashes](../../.benchmarks/research/vue-architecture-experiments/g3-interleaved.jsonl)
and the [source disposition note](../../.benchmarks/research/vue-architecture-experiments/rejected_leaf_paths.md).

## Wrapper-aware direct spread projection and evaluation plan

When the built-in translation wrapper has no active translation work, the
evaluator produces Vue attributes directly and keeps raw values for HTML
fallback. The exact wrapper guard excludes static translations and compiled
catalog work. This path reaches all 140/1,400 canonical
`ProjectOutput` openings and avoids `_prepared_from_resolved()` on those
ordinary renders. It retains the resolved attributes for lazy typed/static
fallback. The evaluation-only plan skips static and closing operations during
normal evaluation while retaining the full fallback program. The spread path
still requires the transparent wrapper, inactive translation work, and safe
attribute checks; the evaluation plan applies only to leaf programs accepted by
the bounded compiler. This differs from the earlier strict direct-spread shortcut,
which could not enter the page's i18n-wrapped opening.

Three alternating fresh processes per mode and size, with two warmups and
three timed full renders per process, produced exact full HTML, manifest,
compiler-input, response-byte, and occurrence-count parity. Combined warm
baseline→gated medians were 20.547→19.834 ms at 140 and 187.623→171.946 ms
at 1,400; cold medians were 50.373→50.525 ms and 229.388→197.008 ms. These
three-timed-sample captures predate G1 source removal. After cleanup, a bounded
same-source interleaved check used three fresh processes per mode and size,
two warmups and one timed render + serialize per process. Full HTML, manifest,
and compiler-input hashes matched; source hashes matched across both arms.
Warm sample medians were 28.409→26.972 ms at 140 rows and 188.527→162.590 ms
at 1,400 rows. The single timed sample per child is a cleanup confirmation, not
a replacement for the earlier multi-sample result. See the
[final-source capture and hashes](../../.benchmarks/research/vue-architecture-experiments/final-source-ab.json).

Source-mode browser readiness used Chromium 151.0.7922.34 and the project
`.venv`, with a warmed source server and two fresh browser contexts per
mode/size. Canonical initial-state and native local-behavior assertions passed
on both loads. First/second readiness intervals were 98.8/64.3 ms baseline and
96.7/63.0 ms candidate at 140 rows; 421.8/373.5 ms baseline and 410.9/370.0
ms candidate at 1,400 rows. One reversed-order pair produced 97.3/62.9 ms
baseline and 96.2/63.0 ms candidate at 140 rows; at 1,400 it produced
420.4/383.0 ms baseline and 407.0/387.0 ms candidate. Across those two small
pairs, 1,400-row server `prepare` time was lower by about 12.9 ms on the first
load and 5.6 ms on the second, while post-response browser time was flat on the
first load and 9.5 ms higher for the candidate on the second. The result
supports the server-side measurements, but does not establish a repeatable
TTI gain. The reversed capture includes application/prepare server timings and
Navigation Timing phases. See the [first source-mode pair and hashes](../../.benchmarks/research/vue-architecture-experiments/source-tti-final-paired.json)
and the [reversed pair with phase timing](../../.benchmarks/research/vue-architecture-experiments/source-tti-reversed-paired.json).
## Early cached leaf return (retained)

The cached definition path hit 141 times per 140-row render and 1,401 times per
1,400-row render. The 20-render normal-GC windows preserved exact HTML,
manifest, and compiler-input hashes. Mean full render + serialize changed
20.388 → 19.274 ms at 140 rows and 171.889 → 160.907 ms at 1,400 rows. GC
pauses changed 42.6 → 29.0 ms and 478.5 → 334.9 ms respectively; both 20-render
windows included gen2 collections, with the normal policy unchanged. This shows
durable whole-path timing in this bounded fixture, without identifying an
object-level cause.

Two source-mode candidate pairs contribute n=2 points per size/load to the
current graph. Their grouped first/second readiness medians are 97.95/62.15 ms
at 140 rows and 397.65/373.80 ms at 1,400 rows. The browser evidence is
experimental and mixed, so it does not establish a TTI gain. The [full
framework-reference copy](../../.benchmarks/results/framework-reference-composite/20260923T-source-mode-early-leaf-citry-n2/report.html)
retains all framework rows and historical Citry action and memory metrics; its
[metric provenance](../../.benchmarks/results/framework-reference-composite/20260923T-source-mode-early-leaf-citry-n2/provenance.json)
labels the mixed dates and source mode.

## Assembly-owned server data adoption (rejected)

`_json_plain` already detaches render-time `js_data`; adopting that owned value
instead of JSON-dumping and loading it again produced exact output parity. The
three-process warm means improved 3.25% at 1,400 rows but were flat at 140. In
the longer normal-GC window the 1,400-row result was flat and the 140-row
direction reversed, so this separate copy-removal step was not retained. The
public `PreparedOccurrence` constructor still deep-detaches caller values.
