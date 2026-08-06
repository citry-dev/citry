# Stage 1 baseline

**Status (2026-07-23): Stage 1 opening baseline captured.**

This refresh anchors Stage 1 findings to current repository content without
changing the user's working tree or index.

## Baseline identity

**Identifier:** `B1-20260723T141813Z-cd177d74`

**Capture window:** 2026-07-23T14:18:13Z to 2026-07-23T14:18:14Z.

| Field | Observation |
| --- | --- |
| HEAD | `cd177d7432d9b883dcf936fe81b776672993e1af` |
| Upstream | Ahead 4, behind 0 relative to `origin/main` |
| Dirty paths | 669 total |
| Unstaged state | 152 modified, 5 deleted |
| Untracked state | 512 files, 349,463,852 bytes |
| Staged state | No staged paths observed |
| Unstaged diff | 157 files, 28,644 additions, 4,700 deletions |
| Submodule | `third_party/rust/ruff` at `45bbb4cb`, clean in the outer repository |

Two consecutive fingerprint passes matched exactly. HEAD and path/status state
were stable within both passes.

## Movement since the Stage 0 review cutoff

Four commits separated the original public `main` baseline from B1:

```text
d8c166e docs: update claude/agent files with reviewer step + other
558b973 chore: update deps, add npm deps
bce933a refactor: parser bugs / cleanup
cd177d7 refactor: rust tests migration + harderinng
```

The commit subjects are recorded verbatim. Their accuracy as descriptions of
the underlying changes is not assumed.

[`stage1_baseline_delta.tsv`](stage1_baseline_delta.tsv) compares B1 with the
Stage 0 review cutoff B0V. Its 47 evidence rows include:

- 21 paths leaving the dirty set;
- 2 new Stage 1 artifact paths;
- 1 staging/status transition;
- 18 common dirty paths whose working-tree SHA-256 changed;
- 2 common paths whose index blob changed; and
- 3 common paths whose HEAD blob changed.

The categories can overlap for one path. Unlike the original B0 delta, this
comparison detects changes to files that remained dirty at both observations.

## Fingerprint scope

[`stage1_baseline_fingerprints.tsv`](stage1_baseline_fingerprints.tsv) records
separate index/worktree status, file or missing state, byte size, SHA-256 of
working-tree bytes, index mode/blob, and HEAD mode/blob for all 669 dirty paths.
The fingerprint artifact uses an explicit self-reference marker because its
final contents necessarily follow the captured placeholder.

This document, the delta, and later Stage 1 research artifacts are finalized
after B1. Their later bytes do not alter the historical cutoff. Any Stage 1
finding must cite B1 or a later explicit refresh when its source inputs changed.

## Charter evidence refresh

At 2026-07-23T14:34:38Z, HEAD remained `cd177d7432d9`. The dirty-path status set
matched B1 except for the four expected Stage 1 outputs created after capture:
the delta, internal evidence note, external norms note, and product/beta
charter. A SHA-256 comparison of all 33 existing local source files cited by the
internal note and charter found no content movement from B1. The charter can
therefore use B1 without silently mixing later source revisions.

At 2026-07-23T14:41:58Z, HEAD and the 673-path status set were unchanged from
that refresh. `python scripts/check.py --reporter agent` passed all ten phases:
Cargo format, Clippy, Rust tests, Ruff lint and formatting, mypy, Pyright, the
private client check, pytest with coverage, and repository validators. This is
a current repository-gate observation, not installed-artifact, browser-matrix,
or live-project evidence.

After the independent-review repairs, a new 2026-07-23T14:49:10Z refresh found
HEAD still at `cd177d7432d9` and the status set still at 673 paths. All 36 current
local source files cited by the internal note and charter remained byte-identical
to their B1 contents. This refresh supersedes the 14:34 source-set count for the
repaired charter without rewriting that historical observation. The repository
gate was rerun after these repairs at 2026-07-23T14:54:54Z with unchanged HEAD
and status counts. It again passed all ten phases listed above.
