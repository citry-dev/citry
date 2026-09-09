//! Retain Python ownership fields and export immutable records when readers need them.

mod retirement;
mod storage;

use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::exceptions::{PyIndexError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyTuple;

struct CallRow {
    invocation: Vec<Py<PyAny>>,
    enqueued_order: Py<PyAny>,
    rendered_order: Option<Py<PyAny>>,
    settled_order: Option<Py<PyAny>>,
    queue_state: Py<PyAny>,
    invocation_cache: Option<Py<PyAny>>,
    queue_cache: Option<Py<PyAny>>,
}

#[pyclass(module = "citry_core._ownership")]
struct Journal {
    rows: Vec<CallRow>,
    invocation_factory: Py<PyAny>,
    queue_factory: Py<PyAny>,
    active: Py<PyAny>,
    enqueued: Py<PyAny>,
    rendered: Py<PyAny>,
    tuple_constructor: Option<Py<PyAny>>,
}

fn index_error() -> PyErr {
    PyIndexError::new_err("journal row index is out of range")
}

fn optional_value(py: Python<'_>, value: &Option<Py<PyAny>>) -> Py<PyAny> {
    value
        .as_ref()
        .map_or_else(|| py.None(), |value| value.clone_ref(py))
}

#[pymethods]
impl Journal {
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.invocation_factory)?;
        visit.call(&self.queue_factory)?;
        visit.call(&self.active)?;
        visit.call(&self.enqueued)?;
        visit.call(&self.rendered)?;
        visit.call(&self.tuple_constructor)?;
        for row in &self.rows {
            for field in &row.invocation {
                visit.call(field)?;
            }
            visit.call(&row.queue_state)?;
            visit.call(&row.enqueued_order)?;
            visit.call(&row.rendered_order)?;
            visit.call(&row.settled_order)?;
            visit.call(&row.invocation_cache)?;
            visit.call(&row.queue_cache)?;
        }
        Ok(())
    }

    fn __clear__(&mut self, py: Python<'_>) {
        self.rows.clear();
        self.invocation_factory = py.None();
        self.queue_factory = py.None();
        self.active = py.None();
        self.enqueued = py.None();
        self.rendered = py.None();
        self.tuple_constructor = None;
    }

    #[new]
    fn new(
        invocation_factory: Py<PyAny>,
        queue_factory: Py<PyAny>,
        active: Py<PyAny>,
        enqueued: Py<PyAny>,
        rendered: Py<PyAny>,
    ) -> Self {
        Self {
            rows: Vec::new(),
            invocation_factory,
            queue_factory,
            active,
            enqueued,
            rendered,
            tuple_constructor: None,
        }
    }

    fn set_tuple_constructor(&mut self, constructor: Option<Py<PyAny>>) {
        self.tuple_constructor = constructor;
    }

    fn __len__(&self) -> usize {
        self.rows.len()
    }

    fn capture(
        &mut self,
        py: Python<'_>,
        values: &Bound<'_, PyTuple>,
        enqueued_order: Py<PyAny>,
    ) -> PyResult<usize> {
        if values.len() != 12 {
            return Err(PyValueError::new_err(
                "capture requires twelve invocation fields",
            ));
        }
        let mut invocation: Vec<_> = values.iter().map(Bound::unbind).collect();
        invocation.push(PyTuple::empty(py).into_any().unbind());
        invocation.push(self.active.clone_ref(py));
        let index = self.rows.len();
        self.rows.push(CallRow {
            invocation,
            enqueued_order,
            rendered_order: None,
            settled_order: None,
            queue_state: self.enqueued.clone_ref(py),
            invocation_cache: None,
            queue_cache: None,
        });
        Ok(index)
    }

    fn bind(
        &mut self,
        py: Python<'_>,
        index: usize,
        class_id: Py<PyAny>,
        render_id: Py<PyAny>,
        order: Py<PyAny>,
        selector: bool,
    ) -> PyResult<Py<PyAny>> {
        let row = self.rows.get_mut(index).ok_or_else(index_error)?;
        if selector {
            let old = row.invocation[12].bind(py).cast::<PyTuple>()?;
            let values: Vec<_> = old
                .iter()
                .map(Bound::unbind)
                .chain(std::iter::once(render_id))
                .collect();
            row.invocation[12] = PyTuple::new(py, values)?.into_any().unbind();
        } else {
            row.invocation[6] = class_id;
            row.invocation[9] = render_id;
            row.rendered_order = Some(order);
            row.queue_state = self.rendered.clone_ref(py);
            row.queue_cache = None;
        }
        row.invocation_cache = None;
        Ok(row.invocation[2].clone_ref(py))
    }

    fn settle(&mut self, index: usize, order: Py<PyAny>, state: Py<PyAny>) -> PyResult<()> {
        let row = self.rows.get_mut(index).ok_or_else(index_error)?;
        row.settled_order = Some(order);
        row.queue_state = state;
        row.queue_cache = None;
        Ok(())
    }

    fn retire_many(
        &mut self,
        py: Python<'_>,
        indexes: Vec<usize>,
        order: &Bound<'_, PyAny>,
        retired: Py<PyAny>,
        queue_retired: Py<PyAny>,
        queue_failed: Py<PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let mut order = order.clone();
        for index in indexes {
            let row = self.rows.get_mut(index).ok_or_else(index_error)?;
            row.invocation[13] = retired.clone_ref(py);
            row.invocation_cache = None;
            if !row.queue_state.bind(py).eq(queue_failed.bind(py))? {
                order = order.add(1)?;
                row.settled_order = Some(order.clone().unbind());
                row.queue_state = queue_retired.clone_ref(py);
                row.queue_cache = None;
            }
        }
        Ok(order.unbind())
    }

    fn retire_output(
        &mut self,
        py: Python<'_>,
        tables: &Bound<'_, PyTuple>,
        inputs: &Bound<'_, PyTuple>,
        order: &Bound<'_, PyAny>,
        states: &Bound<'_, PyTuple>,
    ) -> PyResult<Py<PyAny>> {
        retirement::retire(self, py, tables, inputs, order, states)
    }

    fn invocation(&mut self, py: Python<'_>, index: usize) -> PyResult<Py<PyAny>> {
        let row = self.rows.get_mut(index).ok_or_else(index_error)?;
        if let Some(value) = &row.invocation_cache {
            return Ok(value.clone_ref(py));
        }
        let args = PyTuple::new(py, row.invocation.iter().map(|value| value.clone_ref(py)))?;
        let value =
            storage::export_row(py, &self.invocation_factory, args, &self.tuple_constructor)?;
        row.invocation_cache = Some(value.clone_ref(py));
        Ok(value)
    }

    fn queue(&mut self, py: Python<'_>, index: usize) -> PyResult<Py<PyAny>> {
        let row = self.rows.get_mut(index).ok_or_else(index_error)?;
        if let Some(value) = &row.queue_cache {
            return Ok(value.clone_ref(py));
        }
        let args = PyTuple::new(
            py,
            [
                row.invocation[0].clone_ref(py),
                row.enqueued_order.clone_ref(py),
                row.invocation[9].clone_ref(py),
                optional_value(py, &row.rendered_order),
                optional_value(py, &row.settled_order),
                row.queue_state.clone_ref(py),
            ],
        )?;
        let value = storage::export_row(py, &self.queue_factory, args, &self.tuple_constructor)?;
        row.queue_cache = Some(value.clone_ref(py));
        Ok(value)
    }

    fn invocations(&mut self, py: Python<'_>) -> PyResult<Vec<Py<PyAny>>> {
        (0..self.rows.len())
            .map(|index| self.invocation(py, index))
            .collect()
    }

    fn queues(&mut self, py: Python<'_>) -> PyResult<Vec<Py<PyAny>>> {
        (0..self.rows.len())
            .map(|index| self.queue(py, index))
            .collect()
    }

    fn set_invocation(&mut self, py: Python<'_>, index: usize, value: Py<PyAny>) -> PyResult<()> {
        let fields = value.bind(py).cast::<PyTuple>()?;
        if fields.len() != 14 {
            return Err(PyValueError::new_err("invocation requires fourteen fields"));
        }
        let row = self.rows.get_mut(index).ok_or_else(index_error)?;
        // Generic writes are used by retirement; preserve the immutable input.
        row.invocation = fields.iter().map(Bound::unbind).collect();
        row.invocation_cache = Some(value);
        row.queue_cache = None;
        Ok(())
    }

    fn set_queue(&mut self, py: Python<'_>, index: usize, value: Py<PyAny>) -> PyResult<()> {
        let fields = value.bind(py).cast::<PyTuple>()?;
        if fields.len() != 6 {
            return Err(PyValueError::new_err("queue requires six fields"));
        }
        let row = self.rows.get_mut(index).ok_or_else(index_error)?;
        row.enqueued_order = fields.get_item(1)?.unbind();
        let rendered = fields.get_item(3)?;
        row.rendered_order = (!rendered.is_none()).then(|| rendered.unbind());
        let settled = fields.get_item(4)?;
        row.settled_order = (!settled.is_none()).then(|| settled.unbind());
        row.queue_state = fields.get_item(5)?.unbind();
        row.queue_cache = Some(value);
        Ok(())
    }
}

pub(super) fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<Journal>()?;
    module.add_class::<storage::RecordTable>()?;
    module.add(
        "UnsupportedRetirement",
        module.py().get_type::<retirement::UnsupportedRetirement>(),
    )
}
