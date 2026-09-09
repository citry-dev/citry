# Render ownership relationships

`citry_ownership` calculates which component calls, instances, slot fills and
physical regions to retire when a component replaces its output. Selected
output and fills used by later output can survive that replacement.

The crate accepts numeric identifiers and returns row indexes and receiver
changes. The host binding owns record storage, identifier conversion, applying
changes and observable queue settlement order. This internal crate serves
the regular Python binding and the standalone native ownership experiment.
Runtime activation is tracked in the [integration plan](https://github.com/citry-dev/citry/blob/37007427bc7157085f8ce4d55ff73155d873764f/benchmarks/native_ownership_qualification/integration.md).

Populate a fresh `Graph`, call `index()` once, then call `selection()` and
`plan()` without changing its rows. Discard the graph if indexing fails.
Duplicate invocation, fill or region IDs return an error. Unknown explicit
region IDs are ignored; visited sets terminate cyclic ancestry. Identifiers
use `usize` or `u64`, and order cutoffs use `u64`. A host with a wider value
domain must validate conversion and supply its own fallback before applying
any changes.

`Plan.calls` retains discovery order so a host can reconstruct its required
queue settlement order. The other row lists preserve table order.
