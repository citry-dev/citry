//! Level B2 of the native render path: Rust writes the JSON of an ordinary
//! component's leaf data (and of a `simple='vue'` row's, when Rust did not
//! read the row). The design and every error mode are in
//! `docs/design/native_render.md`.
//!
//! A leaf program is a component template compiled into one reusable program
//! with no component or slot nodes; its leaf data is the values that program
//! sends to the browser. When assembly (`assemble_typed_render` in
//! `citry/_vue/direct_capture.py`) records a component occurrence whose body
//! is one leaf program (an ordinary component, or a `simple='vue'` row that
//! Rust did not read), Python copies each leaf value
//! into the occurrence's `preparedData` dict (with `_json_plain` or
//! `_copy_evaluated_json`), and serialize later writes that dict as JSON.
//! On the precompile path, where no browser hook reads or changes prepared
//! data, assembly asks Rust first:
//!
//! 1. `_leaf_values_json(values, placeholder)` writes each value's JSON, byte
//!    for byte what `_script_json(_json_plain(value))` writes, and returns a
//!    [`LeafJson`] holding it, or a `str` naming why Rust declines.
//! 2. Python stores `placeholder` (one shared Python object that JSON
//!    encoding refuses) under each leaf key instead of a copy, so every
//!    reader of the dict's keys behaves as before, and maps the occurrence
//!    id to the [`LeafJson`] for the manifest encoder.
//! 3. `_encode_occurrences` (in `rows.rs`) writes that occurrence's item
//!    through [`write_leaf_occurrence`], putting each placeholder's JSON at
//!    its sorted key position.
//!
//! Rust writes only exact plain types: `None`, `bool`, an `int` within
//! `i64`, a finite `float` (as Python's `repr` writes it), a `str` with a
//! UTF-8 form, and exact `dict` (with exact `str` keys), `list` and `tuple`
//! containers. For anything else, a container that holds itself, or nesting
//! deeper than [`MAX_DEPTH`], Rust declines the whole leaf, and Python's own
//! conversion then runs for it, raising its own errors (its refusal of a
//! `citry.Secret`, for example). No Python code runs while Rust writes.
//!
//! [`LeafJson`] does not define `__traverse__`, so the cyclic garbage
//! collector does not track it: it holds Rust strings and the placeholder,
//! which is a module-level object that never refers to a `_LeafJson`.

use std::collections::HashMap;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};

use citry_native_render::write_json_str;

use super::rows::{python_float_repr, without_panics};

/// Deeper data declines, and Python's conversion handles it (raising its
/// own `RecursionError` where the interpreter's limit is reached). It is
/// far below Python's default limit of 1,000 frames, of which `_json_plain`
/// uses one per level (two on Python 3.10 and 3.11, where a comprehension
/// has its own frame), and far above the nesting of any real leaf data.
const MAX_DEPTH: usize = 200;

/// Why Rust declines a leaf. Python receives the name as a `str` and then
/// converts the leaf itself; tests read it to show which case declined.
#[derive(Clone, Copy, Debug)]
enum Decline {
    /// A type other than the exact plain types, a dict key that is not an
    /// exact `str`, or leaf data that is not an exact dict.
    NotPlain,
    /// `inf` or `nan`, which Python refuses with its own message.
    NonFinite,
    /// An `int` outside `i64`. A very large int can pass Python's limit on
    /// int-to-text digits, where Python raises, so Python writes every int
    /// outside `i64`.
    BigInt,
    /// A `str` or a key with a lone surrogate (no UTF-8 form).
    NotUtf8,
    /// A container that holds itself, which Python refuses.
    Cycle,
    /// Nesting deeper than `MAX_DEPTH`.
    TooDeep,
}

impl Decline {
    fn as_str(self) -> &'static str {
        match self {
            Decline::NotPlain => "not_plain",
            Decline::NonFinite => "non_finite",
            Decline::BigInt => "big_int",
            Decline::NotUtf8 => "not_utf8",
            Decline::Cycle => "cycle",
            Decline::TooDeep => "too_deep",
        }
    }
}

/// A value Rust refused, or an error Python raised while Rust read it (only
/// a float's `repr` can raise, when memory runs out).
enum WriteError {
    Refused(Decline),
    Python(PyErr),
}

impl From<PyErr> for WriteError {
    fn from(error: PyErr) -> Self {
        WriteError::Python(error)
    }
}

/// Write `value` as `_script_json(_json_plain(value))` would, or refuse it.
///
/// `open` holds the address of each container on the path from the top
/// value down to this one, which is how a container that holds itself is
/// found.
fn write_value(
    out: &mut String,
    value: &Bound<'_, PyAny>,
    depth: usize,
    open: &mut Vec<usize>,
) -> Result<(), WriteError> {
    if value.is_none() {
        out.push_str("null");
        return Ok(());
    }
    // With exact type checks the order does not matter; this one mirrors
    // `json.dumps`, which writes a bool as `true` or `false`.
    if value.is_exact_instance_of::<PyBool>() {
        out.push_str(if value.is_truthy()? { "true" } else { "false" });
        return Ok(());
    }
    if value.is_exact_instance_of::<PyInt>() {
        let number = value
            .extract::<i64>()
            .map_err(|_| WriteError::Refused(Decline::BigInt))?;
        out.push_str(&number.to_string());
        return Ok(());
    }
    if let Ok(number) = value.cast_exact::<PyFloat>() {
        let number = number.value();
        if !number.is_finite() {
            return Err(WriteError::Refused(Decline::NonFinite));
        }
        // `json.dumps` writes a float with `float.__repr__`, which is this
        // CPython formatter.
        out.push_str(&python_float_repr(value.py(), number)?);
        return Ok(());
    }
    if let Ok(text) = value.cast_exact::<PyString>() {
        let text = text
            .to_str()
            .map_err(|_| WriteError::Refused(Decline::NotUtf8))?;
        write_json_str(out, text);
        return Ok(());
    }
    let dict = value.cast_exact::<PyDict>().ok();
    let list = value.cast_exact::<PyList>().ok();
    let tuple = value.cast_exact::<PyTuple>().ok();
    if dict.is_none() && list.is_none() && tuple.is_none() {
        // A `Const` marker, translated text, a `Secret`, a subclass: each
        // gets Python's own conversion or refusal.
        return Err(WriteError::Refused(Decline::NotPlain));
    }
    if depth >= MAX_DEPTH {
        return Err(WriteError::Refused(Decline::TooDeep));
    }
    // Only containers still open on the current path count: the same list
    // written twice side by side is not a cycle, and Python writes it twice.
    let address = value.as_ptr() as usize;
    if open.contains(&address) {
        return Err(WriteError::Refused(Decline::Cycle));
    }
    open.push(address);
    let written = if let Some(dict) = dict {
        write_dict(out, dict, depth, open)
    } else if let Some(list) = list {
        write_items(out, list.iter(), depth, open)
    } else if let Some(tuple) = tuple {
        // `_json_plain` turns a tuple into a list.
        write_items(out, tuple.iter(), depth, open)
    } else {
        Ok(())
    };
    open.pop();
    written
}

/// Write a list or tuple's items as a JSON array.
fn write_items<'py>(
    out: &mut String,
    items: impl Iterator<Item = Bound<'py, PyAny>>,
    depth: usize,
    open: &mut Vec<usize>,
) -> Result<(), WriteError> {
    out.push('[');
    for (index, item) in items.enumerate() {
        if index > 0 {
            out.push(',');
        }
        write_value(out, &item, depth + 1, open)?;
    }
    out.push(']');
    Ok(())
}

/// Write an exact dict with its keys sorted, as `sort_keys=True` sorts them.
fn write_dict(
    out: &mut String,
    dict: &Bound<'_, PyDict>,
    depth: usize,
    open: &mut Vec<usize>,
) -> Result<(), WriteError> {
    let mut entries: Vec<(String, Bound<'_, PyAny>)> = Vec::with_capacity(dict.len());
    for (key, item) in dict.iter() {
        // `_json_plain` accepts a str subclass key and writes `str(key)`,
        // which can run user code, so only an exact str is written here.
        let key = key
            .cast_exact::<PyString>()
            .map_err(|_| WriteError::Refused(Decline::NotPlain))?;
        let key = key
            .to_str()
            .map_err(|_| WriteError::Refused(Decline::NotUtf8))?
            .to_owned();
        entries.push((key, item));
    }
    // UTF-8 byte order is code point order, which is how Python compares two
    // strs; a dict's keys are distinct, so the order is total.
    entries.sort_unstable_by(|left, right| left.0.cmp(&right.0));
    out.push('{');
    for (index, (key, item)) in entries.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        write_json_str(out, key);
        out.push(':');
        write_value(out, item, depth + 1, open)?;
    }
    out.push('}');
    Ok(())
}

/// The JSON Rust wrote for each value of one leaf's data, by key.
#[pyclass(frozen, name = "_LeafJson", module = "citry_core._rust.native_render")]
pub struct LeafJson {
    json: HashMap<String, String>,
    /// The object Python stores under each of these keys instead of a copy;
    /// the encoder finds the keys to fill by this object's identity.
    placeholder: Py<PyAny>,
}

#[pymethods]
impl LeafJson {
    /// The number of leaf values Rust wrote.
    fn __len__(&self) -> usize {
        self.json.len()
    }
}

/// `_leaf_values_json(values, placeholder)`: write the JSON of each value of
/// one leaf's data, or return a `str` naming why Rust declines.
///
/// Python stores `placeholder` under each of the leaf's keys when this
/// returns a [`LeafJson`]. A `values` that is not an exact dict, or a key
/// that is not an exact `str`, declines with `not_plain`. `placeholder` must
/// never refer to a [`LeafJson`]: the collector does not track one, so such
/// a cycle would never be freed. Citry passes one module-level object.
#[pyfunction(name = "_leaf_values_json")]
pub fn leaf_values_json<'py>(
    values: &Bound<'py, PyAny>,
    placeholder: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    let py = values.py();
    without_panics(|| {
        let decline = |reason: Decline| Ok(PyString::new(py, reason.as_str()).into_any());
        let Ok(dict) = values.cast_exact::<PyDict>() else {
            return decline(Decline::NotPlain);
        };
        let mut json = HashMap::with_capacity(dict.len());
        let mut open = Vec::new();
        for (key, value) in dict.iter() {
            let Ok(key) = key.cast_exact::<PyString>() else {
                return decline(Decline::NotPlain);
            };
            // The encoder looks each key up by its text, so a key without
            // a UTF-8 form declines; Citry's leaf keys are ASCII names.
            let Ok(key) = key.to_str() else {
                return decline(Decline::NotUtf8);
            };
            let mut out = String::new();
            match write_value(&mut out, &value, 0, &mut open) {
                Ok(()) => {}
                Err(WriteError::Refused(reason)) => return decline(reason),
                Err(WriteError::Python(error)) => return Err(error),
            }
            json.insert(key.to_owned(), out);
        }
        let leaf = LeafJson {
            json,
            placeholder: placeholder.clone().unbind(),
        };
        Ok(Bound::new(py, leaf)?.into_any())
    })
}

/// Write `value` with `fallback` (`_script_json`). `_script_json` writes a
/// value the same way alone as inside a dict or list, so writing one entry
/// by itself gives the same bytes.
fn write_fallback(
    out: &mut String,
    fallback: &Bound<'_, PyAny>,
    value: &Bound<'_, PyAny>,
) -> PyResult<()> {
    let encoded = fallback.call1((value,))?;
    let text = encoded
        .cast::<PyString>()
        .map_err(|_| PyValueError::new_err("the manifest fallback did not return a str"))?;
    out.push_str(text.to_str()?);
    Ok(())
}

/// Write a value Rust can write exactly without calling Python (`None`, an
/// exact `str` with a UTF-8 form, an exact empty dict), or else through
/// `fallback`. The item's ids and names are such strs, so most of an item
/// is written here.
fn write_simple(
    out: &mut String,
    fallback: &Bound<'_, PyAny>,
    value: &Bound<'_, PyAny>,
) -> PyResult<()> {
    if value.is_none() {
        out.push_str("null");
        return Ok(());
    }
    if let Ok(text) = value.cast_exact::<PyString>()
        && let Ok(text) = text.to_str()
    {
        write_json_str(out, text);
        return Ok(());
    }
    if value
        .cast_exact::<PyDict>()
        .is_ok_and(|dict| dict.is_empty())
    {
        out.push_str("{}");
        return Ok(());
    }
    write_fallback(out, fallback, value)
}

/// Write a dict's entries in `sorted()` key order, each key as `json.dumps`
/// writes it, then `:` and what `value` writes for the entry.
fn write_sorted<'py>(
    out: &mut String,
    dict: &Bound<'py, PyDict>,
    fallback: &Bound<'py, PyAny>,
    mut value: impl FnMut(&mut String, &Bound<'py, PyAny>, &Bound<'py, PyAny>) -> PyResult<()>,
) -> PyResult<()> {
    // Python's own list sort, so the keys come out in the order
    // `sort_keys=True` gives them, a key without a UTF-8 form included.
    // Assembly writes only exact str keys, so the sort runs no user code.
    let keys = dict.keys();
    keys.sort()?;
    out.push('{');
    for (index, key) in keys.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        // `json.dumps` writes a str key as it writes a str value. It writes
        // an int or float key as text in quotes, which `write_simple` would
        // not, but assembly checks every key is an exact str, so any other
        // key is refused here.
        if !key.is_instance_of::<PyString>() {
            return Err(PyValueError::new_err("a manifest item key is not a str"));
        }
        write_simple(out, fallback, &key)?;
        out.push(':');
        // `fallback` is Python code, so the dict is read again by key rather
        // than trusted to be unchanged since the keys were taken.
        let item = dict
            .get_item(&key)?
            .ok_or_else(|| PyValueError::new_err("a manifest key vanished while it was written"))?;
        value(out, &key, &item)?;
    }
    out.push('}');
    Ok(())
}

/// Write one leaf occurrence's manifest item as `_script_json(item)`
/// would, with `leaf`'s JSON at each placeholder in its `preparedData`.
///
/// Every other value is written by [`write_simple`], so the item may carry
/// entries assembly does not make, such as the Events extension's
/// `eventContext`, and they are written as `_script_json` writes them.
pub(super) fn write_leaf_occurrence<'py>(
    out: &mut String,
    item: &Bound<'py, PyDict>,
    leaf: &LeafJson,
    fallback: &Bound<'py, PyAny>,
) -> PyResult<()> {
    let py = item.py();
    let placeholder = leaf.placeholder.bind(py);
    // Each placeholder sits under its own key, so counting them shows whether
    // every value Rust wrote reached the item.
    let mut filled = 0usize;
    write_sorted(out, item, fallback, |out, key, value| {
        let is_prepared = key
            .cast_exact::<PyString>()
            .is_ok_and(|key| key.to_str().is_ok_and(|key| key == "preparedData"));
        if !is_prepared {
            return write_simple(out, fallback, value);
        }
        let prepared = value
            .cast_exact::<PyDict>()
            .map_err(|_| PyValueError::new_err("leaf occurrence preparedData is not a dict"))?;
        write_sorted(out, prepared, fallback, |out, key, value| {
            if !value.is(placeholder) {
                return write_simple(out, fallback, value);
            }
            // A placeholder Rust has no JSON for would otherwise be written
            // as nothing; it means assembly mixed up two leaves' `_LeafJson`s.
            let json = key
                .cast_exact::<PyString>()
                .ok()
                .and_then(|key| key.to_str().ok().and_then(|key| leaf.json.get(key)))
                .ok_or_else(|| {
                    PyValueError::new_err("a leaf data placeholder has no JSON for its key")
                })?;
            out.push_str(json);
            filled += 1;
            Ok(())
        })
    })?;
    // Fewer placeholders than values would drop part of the leaf's data
    // without an error, which only a Citry bug can cause.
    if filled != leaf.json.len() {
        return Err(PyValueError::new_err(
            "a leaf occurrence's preparedData does not hold a placeholder for every value Rust wrote",
        ));
    }
    Ok(())
}

/// Register level B2's class and function on the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<LeafJson>()?;
    module.add_function(wrap_pyfunction!(leaf_values_json, module)?)?;
    Ok(())
}
