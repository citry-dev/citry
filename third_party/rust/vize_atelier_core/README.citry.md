# Citry patch for `vize_atelier_core`

This directory contains the normalized source published as
`vize_atelier_core` 0.420.0 on crates.io. The downloaded crate archive has
SHA-256 `8db1544b90c72dbe51fe237437ff296d59934e44af7b99686f02cf09d0298d4e`.
Citry identifies this patched copy as version `0.420.0+citry.1`.

The registry archive's `Cargo.toml.orig` is preserved byte-for-byte as
`Cargo.upstream.toml`, because Cargo reserves `Cargo.toml.orig` when building
a source package.

The patch changes `src/codegen/v_for/generate.rs` so a single element unwrapped
from `<template v-for>` supplies the custom-directive, `v-model`, and `v-show`
runtime checks and closing calls. A keyed single child remains inside its loop
or conditional Fragment, and custom-directive modifier object keys are quoted.
Regression coverage lives in `tests/v_for_unwrapped_runtime_directives.rs`.

The upstream project is <https://github.com/ubugeeei-prod/vize>. `LICENSE` is
the upstream MIT license text at commit
`b7b308966c9baf4aa32d053448dc6d5ace6359c2`.
