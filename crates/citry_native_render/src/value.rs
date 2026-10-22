//! The values a row template reads, copied out of Python before evaluation.

/// One value the template reads, copied so that later changes to the
/// caller's dicts and lists cannot change this row.
///
/// The tree mirrors the plan's read set ([`crate::ReadNode`]): a dict keeps
/// only the children the template reads, in the read set's order, and a
/// list keeps its items only when the template loops over it.
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    /// A value the template never reads, such as a loop item whose body
    /// reads nothing from it. Only its presence matters.
    Unread,
    None,
    Bool(bool),
    Int(i64),
    /// An int outside the i64 range, kept as the decimal text Python's
    /// `str()` gave it.
    BigInt(String),
    /// A finite float with the text Python's `repr()` gives it. Rust's own
    /// float formatting differs from Python's, so the caller supplies it.
    Float {
        value: f64,
        text: String,
    },
    Str(String),
    Dict {
        /// How many entries the original dict had, which decides its truth value.
        len: usize,
        /// The read children, aligned with the read node's `children`.
        children: Vec<Value>,
        /// For a dict the root `c-bind` spreads: every entry, in the dict's
        /// own order, because the spread writes every name it holds.
        attrs: Option<Attrs>,
    },
    List {
        /// How many items the original list had, which decides its truth value.
        len: usize,
        /// The items, aligned with the read node's `items`; empty when the
        /// template only tests the list's truth.
        items: Vec<Value>,
    },
}

/// The entries of a dict a root `c-bind` spreads, kept in two parallel
/// lists so the names alone can key the per-key-set layout cache.
#[derive(Debug, Clone, PartialEq, Default)]
pub struct Attrs {
    pub names: Vec<String>,
    pub values: Vec<Value>,
}

impl Value {
    /// Python's truth value for the plain types the read set admits.
    ///
    /// The read set only lets a truth test see None, bool, int, float, str,
    /// list or dict, and each answer below is the one Python's `bool()`
    /// gives for that exact builtin type.
    pub(crate) fn truthy(&self) -> Option<bool> {
        Some(match self {
            Value::None => false,
            Value::Bool(flag) => *flag,
            Value::Int(number) => *number != 0,
            // An int outside i64 is never zero.
            Value::BigInt(_) => true,
            // -0.0 compares equal to 0.0, so it is false, as in Python.
            Value::Float { value, .. } => *value != 0.0,
            Value::Str(text) => !text.is_empty(),
            Value::Dict { len, .. } | Value::List { len, .. } => *len > 0,
            Value::Unread => return None,
        })
    }
}
