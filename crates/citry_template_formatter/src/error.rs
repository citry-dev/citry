use std::ops::Range;

use citry_template_parser::{ParseDiagnostic, ParseError};
use thiserror::Error;

/// Broad category for a template-formatting failure.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[non_exhaustive]
pub enum FormatErrorKind {
    Syntax,
    Suppression,
    InvalidSpan,
    Unsupported,
    Provider,
    Invariant,
}

/// A structured refusal to format the supplied template.
#[derive(Debug, Error)]
#[error("{message}")]
pub struct FormatError {
    kind: FormatErrorKind,
    message: String,
    range: Option<Range<usize>>,
    parse_diagnostic: Option<Box<ParseDiagnostic>>,
}

impl FormatError {
    /// Return the broad error category.
    pub const fn kind(&self) -> FormatErrorKind {
        self.kind
    }

    /// Return the stable formatter error code.
    pub const fn code(&self) -> &'static str {
        match self.kind {
            FormatErrorKind::Syntax => "citry.format.syntax",
            FormatErrorKind::Suppression => "citry.format.suppression",
            FormatErrorKind::InvalidSpan | FormatErrorKind::Invariant => "citry.format.invariant",
            FormatErrorKind::Unsupported => "citry.format.unsupported",
            FormatErrorKind::Provider => "citry.format.provider-invalid",
        }
    }

    /// Return the affected half-open UTF-8 byte range, when known.
    pub fn range(&self) -> Option<Range<usize>> {
        self.range.clone()
    }

    /// Return the parser's original diagnostic for a syntax error.
    pub fn parse_diagnostic(&self) -> Option<&ParseDiagnostic> {
        self.parse_diagnostic.as_deref()
    }

    pub(crate) fn from_parse(error: &ParseError) -> Self {
        let diagnostic = error.diagnostic();
        Self {
            kind: FormatErrorKind::Syntax,
            message: diagnostic.message.clone(),
            range: diagnostic
                .start_index
                .zip(diagnostic.end_index)
                .map(|(start, end)| start..end),
            parse_diagnostic: Some(Box::new(diagnostic)),
        }
    }

    pub(crate) fn suppression(message: impl Into<String>, range: Range<usize>) -> Self {
        Self {
            kind: FormatErrorKind::Suppression,
            message: message.into(),
            range: Some(range),
            parse_diagnostic: None,
        }
    }

    pub(crate) fn invalid_span(message: impl Into<String>, range: Range<usize>) -> Self {
        Self {
            kind: FormatErrorKind::InvalidSpan,
            message: message.into(),
            range: Some(range),
            parse_diagnostic: None,
        }
    }

    pub(crate) fn invariant(message: impl Into<String>) -> Self {
        Self {
            kind: FormatErrorKind::Invariant,
            message: message.into(),
            range: None,
            parse_diagnostic: None,
        }
    }

    pub(crate) fn provider(message: impl Into<String>, range: Option<Range<usize>>) -> Self {
        Self {
            kind: FormatErrorKind::Provider,
            message: message.into(),
            range,
            parse_diagnostic: None,
        }
    }
}
