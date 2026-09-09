//! Calculate retirement relationships and update native tables or return Python edits.

use std::collections::{HashMap, HashSet};

use pyo3::exceptions::{PyException, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyInt, PyList, PySet, PyString, PyTuple};

use crate::Journal;
use crate::storage::{RecordTable, StoredRow};
use citry_ownership::{Call, Edge, Fill, Graph, Instance, Region, RenderId};

pyo3::create_exception!(
    citry_ownership_journal_probe,
    UnsupportedRetirement,
    PyException
);

#[derive(Default)]
struct Names {
    indexes: HashMap<String, RenderId>,
    values: Vec<Py<PyAny>>,
}
impl Names {
    fn intern(&mut self, value: &Bound<'_, PyAny>) -> PyResult<RenderId> {
        let string = value.cast_exact::<PyString>().map_err(|_| {
            UnsupportedRetirement::new_err("relationship IDs require exact str values")
        })?;
        let text = string.to_str().map_err(|_| {
            UnsupportedRetirement::new_err("relationship ID is not representable as UTF-8")
        })?;
        if let Some(&id) = self.indexes.get(text) {
            return Ok(id);
        }
        let id = self.values.len();
        self.indexes.insert(text.to_owned(), id);
        self.values.push(value.clone().unbind());
        Ok(id)
    }
    fn optional(&mut self, value: &Bound<'_, PyAny>) -> PyResult<Option<RenderId>> {
        if value.is_none() {
            Ok(None)
        } else {
            self.intern(value).map(Some)
        }
    }
    fn set(&mut self, values: &Bound<'_, PySet>) -> PyResult<HashSet<RenderId>> {
        values.iter().map(|value| self.intern(&value)).collect()
    }
    fn python_set<'py>(
        &self,
        py: Python<'py>,
        values: &HashSet<RenderId>,
    ) -> PyResult<Bound<'py, PySet>> {
        PySet::new(py, values.iter().map(|&id| self.values[id].bind(py)))
    }
}

enum Rows<'py> {
    Python(Bound<'py, PyList>, usize),
    Native(PyRefMut<'py, RecordTable>),
}

enum RowView<'a, 'py> {
    Python(Bound<'py, PyTuple>),
    Native(&'a StoredRow, Python<'py>),
}

impl<'py> RowView<'_, 'py> {
    fn get_item(&self, index: usize) -> PyResult<Bound<'py, PyAny>> {
        match self {
            Self::Python(row) => row.get_item(index),
            Self::Native(row, py) => Ok(row.fields[index].bind(*py).clone()),
        }
    }
}

impl<'py> Rows<'py> {
    fn new(value: Bound<'py, PyAny>, width: usize) -> PyResult<Self> {
        if value.is_instance_of::<RecordTable>() {
            let table: PyRefMut<'py, RecordTable> = value.extract()?;
            if table.width != width {
                return Err(PyValueError::new_err("unexpected ownership table width"));
            }
            Ok(Self::Native(table))
        } else {
            Ok(Self::Python(value.cast_into::<PyList>()?, width))
        }
    }

    fn len(&self) -> usize {
        match self {
            Self::Python(values, _) => values.len(),
            Self::Native(table) => table.rows.len(),
        }
    }

    fn get_item(&self, py: Python<'py>, index: usize) -> PyResult<RowView<'_, 'py>> {
        match self {
            Self::Python(values, width) => {
                let row = values.get_item(index)?.cast_into::<PyTuple>()?;
                if row.len() != *width {
                    return Err(PyValueError::new_err("unexpected ownership record length"));
                }
                Ok(RowView::Python(row))
            }
            Self::Native(table) => Ok(RowView::Native(&table.rows[index], py)),
        }
    }
}

fn integer(value: &Bound<'_, PyAny>) -> PyResult<u64> {
    value
        .cast_exact::<PyInt>()
        .map_err(|_| {
            UnsupportedRetirement::new_err("relationship IDs and orders require exact int values")
        })?
        .extract()
        .map_err(|_| UnsupportedRetirement::new_err("relationship IDs and orders must fit u64"))
}

fn optional_integer(value: &Bound<'_, PyAny>) -> PyResult<Option<u64>> {
    if value.is_none() {
        Ok(None)
    } else {
        integer(value).map(Some)
    }
}

pub fn retire(
    journal: &mut Journal,
    py: Python<'_>,
    tables: &Bound<'_, PyTuple>,
    inputs: &Bound<'_, PyTuple>,
    order: &Bound<'_, PyAny>,
    states: &Bound<'_, PyTuple>,
) -> PyResult<Py<PyAny>> {
    if tables.len() != 4 || inputs.len() != 5 || !matches!(states.len(), 4 | 5) {
        return Err(PyValueError::new_err(
            "retirement needs four tables, five inputs and four or five states",
        ));
    }
    let mut instances = Rows::new(tables.get_item(0)?, 8)?;
    let mut edges = Rows::new(tables.get_item(1)?, 5)?;
    let mut fills = Rows::new(tables.get_item(2)?, 13)?;
    let mut regions = Rows::new(tables.get_item(3)?, 11)?;
    let stored = matches!(instances, Rows::Native(_));
    if [
        matches!(edges, Rows::Native(_)),
        matches!(fills, Rows::Native(_)),
        matches!(regions, Rows::Native(_)),
    ]
    .into_iter()
    .any(|native| native != stored)
        || stored != (states.len() == 5)
    {
        return Err(PyValueError::new_err(
            "retirement tables must use one storage mode",
        ));
    }
    integer(order)?;
    let captured = states.get_item(0)?;
    let retired = states.get_item(1)?;
    let queue_retired = states.get_item(2)?;
    let queue_failed = states.get_item(3)?;
    let mut names = Names::default();
    let owner = names.intern(&inputs.get_item(0)?)?;
    let through = integer(&inputs.get_item(1)?)?;
    let descendants = inputs.get_item(2)?.cast_into::<PySet>()?;
    // Validate all supplied IDs before any native mutation or fallback.
    names.set(&descendants)?;
    let direct = names.set(&inputs.get_item(3)?.cast_into::<PySet>()?)?;
    let explicit = inputs
        .get_item(4)?
        .cast::<PySet>()?
        .iter()
        .map(|value| integer(&value))
        .collect::<PyResult<_>>()?;
    let mut graph = Graph::default();
    for call in &journal.rows {
        let fields = &call.invocation;
        graph.calls.push(Call {
            id: integer(fields[0].bind(py))?,
            order: integer(fields[1].bind(py))?,
            source: names.intern(fields[2].bind(py))?,
            target: names.optional(fields[9].bind(py))?,
            region: optional_integer(fields[10].bind(py))?,
            selectors: fields[12]
                .bind(py)
                .cast::<PyTuple>()?
                .iter()
                .map(|value| names.intern(&value))
                .collect::<PyResult<_>>()?,
        });
    }
    for index in 0..instances.len() {
        let fields = instances.get_item(py, index)?;
        graph.instances.push(Instance {
            order: integer(&fields.get_item(0)?)?,
            id: names.intern(&fields.get_item(1)?)?,
            parent: names.optional(&fields.get_item(5)?)?,
            active: fields.get_item(7)?.eq(journal.active.bind(py))?,
        });
    }
    for index in 0..edges.len() {
        let fields = edges.get_item(py, index)?;
        graph.edges.push(Edge {
            order: integer(&fields.get_item(0)?)?,
            invocation: integer(&fields.get_item(1)?)?,
            parent: names.intern(&fields.get_item(2)?)?,
            child: names.intern(&fields.get_item(3)?)?,
        });
    }
    for index in 0..fills.len() {
        let fields = fills.get_item(py, index)?;
        // Receiver-map insertion happens after native updates. A custom slot
        // hash could observe a different intermediate state, so use Python.
        fields
            .get_item(3)?
            .cast_exact::<PyString>()
            .map_err(|_| UnsupportedRetirement::new_err("slot names require exact str values"))?;
        graph.fills.push(Fill {
            id: integer(&fields.get_item(0)?)?,
            order: integer(&fields.get_item(1)?)?,
            owner: names.optional(&fields.get_item(5)?)?,
            receiver: names.optional(&fields.get_item(9)?)?,
        });
    }
    for index in 0..regions.len() {
        let fields = regions.get_item(py, index)?;
        graph.regions.push(Region {
            id: integer(&fields.get_item(0)?)?,
            order: integer(&fields.get_item(1)?)?,
            fill: integer(&fields.get_item(2)?)?,
            receiver: names.optional(&fields.get_item(3)?)?,
            containing: optional_integer(&fields.get_item(7)?)?,
            captured: fields.get_item(10)?.eq(&captured)?,
        });
    }
    graph.index().map_err(PyValueError::new_err)?;
    let selection = graph.selection(owner, through, &direct, explicit);
    // Python set differences determine the initial LIFO worklist, including
    // collision behavior for sparse IDs and process-randomized string hashes.
    let discarded = descendants
        .call_method0("copy")?
        .call_method1("difference", (names.python_set(py, &selection.preserved)?,))?
        .call_method1("difference", (names.python_set(py, &selection.ancestors)?,))?;
    let initial = discarded
        .cast::<PySet>()?
        .iter()
        .map(|value| names.intern(&value))
        .collect::<PyResult<_>>()?;
    let plan = graph.plan(owner, through, &direct, &selection, initial);
    let invocation_set = PySet::empty(py)?;
    let mut invocation_indexes = HashMap::new();
    for index in &plan.calls {
        let id = graph.calls[*index].id;
        invocation_set.add(id)?;
        invocation_indexes.insert(id, *index);
    }
    let indexes = invocation_set
        .iter()
        .map(|value| {
            let id: u64 = value.extract()?;
            Ok(invocation_indexes[&id])
        })
        .collect::<PyResult<Vec<_>>>()?;
    let promotions = plan
        .fill_promotions
        .iter()
        .map(|&(index, receiver, instance)| {
            let class = match instance {
                Some(i) => instances.get_item(py, i)?.get_item(2)?.unbind(),
                None => py.None(),
            };
            Ok((index, names.values[receiver].clone_ref(py), class))
        })
        .collect::<PyResult<Vec<_>>>()?;
    let region_promotions: Vec<_> = plan
        .region_promotions
        .iter()
        .map(|&(index, receiver)| (index, names.values[receiver].clone_ref(py)))
        .collect();
    // Conversion and planning finish before paired invocation/queue updates.
    let order = journal.retire_many(
        py,
        indexes,
        order,
        retired.clone().unbind(),
        queue_retired.unbind(),
        queue_failed.unbind(),
    )?;
    if let (
        Rows::Native(instances),
        Rows::Native(edges),
        Rows::Native(fills),
        Rows::Native(regions),
    ) = (&mut instances, &mut edges, &mut fills, &mut regions)
    {
        for &index in &plan.instances {
            instances.change(index, 7, retired.clone().unbind());
        }
        for &index in &plan.edges {
            edges.change(index, 4, retired.clone().unbind());
        }
        let mut receiver_updates = Vec::new();
        for (index, receiver, class_id) in promotions {
            receiver_updates.push((
                receiver.clone_ref(py),
                fills.field(py, index, 3).unbind(),
                fills.field(py, index, 0).unbind(),
            ));
            fills.change(index, 9, receiver);
            fills.change(index, 10, class_id);
            fills.change(index, 12, journal.active.clone_ref(py));
        }
        for (index, receiver) in &region_promotions {
            // An outer region changes its transition source along with its receiver.
            if regions.field(py, *index, 7).is_none() {
                regions.change(*index, 8, receiver.clone_ref(py));
            }
            regions.change(*index, 3, receiver.clone_ref(py));
        }
        for &index in &plan.fills {
            fills.change(index, 12, retired.clone().unbind());
        }
        let region_retired = states.get_item(4)?;
        for &index in &plan.regions {
            regions.change(index, 10, region_retired.clone().unbind());
        }
        return Ok((order, receiver_updates, !region_promotions.is_empty())
            .into_pyobject(py)?
            .into_any()
            .unbind());
    }
    Ok((
        order,
        plan.instances,
        plan.edges,
        plan.fills,
        plan.regions,
        promotions,
        region_promotions,
    )
        .into_pyobject(py)?
        .into_any()
        .unbind())
}
