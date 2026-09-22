# Citry vendored patch for `vize_s1_to_s2`

This directory is a vendored, locally patched copy of the upstream
`vize_s1_to_s2` 0.420.0 crate. It is not wholly Citry-authored and is not a
separate hosted fork. The source came from the crates.io archive whose
SHA-256 is
`13d57e14a66a37b558d10c5a46c6c1deb857ffbbfaa7f99118db584646ca096d`; the
upstream repository is <https://github.com/ubugeeei-prod/vize> at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`. Citry identifies the patched
package as `0.420.0+citry.1`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package. `LICENSE` retains the upstream MIT license text from that
commit.

Relative to that archive, the Citry delta is:

- `Cargo.toml`: records the local `0.420.0+citry.1` package version, omits the
  upstream `emit_for` test target (the published manifest does not contain its
  `vize_atelier_dom` development dependency, and adding it would create a
  cycle), registers the `citry_runtime_directives` regression target, and drops
  the upstream `davinci_storage` benchmark target because its source is not
  vendored here.
- `src/emit/directive.rs`: keeps runtime directive and `v-model` wrappers on a
  single element unwrapped from `<template v-for>`; custom-directive modifier
  names are emitted as quoted and escaped JavaScript object keys.
- `src/emit/tpl.rs`: preserves keyed elements when an unwrapped
  `<template v-for>` would otherwise drop the row Fragment, and preserves
  keyed elements, components, and slots inside conditional Fragments. The
  component and slot loop shapes were already retained.
- `tests/emit_tpl.rs`: adds regression assertions for keyed component and slot
  children inside `v-if` template branches.
- `tests/citry_runtime_directives.rs`: adds Citry coverage for custom,
  `v-show`, and `v-model` wrappers in unwrapped loops, modifier-key escaping,
  keyed loop and conditional children, and mixed runtime directives.

All other source and test files are the upstream crate as archived above.
