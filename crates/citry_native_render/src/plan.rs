//! The row plan: the template's operations and the paths it reads.

use std::collections::BTreeSet;
use std::fmt;

/// The ways a template uses one read value, as Python's read set records
/// them. Each kind adds a type check, and a value must pass all of them.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Kinds {
    /// Shown as text or as an attribute value: None or an allowed scalar.
    pub scalar: bool,
    /// Looped over by `c-for`: an exact list.
    pub list: bool,
    /// Tested for truth by `c-if` or a conditional expression.
    pub truth: bool,
    /// Spread by the root `c-bind`: an exact dict of plain scalars, or None.
    pub safe_attrs_or_none: bool,
    /// Like `safe_attrs_or_none`, but None is not allowed.
    pub safe_attrs: bool,
}

impl Kinds {
    /// Parse Python's kind names; an unknown name (such as the `value`
    /// kind child calls use) means the template is outside this plan.
    pub fn from_names<'a>(names: impl IntoIterator<Item = &'a str>) -> Result<Self, PlanError> {
        let mut kinds = Kinds::default();
        for name in names {
            match name {
                "scalar" => kinds.scalar = true,
                "list" => kinds.list = true,
                "truth" => kinds.truth = true,
                "safe_attrs_or_none" => kinds.safe_attrs_or_none = true,
                "safe_attrs" => kinds.safe_attrs = true,
                other => return Err(PlanError(format!("unknown read kind {other:?}"))),
            }
        }
        Ok(kinds)
    }

    fn spreads(&self) -> bool {
        self.safe_attrs || self.safe_attrs_or_none
    }
}

/// A literal the expression subset allows.
#[derive(Debug, Clone, PartialEq)]
pub enum Const {
    None,
    Bool(bool),
    Str(String),
}

/// One expression, as Python's `_SimpleJsonExpr` describes it.
#[derive(Debug, Clone, PartialEq)]
pub enum ExprSpec {
    Const(Const),
    /// `root['key1']['key2']...`; the root is a template variable or a loop
    /// target.
    Path {
        root: String,
        keys: Vec<String>,
    },
    /// `body if test else otherwise`, where `test` is a path.
    If {
        test: Box<ExprSpec>,
        body: Box<ExprSpec>,
        otherwise: Box<ExprSpec>,
    },
}

/// One operation of the generated evaluator, as Python describes it.
#[derive(Debug, Clone, PartialEq)]
pub enum OpSpec {
    /// `{{ expr }}`: writes the value's text under `key`.
    Text { key: String, expr: ExprSpec },
    /// An element's `c-*` attributes: writes the present ones under `key`.
    Open {
        key: String,
        attributes: Vec<(String, ExprSpec)>,
    },
    /// A `c-bind` outside every `c-if` and `c-for` (Python's root `c-bind`):
    /// writes the merged attributes under `key`.
    Spread { key: String, expr: ExprSpec },
    /// `c-if` / `c-elif` / `c-else`: writes the chosen branch's index (-1 for
    /// none) under `key`, then runs that branch into the same record.
    If {
        key: String,
        branches: Vec<(Option<ExprSpec>, Vec<OpSpec>)>,
    },
    /// `c-for target in iterable`: writes one record per item under `key`;
    /// `empty` runs into the enclosing record when there is no item.
    For {
        key: String,
        target: String,
        iterable: ExprSpec,
        body: Vec<OpSpec>,
        empty: Vec<OpSpec>,
    },
}

/// One node of Python's read set: how a value is used and what is read
/// from inside it.
#[derive(Debug, Clone, PartialEq)]
pub struct ReadNodeSpec {
    pub kinds: Kinds,
    pub children: Vec<(String, ReadNodeSpec)>,
    pub items: Option<Box<ReadNodeSpec>>,
}

/// Everything Python passes to build a plan.
#[derive(Debug, Clone, PartialEq)]
pub struct PlanSpec {
    pub ops: Vec<OpSpec>,
    pub roots: Vec<(String, ReadNodeSpec)>,
    /// Every loop target; a template variable with one of these names makes
    /// the row ineligible, as Python's check does.
    pub loop_targets: Vec<String>,
    /// The largest int JavaScript holds exactly (Python's `_JS_SAFE_INTEGER`);
    /// an attribute int beyond it, either way, is sent as text.
    pub js_safe_integer: i64,
}

/// A description Rust cannot evaluate exactly, so the template keeps the
/// Python evaluator.
#[derive(Debug, Clone, PartialEq)]
pub struct PlanError(pub String);

impl fmt::Display for PlanError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl std::error::Error for PlanError {}

/// A read-set node after planning, with its name kept for the reader.
#[derive(Debug, Clone, PartialEq)]
pub struct ReadNode {
    pub name: String,
    pub kinds: Kinds,
    pub children: Vec<ReadNode>,
    pub items: Option<Box<ReadNode>>,
}

/// Where a path starts: a template variable (by position in the read
/// set's roots) or the item of an enclosing loop (by loop depth).
#[derive(Debug, Clone, Copy, PartialEq)]
pub(crate) enum Base {
    Root(usize),
    Local(usize),
}

#[derive(Debug, Clone, PartialEq)]
pub(crate) struct PathRef {
    pub(crate) base: Base,
    /// Child positions to follow from the base value.
    pub(crate) steps: Vec<usize>,
}

#[derive(Debug, Clone, PartialEq)]
pub(crate) enum Expr {
    Const(Const),
    Path(PathRef),
    If(Box<Expr>, Box<Expr>, Box<Expr>),
}

#[derive(Debug, Clone, PartialEq)]
pub(crate) enum Op {
    Text {
        rank: u32,
        expr: Expr,
    },
    Open {
        rank: u32,
        /// Sorted by name, so present attributes come out in JSON order.
        attributes: Vec<(String, Expr)>,
    },
    Spread {
        rank: u32,
        /// Position among the plan's spreads, matching the layouts the
        /// caller passes to [`Plan::write_row`].
        index: usize,
    },
    If {
        rank: u32,
        branches: Vec<(Option<Expr>, Vec<Op>)>,
    },
    For {
        rank: u32,
        iterable: PathRef,
        body: Vec<Op>,
        empty: Vec<Op>,
    },
}

/// A compiled row plan.
#[derive(Debug, Clone, PartialEq)]
pub struct Plan {
    pub(crate) roots: Vec<ReadNode>,
    pub(crate) loop_targets: Vec<String>,
    pub(crate) ops: Vec<Op>,
    /// Every key a record can hold, sorted the way `sort_keys=True` sorts
    /// them; an op stores its key's position here, so a record sorts by
    /// comparing integers.
    pub(crate) keys: Vec<String>,
    /// The position of the root record's `"calls"` key in `keys`.
    pub(crate) calls_rank: u32,
    /// The path each root `c-bind` spreads, in spread order.
    pub(crate) spreads: Vec<PathRef>,
    /// See [`PlanSpec::js_safe_integer`].
    pub(crate) js_safe_integer: i64,
}

/// The value-independent layout of one root `c-bind` key set.
///
/// Python's `_root_spread_plan` works it out once per key set; Rust keeps
/// it sorted by name for the JSON writer.
#[derive(Debug, Clone, PartialEq)]
pub struct SpreadLayout {
    pub(crate) entries: Vec<(String, SpreadSource)>,
}

#[derive(Debug, Clone, PartialEq)]
pub(crate) enum SpreadSource {
    /// A fixed attribute's value, already written as JSON.
    Static(String),
    /// The value at this position of the row's spread dict.
    Row(usize),
}

/// A layout Rust cannot use: a row name that is not in the key set, or two
/// entries with one name.
#[derive(Debug, Clone, PartialEq)]
pub struct SpreadLayoutError;

impl SpreadLayout {
    /// Build a layout from Python's entries `(name, is_static, json)` for the
    /// row key set `keys`. A static entry with no JSON writes nothing.
    pub fn new(
        keys: &[String],
        entries: impl IntoIterator<Item = (String, bool, Option<String>)>,
    ) -> Result<Self, SpreadLayoutError> {
        let mut layout = Vec::new();
        for (name, is_static, json) in entries {
            if is_static {
                if let Some(json) = json {
                    layout.push((name, SpreadSource::Static(json)));
                }
                continue;
            }
            let position = keys
                .iter()
                .position(|key| *key == name)
                .ok_or(SpreadLayoutError)?;
            layout.push((name, SpreadSource::Row(position)));
        }
        // A stable sort keeps the merge's order between equal names, but
        // Python's dict would then hold only one of them; the layouts Python
        // builds never repeat a name, so a repeat is rejected outright.
        layout.sort_by(|left, right| left.0.cmp(&right.0));
        if layout.windows(2).any(|pair| pair[0].0 == pair[1].0) {
            return Err(SpreadLayoutError);
        }
        Ok(SpreadLayout { entries: layout })
    }
}

/// Planning state: the read set paths resolve against, every key seen, and
/// the spreads found so far. `'a` covers both the spec and the read set.
struct Builder<'a> {
    roots: &'a [ReadNode],
    keys: BTreeSet<String>,
    spreads: Vec<PathRef>,
}

/// One loop scope: the target's name and the read node of its items.
struct Local<'a> {
    name: &'a str,
    node: &'a ReadNode,
}

fn plan_read_node(name: &str, spec: &ReadNodeSpec) -> ReadNode {
    ReadNode {
        name: name.to_owned(),
        kinds: spec.kinds,
        children: spec
            .children
            .iter()
            .map(|(child_name, child)| plan_read_node(child_name, child))
            .collect(),
        items: spec
            .items
            .as_ref()
            .map(|items| Box::new(plan_read_node("", items))),
    }
}

impl<'a> Builder<'a> {
    /// Resolve a path to its read node, the way Python's read set and code
    /// generator both do: an enclosing loop target first, then a variable.
    fn path(
        &self,
        expr: &ExprSpec,
        locals: &[Local<'a>],
    ) -> Result<(PathRef, &'a ReadNode), PlanError> {
        let ExprSpec::Path { root, keys } = expr else {
            return Err(PlanError("expected a path".to_owned()));
        };
        let (base, mut node) = if let Some(depth) =
            locals.iter().rposition(|local| local.name == root)
        {
            (Base::Local(depth), locals[depth].node)
        } else {
            let position = self
                .roots
                .iter()
                .position(|candidate| candidate.name == *root)
                .ok_or_else(|| PlanError(format!("path root {root:?} is not in the read set")))?;
            (Base::Root(position), &self.roots[position])
        };
        let mut steps = Vec::with_capacity(keys.len());
        for key in keys {
            let position = node
                .children
                .iter()
                .position(|child| child.name == *key)
                .ok_or_else(|| PlanError(format!("path key {key:?} is not in the read set")))?;
            steps.push(position);
            node = &node.children[position];
        }
        Ok((PathRef { base, steps }, node))
    }

    /// Lower an expression whose value is shown (`scalar`) or tested
    /// (`truth`), and confirm the read set checks that use, so evaluation
    /// can never meet a value of a type the check did not admit.
    fn expr(&self, expr: &ExprSpec, locals: &[Local<'a>], truth: bool) -> Result<Expr, PlanError> {
        match expr {
            ExprSpec::Const(value) => Ok(Expr::Const(value.clone())),
            ExprSpec::Path { .. } => {
                let (path, node) = self.path(expr, locals)?;
                let checked = if truth {
                    node.kinds.truth
                } else {
                    node.kinds.scalar
                };
                if !checked {
                    return Err(PlanError(
                        "a path is used in a way its read node does not check".to_owned(),
                    ));
                }
                Ok(Expr::Path(path))
            }
            ExprSpec::If {
                test,
                body,
                otherwise,
            } => {
                if !matches!(**test, ExprSpec::Path { .. }) {
                    return Err(PlanError("a conditional test must be a path".to_owned()));
                }
                Ok(Expr::If(
                    Box::new(self.expr(test, locals, true)?),
                    Box::new(self.expr(body, locals, truth)?),
                    Box::new(self.expr(otherwise, locals, truth)?),
                ))
            }
        }
    }

    fn key(&mut self, key: &str) -> String {
        self.keys.insert(key.to_owned());
        key.to_owned()
    }

    /// Turn one scope into ops. Ranks are filled in afterwards, once every
    /// key is known, so this stores each key's text in a placeholder list.
    fn ops(
        &mut self,
        ops: &'a [OpSpec],
        locals: &mut Vec<Local<'a>>,
        top_level: bool,
        out_keys: &mut Vec<String>,
    ) -> Result<Vec<Op>, PlanError> {
        let mut lowered = Vec::with_capacity(ops.len());
        for op in ops {
            match op {
                OpSpec::Text { key, expr } => {
                    out_keys.push(self.key(key));
                    lowered.push(Op::Text {
                        rank: 0,
                        expr: self.expr(expr, locals, false)?,
                    });
                }
                OpSpec::Open { key, attributes } => {
                    out_keys.push(self.key(key));
                    let mut planned = Vec::with_capacity(attributes.len());
                    for (name, expr) in attributes {
                        planned.push((name.clone(), self.expr(expr, locals, false)?));
                    }
                    planned.sort_by(|left, right| left.0.cmp(&right.0));
                    // Python writes these into one dict; a repeated name would
                    // keep only the last value, which this writer does not model.
                    if planned.windows(2).any(|pair| pair[0].0 == pair[1].0) {
                        return Err(PlanError("an element repeats an attribute name".to_owned()));
                    }
                    lowered.push(Op::Open {
                        rank: 0,
                        attributes: planned,
                    });
                }
                OpSpec::Spread { key, expr } => {
                    // Python admits `c-bind` only outside every `c-if` and
                    // `c-for`, and the caller looks up each spread's layout
                    // before evaluating, so a spread inside a branch or loop
                    // is refused.
                    if !top_level {
                        return Err(PlanError(
                            "a c-bind spread inside a branch or loop".to_owned(),
                        ));
                    }
                    let (path, node) = self.path(expr, locals)?;
                    if !node.kinds.spreads() {
                        return Err(PlanError(
                            "a spread path is not checked as attributes".to_owned(),
                        ));
                    }
                    out_keys.push(self.key(key));
                    lowered.push(Op::Spread {
                        rank: 0,
                        index: self.spreads.len(),
                    });
                    self.spreads.push(path);
                }
                OpSpec::If { key, branches } => {
                    out_keys.push(self.key(key));
                    let mut planned = Vec::with_capacity(branches.len());
                    for (condition, body) in branches {
                        let condition = match condition {
                            None => None,
                            Some(condition @ ExprSpec::Path { .. }) => {
                                Some(self.expr(condition, locals, true)?)
                            }
                            Some(_) => {
                                return Err(PlanError(
                                    "a c-if condition must be a path".to_owned(),
                                ));
                            }
                        };
                        planned.push((condition, self.ops(body, locals, false, out_keys)?));
                    }
                    lowered.push(Op::If {
                        rank: 0,
                        branches: planned,
                    });
                }
                OpSpec::For {
                    key,
                    target,
                    iterable,
                    body,
                    empty,
                } => {
                    out_keys.push(self.key(key));
                    let (path, node) = self.path(iterable, locals)?;
                    let items = match (&node.items, node.kinds.list) {
                        (Some(items), true) => &**items,
                        _ => {
                            return Err(PlanError(
                                "a c-for iterable is not checked as a list".to_owned(),
                            ));
                        }
                    };
                    locals.push(Local {
                        name: target.as_str(),
                        node: items,
                    });
                    let body = self.ops(body, locals, false, out_keys);
                    locals.pop();
                    let empty = self.ops(empty, locals, false, out_keys)?;
                    lowered.push(Op::For {
                        rank: 0,
                        iterable: path,
                        body: body?,
                        empty,
                    });
                }
            }
        }
        Ok(lowered)
    }
}

/// Assign each op the rank of its key, in the order `ops` was lowered.
fn assign_ranks(ops: &mut [Op], ranks: &mut impl Iterator<Item = u32>) {
    for op in ops {
        match op {
            Op::Text { rank, .. } | Op::Open { rank, .. } | Op::Spread { rank, .. } => {
                *rank = ranks.next().expect("every op recorded its key");
            }
            Op::If { rank, branches } => {
                *rank = ranks.next().expect("every op recorded its key");
                for (_condition, body) in branches {
                    assign_ranks(body, ranks);
                }
            }
            Op::For {
                rank, body, empty, ..
            } => {
                *rank = ranks.next().expect("every op recorded its key");
                assign_ranks(body, ranks);
                assign_ranks(empty, ranks);
            }
        }
    }
}

impl Plan {
    /// Build a plan, or explain why Rust cannot evaluate this template.
    pub fn new(spec: &PlanSpec) -> Result<Self, PlanError> {
        let roots: Vec<ReadNode> = spec
            .roots
            .iter()
            .map(|(name, node)| plan_read_node(name, node))
            .collect();
        let mut builder = Builder {
            roots: &roots,
            keys: BTreeSet::new(),
            spreads: Vec::new(),
        };
        let mut locals = Vec::new();
        let mut op_keys = Vec::new();
        let mut ops = builder.ops(&spec.ops, &mut locals, true, &mut op_keys)?;
        // The root record also holds "calls", which assembly adds; a data
        // key with that name makes assembly raise, so Python keeps the row.
        if !builder.keys.insert("calls".to_owned()) {
            return Err(PlanError("a data key is named \"calls\"".to_owned()));
        }
        let keys: Vec<String> = builder.keys.iter().cloned().collect();
        let rank_of = |key: &str| -> u32 {
            u32::try_from(
                keys.binary_search_by(|probe| probe.as_str().cmp(key))
                    .expect("key was recorded"),
            )
            .expect("fewer than 2**32 keys")
        };
        let mut ranks = op_keys.iter().map(|key| rank_of(key));
        assign_ranks(&mut ops, &mut ranks);
        let calls_rank = rank_of("calls");
        let spreads = builder.spreads;
        Ok(Plan {
            roots,
            loop_targets: spec.loop_targets.clone(),
            ops,
            keys,
            calls_rank,
            spreads,
            js_safe_integer: spec.js_safe_integer,
        })
    }

    /// The read set's roots, which the caller reads in this order.
    pub fn roots(&self) -> &[ReadNode] {
        &self.roots
    }

    /// The loop targets a row's variables must not use as names.
    pub fn loop_targets(&self) -> &[String] {
        &self.loop_targets
    }

    /// How many root `c-bind` spreads the template has.
    pub fn spread_count(&self) -> usize {
        self.spreads.len()
    }

    /// The value spread `index` reads from this row: a [`crate::Value::Dict`]
    /// with attrs, or [`crate::Value::None`].
    pub fn spread_value<'v>(
        &self,
        values: &'v [crate::Value],
        index: usize,
    ) -> Option<&'v crate::Value> {
        crate::eval::resolve_root(values, self.spreads.get(index)?)
    }
}
