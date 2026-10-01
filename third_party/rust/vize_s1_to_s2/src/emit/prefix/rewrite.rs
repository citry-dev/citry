//! `rewrite_expression` (`steps::expression::rewrite` + `reparse` +
//! `retained_rewrite`), ported for the no-binding, non-TS lane: the
//! retained AST drives a span splice when the dialect gate admits it;
//! everything else re-parses through the legacy chain — wrapped
//! expression parse, whole-program parse, simple-identifier fallback —
//! whose byte behavior is the shipped lane's.

use oxc_ast::ast::Expression;
use oxc_ast_visit::Visit;
use oxc_parser::Parser;
use oxc_span::{GetSpan, SourceType};
use vize_s0::expression_guard::{expression_exceeds_max_depth, expression_has_balanced_delimiters};
use vize_s0::{Allocator, String};

use super::collector::IdentifierCollector;
use super::compat::js_module_compatible;
use super::globals::{is_generated_filter_helper, is_simple_identifier};
use super::scope::PrefixScope;
use super::splice::splice_insertions;
use super::strip_typescript_from_expression;

/// A retained AST beside the text it describes: `ast` was parsed from
/// `text[offset..offset + len]`, so its spans shift by `offset`.
#[derive(Clone, Copy)]
pub(super) struct Retained<'r, 'a> {
    pub(super) ast: &'r Expression<'a>,
    pub(super) source: &'a str,
    pub(super) offset: usize,
}

pub(super) struct RewriteResult {
    pub(super) code: String,
    /// Set when a binding was read through `_unref(…)`; the emit marks
    /// that helper once, after the body, the way the shipped lane appends
    /// it after every used helper.
    pub(super) used_unref: bool,
    /// The shipped lane reports `X_INVALID_EXPRESSION` here; the emit
    /// refuses instead (the diagnostic is not recoverable, so the corpus
    /// lane never compares such a template).
    pub(super) parse_error: bool,
}

fn js_module() -> SourceType {
    SourceType::default().with_module(true)
}

fn ts_module() -> SourceType {
    SourceType::ts().with_module(true)
}

/// `as_raw_statements` mirrors the fourth argument of `@vue/compiler-core`'s
/// `processExpression`: only an event handler whose text contains `;` may be
/// read as a list of statements. Everywhere else a statement is a parse
/// error, so the emitter refuses it and the `vize_atelier_core` fallback reports
/// the diagnostic instead of writing the statement into a position that only
/// accepts an expression.
pub(super) fn rewrite_expression(
    content: &str,
    retained: Option<Retained<'_, '_>>,
    scope: &PrefixScope<'_>,
    as_params: bool,
    as_raw_statements: bool,
) -> RewriteResult {
    if !as_params
        && let Some(js) = retained
        && js_module_compatible(js.ast, js.source)
    {
        if !scope.is_ts() {
            return project_aliases(rewrite_retained(content, js, scope), scope);
        }
        // TS lanes strip first, always: the detection scan can false-positive
        // on TS-free text (` as ` inside a string literal) and rewrite bytes
        // through the codegen round-trip. Only the identity outcome keeps the
        // retained byte proof; changed bytes rejoin the legacy chain.
        let js_content = strip_typescript_from_expression(content);
        if js_content.as_str() == content {
            return project_aliases(rewrite_retained(content, js, scope), scope);
        }
        return project_aliases(
            rewrite_reparsed(js_content, content, retained, scope, as_raw_statements),
            scope,
        );
    }
    let overflows = expression_exceeds_max_depth(content);
    if overflows || !expression_has_balanced_delimiters(content) {
        return RewriteResult {
            code: String::from(content),
            used_unref: false,
            parse_error: !overflows,
        };
    }
    let js_content = if scope.is_ts() {
        strip_typescript_from_expression(content)
    } else {
        String::from(content)
    };
    if as_params {
        // The original text is re-checked as TypeScript: the official
        // compiler accepts params the stripping fallback could not lower.
        let accepted = parses_as_params(js_content.as_str(), js_module())
            || (scope.is_ts() && parses_as_params(content, ts_module()));
        return RewriteResult {
            code: js_content,
            used_unref: false,
            parse_error: !accepted,
        };
    }
    project_aliases(
        rewrite_reparsed(js_content, content, retained, scope, as_raw_statements),
        scope,
    )
}

/// The transform's `rewrite_props_aliases` post-pass over both prop
/// objects; a parse failure passes the raw text through untouched.
fn project_aliases(result: RewriteResult, scope: &PrefixScope<'_>) -> RewriteResult {
    if result.parse_error {
        return result;
    }
    RewriteResult {
        code: super::aliases::rewrite_props_aliases(
            result.code,
            scope.bindings(),
            &["__props", "$props"],
        ),
        used_unref: result.used_unref,
        parse_error: false,
    }
}

fn rewrite_retained(
    content: &str,
    retained: Retained<'_, '_>,
    scope: &PrefixScope<'_>,
) -> RewriteResult {
    let mut collector = IdentifierCollector::new_unwrapped(scope, content, retained.offset);
    collector.visit_expression(retained.ast);
    let used_unref = collector.used_unref;
    let code = splice_insertions(content, collector.rewrites, collector.suffix_rewrites, 0);
    RewriteResult {
        code,
        used_unref,
        parse_error: false,
    }
}

/// The legacy re-parse chain over already-stripped text. `original` is
/// the pre-strip text, read only by the TS-acceptance check; a retained
/// AST that passed the dialect gate already proves the original parses as
/// TypeScript, so it short-circuits that check.
fn rewrite_reparsed(
    js_content: String,
    original: &str,
    retained: Option<Retained<'_, '_>>,
    scope: &PrefixScope<'_>,
    as_raw_statements: bool,
) -> RewriteResult {
    let content = js_content.as_str();
    let allocator = Allocator::new();
    let mut wrapped = String::with_capacity(content.len() + 2);
    wrapped.push('(');
    wrapped.push_str(content);
    wrapped.push(')');
    if let Ok(expr) =
        Parser::new(allocator.as_oxc(), wrapped.as_str(), js_module()).parse_expression()
    {
        let mut collector = IdentifierCollector::new(scope, wrapped.as_str());
        collector.visit_expression(&expr);
        let used_unref = collector.used_unref;
        let code = splice_insertions(content, collector.rewrites, collector.suffix_rewrites, 1);
        return RewriteResult {
            code,
            used_unref,
            parse_error: false,
        };
    }

    // The whole-program parse is for multi-statement handlers only; every
    // other caller wraps the text as an expression, where a statement would
    // be emitted as invalid JavaScript.
    let program_allocator = Allocator::new();
    let parsed = as_raw_statements
        .then(|| Parser::new(program_allocator.as_oxc(), content, js_module()).parse())
        .filter(|parsed| parsed.diagnostics.is_empty());
    if let Some(parsed) = parsed {
        let mut collector = IdentifierCollector::new(scope, content);
        collector.visit_program(&parsed.program);
        let used_unref = collector.used_unref;
        let code = splice_insertions(content, collector.rewrites, collector.suffix_rewrites, 0);
        return RewriteResult {
            code,
            used_unref,
            parse_error: false,
        };
    }

    if is_simple_identifier(content) {
        if is_generated_filter_helper(content) {
            return RewriteResult {
                code: String::from(content),
                used_unref: false,
                parse_error: false,
            };
        }
        // The same three-way read the collector makes: prefix, `.value`
        // for an inline ref, `_unref(…)` for an inline `let`.
        let needs_unref = scope.needs_unref(content);
        let code = match scope.identifier_prefix(content) {
            Some(prefix) => {
                let mut code = String::with_capacity(prefix.len() + content.len());
                code.push_str(prefix);
                code.push_str(content);
                code
            }
            None if scope.is_ref_binding(content) => {
                let mut code = String::with_capacity(content.len() + 6);
                code.push_str(content);
                code.push_str(".value");
                code
            }
            None if needs_unref => {
                let mut code = String::with_capacity(content.len() + 8);
                code.push_str("_unref(");
                code.push_str(content);
                code.push(')');
                code
            }
            None => String::from(content),
        };
        return RewriteResult {
            code,
            used_unref: needs_unref,
            parse_error: false,
        };
    }
    let ts_accepts = scope.is_ts()
        && (retained.is_some_and(|js| js_module_compatible(js.ast, js.source))
            || parses_as_typescript(original, as_raw_statements));
    RewriteResult {
        code: js_content,
        used_unref: false,
        parse_error: !ts_accepts,
    }
}

/// `parse_checks::parse_as_params`: the synthesized `(content) => null` parse.
fn parses_as_params(content: &str, source_type: SourceType) -> bool {
    let allocator = Allocator::new();
    let mut wrapped = String::with_capacity(content.len() + 12);
    wrapped.push('(');
    wrapped.push_str(content);
    wrapped.push_str(") => null");
    Parser::new(allocator.as_oxc(), wrapped.as_str(), source_type)
        .parse_expression()
        .is_ok()
}

/// `parse_checks::parses_as_typescript`: the wrapped expression parse, then
/// (only when `as_raw_statements` allows a list of statements) the
/// whole-program parse, both as TypeScript.
fn parses_as_typescript(content: &str, as_raw_statements: bool) -> bool {
    let expr_allocator = Allocator::new();
    let mut wrapped = String::with_capacity(content.len() + 2);
    wrapped.push('(');
    wrapped.push_str(content);
    wrapped.push(')');
    if Parser::new(expr_allocator.as_oxc(), wrapped.as_str(), ts_module())
        .parse_expression()
        .is_ok()
    {
        return true;
    }
    if !as_raw_statements {
        return false;
    }
    let program_allocator = Allocator::new();
    Parser::new(program_allocator.as_oxc(), content, ts_module())
        .parse()
        .diagnostics
        .is_empty()
}

/// `Parser::parse_expression` over the bare text, admitted only when that
/// one expression is the whole text (trailing comments aside), so `a; b()`
/// is not read as the reference `a` or `() => a(); b()` as a function.
pub(super) fn with_whole_expression_parse<T>(
    content: &str,
    decide: impl FnOnce(&Expression<'_>) -> T,
) -> Option<T> {
    if !vize_s0::expression_guard::expression_is_safe_to_parse(content) {
        return None;
    }
    let allocator = Allocator::new();
    Parser::new(allocator.as_oxc(), content, js_module())
        .parse_expression()
        .ok()
        .filter(|expr| only_trailing_trivia(&content[expr.span().end as usize..]))
        .map(|expr| decide(&expr))
}

/// Whether `rest` holds only whitespace and comments. `Parser::parse_expression`
/// stops after one complete expression without checking that the input ended,
/// so the shape checks call this on the text after the parsed expression:
/// `foo; bar()` must not read as the handler reference `foo`, or the whole
/// text is emitted where only that reference is valid.
fn only_trailing_trivia(rest: &str) -> bool {
    let mut rest = rest.trim_start();
    while !rest.is_empty() {
        if let Some(line) = rest.strip_prefix("//") {
            // JavaScript ends a line comment at any of its four line terminators.
            rest = line
                .find(['\n', '\r', '\u{2028}', '\u{2029}'])
                .map_or("", |end| &line[end..]);
        } else if let Some(block) = rest.strip_prefix("/*") {
            let Some(end) = block.find("*/") else {
                return false;
            };
            rest = &block[end + 2..];
        } else {
            return false;
        }
        rest = rest.trim_start();
    }
    true
}
