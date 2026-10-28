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
    BrowserAnalysis, BrowserAnalysisMode, BrowserComponentAnalysis,
    analyze_browser_binding_pattern as analyze_browser_binding_pattern_rust,
    analyze_browser_source as analyze_browser_source_rust,
    analyze_component_scope_writes as analyze_component_scope_writes_rust,
    analyze_component_source as analyze_component_source_rust,
};
use citry_template_parser::compiler::{
    check_template_depth, compile_prepared_template as compile_prepared_template_rust,
    compile_template as compile_template_rust,
};
use citry_template_parser::error::CompileError;
use citry_template_parser::lang::lang::Lang;
use citry_template_parser::parser::{
    parse_template as parse_template_rust,
    parse_template_with_options as parse_template_with_options_rust,
};
use citry_template_parser::parser_context::TagRules;
use citry_template_parser::stack::{with_enough_stack, with_enough_stack_where_measurable};
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
        ParseError::Syntax(_) | ParseError::TooDeep(..) => {
            PySyntaxError::new_err(diagnostic.message.clone())
        }
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
/// - SyntaxError: If the template has invalid syntax, or nests more than 512
///   tags of any kind or more than 256 Citry logic levels.
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
    // The guard comes first so that the parser's large frames run on a new
    // stack segment when Python has left little stack (see
    // `with_enough_stack`). The work reads only Rust data.
    let result = with_enough_stack(|| match options {
        Some(options) => {
            parse_template_with_options_rust(input, lang_enum, rules_rc.as_ref(), &options)
        }
        None => parse_template_rust(input, lang_enum, rules_rc.as_ref()),
    });
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
/// - SyntaxError: If a template built by hand nests more than 512 tags of any
///   kind or more than 256 Citry logic levels.
/// - ValueError: If compilation fails or an unknown language is specified.
#[pyfunction]
#[pyo3(signature = (template, lang=None))]
pub fn compile_template(template: PyRef<'_, Template>, lang: Option<&str>) -> PyResult<String> {
    let lang_enum = lang_from_str(lang)?;
    // A tree built by hand can nest past the parser's limits, so its depth
    // is checked first, with a loop instead of recursion. The clone shares
    // the tree with the Python object, and one compile copies each node once,
    // as it takes the tree apart; the compiler runs inside this guard.
    check_template_depth(&template).map_err(compile_error_to_py)?;
    with_enough_stack(|| compile_template_rust((*template).clone(), lang_enum))
        .map_err(compile_error_to_py)
}

/// Compile a parsed template into the private Python prepared-render node form.
#[pyfunction(name = "_compile_prepared_template")]
#[pyo3(signature = (template, lang=None))]
pub fn compile_prepared_template(
    template: PyRef<'_, Template>,
    lang: Option<&str>,
) -> PyResult<String> {
    let lang_enum = lang_from_str(lang)?;
    // Borrowed and checked for the same reasons as in `compile_template`.
    check_template_depth(&template).map_err(compile_error_to_py)?;
    with_enough_stack(|| compile_prepared_template_rust((*template).clone(), lang_enum))
        .map_err(compile_error_to_py)
}

/// Parse one browser expression or listener statement.
///
/// Returns a `BrowserAnalysis` record: whether the text is valid, the
/// parser's first syntax error when it is not, and each free name with
/// whether the code writes to it. The record is the Rust struct itself, so
/// its fields are defined once, in `citry_template_parser::browser`.
#[pyfunction]
pub fn analyze_browser_source(input: &str, mode: &str) -> PyResult<BrowserAnalysis> {
    let mode = mode
        .parse::<BrowserAnalysisMode>()
        .map_err(PyValueError::new_err)?;
    // Rendering a fill outside the component that wrote it analyzes its
    // expressions on every render, so this skips the guard on wasm32.
    Ok(with_enough_stack_where_measurable(|| {
        analyze_browser_source_rust(input, mode)
    }))
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
    let analysis = with_enough_stack(|| analyze_browser_binding_pattern_rust(input));
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
    with_enough_stack(|| analyze_component_scope_writes_rust(input))
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

/// Analyze the JavaScript of a component's `$component(...)` calls and return
/// a `BrowserComponentAnalysis` record.
#[pyfunction]
pub fn analyze_component_source(input: &str) -> BrowserComponentAnalysis {
    with_enough_stack(|| analyze_component_source_rust(input))
}
