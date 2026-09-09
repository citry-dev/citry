# Rendering performance experiment archive

This branch retains the probes, candidate implementations, raw measurements and
ownership captures from the September 2026 optimization work. It is a reference
branch, not a release branch. Production changes are reviewed separately in
[PR #108](https://github.com/citry-dev/citry/pull/108).

The research starts in
[the performance journal](../docs/design/performance_render_research.md).
The final chart was measured with `benchmarks/publication.py`; its report and
captures are under `benchmarks/results/publication-20260910-release-0.5.0.*`.
See [the benchmark guide](README.md) for dependencies and measurement details.

The archive preserves raw report bytes. Their historical source hashes and
recorded paths describe the original runs, before the `performance_render_*`
and `performance-render` path renames. Commit
`491bd73531300cb9bdaeb5a9e9de36ad9864f679` retains that original layout.
