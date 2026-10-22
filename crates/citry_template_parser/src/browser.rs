//! Portable JavaScript analysis for Citry-owned Vue expression hosts.
//!
//! OXC owns JavaScript syntax and lexical scope resolution here. Citry wraps
//! authored fragments in a generated async function, then maps only exact
//! unresolved identifier references back to authored UTF-8 byte offsets. The
//! wrapper makes Vue statement contexts parseable without pretending that
//! the template language is a complete JavaScript module.
//!
//! The result structs are also Python classes (`citry_core.template_parser`):
//! each is a `#[pyclass(frozen, eq)]` whose `#[pyo3(get)]` fields are what
//! Python reads, so a field change here is a change to citry-core's Python
//! surface and to the hand-written `_rust.pyi` stub.

use std::str::FromStr;

use oxc_allocator::Allocator;
use oxc_ast::ast::{
    Argument, ArrowFunctionBody, AssignmentExpression, AssignmentTarget, CallExpression,
    Expression, FormalParameters, Function, ObjectExpression, ObjectPropertyKind, Program,
    SimpleAssignmentTarget, Statement, VariableDeclarator,
};
use oxc_ast_visit::{walk, Visit};
use oxc_diagnostics::OxcDiagnostic;
use oxc_parser::{ParseOptions, Parser};
use oxc_semantic::{Scoping, SemanticBuilder, SymbolId};
use oxc_span::{GetSpan, SourceType};
use oxc_syntax::{operator::AssignmentOperator, scope::ScopeFlags};
use pyo3::prelude::*;

/// The grammar expected for one authored browser-expression host.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BrowserAnalysisMode {
    Expression,
    Statement,
}

impl FromStr for BrowserAnalysisMode {
    type Err = String;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "expression" => Ok(Self::Expression),
            "statement" => Ok(Self::Statement),
            _ => Err(format!("unknown browser analysis mode: {value:?}")),
        }
    }
}

/// Write one field value the way Python's `repr()` would, so each record's
/// `__repr__` reads like the Python object it is.
trait PyRepr {
    fn py_repr(&self) -> String;
}

impl PyRepr for bool {
    fn py_repr(&self) -> String {
        if *self { "True" } else { "False" }.to_string()
    }
}

impl PyRepr for usize {
    fn py_repr(&self) -> String {
        self.to_string()
    }
}

impl PyRepr for String {
    fn py_repr(&self) -> String {
        // Rust's debug quoting matches Python's for the identifiers, option
        // names, and parser messages these records hold.
        format!("{self:?}")
    }
}

impl<T: PyRepr> PyRepr for Option<T> {
    fn py_repr(&self) -> String {
        self.as_ref()
            .map_or_else(|| "None".to_string(), PyRepr::py_repr)
    }
}

impl<T: PyRepr> PyRepr for Vec<T> {
    fn py_repr(&self) -> String {
        let items = self.iter().map(PyRepr::py_repr).collect::<Vec<_>>();
        format!("[{}]", items.join(", "))
    }
}

impl PyRepr for (usize, usize) {
    fn py_repr(&self) -> String {
        format!("({}, {})", self.0, self.1)
    }
}

/// Give a record a Python `__repr__` listing the named fields, such as
/// `BrowserReference(name="open", start=0, end=4, written=True)`.
macro_rules! python_record_repr {
    ($record:ident { $($field:ident),+ $(,)? }) => {
        impl PyRepr for $record {
            fn py_repr(&self) -> String {
                let fields = [$(format!("{}={}", stringify!($field), self.$field.py_repr())),+];
                format!("{}({})", stringify!($record), fields.join(", "))
            }
        }

        #[pymethods]
        impl $record {
            fn __repr__(&self) -> String {
                self.py_repr()
            }
        }
    };
}

/// One free JavaScript identifier in authored source.
///
/// `start` and `end` are UTF-8 byte offsets into the authored text.
/// `written` is true when the code assigns to or updates the name at this
/// place (`open = false`, `count += 1`, `count++`, `[open] = pair`,
/// `for (open of list)`); `open.count = 1` writes a field and leaves it
/// false. The slot-pattern analysis reuses this struct for the names a
/// pattern declares, and there `written` is always false.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserReference {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
    #[pyo3(get)]
    pub written: bool,
}

python_record_repr!(BrowserReference {
    name,
    start,
    end,
    written
});

/// The JavaScript parser's first error in one authored expression or statement.
///
/// `message` is OXC's own wording, such as `Unexpected token`. `start` and
/// `end` are UTF-8 byte offsets into the authored text with
/// `start <= end <= len(text)`; an error at the end of the text, such as an
/// unfinished `open &&`, has an empty range there.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserSyntaxDiagnostic {
    #[pyo3(get)]
    pub message: String,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
}

python_record_repr!(BrowserSyntaxDiagnostic {
    message,
    start,
    end
});

/// Parser and scope result with generated wrapper details removed.
///
/// `error` is set exactly when `valid` is false, and `references` is empty
/// then, so a caller never sees names from text that does not parse.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserAnalysis {
    #[pyo3(get)]
    pub valid: bool,
    #[pyo3(get)]
    pub error: Option<BrowserSyntaxDiagnostic>,
    #[pyo3(get)]
    pub references: Vec<BrowserReference>,
}

python_record_repr!(BrowserAnalysis {
    valid,
    error,
    references
});

/// One direct synchronous write to the `$component` callback's scope object.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserScopeWrite {
    pub name: String,
    pub name_start: usize,
    pub name_end: usize,
    pub value_start: usize,
    pub value_end: usize,
}

/// Parser and scope result for one Vue slot-props parameter pattern or list.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserBindingPatternAnalysis {
    pub valid: bool,
    pub bindings: Vec<BrowserReference>,
    pub references: Vec<BrowserReference>,
}

/// Parse one Vue slot-props parameter list through a synchronous arrow function.
pub fn analyze_browser_binding_pattern(source: &str) -> BrowserBindingPatternAnalysis {
    let prefix = "(";
    let suffix = ") => {}";
    let wrapped = format!("{prefix}{source}{suffix}");
    let invalid = || BrowserBindingPatternAnalysis {
        valid: false,
        bindings: Vec::new(),
        references: Vec::new(),
    };

    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, &wrapped, SourceType::script()).parse();
    if !parsed.diagnostics.is_empty() {
        return invalid();
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    if !built.diagnostics.is_empty() {
        return invalid();
    }
    let [Statement::ExpressionStatement(statement)] = parsed.program.body.as_slice() else {
        return invalid();
    };
    let Expression::ArrowFunctionExpression(function) = statement.expression.without_parentheses()
    else {
        return invalid();
    };
    let function_span = function.span();
    let params_span = function.params.span();
    let body_span = function.body.span();
    let ArrowFunctionBody::FunctionBody(body) = &function.body else {
        return invalid();
    };
    if function.r#async
        || function_span.start != 0
        || function_span.end as usize != wrapped.len()
        || params_span.start != 0
        || params_span.end as usize != source.len() + 2
        || body_span.start as usize != wrapped.len() - 2
        || body_span.end as usize != wrapped.len()
        || !body.directives.is_empty()
        || !body.statements.is_empty()
    {
        return invalid();
    }

    let source_start = prefix.len();
    let source_end = source_start + source.len();
    let identifiers = function
        .params
        .items
        .iter()
        .flat_map(|parameter| parameter.pattern.get_binding_identifiers())
        .chain(
            function
                .params
                .rest
                .iter()
                .flat_map(|rest| rest.rest.argument.get_binding_identifiers()),
        );
    let mut bindings = identifiers
        .filter_map(|identifier| {
            let span = identifier.span();
            let start = span.start as usize;
            let end = span.end as usize;
            (start >= source_start && end <= source_end && start < end).then(|| {
                BrowserReference {
                    name: identifier.name.to_string(),
                    start: start - source_start,
                    end: end - source_start,
                    // A declared name is not a write the template makes.
                    written: false,
                }
            })
        })
        .collect::<Vec<_>>();
    bindings.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });

    let semantic = built.semantic;
    let mut references = Vec::new();
    for (name, reference_ids) in semantic.scoping().root_unresolved_references() {
        for reference_id in reference_ids {
            let reference = semantic.scoping().get_reference(*reference_id);
            let span = semantic.nodes().get_node(reference.node_id()).span();
            let start = span.start as usize;
            let end = span.end as usize;
            if start >= source_start && end <= source_end && start < end {
                references.push(BrowserReference {
                    name: name.to_string(),
                    start: start - source_start,
                    end: end - source_start,
                    // A default value in a slot pattern can only read.
                    written: false,
                });
            }
        }
    }
    references.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });
    BrowserBindingPatternAnalysis {
        valid: true,
        bindings,
        references,
    }
}

/// One name destructured from the `$component` initializer context.
///
/// `name` is the context field, one of `COMPONENT_CONTEXT_NAMES`;
/// `local_name` is the variable it is bound to; `references` are the byte
/// ranges where the code reads that variable.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentBinding {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub local_name: String,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
    #[pyo3(get)]
    pub references: Vec<(usize, usize)>,
}

python_record_repr!(BrowserComponentBinding {
    name,
    local_name,
    start,
    end,
    references
});

/// One root-unresolved `$component` call authenticated by OXC semantics.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentCall {
    #[pyo3(get)]
    pub call_start: usize,
    #[pyo3(get)]
    pub call_end: usize,
    #[pyo3(get)]
    pub callee_start: usize,
    #[pyo3(get)]
    pub callee_end: usize,
    #[pyo3(get)]
    pub open_paren_end: usize,
    #[pyo3(get)]
    pub argument_start: Option<usize>,
    #[pyo3(get)]
    pub argument_end: Option<usize>,
}

python_record_repr!(BrowserComponentCall {
    call_start,
    call_end,
    callee_start,
    callee_end,
    open_paren_end,
    argument_start,
    argument_end
});

/// One statically named public binding declared by Vue Options.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserPublicName {
    #[pyo3(get)]
    pub authored_name: String,
    #[pyo3(get)]
    pub exposed_name: String,
    #[pyo3(get)]
    pub origin: String,
    #[pyo3(get)]
    pub name_start: usize,
    #[pyo3(get)]
    pub name_end: usize,
    #[pyo3(get)]
    pub value_start: Option<usize>,
    #[pyo3(get)]
    pub value_end: Option<usize>,
    #[pyo3(get)]
    pub required: Option<bool>,
    #[pyo3(get)]
    pub has_default: Option<bool>,
    #[pyo3(get)]
    pub default_is_null: Option<bool>,
    #[pyo3(get)]
    pub type_source: Option<String>,
}

python_record_repr!(BrowserPublicName {
    authored_name,
    exposed_name,
    origin,
    name_start,
    name_end,
    value_start,
    value_end,
    required,
    has_default,
    default_is_null,
    type_source
});

/// Conservative knowledge for one Vue Options namespace.
///
/// `state` is `absent` (the options name nothing there), `complete` (every
/// name is listed), or `unknown`, with `unknown_reason` saying why.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserOptionsSection {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub state: String,
    #[pyo3(get)]
    pub start: Option<usize>,
    #[pyo3(get)]
    pub end: Option<usize>,
    #[pyo3(get)]
    pub unknown_reason: Option<String>,
}

python_record_repr!(BrowserOptionsSection {
    name,
    state,
    start,
    end,
    unknown_reason
});

/// One component-instance member reference with a proven receiver.
///
/// The span normally covers the member name in `receiver.name`. For the
/// `$i18n` member only, it may instead cover a read of a local variable that
/// holds `receiver.$i18n` and is never reassigned, so a consumer that needs
/// the identifier written at the call site reads it from the span.
/// `written` is true when the code assigns to or updates the member itself,
/// as in `this.open = false` or `this.count++`; `this.open.count = 1`
/// writes a field of the member and leaves it false.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentMemberReference {
    #[pyo3(get)]
    pub receiver: String,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
    #[pyo3(get)]
    pub written: bool,
}

python_record_repr!(BrowserComponentMemberReference {
    receiver,
    name,
    start,
    end,
    written
});

/// One event name declared by the Vue Options `emits` section.
///
/// The span covers the string literal of an array entry or the key of an
/// object entry, as authored.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserEmitName {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
}

python_record_repr!(BrowserEmitName { name, start, end });

/// One custom directive name declared by the Vue Options `directives` section.
///
/// `name` is the key as Vue registers it (`iff`, `my-dir`, `myDir`), and the
/// span covers the key as authored, quotes included.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserDirectiveName {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub start: usize,
    #[pyo3(get)]
    pub end: usize,
}

python_record_repr!(BrowserDirectiveName { name, start, end });

/// Source facts proven inside runtime `$component` initializers.
///
/// The lists that hold one entry per `$component` call (`sections` in
/// groups of six, `emits_sections`, `directives_sections`, `inherit_attrs`)
/// skip a call with no argument or a spread argument, so they can be
/// shorter than `component_calls`.
#[pyclass(frozen, eq)]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BrowserComponentAnalysis {
    #[pyo3(get)]
    pub valid: bool,
    #[pyo3(get)]
    pub references: Vec<BrowserReference>,
    #[pyo3(get)]
    pub bindings: Vec<BrowserComponentBinding>,
    /// Read through `analyze_component_scope_writes`, so it stays off the
    /// Python record.
    pub scope_writes: Vec<BrowserScopeWrite>,
    #[pyo3(get)]
    pub component_calls: Vec<BrowserComponentCall>,
    #[pyo3(get)]
    pub public_names: Vec<BrowserPublicName>,
    #[pyo3(get)]
    pub sections: Vec<BrowserOptionsSection>,
    #[pyo3(get)]
    pub member_references: Vec<BrowserComponentMemberReference>,
    /// What each `$component` call proves about its `emits` section, in call
    /// order. It is kept apart from `sections` because declared events are
    /// not instance members: an unreadable `emits` must not make every
    /// instance name unknown.
    #[pyo3(get)]
    pub emits_sections: Vec<BrowserOptionsSection>,
    /// The event names of every `complete` emits section.
    #[pyo3(get)]
    pub emit_names: Vec<BrowserEmitName>,
    /// What each `$component` call proves about its `directives` section, in
    /// call order. Like `emits`, directives are not instance members, so an
    /// unreadable section leaves the instance names alone.
    #[pyo3(get)]
    pub directives_sections: Vec<BrowserOptionsSection>,
    /// The directive names of every `complete` directives section.
    #[pyo3(get)]
    pub directive_names: Vec<BrowserDirectiveName>,
    /// Each `$component` call's `inheritAttrs`, in call order: `Some(false)`
    /// or `Some(true)` when the source proves the value Vue sees (an absent
    /// key is Vue's default, `true`), and `None` when it cannot tell.
    #[pyo3(get)]
    pub inherit_attrs: Vec<Option<bool>>,
}

python_record_repr!(BrowserComponentAnalysis {
    valid,
    references,
    bindings,
    component_calls,
    public_names,
    sections,
    member_references,
    emits_sections,
    emit_names,
    directives_sections,
    directive_names,
    inherit_attrs
});

impl BrowserComponentAnalysis {
    /// The result for source that does not parse: no facts at all, so a
    /// consumer cannot mistake a partial read for a complete one.
    fn invalid() -> Self {
        Self {
            valid: false,
            references: Vec::new(),
            bindings: Vec::new(),
            scope_writes: Vec::new(),
            component_calls: Vec::new(),
            public_names: Vec::new(),
            sections: Vec::new(),
            member_references: Vec::new(),
            emits_sections: Vec::new(),
            emit_names: Vec::new(),
            directives_sections: Vec::new(),
            directive_names: Vec::new(),
            inherit_attrs: Vec::new(),
        }
    }
}

/// The text Citry puts around an authored expression so OXC can resolve its
/// names inside an async function, as Vue runs a listener.
const EXPRESSION_PREFIX: &str = "async function __citry_browser_expression__() { return (\n";
const EXPRESSION_SUFFIX: &str = "\n); }";
/// The same for a listener's statements.
const STATEMENT_PREFIX: &str = "async function __citry_browser_expression__() {\n";
const STATEMENT_SUFFIX: &str = "\n}";

/// Parse one browser expression/statement and return its exact free roots.
///
/// The free names come from parsing the authored text inside a generated
/// async function. When that fails, the syntax error comes from a second
/// parse of the authored text alone, because a mistake such as `open &&`
/// fails inside the generated text after it, where neither the position nor
/// the message describes what the author wrote.
pub fn analyze_browser_source(source: &str, mode: BrowserAnalysisMode) -> BrowserAnalysis {
    let (prefix, suffix) = match mode {
        BrowserAnalysisMode::Expression => (EXPRESSION_PREFIX, EXPRESSION_SUFFIX),
        BrowserAnalysisMode::Statement => (STATEMENT_PREFIX, STATEMENT_SUFFIX),
    };
    let mut wrapped = String::with_capacity(prefix.len() + source.len() + suffix.len());
    wrapped.push_str(prefix);
    wrapped.push_str(source);
    wrapped.push_str(suffix);
    let invalid = |error: BrowserSyntaxDiagnostic| BrowserAnalysis {
        valid: false,
        error: Some(error),
        references: Vec::new(),
    };

    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, &wrapped, SourceType::default()).parse();
    if let Some(diagnostic) = parsed.diagnostics.first() {
        // The standalone parse is expected to fail too; if it does not, the
        // wrapped error is still a real one, moved back into authored text.
        return invalid(
            standalone_syntax_error(source, mode)
                .unwrap_or_else(|| syntax_diagnostic(diagnostic, prefix.len(), source.len())),
        );
    }
    // Text such as `a); (b` closes the generated function and opens another
    // statement, so the wrapped parse succeeds while Vue's would not.
    if !has_generated_shape(&parsed.program, mode, prefix, source.len()) {
        return invalid(standalone_syntax_error(source, mode).unwrap_or_else(|| {
            // Unreachable for any text found so far: escaping the function
            // needs an unmatched closing token, which the standalone parse
            // rejects. The whole text is the honest range if it ever happens.
            BrowserSyntaxDiagnostic {
                message: "Unexpected token".to_string(),
                start: 0,
                end: source.len(),
            }
        }));
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    // Scope errors, such as a name declared twice in a listener, appear only
    // in this pass, and their ranges already sit inside the authored text.
    if let Some(diagnostic) = built.diagnostics.first() {
        return invalid(syntax_diagnostic(diagnostic, prefix.len(), source.len()));
    }

    let semantic = built.semantic;
    let source_start = prefix.len();
    let source_end = source_start + source.len();
    let mut references = Vec::new();
    for (name, reference_ids) in semantic.scoping().root_unresolved_references() {
        for reference_id in reference_ids {
            let reference = semantic.scoping().get_reference(*reference_id);
            let span = semantic.nodes().get_node(reference.node_id()).span();
            let start = span.start as usize;
            let end = span.end as usize;
            if start < source_start || end > source_end || start >= end {
                continue;
            }
            references.push(BrowserReference {
                name: name.to_string(),
                start: start - source_start,
                end: end - source_start,
                // OXC flags the name itself as the target of `=`, `+=`,
                // `++`, destructuring, or `for ... of`; `open.count = 1`
                // only reads `open`.
                written: reference.is_write(),
            });
        }
    }
    references.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });
    BrowserAnalysis {
        valid: true,
        error: None,
        references,
    }
}

/// Return whether a parsed wrapper still has exactly the generated shape.
///
/// That shape is one top-level function spanning the whole wrapped text,
/// whose body opens at the generated `{` and closes at the generated `}`;
/// in expression mode the body is only the generated `return (...)`, with
/// the parentheses at their generated places. Authored text that closes the
/// function early, or splits the returned value, changes one of these spans.
fn has_generated_shape(
    program: &Program<'_>,
    mode: BrowserAnalysisMode,
    prefix: &str,
    source_len: usize,
) -> bool {
    let suffix_len = match mode {
        BrowserAnalysisMode::Expression => EXPRESSION_SUFFIX.len(),
        BrowserAnalysisMode::Statement => STATEMENT_SUFFIX.len(),
    };
    let prefix_len = prefix.len();
    let wrapped_len = prefix_len + source_len + suffix_len;
    let [Statement::FunctionDeclaration(function)] = program.body.as_slice() else {
        return false;
    };
    let Some(body) = &function.body else {
        return false;
    };
    // The first `{` in either prefix opens the function body.
    let Some(body_start) = prefix.find('{') else {
        return false;
    };
    if function.span.start != 0
        || function.span.end as usize != wrapped_len
        || body.span.start as usize != body_start
        || body.span.end as usize != wrapped_len
    {
        return false;
    }
    if mode == BrowserAnalysisMode::Statement {
        return true;
    }
    let [Statement::ReturnStatement(statement)] = body.statements.as_slice() else {
        return false;
    };
    let Some(Expression::ParenthesizedExpression(value)) = &statement.argument else {
        return false;
    };
    // `return (` ends the prefix with `(` and a line break, and the suffix
    // starts with a line break and `)`.
    let source_end = prefix_len + source_len;
    value.span.start as usize == prefix_len - 2 && value.span.end as usize == source_end + 2
}

/// Parse the authored text alone and return its first syntax error.
///
/// An expression is parsed as one expression, so trailing text such as the
/// `)` in `a)` is an error at the place it appears. Statements are parsed as
/// a module that allows `return` and top-level `await`, which is what the
/// generated async function allows.
fn standalone_syntax_error(
    source: &str,
    mode: BrowserAnalysisMode,
) -> Option<BrowserSyntaxDiagnostic> {
    let allocator = Allocator::default();
    let options = ParseOptions {
        allow_return_outside_function: true,
        ..ParseOptions::default()
    };
    let parser = Parser::new(&allocator, source, SourceType::default()).with_options(options);
    match mode {
        BrowserAnalysisMode::Expression => match parser.parse_expression() {
            Err(diagnostics) => diagnostics
                .first()
                .map(|diagnostic| syntax_diagnostic(diagnostic, 0, source.len())),
            // OXC stops after the first complete expression without asking
            // for the end of the text, so leftover text such as the `)` in
            // `a)` is reported here, in OXC's wording for a stray token.
            Ok(expression) => {
                leftover_token(source, expression.span().end as usize).map(|(start, end)| {
                    BrowserSyntaxDiagnostic {
                        message: "Unexpected token".to_string(),
                        start,
                        end,
                    }
                })
            }
        },
        BrowserAnalysisMode::Statement => parser
            .parse()
            .diagnostics
            .first()
            .map(|diagnostic| syntax_diagnostic(diagnostic, 0, source.len())),
    }
}

/// Return the byte range of the first token at or after `from`, skipping
/// whitespace and comments, or `None` when only those remain.
///
/// The range covers a run of identifier characters, or else one character,
/// which is enough to underline a stray `)`, `;`, or name.
fn leftover_token(source: &str, from: usize) -> Option<(usize, usize)> {
    let is_line_end = |character: char| matches!(character, '\n' | '\r' | '\u{2028}' | '\u{2029}');
    let mut position = from;
    loop {
        let rest = &source[position..];
        let trimmed = rest.trim_start_matches(|character: char| {
            character.is_whitespace() || character == '\u{feff}'
        });
        position += rest.len() - trimmed.len();
        if trimmed.starts_with("//") {
            position += trimmed.find(is_line_end).unwrap_or(trimmed.len());
        } else if let Some(comment) = trimmed.strip_prefix("/*") {
            // An unclosed comment ends the text; the parser has already
            // stopped before it, so it is the stray token.
            let Some(close) = comment.find("*/") else {
                return Some((position, position + 2));
            };
            position += 2 + close + 2;
        } else {
            break;
        }
    }
    let rest = &source[position..];
    let first = rest.chars().next()?;
    let is_name = |character: char| {
        character.is_alphanumeric() || matches!(character, '_' | '$') || !character.is_ascii()
    };
    let length = if is_name(first) {
        rest.find(|character: char| !is_name(character))
            .unwrap_or(rest.len())
    } else {
        first.len_utf8()
    };
    Some((position, position + length))
}

/// Turn one OXC diagnostic into authored-text coordinates.
///
/// `shift` is the length of generated text in front of the authored text in
/// the parsed input. The range is the label OXC marks as primary, else its
/// last label (OXC lists context such as an earlier declaration first and
/// the place of the mistake last), else the whole text, and it is clamped into the authored
/// text: a position past its end, such as OXC's "Unexpected end of file",
/// becomes an empty range at the end.
fn syntax_diagnostic(
    diagnostic: &OxcDiagnostic,
    shift: usize,
    source_len: usize,
) -> BrowserSyntaxDiagnostic {
    let labels = &diagnostic.labels;
    let label = labels
        .iter()
        .find(|label| label.primary())
        .or_else(|| labels.last());
    let (start, end) = label.map_or((0, source_len), |label| {
        let offset = label.offset() as usize;
        let start = offset.saturating_sub(shift).min(source_len);
        let end = (offset + label.len() as usize)
            .saturating_sub(shift)
            .clamp(start, source_len);
        (start, end)
    });
    BrowserSyntaxDiagnostic {
        message: diagnostic.message.to_string(),
        start,
        end,
    }
}

/// Analyze runtime `$component` initializers without executing their source.
pub fn analyze_component_source(source: &str) -> BrowserComponentAnalysis {
    let allocator = Allocator::default();
    let parsed = Parser::new(&allocator, source, SourceType::default()).parse();
    if !parsed.diagnostics.is_empty() {
        return BrowserComponentAnalysis::invalid();
    }
    let built = SemanticBuilder::new_compiler()
        .with_build_nodes(true)
        .with_check_syntax_error(true)
        .build(&parsed.program);
    if !built.diagnostics.is_empty() {
        return BrowserComponentAnalysis::invalid();
    }
    let semantic = built.semantic;
    let mut visitor = ComponentVisitor::new(source, semantic.scoping());
    visitor.visit_program(&parsed.program);
    visitor.scope_writes.sort_by(|left, right| {
        (left.name_start, left.name_end, &left.name).cmp(&(
            right.name_start,
            right.name_end,
            &right.name,
        ))
    });
    visitor.scope_writes.dedup();
    let component_symbols = visitor
        .bindings
        .iter()
        .filter(|binding| binding.name == "component")
        .map(|binding| binding.symbol_id)
        .collect::<Vec<_>>();
    let mut alias_members = AliasMemberVisitor {
        scoping: semantic.scoping(),
        component_symbols: &component_symbols,
        references: Vec::new(),
    };
    alias_members.visit_program(&parsed.program);
    visitor.member_references.extend(alias_members.references);
    // Component code often stores the i18n service once
    // (`const i18n = component.$i18n`) and calls `i18n.bind(...)` later. The
    // i18n extension only preloads messages for calls on a proven `$i18n`,
    // so each read of such a variable is reported as that member too.
    let mut i18n_aliases = I18nAliasVisitor {
        scoping: semantic.scoping(),
        members: &visitor.member_references,
        aliases: Vec::new(),
    };
    i18n_aliases.visit_program(&parsed.program);
    for (receiver, symbol) in i18n_aliases.aliases {
        for reference in semantic.scoping().get_resolved_references(symbol) {
            let span = semantic.nodes().get_node(reference.node_id()).span();
            visitor
                .member_references
                .push(BrowserComponentMemberReference {
                    receiver: receiver.clone(),
                    name: "$i18n".to_string(),
                    start: span.start as usize,
                    end: span.end as usize,
                    // Set for write targets once every reference is collected.
                    written: false,
                });
        }
    }
    visitor
        .component_calls
        .sort_by_key(|call| (call.call_start, call.call_end));
    visitor.component_calls.dedup();
    visitor
        .public_names
        .sort_by_key(|name| (name.name_start, name.name_end));
    visitor
        .member_references
        .sort_by_key(|reference| (reference.start, reference.end));
    visitor.member_references.dedup();
    // The member visitors record a write target like any other member, so
    // one pass over the write targets marks them. Marking after `dedup()`
    // keeps one entry per range.
    let mut write_targets = MemberWriteTargetVisitor::default();
    write_targets.visit_program(&parsed.program);
    for reference in &mut visitor.member_references {
        reference.written = write_targets
            .property_spans
            .contains(&(reference.start, reference.end));
    }
    let mut bindings = visitor
        .bindings
        .into_iter()
        .map(|candidate| {
            let mut references = semantic
                .scoping()
                .get_resolved_references(candidate.symbol_id)
                .map(|reference| semantic.nodes().get_node(reference.node_id()).span())
                .map(|span| (span.start as usize, span.end as usize))
                .collect::<Vec<_>>();
            references.sort_unstable();
            references.dedup();
            BrowserComponentBinding {
                name: candidate.name,
                local_name: candidate.local_name,
                start: candidate.start,
                end: candidate.end,
                references,
            }
        })
        .collect::<Vec<_>>();
    bindings.sort_by(|left, right| {
        (left.start, left.end, &left.local_name).cmp(&(right.start, right.end, &right.local_name))
    });
    bindings.dedup();

    // Root-unresolved references are already scope-aware. Keeping only spans
    // inside a proven initializer excludes the helper call and file-level JS.
    let mut references = Vec::new();
    for (name, reference_ids) in semantic.scoping().root_unresolved_references() {
        for reference_id in reference_ids {
            let reference = semantic.scoping().get_reference(*reference_id);
            let span = semantic.nodes().get_node(reference.node_id()).span();
            let start = span.start as usize;
            let end = span.end as usize;
            if start >= end
                || !visitor
                    .initializer_ranges
                    .iter()
                    .any(|(range_start, range_end)| start >= *range_start && end <= *range_end)
            {
                continue;
            }
            references.push(BrowserReference {
                name: name.to_string(),
                start,
                end,
                written: reference.is_write(),
            });
        }
    }
    references.sort_by(|left, right| {
        (left.start, left.end, &left.name).cmp(&(right.start, right.end, &right.name))
    });
    references.dedup();

    BrowserComponentAnalysis {
        valid: true,
        references,
        bindings,
        scope_writes: visitor.scope_writes,
        component_calls: visitor.component_calls,
        public_names: visitor.public_names,
        sections: visitor.sections,
        member_references: visitor.member_references,
        emits_sections: visitor.emits_sections,
        emit_names: visitor.emit_names,
        directives_sections: visitor.directives_sections,
        directive_names: visitor.directive_names,
        inherit_attrs: visitor.inherit_attrs,
    }
}

/// Find static top-level scope properties written during `$component` init.
pub fn analyze_component_scope_writes(source: &str) -> Vec<BrowserScopeWrite> {
    analyze_component_source(source).scope_writes
}

struct ComponentVisitor<'semantic> {
    source: &'semantic str,
    scoping: &'semantic Scoping,
    initializer_ranges: Vec<(usize, usize)>,
    bindings: Vec<ComponentBindingCandidate>,
    scope_writes: Vec<BrowserScopeWrite>,
    component_calls: Vec<BrowserComponentCall>,
    public_names: Vec<BrowserPublicName>,
    sections: Vec<BrowserOptionsSection>,
    member_references: Vec<BrowserComponentMemberReference>,
    emits_sections: Vec<BrowserOptionsSection>,
    emit_names: Vec<BrowserEmitName>,
    directives_sections: Vec<BrowserOptionsSection>,
    directive_names: Vec<BrowserDirectiveName>,
    inherit_attrs: Vec<Option<bool>>,
}

impl<'a> Visit<'a> for ComponentVisitor<'_> {
    fn visit_call_expression(&mut self, call: &CallExpression<'a>) {
        if self.is_unresolved_identifier(&call.callee, "$component") {
            let callee = call.callee.span();
            let call_span = call.span();
            let search_end = call
                .arguments
                .first()
                .map_or(call_span.end as usize, |argument| {
                    argument.span().start as usize
                });
            let open_paren_end = self.source[callee.end as usize..search_end]
                .find('(')
                .map_or(callee.end as usize, |offset| {
                    callee.end as usize + offset + 1
                });
            let argument_span = call.arguments.first().map(GetSpan::span);
            self.component_calls.push(BrowserComponentCall {
                call_start: call_span.start as usize,
                call_end: call_span.end as usize,
                callee_start: callee.start as usize,
                callee_end: callee.end as usize,
                open_paren_end,
                argument_start: argument_span.map(|span| span.start as usize),
                argument_end: argument_span.map(|span| span.end as usize),
            });
            if let Some(argument) = call.arguments.first().and_then(Argument::as_expression) {
                if let Expression::ObjectExpression(options) = argument.without_parentheses() {
                    self.collect_initializer(argument, false);
                    let span = options.span();
                    self.initializer_ranges
                        .push((span.start as usize, span.end as usize));
                    self.collect_options(options);
                } else {
                    self.collect_initializer(argument, true);
                    if matches!(
                        argument.without_parentheses(),
                        Expression::ArrowFunctionExpression(_) | Expression::FunctionExpression(_)
                    ) {
                        // The runtime treats a function literal as
                        // `{onServerRender: fn}`, so it declares no Options
                        // names and every section is known to be empty.
                        self.collect_absent_options();
                    } else {
                        self.collect_unknown_options(argument.span());
                    }
                }
            }
        }
        walk::walk_call_expression(self, call);
    }
}

impl<'semantic> ComponentVisitor<'semantic> {
    fn new(source: &'semantic str, scoping: &'semantic Scoping) -> Self {
        Self {
            source,
            scoping,
            initializer_ranges: Vec::new(),
            bindings: Vec::new(),
            scope_writes: Vec::new(),
            component_calls: Vec::new(),
            public_names: Vec::new(),
            sections: Vec::new(),
            member_references: Vec::new(),
            emits_sections: Vec::new(),
            emit_names: Vec::new(),
            directives_sections: Vec::new(),
            directive_names: Vec::new(),
            inherit_attrs: Vec::new(),
        }
    }

    fn collect_options(&mut self, options: &ObjectExpression<'_>) {
        const SECTIONS: [&str; 6] = ["props", "methods", "computed", "inject", "data", "setup"];
        let options_start = options.span.start as usize;
        for section_name in SECTIONS {
            let mut state = BrowserOptionsSection {
                name: section_name.to_string(),
                state: "absent".to_string(),
                start: None,
                end: None,
                unknown_reason: None,
            };
            for item in &options.properties {
                let Some(property) = item.as_property() else {
                    state.state = "unknown".to_string();
                    state.unknown_reason = Some("top-level-spread".to_string());
                    self.public_names.retain(|name| {
                        name.origin != section_name || name.name_start < options_start
                    });
                    continue;
                };
                if property.computed {
                    state.state = "unknown".to_string();
                    state.unknown_reason = Some("computed-top-level-key".to_string());
                    self.public_names.retain(|name| {
                        name.origin != section_name || name.name_start < options_start
                    });
                    continue;
                }
                if !property.key.is_specific_static_name(section_name) {
                    continue;
                }
                self.public_names
                    .retain(|name| name.origin != section_name || name.name_start < options_start);
                if let (Some(start), Some(end)) = (state.start, state.end) {
                    self.member_references
                        .retain(|reference| reference.start < start || reference.end > end);
                }
                let span = property.span();
                state.start = Some(span.start as usize);
                state.end = Some(span.end as usize);
                state.unknown_reason = None;
                if let Some(object) = section_object(section_name, &property.value) {
                    state.state = "complete".to_string();
                    self.collect_section_names(section_name, object, &mut state);
                } else if section_name == "props" || section_name == "inject" {
                    if let Expression::ArrayExpression(array) = property.value.without_parentheses()
                    {
                        state.state = "complete".to_string();
                        for element in &array.elements {
                            let Some(expression) = element.as_expression() else {
                                state.state = "unknown".to_string();
                                state.unknown_reason = Some("non-literal-entry".to_string());
                                continue;
                            };
                            if let Expression::StringLiteral(literal) =
                                expression.without_parentheses()
                            {
                                let span = literal.span();
                                let authored = literal.value.to_string();
                                self.public_names.push(public_name(
                                    authored,
                                    section_name,
                                    span.start as usize,
                                    span.end as usize,
                                    None,
                                    None,
                                ));
                            } else {
                                state.state = "unknown".to_string();
                                state.unknown_reason = Some("non-literal-entry".to_string());
                            }
                        }
                    } else {
                        state.state = "unknown".to_string();
                        state.unknown_reason = Some("non-literal-section".to_string());
                    }
                } else {
                    state.state = "unknown".to_string();
                    state.unknown_reason = Some("indirect-section".to_string());
                }
                if matches!(section_name, "methods" | "computed" | "data") {
                    self.member_references
                        .extend(bound_instance_members(section_name, &property.value));
                }
            }
            self.sections.push(state);
        }
        // `mixins` and `extends` merge another options object into this one,
        // so any section can gain names this source does not show.
        let inherits = options.properties.iter().any(|item| {
            item.as_property().is_some_and(|property| {
                !property.computed
                    && (property.key.is_specific_static_name("mixins")
                        || property.key.is_specific_static_name("extends"))
            })
        });
        if inherits {
            for state in &mut self.sections {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("inherited-options".to_string());
            }
        }
        self.collect_emits(options, inherits);
        self.collect_directives(options, inherits);
        self.collect_inherit_attrs(options, inherits);
        // Vue also calls lifecycle hooks, `provide()`, and `watch` handlers
        // with `this` set to the instance, so their member reads are proven
        // too. Any other option is read by code Vue does not know, which may
        // call it with a different `this`, so its reads prove nothing.
        for item in &options.properties {
            let Some(property) = item.as_property() else {
                continue;
            };
            if property.computed {
                continue;
            }
            let Some(name) = property.key.static_name() else {
                continue;
            };
            if !INSTANCE_BOUND_OPTIONS.contains(&name.as_ref()) {
                continue;
            }
            self.member_references
                .extend(bound_hook_members(&name, &property.value));
        }
    }

    /// Read the `emits` section: an array of string literals or an object
    /// whose static keys name the events. Anything else leaves the declared
    /// events unknown, so a consumer must accept every event name.
    fn collect_emits(&mut self, options: &ObjectExpression<'_>, inherits: bool) {
        let (state, names) = read_named_option(options, inherits, "emits", true);
        if state.state == "complete" {
            self.emit_names
                .extend(names.into_iter().map(|(name, start, end)| BrowserEmitName {
                    name,
                    start,
                    end,
                }));
        }
        self.emits_sections.push(state);
    }

    /// Read the `directives` section: an object whose static keys name the
    /// custom directives Vue registers for this component. Anything else
    /// leaves them unknown, so a consumer must accept every directive name.
    fn collect_directives(&mut self, options: &ObjectExpression<'_>, inherits: bool) {
        let (state, names) = read_named_option(options, inherits, "directives", false);
        if state.state == "complete" {
            self.directive_names.extend(
                names
                    .into_iter()
                    .map(|(name, start, end)| BrowserDirectiveName { name, start, end }),
            );
        }
        self.directives_sections.push(state);
    }

    /// Read `inheritAttrs` as Vue sees it after merging the options object.
    ///
    /// The last own key wins, as in a JavaScript object literal. A spread or
    /// computed key after it may replace it, and with no own key a mixin or
    /// parent options object may set it, so those give `None`. With no key
    /// and nothing that could add one, Vue uses its default, `true`.
    fn collect_inherit_attrs(&mut self, options: &ObjectExpression<'_>, inherits: bool) {
        let mut value = Some(true);
        let mut own_key = false;
        for item in &options.properties {
            let Some(property) = item.as_property() else {
                value = None;
                continue;
            };
            if property.computed {
                value = None;
                continue;
            }
            if !property.key.is_specific_static_name("inheritAttrs") {
                continue;
            }
            own_key = true;
            // Only a literal proves the value; `inheritAttrs: flag` may be
            // either, so a consumer must allow both.
            value = match property.value.without_parentheses() {
                Expression::BooleanLiteral(literal) => Some(literal.value),
                _ => None,
            };
        }
        // Vue keeps a component's own `inheritAttrs` over a mixin's, so
        // inheritance only hides the value when the source sets none.
        if inherits && !own_key {
            value = None;
        }
        self.inherit_attrs.push(value);
    }

    fn collect_absent_options(&mut self) {
        for name in ["emits", "directives"] {
            let section = BrowserOptionsSection {
                name: name.to_owned(),
                state: "absent".to_owned(),
                start: None,
                end: None,
                unknown_reason: None,
            };
            if name == "emits" {
                self.emits_sections.push(section);
            } else {
                self.directives_sections.push(section);
            }
        }
        // A callback literal sets no options, so Vue's default applies.
        self.inherit_attrs.push(Some(true));
        for name in ["props", "methods", "computed", "inject", "data", "setup"] {
            self.sections.push(BrowserOptionsSection {
                name: name.to_owned(),
                state: "absent".to_owned(),
                start: None,
                end: None,
                unknown_reason: None,
            });
        }
    }

    fn collect_unknown_options(&mut self, span: oxc_span::Span) {
        let unknown = |name: &str| BrowserOptionsSection {
            name: name.to_owned(),
            state: "unknown".to_owned(),
            start: Some(span.start as usize),
            end: Some(span.end as usize),
            unknown_reason: Some("indirect-options".to_owned()),
        };
        self.emits_sections.push(unknown("emits"));
        self.directives_sections.push(unknown("directives"));
        self.inherit_attrs.push(None);
        for name in ["props", "methods", "computed", "inject", "data", "setup"] {
            self.sections.push(unknown(name));
        }
    }

    fn collect_section_names(
        &mut self,
        section_name: &str,
        object: &ObjectExpression<'_>,
        state: &mut BrowserOptionsSection,
    ) {
        for item in &object.properties {
            let Some(property) = item.as_property() else {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("object-spread".to_string());
                continue;
            };
            if property.computed {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("computed-key".to_string());
                continue;
            }
            let Some(name) = property.key.static_name() else {
                state.state = "unknown".to_string();
                state.unknown_reason = Some("dynamic-key".to_string());
                continue;
            };
            let key_span = property.key.span();
            let details = if section_name == "props" {
                prop_details(&property.value, self.source)
            } else {
                None
            };
            self.public_names.push(public_name(
                name.into_owned(),
                section_name,
                key_span.start as usize,
                key_span.end as usize,
                Some(property.value.span()),
                details,
            ));
        }
    }

    fn is_unresolved_identifier(&self, expression: &Expression<'_>, name: &str) -> bool {
        expression
            .get_identifier_reference()
            .is_some_and(|identifier| {
                identifier.name == name
                    && self
                        .scoping
                        .get_reference(identifier.reference_id())
                        .symbol_id()
                        .is_none()
            })
    }

    fn collect_initializer<'a>(&mut self, expression: &Expression<'a>, authenticate_context: bool) {
        match expression.without_parentheses() {
            Expression::ArrowFunctionExpression(function) => {
                self.collect_arrow(function, authenticate_context);
            }
            Expression::FunctionExpression(function) => {
                self.collect_function(function, authenticate_context);
            }
            Expression::ObjectExpression(object) => {
                for property in &object.properties {
                    let Some(property) = property.as_property() else {
                        continue;
                    };
                    // The runtime renames `init` (the 0.5.1 spelling) to
                    // `onServerRender`, so both receive the same context.
                    if property.key.is_specific_static_name("init")
                        || property.key.is_specific_static_name("onServerRender")
                    {
                        self.collect_initializer(&property.value, true);
                    }
                }
            }
            _ => {}
        }
    }

    fn collect_arrow<'a>(
        &mut self,
        function: &oxc_ast::ast::ArrowFunctionExpression<'a>,
        authenticate_context: bool,
    ) {
        let span = function.span();
        self.initializer_ranges
            .push((span.start as usize, span.end as usize));
        if authenticate_context {
            self.bindings
                .extend(component_context_bindings(&function.params));
        }
        if let Some((scope_name, scope_symbol)) = scope_parameter(&function.params) {
            let mut visitor = ScopeWriteVisitor::new(scope_name, scope_symbol, self.scoping);
            match &function.body {
                ArrowFunctionBody::FunctionBody(body) => visitor.visit_function_body(body),
                body => visitor.visit_expression(body.to_expression()),
            }
            visitor.discard_writes_after_rebind();
            self.scope_writes.extend(visitor.writes);
        }
    }

    fn collect_function<'a>(&mut self, function: &Function<'a>, authenticate_context: bool) {
        let span = function.span();
        self.initializer_ranges
            .push((span.start as usize, span.end as usize));
        if authenticate_context {
            self.bindings
                .extend(component_context_bindings(&function.params));
        }
        if let (Some((scope_name, scope_symbol)), Some(body)) =
            (scope_parameter(&function.params), &function.body)
        {
            let mut visitor = ScopeWriteVisitor::new(scope_name, scope_symbol, self.scoping);
            visitor.visit_function_body(body);
            visitor.discard_writes_after_rebind();
            self.scope_writes.extend(visitor.writes);
        }
    }
}

/// Every field the runtime puts on the `onServerRender` context (`runCallback`
/// in `citry/_vue/client.js`). A destructured name outside this list is not a
/// context value, so it gets no binding.
const COMPONENT_CONTEXT_NAMES: &[&str] = &[
    "component",
    "revision",
    "onEvent",
    "id",
    "els",
    "state",
    "sendEvent",
    "loading",
    "error",
    "i18n",
];

struct ComponentBindingCandidate {
    name: String,
    local_name: String,
    start: usize,
    end: usize,
    symbol_id: SymbolId,
}

fn component_context_bindings(params: &FormalParameters<'_>) -> Vec<ComponentBindingCandidate> {
    let Some(first) = params.items.first() else {
        return Vec::new();
    };
    let oxc_ast::ast::BindingPattern::ObjectPattern(pattern) = &first.pattern else {
        return Vec::new();
    };
    pattern
        .properties
        .iter()
        .filter_map(|property| {
            let name = property.key.static_name()?;
            if !COMPONENT_CONTEXT_NAMES.contains(&name.as_ref()) {
                return None;
            }
            let identifier = property.value.get_binding_identifier()?;
            let span = identifier.span();
            Some(ComponentBindingCandidate {
                name: name.into_owned(),
                local_name: identifier.name.to_string(),
                start: span.start as usize,
                end: span.end as usize,
                symbol_id: identifier.symbol_id(),
            })
        })
        .collect()
}

fn scope_parameter<'a>(params: &'a FormalParameters<'a>) -> Option<(&'a str, SymbolId)> {
    let first = params.items.first()?;
    let oxc_ast::ast::BindingPattern::ObjectPattern(pattern) = &first.pattern else {
        return None;
    };
    pattern.properties.iter().find_map(|property| {
        if !property.key.is_specific_static_name("scope") {
            return None;
        }
        let identifier = property.value.get_binding_identifier()?;
        Some((identifier.name.as_str(), identifier.symbol_id()))
    })
}

struct ScopeWriteVisitor<'name, 'semantic> {
    scope_name: &'name str,
    scope_symbol: SymbolId,
    scoping: &'semantic Scoping,
    rebound_at: Option<usize>,
    writes: Vec<BrowserScopeWrite>,
}

impl<'name, 'semantic> ScopeWriteVisitor<'name, 'semantic> {
    fn new(scope_name: &'name str, scope_symbol: SymbolId, scoping: &'semantic Scoping) -> Self {
        Self {
            scope_name,
            scope_symbol,
            scoping,
            rebound_at: None,
            writes: Vec::new(),
        }
    }

    fn is_scope_reference(&self, expression: &Expression<'_>) -> bool {
        expression
            .get_identifier_reference()
            .is_some_and(|identifier| self.identifier_is_scope(identifier))
    }

    fn identifier_is_scope(&self, identifier: &oxc_ast::ast::IdentifierReference<'_>) -> bool {
        identifier.name == self.scope_name
            && self
                .scoping
                .get_reference(identifier.reference_id())
                .symbol_id()
                == Some(self.scope_symbol)
    }

    fn discard_writes_after_rebind(&mut self) {
        if let Some(rebound_at) = self.rebound_at {
            self.writes.retain(|write| write.name_start < rebound_at);
        }
    }

    fn push_member_write(
        &mut self,
        member: &oxc_ast::ast::MemberExpression<'_>,
        value: &Expression<'_>,
    ) {
        if !self.is_scope_reference(member.object()) {
            return;
        }
        let Some((name_span, name)) = member.static_property_info() else {
            return;
        };
        let value_span = value.span();
        self.writes.push(BrowserScopeWrite {
            name: name.to_string(),
            name_start: name_span.start as usize,
            name_end: name_span.end as usize,
            value_start: value_span.start as usize,
            value_end: value_span.end as usize,
        });
    }

    fn collect_assign_object(&mut self, object: &ObjectExpression<'_>) {
        for property in &object.properties {
            let ObjectPropertyKind::ObjectProperty(property) = property else {
                continue;
            };
            let Some(name) = property.key.static_name() else {
                continue;
            };
            let name_span = property.key.span();
            let value_span = property.value.span();
            self.writes.push(BrowserScopeWrite {
                name: name.into_owned(),
                name_start: name_span.start as usize,
                name_end: name_span.end as usize,
                value_start: value_span.start as usize,
                value_end: value_span.end as usize,
            });
        }
    }
}

impl<'a> Visit<'a> for ScopeWriteVisitor<'_, '_> {
    fn visit_assignment_expression(&mut self, assignment: &AssignmentExpression<'a>) {
        if assignment.operator == AssignmentOperator::Assign {
            if let AssignmentTarget::AssignmentTargetIdentifier(identifier) = &assignment.left {
                if self.identifier_is_scope(identifier) {
                    let start = assignment.span.start as usize;
                    self.rebound_at =
                        Some(self.rebound_at.map_or(start, |current| current.min(start)));
                }
            }
            if let Some(member) = assignment
                .left
                .as_simple_assignment_target()
                .and_then(|target| target.as_member_expression())
            {
                self.push_member_write(member, &assignment.right);
            }
        }
        walk::walk_assignment_expression(self, assignment);
    }

    fn visit_call_expression(&mut self, call: &CallExpression<'a>) {
        if call.callee.is_specific_member_access("Object", "assign")
            && call
                .arguments
                .first()
                .and_then(Argument::as_expression)
                .is_some_and(|argument| self.is_scope_reference(argument))
        {
            if let Some(Expression::ObjectExpression(object)) =
                call.arguments.get(1).and_then(Argument::as_expression)
            {
                self.collect_assign_object(object);
            }
        }
        walk::walk_call_expression(self, call);
    }

    // Writes scheduled inside another function do not happen synchronously
    // during component initialization, so they cannot prove server bindings.
    fn visit_function(&mut self, _function: &Function<'a>, _flags: ScopeFlags) {}

    fn visit_arrow_function_expression(
        &mut self,
        _function: &oxc_ast::ast::ArrowFunctionExpression<'a>,
    ) {
    }
}

/// Read one options key whose value names things, such as `emits` or
/// `directives`, the way Vue merges the options object.
///
/// Returns the section's state and, for each name, the name and the byte
/// range of its key or string literal. A later key replaces an earlier one;
/// a spread or computed key may add or replace it until the next explicit
/// key; `mixins` or `extends` may add names. An object literal with static
/// keys is complete, and so is an array of string literals when
/// `accepts_array` is set. Any other value is unknown, with the reason.
fn read_named_option(
    options: &ObjectExpression<'_>,
    inherits: bool,
    key: &str,
    accepts_array: bool,
) -> (BrowserOptionsSection, Vec<(String, usize, usize)>) {
    let mut state = BrowserOptionsSection {
        name: key.to_string(),
        state: "absent".to_string(),
        start: None,
        end: None,
        unknown_reason: None,
    };
    let mut names = Vec::new();
    let mark_unknown = |state: &mut BrowserOptionsSection, reason: &str| {
        state.state = "unknown".to_string();
        state.unknown_reason = Some(reason.to_string());
    };
    for item in &options.properties {
        let Some(property) = item.as_property() else {
            mark_unknown(&mut state, "top-level-spread");
            names.clear();
            continue;
        };
        if property.computed {
            mark_unknown(&mut state, "computed-top-level-key");
            names.clear();
            continue;
        }
        if !property.key.is_specific_static_name(key) {
            continue;
        }
        names.clear();
        let span = property.span();
        state.start = Some(span.start as usize);
        state.end = Some(span.end as usize);
        state.state = "complete".to_string();
        state.unknown_reason = None;
        match property.value.without_parentheses() {
            Expression::ArrayExpression(array) if accepts_array => {
                for element in &array.elements {
                    match element.as_expression().map(Expression::without_parentheses) {
                        Some(Expression::StringLiteral(literal)) => {
                            let span = literal.span();
                            names.push((
                                literal.value.to_string(),
                                span.start as usize,
                                span.end as usize,
                            ));
                        }
                        _ => mark_unknown(&mut state, "non-literal-entry"),
                    }
                }
            }
            Expression::ObjectExpression(object) => {
                for entry in &object.properties {
                    let Some(entry) = entry.as_property() else {
                        mark_unknown(&mut state, "object-spread");
                        continue;
                    };
                    let name = if entry.computed {
                        None
                    } else {
                        entry.key.static_name()
                    };
                    let Some(name) = name else {
                        mark_unknown(&mut state, "computed-key");
                        continue;
                    };
                    let span = entry.key.span();
                    names.push((name.into_owned(), span.start as usize, span.end as usize));
                }
            }
            _ => mark_unknown(&mut state, "non-literal-section"),
        }
    }
    if inherits {
        mark_unknown(&mut state, "inherited-options");
    }
    if state.state != "complete" {
        names.clear();
    }
    (state, names)
}

fn section_object<'a>(
    section: &str,
    value: &'a Expression<'a>,
) -> Option<&'a ObjectExpression<'a>> {
    if section != "data" && section != "setup" {
        return match value.without_parentheses() {
            Expression::ObjectExpression(object) => Some(object),
            _ => None,
        };
    }
    match value.without_parentheses() {
        Expression::ArrowFunctionExpression(function) => match &function.body {
            ArrowFunctionBody::FunctionBody(body) => direct_return_object(&body.statements),
            body => match body.to_expression().without_parentheses() {
                Expression::ObjectExpression(object) => Some(object),
                _ => None,
            },
        },
        Expression::FunctionExpression(function) => function
            .body
            .as_ref()
            .and_then(|body| direct_return_object(&body.statements)),
        _ => None,
    }
}

fn direct_return_object<'a>(
    statements: &'a oxc_allocator::Vec<'a, oxc_ast::ast::Statement<'a>>,
) -> Option<&'a ObjectExpression<'a>> {
    if statements.len() != 1 {
        return None;
    }
    let oxc_ast::ast::Statement::ReturnStatement(statement) = &statements[0] else {
        return None;
    };
    match statement.argument.as_ref()?.without_parentheses() {
        Expression::ObjectExpression(object) => Some(object),
        _ => None,
    }
}

fn public_name(
    authored_name: String,
    origin: &str,
    name_start: usize,
    name_end: usize,
    value_span: Option<oxc_span::Span>,
    prop_details: Option<(bool, bool, bool, Option<String>)>,
) -> BrowserPublicName {
    let exposed_name = if origin == "props" {
        camelize_prop(&authored_name)
    } else {
        authored_name.clone()
    };
    BrowserPublicName {
        authored_name,
        exposed_name,
        origin: origin.to_string(),
        name_start,
        name_end,
        value_start: value_span.map(|span| span.start as usize),
        value_end: value_span.map(|span| span.end as usize),
        required: prop_details.as_ref().map(|details| details.0),
        has_default: prop_details.as_ref().map(|details| details.1),
        default_is_null: prop_details.as_ref().map(|details| details.2),
        type_source: prop_details.and_then(|details| details.3),
    }
}

fn prop_details(
    value: &Expression<'_>,
    source: &str,
) -> Option<(bool, bool, bool, Option<String>)> {
    let Expression::ObjectExpression(object) = value.without_parentheses() else {
        return Some((
            false,
            false,
            false,
            Some(source[value.span().start as usize..value.span().end as usize].to_string()),
        ));
    };
    let mut required = false;
    let mut has_default = false;
    let mut default_is_null = false;
    let mut type_source = None;
    for item in &object.properties {
        let property = item.as_property()?;
        if property.computed || property.key.static_name().is_none() {
            return None;
        }
        if property.key.is_specific_static_name("required") {
            required = matches!(property.value.without_parentheses(), Expression::BooleanLiteral(value) if value.value);
        } else if property.key.is_specific_static_name("default") {
            has_default = true;
            default_is_null = matches!(
                property.value.without_parentheses(),
                Expression::NullLiteral(_)
            );
        } else if property.key.is_specific_static_name("type") {
            let span = property.value.span();
            type_source = Some(source[span.start as usize..span.end as usize].to_string());
        }
    }
    Some((required, has_default, default_is_null, type_source))
}

fn camelize_prop(name: &str) -> String {
    let mut result = String::with_capacity(name.len());
    let mut characters = name.chars().peekable();
    while let Some(character) = characters.next() {
        if character == '-'
            && characters
                .peek()
                .is_some_and(|next| next.is_ascii_alphanumeric() || *next == '_')
        {
            result.push(characters.next().unwrap().to_ascii_uppercase());
        } else {
            result.push(character);
        }
    }
    result
}

fn bound_instance_members(
    section: &str,
    value: &Expression<'_>,
) -> Vec<BrowserComponentMemberReference> {
    let mut visitor = InstanceMemberVisitor::default();
    match (section, value.without_parentheses()) {
        ("methods" | "computed", Expression::ObjectExpression(object)) => {
            for item in &object.properties {
                let Some(property) = item.as_property() else {
                    continue;
                };
                if matches!(
                    property.value.without_parentheses(),
                    Expression::FunctionExpression(_)
                ) {
                    visitor.visit_expression(&property.value);
                } else if section == "computed" {
                    if let Expression::ObjectExpression(descriptor) =
                        property.value.without_parentheses()
                    {
                        for descriptor_item in &descriptor.properties {
                            let Some(descriptor_property) = descriptor_item.as_property() else {
                                continue;
                            };
                            if !descriptor_property.computed
                                && (descriptor_property.key.is_specific_static_name("get")
                                    || descriptor_property.key.is_specific_static_name("set"))
                                && matches!(
                                    descriptor_property.value.without_parentheses(),
                                    Expression::FunctionExpression(_)
                                )
                            {
                                visitor.visit_expression(&descriptor_property.value);
                            }
                        }
                    }
                }
            }
        }
        ("data", Expression::FunctionExpression(_)) => visitor.visit_expression(value),
        _ => {}
    }
    visitor.references
}

/// Options Vue calls with `this` set to the component instance, apart from
/// the `methods`, `computed` and `data` sections handled with their names.
const INSTANCE_BOUND_OPTIONS: [&str; 16] = [
    "beforeCreate",
    "created",
    "beforeMount",
    "mounted",
    "beforeUpdate",
    "updated",
    "beforeUnmount",
    "unmounted",
    "activated",
    "deactivated",
    "errorCaptured",
    "renderTracked",
    "renderTriggered",
    "serverPrefetch",
    "provide",
    "watch",
];

fn bound_hook_members(name: &str, value: &Expression<'_>) -> Vec<BrowserComponentMemberReference> {
    let mut visitor = InstanceMemberVisitor::default();
    match value.without_parentheses() {
        Expression::FunctionExpression(_) => visitor.visit_expression(value),
        Expression::ObjectExpression(object) if name == "watch" => {
            for item in &object.properties {
                let Some(property) = item.as_property() else {
                    continue;
                };
                match property.value.without_parentheses() {
                    Expression::FunctionExpression(_) => visitor.visit_expression(&property.value),
                    // `{ handler() {...}, deep: true }` keeps its handler bound.
                    Expression::ObjectExpression(descriptor) => {
                        for descriptor_item in &descriptor.properties {
                            let Some(descriptor_property) = descriptor_item.as_property() else {
                                continue;
                            };
                            if !descriptor_property.computed
                                && descriptor_property.key.is_specific_static_name("handler")
                                && matches!(
                                    descriptor_property.value.without_parentheses(),
                                    Expression::FunctionExpression(_)
                                )
                            {
                                visitor.visit_expression(&descriptor_property.value);
                            }
                        }
                    }
                    _ => {}
                }
            }
        }
        _ => {}
    }
    visitor.references
}

/// Collect the property ranges of static member expressions that the code
/// writes, so the matching member references can be marked as writes.
///
/// OXC gives every write target the `SimpleAssignmentTarget` type: the left
/// side of an assignment, each target inside a destructuring assignment, the
/// operand of `++` or `--`, and the left side of `for ... in` or `for ... of`.
/// So visiting that type, and nothing else, finds every write.
#[derive(Default)]
struct MemberWriteTargetVisitor {
    property_spans: Vec<(usize, usize)>,
}

impl<'a> Visit<'a> for MemberWriteTargetVisitor {
    fn visit_simple_assignment_target(&mut self, target: &SimpleAssignmentTarget<'a>) {
        if let Some((span, _name)) = target
            .as_member_expression()
            .and_then(|member| member.static_property_info())
        {
            self.property_spans
                .push((span.start as usize, span.end as usize));
        }
        walk::walk_simple_assignment_target(self, target);
    }
}

#[derive(Default)]
struct InstanceMemberVisitor {
    ordinary_function_depth: usize,
    references: Vec<BrowserComponentMemberReference>,
}

struct AliasMemberVisitor<'symbols, 'semantic> {
    scoping: &'semantic Scoping,
    component_symbols: &'symbols [SymbolId],
    references: Vec<BrowserComponentMemberReference>,
}

impl<'a> Visit<'a> for AliasMemberVisitor<'_, '_> {
    fn visit_static_member_expression(
        &mut self,
        member: &oxc_ast::ast::StaticMemberExpression<'a>,
    ) {
        if let Some(identifier) = member.object.get_identifier_reference() {
            let symbol = self
                .scoping
                .get_reference(identifier.reference_id())
                .symbol_id();
            if symbol.is_some_and(|symbol| self.component_symbols.contains(&symbol)) {
                let span = member.property.span();
                self.references.push(BrowserComponentMemberReference {
                    receiver: "component".to_string(),
                    name: member.property.name.to_string(),
                    start: span.start as usize,
                    end: span.end as usize,
                    // Set for write targets once every reference is collected.
                    written: false,
                });
            }
        }
        walk::walk_static_member_expression(self, member);
    }
}

/// Find local variables that hold a proven `$i18n` member.
///
/// A variable qualifies when its declaration is a plain identifier whose
/// initializer is exactly `receiver.$i18n` for an already proven receiver, and
/// nothing assigns or redeclares it afterwards. A `let` or `var` that is never
/// reassigned or redeclared holds the same service as a `const`, so all three
/// count.
/// Destructuring, optional chaining, computed keys, and a variable copied from
/// another variable are not followed; their calls are not preloaded.
struct I18nAliasVisitor<'members, 'semantic> {
    scoping: &'semantic Scoping,
    // Proven member reads. Only a `$i18n` property span in this list may
    // start an alias, so an alias inherits the receiver proof those reads have.
    members: &'members [BrowserComponentMemberReference],
    // The aliased member's receiver and the variable's symbol.
    aliases: Vec<(String, SymbolId)>,
}

impl<'a> Visit<'a> for I18nAliasVisitor<'_, '_> {
    fn visit_variable_declarator(&mut self, declarator: &VariableDeclarator<'a>) {
        let alias = match (
            &declarator.id,
            declarator
                .init
                .as_ref()
                .map(Expression::without_parentheses),
        ) {
            (
                oxc_ast::ast::BindingPattern::BindingIdentifier(identifier),
                Some(Expression::StaticMemberExpression(member)),
            ) if member.property.name == "$i18n" => {
                let span = member.property.span;
                self.members
                    .iter()
                    .find(|reference| {
                        reference.name == "$i18n"
                            && reference.start == span.start as usize
                            && reference.end == span.end as usize
                    })
                    .map(|reference| (reference.receiver.clone(), identifier.symbol_id()))
            }
            _ => None,
        };
        // A later assignment or a second `var` declaration could replace the
        // service before a call runs, so such a variable proves nothing.
        if let Some((receiver, symbol)) = alias {
            if !self.scoping.symbol_is_mutated(symbol)
                && self.scoping.symbol_redeclarations(symbol).is_empty()
            {
                self.aliases.push((receiver, symbol));
            }
        }
        walk::walk_variable_declarator(self, declarator);
    }
}

impl<'a> Visit<'a> for InstanceMemberVisitor {
    fn visit_function(&mut self, function: &Function<'a>, flags: ScopeFlags) {
        self.ordinary_function_depth += 1;
        if self.ordinary_function_depth == 1 {
            walk::walk_function(self, function, flags);
        }
        self.ordinary_function_depth -= 1;
    }

    fn visit_static_member_expression(
        &mut self,
        member: &oxc_ast::ast::StaticMemberExpression<'a>,
    ) {
        if self.ordinary_function_depth <= 1
            && matches!(
                member.object.without_parentheses(),
                Expression::ThisExpression(_)
            )
        {
            let span = member.property.span();
            self.references.push(BrowserComponentMemberReference {
                receiver: "this".to_string(),
                name: member.property.name.to_string(),
                start: span.start as usize,
                end: span.end as usize,
                // Set for write targets once every reference is collected.
                written: false,
            });
        }
        walk::walk_static_member_expression(self, member);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn expression_analysis_reports_only_free_identifiers() {
        let source = "items.map((item) => item.name + suffix)";
        let analysis = analyze_browser_source(source, BrowserAnalysisMode::Expression);

        assert!(analysis.valid);
        assert_eq!(
            analysis.references,
            vec![
                BrowserReference {
                    name: "items".to_string(),
                    start: 0,
                    end: 5,
                    written: false,
                },
                BrowserReference {
                    name: "suffix".to_string(),
                    start: 32,
                    end: 38,
                    written: false,
                },
            ]
        );
    }

    #[test]
    fn statement_analysis_resolves_local_declarations() {
        let source = "const local = source; target = local";
        let analysis = analyze_browser_source(source, BrowserAnalysisMode::Statement);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["source", "target"]
        );
    }

    #[test]
    fn invalid_source_never_returns_partial_references() {
        let analysis = analyze_browser_source("value(", BrowserAnalysisMode::Expression);

        assert!(!analysis.valid);
        assert!(analysis.error.is_some());
        assert!(analysis.references.is_empty());
    }

    fn syntax_error(source: &str, mode: BrowserAnalysisMode) -> (String, usize, usize) {
        let analysis = analyze_browser_source(source, mode);
        assert!(!analysis.valid, "{source:?} should be invalid");
        assert!(analysis.references.is_empty());
        let error = analysis.error.expect("an invalid source carries its error");
        (error.message, error.start, error.end)
    }

    #[test]
    fn syntax_errors_describe_the_authored_text() {
        use BrowserAnalysisMode::{Expression, Statement};
        // Observed from OXC 0.143.0 and locked; offsets are UTF-8 bytes in
        // the authored text, and an error at its end is an empty range there.
        let unexpected = "Unexpected token";
        for (source, mode, message, start, end) in [
            ("open &&", Expression, unexpected, 7, 7),
            ("a +* b", Expression, unexpected, 3, 4),
            ("foo(", Expression, "Expected `)` but found `EOF`", 4, 4),
            ("{ a: }", Expression, unexpected, 5, 6),
            ("x =", Expression, unexpected, 3, 3),
            ("items.map(i =>", Expression, unexpected, 14, 14),
            ("'unclosed", Expression, "Unterminated string", 0, 9),
            ("a)", Expression, unexpected, 1, 2),
            ("(a))", Expression, unexpected, 3, 4),
            ("a\n)", Expression, unexpected, 2, 3),
            ("a }", Statement, unexpected, 2, 3),
            ("open &amp;&amp; ready", Expression, unexpected, 9, 10),
            ("   ", Expression, unexpected, 3, 3),
            ("function() {}", Statement, "Expected function name", 8, 9),
            // `é` is two bytes, so the `*` after `café +` starts at byte 7.
            ("café +* b", Expression, unexpected, 7, 8),
            // The scope pass reports a second declaration at the second one.
            (
                "let a = 1; let a = 2",
                Statement,
                "Identifier `a` has already been declared",
                15,
                16,
            ),
        ] {
            assert_eq!(
                syntax_error(source, mode),
                (message.to_string(), start, end),
                "{source:?} in {mode:?} mode"
            );
        }
    }

    #[test]
    fn text_that_closes_the_generated_function_is_invalid() {
        use BrowserAnalysisMode::{Expression, Statement};
        // Each of these parses inside the generated wrapper by closing it and
        // opening another statement or argument, which Vue rejects.
        for (source, mode, message, start, end) in [
            ("a); (b", Expression, "Unexpected token", 1, 2),
            (
                "a); (b",
                Statement,
                "Expected a semicolon or an implicit semicolon after a statement, but found none",
                1,
                1,
            ),
            ("a), (b", Expression, "Unexpected token", 1, 2),
            ("a } function g() {", Expression, "Unexpected token", 2, 3),
            ("a } function g() {", Statement, "Unexpected token", 2, 3),
        ] {
            assert_eq!(
                syntax_error(source, mode),
                (message.to_string(), start, end),
                "{source:?} in {mode:?} mode"
            );
        }
        for (source, mode) in [
            ("await load()", Expression),
            ("await load()", Statement),
            ("return 1", Statement),
            ("() => go()", Statement),
            ("", Statement),
            ("value // trailing comment", Expression),
        ] {
            let analysis = analyze_browser_source(source, mode);
            assert!(analysis.valid, "{source:?} in {mode:?} mode");
            assert_eq!(analysis.error, None);
        }
    }

    #[test]
    fn free_references_report_whether_the_code_writes_the_name() {
        let source = "open += 1; count++; --other; [a, b] = pair; ({c, d: e} = obj); \
            for (f of list) {}; g.count = 1; h == 1; i = false";
        let analysis = analyze_browser_source(source, BrowserAnalysisMode::Statement);
        assert!(analysis.valid);
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|reference| (reference.name.as_str(), reference.written))
                .collect::<Vec<_>>(),
            [
                ("open", true),
                ("count", true),
                ("other", true),
                ("a", true),
                ("b", true),
                ("pair", false),
                ("c", true),
                ("e", true),
                ("obj", false),
                ("f", true),
                ("list", false),
                ("g", false),
                ("h", false),
                ("i", true),
            ]
        );
        // A comment before `=` still writes the name, and `--count` on the
        // next line updates `count`, not `open`.
        for (source, expected) in [
            ("open /* note */ = false", vec![("open", true)]),
            ("open\n--count", vec![("open", false), ("count", true)]),
        ] {
            let analysis = analyze_browser_source(source, BrowserAnalysisMode::Statement);
            assert_eq!(
                analysis
                    .references
                    .iter()
                    .map(|reference| (reference.name.as_str(), reference.written))
                    .collect::<Vec<_>>(),
                expected,
                "{source:?}"
            );
        }
        let expression = analyze_browser_source("open = false", BrowserAnalysisMode::Expression);
        assert!(expression.valid);
        assert!(expression.references[0].written);
    }

    #[test]
    fn binding_pattern_reports_nested_bindings_and_initializer_references() {
        let source = "{ item: local = fallback, nested: [first, ...rest], [key]: computed }";
        let analysis = analyze_browser_binding_pattern(source);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|item| item.name.as_str())
                .collect::<Vec<_>>(),
            ["local", "first", "rest", "computed"]
        );
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|item| item.name.as_str())
                .collect::<Vec<_>>(),
            ["fallback", "key"]
        );
        for item in analysis.bindings.iter().chain(&analysis.references) {
            assert_eq!(
                &source.as_bytes()[item.start..item.end],
                item.name.as_bytes()
            );
        }
    }

    #[test]
    fn binding_pattern_offsets_are_authored_utf8_bytes_and_invalid_is_empty() {
        let source = "{ café: résumé = fallback }";
        let analysis = analyze_browser_binding_pattern(source);
        assert!(analysis.valid);
        assert_eq!(analysis.bindings[0].name, "résumé");
        assert_eq!(
            &source.as_bytes()[analysis.bindings[0].start..analysis.bindings[0].end],
            "résumé".as_bytes()
        );
        assert_eq!(analysis.references[0].name, "fallback");

        let invalid = analyze_browser_binding_pattern("{ item:");
        assert!(!invalid.valid);
        assert!(invalid.bindings.is_empty());
        assert!(invalid.references.is_empty());

        for escaped in ["x) => {}; (y", "x) => ((y"] {
            let escaped = analyze_browser_binding_pattern(escaped);
            assert!(!escaped.valid);
            assert!(escaped.bindings.is_empty());
            assert!(escaped.references.is_empty());
        }
    }

    #[test]
    fn binding_pattern_accepts_vue_parameter_lists_and_top_level_rest() {
        let parameters = analyze_browser_binding_pattern("x, y = fallback");
        assert!(parameters.valid);
        assert_eq!(
            parameters
                .bindings
                .iter()
                .map(|item| item.name.as_str())
                .collect::<Vec<_>>(),
            ["x", "y"]
        );
        assert_eq!(parameters.references[0].name, "fallback");

        let rest = analyze_browser_binding_pattern("...args");
        assert!(rest.valid);
        assert_eq!(rest.bindings[0].name, "args");
        assert!(rest.references.is_empty());

        let empty = analyze_browser_binding_pattern("");
        assert!(empty.valid);
        assert!(empty.bindings.is_empty());
        assert!(empty.references.is_empty());

        for classic_name in ["await", "yield", "eval", "arguments"] {
            let classic = analyze_browser_binding_pattern(classic_name);
            assert!(classic.valid, "classic Vue parameter {classic_name}");
            assert_eq!(classic.bindings[0].name, classic_name);
        }
    }

    #[test]
    fn component_analysis_reports_context_bindings_and_only_initializer_free_names() {
        let source = r#"
const outside = missingOutside;
$component({ onServerRender({ component: current, revision, onEvent: listen, data }) {
  const local = data.title;
  current.ready = local;
  listen("cart:changed", detail => console.log(revision, detail, missingInside));
} });
"#;

        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| (binding.name.as_str(), binding.local_name.as_str()))
                .collect::<Vec<_>>(),
            [
                ("component", "current"),
                ("revision", "revision"),
                ("onEvent", "listen"),
            ]
        );
        assert!(analysis
            .bindings
            .iter()
            .all(|binding| binding.references.len() == 1));
        assert_eq!(
            analysis
                .references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["console", "missingInside"]
        );
    }

    #[test]
    fn shadowed_component_helpers_do_not_create_initializer_facts() {
        let source = r#"
const $component = (callback) => callback({});
$component(({ scope }) => { console.log(scope, missing); });
"#;

        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert!(analysis.references.is_empty());
        assert!(analysis.bindings.is_empty());
    }

    #[test]
    fn component_options_report_authenticated_calls_sections_and_public_names() {
        let source = r#"const prefix = 1;
$component /* kept */ ({
  props: ["display-name", "count"],
  methods: { save() {}, ...extraMethods },
  computed: { total() { return this.$i18n.locale.length } },
  inject: { service: "service" },
  data() { return { ready: true } },
  setup: () => ({ selected: prefix }),
});"#;
        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert_eq!(analysis.component_calls.len(), 1);
        let call = &analysis.component_calls[0];
        assert_eq!(&source[call.callee_start..call.callee_end], "$component");
        assert_eq!(&source[call.open_paren_end - 1..call.open_paren_end], "(");
        assert_eq!(
            analysis
                .public_names
                .iter()
                .map(|name| (name.origin.as_str(), name.exposed_name.as_str()))
                .collect::<Vec<_>>(),
            [
                ("props", "displayName"),
                ("props", "count"),
                ("methods", "save"),
                ("computed", "total"),
                ("inject", "service"),
                ("data", "ready"),
                ("setup", "selected"),
            ]
        );
        assert_eq!(
            analysis
                .sections
                .iter()
                .find(|section| section.name == "methods")
                .map(|section| (section.state.as_str(), section.unknown_reason.as_deref())),
            Some(("unknown", Some("object-spread")))
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| (reference.receiver.as_str(), reference.name.as_str()))
                .collect::<Vec<_>>(),
            [("this", "$i18n")]
        );
    }

    fn emits_facts(source: &str) -> (Vec<(String, Option<String>)>, Vec<String>) {
        let analysis = analyze_component_source(source);
        assert!(analysis.valid);
        (
            analysis
                .emits_sections
                .iter()
                .map(|section| (section.state.clone(), section.unknown_reason.clone()))
                .collect(),
            analysis
                .emit_names
                .iter()
                .map(|name| source[name.start..name.end].to_string())
                .collect(),
        )
    }

    #[test]
    fn emits_sections_report_declared_event_names() {
        let complete = |names: &[&str]| {
            (
                vec![("complete".to_string(), None)],
                names
                    .iter()
                    .map(|name| (*name).to_string())
                    .collect::<Vec<_>>(),
            )
        };
        assert_eq!(
            emits_facts("$component({ emits: ['drop-task', \"open\"] })"),
            complete(&["'drop-task'", "\"open\""])
        );
        assert_eq!(
            emits_facts(
                "$component({ emits: { 'drop-task'(id) { return true }, open: null, [key]: null } })"
            ),
            (
                vec![("unknown".to_string(), Some("computed-key".to_string()))],
                Vec::new()
            )
        );
        assert_eq!(
            emits_facts("$component({ emits: { 'drop-task': (id) => true, open: null } })"),
            complete(&["'drop-task'", "open"])
        );
        // A later explicit `emits` replaces an earlier spread's contribution.
        assert_eq!(
            emits_facts("$component({ ...base, emits: ['a'] })"),
            complete(&["'a'"])
        );
        for (source, reason) in [
            ("$component({ emits: names })", "non-literal-section"),
            ("$component({ emits: ['a', name] })", "non-literal-entry"),
            ("$component({ emits: ['a'], ...more })", "top-level-spread"),
            ("$component({ emits: { ...base } })", "object-spread"),
            (
                "$component({ emits: ['a'], mixins: [shared] })",
                "inherited-options",
            ),
            ("$component(options)", "indirect-options"),
        ] {
            assert_eq!(
                emits_facts(source),
                (
                    vec![("unknown".to_string(), Some(reason.to_string()))],
                    Vec::new()
                ),
                "{source}"
            );
        }
        for source in [
            "$component({ data() { return {} } })",
            "$component(({ component }) => {})",
        ] {
            assert_eq!(
                emits_facts(source),
                (vec![("absent".to_string(), None)], Vec::new()),
                "{source}"
            );
        }
    }

    #[test]
    fn emit_calls_on_the_instance_are_member_references() {
        let source = "$component({ methods: { m() { this.$emit('a', 1) } }, \
            onServerRender({ component }) { component.$emit('b') } })";
        let analysis = analyze_component_source(source);
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| (
                    reference.receiver.as_str(),
                    &source[reference.start..reference.end]
                ))
                .collect::<Vec<_>>(),
            [("this", "$emit"), ("component", "$emit")]
        );
    }

    #[test]
    fn later_top_level_spread_invalidates_sections_until_explicitly_restored() {
        let analysis = analyze_component_source(
            "$component({ props: { first: Number }, ...other, props: { final: Number } })",
        );
        let props = analysis
            .sections
            .iter()
            .find(|section| section.name == "props")
            .unwrap();
        assert_eq!(props.state, "complete");
        assert_eq!(
            analysis
                .public_names
                .iter()
                .filter(|name| name.origin == "props")
                .map(|name| name.authored_name.as_str())
                .collect::<Vec<_>>(),
            ["final"]
        );
    }

    #[test]
    fn computed_top_level_key_invalidates_every_earlier_section() {
        let analysis = analyze_component_source(
            "$component({ props: { first: Number }, methods: { save() {} }, [section]: replacement })",
        );
        assert!(analysis.public_names.is_empty());
        assert!(analysis.sections.iter().all(|section| {
            section.state == "unknown"
                && section.unknown_reason.as_deref() == Some("computed-top-level-key")
        }));
    }

    #[test]
    fn prop_descriptor_dynamic_members_keep_name_but_invalidate_details() {
        for source in [
            "$component({ props: { value: { type: String, ...details } } })",
            "$component({ props: { value: { type: String, [key]: option } } })",
        ] {
            let analysis = analyze_component_source(source);
            let value = analysis
                .public_names
                .iter()
                .find(|name| name.authored_name == "value")
                .unwrap();
            assert_eq!(
                (
                    value.required,
                    value.has_default,
                    value.type_source.as_deref()
                ),
                (None, None, None)
            );
        }
    }

    #[test]
    fn vue_prop_camelization_preserves_repeated_hyphen() {
        let analysis = analyze_component_source(
            "$component({ props: ['foo--bar', 'foo-_bar', 'plain_name'] })",
        );
        assert_eq!(
            analysis
                .public_names
                .iter()
                .map(|name| name.exposed_name.as_str())
                .collect::<Vec<_>>(),
            ["foo-Bar", "foo_bar", "plain_name"]
        );
    }

    #[test]
    fn indirect_options_keep_every_namespace_unknown() {
        let analysis = analyze_component_source("$component(options)");

        assert!(analysis.public_names.is_empty());
        assert!(analysis.sections.iter().all(|section| {
            section.state == "unknown"
                && section.unknown_reason.as_deref() == Some("indirect-options")
        }));
    }

    #[test]
    fn callback_literals_declare_no_options_names() {
        for source in [
            "$component(({ component }) => { component.ready })",
            "$component(function ({ component }) { component.ready })",
        ] {
            let analysis = analyze_component_source(source);

            assert!(analysis.public_names.is_empty());
            assert_eq!(analysis.sections.len(), 6);
            assert!(analysis
                .sections
                .iter()
                .all(|section| section.state == "absent" && section.unknown_reason.is_none()));
            assert_eq!(analysis.member_references.len(), 1);
        }
    }

    #[test]
    fn duplicate_sections_keep_only_the_effective_names_and_member_references() {
        let analysis = analyze_component_source(
            "$component({ methods: { old() { return this.oldValue } }, methods: { current() { return this.currentValue } } })",
        );

        assert_eq!(
            analysis
                .public_names
                .iter()
                .map(|name| name.authored_name.as_str())
                .collect::<Vec<_>>(),
            ["current"]
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["currentValue"]
        );
    }

    #[test]
    fn this_is_authenticated_only_in_vue_bound_options_functions() {
        let analysis = analyze_component_source(
            "$component({ setup() { return { value: this.setupValue } }, onServerRender() { return this.serverValue }, computed: { doubled: { get() { return this.getValue }, set(value) { this.setValue = value } } } })",
        );

        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["getValue", "setValue"]
        );
    }

    #[test]
    fn lifecycle_hooks_and_watch_handlers_bind_this() {
        let analysis = analyze_component_source(
            "$component({ mounted() { const i = this.$i18n; i.tr('m'); this.hookValue }, provide() { return { p: this.provided } }, watch: { a() { this.watchValue }, b: { handler() { this.handlerValue }, deep: true } }, emits: ['x'] })",
        );

        let mut names = analysis
            .member_references
            .iter()
            .map(|reference| reference.name.as_str())
            .collect::<Vec<_>>();
        names.sort_unstable();
        assert_eq!(
            names,
            [
                "$i18n",
                "$i18n",
                "handlerValue",
                "hookValue",
                "provided",
                "watchValue"
            ]
        );
    }

    #[test]
    fn only_options_vue_calls_on_the_instance_bind_this() {
        let analysis = analyze_component_source(
            "$component({ asyncData() { this.custom }, customOption: function () { this.other }, created() { this.known } })",
        );

        let names = analysis
            .member_references
            .iter()
            .map(|reference| reference.name.as_str())
            .collect::<Vec<_>>();
        assert_eq!(names, ["known"]);
    }

    #[test]
    fn mixins_and_extends_leave_every_section_unknown() {
        for source in [
            "$component({ mixins: [shared], methods: { m() {} } })",
            "$component({ extends: base, methods: { m() {} } })",
        ] {
            let analysis = analyze_component_source(source);
            assert!(analysis.valid);
            assert!(analysis.sections.iter().all(|section| {
                section.state == "unknown"
                    && section.unknown_reason.as_deref() == Some("inherited-options")
            }));
        }
    }

    #[test]
    fn restored_context_fields_are_bindings_and_unknown_names_are_not() {
        let source = r#"$component({ init({ id, els: roots, state, sendEvent: send, loading, error, i18n, scope, data }) {
  send("save", { id, count: roots.length, state, busy: loading(), failed: error(), i18n, scope, data });
} });"#;
        let analysis = analyze_component_source(source);

        assert!(analysis.valid);
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| (
                    binding.name.as_str(),
                    binding.local_name.as_str(),
                    binding.references.len()
                ))
                .collect::<Vec<_>>(),
            [
                ("id", "id", 1),
                ("els", "roots", 1),
                ("state", "state", 1),
                ("sendEvent", "send", 1),
                ("loading", "loading", 1),
                ("error", "error", 1),
                ("i18n", "i18n", 1),
            ]
        );
    }

    #[test]
    fn init_and_on_server_render_authenticate_context_aliases() {
        let analysis = analyze_component_source(
            "$component({ init({ onEvent: ignored }) { ignored(\"init\", () => {}); } }); $component({ onServerRender({ component: direct, onEvent: listen }) { direct.x; listen(\"server\", () => {}); } }); $component({ onServerRender({ component: current }) { current.z } })",
        );
        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| binding.local_name.as_str())
                .collect::<Vec<_>>(),
            ["ignored", "direct", "listen", "current"]
        );
    }

    #[test]
    fn i18n_alias_reads_are_reported_as_i18n_members() {
        let source = r#"$component({
  onServerRender: ({ component: e }) => {
    const t = e.$el, i = e.$i18n;
    i.bind({});
    let j = (e.$i18n);
    j?.tr("a");
    var v = e.$i18n;
    v.tr("b");
    { const e = other; const k = e.$i18n; k.bind({}); }
  },
  methods: { run() { const m = this.$i18n; return m.tr("c"); } },
})"#;
        let analysis = analyze_component_source(source);

        let found = analysis
            .member_references
            .iter()
            .filter(|reference| reference.name == "$i18n")
            .map(|reference| {
                (
                    reference.receiver.as_str(),
                    &source[reference.start..reference.end],
                )
            })
            .collect::<Vec<_>>();
        // Each variable is reported at the `$i18n` read in its initializer and
        // at every later read of the variable; the alias of a shadowing `e` is
        // not.
        assert_eq!(
            found,
            [
                ("component", "$i18n"),
                ("component", "i"),
                ("component", "$i18n"),
                ("component", "j"),
                ("component", "$i18n"),
                ("component", "v"),
                ("this", "$i18n"),
                ("this", "m"),
            ]
        );
    }

    #[test]
    fn i18n_alias_is_not_followed_in_unsupported_forms() {
        let source = r#"$component({
  onServerRender: ({ component }) => {
    let a = component.$i18n;
    a = other;
    a.bind({});
    var b = component.$i18n;
    var b = other;
    b.bind({});
    const { bind } = component.$i18n;
    bind({});
    const c = component?.$i18n;
    c.bind({});
    const d = component["$i18n"];
    d.bind({});
    const f = component.$i18n;
    const g = f;
    g.bind({});
  },
})"#;
        let analysis = analyze_component_source(source);

        let found = analysis
            .member_references
            .iter()
            .filter(|reference| reference.name == "$i18n")
            .map(|reference| &source[reference.start..reference.end])
            .collect::<Vec<_>>();
        // Only the member reads themselves remain proven. The one alias read
        // is `f` copied into `g`; `g.bind` is not followed.
        assert_eq!(found, ["$i18n", "$i18n", "$i18n", "$i18n", "$i18n", "f"]);
    }

    #[test]
    fn server_callback_component_alias_members_are_scope_authenticated() {
        let analysis = analyze_component_source(
            "$component({ onServerRender({ component: instance, revision, onEvent: subscribe }) { instance.$i18n.resolve(revision); { const instance = other; instance.$i18n; } } })",
        );

        assert_eq!(
            analysis
                .bindings
                .iter()
                .map(|binding| (binding.name.as_str(), binding.local_name.as_str()))
                .collect::<Vec<_>>(),
            [
                ("component", "instance"),
                ("revision", "revision"),
                ("onEvent", "subscribe"),
            ]
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| (reference.receiver.as_str(), reference.name.as_str()))
                .collect::<Vec<_>>(),
            [("component", "$i18n")]
        );
    }

    #[test]
    fn options_this_and_helper_selection_follow_javascript_scope() {
        let source = r#"
const $component = value => value;
$component({ methods: { fake() { return this.$i18n } } });
if (enabled) globalThis.$component({ methods: { property() { return this.$i18n } } });
if (enabled) realComponent({});
"#;
        let shadowed = analyze_component_source(source);
        assert!(shadowed.component_calls.is_empty());
        assert!(shadowed.member_references.is_empty());

        let source = r#"if (enabled) $component({
  props: { "naïve-name": { type: String } },
  data: () => ({ lexical: this.$i18n }),
  methods: {
    regular() { (() => this.$i18n)(); function nested() { return this.$i18n } },
  },
});"#;
        let analysis = analyze_component_source(source);
        assert_eq!(analysis.component_calls.len(), 1);
        assert_eq!(
            analysis
                .public_names
                .iter()
                .find(|name| name.origin == "props")
                .map(|name| name.exposed_name.as_str()),
            Some("naïveName")
        );
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| reference.name.as_str())
                .collect::<Vec<_>>(),
            ["$i18n"]
        );
    }

    #[test]
    fn member_references_report_whether_the_code_writes_the_member() {
        let source = "$component({ props: ['open'], methods: { m() { this.open = false; \
            this.open.count = 1; this.open++; [this.open] = pair; ({ a: this.open } = obj); \
            for (this.open of list) {} this.other == 1; } }, \
            onServerRender({ component: c }) { c.open = 1; c.open.x = 2; c.read; } })";
        let analysis = analyze_component_source(source);
        assert!(analysis.valid);
        assert_eq!(
            analysis
                .member_references
                .iter()
                .map(|reference| (
                    reference.receiver.as_str(),
                    reference.name.as_str(),
                    reference.written
                ))
                .collect::<Vec<_>>(),
            [
                ("this", "open", true),
                ("this", "open", false),
                ("this", "open", true),
                ("this", "open", true),
                ("this", "open", true),
                ("this", "open", true),
                ("this", "other", false),
                ("component", "open", true),
                ("component", "open", false),
                ("component", "read", false),
            ]
        );
        // The free names the destructuring reads are not writes.
        assert!(analysis
            .references
            .iter()
            .all(|reference| !reference.written));
    }

    fn directives_facts(source: &str) -> (Vec<(String, Option<String>)>, Vec<String>) {
        let analysis = analyze_component_source(source);
        assert!(analysis.valid);
        (
            analysis
                .directives_sections
                .iter()
                .map(|section| (section.state.clone(), section.unknown_reason.clone()))
                .collect(),
            analysis
                .directive_names
                .iter()
                .map(|name| {
                    assert!(source[name.start..name.end].contains(&name.name));
                    name.name.clone()
                })
                .collect(),
        )
    }

    #[test]
    fn directives_sections_report_declared_directive_names() {
        let complete = |names: &[&str]| {
            (
                vec![("complete".to_string(), None)],
                names
                    .iter()
                    .map(|name| (*name).to_string())
                    .collect::<Vec<_>>(),
            )
        };
        assert_eq!(
            directives_facts("$component({ directives: { iff: {}, 'my-dir': {}, focus } })"),
            complete(&["iff", "my-dir", "focus"])
        );
        // A later key replaces an earlier one, and an explicit key after a
        // spread is what Vue sees.
        assert_eq!(
            directives_facts("$component({ directives: { a: {} }, directives: { b: {} } })"),
            complete(&["b"])
        );
        assert_eq!(
            directives_facts("$component({ ...base, directives: { a: {} } })"),
            complete(&["a"])
        );
        for (source, reason) in [
            ("$component({ directives: { ...base } })", "object-spread"),
            ("$component({ directives: { [k]: {} } })", "computed-key"),
            ("$component({ directives: names })", "non-literal-section"),
            ("$component({ directives: ['a'] })", "non-literal-section"),
            (
                "$component({ directives: { a: {} }, ...more })",
                "top-level-spread",
            ),
            (
                "$component({ directives: { a: {} }, [key]: value })",
                "computed-top-level-key",
            ),
            (
                "$component({ mixins: [m], directives: { a: {} } })",
                "inherited-options",
            ),
            (
                "$component({ extends: base, directives: { a: {} } })",
                "inherited-options",
            ),
            ("$component(options)", "indirect-options"),
        ] {
            assert_eq!(
                directives_facts(source),
                (
                    vec![("unknown".to_string(), Some(reason.to_string()))],
                    Vec::new()
                ),
                "{source}"
            );
        }
        for source in [
            "$component({ data() { return {} } })",
            "$component(() => {})",
        ] {
            assert_eq!(
                directives_facts(source),
                (vec![("absent".to_string(), None)], Vec::new()),
                "{source}"
            );
        }
        // A call with no options argument contributes no entry at all.
        assert_eq!(directives_facts("$component()"), (Vec::new(), Vec::new()));
    }

    #[test]
    fn inherit_attrs_is_known_only_when_the_source_proves_it() {
        for (source, expected) in [
            ("$component({ inheritAttrs: false })", vec![Some(false)]),
            ("$component({ inheritAttrs: true })", vec![Some(true)]),
            // Vue's default when nothing sets it.
            ("$component({ data() { return {} } })", vec![Some(true)]),
            ("$component(() => {})", vec![Some(true)]),
            ("$component({ inheritAttrs: flag })", vec![None]),
            ("$component({ inheritAttrs: false, ...more })", vec![None]),
            (
                "$component({ inheritAttrs: false, [key]: value })",
                vec![None],
            ),
            (
                "$component({ ...more, inheritAttrs: false })",
                vec![Some(false)],
            ),
            (
                "$component({ inheritAttrs: false, inheritAttrs: true })",
                vec![Some(true)],
            ),
            // A component's own key wins over a mixin's; without one, a mixin
            // or parent options object may set it.
            (
                "$component({ mixins: [m], inheritAttrs: false })",
                vec![Some(false)],
            ),
            ("$component({ mixins: [m] })", vec![None]),
            ("$component({ extends: base })", vec![None]),
            ("$component(options)", vec![None]),
            ("$component()", Vec::new()),
            (
                "$component({ inheritAttrs: false }); $component({})",
                vec![Some(false), Some(true)],
            ),
        ] {
            assert_eq!(
                analyze_component_source(source).inherit_attrs,
                expected,
                "{source}"
            );
        }
    }

    #[test]
    fn records_repr_like_python_objects() {
        let analysis = analyze_browser_source("open = 1", BrowserAnalysisMode::Statement);
        assert_eq!(
            analysis.py_repr(),
            "BrowserAnalysis(valid=True, error=None, references=[BrowserReference(name=\"open\", start=0, end=4, written=True)])"
        );
        let invalid = analyze_browser_source("a +* b", BrowserAnalysisMode::Expression);
        assert_eq!(
            invalid.error.unwrap().py_repr(),
            "BrowserSyntaxDiagnostic(message=\"Unexpected token\", start=3, end=4)"
        );
    }
}
