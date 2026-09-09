# AGENTS.md - crates/citry_ownership

Read [`/CLAUDE.md`](../../CLAUDE.md) first.

`src/lib.rs` calculates which component calls, instances, fills and physical
regions survive replacement of component output. It uses numeric identifiers
and has no host-language dependency. See [README.md](README.md) for the input
lifecycle and [the integration plan](https://github.com/citry-dev/citry/blob/37007427bc7157085f8ce4d55ff73155d873764f/benchmarks/native_ownership_qualification/integration.md)
for the staged Python binding work.

Run `cargo test -p citry_ownership` and
`cargo clippy -p citry_ownership --all-targets -- -D warnings`.
