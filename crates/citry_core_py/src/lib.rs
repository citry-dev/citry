// Lints we accept for the PyO3 bindings crate, matching the parser crate's
// posture (large error/enum variants, complex or wide signatures).
#![allow(clippy::result_large_err)]
#![allow(clippy::large_enum_variant)]
#![allow(clippy::type_complexity)]
#![allow(clippy::too_many_arguments)]

pub mod client_graph;
pub mod html_transform;
pub mod i18n;
pub mod safe_eval;
pub mod template_formatter;
pub mod template_parser;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet};

use citry_template_parser::constants::{
    CITRY_DIRECTIVE_NAMES, HTML_VOID_ELEMENTS, RESERVED_TAG_NAMES, STRUCTURAL_TAG_ATTRIBUTE_NAMES,
};
use citry_template_parser::{
    Comment, Expr, FillDataField, FillDataPattern, HtmlAttr, HtmlAttrKind, HtmlEndTag,
    HtmlStartTag, Node, ParseDiagnostic, StaticNamedSlot, TagRules, Template, TemplateElement,
    Text, Token,
};

use crate::client_graph::canonical_json_and_revision;
use crate::html_transform::{mark_html, scan_alpine_html, transform_html};
use crate::i18n::{
    I18nCompileError, PyCatalogCompiler, PyCompiledCatalog, PyTextCatalog, canonicalize_locale,
    locale_direction,
};
use crate::template_formatter::{
    PyEmbeddedFormatPlan, TemplateFormatError, finish_embedded_format, format_template,
    prepare_embedded_format, python_expression_provider,
};
use crate::template_parser::{
    analyze_browser_source, analyze_component_scope_writes, analyze_component_source,
    compile_template, parse_template,
};

/// Singular Python API that brings together all the other Rust crates.
/// Each crate is exposed as a submodule.
///
/// NOTE: The name of this function will be the name of the Python module.
///       It MUST match the `module-name` setting in `pyproject.toml` in `packages/py/citry_core/`.
#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // HTML transformer
    let html_transform_mod = PyModule::new(m.py(), "html_transform")?;
    m.add_submodule(&html_transform_mod)?;
    html_transform_mod.add_function(wrap_pyfunction!(transform_html, &html_transform_mod)?)?;
    html_transform_mod.add_function(wrap_pyfunction!(mark_html, &html_transform_mod)?)?;
    html_transform_mod.add_function(wrap_pyfunction!(scan_alpine_html, &html_transform_mod)?)?;

    // Client graph canonicalization
    let client_graph_mod = PyModule::new(m.py(), "client_graph")?;
    m.add_submodule(&client_graph_mod)?;
    client_graph_mod.add_function(wrap_pyfunction!(
        canonical_json_and_revision,
        &client_graph_mod
    )?)?;

    // Internationalization primitives
    let i18n_mod = PyModule::new(m.py(), "i18n")?;
    m.add_submodule(&i18n_mod)?;
    i18n_mod.add_function(wrap_pyfunction!(canonicalize_locale, &i18n_mod)?)?;
    i18n_mod.add_function(wrap_pyfunction!(locale_direction, &i18n_mod)?)?;
    i18n_mod.add_class::<PyTextCatalog>()?;
    i18n_mod.add_class::<PyCatalogCompiler>()?;
    i18n_mod.add_class::<PyCompiledCatalog>()?;
    i18n_mod.add("I18nCompileError", m.py().get_type::<I18nCompileError>())?;

    // Safe eval
    let safe_eval_mod = PyModule::new(m.py(), "safe_eval")?;
    m.add_submodule(&safe_eval_mod)?;
    safe_eval_mod.add_function(wrap_pyfunction!(
        crate::safe_eval::safe_eval,
        &safe_eval_mod
    )?)?;

    // Template formatter
    let template_formatter_mod = PyModule::new(m.py(), "template_formatter")?;
    m.add_submodule(&template_formatter_mod)?;
    template_formatter_mod
        .add_function(wrap_pyfunction!(format_template, &template_formatter_mod)?)?;
    template_formatter_mod.add_function(wrap_pyfunction!(
        python_expression_provider,
        &template_formatter_mod
    )?)?;
    template_formatter_mod.add_function(wrap_pyfunction!(
        prepare_embedded_format,
        &template_formatter_mod
    )?)?;
    template_formatter_mod.add_function(wrap_pyfunction!(
        finish_embedded_format,
        &template_formatter_mod
    )?)?;
    template_formatter_mod.add_class::<PyEmbeddedFormatPlan>()?;
    template_formatter_mod.add(
        "TemplateFormatError",
        m.py().get_type::<TemplateFormatError>(),
    )?;

    // Template parser
    let template_parser_mod = PyModule::new(m.py(), "template_parser")?;
    m.add_submodule(&template_parser_mod)?;
    // Functions
    template_parser_mod.add_function(wrap_pyfunction!(parse_template, &template_parser_mod)?)?;
    template_parser_mod.add_function(wrap_pyfunction!(compile_template, &template_parser_mod)?)?;
    template_parser_mod.add_function(wrap_pyfunction!(
        analyze_browser_source,
        &template_parser_mod
    )?)?;
    template_parser_mod.add_function(wrap_pyfunction!(
        analyze_component_scope_writes,
        &template_parser_mod
    )?)?;
    template_parser_mod.add_function(wrap_pyfunction!(
        analyze_component_source,
        &template_parser_mod
    )?)?;
    // AST classes
    template_parser_mod.add_class::<ParseDiagnostic>()?;
    template_parser_mod.add_class::<Token>()?;
    template_parser_mod.add_class::<Comment>()?;
    template_parser_mod.add_class::<HtmlAttrKind>()?;
    template_parser_mod.add_class::<FillDataField>()?;
    template_parser_mod.add_class::<FillDataPattern>()?;
    template_parser_mod.add_class::<HtmlAttr>()?;
    template_parser_mod.add_class::<HtmlStartTag>()?;
    template_parser_mod.add_class::<HtmlEndTag>()?;
    template_parser_mod.add_class::<Expr>()?;
    template_parser_mod.add_class::<Text>()?;
    template_parser_mod.add_class::<Node>()?;
    template_parser_mod.add_class::<TemplateElement>()?;
    template_parser_mod.add_class::<StaticNamedSlot>()?;
    template_parser_mod.add_class::<Template>()?;
    // Config
    template_parser_mod.add_class::<TagRules>()?;
    // Constants
    // HTML void elements (elements that cannot have children, e.g. <br/>),
    // single-sourced from the Rust parser so Python never drifts from it.
    template_parser_mod.add(
        "HTML_VOID_ELEMENTS",
        PyFrozenSet::new(m.py(), HTML_VOID_ELEMENTS)?,
    )?;
    // Structural <c-*> names come from the parser itself, so Python registries
    // and documentation guards cannot drift from the grammar's reserved set.
    template_parser_mod.add(
        "RESERVED_TAG_NAMES",
        PyFrozenSet::new(m.py(), RESERVED_TAG_NAMES)?,
    )?;
    // Fixed directives and context-qualified structural attributes let editor
    // integrations prove that their syntax help covers the parser contract.
    template_parser_mod.add(
        "CITRY_DIRECTIVE_NAMES",
        PyFrozenSet::new(m.py(), CITRY_DIRECTIVE_NAMES)?,
    )?;
    let structural_attributes = PyDict::new(m.py());
    for (tag_name, attribute_names) in STRUCTURAL_TAG_ATTRIBUTE_NAMES {
        structural_attributes.set_item(
            tag_name,
            PyFrozenSet::new(m.py(), attribute_names.iter().copied())?,
        )?;
    }
    let mapping_proxy = m
        .py()
        .import("types")?
        .getattr("MappingProxyType")?
        .call1((structural_attributes,))?;
    template_parser_mod.add("STRUCTURAL_TAG_ATTRIBUTE_NAMES", mapping_proxy)?;

    Ok(())
}
