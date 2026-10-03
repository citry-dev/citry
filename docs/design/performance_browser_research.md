# Browser runtime optimization research

This maintained ledger records browser performance experiments and the ideas
still waiting for a controlled comparison. Server repeat-render work has its own
[`summary`](performance_render_experiment_summary.md) and
[`research journal`](performance_render_research.md).

Raw browser profiles, traces, candidate runtimes, and observations stay in the
ignored `.benchmarks/research/` directory. Experiment scripts stay there too;
they are not maintained repository tooling. This document must keep enough
context to interpret a result when those local artifacts are unavailable.

## Evidence and decision rules

A CPU profile or direct timer locates work to investigate. It does not establish
a runtime saving. A complete cohort compares adapters but does not isolate one
Citry change. Only an alternating control/candidate run whose variants differ by
the stated change supports a causal performance decision here.

Run an unchanged A/A comparison when establishing a baseline and when settings
or observed noise change. An ordinary compatible runtime change must beat that
noise reproducibly and pass correctness checks. There is no arbitrary 1 ms
target. A complex build, protocol, or API change also needs evidence that its
gain justifies its build and maintenance cost, payload effect, and behavior
tradeoff. Declare the sample and time budget before measuring.

Disk cleanup is deliberately narrow. The only completed cleanup in this batch
was the old performance target selected by the root. Future cleanup may remove old
qualification captures only when a benchmark needs the headroom; if that is
insufficient, stop the work. Do not delete other runs, research evidence,
builds, environments, source, or generated assets as incidental cleanup.

Savings from separate experiments cannot be added. Two accepted experiment
groups each contain two changes because their individual contributions were not
measured:

- batched manifest discovery plus removal of the second planning-tree copy;
- reuse of the first parsed placement tree plus the qualified leaf-planning
  bypass.

The last complete cohort for the flat-row scenario is run
`20260910T192550Z-7b0a969f`, captured build
`d25e66f85e9e49b58b14bd47f6f1b06aa8877eeed6342efb820fca42501f8672`.
At 1,000 rows it records 113.8 ms initial readiness, 211.25 ms insert, and
265.6 ms reorder for Citry. These are separate cohort observations, not a
cumulative result or a substitute for the 221.0 ms controlled A/B below.

## Workload boundary for the next experiments

The next browser experiments use the canonical project data and hierarchy
derived from
[`test_benchmark_citry.py`](../../packages/py/citry/tests/test_benchmark_citry.py).
The source declares 36 component classes and exercises slots, provided values,
dynamic elements, attachments, dependencies, notes, comments, roles, and a
bookmark. It is a render fixture rather than a working browser application: its
tab composition flattens ownership, some handlers are absent, and its JavaScript
has a startup ordering error. The shared scenario therefore preserves the
canonical data relationships and major page sections through each framework's
native component composition. It documents the interactive adaptations required
for a working application; the canonical baseline below records observed
per-adapter DOM counts. It does not claim the fixture's 36-class architecture,
byte-identical HTML, identical component counts, or identical browser behavior.

The maintained `project_board` scenario now defines output counts rather than
row counts. Profiles and run manifests identify it as
`canonical-project-v1`; reports without that revision retain the historical row
label:

| Scale | Required shape |
| --- | --- |
| 1x, 14 outputs | One project, five phase groups, and one copy of the canonical 14-output content cohort. |
| 10x, 140 outputs | The same shell and groups with ten content replicas, unique IDs, and references rewritten within each replica. |
| 100x, 1,400 outputs | The same linear rule. This opt-in profile runs only after review of 1x and 10x time and memory use. |

The previous flat, homogeneous board remains represented by its captured runs;
it is not maintained as a second application. Alternate branches, slot fallback,
and dynamic-element choices are correctness cases for future qualification, not
a fourth benchmark scale. Unknown counts fail during configuration. A browser
error, stale response, semantic mismatch, missing expected state, or readiness
timeout fails an observation rather than producing a timing.

## Entry format

Every attempt records:

1. **Hypothesis:** which repeated work should fall and why.
2. **Change:** the complete control/candidate difference.
3. **Context and version:** workload and mode, action, browser and version,
   machine/OS, source or captured build, runtime hashes, server setup, cache
   state, warmup, sample count, and profiler state.
4. **Evidence:** raw artifact paths and measurement method.
5. **Results:** control and candidate medians for every measured action, plus
   the path containing all observations.
6. **Correctness:** assertions, browsers, error cases, and falsifying cases.
7. **Decision:** adopted, rejected, diagnostic only, deferred, or queued, with
   the reason.
8. **API risk:** behavior that could change even when final HTML matches.

## Completed attempts

| ID | Hypothesis and change | Context, evidence, and results | Correctness, decision, and API risk |
| --- | --- | --- | --- |
| B1 | Repeated document searches from the Alpine interceptor dominate large-tree initialization. A browser-only probe omitted its per-element manifest drain. | Frozen Citry 0.5.0 build `9b143ddbdb27811241eda44373f819b1cf9572bd50f2492abfeeb86c67f0cbcc`; project board at 1,000 rows; three fresh Chromium contexts per variant, one server, no profiler. Medians: initial 451.4 to 106.6 ms, select 952.2 to 623.3 ms, insert 1024.3 to 632.3 ms, reorder 1022.5 to 649.8 ms. All 60 observations: `.benchmarks/research/citry-1000/ab-observations.json`. | All DOM, disclosure, and draft checks passed. **Diagnostic only:** an external insertion can call `Alpine.initTree` before observer delivery, so omitting synchronous discovery changes behavior. A safe implementation must preserve manifest order, resource holds, startup and late-provider catch-up, and asynchronous cleanup during same-task moves. |
| B2 | Processing only pending manifests and letting simulated morph consume its disposable detached trees should remove repeated searches and one planning copy. | Project board at 1,000 rows; three fresh Chromium contexts per variant, one frozen Python server, runtime bytes as the only variant, no profiler. Medians: initial 493.4 to 119.4 ms, select 1011.8 to 418.7 ms, insert 1017.5 to 436.3 ms, reorder 1043.0 to 462.2 ms. All 60 observations: `.benchmarks/research/citry-1000/after-fixes/ab-observations.json`; summary: `ab-summary.json`. The later cohort carrying both changes has build `c2e2fdb635f60562760fb02844b6722597a9a43396faeef0aa13261a47891a91`. | All 60 observations passed. Planning passed 237 browser checks across Chromium, Firefox, and WebKit plus 19 JavaScript checks and TypeScript; discovery/lifecycle passed 210 cross-browser checks and six focused follow-ups. **Adopted together.** No per-change attribution. Synchronous discovery, asynchronous cleanup, source links, public input retention, and rejection of live roots remain required. |
| B3 | A parsed placement tree can be reused only while its HTML and parsing context remain valid. The first strict validity behavior did not fall back when preparation changed them. | Correctness qualification only; no timing candidate or separate release. Evidence: [`test_prepared_placement_e2e.py`](../../packages/py/citry/tests/e2e/test_prepared_placement_e2e.py) and `.benchmarks/research/citry-1000/planning-followup/findings.md`. Results: no performance observations. | Valid slot staging and framework preparation can change HTML or context. The corrected path reparses on a mismatch and passed 267 broad plus 36 focused checks across three browsers. **Strict behavior rejected; fallback retained in B4.** A strict failure rejects valid updates, while stale reuse can apply the wrong HTML or namespace topology. |
| B4 | Reusing the planning parse removes the application parse. A single-placement leaf without slots, nested ownership, ignore barriers, or teleports can skip ordinary correspondence simulation. | Control already carries B2; project board at 1,000 rows; three fresh Chromium contexts per variant, one frozen server, runtime bytes as the only variant, no profiler. Medians: initial 106.5 to 107.0 ms, select 391.3 to 214.7 ms, insert 412.3 to 221.0 ms, reorder 442.6 to 274.8 ms. Insert observations were 412.3/420.4/411.8 and 221.0/220.7/221.3 ms. All 60 observations: `.benchmarks/research/citry-1000/planning-followup/ab-observations.json`; summary: `ab-summary.json`; candidate hashes: `runtime-sha256.json`. | All 60 observations passed, followed by the same 267 broad and 36 focused cross-browser checks. **Adopted together:** insert fell 46.4%; initial was unchanged within this small run. No per-change attribution. Reuse stays scoped to one transaction and placement and falls back after relevant changes. The bypass keeps full validation and the generic path for slots, nested or malformed caps, multiple placements, ignore barriers, and teleports. |
| B5 | The effective base URI might need to participate in retained-parse validity. Proposed guard: compare `baseURI` and fall back after a relevant `<base>` change. | Source analysis against B4. No captured candidate, measurements, or falsifying correctness case. | **Deferred and unproven.** First establish whether contextual parsing captures URL behavior that differs after insertion and whether the fallback affects it. A missing relevant guard could preserve the wrong URL interpretation; an unnecessary guard adds work and reduces reuse. |
| B6 | Native subtree cloning might explain part of insert latency. A diagnostic wrapper timed calls without changing morph behavior. | Project board 1,000-row insert after B2. One live eight-element `LI#row-1001` clone took 18.6 ms; a planning clone of that row took 2.5 ms; 8,045-element Events serialization clones took about 1.2 ms each. Evidence: `.benchmarks/research/citry-1000/planning-followup/deep-clone-call-times.json`, `clone-diagnostic-observations.json`, and `insert-browser-trace.json`. No control/candidate medians exist. | **Diagnostic only:** the sample does not establish cause, reproducibility, or obtainable saving. Clone, move, and manual construction differ in identity, JavaScript properties, listeners, Alpine markers, custom-element timing, namespaces, templates, traversal, and mirrored reuse. |
| B7 | The canonical keyed reorder exposed a Citry 0.5 correctness bug: Alpine's queued removal observer could clean up a still-live portable node when remove and reinsert records arrived in separate mutation batches. The fix checks whether the removed node's root is the same observed document before cleanup, in addition to the existing added-node check. | Correctness work against the canonical page and both pinned standard and CSP browser builds; no control/candidate comparison or timing result exists. The correct worktree passed 216 broad checks across three browsers, 20 canary checks, 6 focused browser checks, and Citry's complete canonical action sequence without errors. The frozen cohort then passed 22 Citry fault cases and 38 initial/action observations across 14 and 140 outputs. Evidence: `.benchmarks/research/browser-optimization/citry-canonical-remove-illegal-invocation.json`, qualification run `20260910T211550Z-8db0cc0b`, and measurement run `20260910T212003Z-4525b449`. | **Accepted as a correctness fix; no performance gain claimed.** Bare `isConnected` was rejected because a node connected in another document or shadow root is outside this observer's ownership. The same-document root guard preserves a keyed node moved across split mutation batches while retaining cleanup for real removals and moves outside the observed document. Independent technical, recovery, and prose reviews cleared the fix. |

## Canonical scenario baseline

Status: **the first frozen 1x/10x diagnostic cohort passed**. Build
`0c9a4e060a8fb5dcf4fd9e6eea8e5aa15ca2a6010105dc6c57fdab45a6328057`
uses the captured workspace Citry browser runtime and pinned published Python
package. Qualification run `20260910T211550Z-8db0cc0b` accepted all 418
initial/action observations and all 242 fault cases: 11 cases for every adapter
at both 14 and 140 outputs. Measurement run `20260910T212003Z-4525b449`
recorded 418 successful samples and no failures or skipped observations. Its
standalone report is
`.benchmarks/runs/20260910T212003Z-4525b449/report.html`; detailed analysis is
under `.benchmarks/research/browser-optimization/canonical-baseline-20260910/`.

The native loopback run used Chromium 151.0.7922.34 on arm64 macOS, one block,
one session per adapter and count, no warmups, and two action cycles. Initial
has one observation per adapter and count; each action has two. These descriptive
medians are a local baseline, not a publication ranking or a precise tail
estimate. The report was opened in the pinned browser at 1,440 by 1,000; its
output-scale labels, nine charts, observations, and failure counts rendered
without a page error or visible overlap.

| Adapter | Initial 14 / 140 ms | Insert 14 / 140 ms | Reorder 14 / 140 ms |
| --- | ---: | ---: | ---: |
| Citry | 66.30 / 225.80 | 73.30 / 694.80 | 73.70 / 662.15 |
| Django Components | 39.90 / 79.90 | 43.55 / 70.05 | 45.10 / 85.15 |
| Django + HTMX | 30.80 / 56.80 | 44.30 / 63.20 | 40.35 / 64.35 |
| FastHTML | 30.90 / 79.20 | 49.40 / 88.25 | 42.55 / 86.15 |
| Jinja + HTMX | 31.50 / 53.60 | 44.00 / 63.75 | 44.40 / 65.95 |
| React | 21.40 / 42.10 | 19.75 / 20.25 | 17.35 / 18.90 |
| Vue | 20.00 / 29.10 | 19.20 / 23.40 | 17.95 / 21.35 |
| ReactPy | 55.30 / 108.60 | 33.45 / 45.70 | 34.20 / 75.65 |
| Reflex | 60.00 / 82.00 | 16.85 / 19.60 | 17.20 / 24.35 |
| Tetra | 34.40 / 57.20 | 20.30 / 39.85 | 21.00 / 51.25 |
| Unicorn | 39.00 / 80.60 | 25.35 / 55.20 | 25.30 / 62.00 |

At 140 outputs, Citry's insert server HTML-render median was 20.65 ms while the
complete trusted-action median was 694.80 ms. Its synchronous semantic observer
median was 1.50 ms and remains an uncalibrated source of event-loop perturbation.
This split motivates a client profile; it does not isolate DOM matching,
relationship search, transport, or a proposed optimization. The 1,400-output
cohort remains disabled until that profile and the 1x/10x time and memory review.

Initial accepted DOM captures provide the scale evidence below. Counts include
the document shell and framework-owned DOM. Citry had 70 / 322 boundary
comments, 27 / 153 marked root elements, and 29 / 155 distinct DOM component
IDs at 14 / 140 outputs. The IDs are DOM evidence, not a cross-framework claim
of equal native component decomposition.

| Adapter | Elements at 14 / 140 | Comments at 14 / 140 |
| --- | ---: | ---: |
| Citry | 492 / 3,723 | 70 / 322 |
| Django Components | 531 / 4,032 | 0 / 0 |
| Django + HTMX | 531 / 4,041 | 0 / 0 |
| FastHTML | 530 / 4,040 | 0 / 0 |
| Jinja + HTMX | 531 / 4,041 | 0 / 0 |
| React | 472 / 3,253 | 0 / 0 |
| Vue | 472 / 3,253 | 4 / 4 |
| ReactPy | 422 / 2,825 | 1 / 1 |
| Reflex | 509 / 3,290 | 4 / 4 |
| Tetra | 512 / 3,869 | 0 / 0 |
| Unicorn | 437 / 3,290 | 0 / 0 |

The first canonical diagnostic's identity-encoded byte values describe each
adapter's production-shipped assets and transport in that frozen `0c9a4e...`
build. Citry's initial bodies were 851,342 B at 14 and 1,068,919 B at 140
outputs; the other adapters ranged from 78,564 to
587,887 B and from 114,397 to 623,725 B. Citry insert bodies were 53,395.5 and
291,554.5 median bytes; comparison adapters ranged from 5,035.5 to 44,313 and
40,872.5 to 310,341 bytes. These are configured-package outcomes, not normalized
bundle or protocol comparisons. Citry runtime minification and retained-script
cleanup were deferred at that checkpoint.

## Full-cohort checkpoints

The intermediate 1x/10x checkpoint froze Q1a, Q2a, Q1c, and S1 together in build
`77bd4d334df7938131309147be339ecf17d51364f104260c91619066fe960824`.
Qualification run `20260910T230834Z-83780ad9` accepted all 418 initial/action
observations and all 242 fault cases. Measurement run
`20260910T231232Z-f6ffbd3c` recorded 418 successful samples with no failures or
skips. Its graph report is
`.benchmarks/runs/20260910T231232Z-f6ffbd3c/report.html`.

The selected Citry medians below use the same local profile shape as the first
canonical diagnostic. Each column is a separate cohort rather than an
alternating control/candidate experiment. Their differences describe frozen
checkpoints and do not attribute a gain to one change.

| Count and action | First diagnostic, ms | Q1/S1 checkpoint, ms | Q2e/Q2f/Q6d checkpoint, ms | Q2h checkpoint, ms |
| --- | ---: | ---: | ---: | ---: |
| 14 initial | 66.30 | 60.40 | 65.10 | 60.50 |
| 14 insert | 73.30 | 36.00 | 35.15 | 35.50 |
| 14 reorder | 73.70 | 36.20 | 35.75 | 36.65 |
| 140 initial | 225.80 | 117.80 | 120.80 | 116.60 |
| 140 insert | 694.80 | 176.70 | 159.05 | 151.55 |
| 140 reorder | 662.15 | 157.50 | 150.70 | 147.95 |

The Q2e/Q2f/Q6d checkpoint adds those changes to the earlier accepted work. The
reviewed APFS clone produced prepared build
`3d96f11b57d5d2877bb232f12390b958df3efdc8533e6d01a0a1b9b97c3d9e36`
while consuming 25,542,656 physical bytes. Qualification run
`20260911T010000Z-c7392f38` accepted 418/418 initial/action observations,
242/242 fault cases, and 418/418 size records. Normal run
`20260911T010402Z-7799b098` recorded 418/418 successful samples and 418/418
size records without a failure or skip. Its graph report is
`.benchmarks/runs/20260911T010402Z-7799b098/report.html`; detailed analysis is
under
`.benchmarks/research/browser-optimization/final-canonical-checkpoint-20260911/`.

Root opened that report with 140 outputs and insert selected. All nine
graphs, both output choices, all nine actions, one Citry series among all eleven
adapters, and the N/A client HTML-render value appeared without a JavaScript
error, overlap, or clipping. The retained screenshot and inspection record are
`.benchmarks/research/browser-optimization/final-canonical-report-140-insert.png`
and `final-canonical-report-inspection.json`.

That run recorded Citry initial bodies of 638,599 B at 14 outputs and
856,176 B at 140. The earlier `77bd4d...` checkpoint recorded 866,282 B and
1,083,859 B. These identity-encoded configured-package totals include the Q6d
delivery change; they are not normalized bundle sizes or an isolated transfer
comparison.

The Q2h performance checkpoint also adds Q2g and Q2h. The reviewed clone produced
prepared build
`5490ba58173e3a8f48b7a03aff9b65a7307a3af087cf72352966e31948e83b22`.
Qualification run `20260911T030859Z-3bde840f` accepted 418/418 initial/action
observations and 242/242 fault cases. Normal run
`20260911T031252Z-72e7cd37` recorded 418/418 successful samples and 418/418
size records, grouped into 220 timing and 220 size cells, without a failure or
skip. Its graph report is
`.benchmarks/runs/20260911T031252Z-72e7cd37/report.html`. The independently
recomputed artifact summary is
`.benchmarks/research/browser-optimization/final-benchmark-refresh/final-report-analysis.json`.

Root opened the current report with 140 outputs and insert selected. All nine
charts, both output choices, all nine actions, one Citry series among all eleven
adapters, the N/A client HTML-render value, and the 418/0/0 status rendered
without a page error or visible issue.
The retained screenshot and visual metadata are
`.benchmarks/research/browser-optimization/final-benchmark-refresh/final-report-screenshot.png`
and `final-report-visual.json`. The run recorded Citry initial encoded response
bodies of 650,547 B at 14 outputs and 868,124 B at 140. These remain separate
configured-package observations rather than an isolated payload comparison.

The final measurement-instrumented refresh used an APFS clone of that cohort,
updated only the reviewed first-party runner and adapter sources plus the
current runtime mapping, and consumed 28,241,920 physical bytes. Prepared build
`d5c603cba060a2237fee2a534f6a544aa348169aec48587a57cfc1ae131c3895`
retains delivered core `bec63fec...`, standard Events `7eabba03...`, and CSP
Events `5d86f425...`. Qualification run
`20260911T082350Z-028f27d6` passed 418/418 initial and action observations plus
242/242 fault cases. Normal run `20260911T082747Z-128432bb` recorded 418/418
successful timing observations and 418/418 size observations; every server
output-preparation metric and browser phase vector was measured. Preparation
kinds were 266 HTML, 76 JSON, and 76 state-delta observations. Citry medians
were 59.5 / 139.6 ms for initial readiness, 31.2 / 151.05 ms for insert, and
35.75 / 147.6 ms for reorder at 14 / 140 outputs. Its standalone report is
`.benchmarks/runs/20260911T082747Z-128432bb/report.html`. The new
preparation spans cover the bounded output construction and serialization
performed by each adapter and exclude transport, browser work, and unrelated
request or event handling. This is a new instrumented cohort, so its values do
not replace the controlled candidate comparisons or the earlier checkpoint
medians above.

The controlled second-load refresh cloned `d5c603cb...` into runner-only build
`ce8c80d8...`, consumed 29,200,384 physical bytes, and retained the same
`bec63fec...` / `7eabba03...` / `5d86f425...` runtime. Qualification run
`20260911T093412Z-200040ef` passed 440/440 timing and size observations plus
242/242 fault cases. Normal run `20260911T093826Z-0bf38fc3` passed 440/440
timing and size observations and produced 242 timing and 242 size groups. All
440 output-preparation and phase observations were measured: 280 HTML, 80 JSON,
and 80 state delta. Each adapter/count pair used the same application process
but distinct logical sessions and fresh HTTP-asset-cold browser contexts for
load 1 and load 2; all 396 actions ran only on load 2. Citry load 1 / load 2
initial-readiness observations were 61.2 / 45.4 ms at 14 outputs and 117.9 /
98.4 ms at 140. Its load 2 insert and reorder medians were 35.5 / 36.55 ms at 14
and 150.15 / 151.45 ms at 140. Both loads share browser process and host state,
so their difference is a repeat-load outcome rather than attribution to server
caches. The ten-chart report is
`.benchmarks/runs/20260911T093826Z-0bf38fc3/report.html`, SHA-256 `ebec9b7c...`.
It is the complete pre-S2b/S3 11-adapter 14/140 checkpoint and does not alter
any controlled optimization comparison above.

The final runtime-only refresh cloned that qualified build into prepared build
`94421ff0dfe95920c3c5b019c8ff5335cbca665a7d15a595f9bff20a8d6f3675`
and consumed 30,023,680 physical bytes. It carries accepted delivered core
`3992ed57...`, standard Events `2b80fe83...`, and CSP Events `d5937fd3...`.
Qualification run `20260911T115622Z-3b08c229` passed 440/440 timing and size
observations plus 242/242 fault cases. Normal run
`20260911T120026Z-81b161c7` passed 440/440 timing and size observations and
produced 242 timing and 242 size groups. All 440 output-preparation and browser
phase observations were measured; preparation kinds were 280 HTML, 80 JSON, and
80 state delta. Citry load 1 / load 2 initial readiness was 65.8 / 44.9 ms at 14
outputs and 119.5 / 100.3 ms at 140. Its load 2 insert and reorder medians were
39.1 / 38.15 ms at 14 and 152.65 / 154.45 ms at 140. The ten-chart report is
`.benchmarks/runs/20260911T120026Z-81b161c7/report.html`, SHA-256 `cbfbbec6...`;
its load selector and visible report state passed inspection. These cohort
values describe the final combined runtime; they do not add the isolated S2b
and S3 savings or replace either controlled comparison.

The bounded Citry 1,400-output feasibility probe reused exact final build
`3d96f11b...` and passed initial and insert semantics without a browser error.
Initial readiness took 838.6 ms; insert took 23,450.4 ms. The post-assertion
operating-system process-tree RSS sums were 1,604,768 and 2,114,432 KiB. They
can double-count shared pages and are neither peak memory nor browser heap.
The insert used the probe's remaining 30-second soft budget, while the
maintained 100x cohort profile has a 10-second action timeout. This result does
not establish full-profile feasibility: unchanged qualification is expected to
time out Citry. Evidence is in
`.benchmarks/research/browser-optimization/canonical-1400-feasibility/result.json`.

One follow-up exact-runtime CPU profile placed 20,520.820 of 24,072.146 sampled
milliseconds in `compareDocumentPosition` itself, or 85.247%. Its recorded
caller stacks split into live-morph key-map containment (8,409.296 ms),
stationary-range checks (6,185.358 ms), intermediate-range equivalence checks
(3,731.762 ms), and Events retirement (2,073.841 ms). By comparison,
`rangePairsUnder` had 397.267 ms exclusive, `querySelectorAll` 220.219 ms,
`querySelector` 151.875 ms, and `cloneNode` 141.749 ms. This single cold profile
reopens bounded work on repeated live-DOM ordering and containment; it is not a
causal timing comparison, a call count, or evidence that the full 100x cohort
is accepted. Evidence is in `profile-findings.md` and `profile-result.json` in
the same research directory.

## Next baseline work

Status: **S2b and S3 are integrated, the current full 1x/10x checkpoint passed,
and the full 100x cohort is on hold with its 10-second timeout unchanged**. Q4a
and Q7a were evaluated and deferred; the other source-reviewed ideas below are
also deferred for their recorded reasons. The current complete 1x/10x graph
report includes Q2g, Q2h, S2b, and S3.

One maintained 1,400-output full-action feasibility session used frozen build
`5490ba58173e3a8f48b7a03aff9b65a7307a3af087cf72352966e31948e83b22`
and the unchanged 30-second initial and 10-second action timeouts. Initial
readiness passed in 808.2 ms, select in 8,751.7 ms, and filter in 4,822.7 ms.
Clear-filter then timed out at 10 seconds; invalid-save, save, insert, reorder,
remove, and probe did not run. The one Chromium session stopped at that first
failure and was not retried. Its clear-filter response returned HTTP 200 after
179.904 ms of server rendering, before browser readiness timed out. This places
the unresolved completion cost after the server response without assigning a
precise browser duration beyond the timeout. This is separate from Q2h's
isolated 9,046.6 ms candidate insert median under a 40-second diagnostic
timeout and the earlier 23,450.4 ms pre-Q2g/Q2h insert profile. Evidence:
`.benchmarks/research/browser-optimization/final-benchmark-refresh/canonical-1400-session/result.json`,
SHA-256 `7cfafa29...`, and the retained failure capture in that directory.

A later exact-runtime diagnostic used the pre-S2b/S3 instrumented build
`d5c603cba...`, delivered core `bec63fec...`, and standard Events
`7eabba03...` in one Chromium 1,400-output session. Initial readiness completed
in 815.4 ms. Its sampled initial profile placed 139.166 ms of
`querySelectorAll` self time under the global Events-manifest consumer; broader
Alpine initialization, directive, expression, effect, and Citry lifecycle
caller paths overlap and are not additive. After unprofiled select and filter
setup, clear-filter completed with exact semantics in 11,913.5 ms, so it remains
a timeout under the maintained 10-second limit. The response reported 185.948
ms of application work. A mutually exclusive reduction assigned 9,992.925 ms,
or 79.946% of 12,499.566 sampled milliseconds, to
`reconcileComponentLifecycles`; 9,912.062 ms had the recorded caller chain from
Alpine mutation handling through tree and boundary initialization to that full
reconciliation. In the measured `f286a7be...` readable core, the startup reuse
gate at line 327 rejects post-start reuse, and the boundary path at lines
561-566 then calls the full reconciliation. This one sampled interval supplies
attribution rather than a latency comparison, call count, or optimization.
Evidence is in
`.benchmarks/research/browser-optimization/current-canonical-1400-profile/`;
`findings.md` has SHA-256 `07d4350b...`.

The final S2b/S3 runtime used one more maintained 1,400-output session against
prepared build `94421ff0...`. Initial passed in 677.9 ms, select in 8,848.8 ms,
filter in 5,052.3 ms, clear-filter in 1,758.7 ms, and invalid-save in 9,509.5
ms. Save then timed out at 10 seconds; insert, reorder, remove, and probe did not
run. Its 2,686,594-byte encoded response returned HTTP 200 after 197.230 ms of
application work and 189.830 ms of rendering, before client completion and
readiness timed out. The session stopped at that first failure and was not
retried. This is one feasibility observation, not a controlled comparison or
evidence that the full 100x cohort is ready. It is distinct from the earlier
`5490ba58...` session, which timed out at clear-filter, and from S2b and S3's
40-second controlled diagnostics. Evidence is in
`.benchmarks/research/browser-optimization/final-series-refresh/canonical-1400-session/`;
`result.json` has SHA-256 `91346a4a...`.

### Profile-grounded follow-ups

The retained profile supported two bounded design investigations. Each
completed its own correctness and controlled-measurement decision:

- Coalesce full lifecycle reconciliation across one proven bulk post-start
  boundary-initialization phase. S1 applies only while Alpine is starting, so
  its reuse contract does not cover this path. S2a's whole-tree reuse candidate
  was rejected before timing because it reused zero canonical boundaries. A
  follow-up diagnostic found that all 1,300 blockers were disconnected,
  unreferenced, inactive-key, or expected-retirement metadata even though all
  1,421 consulted range entries and 1,414 active roots belonged to the observed
  document. S2b narrowed the guard to the physical alternatives, recursive
  parents, and active roots that the pending full reconciliation can read. It
  was accepted after its eligibility, correctness, and controlled timing checks;
  its result is recorded in the experiment table below. Preserve
  per-boundary initialization and provider order, current-root scope isolation,
  synchronous failure behavior, liveness and corruption checks, and
  invalidation after external DOM mutation.
- S3 replaced repeated document-wide Events-manifest discovery at each boundary
  with an Events-owned pending consumer. This is distinct from B2's core
  pending-manifest path. It preserves synchronous discovery and provider order
  for initial, externally inserted and catch-up manifests, graph and revision
  pairing, errors, and explicit full replay. Its controlled result is recorded
  in the experiment table below.

A separate diagnostic then exercised each of the ten non-Citry adapters from
the same frozen build at 1,400 outputs. It used one sequential Chromium session
per adapter, no warmup or retry, one observation per operation, the maintained
30-second initial and 10-second action timeouts, and a soft five-minute launch
budget checked between adapters. All ten adapter sessions completed within
286.37 seconds. Every one of their 100 operation observations and 100 size
observations passed, with no error or failure capture. The selected values below
are single local observations, not medians, rankings, or evidence of a timing
gain.

| Adapter | Initial, ms | Select, ms | Filter, ms | Clear filter, ms | Insert, ms | Reorder, ms | Slowest of all ten operations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Django + HTMX + Alpine | 320.8 | 449.2 | 237.1 | 360.6 | 789.8 | 929.9 | probe, 996.7 ms |
| FastHTML | 678.0 | 808.4 | 284.8 | 660.6 | 1,148.5 | 1,213.8 | reorder, 1,213.8 ms |
| ReactPy | 713.1 | 577.5 | 302.2 | 928.2 | 708.8 | 2,100.0 | reorder, 2,100.0 ms |
| Tetra | 308.2 | 321.5 | 102.0 | 323.8 | 473.6 | 636.9 | probe, 877.2 ms |
| Unicorn | 492.4 | 392.5 | 125.2 | 487.1 | 389.4 | 461.5 | initial, 492.4 ms |
| Reflex | 349.2 | 149.0 | 48.9 | 466.8 | 158.7 | 252.2 | clear filter, 466.8 ms |
| Jinja + HTMX + Alpine | 297.0 | 429.0 | 241.6 | 342.9 | 839.0 | 889.1 | reorder, 889.1 ms |
| Django Components | 459.7 | 591.1 | 287.3 | 520.0 | 1,016.3 | 1,083.7 | reorder, 1,083.7 ms |
| Python + Vue | 208.6 | 86.2 | 46.8 | 382.8 | 84.4 | 113.0 | clear filter, 382.8 ms |
| Python + React | 263.3 | 132.3 | 45.6 | 442.4 | 150.4 | 232.5 | clear filter, 442.4 ms |

Within this exact local diagnostic, Citry was the only one of the eleven
frozen adapters that failed the maintained full-action 1,400-output sequence:
the separately retained Citry session timed out at clear-filter after initial,
select, and filter passed. This comparison establishes only the observed
feasibility boundary. The non-Citry sessions were sequential, unreplicated,
and not a qualification or cross-adapter performance ranking. Evidence is in
`.benchmarks/research/browser-optimization/non-citry-1400-feasibility/`;
`result.json` has SHA-256 `2ba47079...`. Build `5490ba58...` contains the Q2h
performance checkpoint before the later slot-scope correctness fix. That fix
is after the adoption-plan return used by the benchmark path, so the diagnostic
does not measure its bytes and does not change the retained path attribution.

1. Preserve build `5490ba58...` and run `20260911T031252Z-72e7cd37` as the
   pre-instrumentation historical checkpoint. Preserve build `ce8c80d8...` and
   run `20260911T093826Z-0bf38fc3` as the pre-S2b/S3 second-load checkpoint. Use
   build `94421ff0...` and run `20260911T120026Z-81b161c7` as the current
   complete 11-adapter 14/140 checkpoint. These cohorts do not attribute a gain
   to one optimization.
2. Keep the complete 100x cohort and its prepared helper on hold. The Citry
   final session reached save before failing under the maintained timeout, while
   the ten separate non-Citry diagnostics used an earlier runtime and passed.
   These results do not authorize full qualification or a normal run.
3. Re-profile before reconsidering the remaining intermediate-range or
   Events-retirement consumers. The retained profile motivated S2b and S3,
   which now remove work from that checkpoint. Exercise alternate branches
   separately as correctness cases when their shared model is defined.
   Future asynchronous adapter hooks need new readiness proof rather than an
   arbitrary network-idle wait or rendering delay.

### Deferred end-to-end design questions

The controlled second-render report and bounded 1,400-output profile above now
supply evidence for the current priority questions. The broader questions below
remain queued for explicit later work; they are not current candidates or
performance claims.

- The current report separately measures bounded server output preparation.
  Extend that separation across response transfer, HTML parsing, browser setup
  and browser CPU before describing work as duplicated across server and client.
  The current initial `Browser + subsequent requests` interval is wall-clock
  time. Script, API, socket and bootstrap work can overlap within it, and it
  also includes browser scheduling and semantic-readiness delay. It is not a
  measure of only DOM insertion or Alpine CPU, so raw differences among Citry,
  Vue and React cannot attribute the difference to DOM or Alpine without
  equivalent workload contracts and CPU attribution.
- Evaluate whether versioned backend or compiler output can precompute bounded
  frontend setup, such as ownership, route or binding metadata. Account for the
  added server CPU, payload, validation, compatibility and dynamic fallback
  rather than treating shifted work as removed work.
- Consider selective expression traversal or server-provided references for
  directive-bearing nodes. Preserve dynamic and user-authored DOM, Alpine
  scopes and magics, mutations, CSP behavior and an exact fallback for inputs
  that cannot be certified.
- Keep structured template/value responses and explicit DOM operations as
  distinct protocol designs. Both may reduce browser parsing or matching, but
  can increase server preparation, payload, validation and recovery work. Any
  comparison must include the full response lifecycle and compatibility path.
- Measure Alpine directive traversal, proxy and scope merging, effect creation,
  binding initialization and lifecycle setup before comparing its setup cost
  with Vue. Q7a measured only expression evaluator compilation: it found 16
  cold standard-runtime constructor calls, no insert misses and no supported
  CSP result. It does not rule out cost in the rest of Alpine's binding setup.
- Treat a Vue frontend as a system tradeoff rather than an automatic client
  optimization. Compare it with Citry's current Alpine contract under
  equivalent rendered behavior, server protocol, readiness, bundle and cache
  state, and report server preparation, transfer and browser CPU separately.
- Evaluate server-rendered output beyond time to interactive. Record when useful
  content first becomes visible, behavior without JavaScript, transfer size,
  hydration or initialization CPU, and server cost under equivalent behavior.
  The current readiness endpoint does not measure an earlier visible-content
  benefit and cannot establish that server rendering has no value.

## Delivery checkpoints and remaining gates

The Q2h checkpoint integrated Q1a, Q2a, Q1c, S1, Q2e, Q2f, Q2g, and Q6d.
Its exact-delivery comparison, bounded proof, focused standard and CSP checks,
three-browser native/fallback outcome, complete 11-adapter 14/140 qualification,
normal run, and standalone report were completed before S2b and S3. Its
pre-instrumentation graph report remains
`.benchmarks/runs/20260911T031252Z-72e7cd37/report.html`; the first output-
preparation refresh and current second-load refresh are recorded above.

The complete repository check profile passed every phase in 172.81 seconds on
the Q2h checkpoint before the later slot-scope correction; its retained report is
`.benchmarks/research/browser-optimization/final-gate-setup/full-report.json`.
The separate Linux mypy check passed 552 source files. The previously failing
real preflight shutdown check passed unchanged with `PYTHON_GIL=1`, which
qualifies that interpreter mode rather than changing product behavior. The
ordinary-CPython 3.14.3 distribution verifier passed source-wheel, sdist-wheel,
installed-package, and inventory checks at that checkpoint. Both wheels were
1,144,767 bytes, below the 1,146,880-byte cap. These focused results are
retained beside the full report under `final-gate-setup/`.

The locked ordinary-CPython documentation environment is prepared separately.
The documentation build passed with no guard findings, its unit suite passed
936/936, and its browser suite passed 110/110. Those lanes exercised the Q2h
checkpoint bytes before the later slot-scope correctness fix. Their logs are
under `final-gate-setup/`.

The broad Chromium integration lane on those same checkpoint bytes recorded
1,313 passes and seven failures. Six were an explicit missing generated
Tailwind CSS precondition; the documented generation command and focused
rerun then passed 6/6 without a product change. The remaining failure exposed
a raw slot-region morph ordering bug present in the frozen pre-Q2g/Q2h bytes:
Alpine saw a changed directive before Citry restored the fill route. Citry now
stamps the validated live route onto direct incoming fill roots before
morphing. The matched-root, newly added multi-root, structural-fill, and
generic non-slot outcomes passed 9/9 across
Chromium, Firefox, and WebKit. At that slot-correction checkpoint the readable
core was `f286a7be...`, its delivered companion was `bec63fec...`, and the
standard/CSP Events assets were `7eabba03...` and `5d86f425...`. Failure and
qualification evidence is in
`final-gate-setup/slot-scope-diagnostic/` and
`final-gate-setup/slot-scope-fix-validation.json`. The pre-instrumentation
graph report measured the earlier Q2h bytes; this correctness-only helper is after the
adoption-plan return used by that benchmark path.

The final broad Chromium run against the corrected core passed 1,320/1,320 in
99.80 seconds. The final ordinary-CPython 3.14.3 distribution verifier checked
the source wheel and rebuilt the sdist into a wheel. Both wheels had identical
contents, each was 1,145,134 bytes with 178 members, below the 1,146,880-byte
cap, and both installed-package smokes passed. The source wheel SHA-256 is
`1199e7d6...`; retained logs are
`final-gate-setup/chromium-integration-final.log` and
`final-gate-setup/distribution-verify-slot-correctness.log`. The earlier full
repository and documentation suites cover the pre-correction Q2h checkpoint;
the client build checks, payload checks, focused three-browser outcomes, broad
Chromium lane, and distribution verification cover the corrected browser
runtime. Those checkpoint delivery gates are complete.

The combined S2b/S3 client build then passed all 21 generation and canary checks.
Its payload pairs are 608,656 raw / 139,493 gzip-9 bytes for standard and
626,482 / 143,218 for CSP, within the narrowly revised current budgets. The
final maintained assets are readable core `fc4bea3f...`, delivered core
`3992ed57...`, standard Events `2b80fe83...`, CSP Events `d5937fd3...`, and
unchanged i18n `9602045a...`. The bounded combined browser matrix passed 225
unique Chromium cases. Its selected Firefox/WebKit run passed 151/152 at first;
the sole spaced-text form observation then passed its exact rerun and both
core/Events isolation combinations, so it was retained as a nonreproducible
test observation rather than a runtime failure. Evidence is in
`.benchmarks/research/browser-optimization/s2-post-start-lifecycle-coalescing/final-combined-validation.json`.

The final ordinary-CPython 3.14.3 distribution verifier checked the source
wheel and rebuilt the sdist into a wheel. Both wheels had identical contents,
each was 1,148,133 bytes with 178 members, below the revised 1,150,976-byte
cap, and both installed-package smokes passed. Its retained success log and
command provenance are under
`.benchmarks/research/browser-optimization/final-series-refresh/`. The final
runtime-only clone, qualification, and normal run are recorded in the current
checkpoint above. These checks close the current S2b/S3 delivery gates without
repeating the earlier repository and documentation suites.

Keep the full 100x qualification and normal cohort on hold and retain the
10-second timeout. The final bounded Citry session reached save before timing
out; it did not retry or run insert, reorder, remove, or probe. Preserve compact
failures and raw measurements; do not delete other evidence or builds as
cleanup. The separate earlier frozen-build diagnostic passed all ten operations
for every non-Citry adapter, but its one sequential Chromium observation per
operation is feasibility evidence only and does not replace the held
qualification.

## Experiment queue

The IDs below remain stable as evidence accumulates. Work begins with profiling
on the canonical nested page. Re-profile when an accepted result removes the
cost that motivated a later candidate.

| ID | Candidate and hypothesis | Status, evidence, and decision requirement | Correctness and API risk |
| --- | --- | --- | --- |
| Q1a | Separate repeated relationship-closure work from broader DOM matching, then test plan-local closure reuse. `physicalPlanningMatches` rebuilds a pooled map and array for each range token during planner updates, while ordinary matched and unmatched ancestor checks scan `ordinaryPairs` per ancestor. The accepted change adds a monotonic-input checkpoint around the two closure call sites; it does not add a global index. | Frozen build `0c9a4e...`, `canonical-project-v1`, Chromium, 140 outputs, fresh contexts, one warmup, ABBAAB order with three control and three candidate contexts, standard runtime, and no profiler or tracer in timed contexts. Exact semantic state and zero errors passed for all 24 observations. Control to candidate medians: initial 196.8 to 198.7 ms (+1.0%); select 616.5 to 515.9 ms (-16.3%); insert 711.9 to 615.2 ms (-13.6%); reorder 841.9 to 541.1 ms (-35.7%). Observer calls for select/insert/reorder fell from 156/156/157 closure recomputations to 3/3/3 and from 48,664/48,664/49,290 direct-child calls to 1,540/1,540/1,550. Earlier direct profiling found a 132.3 ms inclusive closure median for 140 insert, containing 120.8 ms recompute and 99.7 ms exclusive direct-child work; nested times are not added. All values, runtime hashes, and the compressed CPU profile are under `.benchmarks/research/browser-optimization/q1a-canonical-profile/`; timed observations are in `candidate-ab-observations.json`. | **Adopted.** The production implementation matches the measured candidate's behavior; its only source difference is explanatory commentary. It passed 30 focused checks across Chromium, Firefox, and WebKit, followed by independent technical and prose review. Three observations per variant bound the timing evidence, and the variable candidate reorder observations include 775.2 ms even though the median fell. The measured core hashes are control `66a18577...` and candidate `9f884700...`; Events stayed `1b104a18...`. Preserve accepted and rejected ownership paths, ordering, duplicates, nested ranges, and invalidation after hooks, awaits, external edits, or any change to the ordinary-pair input. |
| Q1b | Build ordered patch, insert, remove, move-range, and preserve-range operations while ownership and correspondence are accepted, then execute them without a second matching walk. | **Source-reviewed and deferred.** Q1c removes the canonical ordinary-simulation work that motivated this idea, and no current profile isolates executable-plan overhead on the remaining fallback shapes. Re-profile a real fallback workload before reconsidering it. | Carry anchors and landed-node mappings. Recheck after awaits; replan or fall back after hooks, newer responses, or external edits. Qualify ignores, fills, mirrors, nested stationary and portable ranges, teleports, cancellation, and partial failure. |
| Q1c | Bypass ordinary planning for a nested range when the accepted ownership shape proves there is no ignore barrier and no case requiring ordinary correspondence simulation. | Accepted Q2 core `59395393...` was compared with candidate core `765bd95c...`; the candidate Events runtime was `4ca1e85a...`. The frozen `canonical-project-v1` page used Chromium at 140 outputs, fresh contexts, one control warmup, control/candidate/candidate/control/control/candidate order with three contexts per variant, and no profiler or tracer. All 24 exact semantic comparisons passed with no browser errors. Control to candidate medians: initial 197.3 to 197.4 ms (+0.1%, noise), select 334.5 to 171.9 ms (-48.6%), insert 336.2 to 182.0 ms (-45.9%), and reorder 313.3 to 151.5 ms (-51.6%). Evidence: `.benchmarks/research/browser-optimization/q1c-no-barrier-planning/ab-observations.json`, `ab-summary.json`, and `candidate-runtime-manifest.json`. | **Adopted.** The production core `4b423dfe...` adds the reviewed conservative inherited-key guard and passed its complete component-range matrix plus selected duplicate, mirror, ignore, prepared-placement, and teleported-fill outcomes across Chromium, Firefox, and WebKit. The post-planning probe corrected a wrong-endpoint `candidateSlotMatches` assumption. The accepted fallback recognizes only a fully verified fill backlink; it is not a general teleport relaxation. Preserve the generic planner for custom keys, barriers, ambiguous placements, malformed caps, preparation changes, and any unsupported fill, slot, mirror, or teleport shape. |
| Q2a | Replace the recursive boundary scanner with a comment-only `TreeWalker`, then regroup comments by their direct parent so pair validation and emitted order match the existing parent-first scan. | Candidate core `c91ef6...` was measured against control `45ebb12...`, which includes accepted Q1a; Events stayed `1b104a18...`. The frozen `canonical-project-v1` page used Chromium at 140 outputs, fresh contexts, one control warmup, ABBAAB order with three contexts per variant, and no profiler or tracer in timed contexts. Control to candidate medians: initial 198.3 to 197.2 ms (-0.6%, noise), select 515.2 to 336.5 ms (-34.7%), insert 625.9 to 336.7 ms (-46.2%), and reorder 526.0 to 316.5 ms (-39.8%). Every candidate update observation was below every corresponding control observation. Final observations and hashes: `.benchmarks/research/browser-optimization/q2a-treewalker/ab-observations.json`, `ab-summary.json`, and `runtime-manifest.json`. | **Adopted.** Nineteen differential cases matched both the legacy result and an explicit expected outcome in `differential-results.json`, followed by the complete component-range suite and focused manifest, ownership, and prepared-placement checks across Chromium, Firefox, and WebKit. The first fixture set failed to exercise `p1` because incorrect `g1` field indexes generated malformed `p1` comments that were silently ignored; this was corrected before final evidence. A real mixed-realm falsifier then showed that an owner-document walker entered a foreign-realm element which the legacy realm-sensitive `instanceof Element` gate excluded. The candidate gained the matching ancestor guard and the final-byte A/B was repeated. The failure is preserved in `realm-falsifier-before-fix.log`; the earlier candidate measurements remain separately labeled `*-pre-realm-guard.json`. Preserve error precedence, parent-first closing-cap order, boundary intervals, template exclusion, foreign realms, documents and fragments, namespaces, duplicate and mirrored identities, and malformed-cap diagnostics. |
| S1 | Coalesce repeated global lifecycle reconciliation across unchanged component roots during owned Alpine startup. The candidate uses a startup-only mutation observer and reuses only a completed pass whose registered caps, active roots, and current boundary remain in the observed document; a reused boundary still isolates its own root before callbacks flush. | Eligibility found 154 of 177 global reconciliations and 104.2 of 111.5 ms inclusive time inside `alpineStarting` on one canonical 140-output load. The controlled comparison used exact Q2 core `59395393...` and candidate `de402e2f...`, identical Events `1b104a18...`, Chromium, fresh contexts, one control warmup per count, and control/candidate/candidate/control/control/candidate order. All 24 observations passed the semantic oracle with no errors. Initial medians were 46.9 to 43.5 ms (-7.2%) at 14 outputs and 222.0 to 103.9 ms (-53.2%) at 140; insert was 60.2 to 59.7 ms (-0.8%) and 361.5 to 362.5 ms (+0.3%). Evidence: `.benchmarks/research/browser-optimization/s1-startup-coalescing/`. | **Adopted and integrated.** The integrated Q1c plus S1 core is `acd7f30b...`. Ten targeted lifecycle outcomes passed in Chromium, Firefox, and WebKit, for 30/30 final cases. Removing relevant-DOM invalidation makes the later-boundary mutation case fail before the unconditional after-start pass. A registered range moved to a shadow root retained the supported outcome and recorded observed-tree eligibility as false with the generic global path; the fixture's first boundary also lacked a completed pass, so removing only that eligibility predicate was non-distinguishing. The `afterStart` failure case proves the startup observer disconnects. The combined 11-adapter checkpoint passed 418 measurements and 242 fault cases in runs `20260910T231232Z-f6ffbd3c` and `20260910T230834Z-83780ad9`; that cohort does not isolate S1. Preserve provider and hold order, non-boundary globals, the final global pass, current-root pre-flush isolation, scheduled-pass fallback, and conservative fallback for a registered cap or active root outside the observed document. Three timing samples per variant and one Chromium machine bound the gain claim. |
| S2 | Reuse one completed global lifecycle reconciliation across a proven synchronous post-start boundary batch while retaining the already queued final pass. | **S2a was rejected before timing; S2b was adopted.** The whole-tree S2a guard admitted no canonical boundary because 1,300 disconnected expected-retirement records were outside the next reconciliation's read set. S2b instead proves the physical alternatives, recursive parents, and active roots that the pending full reconciliation can read. Its 1,400-output clear-filter proof ran one boundary full pass, 1,299 local reuses, and the queued final full pass. The balanced Chromium comparison used frozen core `bec63fec...` against candidate `3992ed57...`, identical Events `7eabba03...`, one excluded control warmup per count, C-A-A-C-C-A order, and three contexts per variant. All 72 initial/select/filter/clear-filter/insert/reorder operations passed exact semantics. Clear-filter fell from 205.1 to 113.9 ms at 140 (-44.5%) and from 11,587.3 to 1,684.5 ms at 1,400 (-85.5%), with complete separation. Select, filter, insert, and reorder overlapped at both counts. Initial increased from 99.8 to 102.3 ms at 140 and from 813.2 to 840.6 ms at 1,400, also with separated distributions. Evidence: `.benchmarks/research/browser-optimization/s2-post-start-lifecycle-coalescing/`. | The focused candidate passed two mutation and referenced-tree cases; removing either guard failed its intended synchronous provider observation. One hundred existing Chromium lifecycle, slot, range, and atomic-morph tests passed after excluding one independently reproduced console-callback test harness stall; a deferred-handle equivalent passed with control and candidate. **Accepted for the isolated clear-filter improvement with the measured initial and 140 insert costs retained.** Preserve the first full pass, queued final pass, provider and root order, same-task lifetime, error poisoning, relevant mutation and logical scheduling invalidation, recursive referenced-parent proof, active-root compatibility, and fallback for detached, shadow, foreign, corrupt, reentrant, morph, and adoption states. Three observations per variant on one Chromium machine do not establish tail or general-workload effects. |
| S3 | Replace repeated document-wide Events-manifest discovery during context decoration and boundary initialization with an Events-owned pending queue. Keep one boot catch-up scan for a late runtime and keep the explicit full replay API. | **Accepted for production integration.** The earlier 1,400-output initial profile placed 139.166 ms of `querySelectorAll` self time under the Events manifest consumer. The controlled comparison used the same delivered core `bec63fec...` for both variants and changed standard Events from `7eabba03...` to `2b80fe83...`. It ran Chromium at 140 and 1,400 outputs with one excluded control warmup per count and C-A-A-C-C-A order, three contexts per variant. All 72 stored initial/select/filter/clear-filter/insert/reorder operations passed exact semantics with no page errors and exact route hits. At 1,400 outputs, initial fell from 816.0 to 672.8 ms (-17.5%), and all three candidate values were below every control. At 140, initial was 97.6 to 95.7 ms; all six 140 distributions overlapped. Every 1,400 action distribution also overlapped, so no update-path gain is claimed. Evidence: `.benchmarks/research/browser-optimization/s3-events-pending-discovery/`. | The standard and CSP Events assets each grow by 1,634 raw bytes; gzip-9 grows by 446 and 442 bytes. The focused source passed 75 affected Chromium cases and 34 Firefox/WebKit standard/CSP cases. Removing only the queued-tag selector recheck fails the reentrant marker-revocation case. Preserve graph-before-Events provider order, graph revision pairing, transaction rollback, same-task discovery, text completion, type and marker changes, cloned-tag identity, late-runtime catch-up, explicit replay, external insertions, and processed-tag idempotence. This is one local Chromium comparison with three values per variant and count. The 40-second diagnostic cap does not change the maintained 10-second action limit; all six 1,400 clear-filter rows and one insert row per variant remain maintained timeouts. |
| Q2b | Retain or reuse validated ordering and containment relationships so later operations avoid repeated live-DOM comparisons. | **Reopened by 100x attribution; no candidate yet.** One exact-runtime 1,400-output insert profile attributed 20,520.820 of 24,072.146 sampled milliseconds to `compareDocumentPosition` itself. Recorded callers were key-map containment (8,409.296 ms), stationary-range checks (6,185.358 ms), intermediate-range equivalence (3,731.762 ms), and Events retirement (2,073.841 ms). This locates a scaling target but does not select a persistent index, caching scope, or invalidation design. `activeCommittedLink` and `directLogicalChildren` still span mutable ownership states, so external DOM moves, mirrors, hooks, stabilization, and cancellation make a broad retained index risky. Evidence: `.benchmarks/research/browser-optimization/canonical-1400-feasibility/profile-findings.md`. | Framework operations must update any retained relationship. External mutation dirties the affected scope and forces validation or scanning. Hooks, moves, mirrors, shadow/adopted nodes, and cancellation must not leave stale entries. Preserve exact ordering and containment semantics for malformed, mirrored, slotted, and externally moved ranges. One cold profile supplies attribution only; an isolated candidate needs differential correctness and controlled timing. |
| Q2c | Combine excluded, canonical, and runtime-mirror commit scans. | **Deferred after attribution.** The older corrected 140-output profile placed this retirement and commit-scan target at about 1.5 ms, while Q2e addressed the supported boundary scanner. The newer 1,400-output profile's 2,073.841 ms under Events `_expectRetirement` is a separate live-containment caller recorded by Q2b; it does not establish a commit-scan fusion target. Fusion would couple distinct ordering and error phases without a measured remaining target. | Preserve each scan's order, rejection behavior, and diagnostics. One malformed stream must not hide another class of error. |
| Q2d | Compare server-supplied IDs or ordinal hints with source offsets for finding boundaries. | **Source-reviewed and deferred.** Offsets and hints add payload, server construction, and browser validation, yet cannot authoritatively identify caps after contextual parsing, moves, slots, teleports, and mirrors. No current profile establishes that tradeoff. | Source offsets do not identify authoritative DOM comments after contextual parsing, slots, teleports, clones, and moves. Hints require validation and collision-safe fallback. |
| Q2e | When the requested boundary belongs directly to the scan root, start the comment-only `TreeWalker` at the opening cap and stop at the closing cap instead of walking unrelated siblings before applying containment checks. | **Adopted.** Frozen core `acd7f30b...` was compared with candidate `d2ea9f80...`; standard Events stayed `c80eb9d8...`. The `canonical-project-v1` comparison used Chromium at 140 outputs, fresh contexts, one control warmup, control/candidate/candidate/control/control/candidate order, three contexts per variant, and no profiler or tracer. All 24 observations passed exact semantics without browser errors. Control to candidate medians were initial 96.5 to 96.3 ms (-0.2%, noise), select 188.7 to 156.8 ms (-16.9%), insert 171.8 to 166.1 ms (-3.3%), and reorder 152.3 to 152.7 ms (+0.3%, noise). Every candidate insert was below every control insert. Twenty-two differential cases matched legacy and explicit expected outcomes. Production core `4d20b483...` differs from the measured behavior only by explanatory comments and passed the focused range-scan outcomes in Chromium, Firefox, and WebKit. Evidence: `.benchmarks/research/browser-optimization/q2e-bounded-comment-walk/`. | Bound only a same-parent interval whose opening and closing caps were already validated against the scan root. Preserve parent-first order, descendant element traversal, realm filtering, template exclusion, malformed-cap errors, documents and fragments, namespaces, mirrors, both cap formats, and the full-root fallback for a deeper boundary. Three observations per variant and one machine bound the timing claim. |
| Q2f | Skip protected-range containment checks while Alpine builds its keyed map when Events proves that the live key callback is its exact `data-citry-key` lookup and the current ordinary element has no such key. | **Adopted and focused-qualified.** Frozen core `4d20b483...` plus standard Events `c80eb9d8...` was compared with candidate core `c9eff389...` plus Events `001f388b...`. The `canonical-project-v1` comparison used Chromium at 140 outputs, fresh contexts, one control warmup, control/candidate/candidate/control/control/candidate order, three contexts per variant, and no profiler or tracer. All 24 observations passed exact semantics with no errors. Control to candidate medians were initial 95.9 to 96.4 ms (+0.5%, noise), select 156.1 to 154.0 ms (-1.3%), insert 165.4 to 163.2 ms (-1.3%, overlapping), and reorder 158.5 to 151.2 ms (-4.6%). Diagnostic select and insert each saw 4,455 filter calls, including 3,795 empty-filter shortcuts, 262 proven-no-key shortcuts, and 398 fallbacks. The integrated readable core is `146c952a...`; Q6d generated delivery core `9e9dead9...`, standard Events `2b036794...`, and CSP Events `e9fd54f3...`. The focused key, stationary-range, slot, and sentinel outcomes passed 30/30 across Chromium, Firefox, and WebKit. The final native-method/custom-callback rerun passed 12/12, and weakening the native instance-method proof failed the exact `getAttribute` trace as expected. Evidence: `.benchmarks/research/browser-optimization/q2f-proven-no-key/`. | Apply the shortcut per element only for the private Events capability, an own matching key callback, native same-realm `getAttribute` and `hasAttribute`, no `data-citry-key`, and no temporary range marker. Custom callbacks, inherited option properties, custom or foreign-realm attribute methods, keyed nodes, and range adapters use containment. An updating hook can change a deeper element before its own map decision. Pre-load replacement of host attribute intrinsics and monkeypatching Citry-owned cap ordering methods remain outside this measured contract. |
| Q2g | Batch stationary-containment relationships within one morph phase before each synchronous filter or collapse boundary, rather than repeating live `pairContainsPair` ordering checks for the same phase-local inputs. | **Adopted and focused-qualified.** The exact-runtime 1,400-output insert profile attributed 6,185.358 sampled exclusive milliseconds to `compareDocumentPosition` below `insideStationary`. The controlled comparison used delivered control core `9e9dead9...`, candidate `91b57c61...`, unchanged standard Events `2b036794...`, Chromium, fresh contexts, one excluded control warmup per scale, and control/candidate/candidate/control/control/candidate order. All 24 observations passed exact semantics without browser errors. At 140 outputs, control-to-candidate medians were 98.0 to 96.6 ms for initial and 173.8 to 173.2 ms for insert, with overlapping distributions. At 1,400 outputs, initial was 789.0 to 792.7 ms, also overlapping, while insert fell from 23,756.2 to 17,592.7 ms (-25.9%) and every candidate observation was below every control. The proof exercised 17 optimized phases; its other 291 phases combine inputs with no possible benefit and conservative fallbacks. Production readable core `4e613c60...` and delivery core `91b57c61...` match the accepted candidate. The new non-union sibling/nested-range outcome passed in Chromium, Firefox, and WebKit, followed by 54 focused standard and CSP outcomes and 21 client checks. Evidence: `.benchmarks/research/browser-optimization/q2g-stationary-containment/`. | Build old and incoming ordinal snapshots separately only after cap discovery, use each through its synchronous filter, and discard it before collapse or callbacks can mutate the tree. Preserve the exact same-start rule and existential strict enclosure without joining overlapping windows. Foreign realms, disconnected or malformed ranges, and supported ordering-method overrides use the complete phase's live predicate. Pre-load replacement of host ordering and walker intrinsics remains outside this measured environment. Three observations per variant on one Chromium machine support only the 1,400-output insert result; no 140-output, initial, other-action, or full-cohort gain is claimed. |
| Q2h | Build one protected-range membership predicate per pinned Alpine `keyToMap` call by sweeping same-parent siblings once, then discard it before the original key iteration returns. | **Adopted and focused-qualified.** The first ignored candidate conservatively admitted only dense Block Arrays. Its canonical 140-output insert proof optimized 4 of 4,184 keyed-map calls, covering 82 members and 4 boundaries. A reason diagnostic showed that 388 of 403 factory-present calls instead received non-Array inputs. The reviewed revision added exact same-realm native `HTMLCollection` through captured length, item, iterator, and iterator-next operations. Its proof optimized 9 calls covering 502 members and 144 boundaries; the remainder was 357 empty collections, 34 cross-parent batches, and 3 detached-endpoint batches. The exact-delivery comparison used Q2g control core `91b57c61...` with standard Events `2b036794...` and candidate core `b0d6a945...` with factory-enabled Events `7eabba03...`, one excluded control warmup per count, fresh Chromium contexts, and control/candidate/candidate/control/control/candidate order. All 24 initial and insert observations passed exact semantics, route checks, and error checks. At 140 outputs, initial medians were 95.1 to 95.8 ms and insert 171.6 to 170.2 ms, both overlapping. At 1,400 outputs, initial was 773.7 to 768.8 ms, also overlapping, while insert fell from 17,478.3 to 9,046.6 ms (-48.2%) and every candidate observation was below every control. At the Q2h performance checkpoint, production integrated the exact measured readable core `e238a1c9...`, delivered core `b0d6a945...`, standard Events `7eabba03...`, and CSP Events `5d86f425...`. The client checks passed 21/21. A maintained native and matched disabled-factory fallback outcome passed 12/12 across standard and CSP in Chromium, Firefox, and WebKit; both fallback paths produced equal positive iterator-accessor traces while preserving component and input identity, draft state, and the fresh update. Evidence: `.benchmarks/research/browser-optimization/q2h-key-map-sibling-sweep/`. | Admit only the exact own Events key capability and either an ordinary dense Block Array or a native same-realm `HTMLCollection`. Preserve native attribute, node-type, ordering, parent, sibling, cap-type, marker, and endpoint-order checks. Any custom iterator, accessor, callback, proxy, foreign realm, mixed parent, detached endpoint, or malformed cap uses the complete live filter for the whole call. Keep the snapshot local to one `keyToMap` and preserve Alpine's original `for...of` and key-callback order. Three observations per variant on one Chromium machine support only the 1,400-output insert result; select, reorder, full-cohort behavior, and other workloads remain unmeasured. |
| Q3a | Mark dynamic attributes or carry static attribute metadata so unchanged static work can be skipped. | **Source-reviewed and deferred behind a compiler capability or public opt-in.** A useful general skip needs a versioned server/compiler hint and therefore changes the build or wire capability. An internal fast path can remain compatible only for a closed framework-owned attribute set, or by re-reading every live name and value, which largely pays the existing cost. No current profile establishes a target that justifies that contract. | Define invalidation for Alpine bindings, transitions, focused controls, form properties, spreads, custom directives, and external mutations. Incoming syntax alone cannot prove that a live attribute is static. |
| Q3b | Replace or guard string comparisons with hashes or bitwise equality. | **Source-reviewed and deferred.** JavaScript bitwise operators cannot establish equality of arbitrary strings. Collision-safe hashing still reads and confirms the strings while adding computation and possibly payload, and no measured target justifies that work. | Equality must remain exact. Payload, computation, collisions, coercion, Unicode, and adversarial inputs are part of the tradeoff. |
| Q3c | Use a selective `isEqualNode` guard to skip unchanged subtrees. | **Source-reviewed and deferred behind a hook capability or public opt-in.** The guard can skip DOM comparison while Alpine and update hooks still run. Skipping descendant preparation as well requires a certified hook capability or public opt-in, and no current profile establishes that target. | DOM equality does not establish Alpine state, ownership state, form properties, listener state, or safe lifecycle omission. Do not stack the guard at every ancestor. |
| Q4a | Move a proven disposable incoming subtree instead of cloning it. | **Deferred after fresh attribution; no candidate or A/B rejection.** Against frozen build `77bd4d...`, one instrumented canonical 140-output initial/insert context and one exact-runtime CDP context all passed semantic assertions with no errors. Insert classified 146 of 160 inspected sites as provisional leaf candidates, but their clone work was only 5.1 ms exclusive in that instrumented observation, versus 11.0 ms for nested clones and 83.2 ms for morph work. This bounds the provisional leaf-only saving in that observation; wrapper overhead and one context prevent a causal or general ceiling claim. Evidence: `.benchmarks/research/browser-optimization/q4a-fresh-contents/attribution.json`. An internal exact-compatible candidate remains possible only for a freshly parsed, detached, same-document, single-consumer, uninitialized subtree that is neither mirrored nor reused. A caller promise of disposability would be a new public opt-in. | Save the source successor before consuming a node and preserve adding-hook identity and order. Check identity, listeners, Alpine markers, custom elements, templates, namespaces, form state, replacements, insert-before, and mirrors. B6's 18.6 ms live-clone diagnostic and this newer attribution are different workloads and methods; neither establishes an obtainable gain. |
| Q4b | Construct the incoming tree with `createElement` and `createElementNS`. | **Source-classified and deferred.** A general replacement belongs with a structured, versioned template protocol because ordinary construction does not reproduce arbitrary parser behavior. A small internally generated node class could be tested with a fallback. No performance result exists. | Preserve namespaces, templates, custom-element timing, parser normalization, escaping, form defaults, and lifecycle order. |
| Q5a | Bypass `Alpine.cloneNode` during preparation only for elements proven plain. | **Source-reviewed and deferred behind an interceptor capability or public opt-in.** Absence of authored directives is not a proof. Alpine runs every registered clone interceptor, then `initTree` runs init interceptors before directive handling; Citry also wraps clone preparation to preserve ambient source ancestry. Omitting these public extension paths requires an interceptor capability or explicit opt-in, unless the hooks still run and only their internals are optimized. No current profile supports that added contract. | Do not skip a data stack, bound value, Citry interceptor, inherited Alpine state, ambient clone source, or third-party extension hook. Normal live-node initialization still runs. |
| Q5b | Use stable output keys throughout the canonical adapters. | **Folded into the new scenario baseline.** This supports equivalent native rendering and identity assertions; it is not an isolated Citry optimization and has no attributed gain. Historical flat-board runs remain the reference for their old unkeyed shape. | Keys must be stable across filter and reorder, unique across replicas, and new inserts must receive unique keys. Do not attribute append or B6 clone behavior to keys. |
| Q6a | Send a structured template/value protocol with static template IDs and changed values. | **Deferred protocol/API design outside this runtime pass.** It needs explicit payload, server-construction, browser-work, compatibility, version-failure, and maintenance evidence before implementation. | Define arbitrary HTML, slots, mirrors, ownership, client-owned attributes, external edits, escaping, stale responses, and template-version mismatch. |
| Q6b | Send an explicit operation protocol rather than HTML. | **Deferred protocol/API design outside this runtime pass.** Keep it distinct from Q6a and require explicit tradeoff evidence beyond latency before implementation. | Operations require validated targets and ordering, stale-anchor recovery, cancellation, partial-failure behavior, backwards compatibility, and an escape path for arbitrary markup. |
| Q6c | Calibrate semantic readiness against actual complete state. | **Implemented and qualified for this cohort.** All eleven adapters passed the exact action sequence and all 11 fault cases at 14 and 140 outputs. The endpoint timestamp precedes synchronous semantic capture; capture cost is reported as `semantic_observer_ms`. | Keep each framework's real ready endpoint and the resource-completion check. `getComputedStyle` in capture can force style or layout and perturb the event loop across adapters; the mark represents committed semantic DOM rather than paint. Future asynchronous adapter hooks need their own proof. |
| Q6d | Ship validated minified Citry production runtimes. | **Full-minification latency candidate rejected; whitespace-only transfer candidate adopted and fully qualified.** Pinned esbuild 0.28.2 transformed frozen build `77bd4d...` with ES2020, inline legal comments, no property mangling, preserved banners, and unchanged URLs. Full minification with `keepNames` reduced core plus standard Events by 52.0% raw, 31.6% gzip, and 27.0% Brotli; CSP reductions were 51.7%, 31.2%, and 26.7%. Six route-verified Chromium cases passed and exercised all three assets overall; the late catch-up case used candidate core with maintained Events because its delayed route took precedence. The balanced 14/140 comparison used one control warmup per count, three contexts per variant, initial and insert, and no profiler or tracer. All 24 observations passed exact semantics with no errors. Control to candidate medians were 41.6 to 42.0 ms for 14 initial, 40.0 to 43.5 for 14 insert, 104.2 to 99.8 for 140 initial, and 172.1 to 179.1 for 140 insert. All three 140 candidate inserts, 178.8 to 182.5 ms, exceeded all controls, 171.8 to 173.9 ms, so full minification is rejected for latency. Its name-preserving transform injects a helper and hundreds of name-restoration calls, a plausible but unprofiled mechanism. The whitespace-only follow-up disables identifier and syntax transforms and avoids that helper. It reduces the standard pair by 28.0% raw, 20.9% gzip, and 18.1% Brotli, and the CSP pair by 28.2%, 20.7%, and 18.0%. Its matching focused suite passed 6/6. Its 24/24 semantic A/B observations gave control to candidate medians of 41.8 to 40.9 ms for 14 initial (-2.2%), 37.0 to 37.1 for 14 insert (+0.3%), 103.9 to 96.0 for 140 initial (-7.6%), and 174.3 to 175.5 for 140 insert (+0.7%). The overlapping initial distributions and unchanged insert do not establish a latency gain. At the Q6d packaging checkpoint, production retained readable core `4d20b483...` and generated delivery core `5c1e26f7...`, standard Events `b64e9857...`, and CSP Events `94a81e6e...`. Those delivered pairs measured 588,044 raw / 135,306 gzip bytes and 605,870 raw / 139,036 gzip bytes. Exact generation, central route/inline/fragment/SRI delivery, workspace source-to-destination mapping, and a 1,138,582-byte installed wheel passed focused checks. The measured artifact supports the revised 1,146,880-byte wheel cap, leaving 8,298 bytes for metadata and small source movement. The final Q2f-integrated delivery hashes are recorded in its row; full 11-adapter qualification then passed 418/418 observations, 242/242 fault cases, and 418/418 size records in run `20260911T010000Z-c7392f38`. Research evidence: `.benchmarks/research/browser-optimization/q6d-minification/`. | Keep readable maintained `citry.js`, generated delivery bytes, and the existing public URL distinct. Retain legal comments, generated banners, diagnostic names, property names, public globals, standard and CSP behavior, exact-build canaries, stack diagnostics, extension entry points, and reproducible bytes. Minification occurs after exact Alpine source instrumentation. `Function.prototype.toString()` output can still change. Production emits no source map; browser stacks refer to generated bytes and the unserved readable source remains packaged for manual inspection. No public asset-selection flag or runtime minifier was added. Judge the whitespace candidate by its transfer result; no further minifier variant or latency claim follows without a new mechanism. |
| Q6e | Retire consumed framework manifest scripts and emit the Events bootstrap only when required. | **Source-audited and deferred.** No current-compatible JSON retirement point exists. Core startup and catch-up rescan every connected JSON tag and fan each element through registered providers; Events replays retained manifests during evaluation, boundary initialization, and startup, and reads the preceding graph for revision pairing. Dependency tags can launch asynchronous graph-linked assets, and public provider callbacks receive element identity. Retirement therefore needs an explicit consumer-close and replay API. In the archived `0c9a4e...` 140-output session, 18 updates grew script elements from 7 to 97 and HTML by 1,414,033 bytes. Added script markup totaled 1,409,044 bytes: graph 1,299,352; dependency 57,726; `_EVENTS_BOOTSTRAP_STUB` 35,748; Events 11,574; and inert fragment preloader 4,644. An owned inert-preloader marker or bootstrap self-removal could target about 258 or 1,986 DOM bytes per update, respectively, but neither changes response bytes and neither has isolated latency evidence. | Processing a graph or dependency tag is not proof that every consumer has finished. Preserve late-provider and Events replay, revision pairing, asynchronous activation, rollback, streaming and partial-tag behavior, synchronous external insertion, cloned-tag identity, repeated intentional user scripts, dependency order, and CSP behavior. Keep the narrow preloader and bootstrap ideas separate; do not broadly remove retained JSON without a consumer-lifecycle contract. |
| Q7a | Reduce Alpine expression parsing or compilation overhead through precompiled expressions, a versioned function registry, or bounded batch compilation. | **Evaluated and deferred; no candidate.** On standard Alpine 3.17.1, one instrumented context per count and variant found exactly 16 cache misses, unique strings, and constructor calls during initial readiness at both 14 and 140 outputs. Insert had zero misses and all expressions hit the existing cache. Constructor work totaled 0.3 ms at 14 and fell below `performance.now()` resolution at 140; no raw-evaluator call occurred in these canonical intervals. Each cell has one observation, so elapsed differences do not measure overhead or a latency effect. Four standard contexts passed exact semantics without browser errors. The four strict-CSP requests failed server-side validation before a document or runtime asset: the canonical fixture has one raw `Page` script and five multi-statement `ProjectTabs` click expressions. They provide no CSP evaluator evidence, and the fixture was not rewritten. Evidence: `.benchmarks/research/browser-optimization/q7a-expression-evaluation/`. | A named function attribute still compiles a string name lookup through the normal evaluator. A registry or direct-function path must preserve merged reactive scope and `this`, free-variable lookup, assignments, magics, automatic function evaluation, parameters, async results and errors, dynamic fallback, CSP parser restrictions, diagnostics, escaping, and injection resistance. No standard candidate is justified by the measured compile work, and no CSP decision can be made from the incompatible fixture. |
