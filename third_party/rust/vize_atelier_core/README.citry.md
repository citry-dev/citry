# Citry vendored patch for `vize_atelier_core`

This directory is a vendored, locally patched copy of the upstream
`vize_atelier_core` 0.420.0 crate. It is not wholly Citry-authored and is not a
separate hosted fork. The source came from the crates.io archive whose
SHA-256 is
`8db1544b90c72dbe51fe237437ff296d59934e44af7b99686f02cf09d0298d4e`; the
upstream repository is <https://github.com/ubugeeei-prod/vize> at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`. Citry identifies the patched
package as `0.420.0+citry.1`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package. `LICENSE` retains the upstream MIT license text from that
commit.

Relative to that archive, the Citry delta is:

- `Cargo.toml`: records the local `0.420.0+citry.1` package version, registers
  the `v_for_unwrapped_runtime_directives` regression target, and drops the
  upstream `davinci` benchmark target because its source is not vendored here.
- `src/codegen/element/directives.rs`: emits custom-directive modifier names as
  quoted and escaped JavaScript object keys.
- `src/codegen/props/v_model.rs`: emits `v-model` modifier names as quoted and
  escaped JavaScript object keys.
- `src/codegen/v_for/generate.rs`: keeps a keyed single child inside the
  per-row Fragment while still applying the child's custom-directive,
  `v-model`, and `v-show` wrappers and matching closing calls to that child.
- `src/codegen/v_for/helpers.rs`: adds the `has_element_key` helper used by
  the loop generator to detect static and `:key` bindings.
- `src/codegen/v_if/branch.rs`: keeps a keyed single child inside the
  conditional branch Fragment rather than treating the child as the branch's
  identity.
- `tests/v_for_unwrapped_runtime_directives.rs`: adds regression coverage for
  custom, `v-show`, and `v-model` directives in unwrapped loops, modifier-key
  escaping, keyed loop and conditional children, mixed directives, and ordinary
  versus multi-child loop shapes.

All other source and test files are the upstream crate as archived above.
