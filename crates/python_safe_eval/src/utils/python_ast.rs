use ruff_python_ast::name::Name;
use ruff_python_ast::{
    Arguments, Expr, ExprAttribute, ExprCall, ExprContext, ExprName, ExprNoneLiteral,
    ExprNumberLiteral, ExprStringLiteral, ExprTuple, Identifier, Keyword, StringLiteral,
    StringLiteralFlags, StringLiteralValue,
};
use ruff_text_size::{Ranged, TextRange};

pub fn string_literal(value: &str, range: TextRange) -> Expr {
    Expr::StringLiteral(ExprStringLiteral {
        node_index: Default::default(),
        range,
        value: StringLiteralValue::single(StringLiteral {
            range,
            node_index: Default::default(),
            value: value.to_string().into_boxed_str(),
            flags: StringLiteralFlags::empty(),
        }),
    })
}

pub fn number_literal(value: usize, range: TextRange) -> Expr {
    Expr::NumberLiteral(ExprNumberLiteral {
        node_index: Default::default(),
        range,
        value: ruff_python_ast::Number::Int(ruff_python_ast::Int::from(
            value.min(u32::MAX as usize) as u32,
        )),
    })
}

pub fn variable_name(name: &str, range: TextRange) -> Expr {
    Expr::Name(ExprName {
        node_index: Default::default(),
        range,
        id: Name::new(name),
        ctx: ExprContext::Load,
    })
}

pub fn none_literal(range: TextRange) -> Expr {
    Expr::NoneLiteral(ExprNoneLiteral {
        node_index: Default::default(),
        range,
    })
}

pub fn tuple_literal(elements: Vec<Expr>, range: TextRange) -> Expr {
    Expr::Tuple(ExprTuple {
        node_index: Default::default(),
        range,
        ctx: ExprContext::Load,
        parenthesized: true,
        elts: elements,
    })
}

pub fn attribute(value: Expr, attr: &str, range: TextRange) -> Expr {
    Expr::Attribute(ExprAttribute {
        node_index: Default::default(),
        range,
        value: Box::new(value),
        attr: Identifier::new(attr, range),
        ctx: ExprContext::Load,
    })
}

pub fn call(func: Expr, args: Vec<Expr>, keywords: Vec<Keyword>, range: TextRange) -> Expr {
    Expr::Call(ExprCall {
        node_index: Default::default(),
        range_start: range.start(),
        func: Box::new(func),
        arguments: Arguments {
            range,
            node_index: Default::default(),
            args: args.into_boxed_slice(),
            // Ruff stores keywords in a compact vector as of 0.16.2.
            keywords: keywords.into(),
        },
    })
}

/// The prefix of every name the generated code reads: the helper functions it calls
/// (`interceptor_call`) and the two arguments, the context mapping and the source text, it
/// passes to each of them.
///
/// A template reads a free name through `_sx_variable()`, and the Python runtime refuses
/// every name that starts with `_`, so a template cannot read or replace these names that
/// way. A lambda parameter or comprehension variable is bound by Python directly, so the
/// transformer refuses one that starts with this prefix (`refuse_generated_name`). Any
/// other name, `context` and `source` included, is free for the template to use.
pub const GENERATED_NAME_PREFIX: &str = "_sx_";

/// The local variable that holds the context mapping inside the function the Python
/// runtime wraps around the generated code. Every helper receives it first.
pub const CONTEXT_NAME: &str = "_sx_context";

/// The expression's source text, which the Python runtime puts in the evaluation
/// namespace so a helper can point an error at the failing part.
pub const SOURCE_NAME: &str = "_sx_source";

/// Every name the generated code reads, each starting with `GENERATED_NAME_PREFIX`. The
/// Python runtime (`citry_core/safe_eval/eval.py`) defines the same names: the helpers and
/// `_sx_source` in its evaluation namespace, and `_sx_context` as a local variable of the
/// wrapper function.
/// The test `test_generated_names_list_matches_what_the_transformer_writes` fails when the
/// transformer writes a name that is missing here.
pub const GENERATED_NAMES: [&str; 11] = [
    "_sx_variable",
    "_sx_attribute",
    "_sx_subscript",
    "_sx_call",
    "_sx_assign",
    "_sx_slice",
    "_sx_interpolation",
    "_sx_template",
    "_sx_format",
    SOURCE_NAME,
    CONTEXT_NAME,
];

/// Helper to create a call to an interceptor function, given its name without the prefix
/// (e.g. `"variable"` writes `_sx_variable(...)`).
pub fn interceptor_call(
    func_name: &str,
    args: Vec<Expr>,
    keywords: Vec<Keyword>,
    range: ruff_text_size::TextRange,
) -> Expr {
    // Every helper name carries the prefix, so the transformer can refuse any template
    // binding that would match one
    let helper_name = format!("{GENERATED_NAME_PREFIX}{func_name}");
    // A helper missing from the list would not be cross-checked against the runtime
    debug_assert!(GENERATED_NAMES.contains(&helper_name.as_str()));

    // Prepend context, source, and token tuple as first arguments
    let mut all_args = vec![
        variable_name(CONTEXT_NAME, range),
        variable_name(SOURCE_NAME, range),
        // Create tuple: (start_index_int, end_index_int)
        tuple_literal(
            vec![
                number_literal(range.start().to_usize(), range),
                number_literal(range.end().to_usize(), range),
            ],
            range,
        ),
    ];

    // Followed by the rest of the arguments
    all_args.extend(args);

    // E.g. `_sx_call(_sx_context, _sx_source, (start_index, end_index), fn, *args, **kwargs)`
    call(
        variable_name(&helper_name, range),
        all_args,
        keywords,
        range,
    )
}

/// Helper to extract the TextRange from an Expr.
/// Used to get the range of interpolated expressions in f-strings and t-strings.
pub fn get_expr_range(
    expr: &Expr,
    fallback_range: ruff_text_size::TextRange,
) -> ruff_text_size::TextRange {
    match expr {
        Expr::Name(n) => n.range,
        Expr::Call(c) => c.range(),
        Expr::Attribute(a) => a.range,
        Expr::Subscript(s) => s.range,
        Expr::BinOp(b) => b.range,
        Expr::UnaryOp(u) => u.range,
        Expr::Compare(c) => c.range,
        Expr::BoolOp(b) => b.range,
        Expr::If(i) => i.range,
        Expr::Named(n) => n.range,
        Expr::StringLiteral(s) => s.range,
        Expr::NumberLiteral(n) => n.range,
        Expr::BooleanLiteral(b) => b.range,
        Expr::NoneLiteral(n) => n.range,
        Expr::List(l) => l.range,
        Expr::Tuple(t) => t.range,
        Expr::Dict(d) => d.range,
        Expr::Set(s) => s.range,
        Expr::FString(f) => f.range,
        Expr::TString(t) => t.range,
        Expr::Lambda(l) => l.range,
        Expr::ListComp(l) => l.range,
        Expr::SetComp(s) => s.range,
        Expr::DictComp(d) => d.range,
        Expr::Generator(g) => g.range,
        Expr::Starred(s) => s.range,
        Expr::Slice(s) => s.range,
        _ => fallback_range, // Fallback to provided range for unknown types
    }
}
