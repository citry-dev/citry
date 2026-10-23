//! Level C2 of the native render path: Rust walks a call run's loop and
//! reads each row's inputs. The design and every error mode are in
//! `docs/design/native_render.md`.
//!
//! A call run is the rows one `c-for` places at one component call site.
//! Python's walk of such a loop (`ForNode._render_call_run` in
//! `citry/nodes/__init__.py`, level C1) records each row's kwargs dict and
//! call metadata in one `_DeferredRun`. When the loop's iterable, the call's
//! inputs and its key are plain paths (`row in phase['outputs']`,
//! `c-row="row"`, `#c-key="row['id']"`), `ForNode._walk_call_run` asks this
//! module to produce the same two lists, in two passes:
//!
//! 1. [`WalkPlan::read_rows`] reads every row, checking exact types at every
//!    step. It calls no template or user code, except that a dict lookup
//!    runs `__eq__` on a stored key whose hash equals the key looked up, as
//!    Python's own read does. The values it keeps are references to the
//!    objects it read, never copies, as Python's own kwargs dicts hold them.
//! 2. Only when every read succeeded, each row looks its class up with the
//!    registry's `get(name)`, as `ComponentNode._render_run_row` does once
//!    per row. While another thread changes the registry, `get` raises
//!    `CitryLifecycleInProgress`; the walk declines and Python's walk raises
//!    the same error. Then the row's kwargs dict and its
//!    `_PreparedCallMetadata` are built.
//!
//! `walk` returns `(kwargs list, metadata list)`, or a `str` naming why it
//! declined. On a decline Python's walk runs the loop from the start, so a
//! read that fails raises Python's own error with its template position. A
//! decline repeats the reads (so a colliding key's `__eq__` runs again)
//! and, for a decline in pass 2, the `get` calls of the rows before it;
//! Python also repeats the checks it made before calling `walk`. An
//! `Exception` raised by anything the walk calls declines; any other
//! `BaseException`, such as `KeyboardInterrupt`, propagates.
//!
//! This is the one place on the native render path where a Rust panic does
//! not raise `RuntimeError`: `walk` keeps nothing it built, so it declines
//! (reason `panic`) and Python's walk runs instead. Rust's panic hook still
//! prints the message to stderr. PyO3 turns a `PanicException` that Python
//! code raised back into a Rust panic when it fetches the error (after
//! printing it through `sys.excepthook`), so such an exception from a `get`
//! or a colliding `__eq__` declines too.

use std::panic::{AssertUnwindSafe, catch_unwind};

use pyo3::exceptions::{PyException, PyValueError};
use pyo3::gc::PyVisit;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyInt, PyList, PyString, PyTuple, PyType};
use pyo3::{PyTraverseError, intern};

use citry_native_render::{PathSpec, RowKey, Rows, Shape, Step, StepKey, Tree, WalkPlan, WalkSpec};

use super::rows::without_panics;

/// A Python value as the walk reads it. `keys` holds one Python key per
/// plan step, built once with the plan, so a lookup makes no new object.
#[derive(Clone)]
struct Node<'a, 'py> {
    value: Bound<'py, PyAny>,
    keys: &'a [Py<PyAny>],
    marker: &'a Bound<'py, PyType>,
    /// The loop's variables: an exact dict or Citry's `_ConstMapping` (a
    /// dict subclass that overrides no read), read as a dict.
    scope: bool,
}

impl<'a, 'py> Node<'a, 'py> {
    fn wrap(&self, value: Bound<'py, PyAny>) -> Self {
        Node {
            value,
            keys: self.keys,
            marker: self.marker,
            scope: false,
        }
    }
}

impl Tree for Node<'_, '_> {
    type Error = PyErr;

    fn shape(&self) -> Shape {
        let value = &self.value;
        if self.scope || value.is_exact_instance_of::<PyDict>() {
            Shape::Dict
        } else if value.is_exact_instance_of::<PyList>() || value.is_exact_instance_of::<PyTuple>()
        {
            Shape::Seq
        } else if value.is_exact_instance_of::<PyString>() {
            Shape::Str
        } else if value.is_exact_instance_of::<PyInt>() {
            // An int outside i64 fails to extract and reads as Other, so
            // the walk declines it as a key.
            value.extract::<i64>().map_or(Shape::Other, Shape::Int)
        } else if value.get_type().is(self.marker) {
            Shape::Marker
        } else {
            Shape::Other
        }
    }

    fn get(&self, step: &Step) -> PyResult<Option<Self>> {
        // `shape` said Dict, so this is a dict or the scope's dict subclass.
        // The lookup is dict's own, with no `__getitem__` or `__missing__`,
        // which is what Python's evaluator gets for these exact types.
        let dict = self.value.cast::<PyDict>()?;
        let key = self.keys[step.id].bind(self.value.py());
        Ok(dict.get_item(key)?.map(|found| self.wrap(found)))
    }

    fn item(&self, index: usize) -> Option<Self> {
        // Both lookups check the index against the current length, as
        // Python's list iterator does before every item.
        let found = if let Ok(list) = self.value.cast_exact::<PyList>() {
            list.get_item(index).ok()
        } else if let Ok(tuple) = self.value.cast_exact::<PyTuple>() {
            tuple.get_item(index).ok()
        } else {
            None
        };
        found.map(|found| self.wrap(found))
    }

    fn len_hint(&self) -> usize {
        if let Ok(list) = self.value.cast_exact::<PyList>() {
            list.len()
        } else if let Ok(tuple) = self.value.cast_exact::<PyTuple>() {
            tuple.len()
        } else {
            0
        }
    }
}

/// A path as Python passes it: `(name, (step, ...))`, each step an exact
/// `str` or `int`.
fn path_spec(value: &Bound<'_, PyAny>) -> PyResult<PathSpec> {
    let (name, steps): (String, Bound<'_, PyTuple>) = value.extract()?;
    let mut keys = Vec::with_capacity(steps.len());
    for step in steps.iter() {
        if step.is_exact_instance_of::<PyString>() {
            keys.push(StepKey::Str(step.extract()?));
        } else if step.is_exact_instance_of::<PyInt>() {
            keys.push(StepKey::Int(step.extract()?));
        } else {
            return Err(PyValueError::new_err(format!(
                "a path step must be an exact str or int, got {}",
                step.get_type().name()?
            )));
        }
    }
    Ok(PathSpec { name, steps: keys })
}

/// The Rust loop walk for one `c-for` call run; `ForNode` builds one per
/// loop node and keeps it.
#[pyclass(
    frozen,
    name = "_CallRunWalkPlan",
    module = "citry_core._rust.native_render"
)]
pub struct CallRunWalkPlan {
    plan: WalkPlan,
    /// One Python key per plan step (`WalkPlan::steps`).
    keys: Vec<Py<PyAny>>,
    /// Each input's kwarg name, in attribute order.
    kwarg_names: Vec<Py<PyString>>,
    /// The component name the call looks up.
    name: Py<PyString>,
    /// The call node's `source` and `position`, for the call metadata.
    source: Py<PyAny>,
    position: Py<PyAny>,
    /// `_PreparedCallMetadata`, passed in so its fields stay Python's.
    metadata_class: Py<PyAny>,
    /// `_ConstMapping`, the type of the loop's variables besides `dict`.
    scope_type: Py<PyType>,
    /// The class of `Const` markers.
    marker_type: Py<PyType>,
}

#[pymethods]
impl CallRunWalkPlan {
    /// `_CallRunWalkPlan(target, iterable, kwargs, key, kwarg_names, name,
    /// source, position, metadata_class, scope_type, marker_type)`.
    ///
    /// Each path is `(name, steps)`; `kwargs` holds one path per input and
    /// `kwarg_names` its name. Raises ValueError for a plan `walk.rs`
    /// refuses (Python's lowering never passes one) or for malformed
    /// arguments, and RuntimeError for a Rust panic.
    #[new]
    #[allow(clippy::too_many_arguments)]
    fn new(
        py: Python<'_>,
        target: String,
        iterable: &Bound<'_, PyAny>,
        kwargs: Vec<Bound<'_, PyAny>>,
        key: &Bound<'_, PyAny>,
        kwarg_names: Vec<Bound<'_, PyString>>,
        name: Bound<'_, PyString>,
        source: Bound<'_, PyAny>,
        position: Bound<'_, PyAny>,
        metadata_class: Bound<'_, PyAny>,
        scope_type: Bound<'_, PyType>,
        marker_type: Bound<'_, PyType>,
    ) -> PyResult<Self> {
        without_panics(|| {
            if kwarg_names.len() != kwargs.len() {
                return Err(PyValueError::new_err("one kwarg name per input path"));
            }
            let spec = WalkSpec {
                target,
                iterable: path_spec(iterable)?,
                kwargs: kwargs.iter().map(path_spec).collect::<PyResult<_>>()?,
                key: path_spec(key)?,
            };
            let plan = WalkPlan::new(&spec)
                .map_err(|error| PyValueError::new_err(format!("walk plan refused: {error:?}")))?;
            let keys = plan
                .steps()
                .iter()
                .map(|step| match &step.key {
                    // Interned, as the str literals of Python code are, so a
                    // lookup often matches a stored key by identity.
                    StepKey::Str(text) => Ok(PyString::intern(py, text).into_any().unbind()),
                    StepKey::Int(number) => Ok(number.into_pyobject(py)?.into_any().unbind()),
                })
                .collect::<PyResult<Vec<_>>>()?;
            Ok(CallRunWalkPlan {
                plan,
                keys,
                kwarg_names: kwarg_names.into_iter().map(Bound::unbind).collect(),
                name: name.unbind(),
                source: source.unbind(),
                position: position.unbind(),
                metadata_class: metadata_class.unbind(),
                scope_type: scope_type.unbind(),
                marker_type: marker_type.unbind(),
            })
        })
    }

    /// Walk the loop over `variables`; see the module docs.
    ///
    /// `get` is the registry's bound `get`, `run_class` the class every row
    /// must look up, and `origin` the call metadata's template origin.
    fn walk<'py>(
        &self,
        py: Python<'py>,
        variables: &Bound<'py, PyAny>,
        get: &Bound<'py, PyAny>,
        run_class: &Bound<'py, PyAny>,
        origin: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        match catch_unwind(AssertUnwindSafe(|| {
            self.walk_rows(py, variables, get, run_class, origin)
        })) {
            Ok(result) => result,
            // Nothing the walk built is kept, so Python's walk can run instead.
            Err(_) => Ok(intern!(py, "panic").clone().into_any()),
        }
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        // The call node's source can lead back to the template, and so to
        // the loop node that holds this plan, so the collector must see
        // every object the plan holds.
        for key in &self.keys {
            visit.call(key)?;
        }
        for name in &self.kwarg_names {
            visit.call(name)?;
        }
        visit.call(&self.name)?;
        visit.call(&self.source)?;
        visit.call(&self.position)?;
        visit.call(&self.metadata_class)?;
        visit.call(&self.scope_type)?;
        visit.call(&self.marker_type)?;
        Ok(())
    }
}

/// Turn an error into the decline `reason` when it is an ordinary
/// `Exception` (Python's walk then meets it again and raises it with its
/// template position); any other `BaseException`, such as
/// `KeyboardInterrupt`, propagates.
fn decline_or_raise<'py>(
    py: Python<'py>,
    error: PyErr,
    reason: &Bound<'py, PyString>,
) -> PyResult<Bound<'py, PyAny>> {
    if error.is_instance_of::<PyException>(py) {
        Ok(reason.clone().into_any())
    } else {
        Err(error)
    }
}

impl CallRunWalkPlan {
    fn walk_rows<'py>(
        &self,
        py: Python<'py>,
        variables: &Bound<'py, PyAny>,
        get: &Bound<'py, PyAny>,
        run_class: &Bound<'py, PyAny>,
        origin: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        // The scope must be read as a plain dict: any other mapping could
        // run code on every lookup.
        if !(variables.is_exact_instance_of::<PyDict>()
            || variables.get_type().is(self.scope_type.bind(py)))
        {
            return Ok(intern!(py, "scope").clone().into_any());
        }
        let scope = Node {
            value: variables.clone(),
            keys: &self.keys,
            marker: self.marker_type.bind(py),
            scope: true,
        };
        // Pass 1: every read; only a colliding key's `__eq__` can run.
        let rows = match self.plan.read_rows(&scope) {
            Ok(Ok(rows)) => rows,
            Ok(Err(decline)) => return Ok(PyString::new(py, decline.as_str()).into_any()),
            Err(error) => return decline_or_raise(py, error, intern!(py, "read_raised")),
        };
        // Pass 2: per row, the registry lookup, then the kwargs dict and
        // the call metadata.
        let kwargs_list = PyList::empty(py);
        let metadata_list = PyList::empty(py);
        let name = self.name.bind(py);
        for (index, key) in rows.keys.iter().enumerate() {
            match get.call1((name,)) {
                Ok(found) if found.is(run_class) => {}
                // Another class under the name: Python's walk ends the run
                // at this row, so it walks the loop itself.
                Ok(_) => return Ok(intern!(py, "class_changed").clone().into_any()),
                Err(error) => return decline_or_raise(py, error, intern!(py, "get_raised")),
            }
            let built =
                self.build_row(py, &rows, index, key, origin)
                    .and_then(|(kwargs, metadata)| {
                        kwargs_list.append(kwargs)?;
                        metadata_list.append(metadata)
                    });
            // Only an error such as MemoryError or RecursionError can get
            // here; Python's walk then raises it with the row's template
            // position.
            if let Err(error) = built {
                return decline_or_raise(py, error, intern!(py, "build_raised"));
            }
        }
        match PyTuple::new(py, [kwargs_list.into_any(), metadata_list.into_any()]) {
            Ok(result) => Ok(result.into_any()),
            Err(error) => decline_or_raise(py, error, intern!(py, "build_raised")),
        }
    }

    /// Build row `index`'s kwargs dict and its `_PreparedCallMetadata`, as
    /// `ComponentNode._render_run_row` builds them.
    fn build_row<'py>(
        &self,
        py: Python<'py>,
        rows: &Rows<Node<'_, 'py>>,
        index: usize,
        key: &RowKey<Node<'_, 'py>>,
        origin: &Bound<'py, PyAny>,
    ) -> PyResult<(Bound<'py, PyDict>, Bound<'py, PyAny>)> {
        // Inputs in attribute order, as `_resolve_inputs` fills its dict.
        let kwargs = PyDict::new(py);
        for (column, value) in rows.row_kwargs(index).iter().enumerate() {
            kwargs.set_item(self.kwarg_names[column].bind(py), &value.value)?;
        }
        // `str()` of an exact str is the same object; of an int, its decimal
        // text, which Rust writes the same way for an i64.
        let key_text = match key {
            RowKey::Str(node) => node.value.clone(),
            RowKey::Int(number) => PyString::new(py, &number.to_string()).into_any(),
        };
        // `slot_free_body` is true: level C1 accepts only calls with an
        // empty body, as `_render_run_row` passes.
        let metadata = self.metadata_class.bind(py).call1((
            self.source.bind(py),
            self.position.bind(py),
            key_text,
            origin,
            true,
        ))?;
        Ok((kwargs, metadata))
    }
}

/// Register the level C2 loop walk on the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<CallRunWalkPlan>()?;
    Ok(())
}
