# Third-party dependencies

This directory contains upstream git submodules and vendored dependencies that are not part of our core codebase.

## Structure

Third-party dependencies are organized by language:

- `rust/` - Rust crates and dependencies
- `py/` - Python packages
- `js/` - JavaScript/TypeScript packages
- `go/` - Go packages
- `php/` - PHP packages

## Current dependencies

### Rust

- **ruff** (`rust/ruff/`) - Python parser and AST library used by `python_safe_eval`

  - **URL**: https://github.com/astral-sh/ruff.git
  - **Used by**: `crates/python_safe_eval`
  - **License**: MIT
  - **Update policy**: Pin to specific tags/commits, update intentionally

  NOTE: While Rust's Cargo has a feature to define a dependency via git URL,
  this didn't work for unknown reason. And Ruff's Python parser is an internal package. Hence why this is defined as git submodule.

### Patched Vize compiler crates

Citry vendors two patched Vize 0.420.0 compiler crates under `rust/`:

- **`vize_atelier_core`** (`rust/vize_atelier_core/`) comes from the crates.io
  source archive `vize_atelier_core-0.420.0.crate`, whose SHA-256 is
  `8db1544b90c72dbe51fe237437ff296d59934e44af7b99686f02cf09d0298d4e`.
- **`vize_s1_to_s2`** (`rust/vize_s1_to_s2/`) comes from the crates.io source
  archive `vize_s1_to_s2-0.420.0.crate`, whose SHA-256 is
  `13d57e14a66a37b558d10c5a46c6c1deb857ffbbfaa7f99118db584646ca096d`.

Both archives come from the upstream Vize repository at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`
([`ubugeeei-prod/vize`](https://github.com/ubugeeei-prod/vize/commit/b7b308966c9baf4aa32d053448dc6d5ace6359c2)).
Citry identifies the patched packages as version `0.420.0+citry.1`. They are
MIT-licensed; the exact Citry patch inventory is recorded in each crate's
[`README.citry.md`](rust/vize_atelier_core/README.citry.md) and
[`README.citry.md`](rust/vize_s1_to_s2/README.citry.md).

When `citry_vue_compiler` consumes these source dependencies, Cargo compiles
them into `citry_core`. They have no separate publication or deployment. The
vendored copies are updated intentionally and should be removed when the fixes
ship in a compatible released Vize version and the Citry regression tests pass.

## Adding a new submodule

See the [Common Development Tasks](../docs/codebase.md#adding-a-git-submodule) documentation for instructions on adding new git submodules.

## License compliance

All third-party dependencies should have their licenses documented here. Ensure compliance with all upstream licenses when using these dependencies.
