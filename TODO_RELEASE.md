# Citry beta release tracker

Updated: 2026-08-18

This file is the working checklist for the next public release set. It records
release intent; checking it in does not itself authorize publishing, tagging,
or deploying anything.

## Locked release decisions

- [x] Released `citry-core` **1.5.0** on 2026-08-18. Phase 1 corrected the
  accidental unreleased `1.6.0` source version; it was not published as 1.6.0.
- [ ] Release `citry` **0.4.0**, positioned as the Citry beta release. This is
  the final package version (`0.4.0`), not a PEP 440 prerelease such as
  `0.4.0b1`.
- [ ] Release `pygments-citry` **0.2.0**, including the unreleased Fluent
  syntax support.
- [ ] Publish `citry-lsp` **0.1.0** for the first time.
- [ ] Publish `citry-ui` **0.1.0** for the first time. Treat this as an
  early-access release intended to generate real-world feedback; incomplete
  long-tail qualification is not a reason to defer it.
- [ ] Publish the VS Code extension `citry-dev.citry` **0.1.0** after
  `citry-lsp` is installable.
- [ ] Once the new Python artifacts exist, update the playground's complete,
  compatible runtime tuple and sweep all current version constraints, pins,
  examples, tests, and release documentation across the repository.

## Current public/repository state

| Artifact | Public state found during audit | Repository state | Target |
| --- | --- | --- | --- |
| `citry-core` | PyPI 1.5.0 | tagged and released at `citry-core@1.5.0` | 1.5.0 complete |
| `citry` | PyPI 0.3.1 | 0.4.0, unreleased | 0.4.0 beta |
| `pygments-citry` | PyPI 0.1.2 | 0.2.0, unreleased | 0.2.0 |
| `citry-lsp` | not found on PyPI | 0.1.0 | 0.1.0 first release |
| `citry-ui` | not found on PyPI | 0.1.0 | 0.1.0 first release |
| `citry-dev.citry` | not found on VS Marketplace or Open VSX | 0.1.0 | 0.1.0 first release |

The Rust crates and JavaScript/protocol packages currently marked `0.0.0`, as
well as internal Rust crate version numbers, are not automatically part of
this public release set. Do not bulk-replace matching version strings in
third-party, research, historical, or internal files.

## Dependency and publication order

```text
citry-core 1.5.0, published for native platforms and Pyodide/WebAssembly
        |
        v
citry 0.4.0 beta
   |             |
   v             v
citry-lsp 0.1.0  citry-ui 0.1.0
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

- [ ] Confirm that its exact core dependency is `citry-core==1.5.0` and that
  core 1.5.0 is already available from PyPI.
- [ ] Finalize the 0.4.0 changelog and public beta positioning.
- [ ] Verify the existing PyPI Trusted Publisher/workflow/environment setup.
- [ ] Build and inspect the pure-Python wheel and sdist.
- [ ] Tag and publish `citry@0.4.0` from the intended main commit.
- [ ] Verify a clean install, import, and representative render using only
  public artifacts.

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
`ty==0.0.69`). Citry's language-analysis tooling can invoke `ty` to understand
Python expression types. `citry-lsp` requests this extra because it uses that
analysis for editor diagnostics/completions. Ordinary Citry runtime users do
not need the extra. For the beta, verify that the `ty` pin still works on the
supported Python versions and decide explicitly whether it remains an exact
pin.

## 4. First release of `citry-lsp` 0.1.0

- [ ] Update its Citry dependency to the 0.4 series and update docs/changelog
  claims that still name the unreleased 0.3.2/0.3 line.
- [ ] Add a dedicated PyPI OIDC publish workflow and tag convention.
- [ ] Create/configure the PyPI project through a pending Trusted Publisher if
  it does not yet exist. Match the exact GitHub owner, repository, workflow
  filename, and environment.
- [ ] Build and inspect its distribution and console-script entry point.
- [ ] After Citry 0.4.0 is public, verify a clean installation of `citry-lsp`
  pulls `citry[analysis-ty]` and starts the server.
- [ ] Tag, publish, and verify the public package page/install.

## 5. First early-access release of `citry-ui` 0.1.0

- [ ] Update its version and Citry 0.4 dependency constraint.
- [ ] Write a clear 0.1.0 changelog and label the library early access/alpha:
  usable for experimentation, intentionally seeking feedback, and subject to
  API changes.
- [ ] Document known limitations honestly. Do not block publication on the
  complete long-tail manual qualification matrix.
- [ ] Define and run a small launch floor: distribution build/metadata,
  license/readme, clean install/import, registration of a representative
  component, and one representative render/interaction path.
- [ ] Add a dedicated PyPI OIDC publish workflow and tag convention.
- [ ] Create/configure its pending PyPI Trusted Publisher with the exact
  workflow/environment identity.
- [ ] After Citry 0.4.0 is public, tag/publish 0.1.0 and verify a clean public
  install.
- [ ] Add an obvious feedback/issue path to the package and docs so releasing
  early can actually produce useful feedback.

## 6. Release `pygments-citry` 0.2.0

- [ ] Finalize the existing Fluent syntax work and release notes.
- [ ] Verify the existing PyPI Trusted Publisher/workflow configuration.
- [ ] Build and inspect the wheel/sdist and run representative Citry and Fluent
  lexer checks.
- [ ] Tag/publish 0.2.0 and verify a clean install and Pygments entry-point
  discovery.

## 7. Publish the VS Code extension 0.1.0

- [ ] Publish only after `citry-lsp` 0.1.0 is publicly installable, because the
  extension launches that external executable rather than bundling it.
- [ ] Confirm the `citry-dev` publisher identity and extension ownership in
  both Visual Studio Marketplace and Open VSX.
- [ ] Add/document the publishing procedure, secrets, and unique tag scheme.
  Marketplace and Open VSX generally require their own publisher tokens.
- [ ] Finalize the extension changelog, installation docs, dependency/error
  UX, metadata, icon, license, links, and supported platform story.
- [ ] Build one exact `.vsix`, inspect its file list, smoke-test it in a clean
  VS Code profile with public `citry-lsp`, and publish those same bytes to both
  registries.
- [ ] Verify both public listing/install pages and update docs links. The live
  docs currently advertise VS Code installation even though the extension was
  not found in either registry during the audit.

## 8. Promote the new playground runtime tuple

The committed `docs_site/static/playground/runtime.json` is one atomic,
compatible public-artifact tuple. It currently pins Citry 0.3.1 and
`citry-core` 1.4.0 with immutable wheel URLs. A normal deployed build does not
silently substitute workspace packages.

- [ ] Wait until `citry-core` 1.5.0, `citry` 0.4.0, and—if enabling UI examples
  live—`citry-ui` 0.1.0 are publicly downloadable.
- [ ] Update the entire tuple together: Pyodide/Python if intentionally
  changing it; Citry/core/UI versions; immutable wheel URLs; integrity and
  metadata fields; and compatibility notes.
- [ ] Add the `citry-ui` wheel and `citry.ui_version` metadata if public docs
  will offer live UI previews. The current committed static runtime does not
  include UI merely because the local authoring server can build a workspace
  UI wheel.
- [ ] Confirm the core wheel's CPython/PyEmscripten ABI matches the pinned
  Pyodide runtime.
- [ ] Run the real Chromium browser/playground tests, not only pure-Python unit
  tests, and exercise APIs introduced in the beta.
- [ ] Update current docs/examples/tests to the released tuple and deploy the
  public site from `main`.

Because immutable PyPI URLs do not exist before publication, the
`citry@0.4.0` tag may deploy the version snapshot while the live playground is
still on the old known-good tuple. Follow it with a `main` commit that promotes
the new tuple once all required public files can be fetched. The release set is
not considered finished until that follow-up and repository-wide pin sweep are
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
