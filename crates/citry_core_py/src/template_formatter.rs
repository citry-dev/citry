//! Python interface for the authored Citry template formatter.

use citry_template_formatter::{
    EmbeddedFormatNotice as RustEmbeddedFormatNotice, EmbeddedFormatPlan as RustEmbeddedFormatPlan,
    EmbeddedFormatResult as RustEmbeddedFormatResult, FormatError, PYTHON_EXPRESSION_PROVIDER,
    finish_embedded_format as finish_embedded_format_rust, format_template as format_template_rust,
    format_template_with_options as format_template_with_options_rust,
    prepare_embedded_format as prepare_embedded_format_rust,
};
use citry_template_parser::ParseOptions;
use pyo3::create_exception;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

create_exception!(
    citry_core.template_formatter,
    TemplateFormatError,
    PyValueError
);

type EmbeddedRequestTuple = (
    String,
    String,
    String,
    String,
    String,
    (usize, usize),
    usize,
    String,
);
type EmbeddedNoticeTuple = (String, String, Option<String>, Option<String>);
type EmbeddedResultTuple = (
    String,
    String,
    String,
    Option<String>,
    Option<String>,
    Option<String>,
);

/// Opaque source-bound handle used to finish an embedded-formatting pass.
#[pyclass(name = "_EmbeddedFormatPlan", frozen)]
pub struct PyEmbeddedFormatPlan {
    inner: RustEmbeddedFormatPlan,
}

#[pymethods]
impl PyEmbeddedFormatPlan {
    #[getter]
    fn id(&self) -> &str {
        self.inner.id()
    }

    #[getter]
    fn formatted_source(&self) -> &str {
        self.inner.formatted_source()
    }

    #[getter]
    fn requests(&self) -> Vec<EmbeddedRequestTuple> {
        self.inner
            .requests()
            .iter()
            .map(|request| {
                let byte_range = request.byte_range();
                (
                    request.id().to_string(),
                    request.language().as_str().to_string(),
                    request.kind().as_str().to_string(),
                    request.source().to_string(),
                    request.virtual_source().to_string(),
                    (byte_range.start, byte_range.end),
                    request.base_indent(),
                    request.newline().to_string(),
                )
            })
            .collect()
    }

    #[getter]
    fn notices(&self) -> Vec<EmbeddedNoticeTuple> {
        notice_tuples(self.inner.notices())
    }
}

fn format_error_to_py(py: Python<'_>, error: FormatError) -> PyErr {
    let code = error.code();
    let message = error.to_string();
    let range = error.range().map(|range| (range.start, range.end));
    let diagnostic = error.parse_diagnostic().cloned();
    let py_error = TemplateFormatError::new_err(message.clone());
    let attach = || -> PyResult<()> {
        let value = py_error.value(py);
        value.setattr("code", code)?;
        value.setattr("message", message)?;
        value.setattr("range", range)?;
        match diagnostic {
            Some(diagnostic) => value.setattr("diagnostic", Py::new(py, diagnostic)?)?,
            None => value.setattr("diagnostic", py.None())?,
        }
        Ok(())
    };
    match attach() {
        Ok(()) => py_error,
        Err(attachment_error) => attachment_error,
    }
}

fn provider_error_to_py(py: Python<'_>, message: impl Into<String>) -> PyErr {
    let message = message.into();
    let py_error = TemplateFormatError::new_err(message.clone());
    let attach = || -> PyResult<()> {
        let value = py_error.value(py);
        value.setattr("code", "citry.format.provider-invalid")?;
        value.setattr("message", message)?;
        value.setattr("range", py.None())?;
        value.setattr("diagnostic", py.None())?;
        Ok(())
    };
    match attach() {
        Ok(()) => py_error,
        Err(attachment_error) => attachment_error,
    }
}

fn notice_tuples(notices: &[RustEmbeddedFormatNotice]) -> Vec<EmbeddedNoticeTuple> {
    notices
        .iter()
        .map(|notice| {
            (
                notice.code().to_string(),
                notice.message().to_string(),
                notice.region_id().map(str::to_string),
                notice
                    .language()
                    .map(|language| language.as_str().to_string()),
            )
        })
        .collect()
}

/// Format authored Citry template text without app discovery or global state.
///
/// Raises `TemplateFormatError` with a stable `code`, optional UTF-8 byte
/// `range`, and optional parser `diagnostic` when the formatter refuses the
/// input.
#[pyfunction]
#[pyo3(signature = (source, *, options=None))]
pub fn format_template(
    py: Python<'_>,
    source: &str,
    options: Option<ParseOptions>,
) -> PyResult<String> {
    let result = match options {
        Some(options) => format_template_with_options_rust(source, &options),
        None => format_template_rust(source),
    };
    result.map_err(|error| format_error_to_py(py, error))
}

/// Return the pinned identity of the built-in Python expression formatter.
#[pyfunction]
pub const fn python_expression_provider() -> &'static str {
    PYTHON_EXPRESSION_PROVIDER
}

/// Prepare structural Citry output and discover safe embedded provider regions.
#[pyfunction]
pub fn prepare_embedded_format(py: Python<'_>, source: &str) -> PyResult<PyEmbeddedFormatPlan> {
    prepare_embedded_format_rust(source)
        .map(|inner| PyEmbeddedFormatPlan { inner })
        .map_err(|error| format_error_to_py(py, error))
}

/// Validate provider replies and atomically compose the prepared plan.
#[pyfunction]
pub fn finish_embedded_format(
    py: Python<'_>,
    plan: &PyEmbeddedFormatPlan,
    results: Vec<EmbeddedResultTuple>,
) -> PyResult<(String, Vec<EmbeddedNoticeTuple>, Vec<String>)> {
    let mut rust_results = Vec::with_capacity(results.len());
    for (status, plan_id, region_id, text, provider, message) in results {
        let result = match status.as_str() {
            "formatted" => {
                if message.is_some() {
                    return Err(provider_error_to_py(
                        py,
                        "a formatted embedded result cannot carry an error message",
                    ));
                }
                RustEmbeddedFormatResult::formatted(
                    plan_id,
                    region_id,
                    text.ok_or_else(|| {
                        provider_error_to_py(py, "a formatted embedded result requires text")
                    })?,
                    provider,
                )
            }
            "unchanged" => {
                if text.is_some() || provider.is_some() || message.is_some() {
                    return Err(provider_error_to_py(
                        py,
                        "an unchanged embedded result cannot carry output fields",
                    ));
                }
                RustEmbeddedFormatResult::unchanged(plan_id, region_id)
            }
            "unavailable" => {
                if text.is_some() || provider.is_some() {
                    return Err(provider_error_to_py(
                        py,
                        "an unavailable embedded result cannot carry formatted output",
                    ));
                }
                RustEmbeddedFormatResult::unavailable(
                    plan_id,
                    region_id,
                    message.ok_or_else(|| {
                        provider_error_to_py(
                            py,
                            "an unavailable embedded result requires a message",
                        )
                    })?,
                )
            }
            "error" => {
                if text.is_some() || provider.is_some() {
                    return Err(provider_error_to_py(
                        py,
                        "an error embedded result cannot carry formatted output",
                    ));
                }
                RustEmbeddedFormatResult::error(
                    plan_id,
                    region_id,
                    message.ok_or_else(|| {
                        provider_error_to_py(py, "an error embedded result requires a message")
                    })?,
                )
            }
            _ => {
                return Err(provider_error_to_py(
                    py,
                    format!("unknown embedded result status {status:?}"),
                ));
            }
        };
        rust_results.push(result);
    }

    finish_embedded_format_rust(&plan.inner, &rust_results)
        .map(|outcome| {
            (
                outcome.source().to_string(),
                notice_tuples(outcome.notices()),
                outcome.providers().to_vec(),
            )
        })
        .map_err(|error| format_error_to_py(py, error))
}
