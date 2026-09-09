# Preparing repeat-render changes for review and a pull request

Experiment scripts, candidates and raw captures are retained on the
[performance research branch](https://github.com/citry-dev/citry/tree/research/performance-render-20260910).
Historical paths describe the original checkout; the archive guide records
the renames.

This records the preparation checkpoint before integration was authorized.
For subsequent integration and qualification, see
[Citry 0.5.0 release preparation](release_0_5_0.md).

At that checkpoint, the work was preparation only.
No files had been copied into the review worktree, no index or branch pointer
had been changed, and no pull request, push or release had been created.
The chart edits and this note were uncommitted in the performance
worktree. The graph displays only optimized `Citry*`, with an asterisked
performance-guide URL in the image and clickable links below both published
copies. The original measurements, including the ordinary control, remain intact.

## Define the optimization delta

The performance worktree is `/Users/mac/repos/citry-perf-repeat`, on
`perf/repeat-render-20260908`, with committed HEAD
`a7b0a4ef6e167a68d8a595f79a78c7a3881838d8`.
The pre-optimization snapshot is
`1294c51d417b95ab9f31bdf2f639d5d985a23995`. Use that snapshot as the comparison
base, including subsequent uncommitted chart edits and this preparation note.
Comparing directly with `review` would include unrelated work captured in the
initial snapshot.

The destination is `/Users/mac/repos/citry`, on `review` at
`b3772513079dfc52408dff756bbab0202253783b`. Its existing unread changes must
remain present and unread. Copying the performance changes there must leave
`review` HEAD and its staged content unchanged.

At this inspection, local `main` is
`fb9e304c864badfa6175a6cf1a8d9ec254188ccb`, the locally recorded `origin/main`
is `caf296706c55b00d63109b011e0429a4413bbfa3`, and `reviewed-baseline` is
`f400050aef38473e98670bb206abd69c6de07acf`. No fetch was performed. Revalidate
these references and the destination files immediately before any transfer.

## File counts

Relative to the pre-optimization snapshot, including this note and the current
uncommitted chart changes (the preparation checkpoint, excluding subsequent
devlog story and graph artifacts), there are **821 changed files and one changed Git
submodule pointer**, or 822 paths. Of the files, 768 are new and 53 are modified;
none are deleted. Dependency upgrades listed below are planned and are not yet
included in these counts. These counts describe this work, not every unread file in
`review` and not a direct comparison with today's `main`.

| Area | Changed files |
| --- | ---: |
| Benchmark harnesses, experiments and retained results | 740 |
| Python Citry | 41 (22 implementation, 19 tests) |
| Python Citry Core | 6 (3 implementation/stubs, 2 tests, 1 agent guide) |
| Rust crates | 11 |
| Design, research and other documentation | 13 |
| Docs site | 6 |
| Root manifests, lockfile, README and changelog | 4 |
| Total files | 821 |

The separate `third_party/rust/ruff` pointer records
`5b48a040974781ba90b47c8df628f8fd9b6c95dd`. Both worktrees already have that
revision checked out. It was recorded to preserve the original working Ruff
revision; do not treat it as a new optimization or copy the submodule directory.
The 740 benchmark files include rejected prototypes as well as retained evidence;
their presence does not activate them in the runtime.

## Reconcile four destination files

For 49 existing files, the destination bytes still match the snapshot. Another
768 files, including this note, are new relative to the snapshot and absent from
the destination. Four existing files changed independently in `review`:

| File | Review changes to preserve | Performance changes to incorporate |
| --- | --- | --- |
| `CHANGELOG.md` | Component-preview and standalone-template fix entries | Simple API, performance and rendering-correctness entries |
| `README.md` | Coding-agent documentation section | Updated benchmark image description, results and optimization footnote |
| `docs_site/content/_nav.yml` | AI-agent and component-preview links | Simple-component guide link |
| `packages/py/citry/citry/serialize.py` | Transparent-loop/slot boundary correction | Iterative traversal and explicit whole-output placement selection |

The first three need both sets of content. The serializer needs a semantic
review: the performance implementation identifies whole transparent outputs
explicitly, while the destination correction infers them from render identities.
Preserve the destination's regression coverage and verify it against the combined
implementation. Do not overwrite the four files with whole source copies.

## Packages to release

| Distribution | Current version | Required preparation |
| --- | --- | --- |
| `citry-core` | 1.6.1 | Choose a new version, add its owning changelog entry, rebuild and qualify native and browser wheels containing native ownership storage and the expression changes |
| `citry` | 0.4.6 | Bump to **0.5.0**, update its exact Core dependency from `citry-core==1.6.1` to the selected Core release, retain its new changelog entries and qualify the wheel/source distribution |

The new `citry_ownership` Rust crate has `publish = false`; it ships within Core
and needs no independent package release. The performance delta changes no
Citry UI, LSP, VS Code, Pygments, JavaScript-client or browser-protocol source.
Those packages do not need releases solely for the performance work. The added
Dependabot scope below changes that release assessment for LSP and VS Code.
Deploy the updated documentation separately.

Core's Unreleased changelog is currently empty. Package versions, Citry's exact
Core pin and `uv.lock` have not yet been updated for these releases. Native
ownership has a compatibility fallback when an older Core lacks it, but that
older Core does not provide the native performance result. Release the measured
capabilities together rather than relying on that fallback.

Follow the release procedure in [codebase.md](../codebase.md#current-release-process):
refresh the lockfile after changing Python metadata, qualify the selected package
pair, and publish and verify Core before Citry. Prepare compatible browser-runtime
coordinates, but keep deployed playground pins on public packages until the new
artifacts exist and have been verified. The user selected Citry **0.5.0**; the
Core version remains to be selected.
This note does not authorize publication.

Citry 0.5.0 also includes the **Preview extension**, currently being developed by
another agent. Preserve and reconcile its implementation and changelog entries
when combining the work on review; the performance worktree does not contain the
complete release scope. Qualify the combined release before publishing.

## Public API and observable behavior

The feature also adds `LibraryComponent.simple`, not only `Component.simple`.
For classes opting in, static `template_data(kwargs, slots)` callbacks, declaration
restrictions and caller-owned output form the documented simple contract.
Ordinary components retain their existing callback and template contracts.

There are additional changes to exported low-level render APIs:

- `RenderFrame` gains the defaulted `is_transparent_root` boolean field, and
  `RenderFrame.from_context` accepts that keyword.
- `CitryRender(...)` accepts the same optional keyword. It identifies a
  transparent component's whole output separately from caller-owned interiors.

Existing constructor calls remain accepted because the new parameters have
defaults, but these are public surface changes: `RenderFrame` and `CitryRender` are exported from `citry`.
The field also changes the shape of a render frame's dataclass representation.

`ElementAttrsNode` is also exported from `citry`. Its ordinary nonempty render
output can now be an exact `str` rather than `Markup`; code consuming node output
and relying on that safe-string subtype can observe the change. The public
`format_attrs()` helper still returns `Markup`. `CitryContext` adds a private
`_simple_scope` constructor keyword and slot to support the new feature.

The name `simple` becomes a reserved, exact-boolean, immutable declaration on
both component APIs, including classes with `simple=False`. An existing unrelated
class attribute with that name needs renaming; this is a migration consideration.

Internal changes include tuple-based ownership records, native storage, private
context state and a required `transparent_root` field in cached render artifacts.
Ownership records are importable submodule internals, not top-level public
exports; callers depending on dataclass operations on them would be affected.
Cache entries without the field become normal cache misses. The pre-1.0 cache
version remains 1. Browser wire schemas and template syntax are unchanged.
Transparent boundary handling and deeply nested render traversal have observable
correctness fixes, already recorded in the Citry changelog.

## Added dependency and Ruff upgrade scope

The user also requested the open Dependabot updates and issue
[#101](https://github.com/citry-dev/citry/issues/101). This inventory was checked
against GitHub during preparation. No dependency manifests, lockfiles, workflows
or submodule checkout have been changed for these items yet. The six PRs touch
20 distinct paths before adaptations, regenerated outputs or release metadata.

| PR | Requested updates | Work to include |
| --- | --- | --- |
| [#94](https://github.com/citry-dev/citry/pull/94) | Maturin 1.14.1 to 1.15.0 | Core build-system and development requirements, combined Python lock update and native/browser wheel qualification |
| [#98](https://github.com/citry-dev/citry/pull/98) | ty 0.0.73 to 0.0.78; django-components 0.151.1 to 0.152.0 | Citry analysis extra, benchmark dependency and combined Python lock update |
| [#100](https://github.com/citry-dev/citry/pull/100) | setup-node v7, cache v6, setup-java v6 and sccache-action 0.0.11 | Reconcile action uses with current workflows and check runner/toolchain requirements |
| [#102](https://github.com/citry-dev/citry/pull/102) | ty 0.0.73 to 0.0.78 | LSP runtime dependency, coordinated with Citry's optional analysis extra |
| [#103](https://github.com/citry-dev/citry/pull/103) | Five Storybook packages 10.5.9 to 10.6.0 | Citry UI Storybook tooling and combined pnpm lock update |
| [#104](https://github.com/citry-dev/citry/pull/104) | Alpine/CSP/morph 3.17.1, CodeMirror updates, Terser 5.51.2, vnu-jar 26.8.30, Biome 2.5.11 and vscode-languageclient 10.1.1 | All named package manifests, regenerated browser artifacts, combined pnpm lock update, browser and editor checks |

The additional expected distribution releases are `citry-lsp` (currently 0.1.3)
and `vscode-citry` (currently 0.1.2), because their runtime dependencies change.
Since the editor is included, update its `citry.lspVersion` to the selected LSP
release. Publish and verify LSP before shipping the VS Code extension that pins
it. Storybook and the JavaScript workspace packages are private; those
tooling updates do not themselves require a separate package release. Inspect
regenerated Citry UI assets before deciding whether the UI distribution also
needs to ship changed bytes.

Apply the intended dependency values against the current files, preserving
unrelated work. Rebuild each workspace lockfile from the combined declarations;
do not overwrite one Dependabot lockfile with another. The Python PRs overlap
through ty, and the JavaScript PRs overlap through `pnpm-lock.yaml`.

The PR diffs do not cover every matching contract and pin. Include these in the
implementation audit:

- `packages/py/citry_core/pyodide-build.json` also pins Maturin and must agree
  with the Core build requirements.
- `scripts/verify_citry_distribution.py` and
  `scripts/verify_citry_lsp_distribution.py` check the installed ty version;
  update their expectations with the two package declarations.
- Alpine's upgrade changes the runtime against which Citry validates CSP
  expressions. Review `packages/js/citry-client/build-support.mjs` (including
  exact-source directive and morph instrumentation), `citry/_alpine_csp.py`, the diagnostics catalog,
  `packages/js/citry-client/test/csp-contract-runner.mjs`, the versioned CSP
  fixture and browser-analysis tests. Check the new runtime's actual behavior
  before changing expected contracts or version labels. Rebuilding JavaScript
  alone is insufficient. Qualify standard and CSP ownership, isolation, morph
  planning and events; update generated consumers and recheck payload budgets.

For Ruff, the issue body names 0.16.5. The verified latest stable release during
this inspection is [0.16.6](https://github.com/astral-sh/ruff/releases/tag/0.16.6),
whose tag resolves to `22f65a2ab5052990503985c7c794de37598d531e`. The current
checkout is `5b48a040974781ba90b47c8df628f8fd9b6c95dd`. Before switching it,
review the used crate APIs and upstream workspace dependency changes. Update
the submodule, its `.gitmodules` version comment, mirrored root Cargo
dependencies and lockfile together. Adapt first-party callers where required,
then run the full gate, parser/formatter/sandbox coverage and Core distribution
qualification. Update the formatter provider identity in
`crates/citry_template_formatter/src/python.rs` and its live fixture/test
consumers. Qualify formatter golden/idempotence tests, Python bindings, CLI,
LSP and VS Code formatting. Revalidate the target release when implementation starts.
The existing `scripts/ruff_submodule_updates.py` checker and
[codebase submodule procedure](../codebase.md#adding-a-git-submodule) describe the
monitored crates and verification workflow. The issue remains open until the
upgrade is implemented and verified.

Dependency work must be measured separately from the finished optimization
experiments. In particular, the Django-components and Alpine changes mean the
retained publication benchmark is not evidence for the upgraded dependency set.
Rerun the publication benchmark and regenerate its images after the combined
upgrade passes the repository and browser checks. Preserve the dated original
report rather than rewriting its measured versions or observations.

## Transfer and pull-request sequence, when requested

1. Record source and destination HEADs, index state, tracked changes, untracked
   files and hashes. Regenerate an explicit named-file manifest from the snapshot
   delta plus selected uncommitted and untracked files. The manifest must include
   the complete intended research archive; do not silently omit experiments.
2. Reconcile the four files above using snapshot, destination and performance
   contents. Copy only named files and explicitly named deletions into the review
   working tree. Leave its HEAD and index untouched; new files remain untracked
   and existing files remain modified for human review. Verify all copied bytes
   and preservation of unrelated destination changes.
3. For the performance PR, fetch and record current `origin/main`, then prepare
   an isolated PR branch based on that commit. Copy the selected reviewed changes
   from the review working tree using a separate promotion manifest. Compare
   each selected existing file with the recorded main base and reconcile
   independent main changes before copying; unexpected differences stop
   promotion. Preserve main-only files, including generated documentation snapshots, unless a deletion
   is explicitly selected. Do not merge or cherry-pick the review or performance
   branch history into main.
4. Inspect the full combined diff and package metadata, run the repository,
   browser, Linux typing and documentation checks, and commit only in the isolated
   PR branch. Mirror necessary corrections back into the review working tree
   without staging or committing them there. Create the requested PR targeting
   main when that action is authorized.
5. After PR review and merge, use the documented candidate-qualification and
   release controller. Never force-push main or move review's baseline to hide
   unread changes.

The repository documents direct promotion through a clean main worktree. The
isolated PR branch in steps 3-4 adapts that procedure to the requested PR while
preserving its named-file manifest and unread-review rules. It does not authorize
a direct push to main. No Git mutation in this sequence has been performed.


## Preparation checks

The four-series chart was regenerated and visually inspected; both PNG copies
are byte-identical and use the retained simple measurements. Ruff check and
format checks passed for the plotting script. The strict docs build passed with
no guard findings. Read-only recounting confirmed the file totals and four
reconciliation paths above. A direct low-level render check confirmed the
`ElementAttrsNode` result is `str` while `format_attrs()` remains `Markup`.
Independent technical and separate prose reviews covered the chart, release/API
inventory and this transfer plan. These checks do not qualify the dependency
upgrades, which remain unimplemented preparation items.
