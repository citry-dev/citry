//! The `citry_core._rust.native_render` submodule: the PyO3 half of
//! Citry's native render path. The pure-Rust half is the
//! `citry_native_render` crate; the design is in
//! `docs/design/native_render.md`.
//!
//! Every class here is private to Citry (its name starts with `_`), and
//! `citry/_vue/native_render.py` decides whether Citry calls any of it.
//! `rows.rs` holds level A (the row read, the occurrence writer and the
//! call-run ids); `runs.rs` holds level B1 (one object per call run);
//! `walk.rs` holds level C2 (the loop walk of a call run); `leaf_json.rs`
//! holds level B2 (the JSON of ordinary components' leaf data).

mod leaf_json;
mod rows;
mod runs;
mod walk;

use pyo3::prelude::*;

/// Register every class and function of the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    rows::register(module)?;
    runs::register(module)?;
    walk::register(module)?;
    leaf_json::register(module)
}
