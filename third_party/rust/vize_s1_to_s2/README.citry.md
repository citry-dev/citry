# Citry's patched copy of `vize_s1_to_s2`

This directory is a locally patched copy of the upstream
`vize_s1_to_s2` 0.420.0 crate. It is not wholly Citry-authored and is not a
separate hosted fork. The source came from the crates.io archive whose
SHA-256 is
`13d57e14a66a37b558d10c5a46c6c1deb857ffbbfaa7f99118db584646ca096d`; the
upstream repository is <https://github.com/ubugeeei-prod/vize> at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`. Citry identifies the patched
package as `0.420.0+citry.2`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package. `LICENSE` retains the upstream MIT license text from that
commit.

Relative to that archive, the Citry delta is:

- `Cargo.toml`: records the local `0.420.0+citry.2` package version, omits the
  upstream `emit_for` test target (the published manifest does not contain its
  `vize_atelier_dom` development dependency, and adding it would create a
  cycle), registers the `citry_runtime_directives` and
  `citry_event_handler_statements` regression targets, and drops the upstream
  `davinci_storage` benchmark target because its source is not included
  here.
- `src/emit/directive.rs`: keeps runtime directive and `v-model` wrappers on a
  single element unwrapped from `<template v-for>`; custom-directive modifier
  names are emitted as quoted and escaped JavaScript object keys.
- `src/emit/tpl.rs`: preserves keyed elements when an unwrapped
  `<template v-for>` would otherwise drop the row Fragment, and preserves
  keyed elements, components, and slots inside conditional Fragments. The
  component and slot loop shapes were already retained.
- `src/emit/prefix.rs`, `src/emit/prefix/rewrite.rs`,
  `src/emit/prefix/shape.rs`, `src/emit/prefix/handler.rs`, and
  `src/emit/on/wrapped.rs`: apply the same statement rule as the patched
  `vize_atelier_core` (statements only in an event handler that contains `;`,
  and handler shape checks that must match the whole text, read after
  TypeScript syntax is removed when `is_ts` is on), so the emitter refuses
  the text that `vize_atelier_core` reports as an invalid expression. They
  also write trailing line comments in an event handler so that they cannot
  hide the closing `}` or the `,` before the next prop.
- `tests/emit_tpl.rs`: adds regression assertions for keyed component and slot
  children inside `v-if` template branches.
- `tests/citry_runtime_directives.rs`: adds Citry coverage for custom,
  `v-show`, and `v-model` wrappers in unwrapped loops, modifier-key escaping,
  keyed loop and conditional children, and mixed runtime directives.
- `tests/citry_event_handler_statements.rs`: adds Citry coverage for the
  statement rule in event handlers, interpolations, and conditions (with and
  without TypeScript when the `typescript` feature is on), for handlers that
  start with a function, for a TypeScript handler reference, and for trailing
  line comments with and without identifier prefixing.

All other source and test files are the upstream crate as archived above.
