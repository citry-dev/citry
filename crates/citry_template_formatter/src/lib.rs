//! Parser-backed formatting for authored Citry templates.
//!
//! The current capability formats complete structural Citry/HTML layout and
//! validated Python expression regions while preserving sensitive and
//! verbatim content.

mod comments;
mod diagnostic_catalog;
mod embedded;
mod error;
mod formatter;
mod html;
mod layout;
mod newline;
mod printer;
mod projection;
mod python;
mod source;
mod suppression;

pub(crate) const PREFERRED_WIDTH: usize = 100;

pub use embedded::{
    EmbeddedFormatNotice, EmbeddedFormatOutcome, EmbeddedFormatPlan, EmbeddedFormatRequest,
    EmbeddedFormatResult, EmbeddedLanguage, EmbeddedRegionKind, finish_embedded_format,
    prepare_embedded_format,
};
pub use error::{FormatError, FormatErrorKind};

/// Identity of the built-in Python expression formatter.
pub const PYTHON_EXPRESSION_PROVIDER: &str = python::PYTHON_PROVIDER_IDENTITY;

/// Format an authored Citry template with the structural and Python policies.
///
/// Formatting preserves sensitive boundaries, non-whitespace text, verbatim
/// bodies, suppression ranges, comments, tag spelling, quotes, and line-ending
/// style. It normalizes start tags, proven structural gaps, nested template
/// values, Python expressions, `c-for` clauses, and `c-fill data` patterns. It
/// validates that the result reparses, keeps the same structural projection,
/// preserves protected fingerprints, and is idempotent before returning text.
///
/// # Errors
///
/// Returns [`FormatError`] for invalid Citry syntax, malformed formatter
/// directives, invalid parser spans, unsupported safe-printing cases, or a
/// failed formatter invariant.
pub fn format_template(source: &str) -> Result<String, FormatError> {
    formatter::format(source)
}

#[cfg(test)]
mod corpus;
