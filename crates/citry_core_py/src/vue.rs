use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use citry_vue_compiler::{CompileRequest, compile};

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

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(compile_vue, module)?)
}
