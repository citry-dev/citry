//! Experimental primitive attribute cache keys without per-attribute tuples.

use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyInt, PyString, PyTuple};

#[pyfunction]
fn cache_key<'py>(
    py: Python<'py>,
    resolved: &Bound<'py, PyAny>,
) -> PyResult<Option<Bound<'py, PyTuple>>> {
    let Ok(resolved) = resolved.cast_exact::<PyDict>() else {
        return Ok(None);
    };
    if resolved.len() > 16 {
        return Ok(None);
    }
    let mut fields = Vec::with_capacity(resolved.len() * 3);
    let mut chars = 0;
    for (key, value) in resolved.iter() {
        let Ok(name) = key.cast_exact::<PyString>() else {
            return Ok(None);
        };
        chars += name.len()?;
        if let Ok(text) = value.cast_exact::<PyString>() {
            chars += text.len()?;
        } else if value.cast_exact::<PyInt>().is_ok() {
            if value.call_method0("bit_length")?.extract::<usize>()? > 256 {
                return Ok(None);
            }
        } else if !value.is_none() && value.cast_exact::<PyBool>().is_err() {
            return Ok(None);
        }
        if chars > 2048 {
            return Ok(None);
        }
        // The same references become the immutable snapshot used on a miss.
        fields.push(key);
        fields.push(value.get_type().into_any());
        fields.push(value);
    }
    Ok(Some(PyTuple::new(py, fields)?))
}

#[pymodule]
fn citry_native_attrs_output_probe(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(cache_key, module)?)?;
    Ok(())
}
