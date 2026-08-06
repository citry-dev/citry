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

use ruff_formatter::{IndentWidth, LineWidth, printer::LineEnding};
use ruff_python_ast::{
    PythonVersion,
    comparable::ComparableExpr,
    token::{TokenKind, Tokens},
};
use ruff_python_formatter::{PyFormatOptions, QuoteStyle, format_module_ast};
use ruff_python_parser::{Mode, ParseOptions, parse, parse_expression};
use ruff_python_trivia::{CommentRanges, SuppressionKind};

use crate::error::FormatError;
use crate::newline::normalize_to_lf;

/// Wraps a bare expression as `x((<expr>))` so Ruff sees a module. The call
/// parentheses also give it somewhere to break long lines.
const EXPRESSION_WRAPPER: &str = "x";
/// Turns a `c-for` clause into a comprehension, the only Python construct where
/// `item in items` is valid on its own.
const CLAUSE_PREFIX: &str = "None for ";

/// Stable identity for the Python formatter pinned by this workspace.
pub const PYTHON_PROVIDER_IDENTITY: &str = "ruff@0.14.10+45bbb4cbff";

pub(crate) fn format_expression(
    source: &str,
    available_width: usize,
    newline: &str,
) -> Result<String, FormatError> {
    let before = parse_expression(source).map_err(|error| {
        FormatError::invariant(format!(
            "Citry accepted a Python expression that the formatter provider rejected: {error}"
        ))
    })?;
    let before_comments = comment_fingerprint(source, before.tokens());
    // A `# fmt: skip` inside the expression is the author telling Ruff to leave
    // it alone, so return the region untouched rather than formatting it and
    // then failing a comparison.
    if has_provider_suppression(source, before.tokens()) {
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
    let wrapper_comments = CommentRanges::from(parsed_wrapper.tokens());
    let formatted_document =
        format_module_ast(&parsed_wrapper, &wrapper_comments, &wrapped, options)
            .map_err(|error| FormatError::invariant(format!("Python provider failed: {error}")))?;
    let printed = formatted_document
        .print()
        .map_err(|error| FormatError::invariant(format!("Python provider failed: {error}")))?;
    let formatted = extract_wrapped_expression(printed.as_code(), newline)?;
    let after = parse_expression(&formatted).map_err(|error| {
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
    if before_comments != comment_fingerprint(&formatted, after.tokens()) {
        return Err(FormatError::invariant(
            "Python expression provider changed Python comments",
        ));
    }
    Ok(formatted)
}

pub(crate) fn expression_is_provider_suppressed(source: &str) -> bool {
    parse_expression(source).is_ok_and(|parsed| has_provider_suppression(source, parsed.tokens()))
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
    let before_source = format!("({CLAUSE_PREFIX}{source}{newline})");
    let before = parse_expression(&before_source).map_err(|error| {
        FormatError::invariant(format!(
            "Citry accepted a c-for clause that the formatter provider rejected: {error}"
        ))
    })?;
    let before_comments = comment_fingerprint(&before_source, before.tokens());
    let formatted_generator = format_expression(&before_source, available_width, newline)?;
    let formatted = extract_for_clause(&formatted_generator)?;
    let after_source = format!("({CLAUSE_PREFIX}{formatted}\n)");
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
        assert!(manifest.contains("version = \"0.14.10\""));
        assert_eq!(PYTHON_PROVIDER_IDENTITY, "ruff@0.14.10+45bbb4cbff");
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
