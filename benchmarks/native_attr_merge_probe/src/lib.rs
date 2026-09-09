//! Experimental merge of attribute contributions with live Python normalizers.

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};
use std::collections::HashMap;

fn identity(name: &str) -> String {
    if ["@c-", ":c-", "#c-", "$c-", "c-$c-"]
        .iter()
        .any(|prefix| name.starts_with(prefix))
    {
        name.to_owned()
    } else {
        name.to_ascii_lowercase()
    }
}

#[pyfunction]
fn merge<'py>(
    py: Python<'py>,
    items: &Bound<'py, PyAny>,
    attrs: &Bound<'py, PyAny>,
) -> PyResult<Option<Bound<'py, PyDict>>> {
    let Ok(items) = items.cast_exact::<PyList>() else {
        return Ok(None);
    };
    // Inspect all keys before callbacks, so unsupported rows can use Python unchanged.
    let mut rows = Vec::with_capacity(items.len());
    for item in items.iter() {
        let Ok(pair) = item.cast_exact::<PyTuple>() else {
            return Ok(None);
        };
        if pair.len() != 2 {
            return Ok(None);
        }
        let key = pair.get_item(0)?;
        let Ok(text) = key.cast_exact::<PyString>() else {
            return Ok(None);
        };
        let Ok(name) = text.to_str() else {
            return Ok(None);
        };
        rows.push((identity(name), key, pair.get_item(1)?));
    }
    let result = PyDict::new(py);
    let classes = PyList::empty(py);
    let styles = PyList::empty(py);
    let mut keys = HashMap::with_capacity(rows.len());
    for (name, key, value) in rows {
        let output_key = keys.entry(name.clone()).or_insert(key);
        let contributions = match name.as_str() {
            "class" => Some(&classes),
            "style" => Some(&styles),
            _ => None,
        };
        if let Some(contributions) = contributions {
            if !value.is_none() {
                contributions.append(value)?;
            }
            result.set_item(&*output_key, py.None())?;
        } else {
            result.set_item(&*output_key, value)?;
        }
    }
    // Python callbacks remain live, including style replacement by a class callback.
    for (name, values, helper) in [
        ("class", classes, "_normalize_class_contributions"),
        ("style", styles, "normalize_style"),
    ] {
        if !values.is_empty() {
            let output = attrs.getattr(helper)?.call1((values,))?;
            result.set_item(&keys[name], output)?;
        }
    }
    Ok(Some(result))
}

#[pymodule]
fn citry_native_attr_merge_probe(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(merge, module)?)?;
    Ok(())
}
