//! Strict client-graph canonical JSON at the Python/Rust boundary.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBool, PyBytes, PyDict, PyFloat, PyInt, PyList, PyString};
use sha2::{Digest, Sha256};

const MAX_SAFE_INTEGER: i64 = 9_007_199_254_740_991;

fn utf16_units(value: &Bound<'_, PyString>) -> PyResult<Vec<u16>> {
    if let Ok(text) = value.to_str() {
        return Ok(text.encode_utf16().collect());
    }
    // Python permits lone UTF-16 surrogates in ``str``. They are not valid
    // Rust ``str`` values, so preserve them through Python's surrogatepass
    // codec and canonicalize the resulting code units explicitly.
    let encoded = value.call_method1("encode", ("utf-16-be", "surrogatepass"))?;
    let bytes = encoded.cast::<PyBytes>()?.as_bytes();
    Ok(bytes
        .chunks_exact(2)
        .map(|pair| u16::from_be_bytes([pair[0], pair[1]]))
        .collect())
}

fn push_hex_escape(output: &mut String, unit: u16) {
    use std::fmt::Write as _;
    write!(output, "\\u{unit:04x}").expect("writing to String cannot fail");
}

fn push_quoted(value: &Bound<'_, PyString>, output: &mut String) -> PyResult<()> {
    let units = utf16_units(value)?;
    output.push('"');
    let mut index = 0;
    while index < units.len() {
        let unit = units[index];
        match unit {
            0x22 => output.push_str("\\\""),
            0x5c => output.push_str("\\\\"),
            0x08 => output.push_str("\\b"),
            0x09 => output.push_str("\\t"),
            0x0a => output.push_str("\\n"),
            0x0c => output.push_str("\\f"),
            0x0d => output.push_str("\\r"),
            0x00..=0x1f => push_hex_escape(output, unit),
            0xd800..=0xdbff
                if index + 1 < units.len() && (0xdc00..=0xdfff).contains(&units[index + 1]) =>
            {
                let high = u32::from(unit - 0xd800);
                let low = u32::from(units[index + 1] - 0xdc00);
                let scalar = 0x10000 + (high << 10) + low;
                output
                    .push(char::from_u32(scalar).expect("a paired surrogate is a Unicode scalar"));
                index += 1;
            }
            0xd800..=0xdfff => push_hex_escape(output, unit),
            _ => output.push(
                char::from_u32(u32::from(unit)).expect("a non-surrogate u16 is a Unicode scalar"),
            ),
        }
        index += 1;
    }
    output.push('"');
    Ok(())
}

fn write_canonical(value: &Bound<'_, PyAny>, output: &mut String) -> PyResult<()> {
    if value.is_none() {
        output.push_str("null");
    } else if value.is_instance_of::<PyBool>() {
        output.push_str(if value.extract::<bool>()? {
            "true"
        } else {
            "false"
        });
    } else if value.is_instance_of::<PyInt>() {
        let number = value
            .extract::<i64>()
            .map_err(|_| PyValueError::new_err("integer is outside the client-graph range"))?;
        if !(0..=MAX_SAFE_INTEGER).contains(&number) {
            return Err(PyValueError::new_err(
                "integer is outside the client-graph range",
            ));
        }
        output.push_str(&number.to_string());
    } else if value.is_instance_of::<PyFloat>() {
        let number = value.extract::<f64>()?;
        if !number.is_finite() || number.fract() != 0.0 {
            return Err(PyValueError::new_err("number is not a decoded integer"));
        }
        if !(0.0..=MAX_SAFE_INTEGER as f64).contains(&number) {
            return Err(PyValueError::new_err(
                "integer is outside the client-graph range",
            ));
        }
        output.push_str(&(number as i64).to_string());
    } else if let Ok(string) = value.cast::<PyString>() {
        push_quoted(string, output)?;
    } else if let Ok(list) = value.cast::<PyList>() {
        output.push('[');
        for (index, item) in list.iter().enumerate() {
            if index != 0 {
                output.push(',');
            }
            write_canonical(&item, output)?;
        }
        output.push(']');
    } else if let Ok(dict) = value.cast::<PyDict>() {
        let mut entries = Vec::with_capacity(dict.len());
        for (key, item) in dict.iter() {
            let key = key
                .cast_into::<PyString>()
                .map_err(|_| PyValueError::new_err("client-graph object keys must be strings"))?;
            entries.push((utf16_units(&key)?, key, item));
        }
        entries.sort_by(|left, right| left.0.cmp(&right.0));
        output.push('{');
        for (index, (_sort_key, key, item)) in entries.into_iter().enumerate() {
            if index != 0 {
                output.push(',');
            }
            push_quoted(&key, output)?;
            output.push(':');
            write_canonical(&item, output)?;
        }
        output.push('}');
    } else {
        let type_name = value.get_type().name()?.to_string_lossy().into_owned();
        return Err(PyValueError::new_err(format!(
            "unsupported client-graph JSON value {type_name}"
        )));
    }
    Ok(())
}

/// Canonicalize one strict client-graph JSON value and hash those exact bytes.
#[pyfunction]
pub fn canonical_json_and_revision(value: &Bound<'_, PyAny>) -> PyResult<(String, String)> {
    let mut canonical = String::new();
    write_canonical(value, &mut canonical)?;
    let revision = format!("{:x}", Sha256::digest(canonical.as_bytes()));
    Ok((canonical, revision))
}
