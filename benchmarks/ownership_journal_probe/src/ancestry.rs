//! Follow ancestry without exporting immutable records for Python indexes.

use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::types::{PyInt, PySet, PyString, PyTuple};

use crate::Journal;
use crate::retirement::UnsupportedRetirement;
use crate::storage::RecordTable;

#[derive(Default)]
struct Parents {
    logical: Option<Py<PyAny>>,
    invocations: Vec<Py<PyAny>>,
    initialization: Vec<Py<PyAny>>,
}

fn name(value: &Bound<'_, PyAny>) -> PyResult<String> {
    value
        .cast_exact::<PyString>()
        .map_err(|_| UnsupportedRetirement::new_err("ancestry IDs require exact str values"))?
        .to_str()
        .map(str::to_owned)
        .map_err(|_| UnsupportedRetirement::new_err("ancestry ID is not representable as UTF-8"))
}

pub fn ancestors(
    journal: &Journal,
    py: Python<'_>,
    instances: &RecordTable,
    edges: &RecordTable,
    regions: &RecordTable,
    seeds: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    seeds
        .as_any()
        .cast_exact::<PySet>()
        .map_err(|_| UnsupportedRetirement::new_err("ancestry seeds require an exact set"))?;
    // The Python index builder also hashes these relations. Reject callback-
    // capable keys even though this narrower query does not follow them.
    for row in &regions.rows {
        if !row.fields[3].bind(py).is_none() {
            name(row.fields[3].bind(py))?;
        }
        row.fields[2].bind(py).cast_exact::<PyInt>().map_err(|_| {
            UnsupportedRetirement::new_err("region fill IDs require exact int values")
        })?;
        if !row.fields[7].bind(py).is_none() {
            row.fields[7].bind(py).cast_exact::<PyInt>().map_err(|_| {
                UnsupportedRetirement::new_err("containing region IDs require exact int values")
            })?;
        }
    }
    let mut parents: HashMap<String, Parents> = HashMap::new();
    for row in &instances.rows {
        let id = name(row.fields[1].bind(py))?;
        let parent = row.fields[5].bind(py);
        if !parent.is_none() {
            name(parent)?;
            // The Python index keeps the last non-None logical parent.
            parents.entry(id).or_default().logical = Some(parent.clone().unbind());
        }
    }
    for row in &journal.rows {
        name(row.invocation[2].bind(py))?;
        row.invocation[0]
            .bind(py)
            .cast_exact::<PyInt>()
            .map_err(|_| {
                UnsupportedRetirement::new_err("invocation IDs require exact int values")
            })?;
        if !row.invocation[10].bind(py).is_none() {
            row.invocation[10]
                .bind(py)
                .cast_exact::<PyInt>()
                .map_err(|_| {
                    UnsupportedRetirement::new_err("invocation region IDs require exact int values")
                })?;
        }
        let target = row.invocation[9].bind(py);
        if target.is_none() {
            continue;
        }
        let target = name(target)?;
        let source = row.invocation[2].bind(py);
        name(source)?;
        let entry = parents.entry(target).or_default();
        entry.invocations.push(source.clone().unbind());
        for selector in row.invocation[12]
            .bind(py)
            .cast_exact::<PyTuple>()
            .map_err(|_| UnsupportedRetirement::new_err("selectors require an exact tuple"))?
            .iter()
        {
            name(&selector)?;
            entry.invocations.push(selector.unbind());
        }
    }
    for row in &edges.rows {
        let child = name(row.fields[3].bind(py))?;
        let parent = row.fields[2].bind(py);
        name(parent)?;
        parents
            .entry(child)
            .or_default()
            .initialization
            .push(parent.clone().unbind());
    }
    // Seed copying, iteration and insertion follow the Python reference. Keep
    // the actual field objects; interning strings here could change identity.
    let closed = seeds.call_method0("copy")?.cast_into::<PySet>()?;
    let mut pending = Vec::new();
    for value in closed.iter() {
        name(&value)?;
        pending.push(value.unbind());
    }
    while let Some(value) = pending.pop() {
        if let Some(entry) = parents.get(&name(value.bind(py))?) {
            for addition in entry
                .logical
                .iter()
                .chain(&entry.invocations)
                .chain(&entry.initialization)
            {
                if !closed.contains(addition.bind(py))? {
                    closed.add(addition.bind(py))?;
                    pending.push(addition.clone_ref(py));
                }
            }
        }
    }
    Ok(closed.into_any().unbind())
}
