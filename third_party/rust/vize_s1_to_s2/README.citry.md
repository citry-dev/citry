# Citry patch for `vize_s1_to_s2`

This directory contains the normalized source published as `vize_s1_to_s2`
0.420.0 on crates.io. The downloaded crate archive has SHA-256
`13d57e14a66a37b558d10c5a46c6c1deb857ffbbfaa7f99118db584646ca096d`.
Citry identifies this patched copy as version `0.420.0+citry.1`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package.

The patch keeps runtime directive wrappers on a single element unwrapped from
`<template v-for>` and quotes every custom-directive modifier object key.
A keyed single element, component, or slot outlet remains inside its loop or
conditional Fragment, keeping row/branch identity separate from the child's
own identity.

The published `tests/emit_for.rs` remains as source, but its test target is
omitted because the published manifest lacks its `vize_atelier_dom`
development dependency and adding that dependency here would create a cycle.
Citry regression coverage uses the standalone `citry_runtime_directives` test
target.

The upstream project is <https://github.com/ubugeeei-prod/vize>. `LICENSE` is
the upstream MIT license text at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`.
