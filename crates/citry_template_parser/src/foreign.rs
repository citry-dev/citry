use std::collections::HashSet;

use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyBool};

use crate::error::ParseError;

/// One half-open UTF-8 byte range whose syntax belongs to an external
/// template provider.
#[pyclass(frozen)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ForeignSpan {
    #[pyo3(get)]
    pub start_byte: usize,
    #[pyo3(get)]
    pub end_byte: usize,
    #[pyo3(get)]
    pub provider: String,
    #[pyo3(get)]
    pub ordinal: usize,
    #[pyo3(get)]
    pub may_control_body: bool,
}

#[pymethods]
impl ForeignSpan {
    #[new]
    #[pyo3(signature = (start_byte, end_byte, provider, ordinal=0, may_control_body=false))]
    fn new(
        start_byte: &Bound<'_, PyAny>,
        end_byte: &Bound<'_, PyAny>,
        provider: String,
        ordinal: usize,
        may_control_body: bool,
    ) -> PyResult<Self> {
        Ok(Self {
            start_byte: extract_index("start_byte", start_byte)?,
            end_byte: extract_index("end_byte", end_byte)?,
            provider,
            ordinal,
            may_control_body,
        })
    }

    fn __repr__(&self) -> String {
        format!(
            "ForeignSpan(start_byte={}, end_byte={}, provider={:?}, ordinal={}, may_control_body={})",
            self.start_byte, self.end_byte, self.provider, self.ordinal, self.may_control_body,
        )
    }
}

fn extract_index(name: &str, value: &Bound<'_, PyAny>) -> PyResult<usize> {
    if value.is_instance_of::<PyBool>() {
        return Err(PyTypeError::new_err(format!(
            "{name} must be an integer, not bool"
        )));
    }
    value
        .extract::<usize>()
        .map_err(|_| PyTypeError::new_err(format!("{name} must be a non-negative integer")))
}

impl ForeignSpan {
    pub fn from_parts(
        start_byte: usize,
        end_byte: usize,
        provider: impl Into<String>,
        ordinal: usize,
        may_control_body: bool,
    ) -> Self {
        Self {
            start_byte,
            end_byte,
            provider: provider.into(),
            ordinal,
            may_control_body,
        }
    }
}

/// Optional parser inputs. The default is exactly the pre-interop parser.
#[pyclass]
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct ParseOptions {
    #[pyo3(get)]
    pub foreign_spans: Vec<ForeignSpan>,
    /// Absolute byte origin of `input` inside `root_source`.
    #[pyo3(get)]
    pub source_offset: usize,
    /// Original outer source for a projected nested parse.
    #[pyo3(get)]
    pub root_source: Option<String>,
}

#[pymethods]
impl ParseOptions {
    #[new]
    #[pyo3(signature = (foreign_spans=Vec::new(), source_offset=0, root_source=None))]
    fn new(
        foreign_spans: Vec<ForeignSpan>,
        source_offset: usize,
        root_source: Option<String>,
    ) -> Self {
        Self {
            foreign_spans,
            source_offset,
            root_source,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "ParseOptions(foreign_spans={:?}, source_offset={}, root_source={:?})",
            self.foreign_spans, self.source_offset, self.root_source,
        )
    }
}

impl ParseOptions {
    pub fn with_foreign_spans(foreign_spans: Vec<ForeignSpan>) -> Self {
        Self {
            foreign_spans,
            ..Self::default()
        }
    }

    pub fn with_projection(
        foreign_spans: Vec<ForeignSpan>,
        source_offset: usize,
        root_source: impl Into<String>,
    ) -> Self {
        Self {
            foreign_spans,
            source_offset,
            root_source: Some(root_source.into()),
        }
    }

    /// Validate these options against `source` and express every claim relative
    /// to that source.
    ///
    /// Parser projections keep root-absolute offsets for diagnostics. Tools
    /// that rewrite only the projected string need local offsets so they can
    /// carry claims forward when their edits shift later bytes.
    pub fn localized_for_source(&self, source: &str) -> Result<Self, ParseError> {
        let (_, spans) = self.validate(source)?;
        let foreign_spans = spans
            .into_iter()
            .map(|span| Self::localize_span(span, self.source_offset))
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Self::with_foreign_spans(foreign_spans))
    }

    fn localize_span(span: ForeignSpan, source_offset: usize) -> Result<ForeignSpan, ParseError> {
        let start_byte = span.start_byte.checked_sub(source_offset).ok_or_else(|| {
            ParseError::Value("Foreign span starts before its projected source".to_string())
        })?;
        let end_byte = span.end_byte.checked_sub(source_offset).ok_or_else(|| {
            ParseError::Value("Foreign span ends before its projected source".to_string())
        })?;
        Ok(ForeignSpan {
            start_byte,
            end_byte,
            provider: span.provider,
            ordinal: span.ordinal,
            may_control_body: span.may_control_body,
        })
    }

    pub(crate) fn validate(&self, source: &str) -> Result<(String, Vec<ForeignSpan>), ParseError> {
        let root_source = self.root_source.as_deref().unwrap_or(source);
        let source_end = self
            .source_offset
            .checked_add(source.len())
            .ok_or_else(|| {
                ParseError::Value("Projected template source range overflows usize".to_string())
            })?;
        let projected = root_source
            .get(self.source_offset..source_end)
            .ok_or_else(|| {
                ParseError::Value(format!(
                    "Projected template range {}..{} is invalid for {} root-source bytes",
                    self.source_offset,
                    source_end,
                    root_source.len(),
                ))
            })?;
        if projected != source {
            return Err(ParseError::Value(format!(
                "Projected template input does not match root_source bytes {}..{}",
                self.source_offset, source_end,
            )));
        }

        let mut spans = self.foreign_spans.clone();
        spans.sort_by(|left, right| {
            (
                left.start_byte,
                left.end_byte,
                left.provider.as_str(),
                left.ordinal,
            )
                .cmp(&(
                    right.start_byte,
                    right.end_byte,
                    right.provider.as_str(),
                    right.ordinal,
                ))
        });

        let mut claim_ids = HashSet::new();
        for span in &spans {
            if span.provider.is_empty() {
                return Err(ParseError::Value(
                    "Foreign span provider must be a non-empty string".to_string(),
                ));
            }
            if span.start_byte >= span.end_byte {
                return Err(ParseError::Value(format!(
                    "Foreign span for provider {:?} must satisfy start_byte < end_byte, got {}..{}",
                    span.provider, span.start_byte, span.end_byte,
                )));
            }
            if span.end_byte > root_source.len() {
                return Err(ParseError::Value(format!(
                    "Foreign span for provider {:?} is out of bounds for {} source bytes: {}..{}",
                    span.provider,
                    root_source.len(),
                    span.start_byte,
                    span.end_byte,
                )));
            }
            if !root_source.is_char_boundary(span.start_byte)
                || !root_source.is_char_boundary(span.end_byte)
            {
                return Err(ParseError::Value(format!(
                    "Foreign span for provider {:?} must begin and end on UTF-8 boundaries: {}..{}",
                    span.provider, span.start_byte, span.end_byte,
                )));
            }
            if span.start_byte < self.source_offset || span.end_byte > source_end {
                return Err(ParseError::Value(format!(
                    "Foreign span for provider {:?} falls outside projected template bytes {}..{}: {}..{}",
                    span.provider, self.source_offset, source_end, span.start_byte, span.end_byte,
                )));
            }
            if !claim_ids.insert((span.provider.clone(), span.ordinal)) {
                return Err(ParseError::Value(format!(
                    "Foreign span claim ID is duplicated for provider {:?}, ordinal {}",
                    span.provider, span.ordinal,
                )));
            }
        }

        for pair in spans.windows(2) {
            let previous = &pair[0];
            let current = &pair[1];
            if current.start_byte < previous.end_byte {
                return Err(ParseError::Value(format!(
                    "Foreign spans overlap: provider {:?} owns {}..{}, provider {:?} owns {}..{}",
                    previous.provider,
                    previous.start_byte,
                    previous.end_byte,
                    current.provider,
                    current.start_byte,
                    current.end_byte,
                )));
            }
        }

        Ok((root_source.to_string(), spans))
    }
}
