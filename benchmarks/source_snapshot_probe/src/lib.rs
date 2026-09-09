//! Keep immutable source fields available without exporting every public record.

use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::exceptions::{PyIndexError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

struct Row {
    fields: Py<PyTuple>,
    record: Option<Py<PyAny>>,
}

#[pyclass(sequence)]
struct SourceTable {
    rows: Vec<Row>,
    factory: Py<PyAny>,
    constructor: Py<PyAny>,
    raw: Option<Py<PyTuple>>,
}

impl SourceTable {
    fn check(values: &Bound<'_, PyTuple>) -> PyResult<()> {
        if values.len() != 8 {
            return Err(PyValueError::new_err("source rows require eight fields"));
        }
        Ok(())
    }

    fn index(&self, index: isize) -> PyResult<usize> {
        let index = if index < 0 {
            self.rows.len() as isize + index
        } else {
            index
        };
        if index < 0 || index as usize >= self.rows.len() {
            return Err(PyIndexError::new_err("source index out of range"));
        }
        Ok(index as usize)
    }

    fn export(&mut self, py: Python<'_>, index: usize) -> PyResult<Py<PyAny>> {
        let row = &mut self.rows[index];
        if let Some(record) = &row.record {
            return Ok(record.clone_ref(py));
        }
        let record = self.constructor.call1(py, (&self.factory, &row.fields))?;
        row.record = Some(record.clone_ref(py));
        Ok(record)
    }
}

#[pymethods]
impl SourceTable {
    #[new]
    fn new(factory: Py<PyAny>, constructor: Py<PyAny>) -> Self {
        Self {
            rows: Vec::new(),
            factory,
            constructor,
            raw: None,
        }
    }

    fn __len__(&self) -> usize {
        self.rows.len()
    }

    fn __getitem__(&mut self, py: Python<'_>, index: isize) -> PyResult<Py<PyAny>> {
        let index = self.index(index)?;
        self.export(py, index)
    }

    fn __setitem__(&mut self, index: isize, value: &Bound<'_, PyTuple>) -> PyResult<()> {
        Self::check(value)?;
        let index = self.index(index)?;
        self.rows[index] = Row {
            fields: value.clone().unbind(),
            record: Some(value.clone().into_any().unbind()),
        };
        self.raw = None;
        Ok(())
    }

    fn append(&mut self, value: &Bound<'_, PyTuple>) -> PyResult<()> {
        Self::check(value)?;
        self.rows.push(Row {
            fields: value.clone().unbind(),
            record: Some(value.clone().into_any().unbind()),
        });
        self.raw = None;
        Ok(())
    }

    fn append_values(&mut self, value: &Bound<'_, PyTuple>) -> PyResult<()> {
        Self::check(value)?;
        self.rows.push(Row {
            fields: value.clone().unbind(),
            record: None,
        });
        self.raw = None;
        Ok(())
    }

    fn __iter__(&mut self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let values = (0..self.rows.len())
            .map(|index| self.export(py, index))
            .collect::<PyResult<Vec<_>>>()?;
        Ok(PyList::new(py, values)?.call_method0("__iter__")?.unbind())
    }

    fn raw_snapshot(&mut self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        if let Some(raw) = &self.raw {
            return Ok(raw.clone_ref(py));
        }
        let raw = PyTuple::new(py, self.rows.iter().map(|row| row.fields.bind(py)))?.unbind();
        self.raw = Some(raw.clone_ref(py));
        Ok(raw)
    }

    fn export_count(&self) -> usize {
        self.rows.iter().filter(|row| row.record.is_some()).count()
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.factory)?;
        visit.call(&self.constructor)?;
        visit.call(&self.raw)?;
        for row in &self.rows {
            visit.call(&row.fields)?;
            visit.call(&row.record)?;
        }
        Ok(())
    }

    fn __clear__(&mut self, py: Python<'_>) {
        self.rows.clear();
        self.raw = None;
        self.factory = py.None();
        self.constructor = py.None();
    }
}

#[pymodule]
fn citry_source_snapshot_probe(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<SourceTable>()?;
    Ok(())
}
