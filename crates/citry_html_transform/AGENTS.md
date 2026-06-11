# AGENTS.md - crates/citry_html_transform

Adds or modifies attributes on HTML elements. Two entry points: `mark_html`,
a single-pass scan that splices attributes onto root-level tags and splits the
output around placeholder elements (the serializer's hot path), and
`transform_html`, a `quick-xml` rewrite of every element (the tool for
all-element attribute changes). Small and stable.

For repo-level rules see [`/CLAUDE.md`](../../CLAUDE.md). For cross-crate facts
see [`/docs/agent/INDEX.md`](../../docs/agent/INDEX.md).

## Where to look

- `src/lib.rs` - re-exports `mark_html`, `transform_html`, and their types.
- `src/marker.rs` - the root-marking scan.
- `src/transformer.rs` - the every-element rewrite.
- `tests/marker.rs`, `tests/transformer.rs` - the tests.

## Who depends on it

`crates/citry_core_py` exposes it to Python as the `html_transform` submodule
(wrapped on the Python side in `citry_core/html_transform/`).

## Verifying changes

```bash
cargo test -p citry_html_transform
```
