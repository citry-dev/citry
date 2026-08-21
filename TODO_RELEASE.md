# Citry beta release tracker

Updated: 2026-08-21

This file is the working checklist for the next public release set. It records
release intent; checking it in does not itself authorize publishing, tagging,
or deploying anything.

## Locked release decisions

- [x] Released `citry-core` **1.5.0** on 2026-08-18. Phase 1 corrected the
  accidental unreleased `1.6.0` source version; it was not published as 1.6.0.
- [x] Release `citry` **0.4.0**, positioned as the Citry beta release. This is
  the final package version (`0.4.0`), not a PEP 440 prerelease such as
  `0.4.0b1`.
- [x] Released `pygments-citry` **0.2.0** on 2026-08-19, including the Fluent
  syntax support.
- [x] Released `citry-lsp` **0.1.0** on 2026-08-19.
- [x] Released `citry` **0.4.1** and `citry-lsp` **0.1.1** on 2026-08-20 so
  editor formatting keeps ordinary triple-quoted asset quotes and uses
  canonical JavaScript/CSS host framing.
- [x] Released `citry-core` **1.5.1** and `citry` **0.4.2** on 2026-08-21 with
  the render-path performance work, compact ownership aliases, and the Fluent
  link-unit punctuation fix.
- [x] Released `citry-ui` **0.1.0** on 2026-08-19 as an early-access release
  intended to generate real-world feedback.
- [x] Published the VS Code extension `citry-dev.citry` **0.1.0** on
  2026-08-20 after `citry-lsp` became installable.
- [ ] Once the new Python artifacts exist, update the playground's complete,
  compatible runtime tuple and sweep all current version constraints, pins,
  examples, tests, and release documentation across the repository.

## Current public/repository state

| Artifact | Public state found during audit | Repository state | Target |
| --- | --- | --- | --- |
| `citry-core` | PyPI 1.5.1 | tagged and released at `citry-core@1.5.1` | 1.5.1 performance patch complete |
| `citry` | PyPI 0.4.2 | tagged and released at `citry@0.4.2` | 0.4.2 performance patch complete |
| `pygments-citry` | PyPI 0.2.0 | tagged and released at `pygments-citry@0.2.0` | 0.2.0 complete |
| `citry-lsp` | PyPI 0.1.1 | tagged and released at `citry-lsp@0.1.1` | 0.1.1 formatter patch complete |
| `citry-ui` | PyPI 0.1.0 | tagged and released at `citry-ui@0.1.0` | 0.1.0 early access complete |
| `citry-dev.citry` | VS Marketplace and Open VSX 0.1.0 | tagged and released at `vscode-citry@0.1.0` | 0.1.0 complete |

The Rust crates and JavaScript/protocol packages currently marked `0.0.0`, as
well as internal Rust crate version numbers, are not automatically part of
this public release set. Do not bulk-replace matching version strings in
third-party, research, historical, or internal files.

## Dependency and publication order

```text
citry-core 1.5.1, published for native platforms and Pyodide/WebAssembly
        |
        v
citry 0.4.2 beta
   |             |
   v             v
citry-lsp 0.1.1  citry-ui 0.1.0
   |
   v
VS Code extension 0.1.0

pygments-citry 0.2.0 is independent, but should be live before the final
documentation promotion if the docs advertise the new Fluent highlighting.
```

The LSP and UI can be published in parallel after `citry` 0.4.0 is available.
The VS Code extension ships last because it launches a separately installed
`citry-lsp` executable.

## 1. Correct versions and constraints before release

**Status: complete on 2026-08-17.** The repository fast profile passed, as did
focused LSP, UI, Pygments, and docs tests. Public-artifact-dependent
playground promotion remains in section 8.

- [x] Change `packages/py/citry_core/pyproject.toml` from 1.6.0 to 1.5.0.
- [x] Reconcile the `citry-core` changelog so all intended unreleased work is
  under the 1.5.0 release. Do not leave a misleading already-released 1.5 or
  future 1.6 section.
- [x] Change `packages/py/citry/pyproject.toml` from 0.3.2 to 0.4.0 and pin its
  compiled dependency to `citry-core==1.5.0`.
- [x] Change `citry-lsp`'s Citry constraint from
  `citry[analysis-ty]>=0.3.2,<0.4` to the compatible 0.4 series, expected to
  be `citry[analysis-ty]>=0.4.0,<0.5`, and change the LSP's enforced supported
  Citry series to 0.4.x.
- [x] Change `citry-ui` from 0.0.1 to 0.1.0 and its Citry constraint from the
  0.3 series to the compatible 0.4 series, expected to be
  `citry>=0.4.0,<0.5.0`.
- [x] Change `pygments-citry` from 0.1.2 to 0.2.0 and finalize its changelog,
  explicitly including Fluent syntax handling.
- [x] Keep the VS Code extension at 0.1.0, finalize its changelog, and use the
  extension-specific tag `vscode-citry@0.1.0`. Do not reuse
  `citry@0.1.0`, which belongs to the Python package's tag namespace.
- [x] Regenerate `uv.lock` from the corrected authoritative manifests.
- [x] Perform a targeted repository-wide sweep after the manifest edits.
  Classify each hit as current metadata, current dependency/pin, test fixture,
  generated output, historical record, research snapshot, third-party code,
  or unrelated version before changing it.

Known current references that need deliberate reconciliation include:

- [x] Root `TODO.md` release versions and ordering.
- [x] Package manifests, changelogs, READMEs, and install examples.
- [x] `docs/design/docs_playground_ide.md`, the living UI library plan,
  `docs/design/ide_integration.md`, and the VS Code/LSP documentation.
- [x] Docs tests and examples that intentionally assert local package version
  metadata.
- [x] Workflow inputs, artifact names, compatibility banners, and the active
  root lockfile. No workflow version literal required a change.

Deferred until the public artifacts exist:

- [ ] The committed playground tuple in
  `docs_site/static/playground/runtime.json` and its documentation, but only
  after the corresponding public artifacts and immutable URLs exist.

Do not rewrite dated evidence logs, old changelog entries, committed versioned
documentation snapshots, or vendored/third-party files merely because they
contain an old number. Do not hand-edit ignored generated `site/` output.

The tracked `packages/py/citry_core/uv.lock` is a legacy package-local lock
that still records Citry Core 1.3.0. Repository tooling uses the sole root
`uv.lock`; Phase 1 intentionally did not rewrite the obsolete lock. Decide its
deletion as a separate cleanup rather than treating it as a release input.

## 2. Release `citry-core` 1.5.0

### Stage 1: cleanup and audit

**Status: local pre-release preparation complete on 2026-08-18.** No branch
update or release action was taken.

- [x] Replace the verbose 1.5.0 changelog draft with skimmable,
  outcome-focused entries while retaining the host-runtime contract changes.
- [x] Refresh the PyPI README: install/quick-start, current submodules and
  imports, i18n/tooling capabilities, and the actual mixed-package layout.
- [x] Run the relevant Rust/Python format, lint, type, test, validator, native
  distribution, isolated-install, and i18n release checks.

The audit initially found one real failure: rebuilding the generated 1.5.0
sdist outside the repository selected the machine's stable Rust 1.94 even
though `citry_i18n`, Oxc 0.143.0, and vendored Ruff 0.16.2 require Rust 1.95.
The publish workflow also had no sdist rebuild, install smoke, closed artifact
inventory, or permanent PyEmscripten build. The pre-release implementation now
closes those gaps:

- every bundled first-party Rust crate inherits the workspace's Rust 1.95
  minimum, and the package README states that source-build requirement;
- wheel and source builds use the checked Cargo lock and Maturin 1.14.1;
- the workflow keeps builder outputs separate, rejects duplicate filenames,
  and requires the exact 92-file set: 90 native wheels, one PyEmscripten wheel,
  and one sdist;
- release-critical third-party actions are pinned to reviewed commits, and a
  retry fails closed if the PyPI version or GitHub Release already exists;
- every artifact receives metadata, tag, payload, extension, license,
  `RECORD`, and size inspection; runnable native wheels are installed in fresh
  environments, and the sdist is rebuilt outside the checkout with Rust 1.95
  before its wheel is installed and exercised;
- the PyEmscripten wheel is built twice from clean source trees for Pyodide
  314.0.3 / CPython 3.14.2 / Emscripten 5.0.3; the build checks the actual
  SDK-reported Emscripten version before using it, then installs and exercises
  the wheel in that exact Pyodide runtime. The two local builds were byte-identical at
  4,459,644 bytes with SHA-256
  `ccd6c296591d931e84ef2347c1fd1ee6e7bf16621366dd4790dc76c4c8f1acc4`.
  The first unstripped probe was 24,287,271 bytes; removing profiler-only
  DWARF/debug data with the pinned Emscripten optimizer brought it below the
  unchanged 10 MiB release cap and below the 7,011,715-byte 1.4.0 browser
  wheel.

No branch, tag, package registry, or deployment was changed during the local
pre-release preparation.
The focused Citry Core plus Citry compatibility run passed 4,907 tests with
33 skips and one expected failure. The repository `fast` profile also passed
all 18 phases, including Rust format/lint/tests, Python lint/types/tests,
protocols, frontend packages, VS Code, the lockfile, and custom validators.
An independent adversarial review then passed with no remaining findings or
release blockers; its focused artifact suite passed all nine tests, including
the closed archive, canonical metadata, platform-wheel, toolchain, and
fail-closed publication checks.

### Stage 2: promote the prepared source to `main`

**Status: complete on 2026-08-18.** The prepared tree and subsequent release-gate
fixes were pushed to `main` by fast-forward-only promotions, ending at qualified
release commit `b61828a4`. The source tree and clean promotion worktree matched
exactly each time. The original `review` branch, index, and visible working set
remained at the recorded `reviewed-baseline`.

### Stage 3: qualify, tag, and publish

**Status: complete on 2026-08-18.** The annotated `citry-core@1.5.0` tag points
to qualified commit `b61828a4`. The final non-publishing qualification and the
tag-triggered publish workflow both passed before PyPI and the GitHub Release
were independently verified.

- [x] Confirm the 1.5.0 source/changelog contents and compatibility expected by
  `citry` 0.4.0.
- [x] Make the sdist's Rust 1.95+ requirement/toolchain selection reliable and
  rebuild-smoke the artifact outside the checkout.
- [x] Add publish-workflow distribution smoke coverage so an sdist or wheel
  that cannot install/import blocks publication.
- [x] Ensure the existing PyPI publishing workflow builds the supported native
  wheels and sdist with the corrected version.
- [x] Add and run the missing build path that produces the
  PyEmscripten-compatible **variant of the `citry-core` 1.5.0 wheel** for the
  playground's pinned Pyodide Python and Emscripten ABI. PyEmscripten is a
  build target here, not another runtime dependency.
- [x] Verify the PyPI Trusted Publisher/workflow/environment configuration for
  `citry-core`; the tag workflow successfully published through the protected
  `pypi` environment using Trusted Publishing.
- [x] Let the tag workflow build and inspect the complete cross-platform
  distribution set, including all native, PyPy, free-threaded, musllinux, and
  PyEmscripten artifacts plus the sdist rebuild/install smoke.
- [x] Tag and publish `citry-core@1.5.0` using the repository's release
  procedure.
- [x] Verify PyPI installation on a normal supported platform and verify the
  exact URL of the PyEmscripten-compatible `citry-core` artifact that will be
  placed in the playground tuple.

Release evidence:

- final non-publishing qualification:
  <https://github.com/citry-dev/citry/actions/runs/32126745998>;
- successful tag/publish workflow:
  <https://github.com/citry-dev/citry/actions/runs/32130252035>;
- public package: <https://pypi.org/project/citry-core/1.5.0/>;
- GitHub Release:
  <https://github.com/citry-dev/citry/releases/tag/citry-core%401.5.0>;
- PyPI and GitHub each contain the exact 92 distributions in
  `release-inventory.json` with matching sizes and SHA-256 hashes; GitHub also
  carries one publish attestation per distribution;
- a clean CPython 3.14 macOS arm64 install from PyPI passed the full installed
  API smoke suite;
- the immutable PyEmscripten wheel is
  `citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl`, 4,459,502
  bytes, SHA-256
  `4e7c8588f5061f60392f907afc380501e4819b663d29ca75f699bd676970e1a6`, at
  <https://files.pythonhosted.org/packages/09/1f/dbedc0e88b77c4c93de7d367bdc99aa98427149358d367d8901b211bd54d/citry_core-1.5.0-cp314-cp314-pyemscripten_2026_0_wasm32.whl>.

### Why `citry-core` 1.5.0 needs a PyEmscripten-compatible build variant

This is not a new requirement that 1.4.0 somehow avoided. The deployed
playground already pins the PyEmscripten-compatible build of the
`citry-core` 1.4.0 wheel. `citry-core` contains the native Rust/PyO3 extension,
while the docs playground runs Python inside Pyodide/WebAssembly. Native
macOS, Linux, and Windows builds of that same package cannot load there. Each
core version therefore needs a separately built distribution variant whose
package version, CPython ABI, PyEmscripten version, and `wasm32` platform match
the pinned Pyodide runtime.

PyEmscripten is **not** a package that `citry-core` or `citry` depends on, and
it must not be added to either package's runtime dependencies in
`pyproject.toml`. PyPI can hold several platform builds of one `citry-core`
release: macOS, Linux, Windows, and PyEmscripten/WebAssembly. The playground
loads the one PyEmscripten-compatible `citry-core` wheel in place of a native
wheel; it does not install that wheel alongside a second copy of
`citry-core`.

`citry` 0.4.0 and `citry-ui` 0.1.0 are pure-Python wheels, so they do not need
their own platform-specific PyEmscripten builds. In the playground, their
normal dependency on `citry-core` is satisfied by the browser-compatible
1.5.0 build variant.

## 3. Release `citry` 0.4.0 beta

- [x] Confirm that its exact core dependency is `citry-core==1.5.0` and that
  core 1.5.0 is already available from PyPI.
- [x] Finalize the 0.4.0 changelog and public beta positioning.
- [x] Verify the existing PyPI Trusted Publisher/workflow/environment setup.
- [x] Build and inspect the pure-Python wheel and sdist.
- [x] Tag and publish `citry@0.4.0` from the intended main commit.
- [x] Verify a clean install, import, and representative render using only
  public artifacts.

**Released on 2026-08-18.** The annotated `citry@0.4.0` tag points to qualified
commit `1084daff`. Non-publishing qualification run
[`32170190303`](https://github.com/citry-dev/citry/actions/runs/32170190303)
passed across CPython 3.10-3.14, and tag promotion run
[`32172270315`](https://github.com/citry-dev/citry/actions/runs/32172270315)
published its attested wheel/sdist pair to PyPI and the GitHub Release. A clean
public Python 3.10 install resolved `citry==0.4.0` with
`citry-core==1.5.0`, and both packages imported from site-packages.

The first docs tag run exposed two release-only gaps: detached tag worktrees
did not install the tagged Citry packages, and the version-tree guard treated
fictional UI-preview navigation as real while structured `api.yml` links were
not published. Main now creates a locked tag-local docs environment, publishes
the structured API files, and supports immutable-tag recovery through the
manual `release_tag` input. Recovery run
[`32176192140`](https://github.com/citry-dev/citry/actions/runs/32176192140)
built the exact tag snapshot, committed it as `31e7d721`, and deployed Pages.
The live `/v/0.4.0/` build stamp records source commit `1084daff`; the removed
dummy blog URL returns 404 as intended.

The Citry publish workflow uses the same
qualify-then-promote boundary as Citry Core: a manual run qualifies one closed
wheel/sdist pair for an exact `main` commit across CPython 3.10-3.14, and the
tag run may publish only those attested bytes. Manual dispatch cannot publish;
existing PyPI or GitHub Release files make promotion fail closed.

The local distribution proof rebuilt the sdist outside the checkout, compared
both wheels byte-for-byte at the installed-package level, installed and
render-smoked both wheels on Python 3.10 against public `citry-core==1.5.0`, and
passed Twine metadata checks. That proof found and fixed three genuine 3.10
incompatibilities: `datetime.UTC`, stdlib-only `tomllib`, and
`dataclass(weakref_slot=...)`. The final local artifacts were 1,005,387 bytes
for the wheel and 1,561,149 bytes for the sdist; CI will rebuild and record the
release candidates after this tree reaches `main`.

External preflight confirmed the `pypi` environment exists, permits
`citry@*`, and the same Trusted Publishing workflow successfully released
0.3.0 and 0.3.1. The `github-pages` environment permits both `main` and
`citry@*`. Recheck these mutable external settings immediately before tagging.

The `citry@0.4.0` tag is coupled to two workflows: Python package publication
and the versioned docs snapshot/deployment. Before creating it, verify the
GitHub Pages environment permits release-tag deployments and that the docs
snapshot workflow can commit its generated `docs_site/versions/` update back
to protected `main`. `citry-core` and the other package tags do not create a
versioned docs snapshot.

### What `citry[analysis-ty]` means

`analysis-ty` is a Python optional-dependency extra declared by `citry`; it is
not a separate Citry release. Installing:

```sh
pip install "citry[analysis-ty]"
```

installs Citry plus the pinned `ty` Python type checker (currently
`ty==0.0.71`). Citry's language-analysis tooling can invoke `ty` to understand
Python expression types. `citry-lsp` requests this extra because it uses that
analysis for editor diagnostics/completions. Ordinary Citry runtime users do
not need the extra. For the beta, verify that the `ty` pin still works on the
supported Python versions and decide explicitly whether it remains an exact
pin.

## 4. First release of `citry-lsp` 0.1.0

### Stage 1: pre-release preparation

**Status: locally complete on 2026-08-18.** No branch update, qualification
workflow dispatch, tag, publish, or deployment was performed.

- [x] Keep the Phase 1 Citry dependency and runtime guard on the compatible
  0.4 series: `citry[analysis-ty]>=0.4.0,<0.5` and supported series `(0, 4)`.
- [x] Replace the implementation-history changelog with seven skimmable
  outcome-focused first-release entries.
- [x] Prepare the PyPI README with installation, registry and syntax-only
  modes, analyzer degradation, formatting, compatibility, and support links.
- [x] Add `py--citry-lsp--publish.yml` and the package tag
  `citry-lsp@<version>` with the same qualify-then-promote boundary used by
  Citry: manual runs cannot publish, and a tag can promote only the retained
  artifacts qualified for its exact `main` commit.
- [x] Add a closed wheel/sdist verifier, source-distribution rebuild, exact
  metadata/license/entry-point/`RECORD` checks, byte inventory, safe promotion
  extraction, and fail-closed PyPI/GitHub Release preflight.
- [x] Build and inspect the 0.1.0 universal wheel and source distribution;
  `twine check` passed.
- [x] Install the built wheel with only public binary dependencies on CPython
  3.10 through 3.14. Every supported interpreter resolved Citry 0.4.x,
  `ty==0.0.69`, and `pygls==2.1.1`, imported every shipped module, ran the
  installed `citry-lsp --help` entry point, and started/exited the stdio server
  on clean EOF.
- [x] Pass all 479 focused LSP tests, Ruff, formatting, host and Linux mypy,
  the repository fast profile, and the repository full coverage and
  qualification profile.

### Stage 2: update `main`

**Status: complete on 2026-08-19.** The prepared files were promoted through
the clean release worktree in commits `bca20abf` and `1e7989a9`; the dated
release commit is `3efc6203`. The original `review` branch pointer, index, and
working files remained unchanged.

- [x] Copy the named LSP release files into the clean `main` release worktree,
  inspect the resulting diff, run the agreed integration gate, commit, and
  push normally. Keep the original `review` branch pointer, index, and files
  unchanged.

### Stage 3: qualify, tag, and publish

**Status: complete on 2026-08-19.** The annotated `citry-lsp@0.1.0` tag points
to exact commit `3efc6203`. Qualification run `32234879060` produced the
retained release pair; promotion run `32237406471` published those exact bytes
to PyPI and the GitHub Release.

- [x] Create the pending PyPI Trusted Publisher with project `citry-lsp`,
  owner `citry-dev`, repository `citry`, workflow
  `py--citry-lsp--publish.yml`, and environment `pypi`. The pending publisher
  created the project on first use.
- [x] Allow `citry-lsp@*` tags in the GitHub `pypi` environment's deployment
  policy and retain any desired manual approval.
- [x] Manually run `py--citry-lsp--publish.yml` on the exact release commit on
  `main` and wait for the five-version qualification matrix and retained
  `verified-citry-lsp-distributions` bundle.
- [x] Create and push the annotated `citry-lsp@0.1.0` tag at that exact commit.
- [x] Verify the tag workflow promoted the qualified bytes, PyPI and the
  GitHub Release contain the expected pair, and a clean public install starts
  the server.

## 5. First early-access release of `citry-ui` 0.1.0

### Stage 1: pre-release preparation

**Status: locally complete on 2026-08-19.** No second `main` update,
qualification workflow dispatch, tag, publish, or deployment was performed.

- [x] Keep its version at 0.1.0 and its dependency on the compatible
  `citry>=0.4.0,<0.5.0` line.
- [x] Write a clear 0.1.0 changelog and label the library early access/alpha:
  usable for experimentation, intentionally seeking feedback, and subject to
  API changes.
- [x] Document known limitations honestly. Do not block publication on the
  complete long-tail manual qualification matrix.
- [x] Define and run a small launch floor: distribution build/metadata,
  license/readme, clean install/import, registration of a representative
  component, and one representative render/interaction path.
- [x] Add `py--citry-ui--publish.yml` and the `citry-ui@<version>` tag with a
  qualify-then-promote boundary. Manual runs cannot publish, and tags can
  promote only the retained artifacts qualified for their exact `main`
  commit.
- [x] Require a closed universal-wheel/source-distribution pair, exact
  metadata, licenses, runtime and source bytes, every `RECORD` hash, an
  outside-checkout sdist rebuild, Twine rendering, and safe promotion
  extraction.
- [x] Pass 1,909 non-browser UI tests, 21 focused distribution tests, Ruff,
  formatting, host and Linux mypy, five public-dependency install/render
  smokes on CPython 3.10 through 3.14, an installed-wheel Chromium Tabs
  interaction, the strict docs build, and the repository fast profile.
- [x] Add an obvious feedback/issue path to the package and docs so releasing
  early can actually produce useful feedback.

### Stage 2: update `main`

**Status: complete on 2026-08-19.** The prepared files were promoted through
the clean release worktree in commit `7cc690ac`. The original `review` branch
pointer, index, and working files remained unchanged.

- [x] Copy the named Citry UI release files into the clean `main` release
  worktree, inspect the resulting diff, run the agreed integration gate,
  commit, and push normally. Keep the original `review` branch pointer, index,
  and files unchanged.

### Stage 3: qualify, tag, and publish

**Status: complete on 2026-08-19.** The annotated `citry-ui@0.1.0` tag points
to exact commit `7cc690ac`. Qualification run `32247890671` retained the
closed wheel/sdist pair; promotion run `32249108125` published those exact
bytes to PyPI and the GitHub Release.

- [x] Create the pending PyPI Trusted Publisher with project `citry-ui`, owner
  `citry-dev`, repository `citry`, workflow `py--citry-ui--publish.yml`, and
  environment `pypi`.
- [x] Allow `citry-ui@*` tags in the GitHub `pypi` environment's deployment
  policy and retain any desired manual approval.
- [x] Manually run `py--citry-ui--publish.yml` on the exact release commit on
  `main` and retain the `verified-citry-ui-distributions` bundle.
- [x] Date the 0.1.0 changelog, create and push the annotated
  `citry-ui@0.1.0` tag at that exact commit, and let the tag promote the
  qualified bytes.
- [x] Verify PyPI and the GitHub Release contain the expected pair and a clean
  public install registers, renders, and exercises a representative component.

Release evidence:

- qualification: <https://github.com/citry-dev/citry/actions/runs/32247890671>;
- promotion: <https://github.com/citry-dev/citry/actions/runs/32249108125>;
- public package: <https://pypi.org/project/citry-ui/0.1.0/>;
- GitHub Release:
  <https://github.com/citry-dev/citry/releases/tag/citry-ui%400.1.0>;
- wheel: 525,573 bytes, SHA-256
  `8fc344fc634a702dc8da093b68ea5c55acc5487bf6180082b080a314ea59da92`;
- sdist: 500,675 bytes, SHA-256
  `ed97e70e009d5827c27045f085ae484d7c5b20d8ecd838f3899767995eeb7d53`;
- a clean standard CPython 3.14 install from PyPI registered all 101
  definitions and rendered Button, Pagination, and the translated Pagination
  label. The release qualification also exercised Tabs in Chromium from the
  retained wheel.

## 6. Release `pygments-citry` 0.2.0

### Stage 1: pre-release preparation

**Status: locally complete on 2026-08-19.** No `main` update, qualification
workflow dispatch, tag, publication, or deployment was performed.

- [x] Keep the package at 0.2.0 and finalize the concise release notes for
  Fluent `messages` blocks plus `$c-tr` and `c-$c-tr` bindings.
- [x] Confirm the PyPI README explains the `citry`, `citry-html`, `fluent`, and
  `ftl` lexer aliases and shows the common Markdown and Python usage paths.
- [x] Replace the direct tag build with qualify-then-promote. Manual runs
  cannot publish; tags can promote only the retained artifacts qualified for
  their exact `main` commit.
- [x] Add a closed universal-wheel/source-distribution verifier with exact
  metadata, dependency, entry-point, license, source-byte, `RECORD`, safe
  extraction, outside-checkout rebuild, and fail-closed retry checks.
- [x] Verify the existing PyPI Trusted Publisher and the GitHub `pypi`
  environment's `pygments-citry@*` tag policy.
- [x] Pass the package tests, Ruff, formatting, host and Linux mypy, lock
  validation, exact artifact verification, Twine rendering, and installed
  lexer smoke tests on supported Python versions.

### Stage 2: update `main`

**Status: complete on 2026-08-19.** The prepared files were promoted through
the clean release worktree in commit `782111a9`. The original `review` branch
pointer, index, and working files remained unchanged.

- [x] Copy the named pygments-citry release files into the clean `main`
  release worktree, inspect the resulting diff, run the agreed integration
  gate, commit, and push normally. Keep the original `review` branch pointer,
  index, and files unchanged.

### Stage 3: qualify, tag, and publish

**Status: complete on 2026-08-19.** The annotated
`pygments-citry@0.2.0` tag points to exact commit `782111a9`. Qualification
run `32258222907` retained the closed wheel/sdist pair; promotion run
`32261269454` published those exact bytes to PyPI and the GitHub Release.

- [x] Manually run `py--pygments-citry--publish.yml` on the exact release
  commit on `main` and retain the `verified-pygments-citry-distributions`
  bundle.
- [x] Date the 0.2.0 changelog, create and push the annotated
  `pygments-citry@0.2.0` tag at that exact commit, and let the tag promote the
  qualified bytes.
- [x] Verify PyPI and the GitHub Release contain the expected pair and a clean
  public install discovers and exercises all four lexer aliases.

Release evidence:

- qualification: <https://github.com/citry-dev/citry/actions/runs/32258222907>;
- promotion: <https://github.com/citry-dev/citry/actions/runs/32261269454>;
- public package: <https://pypi.org/project/pygments-citry/0.2.0/>;
- GitHub Release:
  <https://github.com/citry-dev/citry/releases/tag/pygments-citry%400.2.0>;
- wheel: 12,718 bytes, SHA-256
  `a8b0a53e60b3d3c0821363555ec4f8990658a74bcc81557d4708a0b9ba01d272`;
- sdist: 21,170 bytes, SHA-256
  `3e35a097cf45150fe841c798a4154835bdf9ef3132c580cb4537702e27511193`;
- a no-cache public CPython 3.14 install discovered `citry`, `citry-html`,
  `fluent`, and `ftl` through Pygments entry points and exercised component
  `messages`, `$c-tr`, and `c-$c-tr` highlighting.

Post-release CI follow-up on 2026-08-19:

- workflow path filters now name their real source, manifest, lockfile,
  toolchain, script, and workflow inputs without treating every `.github/**`
  change as a dependency;
- the docs browser job installs the pinned root `axe-core` runtime used by its
  accessibility checks;
- Python 3.10 uses `tomli` for the Pyodide build helper, and parameterized
  built-in slot-data types keep the same open-container behavior as Python
  3.11 and later.

## 7. Publish the VS Code extension 0.1.0

### Stage 1: pre-publish preparation

**Status: complete on 2026-08-20.** The same qualified universal VSIX is public
on Visual Studio Marketplace and Open VSX and attached to the GitHub Release.

- [x] Wait for public `citry-lsp` 0.1.1. Its dependency floor requires Citry
  0.4.1, while Citry Core remains 1.5.0 and the analysis extra remains
  `ty` 0.0.71
  from PyPI.
- [x] Keep the extension identity `citry-dev.citry`, version 0.1.0, and unique
  tag `vscode-citry@0.1.0`.
- [x] Replace the implementation-history changelog with six skimmable user
  outcomes and prepare a progressive Marketplace README: benefits, install,
  project connection, common editing/formatting paths, troubleshooting,
  requirements, and support.
- [x] Finalize registry metadata and the 256x256 PNG icon. The extension is
  explicitly free and categorized for programming languages, formatting, and
  linting. Its manifest links directly to the VS Code guide, monorepo package,
  issue tracker, GitHub Discussions, and the existing GitHub Sponsors page;
  `SUPPORT.md` gives the same support and private security-reporting routes.
- [x] Add three user-captured product clips: `autocomplete.gif`,
  `refs_hints.gif`, and `formatting.gif`. Each is under 5 MiB, contains no
  personal path/branch/token, lives under `packages/editors/vscode/images/`,
  and is referenced by absolute raw GitHub URL from the Marketplace README.
  The docs guide embeds the same committed URLs. Keep the clips out of the
  VSIX because both listings load the committed media directly.
- [x] Document the supported platform story honestly: desktop VS Code 1.101+
  and compatible desktop/remote workspace hosts. The extension is not a VS
  Code for the Web extension because it starts a Python workspace process.
- [x] Probe for a compatible `citry-lsp` 0.1.x before starting the language
  client, avoiding the low-level connection failure and giving a direct setup
  action when the server is missing or incompatible.
- [x] Build and inspect the closed universal VSIX. Removing the development
  source map and minifying the bundled runtime produced 16 members, 359,936
  bytes compressed and 1,348,497
  bytes expanded; SHA-256
  `7f5e7ba9a3a855577f8ac5a510829d3e557be97289aa6de5357739d9fe2226c9`.
  The qualification build's inventory is authoritative because VSIX ZIP
  timestamps make a later rebuild byte-different. This pre-Dependabot artifact
  is now superseded by the Prettier 3.9.6 bundle update, so the final VSIX must
  be rebuilt and requalified.
- [x] Add exact VSIX metadata/source/member/size/path validation, safe retained
  artifact promotion, byte inventory, and qualification/promotion provenance.
- [x] Load the extracted VSIX in a clean VS Code 1.101.0 profile against a
  clean public `citry-lsp==0.1.1` install, require real `c-if`, `c-for`, and
  `c-slot` completions, and format untidy embedded JavaScript and CSS through
  the exact hash-pinned Prettier 12.4.0 extension. The smoke also selects a
  different standalone CSS formatter to qualify the bundled Prettier fallback.
  The local macOS arm64 smoke passed, including provider selection and
  repeated-command idempotence. The full component fixture also requires plain
  HTML quotes and canonical triple-quoted JavaScript/CSS host framing.
- [x] Publish Citry 0.4.1 with the Python host-framing fix, then publish
  `citry-lsp` 0.1.1 with `citry[analysis-ty]>=0.4.1,<0.5`, before qualifying
  the public extension artifact.
- [x] Add `vscode--citry--publish.yml`. Manual runs can only qualify; a
  `vscode-citry@*` tag can promote only the retained artifact for its exact
  `main` commit to Visual Studio Marketplace, Open VSX, and a GitHub Release.
- [x] Attach the exact qualified `.vsix`, byte inventory, qualification
  provenance, and registry verification to the GitHub Release. The tag job
  creates that release only after both registry versions are public.
- [x] Document the external publisher, secret, environment, partial-retry, and
  PAT-to-Entra/OIDC migration procedure in `docs/codebase.md`.
- [x] Create [issue #84](https://github.com/citry-dev/citry/issues/84) to apply
  for verified-publisher status after the Marketplace listing has been public
  for six months. Its provisional review date is 2027-02-19 and must move if
  the actual publication date is later.
- [x] Confirm both registry entries are absent immediately before preparation:
  Visual Studio Marketplace and Open VSX returned 404 for `citry-dev.citry`.

### Stage 2: update `main` and qualify

- [x] Promote the named Phase 7 files through the clean `main` worktree,
  inspect the diff, commit, and push normally. Keep the original `review`
  branch pointer, index, and working files unchanged.
- [x] Manually run `vscode--citry--publish.yml` on the exact release commit and
  retain `verified-vscode-citry-extension` for that commit.

### Stage 3: configure publishers, tag, and publish

- [x] Confirm or create the `citry-dev` publisher in Visual Studio Marketplace,
  create a Marketplace Manage PAT, and store it as `VSCE_PAT` in the protected
  `vscode-marketplaces` GitHub environment. Replace this temporary PAT route
  before global Azure DevOps PAT retirement on 2026-12-01.
- [x] Recheck the published `@vscode/vsce` client before release. When a stable,
  reviewed version exposes `vsce publish --oidc`, configure the Marketplace
  trusted-publishing policy and remove `VSCE_PAT`; do not build the release
  boundary from an unreleased repository revision.
- [x] Sign the Eclipse Publisher Agreement, create/claim the `citry-dev` Open
  VSX namespace, verify an Open VSX token for it, and store that token as
  `OVSX_PAT` in the same GitHub environment. The ownership claim is pending,
  but the namespace creator is already a contributor and can publish.
- [x] Configure the `vscode-marketplaces` environment to allow
  `vscode-citry@*` tags and retain any desired approval gate.
- [x] Create and push annotated tag `vscode-citry@0.1.0` at the exact qualified
  `main` commit and let it upload the same VSIX to both registries.
- [x] Verify both public registry package endpoints and the GitHub Release, then
  update the public docs from their pre-availability wording and links.

**Release evidence:** qualification
[run 32386637089](https://github.com/citry-dev/citry/actions/runs/32386637089)
retained and attested the artifact for commit `7d115e07`; tag promotion
[run 32386904887](https://github.com/citry-dev/citry/actions/runs/32386904887)
published those bytes to both registries and created the
[GitHub Release](https://github.com/citry-dev/citry/releases/tag/vscode-citry%400.1.0).
The release VSIX is 359,430 bytes with SHA-256
`7d8ff6a69ff63a954037368d4ad3af507aee3c325f1ce3e9c79efe8484c2f7be`.

## 8. Promote the new playground runtime tuple

**Status: complete on 2026-08-21.**

The committed `docs_site/static/playground/runtime.json` is one atomic,
compatible public-artifact tuple. It now pins Citry 0.4.2, `citry-core` 1.5.1,
and `citry-ui` 0.1.0 with immutable wheel URLs while retaining Pyodide 314.0.3
and Python 3.14.2. A normal deployed build does not silently substitute
workspace packages.

- [x] Refresh the server, browser, and i18n benchmarks before promoting the
  tuple. The 2026-08-20 runs record the beta feature set, fixed a quadratic
  ownership scan exposed by the large server scenario, reduced its warm result
  from 87.31 ms to 48.67 ms with byte-identical output, and corrected the
  browser runner's obsolete destroy/recreate expectation for keyed morphs.
  The published server chart and permanent performance notes use the new
  baseline; all i18n gates and browser orientation targets pass.
- [x] Wait until the current patch releases, `citry-core` 1.5.1 and `citry`
  0.4.2, are publicly downloadable. `citry-ui` 0.1.0 is also public before
  enabling live UI examples.
- [x] Update the entire tuple together: Pyodide/Python if intentionally
  changing it; Citry/core/UI versions; immutable wheel URLs; integrity and
  metadata fields; and compatibility notes.
- [x] Add the universal `citry-ui` wheel and the general first-party runtime
  version field `citry.ui_version`. Public builds use the published wheel;
  local authoring replaces that one package entry with a workspace wheel.
- [x] Confirm the core wheel's CPython/PyEmscripten ABI matches the pinned
  Pyodide runtime.
- [x] Run the real Chromium browser/playground tests, not only pure-Python unit
  tests, and exercise APIs introduced in the beta.
- [x] Update current docs/examples/tests to the released tuple and deploy the
  public site from `main`.

**Promotion evidence:** the core wheel is the exact
`cp314-cp314-pyemscripten_2026_0_wasm32` build for the retained Pyodide
314.0.3/Python 3.14.2 ABI. Its immutable PyPI file is 4,507,957 bytes with
SHA-256 `081e1e2a8adfb2a51a49de1dc34749f0325dfd3861bd6960640beee5286bc52f`.
The Citry wheel is 1,019,189 bytes with SHA-256
`b5bdceaac5d6db5bb2f4f2d7af76de8c7285d61a78c0f5e7a65679509b2418b2`;
the Citry UI wheel is 525,573 bytes with SHA-256
`8fc344fc634a702dc8da093b68ea5c55acc5487bf6180082b080a314ea59da92`.
The complete real Chromium playground suite passed, including repeated UI
registration, direct `ComponentLike` rendering, UI assets and interactions,
Events fragments, and the beta getting-started example. Strict docs guards and
the focused runtime/unit suite also pass. Main promotion commit `35df09ad`
deployed the root site in
[run 32494109403](https://github.com/citry-dev/citry/actions/runs/32494109403).
Release-docs recovery
[run 32491123833](https://github.com/citry-dev/citry/actions/runs/32491123833)
then built the exact `citry@0.4.2` snapshot, committed it back to `main` as
`d5fd4b78`, and deployed it. The live snapshot build stamp records source
commit `f1b18c7c`, and `/v/versions.json` makes 0.4.2 the `latest` alias.

Because immutable PyPI URLs do not exist before publication, a Citry tag may
deploy its version snapshot while the live playground remains on the previous
known-good tuple. Follow it with a `main` commit that promotes the new tuple
once all required public files can be fetched. The release set is not
considered finished until that follow-up and repository-wide pin sweep are
complete.

## 9. Public docs and site

- [ ] Keep `docs_site/settings.yml`, deployment workflow URL settings, and
  `https://citry.dev/` aligned.
- [ ] Preserve the deliberate removal of the dummy blog post. Its old URL is
  intended to disappear with no redirect because it was never meant to be
  public. An empty blog index and absent feed are valid.
- [ ] Update package/extension availability and install commands only when the
  corresponding public artifact exists.
- [ ] Assemble production docs with `python -m docs_site assemble`; do not
  commit or hand-edit ignored root `site/` output.
- [ ] Run the strict docs checks and browser suite when time permits. Current
  failing CI/docs checks should be triaged explicitly, but the decision to
  launch `citry-ui` early should not be replaced with an indefinite “defer
  until qualification is complete.”
- [ ] Merge/push the current docs changes to `main` to trigger the routine
  GitHub Pages deployment. Use the `citry@0.4.0` tag workflow for the versioned
  0.4.0 snapshot.
- [ ] Verify the homepage, install pages, playground, version selector, sitemap,
  indexing files, and expected 404 for the removed blog URL after deployment.

## 10. Final verification and closeout

- [ ] Verify public package pages and exact versions for all five Python
  distributions.
- [ ] Install the public dependency chain in clean environments rather than
  relying on workspace resolution.
- [ ] Verify both VS Code registries install the published 0.1.0 extension and
  that it can find/start public `citry-lsp`.
- [ ] Verify `citry.dev` serves the new docs and the promoted playground tuple.
- [ ] Re-run a final targeted version/pin search and record every intentional
  old-version occurrence left behind.
- [ ] Record release URLs, tag SHAs, workflow runs, and any consciously accepted
  failures in this tracker or the permanent release record.
