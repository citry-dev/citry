use ruff_python_ast::name::Name;
use ruff_python_ast::{
    Arguments, Expr, ExprAttribute, ExprCall, ExprContext, ExprName, ExprNoneLiteral,
    ExprNumberLiteral, ExprStringLiteral, ExprTuple, Identifier, Keyword, StringLiteral,
    StringLiteralFlags, StringLiteralValue,
};
use ruff_text_size::TextRange;

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
        elts: elements.into(),
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
        range,
        func: Box::new(func),
        arguments: Arguments {
            range,
            node_index: Default::default(),
            args: args.into_boxed_slice(),
            keywords: keywords.into_boxed_slice(),
        },
    })
}

/// Helper to create a call to an interceptor function (e.g. `variable()`, `call()`, etc)
pub fn interceptor_call(
    func_name: &str,
    args: Vec<Expr>,
    keywords: Vec<Keyword>,
    range: ruff_text_size::TextRange,
) -> Expr {
    // Prepend context, source, and token tuple as first arguments
    let mut all_args = vec![
        variable_name("context", range),
        variable_name("source", range),
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

    // E.g. `call(context, source, (start_index, end_index), fn, *args, **kwargs)`
    call(variable_name(func_name, range), all_args, keywords, range)
}

/// Helper to extract the TextRange from an Expr.
/// Used to get the range of interpolated expressions in f-strings and t-strings.
pub fn get_expr_range(
    expr: &Expr,
    fallback_range: ruff_text_size::TextRange,
) -> ruff_text_size::TextRange {
    match expr {
        Expr::Name(n) => n.range,
        Expr::Call(c) => c.range,
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
