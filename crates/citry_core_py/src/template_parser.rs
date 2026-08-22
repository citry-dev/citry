/// Python interface for the citry_template_parser crate (V3).
///
/// Exposes `parse_template` and `compile_template` as thin wrappers that
/// convert Python-friendly arguments (lang as a string, user_rules as a
/// dict) into their Rust equivalents and map errors to Python exceptions.
use std::collections::HashMap;
use std::rc::Rc;

use pyo3::exceptions::{PySyntaxError, PyValueError};
use pyo3::prelude::*;

use citry_template_parser::browser::{
    BrowserAnalysisMode, analyze_browser_source as analyze_browser_source_rust,
    analyze_component_scope_writes as analyze_component_scope_writes_rust,
    analyze_component_source as analyze_component_source_rust,
};
use citry_template_parser::compiler::compile_template as compile_template_rust;
use citry_template_parser::error::CompileError;
use citry_template_parser::lang::lang::Lang;
use citry_template_parser::parser::{
    parse_template as parse_template_rust,
    parse_template_with_options as parse_template_with_options_rust,
};
use citry_template_parser::parser_context::TagRules;
use citry_template_parser::{ParseError, ParseOptions, Template};

fn lang_from_str(s: Option<&str>) -> PyResult<Option<Lang>> {
    match s {
        None | Some("python") => Ok(Some(Lang::Python)),
        Some("js") | Some("javascript") => Ok(Some(Lang::Js)),
        Some("php") => Ok(Some(Lang::Php)),
        Some("go") => Ok(Some(Lang::Go)),
        Some("rust") => Ok(Some(Lang::Rust)),
        Some(other) => Err(PyValueError::new_err(format!(
            "Unknown language: '{}'. Supported: python, js, php, go, rust",
            other
        ))),
    }
}

fn parse_error_to_py(py: Python<'_>, error: ParseError) -> PyErr {
    let diagnostic = error.diagnostic();
    let py_error = match error {
        ParseError::Syntax(_) => PySyntaxError::new_err(diagnostic.message.clone()),
        ParseError::Value(_) => PyValueError::new_err(diagnostic.message.clone()),
    };
    let result = Py::new(py, diagnostic)
        .and_then(|diagnostic| py_error.value(py).setattr("diagnostic", diagnostic));
    match result {
        Ok(()) => py_error,
        Err(attachment_error) => attachment_error,
    }
}

fn compile_error_to_py(e: CompileError) -> PyErr {
    match e {
        CompileError::Syntax(_) => PySyntaxError::new_err(e.to_string()),
        CompileError::Generic(_) => PyValueError::new_err(e.to_string()),
    }
}

/// Parse a Citry template string into a Template AST.
///
/// **Args:**
///
/// - input (str): The template string to parse.
/// - lang (str, optional): Expression language. One of "python" (default),
///   "js", "php", "go", "rust".
/// - user_rules (dict[str, TagRules], optional): Custom validation rules
///   keyed by tag name.
///
/// **Returns:**
///
/// - Template: The parsed AST.
///
/// **Raises:**
///
/// - SyntaxError: If the template has invalid syntax.
/// - ValueError: If an unknown language is specified or a semantic error occurs.
#[pyfunction]
#[pyo3(signature = (input, lang=None, user_rules=None, *, options=None))]
pub fn parse_template(
    py: Python<'_>,
    input: &str,
    lang: Option<&str>,
    user_rules: Option<HashMap<String, TagRules>>,
    options: Option<ParseOptions>,
) -> PyResult<Template> {
    let lang_enum = lang_from_str(lang)?;
    let rules_rc = user_rules.map(Rc::new);
    let result = match options {
        Some(options) => {
            parse_template_with_options_rust(input, lang_enum, rules_rc.as_ref(), &options)
        }
        None => parse_template_rust(input, lang_enum, rules_rc.as_ref()),
    };
    result.map_err(|error| parse_error_to_py(py, error))
}

/// Compile a parsed Template AST into host-language source code.
///
/// For Python (the default), the output is a `generate_template()` function
/// that returns a list of runtime node objects.
///
/// **Args:**
///
/// - template (Template): The parsed AST from `parse_template`.
/// - lang (str, optional): Target language. One of "python" (default),
///   "js", "php", "go", "rust".
///
/// **Returns:**
///
/// - str: The generated source code.
///
/// **Raises:**
///
/// - ValueError: If compilation fails or an unknown language is specified.
#[pyfunction]
#[pyo3(signature = (template, lang=None))]
pub fn compile_template(template: Template, lang: Option<&str>) -> PyResult<String> {
    let lang_enum = lang_from_str(lang)?;
    compile_template_rust(template, lang_enum).map_err(compile_error_to_py)
}

/// Parse one Alpine expression/statement and return exact free identifier ranges.
#[pyfunction]
pub fn analyze_browser_source(
    input: &str,
    mode: &str,
) -> PyResult<(bool, Vec<(String, usize, usize)>)> {
    let mode = mode
        .parse::<BrowserAnalysisMode>()
        .map_err(PyValueError::new_err)?;
    let analysis = analyze_browser_source_rust(input, mode);
    Ok((
        analysis.valid,
        analysis
            .references
            .into_iter()
            .map(|reference| (reference.name, reference.start, reference.end))
            .collect(),
    ))
}

/// Return direct synchronous `$component` scope writes and their source ranges.
#[pyfunction]
pub fn analyze_component_scope_writes(input: &str) -> Vec<(String, usize, usize, usize, usize)> {
    analyze_component_scope_writes_rust(input)
        .into_iter()
        .map(|write| {
            (
                write.name,
                write.name_start,
                write.name_end,
                write.value_start,
                write.value_end,
            )
        })
        .collect()
}

type ComponentSourceAnalysis = (
    bool,
    Vec<(String, usize, usize)>,
    Vec<(String, String, usize, usize, Vec<(usize, usize)>)>,
    Vec<(String, usize, usize, usize, usize)>,
);

/// Return detached source facts for runtime `$component` initializers.
#[pyfunction]
pub fn analyze_component_source(input: &str) -> ComponentSourceAnalysis {
    let analysis = analyze_component_source_rust(input);
    (
        analysis.valid,
        analysis
            .references
            .into_iter()
            .map(|reference| (reference.name, reference.start, reference.end))
            .collect(),
        analysis
            .bindings
            .into_iter()
            .map(|binding| {
                (
                    binding.name,
                    binding.local_name,
                    binding.start,
                    binding.end,
                    binding.references,
                )
            })
            .collect(),
        analysis
            .scope_writes
            .into_iter()
            .map(|write| {
                (
                    write.name,
                    write.name_start,
                    write.name_end,
                    write.value_start,
                    write.value_end,
                )
            })
            .collect(),
    )
}
