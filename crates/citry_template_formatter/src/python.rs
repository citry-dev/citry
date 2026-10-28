//! Validated formatting adapters for Citry's Python expression regions.
//!
//! Ruff formats Python modules, but a Citry template holds bare fragments: the
//! inside of `{{ ... }}`, or the clause of a `c-for`. Each adapter wraps the
//! fragment in the smallest valid Python that makes it a module, formats that,
//! then extracts the fragment back out.
//!
//! Nothing Ruff returns is trusted on its word. The result is reparsed and its
//! syntax tree compared with the original, and the Python comments are
//! fingerprinted on both sides, so a provider that quietly rewrites meaning is
//! rejected instead of written to the file. The pinned identity below is part of
//! the contract: change it and the corpus's expected bytes change with it.

use python_safe_eval::nesting::check_nesting;
use python_safe_eval::parse_expression;
use ruff_formatter::{IndentWidth, LineWidth, printer::LineEnding};
use ruff_python_ast::{
    PythonVersion,
    comparable::ComparableExpr,
    token::{TokenKind, Tokens},
};
use ruff_python_formatter::{PyFormatOptions, QuoteStyle, format_module_ast};
use ruff_python_parser::{Mode, ParseOptions, parse};
use ruff_python_trivia::{CommentRanges, SuppressionKind, TriviaRanges};

use crate::error::FormatError;
use crate::newline::normalize_to_lf;

/// Wraps a bare expression as `x((<expr>))` so Ruff sees a module. The call
/// parentheses also give it somewhere to break long lines.
const EXPRESSION_WRAPPER: &str = "x";

/// The stack the formatter's Python passes can need for one expression.
///
/// Ruff's formatter and the syntax-tree comparisons call themselves once per
/// tree level, with larger frames than python_safe_eval's passes. At the
/// deepest expressions the template parser accepts, a debug build needed up to
/// about 560 KiB (measured on macOS arm64; about 13 KB per `lambda` in a chain
/// of 29 of them), more than a small thread has. 4 MiB leaves a wide margin.
const STACK_RED_ZONE: usize = 4 * 1024 * 1024;

/// The size of a new stack segment, twice the red zone.
const STACK_SEGMENT: usize = 8 * 1024 * 1024;

/// Run `work` with enough stack for the passes over one expression.
///
/// When less than the red zone is left, `stacker` runs the work on a new
/// segment taken from the heap. The work is pure Rust, so running it off the
/// thread's own stack is safe.
pub(crate) fn with_enough_stack<T>(work: impl FnOnce() -> T) -> T {
    stacker::maybe_grow(STACK_RED_ZONE, STACK_SEGMENT, work)
}
/// Turns a `c-for` clause into a comprehension, the only Python construct where
/// `item in items` is valid on its own.
const CLAUSE_PREFIX: &str = "None for ";

/// Stable identity for the Python formatter pinned by this workspace.
pub const PYTHON_PROVIDER_IDENTITY: &str = "ruff@0.16.6+22f65a2ab5";

/// An authored expression as Citry's template parser reads it.
///
/// The parser wraps each expression in `(\n...\n)` before parsing it, so an
/// author may write an expression that is valid only inside parentheses, such
/// as a `{{ ... }}` whose `a if b` and `else c` parts sit on separate lines, or
/// `{{ x for x in items }}`. Each parse of an authored `{{ ... }}` or attribute
/// expression in this crate uses this text, so the formatter accepts what
/// Citry accepts. A `c-for` clause already has its own wrapper (see
/// `CLAUSE_PREFIX`) and must not be wrapped again, or its nesting count would
/// pass the parser's limit.
///
/// The parentheses add no node to the syntax tree. They are still tokens, so a
/// comment at either end of the expression is anchored to them; the text
/// before and after formatting is parsed the same way so those anchors match.
pub(crate) fn wrap_authored_expression(source: &str) -> String {
    format!("(\n{source}\n)")
}

pub(crate) fn format_expression(
    source: &str,
    available_width: usize,
    newline: &str,
) -> Result<String, FormatError> {
    with_enough_stack(|| format_expression_on_stack(source, available_width, newline))
}

fn format_expression_on_stack(
    source: &str,
    available_width: usize,
    newline: &str,
) -> Result<String, FormatError> {
    format_parsed_expression(source, available_width, newline, wrap_authored_expression)
}

/// Format `source`, and parse `parse_text(source)` and `parse_text(formatted)`
/// for the checks before and after.
///
/// An authored expression is parsed inside `(\n...\n)`, as the template
/// parser does. A `c-for` clause arrives already wrapped as a generator, so
/// it is parsed as it is.
fn format_parsed_expression(
    source: &str,
    available_width: usize,
    newline: &str,
    parse_text: fn(&str) -> String,
) -> Result<String, FormatError> {
    let before_source = parse_text(source);
    let before = parse_expression(&before_source).map_err(|error| {
        FormatError::invariant(format!(
            "Citry accepted a Python expression that the formatter provider rejected: {error}"
        ))
    })?;
    let before_comments = comment_fingerprint(&before_source, before.tokens());
    // A `# fmt: skip` inside the expression is the author telling Ruff to leave
    // it alone, so return the region untouched rather than formatting it and
    // then failing a comparison.
    if has_provider_suppression(&before_source, before.tokens()) {
        return Ok(source.to_string());
    }
    let wrapped = format!("{EXPRESSION_WRAPPER}(({newline}{source}{newline})){newline}");
    // Ruff measures the wrapped text, so the budget is widened by the wrapper it
    // will strip. Without this the expression would be wrapped earlier than the
    // template's own width calls for.
    let wrapper_width = available_width
        .saturating_add(EXPRESSION_WRAPPER.len() + 1)
        .clamp(1, u16::MAX as usize);
    let options = PyFormatOptions::default()
        .with_target_version(PythonVersion::PY310)
        .with_indent_width(IndentWidth::try_from(2).expect("valid Citry indent width"))
        .with_quote_style(QuoteStyle::Preserve)
        .with_line_ending(line_ending(newline))
        .with_line_width(
            LineWidth::try_from(wrapper_width as u16).expect("clamped valid line width"),
        );
    let parsed_wrapper = parse(
        &wrapped,
        ParseOptions::from(Mode::Module).with_target_version(PythonVersion::PY310),
    )
    .map_err(|error| {
        FormatError::invariant(format!(
            "Python expression wrapper failed to parse: {error}"
        ))
    })?;
    // Ruff 0.16.6 gives the formatter comments and other protected trivia in
    // one index, so every non-code range participates in attachment decisions.
    let wrapper_trivia = TriviaRanges::from(parsed_wrapper.tokens());
    let formatted_document = format_module_ast(&parsed_wrapper, &wrapper_trivia, &wrapped, options)
        .map_err(|error| FormatError::invariant(format!("Python provider failed: {error}")))?;
    let printed = formatted_document
        .print()
        .map_err(|error| FormatError::invariant(format!("Python provider failed: {error}")))?;
    let formatted = extract_wrapped_expression(printed.as_code(), newline)?;
    // Ruff may add parentheses. They add no tree level, but the depth check
    // counts each bracket, so they raise the depth bound. Near the limit that
    // could make the template parser, which checks the text as `parse_text`
    // builds it, refuse the formatted template, so the author's text is kept
    // as it is.
    let after_source = parse_text(&formatted);
    if check_nesting(&after_source).is_err() {
        return Ok(source.to_string());
    }
    let after = parse_expression(&after_source).map_err(|error| {
        FormatError::invariant(format!(
            "Python expression provider returned invalid syntax: {error}"
        ))
    })?;
    // Compare syntax trees, not text: reformatting is expected to move bytes
    // around, but the expression has to still mean the same thing. This is the
    // check that would catch a provider bug rewriting `a or b` into something
    // subtly different.
    if ComparableExpr::from(before.syntax().body.as_ref())
        != ComparableExpr::from(after.syntax().body.as_ref())
    {
        return Err(FormatError::invariant(
            "Python expression provider changed the expression syntax tree",
        ));
    }
    if before_comments != comment_fingerprint(&after_source, after.tokens()) {
        return Err(FormatError::invariant(
            "Python expression provider changed Python comments",
        ));
    }
    Ok(formatted)
}

pub(crate) fn expression_is_provider_suppressed(source: &str) -> bool {
    let wrapped = wrap_authored_expression(source);
    parse_expression(&wrapped)
        .is_ok_and(|parsed| has_provider_suppression(&wrapped, parsed.tokens()))
}

pub(crate) fn for_clause_is_provider_suppressed(source: &str, newline: &str) -> bool {
    let wrapped = format!("({CLAUSE_PREFIX}{source}{newline})");
    parse_expression(&wrapped)
        .is_ok_and(|parsed| has_provider_suppression(&wrapped, parsed.tokens()))
}

pub(crate) fn format_for_clause(
    source: &str,
    available_width: usize,
    newline: &str,
) -> Result<String, FormatError> {
    with_enough_stack(|| format_for_clause_on_stack(source, available_width, newline))
}

fn format_for_clause_on_stack(
    source: &str,
    available_width: usize,
    newline: &str,
) -> Result<String, FormatError> {
    let before_source = format!("({CLAUSE_PREFIX}{source}{newline})");
    let before = parse_expression(&before_source).map_err(|error| {
        FormatError::invariant(format!(
            "Citry accepted a c-for clause that the formatter provider rejected: {error}"
        ))
    })?;
    let before_comments = comment_fingerprint(&before_source, before.tokens());
    // The clause is already wrapped as a generator, so it is parsed as it is.
    let formatted_generator =
        format_parsed_expression(&before_source, available_width, newline, str::to_string)?;
    let formatted = extract_for_clause(&formatted_generator)?;
    let after_source = format!("({CLAUSE_PREFIX}{formatted}\n)");
    // The template parser checks a clause wrapped exactly like this, so a
    // formatted clause past its depth limit keeps the author's text.
    if check_nesting(&after_source).is_err() {
        return Ok(source.to_string());
    }
    let after = parse_expression(&after_source).map_err(|error| {
        FormatError::invariant(format!(
            "Python expression provider returned an invalid c-for clause: {error}"
        ))
    })?;
    if ComparableExpr::from(before.syntax().body.as_ref())
        != ComparableExpr::from(after.syntax().body.as_ref())
    {
        return Err(FormatError::invariant(
            "Python expression provider changed the c-for syntax tree",
        ));
    }
    if before_comments != comment_fingerprint(&after_source, after.tokens()) {
        return Err(FormatError::invariant(
            "Python expression provider changed c-for comments",
        ));
    }
    Ok(formatted)
}

fn extract_for_clause(formatted: &str) -> Result<String, FormatError> {
    let parsed = parse_expression(formatted).map_err(|error| {
        FormatError::invariant(format!(
            "Python expression provider returned an invalid c-for wrapper: {error}"
        ))
    })?;
    let first_for = parsed
        .tokens()
        .iter()
        .find(|token| token.kind() == TokenKind::For)
        .ok_or_else(|| FormatError::invariant("Python provider removed the c-for keyword"))?;
    let generator_close = parsed
        .tokens()
        .iter()
        .rev()
        .find(|token| token.kind() == TokenKind::Rpar)
        .ok_or_else(|| FormatError::invariant("Python provider removed the c-for close"))?;
    let start = first_for.as_tuple().1.end().to_usize();
    let end = generator_close.as_tuple().1.start().to_usize();
    let clause = formatted.get(start..end).ok_or_else(|| {
        FormatError::invariant("Python provider returned invalid c-for token ranges")
    })?;
    Ok(clause.trim().to_string())
}

fn extract_wrapped_expression(formatted: &str, newline: &str) -> Result<String, FormatError> {
    let prefix = format!("{EXPRESSION_WRAPPER}(");
    let body = formatted
        .strip_prefix(&prefix)
        .and_then(|value| value.strip_suffix(&format!("){newline}")))
        .ok_or_else(|| {
            FormatError::invariant("Python expression provider changed its wrapper structure")
        })?;
    let body = dedent_wrapper_body(body);
    let trimmed = body.trim();
    let without_artificial_parens = trimmed
        .strip_prefix('(')
        .and_then(|value| value.strip_suffix(')'))
        .map(dedent_wrapper_body)
        .map(|candidate| candidate.trim().to_string())
        .filter(|candidate| parse_expression(candidate).is_ok());
    Ok(without_artificial_parens.unwrap_or_else(|| body.trim().to_string()))
}

fn dedent_wrapper_body(source: &str) -> String {
    let normalized = normalize_to_lf(source);
    let trimmed = normalized.trim_matches('\n');
    let common_indent = trimmed
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| line.len() - line.trim_start_matches([' ', '\t']).len())
        .min()
        .unwrap_or(0);
    trimmed
        .lines()
        .map(|line| line.get(common_indent..).unwrap_or(line))
        .collect::<Vec<_>>()
        .join("\n")
}

#[derive(Debug, PartialEq, Eq)]
struct CommentFingerprint {
    payload: String,
    previous: Option<String>,
    previous_same_line: bool,
    next: Option<String>,
}

fn comment_fingerprint(source: &str, tokens: &Tokens) -> Vec<CommentFingerprint> {
    CommentRanges::from(tokens)
        .iter()
        .filter_map(|range| {
            let index = tokens.iter().position(|token| {
                token.kind() == TokenKind::Comment && token.as_tuple().1 == *range
            })?;
            let previous = tokens[..index]
                .iter()
                .rev()
                .find(|token| is_anchor_token(token.kind()));
            let next = tokens[index + 1..]
                .iter()
                .find(|token| is_anchor_token(token.kind()));
            let comment = &source[range.start().to_usize()..range.end().to_usize()];
            let previous_same_line = previous.is_some_and(|token| {
                let token_range = token.as_tuple().1;
                !source[token_range.end().to_usize()..range.start().to_usize()]
                    .contains(['\n', '\r'])
            });
            Some(CommentFingerprint {
                payload: comment
                    .strip_prefix('#')
                    .unwrap_or(comment)
                    .trim()
                    .to_string(),
                previous: previous.map(|token| token_fingerprint(source, token)),
                previous_same_line,
                next: next.map(|token| token_fingerprint(source, token)),
            })
        })
        .collect()
}

fn has_provider_suppression(source: &str, tokens: &Tokens) -> bool {
    CommentRanges::from(tokens).iter().any(|range| {
        SuppressionKind::from_comment(&source[range.start().to_usize()..range.end().to_usize()])
            .is_some()
    })
}

fn line_ending(newline: &str) -> LineEnding {
    match newline {
        "\r\n" => LineEnding::CarriageReturnLineFeed,
        "\r" => LineEnding::CarriageReturn,
        _ => LineEnding::LineFeed,
    }
}

fn is_anchor_token(kind: TokenKind) -> bool {
    !matches!(
        kind,
        TokenKind::Comment
            | TokenKind::Newline
            | TokenKind::NonLogicalNewline
            | TokenKind::Indent
            | TokenKind::Dedent
            | TokenKind::EndOfFile
    )
}

fn token_fingerprint(source: &str, token: &ruff_python_ast::token::Token) -> String {
    let (kind, range) = token.as_tuple();
    format!(
        "{kind:?}:{}",
        &source[range.start().to_usize()..range.end().to_usize()]
    )
}

#[cfg(test)]
mod tests {
    use super::{PYTHON_PROVIDER_IDENTITY, format_expression, format_for_clause};

    #[test]
    fn provider_identity_matches_the_vendored_ruff_release() {
        let manifest = include_str!("../../../third_party/rust/ruff/crates/ruff/Cargo.toml");
        assert!(manifest.contains("version = \"0.16.6\""));
        assert_eq!(PYTHON_PROVIDER_IDENTITY, "ruff@0.16.6+22f65a2ab5");
    }

    #[test]
    fn formats_an_expression_split_across_lines_without_parentheses() {
        // The template parser accepts this, because it reads each expression
        // inside `(\n...\n)`, so the formatter must accept it too.
        let source = "first if a\nelse second if b\nelse third";
        assert_eq!(
            format_expression(source, 100, "\n").unwrap(),
            "first if a else second if b else third"
        );
        // Too long for one line, so Ruff adds the parentheses itself.
        assert_eq!(
            format_expression(source, 20, "\n").unwrap(),
            "(\n  first\n  if a\n  else second\n  if b\n  else third\n)"
        );
        // Other forms that are valid only inside parentheses.
        for (form, formatted) in [
            ("x  for x in y", "(x for x in y)"),
            ("x  := 1", "(x := 1)"),
            ("*a,  b", "(*a, b)"),
        ] {
            assert_eq!(format_expression(form, 100, "\n").unwrap(), formatted);
        }
        assert!(!super::expression_is_provider_suppressed(source));
        assert!(super::expression_is_provider_suppressed(
            "first if a  # fmt: skip\nelse second"
        ));
    }

    #[test]
    fn formats_and_validates_ordinary_expressions() {
        assert_eq!(
            format_expression("foo( 1,bar= [1,2])", 100, "\n").unwrap(),
            "foo(1, bar=[1, 2])"
        );
        assert_eq!(
            format_expression("[first,  # keep the first item\nsecond]", 100, "\n").unwrap(),
            "[\n  first,  # keep the first item\n  second,\n]",
        );
        assert_eq!(
            format_expression("[first,  # keep\rsecond]", 100, "\r").unwrap(),
            "[\n  first,  # keep\n  second,\n]",
        );
    }

    #[test]
    fn formats_and_validates_for_clauses() {
        assert_eq!(
            format_for_clause("item  in items if  item.visible", 100, "\n").unwrap(),
            "item in items if item.visible",
        );
        assert_eq!(
            format_for_clause(
                "item in items if (\nitem.visible  # keep visible items\n)",
                100,
                "\n"
            )
            .unwrap(),
            "item in items\n  if (\n    item.visible  # keep visible items\n  )",
        );
        assert_eq!(
            format_for_clause("item in items  #keep the items", 100, "\n").unwrap(),
            "item in items  # keep the items",
        );
        assert_eq!(
            format_expression("foo(  1)  # fmt: skip", 100, "\n").unwrap(),
            "foo(  1)  # fmt: skip",
        );
        assert_eq!(
            format_expression("[first,  # keep\r\nsecond]", 100, "\r\n").unwrap(),
            "[\n  first,  # keep\n  second,\n]",
        );
    }

    #[test]
    fn expression_provider_is_idempotent_across_python_shapes() {
        let cases = [
            "lambda value : value+1",
            "[ value*2 for value in values if value>0 ]",
            "(value := call( 1 ))",
            "{'key':value, **rest}",
            "f'{user . name}: {count+1}'",
            "r'raw\\nvalue'",
            "(item for item in items if item.visible)",
            "{'žluťoučký', 'kůň'}",
        ];
        for source in cases {
            let formatted = format_expression(source, 80, "\n").unwrap();
            assert_eq!(
                format_expression(&formatted, 80, "\n").unwrap(),
                formatted,
                "{source}",
            );
        }
    }
}
