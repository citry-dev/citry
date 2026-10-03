use std::collections::HashMap;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use citry_vue_compiler::server_render::{
    RenderRequest, ServerRenderProgram as Program, read_program, render_for_hydration as render,
};
use citry_vue_compiler::{CompileRequest, DynamicElement, compile};

#[pyfunction(name = "_compile_vue")]
#[pyo3(signature = (template, local_calls_json="[]", element_bindings_json="[]", local_call_runs_json="[]", dynamic_elements_json="[]"))]
pub fn compile_vue(
    template: String,
    local_calls_json: &str,
    element_bindings_json: &str,
    local_call_runs_json: &str,
    dynamic_elements_json: &str,
) -> PyResult<String> {
    let local_calls = serde_json::from_str(local_calls_json)
        .map_err(|error| PyValueError::new_err(format!("invalid local call metadata: {error}")))?;
    let element_bindings = serde_json::from_str(element_bindings_json).map_err(|error| {
        PyValueError::new_err(format!("invalid element binding metadata: {error}"))
    })?;
    let local_call_runs = serde_json::from_str(local_call_runs_json).map_err(|error| {
        PyValueError::new_err(format!("invalid local call run metadata: {error}"))
    })?;
    let dynamic_elements = serde_json::from_str(dynamic_elements_json).map_err(|error| {
        PyValueError::new_err(format!("invalid dynamic element metadata: {error}"))
    })?;
    serde_json::to_string(&compile(CompileRequest {
        template,
        local_calls,
        local_call_runs,
        element_bindings,
        dynamic_elements,
    }))
    .map_err(|error| PyValueError::new_err(format!("cannot serialize Vue artifact: {error}")))
}

/// One compiled render function, read once so the server can run it to
/// write HTML that Vue adopts in the browser.
#[pyclass(frozen, name = "ServerRenderProgram", module = "citry_core._rust.vue")]
pub struct ServerRenderProgram {
    program: Program,
}

#[pymethods]
impl ServerRenderProgram {
    /// Whether every part of the render function was read; unread parts
    /// are left for the browser to build.
    #[getter]
    fn fully_supported(&self) -> bool {
        self.program.fully_supported()
    }
}

/// Read a compiled render function (`code` from the compiler artifact).
///
/// **Raises**
///
/// ValueError: If the code is not a render function the compiler emits, or
/// the dynamic element metadata is invalid.
#[pyfunction(name = "_read_server_render_program")]
#[pyo3(signature = (code, dynamic_elements_json="[]"))]
pub fn read_server_render_program(
    code: &str,
    dynamic_elements_json: &str,
) -> PyResult<ServerRenderProgram> {
    let dynamic_elements: Vec<DynamicElement> = serde_json::from_str(dynamic_elements_json)
        .map_err(|error| {
            PyValueError::new_err(format!("invalid dynamic element metadata: {error}"))
        })?;
    let aliases = dynamic_elements
        .into_iter()
        .map(|item| (item.alias, item.tag))
        .collect::<Vec<_>>();
    read_program(code, &aliases)
        .map(|program| ServerRenderProgram { program })
        .map_err(|reason| PyValueError::new_err(format!("cannot read render function: {reason}")))
}

/// One declined part: `(code, detail, component type key, shell tag, shell
/// content)`.
type DeclineTuple = (&'static str, String, Option<String>, Option<String>, bool);

/// Write a page's Vue host content for hydration from its prepared manifest.
///
/// `programs` maps compiled definition ids to their read render functions,
/// `manifest_json` is the prepared manifest, `tags` maps each type key to its
/// registered component tag, and the page is only returned when it writes
/// more than `threshold` elements. `full_parse_check` parses the whole
/// written HTML instead of first checking its tokens against stored parser
/// answers; the two checks must agree, and the render parity check reports
/// any page where they do not. Returns `(html, element_count, shell_count,
/// declines, reason)`, where each decline is `(code, detail, component type
/// key, shell tag, shell content)` and `shell content` says whether the shell
/// carries Citry's HTML for its contents. `html` is `None` and `reason` names
/// why when the page should mount in the browser instead.
#[pyfunction(name = "_render_for_hydration")]
#[pyo3(signature = (programs, manifest_json, tags, threshold, *, full_parse_check=false))]
pub fn render_for_hydration(
    py: Python<'_>,
    programs: HashMap<String, Py<ServerRenderProgram>>,
    manifest_json: &str,
    tags: HashMap<String, String>,
    threshold: usize,
    full_parse_check: bool,
) -> (
    Option<String>,
    usize,
    usize,
    Vec<DeclineTuple>,
    Option<&'static str>,
) {
    let programs = programs
        .iter()
        .map(|(id, program)| (id.clone(), &program.get().program))
        .collect::<HashMap<_, _>>();
    // The render reads only Rust data, so other Python threads may run.
    let result = py.detach(|| {
        render(&RenderRequest {
            programs: &programs,
            manifest_json,
            tags: &tags,
            threshold,
            full_parse_check,
        })
    });
    let declines = result
        .declines
        .into_iter()
        .map(|decline| {
            (
                decline.code,
                decline.detail,
                decline.component,
                decline.shell_tag,
                decline.shell_content,
            )
        })
        .collect();
    (
        result.html,
        result.element_count,
        result.shell_count,
        declines,
        result.reason,
    )
}

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(compile_vue, module)?)?;
    module.add_class::<ServerRenderProgram>()?;
    module.add_function(wrap_pyfunction!(read_server_render_program, module)?)?;
    module.add_function(wrap_pyfunction!(render_for_hydration, module)?)
}
