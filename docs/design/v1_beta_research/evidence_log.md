# Stage 0 evidence log

**Status (2026-07-23): Stage 0 complete; independent review passed.**

This log records timestamped observations. It does not freeze concurrent
feature development. A later baseline supersedes an earlier observation only
for inputs that changed; both remain useful for explaining movement.

## Baseline B0

**Identifier:** `B0-20260723T132129Z-53aec721`

**Captured:** 2026-07-23T13:21:29Z.

| Field | Observation |
| --- | --- |
| HEAD | `53aec721b7b13309880919f0ff3979f08a6b2245` |
| Branch | `main` |
| Upstream | `origin/main`, ahead 0, behind 0 |
| Submodule | `third_party/rust/ruff` at `45bbb4cb`, clean in the outer repository |
| Dirty paths | 692 total: 173 modified, 5 deleted, 514 untracked |
| Tracked diff | 178 files, 29,940 additions, 4,863 deletions |
| Staged diff | None observed |
| Untracked bytes | 349,260,566 bytes across 514 files |

The complete per-path snapshot is
[`change_ledger.tsv`](change_ledger.tsv). Its path classifications are
provisional routing labels derived from status and filename, not completion or
ownership decisions.

### Dirty paths by top-level area

| Area | Paths |
| --- | ---: |
| `packages/` | 262 |
| `docs_site/` | 212 |
| `docs/` | 151 |
| `crates/` | 32 |
| `.github/` | 10 |
| `TODO/` | 5 |
| `benchmarks/` | 3 |
| `scripts/` | 3 |
| Root and other single-file areas | 14 |

### Provisional path classes

| Class | Paths |
| --- | ---: |
| Source or configuration | 217 |
| Test or fixture | 215 |
| Documentation | 154 |
| Research or design evidence | 64 |
| Workflow or repository configuration | 10 |
| Unclassified | 10 |
| Manifest or lock | 9 |
| Binary or reference | 6 |
| Deletion | 5 |
| Agent or tool configuration | 2 |

Ten paths remain deliberately unclassified rather than being guessed into a
workstream. Later stages will verify every provisional class.

### Untracked size risks

The three root reference archives accounted for 341,300,178 bytes:

| File | Bytes |
| --- | ---: |
| `old-djc.zip` | 250,044,481 |
| `old-chk.zip` | 66,921,766 |
| `old-vuetify.zip` | 24,333,931 |

Other large untracked files included a 390,243-byte TODO screenshot, the
267,719-byte generated Events browser bundle, its 261,281-byte TypeScript
source, and several large tests and design reports. Stage 0 records size and
location only. Provenance, licensing, privacy, generated/source status, and
commit disposition remain later review decisions.

## Moving-baseline evidence

A bounded refresh at 2026-07-23T13:26:02Z observed 694 dirty paths: 174
modified, 5 deleted, and 515 untracked. The tracked diff had moved to 179 files
with 29,979 additions and 4,898 deletions. HEAD, upstream position, and the
submodule commit had not changed.

The closing refresh at 2026-07-23T13:36:46Z observed 698 dirty paths: 174
modified, 5 deleted, and 519 untracked. The tracked diff covered 179 files with
29,991 additions and 4,898 deletions. Untracked files occupied 349,365,707
bytes. HEAD, upstream position, and the submodule commit still had not changed.

[`baseline_history.tsv`](baseline_history.tsv) records these observations.
[`baseline_delta.tsv`](baseline_delta.tsv) accounts for every path/status change
from B0 to the closing baseline. It contains the eight Stage 0 artifact paths,
one design becoming modified, one newly named `citry_ui` test, and four paths
leaving the dirty set during concurrent implementation.

A mechanical replay of the 14 delta rows transformed the 692-path B0 set into
the exact 698-path closing set with zero missing paths or status mismatches.
This proves path/status reconciliation only. B0 did not fingerprint file
contents, so it cannot prove that an already-dirty file kept the same bytes.

This movement proves the baseline protocol is working as intended. B0 remains
the complete initial ledger; the closing baseline and explicit delta account
for subsequent work. Stage 1 must take a new timestamped baseline before using
these observations.

## Independent-review cutoff B0V

During independent review, concurrent work advanced HEAD twice and changed the
index. Stage 0 did not create either commit and did not stage, unstage, or edit
the user's parser work.

**Identifier:** `B0V-20260723T134757Z-558b9735`

**Capture window:** 2026-07-23T13:47:57Z to 2026-07-23T13:47:59Z.

| Field | Observation |
| --- | --- |
| HEAD | `558b97353de7665be221a10aa522310e6d541cab` |
| Upstream | Ahead 2, behind 0 relative to `origin/main` |
| Dirty paths | 688 total |
| Unstaged-only state | 163 modified, 5 deleted |
| Untracked state | 516 files, 349,359,571 bytes |
| Staged-only state | 2 modified, 1 added |
| Staged and unstaged state | 1 modified |
| Unstaged diff | 169 files, 29,343 additions, 4,794 deletions |
| Staged diff | 4 files, 272 additions, 64 deletions |
| Submodule | `third_party/rust/ruff` remained at `45bbb4cb` |

The staged paths at the cutoff were:

- modified in both index and worktree:
  `crates/citry_template_parser/src/ast.rs`;
- modified in the index:
  `crates/citry_template_parser/src/lang/python.rs` and
  `crates/citry_template_parser/tests/tag_compiler_dynamic.rs`; and
- added to the index:
  `crates/citry_template_parser/tests/tag_compiler_client_directives.rs`.

[`review_baseline_fingerprints.tsv`](review_baseline_fingerprints.tsv) records,
for every dirty path, separate index/worktree status, file/missing state, byte
size, a SHA-256 worktree fingerprint, the index mode/blob identity, and the HEAD
mode/blob identity. Two consecutive full fingerprint passes matched exactly;
HEAD and path/status state were stable within both passes. The fingerprint file
itself uses an explicit self-reference marker because it was finalized after
the captured placeholder.

The 16 B0F-to-B0V rows in [`baseline_delta.tsv`](baseline_delta.tsv) record 11
paths leaving the dirty set through the concurrent commits, four staging-state
changes, and the new fingerprint artifact. Changes made after B0V, including
final edits to these research artifacts, belong to the mandatory Stage 1
refresh rather than being silently folded into this historical cutoff.

## Toolchain and host

| Tool | Version |
| --- | --- |
| Host | macOS 26.3.1 build 25D2128, arm64 |
| Git | 2.50.1 (Apple Git-155) |
| Python | 3.13.12 |
| uv | 0.10.12 |
| rustc | 1.98.0-nightly (`14210df0e`, 2026-05-31) |
| cargo | 1.98.0-nightly (`fbb61be30`, 2026-05-26) |
| rustup | 1.29.0; repository-overridden nightly arm64 toolchain |
| Node.js | 25.8.1 |
| pnpm | 10.32.1 |
| GitHub CLI | 2.92.0 |
| maturin | 1.10.2 |
| Ruff | 0.14.10 |
| mypy | 1.19.1 |

## Repository inventories

- [`manifest_inventory.tsv`](manifest_inventory.tsv) is the B0 manifest and
  lockfile list. It contains 19 first-party manifest/toolchain entries, one
  repository configuration entry, and 114 vendored Ruff entries. Later
  metadata work uses the first-party boundary. The ignored local
  `.python-version` is recorded only as an environment observation.
- [`workflow_inventory.tsv`](workflow_inventory.tsv) lists 19 working-tree
  workflow files. Public committed GitHub state exposed 16 active workflows.
- [`design_artifact_inventory.tsv`](design_artifact_inventory.tsv) is the B0
  recursive inventory of 150 existing files under `docs/design/`: 124 Markdown,
  13 JavaScript, and 13 Python files. Its state column also includes the tracked
  deletion of `docs/design/extension_commands.md`, so Stage 3 cannot omit that
  design. Stage 0 artifacts created afterward appear in the baseline deltas.
  The closing repository inventory had 159 paths: 158 existing files and that
  tracked deletion.
- The first-party working tree contained five Python `pyproject.toml` files,
  including the newly observed `packages/py/citry_ui/pyproject.toml`; five Cargo
  manifests; two JavaScript `package.json` files; two uv locks; one Cargo lock;
  one pnpm lock; and one pnpm workspace file.

Ignored caches, virtual environments, build output, and dependency-install
trees are excluded. Vendored Ruff files are counted separately and are not
treated as first-party metadata. The tracked Ruff submodule commit is recorded.

## Public-service snapshot

The sanitized public and non-sensitive owner-readable observations are in
[`public_service_snapshot.md`](public_service_snapshot.md). The capture window
was 2026-07-23T13:21:41Z to 2026-07-23T13:25:56Z.

## Repository gate observation

The full required command was attempted after the initial capture:

```console
python scripts/check.py --reporter agent
```

That attempt failed on Ruff, mypy, and pytest while concurrent `citry_ui` work
was changing. The closing delta then showed that the colliding
`citry_ui/tests/test_registration.py` path had been replaced by a uniquely
named test, invalidating the pytest observation. Stage 0 made no source fix.

The same full command was rerun against the B0F inputs. It passed:

| Phase | Closing result |
| --- | --- |
| Cargo format | Passed |
| Cargo Clippy | Passed |
| Cargo tests | Passed |
| Ruff check | Passed |
| Ruff format | Passed |
| mypy | Passed |
| Pyright | Passed |
| `citry-client` | Passed |
| pytest | Passed |
| Custom validators | Passed |

The change between attempts is recorded as concurrent baseline movement, not as
work performed by Stage 0. The pass proves only the repository gate on B0F-era
inputs at HEAD `53aec721`. The later commits and staged changes at B0V are
fingerprinted but were not represented as another full-gate result. Stage 1
must refresh and rerun evidence it needs.

## Exact local commands

Core identity and status:

```console
date -u +%Y-%m-%dT%H:%M:%SZ
git rev-parse HEAD
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
git status --porcelain=v2 --branch
git submodule status --recursive
git -c core.quotepath=false status --porcelain=v1 --untracked-files=all
git diff --shortstat
git diff --cached --shortstat
git diff --numstat
python scripts/check.py --reporter agent
```

Size and inventory inputs:

```console
git ls-files --others --exclude-standard -z
stat -f '%z\t%N'
git ls-files -co --exclude-standard
rg --files .github/workflows
rg --files docs/design
```

Tool versions used each tool's `--version` command. Platform observations used
`uname`, `sw_vers`, and `sysctl -n hw.machine`.

The B0V fingerprint command used Git porcelain v1 with NUL-separated paths,
SHA-256 over working-tree bytes, `git ls-files --stage -z` for index identities,
and `git ls-tree -r -z HEAD` for HEAD identities. It ran two consecutive passes
and accepted the cutoff only when fingerprints, HEAD, and path/status state
matched.

## Command limitations

- Counts are timestamped observations, not atomic filesystem transactions.
- An initial untracked-size attempt that encountered incompatible local Ruby
  behavior was discarded; the successful `stat`-based result is recorded.
- A broad metadata search that descended into the Ruff submodule was discarded.
  Authoritative first-party counts use outer-repository Git inventory and
  explicitly exclude submodule internals.
- No file contents from archives, ignored private configuration, credentials,
  secrets, audit logs, or private user/project data were captured.
