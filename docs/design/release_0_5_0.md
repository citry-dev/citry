# Citry 0.5.0 integration and release preparation

The user authorized this integration on 9 September 2026: copy the optimization
work into review without committing there, preserve Preview, reconcile conflicts,
apply the six open Dependabot updates and Ruff issue #101, fix issue #107, then
prepare release metadata and a pull request based on current main. Publication
and merging the PR are separate later actions.

## Recorded inputs

- Review HEAD: `b3772513079dfc52408dff756bbab0202253783b`.
- Performance HEAD: `a7b0a4ef6e167a68d8a595f79a78c7a3881838d8`, including its
  uncommitted documentation and chart follow-ups.
- Performance delta base: `1294c51d417b95ab9f31bdf2f639d5d985a23995`.
- Transfer audit and byte backups: `/tmp/citry-release-transfer/manifest.json` and
  sibling `base`, `source`, `destination` directories; initial review hashes and
  index patch are retained locally. These are recovery aids, not release inputs.

## Integration progress

- Copied 821 files with no destination conflict; reconciled the README and docs
  navigation automatically. Combined both changelog sections explicitly.
- Serializer uses the performance implementation's iterative traversal and
  explicit transparent placements. Independent review confirmed that this
  addresses the destination's duplicate-cap bug without its ancestor-ID tracking.
  Destination regression tests remain part of the combined qualification.
- Applied Dependabot manifest/workflow changes from #94, #98, #100, #102, #103 and
  #104; regenerated combined lockfiles from their combined dependency updates.
- Selected Ruff 0.16.6 at `22f65a2ab5052990503985c7c794de37598d531e`.
  Upstream adds `stacker`, requires Rust 1.96, changes call-expression ranges,
  and separates semantic syntax validation from parsing. Preserve Citry's
  duplicate-keyword rejection and qualify browser compilation and deep inputs.
- Issue #107 reproduced a constant proxy reaching the dynamic HTML-tag regular
  expression. Fixed after dependency integration, with template/Python parity and
  sibling exact-value boundary coverage.

## Qualification and promotion

Run focused regressions, the repository gate, browser/Preview/simple integration,
distribution and browser-runtime qualification, and a fresh publication benchmark
for the upgraded dependency set. Record actual results and limitations here.
Create a named-file promotion manifest against fetched main; preserve main-only
paths and reconcile independent changes. Commit only in the PR worktree. Review
HEAD and its index must remain unchanged, keeping unread changes visible.

## Release integration results

The combined review tree passes `scripts/check.py --profile full`, including
Rust formatting, Clippy and tests, Python lint/type checks and tests, JavaScript
checks, protocol checks and repository validators. Citry browser tests passed
in Chromium (558 tests), Firefox and WebKit (1,111 tests with four skips).
UI/docs Chromium checks passed after retaining UI's original Citry minimum.
The strict documentation build passed.

- Citry is 0.5.0 and pins Core 1.7.0; UI is 0.2.1, LSP is 0.1.4 and the
  VS Code extension is 0.1.3.
- UI, LSP and examples retain minimum Citry versions without upper bounds.
  The LSP accepts later versions while checking catalog and protocol schemas.
  The owning changelogs and distribution verifiers reflect these contracts.
- Issue #107 was caused by nested constant proxies reaching dynamic tag
  validation. Unwrapping now reaches the original value and detects cycles.
  Cache keys retain their existing one-layer-at-a-time encoding. The combined
  regression run for constants, dynamic tags, caches, Preview, simple components
  and transparent ownership passed 281 tests.
- Ruff 0.16.6 retains duplicate-keyword rejection through shared checked parsing,
  including formatting projections. Native subprocess probes at depths 50 and
  1,000 passed for calls, unary expressions, lambdas and powers. These probes do
  not establish arbitrary-depth or WebAssembly behavior.
- All 31 Alpine CSP qualification cases have unchanged results under 3.17.1.
  Client, UI and playground assets were rebuilt from the upgraded dependencies.
- Core's release wheels and source archive passed inspection and install smoke
  tests; the source archive rebuilt outside the checkout with Rust 1.96.0.
  Citry, UI and LSP wheel/source qualification and VS Code VSIX inspection passed.
  Actual Pyodide build/runtime qualification remains for the candidate workflow;
  native checks do not substitute for that platform qualification.

Independent technical review checked the Ruff migration, constant/cycle handling,
cache key compatibility, Preview/simple composition and minimum-version checks.
A separate prose pass checked compatibility statements and user-facing release
notes. Its reported corrections were applied and rechecked.

## Publication benchmark after dependency updates

The 10 September run uses the inspected Core 1.7.0 CPython 3.14 release wheel,
whose native module SHA-256 is
`a4f2430612277e22e99a657f43902feb8198a6cec471eb01180e811a791c9500`.
Ten balanced blocks retain six initial and 80 warmed outputs per worker.
The report and ownership captures are retained under
`benchmarks/results/publication-20260910-release-0.5.0.*`.

| Configuration | First render, ms | Second render, ms | Warmed render, ms |
| --- | ---: | ---: | ---: |
| Django | 19.675 | 11.791 | 11.671 |
| django-components | 68.273 | 48.114 | 54.692 |
| Jinja2 | 66.096 | 6.765 | 7.211 |
| Citry with simple and pure | 64.192 | 25.023 | 24.624 |

Both publication PNGs show only optimized Citry, with an asterisked
performance-guide URL and clickable links below the images. The raw report retains ordinary Citry as a control (33.771 ms
warmed). Its paired median saving from opting three classes into simple mode is
9.091 ms, or 26.93%. Different engines produce different output and perform
different framework work. The earlier 9 September report remains unchanged.

## PR scope reconciliation

The final manifest leaves all 43 `benchmarks/agent_usage/` paths in review only.
They are unrelated, untracked agent-evaluation work: the optimization transfer
manifest and performance-branch history contain no changes in that directory.
Treating its initial performance snapshot as an upstream base would copy only
20 files and leave an incomplete harness. Independent review confirmed the
exclusion. Existing benchmark source-hash inventories remain historical evidence;
they do not make the unrelated harness a release dependency.

## Final PR checkout validation

The assembled `release/citry-0.5.0` checkout passes all 19 phases of the full
repository gate (117.3 seconds), using its own Python environment and
native build. The strict docs build and a fresh Citry wheel/source qualification
also pass in that checkout. The final chart filename required a formatting fix;
the subsequent complete gate passed. Independent review checked the final
manifest and benchmark calculations.

The PR changes 974 files, including retained experiment scripts and measurements.
Five exact Git whitespace exceptions preserve captured patches, test logs and
generated SVG bytes. The staged diff check passes. The review branch remains at
its recorded HEAD with an empty index; the release commit is made only in the
PR worktree. Publication and cross-platform candidate qualification remain later
release steps.

## Release scope cleanup after review

The performance probes, candidate implementations and raw captures are retained
on [the performance research branch](https://github.com/citry-dev/citry/tree/research/performance-render-20260910).
They are excluded from the release PR, including its replacement commit history.
Main keeps the implementation, tests, design documents, published chart and a
compact measurement summary linked to the archived evidence. Design documents
and assets use the `performance_render_*` prefix. Earlier file counts above
record the initial promotion checkpoint before this cleanup.
