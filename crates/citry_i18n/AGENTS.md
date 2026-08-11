# AGENTS.md - crates/citry_i18n

This crate owns Citry's language-neutral Fluent message runtime. Keep catalog
parsing, validation, linking, and execution here so future Python, JavaScript,
Go, and PHP bindings use the same rules.

For repo-level rules, read [`/CLAUDE.md`](../../CLAUDE.md). The full feature
contract and implementation order live in
[`/docs/design/i18n.md`](../../docs/design/i18n.md).

## Current boundary

The checked compiler owns typed variables, selectors, public message
references, source-unit-local private terms, rich Slot markers, fallback, and
the ICU4X formatter profiles listed in the design. Unsupported formatter
profiles and Fluent operations must still fail with a pointed error. Do not add
a second interpreter in a host-language binding.

`citry_core_py` is only a host binding. New language-neutral behavior belongs
here first, followed by the PyO3 wrapper, `_rust.pyi`, the public Python
wrapper, and tests at both boundaries.

## Verification

```bash
cargo fmt --check
cargo clippy -p citry_i18n --all-targets -- -D warnings
cargo test -p citry_i18n
cargo check -p citry_core_py
```
