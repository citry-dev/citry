# Stage 2 reader-research baseline

**Status (2026-07-26): evidence boundary, invalidation rules, and closing
requirements recorded.**

## Identity

**Identifier:** `DC2-20260726T122608Z-6ad74ee1`

**Opening capture:** 2026-07-26T12:26:08Z.

| Field | Observation |
| --- | --- |
| HEAD | `6ad74ee165f846b3e1c59d7292e39ebdc1d3545e` |
| Branch and upstream | `main`, ahead 20 and behind 0 relative to `origin/main` |
| Porcelain status entries | 616 with `--untracked-files=all` |
| Working-tree diff | 142 tracked files, 31,314 additions, 3,475 deletions |
| Index diff | none |
| Public `main` at observation | `53aec721b7b13309880919f0ff3979f08a6b2245` |
| Stage 1 fingerprint state | Invalid at opening because two renderer inputs had changed after the closing capture |

The working tree is active and most changes are maintainer work outside this
stage. The Stage 2 identifier names the research opening, not a claim that the
entire dirty tree stayed frozen. Each repository-local evidence row therefore
records the SHA-256 of its source file. The validator rejects that row if the
file later changes.

Public service observations describe the public repository and deployment,
which remained behind the active local checkout. A local page or workflow is
therefore repository evidence only unless a separate public observation shows
that it is deployed.

The opening Stage 1 validator reported changed bytes in:

- `packages/py/citry/citry/ext/dependencies/client/citry.js`;
- `packages/py/citry/citry/ownership_manifest.py`.

Those changes invalidate rendered-output measurements that depend on the
files. They do not invalidate reader-job evidence from independent product,
adapter, test, support, or migration sources. Reconcile them before relying on
the Stage 1 closing build measurements again.

## Approved evidence boundary

Stage 2 may retain:

- repository-local source, tests, current content, accepted or provisional
  designs, and repeatable command results;
- public GitHub repository metadata, Issues, Discussions state, and other
  public primary sources observed on a stated date;
- aggregate, non-identifying maintainer observations already recorded in an
  approved repository artifact.

Stage 2 does not inspect or retain private support messages, private
applications, credentials, vulnerability reproductions, analytics exports,
recordings, proprietary application data, or identifying cohort data. A later
expansion requires an approved purpose, consent where applicable, retention,
access, deletion, and storage rule.

## Evidence unavailable at opening

- privacy-approved documentation search queries or analytics;
- a sanitized support-channel corpus;
- reader interviews, surveys, task-based usability sessions, abandonment
  observations, or beta-cohort results;
- direct demographic evidence that distinguishes professional teams,
  independent developers, learners, or ecosystem authors;
- representative `demo/<host>/` applications, recorded production deployments,
  or an isolated upgrade rehearsal in the repository;
- a durable, sanitized maintainer-experience dataset beyond decisions already
  recorded in repository documents.

The research can still rank repository-demonstrated jobs. Frequency and
demographic conclusions that would require these sources remain inference,
with lower confidence and an explicit later falsifying check.

## Invalidation and refresh

- A changed local source hash invalidates only evidence rows that name that
  source. Re-read it, revise affected observations, and record the new hash.
- A public observation is time-bound to its observation date. Re-check it
  before publishing a current service or support-route claim.
- A passing focused test supports only the behavior it exercises. It does not
  establish released-artifact, representative-application, usability, or
  support-matrix evidence.
- A provisional design supports product priority and research direction, not a
  current evergreen product promise.
- Unavailable evidence remains an explicit absence. It cannot support a job or
  silently become an inference presented as observation.

At the Stage 2 close, validate all row-level source hashes, reconcile the wider
Stage 1 fingerprint delta, rerun the focused checks affected by any accepted
change, and record the exact result in `evidence_log.md`.
