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
//!
//! Unlike the deep entry points in the other modules, these do not start with
//! the template parser's stack guard (`with_enough_stack`): they read and
//! create Python objects as they go, and CPython 3.14 and later check the
//! stack pointer against the thread's own stack, so the work cannot run on
//! a stack segment taken from the heap. Their stack use has to stay small
//! on its own, and when Python has left only its last few KiB of stack, a
//! call here can still overflow it.

mod leaf_json;
mod rows;
mod runs;
mod walk;

use pyo3::prelude::*;
use pyo3::{PyClass, PyClassInitializer};

/// Allocate `value` as a Python object that the cyclic garbage collector
/// does not track.
///
/// PyO3 gives every `#[pyclass]` garbage-collector support, so each new
/// object is tracked and every collection walks it. The `_NativeRow`,
/// `_NativeRun`, `_NativeOccurrence` and `_LeafJson` objects hold only
/// strings, Rust data and objects that cannot refer back to them, so no
/// cycle can pass through them. A page makes thousands of them, so leaving
/// them untracked keeps each collection from walking them all.
pub(crate) fn new_untracked<'py, T>(py: Python<'py>, value: T) -> PyResult<Bound<'py, T>>
where
    T: PyClass + Into<PyClassInitializer<T>>,
{
    let object = Bound::new(py, value)?;
    let pointer = object.as_ptr();
    // Untracking is only valid for a collector-managed type. PyO3 0.30 makes
    // every `#[pyclass]` one; checking keeps a later PyO3 that does not from
    // writing to a header the object lacks.
    // SAFETY: `pointer` is the live object just created, and its type
    // pointer is valid for as long as the object is.
    if unsafe { pyo3::ffi::PyType_IS_GC(pyo3::ffi::Py_TYPE(pointer)) } != 0 {
        // SAFETY: `object` is a live, collector-managed object that no other
        // code holds yet. Untracking only stops the collector from visiting
        // it, and PyO3's deallocation may untrack it again.
        unsafe { pyo3::ffi::PyObject_GC_UnTrack(pointer.cast()) };
    }
    Ok(object)
}

/// Register every class and function of the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    rows::register(module)?;
    runs::register(module)?;
    walk::register(module)?;
    leaf_json::register(module)
}
