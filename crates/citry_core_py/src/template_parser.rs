/// Python interface for the citry_template_parser crate (V3).
///
/// Exposes `parse_template` and `compile_template` as thin wrappers that
/// convert Python-friendly arguments (lang as a string, user_rules as a
/// dict) into their Rust equivalents and map errors to Python exceptions.
use std::collections::HashMap;
use std::rc::Rc;

use pyo3::exceptions::{PySyntaxError, PyValueError};
use pyo3::prelude::*;

use citry_template_parser::compiler::compile_template as compile_template_rust;
use citry_template_parser::error::CompileError;
use citry_template_parser::lang::lang::Lang;
use citry_template_parser::parser::parse_template as parse_template_rust;
use citry_template_parser::parser_context::TagRules;
use citry_template_parser::{ParseError, Template};

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

fn parse_error_to_py(e: ParseError) -> PyErr {
    match e {
        ParseError::Syntax(_) => PySyntaxError::new_err(e.to_string()),
        ParseError::Value(_) => PyValueError::new_err(e.to_string()),
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
#[pyo3(signature = (input, lang=None, user_rules=None))]
pub fn parse_template(
    input: &str,
    lang: Option<&str>,
    user_rules: Option<HashMap<String, TagRules>>,
) -> PyResult<Template> {
    let lang_enum = lang_from_str(lang)?;
    let rules_rc = user_rules.map(Rc::new);
    parse_template_rust(input, lang_enum, rules_rc.as_ref()).map_err(parse_error_to_py)
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
