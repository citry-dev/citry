# CI, releases, and new verification steps

These rules are part of the operating rules in [`CLAUDE.md`](../../CLAUDE.md).
They live in their own file because they apply only to some tasks: adding
a test suite, validator, generated file, CI job, or release gate; waiting
on CI or fixing a CI failure; and promoting or releasing packages.
`CLAUDE.md` tells agents to read this file before starting any of those,
so other tasks do not load it.

## Design verification for the whole delivery loop

Treat the time and maintenance cost of every test, validator, generated file,
CI job, qualification step, and release gate as part of its design. More
verification is not automatically better. Before adding or expanding one,
state:

- the concrete user-facing contract or failure it protects;
- the least expensive boundary that can prove that contract;
- when it runs and how often;
- its expected effect on the local feedback loop, ordinary CI, and the release
  critical path;
- which existing build output or evidence it can reuse; and
- which independent work can run concurrently.

Prefer one proof at the boundary that owns an invariant. Repeat a proof at the
unit, integration, distribution, and release layers only when each layer can
fail in a distinct way. Prefer representative boundary cases over an exhaustive
cross-product when a parser, type checker, schema, or lower-level test already
proves the general rule. Remove or combine scaffolding whose maintenance and
runtime cost outweigh the failure it can catch.

Prepare every knowable release value and generated surface in the release
candidate before qualification, including versions, filenames, hashes, runtime
tuples, and metadata. A source mutation after publication is exceptional: use
it only for a value assigned by the registry that cannot be represented or
resolved from information known before publication. Keep that work off the path
to the final tag. Post-release checks confirm that registries and deployments
serve the qualified bytes; they do not become the first place normal package
correctness is proved.

Before implementing a mandatory step expected to add more than one minute to
the longest routine CI or release path, or any step that creates a publish,
source-update, and requalification cycle, call out the cost in the plan and get
the user's explicit agreement. A safety improvement is incomplete when it makes
routine changes or releases disproportionately slow. Reuse work, narrow the
proof, move it earlier, or run independent work concurrently until the wider
workflow remains practical.

## Keep integration and release loops bounded

Do not use CI as a slow, one-failure-at-a-time debugger. Before promoting or
releasing a large change, map the whole operation: the commits to promote, the
packages and versions to publish, their dependency order, the required local
gates, the required CI checks, and the final public verification. State any
step expected to take significant time.

When CI fails:

1. Inspect every failed job and read each job's complete failure output.
2. Group failures by root cause before editing.
3. Reproduce locally where practical.
4. Fix the complete known failure set in one coherent pass.
5. Run focused checks for the affected surfaces.
6. Send the settled candidate through the required full gate.

Do not create and push a new commit for each newly observed symptom when the
remaining CI results can reveal related failures. Wait for the useful results,
collect them, and make one corrective pass.

While waiting on CI or release runs, wake up on the first failure, not only
when every run has finished. A background command that polls `gh run` until
every run finishes hides an early failure behind the slowest run. So the
background command must:

- exit as soon as any run or job finishes with a failure, a cancellation, or a
  timeout; and
- also exit after at most 20 minutes, even when nothing has changed, so the
  agent wakes and checks a slow or stuck run.

When you wake, read the failed jobs right away, even inside runs that are still
going (`gh run view <run-id> --job <job-id> --log-failed`), rather than waiting
for the whole workflow to finish. Then start a new background command on the
runs that are still going, and keep going until every run that can still reveal
a related failure has finished or a failure already makes the rest moot. Use
that wait to group the failures and reproduce them locally. Waking up early
does not mean fixing each failure as it appears: still make one corrective pass
as described above.

Run expensive repository-wide checks only at meaningful stage boundaries.
During implementation and CI repair, use focused checks. Run the full local
gate once the integrated candidate has settled, and run the required exact-SHA
CI gate on the final release candidate. A small follow-up should rerun the
checks its risk requires and any mandatory final gate, but should not
automatically repeat unrelated qualification work that already passed.

Before beginning a release, prefer one clean release candidate over a chain of
incremental release commits. Separate these stages clearly:

1. Stabilize the complete source change.
2. Pass the local integration gate.
3. Promote the settled candidate.
4. Pass the required exact-SHA CI checks.
5. Publish packages in dependency order.
6. Verify each published artifact once from a clean consumer environment.
7. Run exceptional post-release source updates in one non-blocking batch, only
   when their values could not be prepared in the qualified candidate.

Treat release evidence as belonging to one exact dependency closure, not merely
to a commit that once passed locally:

- **Prove the exact dependency closure before the first tag.** The candidate
  must pass distribution qualification in a clean environment that installs
  built artifacts, never workspace or editable installs. Resolve an unselected
  dependency from its public registry. When the dependency is selected in the
  same release, qualify against wheels built from that exact release commit so
  independent builds can run concurrently. During promotion, publish and
  verify the selected dependency's retained candidate bytes before starting
  the dependent layer.
- **Invalidate stale evidence after a late release correction.** If a package
  version, dependency constraint, release lock, browser runtime tuple,
  distribution verifier, or release-coupled test changes after a green gate,
  stop before tagging. Recalculate the affected package/dependent closure and
  rerun its focused checks plus every mandatory exact-SHA gate from the corrected
  state. Do not cite the earlier full gate for files or dependency bytes it did
  not test.
- **Keep release-coupled values single-sourced.** Tests must derive versions,
  ABI tags, and artifact filenames from the owning manifest, runtime manifest,
  or build metadata, then validate their relationships and immutable public
  artifacts. Do not copy the current version or wheel URL into a second test
  literal. When public-registry evidence is required, fetch it in the release
  workflow and pass it into a deterministic validator; unit tests use synthetic
  registry payloads instead of network access.
