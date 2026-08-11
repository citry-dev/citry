use pest::error::{InputLocation, LineColLocation};
use pyo3::prelude::*;
use thiserror::Error;

use crate::diagnostic_catalog::{PARSE_SYNTAX, PARSE_VALUE};
use crate::grammar::Rule;

/// Machine-readable details for one template parse failure.
///
/// Indices are half-open UTF-8 byte offsets in the complete template source.
/// Pest position errors have an empty range. Line and column values are
/// 1-based, matching Pest's rendered diagnostics.
#[pyclass(frozen)]
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
        ParseError::Syntax(pest::error::Error::new_from_span(
            pest::error::ErrorVariant::CustomError { message },
            span,
        ))
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
