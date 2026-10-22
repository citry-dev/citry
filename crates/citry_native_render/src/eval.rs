//! Evaluate a plan over one row's copied values and write the prepared data.
//!
//! The value rules are those of Python's generated evaluator for rows
//! rendered without a component instance (`_SimpleJsonCodegen` in
//! `packages/py/citry/citry/_vue/leaf_program.py`):
//! - a text is `str(value)`, and None shows as an empty text;
//! - None and False leave an attribute out;
//! - in an attribute, a float, or an int beyond plus or minus 2**53 - 1 (the
//!   largest int JavaScript holds exactly), is sent as its Python text;
//! - `c-if` stores the chosen branch's index, -1 when none matches;
//! - `c-for` stores one record per item.

use std::fmt::Write as _;

use crate::json::write_json_str;
use crate::plan::{Base, Const, Expr, Op, PathRef, Plan, SpreadLayout, SpreadSource};
use crate::value::Value;

/// The largest int JavaScript reads exactly; Citry sends larger ints as text.
const JS_SAFE_INTEGER: i64 = (1 << 53) - 1;

/// A value evaluation met that the plan's checks should have excluded. It
/// means the caller built a value tree that does not match the read set;
/// the caller declines the row so Python evaluates it.
#[derive(Debug, Clone, PartialEq)]
pub struct EvalError(pub &'static str);

/// An evaluated expression: a copied value or a template literal.
#[derive(Clone, Copy)]
enum Evaluated<'v, 'p> {
    Value(&'v Value),
    Const(&'p Const),
}

/// One evaluated entry of a record, keyed by its key's rank.
enum Entry<'v, 'p> {
    Text(Evaluated<'v, 'p>),
    Attrs(Vec<(&'p str, Evaluated<'v, 'p>)>),
    Spread(&'p SpreadLayout, &'v [Value]),
    Index(i64),
    Records(Vec<Record<'v, 'p>>),
}

struct Record<'v, 'p> {
    entries: Vec<(u32, Entry<'v, 'p>)>,
}

/// Follow a path from a root value.
pub(crate) fn resolve_root<'v>(values: &'v [Value], path: &PathRef) -> Option<&'v Value> {
    let Base::Root(position) = path.base else {
        return None;
    };
    follow(values.get(position)?, &path.steps)
}

fn follow<'v>(mut value: &'v Value, steps: &[usize]) -> Option<&'v Value> {
    for step in steps {
        match value {
            Value::Dict { children, .. } => value = children.get(*step)?,
            _ => return None,
        }
    }
    Some(value)
}

struct Evaluator<'v, 'p> {
    roots: &'v [Value],
    spreads: &'p [&'p SpreadLayout],
    plan: &'p Plan,
}

impl<'v, 'p> Evaluator<'v, 'p>
where
    'v: 'p,
{
    fn path(&self, path: &PathRef, locals: &[&'v Value]) -> Result<&'v Value, EvalError> {
        let base = match path.base {
            Base::Root(position) => self.roots.get(position),
            Base::Local(depth) => locals.get(depth).copied(),
        }
        .ok_or(EvalError("a path base is missing"))?;
        follow(base, &path.steps).ok_or(EvalError("a path step is missing"))
    }

    fn truth(&self, expr: &'p Expr, locals: &[&'v Value]) -> Result<bool, EvalError> {
        match self.expr(expr, locals)? {
            Evaluated::Value(value) => value
                .truthy()
                .ok_or(EvalError("an unread value was tested")),
            Evaluated::Const(Const::None) => Ok(false),
            Evaluated::Const(Const::Bool(flag)) => Ok(*flag),
            Evaluated::Const(Const::Str(text)) => Ok(!text.is_empty()),
        }
    }

    fn expr(&self, expr: &'p Expr, locals: &[&'v Value]) -> Result<Evaluated<'v, 'p>, EvalError> {
        Ok(match expr {
            Expr::Const(value) => Evaluated::Const(value),
            Expr::Path(path) => Evaluated::Value(self.path(path, locals)?),
            Expr::If(test, body, otherwise) => {
                if self.truth(test, locals)? {
                    self.expr(body, locals)?
                } else {
                    self.expr(otherwise, locals)?
                }
            }
        })
    }

    fn ops(
        &self,
        ops: &'p [Op],
        locals: &mut Vec<&'v Value>,
        record: &mut Record<'v, 'p>,
    ) -> Result<(), EvalError> {
        for op in ops {
            match op {
                Op::Text { rank, expr } => {
                    let value = self.expr(expr, locals)?;
                    record.entries.push((*rank, Entry::Text(value)));
                }
                Op::Open { rank, attributes } => {
                    let mut present = Vec::with_capacity(attributes.len());
                    for (name, expr) in attributes {
                        let value = self.expr(expr, locals)?;
                        if attribute_present(value) {
                            present.push((name.as_str(), value));
                        }
                    }
                    record.entries.push((*rank, Entry::Attrs(present)));
                }
                Op::Spread { rank, index } => {
                    let layout = self
                        .spreads
                        .get(*index)
                        .ok_or(EvalError("a spread layout is missing"))?;
                    let value = resolve_root(self.roots, &self.plan.spreads[*index])
                        .ok_or(EvalError("a spread value is missing"))?;
                    let row_values: &'v [Value] = match value {
                        // None spreads nothing, as Python's `{}` does.
                        Value::None => &[],
                        Value::Dict {
                            attrs: Some(attrs), ..
                        } => &attrs.values,
                        _ => return Err(EvalError("a spread value is not attributes")),
                    };
                    record
                        .entries
                        .push((*rank, Entry::Spread(layout, row_values)));
                }
                Op::If { rank, branches } => {
                    let mut selected: i64 = -1;
                    let mut chosen = None;
                    for (index, (condition, body)) in branches.iter().enumerate() {
                        let matches = match condition {
                            None => true,
                            Some(condition) => self.truth(condition, locals)?,
                        };
                        if matches {
                            selected =
                                i64::try_from(index).map_err(|_| EvalError("too many branches"))?;
                            chosen = Some(body);
                            break;
                        }
                    }
                    record.entries.push((*rank, Entry::Index(selected)));
                    if let Some(body) = chosen {
                        self.ops(body, locals, record)?;
                    }
                }
                Op::For {
                    rank,
                    iterable,
                    body,
                    empty,
                } => {
                    let Value::List { items, len } = self.path(iterable, locals)? else {
                        return Err(EvalError("a loop iterable is not a list"));
                    };
                    if items.len() != *len {
                        return Err(EvalError("a loop's items were not copied"));
                    }
                    let mut records = Vec::with_capacity(items.len());
                    for item in items {
                        let mut item_record = Record {
                            entries: Vec::with_capacity(body.len()),
                        };
                        locals.push(item);
                        let result = self.ops(body, locals, &mut item_record);
                        locals.pop();
                        result?;
                        records.push(item_record);
                    }
                    if items.is_empty() {
                        self.ops(empty, locals, record)?;
                    }
                    record.entries.push((*rank, Entry::Records(records)));
                }
            }
        }
        Ok(())
    }
}

/// Whether an attribute appears at all: None and False leave it out.
fn attribute_present(value: Evaluated<'_, '_>) -> bool {
    !matches!(
        value,
        Evaluated::Value(Value::None | Value::Bool(false))
            | Evaluated::Const(Const::None | Const::Bool(false))
    )
}

/// Write the text a `{{ }}` expression shows: `str(value)`, with None as "".
fn write_text(out: &mut String, value: Evaluated<'_, '_>) -> Result<(), EvalError> {
    match value {
        Evaluated::Value(Value::None) | Evaluated::Const(Const::None) => out.push_str("\"\""),
        Evaluated::Value(Value::Bool(true)) | Evaluated::Const(Const::Bool(true)) => {
            out.push_str("\"True\"");
        }
        Evaluated::Value(Value::Bool(false)) | Evaluated::Const(Const::Bool(false)) => {
            out.push_str("\"False\"");
        }
        Evaluated::Value(Value::Int(number)) => {
            write!(out, "\"{number}\"").expect("writing to a String cannot fail");
        }
        Evaluated::Value(Value::BigInt(text) | Value::Float { text, .. }) => {
            // Decimal digits, a sign, '.', 'e' and '+' need no escaping.
            out.push('"');
            out.push_str(text);
            out.push('"');
        }
        Evaluated::Value(Value::Str(text)) | Evaluated::Const(Const::Str(text)) => {
            write_json_str(out, text);
        }
        Evaluated::Value(Value::Unread | Value::Dict { .. } | Value::List { .. }) => {
            return Err(EvalError("a text value is not a scalar"));
        }
    }
    Ok(())
}

/// Write a present attribute's value as Citry sends it to Vue: True, a str
/// and a JavaScript-safe int unchanged, any other number as its text.
fn write_attribute_value(out: &mut String, value: Evaluated<'_, '_>) -> Result<(), EvalError> {
    match value {
        Evaluated::Value(Value::Bool(true)) | Evaluated::Const(Const::Bool(true)) => {
            out.push_str("true");
        }
        Evaluated::Value(Value::Int(number))
            if (-JS_SAFE_INTEGER..=JS_SAFE_INTEGER).contains(number) =>
        {
            write!(out, "{number}").expect("writing to a String cannot fail");
        }
        Evaluated::Value(Value::Int(number)) => {
            write!(out, "\"{number}\"").expect("writing to a String cannot fail");
        }
        Evaluated::Value(Value::BigInt(text) | Value::Float { text, .. }) => {
            out.push('"');
            out.push_str(text);
            out.push('"');
        }
        Evaluated::Value(Value::Str(text)) | Evaluated::Const(Const::Str(text)) => {
            write_json_str(out, text);
        }
        _ => return Err(EvalError("an attribute value is absent or not a scalar")),
    }
    Ok(())
}

fn write_entry(plan: &Plan, out: &mut String, entry: &Entry<'_, '_>) -> Result<(), EvalError> {
    match entry {
        Entry::Text(value) => write_text(out, *value)?,
        Entry::Attrs(attributes) => {
            out.push('{');
            for (index, (name, value)) in attributes.iter().enumerate() {
                if index > 0 {
                    out.push(',');
                }
                write_json_str(out, name);
                out.push(':');
                write_attribute_value(out, *value)?;
            }
            out.push('}');
        }
        Entry::Spread(layout, row_values) => {
            out.push('{');
            let mut first = true;
            for (name, source) in &layout.entries {
                let value = match source {
                    SpreadSource::Static(json) => {
                        if !first {
                            out.push(',');
                        }
                        first = false;
                        write_json_str(out, name);
                        out.push(':');
                        out.push_str(json);
                        continue;
                    }
                    SpreadSource::Row(position) => row_values
                        .get(*position)
                        .ok_or(EvalError("a spread row value is missing"))?,
                };
                let value = Evaluated::Value(value);
                if !attribute_present(value) {
                    continue;
                }
                if !first {
                    out.push(',');
                }
                first = false;
                write_json_str(out, name);
                out.push(':');
                write_attribute_value(out, value)?;
            }
            out.push('}');
        }
        Entry::Index(index) => write!(out, "{index}").expect("writing to a String cannot fail"),
        Entry::Records(records) => {
            out.push('[');
            for (index, record) in records.iter().enumerate() {
                if index > 0 {
                    out.push(',');
                }
                write_record(plan, out, record, false)?;
            }
            out.push(']');
        }
    }
    Ok(())
}

/// Write a record as a JSON object with its keys sorted. The root record
/// also gets the `"calls": {}` entry assembly adds.
fn write_record(
    plan: &Plan,
    out: &mut String,
    record: &Record<'_, '_>,
    with_calls: bool,
) -> Result<(), EvalError> {
    let mut order: Vec<usize> = (0..record.entries.len()).collect();
    // A stable sort keeps a repeated key's writes in order, so the last one
    // wins below, as a later write to a Python dict replaces the value.
    order.sort_by_key(|position| record.entries[*position].0);
    out.push('{');
    let mut first = true;
    let mut calls_written = !with_calls;
    let mut cursor = 0;
    while cursor < order.len() {
        let rank = record.entries[order[cursor]].0;
        let mut last = cursor;
        while last + 1 < order.len() && record.entries[order[last + 1]].0 == rank {
            last += 1;
        }
        if !calls_written && plan.calls_rank < rank {
            if !first {
                out.push(',');
            }
            first = false;
            out.push_str("\"calls\":{}");
            calls_written = true;
        }
        if !first {
            out.push(',');
        }
        first = false;
        let key = &plan.keys[usize::try_from(rank).expect("rank fits usize")];
        write_json_str(out, key);
        out.push(':');
        write_entry(plan, out, &record.entries[order[last]].1)?;
        cursor = last + 1;
    }
    if !calls_written {
        if !first {
            out.push(',');
        }
        out.push_str("\"calls\":{}");
    }
    out.push('}');
    Ok(())
}

impl Plan {
    /// Evaluate the template over one row's values and write its prepared
    /// data, `{"calls":{},...}`, as `script_json(..., sort_keys=True)` does.
    ///
    /// `values` holds one value per read-set root, in [`Plan::roots`] order;
    /// `spreads` holds the layout of each root `c-bind`'s key set for this
    /// row, in spread order.
    pub fn write_row(
        &self,
        values: &[Value],
        spreads: &[&SpreadLayout],
    ) -> Result<String, EvalError> {
        if values.len() != self.roots.len() || spreads.len() != self.spreads.len() {
            return Err(EvalError("the row does not match the plan"));
        }
        let evaluator = Evaluator {
            roots: values,
            spreads,
            plan: self,
        };
        let mut record = Record {
            entries: Vec::with_capacity(self.ops.len()),
        };
        let mut locals = Vec::new();
        evaluator.ops(&self.ops, &mut locals, &mut record)?;
        let mut out = String::with_capacity(512);
        write_record(self, &mut out, &record, true)?;
        Ok(out)
    }
}
