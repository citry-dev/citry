//! Level B1 of the native render path: one object records every row of a
//! call run during serialize. The design and every error mode are in
//! `docs/design/native_render.md`.
//!
//! A call run is the rows one `c-for` places at one component call site.
//! Assembly (`assemble_typed_render` in `citry/_vue/direct_capture.py`)
//! names and records each row of a run in a Python loop (`run_members`, "the
//! per-row loop" below). When Rust read every row (each is a
//! `SimpleVueRecord` holding a `_NativeRow`), that loop does the same work
//! for each row, so one [`NativeRun`] does it for the whole run instead:
//!
//! 1. `_NativeRun.try_new(...)` reads each row's record once, checks that
//!    the row qualifies (the same class, template fragment and call site as
//!    the others, an exact `str` key and render id with a UTF-8 form, no
//!    `js_data` and no root markers), and computes both ids of each row.
//!    It changes no assembly state, and returns None when any row does not
//!    qualify or a key, render id or child id repeats within the run.
//! 2. `run.commit(...)` checks every row against the assembly's live sets
//!    and dicts first, then writes the rows' entries into them in row order.
//!    It returns False, having written nothing, when any check fails.
//! 3. After the whole assembly, `run.check_invariants(...)` makes, for the
//!    run's rows, the checks Python makes over every occurrence at the end.
//!
//! On None or False, the per-row loop runs the whole run and raises any
//! error at the row where it fails, so Rust never writes Citry's messages.
//!
//! The view then holds one [`NativeOccurrence`] per row, made by
//! `run.occurrences()`. The manifest's occurrence list holds the run itself
//! once, at its first row's place, and `_encode_occurrences` (in `rows.rs`)
//! writes all its rows' items through [`write_run`].
//!
//! Both classes are created untracked ([`super::new_untracked`]), so the
//! cyclic garbage collector skips them: they hold only strs, `_NativeRow`s
//! (also untracked) and, for an occurrence, its run, none of which can refer
//! back to them.

use pyo3::exceptions::{PyException, PyValueError};
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::sync::PyOnceLock;
use pyo3::types::{PyDict, PyList, PySet, PyString, PyTuple, PyType};

use citry_native_render::{OccurrenceItem, RunIds, first_repeat, write_occurrence_item};

use super::rows::{NativeRow, without_panics};

/// One row of a run: the ids Rust computed, and what Python handed over.
struct RunRow {
    child_id: Py<PyString>,
    placement_key: Py<PyString>,
    render_id: Py<PyString>,
    key: Py<PyString>,
    row: Py<NativeRow>,
}

/// One call run whose rows Rust read, recorded with one object instead of
/// one Python record per row.
#[pyclass(frozen, name = "_NativeRun", module = "citry_core._rust.native_render")]
pub struct NativeRun {
    parent_id: Py<PyString>,
    type_key: Py<PyString>,
    definition_id: Py<PyString>,
    rows: Vec<RunRow>,
}

/// Return `value` as an exact `str` that has a UTF-8 form, or None.
fn exact_utf8<'py>(value: &Bound<'py, PyAny>) -> Option<Bound<'py, PyString>> {
    let text = value.cast_exact::<PyString>().ok()?;
    // A lone surrogate has no UTF-8 form, so Rust cannot hash or write it.
    text.to_str().ok()?;
    Some(text.clone())
}

/// Read `name` from `value`; None when the read raises an ordinary exception.
///
/// The per-row loop then makes the same read at that row and raises whatever
/// it meets there. An exception that is not an `Exception` (`KeyboardInterrupt`,
/// `SystemExit`) propagates, so a decline never swallows an interrupt.
fn attr<'py>(
    value: &Bound<'py, PyAny>,
    name: &Bound<'py, PyString>,
) -> PyResult<Option<Bound<'py, PyAny>>> {
    let py = value.py();
    match value.getattr(name) {
        Ok(found) => Ok(Some(found)),
        Err(error) if error.is_instance_of::<PyException>(py) => Ok(None),
        Err(error) => Err(error),
    }
}

/// Whether `value` is true; None when its truth test (`__bool__` or
/// `__len__`) raises an ordinary exception, as for [`attr`].
fn truthy(value: &Bound<'_, PyAny>) -> PyResult<Option<bool>> {
    let py = value.py();
    match value.is_truthy() {
        Ok(flag) => Ok(Some(flag)),
        Err(error) if error.is_instance_of::<PyException>(py) => Ok(None),
        Err(error) => Err(error),
    }
}

/// Unwrap an `Option` inside `read_member`, declining the run on None.
macro_rules! or_decline {
    ($value:expr) => {
        match $value {
            Some(found) => found,
            None => return Ok(None),
        }
    };
}

/// What `try_new` reads from one member that qualifies.
struct Member<'py> {
    key: Bound<'py, PyString>,
    render_id: Bound<'py, PyString>,
    row: Py<NativeRow>,
}

/// The objects every member of a run must share with the first one.
struct RunShape<'a, 'py> {
    record_type: &'a Bound<'py, PyType>,
    component_class: &'a Bound<'py, PyAny>,
    fragment: &'a Bound<'py, PyAny>,
    source: &'a Bound<'py, PyAny>,
    source_span: &'a Bound<'py, PyAny>,
    type_key: &'a str,
}

impl RunShape<'_, '_> {
    /// Read and check one run member; return None when it does not qualify.
    ///
    /// Every failed check, and every ordinary exception raised while reading
    /// (a property that raises), gives None: the per-row loop then reads the
    /// member again and raises any error itself.
    fn read_member<'py>(&self, member: &Bound<'py, PyAny>) -> PyResult<Option<Member<'py>>> {
        let py = member.py();
        // `SimpleVueRecord` is final, so an exact type check is the check
        // the per-row loop makes.
        if !member.get_type().is(self.record_type) {
            return Ok(None);
        }
        // Only a row Rust read has a `_NativeRow`; any other row needs
        // Python's leaf and so the per-row loop.
        let native = or_decline!(attr(member, intern!(py, "native"))?);
        let row = or_decline!(native.cast_exact::<NativeRow>().ok())
            .clone()
            .unbind();
        // The per-row loop sends a row with `js_data` or root markers to
        // `transform_component`, which converts them, so a run holding such
        // a row stays with the per-row loop.
        for name in [intern!(py, "js_data"), intern!(py, "root_markers")] {
            if or_decline!(truthy(&or_decline!(attr(member, name)?))?) {
                return Ok(None);
            }
        }
        let class_id = or_decline!(attr(member, intern!(py, "class_id"))?);
        let class_id = or_decline!(exact_utf8(&class_id));
        if class_id.to_str()? != self.type_key {
            return Ok(None);
        }
        // Python checks the class against the registry once per run, so
        // every row must hold that same class object.
        if !or_decline!(attr(member, intern!(py, "component_class"))?).is(self.component_class) {
            return Ok(None);
        }
        // One definition serves the run only when every row has the same
        // template fragment (assembly caches definitions by its identity).
        if !or_decline!(attr(member, intern!(py, "fragment"))?).is(self.fragment) {
            return Ok(None);
        }
        let metadata = or_decline!(attr(member, intern!(py, "call_metadata"))?);
        // The run's placement prefix was hashed from the first row's source
        // and span, so every row must carry those same objects.
        if !or_decline!(attr(&metadata, intern!(py, "source"))?).is(self.source)
            || !or_decline!(attr(&metadata, intern!(py, "source_span"))?).is(self.source_span)
        {
            return Ok(None);
        }
        let key = or_decline!(exact_utf8(&or_decline!(attr(
            &metadata,
            intern!(py, "explicit_key")
        )?)));
        // An exact str render id compares by its text, which the repeat
        // check in `try_new` relies on; a str subclass stays with Python.
        let render_id = or_decline!(exact_utf8(&or_decline!(attr(
            member,
            intern!(py, "render_id")
        )?)));
        Ok(Some(Member {
            key,
            render_id,
            row,
        }))
    }
}

impl NativeRun {
    /// Write every row's manifest item, separated by commas, with the
    /// definition id the compiler gave this run's definition.
    fn write_items(
        &self,
        py: Python<'_>,
        out: &mut String,
        compiled_definition_id: &str,
    ) -> PyResult<()> {
        let parent_id = self.parent_id.bind(py).to_str()?;
        let type_key = self.type_key.bind(py).to_str()?;
        for (index, row) in self.rows.iter().enumerate() {
            if index > 0 {
                out.push(',');
            }
            write_occurrence_item(
                out,
                &OccurrenceItem {
                    definition_id: compiled_definition_id,
                    id: row.child_id.bind(py).to_str()?,
                    parent_id: Some(parent_id),
                    placement_key: Some(row.placement_key.bind(py).to_str()?),
                    prepared_json: &row.row.get().json,
                    render_id: row.render_id.bind(py).to_str()?,
                    type_key,
                },
            );
        }
        Ok(())
    }
}

#[pymethods]
impl NativeRun {
    /// Read and check a run's members; return the run, or None to leave it
    /// to the per-row loop.
    ///
    /// `record_type` is `SimpleVueRecord`; `component_class`, `fragment`,
    /// `source` and `source_span` are the first member's, and every member
    /// must hold the same objects. `placement_prefix_json` and
    /// `child_prefix_json` are the texts Python's `_DigestPrefix` hashes
    /// before each row's own item. `parent_id` is the occurrence that places
    /// the run, `type_key` the rows' class id and `definition_id` the rows'
    /// shared definition.
    #[staticmethod]
    #[allow(clippy::too_many_arguments)]
    fn try_new<'py>(
        py: Python<'py>,
        members: &Bound<'_, PyList>,
        record_type: &Bound<'_, PyType>,
        component_class: &Bound<'_, PyAny>,
        fragment: &Bound<'_, PyAny>,
        source: &Bound<'_, PyAny>,
        source_span: &Bound<'_, PyAny>,
        placement_prefix_json: &str,
        child_prefix_json: &str,
        parent_id: &Bound<'_, PyString>,
        type_key: &Bound<'_, PyString>,
        definition_id: &Bound<'_, PyString>,
    ) -> PyResult<Option<Bound<'py, NativeRun>>> {
        without_panics(|| {
            // The manifest writer writes the parent id and type key as text,
            // and the getters hand all three back to Python as the exact strs
            // assembly uses, so each must be an exact str with a UTF-8 form.
            let (Some(parent), Some(type_text), Some(definition)) = (
                exact_utf8(parent_id.as_any()),
                exact_utf8(type_key.as_any()),
                exact_utf8(definition_id.as_any()),
            ) else {
                return Ok(None);
            };
            let type_str = type_text.to_str()?.to_owned();
            // An empty run, or a class id Python would reject, goes to the
            // per-row loop, which raises for the latter.
            if members.is_empty() || type_str.is_empty() {
                return Ok(None);
            }
            let shape = RunShape {
                record_type,
                component_class,
                fragment,
                source,
                source_span,
                type_key: &type_str,
            };
            let mut read = Vec::with_capacity(members.len());
            for member in members.iter() {
                match shape.read_member(&member)? {
                    Some(value) => read.push(value),
                    None => return Ok(None),
                }
            }
            // A repeated key or render id fails Python's checks at that row,
            // with Python's message, so the run goes back to the per-row loop.
            let keys = read
                .iter()
                .map(|member| member.key.to_str())
                .collect::<PyResult<Vec<&str>>>()?;
            let render_ids = read
                .iter()
                .map(|member| member.render_id.to_str())
                .collect::<PyResult<Vec<&str>>>()?;
            if first_repeat(keys.iter().copied()).is_some()
                || first_repeat(render_ids.iter().copied()).is_some()
            {
                return Ok(None);
            }
            let ids = RunIds::new(placement_prefix_json, child_prefix_json);
            let pairs: Vec<(String, String)> = keys.iter().map(|key| ids.member_ids(key)).collect();
            // Two keys whose child ids collide would trip Python's own check.
            if first_repeat(pairs.iter().map(|(_, child)| child.as_str())).is_some() {
                return Ok(None);
            }
            let rows = read
                .into_iter()
                .zip(pairs)
                .map(|(member, (placement_key, child_id))| RunRow {
                    child_id: PyString::new(py, &child_id).unbind(),
                    placement_key: PyString::new(py, &placement_key).unbind(),
                    render_id: member.render_id.unbind(),
                    key: member.key.unbind(),
                    row: member.row,
                })
                .collect();
            let run = NativeRun {
                parent_id: parent.unbind(),
                type_key: type_text.unbind(),
                definition_id: definition.unbind(),
                rows,
            };
            Ok(Some(super::new_untracked(py, run)?))
        })
    }

    /// Check the run against the assembly's live state; when every check
    /// passes, write the rows' entries in row order and return True.
    ///
    /// The checks are the ones the per-row loop makes for each row: its
    /// render id and child id are new to `seen_render_ids` and
    /// `seen_occurrence_ids`, its `(member_base, placement_route, key)`
    /// identity is new to `local_identity_keys` (another run of the same
    /// call site under the same owner shares that set), and no fills are
    /// addressed to it in `supplied_fills`. A failed check returns False
    /// before anything is written.
    #[allow(clippy::too_many_arguments)]
    fn commit(
        &self,
        py: Python<'_>,
        seen_render_ids: &Bound<'_, PySet>,
        seen_occurrence_ids: &Bound<'_, PySet>,
        local_identity_keys: &Bound<'_, PySet>,
        member_base: &Bound<'_, PyAny>,
        placement_route: &Bound<'_, PyAny>,
        supplied_fills: &Bound<'_, PyDict>,
        occurrence_to_render: &Bound<'_, PyDict>,
        render_to_occurrence: &Bound<'_, PyDict>,
        occurrence_types: &Bound<'_, PyDict>,
        occurrence_parents: &Bound<'_, PyDict>,
        occurrence_placement_keys: &Bound<'_, PyDict>,
    ) -> PyResult<bool> {
        without_panics(|| {
            // Every check runs before any write, so a False leaves the
            // per-row loop the exact state it would have met.
            let mut identities = Vec::with_capacity(self.rows.len());
            for row in &self.rows {
                let identity = PyTuple::new(
                    py,
                    [
                        member_base.clone(),
                        placement_route.clone(),
                        row.key.bind(py).clone().into_any(),
                    ],
                )?;
                if seen_render_ids.contains(row.render_id.bind(py))?
                    || seen_occurrence_ids.contains(row.child_id.bind(py))?
                    || local_identity_keys.contains(&identity)?
                    // Fills addressed to a row need the per-row loop, which
                    // writes such a run as one call per row with its fills.
                    // `contains` does not run a defaultdict's factory, so an
                    // empty entry a read left also declines.
                    || supplied_fills.contains(row.child_id.bind(py))?
                {
                    return Ok(false);
                }
                identities.push(identity);
            }
            let parent_id = self.parent_id.bind(py);
            let type_key = self.type_key.bind(py);
            for (row, identity) in self.rows.iter().zip(identities) {
                let child_id = row.child_id.bind(py);
                let render_id = row.render_id.bind(py);
                seen_render_ids.add(render_id)?;
                seen_occurrence_ids.add(child_id)?;
                local_identity_keys.add(identity)?;
                occurrence_to_render.set_item(child_id, render_id)?;
                occurrence_types.set_item(child_id, type_key)?;
                occurrence_parents.set_item(child_id, parent_id)?;
                occurrence_placement_keys.set_item(child_id, row.placement_key.bind(py))?;
                render_to_occurrence.set_item(render_id, child_id)?;
            }
            Ok(true)
        })
    }

    /// Make assembly's final per-occurrence checks for the run's rows, in
    /// row order; return None, or `(row index, check)` for the first row
    /// that fails.
    ///
    /// Check 0: no other call references the row (`reference_parents` has
    /// no non-empty entry for it; the run's own reference is implied).
    /// Check 1: the row's `(parent id, placement key)` is new to
    /// `placements`, which this adds it to.
    fn check_invariants(
        &self,
        py: Python<'_>,
        reference_parents: &Bound<'_, PyDict>,
        placements: &Bound<'_, PySet>,
    ) -> PyResult<Option<(usize, u8)>> {
        without_panics(|| {
            let parent_id = self.parent_id.bind(py);
            for (index, row) in self.rows.iter().enumerate() {
                // `get_item` does not run a defaultdict's factory.
                if let Some(references) = reference_parents.get_item(row.child_id.bind(py))?
                    && references.is_truthy()?
                {
                    return Ok(Some((index, 0)));
                }
                let placement = PyTuple::new(
                    py,
                    [
                        parent_id.clone().into_any(),
                        row.placement_key.bind(py).clone().into_any(),
                    ],
                )?;
                if placements.contains(&placement)? {
                    return Ok(Some((index, 1)));
                }
                placements.add(placement)?;
            }
            Ok(None)
        })
    }

    /// The rows' child occurrence ids, in row order: the run's `callRuns`
    /// entry.
    fn member_ids<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        PyList::new(py, self.rows.iter().map(|row| row.child_id.bind(py)))
    }

    /// One `_NativeOccurrence` per row, in row order, for the view.
    fn occurrences<'py>(slf: &Bound<'py, Self>) -> PyResult<Vec<Bound<'py, NativeOccurrence>>> {
        let run = slf.clone().unbind();
        (0..slf.get().rows.len())
            .map(|index| {
                let occurrence = NativeOccurrence {
                    run: run.clone_ref(slf.py()),
                    index,
                };
                super::new_untracked(slf.py(), occurrence)
            })
            .collect()
    }

    /// Whether any of `ids` is one of the run's child occurrence ids.
    fn holds_any(&self, py: Python<'_>, ids: &Bound<'_, PyAny>) -> PyResult<bool> {
        // Callers pass a few ids (the page's Events instances), so each is
        // compared with every row.
        let mut wanted = Vec::new();
        for id in ids.try_iter()? {
            let id = id?;
            if let Ok(text) = id.cast::<PyString>()
                && let Ok(text) = text.to_str()
            {
                wanted.push(text.to_owned());
            }
        }
        for row in &self.rows {
            let child = row.child_id.bind(py).to_str()?;
            if wanted.iter().any(|id| id == child) {
                return Ok(true);
            }
        }
        Ok(false)
    }

    #[getter]
    fn parent_id(&self, py: Python<'_>) -> Py<PyString> {
        self.parent_id.clone_ref(py)
    }

    #[getter]
    fn type_key(&self, py: Python<'_>) -> Py<PyString> {
        self.type_key.clone_ref(py)
    }

    #[getter]
    fn definition_id(&self, py: Python<'_>) -> Py<PyString> {
        self.definition_id.clone_ref(py)
    }

    fn __len__(&self) -> usize {
        self.rows.len()
    }
}

/// The two read-only mappings every run row returns: its server data (an
/// empty mapping) and its prepared data (`{"calls": {}}`, what assembly
/// leaves in a Rust-read row's own dict). One of each, made once.
static SHARED_DATA: PyOnceLock<(Py<PyAny>, Py<PyAny>)> = PyOnceLock::new();

fn shared_data(py: Python<'_>) -> PyResult<&(Py<PyAny>, Py<PyAny>)> {
    SHARED_DATA.get_or_try_init(py, || {
        let proxy = py.import("types")?.getattr("MappingProxyType")?;
        let server = proxy.call1((PyDict::new(py),))?;
        let calls = proxy.call1((PyDict::new(py),))?;
        let prepared = PyDict::new(py);
        prepared.set_item("calls", calls)?;
        let prepared = proxy.call1((prepared,))?;
        Ok((server.unbind(), prepared.unbind()))
    })
}

/// One row of a `_NativeRun`, as the view's occurrence list holds it.
///
/// It has the attributes assembly's consumers read from an occurrence.
/// `server_data` and `prepared_data` return shared read-only mappings, so a
/// consumer that tries to change them fails instead of changing every row.
#[pyclass(
    frozen,
    name = "_NativeOccurrence",
    module = "citry_core._rust.native_render"
)]
pub struct NativeOccurrence {
    run: Py<NativeRun>,
    index: usize,
}

impl NativeOccurrence {
    fn row(&self) -> &RunRow {
        &self.run.get().rows[self.index]
    }
}

#[pymethods]
impl NativeOccurrence {
    #[getter]
    fn id(&self, py: Python<'_>) -> Py<PyString> {
        self.row().child_id.clone_ref(py)
    }

    #[getter]
    fn type_key(&self, py: Python<'_>) -> Py<PyString> {
        self.run.get().type_key.clone_ref(py)
    }

    #[getter]
    fn definition_id(&self, py: Python<'_>) -> Py<PyString> {
        self.run.get().definition_id.clone_ref(py)
    }

    #[getter]
    fn parent_id(&self, py: Python<'_>) -> Py<PyString> {
        self.run.get().parent_id.clone_ref(py)
    }

    #[getter]
    fn placement_key(&self, py: Python<'_>) -> Py<PyString> {
        self.row().placement_key.clone_ref(py)
    }

    #[getter]
    fn render_id(&self, py: Python<'_>) -> Py<PyString> {
        self.row().render_id.clone_ref(py)
    }

    /// The row Rust read, as `PreparedOccurrence._native` holds it.
    #[getter(_native)]
    fn native(&self, py: Python<'_>) -> Py<NativeRow> {
        self.row().row.clone_ref(py)
    }

    #[getter]
    fn server_data(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(shared_data(py)?.0.clone_ref(py))
    }

    #[getter]
    fn prepared_data(&self, py: Python<'_>) -> PyResult<Py<PyAny>> {
        Ok(shared_data(py)?.1.clone_ref(py))
    }

    /// The run this row belongs to.
    #[getter]
    fn run(&self, py: Python<'_>) -> Py<NativeRun> {
        self.run.clone_ref(py)
    }

    /// The row's position in its run.
    #[getter]
    fn index(&self) -> usize {
        self.index
    }

    fn __repr__(&self, py: Python<'_>) -> PyResult<String> {
        // Python's own repr of the id, as a dataclass repr would show it.
        Ok(format!(
            "_NativeOccurrence(id={}, index={})",
            self.row().child_id.bind(py).repr()?,
            self.index
        ))
    }
}

/// Look up a run's compiled definition id in `definition_ids` (logical id
/// to compiled id) and write its rows, for `_encode_occurrences`.
pub(super) fn write_run(
    out: &mut String,
    run: &NativeRun,
    definition_ids: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    // A run's rows carry the compiled id, which only the caller knows.
    let ids = definition_ids.ok_or_else(|| {
        PyValueError::new_err("a manifest with a native run needs definition_ids")
    })?;
    let py = ids.py();
    let compiled = ids
        .get_item(run.definition_id.bind(py))?
        .ok_or_else(|| PyValueError::new_err("native run definition has no compiled id"))?;
    let compiled = compiled
        .cast::<PyString>()
        .map_err(|_| PyValueError::new_err("compiled definition id is not a str"))?;
    run.write_items(py, out, compiled.to_str()?)
}

/// Register level B1's classes on the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<NativeRun>()?;
    module.add_class::<NativeOccurrence>()?;
    Ok(())
}
