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
    BrowserAnalysisMode, analyze_browser_binding_pattern as analyze_browser_binding_pattern_rust,
    analyze_browser_source as analyze_browser_source_rust,
    analyze_component_members as analyze_component_members_rust,
    analyze_component_scope_writes as analyze_component_scope_writes_rust,
    analyze_component_source as analyze_component_source_rust,
};
use citry_template_parser::compiler::{
    compile_prepared_template as compile_prepared_template_rust,
    compile_template as compile_template_rust,
};
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

/// Compile a parsed template into the private Python prepared-render node form.
#[pyfunction(name = "_compile_prepared_template")]
#[pyo3(signature = (template, lang=None))]
pub fn compile_prepared_template(template: Template, lang: Option<&str>) -> PyResult<String> {
    let lang_enum = lang_from_str(lang)?;
    compile_prepared_template_rust(template, lang_enum).map_err(compile_error_to_py)
}

/// Parse one browser expression/statement and return exact free identifier ranges.
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

/// Parse one Vue slot-props binding pattern and return bindings plus free references.
#[pyfunction]
pub fn analyze_browser_binding_pattern(
    input: &str,
) -> (
    bool,
    Vec<(String, usize, usize)>,
    Vec<(String, usize, usize)>,
) {
    let analysis = analyze_browser_binding_pattern_rust(input);
    (
        analysis.valid,
        analysis
            .bindings
            .into_iter()
            .map(|item| (item.name, item.start, item.end))
            .collect(),
        analysis
            .references
            .into_iter()
            .map(|item| (item.name, item.start, item.end))
            .collect(),
    )
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

type ComponentMemberAnalysis = (bool, Vec<(String, String, usize, usize, usize, usize)>);

/// Return proven context members and their exact authored UTF-8 byte ranges.
#[pyfunction]
pub fn analyze_component_members(input: &str) -> ComponentMemberAnalysis {
    let analysis = analyze_component_members_rust(input);
    (
        analysis.valid,
        analysis
            .members
            .into_iter()
            .map(|member| {
                (
                    member.context_name,
                    member.member_name,
                    member.owner_start,
                    member.owner_end,
                    member.member_start,
                    member.member_end,
                )
            })
            .collect(),
    )
}

/// Return direct synchronous `$component` scope writes and their source ranges.
type ComponentSourceAnalysis = (
    bool,
    Vec<(String, usize, usize)>,
    Vec<(String, String, usize, usize, Vec<(usize, usize)>)>,
    Vec<(
        usize,
        usize,
        usize,
        usize,
        usize,
        Option<usize>,
        Option<usize>,
    )>,
    Vec<(
        String,
        String,
        String,
        usize,
        usize,
        Option<usize>,
        Option<usize>,
        Option<bool>,
        Option<bool>,
        Option<bool>,
        Option<String>,
    )>,
    Vec<(String, String, Option<usize>, Option<usize>, Option<String>)>,
    Vec<(String, String, usize, usize)>,
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
            .component_calls
            .into_iter()
            .map(|call| {
                (
                    call.call_start,
                    call.call_end,
                    call.callee_start,
                    call.callee_end,
                    call.open_paren_end,
                    call.argument_start,
                    call.argument_end,
                )
            })
            .collect(),
        analysis
            .public_names
            .into_iter()
            .map(|name| {
                (
                    name.authored_name,
                    name.exposed_name,
                    name.origin,
                    name.name_start,
                    name.name_end,
                    name.value_start,
                    name.value_end,
                    name.required,
                    name.has_default,
                    name.default_is_null,
                    name.type_source,
                )
            })
            .collect(),
        analysis
            .sections
            .into_iter()
            .map(|section| {
                (
                    section.name,
                    section.state,
                    section.start,
                    section.end,
                    section.unknown_reason,
                )
            })
            .collect(),
        analysis
            .member_references
            .into_iter()
            .map(|reference| {
                (
                    reference.receiver,
                    reference.name,
                    reference.start,
                    reference.end,
                )
            })
            .collect(),
    )
}
