//! The `citry_core._rust.native_render` submodule: the PyO3 half of
//! Citry's native render path. The pure-Rust half is the
//! `citry_native_render` crate; the design is in
//! `docs/design/native_render.md`.
//!
//! Every class here is private to Citry (its name starts with `_`), and
//! `citry/_vue/native_render.py` decides whether Citry calls any of it.

mod rows;

use pyo3::prelude::*;

/// Register every class and function of the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    rows::register(module)
}
