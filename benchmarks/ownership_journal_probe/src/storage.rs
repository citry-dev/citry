//! Native field storage with immutable Python records created only on demand.

use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::exceptions::{PyIndexError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

pub struct StoredRow {
    pub fields: Vec<Py<PyAny>>,
    cache: Option<Py<PyAny>>,
}

#[pyclass(sequence)]
pub struct RecordTable {
    pub rows: Vec<StoredRow>,
    factory: Py<PyAny>,
    pub width: usize,
    tuple_constructor: Option<Py<PyAny>>,
}

pub fn export_row(
    py: Python<'_>,
    factory: &Py<PyAny>,
    fields: Bound<'_, PyTuple>,
    constructor: &Option<Py<PyAny>>,
) -> PyResult<Py<PyAny>> {
    match constructor {
        Some(constructor) => constructor.call1(py, (factory, fields)),
        None => factory.call1(py, fields),
    }
}

impl RecordTable {
    pub fn field<'py>(&self, py: Python<'py>, index: usize, field: usize) -> Bound<'py, PyAny> {
        self.rows[index].fields[field].bind(py).clone()
    }

    pub fn change(&mut self, index: usize, field: usize, value: Py<PyAny>) {
        let row = &mut self.rows[index];
        row.fields[field] = value;
        row.cache = None;
    }

    fn index(&self, index: isize) -> PyResult<usize> {
        let index = if index < 0 {
            self.rows.len() as isize + index
        } else {
            index
        };
        if index < 0 || index as usize >= self.rows.len() {
            return Err(PyIndexError::new_err("record index is out of range"));
        }
        Ok(index as usize)
    }

    fn validate(&self, values: &Bound<'_, PyTuple>) -> PyResult<()> {
        if values.len() != self.width {
            return Err(PyValueError::new_err("unexpected stored record width"));
        }
        Ok(())
    }

    fn export(&mut self, py: Python<'_>, index: usize) -> PyResult<Py<PyAny>> {
        let row = &mut self.rows[index];
        if let Some(value) = &row.cache {
            return Ok(value.clone_ref(py));
        }
        let args = PyTuple::new(py, row.fields.iter().map(|value| value.bind(py)))?;
        let value = export_row(py, &self.factory, args, &self.tuple_constructor)?;
        row.cache = Some(value.clone_ref(py));
        Ok(value)
    }
}

#[pymethods]
impl RecordTable {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.factory)?;
        visit.call(&self.tuple_constructor)?;
        for row in &self.rows {
            for field in &row.fields {
                visit.call(field)?;
            }
            visit.call(&row.cache)?;
        }
        Ok(())
    }

    fn __clear__(&mut self, py: Python<'_>) {
        self.rows.clear();
        self.factory = py.None();
        self.tuple_constructor = None;
    }

    #[new]
    fn new(factory: Py<PyAny>, width: usize) -> Self {
        Self {
            rows: Vec::new(),
            factory,
            width,
            tuple_constructor: None,
        }
    }

    fn set_tuple_constructor(&mut self, constructor: Option<Py<PyAny>>) {
        self.tuple_constructor = constructor;
    }

    fn __len__(&self) -> usize {
        self.rows.len()
    }

    fn __getitem__(&mut self, py: Python<'_>, index: isize) -> PyResult<Py<PyAny>> {
        let index = self.index(index)?;
        self.export(py, index)
    }

    fn __setitem__(&mut self, index: isize, value: &Bound<'_, PyTuple>) -> PyResult<()> {
        self.validate(value)?;
        let index = self.index(index)?;
        self.rows[index] = StoredRow {
            fields: value.iter().map(Bound::unbind).collect(),
            cache: Some(value.clone().into_any().unbind()),
        };
        Ok(())
    }

    fn __iter__(&mut self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        let values = (0..self.rows.len())
            .map(|index| self.export(py, index))
            .collect::<PyResult<Vec<_>>>()?;
        Ok(PyList::new(py, values)?.call_method0("__iter__")?.unbind())
    }

    fn append(&mut self, value: &Bound<'_, PyTuple>) -> PyResult<()> {
        self.validate(value)?;
        self.rows.push(StoredRow {
            fields: value.iter().map(Bound::unbind).collect(),
            cache: Some(value.clone().into_any().unbind()),
        });
        Ok(())
    }

    fn append_values(&mut self, values: &Bound<'_, PyTuple>) -> PyResult<()> {
        self.validate(values)?;
        self.rows.push(StoredRow {
            fields: values.iter().map(Bound::unbind).collect(),
            cache: None,
        });
        Ok(())
    }

    fn patch(&mut self, index: isize, fields: Vec<(usize, Py<PyAny>)>) -> PyResult<()> {
        let index = self.index(index)?;
        if fields.iter().any(|(field, _)| *field >= self.width) {
            return Err(PyIndexError::new_err("field index is out of range"));
        }
        for (field, value) in fields {
            self.change(index, field, value);
        }
        Ok(())
    }

    /// Check and bind one template supply without exporting its immutable row.
    fn bind_fill_source(
        &mut self,
        py: Python<'_>,
        index: isize,
        owner: &Bound<'_, PyAny>,
        invocation: &Bound<'_, PyAny>,
        template: &Bound<'_, PyAny>,
        fallback: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        if self.width != 13 {
            return Err(PyValueError::new_err("expected a logical fill table"));
        }
        let index = self.index(index)?;
        // LogicalFillRecord: kind 2, policy 4, lexical owner 5, invocation 8.
        if self.field(py, index, 4).ne(template)? || self.field(py, index, 2).eq(fallback)? {
            return Ok(());
        }
        if self.field(py, index, 5).ne(owner)? {
            return Err(PyRuntimeError::new_err(
                "A template fill source invocation must belong to the fill's lexical owner.",
            ));
        }
        let previous = self.field(py, index, 8);
        if !previous.is_none() && previous.ne(invocation)? {
            return Err(PyRuntimeError::new_err(
                "A template fill cannot be rebound to a second source invocation.",
            ));
        }
        self.change(index, 8, invocation.clone().unbind());
        Ok(())
    }

    /// Attach an active fill; return false when Python must revive or forward it.
    fn attach_active_fill(
        &mut self,
        py: Python<'_>,
        index: isize,
        receiver: &Bound<'_, PyAny>,
        class_id: &Bound<'_, PyAny>,
        active: &Bound<'_, PyAny>,
    ) -> PyResult<bool> {
        if self.width != 13 {
            return Err(PyValueError::new_err("expected a logical fill table"));
        }
        let index = self.index(index)?;
        // LogicalFillRecord: receiver 9, receiver class 10, state 12.
        if !self.field(py, index, 12).eq(active)? {
            return Ok(false);
        }
        let previous = self.field(py, index, 9);
        if !previous.is_none() && !previous.eq(receiver)? {
            return Ok(false);
        }
        self.change(index, 9, receiver.clone().unbind());
        self.change(index, 10, class_id.clone().unbind());
        Ok(true)
    }

    /// Resolve and append one active fill placement without exporting source rows.
    #[allow(clippy::too_many_arguments)]
    fn begin_slot_region(
        &mut self,
        py: Python<'_>,
        fills: &RecordTable,
        fill_index: isize,
        parent_index: Option<isize>,
        ids: &Bound<'_, PyTuple>,
        site: Option<&Bound<'_, PyTuple>>,
        active: &Bound<'_, PyAny>,
        captured: &Bound<'_, PyAny>,
    ) -> PyResult<Option<usize>> {
        if self.width != 11 || fills.width != 13 {
            return Err(PyValueError::new_err(
                "expected region and logical fill tables",
            ));
        }
        if ids.len() != 4 || site.is_some_and(|value| value.len() != 2) {
            return Err(PyValueError::new_err(
                "unexpected region IDs or outlet fields",
            ));
        }
        let fill_index = fills.index(fill_index)?;
        if !fills.field(py, fill_index, 12).eq(active)? {
            return Ok(None);
        }
        let (receiver, location) = match site {
            Some(site) => (site.get_item(0)?, site.get_item(1)?),
            None => (
                fills.field(py, fill_index, 9),
                fills.field(py, fill_index, 11),
            ),
        };
        let transition = match parent_index {
            Some(index) => self.field(py, self.index(index)?, 5),
            None => receiver.clone(),
        };
        let fields = vec![
            ids.get_item(0)?.unbind(),
            ids.get_item(1)?.unbind(),
            ids.get_item(2)?.unbind(),
            receiver.unbind(),
            location.unbind(),
            fills.field(py, fill_index, 5).unbind(),
            fills.field(py, fill_index, 7).unbind(),
            ids.get_item(3)?.unbind(),
            transition.unbind(),
            py.None(),
            captured.clone().unbind(),
        ];
        let index = self.rows.len();
        self.rows.push(StoredRow {
            fields,
            cache: None,
        });
        Ok(Some(index))
    }
}
