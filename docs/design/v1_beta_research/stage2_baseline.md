# Stage 2 baseline

**Status (2026-07-23): Stage 2 pilot opening baseline captured.**

This refresh anchors the bounded Stage 2 change-graph pilot without treating the
active working tree as frozen. An initial fingerprint pair detected concurrent
movement and was discarded. The next two consecutive passes matched.

## Baseline identity

**Identifier:** `B2-20260723T155146Z-cd177d74`

**Capture completed:** 2026-07-23T15:51:46Z.

| Field | Observation |
| --- | --- |
| HEAD | `cd177d7432d9b883dcf936fe81b776672993e1af` |
| Upstream | Ahead 4, behind 0 relative to `origin/main` |
| Dirty paths | 675 total |
| Unstaged state | 152 modified, 5 deleted |
| Untracked state | 518 files, 349,736,255 bytes |
| Staged state | No staged paths observed |
| Unstaged diff | 157 files, 28,683 additions, 4,700 deletions |
| Submodule | `third_party/rust/ruff` at `45bbb4cb`, clean in the outer repository |

[`stage2_baseline_fingerprints.tsv`](stage2_baseline_fingerprints.tsv) records
worktree, index, and HEAD identities for every dirty path. Its own row is an
explicit self-reference marker because finalizing the artifact necessarily
changes its placeholder bytes after the capture.

## Movement since B1

[`stage2_baseline_delta.tsv`](stage2_baseline_delta.tsv) contains 46 evidence
rows:

- 34 existing dirty files changed working-tree bytes;
- 9 paths entered the dirty set; and
- 3 paths left the dirty set.

No index-status, index-blob, or HEAD-blob change was observed. The net six-path
increase reconciles B1's 669 paths with B2's 675.

Four additions are the Stage 1 outputs created after B1, and one is this Stage 2
fingerprint artifact. The remaining path-set movement is in `citry-ui`: two new
support modules and a component package/button implementation entered, while
three earlier button asset files left the dirty set.

Content movement also occurred in the Events TypeScript source, generated
Events browser bundle, dispatcher/routes, several Events tests, UI research,
and Stage 1 evidence files. Stage 2 findings must therefore use B2 or a later
explicit source refresh. B1 remains historical evidence rather than a frozen
repository state.

## Opening verification state

The most recent full gate before B2 failed after concurrent implementation
movement. Cargo formatting, Clippy, Rust tests, Ruff, Pyright, the private client
check, and validators passed. Mypy reported six new `citry-ui` button inheritance
errors. Pytest reported two client payload-budget failures: 522,546 bytes against
a 520,000-byte bundle budget, and 160,272 bytes against a 160,000-byte document
gzip budget. These failures are opening evidence for later technical audit work,
not Stage 2 fixes or proof that the pilot slice caused them.
