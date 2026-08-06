# Stage 1 documentation-content baseline

**Status (2026-07-26): opening and closing baselines captured; Stage 1
reconciliation complete.**

## Baseline identity

**Identifier:** `DC1-20260726T101722Z-9d1a8636`

**Opening capture:** 2026-07-26T10:17:22Z.

| Field | Observation |
| --- | --- |
| HEAD | `9d1a8636230480cd9ae62b5e9d85b3ce77677360` |
| Branch and upstream | `main`, ahead 19 and behind 0 relative to `origin/main` |
| Porcelain status entries | 316 total entries; untracked directories may represent many files |
| Working-tree diff | 185 tracked files, 35,447 additions, 8,214 deletions |
| Index diff | 44 files, 8,281 additions |
| Docs-content scope status | 9 porcelain entries: 3 modified files and 6 untracked paths |
| Opening scope | 235 files after the exclusions below |
| Opening aggregate SHA-256 | `b839a5ba4e8896f4cc54a3bf9a321cfc03ec0cfda23564ca8b7fae839beece70` |

Two consecutive opening fingerprint passes produced the same aggregate hash.
The opening scope includes all non-cache files under `docs_site/`, the root
README and changelog, the docs-site and content design documents, and the six
`repo--docs-*.yml` workflows. The aggregate is the SHA-256 of the sorted
`<file-sha256>  <repository-path>` records.

The Stage 1 research artifacts were created after this opening cutoff. The
closing fingerprint file lists every inventory evidence source separately, and
the evidence log reconciles movement from this opening baseline.

## Closing baseline

**Closing capture:** 2026-07-26T11:28:59Z.

| Field | Observation |
| --- | --- |
| HEAD | `9d1a8636230480cd9ae62b5e9d85b3ce77677360` (unchanged) |
| Branch and upstream | `main`, ahead 19 and behind 0 relative to `origin/main` |
| Porcelain status entries | 665 with `--untracked-files=all`; seven are Stage 1 research files |
| Working-tree diff | 188 tracked files, 33,031 additions, 5,182 deletions |
| Index diff | 47 files, 8,904 additions |
| Closing evidence set | 443 fingerprints, including the executed Python 3.13 native renderer and external Python inventory |
| Opening-scope recheck | 235 files and the original aggregate SHA-256, unchanged |

The wider repository remained active during research. The change in global
status counts is not attributed to Stage 1. Recomputing the exact 235-file
opening scope at closing produced
`b839a5ba4e8896f4cc54a3bf9a321cfc03ec0cfda23564ca8b7fae839beece70`
again, so the authored docs, builder, design, README, changelog, and docs
workflow inputs covered by the opening aggregate did not move.

The closing set deliberately expands the opening boundary. Reference and page
rendering made the Citry package, Citry Core Python and Rust sources, executed
native extension, repository lockfiles, toolchain declarations, package
metadata, and host-cached Python 3.13 Sphinx inventory direct evidence. Every
closing input has an individual size, hash, state, and scope in
`baseline_fingerprints.tsv`. The stable external row records the inventory bytes
without exposing the host's temporary-directory path.

The exact closing aggregate, independent-review repairs, commands, and check
results are recorded in [`evidence_log.md`](evidence_log.md). No Stage 1 command
staged, committed, reverted, or rewrote the maintainer's existing source work.

## Docs-content working state

The opening porcelain entries in scope were:

```text
 M .github/workflows/repo--docs-check.yml
 M CHANGELOG.md
 M README.md
?? docs/design/docs_content.md
?? docs/design/docs_site.md
?? docs_site/content/
?? docs_site/examples/
?? docs_site/snippets/
?? docs_site/static/img/
```

These paths are user work. Stage 1 reads and fingerprints them without staging,
committing, reverting, or changing their content. The new research directory is
the only implementation output authorized by this stage.

## Opening corpus counts

| Unit | Count |
| --- | ---: |
| Markdown content pages | 54 |
| Navigation path entries | 54 |
| Runnable example families | 9 |
| Non-package snippet modules | 5 |
| Generated Reference categories | 15 |
| Docs-site test files | 39 |
| Browser test files | 1 |

Counts establish inventory size only. They do not establish correctness,
reader-job coverage, test sufficiency, or maintainer acceptance.

## Toolchain and host

| Tool | Observation |
| --- | --- |
| Host | macOS 26.3.1 build 25D2128, Darwin 25.3.0 arm64 |
| Git | 2.50.1 (Apple Git-155) |
| Python | 3.13.12 |
| uv | 0.10.12 |
| rustc | 1.98.0-nightly (`14210df0e`, 2026-05-31) |
| cargo | 1.98.0-nightly (`fbb61be30`, 2026-05-26) |
| Node.js | 25.8.1 |
| pnpm | 10.32.1 |

## Opening aggregate command

Run from the repository root:

```sh
{
  find docs_site -type f \
    ! -path 'docs_site/.cache/*' \
    ! -path '*/__pycache__/*' \
    ! -name '*.pyc'
  printf '%s\n' \
    README.md \
    CHANGELOG.md \
    docs/design/docs_content.md \
    docs/design/docs_site.md
  find .github/workflows \
    -maxdepth 1 \
    -type f \
    -name 'repo--docs-*.yml'
} \
  | sort -u \
  | while IFS= read -r task_file; do
      shasum -a 256 "$task_file" \
        | awk -v file="$task_file" '{print $1 "  " file}'
    done \
  | shasum -a 256
```

## Exclusions

- `docs_site/.cache/`, bytecode, and `__pycache__/` are local generated state.
- The local `site/` output is a disposable build and is not source evidence.
- The content inventory records generated output families rather than every
  derived HTML, Markdown, search, or social-card file.
- Private vulnerabilities, credentials, owner-only configuration, and personal
  user evidence are outside this research directory.

## Refresh rule

Before the Stage 1 gate, capture per-file fingerprints for every direct source,
test, guard, and workflow used by the inventory. Compare the live path set and
hashes with the opening scope. If an input moved, repeat only the observations
that depend on it and record the delta in `evidence_log.md`. A changed aggregate
does not by itself invalidate unrelated findings.
