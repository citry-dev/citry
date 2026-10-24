use pest::error::{ErrorVariant, InputLocation, LineColLocation};
use pyo3::prelude::*;
use thiserror::Error;

use crate::diagnostic_catalog::{PARSE_SYNTAX, PARSE_VALUE};
use crate::grammar::Rule;

/// Machine-readable details for one template parse failure.
///
/// Indices are half-open UTF-8 byte offsets in the complete template source.
/// Pest position errors have an empty range. Line and column values are
/// 1-based, matching Pest's rendered diagnostics.
#[pyclass(from_py_object, frozen)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseDiagnostic {
    /// Stable identifier for the broad failure category.
    #[pyo3(get)]
    pub code: String,
    /// The same rendered text carried by the Python exception.
    #[pyo3(get)]
    pub message: String,
    /// Inclusive UTF-8 byte offset, when the parser has a source position.
    #[pyo3(get)]
    pub start_index: Option<usize>,
    /// Exclusive UTF-8 byte offset, when the parser has a source position.
    #[pyo3(get)]
    pub end_index: Option<usize>,
    /// 1-based start line, when the parser has a source position.
    #[pyo3(get)]
    pub start_line: Option<usize>,
    /// 1-based start column, when the parser has a source position.
    #[pyo3(get)]
    pub start_column: Option<usize>,
    /// 1-based end line, when the parser has a source position.
    #[pyo3(get)]
    pub end_line: Option<usize>,
    /// 1-based end column, when the parser has a source position.
    #[pyo3(get)]
    pub end_column: Option<usize>,
}

#[pymethods]
impl ParseDiagnostic {
    fn __repr__(&self) -> String {
        format!(
            "ParseDiagnostic(code={:?}, start_index={:?}, end_index={:?}, start_line={:?}, start_column={:?}, end_line={:?}, end_column={:?})",
            self.code,
            self.start_index,
            self.end_index,
            self.start_line,
            self.start_column,
            self.end_line,
            self.end_column,
        )
    }
}

#[derive(Debug, Error, PartialEq)]
pub enum CompileError {
    #[error("Compile error: {0}")]
    Generic(String),
    #[error("Compile error: {0}")]
    Syntax(String),
}

impl From<String> for CompileError {
    fn from(error: String) -> Self {
        CompileError::Generic(error)
    }
}

impl From<&str> for CompileError {
    fn from(error: &str) -> Self {
        CompileError::Generic(error.to_string())
    }
}

#[derive(Error, Debug)]
pub enum ParseError {
    #[error("Parse error: {0}")]
    Syntax(#[from] pest::error::Error<Rule>),
    #[error("Parse error: {0}")]
    Value(String),
}

impl ParseError {
    /// Helper function to create a ParseError with position information from a span
    pub fn from_span(span: pest::Span, message: String) -> ParseError {
        ParseError::Syntax(error_from_span(ErrorVariant::CustomError { message }, span))
    }

    /// Return stable, machine-readable details without changing display text.
    pub fn diagnostic(&self) -> ParseDiagnostic {
        match self {
            ParseError::Syntax(error) => {
                let (start_index, end_index) = match error.location {
                    InputLocation::Pos(position) => (position, position),
                    InputLocation::Span((start, end)) => (start, end),
                };
                let ((start_line, start_column), (end_line, end_column)) = match error.line_col {
                    LineColLocation::Pos(position) => (position, position),
                    LineColLocation::Span(start, end) => (start, end),
                };
                ParseDiagnostic {
                    code: PARSE_SYNTAX.to_string(),
                    message: self.to_string(),
                    start_index: Some(start_index),
                    end_index: Some(end_index),
                    start_line: Some(start_line),
                    start_column: Some(start_column),
                    end_line: Some(end_line),
                    end_column: Some(end_column),
                }
            }
            ParseError::Value(_) => ParseDiagnostic {
                code: PARSE_VALUE.to_string(),
                message: self.to_string(),
                start_index: None,
                end_index: None,
                start_line: None,
                start_column: None,
                end_line: None,
                end_column: None,
            },
        }
    }
}

/// Build the error `pest::error::Error::new_from_span` builds for `span`, in
/// time that grows only with the input's length.
///
/// Pest renders an error with the first and last line of its span. To find
/// the last one, it walks every line of the span, and each step searches
/// from the ends of the whole input, so a span over many lines of a long
/// template took time that grows with the line count times the input length.
/// The error depends only on the span's first and last lines and on its first
/// and last characters, so a span over three or more lines is rebuilt on a
/// copy holding just those two lines. It is then given its real byte range
/// and its start and end line and column, which pest computes in one pass
/// each.
fn error_from_span(variant: ErrorVariant<Rule>, span: pest::Span) -> pest::error::Error<Rule> {
    let input = span.get_input();
    let (start, end) = (span.start(), span.end());
    // The first line is the one holding `start`, including its `\n`.
    let first_line_start = input[..start].rfind('\n').map_or(0, |index| index + 1);
    let first_line_end = input[start..]
        .find('\n')
        .map_or(input.len(), |index| start + index + 1);
    // Pest's line walk ends on the line holding `end`, or on the line of the
    // last character when `end` is the end of the input.
    let last_probe = if end < input.len() {
        end
    } else {
        input
            .char_indices()
            .next_back()
            .map_or(0, |(index, _)| index)
    };
    let last_line_start = input[..last_probe].rfind('\n').map_or(0, |index| index + 1);
    // A span over one or two lines already costs only a few passes over the
    // input, so pest builds it directly.
    if last_line_start <= first_line_end {
        return pest::error::Error::new_from_span(variant, span);
    }
    let last_line_end = input[last_line_start..]
        .find('\n')
        .map_or(input.len(), |index| last_line_start + index + 1);

    // The copy keeps the span's first and last character, so pest makes the
    // same choice about showing whitespace, and the same two lines.
    let first_line = &input[first_line_start..first_line_end];
    let copy = format!("{first_line}{}", &input[last_line_start..last_line_end]);
    let copy_span = pest::Span::new(
        &copy,
        start - first_line_start,
        first_line.len() + (end - last_line_start),
    )
    .expect("the copied span lies on the same character boundaries");
    let mut error = pest::error::Error::new_from_span(variant, copy_span);

    // The byte range and the start and end line and column describe the real
    // input, computed the way `new_from_span` computes them. An end just after a `\n` points at
    // that `\n`, one column past the last character of its line.
    let line_col = |offset: usize| {
        pest::Position::new(input, offset)
            .expect("span offsets are character boundaries")
            .line_col()
    };
    let mut end_line_col = line_col(end);
    if end_line_col.1 == 1 {
        let before_end = input[..end]
            .char_indices()
            .next_back()
            .map_or(0, |(index, _)| index);
        let (line, column) = line_col(before_end);
        end_line_col = (line, column + 1);
    }
    error.location = InputLocation::Span((start, end));
    error.line_col = LineColLocation::Span(line_col(start), end_line_col);
    error
}

pub fn assert_rule(pair: &pest::iterators::Pair<Rule>, rule: Rule) -> Result<(), ParseError> {
    if pair.as_rule() != rule {
        return Err(ParseError::from_span(
            pair.as_span(),
            format!("Expected {:?}, got {:?}", rule, pair.as_rule()),
        ));
    }
    Ok(())
}

pub fn assert_rules(pair: &pest::iterators::Pair<Rule>, rules: &[Rule]) -> Result<(), ParseError> {
    if !rules.contains(&pair.as_rule()) {
        return Err(ParseError::from_span(
            pair.as_span(),
            format!("Expected one of {:?}, got {:?}", rules, pair.as_rule()),
        ));
    }
    Ok(())
}
