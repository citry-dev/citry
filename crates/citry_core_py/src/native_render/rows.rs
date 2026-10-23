//! Level A of the native render path: Rust reads each `simple='vue'` row
//! and writes its prepared data, and hashes the ids of each row of a call
//! run. The design, the decision of when this runs and every error mode are
//! in `docs/design/native_render.md`.
//!
//! For a `simple='vue'` template it can evaluate without a component
//! instance, Python turns the operations and read set into plain tuples
//! (`native_row_plan_tuples` in `citry/_vue/leaf_program.py`) and builds a
//! [`RowPlan`] from them once per template. For each row, after the
//! row's data callbacks ran, `RowPlan.read(variables, plain_scalar_types)`:
//!
//! 1. reads every value the template reads through the C API, applying the
//!    same type checks as Python's read-set check, and copies it into a
//!    [`citry_native_render::Value`] tree;
//! 2. evaluates the template over that copy and writes the row's prepared
//!    data as JSON;
//! 3. returns a [`NativeRow`] holding both, or None when any check fails or
//!    a case is outside what Rust reproduces exactly (Rust "declines" the row).
//!    Python then runs its own evaluator on the same variables, which raises
//!    its own error or gives its own result.
//!
//! `NativeRow.snapshot()` rebuilds the read values as fresh Python objects,
//! so every output that needs Python's own leaf (static HTML, fragments,
//! pages that keep their body, Events updates) can run the Python evaluator
//! over them later.
//! `_encode_occurrences` writes a manifest's occurrence array, putting each
//! native row's JSON in place of its prepared data, and writes every row of
//! a `_NativeRun` (level B1, `runs.rs`) from Rust, and each ordinary
//! occurrence whose leaf data Rust wrote (level B2, `leaf_json.rs`) with that
//! JSON in place of the placeholder object Python stored under each leaf
//! key. `_RunDigests` computes
//! the ids of each row of a repeated component call, as Python's
//! `_DigestPrefix` does.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::gc::PyVisit;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};
use pyo3::{PyTraverseError, PyTypeInfo, intern};

use crate::panics::catch_panic;
use citry_native_render::{
    Attrs, Const, ExprSpec, Kinds, OpSpec, Plan, PlanSpec, ReadNode, ReadNodeSpec, RunIds,
    SpreadLayout, Value, write_json_str,
};

use super::leaf_json::{LeafJson, write_leaf_occurrence};
use super::runs::{NativeRun, write_run};

// ---------------------------------------------------------------------------
// Why a row goes back to Python.
// ---------------------------------------------------------------------------

/// Why Rust declines a row, so that Python evaluates it.
// Each variant names one reason for the reader of this file; nothing
// counts or reports them, because Python's evaluator then handles the row
// and raises its own error when there is one.
#[derive(Clone, Copy, Debug)]
enum Decline {
    /// The variables are not an exact dict (Python also accepts its
    /// read-only mapping, which Rust leaves to Python).
    VariablesNotDict,
    /// A variable shares a loop target's name.
    ShadowedLoopTarget,
    /// A value the template reads is missing or fails a type check.
    NotPlain,
    /// A str has no UTF-8 form (a lone surrogate).
    NotUtf8,
    /// An int outside the i64 range. Its text depends on Python's int
    /// digit limit, which can change between the render and a later
    /// serialize, so Python evaluates such a row (they are rare).
    BigInt,
    /// Python's layout for this `c-bind` key set is None, so the row needs
    /// Python's per-row merge of the spread with the element's other
    /// attributes (which also raises the errors for invalid names).
    SpreadUnsupported,
    /// A new `c-bind` key set arrived after the layout cache filled up.
    SpreadLimit,
    /// The layout callback raised; Python's own path then evaluates the row
    /// and raises any error there.
    SpreadCallbackError,
    /// Evaluation met a value the checks should have excluded.
    Internal,
}

// ---------------------------------------------------------------------------
// Reading the plan tuples Python passes.
// ---------------------------------------------------------------------------

fn plan_error(message: impl Into<String>) -> PyErr {
    PyValueError::new_err(message.into())
}

fn item<'py>(tuple: &Bound<'py, PyTuple>, index: usize) -> PyResult<Bound<'py, PyAny>> {
    tuple.get_item(index)
}

fn as_tuple<'a, 'py>(value: &'a Bound<'py, PyAny>) -> PyResult<&'a Bound<'py, PyTuple>> {
    value
        .cast_exact::<PyTuple>()
        .map_err(|_| plan_error("row plan parts must be tuples"))
}

fn string_items(value: &Bound<'_, PyAny>) -> PyResult<Vec<String>> {
    as_tuple(value)?
        .iter()
        .map(|item| item.extract::<String>())
        .collect()
}

fn lower_expr(value: &Bound<'_, PyAny>) -> PyResult<ExprSpec> {
    let tuple = as_tuple(value)?;
    let tag: String = item(tuple, 0)?.extract()?;
    match tag.as_str() {
        "c" => {
            let literal = item(tuple, 1)?;
            // Exact types only: the expression subset admits None, bool and
            // str literals, and a subclass could print differently.
            let py = literal.py();
            let kind = literal.get_type_ptr();
            Ok(ExprSpec::Const(if literal.is_none() {
                Const::None
            } else if kind == PyBool::type_object_raw(py) {
                Const::Bool(literal.is_truthy()?)
            } else if kind == PyString::type_object_raw(py) {
                Const::Str(literal.extract()?)
            } else {
                return Err(plan_error("unsupported literal"));
            }))
        }
        "p" => Ok(ExprSpec::Path {
            root: item(tuple, 1)?.extract()?,
            keys: string_items(&item(tuple, 2)?)?,
        }),
        "i" => Ok(ExprSpec::If {
            test: Box::new(lower_expr(&item(tuple, 1)?)?),
            body: Box::new(lower_expr(&item(tuple, 2)?)?),
            otherwise: Box::new(lower_expr(&item(tuple, 3)?)?),
        }),
        other => Err(plan_error(format!("unknown expression {other:?}"))),
    }
}

/// Turn one scope into ops, collecting each spread's layout callback in the
/// order the plan numbers spreads (source order, top level only).
fn lower_ops(value: &Bound<'_, PyAny>, callbacks: &mut Vec<Py<PyAny>>) -> PyResult<Vec<OpSpec>> {
    let mut ops = Vec::new();
    for op in as_tuple(value)?.iter() {
        let tuple = as_tuple(&op)?;
        let tag: String = item(tuple, 0)?.extract()?;
        let key: String = item(tuple, 1)?.extract()?;
        ops.push(match tag.as_str() {
            "text" => OpSpec::Text {
                key,
                expr: lower_expr(&item(tuple, 2)?)?,
            },
            "open" => {
                let mut attributes = Vec::new();
                for attribute in as_tuple(&item(tuple, 2)?)?.iter() {
                    let pair = as_tuple(&attribute)?;
                    attributes.push((item(pair, 0)?.extract()?, lower_expr(&item(pair, 1)?)?));
                }
                OpSpec::Open { key, attributes }
            }
            "spread" => {
                callbacks.push(item(tuple, 3)?.unbind());
                OpSpec::Spread {
                    key,
                    expr: lower_expr(&item(tuple, 2)?)?,
                }
            }
            "if" => {
                let mut branches = Vec::new();
                for branch in as_tuple(&item(tuple, 2)?)?.iter() {
                    let pair = as_tuple(&branch)?;
                    let condition = item(pair, 0)?;
                    let condition = if condition.is_none() {
                        None
                    } else {
                        Some(lower_expr(&condition)?)
                    };
                    branches.push((condition, lower_ops(&item(pair, 1)?, callbacks)?));
                }
                OpSpec::If { key, branches }
            }
            "for" => OpSpec::For {
                key,
                target: item(tuple, 2)?.extract()?,
                iterable: lower_expr(&item(tuple, 3)?)?,
                body: lower_ops(&item(tuple, 4)?, callbacks)?,
                empty: lower_ops(&item(tuple, 5)?, callbacks)?,
            },
            other => return Err(plan_error(format!("unknown operation {other:?}"))),
        });
    }
    Ok(ops)
}

fn lower_read_node(value: &Bound<'_, PyAny>) -> PyResult<ReadNodeSpec> {
    let tuple = as_tuple(value)?;
    let kind_names = string_items(&item(tuple, 0)?)?;
    let kinds = Kinds::from_names(kind_names.iter().map(String::as_str))
        .map_err(|error| plan_error(error.0))?;
    let mut children = Vec::new();
    for child in as_tuple(&item(tuple, 1)?)?.iter() {
        let pair = as_tuple(&child)?;
        children.push((item(pair, 0)?.extract()?, lower_read_node(&item(pair, 1)?)?));
    }
    let items = item(tuple, 2)?;
    let items = if items.is_none() {
        None
    } else {
        Some(Box::new(lower_read_node(&items)?))
    };
    Ok(ReadNodeSpec {
        kinds,
        children,
        items,
    })
}

// ---------------------------------------------------------------------------
// The plan object.
// ---------------------------------------------------------------------------

/// A read node with each child key as an interned Python str, created once,
/// so a row's lookups hash nothing new.
struct PyReadNode {
    kinds: Kinds,
    children: Vec<(Py<PyString>, PyReadNode)>,
    items: Option<Box<PyReadNode>>,
}

impl PyReadNode {
    fn new(py: Python<'_>, node: &ReadNode) -> Self {
        PyReadNode {
            kinds: node.kinds,
            children: node
                .children
                .iter()
                .map(|child| {
                    (
                        PyString::intern(py, &child.name).unbind(),
                        PyReadNode::new(py, child),
                    )
                })
                .collect(),
            items: node
                .items
                .as_ref()
                .map(|items| Box::new(PyReadNode::new(py, items))),
        }
    }

    /// A node nothing reads from: its value is only counted (a loop item
    /// whose body reads nothing from it).
    fn is_unread(&self) -> bool {
        self.kinds == Kinds::default() && self.children.is_empty() && self.items.is_none()
    }
}

/// What a plan and every row made from it share.
struct Shared {
    plan: Plan,
    roots: Vec<(Py<PyString>, PyReadNode)>,
    loop_targets: Vec<Py<PyString>>,
}

/// One root `c-bind`: Python's layout callback and the layouts seen so far.
struct SpreadSite {
    callback: Py<PyAny>,
    /// How many key sets to keep, from Python's `_ROOT_SPREAD_PLAN_LIMIT`
    /// when the plan was built. Past it a row with a new key set is
    /// declined, so a key set that changes every row cannot grow memory.
    limit: usize,
    /// Keyed by the spread dict's names in its own order; None records a key
    /// set Python said needs the full merge.
    layouts: Mutex<HashMap<Vec<String>, Option<Arc<SpreadLayout>>>>,
}

/// The Rust row plan for one `simple='vue'` template.
#[pyclass(frozen, name = "_RowPlan", module = "citry_core._rust.native_render")]
pub struct RowPlan {
    shared: Arc<Shared>,
    spreads: Vec<SpreadSite>,
}

/// Which builtin scalar types the caller's scalar set allows. Citry removes
/// a type from `_simple_json_plain_scalar_types()` once it is registered with
/// `ComponentLike`, so its values then render as components and Rust must
/// decline them, as Python's check does.
struct ScalarSet {
    allows_str: bool,
    allows_int: bool,
    allows_bool: bool,
    allows_float: bool,
}

impl ScalarSet {
    fn from_types(types: &Bound<'_, PyAny>) -> PyResult<Self> {
        let py = types.py();
        // `in` on the frozenset compares type objects by identity, as
        // Python's `type(value) in plain_scalar_types` does.
        Ok(ScalarSet {
            allows_str: types.contains(PyString::type_object(py))?,
            allows_int: types.contains(PyInt::type_object(py))?,
            allows_bool: types.contains(PyBool::type_object(py))?,
            allows_float: types.contains(PyFloat::type_object(py))?,
        })
    }

    /// The fixed set the root `c-bind`'s values are checked against
    /// (`_READSET_ATTR_VALUE_TYPES`), which ignores `ComponentLike`.
    const ALL: ScalarSet = ScalarSet {
        allows_str: true,
        allows_int: true,
        allows_bool: true,
        allows_float: true,
    };
}

/// The exact builtin type of a value; a subclass counts as `Other`, since it
/// could run user code when printed, compared or iterated.
#[derive(Clone, Copy, PartialEq, Eq)]
enum ExactType {
    None,
    Str,
    Int,
    Bool,
    Float,
    List,
    Dict,
    Other,
}

fn exact_type(value: &Bound<'_, PyAny>) -> ExactType {
    let py = value.py();
    if value.is_none() {
        return ExactType::None;
    }
    let kind = value.get_type_ptr();
    if kind == PyString::type_object_raw(py) {
        ExactType::Str
    } else if kind == PyInt::type_object_raw(py) {
        ExactType::Int
    } else if kind == PyBool::type_object_raw(py) {
        ExactType::Bool
    } else if kind == PyFloat::type_object_raw(py) {
        ExactType::Float
    } else if kind == PyList::type_object_raw(py) {
        ExactType::List
    } else if kind == PyDict::type_object_raw(py) {
        ExactType::Dict
    } else {
        ExactType::Other
    }
}

/// Python's `repr()` of a float, from CPython's own formatter.
///
/// This is the function `float.__repr__` calls, so the digits and the
/// placement of the decimal point match Python's on every value, including
/// the cases where two shortest texts are equally close to the value.
pub(super) fn python_float_repr(py: Python<'_>, number: f64) -> PyResult<String> {
    // SAFETY: PyOS_double_to_string only reads its arguments and returns a
    // NUL-terminated buffer from PyMem_Malloc, or NULL with an exception set.
    #[allow(unsafe_code)]
    unsafe {
        let buffer = pyo3::ffi::PyOS_double_to_string(
            number,
            b'r' as std::ffi::c_char,
            0,
            pyo3::ffi::Py_DTSF_ADD_DOT_0,
            std::ptr::null_mut(),
        );
        if buffer.is_null() {
            return Err(PyErr::fetch(py));
        }
        let text = std::ffi::CStr::from_ptr(buffer)
            .to_string_lossy()
            .into_owned();
        pyo3::ffi::PyMem_Free(buffer.cast());
        Ok(text)
    }
}

/// Copy one plain scalar of a known exact type.
fn copy_scalar(value: &Bound<'_, PyAny>, kind: ExactType) -> Result<Value, Decline> {
    let py = value.py();
    Ok(match kind {
        ExactType::None => Value::None,
        ExactType::Bool => Value::Bool(value.is_truthy().map_err(|_| Decline::Internal)?),
        ExactType::Int => Value::Int(value.extract::<i64>().map_err(|_| Decline::BigInt)?),
        ExactType::Float => {
            let number = value
                .cast_exact::<PyFloat>()
                .map_err(|_| Decline::Internal)?
                .value();
            Value::Float {
                value: number,
                text: python_float_repr(py, number).map_err(|_| Decline::Internal)?,
            }
        }
        ExactType::Str => Value::Str(
            value
                .cast_exact::<PyString>()
                .map_err(|_| Decline::Internal)?
                .to_str()
                .map_err(|_| Decline::NotUtf8)?
                .to_owned(),
        ),
        ExactType::List | ExactType::Dict | ExactType::Other => return Err(Decline::Internal),
    })
}

fn allowed_scalar(value: &Bound<'_, PyAny>, kind: ExactType, set: &ScalarSet) -> bool {
    match kind {
        ExactType::None => true,
        ExactType::Str => set.allows_str,
        ExactType::Int => set.allows_int,
        ExactType::Bool => set.allows_bool,
        ExactType::Float => set.allows_float && float_is_finite(value),
        ExactType::List | ExactType::Dict | ExactType::Other => false,
    }
}

fn float_is_finite(value: &Bound<'_, PyAny>) -> bool {
    value
        .cast_exact::<PyFloat>()
        .is_ok_and(|number| number.value().is_finite())
}

/// Read one value against its read node, applying every check Python's
/// read-set check applies to it (`_simple_json_readset_check_lines`).
fn read_value(
    value: &Bound<'_, PyAny>,
    node: &PyReadNode,
    set: &ScalarSet,
) -> Result<Value, Decline> {
    if node.is_unread() {
        return Ok(Value::Unread);
    }
    let kind = exact_type(value);
    let kinds = node.kinds;
    if kinds.scalar && !allowed_scalar(value, kind, set) {
        return Err(Decline::NotPlain);
    }
    if kinds.list && kind != ExactType::List {
        return Err(Decline::NotPlain);
    }
    if kinds.truth {
        let admitted = match kind {
            ExactType::Float => float_is_finite(value),
            ExactType::Other => false,
            _ => true,
        };
        if !admitted {
            return Err(Decline::NotPlain);
        }
    }
    if kinds.safe_attrs && kind != ExactType::Dict {
        return Err(Decline::NotPlain);
    }
    if kinds.safe_attrs_or_none && kind != ExactType::Dict && kind != ExactType::None {
        return Err(Decline::NotPlain);
    }
    if !node.children.is_empty() && kind != ExactType::Dict {
        return Err(Decline::NotPlain);
    }
    if node.items.is_some() && kind != ExactType::List {
        return Err(Decline::NotPlain);
    }
    match kind {
        ExactType::Dict => {
            let dict = value
                .cast_exact::<PyDict>()
                .map_err(|_| Decline::Internal)?;
            let attrs = if kinds.safe_attrs || kinds.safe_attrs_or_none {
                Some(read_attrs(dict)?)
            } else {
                None
            };
            let mut children = Vec::with_capacity(node.children.len());
            for (key, child) in &node.children {
                let child_value = dict
                    .get_item(key.bind(value.py()))
                    .map_err(|_| Decline::Internal)?
                    .ok_or(Decline::NotPlain)?;
                children.push(read_value(&child_value, child, set)?);
            }
            Ok(Value::Dict {
                len: dict.len(),
                children,
                attrs,
            })
        }
        ExactType::List => {
            let list = value
                .cast_exact::<PyList>()
                .map_err(|_| Decline::Internal)?;
            let mut items = Vec::new();
            if let Some(item_node) = &node.items {
                items.reserve(list.len());
                for entry in list.iter() {
                    items.push(read_value(&entry, item_node, set)?);
                }
            }
            Ok(Value::List {
                len: list.len(),
                items,
            })
        }
        ExactType::Other => Err(Decline::NotPlain),
        _ => copy_scalar(value, kind),
    }
}

/// Read the dict a root `c-bind` spreads: str names and plain scalar values
/// from the fixed set (`_readset_safe_attrs`), kept in the dict's order.
fn read_attrs(dict: &Bound<'_, PyDict>) -> Result<Attrs, Decline> {
    let mut attrs = Attrs {
        names: Vec::with_capacity(dict.len()),
        values: Vec::with_capacity(dict.len()),
    };
    for (name, value) in dict.iter() {
        if exact_type(&name) != ExactType::Str {
            return Err(Decline::NotPlain);
        }
        let kind = exact_type(&value);
        if !allowed_scalar(&value, kind, &ScalarSet::ALL) {
            return Err(Decline::NotPlain);
        }
        attrs.names.push(
            name.cast_exact::<PyString>()
                .map_err(|_| Decline::Internal)?
                .to_str()
                .map_err(|_| Decline::NotUtf8)?
                .to_owned(),
        );
        attrs.values.push(copy_scalar(&value, kind)?);
    }
    Ok(attrs)
}

impl SpreadSite {
    /// The layout for this row's key set: cached, or asked of Python once.
    fn layout(&self, py: Python<'_>, names: &[String]) -> Result<Arc<SpreadLayout>, Decline> {
        {
            let layouts = self.layouts.lock().map_err(|_| Decline::Internal)?;
            match layouts.get(names) {
                Some(Some(layout)) => return Ok(layout.clone()),
                Some(None) => return Err(Decline::SpreadUnsupported),
                None if layouts.len() >= self.limit => return Err(Decline::SpreadLimit),
                None => {}
            }
        }
        // The lock is released while Python runs, so the callback can never
        // deadlock against another row of the same template.
        let keys = PyTuple::new(py, names).map_err(|_| Decline::Internal)?;
        let entries = match self.callback.bind(py).call1((keys,)) {
            Ok(entries) => entries,
            // Python's own path calls the same function and raises there,
            // with the template position attached, so nothing is cached here.
            Err(_) => return Err(Decline::SpreadCallbackError),
        };
        let layout = convert_layout(names, &entries)?;
        let mut layouts = self.layouts.lock().map_err(|_| Decline::Internal)?;
        layouts.insert(names.to_vec(), layout.clone());
        layout.ok_or(Decline::SpreadUnsupported)
    }
}

fn convert_layout(
    names: &[String],
    entries: &Bound<'_, PyAny>,
) -> Result<Option<Arc<SpreadLayout>>, Decline> {
    if entries.is_none() {
        return Ok(None);
    }
    let tuple = entries
        .cast_exact::<PyTuple>()
        .map_err(|_| Decline::Internal)?;
    let mut converted = Vec::with_capacity(tuple.len());
    for entry in tuple.iter() {
        let (name, is_static, json): (String, bool, Option<String>) =
            entry.extract().map_err(|_| Decline::Internal)?;
        converted.push((name, is_static, json));
    }
    Ok(SpreadLayout::new(names, converted).ok().map(Arc::new))
}

impl RowPlan {
    fn read_row(
        &self,
        py: Python<'_>,
        variables: &Bound<'_, PyAny>,
        plain_scalar_types: &Bound<'_, PyAny>,
    ) -> PyResult<Result<NativeRow, Decline>> {
        let shared = &self.shared;
        let Ok(variables) = variables.cast_exact::<PyDict>() else {
            return Ok(Err(Decline::VariablesNotDict));
        };
        for target in &shared.loop_targets {
            if variables.contains(target.bind(py))? {
                return Ok(Err(Decline::ShadowedLoopTarget));
            }
        }
        let set = ScalarSet::from_types(plain_scalar_types)?;
        let mut values = Vec::with_capacity(shared.roots.len());
        for (name, node) in &shared.roots {
            let Some(value) = variables.get_item(name.bind(py))? else {
                return Ok(Err(Decline::NotPlain));
            };
            match read_value(&value, node, &set) {
                Ok(copied) => values.push(copied),
                Err(reason) => return Ok(Err(reason)),
            }
        }
        let mut layouts = Vec::with_capacity(self.spreads.len());
        for (index, site) in self.spreads.iter().enumerate() {
            let names: &[String] = match shared.plan.spread_value(&values, index) {
                Some(Value::None) => &[],
                Some(Value::Dict {
                    attrs: Some(attrs), ..
                }) => &attrs.names,
                _ => return Ok(Err(Decline::Internal)),
            };
            match site.layout(py, names) {
                Ok(layout) => layouts.push(layout),
                Err(reason) => return Ok(Err(reason)),
            }
        }
        let layout_refs: Vec<&SpreadLayout> = layouts.iter().map(|layout| &**layout).collect();
        let json = match shared.plan.write_row(&values, &layout_refs) {
            Ok(json) => json,
            Err(_) => return Ok(Err(Decline::Internal)),
        };
        Ok(Ok(NativeRow {
            shared: shared.clone(),
            values,
            json,
        }))
    }
}

/// Run `body`, turning a Rust panic into RuntimeError so Python's error
/// handling (which adds the component path) sees an ordinary exception.
pub(super) fn without_panics<T>(body: impl FnOnce() -> PyResult<T>) -> PyResult<T> {
    catch_panic(body).unwrap_or_else(|detail| {
        Err(PyRuntimeError::new_err(format!(
            "citry native_render failed: {detail}"
        )))
    })
}

impl RowPlan {
    /// The body of `_RowPlan(...)`, run inside `without_panics`.
    fn build(
        py: Python<'_>,
        ops: &Bound<'_, PyAny>,
        roots: &Bound<'_, PyAny>,
        loop_targets: &Bound<'_, PyAny>,
        spread_limit: usize,
        js_safe_integer: i64,
    ) -> PyResult<Self> {
        let mut callbacks = Vec::new();
        let ops = lower_ops(ops, &mut callbacks)?;
        let mut root_specs = Vec::new();
        for root in as_tuple(roots)?.iter() {
            let pair = as_tuple(&root)?;
            root_specs.push((item(pair, 0)?.extract()?, lower_read_node(&item(pair, 1)?)?));
        }
        let spec = PlanSpec {
            ops,
            roots: root_specs,
            loop_targets: string_items(loop_targets)?,
            js_safe_integer,
        };
        let plan = Plan::new(&spec).map_err(|error| plan_error(error.0))?;
        if plan.spread_count() != callbacks.len() {
            return Err(plan_error(
                "every c-bind spread needs exactly one layout callback",
            ));
        }
        let roots = plan
            .roots()
            .iter()
            .map(|node| {
                (
                    PyString::intern(py, &node.name).unbind(),
                    PyReadNode::new(py, node),
                )
            })
            .collect();
        let loop_targets = plan
            .loop_targets()
            .iter()
            .map(|name| PyString::intern(py, name).unbind())
            .collect();
        let spreads = callbacks
            .into_iter()
            .map(|callback| SpreadSite {
                callback,
                limit: spread_limit,
                layouts: Mutex::new(HashMap::new()),
            })
            .collect();
        Ok(RowPlan {
            shared: Arc::new(Shared {
                plan,
                roots,
                loop_targets,
            }),
            spreads,
        })
    }
}

#[pymethods]
impl RowPlan {
    /// Build a plan from `native_row_plan_tuples(node)`: the operations, the
    /// read set's roots, the loop targets, how many root `c-bind` key sets
    /// to keep, and the largest int an attribute sends as a number.
    ///
    /// **Raises**
    ///
    /// ValueError: If the description has a shape Rust cannot evaluate
    /// exactly; the template then keeps the Python evaluator.
    #[new]
    fn new(
        py: Python<'_>,
        ops: &Bound<'_, PyAny>,
        roots: &Bound<'_, PyAny>,
        loop_targets: &Bound<'_, PyAny>,
        spread_limit: usize,
        js_safe_integer: i64,
    ) -> PyResult<Self> {
        // A panic would otherwise raise PanicException, a BaseException that
        // escapes the caller's `except ValueError`.
        without_panics(|| Self::build(py, ops, roots, loop_targets, spread_limit, js_safe_integer))
    }

    /// Let Python's garbage collector see the layout callbacks. Each one
    /// holds the template node that holds this plan, so a dropped template
    /// forms a cycle. The node's own attributes can be cleared, which breaks
    /// that cycle, so this frozen plan needs no `__clear__`.
    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        for site in &self.spreads {
            visit.call(&site.callback)?;
        }
        Ok(())
    }

    /// Check, copy and evaluate one row; return a `_NativeRow`, or None to
    /// hand the row back to Python's evaluator.
    ///
    /// `plain_scalar_types` is Citry's `_simple_json_plain_scalar_types()`,
    /// read again for each row as Python's check does.
    fn read(
        &self,
        py: Python<'_>,
        variables: &Bound<'_, PyAny>,
        plain_scalar_types: &Bound<'_, PyAny>,
    ) -> PyResult<Option<NativeRow>> {
        without_panics(|| match self.read_row(py, variables, plain_scalar_types)? {
            Ok(row) => Ok(Some(row)),
            Err(_reason) => Ok(None),
        })
    }
}

// ---------------------------------------------------------------------------
// One produced row.
// ---------------------------------------------------------------------------

/// One row Rust produced: its copied values and its prepared data's JSON.
#[pyclass(frozen, name = "_NativeRow", module = "citry_core._rust.native_render")]
pub struct NativeRow {
    shared: Arc<Shared>,
    values: Vec<Value>,
    // `runs.rs` writes it into each run row's manifest item.
    pub(super) json: String,
}

/// Rebuild one copied value as a fresh Python object.
fn snapshot_value(py: Python<'_>, value: &Value, node: &PyReadNode) -> PyResult<Py<PyAny>> {
    Ok(match value {
        // An unread value only has to exist; nothing looks at it.
        Value::Unread | Value::None => py.None(),
        Value::Bool(flag) => PyBool::new(py, *flag).to_owned().into_any().unbind(),
        Value::Int(number) => number.into_pyobject(py)?.into_any().unbind(),
        // This reader declines ints outside i64, so only a value tree built
        // elsewhere (the fixture tests) holds one.
        Value::BigInt(text) => PyInt::type_object(py).call1((text.as_str(),))?.unbind(),
        Value::Float { value, .. } => PyFloat::new(py, *value).into_any().unbind(),
        Value::Str(text) => PyString::new(py, text).into_any().unbind(),
        Value::Dict {
            len,
            children,
            attrs,
        } => {
            let dict = PyDict::new(py);
            if let Some(attrs) = attrs {
                // The spread reads every entry, in order, and any child the
                // template also reads is one of them.
                for (name, item) in attrs.names.iter().zip(&attrs.values) {
                    dict.set_item(name, snapshot_value(py, item, node)?)?;
                }
            } else if !node.children.is_empty() {
                for ((key, child_node), child) in node.children.iter().zip(children) {
                    dict.set_item(key.bind(py), snapshot_value(py, child, child_node)?)?;
                }
            } else if *len > 0 {
                // Only the dict's truth is read; any non-empty dict has it.
                dict.set_item("", py.None())?;
            }
            dict.into_any().unbind()
        }
        Value::List { len, items } => {
            let list = PyList::empty(py);
            match &node.items {
                Some(item_node) => {
                    for entry in items {
                        list.append(snapshot_value(py, entry, item_node)?)?;
                    }
                }
                // Only the list's truth is read, so its items stay unread.
                None => {
                    for _ in 0..*len {
                        list.append(py.None())?;
                    }
                }
            }
            list.into_any().unbind()
        }
    })
}

#[pymethods]
impl NativeRow {
    /// The row's prepared data as `script_json({"calls": {}, **data},
    /// sort_keys=True)` writes it.
    #[getter]
    fn prepared_json(&self) -> &str {
        &self.json
    }

    /// Rebuild the read values as a fresh variables dict.
    ///
    /// Python's evaluator over this dict gives the same prepared data as it
    /// would have given over the row's own variables when Rust read them,
    /// even if those dicts changed since. Every value is plain data and every
    /// int fits in i64, so rebuilding it does not depend on interpreter
    /// settings.
    fn snapshot<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        without_panics(|| {
            let variables = PyDict::new(py);
            for ((name, node), value) in self.shared.roots.iter().zip(&self.values) {
                variables.set_item(name.bind(py), snapshot_value(py, value, node)?)?;
            }
            Ok(variables)
        })
    }
}

// ---------------------------------------------------------------------------
// Writing a manifest's occurrences.
// ---------------------------------------------------------------------------

/// The exact keys of a native row's manifest item, in sorted order.
const OCCURRENCE_KEYS: [&str; 8] = [
    "definitionId",
    "id",
    "parentId",
    "placementKey",
    "preparedData",
    "renderId",
    "serverData",
    "typeKey",
];

fn occurrence_error(message: &str) -> PyErr {
    PyValueError::new_err(format!("native occurrence item {message}"))
}

/// Read a str field of a manifest item. A str subclass is accepted, as
/// Citry's render-id check accepts one; `json.dumps` writes it from its
/// text, so the bytes are the same.
fn item_str<'a>(value: &'a Bound<'_, PyAny>, name: &str) -> PyResult<&'a str> {
    value
        .cast::<PyString>()
        .map_err(|_| occurrence_error(&format!("{name} is not a str")))?
        .to_str()
        // A lone surrogate has no UTF-8 form; report it like any other
        // malformed item rather than as a UnicodeEncodeError.
        .map_err(|_| occurrence_error(&format!("{name} has no UTF-8 form")))
}

fn is_empty_dict(value: &Bound<'_, PyAny>) -> bool {
    value
        .cast_exact::<PyDict>()
        .is_ok_and(|dict| dict.is_empty())
}

/// Write one native row's manifest item, confirming it has exactly the
/// shape assembly gives a native occurrence.
fn write_native_occurrence(
    out: &mut String,
    item: &Bound<'_, PyDict>,
    row: &NativeRow,
) -> PyResult<()> {
    let py = item.py();
    if item.len() != OCCURRENCE_KEYS.len() {
        return Err(occurrence_error("has unexpected keys"));
    }
    out.push('{');
    for (index, key) in OCCURRENCE_KEYS.iter().enumerate() {
        let value = item
            .get_item(key)?
            .ok_or_else(|| occurrence_error(&format!("has no {key}")))?;
        if index > 0 {
            out.push(',');
        }
        write_json_str(out, key);
        out.push(':');
        match *key {
            "preparedData" => {
                // Assembly leaves only the "calls" entry here for a native
                // row; the row's own data is the JSON Rust already wrote.
                let prepared = value
                    .cast_exact::<PyDict>()
                    .map_err(|_| occurrence_error("preparedData is not a dict"))?;
                let calls = prepared.get_item(intern!(py, "calls"))?;
                if prepared.len() != 1 || !calls.is_some_and(|calls| is_empty_dict(&calls)) {
                    return Err(occurrence_error("preparedData is not {\"calls\": {}}"));
                }
                out.push_str(&row.json);
            }
            "serverData" => {
                if !is_empty_dict(&value) {
                    return Err(occurrence_error("serverData is not empty"));
                }
                out.push_str("{}");
            }
            "parentId" | "placementKey" if value.is_none() => out.push_str("null"),
            _ => write_json_str(out, item_str(&value, key)?),
        }
    }
    out.push('}');
    Ok(())
}

/// Write a manifest's `occurrences` list as `script_json(list,
/// sort_keys=True)` would, with each native row's prepared data spliced in.
///
/// `natives` maps an occurrence id to its `_NativeRow`; a dict item whose id
/// it holds is written by Rust. It can also map another occurrence to a
/// `_LeafJson` (level B2, `leaf_json.rs`): that item is written with each
/// leaf value's JSON in place of its placeholder in `preparedData`, and its
/// other values as `fallback` writes them. A `_NativeRun` item stands for
/// all its rows, in order. Rust writes each row with the run's compiled
/// definition id, which it looks up in `definition_ids` (logical id to
/// compiled id). Every other item is written by calling `fallback(item)`,
/// which must return that item's JSON. `json.dumps` of a list is
/// `"[" + ",".join(dumps(item)) + "]"` with compact separators, so the
/// result is byte-identical.
///
/// **Raises**
///
/// ValueError: If an item is neither a dict nor a `_NativeRun`, `natives`
/// maps an item to anything but a `_NativeRow` or `_LeafJson`, a native
/// row's item does not have the exact shape assembly gives it, a leaf
/// occurrence's `preparedData` is not an exact dict, holds a placeholder
/// whose key has no JSON or lacks a placeholder for a value Rust wrote, a
/// leaf occurrence's item has a key that is not a str or loses a key while
/// `fallback` runs, a run comes without `definition_ids` or its definition
/// has no compiled id there or that id is not a str, or `fallback` does not
/// return a str.
#[pyfunction(name = "_encode_occurrences", signature = (occurrences, natives, fallback, definition_ids=None))]
pub fn encode_occurrences(
    occurrences: &Bound<'_, PyList>,
    natives: &Bound<'_, PyDict>,
    fallback: &Bound<'_, PyAny>,
    definition_ids: Option<&Bound<'_, PyDict>>,
) -> PyResult<String> {
    let py = occurrences.py();
    without_panics(|| {
        let mut out = String::with_capacity(occurrences.len() * 768);
        out.push('[');
        for (index, item) in occurrences.iter().enumerate() {
            if index > 0 {
                out.push(',');
            }
            // A run writes all its rows here, separated by commas, which is
            // what the list would hold had each row been its own item.
            if let Ok(run) = item.cast_exact::<NativeRun>() {
                write_run(&mut out, run.get(), definition_ids)?;
                continue;
            }
            let dict = item
                .cast_exact::<PyDict>()
                .map_err(|_| occurrence_error("is not a dict"))?;
            let native = match dict.get_item(intern!(py, "id"))? {
                Some(id) => natives.get_item(id)?,
                None => None,
            };
            match native {
                Some(native) => {
                    if let Ok(row) = native.cast_exact::<NativeRow>() {
                        write_native_occurrence(&mut out, dict, row.get())?;
                    } else if let Ok(leaf) = native.cast_exact::<LeafJson>() {
                        // An occurrence whose leaf data Rust wrote
                        // in assembly (level B2, `leaf_json.rs`).
                        write_leaf_occurrence(&mut out, dict, leaf.get(), fallback)?;
                    } else {
                        return Err(occurrence_error(
                            "maps to an object that is not a _NativeRow or _LeafJson",
                        ));
                    }
                }
                None => {
                    let encoded = fallback.call1((dict,))?;
                    out.push_str(item_str(&encoded, "fallback result")?);
                }
            }
        }
        out.push(']');
        Ok(out)
    })
}

// ---------------------------------------------------------------------------
// The ids of each row of a repeated component call (a call run).
// ---------------------------------------------------------------------------

/// The two ids that name each row of one call run, with their constant
/// leading text hashed once.
///
/// Python passes the JSON text it would hash before each row's own item, as
/// `_DigestPrefix` builds it: `_DIGEST_JSON.encode(prefix)[:-1]`. For each
/// row, `member_ids(key)` returns the placement key and the child occurrence
/// id: `citryPlacement` and `citryOccurrence` followed by the first 24 hex
/// digits of `_DigestPrefix(...).digest(("explicit", key))` and
/// `_DigestPrefix(occurrence_id).digest(placement_key)`.
#[pyclass(
    frozen,
    name = "_RunDigests",
    module = "citry_core._rust.native_render"
)]
pub struct RunDigests {
    ids: RunIds,
}

#[pymethods]
impl RunDigests {
    #[new]
    fn new(placement_prefix_json: &str, child_prefix_json: &str) -> PyResult<Self> {
        without_panics(|| {
            Ok(RunDigests {
                ids: RunIds::new(placement_prefix_json, child_prefix_json),
            })
        })
    }

    /// Return `(placement_key, child_id)` for a row with explicit key `key`,
    /// or None when the key has no UTF-8 form (a lone surrogate), which
    /// Python then hashes itself.
    fn member_ids(&self, key: &Bound<'_, PyString>) -> PyResult<Option<(String, String)>> {
        without_panics(|| {
            let Ok(key) = key.to_str() else {
                return Ok(None);
            };
            Ok(Some(self.ids.member_ids(key)))
        })
    }
}

/// Register level A's classes and functions on the `native_render` submodule.
pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<RowPlan>()?;
    module.add_class::<NativeRow>()?;
    module.add_class::<RunDigests>()?;
    module.add_function(wrap_pyfunction!(encode_occurrences, module)?)?;
    Ok(())
}
